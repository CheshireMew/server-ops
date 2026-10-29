"""Check the SSH CLI contract without connecting to a real server."""
from __future__ import annotations

from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

import server


class JsonOutput(io.StringIO):
    def reconfigure(self, **_options):
        pass


class ServerContractTests(unittest.TestCase):
    def test_cli_forwards_command_and_remote_exit_code(self):
        command = "printf 'SSH CLI contract\\n'"
        output = JsonOutput()
        config = {"default_server": "prod"}
        result = {"exit_code": 3, "stdout": "contract", "stderr": "", "approval_provided": False}
        with patch.object(server, "load_config", return_value=config), \
             patch.object(server, "execute", return_value=result) as executor, \
             patch("sys.argv", ["server.py", "exec", "--command", command]), \
             redirect_stdout(output):
            self.assertEqual(server.main(), 3)
        executor.assert_called_once_with("prod", command, 30, config, None)
        self.assertEqual(json.loads(output.getvalue()), result)

    def test_script_cli_forwards_full_content_and_explicit_parameters(self):
        script = "#!/bin/sh\nprintf 'first line\\n'\nprintf 'last line\\n'\n"
        quote = "用户对本次准确操作的授权记录"
        output = JsonOutput()
        config = {"default_server": "prod"}
        with patch.object(server, "load_config", return_value=config), \
             patch.object(Path, "read_text", return_value=script) as reader, \
             patch.object(server, "execute", return_value={"exit_code": 0}) as executor, \
             patch("sys.argv", ["server.py", "exec", "--server", "staging", "--script", "input.sh",
                                "--timeout", "45", "--user-approval", quote]), \
             redirect_stdout(output):
            self.assertEqual(server.main(), 0)
        reader.assert_called_once_with(encoding="utf-8-sig")
        executor.assert_called_once_with("staging", script, 45, config, quote)

    def test_invalid_execution_input_does_not_reach_ssh(self):
        for arguments in (["--command", "  "], ["--command", "printf contract", "--timeout", "0"],
                          ["--server", "../other", "--command", "printf contract"]):
            with self.subTest(arguments=arguments):
                output = JsonOutput()
                with patch.object(server, "load_config", return_value={"default_server": "prod"}), \
                     patch.object(server, "execute") as executor, \
                     patch("sys.argv", ["server.py", "exec", *arguments]), \
                     redirect_stdout(output):
                    self.assertEqual(server.main(), 1)
                executor.assert_not_called()
                self.assertIn("error", json.loads(output.getvalue()))

    def test_execution_error_remains_a_json_error(self):
        output = JsonOutput()
        with patch.object(server, "load_config", return_value={"default_server": "prod"}), \
             patch.object(server, "execute", side_effect=TimeoutError("contract timeout")), \
             patch("sys.argv", ["server.py", "exec", "--command", "printf contract"]), \
             redirect_stdout(output):
            self.assertEqual(server.main(), 1)
        self.assertEqual(json.loads(output.getvalue()), {"error": "contract timeout"})

    def test_ssh_result_redaction_and_authorization_record(self):
        credentials = {"host": "ssh.example.com", "port": 22, "username": "operator",
                       "password": "test-login-secret"}
        command = "printf contract"
        for approval, expected in ((None, False), ("  ", False), ("实际用户授权记录", True)):
            with self.subTest(approval=approval):
                client = MagicMock()
                stdin, stdout, stderr = MagicMock(), MagicMock(), MagicMock()
                client.exec_command.return_value = (stdin, stdout, stderr)
                channel = stdout.channel
                channel.recv_ready.side_effect = [True, False, False]
                channel.recv.return_value = b"result test-login-secret"
                channel.recv_stderr_ready.side_effect = [True, False, False]
                channel.recv_stderr.return_value = b"diagnostic test-login-secret"
                channel.exit_status_ready.return_value = True
                channel.recv_exit_status.return_value = 7
                with patch.object(server, "load_credentials", return_value=credentials), \
                     patch.object(Path, "is_file", return_value=True), \
                     patch("paramiko.SSHClient", return_value=client):
                    result = server.execute("prod", command, 45,
                                            {"known_hosts": "D:/Tools/ssh/known_hosts"}, approval)
                client.exec_command.assert_called_once_with(command, timeout=45)
                client.set_missing_host_key_policy.assert_called_once()
                client.close.assert_called_once()
                self.assertEqual(result, {
                    "server": "prod", "host": "ssh.example.com", "username": "operator",
                    "approval_provided": expected, "exit_code": 7,
                    "stdout": "result [登录密码已隐藏]", "stderr": "diagnostic [登录密码已隐藏]",
                })


if __name__ == "__main__":
    unittest.main()

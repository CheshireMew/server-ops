<!-- readme-header:start -->

<p align="center">
  <img src="./assets/readme/logo.svg" width="112" alt="Server Ops">
</p>

<h1 align="center">Server Ops</h1>

<p align="center">
  <strong>An Agent Skill for SSH server checks, approved deployment and maintenance, and result verification.</strong>
</p>

<p align="center">
  <a href="./README.md">中文</a> · <strong>English</strong> · <a href="./README.ja.md">日本語</a> | <a href="./references/usage.md">文档</a> | <a href="./CONTRIBUTING.md">贡献</a> | <a href="https://github.com/CheshireMew/server-ops/issues">反馈</a>
</p>

<p align="center">
  <a href="https://x.com/0xCheshire" title="X"><img src="https://img.shields.io/badge/X-%400xCheshire-000000?logo=x&amp;logoColor=white" alt="X：@0xCheshire"></a>
  <a href="https://t.me/CheshireBTC" title="Telegram"><img src="https://img.shields.io/badge/Telegram-CheshireBTC-26A5E4?logo=telegram&amp;logoColor=white" alt="Telegram：CheshireBTC"></a>
  <a href="https://blog.blacknico.com/" title="Blog"><img src="https://img.shields.io/badge/Blog-blog.blacknico.com-2E7D32?logo=rss&amp;logoColor=white" alt="博客：blog.blacknico.com"></a>
  <a href="https://blacknico.com/" title="Homepage"><img src="https://img.shields.io/badge/Home-blacknico.com-1F6FEB?logo=googlechrome&amp;logoColor=white" alt="个人主页：blacknico.com"></a>
</p>

<p align="center">
  <a href="https://github.com/CheshireMew/server-ops/stargazers"><img src="https://img.shields.io/github/stars/CheshireMew/server-ops?style=flat" alt="GitHub Stars"></a>
  <a href="https://github.com/CheshireMew/server-ops/forks"><img src="https://img.shields.io/github/forks/CheshireMew/server-ops?style=flat" alt="GitHub Forks"></a>
  <a href="https://github.com/CheshireMew/server-ops/blob/HEAD/LICENSE"><img src="https://img.shields.io/github/license/CheshireMew/server-ops?style=flat" alt="Repository License"></a>
</p>

<!-- readme-header:end -->

Server Ops is an Agent Skill for server operations through SSH. Tell an external Agent which server and project to work on; it investigates, carries out approved changes, and checks the result against the server's actual state. A local tool stores and uses login credentials, so everyday requests only need a server alias.

## Tell the Agent what you need

After loading [SKILL.md](./SKILL.md) and configuring an account, start with:

```text
$server-ops Check prod and report its current state and any issues that need attention.
```

| Task | Example request | Result |
| --- | --- | --- |
| Inspect services and logs | Check nginx on prod and its last 50 log entries; investigate the errors. | Current state, relevant evidence, and remaining unknowns |
| Deploy or update a project | Check the specified project's version, configuration, and startup method on prod; propose an update. | A concrete plan for approval, followed by execution and verification |
| Change configuration or maintain a service | Inspect nginx configuration on prod and explain the required changes and checks. | Scope and impact, then implementation and verification after approval |

Read-only queries and simple harmless operations within the requested task proceed without additional confirmation. Deployments, changes to running configuration, deletion, installation, restarts, and other dangerous operations require your authorization for the specific target and scope. When that authorization is missing, the Agent explains the server, scope, and impact before asking. An approved plan can proceed without asking again for every command.

## Get started

The local tool currently runs on **Windows** and requires **Python 3.10 or newer, Paramiko, and Tkinter**. Remote command examples target Linux; the Agent chooses commands for the actual server.

### 1. Get and load the Skill

```powershell
git clone https://github.com/CheshireMew/server-ops.git D:\Tools\agent-skills\server-ops
Set-Location D:\Tools\agent-skills\server-ops
$serverOpsRoot = (Get-Location).Path
```

Load this directory's `SKILL.md` in a compatible Agent, following that Agent's installation or loading process. You can also call the tool directly from PowerShell.

### 2. Configure the local environment

Choose a Python installation that can import Paramiko and Tkinter. Adjust the example tool path to your machine:

```powershell
& 'D:\Tools\Python310\python.exe' -m pip install paramiko
& 'D:\Tools\Python310\python.exe' -c 'import paramiko, tkinter'
New-Item -ItemType Directory -Path "$serverOpsRoot\.local" -Force | Out-Null
```

Create `.local/config.json` with your Python executable, SSH host record file, and default server alias:

```json
{
  "version": 1,
  "python_executable": "D:/Tools/Python310/python.exe",
  "known_hosts": "D:/Tools/ssh/known_hosts",
  "default_server": "prod"
}
```

`known_hosts` must already exist and contain the target server's verified public key. The tool rejects unknown hosts and mismatched keys. Verify the host key and prepare its record before the first connection.

### 3. Save an account and check the connection

```powershell
& "$serverOpsRoot\server-ops.ps1" setup --server prod --host ssh.example.com
& "$serverOpsRoot\server-ops.ps1" status --server prod
& "$serverOpsRoot\server-ops.ps1" exec --server prod --command 'hostname; whoami; date -Is'
```

Replace the example address and enter the port, username, and password in the window. `status` only checks the saved local account. The final command opens the SSH connection: confirm that `exit_code` is `0` and that `stdout` identifies the expected host, user, and time.

To edit the default account later, double-click [打开服务器账号填写窗口.cmd](./打开服务器账号填写窗口.cmd). Leaving the password blank preserves an existing password.

## Common commands

Use `server-ops.ps1` as the entry point, with `$serverOpsRoot` from the setup above.

| Command | Purpose |
| --- | --- |
| `list` | List saved local server accounts |
| `status --server prod` | Inspect a local account |
| `setup --server prod --host ssh.example.com` | Add or update an account |
| `exec --server prod --command 'uptime'` | Execute a command through SSH |
| `exec --server prod --script <local-script-path>` | Read a UTF-8 script and execute its contents remotely |

Omitting `--server` uses `default_server`. The command timeout defaults to 30 seconds; change it with `--timeout 60`. Store longer task scripts in the Skill's `.runs` directory. See [tool usage](./references/usage.md) for complete examples; the detailed working documents are currently in Chinese.

`list`, `status`, and `exec` return JSON. Execution results include `server`, `host`, `username`, `exit_code`, `stdout`, `stderr`, and `approval_provided`. The Agent reads the complete command or script and assesses its actual effects; the tool no longer uses a command allowlist to block queries or unfamiliar syntax. Read-only and harmless operations omit `--user-approval`; dangerous operations use it to record actual user authorization. The tool returns the remote exit code unchanged. See [SKILL.md](./SKILL.md) for the approval process.

A timeout closes the SSH channel; the remote task may still be running. Check its state before retrying.

## File locations

| Location | Contents |
| --- | --- |
| [SKILL.md](./SKILL.md) | Agent workflow, approval requirements, and completion criteria |
| [references/usage.md](./references/usage.md) | Configuration, commands, and result details |
| `scripts/` | SSH tool and local contract tests |
| `.local/` | Local configuration, encrypted accounts, and server notes; ignored by Git |
| `.runs/` | Task scripts, diagnostic material, and log copies; ignored by Git |

Paths are resolved from the Skill's location, regardless of the caller's working directory. Accounts are encrypted for the Windows user who saves them; enter them again on another machine or Windows account. SSH output is returned to the caller by default; save it in `.runs` when a record is needed.

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for maintenance and checks. Report issues or suggestions through [Issues](https://github.com/CheshireMew/server-ops/issues).

## License

Licensed under **MPL-2.0**. See [LICENSING.md](./LICENSING.md) for scope and third-party dependencies, and [LICENSE](./LICENSE) for the full text.

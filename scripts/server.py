"""Windows encrypted server accounts and a JSON-producing SSH command line."""
from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sys
import time

from guardrails import ApprovalRequired, enforce_approval

SKILL_ROOT = Path(__file__).resolve().parents[1]
LOCAL_ROOT = SKILL_ROOT / ".local"
CONFIG_FILE = LOCAL_ROOT / "config.json"
SERVERS_ROOT = LOCAL_ROOT / "servers"
RUN_ROOT = SKILL_ROOT / ".runs"
ALIAS_PATTERN = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?\Z")
RESERVED_NAMES = {"con", "prn", "aux", "nul"} | {
    f"{prefix}{number}" for prefix in ("com", "lpt") for number in range(1, 10)
}


def validate_alias(alias: str) -> str:
    if not isinstance(alias, str) or not ALIAS_PATTERN.fullmatch(alias) or alias in RESERVED_NAMES:
        raise ValueError("服务器别名需为 1–64 个小写字母、数字或连字符，且不能使用 Windows 保留名称")
    return alias


def load_config() -> dict:
    if not CONFIG_FILE.is_file():
        raise RuntimeError("缺少 .local/config.json，请按 references/usage.md 配置本机入口")
    config = json.loads(CONFIG_FILE.read_text(encoding="utf-8-sig"))
    if not isinstance(config, dict) or config.get("version") != 1:
        raise ValueError("本机配置 version 必须为 1")
    for key in ("python_executable", "known_hosts"):
        value = config.get(key)
        if not isinstance(value, str) or not Path(value).is_absolute():
            raise ValueError(f"本机配置 {key} 必须是绝对路径")
    validate_alias(config.get("default_server", ""))
    return config


def credential_path(alias: str) -> Path:
    return SERVERS_ROOT / validate_alias(alias) / "credentials.dpapi"


class DataBlob(ctypes.Structure):
    _fields_ = [("size", wintypes.DWORD), ("data", ctypes.POINTER(ctypes.c_ubyte))]


def windows_protect(data: bytes, *, decrypt: bool = False) -> bytes:
    if os.name != "nt":
        raise RuntimeError("此账号文件只能在保存它的 Windows 账号下使用")
    buffer = ctypes.create_string_buffer(data)
    source = DataBlob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)))
    output = DataBlob()
    crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
    function = crypt32.CryptUnprotectData if decrypt else crypt32.CryptProtectData
    function.argtypes = [
        ctypes.POINTER(DataBlob), ctypes.c_void_p, ctypes.c_void_p,
        ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(DataBlob),
    ]
    function.restype = wintypes.BOOL
    if not function(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(output)):
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        return ctypes.string_at(output.data, output.size)
    finally:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.LocalFree.argtypes = [ctypes.c_void_p]
        kernel32.LocalFree.restype = ctypes.c_void_p
        kernel32.LocalFree(output.data)


def load_credentials(alias: str) -> dict:
    path = credential_path(alias)
    if not path.is_file():
        raise RuntimeError(f"尚未保存 {alias} 的账号，请运行 setup --server {alias}")
    stored = json.loads(windows_protect(path.read_bytes(), decrypt=True))
    if not isinstance(stored, dict) or stored.get("version") != 1:
        raise ValueError(f"{alias} 的账号文件版本不受支持")
    for key in ("host", "username", "password", "saved_at"):
        if not isinstance(stored.get(key), str) or not stored[key]:
            raise ValueError(f"{alias} 的账号文件缺少 {key}")
    if type(stored.get("port")) is not int or not 1 <= stored["port"] <= 65535:
        raise ValueError(f"{alias} 的账号端口无效")
    return stored


def save_credentials(alias: str, host: str, port: str, username: str, password: str) -> None:
    path = credential_path(alias)
    host, username = host.strip(), username.strip()
    if not password and path.is_file():
        password = load_credentials(alias)["password"]
    if not host or not username or not password:
        raise ValueError("请填写服务器地址、用户名和密码；已有账号的密码留空可保留原密码")
    try:
        port_number = int(port)
    except ValueError:
        raise ValueError("SSH 端口必须是数字") from None
    if not 1 <= port_number <= 65535:
        raise ValueError("SSH 端口必须在 1 到 65535 之间")
    payload = {
        "version": 1, "host": host, "port": port_number,
        "username": username, "password": password,
        "saved_at": datetime.now(timezone.utc).isoformat(),
    }
    encrypted = windows_protect(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_suffix(".pending")
    pending.write_bytes(encrypted)
    os.replace(pending, path)


def setup(alias: str, host: str | None) -> None:
    import tkinter as tk
    from tkinter import messagebox, ttk

    defaults = {"host": "", "port": 22, "username": "root"}
    existing = credential_path(alias).is_file()
    if existing:
        stored = load_credentials(alias)
        defaults.update({key: stored[key] for key in defaults})
    if host is not None:
        defaults["host"] = host
    root = tk.Tk()
    root.title(f"Server Ops · {alias} 登录账号")
    root.geometry("660x410")
    root.resizable(False, False)
    frame = ttk.Frame(root, padding=22)
    frame.pack(fill="both", expand=True)
    ttk.Label(frame, text=f"填写 {alias} 的服务器账号", font=("Microsoft YaHei UI", 12)).grid(
        row=0, column=0, columnspan=2, sticky="w", pady=(0, 18),
    )
    variables = {}
    password_entry = None
    for index, (key, label) in enumerate([
        ("host", "服务器地址"), ("port", "SSH 端口"),
        ("username", "用户名"), ("password", "密码"),
    ], start=1):
        ttk.Label(frame, text=label).grid(row=index, column=0, sticky="w", padx=(0, 16), pady=7)
        variables[key] = tk.StringVar(value=str(defaults.get(key, "")))
        entry = ttk.Entry(frame, textvariable=variables[key], width=50,
                          show="●" if key == "password" else "")
        entry.grid(row=index, column=1, sticky="ew", pady=7)
        if key == "password":
            password_entry = entry
    password_note = "密码留空会保留已保存的密码。" if existing else "首次添加请填写密码。"
    ttk.Label(
        frame,
        text=f"{password_note}\n账号使用 Windows 加密，保存在本 Skill 的 .local 目录。\n"
             "此窗口只保存账号，不修改服务器。",
        foreground="#555555",
    ).grid(row=5, column=0, columnspan=2, sticky="w", pady=(16, 12))

    def save():
        try:
            save_credentials(alias, **{key: value.get() for key, value in variables.items()})
        except Exception as exc:
            messagebox.showerror("保存失败", str(exc), parent=root)
            return
        variables["password"].set("")
        root.destroy()

    buttons = ttk.Frame(frame)
    buttons.grid(row=6, column=0, columnspan=2, sticky="e")
    ttk.Button(buttons, text="取消", command=root.destroy).pack(side="left", padx=8)
    ttk.Button(buttons, text="保存加密账号", command=save).pack(side="left")
    root.bind("<Return>", lambda _event: save())
    root.bind("<Escape>", lambda _event: root.destroy())
    root.lift()
    root.attributes("-topmost", True)
    root.after(200, lambda: root.attributes("-topmost", False))
    password_entry.focus_set()
    root.mainloop()


def account_status(alias: str) -> dict:
    path = credential_path(alias)
    result = {"server": alias, "saved": path.is_file(), "file": str(path)}
    if result["saved"]:
        stored = load_credentials(alias)
        result.update({key: stored[key] for key in ("host", "port", "username", "saved_at")})
    return result


def redact(text: str, password: str = "") -> str:
    if password:
        text = text.replace(password, "[登录密码已隐藏]")
    return re.sub(r"\b\d{6,}:[A-Za-z0-9_-]{20,}\b", "[Telegram Token 已隐藏]", text)


def execute(alias: str, command: str, timeout: int, config: dict,
            user_approval: str | None = None) -> dict:
    enforce_approval(command, user_approval)
    import paramiko

    credentials = load_credentials(alias)
    known_hosts = Path(config["known_hosts"])
    if not known_hosts.is_file():
        raise RuntimeError(f"SSH 主机记录不存在：{known_hosts}")
    client = paramiko.SSHClient()
    client.load_system_host_keys(str(known_hosts))
    client.set_missing_host_key_policy(paramiko.RejectPolicy())
    try:
        client.connect(
            credentials["host"], port=credentials["port"],
            username=credentials["username"], password=credentials["password"],
            allow_agent=False, look_for_keys=False, timeout=12,
            banner_timeout=15, auth_timeout=15,
        )
        stdin, stdout, _stderr = client.exec_command(command, timeout=timeout)
        stdin.close()
        channel = stdout.channel
        out, err = bytearray(), bytearray()
        deadline = time.monotonic() + timeout
        while True:
            while channel.recv_ready():
                out.extend(channel.recv(65536))
            while channel.recv_stderr_ready():
                err.extend(channel.recv_stderr(65536))
            if channel.exit_status_ready() and not channel.recv_ready() and not channel.recv_stderr_ready():
                break
            if time.monotonic() >= deadline:
                channel.close()
                raise TimeoutError(
                    f"服务器命令超过 {timeout} 秒，SSH 通道已关闭；远端命令是否结束需另行检查"
                )
            time.sleep(0.05)
        return {
            "server": alias, "host": credentials["host"], "username": credentials["username"],
            "approval_provided": bool(user_approval and user_approval.strip()),
            "exit_code": channel.recv_exit_status(),
            "stdout": redact(out.decode("utf-8", "replace"), credentials["password"]),
            "stderr": redact(err.decode("utf-8", "replace"), credentials["password"]),
        }
    except paramiko.AuthenticationException:
        raise RuntimeError(f"{alias} SSH 登录失败，请检查已保存的用户名和密码") from None
    finally:
        client.close()


def main() -> int:
    if sys.stdout is not None:
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="action", required=True)
    form = subparsers.add_parser("setup", help="打开服务器账号填写窗口")
    form.add_argument("--server", help="服务器别名；省略时使用本机配置的默认服务器")
    form.add_argument("--host", help="预填服务器地址；省略时沿用已有账号")
    status = subparsers.add_parser("status", help="查看账号状态，不显示密码")
    status.add_argument("--server")
    subparsers.add_parser("list", help="列出已保存的服务器，不显示密码")
    run = subparsers.add_parser("exec", help="使用已保存的账号运行服务器命令或脚本")
    run.add_argument("--server")
    source = run.add_mutually_exclusive_group(required=True)
    source.add_argument("--command")
    source.add_argument("--script", type=Path)
    run.add_argument("--timeout", type=int, default=30)
    run.add_argument("--user-approval", help="当前会话中用户对本次具体操作的明确授权原话；不得自行填写授权")
    args = parser.parse_args()
    try:
        config = load_config()
        if args.action == "list":
            aliases = sorted(path.parent.name for path in SERVERS_ROOT.glob("*/credentials.dpapi"))
            result = {
                "default_server": config["default_server"],
                "servers": [account_status(alias) for alias in aliases],
                "skill_root": str(SKILL_ROOT), "run_root": str(RUN_ROOT),
            }
        else:
            alias = validate_alias(args.server or config["default_server"])
            if args.action == "setup":
                setup(alias, args.host)
                result = account_status(alias)
            elif args.action == "status":
                result = account_status(alias)
            else:
                command = args.command if args.command is not None else args.script.read_text(encoding="utf-8-sig")
                if not command.strip():
                    raise ValueError("服务器命令不能为空")
                if args.timeout <= 0:
                    raise ValueError("超时时间必须大于零")
                result = execute(alias, command, args.timeout, config, args.user_approval)
        print(json.dumps(result, ensure_ascii=False))
        return int(result.get("exit_code", 0))
    except ApprovalRequired as exc:
        print(json.dumps({"error": "操作已拦截：请先取得用户对具体操作的明确同意",
                          "approval_required": True, "reason": str(exc)}, ensure_ascii=False))
        return 3
    except Exception as exc:
        print(json.dumps({"error": redact(str(exc))}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Conservatively recognize Unix query commands before allowing SSH execution."""
from __future__ import annotations

import re
import shlex


class ApprovalRequired(RuntimeError):
    """The caller must first obtain the user's approval for this operation."""


QUERY_PROGRAMS = {
    "cat", "cut", "df", "du", "free", "grep", "head", "id", "ls", "ps", "pwd",
    "readlink", "realpath", "stat", "tail", "uname", "uptime", "wc", "whoami",
}
HOSTNAME_FLAGS = {
    "-a", "--alias", "-A", "--all-fqdns", "-d", "--domain", "-f", "--fqdn",
    "-i", "--ip-address", "-I", "--all-ip-addresses", "-s", "--short",
    "--help", "--version",
}
DATE_FLAGS = {
    "-u", "--utc", "--universal", "-I", "-Is", "--iso-8601",
    "--iso-8601=seconds", "--rfc-3339=seconds", "--help", "--version",
}
SYSTEMCTL_QUERIES = {
    "status", "show", "list-units", "list-unit-files", "list-timers",
    "list-dependencies", "is-active", "is-enabled", "is-failed", "get-default",
}
JOURNAL_FLAGS = {
    "--no-pager", "--no-tail", "--all", "-a", "--quiet", "-q", "--reverse", "-r",
    "--pager-end", "-e", "--dmesg", "-k", "--list-boots", "--disk-usage",
    "--catalog", "-x", "-b", "--boot", "--help", "--version", "-xe", "-ex",
}
JOURNAL_VALUE_FLAGS = {
    "-u", "--unit", "-t", "--identifier", "--since", "--until", "-S", "-U",
    "-n", "--lines", "-p", "--priority", "-o", "--output", "-D", "--directory",
    "--file", "-g", "--grep",
}


def _journal_query(arguments: list[str]) -> bool:
    index = 0
    while index < len(arguments):
        argument = arguments[index]
        if argument in JOURNAL_FLAGS:
            index += 1
        elif argument in JOURNAL_VALUE_FLAGS:
            if index + 1 == len(arguments):
                return False
            value = arguments[index + 1]
            if value.startswith("-") and not re.fullmatch(r"-?\d+", value):
                return False
            index += 2
        elif "=" in argument and argument.split("=", 1)[0] in JOURNAL_VALUE_FLAGS | {"--boot"}:
            index += 1
        elif len(argument) > 2 and argument[:2] in {"-u", "-t", "-n", "-p", "-o", "-g"}:
            index += 1
        elif re.fullmatch(r"[A-Z_][A-Z0-9_]*=.+|-?\d+", argument):
            index += 1
        else:
            return False
    return True


def _query_segment(words: list[str]) -> bool:
    executable, *arguments = words
    name = executable.rsplit("/", 1)[-1]
    if executable not in {name, f"/bin/{name}", f"/usr/bin/{name}"}:
        return False
    if name in QUERY_PROGRAMS:
        return True
    if name in {"true", "false"}:
        return not arguments
    if name == "hostname":
        return all(argument in HOSTNAME_FLAGS for argument in arguments)
    if name == "date":
        return all(argument in DATE_FLAGS or argument.startswith("+") for argument in arguments)
    if name == "systemctl":
        return bool(arguments) and arguments[0] in SYSTEMCTL_QUERIES
    if name == "journalctl":
        return _journal_query(arguments)
    if name == "docker":
        if not arguments:
            return False
        if arguments[0] == "stats":
            return "--no-stream" in arguments[1:]
        return arguments[0] in {"ps", "logs", "inspect", "images", "version", "info"}
    return False


def approval_reason(command: str) -> str | None:
    """Recognize a deliberately small shell subset; uncertain input needs approval.

    This is not a general shell interpreter or a blacklist of destructive words.
    In particular, shlex comments are disabled: '#' inside a filename must never
    hide a following command that the real shell would execute.
    """
    normalized = command.replace("\r\n", "\n")
    if re.search(r"[<>()[\]$`\\\r\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", normalized):
        return "包含重定向、替换、转义或无法安全判断的 Shell 语法"
    lexer = shlex.shlex(normalized, posix=True, punctuation_chars=";&|\n")
    lexer.whitespace = " \t"
    lexer.whitespace_split = True
    lexer.commenters = ""
    try:
        tokens = list(lexer)
    except ValueError:
        return "命令的引号或 Shell 语法无法确认"
    segments: list[list[str]] = []
    current: list[str] = []
    for token in tokens:
        if token and all(character in ";&|\n" for character in token):
            operator = token.replace("\n", "")
            if operator not in {"", ";", "|", "&&", "||"}:
                return "包含后台运行或未支持的命令连接方式"
            if current:
                segments.append(current)
                current = []
        else:
            current.append(token)
    if current:
        segments.append(current)
    if not segments or not all(_query_segment(segment) for segment in segments):
        return "包含未列为查询的命令或参数，需要用户确认具体操作"
    return None


def enforce_approval(command: str, user_approval: str | None) -> None:
    if user_approval is not None and user_approval.strip():
        return
    reason = approval_reason(command)
    if reason is not None:
        raise ApprovalRequired(reason)

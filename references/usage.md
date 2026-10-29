# 连接工具用法

工具目前运行在 Windows，使用 Python、Paramiko 和 Windows 当前账号的加密能力。正式入口是 Skill 根目录中的 `server-ops.ps1`，它读取本 Skill 的 `.local/config.json`，然后启动 `scripts/server.py`。从其它目录调用不会改变配置、账号或任务文件位置。

## 本机配置和账号

`.local/config.json` 的格式如下，三个字符串应填入本机真实值。`python_executable` 必须指向已经能导入 Paramiko 的 Python，`known_hosts` 必须指向保存目标主机记录的 SSH 文件，`default_server` 是省略 `--server` 时使用的别名。

```json
{
  "version": 1,
  "python_executable": "本机 Python 可执行文件的绝对路径",
  "known_hosts": "SSH known_hosts 文件的绝对路径",
  "default_server": "服务器别名"
}
```

账号通过填写窗口创建或更新，保存在 `.local/servers/别名/credentials.dpapi`。服务器地址、端口、用户名和密码一起由 Windows 当前账号加密。该文件在同一 Windows 账号下可以随 Skill 改变目录，换电脑或 Windows 账号后需要重新填写。

双击根目录中的“打开服务器账号填写窗口.cmd”可以编辑默认服务器账号。已有密码不会出现在输入框里；更新账号时留空会保留原密码。新增服务器使用 `setup --server 新别名 --host 地址`，服务器别名由 1–64 个小写字母、数字和连字符组成，首尾需为字母或数字，并避开 Windows 保留名称。

SSH 沿用配置指定的主机记录，不自动接受未知主机。出现未知主机或主机公钥变更时，核对实际服务器及公钥，再按用户授权更新该 SSH 记录。

## 命令入口

下面的 `$serverOpsRoot` 应设为当前加载的 server-ops 目录的绝对路径；它是 Skill 的位置，不是当前项目目录。

```powershell
$serverOpsRoot = '当前加载的 server-ops 目录绝对路径'
& "$serverOpsRoot\server-ops.ps1" list
& "$serverOpsRoot\server-ops.ps1" status --server 服务器别名
& "$serverOpsRoot\server-ops.ps1" setup --server 服务器别名 --host 服务器地址
& "$serverOpsRoot\server-ops.ps1" exec --server 服务器别名 --command 'hostname; whoami; date -Is'
```

需要较长命令时，将本次脚本保存在 Skill 的 `.runs` 中，再执行它。工具读取本地 UTF-8 脚本内容并通过 SSH 执行，不会把脚本文件安装到远端。

```powershell
$taskRoot = Join-Path $serverOpsRoot '.runs\本次任务'
New-Item -ItemType Directory -Path $taskRoot -Force | Out-Null
$scriptPath = Join-Path $taskRoot 'inspect.sh'
'hostname; whoami; date -Is' | Set-Content -LiteralPath $scriptPath -Encoding UTF8
& "$serverOpsRoot\server-ops.ps1" exec --server 服务器别名 --script $scriptPath --timeout 45
```

工具也支持读取用户明确提供的外部脚本；该路径只是输入位置，不改变账号或任务产物根目录。执行入口将完整命令或脚本交给 SSH，不做命令白名单拦截。执行 Agent 先阅读全部内容并按 Skill 正文判断实际影响；只读查询和本次目标内简单无危险的操作直接执行，较长脚本、解释器或陌生语法本身不会触发用户确认。

用户已经明确批准同一服务器和具体操作后，使用 `--user-approval '用户的明确授权原话'` 执行获批命令或脚本。这个参数是授权记录，不能作为 Agent 自行批准操作的开关；授权来源与范围的核实方法见 Skill 正文。

## 结果与依赖

`list`、`status` 和 `exec` 输出 JSON。执行结果包含服务器别名、主机、用户名、远端 `exit_code`、`stdout`、`stderr` 和是否传入授权记录的 `approval_provided`，工具进程返回远端退出码。`approval_provided` 只说明是否提供了授权记录，不是风险判定或授权有效性证明。配置、连接或执行错误输出 `error` 并返回 1；工具不再返回授权拦截状态 `approval_required`，远端退出码 3 与其它远端退出码一样原样返回。默认命令超时为 30 秒，可用 `--timeout` 指定；连接和认证分别使用短超时。账号查询、空命令和无效参数不会执行服务器命令。

登录密码和 Telegram Token 会从执行输出中隐藏。工具不提供密码导出命令；修改密码使用填写窗口。SSH 超时会关闭通道，远端任务是否仍运行应依据服务器状态判断，不能把超时当成已完成或直接重复有副作用的操作。

`.local` 和 `.runs` 由本 Skill 的 `.gitignore` 排除。服务器项目位置和运行方式可以保存在 `.local/servers/别名/notes.txt`，任务脚本、诊断文件和日志副本放在 `.runs`。工具不会默认把这些文件写入调用方仓库，也不会默认保存 SSH 输出。

Python 与依赖保留在配置指定的工具目录，安装或调整环境遵守本机要求，避免占用 C 盘。更新 Skill 源码不替换本机账号文件。检查 Skill 结构时，真实登录验证与 Markdown 预算检查分别说明各自结果。

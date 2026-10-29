<!-- readme-header:start -->

<p align="center">
  <img src="./assets/readme/logo.svg" width="112" alt="Server Ops">
</p>

<h1 align="center">Server Ops</h1>

<p align="center">
  <strong>让 Agent 通过 SSH 检查服务器、执行获准的部署维护操作，并核实实际结果。</strong>
</p>

<p align="center">
  <strong>中文</strong> · <a href="./README.en.md">English</a> · <a href="./README.ja.md">日本語</a> | <a href="./references/usage.md">文档</a> | <a href="./CONTRIBUTING.md">贡献</a> | <a href="https://github.com/CheshireMew/server-ops/issues">反馈</a>
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

Server Ops 是供外部 Agent 使用的服务器运维 Skill。告诉 Agent 要检查哪台服务器、处理哪个项目，它会通过 SSH 调查、执行获准操作，并根据服务器上的实际状态说明结果。账号由本机工具保存和使用，日常请求只需指定服务器别名。

## 直接告诉 Agent 你要做什么

加载 [SKILL.md](./SKILL.md) 并配置账号后，可以这样开始：

```text
$server-ops 检查 prod 的运行状态，列出需要处理的问题。
```

| 你要完成的事 | 请求示例 | 得到的结果 |
| --- | --- | --- |
| 查服务和日志 | 检查 prod 上 nginx 的状态和最近 50 条日志，判断报错原因。 | 当前状态、相关证据和仍需确认的问题 |
| 部署或更新项目 | 检查 prod 上指定项目的版本、配置和启动方式，给出更新方案。 | 待确认的具体操作；批准后执行并核验运行入口 |
| 修改配置或维护服务 | 检查 prod 上 nginx 的配置，说明需要怎样修改和验证。 | 修改范围和影响；批准后实施并检查结果 |

只读查询和本次目标内简单无危险的操作直接完成，无需逐条确认。部署、修改运行配置、删除、安装、重启等危险操作需要你对具体目标和范围的授权；缺少授权时先说明服务器、范围和影响，再取得同意。同一获批方案继续完成，无需逐条重复确认。

## 开始使用

工具当前运行在 **Windows**，需要 **Python 3.10 或更新版本、Paramiko 和 Tkinter**。远端命令示例面向 Linux；实际命令由 Agent 按目标服务器选择。

### 1. 获取并加载 Skill

```powershell
git clone https://github.com/CheshireMew/server-ops.git D:\Tools\agent-skills\server-ops
Set-Location D:\Tools\agent-skills\server-ops
$serverOpsRoot = (Get-Location).Path
```

让兼容的 Agent 加载这个目录中的 `SKILL.md`。Skill 的安装或加载方式由所用 Agent 决定；工具也可以直接从 PowerShell 调用。

### 2. 配置本机环境

选择一个能够导入 Paramiko 和 Tkinter 的 Python。以下为示例工具路径，按本机实际位置调整：

```powershell
& 'D:\Tools\Python310\python.exe' -m pip install paramiko
& 'D:\Tools\Python310\python.exe' -c 'import paramiko, tkinter'
New-Item -ItemType Directory -Path "$serverOpsRoot\.local" -Force | Out-Null
```

创建 `.local/config.json`，填写实际 Python 路径、SSH 主机记录文件和默认服务器别名：

```json
{
  "version": 1,
  "python_executable": "D:/Tools/Python310/python.exe",
  "known_hosts": "D:/Tools/ssh/known_hosts",
  "default_server": "prod"
}
```

`known_hosts` 必须是已存在、包含目标服务器已核实公钥的 SSH 主机记录文件。工具会拒绝未知或公钥不匹配的主机；首次连接前，先核实主机公钥并准备好记录。

### 3. 保存账号并验证连接

```powershell
& "$serverOpsRoot\server-ops.ps1" setup --server prod --host ssh.example.com
& "$serverOpsRoot\server-ops.ps1" status --server prod
& "$serverOpsRoot\server-ops.ps1" exec --server prod --command 'hostname; whoami; date -Is'
```

将示例地址换成实际地址，在窗口中填写端口、用户名和密码。`status` 只查看本地账号保存情况；最后一条命令才会建立 SSH 连接。返回的 `exit_code` 为 `0`，且 `stdout` 中的主机、用户和时间符合预期，才算这次连接验证成功。

以后可双击 [打开服务器账号填写窗口.cmd](./打开服务器账号填写窗口.cmd) 编辑默认服务器账号；已有账号的密码留空会保留原密码。

## 常用命令

统一入口是 `server-ops.ps1`，下例沿用上面的 `$serverOpsRoot`。

| 命令 | 用途 |
| --- | --- |
| `list` | 列出本机已保存的服务器 |
| `status --server prod` | 查看指定服务器的本地账号信息 |
| `setup --server prod --host ssh.example.com` | 添加或更新账号 |
| `exec --server prod --command 'uptime'` | 通过 SSH 执行命令 |
| `exec --server prod --script <本地脚本路径>` | 读取 UTF-8 脚本并在远端执行其内容 |

省略 `--server` 时使用配置中的 `default_server`。执行默认超时为 30 秒，可用 `--timeout 60` 调整。长脚本放到本 Skill 的 `.runs` 中，具体示例见 [连接工具用法](./references/usage.md)。

`list`、`status` 和 `exec` 返回 JSON。远端执行结果包含 `server`、`host`、`username`、`exit_code`、`stdout`、`stderr` 和 `approval_provided`，便于 Agent 或脚本继续检查。Agent 阅读完整命令或脚本，按实际影响判断授权要求；工具不再用命令白名单拦截查询或陌生语法。只读和无危险操作省略 `--user-approval`，危险操作用它记录真实授权，工具进程原样返回远端退出码。授权记录的用法见 [操作授权说明](./SKILL.md#危险操作的用户授权)。

超时只表示 SSH 通道已关闭，远端任务可能仍在运行。继续操作前应检查服务器状态，避免重复执行。

## 文件放在哪里

| 位置 | 内容 |
| --- | --- |
| [SKILL.md](./SKILL.md) | Agent 的工作方式、授权要求和完成标准 |
| [references/usage.md](./references/usage.md) | 配置、完整命令和结果说明 |
| `scripts/` | SSH 工具和本地合同测试 |
| `.local/` | 本机配置、加密账号和服务器笔记，Git 忽略 |
| `.runs/` | 任务脚本、诊断材料和日志副本，Git 忽略 |

配置和任务目录始终相对 Skill 自身解析，从其它工作目录调用不会改变它们的位置。账号由保存时的 Windows 用户加密；换电脑或 Windows 账号后需重新填写。SSH 输出默认只返回给调用方，需要留档时再保存到 `.runs`。

## 参与维护

修改和验证方式见 [贡献指南](./CONTRIBUTING.md)，问题和建议可提交到 [Issues](https://github.com/CheshireMew/server-ops/issues)。

## 许可证

采用 **MPL-2.0**，范围与第三方依赖说明见 [LICENSING.md](./LICENSING.md)，完整文本见 [LICENSE](./LICENSE)。

# 参与维护

欢迎通过 [Issues](https://github.com/CheshireMew/server-ops/issues) 报告问题或讨论改进，通过 Pull Request 提交修改。问题描述请提供 Windows、Python 版本、调用方式、预期与实际结果；涉及日志时先移除账号、服务器地址、密码和 Token。

## 修改入口

| 文件 | 职责 |
| --- | --- |
| `SKILL.md` | 外部 Agent 的工作方式与授权边界 |
| `references/usage.md` | 本机配置、命令和结果合同 |
| `server-ops.ps1` | 从 Skill 自身目录加载配置并启动 Python |
| `scripts/server.py` | 账号窗口、Windows 加密、SSH 执行和 JSON 输出 |
| `scripts/guardrails.py` | SSH 连接前的命令检查 |
| `scripts/test_guardrails.py` | 本地命令检查与授权传递测试 |

改变用户入口、参数或行为时，同步更新用法文档及中、英、日三份 README。只有宿主适配发生变化时才修改 `agents/openai.yaml`。

## 本地验证

在仓库根目录使用 Python 3.10 或更新版本运行：

```powershell
python -B -m unittest discover -s scripts -p test_guardrails.py -v
```

这组测试检查命令分类、连接前拦截和授权传递，不连接真实服务器。SSH 或账号窗口的修改需要另行验证实际入口；在 PR 中写清已测范围和仍未验证的部分。真实服务器上的操作需要对应用户的具体授权。

`.local/` 和 `.runs/` 保留在本机，不提交配置、加密账号、服务器笔记、任务脚本或日志副本。示例使用 `prod`、`ssh.example.com` 等明确的示例值。

## 提交说明

说明修改解决了什么问题、最终行为和验证结果。新增依赖时写清用途；复用第三方内容时保留其许可证与来源。贡献按 [LICENSING.md](./LICENSING.md) 中的项目许可范围提供。

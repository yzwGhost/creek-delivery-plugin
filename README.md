# Creek Delivery

为 creek 系列项目编排多 Agent 需求交付。安装并启用后，在包含项目上下文的新聊天中调用 `$creek-delivery`，提供需求、原型与接口资料，或指定已有批次。

插件沿用已安装 Superpowers 7.0.1 的清单结构，通过 `.codex-plugin/plugin.json` 的 `skills` 字段声明入口目录。在插件目录执行 `python -B -m unittest discover -s tests` 可检查源码。

本机 Codex CLI 通过 `codex plugin marketplace add <本地市场目录>` 注册市场，随后通过 `codex plugin add creek-delivery@<市场名>` 安装市场已登记的插件。本会话的已加载技能目录未列出本插件。需要由包含此插件的市场安装并在新会话验证调用。

运行前检查 Agent 调度、云效连接、权限和 Ant Design 工具；不可用时记录阻塞及恢复条件。云效写入前展示完整清单并取得确认。

本机 Windows 可在插件目录使用 Codex 自带 Python 运行测试和配置检查：

```powershell
$deliveryPython = "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
& $deliveryPython -B -m unittest discover -s tests
& $deliveryPython -B scripts/workflow.py check
```

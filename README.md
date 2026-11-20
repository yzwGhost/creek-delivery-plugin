# Creek Delivery

为 creek 系列项目编排多 Agent 需求交付。安装并启用后，在包含项目上下文的新聊天中调用 `$creek-delivery`，提供需求、原型与接口资料，或指定已有批次。

插件沿用已安装 Superpowers 7.0.1 的清单结构，通过 `.codex-plugin/plugin.json` 的 `skills` 字段声明入口目录。在插件目录执行 `python -B -m unittest discover -s tests` 可检查源码。

本机 Codex CLI 通过 `codex plugin marketplace add <本地市场目录>` 注册市场，随后通过 `codex plugin add creek-delivery@<市场名>` 安装市场已登记的插件。本会话的已加载技能目录未列出本插件。需要由包含此插件的市场安装并在新会话验证调用。

本机提供 Agent 调度与交接工具。本会话未发现云效用例或缺陷工具，云效同步保持待连接。Ant Design CLI 已安装，默认 Node 14 解析其代码时失败，使用本机 Node 20.19.0 运行 CLI。

本机 Windows 可在插件目录使用 Codex 自带 Python 运行测试和配置检查：

```powershell
$deliveryPython = "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
& $deliveryPython -B -m unittest discover -s tests
& $deliveryPython -B scripts/workflow.py check
```

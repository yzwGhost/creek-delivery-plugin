# development

在 creek-web 按接口路径、HTTP 方法和业务名查找 service、类型、controller 与已有路由，核对参数、返回及错误响应；仅按已证实的服务契约补齐路由。未定位服务或契约不一致时记录 API ID 和待确认字段。前端依仓库 AGENTS.md 和 DESIGN.md，核对已有页面、组件及 Ant Design CLI 文档。按 Service → Store → 交互 → 展示分层，由 Service 独占请求客户端。依项目规范处理远程表格查询、变更反馈、状态标签和刷新。联调记录实际请求与脱敏响应，核对成功和失败路径。

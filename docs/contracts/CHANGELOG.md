# AetherVerse 契约变更日志

> 所有 `docs/contracts/` 下文件的变更记录

---

## 2026-03-19

### [NEW] db-schema.sql v1.0
- **变更**: 首次创建完整数据库 Schema DDL
- **内容**: 38 张表 + 22 个 PostgreSQL 枚举类型
- **覆盖模块**: 全部 13 个 MVP 模块（用户/房间/消息/智能体/创作/积分/通知/审核/风控/AI网关/管理/看板/外部Agent）+ 辅助表
- **影响**: Agent A (Marcus) — 需按此建 SQLAlchemy 模型; Agent B (Minerva) — 参考智能体/AI网关相关表; Agent C (Apollo) — 了解数据结构
- **适配状态**: 待 Phase 0 完成后下发

### [NEW] db-er.md v1.0
- **变更**: 首次创建 ER 图（Mermaid 格式）
- **内容**: 全量实体关系图 + 表清单 + 6 项关键设计决策说明
- **影响**: 全部 Agent
- **适配状态**: 待 Phase 0 完成后下发

### [NEW] api-schema.yaml v1.0
- **变更**: 用户端 REST API Schema（OpenAPI 3.0）
- **内容**: 认证/用户/房间/消息/智能体/话题/积分/通知/举报/上传/外部Agent网关 ~50 端点
- **影响**: Agent A (实现), Agent C (调用)
- **适配状态**: 待 Phase 0 完成后下发

### [NEW] admin-api-schema.yaml v1.0
- **变更**: 管理后台 REST API Schema
- **内容**: M-01~M-60 全覆盖 ~60 端点，含 RBAC 权限标注
- **影响**: Agent A (实现)
- **适配状态**: 待 Phase 0 完成后下发

### [NEW] websocket-protocol.md v1.0
- **变更**: WebSocket 协议规范
- **内容**: 12 个事件类型 + 心跳/重连机制 + 限频规则 + 错误码
- **影响**: Agent A (服务端), Agent C (客户端)
- **适配状态**: 待 Phase 0 完成后下发

### [NEW] ai-engine-api.yaml v1.0
- **变更**: AI 引擎内部 API 规范
- **内容**: server ↔ ai-engine HTTP 端点 + RabbitMQ 异步消息队列约定
- **影响**: Agent A (调用方), Agent B (实现方)
- **适配状态**: 待 Phase 0 完成后下发

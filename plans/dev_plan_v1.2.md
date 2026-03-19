# AetherVerse 多 Agent 并行开发计划

> **版本**: v1.2
> **日期**: 2026-03-19
> **角色**: 恺撒（项目经理 / 架构师 / QA，不写产品代码）
> **目标**: 定义多 Agent 工作隔离、契约管理和协作流程

---

## 一、角色架构

恺撒（PM / 架构师 / QA）不写产品代码，负责：
- Phase 0 契约定义（架构设计）
- 代码 Review + 质量把关
- shared/ 共享包维护
- 集成测试 + 联调主导
- 契约变更协调
- DevOps / 部署

| Agent | 负责模块 | 技术栈 | 产出目录 |
|-------|---------|--------|---------|
| **Agent A (Marcus)** | 后端全栈（核心 + 安全 + Agent 网关 + SQLAdmin） | Python FastAPI + PostgreSQL + Redis | server/ |
| **Agent B (Minerva)** | AI 引擎 + 智能体编排 | Python FastAPI + LLM SDK + RabbitMQ | ai-engine/ |
| **Agent C (Apollo)** | Flutter 用户端 | Flutter + Dart | app/ |

### 1.1 详细职责

**恺撒 — PM / 架构师 / QA（不写产品代码）:**
- Phase 0 架构设计（DB Schema / API Schema / 协议定义）
- shared/ 共享包维护（Pydantic schemas / 枚举 / 错误码）
- docs/contracts/ 契约变更管理
- 所有 Agent 的代码 Review + PR 合并
- 集成测试 + 联调主导（Week 5 / Week 10）
- DevOps（Docker Compose / CI/CD / 部署脚本）
- 协调各 Agent 工作，确保目录隔离、避免冲突

**Agent A — 后端全栈:**
- 用户系统（注册/登录/DID/个人资料）
- 房间系统（CRUD/成员管理/消息）
- 聊天系统（WebSocket/私聊/消息投递/历史消息）
- 积分与计费（充值/消耗/事务模型/对账）
- 通知系统（站内消息）
- 安全审核（三层审核管线/AIGC 标识/举报处置/敏感词库）
- Agent 网关（外部 Agent 接入/REST API 鉴权/JWT 认证/行为沙箱/频率限制）
- 管理后台（SQLAdmin + 审核工作台/Go-No-Go 看板自定义页面）

**Agent B — AI 引擎:**
- AI 模型路由 + 智能体编排（L1/L2）
- 记忆系统 + 人格一致性 + 系统智能体（5 个）
- 图片生成/理解 + AI 行为防控
- 开发者 SDK + 文档

**Agent C — Flutter 用户端（不做管理后台）:**
- 用户端全部页面 + UI 组件库
- 状态管理 + 网络层 + WebSocket 客户端

> 管理后台: Phase 1 用 SQLAdmin（Agent A 做），Phase 2 再上 Vue 3 + Element Plus。
> **外部 Agent 接入方案（2026-03-19 简化决策）**: 废弃 AAP 自定义协议，核心用 REST API + JWT 认证。Phase 1B 编写「Agent 激活指令」（给 LLM 看的自然语言操作手册 + curl 示例）。MCP Server 延后到 Phase 2。Phase 0 在 API 设计时预留 /api/v1/agent/* 命名空间。


---

## 二、目录结构与隔离策略

### 2.1 目录规划

- docs/contracts/ — 共享契约（Phase 0 产出，只读）
  - api-schema.yaml, db-schema.sql, db-er.md
  - shared-types.dart, websocket-protocol.md
  - ai-engine-api.yaml, CHANGELOG.md
- shared/ — 共享 Python 包（恺撒维护，Agent A/B 只读引用）
  - schemas/, constants/, exceptions/, utils/, pyproject.toml
- server/ — Agent A 领地（Python FastAPI）
  - app/api/, app/ws/, app/services/, app/models/, app/core/, app/gateway/
  - migrations/, tests/, pyproject.toml
- ai-engine/ — Agent B 领地（Python FastAPI）
  - app/router/, app/orchestrator/, app/memory/, app/persona/
  - app/safety/, app/aap/, app/sdk/, prompts/, tests/, pyproject.toml
- app/ — Agent C 领地（Flutter）
  - lib/core/, lib/models/, lib/services/, lib/providers/
  - lib/screens/, lib/widgets/, assets/, pubspec.yaml
- infra/ — 恺撒负责（DevOps）
  - docker-compose.yml, k8s/, terraform/

### 2.2 隔离原则

| 规则 | 说明 |
|------|------|
| 目录隔离 | 每个 Agent 只能修改自己的目录（server/, ai-engine/, app/） |
| 只读共享 | docs/contracts/ 和 shared/ 是只读共享区，任何修改必须通过恺撒协调 |
| 接口通信 | Agent 之间通过 API 契约通信，不直接调用对方代码 |
| 独立构建 | 每个模块有独立的 pyproject.toml 或 pubspec.yaml |
| Git 分支 | 每个 Agent 在功能分支开发，PR 合并由恺撒审核 |

### 2.3 Git 分支策略

- main: 受保护，只通过 PR 合并
- develop: 开发主线
  - feature/agent-a/xxx: Agent A 功能分支
  - feature/agent-b/xxx: Agent B 功能分支
  - feature/agent-c/xxx: Agent C 功能分支
- release/v1.0: 发布分支
- docs/contracts/ 和 shared/ 的修改只能由恺撒在 develop 上直接提交

---

## 三、契约变更管理

发现需要修改契约 -> 开发者告知恺撒 -> 恺撒评估影响范围 -> 恺撒修改 docs/contracts/ 并更新 CHANGELOG.md -> 所有 Agent 拉取最新契约 -> 集成测试验证

CHANGELOG.md 格式:
- 日期 + 变更描述
- 影响范围（哪些 Agent 需要适配）
- 适配状态跟踪

---

## 四、Phase 0 — 契约与架构定义（1-2 周）

执行者: 恺撒（单 Agent 串行）
目标: 在开启多 Agent 并行前把所有契约定好

| 序号 | 产出 | 文件 |
|------|-----|------|
| 1 | API Schema | docs/contracts/api-schema.yaml |
| 2 | DB Schema | docs/contracts/db-schema.sql |
| 3 | ER 图 | docs/contracts/db-er.md |
| 4 | WebSocket 协议 | docs/contracts/websocket-protocol.md |
| 5 | AI 引擎 API | docs/contracts/ai-engine-api.yaml |
| 6 | ~~AAP 协议~~ 已废弃 |  |
| 7 | 共享类型 | shared/ + shared-types.dart |
| 8 | 变更日志 | docs/contracts/CHANGELOG.md |
| 9 | 项目脚手架 | shared/ + server/ + ai-engine/ + app/ |
| 10 | 本地环境 | infra/docker-compose.yml |
| 11 | CI/CD | .github/workflows/ |

执行顺序:
- Week 1: Day 1-2 DB Schema + Day 3-4 API Schema + Day 5 协议
- Week 2: Day 1 共享类型 + Day 2 脚手架 + Day 3 Docker/CI + Day 4-5 自检+启动指令

---

## 五、各 Agent 启动指令

### 5.1 Marcus (Agent A) 启动指令 — 后端全栈

你是 AetherVerse 项目的后端全栈开发者，代号 Agent A。
负责: 用户系统、房间、聊天、积分、通知、安全审核、Agent 网关、管理后台(SQLAdmin)

工作规则:
1. 只修改 server/ 目录
2. docs/contracts/ 和 shared/ 只读，需要改告知恺撒
3. 按 api-schema.yaml 实现 REST API
4. 按 websocket-protocol.md 实现 WebSocket
5. 按 db-schema.sql 创建 SQLAlchemy 模型
6. 从 shared/ 包 import Pydantic schemas，不重复定义类型
7. 强制 async: 禁止同步阻塞调用
8. Git 分支: feature/agent-a/xxx

必读文件: api-schema.yaml, db-schema.sql, websocket-protocol.md, Phase1_MVP需求文档.md, coding_conventions.md

排期:
- Week 3-4: 用户注册/登录 + 房间 CRUD + WebSocket 消息投递
- Week 5-6: 积分系统 + 私聊 + 通知 + 数据库迁移
- Week 5 末: 中间集成验证
- Week 7-9: 三层审核 + AIGC 标识 + Agent 网关 + SQLAdmin

### 5.2 Minerva (Agent B) 启动指令 — AI 引擎

你是 AetherVerse 项目的 AI 引擎开发者，代号 Agent B。
负责: AI 模型路由、智能体编排、记忆系统、人格一致性、系统 AI(5个)、AI 行为防控、图片能力、SDK

工作规则:
1. 只修改 ai-engine/ 目录
2. docs/contracts/ 和 shared/ 只读
3. 调用后端服务通过 api-schema.yaml
4. 接收后端请求通过 ai-engine-api.yaml
5. Python FastAPI，直接 import shared 包
6. 强制 async
7. Git 分支: feature/agent-b/xxx

必读文件: ai-engine-api.yaml, api-schema.yaml, db-schema.sql, Phase1_MVP需求文档.md 第3章, Phase1落地方案.md 第2.5章, coding_conventions.md

排期:
- Week 3-4: LLM 路由框架 + Prompt 模板 + 基础对话
- Week 5-6: 分身创建、发言调度、记忆系统
- Week 5 末: 中间集成验证
- Week 7-9: 系统 AI(5个) + AI 行为防控 + 图片能力 + SDK

### 5.3 Apollo (Agent C) 启动指令 — Flutter 用户端

你是 AetherVerse 项目的 Flutter 用户端开发者，代号 Agent C。
负责: 用户端 App(iOS/Android)、UI 组件库、状态管理 + 网络层
注意: 管理后台不在你的职责范围内（Agent A 用 SQLAdmin 处理）

工作规则:
1. 只修改 app/ 目录
2. docs/contracts/ 只读
3. 按 api-schema.yaml 调用后端 API
4. 按 websocket-protocol.md 实现消息通信
5. 按 shared-types.dart 使用共享类型
6. Week 3-4 设计稿未到，先做框架层
7. Week 5 起设计稿到位，开始 UI 还原
8. Git 分支: feature/agent-c/xxx

必读文件: api-schema.yaml, websocket-protocol.md, shared-types.dart, Phase1_MVP需求文档.md(模块1-7), prototype_mobile.html, coding_conventions.md

排期:
- Week 3-4: 路由框架 + 状态管理 + 网络层 + WebSocket + 主题系统
- Week 5: 中间集成验证（登录 + 房间列表 + 消息）
- Week 5-6: 按设计稿还原核心页面
- Week 7-9: 分身/积分/个人中心/设置（100% 专注用户体验）

### 5.4 恺撒自身工作

恺撒负责（不写产品代码）:
- Phase 0: 全部契约定义
- shared/ 共享包维护
- docs/contracts/ 变更管理
- 代码 Review + PR 合并
- 集成测试 + 联调
- DevOps（infra/ 部署）
- 协调各 Agent，确保隔离、避免冲突

---

## 六、集成检查点

### 6.1 Week 5 末 — 中间集成验证

| 验证项 | Agent A | Agent B | Agent C |
|--------|---------|---------|---------|
| 用户登录 | 注册/登录 API 可用 | — | 登录页面调通 |
| 房间列表 | 房间 CRUD API 可用 | — | 房间列表展示 |
| 基础消息 | WebSocket 消息投递 | LLM 基础对话可用 | 聊天界面收发消息 |
| AI 发言 | 消息总线联通 | 触发一次 AI 回复 | 展示 AI 消息 + 标识 |
| 积分 | 积分查询 API | — | 余额展示 |

验证方式: 恺撒在本地 Docker Compose 环境中启动三个服务，逐项验证

### 6.2 Week 10 — 全量集成测试

全部 13 个模块的联调。

---

## 七、沟通机制

### 7.1 日常协作

| 场景 | 做法 |
|------|------|
| Agent 需要修改契约 | 在对话中告知恺撒 |
| 恺撒修改了契约 | 更新 CHANGELOG.md，提醒各 Agent |
| 集成验证发现问题 | 恺撒提供错误日志/截图给对应 Agent |
| 紧急冲突 | 恺撒暂停所有 Agent，统一修复后再恢复 |

### 7.2 创始人（智远）的角色

| 事项 | 智远的参与 |
|------|----------|
| 创建 Agent 对话 | 开 3 个新的 AI Agent 对话窗口（A、B、C） |
| 下发启动指令 | 把启动指令分别复制进各 Agent 对话 |
| 契约变更通知 | 恺撒告知智远 -> 智远去对应对话转达 |
| 集成验证配合 | Week 5/10 协调各 Agent 输出 |
| 外部事务 | UI 设计外包、App Store 账号、云服务器 |
| 真机调试 | Agent C 的 Flutter 代码需要智远真机测试 |

---

## 八、Phase 0 立即行动清单

1. [x] 制定多 Agent 并行开发计划（本文档）
2. [x] 设计数据库 Schema（所有表的 DDL）— 38 表 + 22 枚举
3. [x] 绘制 ER 图（Mermaid 格式）
4. [x] 定义 REST API Schema（OpenAPI 3.0）— 用户端 ~50 + 管理后台 ~60 端点
5. [x] 定义 WebSocket 协议— 12 个事件 + 心跳/重连/限频
6. [x] 定义 AI 引擎内部 API— HTTP + RabbitMQ 异步消息
7. [x] ~~定义 AAP 外部 Agent 协议~~ 已废弃，改为 REST API + Agent 激活指令（Phase 1B 编写）
8. [x] 生成共享类型定义文件— Python shared/ + Flutter shared-types.dart
9. [x] 搭建项目脚手架— shared/ + server/ + ai-engine/ + infra/
10. [x] Docker Compose 本地开发环境— PG16 + Redis7 + RabbitMQ + MinIO
11. [x] CI/CD 基础流水线— GitHub Actions (lint + test)
12. [x] 输出 Agent A/B/C 最终启动指令— docs/agent-instructions/

Phase 0 完成标志: 所有契约文件就位 + 脚手架可构建 + 本地环境可启动

Phase 0 完成后，智远创建 Agent A、Agent B、Agent C 对话窗口，粘贴启动指令，正式开工。

---

## 九、关键风险与应对

| 风险 | 影响 | 应对 |
|------|------|------|
| 契约定义不完善 | 多 Agent 返工 | Phase 0 充分设计，覆盖 MVP 需求文档所有接口 |
| Agent 理解偏差 | 集成失败 | 启动指令详尽 + Week 5 中间验证及早发现 |
| 外部 Agent 接入增加安全面 | 安全风险 | REST API + JWT 鉴权 + 行为沙箱，Phase 1B 仅邀请制 |
| 设计稿延迟 | Agent C 阻塞 | Week 3-4 先做框架层，不依赖设计稿 |
| 多 Agent 协调开销 | 响应慢 | 智远转达 + 契约先行减少沟通需求 |

---

> 下一步: 恺撒立即开始 Phase 0 第一项 — 数据库 Schema 设计。


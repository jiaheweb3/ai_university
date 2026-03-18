# AetherVerse 多 Agent 并行开发计划

> **版本**：v1.0  
> **日期**：2026-03-18  
> **角色**：恺撒（项目经理 + 主力开发 Agent）  
> **目标**：规划 Phase 0 → Phase 1 → Phase 2 的开发节奏，定义多 Agent 工作隔离、契约管理和协作流程

---

## 一、Agent 分工定义

### 1.1 Agent 角色

| Agent | 负责模块 | 技术栈 | 产出目录 |
|-------|---------|--------|---------|
| **Agent A（恺撒）** | 后端核心服务 + 安全审核 + Agent 网关 + DevOps | Python FastAPI + PostgreSQL + Redis | `server/` |
| **Agent B** | AI 引擎 + 智能体编排 + 外部 Agent 协议(AAP) | Python FastAPI + LLM SDK + RabbitMQ | `ai-engine/` |
| **Agent C** | Flutter 前端（用户端 + 管理后台） | Flutter + Dart | `app/` |

### 1.2 角色详细职责

**Agent A — 后端核心（恺撒本人）：**
- 用户系统（注册/登录/DID/个人资料）
- 房间系统（CRUD/成员管理/消息）
- 聊天系统（WebSocket/私聊/消息投递/历史消息）
- 积分与计费（充值/消耗/事务模型/对账）
- 通知系统（站内消息）
- 安全审核（三层审核管线/AIGC 标识/举报处置/敏感词库）
- `shared/` 共享包维护（Pydantic schemas/枚举/错误码）
- Agent 网关（外部 Agent 接入/网关鉴权/行为沙箱/频率限制）
- DevOps（CI/CD/部署脚本/监控）
- 管理后台 API（用户管理/房间管理/话题管理/审核台/数据看板）

**Agent B — AI 引擎：**
- AI 模型路由（多供应商管理/降级策略/健康检查）
- 智能体编排（L1 发言调度/触发策略/多智能体冲突处理）
- 智能体 L2 创作（图片生成/作品审核队列）
- 记忆系统（上下文管理/记忆摘要/记忆过期）
- 人格一致性（Prompt 模板/few-shot/角色设定注入）
- 系统智能体（5 个预设 AI 的人格配置/暖场策略/话题发起）
- 图片生成/理解能力
- AI 行为防控（冒充真人检测/社工攻击检测/骚扰限频）
- AAP 协议实现（外部 Agent 消息收发/协议转换）
- 开发者 SDK + 文档

**Agent C — Flutter 前端：**
- 用户端全部页面（登录/注册/首页/房间/聊天/个人中心/积分/引导流）
- 管理后台全部页面（Web 端，Flutter Web 或独立 React/Vue）
- UI 组件库（基于设计稿）
- 状态管理（Riverpod/Bloc）
- 网络层（API 封装/WebSocket 客户端/错误处理）
- 本地存储/缓存

---

## 二、目录结构与隔离策略

### 2.1 目录规划

```
ai_university/
├── docs/                        # 文档（已有）
│   ├── contracts/               # 🔑 共享契约（Phase 0 产出）
│   │   ├── api-schema.yaml      #   OpenAPI 3.0 接口定义
│   │   ├── db-schema.sql        #   数据库 Schema（DDL）
│   │   ├── db-er.md             #   ER 图（Mermaid）
│   │   ├── shared-types.ts      #   前后端共享类型定义
│   │   ├── shared-types.dart    #   Flutter 端类型定义
│   │   ├── websocket-protocol.md#   WebSocket 消息协议
│   │   ├── ai-engine-api.yaml   #   AI 引擎内部 API
│   │   ├── agent-protocol.yaml  #   AAP 外部 Agent 协议
│   │   └── CHANGELOG.md         #   契约变更日志
│   └── ...
├── plans/                       # 计划文档（已有）
├── context_memory/              # 上下文记忆（已有）
│
├── shared/                      # ⭐ 共享 Python 包（Agent A/B 共用）
│   ├── schemas/                 #   Pydantic 模型（API 请求/响应/DB 模型）
│   ├── constants/               #   枚举、错误码、配置常量
│   ├── exceptions/              #   自定义异常类
│   ├── utils/                   #   公共工具函数
│   └── pyproject.toml           #   包定义
│
├── server/                      # ⬅ Agent A 领地（Python FastAPI）
│   ├── app/
│   │   ├── api/                 #   REST 路由（用户/房间/积分/审核/管理后台）
│   │   ├── ws/                  #   WebSocket 处理
│   │   ├── services/            #   业务逻辑层
│   │   ├── models/              #   SQLAlchemy ORM 模型
│   │   ├── core/                #   配置/安全/依赖注入
│   │   └── gateway/             #   Agent 网关
│   ├── migrations/              #   Alembic 数据库迁移
│   ├── tests/                   #   pytest 测试
│   └── pyproject.toml
│
├── ai-engine/                   # ⬅ Agent B 领地（Python FastAPI）
│   ├── app/
│   │   ├── router/              #   模型路由（多供应商/降级）
│   │   ├── orchestrator/        #   编排调度（L1 发言/L2 创作）
│   │   ├── memory/              #   记忆管理
│   │   ├── persona/             #   人格管理
│   │   ├── safety/              #   AI 行为防控
│   │   ├── aap/                 #   AAP 协议实现
│   │   └── sdk/                 #   开发者 SDK
│   ├── prompts/                 #   Prompt 模板
│   ├── tests/                   #   pytest 测试
│   └── pyproject.toml
│
├── app/                         # ⬅ Agent C 领地
│   ├── lib/
│   │   ├── core/                #   核心（网络/主题/路由/常量）
│   │   ├── models/              #   数据模型
│   │   ├── services/            #   API 服务层
│   │   ├── providers/           #   状态管理
│   │   ├── screens/             #   页面
│   │   ├── widgets/             #   组件
│   │   └── main.dart
│   ├── assets/                  #   资源
│   └── pubspec.yaml
│
├── admin-web/                   # ⬅ Agent C 领地（管理后台 Web）
│   └── ...                      #   技术选型待定（Flutter Web / Vue）
│
└── infra/                       # ⬅ Agent A 负责
    ├── docker-compose.yml       #   本地开发环境
    ├── k8s/                     #   K8s 配置（可选）
    └── terraform/               #   云资源配置（可选）
```

### 2.2 隔离原则

| 规则 | 说明 |
|------|------|
| **目录隔离** | 每个 Agent 只能修改自己的目录（`server/`、`ai-engine/`、`app/`） |
| **只读共享** | `docs/contracts/` 是只读共享区，任何修改必须通过恺撒（Agent A）协调 |
| **接口通信** | Agent 之间通过 API 契约通信，不直接调用对方代码 |
| **独立构建** | 每个模块有独立的 `go.mod` 或 `pubspec.yaml`，独立编译运行 |
| **Git 分支** | 每个 Agent 在自己的功能分支开发，PR 合并由恺撒审核 |

### 2.3 Git 分支策略

```
main                              # 受保护，只通过 PR 合并
├── develop                       # 开发主线
│   ├── feature/agent-a/xxx       # Agent A 功能分支
│   ├── feature/agent-b/xxx       # Agent B 功能分支
│   └── feature/agent-c/xxx       # Agent C 功能分支
└── release/v1.0                  # 发布分支
```

**规则：**
- 每个 Agent 从 `develop` 拉分支，命名 `feature/agent-{a|b|c}/{功能名}`
- 功能完成后 PR 到 `develop`，恺撒 review 合并
- 每周末从 `develop` 合入 `main` 一次
- `docs/contracts/` 的修改只能在 `develop` 上直接提交（恺撒操作）

---

## 三、契约变更管理

### 3.1 变更流程

```
发现需要修改契约
     ↓
开发者告知恺撒（通过 context_memory 或对话）
     ↓
恺撒评估影响范围，通知所有相关 Agent
     ↓
恺撒修改 docs/contracts/ 并更新 CHANGELOG.md
     ↓
所有 Agent 拉取最新契约，同步修改各自代码
     ↓
集成测试验证
```

### 3.2 CHANGELOG.md 格式

```markdown
## [日期] - 变更描述

### Changed
- `POST /api/v1/rooms` 新增 `max_members` 字段 (int, optional, default: 200)

### Impact
- Agent A: 需更新 room 创建接口
- Agent C: 需更新房间创建表单
- Agent B: 无影响

### Status
- [x] Agent A 已适配
- [ ] Agent C 待适配
```

---

## 四、Phase 0 — 契约与架构定义（1-2 周）

> **执行者**：恺撒（单 Agent 串行）  
> **目标**：在开启多 Agent 并行前，把所有"契约"定好

### 4.1 具体产出清单

| 序号 | 产出 | 文件 | 说明 |
|------|-----|------|------|
| 1 | API Schema | `docs/contracts/api-schema.yaml` | OpenAPI 3.0 定义所有 REST 接口（用户/房间/聊天/积分/审核/管理后台） |
| 2 | DB Schema | `docs/contracts/db-schema.sql` | 全部数据表 DDL（用户/房间/消息/智能体/积分/审核/通知等） |
| 3 | ER 图 | `docs/contracts/db-er.md` | Mermaid 格式的实体关系图 |
| 4 | WebSocket 协议 | `docs/contracts/websocket-protocol.md` | 消息格式、事件类型、心跳、重连策略 |
| 5 | AI 引擎 API | `docs/contracts/ai-engine-api.yaml` | 后端调 AI 引擎的内部接口 |
| 6 | AAP 协议 | `docs/contracts/agent-protocol.yaml` | 外部 Agent 接入协议完整定义 |
| 7 | 共享类型 | `docs/contracts/shared-types.ts` + `.dart` | 前后端共享的 enum/DTO/Error Code |
| 8 | 变更日志 | `docs/contracts/CHANGELOG.md` | 契约变更记录 |
| 9 | 项目脚手架 | `server/`、`ai-engine/`、`app/` | 各模块初始化（空壳 + 构建配置） |
| 10 | 本地 Dev 环境 | `infra/docker-compose.yml` | PostgreSQL + Redis + MinIO + RabbitMQ |
| 11 | CI/CD | `.github/workflows/` | lint + build + test 基础流水线 |

### 4.2 Phase 0 执行顺序

```
Week 1:
├── Day 1-2: DB Schema（所有表的 DDL + ER 图）
├── Day 3-4: API Schema（所有 REST 接口的 OpenAPI 定义）
├── Day 5:   WebSocket 协议 + AI 引擎内部 API + AAP 协议
│
Week 2:
├── Day 1:   共享类型定义（TS + Dart）
├── Day 2:   项目脚手架搭建（server/、ai-engine/、app/ 初始化）
├── Day 3:   Docker Compose + CI/CD 基础流水线
├── Day 4-5: 自检 + 文档整理 + 输出各 Agent 启动指令
```

---

## 五、各 Agent 启动指令（Phase 1 开工时下发）

> 以下是开启新 Agent 对话窗口时，给每个 Agent 的完整上下文指令。

### 5.1 Agent B 启动指令

```markdown
# Agent B 启动指令 — AI 引擎

## 你是谁
你是 AetherVerse 项目的 AI 引擎开发者，代号 Agent B。

## 项目概述
AetherVerse 是一个 AI 分身社交平台。你负责 AI 引擎模块，包括：
- AI 模型路由（多供应商管理/降级策略）
- 智能体编排（L1 发言调度/L2 创作任务）
- 记忆系统（上下文管理/摘要/过期）
- 人格一致性管理
- 系统预设 AI（5 个暖场角色）
- AI 行为防控（冒充真人检测/社工攻击检测）
- 图片生成/理解
- AAP 协议实现（外部 Agent 消息收发/协议转换）
- 开发者 SDK + 文档

## 工作规则
1. **只修改 `ai-engine/` 目录下的文件**
2. **契约文件在 `docs/contracts/`，只读**，需要修改时告知恺撒
3. 调用后端服务通过 `docs/contracts/api-schema.yaml` 中定义的接口
4. 接收后端请求通过 `docs/contracts/ai-engine-api.yaml` 中定义的接口
5. 技术栈：Python FastAPI（与后端一致），直接 import shared 包
6. Git 分支：从 develop 拉 `feature/agent-b/xxx`
7. 定期读取 `docs/contracts/CHANGELOG.md` 检查契约变更

## 必读文件（开工前先读）
- `docs/contracts/ai-engine-api.yaml` — 你的接口定义
- `docs/contracts/api-schema.yaml` — 后端 API 定义（你要调用的接口）
- `docs/contracts/agent-protocol.yaml` — AAP 协议定义
- `docs/contracts/db-schema.sql` — 理解数据结构
- `docs/Phase1_MVP_需求文档.md` §3（智能体系统）
- `plans/Phase1_落地方案.md` §2.5（外部 Agent 接入）

## 排期
- Week 3-4: LLM 路由框架 + Prompt 模板 + 基础对话能力
- Week 5-6: 分身创建、发言调度、记忆系统
- Week 5 末: ⚡ 中间集成验证（与 Agent A/C 对接）
- Week 7-9: 系统预设 AI（5 个）+ AI 行为防控 + 图片能力 + AAP 协议 + SDK
```

### 5.2 Agent C 启动指令

```markdown
# Agent C 启动指令 — Flutter 前端

## 你是谁
你是 AetherVerse 项目的 Flutter 前端开发者，代号 Agent C。

## 项目概述
AetherVerse 是一个 AI 分身社交平台。你负责全部前端开发：
- 用户端 Flutter App（iOS/Android）
- 管理后台 Web 端
- UI 组件库
- 状态管理 + 网络层 + 本地存储

## 工作规则
1. **只修改 `app/` 和 `admin-web/` 目录下的文件**
2. **契约文件在 `docs/contracts/`，只读**，需要修改时告知恺撒
3. 按 `docs/contracts/api-schema.yaml` 调用后端 API
4. 按 `docs/contracts/websocket-protocol.md` 实现消息通信
5. 按 `docs/contracts/shared-types.dart` 使用共享类型
6. **Week 3-4 设计稿未到**，先做框架层（路由/状态管理/网络层/主题）
7. **Week 5 起设计稿到位**，开始 UI 还原
8. Git 分支：从 develop 拉 `feature/agent-c/xxx`
9. 定期读取 `docs/contracts/CHANGELOG.md` 检查契约变更

## 必读文件（开工前先读）
- `docs/contracts/api-schema.yaml` — 你要调用的所有 API
- `docs/contracts/websocket-protocol.md` — WebSocket 消息协议
- `docs/contracts/shared-types.dart` — 共享类型定义
- `docs/Phase1_MVP_需求文档.md` — 全部功能需求
- `docs/prototype_mobile.html` — 移动端原型
- `docs/prototype_admin.html` — 管理后台原型

## 排期
- Week 3-4: 路由框架 + 状态管理 + 网络层 + WebSocket 客户端 + 主题系统
- Week 5: ⚡ 中间集成验证（登录 + 房间列表 + 消息基本流）
- Week 5-6: 按设计稿还原核心页面（登录/注册/聊天/房间）
- Week 7-9: 分身/积分/个人中心/管理后台/设置页面
```

### 5.3 Agent A（恺撒）自身工作

```
我（恺撒）负责：
- Phase 0 全部契约定义
- server/ 全部后端代码
- infra/ 部署相关
- 所有 Agent 的 PR review
- 契约变更协调
- 集成验证主导
```

---

## 六、集成检查点

### 6.1 Week 5 末 — 中间集成验证

| 验证项 | Agent A 侧 | Agent B 侧 | Agent C 侧 |
|--------|-----------|-----------|-----------|
| 用户登录 | 注册/登录 API 可用 | — | 登录页面调通 |
| 房间列表 | 房间 CRUD API 可用 | — | 房间列表页面展示 |
| 基础消息 | WebSocket 消息投递 | LLM 基础对话可用 | 聊天界面收发消息 |
| AI 发言 | 消息总线联通 | 触发一次 AI 回复 | 展示 AI 消息 + 标识 |
| 积分 | 积分查询 API | — | 余额展示 |

**验证方式**：恺撒在本地 Docker Compose 环境中启动三个服务，逐项验证

### 6.2 Week 10 — 全量集成测试

全部 13 个模块的联调。

---

## 七、沟通机制

### 7.1 日常协作

| 场景 | 做法 |
|------|------|
| Agent B/C 发现需要修改 API | 在对话中@恺撒，描述需要的变更 |
| 恺撒修改了契约 | 更新 `CHANGELOG.md`，在 Agent B/C 对话开头提醒"请拉取最新契约" |
| 集成验证发现问题 | 恺撒在对应 Agent 对话中提供错误日志/截图 |
| 紧急冲突 | 恺撒暂停所有 Agent，统一修复后再恢复 |

### 7.2 创始人（智远）的角色

| 事项 | 智远的参与 |
|------|----------|
| **创建 Agent 对话** | 开 2 个新的 AI Agent 对话窗口（Agent B 和 Agent C） |
| **下发启动指令** | 把上面的启动指令复制到各 Agent 对话中 |
| **契约变更通知** | 恺撒告知智远"请通知 Agent B/C 拉取最新契约"→ 智远去对应对话转达 |
| **集成验证配合** | Week 5 / Week 10 的集成验证需要智远协调 Agent 输出 |
| **外部事务** | UI 设计外包对接、App Store 开发者账号、云服务器开通 |
| **真机调试** | Agent C 产出的 Flutter 代码需要智远在真机上测试 |

---

## 八、Phase 0 立即行动清单

恺撒（我）马上开始 Phase 0，按以下顺序执行：

1. ✅ ~~制定多 Agent 并行开发计划~~（本文档）
2. ⬜ 设计数据库 Schema（所有表的 DDL）
3. ⬜ 绘制 ER 图
4. ⬜ 定义 REST API Schema（OpenAPI 3.0）
5. ⬜ 定义 WebSocket 协议
6. ⬜ 定义 AI 引擎内部 API
7. ⬜ 定义 AAP 外部 Agent 协议
8. ⬜ 生成共享类型定义文件
9. ⬜ 搭建项目脚手架（server/ + ai-engine/ + app/ 初始化）
10. ⬜ Docker Compose 本地开发环境
11. ⬜ CI/CD 基础流水线
12. ⬜ 输出 Agent B/C 最终启动指令

**Phase 0 完成标志**：所有契约文件就位 + 脚手架可构建 + 本地环境可启动

Phase 0 完成后，智远创建 Agent B 和 Agent C 对话窗口，粘贴启动指令，正式开工。

---

## 九、关键风险与应对

| 风险 | 影响 | 应对 |
|------|------|------|
| 契约定义不完善，后期频繁变更 | 多 Agent 返工 | Phase 0 充分设计，覆盖 MVP 需求文档所有接口 |
| Agent B/C 理解偏差 | 集成失败 | 启动指令详尽 + Week 5 中间验证及早发现 |
| 外部 Agent 接入增加安全面 | 安全风险 | Agent 网关统一管控，Phase 1 仅邀请制 |
| 设计稿延迟 | Agent C 阻塞 | Week 3-4 先做框架层，不依赖设计稿 |
| 单人协调多 Agent 沟通效率 | 响应慢 | 智远转达 + 契约先行减少沟通需求 |

---

> **下一步**：智远确认此计划后，恺撒立即开始 Phase 0 第一项：数据库 Schema 设计。

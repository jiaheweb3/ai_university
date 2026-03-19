# 编码规范

> 项目：AetherVerse（AI × 元宇宙社交平台）
> 更新时间：2026-03-18

## 技术栈

| 层 | 选型 | 版本 |
|---|---|---|
| **后端** | Python + FastAPI | Python 3.12+, FastAPI 0.110+ |
| **数据库** | PostgreSQL + Redis | PG 16+, Redis 7+ |
| **消息队列** | RabbitMQ | 3.13+ |
| **对象存储** | MinIO（开发）/ 云 OSS（生产） | — |
| **前端** | Flutter + Dart | Flutter 3.19+, Dart 3.3+ |
| **AI 模型** | 国产优先（DeepSeek/通义千问） | API 调用 |

## ⛔ Async 强制规范（硬性要求）

> **违反此规范 = 线上故障级别。** 所有 Agent 必须严格遵守。

FastAPI 基于 asyncio 事件循环，**任何同步阻塞调用都会卡死整个服务**。

| 场景 | ✅ 正确做法 | ❌ 禁止使用 |
|------|-----------|-----------|
| HTTP 调用（LLM API 等） | `httpx.AsyncClient` | `requests`（同步） |
| 数据库查询 | `asyncpg` / `SQLAlchemy async` | `psycopg2`（同步） |
| 文件 IO | `aiofiles` | `open()`（同步） |
| Redis | `redis.asyncio` | `redis`（同步客户端） |
| 延时/定时 | `asyncio.sleep()` | `time.sleep()` |
| 子进程 | `asyncio.create_subprocess_exec` | `subprocess.run()` |
| 不可避免的同步库 | `run_in_executor()` 包装 | 直接调用 |

**检查方法**：所有 `def` 路由函数必须改为 `async def`，除非明确标注为同步端点（FastAPI 会自动线程池处理 `def`，但不推荐）。

## Python 编码规范

### 类型标注
- 所有函数必须有完整的类型标注（参数 + 返回值）
- 使用 Pydantic BaseModel 定义所有 API 请求/响应模型
- 启用 mypy strict mode 检查

### 项目结构
- `shared/` — 共享包（Pydantic schemas、枚举、错误码、工具函数）
- `server/` — 后端核心（Agent A 领地）
- `ai-engine/` — AI 引擎（Agent B 领地）
- `app/` — Flutter 前端（Agent C 领地）
- **每个 Agent 只修改自己的目录**

### 共享包引用
```toml
# server/pyproject.toml 和 ai-engine/pyproject.toml
[project]
dependencies = [
    "shared @ file:///${PROJECT_ROOT}/shared"
]
```
开发时用 `pip install -e ../shared`，Docker 构建时 `pip install ../shared`。

### 依赖管理
- 使用 `pyproject.toml` + `pip-tools`（或 `poetry`）
- `requirements.txt` 由 lock 文件生成，确保可复现
- 禁止 `pip install xxx` 后不更新依赖文件

### 错误处理
- 业务异常使用自定义 Exception 类（定义在 `shared/exceptions.py`）
- API 层统一 exception handler，返回标准错误格式
- 禁止裸 `except:` 或 `except Exception:`

### 日志
- 使用 `structlog` 结构化日志
- 所有日志必须包含 `request_id`（链路追踪）
- 敏感信息（API Key、手机号）脱敏

### 测试
- 使用 `pytest` + `pytest-asyncio`
- 异步测试用 `@pytest.mark.asyncio`
- 目标覆盖率 ≥ 70%（核心路径 ≥ 90%）

## Flutter 编码规范

### 状态管理
- **选型: Riverpod 2.x** (`flutter_riverpod ^2.6.1`)
- `AsyncNotifierProvider` 用于需要初始化异步加载的状态（如 AuthNotifier）
- `StateNotifierProvider` 用于复杂状态管理（如 RoomListNotifier、AgentListNotifier）
- `FutureProvider` 用于一次性异步数据（如 PersonaTemplate 列表）
- 禁止 StatefulWidget 内写复杂业务逻辑

### 网络层
- API 调用封装在 `services/` 层，统一通过 `ApiClient` 单例发起请求
- `ApiClient` 自动处理 JWT 注入、401 token 刷新、超时重试
- WebSocket 封装为 `WsClient` **单例**，支持心跳 (30s) + 指数退避重连
- 所有 WS 事件名使用 `WsEvents` 常量类引用，禁止硬编码字符串
- 所有请求/响应使用共享类型（`shared-types.dart`）

### 错误处理
- 全局错误提示通过 `AppSnackBar`（挂载 `scaffoldMessengerKey`）
- API 错误映射通过 `mapApiError()` 转为用户友好的中文消息
- 异步操作统一使用 `safeCall()` / `safeCallWithRetry()` 包装
- `ErrorBoundary` widget 包裹 MaterialApp，兜底未捕获异常

### i18n
- 当前: `lib/core/strings.dart` 纯 Dart 常量管理所有用户可见字符串
- 未来: 迁移到 `flutter_localizations` + ARB 文件

### 乐观更新
- 写操作（创建/更新/删除）优先采用「乐观更新 → API 确认 → 失败回滚」模式
- 示例: `AgentListNotifier.delete()` — 先从列表移除，API 失败后回滚

### UI
- 按设计稿开发，组件提取到 `widgets/`
- 使用 Material 3 主题系统 (`useMaterial3: true`)
- 品牌色通过 `ColorScheme.fromSeed()` 生成
- 适配 iOS / Android / Web 三平台

## 文档规范
- 方案文档使用 Markdown 格式
- 演示页使用 H5 页面（鲜亮明快配色）
- API 文档使用 OpenAPI 3.0（FastAPI 自动生成）

## 契约管理
- 契约文件在 `docs/contracts/`，只有恺撒可修改
- 任何变更更新 `docs/contracts/CHANGELOG.md`
- 变更后通知所有相关 Agent 同步

## 代码审查与报告规范

### 审查机制
- **所有 Agent 的代码**均由恺撒统一审查
- 审查报告统一存放在 `reviews/` 目录下
- **命名规则**: `Agent{X}_{名字}_代码审查_{YYYY-MM-DD}.md`
  - 示例: `AgentA_Marcus_代码审查_2026-03-19.md`
  - 示例: `AgentB_Minerva_代码审查_2026-03-20.md`
  - 示例: `AgentC_Apollo_代码审查_2026-03-19.md`

### 审查触发时机
1. **阶段性交付**: 每个 Week 周期结束时（Week 1-2 / Week 3-4 / Week 5-6 / Week 7-9）
2. **关键模块完成**: 核心基础设施（网络层/数据层/状态管理）首次提交时
3. **集成验证前**: Week 5 / Week 10 集成检查点之前
4. **智远主动要求**: 随时可发起

### 报告内容要求
每份审查报告必须包含：
- **Bug 列表**: 标注优先级（P0 必须立即修 / P1 尽快 / P2 下次迭代），附具体文件和行号
- **建议优化**: 不阻塞但值得改进的点
- **做得好的地方**: 肯定正确的设计决策
- **修复优先级表**: 汇总所有问题的预计工时

### 修复跟踪
- Agent 修复后，恺撒在原报告末尾追加「修复确认」章节
- 同一文件多次审查时，新建独立报告（带日期区分），不覆盖历史报告

## 工作日报规范

### 存放位置
- 目录: `reports/`
- **命名规则**: `agent-{x}_{YYYY-MM-DD}.md`
  - 示例: `agent-a_2026-03-19.md` (Agent A — Marcus / 后端)
  - 示例: `agent-b_2026-03-19.md` (Agent B — Minerva / AI 引擎)
  - 示例: `agent-c_2026-03-19.md` (Agent C — Apollo / Flutter)

### 更新策略
- **每天一个文件**，同一天内多次工作更新追加到同一文件，不创建新文件
- 如果当天已有日报文件，在文件内追加新的章节（用分割线 `---` 分隔）
- 日报在每次对话的重要任务完成后更新

### 内容要求
每份日报应包含：
1. **Agent 标识行**: Agent 代号 + 名字 + 工作目录
2. **今日完成**: 按模块列出完成的工作内容
3. **当前状态**: 整体进度概述（测试通过率等）
4. **阻塞项**: 当前无法推进的事项及原因
5. **下一步**: 后续计划

### 目的
- 让恺撒（Caesar / 主控 Agent）快速了解各 Agent 当日产出
- 跨 Agent 协作时作为进度同步依据
- 不替代 `context_memory/` 中的检查点和工作日志，日报更侧重对外汇报

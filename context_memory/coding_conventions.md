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
- 选型待定（Riverpod 或 Bloc），Phase 0 确定
- 禁止 StatefulWidget 内写复杂业务逻辑

### 网络层
- API 调用封装在 `services/` 层
- WebSocket 封装为独立 service，支持自动重连
- 所有请求/响应使用共享类型（`shared-types.dart`）

### UI
- 按设计稿开发，组件提取到 `widgets/`
- 使用 Material 3 主题系统
- 适配 iOS / Android 双平台

## 文档规范
- 方案文档使用 Markdown 格式
- 演示页使用 H5 页面（鲜亮明快配色）
- API 文档使用 OpenAPI 3.0（FastAPI 自动生成）

## 契约管理
- 契约文件在 `docs/contracts/`，只有恺撒（Agent A）可修改
- 任何变更更新 `docs/contracts/CHANGELOG.md`
- 变更后通知所有相关 Agent 同步

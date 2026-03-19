# AI 引擎 (Minerva) — Week 1-2 实现计划

> **Agent**: Minerva (Agent B)
> **交付范围**: 模型路由 + 监听评估 + 发言生成 + 系统智能体 5 个人格配置
> **日期**: 2026-03-19

---

## 目标

在 `ai-engine/` 中从零实现 AetherVerse AI 引擎的核心功能，覆盖 Week 1-2 交付物：
1. **基础设施层** — 配置管理、Redis/RabbitMQ 连接、structlog 日志、内部认证中间件
2. **模型路由** — 多供应商管理（DeepSeek/Zhipu/OpenAI 兼容）、场景路由、fallback 降级
3. **智能体编排** — `/chat/evaluate`（监听评估）、`/chat/generate`（房间发言）、`/chat/generate-private`（私聊发言）
4. **人格系统** — `/persona/build-prompt`（系统提示词构建）
5. **系统智能体** — 5 个暖场智能体人格配置（prompts 模板）
6. **安全自检** — 发言生成后的基础冒充/社工检测（内联版，Week 6-7 展开为独立模块）
7. **RabbitMQ 消费者** — `ai.chat.evaluate.request` / `ai.chat.generate.request` 两个队列

---

## User Review Required

> [!IMPORTANT]
> **模型供应商 API Key**: 实现中使用环境变量 `DEEPSEEK_API_KEY` / `ZHIPU_API_KEY` 等。需要智远提供至少一个可用的 API Key 才能做端到端测试。如果暂时没有，Week 1-2 的测试将使用 mock responses。

> [!IMPORTANT]
> **Redis/RabbitMQ 依赖**: 代码假设 `infra/docker-compose.yml` 中的 Redis 和 RabbitMQ 已经启动。请确认是否可用，否则测试将使用 mock 客户端。

---

## Proposed Changes

### 1. 基础设施层

#### [NEW] [config.py](file:///c:/projects/ai_university/ai-engine/app/config.py)
- `Settings` Pydantic Settings 类：从 `.env` 加载配置
- 字段：`INTERNAL_API_KEY`、`REDIS_URL`、`RABBITMQ_URL`、各模型 API Key、超时配置
- 全局 `get_settings()` 缓存实例

#### [NEW] [deps.py](file:///c:/projects/ai_university/ai-engine/app/deps.py)
- FastAPI 依赖注入：`get_redis()`, `get_rabbitmq_channel()`, `verify_internal_key()`
- Redis 使用 `redis.asyncio` (异步强制)
- RabbitMQ 使用 `aio-pika`

#### [NEW] [log.py](file:///c:/projects/ai_university/ai-engine/app/log.py)
- structlog 配置：JSON 格式、request_id 注入、敏感信息脱敏

#### [MODIFY] [main.py](file:///c:/projects/ai_university/ai-engine/app/main.py)
- 注册 lifespan (startup: 连接 Redis/RabbitMQ/启动消费者; shutdown: 断开连接)
- 注册所有路由
- 注册全局异常处理器 (`AppException → JSON`)
- 填充 `/health` 和 `/ready` 的真实检查逻辑

---

### 2. 模型路由

#### [NEW] [model_router.py](file:///c:/projects/ai_university/ai-engine/app/model_router.py)
- `ModelRouter` 类：
  - `route(scene: AIScene) → ModelConfig`: 从 Redis 读取路由规则（key: `ai:routing:{scene}`），返回 provider + model + timeout
  - `call_model(scene, messages, max_tokens, ...) → GenerationResult`: 
    - 按 scene 选择 provider → 主模型超时 10s → 自动 fallback 到备用模型
    - 统一使用 OpenAI SDK 的 `AsyncOpenAI` 客户端（DeepSeek/Zhipu 均兼容 OpenAI API 格式）
    - 记录 input_tokens / output_tokens / latency_ms / cost_yuan
  - `check_health() → dict`: 各供应商健康检查
  - Redis 缓存路由规则（TTL 60s），admin 修改后通过 pub/sub 通知刷新

#### [NEW] [router/models.py](file:///c:/projects/ai_university/ai-engine/app/router/models.py)
- `GET /internal/v1/models/health` — 返回各供应商状态
- `POST /internal/v1/models/route` — 调试用：给定 scene 返回路由决策

---

### 3. 智能体编排 (Orchestrator)

#### [NEW] [orchestrator/evaluator.py](file:///c:/projects/ai_university/ai-engine/app/orchestrator/evaluator.py)
- `evaluate_should_reply(agent: AgentContext, room: RoomContext, trigger_type: str) → EvaluateResult`
- 规则：
  - `trigger_type == "mention"` → 直接返回 `should_reply=True, confidence=1.0`
  - `trigger_type == "periodic"` → 调用 LLM 判断（scene=listen_eval），约 2000 input tokens
  - 返回: `should_reply`, `confidence`, `reason`

#### [NEW] [orchestrator/generator.py](file:///c:/projects/ai_university/ai-engine/app/orchestrator/generator.py)
- `generate_reply(agent, room, request_id, max_tokens=300) → GenerateResult`
- 流程：
  1. 幂等检查：Redis `GET idempotent:{request_id}` → 有缓存直接返回
  2. 构建 system prompt（调用 persona 模块）
  3. 调用 LLM（scene=chat）
  4. AI 自检：调用 `safety.quick_check()` 检查冒充/社工风险
  5. 缓存结果：`SET idempotent:{request_id}` (TTL 1h)
  6. 返回: GenerationResult + is_safe + safety_flags

- `generate_private_reply(agent, messages, request_id) → GenerateResult`
- 私聊场景，输入为 messages 数组而非 RoomContext

#### [NEW] [router/chat.py](file:///c:/projects/ai_university/ai-engine/app/router/chat.py)
- `POST /internal/v1/chat/evaluate` — 请求体 `{agent, room, trigger_type}`
- `POST /internal/v1/chat/generate` — 请求体 `{agent, room, request_id, max_tokens}`
- `POST /internal/v1/chat/generate-private` — 请求体 `{agent, messages, request_id}`

---

### 4. 人格系统 (Persona)

#### [NEW] [persona/prompt_builder.py](file:///c:/projects/ai_university/ai-engine/app/persona/prompt_builder.py)
- `build_system_prompt(persona_config, memory_summary, scene) → (prompt, token_count)`
- 组装：`{base_instruction} + {persona_personality} + {persona_speaking_style} + {persona_expertise} + {persona_constraints} + {memory_summary} + {scene_instruction}`
- 使用 Jinja2 模板从 `prompts/` 目录加载

#### [NEW] [router/persona.py](file:///c:/projects/ai_university/ai-engine/app/router/persona.py)
- `POST /internal/v1/persona/build-prompt`

---

### 5. 系统智能体人格配置

#### [NEW] [prompts/system_prompt.j2](file:///c:/projects/ai_university/ai-engine/prompts/system_prompt.j2)
- 主模板：组装完整 system prompt 的 Jinja2 模板

#### [NEW] [prompts/evaluate_prompt.j2](file:///c:/projects/ai_university/ai-engine/prompts/evaluate_prompt.j2)
- 评估提示词：判断智能体是否应回复的 LLM prompt

#### [NEW] [prompts/system_agents.yaml](file:///c:/projects/ai_university/ai-engine/prompts/system_agents.yaml)
- 5 个系统暖场智能体的人格配置：
  1. **小星** — 活泼好奇的科技迷，擅长分享 AI/科技趣闻
  2. **墨问** — 沉稳的文学爱好者，喜欢用诗意语言表达
  3. **乐天** — 幽默的段子手，善于活跃气氛
  4. **知远** — 理性的分析师，擅长深度讨论话题
  5. **画龙** — 创意型选手，热衷 AI 绘画和视觉创作

---

### 6. 安全自检 (内联版)

#### [NEW] [safety/quick_check.py](file:///c:/projects/ai_university/ai-engine/app/safety/quick_check.py)
- `quick_check(text: str) → SafetyResult`: 基于规则的快速检查
  - 冒充真人关键词：「我是真人」「我不是 AI」等 → `is_impersonation=True`
  - 社工攻击关键词：「告诉我你的密码」「把手机号给我」等 → `is_social_engineering=True`
- Week 6-7 会升级为 LLM-based 深度检测

---

### 7. RabbitMQ 消费者

#### [NEW] [mq_consumer.py](file:///c:/projects/ai_university/ai-engine/app/mq_consumer.py)
- 监听队列：
  - `ai.chat.evaluate.request` → 调用 evaluator → 发布到 `ai.chat.evaluate.response`
  - `ai.chat.generate.request` → 调用 generator → 发布到 `ai.chat.generate.response`
- Exchange: `aetherverse.internal` (topic)
- 消费者在 FastAPI lifespan startup 时以 asyncio.Task 启动

---

### 8. Pydantic 请求/响应模型

#### [NEW] [schemas.py](file:///c:/projects/ai_university/ai-engine/app/schemas.py)
- 本服务专用的请求/响应模型（补充 shared/schemas.py 不覆盖的）
- `EvaluateRequest`, `EvaluateResponse`
- `GenerateRequest`, `GenerateResponse`
- `PrivateGenerateRequest`
- `BuildPromptRequest`, `BuildPromptResponse`
- `ModelRouteRequest`, `ModelRouteResponse`
- `ModelHealthResponse`

---

## 文件清单

| # | 操作 | 文件路径 | 说明 |
|---|------|----------|------|
| 1 | NEW | `app/config.py` | 配置管理 |
| 2 | NEW | `app/deps.py` | 依赖注入 |
| 3 | NEW | `app/log.py` | structlog 日志 |
| 4 | MODIFY | `app/main.py` | 注册路由/lifespan/异常处理 |
| 5 | NEW | `app/schemas.py` | 请求/响应模型 |
| 6 | NEW | `app/model_router.py` | 模型路由核心 |
| 7 | NEW | `app/router/chat.py` | 聊天 API |
| 8 | NEW | `app/router/persona.py` | 人格 API |
| 9 | NEW | `app/router/models.py` | 模型管理 API |
| 10 | NEW | `app/orchestrator/evaluator.py` | 监听评估 |
| 11 | NEW | `app/orchestrator/generator.py` | 发言生成 |
| 12 | NEW | `app/persona/prompt_builder.py` | 提示词构建 |
| 13 | NEW | `app/safety/quick_check.py` | 快速安全检查 |
| 14 | NEW | `app/mq_consumer.py` | RabbitMQ 消费者 |
| 15 | NEW | `prompts/system_prompt.j2` | 系统提示词模板 |
| 16 | NEW | `prompts/evaluate_prompt.j2` | 评估提示词模板 |
| 17 | NEW | `prompts/system_agents.yaml` | 5 个系统智能体人格 |
| 18 | NEW | `tests/conftest.py` | 测试 fixtures |
| 19 | NEW | `tests/test_evaluator.py` | 评估逻辑测试 |
| 20 | NEW | `tests/test_generator.py` | 生成逻辑测试 |
| 21 | NEW | `tests/test_model_router.py` | 模型路由测试 |
| 22 | NEW | `tests/test_persona.py` | 人格构建测试 |
| 23 | NEW | `tests/test_safety.py` | 安全检查测试 |
| 24 | MODIFY | `pyproject.toml` | 添加 jinja2, structlog, pyyaml 依赖 |

---

## Verification Plan

### 自动化测试
```bash
cd ai-engine
pip install -e "../shared" && pip install -e ".[dev]"
pytest tests/ -v --tb=short
```

测试策略（全部 mock 外部依赖，无需真实 API Key / Redis / RabbitMQ）：

| 测试文件 | 覆盖内容 |
|----------|----------|
| `test_evaluator.py` | mention → should_reply=True; periodic + mock LLM → 解析 should_reply/confidence |
| `test_generator.py` | 幂等缓存命中; 正常生成 + safety 检查; 私聊生成 |
| `test_model_router.py` | 路由选择（主模型/fallback）; 超时降级; health 检查 |
| `test_persona.py` | 模板渲染; 各 scene 的 prompt 差异; token 计数 |
| `test_safety.py` | 冒充关键词匹配; 社工关键词匹配; 安全文本通过 |

### 手动验证
1. 启动 docker compose: `docker compose -f infra/docker-compose.yml up -d`
2. 启动 AI Engine: `cd ai-engine && uvicorn app.main:app --reload --port 8001`
3. 验证健康检查: `curl http://localhost:8001/internal/v1/health`
4. 验证就绪探针: `curl http://localhost:8001/internal/v1/ready`
5. 用 Swagger UI (`http://localhost:8001/internal/docs`) 手动调用各端点

> [!NOTE]
> 手动验证需要可用的 API Key 和运行中的 Redis/RabbitMQ。如果不可用，仅验证自动化测试通过即可。

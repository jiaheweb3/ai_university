# Agent B (Minerva) 代码审查报告

> **审查人**: 恺撒 | **日期**: 2026-03-19
> **审查范围**: `ai-engine/app/` 全部模块（Week 1-4 交付）
> **总体评价**: ⭐⭐⭐⭐½ **优秀** — 架构成熟度高于预期，模型路由 fallback、幂等缓存、两层审核、MQ 消费者设计都很专业。2 个 Bug + 4 个建议。

---

## ❌ Bug（必须修复）

### BUG-1: `_handle_moderation` 返回裸 dict，未经 Pydantic 序列化

[mq_consumer.py#L197-211](file:///c:/projects/ai_university/ai-engine/app/mq_consumer.py#L197-L211):

```python
result = await check_text(...)  # 返回 dict
await exchange.publish(
    Message(body=json.dumps(result).encode(), ...),  # 裸 dict
)
```

`check_text()` 返回的是原始 `dict`，直接 `json.dumps` 发出去。但 `_handle_evaluate` 和 `_handle_generate` 都用了 Pydantic model 的 `model_dump_json()`。这导致：
- 审核响应的字段命名和类型没有经过 schema 校验
- 与 `schemas.ModerationResult` 不一致的写法，后端（Agent A）解析可能出错

同样的问题存在于 `_handle_memory`（L160-176）和 `_handle_creation`（L178-195），都是手动构建 dict。

> **修复**: 统一用 Pydantic model 序列化响应。`_handle_memory` 用 `MemorySummarizeResponse`，`_handle_creation` 用 `ImageGenAccepted`，`_handle_moderation` 用 `ModerationResult`。

---

### BUG-2: `generator.py` 安全自检不安全时仍然返回内容

[generator.py#L87-106](file:///c:/projects/ai_university/ai-engine/app/orchestrator/generator.py#L87-L106):

```python
safety_result = quick_check(result.content)

response = GenerateResponse(
    content=result.content,       # ← 不安全的内容原样返回
    is_safe=safety_result.is_safe,
    safety_flags=safety_result.flags,
)
```

当 `is_safe=False`（检测到冒充/社工）时，`content` 仍然是原始的不安全内容。后端如果没有二次校验就直接广播到房间，违规内容就泄露了。

> **修复**: `is_safe=False` 时替换 content 为安全提示（如"[内容已被安全系统过滤]"），或清空 content 让后端决定。

---

## ⚠️ 建议优化

### S-1: `model_router.py` 成本价格硬编码

[model_router.py#L294-298](file:///c:/projects/ai_university/ai-engine/app/model_router.py#L294-L298):

```python
prices = {
    "deepseek": (1.0 / 1_000_000, 2.0 / 1_000_000),
    "zhipu": (0.1 / 1_000_000, 0.1 / 1_000_000),
    ...
}
```

价格变动频繁。建议移到 `config.py` 或 Redis 动态配置，避免每次调价都要改代码重部署。

---

### S-2: `deps.py` Redis 连接日志泄露 URL

[deps.py#L36](file:///c:/projects/ai_university/ai-engine/app/deps.py#L36):

```python
await logger.ainfo("redis_connected", url=settings.REDIS_URL)
```

如果 Redis URL 包含密码（`redis://:password@host:6379`），会被明文打到日志里。RabbitMQ 同理（L58）。建议脱敏后再打日志。

---

### S-3: `moderator.py` 引用了 `prompt_builder` 的私有函数

[moderator.py#L16](file:///c:/projects/ai_university/ai-engine/app/moderation/moderator.py#L16):

```python
from ..persona.prompt_builder import _get_jinja_env
```

下划线前缀是 Python 的 private 约定。跨模块引用私有函数增加耦合。建议在 `prompt_builder.py` 里暴露一个公开的 `get_jinja_env()` 函数。

---

### S-4: `watermark.py` 缺乏 JPEG 降级警告

水印用 LSB 嵌入到 PNG。但如果后续链路（CDN、对象存储、前端渲染）把 PNG 转成 JPEG，水印信息会完全丢失（JPEG 是有损压缩）。建议：
- 在 `embed_watermark()` 的 docstring 或日志中明确提醒使用方不得转码为 JPEG
- 或者同时在 PNG metadata（EXIF/tEXt chunk）中备份一份水印信息作为冗余

---

## ✅ 做得好的地方

| 项目 | 说明 |
|------|------|
| **模型路由 + fallback** | `model_router.py` 设计精良：Redis 动态路由 → 本地缓存 TTL → 默认规则三级降级，主模型超时自动 fallback ✅ |
| **OpenAI 兼容客户端** | 用 `AsyncOpenAI` 统一对接 DeepSeek/智谱/OpenAI，加新供应商只需加配置 ✅ |
| **幂等缓存** | `generator.py` 用 Redis 做 request_id 幂等，防止 MQ 重复消费 ✅ |
| **两层内容审核** | 关键词快速匹配 → LLM 语义审核，LLM 不可用时优雅降级 ✅ |
| **MQ 消费者架构** | 泛化消费循环 `_consume()`，异常不传播不崩进程 ✅ |
| **lifespan 管理** | Redis/RabbitMQ 初始化失败不阻塞启动，降级运行 ✅ |
| **健康探针** | 分离 liveness (`/health`) 和 readiness (`/ready`)，后者真实检查依赖 ✅ |
| **结构化日志** | 全局 structlog + request_id 链路追踪 ✅ |
| **LLM JSON 解析容错** | `_parse_evaluate_json()` 兼容 markdown 代码块包裹 + 花括号提取 ✅ |
| **安全自检** | 8+8 条正则覆盖冒充和社工场景，Week 6-7 升级 LLM 深度检测的路径清晰 ✅ |
| **Pydantic schemas** | 34 个模型完全对齐 `ai-engine-api.yaml` 契约 ✅ |

---

## 修复优先级

| 优先级 | 项目 | 预计工时 |
|--------|------|---------|
| **P0** | BUG-2: 不安全内容未过滤 | 10 分钟 |
| **P1** | BUG-1: MQ 响应序列化不一致 | 20 分钟 |
| **P2** | S-1 ~ S-4 | 下次迭代 |

---

## 与 Agent A（Marcus 后端）联调注意事项

1. Agent A 消费 MQ 响应时，需要按 Pydantic model 解析。在 BUG-1 修复前，`memory`/`creation`/`moderation` 三个队列的响应格式可能与 schema 不完全一致——Agent A 侧要做兼容处理或等 Minerva 先修
2. `generate` 响应的 `is_safe` 字段——Agent A 需要在广播消息前检查此字段，如果 `is_safe=False` 则不广播并触发审核流程

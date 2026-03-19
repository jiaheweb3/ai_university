# AI 引擎 Week 3-4 实现计划 — 记忆 / 图片生成 / 审核 / 水印

## 目标

在 Week 1-2 基础（模型路由 + 监听评估 + 发言生成 + 人格系统）上，完成剩余全部 AI 引擎端点。

## 范围

| 模块 | 端点 | 类型 |
|------|------|------|
| 记忆 | `POST /memory/summarize` | 同步 |
| 创作 | `POST /creation/generate-image` | 异步 (返回 task_id) |
| 创作 | `GET /creation/status/{task_id}` | 查询 |
| 审核 | `POST /moderation/check-text` | 同步 |
| 审核 | `POST /moderation/check-image` | 同步 |
| 审核 | `POST /moderation/check-persona` | 同步 |
| 安全 | `POST /safety/check-impersonation` | 同步 (逻辑已有) |
| 安全 | `POST /safety/check-social-engineering` | 同步 (逻辑已有) |
| AIGC | `POST /aigc/embed-watermark` | 同步 |
| MQ | `ai.memory.summarize.request` | 消费者 |
| MQ | `ai.creation.request` | 消费者 |
| MQ | `ai.moderation.request` | 消费者 |

---

## 新增 / 修改文件

### 记忆系统

#### [NEW] `app/memory/summarizer.py`
- `summarize_memories(agent_id, persona_config, memories, max_tokens=500)` → 调 LLM 压缩记忆
- 提示词模板: 以智能体视角总结，保持人格一致性
- 输出 ≤ 500 tokens 的摘要

#### [NEW] `prompts/memory_summarize.j2`
- Jinja2 模板：注入智能体人格 + 记忆列表 → 要求以第一人称视角输出摘要

#### [NEW] `app/router/memory.py`
- `POST /memory/summarize` → 调用 summarizer

### 图片生成

#### [NEW] `app/creation/image_generator.py`
- `start_image_generation(agent, topic, request_id, image_size)` → 异步任务
- Redis 存储任务状态 (pending → processing → completed/failed)
- Mock 模式: 返回固定占位图 URL + 模拟延迟
- 生产模式: 调用智谱 CogView-3-Plus

#### [NEW] `app/router/creation.py`
- `POST /creation/generate-image` → 返回 202 + task_id
- `GET /creation/status/{task_id}` → 查询 Redis 中的任务状态

#### [NEW] `prompts/image_gen_prompt.j2`
- 将用户创作主题 + 关键词 → 转化为适合图片模型的英文 prompt

### 内容审核

#### [NEW] `app/moderation/text_moderator.py`
- 两层检测: (1) 高危关键词快速匹配 (2) LLM 语义理解
- 输出: risk_level (safe/suspect/block) + categories + matched_rules + confidence

#### [NEW] `app/moderation/image_moderator.py`
- 框架级: 接收 image_url，返回审核结果
- 当前 mock 返回 safe（等 API Key 后接入多模态模型）

#### [NEW] `app/moderation/persona_moderator.py`
- 检查人格配置是否含违规内容（暴力/色情/政治敏感）
- 规则级 + LLM 辅助审核

#### [NEW] `app/router/moderation.py`
- `POST /moderation/check-text`
- `POST /moderation/check-image`
- `POST /moderation/check-persona`

#### [NEW] `prompts/moderation_prompt.j2`
- LLM 审核提示词，输出 JSON (risk_level + categories + confidence)

### 安全 HTTP 路由

#### [NEW] `app/router/safety.py`
- `POST /safety/check-impersonation` → 调用 quick_check.check_impersonation
- `POST /safety/check-social-engineering` → 调用 quick_check.check_social_engineering

### AIGC 水印

#### [NEW] `app/aigc/watermark.py`
- 基于 Pillow 的 LSB (Least Significant Bit) 水印嵌入
- 输入: image_url + metadata → 下载图片 → 嵌入元数据 → 返回水印图片 URL
- metadata: content_id, generated_at, model, provider

#### [NEW] `app/router/aigc.py`
- `POST /aigc/embed-watermark`

### MQ 消费者扩展

#### [MODIFY] `app/mq_consumer.py`
- 新增 3 个队列消费者: memory.summarize / creation / moderation

### 路由注册

#### [MODIFY] `app/main.py`
- 注册新路由: memory, creation, moderation, safety, aigc

### Schemas 扩展

#### [MODIFY] `app/schemas.py`
- 新增: MemorySummarizeRequest/Response, ImageGenRequest/Response, ModerationRequest/Response 等

---

## 测试

| 文件 | 覆盖 |
|------|------|
| `tests/test_memory.py` | summarizer 输出长度、人格一致性 |
| `tests/test_creation.py` | 任务创建、状态查询、mock 生成 |
| `tests/test_moderation.py` | 文本审核 (safe/suspect/block)、人格审核 |
| `tests/test_watermark.py` | LSB 嵌入 + 提取验证 |

全部 mock LLM 和外部 API。

---

## 验证方式

### 自动化
```bash
cd ai-engine && python -m pytest tests/ -v
```

### 手动 (API Key 到位后)
```bash
# 记忆摘要
curl -X POST http://localhost:8001/internal/v1/memory/summarize \
  -H "X-Internal-Key: changeme" \
  -d '{"agent_id":"...", "memories":[...]}'

# 图片生成
curl -X POST http://localhost:8001/internal/v1/creation/generate-image \
  -H "X-Internal-Key: changeme" \
  -d '{"agent":{...}, "topic":{...}, "request_id":"..."}'
```

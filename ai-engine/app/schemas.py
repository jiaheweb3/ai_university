"""
AetherVerse AI Engine — 请求/响应 Pydantic 模型
补充 shared/schemas.py 中不覆盖的 AI 引擎专用模型
"""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from shared.constants import AIScene
from shared.schemas import AgentContext, GenerationResult, RoomContext, RoomContextMessage


# ============================================================
# Chat — Evaluate
# ============================================================

class EvaluateRequest(BaseModel):
    agent: AgentContext
    room: RoomContext
    trigger_type: str = Field(default="periodic", pattern="^(mention|periodic)$")


class EvaluateResponse(BaseModel):
    should_reply: bool
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = ""
    model: str = ""
    tokens_used: int = 0


# ============================================================
# Chat — Generate
# ============================================================

class GenerateRequest(BaseModel):
    agent: AgentContext
    room: RoomContext
    request_id: str
    max_tokens: int = 300


class GenerateResponse(GenerationResult):
    is_safe: bool = True
    safety_flags: list[str] = Field(default_factory=list)


# ============================================================
# Chat — Generate Private
# ============================================================

class PrivateMessageItem(BaseModel):
    sender_type: str
    content: str
    created_at: str | None = None


class PrivateGenerateRequest(BaseModel):
    agent: AgentContext
    messages: list[PrivateMessageItem] = Field(max_length=20)
    request_id: str


# ============================================================
# Persona — Build Prompt
# ============================================================

class BuildPromptRequest(BaseModel):
    persona_config: dict
    memory_summary: str | None = None
    scene: str = Field(default="room_chat", pattern="^(room_chat|private_chat|creation)$")


class BuildPromptResponse(BaseModel):
    system_prompt: str
    token_count: int = 0


# ============================================================
# Models — Route / Health
# ============================================================

class ModelRouteRequest(BaseModel):
    scene: AIScene
    fallback_level: int = 0


class ModelRouteResponse(BaseModel):
    provider: str
    model: str
    base_url: str
    timeout_ms: int
    is_fallback: bool = False


class ProviderHealth(BaseModel):
    name: str
    status: str = "unknown"
    latency_ms: int | None = None
    available_models: list[str] = Field(default_factory=list)


class ModelHealthResponse(BaseModel):
    providers: list[ProviderHealth] = Field(default_factory=list)


# ============================================================
# Memory — Summarize
# ============================================================

class MemoryItem(BaseModel):
    content: str
    created_at: str | None = None


class MemorySummarizeRequest(BaseModel):
    agent_id: str
    persona_config: dict | None = None
    memories: list[MemoryItem]
    max_tokens: int = 500


class MemorySummarizeResponse(BaseModel):
    summary: str
    token_count: int = 0
    model: str = ""


# ============================================================
# Creation — Image Generation
# ============================================================

class TopicInfo(BaseModel):
    id: str | None = None
    title: str
    description: str = ""
    keywords: list[str] = Field(default_factory=list)
    reference_url: str | None = None


class ImageGenRequest(BaseModel):
    agent: AgentContext
    topic: TopicInfo
    request_id: str
    image_size: str = "1024x1024"


class ImageGenAccepted(BaseModel):
    task_id: str
    estimated_seconds: int


class ImageTaskStatus(BaseModel):
    status: str  # pending | processing | completed | failed
    image_url: str | None = None
    thumbnail_url: str | None = None
    creative_process: dict | None = None
    model: str | None = None
    cost_yuan: float | None = None
    error_message: str | None = None


# ============================================================
# Moderation
# ============================================================

class TextModerationRequest(BaseModel):
    text: str
    context: list[str] | None = None
    sender_type: str = "user"


class ModerationResult(BaseModel):
    risk_level: str = "safe"  # safe | suspect | block
    categories: list[str] = Field(default_factory=list)
    matched_rules: list[str] = Field(default_factory=list)
    confidence: float = 0.0


class ImageModerationRequest(BaseModel):
    image_url: str


class PersonaModerationRequest(BaseModel):
    persona_config: dict
    agent_name: str = ""


# ============================================================
# Safety
# ============================================================

class ImpersonationCheckRequest(BaseModel):
    text: str
    sender_type: str = "agent"


class ImpersonationCheckResponse(BaseModel):
    is_impersonation: bool = False
    matched_patterns: list[str] = Field(default_factory=list)


class SocialEngineeringCheckRequest(BaseModel):
    text: str
    conversation_history: list[str] | None = None


class SocialEngineeringCheckResponse(BaseModel):
    is_social_engineering: bool = False
    risk_indicators: list[str] = Field(default_factory=list)


# ============================================================
# AIGC Watermark
# ============================================================

class WatermarkMetadata(BaseModel):
    content_id: str
    generated_at: str | None = None
    model: str = ""
    provider: str = ""


class WatermarkRequest(BaseModel):
    image_url: str
    metadata: WatermarkMetadata


class WatermarkResponse(BaseModel):
    watermarked_image_url: str | None = None
    status: str = "ok"

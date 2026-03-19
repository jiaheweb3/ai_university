"""
AetherVerse 共享 Pydantic Schemas
API 请求/响应的共享数据模型，Agent A/B/C 统一引用
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from .constants import (
    AgentLevel,
    AgentStatus,
    ArtworkStatus,
    MessageType,
    ModerationStatus,
    NotificationType,
    PointTxStatus,
    PointTxType,
    RoomMemberType,
    TopicStatus,
)


# ============================================================
# 通用
# ============================================================

class ApiResponse(BaseModel):
    """统一 API 响应格式"""
    code: int = 0
    message: str = "success"
    data: dict | list | None = None


class PaginatedData(BaseModel):
    items: list = Field(default_factory=list)
    next_cursor: str | None = None
    has_more: bool = False


# ============================================================
# 用户
# ============================================================

class UserProfileBrief(BaseModel):
    id: UUID
    nickname: str
    avatar_url: str | None = None


class UserProfile(UserProfileBrief):
    bio: str | None = None
    points_balance: int = 0
    agent_count: int = 0
    created_at: datetime


# ============================================================
# 房间
# ============================================================

class RoomMemberInfo(BaseModel):
    id: UUID
    member_type: RoomMemberType
    nickname: str
    avatar_url: str | None = None
    is_online: bool = False
    is_ai: bool = False


# ============================================================
# 消息
# ============================================================

class MessageSender(BaseModel):
    id: UUID
    type: str  # user | agent | system
    nickname: str
    avatar_url: str | None = None
    is_ai: bool = False
    owner_nickname: str | None = None


class MessageOut(BaseModel):
    id: UUID
    room_id: UUID | None = None
    conversation_id: UUID | None = None
    sender: MessageSender
    msg_type: MessageType
    content: str | None = None
    image_url: str | None = None
    reply_to_id: UUID | None = None
    mentions: list[UUID] = Field(default_factory=list)
    is_ai_generated: bool = False
    moderation_status: ModerationStatus | None = None
    created_at: datetime


# ============================================================
# 智能体
# ============================================================

class PersonaConfig(BaseModel):
    personality: str | None = None
    speaking_style: str | None = None
    expertise: str | None = None
    constraints: str | None = None


class AgentOut(BaseModel):
    id: UUID
    owner_id: UUID
    name: str
    avatar_url: str | None = None
    bio: str | None = None
    level: AgentLevel = AgentLevel.L1
    status: AgentStatus = AgentStatus.ACTIVE
    persona_config: PersonaConfig | None = None
    current_room_id: UUID | None = None
    is_speaking: bool = True
    created_at: datetime


# ============================================================
# 话题 / 创作
# ============================================================

class TopicBrief(BaseModel):
    id: UUID
    title: str
    status: TopicStatus
    deadline: datetime | None = None


class ArtworkOut(BaseModel):
    id: UUID
    topic_id: UUID
    agent: UserProfileBrief | None = None
    owner: UserProfileBrief | None = None
    image_url: str | None = None
    thumbnail_url: str | None = None
    status: ArtworkStatus
    points_cost: int = 0
    created_at: datetime


# ============================================================
# 积分
# ============================================================

class PointTransactionOut(BaseModel):
    id: UUID
    tx_type: PointTxType
    status: PointTxStatus
    amount: int
    balance_after: int
    description: str | None = None
    created_at: datetime


# ============================================================
# 通知
# ============================================================

class NotificationOut(BaseModel):
    id: UUID
    ntype: NotificationType
    title: str
    content: str | None = None
    is_read: bool = False
    created_at: datetime


# ============================================================
# AI 引擎内部通信
# ============================================================

class AgentContext(BaseModel):
    """后端 → AI 引擎: 智能体上下文"""
    agent_id: UUID
    owner_id: UUID | None = None
    name: str | None = None
    level: AgentLevel = AgentLevel.L1
    persona_config: PersonaConfig | None = None
    memory_summary: str | None = None
    system_prompt: str | None = None


class RoomContextMessage(BaseModel):
    id: UUID
    sender_name: str
    sender_type: str
    content: str
    created_at: datetime


class RoomContext(BaseModel):
    """后端 → AI 引擎: 房间上下文"""
    room_id: UUID
    room_name: str | None = None
    room_description: str | None = None
    current_topic: str | None = None
    recent_messages: list[RoomContextMessage] = Field(default_factory=list, max_length=20)


class GenerationResult(BaseModel):
    """AI 引擎 → 后端: 生成结果"""
    content: str
    model: str
    provider: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0
    cost_yuan: float = 0.0
    request_id: str | None = None

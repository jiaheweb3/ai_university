"""
AetherVerse 共享枚举定义
从 db-schema.sql 中的 PostgreSQL ENUM 类型 1:1 映射
供 server/ 和 ai-engine/ 共同引用，保证类型一致性
"""

from enum import StrEnum


# ============================================================
# 用户系统
# ============================================================

class UserStatus(StrEnum):
    ACTIVE = "active"
    BANNED_TEMP = "banned_temp"
    BANNED_PERM = "banned_perm"
    DELETED = "deleted"


class DIDType(StrEnum):
    INTERNAL = "internal"
    EXTERNAL = "external"


class LoginMethod(StrEnum):
    PASSWORD = "password"
    SMS = "sms"


# ============================================================
# 房间系统
# ============================================================

class RoomStatus(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class RoomMemberRole(StrEnum):
    MEMBER = "member"
    MODERATOR = "moderator"
    ADMIN = "admin"


class RoomMemberType(StrEnum):
    USER = "user"
    AGENT = "agent"


# ============================================================
# 消息系统
# ============================================================

class MessageType(StrEnum):
    TEXT = "text"
    IMAGE = "image"
    SYSTEM = "system"
    AI_GENERATED = "ai_generated"


class ModerationStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPEALED = "appealed"
    APPEAL_APPROVED = "appeal_approved"
    APPEAL_REJECTED = "appeal_rejected"


# ============================================================
# 智能体系统
# ============================================================

class AgentOwnerType(StrEnum):
    USER = "user"
    SYSTEM = "system"


class AgentLevel(StrEnum):
    L1 = "L1"
    L2 = "L2"


class AgentStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    SUSPENDED = "suspended"
    DELETED = "deleted"


# ============================================================
# 创作系统
# ============================================================

class TopicStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    ENDED = "ended"
    ARCHIVED = "archived"


class ArtworkStatus(StrEnum):
    GENERATING = "generating"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    FAILED = "failed"


# ============================================================
# 积分系统
# ============================================================

class PointTxType(StrEnum):
    RECHARGE = "recharge"
    CREATE_AGENT = "create_agent"
    AGENT_SPEAK = "agent_speak"
    IMAGE_GENERATE = "image_generate"
    FREE_DAILY = "free_daily"
    REFUND = "refund"
    ADMIN_ADJUST = "admin_adjust"


class PointTxStatus(StrEnum):
    FROZEN = "frozen"
    CONFIRMED = "confirmed"
    REFUNDED = "refunded"
    EXPIRED = "expired"


class PayChannel(StrEnum):
    WECHAT = "wechat"
    ALIPAY = "alipay"


class OrderStatus(StrEnum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"
    RECONCILING = "reconciling"


# ============================================================
# 通知系统
# ============================================================

class NotificationType(StrEnum):
    MODERATION_RESULT = "moderation_result"
    AGENT_STATUS = "agent_status"
    ACCOUNT_SECURITY = "account_security"
    TASK_STATUS = "task_status"
    TRANSACTION = "transaction"


# ============================================================
# 审核系统
# ============================================================

class ContentType(StrEnum):
    MESSAGE = "message"
    ARTWORK = "artwork"
    AGENT_PERSONA = "agent_persona"


class SensitiveWordLevel(StrEnum):
    BLOCK = "block"
    SUSPECT = "suspect"
    OBSERVE = "observe"


# ============================================================
# 风控系统
# ============================================================

class RiskCategory(StrEnum):
    RATE_LIMIT = "rate_limit"
    SPAM = "spam"
    SOCIAL_ENGINEERING = "social_engineering"
    IMPERSONATION = "impersonation"
    HARASSMENT = "harassment"


class RiskAction(StrEnum):
    WARN = "warn"
    RATE_LIMIT = "rate_limit"
    PAUSE = "pause"
    BAN = "ban"


class ReportTargetType(StrEnum):
    USER = "user"
    AGENT = "agent"
    MESSAGE = "message"


class ReportStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


# ============================================================
# AI 网关
# ============================================================

class AIScene(StrEnum):
    CHAT = "chat"
    IMAGE_GEN = "image_gen"
    MODERATION = "moderation"
    LISTEN_EVAL = "listen_eval"
    MEMORY_SUMMARY = "memory_summary"


# ============================================================
# 管理后台
# ============================================================

class AdminRole(StrEnum):
    SUPER_ADMIN = "super_admin"
    OPS_ADMIN = "ops_admin"
    REVIEWER = "reviewer"


# ============================================================
# 外部 Agent
# ============================================================

class ExternalAgentStatus(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"

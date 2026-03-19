"""
AetherVerse Server — Models 包
导入所有模型确保 Alembic 能发现它们
"""

from app.models.admin import AdminOperationLog, AdminUser
from app.models.agent import Agent, AgentMemory, AgentRoomAssignment, PersonaTemplate
from app.models.ai_gateway import AIApiKey, AIBudgetConfig, AIProvider, AIRoutingRule, AIUsageLog
from app.models.auxiliary import FileUpload, GlobalConfig, SmsCode
from app.models.base import Base
from app.models.creation import Artwork, Topic
from app.models.external import ExternalAgent, ExternalAgentLog
from app.models.message import Conversation, Message
from app.models.metrics import DailyMetric, DailyRoomMetric
from app.models.moderation import ModerationQueue, SensitiveWord
from app.models.notification import Notification
from app.models.point import PointTransaction, RechargeOrder
from app.models.risk import Report, RiskEvent, RiskRule, UserBan
from app.models.room import Room, RoomMember
from app.models.user import LoginAttempt, User, UserBlock, UserDID, UserSetting

__all__ = [
    "Base",
    # User
    "User", "UserDID", "UserSetting", "UserBlock", "LoginAttempt",
    # Room
    "Room", "RoomMember",
    # Message
    "Message", "Conversation",
    # Agent
    "Agent", "AgentMemory", "AgentRoomAssignment", "PersonaTemplate",
    # Creation
    "Topic", "Artwork",
    # Point
    "PointTransaction", "RechargeOrder",
    # Notification
    "Notification",
    # Moderation
    "ModerationQueue", "SensitiveWord",
    # Risk
    "RiskRule", "RiskEvent", "UserBan", "Report",
    # AI Gateway
    "AIProvider", "AIApiKey", "AIRoutingRule", "AIUsageLog", "AIBudgetConfig",
    # Admin
    "AdminUser", "AdminOperationLog",
    # Metrics
    "DailyMetric", "DailyRoomMetric",
    # External Agent
    "ExternalAgent", "ExternalAgentLog",
    # Auxiliary
    "SmsCode", "FileUpload", "GlobalConfig",
]

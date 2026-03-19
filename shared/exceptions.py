"""
AetherVerse 统一异常 + 业务错误码
所有服务共享，确保 API 错误响应一致
"""


class ErrorCode:
    """业务错误码 (5 位数字)"""

    # 通用 (400xx)
    PARAM_INVALID = 40001
    PARAM_MISSING = 40002
    REQUEST_ID_DUPLICATE = 40003

    # 认证 (401xx)
    TOKEN_INVALID = 40101
    TOKEN_EXPIRED = 40102
    LOGIN_FAILED = 40103
    SMS_CODE_INVALID = 40104
    SMS_CODE_EXPIRED = 40105
    SMS_RATE_LIMITED = 40106
    ACCOUNT_BANNED = 40107
    ACCOUNT_DELETED = 40108
    PASSWORD_WRONG = 40109

    # 权限 (403xx)
    FORBIDDEN = 40301
    ADMIN_ONLY = 40302
    OWNER_ONLY = 40303

    # 未找到 (404xx)
    USER_NOT_FOUND = 40401
    ROOM_NOT_FOUND = 40402
    AGENT_NOT_FOUND = 40403
    MESSAGE_NOT_FOUND = 40404
    TOPIC_NOT_FOUND = 40405
    CONVERSATION_NOT_FOUND = 40406
    TEMPLATE_NOT_FOUND = 40407

    # 冲突 (409xx)
    PHONE_REGISTERED = 40901
    NICKNAME_TAKEN = 40902
    ROOM_FULL = 40903
    AGENT_LIMIT_REACHED = 40904
    ALREADY_JOINED = 40905

    # 业务限制 (422xx)
    POINTS_INSUFFICIENT = 42201
    DAILY_FREE_EXHAUSTED = 42202
    AGENT_SUSPENDED = 42203
    TOPIC_ENDED = 42204
    MODERATION_BLOCKED = 42205

    # 限频 (429xx)
    RATE_LIMITED = 42901
    MESSAGE_RATE_LIMITED = 42902

    # 服务端 (500xx)
    INTERNAL_ERROR = 50001
    AI_MODEL_ERROR = 50002
    AI_MODEL_TIMEOUT = 50003
    PAYMENT_CALLBACK_ERROR = 50004
    EXTERNAL_SERVICE_ERROR = 50005


class AppException(Exception):
    """统一业务异常基类"""

    def __init__(self, code: int, message: str, detail: str | None = None, status_code: int = 400):
        self.code = code
        self.message = message
        self.detail = detail
        self.status_code = status_code
        super().__init__(message)

    def to_dict(self) -> dict:
        result = {"code": self.code, "message": self.message}
        if self.detail:
            result["detail"] = self.detail
        return result


# 常用快捷异常
class NotFoundError(AppException):
    def __init__(self, code: int = ErrorCode.USER_NOT_FOUND, message: str = "资源不存在"):
        super().__init__(code=code, message=message, status_code=404)


class ForbiddenError(AppException):
    def __init__(self, code: int = ErrorCode.FORBIDDEN, message: str = "无权限"):
        super().__init__(code=code, message=message, status_code=403)


class UnauthorizedError(AppException):
    def __init__(self, code: int = ErrorCode.TOKEN_INVALID, message: str = "认证失败"):
        super().__init__(code=code, message=message, status_code=401)


class InsufficientPointsError(AppException):
    def __init__(self, message: str = "积分不足"):
        super().__init__(code=ErrorCode.POINTS_INSUFFICIENT, message=message, status_code=422)


class RateLimitedError(AppException):
    def __init__(self, message: str = "请求过于频繁"):
        super().__init__(code=ErrorCode.RATE_LIMITED, message=message, status_code=429)

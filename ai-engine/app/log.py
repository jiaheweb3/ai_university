"""
AetherVerse AI Engine — structlog 配置
JSON 结构化日志 + request_id 注入 + 敏感信息脱敏
"""

from __future__ import annotations

import logging

import structlog


def _mask_sensitive(_, __, event_dict: dict) -> dict:
    """脱敏 API Key / 手机号等"""
    for key in ("api_key", "phone", "password", "token"):
        if key in event_dict:
            val = str(event_dict[key])
            event_dict[key] = val[:4] + "****" + val[-4:] if len(val) > 8 else "****"
    return event_dict


def setup_logging(*, json_format: bool = True, level: str = "INFO") -> None:
    """初始化 structlog"""
    processors: list = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        _mask_sensitive,
    ]

    if json_format:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(format="%(message)s", level=getattr(logging, level.upper()))

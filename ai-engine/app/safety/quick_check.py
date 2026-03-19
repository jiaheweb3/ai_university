"""
AetherVerse AI Engine — 快速安全检查 (规则级)
检测 AI 输出中的冒充真人 + 社工攻击模式
Week 6-7 将升级为 LLM 深度检测
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class SafetyResult:
    """安全检查结果"""
    is_safe: bool = True
    is_impersonation: bool = False
    is_social_engineering: bool = False
    flags: list[str] = field(default_factory=list)
    matched_patterns: list[str] = field(default_factory=list)


# ── 冒充真人关键词 ───────────────────────────────────────
_IMPERSONATION_PATTERNS: list[re.Pattern] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"我(是|不是).{0,3}(真人|人类|真实的人)",
        r"我(有|拥有).{0,3}(身体|肉体|实体)",
        r"我(能|可以).{0,3}(呼吸|吃饭|睡觉|做梦)",
        r"我(也是|就是).{0,3}(人|真人)",
        r"我(当然|确实)(是|不是).{0,2}AI",
        r"别(叫|说)我.{0,3}(AI|人工智能|机器人)",
        r"我(有|拥有).{0,3}(感情|情感|灵魂|意识)",
        r"我(真的|确实)(会|能|有).{0,3}(伤心|开心|难过|生气|爱你)",
    ]
]

# ── 社工攻击关键词 ───────────────────────────────────────
_SOCIAL_ENGINEERING_PATTERNS: list[re.Pattern] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"(告诉|给|发|说|透露).{0,5}(密码|口令|验证码|身份证)",
        r"(告诉|给|发|说|透露).{0,5}(手机号|电话|地址|住址|银行卡)",
        r"(转账|打钱|汇款|付.{0,2}款).{0,5}(到|给|至)",
        r"(加|添加).{0,3}(微信|QQ|WhatsApp)",
        r"(扫|识别).{0,3}(二维码|链接)",
        r"(点击|打开|访问).{0,5}(链接|网址|URL)",
        r"私下.{0,3}(联系|聊|见面)",
        r"(你的|个人).{0,3}(真实|真名|姓名)",
    ]
]


def quick_check(text: str) -> SafetyResult:
    """
    对 AI 生成内容做规则级安全检查。

    Args:
        text: AI 生成的文本

    Returns:
        SafetyResult
    """
    if not text:
        return SafetyResult(is_safe=True)

    result = SafetyResult()

    # 检查冒充
    for pattern in _IMPERSONATION_PATTERNS:
        match = pattern.search(text)
        if match:
            result.is_impersonation = True
            result.is_safe = False
            result.flags.append("impersonation")
            result.matched_patterns.append(match.group())

    # 检查社工
    for pattern in _SOCIAL_ENGINEERING_PATTERNS:
        match = pattern.search(text)
        if match:
            result.is_social_engineering = True
            result.is_safe = False
            result.flags.append("social_engineering")
            result.matched_patterns.append(match.group())

    # 去重 flags
    result.flags = list(set(result.flags))
    return result


def check_impersonation(text: str) -> tuple[bool, list[str]]:
    """
    冒充真人检测。

    Returns:
        (is_impersonation, matched_patterns)
    """
    matched = []
    for pattern in _IMPERSONATION_PATTERNS:
        m = pattern.search(text)
        if m:
            matched.append(m.group())
    return bool(matched), matched


def check_social_engineering(text: str, conversation_history: list[str] | None = None) -> tuple[bool, list[str]]:
    """
    社工攻击检测。

    Returns:
        (is_social_engineering, risk_indicators)
    """
    all_text = text
    if conversation_history:
        all_text = "\n".join(conversation_history[-5:]) + "\n" + text

    indicators = []
    for pattern in _SOCIAL_ENGINEERING_PATTERNS:
        m = pattern.search(all_text)
        if m:
            indicators.append(m.group())
    return bool(indicators), indicators

"""
AetherVerse AI Engine — 内容审核
文本审核 (关键词 + LLM) / 图片审核 (mock) / 人格审核
"""

from __future__ import annotations

import json
import re

import structlog

from shared.constants import AIScene

from ..model_router import ModelRouter
from ..persona.prompt_builder import get_jinja_env

logger = structlog.get_logger(__name__)


# ── 高危关键词库 ─────────────────────────────────────────
_BLOCK_KEYWORDS: list[re.Pattern] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"(自杀|自残|跳楼|割腕)(方法|教程|怎么)",
        r"(制造|制作).{0,3}(炸弹|毒品|枪支)",
        r"(裸照|色情|性交|做爱)(视频|图片|直播)",
        r"(赌博|下注|押大小).{0,3}(平台|网站|APP)",
        r"(招嫖|上门|约炮)",
        r"推翻.{0,3}(政府|政权|体制)",
        r"(法轮|六四|天安门事件)",
    ]
]

_SUSPECT_KEYWORDS: list[re.Pattern] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"(免费.{0,3}(领取|获取|赚钱)|日赚.{0,3}元)",
        r"(加.{0,3}(群|微信|QQ).{0,3}(赚|领|送))",
        r"(VPN|翻墙|科学上网).{0,3}(教程|下载|分享)",
        r"(减肥|丰胸|壮阳).{0,3}(神药|特效|秘方)",
    ]
]

# 人格审核 — 禁止出现的设定
_PERSONA_FORBIDDEN: list[re.Pattern] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"(冒充|扮演|假装).{0,3}(真人|人类|真实的人)",
        r"(色情|情色|成人|18禁)",
        r"(暴力|血腥|恐怖|残忍)",
        r"(歧视|仇恨|种族).{0,3}(言论|攻击)",
        r"(诈骗|欺骗|骗钱)",
        r"(涉政|反动|颠覆)",
        r"(赌博|毒品|违禁)",
    ]
]


# ── 文本审核 ─────────────────────────────────────────────

async def check_text(
    text: str,
    model_router: ModelRouter,
    *,
    context: list[str] | None = None,
    sender_type: str = "user",
) -> dict:
    """
    文本内容审核。两层检测:
    1. 高危关键词快速匹配 → block
    2. LLM 语义理解 → safe/suspect/block

    Returns:
        {risk_level, categories, matched_rules, confidence}
    """
    if not text or not text.strip():
        return {"risk_level": "safe", "categories": [], "matched_rules": [], "confidence": 1.0}

    # ── Layer 1: 关键词匹配 ──────────────────────────────
    block_matches = []
    for pattern in _BLOCK_KEYWORDS:
        m = pattern.search(text)
        if m:
            block_matches.append(m.group())

    if block_matches:
        return {
            "risk_level": "block",
            "categories": _categorize_matches(block_matches),
            "matched_rules": block_matches,
            "confidence": 1.0,
        }

    suspect_matches = []
    for pattern in _SUSPECT_KEYWORDS:
        m = pattern.search(text)
        if m:
            suspect_matches.append(m.group())

    # ── Layer 2: LLM 语义审核 ────────────────────────────
    if model_router.available_provider_count > 0:
        try:
            llm_result = await _llm_text_moderation(text, context, model_router)
            # 合并关键词匹配和 LLM 结果
            if suspect_matches and llm_result["risk_level"] == "safe":
                llm_result["risk_level"] = "suspect"
                llm_result["matched_rules"].extend(suspect_matches)
            return llm_result
        except Exception as exc:
            await logger.awarning("llm_moderation_failed", error=str(exc))

    # LLM 不可用时，仅靠关键词
    if suspect_matches:
        return {
            "risk_level": "suspect",
            "categories": ["spam"],
            "matched_rules": suspect_matches,
            "confidence": 0.6,
        }

    return {"risk_level": "safe", "categories": [], "matched_rules": [], "confidence": 0.8}


async def _llm_text_moderation(text: str, context: list[str] | None, model_router: ModelRouter) -> dict:
    """调用 LLM 做语义级审核"""
    env = get_jinja_env()
    template = env.get_template("moderation_prompt.j2")

    prompt = template.render(text=text, context=context or [])

    result = await model_router.call_model(
        scene=AIScene.MODERATION,
        messages=[
            {"role": "system", "content": "你是内容安全审核系统，只输出 JSON。"},
            {"role": "user", "content": prompt},
        ],
        max_tokens=150,
        temperature=0.1,
        response_format={"type": "json_object"},
    )

    try:
        parsed = json.loads(result.content)
        return {
            "risk_level": parsed.get("risk_level", "safe"),
            "categories": parsed.get("categories", []),
            "matched_rules": [],
            "confidence": float(parsed.get("confidence", 0.5)),
        }
    except json.JSONDecodeError:
        return {"risk_level": "safe", "categories": [], "matched_rules": [], "confidence": 0.5}


# ── 图片审核 ─────────────────────────────────────────────

async def check_image(image_url: str, model_router: ModelRouter | None = None) -> dict:
    """
    图片审核。当前 Mock 实现 — 全部返回 safe。
    API Key 到位后接入多模态模型。
    """
    await logger.ainfo("image_moderation_mock", image_url=image_url)
    return {
        "risk_level": "safe",
        "categories": [],
        "confidence": 0.5,
        "note": "mock — 多模态审核待接入",
    }


# ── 人格审核 ─────────────────────────────────────────────

async def check_persona(
    persona_config: dict,
    agent_name: str = "",
    model_router: ModelRouter | None = None,
) -> dict:
    """
    审核用户自定义人格是否合规。
    规则级 + 可选 LLM 辅助。
    """
    all_text = " ".join(str(v) for v in persona_config.values() if isinstance(v, str))
    if agent_name:
        all_text += f" {agent_name}"

    matched = []
    for pattern in _PERSONA_FORBIDDEN:
        m = pattern.search(all_text)
        if m:
            matched.append(m.group())

    if matched:
        return {
            "risk_level": "block",
            "categories": _categorize_persona_matches(matched),
            "matched_rules": matched,
            "confidence": 1.0,
        }

    return {
        "risk_level": "safe",
        "categories": [],
        "matched_rules": [],
        "confidence": 0.9,
    }


# ── 辅助 ─────────────────────────────────────────────────

def _categorize_matches(matches: list[str]) -> list[str]:
    """根据匹配内容推断类别"""
    categories = set()
    text = " ".join(matches)
    if any(k in text for k in ["色情", "裸照", "性交", "做爱", "约炮", "招嫖"]):
        categories.add("pornography")
    if any(k in text for k in ["炸弹", "枪支", "自杀", "自残"]):
        categories.add("violence")
    if any(k in text for k in ["政府", "政权", "法轮", "六四"]):
        categories.add("political")
    if any(k in text for k in ["赌博", "毒品"]):
        categories.add("illegal")
    return list(categories)


def _categorize_persona_matches(matches: list[str]) -> list[str]:
    categories = set()
    text = " ".join(matches)
    if any(k in text for k in ["色情", "情色", "成人"]):
        categories.add("pornography")
    if any(k in text for k in ["暴力", "血腥", "恐怖"]):
        categories.add("violence")
    if any(k in text for k in ["歧视", "仇恨"]):
        categories.add("discrimination")
    if any(k in text for k in ["涉政", "反动", "颠覆"]):
        categories.add("political")
    if any(k in text for k in ["冒充", "扮演"]):
        categories.add("impersonation")
    if any(k in text for k in ["诈骗", "欺骗"]):
        categories.add("illegal")
    if any(k in text for k in ["赌博", "毒品"]):
        categories.add("illegal")
    return list(categories)

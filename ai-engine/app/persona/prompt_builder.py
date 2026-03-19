"""
AetherVerse AI Engine — 人格系统 / 系统提示词构建
Jinja2 模板渲染 + token 估算
"""

from __future__ import annotations

from pathlib import Path

import structlog
import yaml
from jinja2 import Environment, FileSystemLoader

from ..config import get_settings

logger = structlog.get_logger(__name__)

# ── Jinja2 环境 ──────────────────────────────────────────
_env: Environment | None = None


def get_jinja_env() -> Environment:
    global _env
    if _env is None:
        prompts_dir = Path(get_settings().PROMPTS_DIR)
        if not prompts_dir.is_absolute():
            # 相对于 ai-engine/ 根目录
            prompts_dir = Path(__file__).resolve().parent.parent / prompts_dir
        _env = Environment(
            loader=FileSystemLoader(str(prompts_dir)),
            autoescape=False,
            keep_trailing_newline=True,
        )
    return _env


# ── 系统智能体配置加载 ───────────────────────────────────

_system_agents: list[dict] | None = None


def load_system_agents() -> list[dict]:
    """加载 prompts/system_agents.yaml"""
    global _system_agents
    if _system_agents is not None:
        return _system_agents

    prompts_dir = Path(get_settings().PROMPTS_DIR)
    if not prompts_dir.is_absolute():
        prompts_dir = Path(__file__).resolve().parent.parent / prompts_dir
    agents_file = prompts_dir / "system_agents.yaml"

    with open(agents_file, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    _system_agents = data.get("system_agents", [])
    return _system_agents


# ── 提示词构建 ───────────────────────────────────────────

def build_system_prompt(
    persona_config: dict,
    memory_summary: str | None = None,
    scene: str = "room_chat",
) -> tuple[str, int]:
    """
    构建完整系统提示词。

    Args:
        persona_config: 人格配置 dict (personality, speaking_style, expertise, constraints)
        memory_summary: 近期记忆摘要（可选）
        scene: 场景 (room_chat / private_chat / creation)

    Returns:
        (system_prompt, estimated_token_count)
    """
    env = get_jinja_env()
    template = env.get_template("system_prompt.j2")

    prompt = template.render(
        persona=persona_config,
        memory_summary=memory_summary or "",
        scene=scene,
    )

    token_count = estimate_tokens(prompt)
    return prompt, token_count


def build_evaluate_prompt(
    agent_name: str,
    persona_summary: str,
    recent_messages: list[dict],
) -> str:
    """
    构建监听评估提示词（JSON 输出约束）。

    Args:
        agent_name: 智能体名称
        persona_summary: 人格摘要
        recent_messages: 最近消息列表 [{sender_name, sender_type, content}]

    Returns:
        评估用 user prompt
    """
    env = get_jinja_env()
    template = env.get_template("evaluate_prompt.j2")

    return template.render(
        agent_name=agent_name,
        persona_summary=persona_summary,
        recent_messages=recent_messages,
    )


# ── Token 估算 ───────────────────────────────────────────

def estimate_tokens(text: str) -> int:
    """
    粗估 token 数。
    中文约 1.5 字/token，英文约 4 字符/token。
    粗估公式: len(text) * 0.6 (按中英混合)
    """
    if not text:
        return 0
    # 统计中文字符占比来调整
    chinese_chars = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
    total_chars = len(text)
    if total_chars == 0:
        return 0
    chinese_ratio = chinese_chars / total_chars
    # 中文部分: 1.5 字/token → token = chinese_chars / 1.5
    # 英文部分: 4 字符/token → token = (total - chinese) / 4
    tokens = chinese_chars / 1.5 + (total_chars - chinese_chars) / 4
    return max(1, int(tokens))

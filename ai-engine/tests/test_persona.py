"""
测试 — 人格系统 (prompt_builder)
"""

import os
import pytest
from pathlib import Path

# 确保 prompts 目录可被找到
os.environ.setdefault("PROMPTS_DIR", str(Path(__file__).resolve().parent.parent / "prompts"))

from app.persona.prompt_builder import (
    build_evaluate_prompt,
    build_system_prompt,
    estimate_tokens,
    load_system_agents,
)


class TestBuildSystemPrompt:
    def test_basic_prompt(self):
        persona = {
            "name": "测试智能体",
            "personality": "友善温暖",
            "speaking_style": "轻松活泼",
            "expertise": "科技",
        }
        prompt, token_count = build_system_prompt(persona)
        assert "测试智能体" in prompt
        assert "友善温暖" in prompt
        assert "科技" in prompt
        assert token_count > 0

    def test_room_chat_scene(self):
        persona = {"name": "小星", "personality": "好奇"}
        prompt, _ = build_system_prompt(persona, scene="room_chat")
        assert "群聊房间" in prompt

    def test_private_chat_scene(self):
        persona = {"name": "小星", "personality": "好奇"}
        prompt, _ = build_system_prompt(persona, scene="private_chat")
        assert "私聊" in prompt

    def test_creation_scene(self):
        persona = {"name": "画龙", "personality": "创意"}
        prompt, _ = build_system_prompt(persona, scene="creation")
        assert "创作" in prompt

    def test_with_memory(self):
        persona = {"name": "知远", "personality": "理性"}
        prompt, _ = build_system_prompt(persona, memory_summary="上次讨论了量子计算")
        assert "量子计算" in prompt

    def test_without_optional_fields(self):
        persona = {"name": "简单智能体"}
        prompt, count = build_system_prompt(persona)
        assert "简单智能体" in prompt
        assert count > 0


class TestBuildEvaluatePrompt:
    def test_basic(self):
        prompt = build_evaluate_prompt(
            agent_name="小星",
            persona_summary="活泼好奇",
            recent_messages=[
                {"sender_name": "小明", "sender_type": "user", "content": "AI 画画好厉害"},
                {"sender_name": "小红", "sender_type": "user", "content": "确实很有趣"},
            ],
        )
        assert "小星" in prompt
        assert "AI 画画好厉害" in prompt
        assert "JSON" in prompt  # 输出约束为 JSON

    def test_empty_messages(self):
        prompt = build_evaluate_prompt("测试", "机器人", [])
        assert "测试" in prompt


class TestEstimateTokens:
    def test_chinese_text(self):
        tokens = estimate_tokens("你好世界")
        assert tokens > 0

    def test_english_text(self):
        tokens = estimate_tokens("hello world this is a test")
        assert tokens > 0

    def test_empty(self):
        assert estimate_tokens("") == 0

    def test_mixed(self):
        tokens = estimate_tokens("Hello 世界 this is AI 人工智能")
        assert tokens > 0


class TestLoadSystemAgents:
    def test_load(self):
        agents = load_system_agents()
        assert len(agents) == 5
        names = [a["name"] for a in agents]
        assert "小星" in names
        assert "墨问" in names
        assert "乐天" in names
        assert "知远" in names
        assert "画龙" in names

    def test_persona_fields(self):
        agents = load_system_agents()
        for agent in agents:
            assert "persona_config" in agent
            config = agent["persona_config"]
            assert "personality" in config
            assert "speaking_style" in config
            assert "expertise" in config

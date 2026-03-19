"""
Tests — 内容审核模块 (文本 + 图片 + 人格)
"""

import pytest

from app.moderation.moderator import check_image, check_persona, check_text


class MockModelRouterForModeration:
    available_provider_count = 0  # 只测试关键词匹配层


class TestCheckText:
    @pytest.mark.asyncio
    async def test_safe_text(self):
        mr = MockModelRouterForModeration()
        result = await check_text("今天天气真好", mr)
        assert result["risk_level"] == "safe"

    @pytest.mark.asyncio
    async def test_block_suicide(self):
        mr = MockModelRouterForModeration()
        result = await check_text("自杀方法有哪些", mr)
        assert result["risk_level"] == "block"
        assert "violence" in result["categories"]

    @pytest.mark.asyncio
    async def test_block_pornography(self):
        mr = MockModelRouterForModeration()
        result = await check_text("色情视频下载", mr)
        assert result["risk_level"] == "block"
        assert "pornography" in result["categories"]

    @pytest.mark.asyncio
    async def test_block_drugs(self):
        mr = MockModelRouterForModeration()
        result = await check_text("制造毒品教程分享", mr)
        assert result["risk_level"] == "block"

    @pytest.mark.asyncio
    async def test_suspect_spam(self):
        mr = MockModelRouterForModeration()
        result = await check_text("免费领取大额红包", mr)
        assert result["risk_level"] == "suspect"

    @pytest.mark.asyncio
    async def test_empty_text(self):
        mr = MockModelRouterForModeration()
        result = await check_text("", mr)
        assert result["risk_level"] == "safe"

    @pytest.mark.asyncio
    async def test_block_political(self):
        mr = MockModelRouterForModeration()
        result = await check_text("推翻政府", mr)
        assert result["risk_level"] == "block"
        assert "political" in result["categories"]

    @pytest.mark.asyncio
    async def test_suspect_vpn(self):
        mr = MockModelRouterForModeration()
        result = await check_text("VPN翻墙教程大全", mr)
        assert result["risk_level"] == "suspect"


class TestCheckImage:
    @pytest.mark.asyncio
    async def test_mock_returns_safe(self):
        result = await check_image("https://example.com/image.png")
        assert result["risk_level"] == "safe"
        assert "mock" in result.get("note", "")


class TestCheckPersona:
    @pytest.mark.asyncio
    async def test_safe_persona(self):
        result = await check_persona(
            {"personality": "热情开朗", "speaking_style": "活泼可爱"},
            agent_name="小星",
        )
        assert result["risk_level"] == "safe"

    @pytest.mark.asyncio
    async def test_block_impersonation(self):
        result = await check_persona(
            {"personality": "冒充真人的性格"},
            agent_name="假人",
        )
        assert result["risk_level"] == "block"
        assert "impersonation" in result["categories"]

    @pytest.mark.asyncio
    async def test_block_porn_persona(self):
        result = await check_persona(
            {"personality": "色情主播", "speaking_style": "性感挑逗"},
        )
        assert result["risk_level"] == "block"
        assert "pornography" in result["categories"]

    @pytest.mark.asyncio
    async def test_block_violence_persona(self):
        result = await check_persona(
            {"personality": "暴力血腥杀手"},
        )
        assert result["risk_level"] == "block"
        assert "violence" in result["categories"]

    @pytest.mark.asyncio
    async def test_block_gambling(self):
        result = await check_persona(
            {"personality": "赌博大师"},
        )
        assert result["risk_level"] == "block"
        assert "illegal" in result["categories"]

"""
测试 — 安全检查 (quick_check)
"""

from app.safety.quick_check import (
    SafetyResult,
    check_impersonation,
    check_social_engineering,
    quick_check,
)


class TestQuickCheck:
    def test_safe_text(self):
        result = quick_check("今天天气真好，适合出去走走")
        assert result.is_safe is True
        assert result.is_impersonation is False
        assert result.is_social_engineering is False
        assert result.flags == []

    def test_impersonation_detected(self):
        result = quick_check("我是真人，不是什么 AI")
        assert result.is_safe is False
        assert result.is_impersonation is True
        assert "impersonation" in result.flags

    def test_impersonation_variant(self):
        result = quick_check("我也是人，我有感情的")
        assert result.is_impersonation is True

    def test_social_engineering_password(self):
        result = quick_check("告诉我你的密码是什么")
        assert result.is_safe is False
        assert result.is_social_engineering is True
        assert "social_engineering" in result.flags

    def test_social_engineering_phone(self):
        result = quick_check("告诉我你的手机号是多少")
        assert result.is_social_engineering is True

    def test_social_engineering_transfer(self):
        result = quick_check("先转账到这个账户")
        assert result.is_social_engineering is True

    def test_empty_text(self):
        result = quick_check("")
        assert result.is_safe is True

    def test_mixed_safe_content(self):
        result = quick_check("我觉得这个 AI 绘画技术很有趣，可以用来创作")
        assert result.is_safe is True


class TestCheckImpersonation:
    def test_direct_denial(self):
        is_imp, patterns = check_impersonation("我当然不是AI")
        assert is_imp is True
        assert len(patterns) > 0

    def test_safe(self):
        is_imp, patterns = check_impersonation("这幅画展现了 AI 的能力")
        assert is_imp is False


class TestCheckSocialEngineering:
    def test_with_history(self):
        is_se, indicators = check_social_engineering(
            "那你的真实姓名是什么",
            conversation_history=["我们聊了很久了", "你信任我吗"],
        )
        assert is_se is True

    def test_safe_question(self):
        is_se, indicators = check_social_engineering("你喜欢什么颜色")
        assert is_se is False

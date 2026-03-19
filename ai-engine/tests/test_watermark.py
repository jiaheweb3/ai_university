"""
Tests — AIGC 数字水印 (LSB)
"""

import io
import json

import pytest
from PIL import Image

from app.aigc.watermark import embed_watermark, extract_watermark


def _create_test_image(width=100, height=100, color=(128, 128, 128)):
    """创建测试用纯色 PNG 图片"""
    img = Image.new("RGB", (width, height), color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class TestEmbedWatermark:
    def test_basic_embed(self):
        img_bytes = _create_test_image()
        metadata = {"content_id": "test-001", "model": "cogview-3", "provider": "zhipu"}

        result = embed_watermark(img_bytes, metadata)

        assert isinstance(result, bytes)
        assert len(result) > 0
        # 应该是 PNG 格式
        assert result[:4] == b"\x89PNG"

    def test_embed_preserves_dimensions(self):
        img_bytes = _create_test_image(200, 150)
        metadata = {"content_id": "test-002"}

        result = embed_watermark(img_bytes, metadata)

        # 读取结果图片验证尺寸
        img = Image.open(io.BytesIO(result))
        assert img.size == (200, 150)

    def test_embed_too_small_image(self):
        img_bytes = _create_test_image(2, 2)  # 只有 4 个像素 = 12 bit 容量
        metadata = {"content_id": "test-003", "data": "x" * 100}

        with pytest.raises(ValueError, match="too small"):
            embed_watermark(img_bytes, metadata)


class TestExtractWatermark:
    def test_roundtrip(self):
        """嵌入 → 提取 → 验证一致性"""
        img_bytes = _create_test_image()
        metadata = {
            "content_id": "uuid-123",
            "generated_at": "2026-03-19T10:00:00",
            "model": "cogview-3-plus",
            "provider": "zhipu",
        }

        watermarked = embed_watermark(img_bytes, metadata)
        extracted = extract_watermark(watermarked)

        assert extracted is not None
        assert extracted["content_id"] == "uuid-123"
        assert extracted["model"] == "cogview-3-plus"
        assert extracted["provider"] == "zhipu"

    def test_no_watermark(self):
        """无水印图片应返回 None"""
        img_bytes = _create_test_image()
        result = extract_watermark(img_bytes)
        assert result is None

    def test_chinese_metadata(self):
        """中文元数据"""
        img_bytes = _create_test_image(200, 200)
        metadata = {"content_id": "中文测试", "model": "国产模型"}

        watermarked = embed_watermark(img_bytes, metadata)
        extracted = extract_watermark(watermarked)

        assert extracted is not None
        assert extracted["content_id"] == "中文测试"
        assert extracted["model"] == "国产模型"

    def test_different_colors(self):
        """不同底色的图片"""
        for color in [(0, 0, 0), (255, 255, 255), (100, 200, 50)]:
            img_bytes = _create_test_image(color=color)
            metadata = {"content_id": f"color-{color[0]}"}

            watermarked = embed_watermark(img_bytes, metadata)
            extracted = extract_watermark(watermarked)

            assert extracted is not None
            assert extracted["content_id"] == f"color-{color[0]}"

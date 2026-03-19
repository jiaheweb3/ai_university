"""
AetherVerse AI Engine — AIGC 数字水印
基于 Pillow LSB (Least Significant Bit) 水印嵌入
"""

from __future__ import annotations

import io
import json
import struct
from datetime import datetime
from pathlib import Path

import structlog

logger = structlog.get_logger(__name__)

# 水印魔数标记
_WATERMARK_MAGIC = b"AVWM"  # AetherVerse WaterMark


def embed_watermark(image_bytes: bytes, metadata: dict) -> bytes:
    """
    在图片中嵌入不可见数字水印 (LSB)。

    Args:
        image_bytes: 原始图片字节
        metadata: 水印元数据 {content_id, generated_at, model, provider}

    Returns:
        嵌入水印后的图片字节 (PNG 格式)

    Warning:
        LSB 水印仅在无损格式 (PNG) 下可靠。如果后续链路将图片转码为
        JPEG 等有损格式，水印信息将完全丢失。请确保存储和分发环节
        保持 PNG 格式，或在 PNG tEXt chunk 中备份一份水印元数据。
    """
    from PIL import Image

    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    pixels = img.load()
    width, height = img.size

    # 序列化元数据
    meta_json = json.dumps(metadata, ensure_ascii=False, default=str).encode("utf-8")
    payload = _WATERMARK_MAGIC + struct.pack(">I", len(meta_json)) + meta_json

    # 检查图片容量
    max_bits = width * height * 3  # RGB 每通道 1 bit
    required_bits = len(payload) * 8
    if required_bits > max_bits:
        raise ValueError(f"Image too small for watermark: need {required_bits} bits, have {max_bits}")

    # 嵌入 — 修改每个像素 RGB 通道最低位
    bit_index = 0
    total_bits = len(payload) * 8

    for y in range(height):
        for x in range(width):
            if bit_index >= total_bits:
                break
            r, g, b = pixels[x, y]
            new_rgb = []
            for channel in (r, g, b):
                if bit_index < total_bits:
                    byte_idx = bit_index // 8
                    bit_pos = 7 - (bit_index % 8)
                    bit_val = (payload[byte_idx] >> bit_pos) & 1
                    new_channel = (channel & 0xFE) | bit_val
                    new_rgb.append(new_channel)
                    bit_index += 1
                else:
                    new_rgb.append(channel)
            pixels[x, y] = tuple(new_rgb)
        if bit_index >= total_bits:
            break

    # 输出 PNG
    output = io.BytesIO()
    img.save(output, format="PNG")
    return output.getvalue()


def extract_watermark(image_bytes: bytes) -> dict | None:
    """
    从图片中提取数字水印。

    Returns:
        水印元数据，提取失败返回 None
    """
    from PIL import Image

    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    pixels = img.load()
    width, height = img.size

    # 先提取魔数 + 长度 (4 + 4 = 8 bytes = 64 bits)
    header_bytes = _extract_bits(pixels, width, height, 0, 64)

    if header_bytes[:4] != _WATERMARK_MAGIC:
        return None

    meta_len = struct.unpack(">I", header_bytes[4:8])[0]
    if meta_len > 10000:  # 防止异常大小
        return None

    # 提取元数据
    total_header_bits = 64
    meta_bytes = _extract_bits(pixels, width, height, total_header_bits, meta_len * 8)

    try:
        return json.loads(meta_bytes.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


def _extract_bits(pixels, width: int, height: int, start_bit: int, num_bits: int) -> bytes:
    """从像素 LSB 提取指定范围的比特"""
    result_bits = []
    bit_index = 0
    target_end = start_bit + num_bits

    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            for channel in (r, g, b):
                if bit_index >= start_bit and bit_index < target_end:
                    result_bits.append(channel & 1)
                bit_index += 1
                if bit_index >= target_end:
                    break
            if bit_index >= target_end:
                break
        if bit_index >= target_end:
            break

    # bits → bytes
    result = bytearray()
    for i in range(0, len(result_bits), 8):
        byte_val = 0
        for j in range(8):
            if i + j < len(result_bits):
                byte_val = (byte_val << 1) | result_bits[i + j]
            else:
                byte_val <<= 1
        result.append(byte_val)
    return bytes(result)

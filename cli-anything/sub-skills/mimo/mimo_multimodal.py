#!/usr/bin/env python3
"""
mimo_multimodal.py — Xiaomi MiMo 多模态理解 CLI 封装
支持图片理解、音频理解、视频理解
"""

import argparse
import base64
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

try:
    from openai import OpenAI
except ImportError:
    print("ERROR: pip install openai", file=sys.stderr)
    sys.exit(1)

# ─── 配置 ───────────────────────────────────────────
DEFAULT_BASE_URL = "https://token-plan-cn.xiaomimimo.com/v1"
DEFAULT_MODEL = "mimo-v2.5"
DEFAULT_MAX_TOKENS = 1024

# ─── 格式白名单 ─────────────────────────────────────
IMAGE_FORMATS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
AUDIO_FORMATS = {".mp3", ".wav", ".flac", ".m4a", ".ogg"}
VIDEO_FORMATS = {".mp4", ".mov", ".avi", ".wmv"}

MIME_MAP = {
    ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
    ".gif": "image/gif", ".webp": "image/webp", ".bmp": "image/bmp",
    ".mp3": "audio/mpeg", ".wav": "audio/wav", ".flac": "audio/flac",
    ".m4a": "audio/mp4", ".ogg": "audio/ogg",
    ".mp4": "video/mp4", ".mov": "video/quicktime",
    ".avi": "video/x-msvideo", ".wmv": "video/x-ms-wmv",
}


def get_mime(path: str) -> str:
    ext = Path(path).suffix.lower()
    return MIME_MAP.get(ext, "application/octet-stream")


def is_url(s: str) -> bool:
    return urlparse(s).scheme in ("http", "https")


def file_to_base64_data_uri(path: str) -> str:
    mime = get_mime(path)
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return f"data:{mime};base64,{b64}"


def resolve_input(source: str) -> str:
    """本地文件 → base64 data URI; URL → 原样返回"""
    if is_url(source):
        return source
    p = Path(source).expanduser().resolve()
    if not p.exists():
        print(f"ERROR: 文件不存在: {source}", file=sys.stderr)
        sys.exit(1)
    return file_to_base64_data_uri(str(p))


def detect_media_type(source: str) -> str:
    """根据文件扩展名或 URL 判断 media type"""
    if is_url(source):
        path = urlparse(source).path
    else:
        path = source
    ext = Path(path).suffix.lower()
    if ext in IMAGE_FORMATS:
        return "image"
    if ext in AUDIO_FORMATS:
        return "audio"
    if ext in VIDEO_FORMATS:
        return "video"
    # 兜底：猜 image
    return "image"


def build_content(source: str, media_type: str, prompt: str, fps: float = 2.0, media_resolution: str = "default") -> list:
    """构造 OpenAI 兼容的 messages content"""
    resolved = resolve_input(source)

    if media_type == "image":
        if is_url(resolved):
            part = {"type": "image_url", "image_url": {"url": resolved}}
        else:
            part = {"type": "image_url", "image_url": {"url": resolved}}
    elif media_type == "audio":
        part = {"type": "input_audio", "input_audio": {"data": resolved}}
    elif media_type == "video":
        part = {
            "type": "video_url",
            "video_url": {"url": resolved},
            "fps": fps,
            "media_resolution": media_resolution,
        }
    else:
        print(f"ERROR: 不支持的媒体类型: {media_type}", file=sys.stderr)
        sys.exit(1)

    return [part, {"type": "text", "text": prompt}]


def call_mimo(content: list, model: str, max_tokens: int, api_key: str, base_url: str) -> dict:
    """调用 MiMo API"""
    client = OpenAI(api_key=api_key, base_url=base_url)
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are MiMo, an AI assistant developed by Xiaomi."},
            {"role": "user", "content": content},
        ],
        max_completion_tokens=max_tokens,
    )
    return completion.model_dump()


def format_output(result: dict, fmt: str) -> str:
    msg = result.get("choices", [{}])[0].get("message", {})
    content = msg.get("content", "")
    reasoning = msg.get("reasoning_content", "")

    if fmt == "json":
        return json.dumps(result, ensure_ascii=False, indent=2)

    # text 格式
    parts = []
    if content:
        parts.append(content)
    if reasoning:
        parts.append(f"\n---\nReasoning:\n{reasoning}")

    usage = result.get("usage", {})
    if usage:
        prompt_t = usage.get("prompt_tokens", 0)
        comp_t = usage.get("completion_tokens", 0)
        total_t = usage.get("total_tokens", 0)
        parts.append(f"\n---\nTokens: prompt={prompt_t}, completion={comp_t}, total={total_t}")

    return "\n".join(parts) if parts else "(空响应)"


def main():
    parser = argparse.ArgumentParser(description="MiMo 多模态理解 CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    # ─── 公共参数 ───────────────────────────────────
    def add_common(p):
        p.add_argument("source", help="图片/音频/视频 文件路径或 URL")
        p.add_argument("-p", "--prompt", default="请描述这个内容", help="提示词")
        p.add_argument("-m", "--model", default=DEFAULT_MODEL, help="模型名")
        p.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS)
        p.add_argument("--api-key", default=os.environ.get("MIMO_API_KEY", ""))
        p.add_argument("--base-url", default=os.environ.get("MIMO_BASE_URL", DEFAULT_BASE_URL))
        p.add_argument("--json", action="store_true", help="JSON 输出")

    # image
    img = sub.add_parser("image", help="图片理解")
    add_common(img)

    # audio
    aud = sub.add_parser("audio", help="音频理解")
    add_common(aud)

    # video
    vid = sub.add_parser("video", help="视频理解")
    add_common(vid)
    vid.add_argument("--fps", type=float, default=2.0, help="抽帧率 (0.1-10)")
    vid.add_argument("--resolution", choices=["default", "max"], default="default", help="分辨率级别")

    # auto (自动检测)
    auto = sub.add_parser("auto", help="自动检测媒体类型")
    add_common(auto)
    auto.add_argument("--fps", type=float, default=2.0)
    auto.add_argument("--resolution", choices=["default", "max"], default="default")

    args = parser.parse_args()

    if not args.api_key:
        print("ERROR: 需要 MIMO_API_KEY 环境变量或 --api-key 参数", file=sys.stderr)
        sys.exit(1)

    # 确定媒体类型
    media_map = {"image": "image", "audio": "audio", "video": "video", "auto": None}
    media_type = media_map[args.command]
    if media_type is None:
        media_type = detect_media_type(args.source)

    fps = getattr(args, "fps", 2.0)
    resolution = getattr(args, "resolution", "default")

    content = build_content(args.source, media_type, args.prompt, fps, resolution)
    result = call_mimo(content, args.model, args.max_tokens, args.api_key, args.base_url)

    fmt = "json" if args.json else "text"
    print(format_output(result, fmt))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""多模态输入的共享编解码 —— llama_chat.py 与 llama_batch.py 共用。

llama-server 的 /v1/chat/completions 接受 OpenAI 格式的多模态 content：

    图像  {"type": "image_url",  "image_url":   {"url": "data:<mime>;base64,<B64>"}}
    音频  {"type": "input_audio", "input_audio": {"data": "<B64>", "format": "wav"}}

⚠️ 音频输入在 llama.cpp 里被标为 highly experimental。大文件出问题时，退路是
   启动 server 时加 --no-mmproj-offload（音频编码器退回 CPU）。

没有媒体时 build_content 返回**纯字符串**，保持与旧调用方的行为一致 —— 这样
给 llama_chat.py / llama_batch.py 加多模态支持不会改变任何现有纯文本用法。
"""
import base64
import os

# 覆盖 llama-server 实际能解的图片格式；其余一律显式报错，不静默发出去
IMAGE_MIME = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".bmp": "image/bmp",
}

# 音频白名单：与图片同一条家规 —— 不在表里就显式报错，别把 .m4a/.flac 原样
# 送到 server 再吃一个不可读的失败。本机 asr 素材链路只实测过 wav（meeting.wav），
# mp3/flac/m4a 是 llama-server 文档声称支持的常见容器，进来仍以 server 实际解不了为准。
AUDIO_FORMATS = {"wav", "mp3", "flac", "m4a"}


def encode_file(path: str) -> str:
    """读文件并 base64 编码。读不了直接抛，由调用方决定怎么记（单条失败还是整批退出）。"""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


def _image_part(path: str) -> dict:
    ext = os.path.splitext(path)[1].lower()
    mime = IMAGE_MIME.get(ext)
    if not mime:
        raise ValueError(
            f"不支持的图片格式：{path}（支持 {', '.join(sorted(IMAGE_MIME))}）")
    return {"type": "image_url",
            "image_url": {"url": f"data:{mime};base64,{encode_file(path)}"}}


def _audio_part(path: str) -> dict:
    fmt = os.path.splitext(path)[1].lower().lstrip(".")
    if not fmt:
        raise ValueError(f"音频文件缺少扩展名，无法判断格式：{path}")
    if fmt not in AUDIO_FORMATS:
        raise ValueError(
            f"不支持的音频格式：{path}（支持 {', '.join(sorted(AUDIO_FORMATS))}；"
            f"其他格式先用 ffmpeg 转成 wav）")
    return {"type": "input_audio",
            "input_audio": {"data": encode_file(path), "format": fmt}}


def build_content(prompt: str, images=None, audio=None):
    """构造 user message 的 content。

    无媒体 → 纯字符串（与旧版逐字一致）；有媒体 → OpenAI 多模态 content 数组。
    images 接受 str 或 list[str] —— 批量场景 JSONL 里写单个字符串更省事。
    """
    imgs = [images] if isinstance(images, str) else list(images or [])
    if not imgs and not audio:
        return prompt
    parts = [{"type": "text", "text": prompt}]
    parts += [_image_part(p) for p in imgs]
    if audio:
        parts.append(_audio_part(audio))
    return parts

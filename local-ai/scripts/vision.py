#!/usr/bin/env python3
"""qwen2.5vl:3b 本地视觉理解（走 Ollama API）。

为什么需要脚本：IPEX-LLM 版 Ollama 的 `ollama run` 命令不支持 `--images` flag，
本地看图/OCR 只能走 API（/api/generate + base64 图片）。

用法：
    py -3 vision.py <图片路径> [提示词]
默认提示词：描述这张图片的内容
"""
import base64
import json
import os
import sys
import time
import urllib.request


def main() -> None:
    if len(sys.argv) < 2:
        print("用法: py -3 vision.py <图片路径> [提示词]", file=sys.stderr)
        sys.exit(1)
    img_path = sys.argv[1]
    prompt = sys.argv[2] if len(sys.argv) > 2 else "描述这张图片的内容"
    if not os.path.exists(img_path):
        print(f"[错误] 图片不存在: {img_path}", file=sys.stderr)
        sys.exit(1)

    b64 = base64.b64encode(open(img_path, "rb").read()).decode()
    payload = json.dumps(
        {"model": "qwen2.5vl:3b", "prompt": prompt, "images": [b64], "stream": False}
    ).encode()
    req = urllib.request.Request(
        "http://127.0.0.1:11434/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    t = time.time()
    resp = json.load(urllib.request.urlopen(req, timeout=120))
    text = resp.get("response", "")
    print(text if text else "(无输出，检查 Ollama 服务是否启动)")
    print(f"\n[耗时 {time.time() - t:.1f}s]", file=sys.stderr)


if __name__ == "__main__":
    main()

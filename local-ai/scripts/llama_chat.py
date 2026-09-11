#!/usr/bin/env python3
"""本地 LLM 对话 —— 走 llama-server (CUDA GPU)。

用法:
    py -3 llama_chat.py "你的问题"                # 默认开启思考
    py -3 llama_chat.py --no-think "改一下这句话"   # 关思考，省 token / 更快
    py -3 llama_chat.py --image photo.jpg "图里有什么"       # 视觉（需先 start.sh vl4）
    py -3 llama_chat.py --audio meeting.wav "转写并分段落"    # 语音（需先 start.sh asr）

模型由 llama-server 启动时决定（客户端不能切换）:
    minicpm - MiniCPM5-2B Q8_0，纯文本 2.6B，128K ctx，轻量任务，~85-107 tok/s
    9b      - Qwen3.8-9B-Distill Q4_K_M，代码/推理主力，32K ctx，~55 tok/s

先启动 llama-server (CUDA, 本机 RTX 5060 Laptop / 8GB VRAM):
    bash C:/Users/caill/.claude/skills/local-ai/scripts/start.sh minicpm

思考控制 —— 走请求级参数（重要）:
    两个模型都是 thinking 模型。默认**开启思考**（本机主要用途是跑 pi coding agent
    这类需要推理的活）；简单任务加 --no-think，请求体里会带
    "chat_template_kwargs": {"enable_thinking": false}，实测能省 90%+ token
    （同一改写请求：关思考 8 tokens / 开思考 158~300 tokens）。

    ⚠️ 这件事**只能**在请求级做。server 启动参数 --reasoning off /
    --reasoning-budget 0 / --chat-template-kwargs '{"enable_thinking":false}'
    在本机 build (b10883) 上**全部实测失效**——llama.cpp 上游 bug
    （PR #22336「respect per-request enable_thinking toggle」至今 OPEN 未合并），
    连 --chat-template / --chat-template-file 覆盖模板也不生效。
    换 build 前请先复测，不要假设"新版本就好了"。

    注：第三方客户端（如 pi）不发 chat_template_kwargs，模板变量未定义，
    模型按自身默认行为走 —— 实测就是**思考开启**，正好符合 agent 场景。

本机一律走 GPU，不提供 CPU 降级 —— 静默退回 CPU 会让速度掉 10 倍还不报错。
server 连不上时见 SKILL.md「GPU 生效判定」一节排障。
"""
import os
import argparse
import json
import sys
import time
import urllib.request

import llama_media

SERVER_URL = "http://127.0.0.1:8080/v1/chat/completions"


def _pick_text(message: dict) -> str:
    """取正文；content 为空时回落到 reasoning_content（thinking 模型可能把内容
    全放进推理字段，尤其在 max_tokens 被思考吃光时）。"""
    return (message.get("content") or "").strip() or \
           (message.get("reasoning_content") or "").strip()


def chat_with_server(prompt: str, system: str = None, max_tokens: int = 512,
                     temperature: float = 0.7, enable_think: bool = True,
                     images=None, audio=None) -> str:
    """通过 llama-server API 对话（CUDA GPU）。"""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    # 无媒体时 build_content 返回纯字符串，行为与加多模态之前完全一致
    messages.append({"role": "user",
                     "content": llama_media.build_content(prompt, images, audio)})

    payload = json.dumps({
        "model": "local",
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        # 思考开关：必须走请求级 chat_template_kwargs，理由见模块 docstring
        "chat_template_kwargs": {"enable_thinking": bool(enable_think)},
    }).encode("utf-8")

    req = urllib.request.Request(
        SERVER_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
    )

    t = time.time()
    try:
        resp = json.load(urllib.request.urlopen(req, timeout=300))
    except Exception as e:
        print(f"[错误] 连不上 llama-server: {e}\n"
              f"  请先启动（GPU）：bash C:/Users/caill/.claude/skills/local-ai/scripts/start.sh minicpm\n"
              f"  或 Windows CMD：  start.bat minicpm", file=sys.stderr)
        sys.exit(1)

    elapsed = time.time() - t
    text = _pick_text(resp["choices"][0]["message"])
    tokens = resp.get("usage", {}).get("completion_tokens", 0)
    print(f"\n[GPU {elapsed:.1f}s | {tokens/elapsed:.1f} tok/s | "
          f"thinking={'on' if enable_think else 'off'}]", file=sys.stderr)
    return text


def main() -> None:
    # Windows 下统一 stdout/stderr 为 UTF-8，避免中文在 GBK 终端乱码
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="本地 LLM 对话（llama-server / CUDA GPU）")
    parser.add_argument("prompt", help="输入提示词")
    parser.add_argument("-s", "--system", help="系统提示词")
    parser.add_argument("-n", "--max-tokens", type=int, default=512, help="最大生成 token 数")
    parser.add_argument("-t", "--temperature", type=float, default=0.7, help="温度")
    parser.add_argument("--no-think", action="store_true",
                        help="关闭思考（默认开启）；简单改写/分类/抽取用它能省 90%% token")
    parser.add_argument("--image", action="append", metavar="PATH",
                        help="图片路径，可重复指定多张（需 server 跑着 vl4/vl8）")
    parser.add_argument("--audio", metavar="PATH",
                        help="音频路径（需 server 跑着 asr）")

    args = parser.parse_args()

    try:
        print(chat_with_server(args.prompt, args.system, args.max_tokens,
                               args.temperature, not args.no_think,
                               images=args.image, audio=args.audio))
    except (OSError, ValueError) as e:
        sys.exit(f"[错误] 读取媒体文件失败：{e}")


if __name__ == "__main__":
    main()

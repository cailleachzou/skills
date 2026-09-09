#!/usr/bin/env python3
"""本地 LLM 对话 —— 优先 llama-server (CUDA GPU)，回退 llama-cpp-python (CPU)。

用法:
    py -3 llama_chat.py "你的问题"
    py -3 llama_chat.py -m qwen2.5:14b "更复杂的问题"

模型 (llama-server 需已加载对应模型):
    qwen2.5:7b   - Qwen2.5 7B Q4_K_M，整卡进 GPU，中文主力
    qwen2.5:14b  - Qwen2.5 14B Q4_K_M，复杂推理/长文，需 -ngl 部分 offload

先启动 llama-server (CUDA, 本机 RTX 5060 Laptop / 8GB VRAM):
    cd C:\\Users\\caill\\tools\\llama-cpp\\cuda
    llama-server.exe -m D:\\models\\gguf\\qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf -ngl 99 --host 127.0.0.1 --port 8080 -c 2048

CPU 回退: 需 `pip install llama-cpp-python`；不想装时可用 `llama-server -ngl 0` 实现纯 CPU。
"""
import argparse
import json
import os
import sys
import time
import urllib.request

SERVER_URL = "http://127.0.0.1:8080/v1/chat/completions"

# GGUF 模型名 -> 绝对路径（分片 GGUF 传第一个分片，自动加载同目录同系列其余分片）
GGUF_MODELS = {
    "qwen2.5:7b": r"D:\models\gguf\qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf",
    "qwen2.5:14b": r"D:\models\gguf\qwen2.5-14b-instruct-q4_k_m-00001-of-00003.gguf",
}
DEFAULT_MODEL = "qwen2.5:7b"
N_CPU_THREADS = 16  # Ryzen 9 8945HX 物理核心数（CPU 回退用）


def chat_with_server(prompt: str, system: str = None,
                     max_tokens: int = 512, temperature: float = 0.7) -> str:
    """通过 llama-server API 对话（CUDA GPU）。"""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = json.dumps({
        "model": "local",
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }).encode("utf-8")

    req = urllib.request.Request(
        SERVER_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
    )

    t = time.time()
    try:
        resp = json.load(urllib.request.urlopen(req, timeout=120))
        elapsed = time.time() - t
        text = resp["choices"][0]["message"]["content"].strip()
        tokens = resp.get("usage", {}).get("completion_tokens", 0)
        print(f"\n[GPU {elapsed:.1f}s | {tokens/elapsed:.1f} tok/s]", file=sys.stderr)
        return text
    except Exception as e:
        print(f"[警告] llama-server 不可用: {e}", file=sys.stderr)
        return None


def chat_with_llama_cpp(prompt: str, model_name: str = DEFAULT_MODEL, system: str = None,
                        max_tokens: int = 512, temperature: float = 0.7) -> str:
    """通过 llama-cpp-python 对话（CPU 备用）。"""
    try:
        from llama_cpp import Llama
    except ImportError:
        print("[错误] 未安装 llama-cpp-python，CPU 回退不可用。\n"
              "  方案1: pip install llama-cpp-python\n"
              "  方案2: 用 llama-server -ngl 0 跑纯 CPU 推理", file=sys.stderr)
        sys.exit(1)

    model_path = GGUF_MODELS.get(model_name, model_name)
    if not os.path.exists(model_path):
        print(f"[错误] 模型不存在: {model_path}", file=sys.stderr)
        sys.exit(1)

    t = time.time()
    llm = Llama(
        model_path=model_path,
        n_gpu_layers=0,  # CPU
        n_ctx=2048,
        n_threads=N_CPU_THREADS,
        n_threads_batch=N_CPU_THREADS,
        chat_format="chatml",
        verbose=False,
    )
    load_time = time.time() - t

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    t = time.time()
    result = llm.create_chat_completion(
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    gen_time = time.time() - t

    text = result["choices"][0]["message"]["content"].strip()
    tokens = result.get("usage", {}).get("completion_tokens", 0)

    print(f"\n[CPU {load_time:.1f}s加载 + {gen_time:.1f}s | {tokens/gen_time:.1f} tok/s]", file=sys.stderr)
    return text


def main() -> None:
    # Windows 下统一 stdout/stderr 为 UTF-8，避免中文在 GBK 终端乱码
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="本地 LLM 对话")
    parser.add_argument("prompt", help="输入提示词")
    parser.add_argument("-m", "--model", default=DEFAULT_MODEL, help=f"模型名 (默认: {DEFAULT_MODEL})")
    parser.add_argument("-s", "--system", help="系统提示词")
    parser.add_argument("-n", "--max-tokens", type=int, default=512, help="最大生成 token 数")
    parser.add_argument("-t", "--temperature", type=float, default=0.7, help="温度")
    parser.add_argument("--cpu", action="store_true", help="强制使用 CPU")

    args = parser.parse_args()

    # 优先 GPU (llama-server)
    if not args.cpu:
        result = chat_with_server(args.prompt, args.system, args.max_tokens, args.temperature)
        if result:
            print(result)
            return

    # CPU 回退
    result = chat_with_llama_cpp(args.prompt, args.model, args.system,
                                 args.max_tokens, args.temperature)
    print(result)


if __name__ == "__main__":
    main()

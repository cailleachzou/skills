#!/usr/bin/env python3
"""本地 LLM 对话 —— 优先 llama-server Vulkan GPU，回退 llama-cpp-python CPU。

用法:
    py -3 llama_chat.py "你的问题"
    py -3 llama_chat.py -m phi4-mini "把这段话改写成更正式的语气：..."

支持的模型 (llama-server 已加载的模型):
    qwen2.5:7b  - Qwen2.5 7B (中文最强, ~61 tok/s)
    lfm2.5      - LiquidAI LFM2.5-2.6B (英文最快, ~120 tok/s)
    phi4-mini   - Microsoft Phi-4 Mini (英文/代码)
    llama3      - Meta Llama 3 8B

需要先启动 llama-server:
    cd C:\\Users\\caill\\tools\\llama-cpp\\vulkan
    llama-server.exe -m <GGUF路径> -ngl 99 --host 127.0.0.1 --port 8080 -c 2048
"""
import argparse
import json
import os
import sys
import time
import urllib.request

SERVER_URL = "http://127.0.0.1:8080/v1/chat/completions"

# 模型名 -> GGUF blob 文件名映射（用于 CPU 回退）
OLLAMA_MODELS = {
    "lfm2.5": "sha256-79fdf00351b46cf26f020aead28d01889886be87c55fa0eb907e6f9b00bfee14",
    "phi4-mini": "sha256-4a770663d4551fb217658be33bbd71426ec9efa91233b0e6ab5d48fdcfb593ed",
    "qwen2.5:7b": "sha256-2bada8a7450677000f678be90653b85d364de7db25eb5ea54136ada5f3933730",
    "llama3": "sha256-6a0746a1ec1aef3e7ec53868f220ff6e389f6f8ef87a01d77c96807de94ca2aa",
}

BLOBS_DIR = r"C:\Users\caill\.ollama\models\blobs"
DEFAULT_MODEL = "qwen2.5:7b"


def chat_with_server(prompt: str, system: str = None,
                     max_tokens: int = 512, temperature: float = 0.7) -> str:
    """通过 llama-server API 对话（Vulkan GPU）。"""
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
    from llama_cpp import Llama
    
    blob_name = OLLAMA_MODELS.get(model_name, model_name)
    model_path = os.path.join(BLOBS_DIR, blob_name)
    if not os.path.exists(model_path):
        print(f"[错误] 模型不存在: {model_path}", file=sys.stderr)
        sys.exit(1)
    
    t = time.time()
    llm = Llama(
        model_path=model_path,
        n_gpu_layers=0,  # CPU
        verbose=False,
        n_ctx=2048,
        n_threads=12,
        n_threads_batch=12,
    )
    load_time = time.time() - t
    
    if system:
        full_prompt = f"<|system|>\n{system}\n<|user|>\n{prompt}\n<|assistant|>\n"
    else:
        full_prompt = f"<|user|>\n{prompt}\n<|assistant|>\n"
    
    t = time.time()
    result = llm(
        full_prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        stop=["<|user|>", "<|end|>", "<|assistant|>", "<|/assistant|>", "<|/user|>", "\n\n"],
    )
    gen_time = time.time() - t
    
    text = result["choices"][0]["text"].strip()
    for stop_word in ["<|assistant|>", "<|end|>", "<|user|>", "<|/assistant|>", "<|/user|>"]:
        if stop_word in text:
            text = text[:text.index(stop_word)].strip()
    tokens = result["usage"]["completion_tokens"]
    
    print(f"\n[CPU {load_time:.1f}s加载 + {gen_time:.1f}s | {tokens/gen_time:.1f} tok/s]", file=sys.stderr)
    return text


def main() -> None:
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

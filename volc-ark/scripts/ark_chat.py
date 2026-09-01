# -*- coding: utf-8 -*-
"""火山方舟 Ark 云端模型调用（豆包/DeepSeek/GLM/Kimi）
用法:
  py -3 ark_chat.py "问题"
  py -3 ark_chat.py glm5 "问题"            # 指定模型别名
  py -3 ark_chat.py --models              # 列出可用模型
密钥: 环境变量 ARK_API_KEY（setx ARK_API_KEY ...）
"""
import json, os, sys, urllib.request, urllib.error

KEY = os.environ.get("ARK_API_KEY", "")
BASE = "https://ark.cn-beijing.volces.com/api/v3"

MODELS = {
    "ds-pro":     "deepseek-v4-pro-ga-260813",    # DeepSeek V4 Pro GA，1M 上下文（默认）
    "ds-flash":   "deepseek-v4-flash-ga-260731",  # DeepSeek V4 Flash GA，1M 上下文
    "ds-pro-0425":"deepseek-v4-pro-260425",       # DeepSeek V4 Pro（旧版）
    "ds-flash-0425":"deepseek-v4-flash-260425",   # DeepSeek V4 Flash（旧版）
    "glm5":       "glm-5-2-260617",               # GLM 5.2，1M 上下文
    "seed-pro":   "doubao-seed-2-1-pro-260628",   # 豆包 Seed 2.1 Pro，VLM
    "seed-turbo": "doubao-seed-2-1-turbo-260628", # 豆包 Seed 2.1 Turbo，VLM
    "seed2-pro":  "doubao-seed-2-0-pro-260215",   # 豆包 Seed 2.0 Pro，VLM
    "seed-lite":  "doubao-seed-2-0-lite-260428",  # 豆包 Seed 2.0 Lite，VLM+音频
    "seed-mini":  "doubao-seed-2-0-mini-260428",  # 豆包 Seed 2.0 Mini，VLM+音频
    "seed-flash": "doubao-seed-1-6-flash-250828", # 豆包 Seed 1.6 Flash，VLM
    "character":  "doubao-seed-character-260628", # 豆包 Seed Character，角色扮演
    "evolving":   "doubao-seed-evolving",          # Doubao Seed Evolving，1M 上下文 VLM 动态版
}
DEFAULT = "deepseek-v4-pro-ga-260813"

def chat(model: str, prompt: str, max_tokens: int = 1024, temperature: float = 0.7):
    if not KEY:
        return "错误: 未设置环境变量 ARK_API_KEY"
    payload = {"model": model, "messages": [{"role": "user", "content": prompt}],
               "max_tokens": max_tokens, "temperature": temperature}
    req = urllib.request.Request(
        f"{BASE}/chat/completions",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json"},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return json.loads(r.read().decode("utf-8"))["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        return f"HTTP {e.code}: {e.read().decode('utf-8')[:300]}"

if __name__ == "__main__":
    args = sys.argv[1:]
    if "--models" in args:
        for alias, mid in MODELS.items():
            print(f"{alias:10s} {mid}")
        sys.exit(0)
    model = DEFAULT
    if args and args[0] in MODELS:
        model = MODELS[args.pop(0)]
    elif args and "." in args[0] and "-" in args[0]:
        model = args.pop(0)  # 直接传完整模型 ID
    prompt = " ".join(args) if args else "你好"
    print(chat(model, prompt))

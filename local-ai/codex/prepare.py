"""为 codex 准备 llama.cpp 侧的两样东西：codex 兼容 chat 模板、模型目录 JSON。

为什么需要模板补丁
------------------
codex 0.154 只讲 OpenAI **Responses API**（`wire_api = "chat"` 已被移除），
而 llama-server 内置 `OpenAI Responses -> OpenAI Chat Completions` 转换层，
所以协议本身是通的。问题出在消息角色上：

  codex 一次请求里既有顶层 `instructions`，又有一条 `developer` 消息，
  两者都被 llama-server 转成 system 角色 → 消息列表以**两条 system 开头**。

Qwen3.8 的原版模板对「system 不在 loop.first」直接 raise：

    {%- if message.role == "system" %}
        {%- if not loop.first %}
            {{- raise_exception('System message must be at the beginning.') }}

于是**每一个** codex 请求都 HTTP 500。实测（2026-09-26，build b10883）：

  instructions + developer + user  →  500 System message must be at the beginning.
  instructions + user              →  OK
  developer + user                 →  OK

补丁只做一件事：把**所有** system 消息合并进模板本来就会输出的那一块 system，
并去掉位置断言。工具调用解析、thinking 标签、其余渲染路径逐字未动。
单 system 的客户端（llama_chat.py / pi 等）下这是 no-op。

⚠️ MiniCPM5-2B 的模板**没有**这个断言（它把非首个 system 直接渲染出来），
   所以不需要补丁 —— `patch_template()` 认不出锚点时会如实报「无需补丁」。

关于模型目录
------------
`model_catalog_json` 是**整体替换**，不是合并：设了它，内置的 GPT-5.x/6 全部消失。
所以生成的目录只能挂到 profile（`codex -p local`）上，绝不能进全局 config.toml。
"""
import argparse
import json
import os
import struct
import subprocess
import sys
from pathlib import Path

# GGUF 元数据类型
_SCALAR = {0: "<B", 1: "<b", 2: "<H", 3: "<h", 4: "<I", 5: "<i",
           6: "<f", 7: "<B", 10: "<Q", 11: "<q", 12: "<d"}
_STRING, _ARRAY = 8, 9

# 与 scripts/start.sh 的模型表保持一致（start.sh 是唯一权威，这里只读它的路径）
MODELS = {
    "9b": os.environ.get("MODEL_9B", "D:/models/gguf/qwen3.8-9b-distill/Qwen3.8-9B-Q4_K_M.gguf"),
    "minicpm": os.environ.get("MODEL_MINICPM", "D:/models/gguf/minicpm5-2b/MiniCPM5-2B-Q8_0.gguf"),
}

# 模型目录条目：slug 必须与 `codex -m` / local.config.toml 里的 model 一致
CATALOG_MODELS = [
    {"slug": "qwen3.8-9b-distill", "display_name": "Qwen3.8-9B-Distill (local)",
     "description": "本机 llama.cpp，64K ctx，偏代码的 9B。",
     "context_window": 65536, "max_context_window": 65536},
    {"slug": "minicpm5-2b", "display_name": "MiniCPM5-2B (local)",
     "description": "本机 llama.cpp，128K ctx，快但弱。",
     "context_window": 131072, "max_context_window": 131072},
]

# 相对内置 GPT 条目需要改写的字段，以及为什么
CATALOG_OVERRIDES = {
    # llama.cpp 没有 Responses "lite" 形态，也没有 OpenAI 专有工具
    "use_responses_lite": False,
    "experimental_supported_tools": [],
    "node_repl_auto_review_required": False,
    "node_repl_disabled": True,
    "supports_search_tool": False,
    "supports_experimental_context": False,
    # 纯 shell 编辑：apply_patch 是 Responses 的 custom tool（语法文法），
    # llama-server 解析不了，留空让 codex 改用 shell 命令改文件。
    "apply_patch_tool_type": None,
    "shell_type": "shell_command",
    # 思考由 chat 模板管，codex 的 reasoning 参数 llama-server 直接忽略
    "default_reasoning_level": "none",
    "supported_reasoning_levels": [],
    "default_reasoning_summary": "none",
    "support_verbosity": False,
    "default_verbosity": None,
    "input_modalities": ["text"],
    "visibility": "list",
    "supported_in_api": True,
    "priority": 1,
    "supports_image_detail_original": False,
    "web_search_tool_type": "text",
}

# start-codex.sh 用它判断「8080 上跑的是不是带补丁的那份模板」
MARKER = "set sys_text"

_ANCHOR_TOOLS = """    {%- if messages[0].role == 'system' %}
        {%- set content = render_content(messages[0].content, false, true)|trim %}
        {%- if content %}
            {{- '\\n\\n' + content }}
        {%- endif %}
    {%- endif %}"""

_NEW_TOOLS = """    {%- if sys_text %}
        {{- '\\n\\n' + sys_text }}
    {%- endif %}"""

_ANCHOR_PLAIN = """    {%- if messages[0].role == 'system' %}
        {%- set content = render_content(messages[0].content, false, true)|trim %}
        {{- '<|im_start|>system\\n' + content + '<|im_end|>\\n' }}
    {%- endif %}"""

_NEW_PLAIN = """    {%- if sys_text %}
        {{- '<|im_start|>system\\n' + sys_text + '<|im_end|>\\n' }}
    {%- endif %}"""

_ANCHOR_GUARD = """    {%- if message.role == "system" %}
        {%- if not loop.first %}
            {{- raise_exception('System message must be at the beginning.') }}
        {%- endif %}
    {%- elif message.role == "user" %}"""

_NEW_GUARD = """    {%- if message.role == "system" %}
    {%- elif message.role == "user" %}"""

_MERGE = """{%- set ns_sys = namespace(text='') %}
{%- for m in messages %}
    {%- if m.role == 'system' %}
        {%- set c = render_content(m.content, false, true)|trim %}
        {%- if c %}
            {%- set ns_sys.text = ns_sys.text + ('\\n\\n' if ns_sys.text else '') + c %}
        {%- endif %}
    {%- endif %}
{%- endfor %}
{%- set sys_text = ns_sys.text %}
"""


# ── GGUF 元数据 ────────────────────────────────────────────────────────────

class _Reader:
    def __init__(self, fh):
        self.fh = fh

    def raw(self, n):
        b = self.fh.read(n)
        if len(b) != n:
            raise EOFError("GGUF 文件被截断")
        return b

    def u32(self):
        return struct.unpack("<I", self.raw(4))[0]

    def u64(self):
        return struct.unpack("<Q", self.raw(8))[0]

    def string(self):
        return self.raw(self.u64()).decode("utf-8", "replace")

    def value(self, vtype):
        if vtype == _STRING:
            return self.string()
        if vtype == _ARRAY:
            elem = self.u32()
            return [self.value(elem) for _ in range(self.u64())]
        fmt = _SCALAR.get(vtype)
        if fmt is None:
            raise ValueError(f"未知的 GGUF 类型 {vtype}")
        return struct.unpack(fmt, self.raw(struct.calcsize(fmt)))[0]


def gguf_key(path, wanted="tokenizer.chat_template"):
    """离线读取 GGUF 里的一个元数据键。

    只扫 header，不碰权重 —— 比为了拿一个字符串去启动 6GB 模型快得多。
    """
    with open(path, "rb") as fh:
        r = _Reader(fh)
        if r.raw(4) != b"GGUF":
            raise ValueError(f"{path}: 不是 GGUF 文件")
        if r.u32() not in (2, 3):
            raise ValueError(f"{path}: 不支持的 GGUF 版本")
        r.u64()  # tensor 数
        for _ in range(r.u64()):
            key = r.string()
            value = r.value(r.u32())
            if key == wanted:
                return value
    raise KeyError(f"{path}: 找不到 {wanted}")


# ── 模板补丁 ──────────────────────────────────────────────────────────────

def patch_template(tpl):
    """把多条 system 合并成一条。返回 (patched, note)。

    认不出锚点就原样返回 —— 该模型的模板本来就能处理多条 system。
    """
    if _ANCHOR_GUARD not in tpl:
        return tpl, "该模型模板无需补丁（本就把非首个 system 正常渲染）"

    for old, new in ((_ANCHOR_TOOLS, _NEW_TOOLS),
                     (_ANCHOR_PLAIN, _NEW_PLAIN),
                     (_ANCHOR_GUARD, _NEW_GUARD)):
        if tpl.count(old) != 1:
            raise SystemExit(
                f"锚点命中 {tpl.count(old)} 次（应为 1 次），模板可能已变：\n{old[:80]}")
        tpl = tpl.replace(old, new)

    head = "{%- if not messages %}"
    if tpl.count(head) != 1:
        raise SystemExit("前导锚点命中次数不为 1，模板可能已变")
    tpl = tpl.replace(head, _MERGE + head)
    return tpl, "已合并 system 消息"


# ── 模型目录 ──────────────────────────────────────────────────────────────

def _norm(s):
    """比对模板时忽略换行风格与首尾空白（GGUF 里是 LF，Windows 写出可能是 CRLF）。"""
    return s.replace("\r\n", "\n").strip()


def build_catalog(out_path):
    """从内置目录克隆一条完整条目再改写 —— 字段是严格校验的，缺一个就解析失败。"""
    # 必须按字节取再 utf-8 解码：text=True 会用控制台代码页（cp1252）解，直接崩
    builtin = json.loads(subprocess.run(["codex", "debug", "models"],
                                        capture_output=True,
                                        check=True).stdout.decode("utf-8"))
    by_slug = {m["slug"]: m for m in builtin["models"]}
    template = by_slug["gpt-5.4-mini"]  # 随便挑一条当字段骨架

    entries = []
    for spec in CATALOG_MODELS:
        entry = dict(template)
        entry.update(CATALOG_OVERRIDES)
        entry.update(spec)
        entries.append(entry)

    Path(out_path).write_text(
        json.dumps({"models": entries}, ensure_ascii=False, indent=1),
        encoding="utf-8", newline="\n")
    return [e["slug"] for e in entries]


# ── CLI ───────────────────────────────────────────────────────────────────

def main():
    # 被脚本调用时 stdout 往往不是控制台，Python 会退回 cp1252，
    # 打印任何中文都 UnicodeEncodeError。先钉死 utf-8。
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError):
            pass

    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    t = sub.add_parser("template", help="生成 codex 兼容 chat 模板")
    t.add_argument("--model", choices=sorted(MODELS))
    t.add_argument("--gguf")
    t.add_argument("--out", required=True)

    c = sub.add_parser("catalog", help="生成模型目录 JSON")
    c.add_argument("--out", required=True)

    k = sub.add_parser("check-template",
                       help="从 stdin 读 /props，比对在跑的是不是本文件模板")
    k.add_argument("--file", required=True)

    s = sub.add_parser("show", help="查看某模型的模板是否需要补丁")
    s.add_argument("--model", choices=sorted(MODELS))
    s.add_argument("--gguf")

    a = ap.parse_args()
    gguf = getattr(a, "gguf", None) or MODELS.get(getattr(a, "model", None))

    if a.cmd == "check-template":
        # 退出码即答案：0 = 一致，1 = 不一致/没在跑。
        # 不能比对固定 marker —— 有些模型的模板本来就不需要补丁，
        # 那种情况下 marker 永远不出现，会退化成「每次都重启」。
        try:
            live = json.load(sys.stdin).get("chat_template") or ""
        except (json.JSONDecodeError, UnicodeDecodeError):
            return 1
        want = Path(a.file).read_text(encoding="utf-8")
        return 0 if _norm(live) == _norm(want) else 1
    elif a.cmd == "template":
        tpl, note = patch_template(gguf_key(gguf))
        Path(a.out).write_text(tpl, encoding="utf-8", newline="\n")
        print(f"{a.out} <- {gguf}  [{note}]")
    elif a.cmd == "catalog":
        print("已写入", a.out, build_catalog(a.out))
    elif a.cmd == "show":
        tpl, note = patch_template(gguf_key(gguf))
        print(f"{gguf}\n  {note}\n  marker={MARKER in tpl}")


if __name__ == "__main__":
    sys.exit(main())

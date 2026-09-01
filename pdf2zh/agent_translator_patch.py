#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Patch PDFMathTranslate (pdf2zh) to register the AgentTranslator.

The AgentTranslator makes the *current conversation* (PI coding agent) the
translation engine: it never calls an external translation API (no MiMo,
Google, DeepL, ...). Workflow is two-pass:

   1. run `pdf2zh paper.pdf -s agent -o out/`  -> collects pending texts
      into ~/.pdf2zh-agent/inbox.json (PDF is built with original text)
   2. the agent translates them in-chat and writes ~/.pdf2zh-agent/outbox.json
   3. re-run the same command -> outbox hits -> real mono/dual PDF

Supports both code layouts:
  * new layout (master, 23+ services, `for translator in [...]` lists)
  * old layout (PyPI 1.7.9: if/elif chain in converter.py, 6 services)

Usage (from this skill dir):
    py -3 agent_translator_patch.py status
    py -3 agent_translator_patch.py install [--package-dir DIR]   # agent 引擎（备用）
    py -3 agent_translator_patch.py compat [--package-dir DIR]    # 仅 numpy2 兼容修复（1.7.9 必需）
    py -3 agent_translator_patch.py uninstall

Idempotent; backs up every edited file to <file>.harness.bak.
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

MARK = "# --- AgentTranslator patch (harness) ---"

AGENT_CLASS_NEW = '''
# ============================================================
# --- AgentTranslator patch (harness) ---
# Translation engine = the current conversation (PI coding agent).
# No external translation API is called. Workflow (two-pass):
#   1. run `pdf2zh -s agent`  -> collects pending texts -> inbox.json
#   2. agent translates them in-chat -> writes outbox.json
#   3. re-run `pdf2zh -s agent` -> real mono/dual PDF
# ============================================================
class AgentTranslator(BaseTranslator):
    """Translate via the current conversation (PI coding agent)."""

    name = "agent"
    envs = {
        "AGENT_BRIDGE_DIR": os.path.join(os.path.expanduser("~"), ".pdf2zh-agent"),
    }
    CustomPrompt = True

    def __init__(self, lang_in, lang_out, model, envs=None, prompt=None, ignore_cache=False):
        import hashlib
        from pathlib import Path as _Path
        self._hashlib = hashlib
        self.set_envs(envs)
        self.bridge_dir = _Path(
            self.envs.get("AGENT_BRIDGE_DIR")
            or os.path.join(os.path.expanduser("~"), ".pdf2zh-agent")
        )
        self.bridge_dir.mkdir(parents=True, exist_ok=True)
        self.inbox_path = self.bridge_dir / "inbox.json"
        self.outbox_path = self.bridge_dir / "outbox.json"
        self.lang_in = lang_in
        self.lang_out = lang_out
        self.model = model
        self.ignore_cache = ignore_cache
        self.prompttext = prompt
        self._pending = {}

    def _load_json(self, path):
        try:
            if path.exists():
                return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
        return {}

    def _save_json(self, path, data):
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _key(self, text):
        return self._hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]

    def translate(self, text, ignore_cache=False):
        # Bypass BaseTranslator's SQLite cache: the first (collecting) run
        # would cache text->text and shadow real translations on the second run.
        # The outbox is the single source of truth.
        return self.do_translate(text)

    def do_translate(self, text):
        key = self._key(text)
        outbox = self._load_json(self.outbox_path)
        if key in outbox:
            val = outbox[key]
            if isinstance(val, dict):
                # {"lang_out": "zh", "text": "译文"} — 校验目标语言
                if val.get("lang_out") == self.lang_out:
                    return val.get("text", text)
            else:
                # 简写 "译文"（按 inbox 的 lang_out 翻译）
                return val
        if key not in self._pending:
            self._pending[key] = {
                "key": key,
                "lang_in": self.lang_in,
                "lang_out": self.lang_out,
                "text": text,
            }
            merged = self._load_json(self.inbox_path)
            merged[key] = self._pending[key]
            self._save_json(self.inbox_path, merged)
        return text
# --- /AgentTranslator patch (harness) ---
'''

AGENT_CLASS_OLD = '''
# ============================================================
# --- AgentTranslator patch (harness) ---
# Translation engine = the current conversation (PI coding agent).
# No external translation API is called. Workflow (two-pass):
#   1. run `pdf2zh -s agent`  -> collects pending texts -> inbox.json
#   2. agent translates them in-chat -> writes outbox.json
#   3. re-run `pdf2zh -s agent` -> real mono/dual PDF
# ============================================================
class AgentTranslator(BaseTranslator):
    """Translate via the current conversation (PI coding agent)."""

    def __init__(self, service, lang_out, lang_in, model):
        import hashlib
        import json as _json
        from pathlib import Path as _Path
        self._hashlib = hashlib
        self._json = _json
        self.service = service
        self.lang_out = lang_out
        self.lang_in = lang_in
        self.model = model
        self.bridge_dir = _Path(
            os.environ.get("AGENT_BRIDGE_DIR")
            or os.path.join(os.path.expanduser("~"), ".pdf2zh-agent")
        )
        self.bridge_dir.mkdir(parents=True, exist_ok=True)
        self.inbox_path = self.bridge_dir / "inbox.json"
        self.outbox_path = self.bridge_dir / "outbox.json"
        self._pending = {}

    def _load_json(self, path):
        try:
            if path.exists():
                return self._json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
        return {}

    def _save_json(self, path, data):
        path.write_text(self._json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _key(self, text):
        return self._hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]

    def translate(self, text):
        # 绕过外部缓存：第一遍会把"原文->原文"写进 converter 的 paragraph 缓存，
        # 第二遍会抢先命中导致译文不生效。converter 已为 agent 引擎跳过缓存读取，
        # 这里只需以 outbox 为唯一真源。
        key = self._key(text)
        outbox = self._load_json(self.outbox_path)
        if key in outbox:
            val = outbox[key]
            if isinstance(val, dict):
                # {"lang_out": "zh", "text": "译文"} — 校验目标语言
                if val.get("lang_out") == self.lang_out:
                    return val.get("text", text)
            else:
                # 简写 "译文"（按 inbox 的 lang_out 翻译）
                return val
        if key not in self._pending:
            self._pending[key] = {
                "key": key,
                "lang_in": self.lang_in,
                "lang_out": self.lang_out,
                "text": text,
            }
            merged = self._load_json(self.inbox_path)
            merged[key] = self._pending[key]
            self._save_json(self.inbox_path, merged)
        return text
# --- /AgentTranslator patch (harness) ---
'''

CANDIDATE_DIRS = [
    Path("C:/Program Files/pdf2zh/build/site-packages"),
    Path("C:/Program Files (x86)/pdf2zh/build/site-packages"),
]

# new layout (master): registration via import lists + `for translator in [...]`
NEW_PATCHES = {
    "pdf2zh.py": [
        ("        X302AITranslator,\n    )",
         "        X302AITranslator,\n        AgentTranslator,\n    )"),
        ("        X302AITranslator,\n    ]:",
         "        X302AITranslator,\n        AgentTranslator,\n    ]:"),
    ],
    "converter.py": [
        ("    X302AITranslator,\n)",
         "    X302AITranslator,\n    AgentTranslator,\n)"),
        ("QwenMtTranslator, X302AITranslator]:",
         "QwenMtTranslator, X302AITranslator, AgentTranslator]:"),
    ],
}

# old layout (PyPI 1.7.9): if/elif chain + paragraph cache in converter.py
OLD_PATCHES = {
    "converter.py": [
        ("    AzureTranslator,\n)",
         "    AzureTranslator,\n    AgentTranslator,\n)"),
        (
            "            self.translator: BaseTranslator = AzureTranslator(\n"
            "                service, lang_out, lang_in, None\n"
            "            )\n"
            "        else:\n"
            '            raise ValueError("Unsupported translation service")',
            "            self.translator: BaseTranslator = AzureTranslator(\n"
            "                service, lang_out, lang_in, None\n"
            "            )\n"
            '        elif param[0] == "agent":\n'
            "            self.translator: BaseTranslator = AgentTranslator(\n"
            "                service, lang_out, lang_in, None\n"
            "            )\n"
            "        else:\n"
            '            raise ValueError("Unsupported translation service")',
        ),
        (
            "                    new = cache.load_paragraph(hash_key, hash_key_paragraph) # 查询缓存",
            "                    # agent 引擎绕过 paragraph 缓存（第一遍会把原文缓存导致第二遍译文不生效）\n"
            "                    new = None if isinstance(self.translator, AgentTranslator) else cache.load_paragraph(hash_key, hash_key_paragraph) # 查询缓存",
        ),
    ],
    # numpy 2.x 兼容：np.fromstring 已移除，改 frombuffer（语义相同）
    "high_level.py": [
        (
            "        image = np.fromstring(pix.samples, np.uint8).reshape(pix.height, pix.width, 3)[:, :, ::-1]",
            "        image = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, 3)[:, :, ::-1]  # numpy2 compat",
        ),
    ],
}

EDIT_FILES = ["translator.py", "pdf2zh.py", "converter.py", "high_level.py"]


def find_package_dir(override=None):
    if override:
        p = Path(override)
        if (p / "pdf2zh" / "translator.py").exists():
            return p
        raise SystemExit(f"package dir not found: {p}")
    env = os.environ.get("PDF2ZH_PACKAGE_DIR")
    if env:
        p = Path(env)
        if (p / "pdf2zh" / "translator.py").exists():
            return p
    for d in CANDIDATE_DIRS:
        if (d / "pdf2zh" / "translator.py").exists():
            return d
    try:
        out = subprocess.check_output(
            [sys.executable, "-m", "pip", "show", "pdf2zh"], text=True
        )
        for line in out.splitlines():
            if line.startswith("Location:"):
                loc = Path(line.split(":", 1)[1].strip())
                if (loc / "pdf2zh" / "translator.py").exists():
                    return loc
    except Exception:
        pass
    raise SystemExit(
        "Could not locate pdf2zh site-packages. Install pdf2zh first or pass --package-dir."
    )


def patch_register(text, old, new):
    """Insert `new` if `old` found; no-op if `new` already present (idempotent)."""
    if new in text:
        return text
    if old not in text:
        raise SystemExit(f"anchor not found in file: {old[:80]!r}")
    return text.replace(old, new, 1)


def detect_layout(translator_text):
    return "new" if "X302AITranslator" in translator_text else "old"


def install(package_dir):
    tr_path = package_dir / "pdf2zh" / "translator.py"
    if not tr_path.exists():
        raise SystemExit(f"missing {tr_path}")
    tr_text = tr_path.read_text(encoding="utf-8")
    layout = detect_layout(tr_text)
    print(f"  layout: {layout}")

    # translator.py: append AgentTranslator class
    bak = Path(str(tr_path) + ".harness.bak")
    if not bak.exists():
        shutil.copy2(tr_path, bak)
    if MARK not in tr_text:
        cls = AGENT_CLASS_NEW if layout == "new" else AGENT_CLASS_OLD
        tr_text = tr_text.rstrip() + "\n" + cls
        tr_path.write_text(tr_text, encoding="utf-8")
        print(f"  patched {tr_path}")

    # registration files (pdf2zh.py + converter.py for new; converter.py only for old)
    files = NEW_PATCHES if layout == "new" else OLD_PATCHES
    for name, repls in files.items():
        path = package_dir / "pdf2zh" / name
        if not path.exists():
            raise SystemExit(f"missing {path}")
        b = Path(str(path) + ".harness.bak")
        if not b.exists():
            shutil.copy2(path, b)
        text = path.read_text(encoding="utf-8")
        for old, new in repls:
            text = patch_register(text, old, new)
        path.write_text(text, encoding="utf-8")
        print(f"  patched {path}")


def compat(package_dir):
    """numpy 2.x compatibility only (np.fromstring -> np.frombuffer). Required for 1.7.9."""
    for name, repls in {"high_level.py": OLD_PATCHES["high_level.py"]}.items():
        path = package_dir / "pdf2zh" / name
        if not path.exists():
            raise SystemExit(f"missing {path}")
        b = Path(str(path) + ".harness.bak")
        if not b.exists():
            shutil.copy2(path, b)
        text = path.read_text(encoding="utf-8")
        for old, new in repls:
            text = patch_register(text, old, new)
        path.write_text(text, encoding="utf-8")
        print(f"  patched {path} (numpy2 compat)")


def uninstall(package_dir):
    for name in EDIT_FILES:
        path = package_dir / "pdf2zh" / name
        bak = Path(str(path) + ".harness.bak")
        if bak.exists():
            shutil.copy2(bak, path)
            bak.unlink()
            print(f"  restored {path}")
        else:
            print(f"  no backup for {path} (skip)")


def status(package_dir):
    for name in EDIT_FILES:
        path = package_dir / "pdf2zh" / name
        bak = Path(str(path) + ".harness.bak")
        if not path.exists():
            print(f"  {name}: MISSING")
            continue
        text = path.read_text(encoding="utf-8")
        marked = "yes" if MARK in text else "no"
        agent_reg = "yes" if "AgentTranslator" in text else "no"
        print(f"  {name}: marked={marked} agent_registered={agent_reg} backup={bak.exists()}")


def main():
    ap = argparse.ArgumentParser(description="Register AgentTranslator in pdf2zh")
    ap.add_argument("action", choices=["install", "uninstall", "compat", "status"])
    ap.add_argument("--package-dir", default=None)
    args = ap.parse_args()
    pkg = find_package_dir(args.package_dir)
    print(f"pdf2zh site-packages: {pkg}")
    if args.action == "install":
        install(pkg)
        print("done. Now: pdf2zh paper.pdf -s agent -o out/")
    elif args.action == "compat":
        compat(pkg)
        print("done. (numpy2 compat only)")
    elif args.action == "uninstall":
        uninstall(pkg)
        print("done.")
    else:
        status(pkg)


if __name__ == "__main__":
    main()

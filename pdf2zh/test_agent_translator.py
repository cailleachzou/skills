# -*- coding: utf-8 -*-
"""Verify AgentTranslator two-pass behavior on the patched translator.py."""
import json
import os
import sys
import tempfile
import types
from pathlib import Path

# --- stub external deps of translator.py ---
for name in [
    "deepl", "ollama", "openai", "requests", "xinference_client",
    "azure", "azure.ai", "azure.ai.translation", "azure.ai.translation.text",
    "azure.core", "azure.core.credentials",
    "tencentcloud", "tencentcloud.common", "tencentcloud.tmt",
    "tencentcloud.tmt.v20180321", "tencentcloud.tmt.v20180321.models",
]:
    sys.modules.setdefault(name, types.ModuleType(name))
sys.modules["azure.ai.translation.text"].TextTranslationClient = object
sys.modules["azure.core.credentials"].AzureKeyCredential = object
sys.modules["tencentcloud.tmt.v20180321.models"].TextTranslateRequest = object
sys.modules["tencentcloud.tmt.v20180321.models"].TextTranslateResponse = object
sys.modules["tencentcloud.tmt.v20180321.models"].TextTranslateResponse = object
sys.modules["tencentcloud.common"].credential = types.SimpleNamespace(Credential=object)
sys.modules["tencentcloud.tmt.v20180321"].tmt_client = types.SimpleNamespace(TmtClient=object)
sys.modules["tencentcloud.tmt.v20180321.tmt_client"] = sys.modules["tencentcloud.tmt.v20180321"].tmt_client
sys.modules["openai"] = types.SimpleNamespace(
    OpenAI=lambda *a, **k: None,
    AzureOpenAI=lambda *a, **k: None,
    APIError=Exception,
    APIConnectionError=Exception,
    RateLimitError=Exception,
    BadRequestError=Exception,
)
sys.modules["ollama"] = types.SimpleNamespace(Client=lambda *a, **k: None)
sys.modules["deepl"] = types.SimpleNamespace(Translator=lambda *a, **k: None)
sys.modules["xinference_client"] = types.ModuleType("xinference_client")
sys.modules["xinference_client"].Client = object
sys.modules["requests"] = types.SimpleNamespace(
    post=lambda *a, **k: types.SimpleNamespace(json=lambda: {}, raise_for_status=lambda: None)
)


def _retry_factory(*a, **k):
    def deco(fn):
        return fn
    return deco


sys.modules["tenacity"] = types.SimpleNamespace(
    retry=_retry_factory,
    retry_if_exception_type=_retry_factory,
    stop_after_attempt=_retry_factory,
    wait_exponential=_retry_factory,
)

FAKE = r"C:/Users/caill/AppData/Local/Temp/fake_pkg"
sys.path.insert(0, FAKE)

import pdf2zh  # noqa: E402
pdf2zh.cache = types.ModuleType("pdf2zh.cache")
pdf2zh.cache.TranslationCache = lambda *a, **k: None
pdf2zh.config = types.ModuleType("pdf2zh.config")
pdf2zh.config.ConfigManager = types.SimpleNamespace(
    get_translator_by_name=lambda name: None,
    set_translator_by_name=lambda name, envs: None,
)
sys.modules["pdf2zh.cache"] = pdf2zh.cache
sys.modules["pdf2zh.config"] = pdf2zh.config

from pdf2zh.translator import AgentTranslator, BaseTranslator  # noqa: E402

assert issubclass(AgentTranslator, BaseTranslator)
assert AgentTranslator.name == "agent"

bridge = Path(tempfile.mkdtemp(prefix="agent_bridge_"))
os.environ["AGENT_BRIDGE_DIR"] = str(bridge)

text = "Hello, world! This is a test line.\nSecond line with $math$."

# Pass 1: collect -> returns original text, writes inbox.json
t = AgentTranslator("en", "zh", None)
r1 = t.do_translate(text)
assert r1 == text, r1
inbox = json.loads((bridge / "inbox.json").read_text(encoding="utf-8"))
assert len(inbox) == 1
key = next(iter(inbox))
assert inbox[key]["lang_out"] == "zh"
assert inbox[key]["text"] == text
print("PASS pass1 collect:", key)

# Pass 2a: outbox simple string form
(bridge / "outbox.json").write_text(
    json.dumps({key: "你好，世界！这是测试行。\n第二行含 $math$。"}, ensure_ascii=False),
    encoding="utf-8",
)
r2 = t.do_translate(text)
assert r2 == "你好，世界！这是测试行。\n第二行含 $math$。", r2
print("PASS pass2 simple-string")

# Pass 2b: dict form with lang_out guard (ja run must NOT reuse zh translation)
(bridge / "outbox.json").write_text(
    json.dumps({key: {"lang_out": "zh", "text": "你好，世界！"}}, ensure_ascii=False),
    encoding="utf-8",
)
t_zh = AgentTranslator("en", "zh", None)
assert t_zh.do_translate(text) == "你好，世界！"
t_ja = AgentTranslator("en", "ja", None)
assert t_ja.do_translate(text) == text  # lang mismatch -> still pending
inbox2 = json.loads((bridge / "inbox.json").read_text(encoding="utf-8"))
assert inbox2[key]["lang_out"] == "ja"  # pending entry updated for ja
print("PASS pass2 dict-form lang guard")

# Pass 3: repeated collect must not duplicate
(bridge / "outbox.json").unlink()
t3 = AgentTranslator("en", "zh", None)
t3.do_translate(text)
inbox3 = json.loads((bridge / "inbox.json").read_text(encoding="utf-8"))
assert len(inbox3) == 1, inbox3
print("PASS no-duplicate pending")

print("ALL PASS")

---
name: pdf2zh
description: "Translate PDFs with layout preserved (math, columns) via PDFMathTranslate. Uses external translation services — google (free, no key), openai, deepl, deeplx, ollama, azure. 1.7.9 quirk: use --lang-out zh-CN for Chinese with google."
---

# pdf2zh（外部翻译服务版）

> PDFMathTranslate 解析 PDF 并保留布局（数学公式、双栏），翻译交给**外部翻译服务**。
> 本机已装 PyPI 最新版 **1.7.9**（旧版 CLI：无 `-o`，PDF 输出到当前目录 `<名>-zh.pdf` / `<名>-dual.pdf`）。

## 支持的服务（1.7.9）

| 服务 | 命令 | Key 配置 |
|------|------|----------|
| Google（免费） | `-s google` | 无需 key |
| OpenAI 兼容 | `-s openai:<模型>` | `OPENAI_API_KEY`（可选 `OPENAI_BASE_URL`） |
| DeepL | `-s deepl` | `DEEPL_AUTH_KEY` |
| DeepLX | `-s deeplx` | `DEEPLX_AUTH_KEY`、`DEEPLX_SERVER_URL` |
| Ollama（本地） | `-s ollama:<模型>` | 本机 ollama |
| Azure | `-s azure` | `AZURE_APIKEY`、`AZURE_ENDPOINT`、`AZURE_REGION` |

> 想用其他 OpenAI 兼容服务（包括 MiMo）：设 `OPENAI_API_KEY` + `OPENAI_BASE_URL`，用 `-s openai:<模型>`。

## 安装（已完成）

```bash
pip install pdf2zh                      # 1.7.9 + torch 等依赖（已装）
py -3 agent_translator_patch.py compat  # numpy 2.x 兼容修复（1.7.9 必需，否则报 fromstring 错误）
```

`compat` 只改 `high_level.py` 一处（`np.fromstring` → `np.frombuffer`），留 `.harness.bak`，`uninstall` 可还原。
本机走代理 `127.0.0.1:7897`，google 服务可用。

## 常用命令

```bash
# 英→中（注意：google 中文目标语言用 zh-CN，用 zh 会返回原文！）
pdf2zh paper.pdf -s google --lang-in en --lang-out zh-CN

# 英→日
pdf2zh paper.pdf -s google --lang-in en --lang-out ja

# 指定页
pdf2zh book.pdf -s google --lang-in en --lang-out zh-CN --pages 1-3

# OpenAI 兼容（含 MiMo）
OPENAI_API_KEY=sk-... OPENAI_BASE_URL=https://api.xiaomimimo.com/v1 \
  pdf2zh paper.pdf -s openai:mimo-v2.5 --lang-in en --lang-out zh-CN
```

## 注意事项

* **语言码**：google 用 `zh-CN`/`ja`/`en` 等；`zh` 不被 google 网页端点识别（返回原文）。`auto` 也安全。
* **公式占位符**：pdf2zh 把公式替换成 `$v0$ $v1$` 再翻译，译文必须原样保留这些标记，管道回填成真实公式。
* **缓存**：位于 `%TEMP%\cache\<hash>\`。翻译结果会缓存，改服务/语言后 key 不同不受影响；想强制重译删该目录。
* **多线程**：`-t` 默认 4，并发调翻译服务。

## 排错

| 现象 | 处理 |
|------|------|
| `ValueError: The binary mode of fromstring is removed` | 没打 numpy 兼容：`py -3 agent_translator_patch.py compat` |
| 译文和原文一样 | 检查语言码（google 中文用 `zh-CN`）；网络/代理可达性 |
| `Empty translation result` | google 页面结构变化或网络问题，换 `-s openai` 等服务 |
| `Unsupported translation service` | 服务名拼错，或该服务不在 1.7.9 列表 |

## 备用：当前对话翻译引擎（agent）

`agent_translator_patch.py install` 会注册 `-s agent`（由 coding agent 在对话中翻译，无外部 API），
两遍法工作流详见脚本注释。当前默认使用外部服务，需要时再启用。

## 文件位置

| 内容 | 位置 |
|------|------|
| 包 | `C:\Users\caill\AppData\Local\Programs\Python\Python314\Lib\site-packages\pdf2zh\` |
| 补丁备份 | `pdf2zh\*.py.harness.bak` |
| 翻译缓存 | `%TEMP%\cache\` |
| 布局模型 | `~/.cache/huggingface/`（首次运行自动下载） |

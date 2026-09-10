---
name: pdf2zh
description: "Translate PDFs with layout preserved (math, columns) via PDFMathTranslate. Uses external translation services — google (free, no key), openai, deepl, deeplx, azure. Installed on this machine via uv tool as v1.9.11 (pin tencentcloud-sdk-python-tmt==3.1.70 or it crashes on import). For Chinese with google use --lang-out zh-CN."
---

# pdf2zh（外部翻译服务版）

> ✅ **本机已装 v1.9.11**（uv tool 隔离环境，2026-09-10 安装并实测启动正常）。命令在 `C:\Users\caill\.local\bin\pdf2zh.exe`。
> PDFMathTranslate 解析 PDF 并保留布局（数学公式、双栏），翻译交给**外部翻译服务**。
> ⚠️ **版本与旧文档不同**：本文件原先通篇按 **1.7.9** 编写。1.9.11 有三处行为变化，已在下文逐条标注。

## ⚠️ 启动前提：腾讯 SDK 必须钉版本

**症状**：装好后任何命令都直接崩，连 `--help` 都跑不起来 ——

```
ImportError: cannot import name 'TextTranslateRequest' from 'tencentcloud.tmt.v20180321.models'
```

**根因**：`tencentcloud-sdk-python-tmt` 新版**移除了 `TextTranslateRequest`**（当前 `models.py` 只剩 6 个类），而 pdf2zh 在 `translator.py` **模块顶层**硬导入它 —— 与你是否用腾讯翻译**无关**，纯粹是导入期就炸。

**修法**（已实测有效）：

```bash
uv pip install --python "C:/Users/caill/AppData/Roaming/uv/tools/pdf2zh/Scripts/python.exe" \
  "tencentcloud-sdk-python-tmt<3.1.100"
# 实测落在 3.1.70，该类尚存 → pdf2zh v1.9.11 恢复正常
```

> ⚠️ `uv tool upgrade pdf2zh` 会把这个钉子冲掉，升级后需**重新钉一遍**。

## 支持的服务

| 服务 | 命令 | Key 配置 |
|------|------|----------|
| Google（免费） | `-s google` | 无需 key |
| OpenAI 兼容 | `-s openai:<模型>` | `OPENAI_API_KEY`（可选 `OPENAI_BASE_URL`） |
| DeepL | `-s deepl` | `DEEPL_AUTH_KEY` |
| DeepLX | `-s deeplx` | `DEEPLX_AUTH_KEY`、`DEEPLX_SERVER_URL` |
| Azure | `-s azure` | `AZURE_APIKEY`、`AZURE_ENDPOINT`、`AZURE_REGION` |
| Ollama（本地） | `-s ollama:<模型>` | ⛔ 本机 ollama 已于 2026-09-10 卸载，此路不通 |

> 想用其他 OpenAI 兼容服务（包括 MiMo）：设 `OPENAI_API_KEY` + `OPENAI_BASE_URL`，用 `-s openai:<模型>`。
> ⚠️ 上表服务名**沿用 1.7.9 文档，未在 1.9.11 上逐个复验**（`--help` 不列服务清单）。

## 安装

```bash
uv tool install pdf2zh        # 本机实际装法：隔离环境，不污染系统 Python
```

**关于 Python 版本**（重要，别在系统 Python 上装）：

- pdf2zh **1.8.0+ 要求 Python `<3.13`**；本机系统 Python 是 **3.14**，所以 `py -3 -m pip install pdf2zh` 会**静默退回 1.7.9**（该版本无 Python 约束）。
- uv 用的是自己下载的 **3.12.14**，因此装到的是最新版 **1.9.11**。
- **1.9.11 不再依赖 torch**（版面走 onnxruntime）。旧文档里「torch 等依赖」的说法已不成立。
- **那个 numpy 兼容补丁不再需要**：1.9.11 源码里已无 `np.fromstring`，`agent_translator_patch.py compat` 是针对 1.7.9 的，对 1.9.11 无意义。

## 常用命令

```bash
# 英→中
pdf2zh paper.pdf -s google --lang-in en --lang-out zh-CN

# 英→日
pdf2zh paper.pdf -s google --lang-in en --lang-out ja

# 指定页
pdf2zh book.pdf -s google --lang-in en --lang-out zh-CN --pages 1-3

# 指定输出目录（✅ 1.9.11 已支持 -o；旧文档「旧版无 -o」作废）
pdf2zh paper.pdf -s google --lang-out zh-CN -o out/

# OpenAI 兼容（含 MiMo）
OPENAI_API_KEY=sk-... OPENAI_BASE_URL=https://api.xiaomimimo.com/v1 \
  pdf2zh paper.pdf -s openai:mimo-v2.5 --lang-in en --lang-out zh-CN
```

> 命令会先打印一行 `not in git repo` —— 这是它探测当前目录是否 git 仓库的提示，**无害**。

**1.9.11 新增的参数**（`--help` 实测列出，多数未复验）：`--babeldoc`、`--onnx`、`--mcp`、`--sse`、`--flask`、`--celery`、`--config`、`--dir`、`--ignore-cache`、`--skip-subset-fonts`、`--prompt`、`--compatible`。

## 注意事项

* **语言码**：google 中文目标语言用 `zh-CN`。⚠️「用 `zh` 会返回原文」是 **1.7.9 时期的经验，1.9.11 未复验**，遇到译文=原文时优先怀疑它。
* **公式占位符**：pdf2zh 把公式替换成 `$v0$ $v1$` 再翻译，译文必须原样保留这些标记，管道回填成真实公式。
* **缓存**：位于 `%TEMP%\cache\<hash>\`。翻译结果会缓存，想强制重译删该目录（或试 `--ignore-cache`）。
* **多线程**：`-t`，并发调翻译服务。

## 排错

| 现象 | 处理 |
|------|------|
| `ImportError: cannot import name 'TextTranslateRequest'` | 腾讯 SDK 漂移，见上文「启动前提」，把 `tencentcloud-sdk-python-tmt` 钉回 3.1.70 |
| 译文和原文一样 | 检查语言码（google 中文用 `zh-CN`）；网络/代理可达性 |
| `Empty translation result` | google 页面结构变化或网络问题，换 `-s openai` 等服务 |
| `Unsupported translation service` | 服务名拼错，或该服务不在当前版本列表 |

## 文件位置

| 内容 | 位置 |
|------|------|
| 命令 | `C:\Users\caill\.local\bin\pdf2zh.exe` |
| 工具环境 | `C:\Users\caill\AppData\Roaming\uv\tools\pdf2zh\`（`Lib\site-packages\pdf2zh\`） |
| 翻译缓存 | `%TEMP%\cache\` |
| 布局模型 | `~/.cache/huggingface/`（首次运行自动下载） |
| 补丁脚本 | `pdf2zh\agent_translator_patch.py` — ⚠️ 为 **1.7.9** 编写，对 1.9.11 **未复验**，`compat` 那部分已确认不再需要 |

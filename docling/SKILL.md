---
name: docling
description: >
  Use Docling to read, parse, convert, extract, or chunk documents in any
  supported format — PDF (born-digital or scanned), DOCX, PPTX, XLSX, HTML,
  Markdown, AsciiDoc, CSV, images, audio, video, and XML — into a unified
  DoclingDocument (Markdown or structured JSON). 当用户需要理解/解析/转换/提取
  无法直接读取的文件内容时使用："这个 PDF 里有什么"、"把这篇文档转成 Markdown"、
  "提取表格"、"为 RAG 分块"、"扫描件识别"、"解析这个 DOCX/PPTX"。Covers the
  `docling convert` CLI, the Python SDK (DocumentConverter + PipelineOptions),
  and the remote Service Client (self-hosted or managed docling-serve).
compatibility: |
  docling 2.118.0，独立 venv：`C:\Users\59620\.venv-docling\`（Python 3.12.12）
  CLI：`C:\Users\59620\.venv-docling\Scripts\docling.exe`（子命令式：`docling convert <source>`）
  ⚠️ 必须先设置 `TORCH_COMPILE_DISABLE=1` 和 `TORCHINDUCTOR_DISABLE=1`（torch 2.13 在无 MSVC 的 Windows 上报 inductor 错）
  模型缓存：`~/.cache/huggingface/`（约 2GB，首次转换自动下载）
  ⚠️ 本机 16GB 内存：处理大文档（>30 页）必须调小 `--page-batch-size`（默认 4）
license: MIT
metadata:
  author: docling-project (本地移植)
  version: "1.0"
  upstream: https://github.com/docling-project/docling
allowed-tools: Bash(docling:*) Bash(python3:*) Bash(uvx:*)
---

# Docling — 文档解析与转换

Docling 把 PDF、DOCX、PPTX、XLSX、HTML、Markdown、AsciiDoc、CSV、图片、音频、
视频、XML 等解析成统一表示 **`DoclingDocument`**，可导出为 **Markdown**（可读）
或 **JSON**（结构化、无损）。当用户需要理解一个无法直接读取的文件内容时用它，
尤其是 PDF（含扫描件，走 OCR 或视觉语言模型）。

## 本机安装情况

```bash
# 独立 venv（已装好，勿用系统 Python）
DOCLING="C:\Users\59620\.venv-docling\Scripts\docling.exe"
"$DOCLING" --version
#   → Docling version: 2.118.0
#   → Python: cpython-312 (3.12.12)

# CLI 是子命令式（不是 `docling report.pdf`，而是 `docling convert report.pdf`）
```

## ⚠️ 环境变量：torch inductor 报错（必须设）

**torch 2.13 在 Windows 上默认启用 inductor，会尝试用 MSVC `cl.exe` 编译。
本机无 MSVC → 报 `InvalidCxxCompiler: Compiler: cl is not found`，转换必然失败。**

```bash
export TORCH_COMPILE_DISABLE=1
export TORCHINDUCTOR_DISABLE=1
```

设置后再跑 `docling convert`。本技能提供的 wrapper 脚本已固化这两个变量
（见下文「推荐用法」），无需手动 export。

## 最快的路径：CLI

```bash
# ① 每次会话先设环境变量 + 定义变量
export TORCH_COMPILE_DISABLE=1
export TORCHINDUCTOR_DISABLE=1
DOCLING="C:\Users\59620\.venv-docling\Scripts\docling.exe"

# 转换本地 PDF → Markdown
"$DOCLING" convert report.pdf --to md --output ./out/

# 转 URL
"$DOCLING" convert https://example.com/paper.pdf --to md --output ./out/

# 一次输出多格式
"$DOCLING" convert report.pdf --to md --to json --output ./out/
```

输出文件按输入命名（`report.pdf` → `report.md`）。默认输出目录是当前目录。
支持格式：`pdf`、`docx`/`doc`、`pptx`/`ppt`、`xlsx`/`xls`、`html`、`md`、
`asciidoc`、`csv`、`odt`/`ods`/`odp`、图片、`audio`、多种 XML。

> **注意**：本机安装的 docling 2.118 是**子命令式 CLI**（`docling convert`）。
> 官方 README 里的旧式 `docling <source>` 写法在此版本不可用。

## 推荐用法：wrapper 脚本

`scripts/docling.ps1` 自动完成两件事：设置上述环境变量 + 追加 16GB 内存友好
默认参数（`--page-batch-size 2 --num-threads 4`，除非你已显式指定）。

```powershell
# PowerShell
& "C:\Users\59620\.claude\skills\docling\scripts\docling.ps1" convert report.pdf --to md --output ./out/
```

```bash
# Git Bash（MSYS2）下调用 PowerShell 脚本
powershell -NoProfile -ExecutionPolicy Bypass -File \
  "C:\Users\59620\.claude\skills\docling\scripts\docling.ps1" convert report.pdf --to md --output ./out/
```

## ⚠️ 本机关键限制：16GB 内存

验证发现：**处理大文档（>30 页 PDF）默认配置会 `std::bad_alloc` 内存不足**。
必须用以下参数控制内存：

```bash
# 大文档（>30 页）推荐
"$DOCLING" convert book.pdf --to md --output ./out/ \
  --page-batch-size 2        # 每批页数，默认 4，内存不足时降到 2 或 1
  --num-threads 4            # CPU 线程，降低并发内存

# 扫描件 / 图片型 PDF 内存压力更大，OCR 也吃内存
"$DOCLING" convert scan.pdf --to md --output ./out/ --page-batch-size 1
```

## 选择 pipeline（PDF / 图片）

| Pipeline | 标志 | 适用 | 权衡 |
|---|---|---|---|
| **Standard**（默认） | `--pipeline standard` | 数字原生态 PDF、速度 | CPU 即可；OCR 处理扫描页 |
| **VLM** | `--pipeline vlm` | 复杂版式、手写、公式、含文字图片 | 需 GPU（或 Apple MPS）；慢 |
| **ASR** | `--pipeline asr` | 音频转写 | — |

```bash
"$DOCLING" convert report.pdf --pipeline vlm --output ./out/
"$DOCLING" convert report.pdf --pipeline vlm --vlm-model granite_docling --output ./out/
"$DOCLING" convert interview.wav --pipeline asr --to md --output ./out/
```

决策：

| 文档 | 用 |
|---|---|
| 数字原生态 PDF（文字可选中） | Standard（快，无 GPU） |
| 扫描件 / 纯图片 PDF | Standard + OCR，或 `--pipeline vlm` 质量最好 |
| 复杂多栏版式、密集表格 | `--pipeline vlm` |
| 手写或公式 | `--pipeline vlm`（标准 OCR 处理不了） |
| 无 GPU / 离网 | Standard |
| 求速度、精度次要 | Standard + `--no-ocr` 和/或 `--no-tables` |

## OCR（扫描件和图片）

```bash
"$DOCLING" convert scan.pdf --to md --output ./out/              # OCR 默认开启
"$DOCLING" convert scan.pdf --to md --output ./out/ --ocr-engine rapidocr  # 轻量引擎
"$DOCLING" convert scan.pdf --to md --output ./out/ --force-ocr   # 强制重新 OCR
"$DOCLING" convert report.pdf --to md --output ./out/ --no-ocr    # 跳过 OCR（更快）
"$DOCLING" convert scan.pdf --to md --output ./out/ --ocr-lang en --ocr-lang de
```

## 表格、增强、其他内容

```bash
"$DOCLING" convert report.pdf --to md --output ./out/ --no-tables        # 跳过表格结构
"$DOCLING" convert report.pdf --to md --output ./out/ --table-mode accurate
"$DOCLING" convert report.pdf --to md --output ./out/ --enrich-code       # 代码理解
"$DOCLING" convert report.pdf --to md --output ./out/ --enrich-formula    # 公式理解
```

## 常见问题

| 情况 | 处理 |
|---|---|
| 扫描件 / 纯图片 PDF | Standard + OCR，或 `--pipeline vlm` |
| 加密 PDF | `--pdf-password PASSWORD`（错了抛 `ConversionError`） |
| 超大文档（500+ 页） | Standard + `--no-tables`；调小 `--page-batch-size` |
| 复杂多栏版式 | `--pipeline vlm`（standard 可能错乱阅读顺序） |
| 输出近乎空 / 大量 `�` | 开 OCR 或换 `--pipeline vlm` |
| 内存不足（`std::bad_alloc`） | `--page-batch-size 1-2 --num-threads 4` |
| `InvalidCxxCompiler: cl is not found` | 设 `TORCH_COMPILE_DISABLE=1 TORCHINDUCTOR_DISABLE=1` |

## 离线模型

```bash
# 预下载模型，离线跑（air-gapped）
docling-tools models download --output-dir /models
"$DOCLING" convert report.pdf --to md --output ./out/ --artifacts-path /models
```

`--artifacts-path` 覆盖默认 HF 缓存；也可用 `HF_HOME` 重定位缓存。

## 选型

| 需要… | 用 | 参考 |
|---|---|---|
| 一次性读/转文件（shell） | **CLI**（`docling convert …`） | `references/cli.md` |
| 编程式转换、调 pipeline、批量、导出图片表格 | **Python SDK**（`DocumentConverter` + `PipelineOptions`） | `references/python-sdk.md` |
| 从文档抽特定类型字段 | **DocumentExtractor**（结构化提取，beta） | `references/extraction.md` |
| 为检索/RAG 分块 | **Chunking + 框架加载器** | `references/rag.md` |
| 卸载到远程服务（低延迟、免本机 ML 依赖） | **Service Client**（自托管或托管 docling-serve） | `references/service-client.md` |

## 输出约定

- 始终报告转换状态和（PDF 的）页数
- 用户未指定格式时，问要 **Markdown**（可读）还是 **JSON / DoclingDocument**（结构化、无损）
- 表格优先用 `export_to_markdown()` / `export_to_dataframe()`（Python）
- 转换结果近空/重复/满屏 `�` → 源可能是扫描件或复杂版式 → 用 OCR 或 `--pipeline vlm` 重试

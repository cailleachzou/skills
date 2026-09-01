---
name: docs-translate
description: >
  完全离线的文档翻译 skill —— Word(.docx) / PPT(.pptx) / PDF 批量翻译，尽量保留原格式。
  docx/pptx 通过解包->提取 XML 文本->本地模型翻译->回填->重新打包，样式 100% 保留；
  PDF 用 pymupdf 输出"原文+译文"双层 PDF（原文排版不动，译文叠加在下方）。
  翻译引擎为本机 llama.cpp Vulkan + Qwen2.5 GGUF（OpenAI 兼容 API），免费、离线、隐私不出本机。
  当用户要求"翻译 Word/PPT/PDF 文档""批量翻译文件""离线翻译文档""文档翻译成中文/英文"
  "翻译后保持格式"时使用。纯文本/一句话翻译也走本 skill（`--text`），是唯一翻译入口。
compatibility: |
  依赖:
  - llama-server.exe (Vulkan): C:\Users\caill\tools\llama-cpp\vulkan\llama-server.exe
  - Python 3 + requests + lxml + pymupdf
  模型 (GGUF):
  - qwen7b (默认, 快, 质量够用): ollama blob sha256-2bada8a...
  - qwen14b (PDF/长文推荐, 慢但质量好): C:\Users\caill\models\Qwen2.5-14B-Instruct-Q4_K_M.gguf
  - qwen7b-q6 (高精度): C:\Users\caill\models\Qwen2.5-7B-Instruct-Q6_K.gguf
  ⚠️ 完全离线: 不调用任何云 API；llama-server 未运行时会自动拉起
metadata:
  author: Cailleach Zou
  version: "1.0"
  created: 2026-08-26
allowed-tools: Bash(*)
---

# docs-translate — 离线文档翻译（保留格式）

## 何时用

* 用户要翻译 **Word / PPT / PDF 文档**（单个、多个、整个目录）
* 要求 **保留原格式**、**离线**、**免费**（不耗 mimo token）
* 批量翻译文件
* 纯文本/一句话翻译（`--text` 参数，输出到终端）

**不走本 skill**：CAD 图纸 → `dwg-translate`；扫描版 PDF（图片型，无文本层）→ 本 skill 无法处理，提示用户。

## 快速开始

```bash
# 单个文件（自动启动模型，输出 _zh.docx 到同目录）
py -3 "C:\Users\caill\.pi\agent\skills\docs-translate\scripts\translate_docs.py" report.docx

# 整个目录（批量）
py -3 "C:\Users\caill\.pi\agent\skills\docs-translate\scripts\translate_docs.py" ./docs/ -o ./docs_zh/

# 直接选档位：质量优先（PDF 推荐）
py -3 "C:\Users\caill\.pi\agent\skills\docs-translate\scripts\translate_docs.py" paper.pdf --mode quality

# 直接选档位：速度优先
py -3 "C:\Users\caill\.pi\agent\skills\docs-translate\scripts\translate_docs.py" notes.docx --mode fast

# 翻成英文
py -3 "C:\Users\caill\.pi\agent\skills\docs-translate\scripts\translate_docs.py" 报告.docx --lang en

# 纯文本一句话翻译（直接输出到终端）
py -3 "C:\Users\caill\.pi\agent\skills\docs-translate\scripts\translate_docs.py" --text "Hello, how are you?" --lang zh
```

## 速度/质量档位（`--mode`）

不指定 `--model` 时，可**交互式选择**档位（终端下运行会提示输入），或用 `--mode` 直接指定：

| 档位 | 模型 | 速度 | 适合场景 |
|------|------|------|----------|
| `fast` | qwen7b | ~61 tok/s | 草稿/速览，量大求快 |
| `balanced`（默认） | qwen7b-q6 | ~49 tok/s | 日常翻译，精度更好 |
| `quality` | qwen14b | ~28 tok/s | 正式文档、PDF、质量优先 |

## 参数

| 参数 | 默认 | 说明 |
|------|------|------|
| `input` | 文件模式必填 | .docx/.pptx/.pdf 文件或目录（`--text` 模式下可省略） |
| `--text` | — | 直接翻译命令行文本（单段），输出到 stdout；与 `input` 二选一 |
| `-o` | 同目录（文件）/ `_zh_out`（目录） | 输出目录 |
| `--mode` | 交互选择 | 档位：`fast` / `balanced` / `quality`（映射见上表） |
| `--model` | — | 直接指定模型：`qwen7b` / `qwen14b` / `qwen7b-q6`（与 `--mode` 二选一） |
| `--lang` | `zh` | 目标语言：`zh` 或 `en` |
| `--port` | `8080` | llama-server 端口 |
| `--batch` | `10` | 每批翻译条数（越小越稳，越慢） |
| `--no-server` | 关 | 不自动启动 llama-server（复用已在跑的） |

## 为什么翻译引擎是 Qwen2.5（而非 NLLB/T5）

1080 Ti（Pascal 架构）只能用 llama.cpp Vulkan 后端 + GGUF 格式，而 llama.cpp 只支持 **decoder-only** 架构。
Hugging Face「翻译」榜上的 NLLB-200 / T5 / opus-mt 等均为 **encoder-decoder** 架构，llama.cpp 无法加载（无 GGUF）。
本地中英翻译最强的 decoder-only 模型就是 Qwen2.5-7B/14B（评测开源第一），故本 skill 用 Qwen 做翻译引擎。

## 工作原理

### docx / pptx（格式 100% 保留）
1. 解包（Office 文档本质是 zip）
2. 用 lxml 解析 `word/document.xml` + 页眉页脚（docx）或 `ppt/slides/slide*.xml`（pptx）
3. 按段落合并文本节点（`w:t` / `a:t`），跳过空/数字/URL
4. 分块发给 llama-server（OpenAI 兼容 API）批量翻译，数量不符自动降级逐条
5. 译文回填到段落第一个文本节点，其余清空（保留 run 结构）
6. 重新打包为 `*_zh.docx` / `*_zh.pptx`

### pdf（原文+译文双层）
1. pymupdf 提取每行文本（带坐标）
2. 分块翻译
3. 在原文 bbox 下方插入蓝色小号译文，输出 `*_zh.pdf`
4. 原文排版完全不动；扫描件（无文本层）不支持

## 注意事项

- **llama-server 会自动拉起**（默认 qwen7b），任务结束后**自动关闭本次启动的服务器**；若 8080 已有服务则复用且不动它
- 已有服务器跑的是别的模型时不会自动切换——想换模型先杀掉旧进程
- PDF 翻译质量依赖文本层；图表/公式内的文字只提取外层文本
- 中文 PDF 翻英文时，译文字体用内置 china-s，个别生僻字可能缺字形
- 批量大文件建议 `--batch 5` 更稳；模型输出条数不符会逐条重试，慢但不会错位

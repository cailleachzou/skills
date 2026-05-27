# Claude Code Skills

> 本仓库存储所有自定义 Claude Code 技能

## 技能列表

| 技能                      | 触发关键词                | 功能                                |
| ----------------------- | -------------------- | --------------------------------- |
| **bailian-cli**         | 通义、阿里云、bl            | Aliyun Model Studio CLI (`bl`) — ASR speech-to-text only (RESTRICTED); other tasks use Claude/mmx-cli |
| **batch-image-renamer** | 批量重命名、Tendo - XXX    | Renames images to `Tendo - <description>-NNN.<ext>` format, uses AI to understand image content and deduplicates conflicts |
| **cli-anything-ffmpeg** | FFmpeg、视频转换、音频处理     | AI-friendly FFmpeg CLI harness — transcoding, probing, batch processing with presets, session management, JSON output |
| **diagram-skill**       | 画图、mermaid、甘特图、时序图   | Generates and edits Mermaid diagram code — flowchart, sequence, gantt, mindmap, architecture, ER, state, C4, and more |
| **docx**                | .docx Word 文档        | Full Word doc workflow via pandoc templates, docx-js scripting, or XML editing — tracked changes, comments, footnotes, tables, images, TOC, letterhead |
| **dxf-dwg-converter**   | DWG转DXF、CAD转换、图层列表、DXF翻译    | CAD全家桶 — DWG↔DXF转换、文字提取翻译、图层管理、SVG导出、批量处理 |
| **email-eml**           | 生成邮件、.eml            | Generates .eml email files with To/Subject/Body (user adds signature in Outlook manually) |
| **markitdown**          | 转换 md、PDF 转 markdown | Converts 20+ file formats to Markdown using Microsoft MarkItDown, preserves document structure |
| **minimaxi-mmx**        | MiniMax、mmx、图片生成、TTS | Multi-modal AI CLI tool via mmx — text chat, image/video generation, TTS, music, web search, image understanding, batch analysis |
| **mmx-cli**             | mmx 命令行              | MiniMax multi-modal CLI — text, image generation, video, speech synthesis, music creation |
| **pdf**                 | PDF 操作、建筑图纸          | Full PDF operations — text/table extraction, merge/split/rotate, watermarks, forms, OCR, AI vision-based drawing review |
| **pptx**                | .pptx PowerPoint     | Template-based editing (unpack/edit/pack) or pptxgenjs from-scratch — design guidelines, color palettes, visual QA |
| **skill-creator**       | 创建 skill             | Full lifecycle skill development — drafting, subagent testing, human review, iteration, benchmarking, description optimization |
| **tendo-brand**         | Tendo、品牌样式           | Applies official Tendo Technology brand theme (colors, fonts, visual patterns) to presentations and collateral |
| **theme-factory**       | 主题、styling           | Toolkit of 10 professional color/font themes + custom theme generation for slides, docs, reports, HTML pages |
| **xlsx**                | .xlsx Excel          | Excel via openpyxl and pandas — formulas, financial color-coding, LibreOffice recalculation, zero-error requirement |

## 目录结构

```
skill-name/
├── SKILL.md          # 技能定义（YAML frontmatter + 说明）
├── scripts/          # 可执行脚本
├── references/       # 参考文档
├── assets/           # 模板、图标、字体
└── evals/            # 测试用例
```

## 工作流

```
Pandoc/markitdown  →  转换源文件为 Markdown
↓                  →  在 Obsidian 中编辑
docx/xlsx/pptx     →  生成最终交付物
minimaxi-mmx       →  生成图片/视频/语音
tendo-brand/theme  →  应用视觉样式
git               →  版本控制
```

## 快速开始

```bash
# 克隆仓库
git clone https://github.com/cailleachzou/skills.git

# 查看所有技能 — 直接看本文件即可
```

## 环境依赖

### Python 环境

**Python 路径**（Windows）：`C:\Users\59620\AppData\Local\Python\python.exe`
> 所有 Python 技能均使用此路径（不要用裸 `python`，Windows 上不存在）

| 技能 | Python 包 | 其他依赖 |
|------|-----------|---------|
| **markitdown** | `pip install 'markitdown[all]'` | markitdown CLI |
| **xlsx** | `openpyxl`, `pandas` | LibreOffice (`soffice`) |
| **pdf** | `pypdf`, `pdfplumber`, `reportlab`, `pypdfium2`, `pytesseract`, `pdf2image` | Poppler utils (`pdftotext`, `pdfimages`), qpdf |
| **pptx** | `markitdown[pptx]`, `Pillow` | LibreOffice, Poppler (`pdftoppm`), npm `pptxgenjs` |
| **docx** | — | pandoc, npm `docx`, LibreOffice, Poppler (`pdftoppm`) |
| **cli-anything-ffmpeg** | `click >= 8.0` | ffmpeg, ffprobe |
| **dxf-dwg-converter** | `ezdxf` | LibreDWG (`dwg2dxf`, `dxf2dwg`, `dwg2SVG`, `dwglayers`, `dwgread`) + 文字提取/翻译 |
| **skill-creator** | — | （Eval 工具，脚本见 skill 内部） |

### Node.js / npm 包

| 技能 | 安装命令 |
|------|---------|
| **mmx-cli** | `npm install -g mmx-cli` |
| **docx** | `npm install -g docx` |
| **pptx** | `npm install -g pptxgenjs` |

### CLI 工具

| 工具 | 技能 | 说明 |
|------|------|------|
| **pandoc** | docx | Markdown → docx 转换 |
| **LibreOffice** (`soffice`) | xlsx, pptx, docx | 公式重算、格式转换、接受修订 |
| **ffmpeg / ffprobe** | cli-anything-ffmpeg | 音视频转码 |
| **Poppler utils** (`pdftotext`, `pdftoppm`, `pdfimages`) | pptx, docx, pdf | PDF 文本提取 / 渲染 |
| **LibreDWG** | dxf-dwg-converter | DWG ↔ DXF 转换、SVG 导出、图层读取 |
| **bl** (bailian-cli) | bailian-cli | ASR 语音转文字（唯一用途）|

### 其他环境

| 工具 | 用途 |
|------|------|
| **Montserrat 字体** | tendo-brand（Google Fonts CDN） |
| **Mermaid** | diagram-skill（渲染：Obsidian / Mermaid Live Editor） |
| **MiniMax MCP** | batch-image-renamer（图片内容理解）|

### 一键安装（Python + pip）

```bash
C:\Users\59620\AppData\Local\Python\python.exe -m pip install \
  'markitdown[all]' \
  openpyxl pandas \
  pypdf pdfplumber reportlab pypdfium2 pytesseract pdf2image \
  click ezdxf
```

---

## 更新日志

- **2026/05/27** 合并 dxf-text-translate 至 dxf-dwg-converter；新增环境依赖说明；bailian-cli 限制为 ASR only
- **2026/05/26** 新增 bailian-cli、cli-anything-ffmpeg、dxf-text-translate、mmx-cli；同步 SKILLS.md 与 README.md
- **2026/05/18** 初始导入：14 个技能 + SKILLS.md 清单
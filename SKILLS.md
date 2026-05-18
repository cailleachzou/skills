# Skills Inventory

> Last updated: 2026/05/18

| Skill | Trigger keywords | What it does |
|-------|-----------------|--------------|
| **batch-image-renamer** | 批量重命名、rename photos、Tendo - XXX naming | Renames images to `Tendo - <description>-NNN.<ext>` format, uses AI to understand image content and deduplicates conflicts |
| **claude-api** | `anthropic`/`@anthropic-ai/sdk`/`claude_agent_sdk` imports, Claude API / Anthropic SDK questions | Build LLM apps using Claude API or Agent SDK — language detection, surface selection, model params, streaming/compaction |
| **diagram-skill** | 画图、mermaid、甘特图、流程图、时序图、思维导图、架构图、ER图、状态图 | Generates and edits Mermaid diagram code — flowchart, sequence, gantt, mindmap, architecture, ER, state, C4, and more |
| **docx** | .docx Word creation/editing | Full Word doc workflow via pandoc templates, docx-js scripting, or XML editing — tracked changes, comments, footnotes, tables, images, TOC, letterhead |
| **email-eml** | 生成邮件、创建 eml、写邮件、.eml | Generates .eml email files with To/Subject/Body (user adds signature in Outlook manually) |
| **markitdown** | convert files to Markdown, PDF/DOCX/XLSX to md | Converts 20+ file formats to Markdown using Microsoft MarkItDown, preserves document structure |
| **mcp-builder** | Building MCP servers, integrate external APIs | Step-by-step guide for creating MCP servers in Python/TypeScript — research, implementation, testing, evaluation |
| **minimaxi-mmx** | MiniMax、mmx、生成图片、生成视频、TTS、文字转语音、搜索信息 | Multi-modal AI CLI tool via mmx — text chat, image/video generation, TTS, music, web search, image understanding, batch analysis |
| **pdf** | PDF 操作、PDF merger、split、watermark、OCR、建筑图纸review | Full PDF operations — text/table extraction, merge/split/rotate, watermarks, forms, OCR, AI vision-based drawing review |
| **pptx** | .pptx PowerPoint creation/editing | Template-based editing (unpack/edit/pack) or pptxgenjs from-scratch — design guidelines, color palettes, visual QA |
| **skill-creator** | 创建skill、更新skill、run evals | Full lifecycle skill development — drafting, subagent testing, human review, iteration, benchmarking, description optimization |
| **tendo-brand** | Tendo、brand styling、公司文档 | Applies official Tendo Technology brand theme (colors, fonts, visual patterns) to presentations and collateral |
| **theme-factory** | Styling artifacts with theme | Toolkit of 10 professional color/font themes + custom theme generation for slides, docs, reports, HTML pages |
| **xlsx** | .xlsx Excel creation/editing | Excel via openpyxl and pandas — formulas, financial color-coding, LibreOffice recalculation, zero-error requirement |

---

## Skill Anatomy

```
skill-name/
├── SKILL.md (required)     — YAML frontmatter + markdown instructions
├── scripts/               — Executable code (bundled resources)
├── references/            — Docs loaded as needed
├── assets/                — Templates, icons, fonts
└── evals/                 — Test cases
```

## Workflow Summary

```
Pandoc/markitdown  →  convert source files to Markdown
↓                  →  edit in Obsidian
docx/xlsx/pptx     →  generate final deliverables
minimaxi-mmx       →  generate images/video/audio as needed
tendo-brand/theme →  apply visual styling
git               →  version control
```
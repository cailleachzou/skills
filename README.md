# Claude Code Skills

> 本仓库存储所有自定义 Claude Code 技能

## 技能列表

| 技能                      | 触发关键词                | 功能                                |
| ----------------------- | -------------------- | --------------------------------- |
| **bailian-cli**         | 通义、阿里云、bl            | 阿里云百炼 AI CLI（`bl`）— 仅限 ASR 语音转文字，其他任务使用 Claude/mmx-cli |
| **batch-image-renamer** | 批量重命名、Tendo - XXX    | 按 `Tendo - <描述>-NNN.<ext>` 格式批量重命名图片，AI 识别内容，自动去重冲突 |
| **cli-anything-ffmpeg** | FFmpeg、视频转换、音频处理     | FFmpeg CLI 封装 — 转码、探测、批量处理，预设管理、会话管理、JSON 输出 |
| **diagram-skill**       | 画图、mermaid、甘特图、时序图   | 生成和编辑 Mermaid 图表代码 — 流程图、时序图、甘特图、思维导图、架构图、ER 图、状态图、C4 等 |
| **docx**                | .docx Word 文档        | Word 文档完整工作流 — pandoc 模板、docx-js 脚本、XML 编辑，支持修订、批注、脚注、表格、图片、目录、信纸 |
| **dxf-dwg-converter**   | DWG转DXF、CAD转换、图层列表、DXF翻译    | CAD 全家桶 — DWG↔DXF 转换、文字提取/翻译、图层管理、SVG 导出、批量处理 |
| **email-eml**           | 生成邮件、.eml            | 生成 .eml 邮件文件，支持收件人/主题/正文（签名由用户在 Outlook 手动添加） |
| **markitdown**          | 转换 md、PDF 转 markdown | 使用 Microsoft MarkItDown 将 20+ 格式转换为 Markdown，保留文档结构 |
| **minimaxi-mmx**        | MiniMax、mmx、图片生成、TTS | MiniMax 多模态 AI CLI — 文字对话、图片/视频生成、TTS、音乐、网页搜索、图像理解、批量分析 |
| **mmx-cli**             | mmx 命令行              | MiniMax 多模态 CLI — 文字、图片生成、视频、语音合成、音乐创作 |
| **pdf**                 | PDF 操作、建筑图纸          | PDF 完整操作 — 文本/表格提取、合并/分割/旋转、水印、表单、OCR、AI 视觉图纸审查 |
| **pptx**                | .pptx PowerPoint     | 模板编辑（解包/编辑/打包）或 pptxgenjs 从零创建 — 设计指南、配色方案、视觉 QA |
| **skill-creator**       | 创建 skill             | 完整技能开发周期 — 起草、子代理测试、人工审查、迭代、基准测试、描述优化 |
| **tendo-brand**         | Tendo、品牌样式           | 应用 Tendo Technology 官方品牌主题（色彩、字体、视觉样式）至演示和文稿 |
| **theme-factory**       | 主题、styling           | 10 种专业配色/字体主题工具包 + 自定义主题生成，适用于幻灯片、文档、报告、HTML 页面 |
| **umi-ocr**             | OCR、文字识别、图片转文字     | 离线 OCR — 截图/照片/PDF 文字提取，基于 Umi-OCR HTTP API，纯文本输出 |
| **xlsx**                | .xlsx Excel          | Excel via openpyxl 和 pandas — 公式、财务配色、LibreOffice 重算、零错误要求 |

## 目录结构

```
skill-name/
├── SKILL.md          # 技能定义（YAML frontmatter + 说明）
├── scripts/          # 可执行脚本
├── references/       # 参考文档
├── assets/           # 模板、图标、字体
└── evals/            # 测试用例
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

---

## 更新日志

- **2026/06/03** diagram-skill 升级为 subagent 架构：新增 `agents/mermaid-agent.md` 路由 15 种语法、`agents/examples-agent.md` 维护范本、`examples/` 6 个范本文件；新增 `.gitignore` 屏蔽 Slidev 符号链接、Python/Node 缓存
- **2026/05/27** 合并 dxf-text-translate 至 dxf-dwg-converter；新增环境依赖说明；bailian-cli 限制为 ASR only
- **2026/05/26** 新增 bailian-cli、cli-anything-ffmpeg、dxf-text-translate、mmx-cli；同步 SKILLS.md 与 README.md
- **2026/05/18** 初始导入：14 个技能 + SKILLS.md 清单
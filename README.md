# Claude Code Skills

> 本仓库存储所有自定义 Claude Code 技能

## 技能列表

| 技能                      | 触发关键词                | 功能                                |
| ----------------------- | -------------------- | --------------------------------- |
| **ocr**               | OCR、文字识别、图片转文字、截图识字 | 离线 OCR 文字提取（Umi-OCR HTTP API）+ PDF→Markdown（marker-pdf） |
| **docling**           | Docling、文档解析、PDF解析、转Markdown、提取表格 | 文档解析与转换（IBM Docling）— PDF/DOCX/PPTX/XLSX/HTML/图片/音频 → Markdown/JSON |
| **dwg**               | DWG、DXF、CAD、图层、DXF翻译 | CAD 格式转换、文字提取/翻译、SVG 导出、批量处理（LibreDWG + ezdxf） |
| **dxf-review**        | 视觉复查、预览、DXF检查、对比原图 | DXF 视觉复查 — 渲染预览、多模态对比、自动验证 |
| **ffmpeg**            | FFmpeg、转码、视频、音频    | 音视频转码、批量处理、预设管理、会话管理 |
| **pdf2zh**            | PDF 翻译、pdf2zh       | PDF 翻译（保留 layout，23+ 引擎，含 MiMo 补丁） |
| **officecli**         | Office、docx、xlsx、pptx | 创建/检查/修改 Office 文档（.docx/.xlsx/.pptx） |
| **tendo-brand**         | Tendo、品牌样式           | 应用 Tendo Technology 官方品牌主题（色彩、字体、视觉样式）至演示和文稿 |
| **tyc-it**            | 天眼查、企业查询、尽调、股权、风险 | 天眼查 CLI「天眼一下」— 商业查询、尽调、主体核验、关联关系、司法风险等 |

## 已安装插件（Plugins）

| 插件                               | 源地址                                                                                   | 说明                                    |
| -------------------------------- | ------------------------------------------------------------------------------------- | ------------------------------------- |
| **claude-api**                   | anthropic-agent-skills                                                                | Claude API 技能 — SDK 集成、Tool Use、Streaming、Batch 等 |
| **cli-anything**                 | [HKUDS/CLI-Anything](https://github.com/HKUDS/CLI-Anything)                           | CLI 工具集成框架 — 通过 CLI-Hub 安装管理各类 CLI 技能 |
| **claude-md-management**         | claude-plugins-official                                                               | CLAUDE.md 管理工具 — 项目/用户级指令文件管理 |
| **code-review**                  | claude-plugins-official                                                               | 代码审查工具 — 多维度代码质量检查 |
| **document-skills**              | anthropic-agent-skills                                                                | 文档处理技能 — docx/pdf/pptx/xlsx 创建编辑（替代本地版本） |
| **frontend-design**              | claude-plugins-official                                                               | 前端设计辅助工具                              |
| **obsidian-skills**              | [kepano/obsidian-skills](https://github.com/kepano/obsidian-skills)                   | Obsidian 集成技能 — 笔记管理、Defuddle 网页提取等   |
| **playground**                   | claude-plugins-official                                                               | Playground 实验工具 — 交互式测试环境 |
| **skill-creator**                | claude-plugins-official                                                               | 官方技能创建工具                              |
| **superpowers**                  | claude-plugins-official                                                               | Claude Code 超级能力增强                    |

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

## 学习资料

新手上路？查看 [`learning/`](learning/) 目录：

- [`learning/knowledge/skill-overview.md`](learning/knowledge/skill-overview.md) — 技能全景图（38 个技能按功能域分类）
- [`learning/knowledge/workflow-examples.md`](learning/knowledge/workflow-examples.md) — 6 个真实工作流场景（从简单到复杂）
- [`learning/knowledge/tips-and-tricks.md`](learning/knowledge/tips-and-tricks.md) — 使用技巧、常见坑、组合模式
- [`learning/prompts/self-assessment.md`](learning/prompts/self-assessment.md) — 渐进式自测提示词（4 个关卡，直接粘贴使用）

## 环境依赖

### Python 环境

**Python 路径**（Windows）：`C:\Users\59620\AppData\Local\Python\python.exe`
> 所有 Python 技能均使用此路径（不要用裸 `python`，Windows 上不存在）

| 技能            | Python 包          | 其他依赖                                                              |
| --------------- | ----------------- | --------------------------------------------------------------------- |
| **ocr**        | —                 | Umi-OCR Rapid v2.1.5+（HTTP API 在 1224 端口）；marker-pdf venv（`C:\Users\59620\.venv-marker\`）|
| **docling**     | 独立 venv（见下）  | docling venv（`C:\Users\59620\.venv-docling\`）；⚠️ 需设 `TORCH_COMPILE_DISABLE=1 TORCHINDUCTOR_DISABLE=1` |
| **dwg**        | `ezdxf`           | LibreDWG (`dwg2dxf`, `dxf2dwg`, `dwg2SVG`, `dwglayers`, `dwgread`) + `libgcc_s_dw2-1.dll` |
| **ffmpeg**     | `click >= 8.0`    | ffmpeg, ffprobe（PATH 中）                                            |
| **pdf2zh**     | `click`, `pdfminer.six` | pdf2zh.exe（`C:\Program Files\pdf2zh\build\pdf2zh.exe`）           |

> **docling 用独立 venv**（`C:\Users\59620\.venv-docling\`，Python 3.12，勿用系统 Python）
> 已装：docling 2.118.0 + torch 2.13.0（venv 约 1.1GB，模型缓存 `~/.cache/huggingface/` 约 2GB）
> 调用：`C:\Users\59620\.venv-docling\Scripts\docling.exe convert <source> --to md --output <dir>`
> 重建：`uv venv ~/.venv-docling --python 3.12 && uv pip install --python ~/.venv-docling docling`
> wrapper：`docling/scripts/docling.ps1`（自动设环境变量 + 16GB 内存友好参数）

### CLI 工具

| 工具                                                       | 技能路径            | 说明                       |
| -------------------------------------------------------- | ----------------- | ------------------------ |
| **Umi-OCR HTTP API**                                     | `ocr/`            | 离线 OCR 文字识别（端口 1224）        |
| **LibreDWG**                                             | `dwg/`            | DWG ↔ DXF 转换、SVG 导出、图层读取    |
| **ffmpeg / ffprobe**                                     | `ffmpeg/`         | 音视频转码                    |
| **pdf2zh.exe**                                           | `pdf2zh/`         | PDF 翻译（PDFMathTranslate 引擎）|

### 其他环境

| 工具 | 用途 |
|------|------|
| **Montserrat 字体** | tendo-brand（Google Fonts CDN） |
| **Mermaid** | diagram-skill（渲染：Obsidian / Mermaid Live Editor） |

---

## 更新日志

- **2026/08/07** 新增 **docling** 技能（IBM Docling 文档解析）：PDF/DOCX/PPTX/XLSX/HTML/图片/音频 → Markdown/JSON，含表格提取、OCR、RAG 分块；独立 venv（`~/.venv-docling`，Python 3.12）；wrapper 脚本固化 `TORCH_COMPILE_DISABLE/TORCHINDUCTOR_DISABLE`（torch 2.13 无 MSVC 报错）与 16GB 内存友好参数（`--page-batch-size`）
- **2026/08/07** mimo 全面切换计量计费：CLAUDE.md 新增「多模态任务处理」章节（图像/视频/音频理解、TTS、小任务备用，curl 直连 `api.xiaomimimo.com`）；pdf2zh 的 mimo 引擎、dxf-review 的 `compare`/`read-image` 均改为读环境变量 `MIMO_API_KEY`（sk- 开头），删除 tokenplan 引用；`mimo_multimodal` 模块依赖改为标准库 urllib 直连
- **2026/08/06** 拆除 cli-anything 路由器：将 5 个 CLI 子技能（ocr / dwg / dxf-review / ffmpeg / pdf2zh）提升为顶层独立技能（自动发现）；删除 cli-anything 包及 cctv-cad、web-search-fast、mimo 子技能
- **2026/07/22** 新增 survey-photo-workflow（勘察照片整理+归档+报告）、audio-meeting-minutes（录音转会议纪要）；tendo-brand 新增 delivery-order agent（出库单生成）
- **2026/06/12** 删除本地 docx/pdf/pptx/xlsx/skill-creator/theme-factory/markitdown 七个技能，改用 Plugin 或移除；卸载 claude-hud、ecc 插件；新增 claude-api、claude-md-management、code-review、document-skills、playground 插件
- **2026/06/10** 新增「已安装插件」章节，列出 4 个第三方插件 + 3 个官方插件的源地址和说明
- **2026/06/08** 移除 bailian-cli、mmx-cli；新增 cli-anything-pdf2zh（PDF 翻译，内置 MiMo 补丁）、cli-anything-web-search-fast（联网搜索）、mimo-multimodal（小米多模态理解）；同步更新 CLAUDE.md 与 README.md
- **2026/06/03** diagram-skill 升级为 subagent 架构：新增 `agents/mermaid-agent.md` 路由 15 种语法、`agents/examples-agent.md` 维护范本、`examples/` 6 个范本文件；新增 `.gitignore` 屏蔽 Slidev 符号链接、Python/Node 缓存
- **2026/05/27** 合并 dxf-text-translate 至 dxf-dwg-converter；新增环境依赖说明；bailian-cli 限制为 ASR only
- **2026/05/26** 新增 bailian-cli、cli-anything-ffmpeg、dxf-text-translate、mmx-cli；同步 SKILLS.md 与 README.md
- **2026/05/18** 初始导入：14 个技能 + SKILLS.md 清单
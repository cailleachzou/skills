# Claude Code Skills

> 本仓库存储所有自定义 Claude Code 技能

## 技能列表

| 技能                      | 触发关键词                | 功能                                |
| ----------------------- | -------------------- | --------------------------------- |
| **cli-anything** | CLI 工具、OCR、DWG、PDF翻译、视频转码、联网搜索 | **路由器型 meta-skill** — 统一入口，自动路由到 6 个子 CLI 技能（见下方子表） |
| **batch-image-renamer** | 批量重命名、Tendo - XXX    | 按 `Tendo - <描述>-NNN.<ext>` 格式批量重命名图片，AI 识别内容，自动去重冲突 |
| **diagram-skill**       | 画图、mermaid、甘特图、时序图   | 生成和编辑 Mermaid 图表代码 — 流程图、时序图、甘特图、思维导图、架构图、ER 图、状态图、C4 等 |
| **email-eml**           | 生成邮件、.eml            | 生成 .eml 邮件文件，支持收件人/主题/正文（签名由用户在 Outlook 手动添加） |
| **mimo-multimodal**     | MiMo多模态、图片分析、音频分析、视频分析 | 小米 MiMo 多模态理解 — 图片/音频/视频内容分析，支持 auto 自动检测媒体类型 |
| **tendo-brand**         | Tendo、品牌样式           | 应用 Tendo Technology 官方品牌主题（色彩、字体、视觉样式）至演示和文稿 |

### cli-anything 子技能索引

`cli-anything/` 是个路由器（meta-skill），内部收纳 6 个子技能：

| 子技能路径 | 触发词 | 用途 | 实际命令来源 |
|----------|--------|------|------|
| `cli-anything/sub-skills/ocr/` | OCR / 文字识别 / 图片转文字 | 离线 OCR 文字提取 | Umi-OCR HTTP API（`C:\Users\59620\Downloads\Programs\Umi-OCR_Rapid_v2.1.5\`）|
| `cli-anything/sub-skills/dwg/` | DWG / DXF / CAD / 图层 | CAD 格式转换、文字提取/翻译、SVG 导出 | LibreDWG + ezdxf（`C:\Program Files\libredwg-0.13.4-win32\`）|
| `cli-anything/sub-skills/ffmpeg/` | FFmpeg / 转码 / 视频 / 音频 | 音视频转码、批量处理 | `pip install -e .` 装在外部 |
| `cli-anything/sub-skills/pdf2zh/` | PDF 翻译 / pdf2zh | PDF 翻译（保留 layout，23+ 引擎）| `pip install -e .` 装在 `C:\Program Files\pdf2zh\agent-harness` |
| `cli-anything/sub-skills/web-search-fast/` | 联网搜索 / web search | 联网搜索（多引擎回退）| `pip install -e .` 装在外部 |
| `cli-anything/sub-skills/mimo/` | 多模态 / 图片理解 / 音频理解 | MiMo 多模态内容分析 | `mimo_multimodal.py` 脚本（仓库内）|

> **架构**：所有 CLI 工具调用都从 `cli-anything` 入口走。子技能藏在 `sub-skills/` 内，Claude 启动时不会自动发现，由路由器引导加载。详见 [`docs/superpowers/specs/2026-06-15-cli-anything-router-design.md`](docs/superpowers/specs/2026-06-15-cli-anything-router-design.md)。

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

| 技能                               | Python 包                                                               | 其他依赖                                                                         |
| -------------------------------- | ---------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| **cli-anything** (路由器)        | —                                                                      | 汇总：见下方子表                                                                 |
| &nbsp;&nbsp;↳ `ocr`              | —                                                                      | Umi-OCR Rapid v2.1.5+（HTTP API 在 1224 端口）                                              |
| &nbsp;&nbsp;↳ `dwg`              | `ezdxf`                                                                | LibreDWG (`dwg2dxf`, `dxf2dwg`, `dwg2SVG`, `dwglayers`, `dwgread`) + `libgcc_s_dw2-1.dll` |
| &nbsp;&nbsp;↳ `ffmpeg`           | `click >= 8.0`                                                         | ffmpeg, ffprobe（PATH 中）                                                              |
| &nbsp;&nbsp;↳ `pdf2zh`           | `click`, `pdfminer.six`                                                | pdf2zh.exe（`C:\Program Files\pdf2zh\build\pdf2zh.exe`）                                 |
| &nbsp;&nbsp;↳ `web-search-fast`  | `camoufox`, `web-search-fast`                                          | Camoufox 浏览器（`python -m camoufox fetch`）                                     |
| &nbsp;&nbsp;↳ `mimo`             | `openai`                                                               | `MIMO_API_KEY` 环境变量                                                               |

### CLI 工具

| 工具                                                       | 子技能路径                  | 说明                       |
| -------------------------------------------------------- | ----------------------- | ------------------------ |
| **Umi-OCR HTTP API**                                     | `cli-anything/sub-skills/ocr/`    | 离线 OCR 文字识别（端口 1224）        |
| **LibreDWG**                                             | `cli-anything/sub-skills/dwg/`    | DWG ↔ DXF 转换、SVG 导出、图层读取    |
| **ffmpeg / ffprobe**                                     | `cli-anything/sub-skills/ffmpeg/` | 音视频转码                    |
| **pdf2zh.exe**                                           | `cli-anything/sub-skills/pdf2zh/` | PDF 翻译（PDFMathTranslate 引擎）|
| **web-search-fast (Camoufox)**                           | `cli-anything/sub-skills/web-search-fast/` | 联网搜索（多引擎回退）        |
| **MiMo API**                                             | `cli-anything/sub-skills/mimo/`   | 小米多模态理解                |

### 其他环境

| 工具 | 用途 |
|------|------|
| **Montserrat 字体** | tendo-brand（Google Fonts CDN） |
| **Mermaid** | diagram-skill（渲染：Obsidian / Mermaid Live Editor） |
| **mimo-multimodal** | batch-image-renamer（图片内容理解，小米 MiMo API）|

---

## 更新日志

- **2026/06/12** 删除本地 docx/pdf/pptx/xlsx/skill-creator/theme-factory/markitdown 七个技能，改用 Plugin 或移除；卸载 claude-hud、ecc 插件；新增 claude-api、claude-md-management、code-review、document-skills、playground 插件
- **2026/06/10** 新增「已安装插件」章节，列出 4 个第三方插件 + 3 个官方插件的源地址和说明
- **2026/06/08** 移除 bailian-cli、mmx-cli；新增 cli-anything-pdf2zh（PDF 翻译，内置 MiMo 补丁）、cli-anything-web-search-fast（联网搜索）、mimo-multimodal（小米多模态理解）；同步更新 CLAUDE.md 与 README.md
- **2026/06/03** diagram-skill 升级为 subagent 架构：新增 `agents/mermaid-agent.md` 路由 15 种语法、`agents/examples-agent.md` 维护范本、`examples/` 6 个范本文件；新增 `.gitignore` 屏蔽 Slidev 符号链接、Python/Node 缓存
- **2026/05/27** 合并 dxf-text-translate 至 dxf-dwg-converter；新增环境依赖说明；bailian-cli 限制为 ASR only
- **2026/05/26** 新增 bailian-cli、cli-anything-ffmpeg、dxf-text-translate、mmx-cli；同步 SKILLS.md 与 README.md
- **2026/05/18** 初始导入：14 个技能 + SKILLS.md 清单
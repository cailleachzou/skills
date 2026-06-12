# Claude Code Skills

> 本仓库存储所有自定义 Claude Code 技能

## 技能列表

| 技能                      | 触发关键词                | 功能                                |
| ----------------------- | -------------------- | --------------------------------- |
| **batch-image-renamer** | 批量重命名、Tendo - XXX    | 按 `Tendo - <描述>-NNN.<ext>` 格式批量重命名图片，AI 识别内容，自动去重冲突 |
| **cli-anything-ffmpeg** | FFmpeg、视频转换、音频处理     | FFmpeg CLI 封装 — 转码、探测、批量处理，预设管理、会话管理、JSON 输出 |
| **cli-anything-pdf2zh** | PDF翻译、pdf2zh、PDFMathTranslate | PDF 翻译 CLI — 调用 pdf2zh.exe 翻译 PDF（保留排版），支持 23+ 翻译引擎，内置小米 MiMo 翻译补丁 |
| **cli-anything-web-search-fast** | 联网搜索、web search、网页查询 | 联网搜索 CLI — Camoufox 隐身浏览器，多引擎自动回退（Google→DuckDuckGo→Bing），JSON 输出 |
| **diagram-skill**       | 画图、mermaid、甘特图、时序图   | 生成和编辑 Mermaid 图表代码 — 流程图、时序图、甘特图、思维导图、架构图、ER 图、状态图、C4 等 |
| **dxf-dwg-converter**   | DWG转DXF、CAD转换、图层列表、DXF翻译    | CAD 全家桶 — DWG↔DXF 转换、文字提取/翻译、图层管理、SVG 导出、批量处理 |
| **email-eml**           | 生成邮件、.eml            | 生成 .eml 邮件文件，支持收件人/主题/正文（签名由用户在 Outlook 手动添加） |
| **mimo-multimodal**     | MiMo多模态、图片分析、音频分析、视频分析 | 小米 MiMo 多模态理解 — 图片/音频/视频内容分析，支持 auto 自动检测媒体类型 |
| **tendo-brand**         | Tendo、品牌样式           | 应用 Tendo Technology 官方品牌主题（色彩、字体、视觉样式）至演示和文稿 |
| **umi-ocr**             | OCR、文字识别、图片转文字     | 离线 OCR — 截图/照片/PDF 文字提取，基于 Umi-OCR HTTP API，纯文本输出 |

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
| **cli-anything-ffmpeg**          | `click >= 8.0`                                                         | ffmpeg, ffprobe                                                              |
| **dxf-dwg-converter**            | `ezdxf`                                                                | LibreDWG (`dwg2dxf`, `dxf2dwg`, `dwg2SVG`, `dwglayers`, `dwgread`) + 文字提取/翻译 |
| **cli-anything-pdf2zh**          | —                                                                      | pdf2zh.exe（PDFMathTranslate Windows EXE）                                     |
| **cli-anything-web-search-fast** | `camoufox`, `web-search-fast`                                          | Camoufox 浏览器（`python -m camoufox fetch`）                                     |
| **mimo-multimodal**              | —                                                                      | MIMO_API_KEY 环境变量                                                            |

### CLI 工具

| 工具                                                       | 技能                  | 说明                       |
| -------------------------------------------------------- | ------------------- | ------------------------ |
| **ffmpeg / ffprobe**                                     | cli-anything-ffmpeg | 音视频转码                    |
| **LibreDWG**                                             | dxf-dwg-converter   | DWG ↔ DXF 转换、SVG 导出、图层读取 |

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
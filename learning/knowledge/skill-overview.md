# 技能全景图

> 49 个技能，按功能域分为 9 大类。每个技能标注触发关键词和典型场景。
> 所有技能都在本机 `~/.pi/agent/skills/` 目录，由 Claude 根据描述自动触发。

---

## 1. 文档 & 办公

| 技能                     | 触发关键词                  | 典型场景                                          |
| ---------------------- | ---------------------- | --------------------------------------------- |
| **docx**               | `.docx`、Word 文档        | 创建/编辑 Word 文档，目录、页眉、修订批注、脚注表格                 |
| **pptx**               | `.pptx`、PowerPoint、幻灯片 | 模板编辑或从零创建演示文稿，设计指南、配色方案                       |
| **xlsx**               | `.xlsx`、Excel、表格       | Excel 公式、样式、图表、数据清洗、格式转换                      |
| **pdf**                | `.pdf`、PDF 操作          | PDF 提取/合并/分割/旋转/水印/表单，OCR 扫描件                 |
| **pdf2zh**             | PDF翻译、pdf2zh           | PDF 翻译（保留排版），内置 MiMo 翻译引擎                     |
| **docs-translate**     | 翻译文档、离线翻译              | Word/PPT/PDF 批量翻译，本机模型，样式 100% 保留             |
| **docling**            | 文档解析、转Markdown、提取表格    | PDF/DOCX/PPTX/XLSX/图片 → Markdown/JSON，扫描件 OCR |
| **doc-coauthoring**    | 写文档、写方案、写规格            | 结构化协作撰写：需求→迭代→验证                              |
| **internal-comms**     | 内部通讯、状态报告、公司简报         | 状态报告、领导汇报、FAQ、事故报告、项目更新                       |
| **officecli**          | 检查 Office 文档、校对        | 分析/校对/修改 .docx/.xlsx/.pptx，找格式问题              |
| **claude-md-improver** | CLAUDE.md 优化、项目记忆      | 审计并改进仓库中的 CLAUDE.md 质量                        |

---

## 2. 视觉 & 设计

| 技能                        | 触发关键词                     | 典型场景                                      |
| ------------------------- | ------------------------- | ----------------------------------------- |
| **canvas-design**         | 海报、设计、视觉作品                | 创建精美 .png/.pdf 视觉设计                       |
| **algorithmic-art**       | 算法艺术、生成艺术、p5.js           | 用代码生成艺术：流场、粒子系统、可复现随机                     |
| **frontend-design**       | 前端、网页组件、界面                | 高质量前端界面，避免 AI 通用审美                        |
| **theme-factory**         | 主题、样式、配色                  | 10 种专业主题 + 自定义，应用到任意产物                    |
| **brand-guidelines**      | Anthropic 品牌色、品牌规范        | 应用官方品牌色/字体到产物                             |
| **web-artifacts-builder** | 复杂 HTML artifact、React 组件 | React + Tailwind + shadcn/ui 多组件 artifact |
| **playground**            | 交互式演示、explorer            | 单文件 HTML 交互工具：控件配置+实时预览                   |

---

## 3. 媒体 & 音频

| 技能 | 触发关键词 | 典型场景 |
| ---- | ---------- | -------- |
| **ffmpeg** | 视频转换、音视频处理 | 音视频转码、探测、批量处理、预设管理 |
| **ncm-dump** | `.ncm`、网易云解密 | 解密网易云加密音乐为 mp3/flac |
| **slack-gif-creator** | GIF、Slack 动图 | 生成适配 Slack 的动图 |

---

## 4. CAD & 工程

| 技能 | 触发关键词 | 典型场景 |
| ---- | ---------- | -------- |
| **dwg** | DWG、DXF、CAD、图纸 | DWG↔DXF 转换、文字提取/翻译、批量处理 |

---

## 5. 搜索 & 抓取

| 技能           | 触发关键词       | 典型场景                   |
| ------------ | ----------- | ---------------------- |
| **defuddle** | URL、网页内容、文章 | 提取网页干净 Markdown，去广告去导航 |

---

## 6. 商业 & 办公自动化

| 技能          | 触发关键词            | 典型场景                            |
| ----------- | ---------------- | ------------------------------- |
| **tyc-it**  | 天眼查、查公司、企业信息     | 企业信息查询、尽调、关联关系、风险排查、行业发现        |
| **outlook** | Outlook、日历、日程、邮件 | 添加/查询/修改日程、列出/读取邮件、创建草稿（COM 直连） |

---

## 7. AI 本地 & API

| 技能              | 触发关键词                     | 典型场景                                        |
| --------------- | ------------------------- | ------------------------------------------- |
| **local-ai**    | 本地模型、离线、省token、隐私         | 最简单任务用本机 llama.cpp（GTX 1080 Ti），免费离线        |
| **claude-api**  | Claude API、Anthropic、模型选择 | Claude API 参考：模型 id、定价、缓存、token 统计、tool use |
| **mcp-builder** | MCP 服务器、外部服务集成            | 用 FastMCP/MCP SDK 构建高质量 MCP server          |

---

## 8. Obsidian 生态

| 技能 | 触发关键词 | 典型场景 |
| ---- | ---------- | -------- |
| **obsidian-cli** | Obsidian、笔记、vault | 读写搜索管理笔记、任务、属性、插件开发 |
| **obsidian-bases** | `.base`、Bases、表格视图 | 数据库视图：表格/卡片/筛选/公式/汇总 |
| **obsidian-markdown** | wikilinks、callouts、frontmatter | Obsidian 风格 Markdown 写作 |
| **json-canvas** | `.canvas`、mind map、流程图 | 可视化画布：节点、连线、分组 |

---

## 9. 开发工作流

### 9.1 Superpowers 流程（15 个）

覆盖完整软件开发生命周期：

| 技能 | 触发关键词 | 作用 |
| ---- | ---------- | ---- |
| **using-superpowers** | （会话开始自动触发） | 元技能：建立技能发现机制 |
| **brainstorming** | creating features、需求设计 | 需求探索→设计方案→用户确认，实现前必做 |
| **writing-plans** | write plan、实现计划 | 把需求拆成可执行的分步计划 |
| **writing-skills** | write skill、创建技能 | 创建/编辑/验证技能 |
| **skill-creator** | 创建 skill | 完整技能开发周期：起草→测试→审查→迭代→基准 |
| **test-driven-development** | TDD、写测试 | 先写测试再写实现，红绿重构 |
| **subagent-driven-development** | 子代理执行计划 | 用子代理并行执行计划中的独立任务 |
| **dispatching-parallel-agents** | 并行任务、independent tasks | 2+ 个独立任务并行派发 |
| **executing-plans** | execute plan、执行计划 | 在独立会话中执行计划，带审查检查点 |
| **systematic-debugging** | bug、测试失败 | 系统化调试：先定位再修复 |
| **using-git-worktrees** | worktree、feature branch | Git 工作树隔离，避免污染主分支 |
| **requesting-code-review** | code review、合并前审查 | 完成后主动请求代码审查 |
| **receiving-code-review** | 审查反馈 | 收到反馈后，验证再实现 |
| **verification-before-completion** | verify、完成前验证 | 声明完成前必须跑验证命令 |
| **finishing-a-development-branch** | finish branch、merge、PR | 分支收尾：合并/PR/清理选项 |

### 9.2 代码分析 & 测试（2 个）

| 技能 | 触发关键词 | 典型场景 |
| ---- | ---------- | -------- |
| **graphify** | 代码库架构、知识图谱 | 把代码/文档/论文变成持久知识图谱，支持查询/路径/解释 |
| **webapp-testing** | 本地 Web 测试、Playwright | 与本地 Web 应用交互、验证 UI、截图、看日志 |

### Superpowers 典型流程

```
brainstorming（需求探索）
    → writing-plans（制定计划）
    → test-driven-development（写测试）
    → subagent-driven-development（并行实现）
    → systematic-debugging（修 bug）
    → requesting-code-review（代码审查）
    → verification-before-completion（验证）
    → finishing-a-development-branch（收尾）
```

---

## 触发机制说明

Claude Skills 的技能触发有两种方式：

### 1. 自动触发

Claude 根据你的对话内容，自动匹配 SKILL.md 中的 `description` 字段。**不需要你手动指定技能名**，只要描述清楚你要做什么。

示例：
- ❌ `帮我调用 docx 技能` — 太机械
- ✅ `帮我把这份方案生成 Word 文档，要有目录和页眉` — Claude 会自动匹配 docx 技能

### 2. 手动触发

用 `/技能名` 的方式直接调用，适合你明确知道要用哪个技能的场景。

### 触发技巧

1. **描述意图，别描述工具** — 说「我要画一个项目甘特图」而不是「帮我调用 mermaid」
2. **给够上下文** — 文件路径、输出格式、特殊要求都写上
3. **用中文就行** — 所有技能都支持中文触发
4. **复合任务拆着说** — 一个消息说清楚整个流程，Claude 会自动串联技能

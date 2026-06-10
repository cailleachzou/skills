# 技能全景图

> 38 个技能，按功能域分为 6 大类。每个技能标注触发关键词和典型场景。

---

## 1. 文档处理

| 技能                    | 来源  | 触发关键词                                | 典型场景                                                  |
| --------------------- | --- | ------------------------------------ | ----------------------------------------------------- |
| **docx**              | 自建  | `.docx`、Word 文档                      | 创建/编辑 Word 文档，支持 pandoc 模板、修订批注、脚注表格、目录信纸             |
| **pdf**               | 自建  | `.pdf`、PDF 操作、建筑图纸                   | PDF 提取/合并/分割/旋转/水印/表单，OCR 扫描件，AI 视觉审查图纸               |
| **markitdown**        | 自建  | 转换 md、PDF 转 markdown                 | 20+ 格式转 Markdown（Word/PPT/Excel/PDF/图片等）              |
| **email-eml**         | 自建  | 生成邮件、`.eml`                          | 生成 .eml 邮件文件，收件人/主题/正文                                |
| **obsidian-markdown** | 插件  | `.md` in Obsidian、wikilinks、callouts | Obsidian 风格 Markdown：wikilinks、嵌入、callout、frontmatter |

### 典型串联

```
PDF 资料 → markitdown 提取文字 → docx 生成方案文档
```

---

## 2. 图表 & 设计

| 技能                  | 来源  | 触发关键词                         | 典型场景                                            |
| ------------------- | --- | ----------------------------- | ----------------------------------------------- |
| **diagram-skill**   | 自建  | 画图、mermaid、甘特图、流程图、时序图        | 生成 Mermaid 图表：流程图、甘特图、思维导图、架构图、ER 图、状态图等 15+ 类型 |
| **tendo-brand**     | 自建  | Tendo、品牌样式                    | 应用 Tendo Technology 官方品牌主题（色彩、字体）               |
| **theme-factory**   | 自建  | 主题、styling                    | 10 种专业配色/字体主题 + 自定义主题生成                         |
| **frontend-design** | 插件  | build web components、frontend | 创建高质量前端界面，避免 AI 通用审美                            |
| **json-canvas**     | 插件  | `.canvas`、canvas、mind map     | Obsidian Canvas 文件：节点、连线、分组、可视化画布               |

### 典型串联

```
diagram-skill 生成架构图 → tendo-brand 应用品牌色 → 嵌入 docx 方案文档
```

---

## 3. 媒体 & OCR

| 技能                      | 来源  | 触发关键词               | 典型场景                       |
| ----------------------- | --- | ------------------- | -------------------------- |
| **cli-anything-ffmpeg** | 自建  | FFmpeg、视频转换、音频处理    | 音视频转码、探测、批量处理、预设管理         |
| **mimo-multimodal**     | 自建  | MiMo多模态、图片分析、音频分析   | 小米 MiMo 多模态理解：图片/音频/视频内容分析 |
| **umi-ocr**             | 自建  | OCR、文字识别、图片转文字      | 离线 OCR：截图/照片/PDF 文字提取      |
| **batch-image-renamer** | 自建  | 批量重命名、`Tendo - XXX` | AI 识别图片内容，按规范格式批量重命名       |

### 典型串联

```
截图 → umi-ocr 提取文字 → 粘贴到文档
照片 → mimo-multimodal 识别内容 → batch-image-renamer 重命名
```

---

## 4. CAD & 工程

| 技能                    | 来源  | 触发关键词              | 典型场景                                |
| --------------------- | --- | ------------------ | ----------------------------------- |
| **dxf-dwg-converter** | 自建  | DWG转DXF、CAD转换、图层列表 | DWG↔DXF 转换、文字提取/翻译、图层管理、SVG 导出、批量处理 |

### 典型串联

```
DWG 图纸 → dxf-dwg-converter 提取中文 → 翻译 → 导出新 DXF
```

---

## 5. 搜索 & 翻译

| 技能                               | 来源  | 触发关键词                            | 典型场景                                           |
| -------------------------------- | --- | -------------------------------- | ---------------------------------------------- |
| **cli-anything-web-search-fast** | 自建  | 联网搜索、web search                  | Camoufox 隐身浏览器，多引擎自动回退（Google→DuckDuckGo→Bing） |
| **cli-anything-pdf2zh**          | 自建  | PDF翻译、pdf2zh                     | PDF 翻译（保留排版），23+ 翻译引擎，内置 MiMo 翻译补丁             |
| **defuddle**                     | 插件  | URL、read web page、fetch web page | 网页内容提取，去广告去导航，干净 Markdown 输出                   |

### 典型串联

```
defuddle 提取网页内容 → 翻译 → docx 生成中文文档
```

---

## 6. 开发工作流

### 6.1 数据处理

| 技能       | 来源  | 触发关键词              | 典型场景                         |
| -------- | --- | ------------------ | ---------------------------- |
| **xlsx** | 自建  | `.xlsx`、Excel      | Excel 公式、财务配色、LibreOffice 重算 |
| **pptx** | 自建  | `.pptx`、PowerPoint | 模板编辑或从零创建，设计指南、配色方案、视觉 QA    |

### 6.2 技能管理

| 技能                | 来源    | 触发关键词    | 典型场景                       |
| ----------------- | ----- | -------- | -------------------------- |
| **skill-creator** | 自建+插件 | 创建 skill | 完整技能开发周期：起草→测试→审查→迭代→基准→优化 |

### 6.3 Obsidian 生态

| 技能                 | 来源  | 触发关键词                       | 典型场景                          |
| ------------------ | --- | --------------------------- | ----------------------------- |
| **obsidian-cli**   | 插件  | Obsidian vault、manage notes | 读写搜索管理 Obsidian 笔记、任务、属性、插件开发 |
| **obsidian-bases** | 插件  | `.base`、Bases、table view    | Obsidian 数据库视图：表格/卡片/筛选/公式/汇总 |

### 6.4 Superpowers 开发流程（14 个技能）

这是最复杂的一组技能，覆盖完整的软件开发生命周期：

| 技能                                 | 触发关键词                               | 作用                   |
| ---------------------------------- | ----------------------------------- | -------------------- |
| **brainstorming**                  | creating features、design            | 需求探索→设计方案→用户确认，实现前必做 |
| **writing-plans**                  | write plan、implementation plan      | 把需求拆成可执行的分步计划        |
| **writing-skills**                 | write skill、create skill            | 创建/编辑/验证技能           |
| **test-driven-development**        | TDD、write tests                     | 先写测试再写实现，红绿重构        |
| **subagent-driven-development**    | execute plan with subagents         | 用子代理并行执行计划中的独立任务     |
| **dispatching-parallel-agents**    | parallel tasks、independent failures | 2+ 个独立任务并行派发         |
| **executing-plans**                | execute plan、run plan               | 在独立会话中执行计划，带审查检查点    |
| **systematic-debugging**           | bug、test failure                    | 系统化调试：先定位再修复         |
| **using-git-worktrees**            | worktree、feature branch             | Git 工作树隔离，避免污染主分支    |
| **requesting-code-review**         | code review、before merge            | 完成后主动请求代码审查          |
| **receiving-code-review**          | code review feedback                | 收到审查反馈后，验证再实现        |
| **verification-before-completion** | verify、before commit                | 声明完成前必须跑验证命令         |
| **finishing-a-development-branch** | finish branch、merge、PR              | 分支收尾：合并/PR/清理选项      |
| **using-superpowers**              | （会话开始自动触发）                          | 元技能：建立技能发现机制         |

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

Claude Code 的技能触发有两种方式：

### 1. 自动触发

Claude 根据你的对话内容，自动匹配 SKILL.md 中的 `description` 字段。**不需要你手动指定技能名**，只要描述清楚你要做什么。

示例：
- ❌ `帮我调用 docx 技能` — 太机械
- ✅ `帮我把这份方案生成 Word 文档，要有目录和页眉` — Claude 会自动匹配 docx 技能

### 2. 手动触发

用 `/技能名` 的方式直接调用，适合你明确知道要用哪个技能的场景。

示例：
- `/diagram-skill` — 直接触发图表技能
- `/skill-creator` — 直接触发技能创建工具

### 触发技巧

1. **描述意图，别描述工具** — 说「我要画一个项目甘特图」而不是「帮我调用 mermaid」
2. **给够上下文** — 文件路径、输出格式、特殊要求都写上
3. **用中文就行** — 所有自建技能都支持中文触发
4. **复合任务拆着说** — 一个消息说清楚整个流程，Claude 会自动串联技能

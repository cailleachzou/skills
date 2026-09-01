# Claude Skills 学习资料

> 本目录包含本机 Claude Skills 库的学习资料，帮助你快速掌握 49 个技能的使用方法。

## 目录结构

```
learning/
├── README.md                    ← 你在这里
├── knowledge/                   # 知识部分
│   ├── skill-overview.md        # 技能全景图（按功能域分类）
│   ├── workflow-examples.md     # 真实工作流场景（简单→复杂）
│   └── tips-and-tricks.md       # 使用技巧、常见坑、组合模式
└── prompts/                     # 提示词部分
    └── self-assessment.md       # 渐进式自测提示词（可直接粘贴到 coding agent）
```

## 怎么用

### 第一步：浏览知识

1. 先看 `knowledge/skill-overview.md` — 了解有哪些技能、怎么触发
2. 再看 `knowledge/workflow-examples.md` — 看真实场景怎么串联技能
3. 最后看 `knowledge/tips-and-tricks.md` — 避坑技巧

### 第二步：自测

打开 `prompts/self-assessment.md`，把里面的提示词粘贴到一个新对话，跟着 Claude 的引导做 4 个关卡的测试。

测试完你会得到：
- 各维度能力评分
- 薄弱环节分析
- 推荐学习路径

### 第三步：实战

根据测试结果，挑 1-2 个工作流实际操作一遍，比看 10 遍文档有用。

## 技能总览

| 功能域         | 数量     | 说明                              |
| ----------- | ------ | ------------------------------- |
| 文档 & 办公     | 11     | Word/PPT/Excel/PDF/翻译/文档解析/内部沟通 |
| 视觉 & 设计     | 7      | 设计、算法艺术、前端、主题、Canvas、playground |
| 媒体 & 音频     | 3      | FFmpeg、网易云解密、Slack GIF          |
| CAD & 工程    | 1      | DWG/DXF 转换翻译                    |
| 搜索 & 抓取     | 1      | 网页内容提取                          |
| 商业 & 办公自动化  | 2      | 天眼查、Outlook 日历/邮件               |
| AI 本地 & API | 3      | 本地模型、Claude API、MCP 构建          |
| Obsidian 生态 | 4      | CLI、Bases、Markdown、Canvas       |
| 开发工作流       | 17     | Superpowers 全流程 + 代码分析 + Web 测试 |
| **合计**      | **49** |                                 |

详细分类见 `knowledge/skill-overview.md`。

## 协作机制说明

本机是多模型协作环境：
- **主模型**负责文本推理、代码、写作
- **mimo-v2.5** 负责图像/视频/音频理解、语音合成（涉及"看听说"自动调用，无需手动指定）
- **local-ai** 用于最简单的本地任务（省 token、可离线、保隐私）

学习技能时无需记忆这些分工，Claude 会自动选择。

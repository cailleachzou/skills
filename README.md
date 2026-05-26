# Claude Code Skills

> 本仓库存储所有自定义 Claude Code 技能

## 技能列表

| 技能                      | 触发关键词                | 功能                                |
| ----------------------- | -------------------- | --------------------------------- |
| **bailian-cli**         | 通义、阿里云、bl            | 阿里云百炼 AI CLI（文字对话、多模态）            |
| **batch-image-renamer** | 批量重命名、Tendo - XXX    | 批量重命名图片，AI 识别内容，自动去重冲突            |
| **cad2x-converter**     | CAD、DXF、DWG、CAD转换    | CAD 文件格式转换（DXF/DWG ↔ PDF/PNG/SVG） |
| **cli-anything-ffmpeg** | FFmpeg、视频转换、音频处理     | FFmpeg CLI 封装，支持预设、转码、批量处理        |
| **diagram-skill**       | 画图、mermaid、甘特图、时序图   | 生成 Mermaid 图表代码                   |
| **docx**                | .docx Word 文档        | Word 文档创建/编辑（pandoc、docx-js、XML）  |
| **dxf-text-translate**  | DXF翻译、CAD文字翻译        | 提取并翻译 DXF 文件中的文字实体                |
| **email-eml**           | 生成邮件、.eml            | 生成 .eml 邮件文件                      |
| **markitdown**          | 转换 md、PDF 转 markdown | 多格式文件转 Markdown                   |
| **minimaxi-mmx**        | MiniMax、mmx、图片生成、TTS | MiniMax 多模态 AI CLI                |
| **mmx-cli**             | mmx 命令行              | MiniMax 多模态 CLI（文字、图片、视频、语音、音乐）   |
| **pdf**                 | PDF 操作、建筑图纸          | PDF 处理 + 建筑图纸 AI 审查               |
| **pptx**                | .pptx PowerPoint     | PowerPoint 创建/编辑                  |
| **skill-creator**       | 创建 skill             | 开发新技能的完整工作流                       |
| **tendo-brand**         | Tendo、品牌样式           | Tendo 官方品牌主题                      |
| **theme-factory**       | 主题、styling           | 10 种预设主题 + 自定义生成                  |
| **xlsx**                | .xlsx Excel          | Excel 创建/编辑（openpyxl、pandas）      |

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

# 查看所有技能
cat SKILLS.md
```

## 更新日志

- **2026/05/26** 新增 bailian-cli、cli-anything-ffmpeg、dxf-text-translate、mmx-cli；同步 SKILLS.md 与 README.md
- **2026/05/18** 初始导入：14 个技能 + SKILLS.md 清单
---
name: pptx
description: "Internal rules for PowerPoint (.pptx) creation and editing. Provides template-based editing (unpack/edit/pack), pptxgenjs from-scratch creation, thumbnail preview, visual QA workflow, slide design guidelines, and color palette recommendations."
license: Proprietary. LICENSE.txt has complete terms
---

# PPTX 技能

## 快速参考

| 任务       | 指南                                                                                   |
| -------- | ------------------------------------------------------------------------------------ |
| 读取/分析内容  | `/c/Users/59620/AppData/Local/Python/bin/python.exe -m markitdown presentation.pptx` |
| 编辑或从模板创建 | 阅读 [editing.md](editing.md)                                                          |
| 从零开始创建   | 阅读 [pptxgenjs.md](pptxgenjs.md)                                                      |

---

## 读取内容

```bash
# 文本提取
/c/Users/59620/AppData/Local/Python/bin/python.exe -m markitdown presentation.pptx

# 可视化概览
/c/Users/59620/AppData/Local/Python/bin/python.exe scripts/thumbnail.py presentation.pptx

# 原始 XML
/c/Users/59620/AppData/Local/Python/bin/python.exe scripts/office/unpack.py presentation.pptx unpacked/
```

---

## 编辑工作流

**阅读 [editing.md](editing.md) 了解完整详情。**

1. 用 `thumbnail.py` 分析模板
2. 解包 → 操作幻灯片 → 编辑内容 → 清理 → 打包

---

## 从零开始创建

**阅读 [pptxgenjs.md](pptxgenjs.md) 了解完整详情。**

在没有模板或参考演示文稿时使用。

---

## 设计理念

**别做无聊的幻灯片。** 白底纯文字列表不会给任何人留下深刻印象。为每张幻灯片考虑以下创意。

### 开始之前

- **选择与内容契合的醒目配色方案**：配色应该为这个主题量身定制。如果把配色换到另一个完全不同的演示文稿里仍然"合适"，说明你的选择还不够具体。
- **主次分明**：一种颜色应占主导地位（60-70% 视觉权重），配合 1-2 种辅助色调和一种尖锐的强调色。永远不要给所有颜色同等权重。
- **明暗对比**：标题页和总结页用深色背景，内容页用浅色背景（"三明治"结构）。或者全程使用深色以呈现高级质感。
- **坚持一个视觉主题**：选择一个独特的元素并贯穿始终——圆角图片框、着色圆形里的图标、粗单侧边框。在每张幻灯片上保持一致。

### 配色方案

选择与主题匹配的配色——不要默认使用通用蓝色。以这些配色为灵感：

| 主题 | 主色 | 辅色 | 强调色 |
|------|------|------|--------|
| **午夜 executive** | `1E2761`（藏青） | `CADCFC`（冰蓝） | `FFFFFF`（白） |
| **森林苔藓** | `2C5F2D`（森林绿） | `97BC62`（苔藓绿） | `F5F5F5`（奶油白） |
| **珊瑚活力** | `F96167`（珊瑚红） | `F9E795`（金色） | `2F3C7E`（藏青） |
| **暖陶土** | `B85042`（陶土红） | `E7E8D1`（沙色） | `A7BEAE`（鼠尾草绿） |
| **海洋渐变** | `065A82`（深蓝） | `1C7293`（青蓝） | `21295C`（午夜蓝） |
| **炭灰极简** | `36454F`（炭灰） | `F2F2F2`（米白） | `212121`（黑） |
| **青绿信赖** | `028090`（青色） | `00A896`（海沫绿） | `02C39A`（薄荷绿） |
| **浆果奶油** | `6D2E46`（浆果紫） | `A26769`（灰玫瑰） | `ECE2D0`（奶油白） |
| **鼠尾草宁静** | `84B59F`（鼠尾草绿） | `69A297`（桉树绿） | `50808E`（石板蓝） |
| **樱桃张扬** | `990011`（樱桃红） | `FCF6F5`（米白） | `2F3C7E`（藏青） |

### 每张幻灯片

**每张幻灯片都需要一个视觉元素**——图片、图表、图标或形状。纯文字幻灯片容易被遗忘。

**版式选项：**
- 双栏（文字在左，插图在右）
- 图标+文字行（图标在着色圆形里，粗体标题，下方配描述）
- 2x2 或 2x3 网格（一边是图片，另一边是内容块网格）
- 半出血图片（占据左侧或右侧全高），叠加内容

**数据展示：**
- 大数字强调（大号数字 60-72pt，下方配小标签）
- 对比栏（之前/之后、利弊、选项并排）
- 时间轴或流程图（编号步骤、箭头）

**视觉打磨：**
- 小着色圆形内的图标，放在章节标题旁边
- 斜体强调文字用于关键数据或标语

### 字体排版

**选择有趣的字体搭配**——不要默认使用 Arial。选一个有特色的标题字体，搭配干净的正文字体。

| 标题字体 | 正文字体 |
|---------|---------|
| Georgia | Calibri |
| Arial Black | Arial |
| Calibri | Calibri Light |
| Cambria | Calibri |
| Trebuchet MS | Calibri |
| Impact | Arial |
| Palatino | Garamond |
| Consolas | Calibri |

| 元素 | 字号 |
|-----|------|
| 幻灯片标题 | 36-44pt 粗体 |
| 章节标题 | 20-24pt 粗体 |
| 正文 | 14-16pt |
| 图片说明 | 10-12pt 淡色 |

### 间距

- 最小边距 0.5"
- 内容块间距 0.3-0.5"
- 留呼吸空间——别填满每个角落

### 避免（常见错误）

- **不要重复相同的版式**——跨幻灯片变化使用分栏、卡片和强调块
- **正文不要居中**——段落和列表左对齐；仅标题居中
- **不要吝啬字号对比**——标题需要 36pt+ 才能与 14-16pt 正文明显区分
- **不要默认使用蓝色**——选择反映特定主题的配色
- **不要随机混用间距**——选择 0.3" 或 0.5" 的间距并保持一致
- **不要只设计一张幻灯片而其他都敷衍**——要么全面投入，要么全程保持简洁
- **不要做纯文字幻灯片**——添加图片、图标、图表或视觉元素；避免简单的标题+列表
- **不要忘记文本框内边距**——当线条或形状与文本边缘对齐时，在文本框上设置 `margin: 0` 或偏移形状以预留内边距
- **不要使用低对比度元素**——图标和文字都需要与背景形成强对比；避免浅色文字配浅色背景或深色文字配深色背景
- **绝对不要在标题下方使用装饰线**——这是 AI 生成幻灯片的标志；改用留白或背景色

---

## QA（必须执行）

**假设存在问题。你的工作是找到它们。**

你的第一版渲染几乎不可能完全正确。将 QA 视为找 bug，而不是确认环节。如果你第一次检查就发现零问题，说明你看得不够仔细。

### 内容 QA

```bash
/c/Users/59620/AppData/Local/Python/bin/python.exe -m markitdown output.pptx
```

检查内容缺失、拼写错误、顺序错误。

**使用模板时，检查是否有遗留的占位符文本：**

```bash
/c/Users/59620/AppData/Local/Python/bin/python.exe -m markitdown output.pptx | grep -iE "xxxx|lorem|ipsum|this.*(page|slide).*layout"
```

如果 grep 有结果，在宣布完成前修复它们。

### 视觉 QA

**⚠️ 使用子代理**——即使只有 2-3 张幻灯片。你一直盯着代码，会看到你期望的内容而非实际内容。子代理有新鲜视角。

将幻灯片转换为图片（见 [转换为图片](#converting-to-images)），然后使用以下提示：

```
对这些幻灯片进行视觉检查。假设存在问题——找到它们。

检查项：
- 元素重叠（文字穿过形状、线条穿过文字、元素堆叠）
- 文字溢出或被边缘/框边界截断
- 用于单行文字的装饰线，但标题换行成了两行
- 来源引用或页脚与上方内容冲突
- 元素间距过近（< 0.3" 空隙）或卡片/段落几乎相触
- 间隙不均匀（一处大面积空白，另一处拥挤）
- 距幻灯片边缘边距不足（< 0.5"）
- 分栏或类似元素对齐不一致
- 文字对比度低（例如，浅灰文字配奶油色背景）
- 图标对比度低（例如，深色图标配深色背景且无对比圆形衬托）
- 文本框过窄导致过度换行
- 遗留的占位符内容

每张幻灯片列出问题或关注点，即使是小问题。

读取并分析这些图片：
1. /path/to/slide-01.jpg（预期：[简要描述]）
2. /path/to/slide-02.jpg（预期：[简要描述]）

报告发现的所有问题，包括小问题。
```

### 验证循环

1. 生成幻灯片 → 转换为图片 → 检查
2. **列出发现的问题**（如未发现问题，再次更批判性地审视）
3. 修复问题
4. **重新验证受影响的幻灯片**——一次修复往往会产生另一个问题
5. 重复直至完整检查未发现新问题

**完成至少一次修复-验证循环之前，不要宣布完成。**

---

## 转换为图片

将演示文稿转换为独立的幻灯片图片以便视觉检查：

```bash
/c/Users/59620/AppData/Local/Python/bin/python.exe scripts/office/soffice.py --headless --convert-to pdf output.pptx
pdftoppm -jpeg -r 150 output.pdf slide
```

这将创建 `slide-01.jpg`、`slide-02.jpg` 等文件。

修复后重新渲染特定幻灯片：

```bash
pdftoppm -jpeg -r 150 -f N -l N output.pdf slide-fixed
```

---

## 依赖项

- `pip install "markitdown[pptx]"` - 文本提取
- `pip install Pillow` - 缩略图网格
- `npm install -g pptxgenjs` - 从零创建
- LibreOffice (`soffice`) - PDF 转换（通过 `scripts/office/soffice.py` 为沙盒环境自动配置）
- Poppler (`pdftoppm`) - PDF 转图片
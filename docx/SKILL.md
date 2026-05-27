---
name: docx
description: "Internal rules for Word (.docx) creation and editing. Provides pandoc + Tendo template workflow, docx-js programmatic creation, XML-level editing, tracked changes, comments, footnotes, tables, images, TOC, and letterhead generation."
license: Proprietary. LICENSE.txt has complete terms
template: TendoCN - Letterhead .docx
template_path: references/TendoCN - Letterhead .docx
template_styles:
  - Heading1 (centered, #0F4761, 20pt)
  - Heading2-9 (various)
  - Title, Subtitle, BodyText, Normal
  - FirstParagraph, Compact, Author, Date
  - FootnoteText, Caption, TableCaption
  - ListTable1-6 styles
template_numbering:
  - abstractNumId=0: bullet ( multilevel, 9 levels, space " ")
  - abstractNumId=1: decimal (multilevel, 9 levels, %1./%2. etc.)
  - numId=1 → abstractNumId=0 (bullet)
  - numId=2 → abstractNumId=1 (decimal, with lvlOverride restart)
template_settings:
  - defaultTabStop: 720 DXA
  - drawingGrid: 360 DXA spacing
  - footnote restart: each section
  - compatibilityMode: 12
---

# DOCX 文件的创建、编辑与分析

## 概述

`.docx` 文件是一个 ZIP 压缩包，内部包含 XML 文件。

## 快速参考

| 任务 | 方法 |
|------|------|
| 读取/分析内容 | `pandoc` 或解压后查看原始 XML |
| 创建新文档 | `docx-js`（完整程序化控制） |
| 编辑现有文档 | 解压 → 编辑 XML → 重新打包 - 详见下方「编辑现有文档」章节 |

### 将 .doc 转换为 .docx

旧版 `.doc` 文件需先转换才能编辑：

```bash
/c/Users/59620/AppData/Local/Python/bin/python.exe scripts/office/soffice.py --headless --convert-to docx document.doc
```

### 读取内容

```bash
# 提取文本（含修订痕迹）
pandoc --track-changes=all document.docx -o output.md

# 访问原始 XML
/c/Users/59620/AppData/Local/Python/bin/python.exe scripts/office/unpack.py document.docx unpacked/
```

### 转换为图片

```bash
/c/Users/59620/AppData/Local/Python/bin/python.exe scripts/office/soffice.py --headless --convert-to pdf document.docx
pdftoppm -jpeg -r 150 document.pdf page
```

### 接受修订痕迹

生成一份干净文档，所有修订痕迹均被接受（需要 LibreOffice）：

```bash
/c/Users/59620/AppData/Local/Python/bin/python.exe scripts/accept_changes.py input.docx output.docx
```

---

## 创建新文档

大多数文档使用 **pandoc** 搭配模板——它能完美保留模板样式。仅在需要程序化控制时（动态内容、复杂表格、图片）使用 **docx-js**。安装方式：`npm install -g docx`

### Pandoc（推荐——保留所有模板样式）

**⚠️ 转换前：先去掉手动标题编号。**
Word 会根据标题样式自动生成编号。如果 MD 里写 `## 1.1 设计范围`，Word 会显示"1.1 设计范围"（编号重复）。先运行剥离脚本：

```bash
python scripts/strip_heading_numbers.py input.md input_clean.md
```

然后转换：

```bash
pandoc input_clean.md -o output.docx --reference-doc=references/TendoCN\ -\ Letterhead.docx
```

**⚠️ 关键：pandoc 转换后必须运行 `apply_template.py`。**
Pandoc 使用 `--reference-doc` 能正确应用段落样式，但其列表 numId 与模板的冲突。需运行修复脚本重新映射：

```bash
cd <skill-dir>
/c/Users/59620/AppData/Local/Python/bin/python.exe scripts/apply_template.py output.docx output_fixed.docx
/c/Users/59620/AppData/Local/Python/bin/python.exe scripts/apply_table_borders.py output_fixed.docx output_final.docx
```

**`apply_template.py` 的作用：**
- 解析 `word/numbering.xml`，找出 pandoc 生成的 `<w:num>` 条目
- 对于 abstractNum 中 `numFmt="bullet"` 的 num → 重新映射到模板的 `numId=1`
- 对于 abstractNum 中 `numFmt="decimal"` 的 num → 重新映射到模板的 `numId=2`
- 相应替换 `document.xml` 中所有的 `<w:numId w:val="...">`
- 重新打包并验证

**继承的模板样式：**
- 段落样式：Heading1（居中、#0F4761、20pt）、Heading2–9、Title、Subtitle、BodyText、Normal、FirstParagraph、Author、Date、Caption、FootnoteText 等
- 列表样式：bullet（numId=1）和 decimal（numId=2），均支持 9 级
- 默认字体：主题字体（minorHAnsi）、12pt；段后距=200 DXA
- 制表位：720 DXA；绘图网格：360 DXA

### docx-js（用于程序化/复杂文档）

```javascript
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun,
        Header, Footer, AlignmentType, PageOrientation, LevelFormat, ExternalHyperlink,
        InternalHyperlink, Bookmark, FootnoteReferenceRun, PositionalTab,
        TabStopType, TabStopPosition, Column, SectionType,
        TableOfContents, HeadingLevel, BorderStyle, WidthType, ShadingType,
        VerticalAlign, PageNumber, PageBreak } = require('docx');

const doc = new Document({ sections: [{ children: [/* 内容 */] }] });
Packer.toBuffer(doc).then(buffer => fs.writeFileSync("doc.docx", buffer));
```

### 验证
文件创建后需验证。若验证失败，解压、修复 XML、重新打包。
```bash
/c/Users/59620/AppData/Local/Python/bin/python.exe scripts/office/validate.py doc.docx
```

### 页面尺寸

```javascript
// 关键：docx-js 默认 A4，非 US Letter
// 为保证一致，需显式设置页面尺寸
sections: [{
  properties: {
    page: {
      size: {
        width: 12240,   // 8.5 英寸（DXA）
        height: 15840   // 11 英寸（DXA）
      },
      margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } // 1 英寸边距
    }
  },
  children: [/* 内容 */]
}]
```

**常见纸张尺寸（DXA 单位，1440 DXA = 1 英寸）：**

| 纸张 | 宽度 | 高度 | 内容宽度（1" 边距） |
|------|------|------|-------------------|
| US Letter | 12,240 | 15,840 | 9,360 |
| A4（默认） | 11,906 | 16,838 | 9,026 |

**横向页面：** docx-js 在内部交换宽高，传入纵向尺寸让其处理：
```javascript
size: {
  width: 12240,   // 短边作为宽度传入
  height: 15840,  // 长边作为高度传入
  orientation: PageOrientation.LANDSCAPE  // docx-js 在 XML 中交换两者
},
// 内容宽度 = 15840 - 左边距 - 右边距（使用长边）
```

### 样式（覆盖内置标题样式）

默认字体使用 Arial（广泛支持）。标题保持黑色以保证可读性。

```javascript
const doc = new Document({
  styles: {
    default: { document: { run: { font: "Arial", size: 24 } } }, // 12pt 默认
    paragraphStyles: [
      // 重要：使用精确 ID 来覆盖内置样式
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: "Arial" },
        paragraph: { spacing: { before: 240, after: 240 }, outlineLevel: 0 } }, // outlineLevel 为 TOC 必需
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, font: "Arial" },
        paragraph: { spacing: { before: 180, after: 180 }, outlineLevel: 1 } },
    ]
  },
  sections: [{
    children: [
      new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("标题")] }),
    ]
  }]
});
```

### 列表（绝对不要用 unicode 项目符号）

```javascript
// ❌ 错误 —— 禁止手动插入项目符号字符
new Paragraph({ children: [new TextRun("• 列表项")] })  // 错误
new Paragraph({ children: [new TextRun("\u2022 列表项")] })  // 错误

// ✅ 正确 —— 使用带 LevelFormat.BULLET 的编号配置
const doc = new Document({
  numbering: {
    config: [
      { reference: "bullets",
        levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "numbers",
        levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    ]
  },
  sections: [{
    children: [
      new Paragraph({ numbering: { reference: "bullets", level: 0 },
        children: [new TextRun("项目符号列表项")] }),
      new Paragraph({ numbering: { reference: "numbers", level: 0 },
        children: [new TextRun("编号列表项")] }),
    ]
  }]
});

// ⚠️ 每个 reference 创建独立的编号序列
// 相同 reference = 连续编号 (1,2,3 然后 4,5,6)
// 不同 reference = 重新编号 (1,2,3 然后 1,2,3)
```

### 表格

**Pandoc 生成的表格必须运行 `apply_table_borders.py`。**
Pandoc 的 `Table` 样式仅对首行（firstRow）定义边框，数据行单元格的边框全部缺失。运行边框修复脚本注入所有缺失的 `<w:tcBorders>`：

```bash
python scripts/apply_table_borders.py output_fixed.docx output_final.docx
```

**关键：表格需要双向宽度设置**——表格上设置 `columnWidths`，同时每个单元格上设置 `width`。两者缺一不可，否则在不同平台上渲染异常。

```javascript
// 关键：务必设置表格宽度以保证渲染一致
// 关键：使用 ShadingType.CLEAR（非 SOLID）避免黑色背景
const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: border, bottom: border, left: border, right: border };

new Table({
  width: { size: 9360, type: WidthType.DXA }, // 始终使用 DXA（百分比在 Google Docs 中失效）
  columnWidths: [4680, 4680], // 必须与表格宽度之和相等（DXA: 1440 = 1 英寸）
  rows: [
    new TableRow({
      children: [
        new TableCell({
          borders,
          width: { size: 4680, type: WidthType.DXA }, // 每个单元格也要设置
          shading: { fill: "D5E8F0", type: ShadingType.CLEAR }, // CLEAR 而非 SOLID
          margins: { top: 80, bottom: 80, left: 120, right: 120 }, // 单元格内边距（内部，不加到宽度上）
          children: [new Paragraph({ children: [new TextRun("单元格")] })]
        })
      ]
    })
  ]
})
```

**表格宽度计算：**

始终使用 `WidthType.DXA`——`WidthType.PERCENTAGE` 在 Google Docs 中会失效。

```javascript
// 表格宽度 = columnWidths 之和 = 内容宽度
// US Letter 1" 边距：12240 - 2880 = 9360 DXA
width: { size: 9360, type: WidthType.DXA },
columnWidths: [7000, 2360]  // 必须与表格宽度之和相等
```

**宽度规则：**
- **始终使用 `WidthType.DXA`**——禁用 `WidthType.PERCENTAGE`（与 Google Docs 不兼容）
- 表格宽度必须等于 `columnWidths` 之和
- 单元格 `width` 必须与对应的 `columnWidth` 一致
- 单元格 `margins` 是内部边距——它们压缩内容区域，不增加单元格宽度
- 满宽表格：使用内容宽度（页面宽度减去左右边距）

### 图片

```javascript
// 关键：type 参数是必需的
new Paragraph({
  children: [new ImageRun({
    type: "png", // 必需：png, jpg, jpeg, gif, bmp, svg
    data: fs.readFileSync("image.png"),
    transformation: { width: 200, height: 150 },
    altText: { title: "标题", description: "描述", name: "名称" } // 三者均必需
  })]
})
```

### 分页符

```javascript
// 关键：PageBreak 必须放在 Paragraph 内
new Paragraph({ children: [new PageBreak()] })

// 或使用 pageBreakBefore
new Paragraph({ pageBreakBefore: true, children: [new TextRun("新页面")] })
```

### 超链接

```javascript
// 外部链接
new Paragraph({
  children: [new ExternalHyperlink({
    children: [new TextRun({ text: "点击这里", style: "Hyperlink" })],
    link: "https://example.com",
  })]
})

// 内部链接（书签 + 引用）
// 1. 在目标位置创建书签
new Paragraph({ heading: HeadingLevel.HEADING_1, children: [
  new Bookmark({ id: "chapter1", children: [new TextRun("第一章")] }),
]})
// 2. 创建指向它的链接
new Paragraph({ children: [new InternalHyperlink({
  children: [new TextRun({ text: "参见第一章", style: "Hyperlink" })],
  anchor: "chapter1",
})]})
```

### 脚注

```javascript
const doc = new Document({
  footnotes: {
    1: { children: [new Paragraph("来源：2024 年度报告")] },
    2: { children: [new Paragraph("方法论见附录")] },
  },
  sections: [{
    children: [new Paragraph({
      children: [
        new TextRun("收入增长 15%"),
        new FootnoteReferenceRun(1),
        new TextRun("（使用调整后指标）"),
        new FootnoteReferenceRun(2),
      ],
    })]
  }]
});
```

### 制表位

```javascript
// 同一行右对齐文本（例如日期与标题对侧）
new Paragraph({
  children: [
    new TextRun("公司名称"),
    new TextRun("\t2025 年 1 月"),
  ],
  tabStops: [{ type: TabStopType.RIGHT, position: TabStopPosition.MAX }],
})

// 点线引导（例如目录风格）
new Paragraph({
  children: [
    new TextRun("目录"),
    new TextRun({ children: [
      new PositionalTab({
        alignment: PositionalTabAlignment.RIGHT,
        relativeTo: PositionalTabRelativeTo.MARGIN,
        leader: PositionalTabLeader.DOT,
      }),
      "3",
    ]}),
  ],
})
```

### 多栏布局

```javascript
// 等宽栏
sections: [{
  properties: {
    column: {
      count: 2,          // 栏数
      space: 720,        // 栏间距（DXA，720 = 0.5 英寸）
      equalWidth: true,
      separate: true,    // 栏间竖线
    },
  },
  children: [/* 内容自然跨栏流动 */]
}]

// 自定义宽度栏（equalWidth 必须为 false）
sections: [{
  properties: {
    column: {
      equalWidth: false,
      children: [
        new Column({ width: 5400, space: 720 }),
        new Column({ width: 3240 }),
      ],
    },
  },
  children: [/* 内容 */]
}]
```

使用 `type: SectionType.NEXT_COLUMN` 的新分节来强制栏分隔。

### 目录

```javascript
// 关键：标题必须仅使用 HeadingLevel——不可用自定义样式
new TableOfContents("目录", { hyperlink: true, headingStyleRange: "1-3" })
```

### 页眉/页脚

```javascript
sections: [{
  properties: {
    page: { margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } // 1440 = 1 英寸
  },
  headers: {
    default: new Header({ children: [new Paragraph({ children: [new TextRun("页眉")] })] })
  },
  footers: {
    default: new Footer({ children: [new Paragraph({
      children: [new TextRun("第 "), new TextRun({ children: [PageNumber.CURRENT] }), new TextRun(" 页")]
    })] })
  },
  children: [/* 内容 */]
}]
```

### docx-js 关键规则

- **显式设置页面尺寸** - docx-js 默认 A4；美式文档使用 US Letter（12240 x 15840 DXA）
- **横向：传入纵向尺寸** - docx-js 在内部交换宽高；短边作为 `width`，长边作为 `height`，并设置 `orientation: PageOrientation.LANDSCAPE`
- **绝对不要用 `\n`** - 使用单独的 Paragraph 元素
- **绝对不要用 unicode 项目符号** - 使用带 `LevelFormat.BULLET` 的编号配置
- **PageBreak 必须在 Paragraph 内** - 单独放置会生成无效 XML
- **ImageRun 需要 `type`** - 始终指定 png/jpg 等
- **始终用 DXA 设置表格 `width`** - 禁用 `WidthType.PERCENTAGE`（在 Google Docs 中失效）
- **表格需要双向宽度** - `columnWidths` 数组和单元格 `width` 两者必须匹配
- **表格宽度 = columnWidths 之和** - DXA 场景需确保精确相加
- **始终添加单元格边距** - 使用 `margins: { top: 80, bottom: 80, left: 120, right: 120 }` 保证可读性
- **使用 `ShadingType.CLEAR`** - 表格阴影禁止使用 SOLID
- **绝对不要用表格作分隔线/标尺** - 单元格有最小高度，会渲染为空框（在页眉/页脚中亦然）；改用 Paragraph 的 `border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "2E75B6", space: 1 } }`。双栏页脚使用制表位（参见制表位章节），不要用表格
- **目录仅限 HeadingLevel** - 标题段落不可使用自定义样式
- **覆盖内置样式** - 使用精确 ID："Heading1"、"Heading2" 等
- **包含 `outlineLevel`** - TOC 必需（H1 对应 0，H2 对应 1，以此类推）

---

## 编辑现有文档

**按顺序执行以下三个步骤。**

### 第一步：解压
```bash
/c/Users/59620/AppData/Local/Python/bin/python.exe scripts/office/unpack.py document.docx unpacked/
```
提取 XML、格式化、合并相邻 runs、将智能引号转换为 XML 实体（`&#x201C;` 等），以便编辑后保留。使用 `--merge-runs false` 可跳过 run 合并。

### 第二步：编辑 XML

编辑 `unpacked/word/` 下的文件。模式参见下方 XML 参考。

**使用"Claude"作为修订和批注的作者**，除非用户明确指定其他姓名。

**直接使用 Edit 工具进行字符串替换。不要写 Python 脚本。** 脚本会引入不必要的复杂性。Edit 工具精确显示替换内容。

**关键：新内容使用智能引号。** 添加含撇号或引号的文本时，使用 XML 实体生成智能引号：
```xml
<!-- 专业排版使用以下实体 -->
<w:t>此处&#x2019;s 一个引述：&#x201C;你好&#x201D;</w:t>
```
| 实体 | 字符 |
|------|------|
| `&#x2018;` | ' （左单引号） |
| `&#x2019;` | ' （右单引号 / 撇号） |
| `&#x201C;` | " （左双引号） |
| `&#x201D;` | " （右双引号） |

**添加批注：** 使用 `comment.py` 处理跨多个 XML 文件的模板（文本需预先转义为 XML）：
```bash
/c/Users/59620/AppData/Local/Python/bin/python.exe scripts/comment.py unpacked/ 0 "批注文本（含 &amp; 和 &#x2019;）"
/c/Users/59620/AppData/Local/Python/bin/python.exe scripts/comment.py unpacked/ 1 "回复文本" --parent 0  # 回复批注 0
/c/Users/59620/AppData/Local/Python/bin/python.exe scripts/comment.py unpacked/ 0 "文本" --author "自定义作者"  # 自定义作者名
```
然后在 document.xml 中添加标记（参见 XML 参考中的批注部分）。

### 第三步：打包
```bash
/c/Users/59620/AppData/Local/Python/bin/python.exe scripts/office/pack.py unpacked/ output.docx --original document.docx
```
验证并自动修复、压缩 XML、创建 DOCX。使用 `--validate false` 跳过验证。

**自动修复范围：**
- `durableId` >= 0x7FFFFFFF（重新生成有效 ID）
- 含空白的 `<w:t>` 缺少 `xml:space="preserve"`

**自动修复无法处理：**
- 格式错误的 XML、元素嵌套无效、缺少关系、模式违规

### 常见陷阱

- **替换整个 `<w:r>` 元素**：添加修订时，用 `<w:del>...<w:ins>...` 作为同级元素替换整个 `<w:r>...</w:r>` 块。禁止在 run 内部注入修订标签。
- **保留 `<w:rPr>` 格式**：将原始 run 的 `<w:rPr>` 块复制到修订 run 中，以保持粗体、字号等格式。

---

## XML 参考

### 模式合规

- **`<w:pPr>` 中元素顺序**：`<w:pStyle>`、`<w:numPr>`、`<w:spacing>`、`<w:ind>`、`<w:jc>`、`<w:rPr>` 最后
- **空白**：含首尾空格的 `<w:t>` 需添加 `xml:space="preserve"`
- **RSID**：必须是 8 位十六进制（如 `00AB1234`）

### 修订痕迹

**插入：**
```xml
<w:ins w:id="1" w:author="Claude" w:date="2025-01-01T00:00:00Z">
  <w:r><w:t>插入的文本</w:t></w:r>
</w:ins>
```

**删除：**
```xml
<w:del w:id="2" w:author="Claude" w:date="2025-01-01T00:00:00Z">
  <w:r><w:delText>删除的文本</w:delText></w:r>
</w:del>
```

**在 `<w:del>` 内**：使用 `<w:delText>` 替代 `<w:t>`，使用 `<w:delInstrText>` 替代 `<w:instrText>`。

**最小化编辑**——仅标记变化部分：
```xml
<!-- 将"30 天"改为"60 天" -->
<w:r><w:t>合同期限为 </w:t></w:r>
<w:del w:id="1" w:author="Claude" w:date="...">
  <w:r><w:delText>30</w:delText></w:r>
</w:del>
<w:ins w:id="2" w:author="Claude" w:date="...">
  <w:r><w:t>60</w:t></w:r>
</w:ins>
<w:r><w:t> 天。</w:t></w:r>
```

**删除整段/列表项**——当移除段落全部内容时，同时标记段落标记为已删除，使其与下一段合并。在 `<w:pPr><w:rPr>` 内添加 `<w:del/>`：
```xml
<w:p>
  <w:pPr>
    <w:numPr>...</w:numPr>  <!-- 列表编号（如有） -->
    <w:rPr>
      <w:del w:id="1" w:author="Claude" w:date="2025-01-01T00:00:00Z"/>
    </w:rPr>
  </w:pPr>
  <w:del w:id="2" w:author="Claude" w:date="2025-01-01T00:00:00Z">
    <w:r><w:delText>整段内容被删除...</w:delText></w:r>
  </w:del>
</w:p>
```
若 `<w:pPr><w:rPr>` 内没有 `<w:del/>`，接受修订后会留下空段落/列表项。

**拒绝另一作者的插入**——在其插入内嵌套删除：
```xml
<w:ins w:author="Jane" w:id="5">
  <w:del w:author="Claude" w:id="10">
    <w:r><w:delText>他们插入的文本</w:delText></w:r>
  </w:del>
</w:ins>
```

**恢复另一作者的删除**——在其后添加插入（不要修改他们的删除）：
```xml
<w:del w:author="Jane" w:id="5">
  <w:r><w:delText>删除的文本</w:delText></w:r>
</w:del>
<w:ins w:author="Claude" w:id="10">
  <w:r><w:t>删除的文本</w:t></w:r>
</w:ins>
```

### 批注

运行 `comment.py`（参见第二步）后，在 document.xml 中添加标记。回复使用 `--parent` 标志并嵌套在父批注内。

**关键：`<w:commentRangeStart>` 和 `<w:commentRangeEnd>` 是 `<w:r>` 的同级元素，绝不在 `<w:r>` 内部。**

```xml
<!-- 批注标记是 w:p 的直接子级，绝不在 w:r 内部 -->
<w:commentRangeStart w:id="0"/>
<w:del w:id="1" w:author="Claude" w:date="2025-01-01T00:00:00Z">
  <w:r><w:delText>已删除</w:delText></w:r>
</w:del>
<w:r><w:t> 更多文本</w:t></w:r>
<w:commentRangeEnd w:id="0"/>
<w:r><w:rPr><w:rStyle w:val="CommentReference"/></w:rPr><w:commentReference w:id="0"/></w:r>

<!-- 批注 0，含嵌套的回复批注 1 -->
<w:commentRangeStart w:id="0"/>
  <w:commentRangeStart w:id="1"/>
  <w:r><w:t>文本</w:t></w:r>
  <w:commentRangeEnd w:id="1"/>
<w:commentRangeEnd w:id="0"/>
<w:r><w:rPr><w:rStyle w:val="CommentReference"/></w:rPr><w:commentReference w:id="0"/></w:r>
<w:r><w:rPr><w:rStyle w:val="CommentReference"/></w:rPr><w:commentReference w:id="1"/></w:r>
```

### 图片

1. 将图片文件添加到 `word/media/`
2. 在 `word/_rels/document.xml.rels` 中添加关系：
```xml
<Relationship Id="rId5" Type=".../image" Target="media/image1.png"/>
```
3. 在 `[Content_Types].xml` 中添加内容类型：
```xml
<Default Extension="png" ContentType="image/png"/>
```
4. 在 document.xml 中引用：
```xml
<w:drawing>
  <wp:inline>
    <wp:extent cx="914400" cy="914400"/>  <!-- EMUs：914400 = 1 英寸 -->
    <a:graphic>
      <a:graphicData uri=".../picture">
        <pic:pic>
          <pic:blipFill><a:blip r:embed="rId5"/></pic:blipFill>
        </pic:pic>
      </a:graphicData>
    </a:graphic>
  </wp:inline>
</w:drawing>
```

---

## 依赖项

- **pandoc**：使用 `--reference-doc` 模板将 Markdown 转换为 docx
- **apply_template.py**：后处理 pandoc 输出，将列表 numId 重新映射到模板定义
- **docx**：`npm install -g docx`（新文档，完整程序化控制）
- **LibreOffice**：PDF 转换（通过 `scripts/office/soffice.py` 为沙盒环境自动配置）
- **Poppler**：`pdftoppm` 用于图片生成
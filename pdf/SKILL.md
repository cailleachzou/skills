---
name: pdf
description: Use this skill whenever the user wants to do anything with PDF files. This includes reading or extracting text/tables from PDFs, combining or merging multiple PDFs into one, splitting PDFs apart, rotating pages, adding watermarks, creating new PDFs, filling PDF forms, encrypting/decrypting PDFs, extracting images, OCR on scanned PDFs, and AI vision-based review of PDF drawings/plans (e.g., checking architectural or ELV drawings with dual-modality text extraction + visual verification). If the user mentions a .pdf file, asks to "review" or "check" a drawing, or wants AI to verify content against a PDF, use this skill.
license: Proprietary. LICENSE.txt has complete terms
---

# PDF 处理指南

> **Windows Python 路径修复**：在这台机器上，请使用 `/c/Users/59620/AppData/Local/Python/bin/python.exe` 而非裸 `python` 命令，以避免 Windows 应用商店重定向问题。

## 概述

本指南涵盖使用 Python 库和命令行工具进行 PDF 处理的基本操作。高级功能、JavaScript 库和详细示例请参见 REFERENCE.md。如需填写 PDF 表单，请阅读 FORMS.md 并按其说明操作。

## 快速上手

```python
from pypdf import PdfReader, PdfWriter

# 读取 PDF
reader = PdfReader("document.pdf")
print(f"页数: {len(reader.pages)}")

# 提取文本
text = ""
for page in reader.pages:
    text += page.extract_text()
```

## Python 库

### pypdf - 基本操作

#### 合并 PDF
```python
from pypdf import PdfWriter, PdfReader

writer = PdfWriter()
for pdf_file in ["doc1.pdf", "doc2.pdf", "doc3.pdf"]:
    reader = PdfReader(pdf_file)
    for page in reader.pages:
        writer.add_page(page)

with open("merged.pdf", "wb") as output:
    writer.write(output)
```

#### 拆分 PDF
```python
reader = PdfReader("input.pdf")
for i, page in enumerate(reader.pages):
    writer = PdfWriter()
    writer.add_page(page)
    with open(f"page_{i+1}.pdf", "wb") as output:
        writer.write(output)
```

#### 提取元数据
```python
reader = PdfReader("document.pdf")
meta = reader.metadata
print(f"标题: {meta.title}")
print(f"作者: {meta.author}")
print(f"主题: {meta.subject}")
print(f"创建者: {meta.creator}")
```

#### 旋转页面
```python
reader = PdfReader("input.pdf")
writer = PdfWriter()

page = reader.pages[0]
page.rotate(90)  # 顺时针旋转 90 度
writer.add_page(page)

with open("rotated.pdf", "wb") as output:
    writer.write(output)
```

### pdfplumber - 文本和表格提取

#### 保留布局提取文本
```python
import pdfplumber

with pdfplumber.open("document.pdf") as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        print(text)
```

#### 提取表格
```python
with pdfplumber.open("document.pdf") as pdf:
    for i, page in enumerate(pdf.pages):
        tables = page.extract_tables()
        for j, table in enumerate(tables):
            print(f"第 {i+1} 页的表格 {j+1}:")
            for row in table:
                print(row)
```

#### 高级表格提取
```python
import pandas as pd

with pdfplumber.open("document.pdf") as pdf:
    all_tables = []
    for page in pdf.pages:
        tables = page.extract_tables()
        for table in tables:
            if table:  # 检查表格是否非空
                df = pd.DataFrame(table[1:], columns=table[0])
                all_tables.append(df)

# 合并所有表格
if all_tables:
    combined_df = pd.concat(all_tables, ignore_index=True)
    combined_df.to_excel("extracted_tables.xlsx", index=False)
```

### reportlab - 创建 PDF

#### 创建基本 PDF
```python
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

c = canvas.Canvas("hello.pdf", pagesize=letter)
width, height = letter

# 添加文本
c.drawString(100, height - 100, "Hello World!")
c.drawString(100, height - 120, "This is a PDF created with reportlab")

# 添加一条线
c.line(100, height - 140, 400, height - 140)

# 保存
c.save()
```

#### 创建多页 PDF
```python
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet

doc = SimpleDocTemplate("report.pdf", pagesize=letter)
styles = getSampleStyleSheet()
story = []

# 添加内容
title = Paragraph("Report Title", styles['Title'])
story.append(title)
story.append(Spacer(1, 12))

body = Paragraph("This is the body of the report. " * 20, styles['Normal'])
story.append(body)
story.append(PageBreak())

# 第 2 页
story.append(Paragraph("Page 2", styles['Heading1']))
story.append(Paragraph("Content for page 2", styles['Normal']))

# 生成 PDF
doc.build(story)
```

#### 下标和上标

**重要**：请勿在 ReportLab PDF 中使用 Unicode 下标/上标字符（₀₁₂₃₄₅₆₇₈₉、⁰¹²³⁴⁵⁆⁸⁹）。内置字体不包含这些字形，会导致渲染为实心黑块。

请改用 ReportLab 的 XML 标记在 Paragraph 对象中：
```python
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet

styles = getSampleStyleSheet()

# 下标：使用 <sub> 标签
chemical = Paragraph("H<sub>2</sub>O", styles['Normal'])

# 上标：使用 <super> 标签
squared = Paragraph("x<super>2</super> + y<super>2</super>", styles['Normal'])
```

对于 Canvas 绘制的文本（非 Paragraph 对象），请手动调整字体大小和位置，而非使用 Unicode 下标/上标。

## 命令行工具

### pdftotext (poppler-utils)
```bash
# 提取文本
pdftotext input.pdf output.txt

# 保留布局提取文本
pdftotext -layout input.pdf output.txt

# 提取指定页面
pdftotext -f 1 -l 5 input.pdf output.txt  # 第 1-5 页
```

### qpdf
```bash
# 合并 PDF
qpdf --empty --pages file1.pdf file2.pdf -- merged.pdf

# 拆分页面
qpdf input.pdf --pages . 1-5 -- pages1-5.pdf
qpdf input.pdf --pages . 6-10 -- pages6-10.pdf

# 旋转页面
qpdf input.pdf output.pdf --rotate=+90:1  # 将第 1 页旋转 90 度

# 移除密码
qpdf --password=mypassword --decrypt encrypted.pdf decrypted.pdf
```

### pdftk（如果有）
```bash
# 合并
pdftk file1.pdf file2.pdf cat output merged.pdf

# 拆分
pdftk input.pdf burst

# 旋转
pdftk input.pdf rotate 1east output rotated.pdf
```

## 常见任务

### 从扫描件 PDF 中提取文本
```python
# 需要：pip install pytesseract pdf2image
import pytesseract
from pdf2image import convert_from_path

# 将 PDF 转换为图片
images = convert_from_path('scanned.pdf')

# 对每页进行 OCR
text = ""
for i, image in enumerate(images):
    text += f"第 {i+1} 页:\n"
    text += pytesseract.image_to_string(image)
    text += "\n\n"

print(text)
```

### 添加水印
```python
from pypdf import PdfReader, PdfWriter

# 创建水印（或加载已有）
watermark = PdfReader("watermark.pdf").pages[0]

# 应用到所有页面
reader = PdfReader("document.pdf")
writer = PdfWriter()

for page in reader.pages:
    page.merge_page(watermark)
    writer.add_page(page)

with open("watermarked.pdf", "wb") as output:
    writer.write(output)
```

### 提取图片
```bash
# 使用 pdfimages（poppler-utils）
pdfimages -j input.pdf output_prefix

# 提取所有图片为 output_prefix-000.jpg、output_prefix-001.jpg 等
```

### 密码保护
```python
from pypdf import PdfReader, PdfWriter

reader = PdfReader("input.pdf")
writer = PdfWriter()

for page in reader.pages:
    writer.add_page(page)

# 添加密码
writer.encrypt("userpassword", "ownerpassword")

with open("encrypted.pdf", "wb") as output:
    writer.write(output)
```

## 快速参考

| 任务 | 推荐工具 | 命令/代码 |
|------|-----------|--------------|
| 合并 PDF | pypdf | `writer.add_page(page)` |
| 拆分 PDF | pypdf | 每页一个文件 |
| 提取文本 | pdfplumber | `page.extract_text()` |
| 提取表格 | pdfplumber | `page.extract_tables()` |
| 创建 PDF | reportlab | Canvas 或 Platypus |
| 命令行合并 | qpdf | `qpdf --empty --pages ...` |
| 扫描件 OCR | pytesseract | 先转为图片 |
| 填写 PDF 表单 | pdf-lib 或 pypdf（见 FORMS.md） | 参见 FORMS.md |

## AI 视觉审图（带 OCR/MCP fallback）

新脚本 `extract_with_fallback.py` 把整个审图流程串起来：先用 pdfplumber 逐页抽文，**抽不到文字的页自动调 UMI-OCR**，**OCR 也抽不到的页标记为 `needs-vision`**，由 Claude 在主会话里调 `mcp__MiniMax__understand_image` 做语义理解。

### 调用方式

```bash
python scripts/extract_with_fallback.py <input.pdf> <output_dir> \
    [--ocr-lang 简体中文] [--text-threshold 50] [--scale 2.0] \
    [--skip-ocr]
```

输出到 `<output_dir>/`：
- `extracted_text.txt` — 合并结果，每页带来源标签
- `extracted_tables.txt` — 表格（如果有）
- `page_NNN.png` — 导出的页面图（OCR 和 vision 共用）

### 决策树

```
每页 pdfplumber 抽文
   ├─ char_count ≥ 阈值（默认 50）→ 标签 (source: pdfplumber)
   └─ char_count < 阈值 → 导出 PNG → UMI-OCR
                              ├─ OCR 成功 → 标签 (source: umi-ocr)
                              └─ OCR 失败/空 → 标签 (source: needs-vision)
                                                  ↓
                                        Claude 调 mcp__MiniMax__understand_image
                                                  ↓
                                        Claude 把结果回写到 extracted_text.txt
```

### 逐页标签格式

```
=== Page 1 (source: pdfplumber) ===
[正文...]

=== Page 2 (source: umi-ocr) ===
[OCR 抽出的文字...]

=== Page 3 (source: needs-vision) ===
[image: page_003.png — please run mcp__MiniMax__understand_image for semantic understanding]
```

### Claude 侧：处理 `needs-vision` 标记

1. 读 `extracted_text.txt`，正则匹配 `=== Page (\d+) \(source: needs-vision\) ===` 块
2. 对每个匹配，取 `image:` 后的 PNG 路径
3. 调 `mcp__MiniMax__understand_image`，prompt 用下面模板（针对弱电/建筑审图）：
   ```
   你在看一份弱电/建筑专业图纸。请描述：
   - 图中可见的设备、机房、管井、点位
   - 系统标注（CCTV/门禁/BA/网络/消防等）
   - 房间名称、功能区
   - 标高、尺寸、比例尺
   - 任何文字标注（精确转写）
   ```
4. 把 vision 输出**就地替换**对应 `needs-vision` 块的内容（保留 `=== Page N (source: mcp-vision) ===` 头）
5. 改完保存回 `extracted_text.txt`

### 弱电/建筑审图增强

默认模板通用，针对专业场景可重点核查：
- 设备机房、弱电间、管井位置是否准确
- 系统标注（消防、安防、BA、网络点位）是否一致
- 比例尺、标高、尺寸标注是否正确
- 房间名称、功能标注与图纸是否匹配

## 下一步

- pypdfium2 高级用法，参见 REFERENCE.md
- JavaScript 库（pdf-lib），参见 REFERENCE.md
- 如需填写 PDF 表单，请按 FORMS.md 中的说明操作
- 故障排除指南，参见 REFERENCE.md
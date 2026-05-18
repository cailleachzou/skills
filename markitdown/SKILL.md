---
name: markitdown
description: "Use this skill whenever the user wants to convert files to Markdown format. This includes: converting PDF, DOCX, PPTX, XLSX, images, audio files, HTML, EPUB, CSV, JSON, XML, ZIP archives, YouTube videos, Wikipedia pages, and other file formats to Markdown. Triggers include: any mention of 'convert to markdown', 'export to markdown', '.md conversion', extracting text from binary files, or making files LLM-friendly."
license: MIT
---

# MarkItDown - 文件转 Markdown 转换器

> [!TIP]
> 在本机上，请使用 `/c/Users/59620/AppData/Local/Python/bin/python.exe` 而非裸 `python` 命令，以避免 Windows 应用商店重定向问题。

## 概述

MarkItDown 是微软出品的一个工具，可将各种文件格式转换为 Markdown，以便与大语言模型配合使用。它能保留文档结构，包括标题、列表、表格、链接等。

## 支持的格式

| 格式      | 扩展名           | 说明                                |
| ---------- | ---------------- | ------------------------------------ |
| PDF        | .pdf             | 便携式文档格式                       |
| Word       | .docx            | Microsoft Word 文档                  |
| Excel      | .xlsx, .xls      | Microsoft Excel 电子表格            |
| PowerPoint | .pptx            | Microsoft PowerPoint 演示文稿        |
| 图片       | .jpg, .png 等     | EXIF 元数据 + OCR                    |
| 音频       | .mp3, .wav, .m4a | EXIF 元数据 + 语音转录               |
| HTML       | .html, .htm      | 原始网页                             |
| **网页/URL** | URL              | 请使用 **Defuddle**（见下方）         |
| EPUB       | .epub            | 电子书                              |
| CSV        | .csv             | 逗号分隔值                          |
| JSON       | .json            | JavaScript 对象表示法                |
| XML        | .xml             | 可扩展标记语言                       |
| ZIP        | .zip             | 压缩包（遍历内部内容）               |
| Jupyter    | .ipynb           | Jupyter 笔记本                      |
| Outlook    | .msg             | Outlook 邮件                        |
| YouTube    | URL              | 视频字幕                            |
| Wikipedia  | URL              | Wikipedia 文章                       |

## 安装

```bash
# 安装所有依赖（推荐）
/c/Users/59620/AppData/Local/Python/bin/python.exe -m pip install 'markitdown[all]'

# 或仅安装特定格式支持
/c/Users/59620/AppData/Local/Python/bin/python.exe -m pip install 'markitdown[pdf,docx,pptx]'
```

## 快速入门

### 命令行用法

```bash
# 基本转换
markitdown path-to-file.pdf -o output.md

# 从标准输入管道
cat file.docx | markitdown > output.md

# 为标准输入指定格式提示
cat file.xyz | markitdown -x .pdf > output.md

# 使用插件
markitdown path-to-file.pdf --use-plugins -o output.md

# 列出可用插件
markitdown --list-plugins
```

### Python API

```python
from markitdown import MarkItDown

md = MarkItDown(enable_plugins=False)
result = md.convert("document.pdf")
print(result.text_content)
```

### 配合 Azure Document Intelligence 使用

```python
from markitdown import MarkItDown

md = MarkItDown(docintel_endpoint="https://your-endpoint.cognitiveservices.azure.com/")
result = md.convert("document.pdf")
print(result.text_content)
```

### 配合 LLM 图片描述使用

```python
from markitdown import MarkItDown
from openai import OpenAI

client = OpenAI()
md = MarkItDown(llm_client=client, llm_model="gpt-4o", llm_prompt="Describe this image:")
result = md.convert("photo.jpg")
print(result.text_content)
```

## 常见任务

### 转换 URL / 网页 → MD（首选 Defuddle）

对于在线文档、文章、博客、标准网页，**优先使用 Defuddle**，它能去除导航、广告等噪音，节省 token：

```bash
defuddle parse <url> --md -o content.md
```

提取元数据：
```bash
defuddle parse <url> -p title
defuddle parse <url> -p description
defuddle parse <url> -p domain
```

> [!NOTE]
> 如果 Defuddle 失败或无法安装，才 fallback 到 `markitdown <url>`。

```bash
markitdown document.pdf -o document.md
```

```python
from markitdown import MarkItDown
md = MarkItDown()
result = md.convert("document.pdf")
print(result.text_content)
```

### 转换 Word 文档

```bash
markitdown document.docx -o document.md
```

### 转换 Excel 电子表格

```bash
markitdown spreadsheet.xlsx -o spreadsheet.md
```

### 转换 PowerPoint 演示文稿

```bash
markitdown presentation.pptx -o presentation.md
```

### 批量转换多个文件

```python
from markitdown import MarkItDown
import glob

md = MarkItDown()
for filepath in glob.glob("*.pdf"):
    result = md.convert(filepath)
    output_path = filepath.rsplit(".", 1)[0] + ".md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(result.text_content)
```

### 批量转换整个目录

```python
from markitdown import MarkItDown
from pathlib import Path

md = MarkItDown()
for file in Path(".").rglob("*"):
    if file.is_file():
        try:
            result = md.convert(str(file))
            output = file.with_suffix(".md")
            output.write_text(result.text_content, encoding="utf-8")
            print(f"Converted: {file} -> {output}")
        except Exception as e:
            print(f"Skipped {file}: {e}")
```

### 从 URL 转换

```python
from markitdown import MarkItDown

md = MarkItDown()
# 转换网页
result = md.convert("https://example.com/page.html")

# 转换 Wikipedia 文章
result = md.convert("https://en.wikipedia.org/wiki/Python_(programming_language)")

# 转换 YouTube 视频（字幕）
result = md.convert("https://www.youtube.com/watch?v=example")
```

### 从 ZIP 压缩包提取内容

```python
from markitdown import MarkItDown
from pathlib import Path

md = MarkItDown()
result = md.convert("archive.zip")
print(result.text_content)
```

### 自定义 LLM 图片提示词

```python
from markitdown import MarkItDown
from openai import OpenAI

client = OpenAI()
md = MarkItDown(
    llm_client=client,
    llm_model="gpt-4o",
    llm_prompt="Describe this image in detail, focusing on text content:"
)
result = md.convert("screenshot.png")
print(result.text_content)
```

## 高级用法

### 保留 Data URI（Base64 图片）

默认情况下，Data URI 会被截断。使用 `--keep-data-uris` 可保留完整内容：

```bash
markitdown document.pptx --keep-data-uris -o output.md
```

```python
result = md.convert("document.pptx", keep_data_uris=True)
```

### 插件系统

MarkItDown 支持第三方插件。启用方式：

```bash
markitdown file.pdf --use-plugins -o output.md
```

可在 GitHub 上搜索 `#markitdown-plugin` 查找插件。

### 流式转换（二进制 IO）

```python
from markitdown import MarkItDown
import io

md = MarkItDown()

# 从二进制流转换
with open("document.pdf", "rb") as f:
    result = md.convert_stream(f)
    print(result.text_content)

# 从 BytesIO 转换
data = open("document.pdf", "rb").read()
buffer = io.BytesIO(data)
result = md.convert_stream(buffer)
```

## 结果对象

`convert()` 方法返回一个 `DocumentConverterResult` 对象，包含：

- `text_content`：转换后的 Markdown 文本
- `markdown`：`text_content` 的别名
- 具体元数据因转换器而异

## 快速参考

| 任务               | 命令                                |
|------|---------|
| 转换 PDF           | `markitdown file.pdf -o out.md`     |
| 转换 DOCX          | `markitdown file.docx -o out.md`    |
| 转换 XLSX          | `markitdown file.xlsx -o out.md`    |
| 从标准输入转换      | `cat file.pdf \| markitdown > out.md` |
| 指定格式           | `cat file \| markitdown -x .pdf > out.md` |
| 启用插件           | `markitdown file.pdf --use-plugins -o out.md` |
| 列出插件           | `markitdown --list-plugins`         |
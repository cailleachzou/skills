---
name: markitdown
description: "Use this skill whenever the user wants to convert files to Markdown format. This includes: converting PDF, DOCX, PPTX, XLSX, images, audio files, HTML, EPUB, CSV, JSON, XML, ZIP archives, YouTube videos, Wikipedia pages, and other file formats to Markdown. Triggers include: any mention of 'convert to markdown', 'export to markdown', '.md conversion', extracting text from binary files, or making files LLM-friendly."
license: MIT
---

# MarkItDown - File to Markdown Converter

> [!TIP]
> On this machine, use `/c/Users/59620/AppData/Local/Python/bin/python.exe` instead of bare `python` command to avoid Windows Store redirect issues.

## Overview

MarkItDown is a Microsoft utility that converts various file formats to Markdown for use with LLMs. It preserves document structure including headings, lists, tables, links, and more.

## Supported Formats

| Format     | Extension        | Description                          |
| ---------- | ---------------- | ------------------------------------ |
| PDF        | .pdf             | Portable Document Format             |
| Word       | .docx            | Microsoft Word documents             |
| Excel      | .xlsx, .xls      | Microsoft Excel spreadsheets         |
| PowerPoint | .pptx            | Microsoft PowerPoint presentations   |
| Images     | .jpg, .png, etc. | EXIF metadata + OCR                  |
| Audio      | .mp3, .wav, .m4a | EXIF metadata + speech transcription |
| HTML       | .html, .htm      | Raw web pages                        |
| **Web/URL**| URL               | Use **Defuddle** instead（见下方）    |
| EPUB       | .epub            | E-books                              |
| CSV        | .csv             | Comma-separated values               |
| JSON       | .json            | JavaScript Object Notation           |
| XML        | .xml             | Extensible Markup Language           |
| ZIP        | .zip             | Archive (iterates over contents)     |
| Jupyter    | .ipynb           | Jupyter notebooks                    |
| Outlook    | .msg             | Outlook messages                     |
| YouTube    | URL              | Video transcripts                    |
| Wikipedia  | URL              | Wikipedia articles                   |

## Installation

```bash
# Install with all dependencies (recommended)
/c/Users/59620/AppData/Local/Python/bin/python.exe -m pip install 'markitdown[all]'

# Or install specific format support
/c/Users/59620/AppData/Local/Python/bin/python.exe -m pip install 'markitdown[pdf,docx,pptx]'
```

## Quick Start

### Command-Line Usage

```bash
# Basic conversion
markitdown path-to-file.pdf -o output.md

# Pipe from stdin
cat file.docx | markitdown > output.md

# Specify format hint for stdin input
cat file.xyz | markitdown -x .pdf > output.md

# Use plugins
markitdown path-to-file.pdf --use-plugins -o output.md

# List available plugins
markitdown --list-plugins
```

### Python API

```python
from markitdown import MarkItDown

md = MarkItDown(enable_plugins=False)
result = md.convert("document.pdf")
print(result.text_content)
```

### With Azure Document Intelligence

```python
from markitdown import MarkItDown

md = MarkItDown(docintel_endpoint="https://your-endpoint.cognitiveservices.azure.com/")
result = md.convert("document.pdf")
print(result.text_content)
```

### With LLM Image Descriptions

```python
from markitdown import MarkItDown
from openai import OpenAI

client = OpenAI()
md = MarkItDown(llm_client=client, llm_model="gpt-4o", llm_prompt="Describe this image:")
result = md.convert("photo.jpg")
print(result.text_content)
```

## Common Tasks

### Convert a URL / Web Page → MD（首选 Defuddle）

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

### Convert a Word Document

```bash
markitdown document.docx -o document.md
```

### Convert an Excel Spreadsheet

```bash
markitdown spreadsheet.xlsx -o spreadsheet.md
```

### Convert a PowerPoint

```bash
markitdown presentation.pptx -o presentation.md
```

### Convert Multiple Files

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

### Batch Convert Directory

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

### Convert from URL

```python
from markitdown import MarkItDown

md = MarkItDown()
# Convert web page
result = md.convert("https://example.com/page.html")

# Convert Wikipedia article
result = md.convert("https://en.wikipedia.org/wiki/Python_(programming_language)")

# Convert YouTube video (transcript)
result = md.convert("https://www.youtube.com/watch?v=example")
```

### Extract from ZIP Archive

```python
from markitdown import MarkItDown
from pathlib import Path

md = MarkItDown()
result = md.convert("archive.zip")
print(result.text_content)
```

### Custom LLM Prompt for Images

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

## Advanced Usage

### Keep Data URIs (Base64 Images)

By default, data URIs are truncated. Use `--keep-data-uris` to keep them:

```bash
markitdown document.pptx --keep-data-uris -o output.md
```

```python
result = md.convert("document.pptx", keep_data_uris=True)
```

### Plugin System

MarkItDown supports 3rd-party plugins. To enable:

```bash
markitdown file.pdf --use-plugins -o output.md
```

Find plugins by searching for `#markitdown-plugin` on GitHub.

### Stream Conversion (Binary IO)

```python
from markitdown import MarkItDown
import io

md = MarkItDown()

# Convert from binary stream
with open("document.pdf", "rb") as f:
    result = md.convert_stream(f)
    print(result.text_content)

# Convert from BytesIO
data = open("document.pdf", "rb").read()
buffer = io.BytesIO(data)
result = md.convert_stream(buffer)
```

## Result Object

The `convert()` method returns a `DocumentConverterResult` with:

- `text_content`: The converted Markdown text
- `markdown`: Alias for text_content
- Additional metadata depending on converter

## Quick Reference

| Task | Command |
|------|---------|
| Convert PDF | `markitdown file.pdf -o out.md` |
| Convert DOCX | `markitdown file.docx -o out.md` |
| Convert XLSX | `markitdown file.xlsx -o out.md` |
| Convert from stdin | `cat file.pdf \| markitdown > out.md` |
| Specify format | `cat file \| markitdown -x .pdf > out.md` |
| Enable plugins | `markitdown file.pdf --use-plugins -o out.md` |
| List plugins | `markitdown --list-plugins` |

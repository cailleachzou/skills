---
name: ocr
description: Use Umi-OCR to extract text from images (screenshots, photos, scanned documents) and PDFs/DOCX files. Make sure to use this skill whenever the user wants to recognize, extract, or read text from an image file, screenshot, PDF page, or any visual content — whether they explicitly mention "OCR", "文字识别", "图片转文字", "截图识字", or just ask to "extract text from [file]". Umi-OCR is an offline, free OCR engine that runs locally with a HTTP API. Also converts PDF → Markdown (layout/table preserved) via marker-pdf.
compatibility: Umi-OCR Rapid v2.1.5+ installed at `C:\Users\59620\Downloads\Programs\Umi-OCR_Rapid_v2.1.5\Umi-OCR.exe`
---

# OCR Skill — 两套引擎

本技能提供两种 OCR 引擎，按场景选择：

| 场景 | 引擎 | 输出 |
|------|------|------|
| **图片 → 纯文本** | Umi-OCR | 纯文本 |
| **PDF → Markdown（保留布局/表格）** | marker-pdf | Markdown |

## 选择规则

- **PDF 文件转 Markdown** → 用 marker-pdf（Section A）
- **图片 OCR / 纯文本提取** → 用 Umi-OCR（Section B）

---

# Section A — marker-pdf（PDF → Markdown）

## 安装位置

- **Python venv**: `C:\Users\59620\.venv-marker\`
- **marker CLI**: `C:\Users\59620\.venv-marker\Scripts\marker.exe`
- **Wrapper 脚本**: `ocr/scripts/pdf2md.ps1`

## 必需环境变量（surya / llama.cpp 后端）

marker v2 基于 surya，启动时强制初始化 OCR 推理后端（spawn `llama-server`），
**缺少下列变量会直接报 `SpawnError: llama-server binary not found`**：

| 环境变量 | 值（本机） |
|---------|-----------|
| `LLAMA_CPP_BINARY` | `C:\Users\59620\.models\llama-x64\llama-server.exe` |
| `SURYA_GGUF_LOCAL_MODEL_PATH` | `C:\Users\59620\.models\surya\surya-2.gguf` |
| `SURYA_GGUF_LOCAL_MMPROJ_PATH` | `C:\Users\59620\.models\surya\surya-2-mmproj.gguf` |

> `pdf2md.ps1` wrapper 已内置这些变量，直接用即可；手敲 marker.exe 时需自行设置。
> GGUF 可改成局域网路径，供多机复用（surya 支持 `s3://`、`hf://` 前缀）。

## 快速用法

```powershell
# 基本转换 — PDF → Markdown（同目录输出）
& "C:\Users\59620\.venv-marker\Scripts\marker.exe" "<含PDF的文件夹>" --output_format markdown --output_dir "<输出目录>"

# 指定页码范围
& "C:\Users\59620\.venv-marker\Scripts\marker.exe" "<文件夹>" --output_format markdown --output_dir "<输出>" --page_range "0,1-3,5"

# 强制 OCR 模式（扫描件）
& "C:\Users\59620\.venv-marker\Scripts\marker.exe" "<文件夹>" --output_format markdown --output_dir "<输出>" --mode balanced

# Wrapper 脚本（推荐）
powershell -File "C:\Users\59620\.claude\skills\ocr\scripts\pdf2md.ps1" -Input "C:\path\to\scan.pdf"
```

## marker 关键参数

| 参数 | 说明 |
|------|------|
| `--output_format markdown` | 输出 Markdown 格式 |
| `--output_dir PATH` | 输出目录 |
| `--mode balanced\|fast` | balanced=GPU最佳质量，fast=CPU轻量（默认按设备自动选择） |
| `--page_range "0,1-5,10"` | 指定页码（0-indexed） |
| `--force_ocr` | 强制全文 OCR |
| `--disable_image_extraction` | 不提取图片 |
| `--skip_existing` | 跳过已转换文件 |

## 工作流程

1. 将 PDF 文件放入一个临时文件夹
2. 运行 `marker <文件夹> --output_format markdown --output_dir <输出目录>`
3. marker 自动检测语言（含中文 surya-ocr 引擎）
4. 输出 `<文件名>.md` 到指定目录

## 注意事项

- 首次运行会下载模型（surya 布局/检测模型，约 1-2GB），需联网；GGUF 大模型（surya-2.gguf）用 `SURYA_GGUF_LOCAL_*` 指向本地，避免重复下载
- CPU 模式下较慢（文本层 PDF ≈10-12 页/分），大文件建议用 GPU
- marker 输入是**文件夹**（不是单个文件），会处理文件夹内所有 PDF
- 中文支持由 surya-ocr 引擎提供，效果良好
- 输出可能落在 `<output_dir>/<文件名>/<文件名>.md` 子目录（v2 按文件分目录），wrapper 已用递归查找
- Windows 下结束时报 `Failed to stop llamacpp [WinError 87]` 是清理子进程的无害噪音，不影响结果

---

# Section B — Umi-OCR（图片/文档 → 纯文本）

## Umi-OCR 安装位置

- **Exe path**: `C:\Users\59620\Downloads\Programs\Umi-OCR_Rapid_v2.1.5\Umi-OCR.exe`
- **Data dir**: `C:\Users\59620\Downloads\Programs\Umi-OCR_Rapid_v2.1.5\UmiOCR-data`
- **HTTP API port**: 1224 (default, auto-increments if occupied)
- **API base URL**: `http://127.0.0.1:1224`

## Workflow

### Step 1 — Ensure Umi-OCR is Running

Ping the API to check if the service is up:

```bash
curl -s http://127.0.0.1:1224/umiocr
```

If the response is empty or connection is refused, start Umi-OCR:

```bash
"C:/Users/59620/Downloads/Programs/Umi-OCR_Rapid_v2.1.5/Umi-OCR.exe" &
```

Wait 3–5 seconds for the HTTP server to initialize.

### Step 2 — OCR Request

Build the POST request:

1. Read the input file as binary
2. Base64-encode it
3. POST to `http://127.0.0.1:1224/api/ocr` with JSON body:

```json
{
  "base64": "<base64 string>",
  "options": {
    "ocr.language": "简体中文",
    "tbpu.parser": "multi_para",
    "data.format": "text"
  }
}
```

**cURL example:**
```bash
curl -s -X POST http://127.0.0.1:1224/api/ocr \
  -H "Content-Type: application/json" \
  -d "{\"base64\":\"$(base64 -w0 /path/to/file)\",\"options\":{\"ocr.language\":\"简体中文\",\"tbpu.parser\":\"multi_para\",\"data.format\":\"text\"}}"
```

**Python example** (if Bash base64 is unavailable):
```bash
python -c "
import sys, base64, json, urllib.request
path = sys.argv[1]
b64 = base64.b64encode(open(path,'rb').read()).decode()
data = json.dumps({'base64': b64, 'options': {'ocr.language': '简体中文', 'tbpu.parser': 'multi_para', 'data.format': 'text'}}).encode()
req = urllib.request.Request('http://127.0.0.1:1224/api/ocr', data=data, headers={'Content-Type':'application/json'})
res = urllib.request.urlopen(req)
print(res.read().decode())
" <file_path>
```

### Step 3 — Parse Response

The API returns JSON:
```json
{"code": 100, "data": "识别出的文本内容"}
```

- `code == 100`: success — extract `data` field
- `code != 100`: error — show `data` as error message

### Step 4 — Output

- Print the extracted text directly to stdout
- If user specified an output file with `-o <path>`, write text to that file
- Do NOT add quotes, headers, or commentary to the extracted text

## Input Types

| Type | Extensions | Notes |
|------|-----------|-------|
| Images | `.png`, `.jpg`, `.jpeg`, `.bmp`, `.webp`, `.gif`, `.tiff` | Direct OCR |
| PDF/DOCX | `.pdf`, `.docx`, `.xlsx`, `.pptx`, `.odt` | Use `/api/doc/upload` instead |

For PDF/DOCX, use the doc endpoint:
```bash
# Upload
curl -s -X POST http://127.0.0.1:1224/api/doc/upload \
  -F "file=@/path/to/document.pdf" \
  -F "json={\"ocr.language\":\"简体中文\",\"tbpu.parser\":\"multi_para\"}"

# Response: {"code": 100, "data": "<task_id>"}
# Poll result
curl -s -X POST http://127.0.0.1:1224/api/doc/result \
  -H "Content-Type: application/json" \
  -d '{"id":"<task_id>","is_data":true,"format":"text"}'
```

## Options Reference

| Option | Values | Default | Description |
|--------|--------|---------|-------------|
| `ocr.language` | `简体中文`, `English`, `日本語`, `한국어`, `etc.` | `简体中文` | Recognition language |
| `tbpu.parser` | `multi_para`, `multi_line`, `multi_none`, `single_para`, `single_line`, `single_none`, `single_code`, `none` | `multi_para` | Text layout parser. `multi_para` = multi-column with natural paragraph breaks |
| `data.format` | `dict`, `text` | `dict` | Use `text` for plain text output |
| `ocr.angle` | `true`, `false` | `false` | Auto-rotate image |

## Troubleshooting

- **Connection refused**: Umi-OCR not running — start it first (Step 1)
- **Empty result**: Try `ocr.language: "English"` or check if image is valid
- **Port already in use**: Umi-OCR auto-increments port. Find actual port by checking `http://127.0.0.1:1224`, `1225`, `1226`... or read `pre_configs.json` in the data dir
- **Slow startup**: Umi-OCR loads models on first launch. Wait up to 10 seconds before pinging.
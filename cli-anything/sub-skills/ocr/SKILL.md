---
name: ocr
description: Use Umi-OCR to extract text from images (screenshots, photos, scanned documents) and PDFs/DOCX files. Make sure to use this skill whenever the user wants to recognize, extract, or read text from an image file, screenshot, PDF page, or any visual content — whether they explicitly mention "OCR", "文字识别", "图片转文字", "截图识字", or just ask to "extract text from [file]". Umi-OCR is an offline, free OCR engine that runs locally with a HTTP API.
type: cli-sub
compatibility: Umi-OCR Rapid v2.1.5+ installed at `C:\Users\59620\Downloads\Programs\Umi-OCR_Rapid_v2.1.5\Umi-OCR.exe`
---

# Umi-OCR Skill

Extract plain text from images and documents via Umi-OCR's HTTP API.

## Umi-OCR Installation

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
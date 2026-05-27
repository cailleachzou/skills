---
name: dxf-dwg-converter
description: CAD file format converter and text extractor/translator for DWG/DXF files. Use when users want to convert DWG to DXF or DXF to DWG, extract text, translate text entities in CAD drawings (Chinese/English labels), list or filter CAD layers, export DWG to SVG, or batch process multiple CAD files. Triggers for "DWG转DXF", "CAD文字提取", "图层列表", "批量转换", "导出SVG", "dxf", "dwg", "CAD", "DXF翻译".
type: skill
---

# dxf-dwg-converter

CAD file processing toolkit — wraps LibreDWG executables and ezdxf Python library for format conversion, text extraction, layer management, and batch processing.

## Prerequisites

- **LibreDWG** — `C:\Program Files\libredwg-0.13.4-win32\` (Windows install)
- **ezdxf** — `pip install ezdxf`

## Commands

### `convert dwg2dxf` — Convert DWG to DXF

```bash
python scripts/convert.py dwg2dxf INPUT OUTPUT [OPTIONS]
```

**Options:**
- `--version` — DXF version output (default: `R2000`)
- `--ascii` — Output ASCII DXF (default)
- `--binary` — Output binary DXF
- `--y` — Overwrite output file
- `--dry-run` — Show command without executing

**Examples:**
```bash
# Basic conversion
python scripts/convert.py dwg2dxf input.dwg output.dxf

# Specify DXF version
python scripts/convert.py dwg2dxf input.dwg output.dxf --version R2010

# Dry run
python scripts/convert.py dwg2dxf input.dwg output.dxf --dry-run
```

### `convert dxf2dwg` — Convert DXF to DWG

```bash
python scripts/convert.py dxf2dwg INPUT OUTPUT [OPTIONS]
```

**Options:**
- `--version` — DWG version output (default: `R2000`)
- `--y` — Overwrite output file
- `--dry-run` — Show command without executing

**Examples:**
```bash
python scripts/convert.py dxf2dwg input.dxf output.dwg
python scripts/convert.py dxf2dwg input.dxf output.dwg --version R2013 --dry-run
```

### `text extract` — Extract text from DXF

```bash
python scripts/extract_text.py INPUT [--layer LAYER] [--type TYPE] [--json]
```

**Options:**
- `--layer` — Filter by layer name (partial match)
- `--type` — Filter by entity type (`TEXT`, `MTEXT`, `ATTRIB`, `ATTDEF`)
- `--json` — Output machine-readable JSON

**Returns:**
```json
{
  "source": "C:/path/to/file.dxf",
  "version": "R2010",
  "count": 153,
  "texts": [
    {
      "handle": "1A1B",
      "type": "TEXT",
      "content": "PT. JAYA KARYA INTEGRASI",
      "layer": "X_A1_TITLE_BLOCK_2024-IMPC"
    },
    {
      "handle": "1A1D",
      "type": "MTEXT",
      "content": "会议室 Meeting Room",
      "layer": "ANNO-TEXT"
    }
  ]
}
```

**Examples:**
```bash
# Extract all text
python scripts/extract_text.py drawing.dxf

# Filter by layer
python scripts/extract_text.py drawing.dxf --layer ANNO-TEXT

# JSON output for programmatic use
python scripts/extract_text.py drawing.dxf --json
```

### `text translate` — Translate and save text back to DXF

```bash
python scripts/extract_text.py INPUT --translate TRANSLATIONS [--output OUTPUT]
```

**Parameters:**
- `TRANSLATIONS` — JSON string or dict `{handle: new_text, ...}`
- `--output` — Output DXF path (default: `<stem>_translated.dxf`)

**Example:**
```bash
python scripts/extract_text.py drawing.dxf \
  --translate '{"1A1B": "会议室", "1A1D": "安防控制室"}' \
  --output drawing_zh.dxf
```

### `layers list` — List all layers

```bash
python scripts/layers.py INPUT [--json]
```

**Example output:**
```
Layer List for: drawing.dxf
============================================================
Layer Name                    Color   LineType  Frozen
----------------------------  ------  --------  ------
0                             7       CONTINUOUS No
ANNO-TEXT                     1       CONTINUOUS No
X_A1_TITLE_BLOCK             7       CONTINUOUS No
...
Total: 24 layers
```

### `layers filter` — Filter entities by layer

```bash
python scripts/layers.py INPUT --layer PATTERN [--json]
```

### `svg export` — Export DWG to SVG

```bash
python scripts/svg_export.py INPUT OUTPUT [OPTIONS]
```

**Options:**
- `--width` — Output width in pixels
- `--height` — Output height in pixels
- `--layers` — Comma-separated layer whitelist
- `--all` — Include all layers (default)

**Examples:**
```bash
python scripts/svg_export.py input.dwg output.svg
python scripts/svg_export.py input.dwg output.svg --width 1920 --layers "0,ANNO-TEXT"
```

### `batch convert` — Batch convert multiple files

```bash
python scripts/batch.py "*.dwg" OUTPUT_DIR --operation dwg2dxf [OPTIONS]
```

**Options:**
- `--operation` — `dwg2dxf` or `dxf2dwg`
- `--pattern` — Glob pattern (default: `*.dwg`)
- `--suffix` — Output suffix (default: `_converted`)
- `--y` — Overwrite without asking
- `--workers` — Parallel workers (default: 4)

**Examples:**
```bash
# Batch DWG to DXF
python scripts/batch.py "C:/project/*.dwg" "C:/project/dxf/" --operation dwg2dxf

# Batch with custom suffix
python scripts/batch.py "*.dxf" "C:/project/dwg/" --operation dxf2dwg --suffix _r2010

# Dry run
python scripts/batch.py "*.dwg" "C:/project/dxf/" --operation dwg2dxf --dry-run
```

### `info status` — Check installation

```bash
python scripts/info.py
```

**Output:**
```json
{
  "libredwg": {
    "path": "C:\\Program Files\\libredwg-0.13.4-win32",
    "tools": ["dwg2dxf.exe", "dxf2dwg.exe", "dwg2SVG.exe", "dwgread.exe", "dwglayers.exe"]
  },
  "ezdxf": {
    "installed": true,
    "version": "1.1.0"
  }
}
```

## Common Workflows

### Convert and translate Chinese labels
```bash
# 1. Extract text
python scripts/extract_text.py floorplan.dxf --json > texts.json

# 2. Translate (edit texts.json manually or via AI)

# 3. Apply translations
python scripts/extract_text.py floorplan.dxf \
  --translate '{"1A1B": "弱电机房", "1A1D": "监控室"}' \
  --output floorplan_zh.dxf
```

### Batch convert project folder
```bash
python scripts/batch.py "P:/项目/*.dwg" "P:/项目/DXF/" --operation dwg2dxf --workers 8
```

### Export specific layers to SVG
```bash
python scripts/svg_export.py layout.dwg preview.svg --layers "0,ANNO-TEXT,WALLS"
```

## Input/Output Formats

| Format | Extensions | Read | Write |
|--------|-----------|------|--------|
| DWG | `.dwg` | LibreDWG | LibreDWG (R2000) |
| DXF | `.dxf` | ezdxf / LibreDWG | ezdxf / LibreDWG |
| SVG | `.svg` | — | LibreDWG |
| JSON | `.json` | — | ezdxf (via extract_text) |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Generic error |
| 2 | Input file not found |
| 3 | Invalid file format |
| 4 | Output path not writable |

## Error Handling

- **File not found** — Clear error with path attempted
- **Invalid DWG version** — List supported versions in error
- **LibreDWG missing** — Point to install location
- **ezdxf not installed** — `pip install ezdxf` in error message
- **Batch failures** — Continue with remaining files, log failures at end

## For AI Agents

**Prefer ezdxf for DXF operations** (more complete Python API, better for text extraction).

**Use LibreDWG for DWG-only operations** (DWG format support beyond what ezdxf handles).

The `--dry-run` flag is safe to use without real files — good for validation before batch operations.

**Layer naming conventions in Chinese CAD:**
- `X_A1_*` — Title block / 图框
- `ANNO-*` — Annotations / 标注
- `WALLS` / `WALL` — 墙体
- `DOORS` / `WINDOWS` — 门窗
- `TEXT` / `MTEXT` — 文字

```python
# Quick layer filter example
doc = ezdxf.readfile("drawing.dxf")
layers = [l.name for l in doc.layers if not l.is_frozen()]
```
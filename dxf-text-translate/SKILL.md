---
name: dxf-text-translate
description: Extract and translate text entities in DXF files. Use when asked to translate DXF text, extract text from CAD files, work with DXF text entities, or convert Chinese/English labels in CAD drawings. This skill handles the full workflow: extract text to JSON → edit in conversation → write translations back to DXF. Works on MTEXT, TEXT, ATTRIB, and ATTDEF entities.
---

# DXF Text Extraction & Translation

Extract text from DXF files for translation editing, then apply the edited text back into the DXF file.

## Prerequisites

- Python with `ezdxf` installed: `pip install ezdxf`

## Workflow

```
1.  extract_text(dxf_path)              → JSON shown in conversation
2.  Translate texts manually or via AI in conversation
3.  Build a {handle: chinese_text, ...} translation dict
4.  save_edits(translations, dxf_path)  → Write changes back to DXF
```

## Core Functions

### `extract_text(dxf_path)`

Parses a DXF file and extracts all text entities.

**Parameters:**
- `dxf_path` (str) — Absolute or relative path to DXF file

**Returns:** Python dict (also saveable as JSON):
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

Handles: `dxf.handle` (hex string, e.g. `"1A1B"`)
Entity types: `TEXT`, `MTEXT`, `ATTRIB`, `ATTDEF`

### `save_edits(translations, dxf_path, output_path=None)`

Applies edited text content back to the DXF file.

**Parameters:**
- `translations` (dict) — `{handle: new_text, ...}` mapping. Example: `{"1A21": "Workshop 车间", "2090": "安防控制室"}`
- `dxf_path` (str) — Original DXF file path
- `output_path` (str, optional) — Output DXF path. Default: `<stem>_中文.dxf`

**Returns:** Path to the output DXF file

## Example Session

```
You: Extract text from floorplan.dxf
AI:  data = extract_text("floorplan.dxf")
     Shows JSON of 45 text entities

You: Translate all Chinese labels to English
AI:  Modifies the "content" field for each Chinese entity

You: Save the changes back to the DXF
AI:  save_edits(data, "floorplan.dxf")
     Output: floorplan_translated.dxf
```

## Complete Workflow Code

```python
import sys
sys.path.insert(0, '/path/to/ezdxf/src')  # if using local ezdxf clone
from ezdxf.recover import readfile
from pathlib import Path

DXF_PATH = "your_drawing.dxf"

# Step 1: Extract
doc, _ = readfile(DXF_PATH)
texts = []
for entity in doc.query("MTEXT TEXT ATTRIB ATTDEF"):
    dxf = entity.dxf
    content = getattr(dxf, "text", "")
    if content and content.strip():
        texts.append({
            "handle": dxf.handle,     # hex string, e.g. "1A1B"
            "type": entity.dxftype(),
            "content": content,
            "layer": getattr(dxf, "layer", "0"),
        })
print(f"Found {len(texts)} texts")
for t in texts:
    print(f'  [{t["type"]}] [{t["layer"]}] {t["handle"]} {repr(t["content"][:60])}')

# Step 2: Build translation dict (edit in conversation or via AI)
translations = {
    "1A21": "Workshop 车间",
    "2071": "POE网络交换机入口",
    "2090": "安防控制室",
    "2142": "发射/接收器",
    "2146": "光纤",
    "214A": "CAT6A网线",
    "23AD": "周界报警传感器线缆",
    "2401": "图名",
    "2405": "比例",
    "2409": "创建日期",
    "240D": "图号",
    "243E": "机电",
    "24D4": "备注：",
    # ... add more
}

# Step 3: Apply and save
doc2, _ = readfile(DXF_PATH)
updated = 0
for entity in doc2.query("MTEXT TEXT ATTRIB ATTDEF"):
    h = entity.dxf.handle
    if h in translations:
        entity.dxf.text = translations[h]
        updated += 1

out = str(Path(DXF_PATH).parent / f"{Path(DXF_PATH).stem}_中文.dxf")
doc2.saveas(out)
print(f"Updated {updated} texts -> {out}")
```

**Tested on:** real DXF file (DCP157.06 Jakarta data center, 148 text entities) — 82 entities updated successfully.

## Tips

- **Handle** is the entity ID (from `dxf.handle`, e.g. `"1A1B"`) — use it to match edits back to entities
- **Empty content** (`""`) is skipped during extraction to avoid noise
- **MTEXT formatting codes** (`\f...|`, `\P` for newlines) are included as-is; strip them if needed: `re.sub(r'\\P', '\n', text)`
- **Layer** tells you where the text lives — useful for filtering (e.g., `layer == 'ANNO-TEXT'`)
- **DXF version**: R12 uses GB/GBK encoding; R2000+ uses UTF-8. ezdxf handles decoding automatically.

## Filter by layer

To extract text from a specific layer only:

```python
doc, _ = readfile(dxf_path)
for entity in doc.query("MTEXT TEXT"):
    if entity.dxf.layer == "MY_LAYER":
        # ...
```
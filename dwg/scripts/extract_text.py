#!/usr/bin/env python3
"""Extract text from DXF files using ezdxf."""

import sys
import json
import argparse
from pathlib import Path

try:
    import ezdxf
except ImportError:
    print(json.dumps({"status": "error", "message": "ezdxf not installed. Run: pip install ezdxf"}))
    sys.exit(1)


def extract_text(dxf_path, layer_filter=None, type_filter=None, translate_dict=None, output_path=None):
    """Extract text entities from DXF file."""
    try:
        doc = ezdxf.readfile(str(dxf_path))
    except Exception as e:
        return {"status": "error", "message": str(e)}

    # Query text entities
    query_types = ["MTEXT", "TEXT", "ATTRIB", "ATTDEF"]
    if type_filter:
        query_types = [type_filter]

    entities = list(doc.query(" ".join(query_types)))

    texts = []
    updated = 0

    for entity in entities:
        dxf = entity.dxf
        content = getattr(dxf, "text", "") or ""

        if not content or not content.strip():
            continue

        layer = getattr(dxf, "layer", "0")

        if layer_filter and layer_filter.lower() not in layer.lower():
            continue

        handle = dxf.handle or ""

        # Apply translations if provided
        if translate_dict and handle in translate_dict:
            new_text = translate_dict[handle]
            entity.dxf.text = new_text
            updated += 1
        else:
            texts.append({
                "handle": handle,
                "type": entity.dxftype(),
                "content": content,
                "layer": layer
            })

    result = {
        "status": "success",
        "source": str(dxf_path),
        "version": doc.dxfversion,
        "count": len(texts),
        "texts": texts
    }

    # Save translated DXF
    if translate_dict and output_path:
        out_path = Path(output_path)
        try:
            doc.saveas(str(out_path))
            result["output"] = str(out_path)
            result["updated"] = updated
        except Exception as e:
            result["status"] = "error"
            result["message"] = f"saveas failed: {e}"
            return result

    return result


def main():
    parser = argparse.ArgumentParser(description="Extract text from DXF files")
    parser.add_argument("input", help="Input DXF file")
    parser.add_argument("--layer", help="Filter by layer name (partial match)")
    parser.add_argument("--type", help="Filter by entity type (TEXT, MTEXT, ATTRIB, ATTDEF)")
    parser.add_argument("--translate", help="JSON translation dict {handle: text}")
    parser.add_argument("--output", help="Output DXF path for translated version")
    parser.add_argument("--json", action="store_true", help="Output JSON")

    args = parser.parse_args()

    input_p = Path(args.input)
    if not input_p.exists():
        print(json.dumps({"status": "error", "code": 2, "message": f"Input not found: {input_p}"}))
        sys.exit(2)

    translate_dict = None
    if args.translate:
        try:
            translate_dict = json.loads(args.translate)
        except json.JSONDecodeError:
            print(json.dumps({"status": "error", "message": "Invalid JSON in --translate"}))
            sys.exit(1)

    result = extract_text(
        input_p,
        layer_filter=args.layer,
        type_filter=args.type,
        translate_dict=translate_dict,
        output_path=args.output
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result["status"] == "error":
            print(f"Error: {result['message']}")
            sys.exit(1)
        print(f"DXF: {result['source']}")
        print(f"Version: {result['version']}")
        print(f"Found {result['count']} text entities")
        print()
        for t in result.get("texts", []):
            print(f"[{t['type']}] [{t['layer']}] {t['handle']}")
            print(f"  {t['content'][:80]}")
            print()


if __name__ == "__main__":
    main()
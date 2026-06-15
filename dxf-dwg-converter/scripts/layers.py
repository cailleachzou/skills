#!/usr/bin/env python3
"""List and manage CAD layers."""

import sys
import json
import argparse
from pathlib import Path

try:
    import ezdxf
except ImportError:
    print(json.dumps({"status": "error", "message": "ezdxf not installed. Run: pip install ezdxf"}))
    sys.exit(1)


def list_layers(dxf_path, pattern=None, json_output=False):
    """List all layers in a DXF file."""
    try:
        doc = ezdxf.readfile(str(dxf_path))
    except Exception as e:
        return {"status": "error", "message": str(e)}

    layers = []
    for layer in doc.layers:
        if pattern:
            if pattern.lower() not in layer.dxf.name.lower():
                continue
        layers.append({
            "name": layer.dxf.name,
            "color": layer.color,
            "line_type": layer.dxf.linetype or "CONTINUOUS",
            "frozen": layer.is_frozen(),
            "locked": layer.is_locked()
        })

    if json_output:
        return {
            "status": "success",
            "source": str(dxf_path),
            "count": len(layers),
            "layers": layers
        }

    # Human-readable output
    lines = [
        f"Layer List for: {dxf_path}",
        "=" * 60,
        f"{'Layer Name':<30} {'Color':<8} {'LineType':<14} {'Frozen'}",
        "-" * 60
    ]
    for l in layers:
        lines.append(
            f"{l['name']:<30} {l['color']:<8} {l['line_type']:<14} {'Yes' if l['frozen'] else 'No'}"
        )
    lines.append("-" * 60)
    lines.append(f"Total: {len(layers)} layers")

    return {"status": "success", "output": "\n".join(lines), "count": len(layers)}


def main():
    parser = argparse.ArgumentParser(description="List CAD layers")
    parser.add_argument("input", help="Input DXF/DWG file")
    parser.add_argument("--layer", dest="pattern", help="Filter by layer name (partial match)")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--entities", action="store_true", help="Also count entities per layer")

    args = parser.parse_args()

    input_p = Path(args.input)
    if not input_p.exists():
        print(json.dumps({"status": "error", "code": 2, "message": f"Input not found: {input_p}"}))
        sys.exit(2)

    result = list_layers(input_p, pattern=args.pattern, json_output=args.json)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result["status"] == "error":
            print(f"Error: {result['message']}")
            sys.exit(1)
        print(result["output"])

        if args.entities:
            # Count entities per layer
            doc = ezdxf.readfile(str(input_p))
            counts = {}
            for entity in doc.modelspace():
                layer = entity.dxf.layer
                counts[layer] = counts.get(layer, 0) + 1
            print("\nEntities per layer:")
            for name, count in sorted(counts.items(), key=lambda x: -x[1]):
                print(f"  {name}: {count}")


if __name__ == "__main__":
    main()
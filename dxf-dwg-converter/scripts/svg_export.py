#!/usr/bin/env python3
"""Export DWG to SVG using LibreDWG dwg2SVG."""

import sys
import json
import subprocess
import argparse
from pathlib import Path

LIBREDWG_PATH = r"C:\Program Files\libredwg-0.13.4-win32"


def main():
    parser = argparse.ArgumentParser(description="Export DWG to SVG")
    parser.add_argument("input", help="Input DWG file")
    parser.add_argument("output", help="Output SVG file")
    parser.add_argument("--width", type=int, help="Output width in pixels")
    parser.add_argument("--height", type=int, help="Output height in pixels")
    parser.add_argument("--layers", help="Comma-separated layer whitelist")
    parser.add_argument("--all", action="store_true", help="Include all layers (default)")
    parser.add_argument("--dry-run", action="store_true", help="Show command without executing")

    args = parser.parse_args()

    input_p = Path(args.input)
    if not input_p.exists():
        print(json.dumps({"status": "error", "code": 2, "message": f"Input not found: {input_p}"}))
        sys.exit(2)

    tool_exe = Path(LIBREDWG_PATH) / "dwg2SVG.exe"
    if not tool_exe.exists():
        print(json.dumps({"status": "error", "message": f"LibreDWG not found at {LIBREDWG_PATH}"}))
        sys.exit(1)

    cmd = [str(tool_exe), str(input_p), str(args.output)]

    if args.width:
        cmd.extend(["--width", str(args.width)])
    if args.height:
        cmd.extend(["--height", str(args.height)])
    if args.layers:
        cmd.extend(["--layers", args.layers])

    if args.dry_run:
        print(json.dumps({"status": "dry-run", "command": cmd}))
        return

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(json.dumps({
            "status": "error",
            "code": result.returncode,
            "message": result.stderr or result.stdout
        }))
        sys.exit(result.returncode)

    print(json.dumps({
        "status": "success",
        "input": str(input_p),
        "output": args.output
    }))


if __name__ == "__main__":
    main()
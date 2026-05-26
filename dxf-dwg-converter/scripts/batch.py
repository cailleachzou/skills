#!/usr/bin/env python3
"""Batch convert DWG/DXF files."""

import sys
import json
import subprocess
import argparse
import glob
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

LIBREDWG_PATH = r"C:\Program Files\libredwg-0.13.4-win32"


def convert_file(input_path, output_dir, operation, suffix="_converted", overwrite=False):
    """Convert a single file."""
    input_p = Path(input_path)
    ext = ".dxf" if operation == "dwg2dxf" else ".dwg"
    output_p = output_dir / f"{input_p.stem}{suffix}{ext}"

    tool_exe = Path(LIBREDWG_PATH) / ("dwg2dxf.exe" if operation == "dwg2dxf" else "dxf2dwg.exe")

    cmd = [str(tool_exe), str(input_p), str(output_p)]
    if overwrite:
        cmd.append("-y")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            return {"status": "success", "input": str(input_p), "output": str(output_p)}
        else:
            return {"status": "error", "input": str(input_p), "message": result.stderr or result.stdout}
    except Exception as e:
        return {"status": "error", "input": str(input_p), "message": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Batch convert CAD files")
    parser.add_argument("pattern", help="Glob pattern for input files (e.g. '*.dwg')")
    parser.add_argument("output_dir", help="Output directory")
    parser.add_argument("--operation", required=True, choices=["dwg2dxf", "dxf2dwg"],
                        help="Conversion operation")
    parser.add_argument("--suffix", default="_converted", help="Output filename suffix")
    parser.add_argument("-y", "--overwrite", action="store_true", help="Overwrite outputs")
    parser.add_argument("--workers", type=int, default=4, help="Parallel workers (default: 4)")
    parser.add_argument("--dry-run", action="store_true", help="Show files without converting")

    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find matching files
    pattern_paths = Path(".").glob(args.pattern) if not Path(args.pattern).is_absolute() else glob.glob(args.pattern)
    # More robust glob
    if "\\" in args.pattern or "/" in args.pattern:
        pattern_paths = list(Path(args.pattern).parent.glob(Path(args.pattern).name))
    else:
        pattern_paths = list(Path(".").glob(args.pattern))

    files = [p for p in pattern_paths if p.is_file()]

    if not files:
        print(json.dumps({"status": "error", "message": f"No files found matching: {args.pattern}"}))
        sys.exit(1)

    if args.dry_run:
        print(json.dumps({
            "status": "dry-run",
            "operation": args.operation,
            "files": [str(f) for f in files],
            "count": len(files)
        }))
        return

    results = {"success": [], "error": []}

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(convert_file, f, output_dir, args.operation, args.suffix, args.overwrite): f
            for f in files
        }
        for future in as_completed(futures):
            result = future.result()
            if result["status"] == "success":
                results["success"].append(result)
            else:
                results["error"].append(result)

    print(json.dumps({
        "status": "complete",
        "operation": args.operation,
        "total": len(files),
        "success": len(results["success"]),
        "error": len(results["error"]),
        "results": results
    }, indent=2))

    if results["error"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""DWG/DXF conversion using LibreDWG executables."""

import sys
import json
import subprocess
import argparse
from pathlib import Path

LIBREDWG_PATH = r"C:\Program Files\libredwg-0.13.4-win32"

TOOLS = {
    "dwg2dxf": "dwg2dxf.exe",
    "dxf2dwg": "dxf2dwg.exe",
}

VERSION_MAP = {
    "R12": "ac1009",
    "R2000": "ac1009",
    "R2004": "ac1015",
    "R2007": "ac1018",
    "R2010": "ac1021",
    "R2013": "ac1027",
    "R2018": "ac1064",
}


def run_tool(tool_name, input_path, output_path, version=None, binary=False, dry_run=False, overwrite=False):
    tool_exe = Path(LIBREDWG_PATH) / TOOLS[tool_name]
    if not tool_exe.exists():
        raise FileNotFoundError(f"LibreDWG not found at {LIBREDWG_PATH}. Install from https://github.com/LibreDWG/libredwg/releases")

    cmd = [str(tool_exe)]
    cmd.append(str(input_path))
    cmd.append(str(output_path))

    if version:
        ver_flag = VERSION_MAP.get(version, version)
        cmd.extend(["--version", ver_flag])

    if binary and tool_name == "dwg2dxf":
        cmd.append("--binary")

    if overwrite:
        cmd.append("-y")

    if dry_run:
        return None, cmd

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result, cmd


def main():
    parser = argparse.ArgumentParser(description="Convert between DWG and DXF using LibreDWG")
    subparsers = parser.add_subparsers(dest="operation", required=True)

    # DWG to DXF
    p_dwg2dxf = subparsers.add_parser("dwg2dxf", help="Convert DWG to DXF")
    p_dwg2dxf.add_argument("input", help="Input DWG file")
    p_dwg2dxf.add_argument("output", help="Output DXF file")
    p_dwg2dxf.add_argument("--version", default="R2000", choices=list(VERSION_MAP.keys()), help="DXF version")
    p_dwg2dxf.add_argument("--binary", action="store_true", help="Output binary DXF")
    p_dwg2dxf.add_argument("-y", "--overwrite", action="store_true", help="Overwrite output")
    p_dwg2dxf.add_argument("--dry-run", action="store_true", help="Show command without executing")

    # DXF to DWG
    p_dxf2dwg = subparsers.add_parser("dxf2dwg", help="Convert DXF to DWG")
    p_dxf2dwg.add_argument("input", help="Input DXF file")
    p_dxf2dwg.add_argument("output", help="Output DWG file")
    p_dxf2dwg.add_argument("--version", default="R2000", help="DWG version (default: R2000)")
    p_dxf2dwg.add_argument("-y", "--overwrite", action="store_true", help="Overwrite output")
    p_dxf2dwg.add_argument("--dry-run", action="store_true", help="Show command without executing")

    args = parser.parse_args()

    input_p = Path(args.input)
    if not input_p.exists():
        print(json.dumps({"status": "error", "code": 2, "message": f"Input not found: {input_p}"}))
        sys.exit(2)

    result, cmd = run_tool(
        args.operation,
        input_p,
        args.output,
        version=args.version,
        binary=args.binary,
        dry_run=args.dry_run,
        overwrite=args.overwrite
    )

    if args.dry_run:
        print(json.dumps({"status": "dry-run", "command": cmd}))
        return

    if result.returncode != 0:
        print(json.dumps({
            "status": "error",
            "code": result.returncode,
            "message": result.stderr or result.stdout,
            "command": cmd
        }))
        sys.exit(result.returncode)

    output_p = Path(args.output)
    print(json.dumps({
        "status": "success",
        "input": str(input_p),
        "output": str(output_p),
        "operation": args.operation
    }))


if __name__ == "__main__":
    main()
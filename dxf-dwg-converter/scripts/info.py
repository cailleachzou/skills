#!/usr/bin/env python3
"""Check installation status of CAD tools."""

import sys
import json
import subprocess
from pathlib import Path

LIBREDWG_PATH = r"C:\Program Files\libredwg-0.13.4-win32"

TOOLS = [
    "dwg2dxf.exe",
    "dxf2dwg.exe",
    "dwg2SVG.exe",
    "dwgread.exe",
    "dwglayers.exe",
    "dwggrep.exe",
    "dwgbmp.exe",
]


def main():
    result = {
        "libredwg": {
            "path": LIBREDWG_PATH,
            "installed": False,
            "tools": {}
        },
        "ezdxf": {
            "installed": False,
            "version": None
        }
    }

    # Check LibreDWG
    libre_path = Path(LIBREDWG_PATH)
    if libre_path.exists():
        result["libredwg"]["installed"] = True
        for tool in TOOLS:
            tool_path = libre_path / tool
            result["libredwg"]["tools"][tool] = tool_path.exists()
    else:
        print(json.dumps({"status": "error", "message": f"LibreDWG not found at {LIBREDWG_PATH}"}))
        sys.exit(1)

    # Check ezdxf
    try:
        import ezdxf
        result["ezdxf"]["installed"] = True
        result["ezdxf"]["version"] = ezdxf.__version__
    except ImportError:
        pass

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
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

# MinGW runtime DLLs required on 64-bit Windows. The official
# libredwg-0.13.4-win32 zip omits these, so EXEs silently fail with
# STATUS_DLL_NOT_FOUND (0xC0000135) without them.
MINGW_RUNTIME_DLLS = [
    "libgcc_s_dw2-1.dll",
    "libstdc++-6.dll",
]


def check_runtime(libre_path):
    """Verify MinGW runtime DLLs are present and the EXEs can launch."""
    missing = [dll for dll in MINGW_RUNTIME_DLLS if not (libre_path / dll).exists()]

    smoke_ok = True
    smoke_error = None
    if not missing:
        dwg2dxf = libre_path / "dwg2dxf.exe"
        if dwg2dxf.exists():
            try:
                proc = subprocess.run(
                    [str(dwg2dxf), "--help"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if proc.returncode != 0 and "STATUS_DLL_NOT_FOUND" in (proc.stderr or ""):
                    smoke_ok = False
                    smoke_error = proc.stderr.strip()
            except subprocess.TimeoutExpired:
                pass
            except FileNotFoundError as e:
                smoke_ok = False
                smoke_error = str(e)

    runtime_ok = (not missing) and smoke_ok

    remediation = None
    if not runtime_ok:
        remediation = (
            f"Copy {', '.join(MINGW_RUNTIME_DLLS)} from any MinGW-w64 distribution "
            f"into {LIBREDWG_PATH}\\. "
            f"Verify with: python scripts/info.py"
        )
        if smoke_error:
            remediation += f" (smoke-test error: {smoke_error})"

    return {
        "runtime_ok": runtime_ok,
        "missing_dlls": missing,
        "smoke_test_ok": smoke_ok,
        "remediation": remediation,
    }


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

    result["runtime"] = check_runtime(libre_path)

    print(json.dumps(result, indent=2))

    if not result["runtime"]["runtime_ok"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
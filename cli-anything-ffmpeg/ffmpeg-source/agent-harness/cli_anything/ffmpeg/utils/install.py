"""Build detection and installation check for ffmpeg/ffprobe binaries."""

import subprocess
import shutil
import re
import os
from typing import Optional, Tuple, Dict, Any


def find_binary(name: str) -> Optional[str]:
    """Find ffmpeg or ffprobe binary in PATH."""
    return shutil.which(name)


def get_version(binary: str = "ffmpeg") -> Optional[str]:
    """Get ffmpeg version string."""
    try:
        result = subprocess.run(
            [binary, "-version"],
            capture_output=True,
            text=True,
            errors="replace",
            timeout=10,
        )
        if result.returncode == 0:
            # Parse first line: "ffmpeg version 7.1 Copyright ..."
            first_line = result.stdout.splitlines()[0] if result.stdout else ""
            m = re.search(r"ffmpeg\s+version\s+([\d.]+)", first_line)
            if m:
                return m.group(1)
            # Fallback: just return the first line
            return first_line.strip()
    except Exception:
        pass
    return None


def check_installation() -> Dict[str, Any]:
    """Check ffmpeg and ffprobe installation status."""
    ffmpeg_bin = find_binary("ffmpeg")
    ffprobe_bin = find_binary("ffprobe")

    result = {
        "ffmpeg": {
            "found": ffmpeg_bin is not None,
            "path": ffmpeg_bin,
            "version": get_version("ffmpeg") if ffmpeg_bin else None,
        },
        "ffprobe": {
            "found": ffprobe_bin is not None,
            "path": ffprobe_bin,
            "version": get_version("ffprobe") if ffprobe_bin else None,
        },
    }

    # Check shared libraries path
    if ffmpeg_bin:
        result["lib_path"] = os.path.dirname(ffmpeg_bin)

    return result


def get_codecs(binary: str = "ffmpeg") -> Dict[str, list]:
    """Get available encoders/decoders."""
    try:
        result = subprocess.run(
            [binary, "-hide_banner", "-encoders"],
            capture_output=True,
            text=True,
            errors="replace",
            timeout=15,
        )
        encoders = []
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                m = re.match(r"\s+[VAFS]\s+([a-z0-9_]+)\s+(.+)", line)
                if m:
                    encoders.append({"codec": m.group(1), "name": m.group(2).strip()})
    except Exception:
        encoders = []

    try:
        result = subprocess.run(
            [binary, "-hide_banner", "-decoders"],
            capture_output=True,
            text=True,
            errors="replace",
            timeout=15,
        )
        decoders = []
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                m = re.match(r"\s+[VAFS]\s+([a-z0-9_]+)\s+(.+)", line)
                if m:
                    decoders.append({"codec": m.group(1), "name": m.group(2).strip()})
    except Exception:
        decoders = []

    return {"encoders": encoders, "decoders": decoders}


def get_filters(binary: str = "ffmpeg") -> list:
    """Get available filters."""
    try:
        result = subprocess.run(
            [binary, "-hide_banner", "-filters"],
            capture_output=True,
            text=True,
            errors="replace",
            timeout=15,
        )
        filters = []
        if result.returncode == 0:
            for line in result.stdout.splitlines()[4:]:  # Skip header
                parts = line.split()
                if len(parts) >= 3:
                    filters.append(parts[0])
    except Exception:
        pass
    return filters


def ensure_ffmpeg() -> Tuple[bool, str]:
    """Ensure ffmpeg is installed. Returns (ok, message)."""
    info = check_installation()
    if not info["ffmpeg"]["found"]:
        return False, "ffmpeg not found in PATH. Install from https://ffmpeg.org"
    if not info["ffprobe"]["found"]:
        return False, "ffprobe not found in PATH (needed for probe commands)"
    return True, f"ffmpeg {info['ffmpeg']['version']} at {info['ffmpeg']['path']}"
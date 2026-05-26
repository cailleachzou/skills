"""Option validation utilities."""

import os
import re
from pathlib import Path
from typing import Tuple, Optional, List


def validate_input_path(path: str) -> Tuple[bool, Optional[str]]:
    """Check input file exists and is readable."""
    p = Path(path)
    if not p.exists():
        return False, f"Input file not found: {path}"
    if not os.access(p, os.R_OK):
        return False, f"Input file not readable: {path}"
    return True, None


def validate_output_path(path: str, overwrite: bool = False) -> Tuple[bool, Optional[str]]:
    """Check output path is valid and writable."""
    p = Path(path)
    if p.exists():
        if not overwrite:
            return False, f"Output file exists (use -y to overwrite): {path}"
        if not os.access(p, os.W_OK):
            return False, f"Output file not writable: {path}"
    else:
        parent = p.parent
        if not parent.exists():
            try:
                parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                return False, f"Cannot create output directory: {e}"
        if not os.access(parent, os.W_OK):
            return False, f"Output directory not writable: {parent}"
    return True, None


def validate_codec(codec: str, codec_type: str = "video") -> bool:
    """Check if codec is valid (basic check)."""
    # Common valid codec names
    if codec == "copy":
        return True
    # Allow literal codec names
    if re.match(r"^[a-z0-9_]+$", codec):
        return True
    return False


def validate_preset_name(name: str) -> bool:
    """Preset names must be alphanumeric + hyphens."""
    return bool(re.match(r"^[a-zA-Z0-9_-]+$", name))


def validate_bitrate(bitrate: str) -> bool:
    """Validate bitrate string (e.g. '2M', '500k')."""
    if not bitrate:
        return False
    return bool(re.match(r"^\d+(\.\d+)?[kKmMgG]?$", bitrate))


def validate_resolution(res: str) -> Tuple[bool, Optional[str]]:
    """Validate resolution string (e.g. '1920x1080')."""
    if not res:
        return False, "Resolution cannot be empty"
    m = re.match(r"^(\d+)x(\d+)$", res)
    if not m:
        return False, f"Invalid resolution format: {res} (expected WxH)"
    w, h = int(m.group(1)), int(m.group(2))
    if w <= 0 or h <= 0:
        return False, f"Invalid resolution: {w}x{h}"
    if w > 8192 or h > 8192:
        return False, f"Resolution too large: {w}x{h} (max 8192x8192)"
    return True, None


def validate_crf(crf: int) -> Tuple[bool, Optional[str]]:
    """Validate CRF value."""
    if not 0 <= crf <= 51:
        return False, f"CRF must be between 0 and 51, got {crf}"
    return True, None


def validate_time(time_str: str) -> Tuple[bool, Optional[str]]:
    """Validate time string (HH:MM:SS.ms or seconds)."""
    if not time_str:
        return False, "Time cannot be empty"
    # Seconds as float
    try:
        float(time_str)
        return True, None
    except ValueError:
        pass
    # HH:MM:SS.ms format
    m = re.match(r"^(\d+):(\d{1,2}):(\d{1,2})(?:\.(\d+))?$", time_str)
    if not m:
        return False, f"Invalid time format: {time_str}"
    h, m, s = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if m >= 60 or s >= 60:
        return False, f"Invalid time value: {time_str}"
    return True, None


def validate_filters(filters: str) -> Tuple[bool, Optional[str]]:
    """Basic filter chain validation."""
    if not filters:
        return True, None
    # Basic check: no unbalanced quotes
    if filters.count("'") % 2 != 0:
        return False, "Unbalanced quotes in filter chain"
    # Check for common filter names
    known_filters = [
        "scale", "crop", "trim", "overlay", "fade", "setpts",
        "volume", "anull", "null", "copy", "resize", "rotate",
        "drawtext", "subtitles", "deinterlace", "yadif", "unsharp",
    ]
    # Just check syntax roughly
    return True, None


def build_validation_report(errors: List[str]) -> str:
    """Build a validation report from error list."""
    if not errors:
        return "Validation passed."
    lines = ["[ffmpeg] Validation failed:"]
    for e in errors:
        lines.append(f"  - {e}")
    return "\n".join(lines)
"""Output formatters — JSON and human-readable."""

import json
from typing import Dict, Any, Optional, List


class OutputFormatter:
    def __init__(self, json_mode: bool = False):
        self.json_mode = json_mode

    def format(self, data: Dict[str, Any]) -> str:
        if self.json_mode:
            return json.dumps(data, indent=2, ensure_ascii=False)
        return self._format_human(data)

    def _format_human(self, data: Dict[str, Any]) -> str:
        """Format result as human-readable text."""
        status = data.get("status", "unknown")
        if status == "error":
            return f"[ffmpeg] ERROR: {data.get('error', 'unknown')}"
        if status == "failed":
            return f"[ffmpeg] FAILED: {data.get('stderr', data.get('error', 'unknown'))}"
        if status == "complete":
            lines = [f"[ffmpeg] Complete: {data.get('output', '?')}"]
            v = data.get("video")
            a = data.get("audio")
            if v:
                lines.append(f"  Video: {v.get('codec', '?')}, {v.get('width', '?')}x{v.get('height', '?')}, {v.get('fps', '?')}fps")
            if a:
                lines.append(f"  Audio: {a.get('codec', '?')}, {a.get('sample_rate', '?')}Hz, {a.get('bitrate', '?')}bps")
            dur = data.get("duration")
            if dur:
                lines.append(f"  Duration: {dur:.1f}s")
            sz = data.get("size_bytes")
            if sz:
                lines.append(f"  Size: {_format_size(sz)}")
            return "\n".join(lines)
        if status == "probe":
            return self._format_probe(data)
        return json.dumps(data, indent=2, ensure_ascii=False)

    def _format_probe(self, data: Dict[str, Any]) -> str:
        lines = [f"[ffprobe] {data.get('filename', '?')}"]
        v = data.get("video")
        a = data.get("audio")
        if v:
            lines.append(f"  Video: {v.get('codec', '?')} {v.get('width', '?')}x{v.get('height', '?')} @ {v.get('fps', '?')}fps")
        if a:
            lines.append(f"  Audio: {a.get('codec', '?')} {v.get('sample_rate', '?')}Hz ch{data.get('channels', '?')}")
        dur = data.get("duration")
        if dur:
            lines.append(f"  Duration: {_format_duration(dur)}")
        lines.append(f"  Format: {data.get('format', '?')}, {_format_size(data.get('size_bytes', 0))}")
        return "\n".join(lines)


def format_progress(pct: float, current: str, total: str, speed: str, bitrate: str) -> str:
    bar_len = 30
    filled = int(bar_len * pct / 100)
    bar = "#" * filled + "-" * (bar_len - filled)
    return f"\r[{bar}] {pct:5.1f}%  {current}/{total}  speed={speed}  bitrate={bitrate}  "


def _format_size(size_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}TB"


def _format_duration(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"
"""ffprobe wrapper — analyze media streams and extract metadata."""

import json
import subprocess
from typing import Dict, Any, Optional, List


class FFProbe:
    """Wrapper for ffprobe binary."""

    def __init__(self, binary: str = "ffprobe"):
        self.binary = binary

    def _run(self, args: List[str]) -> subprocess.CompletedProcess:
        cmd = [self.binary, "-v", "quiet"] + args
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            errors="replace",
        )

    def probe(self, input_path: str) -> Optional[Dict[str, Any]]:
        """Run full probe on a media file."""
        cmd = [
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            "-show_chapters",
            input_path,
        ]
        result = self._run(cmd)
        if result.returncode != 0:
            return None
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return None

    def streams(self, input_path: str) -> List[Dict[str, Any]]:
        """Get stream info."""
        data = self.probe(input_path)
        if not data:
            return []
        return data.get("streams", [])

    def format_info(self, input_path: str) -> Optional[Dict[str, Any]]:
        """Get format info."""
        data = self.probe(input_path)
        if not data:
            return None
        return data.get("format", {})

    def video_stream(self, input_path: str) -> Optional[Dict[str, Any]]:
        """Get first video stream."""
        for s in self.streams(input_path):
            if s.get("codec_type") == "video":
                return s
        return None

    def audio_stream(self, input_path: str) -> Optional[Dict[str, Any]]:
        """Get first audio stream."""
        for s in self.streams(input_path):
            if s.get("codec_type") == "audio":
                return s
        return None

    def summary(self, input_path: str) -> Dict[str, Any]:
        """Get a quick human-readable summary."""
        data = self.probe(input_path)
        if not data:
            return {"error": "probe failed"}

        streams = data.get("streams", [])
        fmt = data.get("format", {})

        video = None
        audio = None
        for s in streams:
            if s.get("codec_type") == "video" and not video:
                video = {
                    "codec": s.get("codec_name"),
                    "width": s.get("width"),
                    "height": s.get("height"),
                    "fps": self._parse_fps(s.get("r_frame_rate")),
                    "bitrate": s.get("bit_rate"),
                    "pix_fmt": s.get("pix_fmt"),
                }
            elif s.get("codec_type") == "audio" and not audio:
                audio = {
                    "codec": s.get("codec_name"),
                    "sample_rate": s.get("sample_rate"),
                    "channels": s.get("channels"),
                    "bitrate": s.get("bit_rate"),
                }

        return {
            "filename": fmt.get("filename"),
            "format": fmt.get("format_name"),
            "duration": float(fmt.get("duration", 0)),
            "size_bytes": int(fmt.get("size", 0)),
            "bitrate": int(fmt.get("bit_rate", 0)),
            "video": video,
            "audio": audio,
        }

    def _parse_fps(self, fps_str: Optional[str]) -> Optional[float]:
        if not fps_str:
            return None
        try:
            num, denom = fps_str.split("/")
            return float(num) / float(denom)
        except (ValueError, ZeroDivisionError):
            return None
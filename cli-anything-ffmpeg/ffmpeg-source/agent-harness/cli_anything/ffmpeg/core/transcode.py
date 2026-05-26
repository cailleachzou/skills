"""ffmpeg subprocess runner — executes transcode jobs."""

import subprocess
import re
import json
import os
import signal
from typing import Dict, Any, List, Optional, Callable, Tuple
from pathlib import Path

from .preset import get_preset, to_ffmpeg_args


class FFmpegRunner:
    """Run ffmpeg transcode jobs with progress tracking."""

    def __init__(self, binary: str = "ffmpeg", progress_callback: Optional[Callable] = None):
        self.binary = binary
        self.progress_callback = progress_callback
        self._process: Optional[subprocess.Popen] = None

    def transcode(
        self,
        input_path: str,
        output_path: str,
        preset_name: str = "default",
        extra_args: Optional[List[str]] = None,
        overwrite: bool = True,
        dry_run: bool = False,
    ) -> Tuple[int, str, str]:
        """Run a transcode job. Returns (returncode, stdout, stderr)."""
        preset = get_preset(preset_name)
        if not preset:
            return 1, "", f"Unknown preset: {preset_name}"

        args = [self.binary]

        # Global options
        args += ["-y"] if overwrite else ["-n"]
        args += ["-hide_banner"]

        # Input
        args += ["-i", input_path]

        # Preset encoding args
        args += to_ffmpeg_args(preset)

        # Extra user args
        if extra_args:
            args.extend(extra_args)

        # Output
        args.append(output_path)

        if dry_run:
            cmd_str = subprocess.list2cmdline(args)
            return 0, cmd_str, "(dry run)"

        # Run
        self._process = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            errors="replace",
        )
        stdout, stderr = self._process.communicate()
        return self._process.returncode, stdout, stderr

    def probe_and_transcode(
        self,
        input_path: str,
        output_path: str,
        preset_name: str = "default",
        extra_args: Optional[List[str]] = None,
        overwrite: bool = True,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Full pipeline: probe → transcode → probe output."""
        from .probe import FFProbe

        # Probe input
        probe = FFProbe(self.binary.replace("ffmpeg", "ffprobe"))
        input_info = probe.summary(input_path)

        if input_info.get("error"):
            return {"status": "error", "error": f"Input probe failed: {input_info['error']}"}

        # Transcode
        code, out, err = self.transcode(
            input_path, output_path, preset_name, extra_args, overwrite, dry_run
        )

        if code != 0:
            return {
                "status": "failed",
                "returncode": code,
                "stderr": self._parse_error(err),
                "input": input_info,
            }

        # Probe output
        output_info = probe.summary(output_path)

        return {
            "status": "complete",
            "input": input_path,
            "output": output_path,
            "video": output_info.get("video"),
            "audio": output_info.get("audio"),
            "duration": output_info.get("duration"),
            "size_bytes": output_info.get("size_bytes"),
        }

    def _parse_error(self, stderr: str) -> str:
        """Extract the most useful error line from ffmpeg stderr."""
        if not stderr:
            return "Unknown error"
        lines = stderr.strip().splitlines()
        # Last non-empty line before "Error" markers is usually the key message
        for line in reversed(lines):
            if line.strip() and not line.startswith("ffmpeg version"):
                return line.strip()
        return lines[-1] if lines else "Unknown error"

    def parse_progress(self, stderr: str) -> Optional[Dict[str, Any]]:
        """Parse progress from ffmpeg stderr output."""
        # ffmpeg -progress output goes to stdout, not stderr
        # This parses ffmpeg's textual progress output in stderr
        progress = {}
        time_re = re.compile(r"time=(\d+):(\d+):(\d+\.\d+)")
        speed_re = re.compile(r"speed=\s*([\d.]+)x")
        size_re = re.compile(r"size=\s*(\d+)kB")
        bitrate_re = re.compile(r"bitrate=\s*([\d.]+)kbits/s")

        for line in stderr.splitlines():
            tm = time_re.search(line)
            if tm:
                h, m, s = int(tm.group(1)), int(tm.group(2)), float(tm.group(3))
                progress["time_current"] = f"{h:02d}:{m:02d}:{tm.group(3)}"
                progress["time_secs"] = h * 3600 + m * 60 + s
            sm = speed_re.search(line)
            if sm:
                progress["speed"] = f"{sm.group(1)}x"
            szm = size_re.search(line)
            if szm:
                progress["size_kb"] = int(szm.group(1))
            brm = bitrate_re.search(line)
            if brm:
                progress["bitrate"] = f"{brm.group(1)}k"

        return progress if progress else None

    def cancel(self) -> None:
        """Cancel running job."""
        if self._process and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
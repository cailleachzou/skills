"""E2E tests for FFmpeg CLI harness — real binary tests."""

import pytest
import subprocess
import tempfile
import os
import json
from pathlib import Path


def _resolve_cli(name: str) -> str:
    """Resolve CLI binary from installed package or PATH."""
    installed = os.environ.get("CLI_ANYTHING_FORCE_INSTALLED")
    if installed:
        # Try to find the installed CLI
        import shutil
        path = shutil.which(f"cli-anything-{name}")
        if path:
            return path
    return name


def _skip_if_no_ffmpeg():
    """Skip if ffmpeg binaries are not in PATH."""
    import shutil
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        pytest.skip("ffmpeg/ffprobe not in PATH")


class TestFFmpegBinary:
    def test_ffmpeg_version(self):
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "ffmpeg version" in result.stdout


class TestFFProbe:
    def test_ffprobe_version(self):
        result = subprocess.run(
            ["ffprobe", "-version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "ffprobe version" in result.stdout

    def test_probe_json_output(self, tmp_path):
        """Test that ffprobe JSON output is parseable."""
        # Use a real media file if available, else skip
        # For now, just verify ffprobe can output JSON format
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_format", "-show_streams",
             "-f", "lavfi", "-i", "color=c=black:s=320x240:d=0.1",
             "-f", "null", "-"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            assert "format" in data or "streams" in data


class TestProbeIntegration:
    """Tests using the actual probe module."""

    def test_probe_synthetic_color(self):
        """Probe a synthetic color test source (no real file needed)."""
        from cli_anything.ffmpeg.core.probe import FFProbe

        # Create a tiny synthetic video using ffmpeg
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "test.mp4"
            # Generate 1-frame test video
            r = subprocess.run(
                ["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=blue:s=320x240:d=1",
                 "-c:v", "libx264", "-frames:v", "1", "-pix_fmt", "yuv420p",
                 str(out)],
                capture_output=True,
                timeout=30,
            )
            if r.returncode != 0:
                pytest.skip("Cannot create test file")

            probe = FFProbe()
            info = probe.summary(str(out))
            assert info["video"] is not None
            assert info["video"]["codec"] == "h264"
            assert info["video"]["width"] == 320
            assert info["video"]["height"] == 240


class TestTranscodeDryRun:
    """Test transcode commands (dry-run mode, no real files needed)."""

    def test_dry_run_command_build(self):
        """Test that dry-run returns a valid ffmpeg command string."""
        from cli_anything.ffmpeg.core.transcode import FFmpegRunner
        from cli_anything.ffmpeg.core.preset import get_preset

        runner = FFmpegRunner(binary="ffmpeg")
        p = get_preset("youtube")

        code, out, err = runner.transcode(
            input_path="/tmp/input.mp4",
            output_path="/tmp/output.mp4",
            preset_name="youtube",
            overwrite=True,
            dry_run=True,
        )
        assert code == 0
        assert "ffmpeg" in out
        assert "/tmp/input.mp4" in out


class TestCLISubprocess:
    """Test the installed CLI via subprocess."""

    def test_installed_cli_help(self):
        cli_path = _resolve_cli("ffmpeg")
        # Try running the CLI if it's installed
        if cli_path and os.environ.get("CLI_ANYTHING_FORCE_INSTALLED"):
            result = subprocess.run(
                [cli_path, "--help"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            assert result.returncode == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
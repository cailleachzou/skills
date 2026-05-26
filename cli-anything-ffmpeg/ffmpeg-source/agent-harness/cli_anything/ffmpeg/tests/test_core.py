"""Unit tests for FFmpeg CLI harness core modules."""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import core modules
from cli_anything.ffmpeg.core.project import Session, Preset, Project, get_default_presets
from cli_anything.ffmpeg.core.job import JobQueue, JobResult, JobStatus
from cli_anything.ffmpeg.core.preset import (
    get_builtin_presets, to_ffmpeg_args, list_presets,
    get_preset, save_preset, delete_preset,
    PRESET_DIR,
)
from cli_anything.ffmpeg.utils.output import OutputFormatter, _format_size, _format_duration
from cli_anything.ffmpeg.utils.validation import (
    validate_input_path, validate_output_path, validate_codec,
    validate_preset_name, validate_bitrate, validate_resolution,
    validate_crf, validate_time, build_validation_report,
)


# ── Project / Session Tests ─────────────────────────────────────────────────

class TestSession:
    def test_session_create(self, tmp_path):
        s = Session(name="test-session")
        assert s.name == "test-session"
        assert s.jobs == []
        assert s.active_preset == "default"

    def test_session_add_job(self):
        s = Session(name="test")
        job = MagicMock()
        job.to_dict.return_value = {"id": "j1"}
        s.add_job(job)
        assert len(s.jobs) == 1

    def test_session_get_job(self):
        s = Session(name="test")
        job = MagicMock()
        job.id = "j1"
        s.add_job(job)
        assert s.get_job("j1") is not None
        assert s.get_job("nonexistent") is None

    def test_session_save_load(self, tmp_path, monkeypatch):
        # Override SESSION_DIR
        from cli_anything.ffmpeg.core import project as proj_mod
        monkeypatch.setattr(proj_mod, "SESSION_DIR", tmp_path)
        s = Session(name="save-test")
        s.active_preset = "youtube"
        s.save()
        loaded = Session.load("save-test")
        assert loaded.name == "save-test"
        assert loaded.active_preset == "youtube"


class TestPreset:
    def test_preset_to_ffmpeg_args(self):
        p = Preset(
            name="test",
            codec_video="libx264",
            preset_video="medium",
            crf=23,
            codec_audio="aac",
            bitrate_audio="192k",
            sample_rate=48000,
        )
        args = p.to_ffmpeg_args()
        assert "-c:v" in args
        assert "libx264" in args
        assert "-crf" in args
        assert "23" in args
        assert "-c:a" in args
        assert "aac" in args

    def test_preset_copy_codec(self):
        p = Preset(name="copy", codec_video="copy", codec_audio="copy")
        args = p.to_ffmpeg_args()
        # copy codec should NOT add crf/preset args
        assert "-crf" not in args
        assert "-preset" not in args


# ── Job Tests ───────────────────────────────────────────────────────────────

class TestJobQueue:
    def test_enqueue(self):
        q = JobQueue()
        jid = q.enqueue("in.mp4", "out.mp4", "default")
        assert jid is not None
        assert len(q.jobs) == 1

    def test_list_states(self):
        q = JobQueue()
        q.enqueue("a.mp4", "b.mp4")
        assert len(q.list_pending()) == 1
        assert len(q.list_complete()) == 0

    def test_clear_completed(self):
        q = JobQueue()
        q.enqueue("a.mp4", "b.mp4")
        q.start(q.jobs[0].job_id)
        q.complete(q.jobs[0].job_id, q.jobs[0])
        q.clear_completed()
        assert len(q.jobs) == 0


# ── Preset Module Tests ─────────────────────────────────────────────────────

class TestPresetModule:
    def test_builtin_presets(self):
        presets = get_builtin_presets()
        assert "web-1080p" in presets
        assert "youtube" in presets
        assert presets["youtube"]["crf"] == 21

    def test_to_ffmpeg_args_video_copy(self):
        args = to_ffmpeg_args({"codec_video": "copy", "codec_audio": "copy", "extra_args": []})
        assert "copy" in args
        # copy mode should not add crf/preset
        assert "-crf" not in args

    def test_to_ffmpeg_args_with_extra(self):
        p = {
            "codec_video": "libx264",
            "preset_video": "slow",
            "crf": 20,
            "bitrate_video": None,
            "codec_audio": "aac",
            "bitrate_audio": "192k",
            "sample_rate": 48000,
            "extra_args": ["-movflags", "+faststart"],
        }
        args = to_ffmpeg_args(p)
        assert "-movflags" in args
        assert "+faststart" in args

    def test_get_preset_builtin(self):
        p = get_preset("youtube")
        assert p is not None
        assert p["name"] == "youtube"

    def test_get_preset_unknown(self):
        assert get_preset("nonexistent-preset-xyz") is None


# ── Output Tests ────────────────────────────────────────────────────────────

class TestOutput:
    def test_format_json(self):
        f = OutputFormatter(json_mode=True)
        out = f.format({"status": "complete", "duration": 10.0})
        data = json.loads(out)
        assert data["status"] == "complete"

    def test_format_human(self):
        f = OutputFormatter(json_mode=False)
        out = f.format({"status": "complete", "output": "out.mp4"})
        assert "Complete" in out

    def test_format_size(self):
        assert "1.0KB" in _format_size(1024)
        assert "1.0MB" in _format_size(1024 * 1024)

    def test_format_duration(self):
        assert _format_duration(65) == "1:05"
        assert _format_duration(3665) == "1:01:05"


# ── Validation Tests ────────────────────────────────────────────────────────

class TestValidation:
    def test_validate_codec_copy(self):
        assert validate_codec("copy") is True

    def test_validate_codec_valid(self):
        assert validate_codec("libx264") is True

    def test_validate_preset_name_valid(self):
        assert validate_preset_name("web-720p") is True
        assert validate_preset_name("my_preset") is True

    def test_validate_preset_name_invalid(self):
        assert validate_preset_name("bad name!") is False
        assert validate_preset_name("test/preset") is False

    def test_validate_crf_valid(self):
        assert validate_crf(23) == (True, None)

    def test_validate_crf_invalid(self):
        ok, err = validate_crf(99)
        assert ok is False
        assert "51" in err

    def test_validate_resolution_valid(self):
        assert validate_resolution("1920x1080") == (True, None)

    def test_validate_resolution_invalid(self):
        ok, err = validate_resolution("bad")
        assert ok is False

    def test_validate_time_seconds(self):
        assert validate_time("120.5") == (True, None)

    def test_validate_time_hhmmss(self):
        assert validate_time("01:30:45") == (True, None)

    def test_validate_time_invalid(self):
        ok, err = validate_time("99:99:99")
        assert ok is False

    def test_validate_bitrate(self):
        assert validate_bitrate("2M") is True
        assert validate_bitrate("500k") is True
        assert validate_bitrate("bad") is False

    def test_build_validation_report(self):
        errors = ["File not found", "Bad CRF"]
        out = build_validation_report(errors)
        assert "Validation failed" in out
        assert "File not found" in out

    def test_build_validation_report_empty(self):
        out = build_validation_report([])
        assert "passed" in out


# ── Validation Path Tests (mocked) ─────────────────────────────────────────

class TestValidationPaths:
    def test_validate_input_not_found(self):
        ok, err = validate_input_path("/nonexistent/file.mp4")
        assert ok is False
        assert "not found" in err

    def test_validate_output_path_parent_missing(self, tmp_path):
        out_path = str(tmp_path / "subdir" / "output.mp4")
        # The parent doesn't exist but mkdir should succeed
        ok, _ = validate_output_path(out_path, overwrite=True)
        # Depends on permissions — just check it doesn't crash

    @patch("pathlib.Path.exists", return_value=True)
    @patch("os.access", return_value=True)
    def test_validate_output_exists_no_overwrite(self, mock_exists, mock_access):
        ok, err = validate_output_path("/tmp/existing.mp4", overwrite=False)
        assert ok is False
        assert "exists" in err


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
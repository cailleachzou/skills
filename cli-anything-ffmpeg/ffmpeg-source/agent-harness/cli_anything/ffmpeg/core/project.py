"""Project and session management for FFmpeg CLI harness."""

import json
import os
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from pathlib import Path

SESSION_DIR = Path.home() / ".cli-anything-ffmpeg" / "sessions"
SESSION_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class Job:
    """Single transcode job."""
    id: str
    input_path: str
    output_path: str
    preset: str
    status: str = "pending"  # pending, running, complete, failed
    error: Optional[str] = None
    duration: Optional[float] = None
    size_bytes: Optional[int] = None
    video_info: Optional[Dict[str, Any]] = None
    audio_info: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class Preset:
    """Encoding preset."""
    name: str
    codec_video: str = "libx264"
    codec_audio: str = "aac"
    preset_video: str = "medium"
    crf: int = 23
    bitrate_video: Optional[str] = None
    bitrate_audio: str = "192k"
    sample_rate: int = 48000
    extra_args: List[str] = field(default_factory=list)

    def to_ffmpeg_args(self) -> List[str]:
        args = ["-c:v", self.codec_video]
        if self.codec_video != "copy":
            args += ["-preset", self.preset_video]
            if self.crf:
                args += ["-crf", str(self.crf)]
            if self.bitrate_video:
                args += ["-b:v", self.bitrate_video]
        args += ["-c:a", self.codec_audio]
        if self.codec_audio != "copy":
            args += ["-b:a", self.bitrate_audio, "-ar", str(self.sample_rate)]
        args.extend(self.extra_args)
        return args

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["extra_args"] = self.extra_args
        return d


@dataclass
class Session:
    """FFmpeg CLI session — holds job queue and settings."""
    name: str
    version: int = 1
    jobs: List[Job] = field(default_factory=list)
    active_preset: str = "default"
    global_opts: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[str] = None

    def path(self) -> Path:
        return SESSION_DIR / f"{self.name}.json"

    def save(self) -> None:
        data = {
            "version": self.version,
            "name": self.name,
            "jobs": [j.to_dict() for j in self.jobs],
            "active_preset": self.active_preset,
            "global_opts": self.global_opts,
            "created_at": self.created_at,
        }
        with open(self.path(), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, name: str) -> "Session":
        p = SESSION_DIR / f"{name}.json"
        if not p.exists():
            return cls(name=name)
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        jobs = [Job(**j) for j in data.get("jobs", [])]
        s = cls(
            name=data["name"],
            version=data.get("version", 1),
            jobs=jobs,
            active_preset=data.get("active_preset", "default"),
            global_opts=data.get("global_opts", {}),
            created_at=data.get("created_at"),
        )
        return s

    def add_job(self, job: Job) -> None:
        self.jobs.append(job)

    def get_job(self, job_id: str) -> Optional[Job]:
        for j in self.jobs:
            if j.id == job_id:
                return j
        return None

    def list_sessions() -> List[str]:
        if not SESSION_DIR.exists():
            return []
        return [p.stem for p in SESSION_DIR.glob("*.json")]


@dataclass
class Project:
    """Named project — collection of source files + target settings."""
    name: str
    source_dir: str
    output_dir: str
    preset: str = "default"
    session_name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def get_default_presets() -> Dict[str, Preset]:
    return {
        "web-1080p": Preset(
            name="web-1080p",
            codec_video="libx264",
            preset_video="medium",
            crf=23,
            codec_audio="aac",
            bitrate_audio="192k",
            extra_args=["-movflags", "+faststart"],
        ),
        "web-720p": Preset(
            name="web-720p",
            codec_video="libx264",
            preset_video="medium",
            crf=24,
            codec_audio="aac",
            bitrate_audio="128k",
            extra_args=["-movflags", "+faststart", "-vf", "scale=-2:720"],
        ),
        "archive-high": Preset(
            name="archive-high",
            codec_video="libx265",
            preset_video="slow",
            crf=20,
            codec_audio="flac",
            extra_args=["-pix_fmt", "yuv420p10"],
        ),
        "fast-copy": Preset(
            name="fast-copy",
            codec_video="copy",
            codec_audio="copy",
        ),
        "youtube": Preset(
            name="youtube",
            codec_video="libx264",
            preset_video="medium",
            crf=21,
            codec_audio="aac",
            bitrate_audio="320k",
            extra_args=["-movflags", "+faststart"],
        ),
        "default": Preset(name="default"),
    }
"""Encoding preset library for FFmpeg CLI."""

import json
from pathlib import Path
from typing import Dict, List, Optional

PRESET_DIR = Path.home() / ".cli-anything-ffmpeg" / "presets"
PRESET_DIR.mkdir(parents=True, exist_ok=True)


def get_builtin_presets() -> Dict[str, dict]:
    return {
        "web-1080p": {
            "name": "web-1080p",
            "codec_video": "libx264",
            "preset_video": "medium",
            "crf": 23,
            "bitrate_video": None,
            "codec_audio": "aac",
            "bitrate_audio": "192k",
            "sample_rate": 48000,
            "extra_args": ["-movflags", "+faststart"],
        },
        "web-720p": {
            "name": "web-720p",
            "codec_video": "libx264",
            "preset_video": "medium",
            "crf": 24,
            "codec_audio": "aac",
            "bitrate_audio": "128k",
            "sample_rate": 48000,
            "extra_args": ["-movflags", "+faststart", "-vf", "scale=-2:720"],
        },
        "archive-high": {
            "name": "archive-high",
            "codec_video": "libx265",
            "preset_video": "slow",
            "crf": 20,
            "codec_audio": "flac",
            "sample_rate": 48000,
            "extra_args": ["-pix_fmt", "yuv420p10"],
        },
        "fast-copy": {
            "name": "fast-copy",
            "codec_video": "copy",
            "codec_audio": "copy",
            "extra_args": [],
        },
        "youtube": {
            "name": "youtube",
            "codec_video": "libx264",
            "preset_video": "medium",
            "crf": 21,
            "codec_audio": "aac",
            "bitrate_audio": "320k",
            "sample_rate": 48000,
            "extra_args": ["-movflags", "+faststart"],
        },
        "default": {
            "name": "default",
            "codec_video": "libx264",
            "preset_video": "medium",
            "crf": 23,
            "codec_audio": "aac",
            "bitrate_audio": "192k",
            "sample_rate": 48000,
            "extra_args": [],
        },
    }


def to_ffmpeg_args(preset: dict) -> List[str]:
    args = []
    # Video
    args += ["-c:v", preset["codec_video"]]
    if preset["codec_video"] != "copy":
        if preset.get("preset_video"):
            args += ["-preset", preset["preset_video"]]
        if preset.get("crf") is not None:
            args += ["-crf", str(preset["crf"])]
        if preset.get("bitrate_video"):
            args += ["-b:v", preset["bitrate_video"]]
    # Audio
    args += ["-c:a", preset["codec_audio"]]
    if preset["codec_audio"] != "copy":
        args += ["-b:a", preset.get("bitrate_audio", "192k")]
        args += ["-ar", str(preset.get("sample_rate", 48000))]
    # Extra
    args.extend(preset.get("extra_args", []))
    return args


def list_presets() -> List[str]:
    """List all available presets (builtin + user)."""
    names = list(get_builtin_presets().keys())
    for p in PRESET_DIR.glob("*.json"):
        name = p.stem
        if name not in names:
            names.append(name)
    return sorted(names)


def get_preset(name: str) -> Optional[dict]:
    """Get a preset by name."""
    builtins = get_builtin_presets()
    if name in builtins:
        return builtins[name]
    # User preset
    path = PRESET_DIR / f"{name}.json"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return None


def save_preset(name: str, preset: dict) -> None:
    """Save a user preset."""
    path = PRESET_DIR / f"{name}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(preset, f, indent=2, ensure_ascii=False)


def delete_preset(name: str) -> bool:
    """Delete a user preset. Returns False if builtin."""
    if name in get_builtin_presets():
        return False
    path = PRESET_DIR / f"{name}.json"
    if path.exists():
        path.unlink()
        return True
    return False


def import_preset(path: str) -> Optional[str]:
    """Import a preset from a JSON file. Returns preset name."""
    import shutil
    name = Path(path).stem
    dest = PRESET_DIR / f"{name}.json"
    shutil.copy(path, dest)
    return name
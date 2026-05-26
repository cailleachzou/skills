---
name: cli-anything-ffmpeg
description: AI-friendly CLI harness for FFmpeg — transcode, probe, batch-process media with presets, session management, and JSON output. Use when users ask to convert/encode/transcode video, probe media files, batch process video files, or manage encoding presets.
type: skill
---

# cli-anything-ffmpeg

AI-friendly CLI harness wrapping `ffmpeg` and `ffprobe` binaries — adds stateful session management, encoding presets, job queues, batch processing, and machine-readable JSON output for AI agent consumption.

## Commands

### `transcode run` — Single file transcode

```bash
ffmpeg transcode run INPUT OUTPUT [OPTIONS]
```

**Options:**
- `--preset, -p` — Encoding preset (default: `default`)
- `--crf` — Override CRF (quality 0-51)
- `--codec-video, -c:v` — Video codec (libx264, libx265, copy, etc.)
- `--codec-audio, -c:a` — Audio codec (aac, mp3, copy, flac, etc.)
- `--bitrate-video, -b:v` — Video bitrate (e.g. `2M`)
- `--bitrate-audio, -b:a` — Audio bitrate (e.g. `192k`)
- `--vf` — Video filter chain
- `--af` — Audio filter chain
- `--resolution, -s` — Output resolution (e.g. `1920x1080`)
- `--fps, -r` — Frame rate
- `--start, -ss` — Start time
- `--duration, -t` — Duration in seconds
- `--y` — Overwrite output without asking
- `--dry-run` — Show command without executing

**Examples:**
```bash
# Convert to web 1080p H.264
ffmpeg transcode run input.avi output.mp4 --preset web-1080p

# H.265 for archiving
ffmpeg transcode run input.mp4 archive.mp4 --preset archive-high

# Remux without re-encoding (fast!)
ffmpeg transcode run input.mkv output.mp4 --preset fast-copy

# Crop to 720p with custom CRF
ffmpeg transcode run input.mp4 output.mp4 -p youtube --crf 20 --vf scale=1280:720

# Extract audio only
ffmpeg transcode run video.mp4 audio.aac -c:v copy -c:a aac -b:a 256k

# Dry run — see exact ffmpeg command
ffmpeg transcode run input.mp4 output.mp4 --preset youtube --dry-run
```

### `transcode batch` — Batch transcode

```bash
ffmpeg transcode batch "*.mp4" OUTPUT_DIR [OPTIONS]
```

**Options:**
- `--preset, -p` — Encoding preset
- `--suffix` — Output filename suffix (default: `_converted`)
- `--y` — Overwrite outputs

### `probe info` — Inspect media file

```bash
ffmpeg probe info INPUT [--full]
```

Returns codec, resolution, fps, duration, bitrate for video and audio streams.

### `probe streams` — List all streams

```bash
ffmpeg probe streams INPUT
```

### `probe format` — Container info

```bash
ffmpeg probe format INPUT
```

### `preset list` — Available presets

```bash
ffmpeg preset list
```

### `preset show` — Preset details

```bash
ffmpeg preset show PRESET_NAME
```

### `preset create` — Create custom preset

```bash
ffmpeg preset create NAME \
  --codec-video libx265 --preset-video slow --crf 20 \
  --codec-audio flac --bitrate-audio 512k
```

### `preset delete` — Delete custom preset

```bash
ffmpeg preset delete my-preset
```

### `session save/load` — Session management

```bash
ffmpeg session save my-project --preset youtube
ffmpeg session load my-project
```

### `info status` — Check installation

```bash
ffmpeg info status
ffmpeg info codecs
ffmpeg info filters
```

## Built-in Presets

| Preset | Video Codec | CRF | Audio | Best for |
|--------|-------------|-----|-------|----------|
| `web-1080p` | libx264 | 23 | AAC 192k | Web delivery |
| `web-720p` | libx264 | 24 | AAC 128k | Mobile web |
| `youtube` | libx264 | 21 | AAC 320k | YouTube upload |
| `archive-high` | libx265 | 20 | FLAC | Long-term archive |
| `fast-copy` | copy | — | copy | Remux only |
| `default` | libx264 | 23 | AAC 192k | General purpose |

## JSON Output

Add `--json` to any command for machine-readable output:

```bash
ffmpeg --json probe info video.mp4
```

```json
{
  "status": "probe",
  "filename": "video.mp4",
  "format": "mov,mp4,m4a,3gp,3g2,mj2",
  "duration": 185.5,
  "size_bytes": 10485760,
  "video": {
    "codec": "h264",
    "width": 1920,
    "height": 1080,
    "fps": 24.0
  },
  "audio": {
    "codec": "aac",
    "sample_rate": 48000,
    "channels": 2,
    "bitrate": 192000
  }
}
```

## Common Workflows

### Video to GIF
```bash
ffmpeg transcode run input.mp4 output.gif -c:v copy -vf "fps=10,scale=480:-1"
```

### Extract audio track
```bash
ffmpeg transcode run video.mp4 audio.mp3 --preset fast-copy -vn -c:a libmp3lame -b:a 320k
```

### Extract single frame as image
```bash
ffmpeg -i input.mp4 -ss 00:00:10 -vframes 1 thumbnail.jpg
```

### Concatenate videos
```bash
# Create file list
echo "file 'a.mp4'" > list.txt
echo "file 'b.mp4'" >> list.txt
ffmpeg -f concat -safe 0 -i list.txt -c copy output.mp4
```

### Add watermark
```bash
ffmpeg transcode run input.mp4 output.mp4 --vf "movie=logo.png[wm];[in][wm]overlay=10:10[out]"
```

### Speed up/slow down video
```bash
ffmpeg transcode run input.mp4 output.mp4 --vf "setpts=0.5*PTS"  # 2x faster
ffmpeg transcode run input.mp4 output.mp4 --vf "setpts=2.0*PTS"  # 2x slower
```

### Extract subtitle track
```bash
ffmpeg -i input.mkv -map 0:s:0 subtitles.srt
```

### Check video quality stats
```bash
ffmpeg -i input.mp4 -vf vstats -f null -
```

## Key FFmpeg Options

### Codec Selection
- `-c:v copy` — Skip video re-encoding (fast remux)
- `-c:v libx264` — H.264 (most compatible)
- `-c:v libx265` — HEVC/H.265 (better compression)
- `-c:v libvpx-vp9` — VP9 (royalty-free)
- `-c:v copy` + `-c:a copy` — Remux without re-encoding

### Quality Control
- `-crf N` — Constant Rate Factor (lower = better, 18-28 for visually lossless)
- `-b:v 2M` — Target bitrate
- `-preset veryslow` — Better compression (slower encode)

### Stream Selection
- `-vn` — No video
- `-an` — No audio
- `-sn` — No subtitles
- `-map 0:v:0 -map 0:a:1` — Select specific streams

### Filtering
- `-vf scale=1280:720` — Resize
- `-vf crop=1920:800:0:140` — Crop
- `-vf "hue=h=0:s=0"` — Grayscale
- `-af "volume=0.5"` — Reduce volume

### Temporal
- `-ss 00:01:30` — Start position
- `-t 60` — Duration
- `-to 00:03:00` — End position
- `-r 30` — Frame rate

## Important Behavioral Notes

1. **Always use `-y` or `--overwrite`** when you intend to replace files
2. **Use `copy` codec** for remuxing (no decode/encode, just stream copy)
3. **MP4 for web** — add `-movflags +faststart` for streaming
4. **H.265 is slower** to encode but produces ~30% smaller files at same quality
5. **batch** processes all matching files — be careful with glob patterns
6. **Preset names** must be alphanumeric + hyphens/underscores

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Generic error |
| 2 | File not found / invalid input |
| 255 | User interrupted (Ctrl+C) |

## Requirements

- `ffmpeg` binary in PATH
- `ffprobe` binary in PATH
- Python 3.8+
- `click` >= 8.0

## For AI Agents

Use `--json` flag when parsing programmatically. The harness validates inputs before running ffmpeg, so errors are caught early with clear messages. Session state is saved after each transcode job for recovery. Presets are stored as JSON at `~/.cli-anything-ffmpeg/presets/`. User presets override builtins. The `--dry-run` flag is safe to use without any real files.
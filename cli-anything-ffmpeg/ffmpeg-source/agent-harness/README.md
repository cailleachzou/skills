# cli-anything-ffmpeg

AI-friendly CLI harness for FFmpeg — stateful wrapper with presets, job queues, batch processing, and JSON output for agent consumption.

## Installation

```bash
# From the agent-harness directory
cd agent-harness
pip install -e .

# Verify installation
cli-anything-ffmpeg --help
```

## Commands

```
ffmpeg transcode run   INPUT OUTPUT   # Single transcode job
ffmpeg transcode batch "*.mp4" DIR    # Batch transcode
ffmpeg probe info      FILE           # Inspect media file
ffmpeg probe streams   FILE           # List streams
ffmpeg preset list                      # List presets
ffmpeg preset show     PRESET          # Show preset details
ffmpeg preset create   NAME            # Create preset
ffmpeg session save    NAME            # Save session
ffmpeg session load    NAME            # Load session
ffmpeg info status                       # Check ffmpeg installation
ffmpeg info codecs                       # List encoders/decoders
```

## Options

- `--json` Output machine-readable JSON
- `--ffmpeg-bin` Path to ffmpeg binary (default: ffmpeg)
- `--ffprobe-bin` Path to ffprobe binary (default: ffprobe)

## Presets

Built-in presets: `web-1080p`, `web-720p`, `archive-high`, `fast-copy`, `youtube`, `default`

## Examples

```bash
# Transcode to web-ready 1080p
ffmpeg transcode run input.mp4 output.mp4 --preset web-1080p

# Dry run to see exact command
ffmpeg transcode run input.mp4 output.mp4 --preset youtube --dry-run

# Probe a file
ffmpeg probe info input.mp4

# Batch convert all MP4s
ffmpeg transcode batch "*.mp4" ./output --preset youtube --overwrite

# Create custom preset
ffmpeg preset create high-quality \
  --codec-video libx265 --preset-video slow --crf 18 \
  --codec-audio flac --bitrate-audio 512k

# Check installation
ffmpeg info status
ffmpeg info codecs
```

## JSON Output

Use `--json` flag for machine-readable output:

```bash
ffmpeg probe info video.mp4 --json | jq '.video'
```

## Session Management

```bash
# Save current settings as a session
ffmpeg session save my-project --preset youtube

# Load and reuse
ffmpeg session load my-project
```

## Requirements

- Python 3.8+
- FFmpeg and ffprobe binaries in PATH
- click >= 8.0

## License

LGPL v2.1 — same as FFmpeg
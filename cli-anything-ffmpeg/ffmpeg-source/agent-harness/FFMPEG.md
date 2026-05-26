# FFmpeg CLI Harness — Software-Specific SOP

## What is FFmpeg

**FFmpeg** is the premier open-source multimedia framework for transcoding, streaming, and processing audio/video. The `ffmpeg` binary reads input files, processes them through optional filters, and writes encoded output.

**Key binaries produced by this repo:**
- `ffmpeg` — the main converter/transcoder
- `ffprobe` — media stream analyzer
- `ffplay` — simple media player
- `ffmpeg-dbg` — debug build

**Already CLI-native:** FFmpeg is a command-line tool. This harness adds a structured Python CLI layer with state management, preset system, job queue, and JSON output for agent consumption.

---

## Data Model

### Core Entities

**InputFile**
- URL, format context, stream list, start time, TS offset
- States: closed → opened

**OutputFile**
- URL, muxer, stream list, recording time, start time
- States: closed → opened → writing → finalized

**InputStream**
- Source file, stream index, codec params, decoder
- Decoding state: raw / filtered / copied

**OutputStream**
- Output file, source input stream, encoder, filters
- Encoding state: initializing → encoding → finished

**FilterGraph**
- Inputs[], Outputs[], graph description string
- State: unbuilt → built → active

### Media Types
- `video` — H.264, H.265/HEVC, VP9, AV1, MPEG-1/2/4
- `audio` — AAC, MP3, FLAC, Opus, PCM
- `subtitle` — ASS/SAA, SRT, CEA-608/708
- `data` — teletext, CEA-608, metadata

---

## Command Groups

### `ffmpeg transcode`
One-shot transcoding. Input → filtergraph → output.

```
ffmpeg -i input.mp4 -c:v libx264 -preset medium -crf 23 output.mp4
```

### `ffmpeg probe`
Stream inspection via ffprobe.

```
ffprobe -v quiet -print_format json -show_streams -show_format input.mp4
```

### `ffmpeg batch`
Process multiple files through a pipeline. Job list stored in session.

### `ffmpeg info`
Show installed build info, available encoders, decoders, filters.

### `ffmpeg preset`
Manage encoding presets (CRF, bitrate, codec params).

### `ffmpeg session`
Save/load conversion sessions (job queue, settings).

---

## State Model

- **Session**: holds job queue, active preset, global settings
- **Project**: named collection of source files + target settings
- **Job**: single transcode operation with status

### Session State File
`~/.cli-anything-ffmpeg/sessions/<name>.json`
```json
{
  "version": 1,
  "jobs": [...],
  "active_preset": "youtube-1080p",
  "global_opts": {"loglevel": "info"}
}
```

---

## Output Formats

### Human (default)
```
[ffmpeg] Converting input.mp4 → output.mp4
  Video: libx264, 1920x1080, 24fps
  Audio: AAC, 48kHz, 192kbps
  Progress: 45% (00:01:23 / 00:03:05)
```

### JSON (`--json`)
```json
{
  "status": "complete",
  "input": "input.mp4",
  "output": "output.mp4",
  "video": {"codec": "libx264", "width": 1920, "height": 1080, "fps": 24},
  "audio": {"codec": "aac", "sample_rate": 48000, "bitrate": 192000},
  "duration": 185.0,
  "size_bytes": 10485760
}
```

### Progress JSON (for long jobs)
```json
{
  "event": "progress",
  "percent": 45,
  "time_current": "00:01:23",
  "time_total": "00:03:05",
  "speed": "1.4x",
  "bitrate": "2.5M"
}
```

---

## Architecture

```
cli_anything.ffmpeg
├── ffmpeg_cli.py        # Click CLI, main entry point
├── core/
│   ├── project.py       # Project/session management
│   ├── job.py           # Job queue, status tracking
│   ├── preset.py        # Encoding preset library
│   ├── probe.py         # ffprobe wrapper + stream parsing
│   └── transcode.py     # ffmpeg subprocess runner
├── utils/
│   ├── output.py        # JSON/text output formatters
│   ├── validation.py    # Option validation
│   └── install.py       # Build detection / installation check
└── tests/
    ├── test_core.py
    └── test_full_e2e.py
```

---

## FFmpeg Option Mapping

### Video Encoding
| CLI | Description |
|-----|-------------|
| `-c:v` | Video codec (libx264, libx265, libvpx-vp9, copy) |
| `-preset` | Encoding speed (ultrafast → veryslow) |
| `-crf` | Constant Rate Factor (quality, 0-51) |
| `-b:v` | Video bitrate |
| `-r` | Frame rate |
| `-s` | Output size (WxH) |
| `-vf` | Video filter chain |

### Audio Encoding
| CLI | Description |
|-----|-------------|
| `-c:a` | Audio codec (aac, libmp3lame, copy, flac) |
| `-b:a` | Audio bitrate |
| `-ar` | Sample rate |
| `-ac` | Channel count |
| `-af` | Audio filter chain |

### Stream Selection
| CLI | Description |
|-----|-------------|
| `-map` | Stream mapping |
| `-sn` | Disable subtitles |
| `-an` | Disable audio |
| `-vn` | Disable video |

### Input/Output
| CLI | Description |
|-----|-------------|
| `-i` | Input file |
| `-t` | Duration limit |
| `-ss` | Start time |
| `-to` | End time |
| `-y` | Overwrite output |
| `-n` | Do not overwrite |

---

## Key FFmpeg Behavioral Notes

1. **Codec preference**: ffmpeg picks "best" codec per format. Use `-c:v copy` to skip re-encoding.
2. **Filtergraphs**: Complex filters use `-vf` for simple chains, `-filter_complex` for multi-input/output.
3. **Timestamp handling**: `-itsoffset`, `-ss`, `-t`, `-timestamp` control temporal aspects.
4. **Stream copying**: `copy` codec skips decode/encode, just remuxes — very fast.
5. **Container formats**: MP4 needs `-movflags +faststart` for web streaming.
6. **Progress**: Use `-progress` to get machine-readable progress output.
7. **Hardware acceleration**: `-hwaccel cuda`, `-hwaccel qsv`, `-hwaccel vaapi`.

---

## ffprobe Integration

`ffprobe` outputs JSON for:
- Stream metadata (codec, bitrate, resolution, duration)
- Format info (container, file size, bitrate)
- Chapter markers
- Packet-level statistics

Use `avprobe` results to auto-populate output settings.

---

## Preset Hierarchy

1. **Built-in presets**: `ultrafast`, `fast`, `medium`, `slow`, `veryslow` (x264)
2. **Custom presets**: User-defined JSON files with codec + filter settings
3. **Per-codec profiles**: H.264 profiles (baseline, main, high), HEVC tiers

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Generic error |
| 2 | File not found |
| 255 | User interrupted |

---

## Auto-Save Pattern

FFmpeg CLI is a **one-shot tool** — each invocation is a complete job. Session state (job history, presets) should be saved after each job completes. The `--dry-run` flag suppresses the actual ffmpeg call while still validating options.
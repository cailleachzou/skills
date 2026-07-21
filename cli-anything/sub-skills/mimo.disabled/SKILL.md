---
name: mimo
description: Xiaomi MiMo 多模态理解 — 图片/音频/视频内容分析。当用户需要分析图片内容、音频内容、视频内容时使用。
type: cli-sub
---

# MiMo Multimodal — 多模态理解

基于 Xiaomi MiMo API 的多模态理解工具，支持图片、音频、视频三种媒体类型。

## 环境变量

- `MIMO_API_KEY` — API Key（必需）
- `MIMO_BASE_URL` — API 地址（默认 `https://token-plan-cn.xiaomimimo.com/v1`）

## 用法

```bash
python mimo_multimodal.py <command> <source> [options]
```

### 子命令

| 命令 | 说明 |
|------|------|
| `image` | 图片理解 |
| `audio` | 音频理解 |
| `video` | 视频理解 |
| `auto`  | 自动检测媒体类型 |

### 公共参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `source` | 文件路径或 URL | 必需 |
| `-p, --prompt` | 提示词 | "请描述这个内容" |
| `-m, --model` | 模型名 | `mimo-v2.5` |
| `--max-tokens` | 最大输出 token | 1024 |
| `--api-key` | API Key | 环境变量 |
| `--base-url` | API 地址 | 环境变量 |
| `--json` | JSON 输出 | 关闭 |

### Video 专用参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--fps` | 抽帧率 (0.1-10) | 2.0 |
| `--resolution` | 分辨率级别 (default/max) | default |

## 支持格式

| 类型 | 格式 | 大小限制 |
|------|------|---------|
| 图片 | JPEG, PNG, GIF, WebP, BMP | URL: 50MB, Base64: 50MB |
| 音频 | MP3, WAV, FLAC, M4A, OGG | URL: 100MB, Base64: 50MB |
| 视频 | MP4, MOV, AVI, WMV | URL: 300MB, Base64: 50MB |

## 支持模型

- `mimo-v2.5`（推荐）
- `mimo-v2-omni`

## 示例

### 图片理解
```bash
python mimo_multimodal.py image photo.jpg -p "描述这张图片"
python mimo_multimodal.py image https://example.com/photo.png -p "识别图中的文字" --json
```

### 音频理解
```bash
python mimo_multimodal.py audio recording.wav -p "转录这段语音"
python mimo_multimodal.py audio https://example.com/audio.mp3 -p "总结音频内容"
```

### 视频理解
```bash
python mimo_multimodal.py video clip.mp4 -p "描述视频内容"
python mimo_multimodal.py video clip.mp4 --fps 5 --resolution max -p "详细分析每一帧"
python mimo_multimodal.py video https://example.com/video.mp4 --json
```

### 自动检测
```bash
python mimo_multimodal.py auto media_file.mp4 -p "分析内容"
```

## Token 估算

- **图片**: 取决于分辨率，参考官方 Token 计算公式
- **音频**: `tokens ≈ 秒数 × 6.25`
- **视频**: 分为 video_tokens（视觉）和 audio_tokens（音频），参考官方公式

## Agent 使用指南

当用户要求分析图片/音频/视频时：
1. 确认文件路径或 URL
2. 确定媒体类型（或用 `auto`）
3. 根据用户需求构造 prompt
4. 调用脚本，返回结果

对于本地文件，脚本会自动转为 Base64 编码上传。

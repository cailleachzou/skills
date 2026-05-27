---
name: aliyun-model-studio-cli
description: >-
  **RESTRICTED — ASR only**. Aliyun Model Studio CLI (`bl`) is used ONLY for
  speech-to-text (ASR / voice transcription): `bl speech recognize`.
  All other AI tasks (text chat, image, video, TTS, etc.) use Claude's built-in models or other skills.
  Do NOT use `bl` for text generation, image, video, or any other task.
---

# Aliyun Model Studio CLI (`bl`) — ASR Only

> **RESTRICTED** — Only use `bl` for ASR (speech recognize). All other tasks use Claude or other skills.

## ASR — the only allowed command

```bash
bl speech recognize --url ./meeting.wav
```

Local paths are supported — pass the path directly, no URL needed:

```bash
bl speech recognize --url ./audio.mp3
```

For any other need:

| Intent | Tool / Skill |
|--------|--------------|
| Text chat / code / translation | Claude built-in model |
| Image generation | mmx-cli skill |
| Video | mmx-cli skill |
| TTS | mmx-cli skill |
| Web search | Claude or mmx-cli |

## Reference

See `reference/speech.md` for `bl speech recognize` options.

## Auth

```bash
bl auth status          # check current auth
export DASHSCOPE_API_KEY=sk-...
```

Get API key: https://bailian.console.aliyun.com/cn-beijing/?tab=app#/api-key
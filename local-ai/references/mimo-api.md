# mimo API 调用参考

> **本文件是兜底路径的调用参考，不是默认路径。**
> 图像理解 / 音频转写 / 文档 OCR **默认走本机**（`vl4`/`vl8`/`asr`/`ocr`，0 token、不出本机）。
> 只有 **视频**、高质量开放式视觉推理、或本地返回空/连续失败时，才按这里的格式调 mimo。
> 判断标准见 `SKILL.md` 的「什么时候回退 mimo」一节 —— 尤其注意**敏感资料一律不出本机**。

**凭据**：`MIMO_API_KEY` 在 `~/.claude/.env`，**不在** Windows 环境变量。
用前先加载：

```bash
set -a; source ~/.claude/.env; set +a
```

**端点**：`https://api.xiaomimimo.com/v1`（OpenAI 兼容），
请求头 `Authorization: Bearer $MIMO_API_KEY`

**通用 curl 模式**：

```bash
curl -s https://api.xiaomimimo.com/v1/chat/completions \
  -H "Authorization: Bearer $MIMO_API_KEY" \
  -H "Content-Type: application/json" \
  -d '<JSON_BODY>'
```

| 任务 | model | content 差异 |
|------|-------|-------------|
| 图像理解 | mimo-v2.5 | `[{"type":"text","text":"..."},{"type":"image_url","image_url":{"url":"data:image/png;base64,<BASE64>"}}]` |
| 音频理解 | mimo-v2.5 | `[{"type":"text","text":"..."},{"type":"input_audio","input_audio":{"data":"<BASE64>","format":"wav"}}]` |
| 视频理解 | mimo-v2.5 | 抽帧后按图像处理 |
| 语音合成 | mimo-v2.5-tts | `messages:[{role:user,content:"语气"},{role:assistant,content:"文本"}]`，加 `audio:{format:"wav",voice:"白桦"}` |
| 小任务 | mimo-v2.5 | `[{"type":"text","text":"..."}]` |

**TTS 音色**：白桦（默认，成熟男声）、冰糖、茉莉、苏打、Chloe、Mia、Milo、Dean

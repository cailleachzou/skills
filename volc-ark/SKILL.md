---
name: volc-ark
description: >
  火山方舟（Volcano Ark）云端大模型 API——豆包/DeepSeek/GLM 等模型，OpenAI 兼容。
  当用户要求用"豆包/Doubao/DeepSeek/GLM/智谱/Kimi"等云端模型处理文本，
  或需要超大上下文（1M tokens）、视觉理解（图片/视频）时使用；
  与 local-ai（本地免费模型）和 mimo（多模态）互补。
  触发词：火山引擎、方舟、ark、豆包、doubao、deepseek、glm、智谱、kimi、1M 上下文。
metadata:
  author: Cailleach Zou
  version: "2.0"
  created: 2026-08-26
  updated: 2026-08-26
allowed-tools: Bash(*)
---

# volc-ark — 火山方舟云端模型

云端 LLM 备用层，**15 个模型实测可用**（2026-08-26 全量扫描）。

## 模型（全部实测可用）

### DeepSeek V4（纯文本，1M 上下文）
| 别名 | 模型 ID | 特点 |
|------|---------|------|
| `ds-pro` | `deepseek-v4-pro-ga-260813` | V4 Pro GA（默认） |
| `ds-flash` | `deepseek-v4-flash-ga-260731` | V4 Flash GA，更快 |
| `ds-pro-0425` | `deepseek-v4-pro-260425` | V4 Pro 旧版 |
| `ds-flash-0425` | `deepseek-v4-flash-260425` | V4 Flash 旧版 |

### GLM
| 别名 | 模型 ID | 特点 |
|------|---------|------|
| `glm5` | `glm-5-2-260617` | GLM 5.2，1M 上下文 |

### 豆包 Seed（VLM，支持图片/视频输入）
| 别名 | 模型 ID | 特点 |
|------|---------|------|
| `seed-pro` | `doubao-seed-2-1-pro-260628` | 2.1 Pro，262K 上下文 |
| `seed-turbo` | `doubao-seed-2-1-turbo-260628` | 2.1 Turbo |
| `seed2-pro` | `doubao-seed-2-0-pro-260215` | 2.0 Pro |
| `seed-lite` | `doubao-seed-2-0-lite-260428` | 2.0 Lite，支持音频输入 |
| `seed-mini` | `doubao-seed-2-0-mini-260428` | 2.0 Mini，支持音频输入 |
| `seed-flash` | `doubao-seed-1-6-flash-250828` | 1.6 Flash |
| `character` | `doubao-seed-character-260628` | 角色扮演专用 |

### Doubao Seed Evolving（主推，1M 上下文 VLM 动态版）
| 别名 | 模型 ID | 特点 |
|------|---------|------|
| `evolving` | `doubao-seed-evolving` | 动态最新版，1M 上下文，262K 输出，图片/视频输入 |

## 调用

```bash
py -3 "C:\Users\caill\.claude\skills\volc-ark\scripts\ark_chat.py" "问题"                      # 默认 ds-pro
py -3 "C:\Users\caill\.claude\skills\volc-ark\scripts\ark_chat.py" seed-pro "问题"             # 指定别名
py -3 "C:\Users\caill\.claude\skills\volc-ark\scripts\ark_chat.py" --models                   # 列出模型
```

密钥：环境变量 `ARK_API_KEY`（UUID 格式，setx 已配 Windows 用户环境变量）。

## 原始 API（OpenAI 兼容，Python urllib 直接调）

- 端点：`https://ark.cn-beijing.volces.com/api/v3/chat/completions`
- 认证：`Authorization: Bearer <ARK_API_KEY>`
- 列出可用模型：`GET https://ark.cn-beijing.volces.com/api/v3/models`
- 标准 OpenAI 请求体（model/messages/max_tokens/temperature），支持 function calling、vision（image/video 输入）、stream
- ⚠️ 方舟**不提供** Anthropic 协议端点（`/v1/messages` 404），只能走 OpenAI 兼容

## PI Coding agent 接入

已注册进 `~/.pi/agent/models-store.json`（provider: `ark`）+ `auth.json`：
重启 PI 后模型选择里可切换到 ark 的 15 个模型。

## 注意事项

- 未开通：`doubao-seed-2-0-code-preview`、`doubao-seed-translation`（ModelNotOpen，需控制台开通）
- ⚠️ `doubao-seed-evolving` 开通后有约 30 秒~1 分钟生效延迟，刚开通时可能报 ModelNotOpen，重试即可
- 已下线（NotFound）：doubao-1-5 系列、seed-1-6-250615/251015、seed-1-8、glm-4-x、qwen3 系列等
- DeepSeek 系列返回 `reasoning_tokens`（思维链），响应稍慢但质量高
- 与其他层分工：复杂文本/超大上下文/视觉 → 本技能；极简任务 → local-ai；mimo 多模态仍是首选（性价比）

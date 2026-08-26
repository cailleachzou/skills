---
name: local-ai
description: >
  处理"最简单任务"时优先用本机本地模型——省 token、可离线、保隐私。
  通用文本问答/翻译/改写用 llama.cpp Vulkan 后端 + GTX 1080 Ti GPU。
  当用户要求"本地处理 / 离线 / 断网 / 不耗 token / 最简单任务 / 小事件 / 省电 / 隐私 / 本机模型"，
  或任务简单到没必要动用主模型或 mimo 时使用本技能。
  mimo 多模态调用模板见全局 CLAUDE.md，不在此重复。
compatibility: |
  硬件: AMD Ryzen 5 3600X + NVIDIA GTX 1080 Ti (11GB VRAM, Vulkan 1.3)
  软件:
  - llama.cpp 预编译 Vulkan 版 (b10630): `C:\Users\caill\tools\llama-cpp\vulkan\llama-server.exe`
  - Python 3.14.2 + llama-cpp-python 0.3.35 (CPU fallback)
  模型 (GGUF 格式, 存储在 ~/.ollama/models/blobs/):
  - lfm2.5: LiquidAI LFM2.5-2.6B (1.6GB, 英文最快 ~120 tok/s)
  - phi4-mini: Microsoft Phi-4 Mini (2.4GB)
  - qwen2.5:7b: Qwen2.5 7B (4.4GB, 中文最强 ~61 tok/s)
  - llama3: Meta Llama 3 8B (4.4GB)
  ⚠️ GTX 1080 Ti (CC 6.1) 不兼容 Ollama 0.32.9 和 llama-cpp-python CUDA 版，只能用 Vulkan 后端
metadata:
  author: Cailleach Zou
  version: "3.0"
  created: 2026-08-11
  updated: 2026-08-26
allowed-tools: Bash(*)
---

# local-ai — 本地模型处理最简单任务

本技能只负责**本地模型层**：最省 token、可离线、隐私不出的"最简单任务"。
复杂推理留主模型、多模态走 mimo（模板见全局 CLAUDE.md），这里不重复 mimo 内容。

## 何时用本技能（三层分工）

| 层 | 载体 | 职责 |
|----|------|------|
| 主模型 | 当前 Claude | 复杂规划、排期、代码、写作——**不外包** |
| 次模型 | mimo-v2.5（API） | 图像/视频/音频理解、TTS（全局 CLAUDE.md 模板） |
| **本地模型（本技能）** | llama.cpp Vulkan | **最简单任务**，省 token / 离线 / 隐私 |

**走本地**：任务极简（一句话问答、翻译、改写、分类、抽关键词）、离线断网、隐私敏感、图省 token。
**不走本地**：需强推理/长上下文/多步 → 主模型；涉及看/听/说 → mimo；复杂文档解析 → `docling` skill。

## 工具总览

| 模型/工具 | 设备 | 职责 | 实测速度 |
|-----------|------|------|----------|
| llama-server Vulkan + qwen2.5:7b | GTX 1080 Ti | **中文任务**（翻译/改写/问答） | ~61 tok/s |
| llama-server Vulkan + lfm2.5 | GTX 1080 Ti | 英文任务（最快） | ~120 tok/s |
| llama-server Vulkan + phi4-mini | GTX 1080 Ti | 英文/代码 | ~80 tok/s |
| llama-cpp-python (CPU fallback) | CPU 12线程 | 备用 | ~9 tok/s |

> ⚠️ **GPU 方案**: GTX 1080 Ti (CC 6.1) 与 Ollama 0.32.9 和 llama-cpp-python CUDA 版不兼容。
> 唯一可用的 GPU 方案是 **llama.cpp Vulkan 后端**（对架构无限制）。

## 调用方法

### 1. 启动 llama-server（推荐方式）

```cmd
:: 启动 Vulkan 后端服务器（qwen2.5:7b 中文模型）
cd /d C:\Users\caill\tools\llama-cpp\vulkan
llama-server.exe -m "C:\Users\caill\.ollama\models\blobs\sha256-2bada8a7450677000f678be90653b85d364de7db25eb5ea54136ada5f3933730" -ngl 99 --host 127.0.0.1 --port 8080 -c 2048
```

验证: `curl http://127.0.0.1:8080/health`

### 2. 通过 API 对话（OpenAI 兼容）

```bash
curl -s http://127.0.0.1:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"local","messages":[{"role":"user","content":"用一句话介绍量子计算"}],"max_tokens":100}'
```

或封装脚本:

```bash
py -3 "C:\Users\caill\.pi\agent\skills\local-ai\scripts\llama_chat.py" "用一句话介绍量子计算"
```

### 3. 模型切换（需重启服务器）

| 模型 | GGUF 路径 | 用途 |
|------|-----------|------|
| qwen2.5:7b | sha256-2bada8a7450677000f678be90653b85d364de7db25eb5ea54136ada5f3933730 | **中文**（推荐） |
| lfm2.5 | sha256-79fdf00351b46cf26f020aead28d01889886be87c55fa0eb907e6f9b00bfee14 | 英文（最快） |
| phi4-mini | sha256-4a770663d4551fb217658be33bbd71426ec9efa91233b0e6ab5d48fdcfb593ed | 英文/代码 |
| llama3 | sha256-6a0746a1ec1aef3e7ec53868f220ff6e389f6f8ef87a01d77c96807de94ca2aa | 通用 |

### 4. CPU 备用方案（llama-cpp-python）

```bash
# 当 llama-server 不可用时
py -3 "C:\Users\caill\.pi\agent\skills\local-ai\scripts\llama_chat.py" --cpu "你的问题"
```

## 可用模型详情

| 模型 | 大小 | 中文 | 英文 | GPU 速度 | CPU 速度 |
|------|------|------|------|----------|----------|
| qwen2.5:7b | 4.4GB | ★★★★★ | ★★★★ | ~61 tok/s | ~3.6 tok/s |
| lfm2.5 | 1.6GB | ★★★ | ★★★★ | ~120 tok/s | ~9 tok/s |
| phi4-mini | 2.4GB | ★★ | ★★★★★ | ~80 tok/s | ~5 tok/s |
| llama3 | 4.4GB | ★★★ | ★★★★ | ~60 tok/s | ~4 tok/s |

## 注意事项

- **GPU 方案**: GTX 1080 Ti 用 Vulkan 后端（llama-server.exe），支持所有架构
- **中文任务**: 推荐 qwen2.5:7b（LFM2.5 中文输出有问题）
- **VRAM**: GTX 1080 Ti 11GB，7B 模型约占 5.7GB，可同时跑其他应用
- **首次加载**: qwen2.5:7b 加载约 10 秒，后续请求快速
- **端口**: 默认 8080，可用 `--port` 参数修改
- **温度设置**: 创意任务用 0.7-1.0，精确任务用 0.1-0.3
- **上下文长度**: 默认 2048 tokens，可用 `-c` 参数调整

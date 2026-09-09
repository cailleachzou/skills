---
name: local-ai
description: >
  处理"最简单任务"时优先用本机本地模型——省 token、可离线、保隐私。
  通用文本问答/改写/摘要用 llama.cpp CUDA 后端 + RTX 5060 Laptop GPU（翻译统一走 docs-translate，视觉/OCR 走 mimo/docling，本技能不负责）。
  当用户要求"本地处理 / 离线 / 断网 / 不耗 token / 最简单任务 / 小事件 / 省电 / 隐私 / 本机模型"，
  或任务简单到没必要动用主模型或 mimo 时使用本技能。
  mimo 多模态调用模板见全局 CLAUDE.md，不在此重复。
compatibility: |
  硬件: AMD Ryzen 9 8945HX (16C/32T) + NVIDIA RTX 5060 Laptop 8GB VRAM (GB206 / Blackwell / sm_120 / CC 12.0) + 32GB DDR5
  软件:
  - llama.cpp CUDA 预编译版 (b10864, CUDA 13.3 runtime): `C:\Users\caill\tools\llama-cpp\cuda\llama-server.exe`
  - ⚠️ llama.cpp win-cuda zip 不含 cuBLAS/cudart dll，须把同版本 `cudart-llama-bin-win-cuda-*.x64.zip` 一并解压进同目录，否则 `--list-devices` 显示 (none)
  - Python 3.14 + llama-cpp-python（可选，CPU fallback；纯 CPU 也可用 `llama-server -ngl 0`）
  GGUF 模型 (Q4_K_M, 位于 D:\models\gguf\):
  - qwen2.5:7b: Qwen2.5 7B Q4_K_M（分片 2 片，中文主力，整卡进 GPU）
  - qwen2.5:14b: Qwen2.5 14B Q4_K_M（分片 3 片，复杂推理/长文备选，需 -ngl 部分 offload）
  ⚠️ 8GB VRAM：7B Q4 可整卡；14B Q4 权重 ~8.5GB 超显存，必须 -ngl 留若干层在 CPU
metadata:
  author: Cailleach Zou
  version: "4.0"
  created: 2026-08-11
  updated: 2026-09-08
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
| **本地模型（本技能）** | llama.cpp CUDA | **最简单任务**，省 token / 离线 / 隐私 |

**走本地**：任务极简（一句话问答、改写、分类、抽关键词）、离线断网、隐私敏感、图省 token。
**不走本地**：需强推理/长上下文/多步 → 主模型；涉及看/听/说 → mimo；复杂文档解析/OCR → `docling` skill；翻译（含一句话/文档翻译）→ `docs-translate` skill。

## 工具总览

| 模型/工具                          | 设备                          | 职责                    | 实测速度          |
| ------------------------------- | --------------------------- | --------------------- | ------------- |
| llama-server CUDA + qwen2.5:7b  | RTX 5060 Laptop（整卡 ngl99）   | **中文任务**（改写/问答/摘要）    | ~39 tok/s（decode） |
| llama-server CUDA + qwen2.5:14b | RTX 5060 Laptop（offload ngl36） | 复杂推理/长文中文         | ~14 tok/s（decode） |
| llama-cpp-python / -ngl 0       | CPU 16线程（Ryzen 8945HX）      | 备用（server 不在时）       | ~11 tok/s（decode） |

> ✅ **GPU 方案**: RTX 5060 Laptop = Blackwell sm_120（CC 12.0），原生 CUDA。llama.cpp CUDA 版直跑，
> 已无旧机（GTX 1080 Ti / CC 6.1）"只能 Vulkan、不兼容 CUDA"的限制。
> ⚠️ 笔记本 **TGP 功耗墙**：整卡 decode ~39 tok/s 低于旧桌面 1080 Ti 的 ~61；但 prefill 极快（pp ~1700 tok/s）。

## 调用方法

### 1. 启动 llama-server（推荐方式）

```cmd
:: 启动 CUDA 后端服务器（qwen2.5:7b 中文主力，整卡）
cd /d C:\Users\caill\tools\llama-cpp\cuda
llama-server.exe -m D:\models\gguf\qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf -ngl 99 --host 127.0.0.1 --port 8080 -c 2048
```

验证: `curl http://127.0.0.1:8080/health`（应返回 `{"status":"ok"}`）

> 分片 GGUF 只需在 `-m` 给 `-00001-of-*` 第一片，会自动加载同目录同系列其余分片。

### 2. 通过 API 对话（OpenAI 兼容）

```bash
curl -s http://127.0.0.1:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"local","messages":[{"role":"user","content":"用一句话介绍量子计算"}],"max_tokens":100}'
```

或封装脚本（真实调用会打印 `[GPU Xs | Y tok/s]` 到 stderr）：

```bash
py -3 "C:\Users\caill\.claude\skills\local-ai\scripts\llama_chat.py" "用一句话介绍量子计算"
```

### 3. 模型切换（需重启服务器）

| 模型 | GGUF 路径（第一个分片） | 用途 | -ngl |
|------|-----------|------|------|
| qwen2.5:7b | `D:\models\gguf\qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf` | **中文**（推荐） | 99 |
| qwen2.5:14b | `D:\models\gguf\qwen2.5-14b-instruct-q4_k_m-00001-of-00003.gguf` | 复杂推理/长文 | 36（见下表） |

### 4. CPU 备用方案

```bash
# 方案 A：llama-cpp-python（需 pip install llama-cpp-python；PyPI 暂无 cp314 wheel 时可源码构建或弃用）
py -3 "C:\Users\caill\.claude\skills\local-ai\scripts\llama_chat.py" --cpu "你的问题"
# 方案 B：同款 llama-server 纯 CPU（无需额外安装，推荐）
llama-server.exe -m <7B GGUF> -ngl 0 --host 127.0.0.1 --port 8080 -c 2048
```

## 实测性能（2026-09-08，llama-bench / b10864 / CUDA 13.3）

| 模型 | 配置 | decode (tg128) | prefill (pp128) | VRAM |
| ---- | ---- | ---- | ---- | ---- |
| qwen2.5:7b Q4 | 整卡 -ngl 99 | **38.6 tok/s** | 1687 tok/s | ~6.0 GB |
| qwen2.5:7b Q4 | 纯 CPU -ngl 0 | 11.2 tok/s | — | 0 |
| qwen2.5:14b Q4 | -ngl 36 | **14.2 tok/s** | — | ~6.3 GB |
| qwen2.5:14b Q4 | -ngl 30 | 11.5 tok/s | — | ~5.5 GB |
| qwen2.5:14b Q4 | -ngl 20 | 8.9 tok/s | — | ~4.0 GB |
| qwen2.5:14b Q4 | 纯 CPU -ngl 0 | 5.9 tok/s | — | 0 |

> 14B Q4 权重 8.5GB > 8GB VRAM，无法整卡；推荐 **-ngl 36**（decode 上限 ~14 tok/s）。
> 想更快跑 14B：可换 Q3_K_M（~6.5GB，可整卡，速度接近 7B 整卡档）——留作后续可选。

## 注意事项

- **GPU 方案**: RTX 5060 Laptop（sm_120 / CC 12.0）走 llama.cpp CUDA 后端；解码受笔记本功耗墙限制偏低，prefill 极快
- **中文任务**: 推荐 qwen2.5:7b（整卡 ~39 tok/s）；qwen2.5:14b 需 -ngl offload（~14 tok/s），仅复杂推理才值得
- **sm_120 版本要求**: 需 CUDA ≥ 12.8 runtime 编译的 llama.cpp（本机 b10864 / CUDA 13.3 runtime）；避开 CUDA 13.0–13.2（Blackwell 上出乱码）；驱动 592.01 实测正常
- **冷启动**: llama-server 从磁盘加载 7B 约 2~3s（mmap 到 D 盘）；强杀关闭即可，无后台驻留
- **KV/上下文**: 默认 -c 2048；7B 整卡时可开大些（VRAM 余 ~1GB）；14B offload 时别贪大上下文
- **端口**: 默认 8080，可用 `--port` 修改
- **温度**: 创意任务 0.7-1.0，精确任务 0.1-0.3
- **模型文件大小**: qwen2.5:7b Q4 = 4.46GB（2 片）；qwen2.5:14b Q4 = 8.56GB（3 片）

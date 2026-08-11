---
name: local-ai
description: >
  处理"最简单任务"时优先用本机本地模型——省 token、可离线、保隐私。通用文本问答/翻译/改写用
  Ollama `qwen3:4b`（iGPU），看图/图像理解用 `qwen2.5vl:3b`（iGPU），**OCR 文字提取走 NPU**
  （docling + rapidocr，比 CPU 快约 5 倍），超轻量小事件用 `DeepSeek-R1-1.5B`（NPU，省电），
  文档 RAG 检索用 `bge-m3` 嵌入（1024 维），语音转文字用 whisper-small（CPU）。
  当用户要求"本地处理 / 离线 / 断网 / 不耗 token / 最简单任务 / 小事件 / 省电 / 隐私 / 本机模型 /
  OCR / 提取图片文字 / 扫描件"，或任务简单到没必要动用主模型或 mimo 时使用本技能。
  工具根目录 `C:\Users\59620\tools\`；mimo 多模态调用模板见全局 CLAUDE.md，不在此重复。
compatibility: |
  全部为已部署的本地工具（Intel Core Ultra 5 125H / Meteor Lake / 16GB / iGPU+NPU）：
  - Ollama（IPEX-LLM 版，走 iGPU/SYCL0）：`C:\Users\59620\tools\ollama-xpu\ollama.exe`
    模型：`qwen3:4b`（文本）、`qwen2.5vl:3b`（视觉）、`bge-m3`（嵌入）
  - llama.cpp NPU 版：`C:\Users\59620\tools\llama-npu\llama-cli-npu.exe`
    模型：`DeepSeek-R1-Distill-Qwen-1.5B-Q4_K_M.gguf`
  - whisper.cpp：`C:\Users\59620\tools\whisper\Release\whisper-cli.exe` + `ggml-small.bin`
  - OCR（NPU，独立于 Ollama）：`C:\Users\59620\.venv-docling\Scripts\python.exe` +
    `C:\Users\59620\Desktop\docling_npu.py`（docling + rapidocr，OpenVINO NPU 引擎）
  - Ollama 服务需先启动（`start-ollama-xpu.bat`，监听 127.0.0.1:11434）；OCR 不需要 Ollama
  ⚠️ 本机仅 16GB 内存，勿同时常驻多个模型（qwen3 约 2.5G + 视觉 3.2G 同载约 5.7G）
metadata:
  author: Cailleach Zou
  version: "1.0"
  created: 2026-08-11
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
| **本地模型（本技能）** | 下表 | **最简单任务**，省 token / 离线 / 隐私 |

**走本地**：任务极简（一句话问答、翻译、改写、分类、抽关键词）、离线断网、隐私敏感、图省 token。
**不走本地**：需强推理/长上下文/多步 → 主模型；涉及看/听/说 → mimo；复杂文档解析 → `docling` skill。

## 工具总览

| 模型/工具 | 设备 | 职责 | 实测 |
|-----------|------|------|------|
| Ollama `qwen3:4b` | iGPU (SYCL0) | 通用文本、翻译、改写 | 中文回复正常 |
| Ollama `qwen2.5vl:3b` | iGPU (SYCL0) | **图像理解** / 看图描述 | 1~10s 描述图内文字 |
| docling + rapidocr | **NPU** | **OCR 文字提取**（图片/扫描PDF） | 6.6s 中文；比 CPU 快约 5 倍 |
| `DeepSeek-R1-1.5B` | NPU | 超轻量文本、小事件（省电） | 30 tok/s，**输出不可见** |
| Ollama `bge-m3` | CPU | RAG 嵌入 | 1024 维 |
| whisper-small | CPU | 语音转文字 | 6s / 中文基本正确 |

## 调用方法

### 0. 启动 Ollama 服务（一次性）

```cmd
:: 双击 C:\Users\59620\tools\start-ollama-xpu.bat，保持窗口开着；或：
cd /d C:\Users\59620\tools\ollama-xpu
call start-ollama.bat
```

验证：`curl http://127.0.0.1:11434/api/tags`

### 1. 通用文本（qwen3:4b · iGPU）

```bash
"C:\Users\59620\tools\ollama-xpu\ollama.exe" run qwen3:4b "把这段翻译成英文：你好世界"
```

- qwen3 默认带思考过程；要快速答复加 `--hidethinking`
- `ollama.exe` 在 PATH 默认没有，用完整路径

### 2a. 图像理解 / 看图（qwen2.5vl:3b · iGPU）

⚠️ 需 Ollama 服务在跑（第 0 节）；本版 `ollama run` **不支持 `--images`**，视觉必须走 API。已封装脚本：

```bash
py -3 "C:\Users\59620\.claude\skills\local-ai\scripts\vision.py" "图片.png" "描述这张图片的内容"
```

### 2b. OCR 文字提取（docling + rapidocr · NPU）

从图片 / 扫描 PDF 里**提取文字**，走 NPU，不依赖 Ollama：

```bash
py -3 "C:\Users\59620\.claude\skills\local-ai\scripts\ocr.py" "扫描件.png"                 # 文字打印到终端
py -3 "C:\Users\59620\.claude\skills\local-ai\scripts\ocr.py" "扫描件.pdf" -o out.md       # 结果写入 md
py -3 "C:\Users\59620\.claude\skills\local-ai\scripts\ocr.py" "图.png" --cpu              # OpenVINO CPU 对比
```

- 引擎：OpenVINO + rapidocr PP-OCR，NPU 加速，比 CPU 快约 5 倍
- 小模型对长数字末尾偶有丢失（`12345`→`1234`）；复杂版式可用 `--cpu` 对比精度

### 3. 文档 RAG 嵌入（bge-m3 · CPU）

```bash
curl http://127.0.0.1:11434/api/embed -H "Content-Type: application/json" \
  -d "{\"model\":\"bge-m3\",\"input\":\"要检索的文本\"}"
```

返回 1024 维向量（`embeddings[0]`）。

### 4. 超轻量文本 / 小事件（DeepSeek-R1-1.5B · NPU）

双击 `C:\Users\59620\tools\run-npu.bat`，或：

```cmd
cd /d C:\Users\59620\tools\llama-npu
set IPEX_LLM_NPU_MTL=1
llama-cli-npu.exe -m DeepSeek-R1-Distill-Qwen-1.5B-Q4_K_M.gguf -c 512 -n 32 --prompt "你的问题"
```

⚠️ **NPU 版生成文本不打印到终端**（stdout 只有日志，`-o` 输出文件也无效，仅可见性能统计）。
交互式问答看不到回复时，改用 qwen3:4b。

限制：输入 ≤960 token、总序列 ≤1024；NPU 官方仅支持 Llama-3.2-3B /
DeepSeek-R1-Distill-Qwen-1.5B / 7B 三个模型。Meteor Lake 必须设 `IPEX_LLM_NPU_MTL=1`。

### 5. 语音转文字（whisper-small · CPU）

```cmd
cd /d C:\Users\59620\tools\whisper
Release\whisper-cli.exe -m ggml-small.bin -f 音频.wav -l zh -otxt
```

输出文本写入 `<音频名>.txt`。

## 注意事项

- **16GB 内存**：勿同时常驻多模型；模型加载占用的是系统内存（iGPU 共享内存）
- **OCR 不需要 Ollama**（docling+rapidocr 走 NPU）；**图像理解需要 Ollama 服务**
- **NPU 的两条实际用途**：OCR 加速（docling_npu.py，约 5 倍）与超轻量文本（llama-cli-npu，但生成文本不可见）
- **Ollama 原生不支持 NPU**：本机 Ollama 走 iGPU/SYCL0
- 视觉模型 small 精度有限（如 `12345`→`1234`），复杂图可试 `--cpu` 对比或换 gemma3:4b
- 查看已装模型：`ollama list`；删除：`ollama rm <模型名>`

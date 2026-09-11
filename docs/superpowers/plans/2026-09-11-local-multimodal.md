# 本机多模态能力扩展 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 `local-ai` 技能新增视觉（Qwen3-VL-4B/8B）、语音识别（Qwen3-ASR-1.7B）、文档 OCR（baidu/Unlimited-OCR）三条全本地路径，让敏感资料不出本机。

**Architecture:** llama.cpp 主干 + Python OCR 特例。4 个模型共用现成的 `llama-server` 体系（复用 `start.sh` 显存调度与 `llama_batch.py` 回执机制），OCR 因架构不被 llama.cpp 支持而隔离在独立 venv 中。

**Tech Stack:** llama.cpp b10883 (CUDA 13.3) / Python 3.14（脚本层）/ Python 3.12 + torch 2.10.0 + transformers 4.57.1（OCR venv）/ `hf` CLI 1.30.0

**Spec:** `docs/superpowers/specs/2026-09-11-local-multimodal-design.md`

## Global Constraints

- **GPU**: RTX 5060 Laptop, 8151 MiB 总显存，桌面常驻约 1243 MiB → 可用约 6908 MB
- **一次只跑一个模型** —— 这是硬约束，切换必须走 `start.sh` / `stop.sh`
- **llama.cpp 必须用 b10883**（`C:/Users/caill/tools/llama-cpp/cuda-b10883`）；CUDA 13 构建，混入 CUDA 12 版会静默退回 CPU
- **思考开关只能走请求级** `chat_template_kwargs`；server 启动参数实测全部失效（上游 PR #22336 未合并）
- **`start.bat` 内不得出现带未转义 `)` 的 `if(...)` 块** —— 会静默提前终止（历史上踩过，见 git log）
- **脚本编码**: 所有 Python 脚本开头统一 `sys.stdout/stderr.reconfigure(encoding="utf-8")`，避免中文在 GBK 终端乱码
- **离线**: OCR 路径设置 `HF_HUB_OFFLINE=1`，确保不联网
- **签名**: git 提交用 `Co-Authored-By: Claude Code <noreply@anthropic.com>`
- **提交前缀**: `skills: `

---

### Task 1: 下载三个模型并落盘

**Files:**
- Create: `D:/models/gguf/qwen3-vl-4b/`（2 个文件）
- Create: `D:/models/gguf/qwen3-vl-8b/`（2 个文件）
- Create: `D:/models/gguf/qwen3-asr-1.7b/`（2 个文件）
- Create: `D:/models/unlimited-ocr/`（整个仓库）

**Interfaces:**
- Produces: 后续所有任务依赖的模型路径常量：
  - `D:/models/gguf/qwen3-vl-4b/Qwen3VL-4B-Instruct-Q4_K_M.gguf`
  - `D:/models/gguf/qwen3-vl-4b/mmproj-Qwen3VL-4B-Instruct-F16.gguf`
  - `D:/models/gguf/qwen3-vl-8b/Qwen3VL-8B-Instruct-Q4_K_M.gguf`
  - `D:/models/gguf/qwen3-vl-8b/mmproj-Qwen3VL-8B-Instruct-Q8_0.gguf`
  - `D:/models/gguf/qwen3-asr-1.7b/Qwen3-ASR-1.7B-Q8_0.gguf`
  - `D:/models/gguf/qwen3-asr-1.7b/mmproj-Qwen3-ASR-1.7b-BF16.gguf`
  - `D:/models/unlimited-ocr/`

- [ ] **Step 1: 下载 VL-4B**

```bash
hf download Qwen/Qwen3-VL-4B-Instruct-GGUF \
  Qwen3VL-4B-Instruct-Q4_K_M.gguf mmproj-Qwen3VL-4B-Instruct-F16.gguf \
  --local-dir D:/models/gguf/qwen3-vl-4b
```

- [ ] **Step 2: 下载 VL-8B**

```bash
hf download Qwen/Qwen3-VL-8B-Instruct-GGUF \
  Qwen3VL-8B-Instruct-Q4_K_M.gguf mmproj-Qwen3VL-8B-Instruct-Q8_0.gguf \
  --local-dir D:/models/gguf/qwen3-vl-8b
```

- [ ] **Step 3: 下载 ASR**

```bash
hf download JamePeng2023/Qwen3-ASR-1.7B-GGUF \
  Qwen3-ASR-1.7B-Q8_0.gguf mmproj-Qwen3-ASR-1.7b-BF16.gguf \
  --local-dir D:/models/gguf/qwen3-asr-1.7b
```

- [ ] **Step 4: 下载 Unlimited-OCR 全仓库**

```bash
hf download baidu/Unlimited-OCR --local-dir D:/models/unlimited-ocr
```

- [ ] **Step 5: 校验文件大小与清单**

Run:
```bash
ls -l D:/models/gguf/qwen3-vl-4b/ D:/models/gguf/qwen3-vl-8b/ D:/models/gguf/qwen3-asr-1.7b/
du -sh D:/models/unlimited-ocr/
```

Expected（字节数可有小幅出入，量级必须对上）:
```
qwen3-vl-4b:      Qwen3VL-4B-Instruct-Q4_K_M.gguf        2497 MB
                  mmproj-Qwen3VL-4B-Instruct-F16.gguf     836 MB
qwen3-vl-8b:      Qwen3VL-8B-Instruct-Q4_K_M.gguf        5028 MB
                  mmproj-Qwen3VL-8B-Instruct-Q8_0.gguf    752 MB
qwen3-asr-1.7b:   Qwen3-ASR-1.7B-Q8_0.gguf               2165 MB
                  mmproj-Qwen3-ASR-1.7b-BF16.gguf         642 MB
unlimited-ocr:    约 6.8 GB
```

若某个 mmproj 缺少，说明该量化档位不存在 —— 回到 HF 仓库页面确认实际文件名后重下。

- [ ] **Step 6: 提交（仅记录，不提交大文件）**

模型是二进制大文件，**不要 `git add`**。本任务无代码改动，跳过提交，直接进入 Task 2。

---

### Task 2: `llama_media.py` —— 多模态编解码共享模块

**Files:**
- Create: `C:\Users\caill\.claude\skills\local-ai\scripts\llama_media.py`
- Test: 内联断言（无测试框架，用 `py -3 -` 直接跑）

**Interfaces:**
- Consumes: 无
- Produces:
  - `encode_file(path: str) -> str` —— 读文件并返回 base64 字符串；文件不存在抛 `OSError`
  - `build_content(prompt: str, images=None, audio=None) -> str | list`
    - 无媒体 → 返回 `prompt` 原字符串（与旧版行为完全一致）
    - 有媒体 → 返回 OpenAI 格式 content 数组，首元素是 `{"type":"text","text":prompt}`
    - `images` 接受 `str` 或 `list[str]`；`audio` 接受 `str`
  - 常量 `IMAGE_MIME: dict[str, str]`

`llama_chat.py`（Task 4）与 `llama_batch.py`（Task 5）都 import 本模块。**不要在两处重复实现** —— 30 行代码 + MIME 表复制会漂移。

- [ ] **Step 1: 写失败测试**

创建临时测试文件 `D:/tmp/test_media.py`：

```python
import base64, os, sys
sys.path.insert(0, r"C:\Users\caill\.claude\skills\local-ai\scripts")
import llama_media

# 准备一个真文件
p = r"D:/tmp/_media_probe.png"
with open(p, "wb") as f:
    f.write(b"\x89PNG\r\n\x1a\n" + b"payload")

# 1) 无媒体 → 纯字符串，且与旧行为逐字一致
assert llama_media.build_content("你好") == "你好", "无媒体必须返回原字符串"

# 2) 单图 → 数组，首元素为 text
c = llama_media.build_content("看图", images=p)
assert isinstance(c, list) and len(c) == 2
assert c[0] == {"type": "text", "text": "看图"}
assert c[1]["type"] == "image_url"
assert c[1]["image_url"]["url"].startswith("data:image/png;base64,")
assert base64.b64decode(c[1]["image_url"]["url"].split(",", 1)[1]) == open(p, "rb").read()

# 3) images 传 str 与传 list 等价
assert llama_media.build_content("看图", images=[p]) == c

# 4) 音频
a = r"D:/tmp/_media_probe.wav"
with open(a, "wb") as f:
    f.write(b"RIFF0000WAVE")
ca = llama_media.build_content("转写", audio=a)
assert ca[0] == {"type": "text", "text": "转写"}
assert ca[1]["type"] == "input_audio"
assert ca[1]["input_audio"]["format"] == "wav"

# 5) 不支持的图片格式要明确报错，而不是静默发出去
try:
    llama_media.build_content("x", images=r"D:/tmp/_media_probe.bmp2")
    raise AssertionError("应当抛 ValueError")
except ValueError as e:
    assert "不支持的图片格式" in str(e)

# 6) 文件不存在要抛 OSError
try:
    llama_media.build_content("x", images=r"D:/tmp/does_not_exist.png")
    raise AssertionError("应当抛 OSError")
except OSError:
    pass

print("ALL OK")
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `mkdir -p D:/tmp && py -3 D:/tmp/test_media.py`
Expected: `ModuleNotFoundError: No module named 'llama_media'`

- [ ] **Step 3: 写实现**

创建 `C:\Users\caill\.claude\skills\local-ai\scripts\llama_media.py`：

```python
#!/usr/bin/env python3
"""多模态输入的共享编解码 —— llama_chat.py 与 llama_batch.py 共用。

llama-server 的 /v1/chat/completions 接受 OpenAI 格式的多模态 content：

    图像  {"type": "image_url",  "image_url":   {"url": "data:<mime>;base64,<B64>"}}
    音频  {"type": "input_audio", "input_audio": {"data": "<B64>", "format": "wav"}}

⚠️ 音频输入在 llama.cpp 里被标为 highly experimental。大文件出问题时，退路是
   启动 server 时加 --no-mmproj-offload（音频编码器退回 CPU）。

没有媒体时 build_content 返回**纯字符串**，保持与旧调用方的行为一致 —— 这样
给 llama_chat.py / llama_batch.py 加多模态支持不会改变任何现有纯文本用法。
"""
import base64
import os

# 覆盖 llama-server 实际能解的图片格式；其余一律显式报错，不静默发出去
IMAGE_MIME = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".bmp": "image/bmp",
}


def encode_file(path: str) -> str:
    """读文件并 base64 编码。读不了直接抛，由调用方决定怎么记（单条失败还是整批退出）。"""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


def _image_part(path: str) -> dict:
    ext = os.path.splitext(path)[1].lower()
    mime = IMAGE_MIME.get(ext)
    if not mime:
        raise ValueError(
            f"不支持的图片格式：{path}（支持 {', '.join(sorted(IMAGE_MIME))}）")
    return {"type": "image_url",
            "image_url": {"url": f"data:{mime};base64,{encode_file(path)}"}}


def _audio_part(path: str) -> dict:
    fmt = os.path.splitext(path)[1].lower().lstrip(".")
    if not fmt:
        raise ValueError(f"音频文件缺少扩展名，无法判断格式：{path}")
    return {"type": "input_audio",
            "input_audio": {"data": encode_file(path), "format": fmt}}


def build_content(prompt: str, images=None, audio=None):
    """构造 user message 的 content。

    无媒体 → 纯字符串（与旧版逐字一致）；有媒体 → OpenAI 多模态 content 数组。
    images 接受 str 或 list[str] —— 批量场景 JSONL 里写单个字符串更省事。
    """
    imgs = [images] if isinstance(images, str) else list(images or [])
    if not imgs and not audio:
        return prompt
    parts = [{"type": "text", "text": prompt}]
    parts += [_image_part(p) for p in imgs]
    if audio:
        parts.append(_audio_part(audio))
    return parts
```

- [ ] **Step 4: 运行测试，确认通过**

Run: `py -3 D:/tmp/test_media.py`
Expected: `ALL OK`

- [ ] **Step 5: 清理临时文件并提交**

```bash
rm -f D:/tmp/test_media.py D:/tmp/_media_probe.png D:/tmp/_media_probe.wav
cd C:/Users/caill/.claude/skills
git add local-ai/scripts/llama_media.py
git commit -m "$(cat <<'EOF'
skills: local-ai 新增 llama_media.py 多模态编解码共享模块

llama-server 的 /v1/chat/completions 接受 OpenAI 多模态 content（图像走
image_url + data URI，音频走 input_audio）。两个调用脚本都需要这段编解码，
抽成共享模块以免复制漂移。

- build_content 在无媒体时返回纯字符串，保证现有纯文本用法逐字不变
- 不支持的图片格式显式抛 ValueError，不静默发出去让 server 报一个看不懂的错

Co-Authored-By: Claude Code <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: `start.sh` / `start.bat` 支持 vl4 / vl8 / asr

**Files:**
- Modify: `C:\Users\caill\.claude\skills\local-ai\scripts\start.sh`
- Modify: `C:\Users\caill\.claude\skills\local-ai\scripts\start.bat`

**Interfaces:**
- Consumes: Task 1 的模型路径
- Produces: `bash start.sh vl4|vl8|asr [port]` 可启动对应 server；`running_model()` 能正确识别全部 5 个模型

- [ ] **Step 1: 在 `start.sh` 加模型路径常量**

在现有 `MODEL_9B=` 那一行之后插入：

```bash
MODEL_VL4="D:/models/gguf/qwen3-vl-4b/Qwen3VL-4B-Instruct-Q4_K_M.gguf"
MMPROJ_VL4="D:/models/gguf/qwen3-vl-4b/mmproj-Qwen3VL-4B-Instruct-F16.gguf"
MODEL_VL8="D:/models/gguf/qwen3-vl-8b/Qwen3VL-8B-Instruct-Q4_K_M.gguf"
MMPROJ_VL8="D:/models/gguf/qwen3-vl-8b/mmproj-Qwen3VL-8B-Instruct-Q8_0.gguf"
MODEL_ASR="D:/models/gguf/qwen3-asr-1.7b/Qwen3-ASR-1.7B-Q8_0.gguf"
MMPROJ_ASR="D:/models/gguf/qwen3-asr-1.7b/mmproj-Qwen3-ASR-1.7b-BF16.gguf"
```

- [ ] **Step 2: 扩展 `running_model()` 的匹配分支**

把现有 case 替换为：

```bash
  case "$body" in
    *MiniCPM*)         echo minicpm ;;
    *9B-Q4_K_M*)       echo 9b ;;
    *Qwen3VL-4B*)      echo vl4 ;;
    *Qwen3VL-8B*)      echo vl8 ;;
    *Qwen3-ASR-1.7B*)  echo asr ;;
    *)                 echo unknown ;;
  esac
```

> ⚠️ **这是本次改动最容易埋雷的地方。** 不加这几个分支，切换时会把「已经是目标模型」误判成 `unknown`，于是每次都白白重启一遍、丢掉前缀缓存 —— 而且**不报错**，只是变慢。

- [ ] **Step 3: 扩展参数校验与 usage**

把 `case "$MODEL_TYPE" in minicpm|9b) ;; *) usage; exit 1 ;; esac` 改成：

```bash
case "$MODEL_TYPE" in
  minicpm|9b|vl4|vl8|asr) ;;
  *) usage; exit 1 ;;
esac
```

并在 `usage()` 里补三行：

```bash
  echo "  vl4     - Qwen3-VL-4B Q4_K_M + mmproj F16, 16K ctx (视觉/图片理解，默认视觉模型)"
  echo "  vl8     - Qwen3-VL-8B Q4_K_M + mmproj Q8_0, 8K ctx (视觉备用；显存余量仅 ~500MB)"
  echo "  asr     - Qwen3-ASR-1.7B Q8_0 + mmproj BF16, 32K ctx (语音转写)"
```

- [ ] **Step 4: 加三个启动分支**

在现有 `9b)` 分支之后、`esac` 之前插入：

```bash
  vl4)
    echo "启动 Qwen3-VL-4B (GPU 整卡, 16K ctx, 视觉)"
    exec "$LLAMA_DIR/llama-server.exe" \
      -m "$MODEL_VL4" \
      --mmproj "$MMPROJ_VL4" \
      -ngl 99 \
      --host 127.0.0.1 \
      --port "$PORT" \
      -c 16384 \
      --jinja \
      --cache-type-k q8_0 \
      --cache-type-v q8_0 \
      --temp 0.7 \
      --top-p 0.8
    ;;
  vl8)
    echo "启动 Qwen3-VL-8B (GPU 整卡, 8K ctx, 视觉备用)"
    exec "$LLAMA_DIR/llama-server.exe" \
      -m "$MODEL_VL8" \
      --mmproj "$MMPROJ_VL8" \
      -ngl 99 \
      --host 127.0.0.1 \
      --port "$PORT" \
      -c 8192 \
      --jinja \
      --cache-type-k q8_0 \
      --cache-type-v q8_0 \
      --temp 0.7 \
      --top-p 0.8
    ;;
  asr)
    echo "启动 Qwen3-ASR-1.7B (GPU 整卡, 32K ctx, 语音转写)"
    exec "$LLAMA_DIR/llama-server.exe" \
      -m "$MODEL_ASR" \
      --mmproj "$MMPROJ_ASR" \
      -ngl 99 \
      --host 127.0.0.1 \
      --port "$PORT" \
      -c 32768 \
      --jinja \
      --cache-type-k q8_0 \
      --cache-type-v q8_0 \
      --temp 0.0
    ;;
```

> `vl4/vl8` 的 `--temp 0.7 --top-p 0.8` 是 Qwen3-VL **Instruct** 的官方推荐值（非 thinking 档）。`asr` 用 `--temp 0.0` —— 转写要确定性输出。

- [ ] **Step 5: 验证 `start.sh` 语法**

Run: `bash -n "C:/Users/caill/.claude/skills/local-ai/scripts/start.sh"`
Expected: 无输出（语法通过）

- [ ] **Step 6: 同步 `start.bat`**

在 `set MODEL_9B=...` 之后加：

```bat
set MODEL_VL4=D:\models\gguf\qwen3-vl-4b\Qwen3VL-4B-Instruct-Q4_K_M.gguf
set MMPROJ_VL4=D:\models\gguf\qwen3-vl-4b\mmproj-Qwen3VL-4B-Instruct-F16.gguf
set MODEL_VL8=D:\models\gguf\qwen3-vl-8b\Qwen3VL-8B-Instruct-Q4_K_M.gguf
set MMPROJ_VL8=D:\models\gguf\qwen3-vl-8b\mmproj-Qwen3VL-8B-Instruct-Q8_0.gguf
set MODEL_ASR=D:\models\gguf\qwen3-asr-1.7b\Qwen3-ASR-1.7B-Q8_0.gguf
set MMPROJ_ASR=D:\models\gguf\qwen3-asr-1.7b\mmproj-Qwen3-ASR-1.7b-BF16.gguf
set MMPROJ_ARG=
```

把分发段改成：

```bat
if "%MODEL_TYPE%"=="9b" goto :start_9b
if "%MODEL_TYPE%"=="minicpm" goto :start_minicpm
if "%MODEL_TYPE%"=="vl4" goto :start_vl4
if "%MODEL_TYPE%"=="vl8" goto :start_vl8
if "%MODEL_TYPE%"=="asr" goto :start_asr
goto :usage
```

在 `:start_minicpm` 块之后加三个新块：

```bat
:start_vl4
set TARGET=%MODEL_VL4%
set MMPROJ_ARG=--mmproj "%MMPROJ_VL4%"
set BANNER=[START] Qwen3-VL-4B GPU full offload, 16K ctx (vision)
set EXTRA=--temp 0.7 --top-p 0.8
set CTX=16384
goto :maybe_switch

:start_vl8
set TARGET=%MODEL_VL8%
set MMPROJ_ARG=--mmproj "%MMPROJ_VL8%"
set BANNER=[START] Qwen3-VL-8B GPU full offload, 8K ctx (vision, fallback)
set EXTRA=--temp 0.7 --top-p 0.8
set CTX=8192
goto :maybe_switch

:start_asr
set TARGET=%MODEL_ASR%
set MMPROJ_ARG=--mmproj "%MMPROJ_ASR%"
set BANNER=[START] Qwen3-ASR-1.7B GPU full offload, 32K ctx (speech)
set EXTRA=--temp 0.0
set CTX=32768
goto :maybe_switch
```

在 `:maybe_switch` 的探测段补匹配（紧跟现有两行 `findstr` 之后）：

```bat
echo !BODY! | findstr /C:"Qwen3VL-4B" >nul && set RUNNING=vl4
echo !BODY! | findstr /C:"Qwen3VL-8B" >nul && set RUNNING=vl8
echo !BODY! | findstr /C:"Qwen3-ASR-1.7B" >nul && set RUNNING=asr
```

把 `:launch` 那行改成带上 `%MMPROJ_ARG%`：

```bat
"%LLAMA_DIR%\llama-server.exe" -m "%TARGET%" %MMPROJ_ARG% -ngl 99 --host 127.0.0.1 --port %PORT% -c %CTX% --jinja --cache-type-k q8_0 --cache-type-v q8_0 %EXTRA%
```

> ⚠️ 改 `start.bat` 时**不得引入带未转义 `)` 的 `if(...)` 块** —— 会静默提前终止，历史上踩过一次。新增内容全部用 `goto` 标签形式，与本计划给出的写法保持一致。
>
> `minicpm` / `9b` 两个分支也要能正常走 `%MMPROJ_ARG%`（此时它为空字符串），这是刻意的：保持 `:launch` 只有一行，避免复制出问题。

- [ ] **Step 7: 验证 start.sh 能真正启动并幂等**

> ⚠️ **`start.sh` 是前台阻塞进程**（内部 `exec llama-server`），会一直占着终端。
> 在 Bash 工具里必须**后台启动**，否则会把当前调用卡死：
> 加 `run_in_background` 参数，或 `nohup bash .../start.sh vl4 > /tmp/llama.log 2>&1 &`。

```bash
cd C:/Users/caill/.claude/skills/local-ai/scripts
nohup bash start.sh vl4 > /tmp/llama_vl4.log 2>&1 &
```

等待约 15 秒让模型加载完，再检查：

```bash
sleep 15
curl -s http://127.0.0.1:8080/health
curl -s http://127.0.0.1:8080/v1/models
nvidia-smi --query-gpu=memory.used --format=csv,noheader
```

Expected:
- `/health` 返回 `{"status":"ok"}`
- `/v1/models` 的 id 里含 `Qwen3VL-4B`
- 显存占用约 4.5 GB（不是 1.3 GB —— 那样说明掉到 CPU 了）

- [ ] **Step 8: 验证幂等（关键）**

不要停 server，再跑一次：

```bash
bash start.sh vl4
```

Expected: 打印 `[复用] 8080 上已经在跑 vl4，不重启`
**如果打印的是 `[切换]` 或重新加载，说明 Step 2 的匹配没生效 —— 回去修。**

- [ ] **Step 9: 依次验证 vl8 与 asr 可启动**

```bash
nohup bash start.sh vl8 > /tmp/llama_vl8.log 2>&1 &   # 同样后台启动
sleep 15; grep -i "failed to fit params" /tmp/llama_vl8.log || echo "vl8 OK"
bash stop.sh

nohup bash start.sh asr > /tmp/llama_asr.log 2>&1 &
sleep 15; curl -s http://127.0.0.1:8080/health
bash stop.sh
```

Expected: 两个都能起来；vl8 若出现 `failed to fit params` 说明余量不足，把 `-c 8192` 降到 `-c 4096` 后重试。

- [ ] **Step 10: 提交**

```bash
cd C:/Users/caill/.claude/skills
git add local-ai/scripts/start.sh local-ai/scripts/start.bat
git commit -m "$(cat <<'EOF'
skills: local-ai start 脚本支持 vl4 / vl8 / asr 三个多模态模型

- start.sh / start.bat 各加三个分支：vl4 (16K ctx) / vl8 (8K ctx) / asr (32K ctx)，
  全部带 --mmproj，沿用现有 --cache-type-k/v q8_0
- 扩展 running_model() 的匹配分支 —— 不加会把「已是目标模型」误判成 unknown，
  每次切换白白重启并丢掉前缀缓存，且不报错只变慢
- vl4/vl8 用 Qwen3-VL Instruct 官方推荐采样 (temp 0.7 / top-p 0.8)；asr 用 temp 0
- start.bat 新增内容全部走 goto 标签，不引入带未转义 ")" 的 if(...) 块

Co-Authored-By: Claude Code <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: `llama_chat.py` 支持 `--image` / `--audio`

**Files:**
- Modify: `C:\Users\caill\.claude\skills\local-ai\scripts\llama_chat.py`

**Interfaces:**
- Consumes: `llama_media.build_content(prompt, images, audio)`（Task 2）
- Produces: `chat_with_server(prompt, system, max_tokens, temperature, enable_think, images=None, audio=None) -> str`
- CLI: `--image PATH`（可重复）、`--audio PATH`

- [ ] **Step 1: 加 import 与模块 docstring 补充**

在 `import argparse` 前加 `import os`，并在 imports 之后加：

```python
import llama_media
```

在模块 docstring 的用法段补两行：

```
    py -3 llama_chat.py --image photo.jpg "图里有什么"       # 视觉（需先 start.sh vl4）
    py -3 llama_chat.py --audio meeting.wav "转写并分段落"    # 语音（需先 start.sh asr）
```

- [ ] **Step 2: 扩展 `chat_with_server` 签名与消息构造**

把函数签名改为：

```python
def chat_with_server(prompt: str, system: str = None, max_tokens: int = 512,
                     temperature: float = 0.7, enable_think: bool = True,
                     images=None, audio=None) -> str:
```

把 messages 构造段：

```python
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
```

改为：

```python
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    # 无媒体时 build_content 返回纯字符串，行为与加多模态之前完全一致
    messages.append({"role": "user",
                     "content": llama_media.build_content(prompt, images, audio)})
```

- [ ] **Step 3: 加 CLI 参数并透传**

在 `parser.add_argument("--no-think", ...)` 之后加：

```python
    parser.add_argument("--image", action="append", metavar="PATH",
                        help="图片路径，可重复指定多张（需 server 跑着 vl4/vl8）")
    parser.add_argument("--audio", metavar="PATH",
                        help="音频路径（需 server 跑着 asr）")
```

把最后的调用改为：

```python
    try:
        print(chat_with_server(args.prompt, args.system, args.max_tokens,
                               args.temperature, not args.no_think,
                               images=args.image, audio=args.audio))
    except (OSError, ValueError) as e:
        sys.exit(f"[错误] 读取媒体文件失败：{e}")
```

- [ ] **Step 4: 回归 —— 确认纯文本用法未破坏**

```bash
nohup bash "C:/Users/caill/.claude/skills/local-ai/scripts/start.sh" minicpm > /tmp/llama_2b.log 2>&1 &
sleep 10
py -3 "C:/Users/caill/.claude/skills/local-ai/scripts/llama_chat.py" --no-think "用一句话介绍量子计算"
```

Expected: 正常返回一句中文，无异常。这一步证明加多模态没有破坏旧路径。

- [ ] **Step 5: 视觉路径实测**

准备一张真实测试图（用系统里现成的 PNG/JPG 即可，或：

```bash
py -3 -c "
from PIL import Image, ImageDraw
img = Image.new('RGB', (900, 220), 'white')
d = ImageDraw.Draw(img)
d.text((30, 100), 'HELLO OCR 2026', fill='black')
img.save('D:/tmp/vision_probe.png')
"
```

）：

```bash
nohup bash "C:/Users/caill/.claude/skills/local-ai/scripts/start.sh" vl4 > /tmp/llama_vl4.log 2>&1 &
sleep 15
py -3 "C:/Users/caill/.claude/skills/local-ai/scripts/llama_chat.py" \
  --image D:/tmp/vision_probe.png -n 200 "图里的文字是什么？只回答文字本身"
```

Expected: 输出包含 `HELLO OCR 2026`（大小写与空格可能有出入，但字母和数字必须对）。
若报 `[错误] 连不上 llama-server` → server 没起来；若返回空 → 试 `--no-think`。

- [ ] **Step 6: 提交**

```bash
cd C:/Users/caill/.claude/skills
git add local-ai/scripts/llama_chat.py
git commit -m "$(cat <<'EOF'
skills: local-ai llama_chat.py 支持 --image / --audio

- 新增 --image（可重复）与 --audio，走 llama_media.build_content 构造
  OpenAI 多模态 content 发往 llama-server
- 无媒体时 content 仍是纯字符串，纯文本用法逐字不变
- 媒体读取失败给出明确报错，不把 traceback 抛给用户

Co-Authored-By: Claude Code <noreply@anthropic.com>
EOF
)"
```

---

### Task 5: `llama_batch.py` 支持 image / audio 字段

**Files:**
- Modify: `C:\Users\caill\.claude\skills\local-ai\scripts\llama_batch.py`

**Interfaces:**
- Consumes: `llama_media.build_content`（Task 2）
- Produces: JSONL 任务支持可选 `image`（字符串或数组）与 `audio`（字符串）字段；失败走现有 `error` 通道，错误文本以 `媒体读取失败:` 开头

- [ ] **Step 1: 加 import 与 docstring 补充**

在 imports 之后加：

```python
import llama_media
```

在 docstring 的输入格式段，把 jsonl 说明改为：

```
    jsonl : {"id": "任意标识", "prompt": "必填", "system": "可选", "max_tokens": 100,
             "temperature": 0.3, "image": "页面.png", "audio": "录音.wav"}
            只有 prompt 必填，其余字段按需覆盖全局默认值。
            image 可写单个路径或路径数组（多图）；音频走 audio 字段。
```

- [ ] **Step 2: 修改 `_call` —— 媒体构造失败直接记 error**

把 `_call` 开头的：

```python
    prompt = task["prompt"]
    payload = json.dumps({
```

改为：

```python
    prompt = task["prompt"]

    # 媒体读取失败重试没有意义（文件不会自己出现），所以放在重试循环之外，
    # 直接产出一条带 error 的记录 —— 与「调用失败」走同一条通道，不打断整批。
    try:
        content = llama_media.build_content(prompt, task.get("image"), task.get("audio"))
    except (OSError, ValueError) as e:
        return {"index": index, "id": task.get("id", str(index)), "prompt": prompt,
                "result": None, "completion_tokens": 0, "elapsed": None,
                "error": f"媒体读取失败: {e}"}

    payload = json.dumps({
```

并把 payload 里的 messages 构造段：

```python
        "messages": ([{"role": "system", "content": task.get("system") or opts.system}]
                     if (task.get("system") or opts.system) else []) +
                    [{"role": "user", "content": prompt}],
```

改为：

```python
        "messages": ([{"role": "system", "content": task.get("system") or opts.system}]
                     if (task.get("system") or opts.system) else []) +
                    [{"role": "user", "content": content}],
```

- [ ] **Step 3: 在回执里把「媒体读取失败」单列一类**

在 `_anomalies` 函数里，把开头的：

```python
    if rec.get("error"):
        return ["失败"]
```

改为：

```python
    if rec.get("error"):
        # 媒体读取失败和「模型答得不好」是两回事：前者改文件路径即可，后者要改 prompt
        if str(rec["error"]).startswith("媒体读取失败"):
            return ["媒体读取失败"]
        return ["失败"]
```

**同时在 `_write_report` 里改掉失败统计的依据。** 现有实现是：

```python
    failed = [i for i, tags in tagged if "失败" in tags]
```

这是**列表成员检查**，不是子串检查 —— `"失败" in ["媒体读取失败"]` 为 `False`。
不改的话，「媒体读取失败」的记录不计入失败数，回执会打印
「成功 N ｜ 失败 0 ｜ 异常 M」这种自相矛盾的数字，且下面 `all_conn` 的判断也会连带失准。

改为按 `error` 字段判定，不再依赖标签文案：

```python
    failed = [r["index"] for r in ordered if r.get("error")]
```

- [ ] **Step 4: 在回执建议里补一条针对性提示**

在 `_write_report` 的 `advice` 构造段，把：

```python
    if {t for _, tags in bad for t in tags} & {"原样回显", "JSON 解析失败", "带代码块围栏"}:
        advice.append("格式类异常多半是 prompt 没给 one-shot 示例 —— 见 SKILL.md「写 prompt 的实测经验」。")
```

改为：

```python
    if {t for _, tags in bad for t in tags} & {"原样回显", "JSON 解析失败", "带代码块围栏"}:
        advice.append("格式类异常多半是 prompt 没给 one-shot 示例 —— 见 SKILL.md「写 prompt 的实测经验」。")
    if {t for _, tags in bad for t in tags} & {"媒体读取失败"}:
        advice.append("媒体读取失败：检查 JSONL 里 image/audio 的路径是否正确、"
                      "图片格式是否受支持（见 llama_media.IMAGE_MIME）。")
```

- [ ] **Step 5: 验证纯文本批量未破坏（回归）**

```bash
printf '把这句话改得正式些：这方案不太行\n把这句话改得正式些：明天再说\n' > D:/tmp/plain.txt
nohup bash "C:/Users/caill/.claude/skills/local-ai/scripts/start.sh" minicpm > /tmp/llama_2b.log 2>&1 &
sleep 10
py -3 "C:/Users/caill/.claude/skills/local-ai/scripts/llama_batch.py" \
  D:/tmp/plain.txt -o D:/tmp/plain.out.jsonl -j 2 --no-think
cat D:/tmp/plain.report.md
```

Expected: 2 条成功，回执里异常清单为「无」，`server 实际模型` 含 `MiniCPM`。

- [ ] **Step 6: 验证批量图片路径**

```bash
py -3 -c "
from PIL import Image, ImageDraw
import os
os.makedirs('D:/tmp/scans', exist_ok=True)
for i, t in enumerate(['ALPHA 101', 'BETA 202', 'GAMMA 303'], 1):
    img = Image.new('RGB', (900, 220), 'white')
    ImageDraw.Draw(img).text((30, 100), t, fill='black')
    img.save(f'D:/tmp/scans/page_{i:03d}.png')
"
py -3 - <<'PY'
import json
rows = [{"id": f"p{i}", "prompt": "图里的文字是什么？只输出文字本身",
         "image": f"D:/tmp/scans/page_{i:03d}.png"} for i in (1, 2, 3)]
with open("D:/tmp/scans.jsonl", "w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
PY
nohup bash "C:/Users/caill/.claude/skills/local-ai/scripts/start.sh" vl4 > /tmp/llama_vl4.log 2>&1 &
sleep 15
py -3 "C:/Users/caill/.claude/skills/local-ai/scripts/llama_batch.py" \
  D:/tmp/scans.jsonl -o D:/tmp/scans.out.jsonl -j 1 --no-think
cat D:/tmp/scans.report.md
```

Expected: 3 条成功，回执 `server 实际模型` 含 `Qwen3VL-4B`，抽样里能看到 ALPHA/BETA/GAMMA。
（`-j 1` 是刻意的：视觉模型单次图像编码开销大，先确认正确性再谈并发。）

- [ ] **Step 7: 验证媒体读取失败被正确归类**

```bash
printf '{"id":"bad","prompt":"看图","image":"D:/tmp/不存在.png"}\n' > D:/tmp/bad.jsonl
py -3 "C:/Users/caill/.claude/skills/local-ai/scripts/llama_batch.py" \
  D:/tmp/bad.jsonl -o D:/tmp/bad.out.jsonl -j 1
cat D:/tmp/bad.report.md
```

Expected: 回执计数为 **「总 1 ｜ 成功 0 ｜ 失败 1 ｜ 异常 1」**（若显示「失败 0 异常 1」说明
失败统计没改对），异常清单标签为 **`媒体读取失败`**，且建议里出现「检查 JSONL 里 image/audio 的路径」。
**若标签是「失败」而非「媒体读取失败」，说明 Step 3 没生效。**

- [ ] **Step 8: 提交**

```bash
cd C:/Users/caill/.claude/skills
git add local-ai/scripts/llama_batch.py
git commit -m "$(cat <<'EOF'
skills: local-ai llama_batch.py 支持 image / audio 字段

- JSONL 任务新增可选 image（字符串或数组）与 audio 字段
- 媒体读取失败在重试循环之外直接产出 error 记录 —— 路径错了重试没有意义；
  与调用失败共用 error 通道，不打断整批
- 回执里单列「媒体读取失败」标签并给出针对性建议，与「模型答得不好」区分开
- 纯文本批量路径逐字未变

Co-Authored-By: Claude Code <noreply@anthropic.com>
EOF
)"
```

---

### Task 6: Unlimited-OCR 独立栈

**Files:**
- Create: `C:\Users\caill\.claude\skills\local-ai\ocr\requirements.txt`
- Create: `C:\Users\caill\.claude\skills\local-ai\ocr\ocr.py`
- Create: `C:\Users\caill\.claude\skills\local-ai\ocr\run.sh`
- Create: `D:/models/venvs/unlimited-ocr/`（venv，不入 git）

**Interfaces:**
- Consumes: Task 1 的 `D:/models/unlimited-ocr/`；现有 `scripts/stop.sh`
- Produces: `bash ocr/run.sh --pdf FILE --out DIR` 与 `bash ocr/run.sh --image FILE --out DIR`，输出 markdown 与同格式回执

- [ ] **Step 1: 建 venv**

```bash
uv venv --python 3.12 --seed D:/models/venvs/unlimited-ocr
```

⚠️ **`--seed` 不能省。** `uv venv` 默认**不安装 pip**，而下面 Step 3 用的是
`<venv>/Scripts/python.exe -m pip install` —— 没有 pip 就会以
`No module named pip` 失败。实测踩到过（见 ledger Ruling 8）。

Expected: `D:/models/venvs/unlimited-ocr/Scripts/python.exe` 存在，**且**
`<venv>/Scripts/python.exe -m pip --version` 能打印出版本号。
第二步是真正的门槛 —— 只检查 python.exe 存在会放过这个坑。

- [ ] **Step 2: 写 requirements.txt**

创建 `C:\Users\caill\.claude\skills\local-ai\ocr\requirements.txt`：

```
# ⚠️ 不能照抄官方 README 的「Python 3.12.3 + CUDA 12.9」组合：
#    cu129 索引的 torch 最高只到 2.9.0，而本文件要求 2.10.0 —— 于是 pip
#    **静默回落到 PyPI** 拿到 `2.10.0+cpu` 构建。不报错，只是 CUDA 不可用、
#    慢十倍。实测踩到过（见 ledger Ruling 9）。
#    本机是 CUDA 13（驱动 592.01，llama.cpp 侧亦为 CUDA 13.3），故走 cu130。
# 本地版本号（+cu130）显式钉死：索引里没有就直接报错，不给静默回落留机会。
torch==2.10.0+cu130
torchvision==0.25.0+cu130
transformers==4.57.1
Pillow==12.1.1
matplotlib==3.10.8
einops==0.8.2
addict==2.4.0
easydict==1.13
pymupdf==1.27.2.2
psutil==7.2.2
```

- [ ] **Step 3: 安装依赖**

```bash
D:/models/venvs/unlimited-ocr/Scripts/python.exe -m pip install --upgrade pip
D:/models/venvs/unlimited-ocr/Scripts/python.exe -m pip install \
  -r "C:/Users/caill/.claude/skills/local-ai/ocr/requirements.txt" \
  --index-url https://download.pytorch.org/whl/cu130 \
  --extra-index-url https://pypi.org/simple
```

> ⚠️ **索引必须是 cu130，不是 cu129。** cu129 的 torch 最高只到 2.9.0；
> 写 `--index-url .../cu129` 加 `torch==2.10.0` 不会报「找不到」——pip 会**静默**
> 去 `--extra-index-url` 拿 PyPI 的 `+cpu` 构建，装完看着成功，直到 Step 4 才发现
> CUDA 不可用。requirements.txt 里已把版本钉成 `+cu130`，索引缺失时会**直接报错**。
>
> 若真的报错，先查该索引有什么：
> `D:/models/venvs/unlimited-ocr/Scripts/python.exe -m pip index versions torch --index-url https://download.pytorch.org/whl/cu130`
> **不要退回默认索引** —— 那必然装成 CPU 版。

- [ ] **Step 4: 验证 torch 拿到的是 CUDA 版（关键）**

```bash
D:/models/venvs/unlimited-ocr/Scripts/python.exe -c \
  "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'NO CUDA')"
```

Expected: `2.10.0+cu129 True NVIDIA GeForce RTX 5060 Laptop GPU`

**若输出 `False`** —— pip 装到了 CPU 版。这会让 OCR 慢到不可用且**不报错**。重新安装并确认 `--index-url` 指向 `download.pytorch.org/whl/cu129`。

- [ ] **Step 5: 写 ocr.py**

创建 `C:\Users\caill\.claude\skills\local-ai\ocr\ocr.py`：

```python
#!/usr/bin/env python3
"""Unlimited-OCR 本地推理 —— 扫描件 / 复杂版面 / 公式表格 / 长文档。

为什么单独一个栈（不走 llama-server）:
    Unlimited-OCR 是 DeepseekV2-style MoE + 自定义建模代码（trust_remote_code），
    llama.cpp 不认这个架构，只能走 transformers。

显存: 权重是 bf16 单文件约 6.7GB，本机可用约 6.9GB —— **贴边**。
      所以 run.sh 会先 stop.sh 腾显存。跑完不常驻，不占着卡。

用法:
    bash run.sh --pdf 合同.pdf --out ./out/
    bash run.sh --image 扫描件.png --out ./out/
    bash run.sh --pdf 长文档.pdf --out ./out/ --dpi 200
"""
import argparse
import json
import os
import sys
import tempfile
import time

MODEL_DIR = os.environ.get("UNLIMITED_OCR_DIR", "D:/models/unlimited-ocr")


def _report(out_dir: str, src: str, pages: int, results: list, elapsed: float) -> str:
    """同 llama_batch.py 的回执格式 —— 主模型只读这一份就够。"""
    path = os.path.join(out_dir, "ocr.report.md")
    ok = [r for r in results if r.get("error") is None]
    bad = [r for r in results if r.get("error") is not None]
    lines = [
        "# OCR 回执",
        "",
        f"- 生成：{time.strftime('%Y-%m-%d %H:%M')}",
        f"- 输入：{src}（{pages} 页）",
        f"- 输出目录：{out_dir}",
        f"- 模型：baidu/Unlimited-OCR (bf16, 本地 {MODEL_DIR})",
        f"- 耗时：{elapsed:.1f}s",
        "",
        "## 计数",
        "",
        f"总 **{len(results)}** ｜ 成功 {len(ok)} ｜ 失败 **{len(bad)}**",
        "",
        "## 异常清单",
        "",
    ]
    if not bad:
        lines.append("无。")
    else:
        lines += ["| 页 | 错误 |", "| --- | --- |"]
        for r in bad:
            lines.append(f"| {r['page']} | {r['error']} |")
    lines += ["", "## 输出文件", ""]
    for r in ok:
        lines.append(f"- 第 {r['page']} 页 → `{os.path.basename(r['output'])}`")
    lines.append("")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path


def pdf_to_images(pdf_path: str, dpi: int) -> list:
    import fitz  # PyMuPDF
    doc = fitz.open(pdf_path)
    tmp_dir = tempfile.mkdtemp(prefix="ocr_pdf_")
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    paths = []
    for i, page in enumerate(doc):
        out = os.path.join(tmp_dir, f"page_{i + 1:04d}.png")
        page.get_pixmap(matrix=mat).save(out)
        paths.append(out)
    doc.close()
    return paths


def main() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

    ap = argparse.ArgumentParser(description="Unlimited-OCR 本地推理（transformers / CUDA）")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--pdf", help="PDF 路径（逐页转图后解析）")
    src.add_argument("--image", help="单张图片路径")
    ap.add_argument("--out", required=True, help="输出目录（markdown 与回执写在这里）")
    ap.add_argument("--dpi", type=int, default=300, help="PDF 转图 DPI（默认 300）")
    ap.add_argument("--max-length", type=int, default=32768, help="单次生成上限")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)

    # 延迟导入：让 --help 不必加载 torch（几秒起步）
    import torch
    from transformers import AutoModel, AutoTokenizer

    if not torch.cuda.is_available():
        sys.exit("[错误] CUDA 不可用 —— OCR 会在 CPU 上慢到不可用。"
                 "检查 torch 是否为 cu129 版："
                 "D:/models/venvs/unlimited-ocr/Scripts/python.exe -c "
                 "\"import torch; print(torch.__version__, torch.cuda.is_available())\"")

    print(f"[加载] {MODEL_DIR} …", file=sys.stderr)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR, trust_remote_code=True)
    model = AutoModel.from_pretrained(
        MODEL_DIR,
        trust_remote_code=True,
        use_safetensors=True,
        torch_dtype=torch.bfloat16,
    )
    model = model.eval().cuda()
    print("[加载] 完成", file=sys.stderr)

    t0 = time.time()
    results = []

    if args.image:
        out_path = os.path.join(args.out, os.path.splitext(os.path.basename(args.image))[0])
        try:
            model.infer(
                tokenizer,
                prompt="<image>document parsing.",
                image_file=args.image,
                output_path=out_path,
                base_size=1024, image_size=640, crop_mode=True,
                max_length=args.max_length,
                no_repeat_ngram_size=35, ngram_window=128,
                save_results=True,
            )
            results.append({"page": 1, "output": out_path, "error": None})
        except Exception as e:
            results.append({"page": 1, "output": None, "error": f"{type(e).__name__}: {e}"})
        total_pages = 1
    else:
        pages = pdf_to_images(args.pdf, args.dpi)
        total_pages = len(pages)
        print(f"[PDF] {total_pages} 页已转图", file=sys.stderr)
        # 逐页单独推理：整本 infer_multi 会一次性占满显存，8GB 上风险太高
        for idx, page_png in enumerate(pages, 1):
            out_path = os.path.join(args.out, f"page_{idx:04d}")
            print(f"  [{idx}/{total_pages}] {os.path.basename(page_png)}", file=sys.stderr)
            try:
                model.infer(
                    tokenizer,
                    prompt="<image>document parsing.",
                    image_file=page_png,
                    output_path=out_path,
                    base_size=1024, image_size=1024, crop_mode=False,
                    max_length=args.max_length,
                    no_repeat_ngram_size=35, ngram_window=1024,
                    save_results=True,
                )
                results.append({"page": idx, "output": out_path, "error": None})
            except Exception as e:
                # 单页失败不中断整本 —— 与 llama_batch.py 的容错策略一致
                results.append({"page": idx, "output": None,
                                "error": f"{type(e).__name__}: {e}"})

    report = _report(args.out, args.pdf or args.image, total_pages, results, time.time() - t0)
    print(f"[完成] 回执 → {report}", file=sys.stderr)


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: 写 run.sh**

创建 `C:\Users\caill\.claude\skills\local-ai\ocr\run.sh`：

```bash
#!/bin/bash
# Unlimited-OCR 启动器 —— 独立栈，所以在跑之前必须先把 llama-server 腾掉。
#
# 为什么第一步是 stop.sh：OCR 权重 6.7GB，本机可用显存约 6.9GB，**贴边**。
# 显存没回收干净就会把部分层挤到 CPU —— 不报错，只是慢十倍。
# stop.sh 会轮询显存直到真的掉下来，正是为这种场景准备的。
#
# 用法: ./run.sh --pdf 文件.pdf --out ./out/
#       ./run.sh --image 图片.png --out ./out/
set -e -u

HERE="$(cd "$(dirname "$0")" && pwd)"
VENV="${UNLIMITED_OCR_VENV:-D:/models/venvs/unlimited-ocr}"
PY="$VENV/Scripts/python.exe"

[ -x "$PY" ] || { echo "[错误] 找不到 venv Python：$PY" >&2; exit 1; }

# 离线运行 —— 隐私场景下不允许任何联网调用
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1

bash "$HERE/../scripts/stop.sh" || true

echo "[OCR] 显存已腾出，开始推理…" >&2
exec "$PY" "$HERE/ocr.py" "$@"
```

- [ ] **Step 7: 验证语法**

```bash
bash -n "C:/Users/caill/.claude/skills/local-ai/ocr/run.sh"
D:/models/venvs/unlimited-ocr/Scripts/python.exe -m py_compile "C:/Users/caill/.claude/skills/local-ai/ocr/ocr.py"
```

Expected: 均无输出

- [ ] **Step 8: 造一张真实测试图并实跑**

```bash
D:/models/venvs/unlimited-ocr/Scripts/python.exe -c "
from PIL import Image, ImageDraw
img = Image.new('RGB', (1240, 350), 'white')
ImageDraw.Draw(img).text((40, 150), 'INVOICE NO 2026-0911   TOTAL 1234.56', fill='black')
img.save('D:/tmp/ocr_probe.png')
"
bash "C:/Users/caill/.claude/skills/local-ai/ocr/run.sh" \
  --image D:/tmp/ocr_probe.png --out D:/tmp/ocr_out/
```

Expected:
- 显存被腾出（stop.sh 打印显存回落）
- 推理完成，`D:/tmp/ocr_out/` 下有 markdown 产物
- `D:/tmp/ocr_out/ocr.report.md` 里计数为「成功 1」

打开产物确认文字内容含 `2026-0911` 或 `1234.56`（OCR 对纯文本图片的识别）。

- [ ] **Step 9: 验证显存贴边但不溢出**

在上一步运行过程中另开一个终端：

```bash
nvidia-smi --query-gpu=memory.used --format=csv,noheader
```

Expected: 约 6.9 GB（贴近上限）。**若启动日志或推理速度异常慢**，说明有层掉到 CPU —— 先确认没有其他程序占显存，再考虑 `--image-size` 调小。

- [ ] **Step 10: 提交**

```bash
cd C:/Users/caill/.claude/skills
git add local-ai/ocr/requirements.txt local-ai/ocr/ocr.py local-ai/ocr/run.sh
git commit -m "$(cat <<'EOF'
skills: local-ai 新增 Unlimited-OCR 独立栈（本地文档解析）

Unlimited-OCR 是 DeepseekV2-style MoE + trust_remote_code 自定义建模代码，
llama.cpp 不认这个架构，只能走 transformers —— 因此单独一个 venv
(D:/models/venvs/unlimited-ocr)，与系统 Python 3.14 和 .venv-docling 隔离。

- ocr/run.sh: 先 stop.sh 腾显存再推理。权重 6.7GB / 可用 6.9GB 贴边，
  显存没回收干净会把层挤到 CPU，不报错只慢十倍
- 强制 HF_HUB_OFFLINE / TRANSFORMERS_OFFLINE：隐私场景不允许联网
- PDF 逐页单独推理而非整本 infer_multi：8GB 上一次吃满显存风险太高；
  单页失败不中断整本，与 llama_batch.py 的容错策略一致
- 启动即校验 CUDA 可用 —— 装到 CPU 版 torch 会静默慢到不可用
- 输出同 llama_batch.py 格式的回执，主模型只读这一份

Co-Authored-By: Claude Code <noreply@anthropic.com>
EOF
)"
```

---

### Task 7: 文档同步与边界改写

**Files:**
- Modify: `C:\Users\caill\.claude\CLAUDE.md`
- Modify: `C:\Users\caill\.claude\skills\local-ai\SKILL.md`
- Modify: `C:\Users\caill\.claude\skills\README.md`

**Interfaces:**
- Consumes: 前三项任务的成果（模型别名、脚本用法、OCR 入口）
- Produces: 三处边界描述一致，无残留「多模态一律走 mimo」

- [ ] **Step 1: 改全局 `CLAUDE.md` 的模型分工段**

把：

```
- **主模型（Claude）**：文本推理、代码、写作
- **mimo-v2.5**（计量计费）：多模态（图像/视频/音频）、简单文本小任务
- **判定**：涉及"看、听、说" → mimo；简单查询/快速命令也外包 mimo 节省 token
- Claude 无多模态能力，遇图片/视频/音频**必须**走 mimo API
```

改为：

```
- **主模型（Claude）**：文本推理、代码、写作
- **本地多模态**（`local-ai` 技能，0 token、不出本机）：图像理解（vl4/vl8）、
  音频转写（asr）、文档 OCR（ocr）—— **默认走这里**
- **mimo-v2.5**（计量计费）：视频理解、高质量开放式视觉推理、简单文本小任务
- **判定**：文档/录音/敏感资料 → 本地；视频、复杂图表分析、多图对比推理 → mimo；
  本地返回空或明显失败 → 回退 mimo
- 敏感资料（合同、证件、简历等）**一律本地，不出本机**
```

- [ ] **Step 2: 在 `local-ai/SKILL.md` 加多模态章节**

在文件末尾（「注意事项」之前）插入新章节：

```markdown
## 十、多模态：视觉 / 语音 / 文档 OCR

文本以外的三条本地路径。**能本地就本地** —— 不出本机、不花 token。

| 用途 | 别名 | 模型 | 显存 | 入口 |
| --- | --- | --- | --- | --- |
| 图片理解、截图、图表 | `vl4` | Qwen3-VL-4B Q4_K_M | ~4.5 GB | `start.sh vl4` |
| 同上，4B 不够时 | `vl8` | Qwen3-VL-8B Q4_K_M | ~6.4 GB ⚠️ | `start.sh vl8` |
| 录音转写 | `asr` | Qwen3-ASR-1.7B Q8_0 | ~4.6 GB | `start.sh asr` |
| 扫描件 / 复杂版面 / 长文档 | — | baidu/Unlimited-OCR | ~6.9 GB ⚠️ | `bash ocr/run.sh` |

`vl4` / `vl8` / `asr` 走同一个 `llama-server`，**依旧受「一次只跑一个模型」约束** ——
切模型照旧用 `start.sh`（幂等）。`ocr` 是独立栈，`run.sh` 会**先 stop.sh 腾显存**再跑。

### 调用

```bash
py -3 .../scripts/llama_chat.py --image photo.jpg "图里有什么"
py -3 .../scripts/llama_chat.py --audio meeting.wav "转写并分段落"
py -3 .../scripts/llama_chat.py --image a.png --image b.png "对比这两张图"

# 批量：JSONL 每条绑定自己的文件（回执机制与纯文本批量一致）
py -3 .../scripts/llama_batch.py scans.jsonl -o out.jsonl -j 1 --no-think
#   {"id":"p1","prompt":"转成 markdown","image":"page_001.png"}

# 文档 OCR（独立栈，先自动腾显存）
bash .../ocr/run.sh --pdf contract.pdf --out ./out/
bash .../ocr/run.sh --image scan.png --out ./out/
```

### 什么时候回退 mimo

- **视频** —— 本地没有视频模型，这是硬缺口
- 高质量开放式视觉推理（复杂图表分析、多图对比推理）—— 4B 扛不动这类
- 本地返回空结果 / 明显幻觉 / 连续失败

### docling 还是 Unlimited-OCR

两者都做文档解析，分工按「文档里有没有可选的文字」：

- **有字可选**（PDF/DOCX/PPTX 里本来就是文本）→ `docling`，快、准、结构化好
- **是扫描图**（复杂版面、公式表格、长文档）→ `ocr/run.sh`（Unlimited-OCR）

### 已知限制

- ⚠️ **`vl8` 显存余量仅约 500 MB**：它是备用而非默认 —— 平时用 `vl4`，只在 4B 明显不够时切过来。溢出时把 ctx 降到 4K。
- ⚠️ **OCR 贴边**（6.7GB 权重 / 6.9GB 可用）：跑前务必 `stop.sh`，别同时开占显存的程序。
- ⚠️ **音频输入在 llama.cpp 里是 highly experimental**：大文件出问题的退路是启动时加 `--no-mmproj-offload`（音频编码器退回 CPU）。
- 图像格式限 `llama_media.IMAGE_MIME` 里的六种（png/jpg/jpeg/gif/webp/bmp），其余显式报错。
- OCR 需 `trust_remote_code=True`（百度官方 MIT 许可）—— 会执行仓库内的自定义建模代码。
```

- [ ] **Step 3: 改 `local-ai/SKILL.md` 里过时的边界描述**

⚠️ **本步实际有三处，不是两处**（pre-flight scan 后修正）：除下面列出的两处，
**frontmatter 的 `description` 末行**也写着 `视觉/OCR/音频走 mimo 或 docling，不在此技能。`
—— Step 5 的验收 grep 会命中它，不改则验收永远无法通过。该行是技能的**触发机制**，
应改为：

```
  视觉/OCR/音频也走本机多模态（vl4/vl8/asr/ocr，0 token、不出本机），视频与高难度视觉推理才回退 mimo。
```

把文件开头「复杂规划、跨系统重构留主模型；视觉/OCR/音频走 mimo 或 `docling`。」改为：

```
复杂规划、跨系统重构留主模型；视觉/OCR/音频默认走本机多模态（见「十、多模态」），
视频与高难度视觉推理回退 mimo。
```

并把「注意事项」里最后一条：

```
- **不负责的**：视觉/OCR/音频 → mimo 或 `docling`；无 mmproj 文件，两个模型均**纯文本**。
```

改为：

```
- **文本模型的边界**：MiniCPM5-2B 与 Qwen3.8-9B 无 mmproj，均**纯文本**；
  视觉/语音/OCR 走各自的多模态模型，见「十、多模态」。
```

- [ ] **Step 4: 同步 `skills/README.md`**

在技能表中为 `local-ai` 补上多模态能力说明，并在更新日志加一条：

```markdown
## 更新日志

### 2026-09-11
- **local-ai 新增多模态三路径**：Qwen3-VL-4B/8B（视觉，`vl4`/`vl8`）、
  Qwen3-ASR-1.7B（语音，`asr`）走 llama.cpp 主干；baidu/Unlimited-OCR（文档解析）
  走独立 venv（`D:/models/venvs/unlimited-ocr`）
- 显存账本：vl4 ~4.5GB / asr ~4.6GB / vl8 ~6.4GB（贴边，备用）/ ocr ~6.9GB（贴边）
- 边界改写：图像/音频/文档**默认走本地**（隐私、0 token），视频与高难度视觉推理回退 mimo
- docling 与 Unlimited-OCR 的分工：有字可选 → docling；扫描图 → Unlimited-OCR
```

- [ ] **Step 5: 一致性检查**

Run:
```bash
cd C:/Users/caill/.claude/skills
grep -rn "必须走 mimo\|视觉/OCR/音频走 mimo\|不负责的" local-ai/SKILL.md README.md ../CLAUDE.md
```

Expected: 无输出（旧表述已全部清除）。**若有输出，说明还有残留的冲突描述。**

- [ ] **Step 6: 提交**

```bash
cd C:/Users/caill/.claude/skills
git add local-ai/SKILL.md README.md
git commit -m "$(cat <<'EOF'
skills: local-ai 文档同步「多模态默认本地」边界

- SKILL.md 新增「十、多模态」：三条路径的别名/显存/入口、调用长相、
  回退 mimo 的条件、docling 与 Unlimited-OCR 的分工、四条已知限制
- 改掉两处过时边界：「视觉/OCR/音频走 mimo 或 docling」「两个模型均纯文本」
- README 技能表与更新日志同步
- 全局 CLAUDE.md 的模型分工改为「本地默认 + mimo 兜底」，敏感资料一律本地

Co-Authored-By: Claude Code <noreply@anthropic.com>
EOF
)"
```

> 全局 `~/.claude/CLAUDE.md` 不在本仓库内，**不随本次提交** —— Step 1 改完后单独确认即可。

---

### Task 8: 补 evals 用例

**Files:**
- Modify: `C:\Users\caill\.claude\skills\local-ai\evals\evals.json`

**Interfaces:**
- Consumes: Task 4/5/6 的 CLI 入口
- Produces: 三个多模态 eval 用例（id 3/4/5）

- [ ] **Step 1: 准备 eval 输入素材**

三个新用例引用的输入文件尚不存在，需要先造出来（现有用例的输入在 `iteration-1/inputs/` 下，跟随同一结构）：

```bash
mkdir -p "C:/Users/caill/.claude/skills/local-ai/evals/iteration-1/inputs/scans"
py -3 -c "
from PIL import Image, ImageDraw
import os
base = r'C:/Users/caill/.claude/skills/local-ai/evals/iteration-1/inputs'
for i, t in enumerate(['ALPHA 101', 'BETA 202', 'GAMMA 303'], 1):
    img = Image.new('RGB', (900, 220), 'white')
    ImageDraw.Draw(img).text((30, 100), t, fill='black')
    img.save(f'{base}/scans/page_{i:03d}.png')
img = Image.new('RGB', (1240, 400), 'white')
d = ImageDraw.Draw(img)
d.text((40, 80), 'QUARTERLY REPORT', fill='black')
d.text((40, 160), 'Revenue 1234567', fill='black')
d.text((40, 240), 'Cost 765432', fill='black')
img.save(f'{base}/scan_doc.png')
"
```

音频 `meeting.wav` 需要一段真实中文语音（TTS 或录音均可）。可复用本机 mimo TTS 生成：

```bash
set -a; source ~/.claude/.env; set +a
# 用 mimo-v2.5-tts 生成一段中文语音，保存为 meeting.wav（见全局 CLAUDE.md 的 TTS 参数）
```

若暂时拿不到合适音频，**用例 4 可先跳过**，不影响用例 3/5 的验证。

- [ ] **Step 2: 追加三个用例**

在 `evals.json` 的 `evals` 数组末尾（现有 id 2 之后）追加：

```json
    {
      "id": 3,
      "name": "vision-batch-ocr",
      "prompt": "用 local-ai 技能识别这批扫描页的文字。输入目录：inputs/scans/（3 张 PNG，每张一行印刷体文字）。把每页的文字转出来，结果存成 JSONL，每条一行，包含 index 与识别出的文字。",
      "expected_output": "一个 JSONL 文件，3 条记录，每条的识别文字与图片内容一致",
      "files": ["iteration-1/inputs/scans/"],
      "assertions": [
        "输出文件存在且是合法 JSONL",
        "恰好包含 3 条记录",
        "每条记录含 index 与文字两个字段",
        "识别出的文字与图片内容一致（字母与数字正确）",
        "回执文件 <out>.report.md 存在，且 server 实际模型为 Qwen3-VL"
      ]
    },
    {
      "id": 4,
      "name": "audio-transcribe",
      "prompt": "用 local-ai 技能转写这段会议录音。输入文件：inputs/meeting.wav。把内容转写成文字，保留分段。",
      "expected_output": "转写文本，内容与录音一致，且有合理分段",
      "files": ["iteration-1/inputs/meeting.wav"],
      "assertions": [
        "输出非空",
        "转写内容与录音音频一致（关键词语句正确）",
        "不是原样回显 prompt 或空结果",
        "输出为可读的中文文本"
      ]
    },
    {
      "id": 5,
      "name": "doc-ocr",
      "prompt": "用 local-ai 技能解析这份扫描版文档。输入文件：inputs/scan_doc.png。把文档内容转成 markdown。",
      "expected_output": "markdown 文件，内容与扫描件一致，版面结构（标题/段落/表格）得到保留",
      "files": ["iteration-1/inputs/scan_doc.png"],
      "assertions": [
        "输出 markdown 文件存在",
        "内容与扫描件文字一致",
        "保留了基本的版面结构（标题或列表或表格）",
        "回执文件 ocr.report.md 存在且计数正确"
      ]
    }
```

- [ ] **Step 3: 校验 JSON 合法**

Run:
```bash
py -3 -c "import json; d=json.load(open('C:/Users/caill/.claude/skills/local-ai/evals/evals.json', encoding='utf-8')); print(len(d['evals']), 'cases:', [e['id'] for e in d['evals']])"
```

Expected: `6 cases: [0, 1, 2, 3, 4, 5]`

- [ ] **Step 4: 提交**

```bash
cd C:/Users/caill/.claude/skills
git add local-ai/evals/evals.json
git commit -m "$(cat <<'EOF'
skills: local-ai 补三个多模态 eval 用例

覆盖视觉批量 OCR（vision-batch-ocr）、音频转写（audio-transcribe）、
文档 OCR（doc-ocr），断言里含回执存在性与 server 实际模型名的核对。

Co-Authored-By: Claude Code <noreply@anthropic.com>
EOF
)"
```

---

## 附录：验收总表

全部任务完成后，逐条核对（对应 spec §8）：

- [ ] 1. 四个新路径各自跑出正确结果（vl4 / vl8 / asr / ocr 各一条真实输入）
- [ ] 2. 显存不溢出 —— 每个模型启动后 `nvidia-smi` 与启动日志确认无层掉到 CPU
- [ ] 3. 切换幂等 —— 连续两次 `start.sh vl4`，第二次必须打印 `[复用]`
- [ ] 4. 批量回执正常 —— 多模态批量跑完生成 `<out>.report.md`，含 server 实际模型名
- [ ] 5. 纯文本用法未破坏 —— 现有 `llama_chat.py` / `llama_batch.py` 文本用法回归通过
- [ ] 6. 文档同步 —— CLAUDE.md / SKILL.md / README.md 三处一致，无残留冲突

**收工**：`bash scripts/stop.sh` —— 释放显存。

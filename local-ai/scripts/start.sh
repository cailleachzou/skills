#!/bin/bash
# local-ai 启动 / 切换脚本
# 用法: ./start.sh [minicpm|9b|ornith|ornith-vl|vl4|vl8|asr] [port] [--额外 llama-server 参数…]
#       默认 minicpm (2B)
#
# 第 3 个参数起**原样透传**给 llama-server（`"${@:3}"`，追加在最后）。例：
#   ./start.sh 9b 8080 --chat-template-file /path/to/tpl.jinja
# 用于 codex（见 ../codex/start-codex.sh）—— codex 需要一份合并 system 消息的模板。
# 追加在最后是有意的：`--jinja` 必须先于 `--chat-template-file` 出现，
# 否则自定义模板会被当成「非通用模板」拒掉。
#
# Git Bash 别名（~/.bashrc）：  llama = 2B，  llama9 = 9B，  llamaOT = ornith，  llamaOV = ornith-vl
#
# 幂等：先问在跑的是哪个模型 ——
#   已经是目标模型 → 直接复用（不重启，省掉重新加载、也保住前缀缓存）
#   是另一个模型   → 先 stop.sh（等显存回收）再启动目标模型
#   没有在跑       → 直接启动
#
# ⚠️ llama-server 一次只装一个模型，且**忽略请求体里的 model 字段**。
#    换模型 = 重启本脚本。别为单条任务来回切 —— 选定一轮只用一个（见 SKILL.md「一」）。
#
# 服务端按官方推荐配置启动（MiniCPM5 官方 llama.cpp cookbook：
#   llama-server -m <gguf> -ngl 99 -c <ctx> --jinja）。
#
# ⚠️ 思考开关不在这里 —— 三个文本模型 (minicpm / 9b / ornith) 都是 thinking 模型；
#    vl4 / vl8 / asr 是 Instruct / 转写模型，本身没有思考档。关闭思考**必须走请求级**
#    参数 chat_template_kwargs（见 llama_chat.py）。服务端的 --reasoning off /
#    --reasoning-budget 0 / --chat-template-kwargs 在本机 build(b10883) 上全部实测失效
#    （llama.cpp 上游 bug，PR #22336 未合并）。

set -e -u

# 下面每个路径都**可以用同名环境变量覆盖**：`VAR="${VAR:-默认}"`。
# 同事的 llama.cpp 与模型不在 C:/D: 下时，导出变量即可，不必改这个文件：
#   export LLAMA_DIR=/c/tools/llama-cpp/cuda-b10883
#   export MODEL_9B=/c/models/qwen3.8-9b/Qwen3.8-9B-Q4_K_M.gguf
# 用法同 `ocr/run.sh` 的 `UNLIMITED_OCR_VENV` — 本仓库既有风格，勿另造机制。
LLAMA_DIR="${LLAMA_DIR:-C:/Users/caill/tools/llama-cpp/cuda-b10883}"
MODEL_MINICPM="${MODEL_MINICPM:-D:/models/gguf/minicpm5-2b/MiniCPM5-2B-Q8_0.gguf}"
MODEL_9B="${MODEL_9B:-D:/models/gguf/qwen3.8-9b-distill/Qwen3.8-9B-Q4_K_M.gguf}"
# Ornith-1.5-9B：同为 qwen35 架构（33 blocks / 24 层 SSM + 8 层全注意力 / nextn MTP），
# 实测与 9B-Distill 同速（34 vs 35 tok/s）、显存同量级。见 SKILL.md「一」的选型说明。
MODEL_ORNITH="${MODEL_ORNITH:-D:/models/gguf/ornith-1.5-9b/Ornith-1.5-9B-Q4_K_M.gguf}"
# 视觉版：**同一个权重文件** + mmproj。两个配置共用 basename，所以 running_model()
# 只能靠 /props 的 modalities.vision 区分（见下）。8K ctx 时整卡 7556 MiB（实测）。
MMPROJ_ORNITH="${MMPROJ_ORNITH:-D:/models/gguf/ornith-1.5-9b/mmproj-Ornith-1.5-9B-BF16.gguf}"
# ⚠️ 改这个文件名前先看 evals/evals.json 的 id 3 —— 那里的断言写死了这个 basename
#    （回执里的 server 模型名取自 GGUF basename，是 4B/8B 唯一的机械判别器）。
MODEL_VL4="${MODEL_VL4:-D:/models/gguf/qwen3-vl-4b/Qwen3VL-4B-Instruct-Q4_K_M.gguf}"
MMPROJ_VL4="${MMPROJ_VL4:-D:/models/gguf/qwen3-vl-4b/mmproj-Qwen3VL-4B-Instruct-F16.gguf}"
MODEL_VL8="${MODEL_VL8:-D:/models/gguf/qwen3-vl-8b/Qwen3VL-8B-Instruct-Q4_K_M.gguf}"
MMPROJ_VL8="${MMPROJ_VL8:-D:/models/gguf/qwen3-vl-8b/mmproj-Qwen3VL-8B-Instruct-Q8_0.gguf}"
MODEL_ASR="${MODEL_ASR:-D:/models/gguf/qwen3-asr-1.7b/Qwen3-ASR-1.7B-Q8_0.gguf}"
MMPROJ_ASR="${MMPROJ_ASR:-D:/models/gguf/qwen3-asr-1.7b/mmproj-Qwen3-ASR-1.7b-BF16.gguf}"

MODEL_TYPE="${1:-minicpm}"
PORT="${2:-8080}"
HERE="$(cd "$(dirname "$0")" && pwd)"

usage() {
  echo "用法: $0 [minicpm|9b|ornith|ornith-vl|vl4|vl8|asr] [port] [额外的 llama-server 参数…]"
  echo "  minicpm - MiniCPM5-2B Q8 GPU 整卡, 128K ctx (默认；批量 / 长文本 / 并发)"
  echo "  9b      - Qwen3.8-9B-Distill GPU 整卡, 64K ctx (pi agent / 复杂任务 / 代码) [默认 9B 级]"
  echo "  ornith  - Ornith-1.5-9B Q4_K_M GPU 整卡, 64K ctx (9B 级备选)"
  echo "  ornith-vl - 同上 + mmproj, 32K ctx (一个模型兼做视觉；agent 能看图)"
  echo "  vl4     - Qwen3-VL-4B Q4_K_M + mmproj F16, 16K ctx (视觉/图片理解，默认视觉模型)"
  echo "  vl8     - Qwen3-VL-8B Q4_K_M + mmproj Q8_0, 8K ctx (视觉备用；显存余量仅 ~440 MiB)"
  echo "  asr     - Qwen3-ASR-1.7B Q8_0 + mmproj BF16, 32K ctx (语音转写)"
  echo ""
  echo "Git Bash 别名：llama = 2B，llama9 = 9B，llamaOT = ornith，llamaOV = ornith-vl"
  echo "幂等：已经在跑目标模型就不重启；跑着别的模型会先停掉再启。"
  echo "思考开关在客户端：llama_chat.py（默认开思考，--no-think 关闭）"
  echo ""
  echo "路径可用环境变量覆盖：LLAMA_DIR / MODEL_* / MMPROJ_*（默认指本机安装位置）"
}

case "$MODEL_TYPE" in
  minicpm|9b|ornith|ornith-vl|vl4|vl8|asr) ;;
  *) usage; exit 1 ;;
esac

# 问出当前在跑的是哪个模型；没在跑就返回非零
running_model() {
  local body
  body=$(curl -s -m 3 "http://127.0.0.1:${PORT}/v1/models" 2>/dev/null) || return 1
  [ -n "$body" ] || return 1
  case "$body" in
    *MiniCPM*)         echo minicpm ;;
    # ⚠️ Ornith 的 basename 是 Ornith-1.5-9B-Q4_K_M.gguf，**也含 "9B-Q4_K_M"** ——
    #    这条必须排在下面那条之前，否则 Ornith 会被认成 9b：`start.sh 9b` 会误报
    #    「[复用] 已经在跑 9b」并静默返回，实际跑的还是 Ornith（实测复现过）。
    *Ornith*)
      # 文本版与视觉版共用同一权重文件，basename 分不开 —— 靠 /props 的
      # modalities.vision 判别（带 mmproj 才是 true）。见 SKILL.md「一」的说明。
      local props
      props=$(curl -s -m 3 "http://127.0.0.1:${PORT}/props" 2>/dev/null)
      case "$props" in
        *'"vision": true'*|*'"vision":true'*) echo ornith-vl ;;
        *)                                    echo ornith ;;
      esac ;;
    *9B-Q4_K_M*)       echo 9b ;;
    *Qwen3VL-4B*)      echo vl4 ;;
    *Qwen3VL-8B*)      echo vl8 ;;
    *Qwen3-ASR-1.7B*)  echo asr ;;
    *)                 echo unknown ;;
  esac
}

if current=$(running_model); then
  if [ "$current" = "$MODEL_TYPE" ]; then
    echo "[复用] ${PORT} 上已经在跑 $MODEL_TYPE，不重启"
    exit 0
  fi
  echo "[切换] ${PORT} 上跑的是 $current，先停掉"
  bash "$HERE/stop.sh" "$PORT"
fi

case "$MODEL_TYPE" in
  minicpm)
    echo "启动 MiniCPM5-2B Q8 (GPU 整卡, 128K ctx 由 4 slot 共享, ~85-107 tok/s) [默认]"
    exec "$LLAMA_DIR/llama-server.exe" \
      -m "$MODEL_MINICPM" \
      -ngl 99 \
      --host 127.0.0.1 \
      --port "$PORT" \
      -c 131072 \
      --jinja \
      --cache-type-k q8_0 \
      --cache-type-v q8_0 \
      --temp 1.0 \
      --top-p 0.95 \
      "${@:3}"
    ;;
  9b)
    # 64K ctx（2026-09-24 实测）：整卡 7228 MiB，decode 与 32K 无差别
    # （32K 53.8–56.7 / 64K 51.0–55.9 tok/s，差在噪声内），所以别退回 32K。
    echo "启动 Qwen3.8-9B-Distill (GPU 整卡, 64K ctx 由 4 slot 共享, ~55 tok/s)"
    exec "$LLAMA_DIR/llama-server.exe" \
      -m "$MODEL_9B" \
      -ngl 99 \
      --host 127.0.0.1 \
      --port "$PORT" \
      -c 65536 \
      --jinja \
      --cache-type-k q8_0 \
      --cache-type-v q8_0 \
      --temp 0.6 \
      --top-p 0.95 \
      --top-k 20 \
      "${@:3}"
    ;;
  ornith)
    # 采样参数按官方「精确编码任务」推荐：temp 0.6 / top_p 0.95 / top_k 20
    # （官方通用档另建议 presence_penalty 1.5，本机脚本不设，需要时按请求传）
    # 64K ctx（2026-09-24 实测）：整卡 7112 MiB，decode 56.3 tok/s —— 与 32K 的
    # 57.4 基本持平（+714 MiB 换一倍上下文）。上限是原生 262144，但那时掉到 22。
    echo "启动 Ornith-1.5-9B (GPU 整卡, 64K ctx 由 4 slot 共享, ~56 tok/s)"
    exec "$LLAMA_DIR/llama-server.exe" \
      -m "$MODEL_ORNITH" \
      -ngl 99 \
      --host 127.0.0.1 \
      --port "$PORT" \
      -c 65536 \
      --jinja \
      --cache-type-k q8_0 \
      --cache-type-v q8_0 \
      --temp 0.6 \
      --top-p 0.95 \
      --top-k 20 \
      "${@:3}"
    ;;
  ornith-vl)
    # 32K ctx（不是 64K）：权重 + mmproj 在 64K 下实测整卡 7833 MiB = 整卡 96%，
    # 只剩 ~318 MiB —— 比已知贴边的 vl8（~440 MiB）还紧，图像编码再要缓冲区，
    # 一旦溢出就是「不报错只变慢」。32K 下约 7.3 GB，留 ~850 MiB 余量。
    # 磁盘开销：一张 768px 图 ≈ 576 token，32K 约能放 50 张。
    echo "启动 Ornith-1.5-9B + mmproj (GPU 整卡, 32K ctx, 文本+视觉)"
    exec "$LLAMA_DIR/llama-server.exe" \
      -m "$MODEL_ORNITH" \
      --mmproj "$MMPROJ_ORNITH" \
      -ngl 99 \
      --host 127.0.0.1 \
      --port "$PORT" \
      -c 32768 \
      --jinja \
      --cache-type-k q8_0 \
      --cache-type-v q8_0 \
      --temp 0.7 \
      --top-p 0.8 \
      "${@:3}"
    ;;
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
      --top-p 0.8 \
      "${@:3}"
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
      --top-p 0.8 \
      "${@:3}"
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
      --temp 0.0 \
      "${@:3}"
    ;;
esac

#!/bin/bash
# local-ai 启动 / 切换脚本
# 用法: ./start.sh [minicpm|9b|vl4|vl8|asr] [port]      # 默认 minicpm (2B)
#
# Git Bash 别名（~/.bashrc）：  llama = 2B，  llama9 = 9B
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
# ⚠️ 思考开关不在这里 —— 只有两个文本模型 (minicpm / 9b) 是 thinking 模型；
#    vl4 / vl8 / asr 是 Instruct / 转写模型，本身没有思考档。关闭思考**必须走请求级**
#    参数 chat_template_kwargs（见 llama_chat.py）。服务端的 --reasoning off /
#    --reasoning-budget 0 / --chat-template-kwargs 在本机 build(b10883) 上全部实测失效
#    （llama.cpp 上游 bug，PR #22336 未合并）。

set -e -u

LLAMA_DIR="C:/Users/caill/tools/llama-cpp/cuda-b10883"
MODEL_MINICPM="D:/models/gguf/minicpm5-2b/MiniCPM5-2B-Q8_0.gguf"
MODEL_9B="D:/models/gguf/qwen3.8-9b-distill/Qwen3.8-9B-Q4_K_M.gguf"
# ⚠️ 改这个文件名前先看 evals/evals.json 的 id 3 —— 那里的断言写死了这个 basename
#    （回执里的 server 模型名取自 GGUF basename，是 4B/8B 唯一的机械判别器）。
MODEL_VL4="D:/models/gguf/qwen3-vl-4b/Qwen3VL-4B-Instruct-Q4_K_M.gguf"
MMPROJ_VL4="D:/models/gguf/qwen3-vl-4b/mmproj-Qwen3VL-4B-Instruct-F16.gguf"
MODEL_VL8="D:/models/gguf/qwen3-vl-8b/Qwen3VL-8B-Instruct-Q4_K_M.gguf"
MMPROJ_VL8="D:/models/gguf/qwen3-vl-8b/mmproj-Qwen3VL-8B-Instruct-Q8_0.gguf"
MODEL_ASR="D:/models/gguf/qwen3-asr-1.7b/Qwen3-ASR-1.7B-Q8_0.gguf"
MMPROJ_ASR="D:/models/gguf/qwen3-asr-1.7b/mmproj-Qwen3-ASR-1.7b-BF16.gguf"

MODEL_TYPE="${1:-minicpm}"
PORT="${2:-8080}"
HERE="$(cd "$(dirname "$0")" && pwd)"

usage() {
  echo "用法: $0 [minicpm|9b|vl4|vl8|asr] [port]"
  echo "  minicpm - MiniCPM5-2B Q8 GPU 整卡, 128K ctx (默认；批量 / 长文本 / 并发)"
  echo "  9b      - Qwen3.8-9B-Distill GPU 整卡, 32K ctx (pi agent / 复杂任务 / 代码)"
  echo "  vl4     - Qwen3-VL-4B Q4_K_M + mmproj F16, 16K ctx (视觉/图片理解，默认视觉模型)"
  echo "  vl8     - Qwen3-VL-8B Q4_K_M + mmproj Q8_0, 8K ctx (视觉备用；显存余量仅 ~440 MiB)"
  echo "  asr     - Qwen3-ASR-1.7B Q8_0 + mmproj BF16, 32K ctx (语音转写)"
  echo ""
  echo "Git Bash 别名：llama = 2B，llama9 = 9B"
  echo "幂等：已经在跑目标模型就不重启；跑着别的模型会先停掉再启。"
  echo "思考开关在客户端：llama_chat.py（默认开思考，--no-think 关闭）"
}

case "$MODEL_TYPE" in
  minicpm|9b|vl4|vl8|asr) ;;
  *) usage; exit 1 ;;
esac

# 问出当前在跑的是哪个模型；没在跑就返回非零
running_model() {
  local body
  body=$(curl -s -m 3 "http://127.0.0.1:${PORT}/v1/models" 2>/dev/null) || return 1
  [ -n "$body" ] || return 1
  case "$body" in
    *MiniCPM*)         echo minicpm ;;
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
      --top-p 0.95
    ;;
  9b)
    echo "启动 Qwen3.8-9B-Distill (GPU 整卡, 32K ctx 由 4 slot 共享, ~55 tok/s)"
    exec "$LLAMA_DIR/llama-server.exe" \
      -m "$MODEL_9B" \
      -ngl 99 \
      --host 127.0.0.1 \
      --port "$PORT" \
      -c 32768 \
      --jinja \
      --cache-type-k q8_0 \
      --cache-type-v q8_0 \
      --temp 0.6 \
      --top-p 0.95 \
      --top-k 20
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
esac

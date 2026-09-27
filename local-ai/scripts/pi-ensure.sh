#!/bin/bash
# pi-ensure.sh —— 确保 8080 上跑着 Ornith-1.5-9B **文本版**（= Git Bash 别名 llamaOT 的那个）。
#
# 用法: ./pi-ensure.sh [port]
#
# 退出码（调用方据此决定退出时要不要收工 —— 这是本脚本存在的意义）：
#   0 = 已经在跑 ornith 文本版，**没动它**   → 这份 server 不归你，退出时别停
#   3 = 本次由我拉起 / 从别的模型切过来       → 退出时该跑 stop.sh
#   1 = 失败（日志尾部已打到 stderr）         → 不要进 pi
#
# 约定：
#   - stdout 保持干净（调用方可能只用退出码，但留着以后解析的余地）
#   - 提示一律走 stderr，且**写英文** —— 本脚本会被 CMD / PowerShell 调起来，
#     中文经管道跨解释器会乱码（实测 `Write-Host "中文"` 传到 bash 显示为 `????`）。
#     这与 start.bat / stop.bat 用英文是同一个理由。
#   - **不要加 set -e**：curl 在没人监听时返回非零，而那正是「需要我启动」的主分支。
#
# ⚠️ Ornith 文本版 / vl 版的判别，是这里唯一复制自 start.sh `running_model()` 的逻辑
#    （两者共用同一个 GGUF basename，只能靠 /props 的 modalities.vision 分）。改一处要改两处。
#
# 前台阻塞的 start.sh 由这里后台拉起（它的结尾是 exec llama-server.exe）。

set -u

PORT="${1:-8080}"
TARGET=ornith
SCRIPTS="$(cd "$(dirname "$0")" && pwd)"
LOG="${TMPDIR:-/tmp}/pi-llama.log"
BASE="http://127.0.0.1:${PORT}"

# 从 CMD / PowerShell 调起来时的兜底（实测 Git Bash 自带 PATH 也够用）
export PATH="/mingw64/bin:/usr/bin:/bin:$PATH"

# HTTP 码：200 = 就绪；503 = 已监听但模型还在加载；000 = 连接被拒（没人跑）
health() { curl -s -o /dev/null -w '%{http_code}' -m 2 "${BASE}/health" 2>/dev/null; }

llama_alive() {
  tasklist //FI "IMAGENAME eq llama-server.exe" 2>/dev/null | grep -qi 'llama-server'
}

running_model() {
  local body props
  body=$(curl -s -m 3 "${BASE}/v1/models" 2>/dev/null)
  case "$body" in
    *Ornith*)
      props=$(curl -s -m 3 "${BASE}/props" 2>/dev/null)
      case "$props" in
        *'"vision": true'*|*'"vision":true'*) echo ornith-vl ;;
        *)                                    echo ornith ;;
      esac ;;
    *MiniCPM*)    echo minicpm ;;
    *9B-Q4_K_M*)  echo 9b ;;
    *Qwen3VL-4B*) echo vl4 ;;
    *Qwen3VL-8B*) echo vl8 ;;
    *Qwen3-ASR*)  echo asr ;;
    *)            echo unknown ;;
  esac
}

start_server() {
  echo "[start] loading Ornith-1.5-9B (llamaOT) on ${PORT} ..." >&2
  nohup bash "${SCRIPTS}/start.sh" "$TARGET" "$PORT" >>"$LOG" 2>&1 &
  local i h
  for i in $(seq 1 240); do                       # 最多 120s，0.5s 一探
    h=$(health)
    # ⚠️ 光看 200 不够：切换时**旧 server 还在应答**（start.sh 正忙着 stop.sh），
    #    第一次探测就会 200。必须同时确认加载的就是目标模型 —— 实测漏掉这步会
    #    在 0.37s 内报「ready」而实际还是上一个模型。
    if [ "$h" = 200 ] && [ "$(running_model)" = "$TARGET" ]; then
      echo "[ready] ornith is up on ${PORT}" >&2
      exit 3
    fi
    # 快速失败：已经等了 8s，端口没人答、连 llama-server 进程都不在 —— 别再干等两分钟
    if [ "$i" -gt 16 ] && [ "$h" = 000 ] && ! llama_alive; then
      echo "[error] llama-server is not running and ${PORT} does not answer. log tail:" >&2
      tail -20 "$LOG" >&2
      exit 1
    fi
    sleep 0.5
  done
  echo "[error] not ready within 120s. log: ${LOG}" >&2
  tail -20 "$LOG" >&2
  exit 1
}

# ── 串行化：两个终端同时敲 pi 时，别让两个 start.sh 互相抢显存 ──────────────
LOCK="${TMPDIR:-/tmp}/pi-ensure-${PORT}.lock"
LOCKED=0
for _ in $(seq 1 120); do                          # 最多等 60s
  if mkdir "$LOCK" 2>/dev/null; then
    trap 'rmdir "$LOCK" 2>/dev/null' EXIT
    LOCKED=1
    break
  fi
  [ -n "$(find "$LOCK" -maxdepth 0 -mmin +3 2>/dev/null)" ] && rmdir "$LOCK" 2>/dev/null   # 陈旧锁
  sleep 0.5
done
[ "$LOCKED" = 1 ] || echo "[warn] ${LOCK} 等了 60s 仍被占用 —— 未持锁继续，可能与并发的 start.sh 抢显存" >&2

# ── 拿锁之后再判一次状态（第二个进场的人应该直接复用第一个起好的）────────────
case "$(health)" in
  200)
    current=$(running_model)
    if [ "$current" = "$TARGET" ]; then
      echo "[reuse] ${PORT} already serves ornith (llamaOT); leaving it running" >&2
      exit 0
    fi
    # 视觉版也共用同一份权重，但 ctx 只有 32K 而 pi 侧声明 64K —— 不复用，切成文本版
    echo "[switch] ${PORT} serves ${current} -> ${TARGET} (the old server is NOT restored on exit)" >&2
    start_server
    ;;
  503)
    echo "[wait] another llama-server is loading on ${PORT}; waiting for it ..." >&2
    for _ in $(seq 1 240); do [ "$(health)" = 200 ] && break; sleep 0.5; done
    if [ "$(health)" = 200 ]; then
      if [ "$(running_model)" = "$TARGET" ]; then
        echo "[reuse] ornith is up (loaded by another session); leaving it running" >&2
        exit 0                                    # 别人起的 —— 退出时不该由我们停
      fi
      echo "[switch] ${PORT} serves $(running_model) -> ${TARGET} (the old server is NOT restored on exit)" >&2
    fi
    start_server
    ;;
  *)
    start_server
    ;;
esac

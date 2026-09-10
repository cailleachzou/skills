#!/bin/bash
# 停掉本机的 llama-server，并**等显存真的回收**。
#
# 用法: ./stop.sh [port]
#
# 为什么杀完不能立刻走：驱动回收显存有延迟。紧接着启动新模型时，未释放的显存
# 会把部分层挤到 CPU —— **不报错**，只是慢十倍（SKILL.md「实测性能」有记录）。
# 所以这里不 sleep 固定秒数，而是轮询显存直到它真的掉下来。
#
# 什么时候该跑它：一轮本地任务收工之后。服务器常驻不会自己退出，会把
# 6~7GB 显存在后台占着不放。

set -u

PORT="${1:-8080}"

vram() { nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits 2>/dev/null \
         | head -1 | tr -d ' \r'; }
running() { curl -s -m 2 "http://127.0.0.1:${PORT}/health" >/dev/null 2>&1; }

if ! tasklist //FI "IMAGENAME eq llama-server.exe" 2>/dev/null | grep -qi "llama-server"; then
  echo "[停止] 没有在跑的 llama-server，显存占用 $(vram) MiB"
  exit 0
fi

before=$(vram); before=${before:-0}

echo "[停止] 结束 llama-server…"
taskkill //F //IM llama-server.exe //T >/dev/null 2>&1 || true

# 退出 + 显存回落，两者都满足才走；最多等 30s
vram_dropped() {
  [ "$before" -eq 0 ] && return 0          # 读不到 nvidia-smi 就别卡在这
  local now; now=$(vram); now=${now:-0}
  [ $((before - now)) -ge 2500 ]
}
for _ in $(seq 1 30); do
  if ! running && vram_dropped; then break; fi
  sleep 1
done

if running; then
  echo "[警告] 端口 ${PORT} 仍有服务应答，可能有别的进程占着" >&2
  exit 1
fi

after=$(vram); after=${after:-0}
if ! vram_dropped; then
  echo "[警告] 进程已退出，但显存只从 ${before} 掉到 ${after} MiB" >&2
  echo "       立刻重启新模型可能掉到 CPU，建议等几秒" >&2
  exit 0
fi

echo "[停止] 已退出，显存 ${before} → ${after} MiB"

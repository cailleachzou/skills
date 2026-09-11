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

# stop.sh 只在一种情况下 exit 1：杀完之后端口仍有服务应答 —— 意思就是
# 「显存没干净回收」。而这恰恰是最不能吞掉的一种失败：OCR 权重 6.7GB、
# 本机可用约 6.9GB，与残留的 6~7GB 装不下同一张卡 —— 轻则部分层落到 CPU
#（不报错、只慢十倍，正是本栈存在的理由），重则加载期 CUDA OOM 崩在 try 之外、
# 连回执都不留。所以这里判退出码并中止，不吞。
if ! bash "$HERE/../scripts/stop.sh"; then
  echo "[错误] stop.sh 没能确认显存回收 —— 中止，不启动 OCR。" >&2
  echo "       为什么危险：OCR 权重 6.7GB / 可用约 6.9GB 贴边，残留显存会把" >&2
  echo "       部分层挤到 CPU（不报错、只慢十倍），或直接 CUDA OOM 崩掉。" >&2
  echo "       先查：nvidia-smi 看还有谁占着卡；必要时手动结束残留进程再重试。" >&2
  exit 1
fi

echo "[OCR] 显存已腾出，开始推理…" >&2
exec "$PY" "$HERE/ocr.py" "$@"

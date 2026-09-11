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

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

# 显存守卫分两层 —— 因为 stop.sh 的退出码盖不住最危险的那种残留：
#   ① stop.sh 只在「杀完之后端口仍有服务应答」时 exit 1（这个报错要留）；
#      而「进程已退出、显存却没跌够」那条路它是 **exit 0**（自己只当警告打印）。
#      只判退出码的话，那种残留会原样放行到 6.7GB 的加载。
#   ② 所以下面再自己读一次 nvidia-smi 的余量，不够就中止。
# 为什么不改 stop.sh 让它也 exit 1：那会误伤 start.sh —— 它在 `set -e` 下直接
# `bash "$HERE/stop.sh" "$PORT"`，非零会让「切换模型」整步中止。守卫加在真正
# 需要它的这一侧，stop.sh 语义保持不变。
if ! bash "$HERE/../scripts/stop.sh"; then
  echo "[错误] stop.sh 没能确认显存回收 —— 中止，不启动 OCR。" >&2
  echo "       先查：nvidia-smi 看还有谁占着卡；必要时手动结束残留进程再重试。" >&2
  exit 1
fi

# 第二层：余量自检。OCR 权重 6.7GB / 本机可用约 6.9GB，贴边；余量不够时
# 轻则部分层落到 CPU（不报错、只慢十倍，正是本栈存在的理由），重则加载期
# CUDA OOM 崩在 try 之外、连回执都不留。
NEED_MIB=6600
vram_line=$(nvidia-smi --query-gpu=memory.total,memory.used --format=csv,noheader,nounits 2>/dev/null \
            | head -1 | tr -d ' \r')
total_mib=${vram_line%%,*}
used_mib=${vram_line##*,}
case "${total_mib}${used_mib}" in
  ''|*[!0-9]*)
    echo "[警告] 读不到 nvidia-smi 的显存读数，跳过余量自检 —— 刚切过模型的话请手动确认。" >&2 ;;
  *)
    free_mib=$((total_mib - used_mib))
    if [ "$free_mib" -lt "$NEED_MIB" ]; then
      echo "[错误] 显存余量不足：仅 ${free_mib} MiB 可用（已用 ${used_mib} / 总 ${total_mib}），" >&2
      echo "       OCR 需要约 ${NEED_MIB} MiB —— 中止，不启动 OCR。" >&2
      echo "       为什么危险：余量不够时部分层会被挤到 CPU（不报错、只慢十倍），" >&2
      echo "       或直接 CUDA OOM 崩在 try 之外、连回执都不留。" >&2
      echo "       先查：nvidia-smi 看还有谁占着卡；必要时手动结束残留进程再重试。" >&2
      exit 1
    fi
    echo "[OCR] 显存余量 ${free_mib} MiB（已用 ${used_mib} / 总 ${total_mib}），开始推理…" >&2 ;;
esac

exec "$PY" "$HERE/ocr.py" "$@"

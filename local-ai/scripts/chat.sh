#!/bin/bash
# local-ai 交互式对话（llama_chat.py 的薄封装，单轮逻辑不重复实现）
# 用法: ./chat.sh [--no-think] [system_prompt]
#
# 默认开启思考；简单任务加 --no-think 省 token。
# 需先启动 llama-server：`llama`（默认 2B）或 `llama9`（9B）—— 见 start.sh

SCRIPT="$(dirname "$0")/llama_chat.py"

THINK_ARG=""
if [ "$1" = "--no-think" ]; then
  THINK_ARG="--no-think"
  shift
fi
SYSTEM_PROMPT="${1:-你是一个有用的AI助手，简洁明了地回答问题。}"

echo "=== local-ai 交互对话 ==="
echo "输入问题，按 Enter 发送。输入 'exit' 或 'quit' 退出。"
if [ -z "$THINK_ARG" ]; then
  echo "（思考已开启；要省 token 请用：chat.sh --no-think）"
fi
echo ""

while true; do
  read -r -p "> " user_input

  case "$user_input" in
    exit|quit) echo "再见！"; break ;;
    "") continue ;;
  esac

  py -3 "$SCRIPT" $THINK_ARG -s "$SYSTEM_PROMPT" "$user_input"
  echo ""
done

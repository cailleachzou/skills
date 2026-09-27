#!/bin/bash
# 起一个 **codex 能用** 的 llama-server。
#
# 用法: ./start-codex.sh [9b|minicpm] [port]      # 默认 9b / 8080
#
# 和 scripts/start.sh 的唯一区别：多加一个 --chat-template-file <合并版模板>。
# 其余（模型路径、ctx、KV 量化、采样参数）全部复用 start.sh —— 单一事实来源。
#
# ⚠️ 为什么不能用 `start.sh 9b` 起服务再跑 codex：
#    codex 只讲 Responses API，每个请求同时带 `instructions` 和一条 `developer`
#    消息，llama-server 把两者都转成 system 角色 → 消息以两条 system 开头。
#    Qwen3.8 原版模板对此直接 raise，**每个** codex 请求都 HTTP 500
#    （`System message must be at the beginning.`）。必须换合并版模板。
#
# ⚠️ 前台阻塞进程（内部 exec llama-server），在工具里要后台启动：
#    nohup bash start-codex.sh 9b > /tmp/llama.log 2>&1 &
#
# 幂等：比对 /props 回读的模板与本地模板**内容**是否一致 ——
# 不能只看模型名（`start.sh 9b` 起的同名服务模板不对），
# 也不能比对固定 marker（minicpm 的模板本来就不需要补丁，永远不会有 marker）。

set -e -u

HERE="$(cd "$(dirname "$0")" && pwd)"
SCRIPTS="$HERE/../scripts"
MODEL_TYPE="${1:-9b}"
PORT="${2:-8080}"
TPL="$HERE/template-${MODEL_TYPE}.jinja"

usage() {
  echo "用法: $0 [9b|minicpm] [port]"
  echo "  9b      - Qwen3.8-9B-Distill，64K ctx（codex 推荐）"
  echo "  minicpm - MiniCPM5-2B，128K ctx（快，但 agent 能力弱）"
  echo ""
  echo "起完后： codex -p local"
}

case "$MODEL_TYPE" in
  9b|minicpm) ;;
  *) usage; exit 1 ;;
esac

# 1) 生成/刷新模板（离线读 GGUF，不占显存，秒级）
echo "[模板] $TPL"
py -3 "$HERE/prepare.py" template --model "$MODEL_TYPE" --out "$TPL"

# 2) 幂等判断：端口上跑的模板和本地这份是不是同一份？
running_uses_our_template() {
  local props
  props=$(curl -s -m 3 "http://127.0.0.1:${PORT}/props" 2>/dev/null) || return 1
  [ -n "$props" ] || return 1
  printf '%s' "$props" \
    | py -3 "$HERE/prepare.py" check-template --file "$TPL"
}

if curl -s -m 2 "http://127.0.0.1:${PORT}/health" >/dev/null 2>&1; then
  if running_uses_our_template; then
    echo "[复用] ${PORT} 上已经是同一份模板，不重启"
    exit 0
  fi
  echo "[切换] ${PORT} 上的服务模板不同（多半是 start.sh 起的），先停掉"
  bash "$SCRIPTS/stop.sh" "$PORT"
fi

# 3) 交给 start.sh 起服务，把模板作为额外参数透传（start.sh 的第 3 个参数起）
exec bash "$SCRIPTS/start.sh" "$MODEL_TYPE" "$PORT" \
  --chat-template-file "$TPL"

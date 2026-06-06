#!/usr/bin/env bash
# Manage web-search-fast MCP server for Claude Code
# Usage:
#   ./scripts/mcp-server.sh register          # Register stdio MCP (recommended)
#   ./scripts/mcp-server.sh start             # Start HTTP background server + register
#   ./scripts/mcp-server.sh stop              # Stop HTTP background server
#   ./scripts/mcp-server.sh status            # Check status
#   ./scripts/mcp-server.sh unregister        # Remove from Claude Code
set -euo pipefail

# --- Config ---
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="${PYTHON:-python3}"
MCP_NAME="web-search-fast"
SCOPE="user"                    # user | local | project
HOST="127.0.0.1"
PORT="8897"
PIDFILE="/tmp/web-search-mcp.pid"
LOGFILE="/tmp/web-search-mcp.log"

# --- Register stdio mode (recommended) ---
register() {
    claude mcp remove "$MCP_NAME" -s "$SCOPE" 2>/dev/null || true
    claude mcp add-json -s "$SCOPE" "$MCP_NAME" "$(cat <<ENDJSON
{
  "type": "stdio",
  "command": "$PYTHON",
  "args": ["-m", "src.mcp_server", "--transport", "stdio"],
  "env": {"PYTHONUNBUFFERED": "1"},
  "cwd": "$PROJECT_DIR"
}
ENDJSON
)"
    echo "Registered $MCP_NAME (stdio, scope=$SCOPE)"
    echo "  command: $PYTHON -m src.mcp_server --transport stdio"
    echo "  cwd:     $PROJECT_DIR"
    echo ""
    echo "Restart Claude Code session to activate."
}

# --- Unregister ---
unregister() {
    claude mcp remove "$MCP_NAME" -s "$SCOPE" 2>/dev/null || true
    echo "Removed $MCP_NAME from Claude Code (scope=$SCOPE)"
}

# --- HTTP background server ---
start() {
    if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
        echo "Already running (PID $(cat "$PIDFILE"))"
        return 0
    fi
    echo "Starting $MCP_NAME HTTP server on $HOST:$PORT ..."
    cd "$PROJECT_DIR"
    PYTHONUNBUFFERED=1 nohup "$PYTHON" -m src.mcp_server \
        --transport http --host "$HOST" --port "$PORT" \
        > "$LOGFILE" 2>&1 &
    echo $! > "$PIDFILE"

    MCP_URL="http://${HOST}:${PORT}/mcp"
    for _ in $(seq 1 30); do
        HTTP_CODE=$(curl -sf -o /dev/null -w "%{http_code}" -X POST "$MCP_URL" -m 3 2>/dev/null || true)
        if [ -n "$HTTP_CODE" ] && [ "$HTTP_CODE" != "000" ]; then
            echo "Ready (PID $(cat "$PIDFILE")) — $MCP_URL"
            # Register HTTP transport
            claude mcp remove "$MCP_NAME" -s "$SCOPE" 2>/dev/null || true
            claude mcp add -s "$SCOPE" -t http "$MCP_NAME" "$MCP_URL" 2>/dev/null
            echo "Registered $MCP_NAME (http, scope=$SCOPE)"
            return 0
        fi
        sleep 1
    done
    echo "Warning: server started but health check timed out. Check $LOGFILE"
}

stop() {
    if [ ! -f "$PIDFILE" ]; then
        echo "Not running"
        return 0
    fi
    PID=$(cat "$PIDFILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo "Stopping PID $PID ..."
        kill "$PID"
        sleep 2
        kill -0 "$PID" 2>/dev/null && kill -9 "$PID" 2>/dev/null
        echo "Stopped"
    else
        echo "Stale PID file, cleaning up"
    fi
    rm -f "$PIDFILE"
}

status() {
    echo "=== Claude Code MCP ==="
    claude mcp get "$MCP_NAME" 2>&1 || echo "  Not registered"
    echo ""
    echo "=== HTTP Server ==="
    if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
        echo "  Running (PID $(cat "$PIDFILE"))"
        MCP_URL="http://${HOST}:${PORT}/mcp"
        HTTP_CODE=$(curl -sf -o /dev/null -w "%{http_code}" -X POST "$MCP_URL" -m 2 2>/dev/null || true)
        [ -n "$HTTP_CODE" ] && [ "$HTTP_CODE" != "000" ] \
            && echo "  Endpoint OK ($HTTP_CODE)" \
            || echo "  Endpoint not responding"
    else
        echo "  Not running (stdio mode doesn't need it)"
    fi
}

restart() {
    stop
    start
}

# --- Register Docker HTTP mode ---
# Usage:
#   WSM_API_KEY=wsm_xxx ./scripts/mcp-server.sh docker-register
docker_register() {
    local DOCKER_HOST="${DOCKER_MCP_HOST:-127.0.0.1}"
    local DOCKER_PORT="${DOCKER_MCP_PORT:-8897}"
    local API_KEY="${WSM_API_KEY:-}"
    local MCP_URL="http://${DOCKER_HOST}:${DOCKER_PORT}/mcp"

    claude mcp remove "$MCP_NAME" -s "$SCOPE" 2>/dev/null || true

    if [ -n "$API_KEY" ]; then
        claude mcp add-json -s "$SCOPE" "$MCP_NAME" "$(cat <<ENDJSON
{
  "type": "http",
  "url": "$MCP_URL",
  "headers": {"Authorization": "Bearer $API_KEY"}
}
ENDJSON
)"
        echo "Registered $MCP_NAME (http+auth, scope=$SCOPE)"
    else
        claude mcp add -s "$SCOPE" -t http "$MCP_NAME" "$MCP_URL" 2>/dev/null
        echo "Registered $MCP_NAME (http, no auth, scope=$SCOPE)"
        echo "  ⚠ No WSM_API_KEY set. Create one via Admin panel and re-register."
    fi
    echo "  url: $MCP_URL"
    echo ""
    echo "Restart Claude Code session to activate."
}

# --- Update (unregister + re-register) ---
update() {
    echo "Updating $MCP_NAME in Claude Code ..."
    unregister
    register
    echo "Done. Restart Claude Code session to activate."
}

docker_update() {
    echo "Updating $MCP_NAME (Docker) in Claude Code ..."
    unregister
    docker_register
    echo "Done. Restart Claude Code session to activate."
}

case "${1:-register}" in
    register)        register        ;;
    unregister)      unregister      ;;
    start)           start           ;;
    stop)            stop            ;;
    status)          status          ;;
    restart)         restart         ;;
    update)          update          ;;
    docker-register) docker_register ;;
    docker-update)   docker_update   ;;
    *)
        echo "Usage: $0 {register|unregister|start|stop|status|restart|update|docker-register|docker-update}"
        echo ""
        echo "  register         Register stdio MCP to Claude Code (recommended)"
        echo "  unregister       Remove MCP from Claude Code"
        echo "  start            Start HTTP background server + register"
        echo "  stop             Stop HTTP background server"
        echo "  status           Show registration and server status"
        echo "  restart          Restart HTTP background server"
        echo "  update           Unregister + re-register stdio MCP"
        echo "  docker-register  Register Docker HTTP MCP (set WSM_API_KEY for auth)"
        echo "  docker-update    Unregister + re-register Docker HTTP MCP"
        ;;
esac

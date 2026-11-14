#!/usr/bin/env bash
# AI Workforce OS Startup Script
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$DIR"

mkdir -p "$DIR/data" "$DIR/logs"
PID_FILE="$DIR/data/os.pid"
LOG_FILE="$DIR/logs/os.log"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "AI Workforce OS is already running (PID: $PID) at http://127.0.0.1:8765"
        exit 0
    else
        rm -f "$PID_FILE"
    fi
fi

echo "Starting AI Workforce OS on http://127.0.0.1:8765..."
nohup ~/.local/bin/uv run uvicorn core.app:app --host 127.0.0.1 --port 8765 > "$LOG_FILE" 2>&1 &
OS_PID=$!
echo "$OS_PID" > "$PID_FILE"

# Wait for health check
sleep 2
for i in {1..15}; do
    if curl -s http://127.0.0.1:8765/api/health | grep -q "healthy"; then
        echo "✓ AI Workforce OS is live and healthy (PID: $OS_PID)!"
        echo "  Web Control Interface: http://127.0.0.1:8765"
        exit 0
    fi
    sleep 1
done

echo "⚠ Warning: OS started but did not respond to health check within 15 seconds. Check $LOG_FILE"

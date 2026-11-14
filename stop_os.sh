#!/usr/bin/env bash
# AI Workforce OS Graceful Shutdown Script
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
PID_FILE="$DIR/data/os.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "AI Workforce OS is not running (no PID file found)."
    exit 0
fi

PID=$(cat "$PID_FILE")
if ps -p "$PID" > /dev/null 2>&1; then
    echo "Stopping AI Workforce OS (PID: $PID)..."
    kill "$PID" || true
    sleep 1
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "Process did not terminate; forcing shutdown..."
        kill -9 "$PID" || true
    fi
    rm -f "$PID_FILE"
    echo "✓ AI Workforce OS stopped."
else
    echo "AI Workforce OS process $PID is no longer active."
    rm -f "$PID_FILE"
fi

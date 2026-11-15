#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$DIR"

for pidfile in .runtime/worker.pid .runtime/ollama.pid data/os.pid; do
  if [ -f "$pidfile" ]; then
    PID=$(cat "$pidfile")
    if ps -p "$PID" > /dev/null 2>&1; then
      echo "Stopping PID $PID ($pidfile)..."
      kill "$PID" 2>/dev/null || true
    fi
    rm -f "$pidfile"
  fi
done

lsof -ti:8765 | xargs kill -9 2>/dev/null || true
echo "✓ AI Workforce OS stopped."

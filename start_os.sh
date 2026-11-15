#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$DIR"

mkdir -p .runtime logs data

# 1. Start Ollama if installed and not already running
if command -v ollama >/dev/null 2>&1; then
  if ! curl -sf http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
    echo "Starting local Ollama server..."
    nohup ollama serve > .runtime/ollama.log 2>&1 &
    echo $! > .runtime/ollama.pid
    sleep 2
  fi
fi

# 2. Check if local worker is already running on port 8765
if curl -sf http://127.0.0.1:8765/health >/dev/null 2>&1; then
  echo "✓ Local Worker & Bridge is already running at http://127.0.0.1:8765"
  exit 0
fi

# 3. Start local worker on 8765
echo "Starting AI Workforce OS Local Worker & Bridge on http://127.0.0.1:8765..."
PYTHON_BIN="$DIR/.venv/bin/python"
if [ ! -f "$PYTHON_BIN" ]; then
  PYTHON_BIN="python3"
fi

nohup "$PYTHON_BIN" -m uvicorn core.hybrid.runtime_worker:app --host 127.0.0.1 --port 8765 > .runtime/worker.log 2>&1 &
WORKER_PID=$!
echo "$WORKER_PID" > .runtime/worker.pid
echo "$WORKER_PID" > data/os.pid

sleep 2
if curl -sf http://127.0.0.1:8765/health >/dev/null 2>&1; then
  echo "✓ AI Workforce OS Local Worker is live at http://127.0.0.1:8765"
  exit 0
else
  echo "⚠ Worker started with PID $WORKER_PID, checking logs in .runtime/worker.log"
fi

#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "Starting Backend..."
cd "$ROOT/backend"
source venv/bin/activate
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
BACKEND_PID=$!

echo "Starting Frontend..."
cd "$ROOT/frontend"
nohup npm run dev -- --port 5173 > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!

sudo systemctl start ollama
ollama run qwen2.5:14b

echo ""
echo "Backend:  http://localhost:8000  (log: /tmp/backend.log)"
echo "Frontend: http://localhost:5173  (log: /tmp/frontend.log)"
echo ""
echo "Press Ctrl+C to stop both."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait

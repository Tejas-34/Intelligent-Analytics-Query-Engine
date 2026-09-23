#!/bin/sh
set -e

# Default ports and settings
PORT=${PORT:-8501}
API_PORT=${API_PORT:-8000}
export API_URL=${API_URL:-http://127.0.0.1:$API_PORT}

echo "=========================================="
echo " Starting Intelligent Analytics Engine    "
echo " Backend Internal Port: $API_PORT         "
echo " Frontend External Port: $PORT            "
echo " API URL: $API_URL                        "
echo "=========================================="

# Start FastAPI backend in background
python3 -m uvicorn app.main:app --host 127.0.0.1 --port "$API_PORT" &
BACKEND_PID=$!

# Trap termination signals to stop both services gracefully
cleanup() {
    echo "Received termination signal. Stopping backend (PID: $BACKEND_PID)..."
    kill -TERM "$BACKEND_PID" 2>/dev/null || true
    wait "$BACKEND_PID" 2>/dev/null || true
    exit 0
}
trap cleanup SIGINT SIGTERM

# Wait for backend health check
echo "Waiting for backend service to become ready..."
MAX_RETRIES=30
RETRY_COUNT=0
until python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:$API_PORT/health')" 2>/dev/null; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ "$RETRY_COUNT" -ge "$MAX_RETRIES" ]; then
        echo "Error: Backend failed to start within timeout."
        kill -9 "$BACKEND_PID" 2>/dev/null || true
        exit 1
    fi
    sleep 0.5
done
echo "Backend is healthy and ready."

# Launch Streamlit frontend in foreground
echo "Launching Streamlit UI..."
exec streamlit run app/frontend.py \
    --server.port "$PORT" \
    --server.address 0.0.0.0 \
    --server.headless true \
    --browser.gatherUsageStats false

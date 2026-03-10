#!/bin/bash
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"

# Load API key from .env if it exists
if [ -f "$DIR/.env" ]; then
    export $(grep -v '^#' "$DIR/.env" | xargs)
fi

if [ -z "$OPENROUTER_API_KEY" ]; then
    echo "Error: OPENROUTER_API_KEY not set. Create a .env file or export it."
    exit 1
fi

# Start the Python server in the background
echo "Starting server on port 8787..."
cd "$DIR/server"
source .venv/bin/activate
uvicorn main:app --host 127.0.0.1 --port 8787 &
SERVER_PID=$!

# Wait for server to be ready
for i in $(seq 1 10); do
    if curl -s http://localhost:8787/docs > /dev/null 2>&1; then
        break
    fi
    sleep 0.5
done

echo "Server running (PID $SERVER_PID)"

# Start the Swift hotkey app
echo "Starting hotkey listener..."
cd "$DIR/baldur-assist"
./baldur-assist

# Clean up server when Swift app exits
kill $SERVER_PID 2>/dev/null

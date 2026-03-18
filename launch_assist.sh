#!/bin/bash
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"

# Load shared configuration
source "$DIR/config.sh"

# Parse CLI arguments
VOICE_CLONE_FLAG=""
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --voice-clone)
            VOICE_CLONE_FLAG="--voice-clone"
            echo "Voice cloning enabled"
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--voice-clone]"
            exit 1
            ;;
    esac
    shift
done

# Load API key from .env if it exists
if [ -f "$DIR/server/.env" ]; then
    export $(grep -v '^#' "$DIR/server/.env" | xargs)
elif [ -f "$DIR/.env" ]; then
    export $(grep -v '^#' "$DIR/.env" | xargs)
fi

if [ -z "$OPENROUTER_API_KEY" ]; then
    echo "Error: OPENROUTER_API_KEY not set. Create a .env file or export it."
    exit 1
fi

# Start the Python server in the background
echo "Starting server on port $SERVER_PORT..."
source "$DIR/.venv/bin/activate"
cd "$DIR/server"
python main.py $VOICE_CLONE_FLAG &
SERVER_PID=$!

# Wait for server to be ready
for i in $(seq 1 $STARTUP_RETRY_COUNT); do
    if curl -s "$SERVER_HEALTH_URL" > /dev/null 2>&1; then
        break
    fi
    sleep $STARTUP_RETRY_DELAY
done

echo "Server running (PID $SERVER_PID)"

# Clean up server on exit (Ctrl+C or normal exit)
cleanup() {
    echo "Shutting down server..."
    kill $SERVER_PID 2>/dev/null
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# Start the Swift hotkey app
echo "Starting hotkey listener..."
cd "$DIR/baldur-assist"
./baldur-assist

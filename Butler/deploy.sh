#!/bin/bash

# === LOAD FROM .env IF EXISTS ===
if [ -f ".env" ]; then
  export $(grep -v '^#' .env | xargs)
fi

# === CONFIGURATION (env vars with fallbacks) ===
VENV_DIR="${VENV_DIR:-./venv}"
APP_ENTRY="${APP_ENTRY:-app:app}"
DEFAULT_PORT="${PORT:-9999}"
LOG_FILE="${LOG_FILE:-chat.log}"

PORT="${1:-$DEFAULT_PORT}"

# 1. Ensure venv exists
if [ ! -d "$VENV_DIR" ]; then
  echo "[+] Virtual environment not found. Creating one at $VENV_DIR..."
  python3 -m venv "$VENV_DIR"
fi

# 2. Activate venv
echo "[+] Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# 3. Install dependencies
if [ -f "requirements.txt" ]; then
  echo "[+] Installing dependencies from requirements.txt..."
  pip install --upgrade pip
  pip install -r requirements.txt
else
  echo "[!] requirements.txt not found — skipping dependency install"
fi

# 4. Kill existing process on this port
echo "[+] Checking for existing server instance..."
# CURRENT_DIR=$(pwd)
PIDS=$(lsof -i :$PORT -sTCP:LISTEN -t)

for PID in $PIDS; do
#   CMD=$(ps -p $PID -o comm=)
#   FULL_CMD=$(ps -p $PID -o args=)

#   if [[ "$CMD" == "python"* ]] && [[ "$FULL_CMD" == *"uvicorn"* ]] && [[ "$FULL_CMD" == *"$CURRENT_DIR"* ]]; then
  echo "[x] Killing process on port $PORT (PID: $PID)"
  kill -9 $PID
#   else
#     echo "[~] Skipping unrelated process (PID: $PID)"
#   fi
done

# 4. Kill existing uvicorn process on this port
# echo "[+] Stopping existing uvicorn server on port $PORT..."
# pkill -f 'uvicorn app:app'

# 5. Start the FastAPI app in background
echo "[+] Starting FastAPI server from $APP_ENTRY on port $PORT..."

nohup uvicorn "$APP_ENTRY" --host 0.0.0.0 --port "$PORT" >> "$LOG_FILE" 2>&1 &

echo "[✔] Server started successfully"

echo "[ℹ] Access the app at http://localhost:$PORT"
echo "[ℹ] To stop the server, run: pkill -f 'uvicorn $APP_ENTRY'"
echo "[ℹ] To view logs, run: tail -f $LOG_FILE"
 
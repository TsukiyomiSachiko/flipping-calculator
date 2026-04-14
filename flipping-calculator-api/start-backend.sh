#!/bin/bash
# start-backend.sh
# Starts the FastAPI backend in WSL with venv
# Run from WSL: ./start-backend.sh

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$SCRIPT_DIR"

PORT=8000

echo ""
echo "========================================"
echo "  OSRS Flip - Backend API Server (WSL)"
echo "========================================"
echo ""
echo "Port:         $PORT"

# Get WSL IP address
WSL_IP=$(ip addr show eth0 2>/dev/null | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | head -1)
if [ -z "$WSL_IP" ]; then
    WSL_IP=$(hostname -I | awk '{print $1}')
fi

echo ""
echo "API accessible at:"
echo "  http://localhost:$PORT"
if [ -n "$WSL_IP" ]; then
    echo "  http://${WSL_IP}:${PORT}"
    echo "  http://${WSL_IP}:${PORT}/docs  (Swagger UI)"
fi
echo ""

# --- Check venv exists ---
cd "$PROJECT_DIR"

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create venv. Is Python 3 installed?"
        echo "Install with: sudo apt install python3 python3-venv python3-pip"
        exit 1
    fi
fi

if [ ! -f "venv/bin/uvicorn" ]; then
    echo "Installing dependencies..."
    source venv/bin/activate
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install dependencies."
        exit 1
    fi
    echo "Dependencies installed."
fi

# --- Activate venv ---
echo "Activating virtual environment..."
source venv/bin/activate
echo "Venv activated."

echo ""
echo "Starting FastAPI server... (Ctrl+C to stop)"
echo "========================================"
echo ""

# --- Start the server ---
trap 'echo -e "\n========================================\n  Shutting down...\n========================================"; deactivate; echo -e "\nCleanup complete. Goodbye!\n"; exit' INT TERM

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port $PORT

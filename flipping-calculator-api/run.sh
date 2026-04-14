#!/bin/bash

# OSRS Flipping Calculator API - Startup Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Starting OSRS Flipping Calculator API..."
echo "========================================"
echo ""

# Check if virtual environment exists, create if not
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create virtual environment. Make sure python3-venv is installed:"
        echo "   sudo apt install python3-venv"
        exit 1
    fi
fi

# Use venv binaries directly (more reliable than source activate)
PIP="./venv/bin/pip"
UVICORN="./venv/bin/uvicorn"

# Install/update dependencies
echo "Installing dependencies..."
$PIP install -r requirements.txt --quiet
if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies."
    exit 1
fi

echo ""
echo "========================================"
echo "API Server Starting..."
echo "========================================"
echo ""
echo "📍 API: http://localhost:8000"
echo "📖 Docs: http://localhost:8000/docs"
echo "📚 ReDoc: http://localhost:8000/redoc"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Start the server using the venv's uvicorn directly
$UVICORN app.main:app --reload --host 0.0.0.0 --port 8000
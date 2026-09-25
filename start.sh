#!/bin/bash

# ==============================================================================
# Aero ATS - Unified Startup Script
# ==============================================================================

echo "🚀 Starting Aero ATS locally..."

# Function to handle cleanup on script exit
cleanup() {
    echo -e "\n🛑 Stopping services..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
    fi
    exit 0
}

# Register the cleanup function for when Ctrl+C is pressed
trap cleanup SIGINT SIGTERM

# 1. Start the FastAPI Backend
echo "📦 Starting FastAPI backend on port 8000..."
source venv/bin/activate
PYTHONPATH=. uvicorn src.api.main:app --reload --port 8000 &
BACKEND_PID=$!

# Wait a moment to ensure backend starts
sleep 2

# 2. Start the Vite Frontend
echo "💻 Starting Vite frontend..."
cd frontend
npm run dev

# (When Vite is closed by Ctrl+C, the trap will trigger and kill the backend)

#!/bin/bash

# Brain-AI Production Stop Script
# Version: 4.5.0

echo "🛑 Stopping Brain-AI Production Services..."
echo ""

# Read PIDs if file exists
if [ -f brain-ai.pids ]; then
    source brain-ai.pids
    
    # Stop services by PID
    if [ ! -z "$OCR_PID" ]; then
        echo "Stopping OCR Service (PID: $OCR_PID)..."
        kill $OCR_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$API_PID" ]; then
        echo "Stopping REST API (PID: $API_PID)..."
        kill $API_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$GUI_PID" ]; then
        echo "Stopping GUI (PID: $GUI_PID)..."
        kill $GUI_PID 2>/dev/null || true
    fi
    
    rm brain-ai.pids
fi

# Fallback: kill by process name
echo "Cleaning up any remaining processes..."
pkill -f "uvicorn.*8000" 2>/dev/null || true
pkill -f "uvicorn.*5001" 2>/dev/null || true
pkill -f "serve.*dist" 2>/dev/null || true

echo ""
echo "✅ All services stopped"

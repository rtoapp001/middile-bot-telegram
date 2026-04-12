#!/bin/bash

# 🤖 Bot Auto-Restart Script for 24/7 Uptime

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "📍 Project directory: $PROJECT_DIR"
echo "🚀 Starting Telegram Bot with auto-restart..."

# Create logs directory if it doesn't exist
mkdir -p logs

# Run bot with auto-restart
while true; do
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ▶️  Starting bot..."
    python3 main_bot.py
    
    EXIT_CODE=$?
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ Bot exited with code $EXIT_CODE"
    
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⏳ Waiting 10 seconds before restart..."
    sleep 10
done

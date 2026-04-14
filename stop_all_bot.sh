#!/usr/bin/env sh
cd "$(dirname "$0")"

echo "Stopping all bot instances and disabling auto-start..."
python3 reset.py --disable

if [ $? -eq 0 ]; then
  echo "Done. Bot is disabled until you run 'python3 reset.py --enable' or remove bot_disabled.lock."
else
  echo "Failed to stop the bot. Check reset.py output for details."
fi

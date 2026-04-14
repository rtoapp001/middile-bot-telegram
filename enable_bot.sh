#!/usr/bin/env sh
cd "$(dirname "$0")"

echo "Re-enabling bot startup..."
python3 reset.py --enable

if [ $? -eq 0 ]; then
  echo "Done. You can now start the bot again with 'python3 main_bot.py'."
else
  echo "Failed to enable the bot. Check reset.py output for details."
fi

# Telegram APK Processing Automation System

This system automates APK processing using Telegram bots and Firebase Storage.

## Workflow

1. User sends a code like "U12345" to the main bot
2. Bot looks up the Firebase URL for that code
3. Downloads the APK from Firebase
4. Userbot sends the APK to @android_protect_bot
5. Waits for the processed APK response
6. Sends the processed APK back to the user

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Create a `.env` file based on `.env.example`:
   - `BOT_TOKEN`: Token for your main bot from @BotFather
   - `API_ID` and `API_HASH`: From https://my.telegram.org/
   - `TARGET_BOT_USERNAME`: @android_protect_bot

3. Update the mapping in `firebase_handler.py` with actual Firebase download URLs

4. Run the system:
   ```
   python main_bot.py
   ```

5. On first run, Telethon will prompt for phone number and login code

## Features

- **Queue System**: FIFO processing of requests
- **Multiple Users**: Handles multiple users simultaneously via queue
- **Async Processing**: Full async implementation
- **Error Handling**: Timeouts, network errors, logging
- **File Management**: Automatic download/upload and cleanup
- **Firebase Integration**: Direct download from Firebase URLs

## Project Structure

- `main_bot.py`: Aiogram bot for user interaction
- `userbot.py`: Telethon userbot for backend processing
- `bridge.py`: Communication layer with queue system
- `firebase_handler.py`: Firebase download handling
- `config.py`: Configuration management
- `requirements.txt`: Dependencies

## Notes

- Requests are processed sequentially to avoid response mix-ups
- Timeout for target bot response: 60 seconds
- Temporary files are cleaned up automatically
- Logging is enabled for debugging
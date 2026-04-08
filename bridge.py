import asyncio
import tempfile
import os
from telethon import events
import userbot
from config import TARGET_BOT_USERNAME

# 🔥 Per-user queues
user_queues = {}  # user_id -> asyncio.Queue()

# 🔥 Global response queue
responses_queue = None

async def init():
    global responses_queue
    responses_queue = asyncio.Queue()

# 🔥 Handle incoming file from target bot
async def setup_handler():
    @userbot.client.on(events.NewMessage(from_users=TARGET_BOT_USERNAME))
    async def handler(event):
        if not event.message.file:
            return

        # 🔥 Get first waiting user safely
        for user_id, queue in user_queues.items():
            if not queue.empty():
                request_id = await queue.get()

                fd, path = tempfile.mkstemp(suffix=".apk")
                os.close(fd)

                await event.download_media(path)

                await responses_queue.put((user_id, path))
                return

# 🔥 Send request
async def send_apk(file_path, user_id):
    if user_id not in user_queues:
        user_queues[user_id] = asyncio.Queue()

    await user_queues[user_id].put(file_path)

    # 🔥 send file to target bot
    await userbot.client.send_file(TARGET_BOT_USERNAME, file_path)

# 🔥 Worker not needed anymore (direct send)
async def start_worker():
    await init()
    await setup_handler()
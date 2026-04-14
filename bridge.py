import asyncio
import tempfile
import os
import logging
from telethon import events
import userbot
from config import TARGET_BOT_USERNAME, BOT_TOKEN

logger = logging.getLogger(__name__)

# 🔥 Pending request tracking
pending_request_order = []  # FIFO list of request_ids waiting for file response
request_to_user = {}  # request_id -> user_id

# 🔥 Global response queues
responses_queue = None
status_queue = None  # For queue position updates

async def init():
    global responses_queue, status_queue
    responses_queue = asyncio.Queue()
    status_queue = asyncio.Queue()

# 🔥 Handle incoming messages from target bot
async def setup_handler():
    bot = None
    try:
        from aiogram import Bot
        bot = Bot(token=BOT_TOKEN)
    except:
        logger.warning("Could not import Bot for status updates")
    
    async def _process_target_message(event):
        text = event.message.text.strip() if event.message and event.message.text else None
        logger.info(f"📨 Message from {TARGET_BOT_USERNAME}: {text if text else '[FILE]'}")
        
        # 🔥 CASE 1: File received (APK)
        if event.message and event.message.file:
            logger.info("📦 APK file received")
            
            if not pending_request_order:
                logger.warning("⚠️ Received APK file but no pending request exists")
                return

            request_id = pending_request_order.pop(0)
            user_id = request_to_user.pop(request_id, None)

            try:
                fd, path = tempfile.mkstemp(suffix=".apk")
                os.close(fd)
                await event.download_media(path)
                logger.info(f"✅ APK downloaded for user {user_id} (Request #{request_id})")
                await responses_queue.put((request_id, user_id, path))
            except Exception as e:
                logger.error(f"❌ Error downloading APK for request {request_id}: {e}")
            return

        # 🔥 CASE 2: Text message (Queue position, status, etc.)
        if text:
            logger.info(f"📝 Text message from bot: {text}")
            if not pending_request_order:
                logger.warning("⚠️ Received status update but no pending request exists")
                return

            request_id = pending_request_order[0]
            user_id = request_to_user.get(request_id)
            logger.info(f"📤 Sending status to user {user_id} (Request #{request_id}): {text}")

            if request_id is not None:
                try:
                    from database import db
                    db.update_request_status(request_id, "in_queue", queue_message=text)
                except Exception as e:
                    logger.warning(f"⚠️ Could not update queue status in database for request {request_id}: {e}")

            await status_queue.put((request_id, user_id, text))

    @userbot.client.on(events.NewMessage(from_users=TARGET_BOT_USERNAME))
    @userbot.client.on(events.MessageEdited(from_users=TARGET_BOT_USERNAME))
    async def handler(event):
        await _process_target_message(event)

# 🔥 Send request to android_protect_bot
async def send_apk(file_path, user_id, request_id=None):
    if request_id is None:
        logger.warning("⚠️ send_apk called without request_id")
    else:
        request_to_user[request_id] = user_id
        pending_request_order.append(request_id)
    
    logger.info(f"📤 Sending APK to {TARGET_BOT_USERNAME} for user {user_id} (Request #{request_id})")
    
    try:
        await userbot.client.send_file(TARGET_BOT_USERNAME, file_path)
    except Exception as e:
        logger.error(f"❌ Error sending APK for request {request_id}: {e}")
        if request_id is not None and request_id in pending_request_order:
            pending_request_order.remove(request_id)
            request_to_user.pop(request_id, None)

# 🔥 Handler for status messages
async def start_status_listener():
    """Listen for status updates and send to users"""
    from aiogram import Bot
    bot = Bot(token=BOT_TOKEN)
    
    logger.info("🔔 Status listener started")
    while True:
        try:
            user_id, message = await status_queue.get()
            
            try:
                logger.info(f"📨 Sending status to user {user_id}: {message}")
                await bot.send_message(user_id, message, parse_mode="HTML")
            except Exception as e:
                logger.error(f"❌ Error sending status to {user_id}: {e}")
        except Exception as e:
            logger.error(f"❌ Error in status listener: {e}")
            await asyncio.sleep(5)

# 🔥 Worker - start both handlers
async def start_worker():
    await init()
    await setup_handler()
    logger.info("🚀 Bridge workers started")
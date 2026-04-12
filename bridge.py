import asyncio
import tempfile
import os
import logging
from telethon import events
import userbot
from config import TARGET_BOT_USERNAME, BOT_TOKEN

logger = logging.getLogger(__name__)

# 🔥 Per-user queues with tracking
user_queues = {}  # user_id -> {'queue': asyncio.Queue(), 'timestamp': time}
pending_requests = {}  # file_name -> user_id (for tracking which file belongs to which user)
user_to_request = {}  # user_id -> request_id (for tracking requests)

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
    
    @userbot.client.on(events.NewMessage(from_users=TARGET_BOT_USERNAME))
    async def handler(event):
        logger.info(f"📨 Message from {TARGET_BOT_USERNAME}: {event.message.text if event.message.text else '[FILE]'}")
        
        # 🔥 CASE 1: File received (APK)
        if event.message.file:
            logger.info("📦 APK file received")
            
            # Get first waiting user
            for user_id, data in list(user_queues.items()):
                queue = data['queue']
                if not queue.empty():
                    try:
                        file_info = await queue.get()
                        
                        fd, path = tempfile.mkstemp(suffix=".apk")
                        os.close(fd)
                        
                        await event.download_media(path)
                        logger.info(f"✅ APK downloaded for user {user_id}")
                        
                        await responses_queue.put((user_id, path))
                        
                        # Mark request as completed in database
                        if user_id in user_to_request:
                            from database import db
                            request_id = user_to_request[user_id]
                            db.complete_request(request_id)
                            del user_to_request[user_id]
                        
                        # Clean up
                        if user_id in user_queues:
                            del user_queues[user_id]
                        return
                    except Exception as e:
                        logger.error(f"❌ Error downloading APK: {e}")
                        return
        
        # 🔥 CASE 2: Text message (Queue position, status, etc.)
        if event.message.text:
            text = event.message.text.strip()
            logger.info(f"📝 Text message from bot: {text}")
            
            # Find which user this status is for
            for user_id in list(user_queues.keys()):
                logger.info(f"📤 Sending status to user {user_id}: {text}")
                await status_queue.put((user_id, text))
                break

# 🔥 Send request to android_protect_bot
async def send_apk(file_path, user_id, request_id=None):
    if user_id not in user_queues:
        user_queues[user_id] = {'queue': asyncio.Queue(), 'timestamp': None}
    
    await user_queues[user_id]['queue'].put(file_path)
    
    # Track request_id for later completion
    if request_id:
        user_to_request[user_id] = request_id
    
    logger.info(f"📤 Sending APK to {TARGET_BOT_USERNAME} for user {user_id}")
    
    try:
        await userbot.client.send_file(TARGET_BOT_USERNAME, file_path)
    except Exception as e:
        logger.error(f"❌ Error sending APK: {e}")

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
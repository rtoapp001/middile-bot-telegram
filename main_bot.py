import asyncio
import os
import logging
import sqlite3
import time
import signal
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils.exceptions import TerminatedByOtherGetUpdates

from config import BOT_TOKEN, ADMIN_ID
from firebase_handler import download_apk
import bridge
from bridge import send_apk, start_worker
from userbot import start_userbot
from database import db
from rate_limiter import rate_limiter
from ui_helper import ui, formatter, notifications

# 📝 Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

AI_REPLY = "🤖 Your APK has been queued. Please wait 5 minutes..."

# Pending status messages to delete when APK is ready
pending_user_messages = {}  # user_id -> list[tuple[chat_id, message_id]]
last_status_message = {}  # user_id -> (chat_id, message_id)

# 🔥 Save leads
def save_lead(user):
    with open("leads.txt", "a") as f:
        f.write(f"{user.id},{user.username}\n")


# ✅ START COMMAND
@dp.message_handler(commands=["start"])
async def start_cmd(message: types.Message):
    user = message.from_user
    
    # Add to database
    db.add_user(user.id, user.username, user.first_name, user.last_name or "")
    save_lead(user)
    
    welcome_text = formatter.format_welcome_message(user.first_name or "User")
    await message.answer(welcome_text, reply_markup=ui.get_start_keyboard(), parse_mode="HTML")
    logger.info(f"👤 New/returning user: {user.id} - {user.username}")


# ✅ HELP COMMAND
@dp.message_handler(commands=["help"])
async def help_cmd(message: types.Message):
    await message.answer(ui.get_help_message(), parse_mode="Markdown")


# ✅ ABOUT COMMAND
@dp.message_handler(commands=["about"])
async def about_cmd(message: types.Message):
    await message.answer(ui.get_about_message(), parse_mode="Markdown")


# ✅ STATS COMMAND
@dp.message_handler(commands=["stats"])
async def stats_cmd(message: types.Message):
    user_id = message.from_user.id
    stats = db.get_user_stats(user_id)
    
    if stats:
        stats_text = formatter.format_welcome_message(message.from_user.first_name) + "\n" + ui.get_stats_message(stats)
        await message.answer(stats_text, reply_markup=ui.get_stats_keyboard(), parse_mode="HTML")
    else:
        await message.answer("❌ कोई data नहीं\n\n(No stats available)", reply_markup=ui.get_stats_keyboard())


# ✅ ADMIN STATS COMMAND
@dp.message_handler(commands=["admin"])
async def admin_cmd(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply("❌ Admin only")
        return
    
    stats = db.get_admin_stats()
    admin_text = f"""
📊 <b>Bot Analytics</b>

👥 Total Users: {stats.get('total_users', 0)}
📥 Total Downloads: {stats.get('total_downloads', 0)}
⏳ Pending Requests: {stats.get('pending_requests', 0)}
⏱️ Avg Time: {stats.get('avg_time_minutes', 0)} minutes

Last Update: Just now
"""
    await message.answer(admin_text, reply_markup=ui.get_admin_keyboard(), parse_mode="HTML")


# ✅ MAIN HANDLER
@dp.message_handler()
async def handle(message: types.Message):
    user_id = message.from_user.id
    code = message.text.strip().upper()

    # Validate code format
    if not code.startswith("U") or len(code) < 5:
        await message.reply(
            "❌ Invalid code format\n\n"
            "Correct: U12345\n"
            "/help for more info",
            reply_markup=ui.get_start_keyboard()
        )
        return
    
    # Check if user is blocked
    if db.is_user_blocked(user_id):
        await message.reply("🚫 You have been blocked from using this bot")
        logger.warning(f"⛔ Blocked user {user_id} tried to access")
        return
    
    # Check rate limits
    allowed, limit_msg = rate_limiter.check_rate_limit(user_id)
    if not allowed:
        await message.reply(limit_msg)
        logger.warning(f"⚠️ Rate limit triggered for user {user_id}")
        return
    
    # Create request in database
    request_id = db.create_request(user_id, code)
    
    status_msg = await message.reply(
        formatter.format_processing_message(code),
        parse_mode="HTML"
    )
    pending_user_messages.setdefault(user_id, []).append((message.chat.id, status_msg.message_id))

    try:
        logger.info(f"Processing code {code} from user {user_id} (Request #{request_id})")
        file_path = download_apk(code)

        # Send to android_protect_bot
        await send_apk(file_path, user_id, request_id)
        db.update_request_status(request_id, "in_queue")
        logger.info(f"✅ APK sent for code {code}")

    except Exception as e:
        logger.error(f"Error processing code {code}: {e}", exc_info=True)
        db.update_request_status(request_id, "error")
        await message.reply(formatter.format_error_message(str(e)))


# ✅ CALLBACK HANDLER FOR BUTTONS
@dp.callback_query_handler(lambda c: c.data == "my_stats")
async def callback_stats(call: types.CallbackQuery):
    await stats_cmd(call.message)
    await call.answer()


@dp.callback_query_handler(lambda c: c.data == "help")
async def callback_help(call: types.CallbackQuery):
    await call.message.answer(ui.get_help_message(), parse_mode="Markdown")
    await call.answer()


@dp.callback_query_handler(lambda c: c.data == "about")
async def callback_about(call: types.CallbackQuery):
    await call.message.answer(ui.get_about_message(), parse_mode="Markdown")
    await call.answer()


@dp.callback_query_handler(lambda c: c.data == "get_apk")
async def callback_get_apk(call: types.CallbackQuery):
    await call.message.answer(
        "📱 APK Code भेजो\n\n"
        "Ex: U12345",
        reply_markup=ui.get_start_keyboard()
    )
    await call.answer()


@dp.callback_query_handler(lambda c: c.data == "back")
async def callback_back(call: types.CallbackQuery):
    welcome_text = formatter.format_welcome_message(call.from_user.first_name or "User")
    await call.message.answer(welcome_text, reply_markup=ui.get_start_keyboard(), parse_mode="HTML")
    await call.answer()


@dp.callback_query_handler(lambda c: c.data == "admin_stats")
async def callback_admin_stats(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        await call.answer("❌ Admin only", show_alert=True)
        return
    
    stats = db.get_admin_stats()
    admin_text = f"""
📊 <b>Bot Analytics</b>

👥 Total Users: {stats.get('total_users', 0)}
📥 Total Downloads: {stats.get('total_downloads', 0)}
⏳ Pending Requests: {stats.get('pending_requests', 0)}
⏱️ Avg Time: {stats.get('avg_time_minutes', 0)} minutes

Last Update: Just now
"""
    await call.message.answer(admin_text, parse_mode="HTML")
    await call.answer()


# 🔥 RESPONSE HANDLER (APK Files)
async def response_handler():
    logger.info("📥 Response handler started")
    while True:
        try:
            user_id, file_path = await bridge.responses_queue.get()

            try:
                # Delete previous status/messages before sending final APK
                if user_id in pending_user_messages:
                    for chat_id, msg_id in pending_user_messages[user_id]:
                        try:
                            await bot.delete_message(chat_id, msg_id)
                        except Exception:
                            pass
                    del pending_user_messages[user_id]
                    if user_id in last_status_message:
                        del last_status_message[user_id]

                with open(file_path, "rb") as f:
                    await bot.send_document(
                        user_id, 
                        f,
                        caption="✅ APK तैयार!\n\n📥 Download कीजिए, ऐप इस्तेमाल करने के लिए तैयार है।"
                    )
                    logger.info(f"✅ APK file sent to user {user_id}")
                    
                    # Mark all pending requests as completed
                    # (In production, track request_id separately)
                    db.get_all_users_count()  # Just to log activity

            except Exception as e:
                logger.error(f"Error sending file to {user_id}: {e}")
                await bot.send_message(user_id, "❌ Error sending APK")

            finally:
                if os.path.exists(file_path):
                    os.remove(file_path)
        except Exception as e:
            logger.error(f"Error in response_handler: {e}", exc_info=True)
            await asyncio.sleep(5)


# 🔥 STATUS UPDATE HANDLER
async def status_update_handler():
    """Listen for status updates from android_protect_bot and send to users"""
    logger.info("🔔 Status update handler started")
    while True:
        try:
            user_id, status_message = await bridge.status_queue.get()
            
            try:
                if user_id in last_status_message:
                    chat_id, msg_id = last_status_message[user_id]
                    await bot.edit_message_text(status_message, chat_id=chat_id, message_id=msg_id, parse_mode="HTML")
                    logger.info(f"📝 Updated status message for user {user_id}")
                else:
                    logger.info(f"📨 Sending status update to user {user_id}")
                    status_obj = await bot.send_message(user_id, status_message, parse_mode="HTML")
                    last_status_message[user_id] = (user_id, status_obj.message_id)
                    pending_user_messages.setdefault(user_id, []).append((user_id, status_obj.message_id))
            except Exception as e:
                logger.error(f"❌ Error sending status to {user_id}: {e}")
        except Exception as e:
            logger.error(f"❌ Error in status_update_handler: {e}")
            await asyncio.sleep(5)


# 🔥 BROADCAST
@dp.message_handler(commands=["broadcast"])
async def broadcast(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    text = message.get_args()

    if not os.path.exists("leads.txt"):
        await message.reply("No leads yet")
        return

    with open("leads.txt") as f:
        users = f.readlines()

    for u in users:
        uid = int(u.split(",")[0])
        try:
            await bot.send_message(uid, text)
        except:
            pass

    await message.reply("✅ Broadcast done")


# 🔥 MAIN
from aiogram.utils.exceptions import TerminatedByOtherGetUpdates


async def main():
    try:
        logger.info("⏳ Initializing bot components...")
        await start_userbot()
        await start_worker()
        
        # Start both handlers
        asyncio.create_task(response_handler())
        asyncio.create_task(status_update_handler())
        
        # Clear any webhook and pending updates before polling
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Webhook cleared, pending updates dropped")
        
        # Drop any old updates and start fresh
        await dp.skip_updates()
        logger.info("✅ Old updates skipped")
        
        logger.info("🚀 Bot started successfully")
        await dp.start_polling(relax=0.1, timeout=20, reset_webhook=True)
        
    except asyncio.CancelledError:
        logger.info("✋ Bot shutdown requested")
        raise
    except Exception as e:
        logger.error(f"❌ Error in main loop: {e}", exc_info=True)
        raise


async def run_bot_with_restart():
    """Run bot with automatic restart on crash"""
    restart_delay = 5
    max_delay = 300  # Max 5 minutes
    
    while True:
        try:
            await main()
        except asyncio.CancelledError:
            logger.info("Bot gracefully stopped")
            break
        except TerminatedByOtherGetUpdates as e:
            logger.error("❌ Another bot instance or polling session is active for this token.")
            logger.error(f"🔄 Retrying in {restart_delay}s: {e}")
            await asyncio.sleep(restart_delay)
            restart_delay = min(restart_delay * 1.5, max_delay)
        except sqlite3.OperationalError as e:
            logger.error(f"❌ SQLite operational error: {e}")
            logger.error(f"🔄 Waiting {restart_delay}s before retrying")
            await asyncio.sleep(restart_delay)
            restart_delay = min(restart_delay * 1.5, max_delay)
        except Exception as e:
            logger.error(f"🔄 Bot crashed, restarting in {restart_delay}s: {e}")
            await asyncio.sleep(restart_delay)
            restart_delay = min(restart_delay * 1.5, max_delay)
            logger.info("🔁 Attempting restart...")


if __name__ == "__main__":
    try:
        asyncio.run(run_bot_with_restart())
    except KeyboardInterrupt:
        logger.info("Bot interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
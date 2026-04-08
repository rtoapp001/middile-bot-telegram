import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from config import BOT_TOKEN, ADMIN_ID
from firebase_handler import download_apk
import bridge
from bridge import send_apk, start_worker
from userbot import start_userbot

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

AI_REPLY = "🤖 Your APK has been queued. Please wait 5 minutes..."

# 🔥 Save leads
def save_lead(user):
    with open("leads.txt", "a") as f:
        f.write(f"{user.id},{user.username}\n")

@dp.message_handler(commands=["start"])
async def start_cmd(message: types.Message):
    save_lead(message.from_user)
    await message.reply("👋 Welcome!\nSend code like U12345")

@dp.message_handler()
async def handle(message: types.Message):
    code = message.text.strip()

    if not code.startswith("U"):
        await message.reply("❌ Invalid code")
        return

    await message.reply(AI_REPLY)

    try:
        file_path = await download_apk(code)

        # 🔥 send request
        await send_apk(file_path, message.from_user.id)

    except:
        await message.reply("❌ Error")

# 🔥 Response handler
async def response_handler():
    while True:
        user_id, file_path = await bridge.responses_queue.get()

        try:
            with open(file_path, "rb") as f:
                await bot.send_document(user_id, f)
        except:
            await bot.send_message(user_id, "❌ Send error")
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

# 🔥 Broadcast
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

async def main():
    await start_userbot()
    await start_worker()

    asyncio.create_task(response_handler())

    print("🚀 Bot started")
    await dp.start_polling()

if __name__ == "__main__":
    asyncio.run(main())
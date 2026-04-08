from telethon import TelegramClient
from config import API_ID, API_HASH

client = None

async def start_userbot():
    global client
    client = TelegramClient("session", API_ID, API_HASH)
    await client.start()
    print("✅ Userbot started")
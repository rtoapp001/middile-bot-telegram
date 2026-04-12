import json
from pathlib import Path
from telethon import TelegramClient
from config import API_ID, API_HASH, SESSION_NAME, PHONE, CODE

client = None
META_FILE = Path("session_meta.json")


def _clean_old_session():
    """Delete old session files when credentials change."""
    if not META_FILE.exists():
        return

    try:
        with META_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return

    old_api_id = data.get("API_ID")
    old_api_hash = data.get("API_HASH")
    old_session_name = data.get("SESSION_NAME")
    old_phone = data.get("PHONE")
    old_code = data.get("CODE")

    if old_api_id != API_ID or old_api_hash != API_HASH or old_session_name != SESSION_NAME or old_phone != PHONE or old_code != CODE:
        session_file = Path(f"{SESSION_NAME}.session")
        journal_file = Path(f"{SESSION_NAME}.session-journal")
        if session_file.exists():
            session_file.unlink(missing_ok=True)
        if journal_file.exists():
            journal_file.unlink(missing_ok=True)
        META_FILE.unlink(missing_ok=True)
        print("🧹 Old Telegram session cleared because credentials changed.")


def _save_session_meta():
    try:
        with META_FILE.open("w", encoding="utf-8") as f:
            json.dump({
                "API_ID": API_ID,
                "API_HASH": API_HASH,
                "SESSION_NAME": SESSION_NAME,
                "PHONE": PHONE,
                "CODE": CODE
            }, f)
    except Exception:
        pass


async def start_userbot():
    global client
    _clean_old_session()
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    
    async def code_callback():
        return CODE
    
    if PHONE:
        if CODE:
            await client.start(phone=PHONE, code_callback=code_callback)
        else:
            await client.start(phone=PHONE)
    
    _save_session_meta()
    print("✅ Userbot started")
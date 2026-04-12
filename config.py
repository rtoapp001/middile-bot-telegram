import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
TARGET_BOT_USERNAME = os.getenv("TARGET_BOT_USERNAME")
SESSION_NAME = os.getenv("SESSION_NAME", "session")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
PHONE = os.getenv("PHONE")
CODE = os.getenv("CODE")
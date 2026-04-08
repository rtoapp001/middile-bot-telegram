import aiohttp
import tempfile
import os

FIREBASE_DB_URL = "https://fir-app-buyer-default-rtdb.firebaseio.com/.json"

async def get_mapping():
    async with aiohttp.ClientSession() as session:
        async with session.get(FIREBASE_DB_URL) as resp:
            data = await resp.json()

            # 🔥 FIX: apks ke andar se read karo
            if data and "apks" in data:
                return data["apks"]
            return {}

async def download_apk(code):
    mapping = await get_mapping()

    if code not in mapping:
        raise Exception("Invalid Code")

    url = mapping[code]

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.read()

    fd, path = tempfile.mkstemp(suffix=".apk")
    os.close(fd)

    with open(path, "wb") as f:
        f.write(data)

    return path
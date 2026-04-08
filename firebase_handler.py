import requests
import tempfile
import os

FIREBASE_DB_URL = "https://fir-app-buyer-default-rtdb.firebaseio.com/.json"


def get_mapping():
    resp = requests.get(FIREBASE_DB_URL)
    data = resp.json()

    # 🔥 same logic: apks ke andar se read karo
    if data and "apks" in data:
        return data["apks"]

    return {}


def download_apk(code):
    mapping = get_mapping()

    if code not in mapping:
        raise Exception("Invalid Code")

    url = mapping[code]

    resp = requests.get(url)
    data = resp.content

    fd, path = tempfile.mkstemp(suffix=".apk")
    os.close(fd)

    with open(path, "wb") as f:
        f.write(data)

    return path
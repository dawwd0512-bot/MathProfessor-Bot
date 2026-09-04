import json
import os

MEMORY_FILE = "memory.json"
MAX_HISTORY = 10


def _load():
    if not os.path.exists(MEMORY_FILE):
        return {}

    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def _save(data):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_history(user_id):
    data = _load()
    return data.get(str(user_id), [])


def add_message(user_id, role, text):
    data = _load()

    uid = str(user_id)

    if uid not in data:
        data[uid] = []

    data[uid].append({
        "role": role,
        "text": text
    })

    data[uid] = data[uid][-MAX_HISTORY:]

    _save(data)


def build_history(user_id):
    history = get_history(user_id)

    text = ""

    for msg in history:
        if msg["role"] == "user":
            text += f"المستخدم: {msg['text']}\n"
        else:
            text += f"المساعد: {msg['text']}\n"

    return text

def clear_history(user_id):
    data = _load()

    uid = str(user_id)

    if uid in data:
        del data[uid]
        _save(data)

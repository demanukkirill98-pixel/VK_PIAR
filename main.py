import requests
import time
import os
import json
import threading

# ========== НАСТРОЙКИ ==========
GROUP_TOKEN = "vk1.a.GENAzRdaR86f91rPAydFj660SgWD7ylgOKpjwrrPaDtgE64s3ZSMn02sa_QPL7IKcOsFIEgMK17_DlaTsjXVlpJb-a4eLqQcbEfCA4OnTcqbn5J5cjqwh-eyKrwxFbmdgJSKMY8PgIiwj8DRhOaOU3DvdDchvGw5ebC-ysGXDA9Cyg0-knFBsdhf_o__aoKHrR0RceQB658D-WjG5xBbqg"
GROUP_ID = 239058698
ADMIN_CHAT_ID = 2000000062
OWNER_ID = 835770623
OWNER_LINK = "vk.com/club239058698"

SEND_DELAY = 0.1  # Задержка для проверки (0.1 сек)
SPAM_INTERVAL = 60
CHATS_FILE = "chats.txt"
IDS_FILE = "id.txt"
PIAR_FILE = "piar.txt"

awaiting_reply = {}

VK_URL = "https://api.vk.com/method/"
V = "5.199"

# Список ID, которые уже проверены и недоступны
invalid_chats = set()

def log(msg):
    print(msg, flush=True)

def api(method, params):
    params["access_token"] = GROUP_TOKEN
    params["v"] = V
    try:
        resp = requests.get(VK_URL + method, params=params, timeout=5).json()
        if "error" in resp:
            return resp
        return resp
    except Exception as e:
        return {"error": {"error_msg": str(e)}}

def send_message(peer_id, message, silent=False, keyboard=None, reply_to=None):
    if not message or not message.strip():
        return False
    
    # Проверяем, есть ли ID в списке невалидных
    if str(peer_id) in invalid_chats:
        return False
    
    params = {
        "peer_id": peer_id,
        "message": message,
        "random_id": int(time.time() * 1000000)
    }
    if keyboard:
        params["keyboard"] = json.dumps(keyboard, ensure_ascii=False)
    if reply_to:
        params["reply_to"] = reply_to
    
    resp = api("messages.send", params)
    
    if "error" in resp:
        code = resp["error"].get("error_code")
        msg = resp["error"].get("error_msg", "")
        
        # Если ошибка доступа - добавляем в невалидные
        if code in [917, 924] or "kicked" in msg or "restricted" in msg or "access" in msg:
            invalid_chats.add(str(peer_id))
            remove_chat(peer_id)
            log(f"🚫 Беседа {peer_id} добавлена в чёрный список")
        return False
    return resp.get("response", 0)

def remove_chat(chat_id):
    """Удаляет ID беседы из chats.txt"""
    if os.path.exists(CHATS_FILE):
        with open(CHATS_FILE, "r") as f:
            chats = [line.strip() for line in f if line.strip().isdigit()]
        
        if str(chat_id) in chats:
            chats.remove(str(chat_id))
            with open(CHATS_FILE, "w") as f:
                for cid in chats:
                    f.write(f"{cid}\n")

def clear_invalid_chats():
    """Удаляет все невалидные ID из chats.txt при запуске"""
    if os.path.exists(CHATS_FILE):
        with open(CHATS_FILE, "r") as f:
            chats = [line.strip() for line in f if line.strip().isdigit()]
        
        # Проверяем каждую беседу
        valid_chats = []
        for chat_id in chats:
            # Быстрая проверка через getConversationsById
            resp = api("messages.getConversationsById", {"peer_ids": int(chat_id)})
            if "error" in resp:
                code = resp["error"].get("error_code")
                msg = resp["error"].get("error_msg", "")
                if code in [917, 924] or "kicked" in msg or "restricted" in msg or "access" in msg:
                    invalid_chats.add(chat_id)
                    log(f"🚫 Беседа {chat_id} добавлена в чёрный список")
                    continue
            valid_chats.append(chat_id)
        
        # Сохраняем только валидные
        with open(CHATS_FILE, "w") as f:
            for cid in valid_chats:
                f.write(f"{cid}\n")
        log(f"✅ Очищено: {len(chats) - len(valid_chats)} невалидных бесед")

def load_piar_text():
    if os.path.exists(PIAR_FILE):
        with open(PIAR_FILE, "r", encoding="utf-8") as f:
            text = f.read().strip()
            return text if text else None
    return None

def save_piar_text(text):
    with open(PIAR_FILE, "w", encoding="utf-8") as f:
        f.write(text)
    log(f"💾 Сохранён текст пиара")

def clear_piar_text():
    with open(PIAR_FILE, "w", encoding="utf-8") as f:
        f.write("")
    log(f"🗑️ Файл пиара очищен")
    return None

PIAR_TEXT = load_piar_text()

def is_owner(user_id):
    return user_id == OWNER_ID

def load_ids():
    if os.path.exists(IDS_FILE):
        with open(IDS_FILE, "r") as f:
            return [line.strip() for line in f if line.strip().isdigit()]
    return []

def save_id(user_id):
    ids = load_ids()
    if str(user_id) not in ids:
        with open(IDS_FILE, "a") as f:
            f.write(f"{user_id}\n")
        log(f"💾 Сохранён ID: {user_id}")

def load_chats():
    if os.path.exists(CHATS_FILE):
        with open(CHATS_FILE, "r") as f:
            return [line.strip() for line in f if line.strip().isdigit()]
    return []

def save_chat(chat_id):
    chats = load_chats()
    if str(chat_id) not in chats and str(chat_id) not in invalid_chats:
        with open(CHATS_FILE, "a") as f:
            f.write(f"{chat_id}\n")
        log(f"💾 Сохранена беседа: {chat_id}")

def get_user_name(user_id):
    resp = api("users.get", {"user_ids": user_id})
    users = resp.get("response", [])
    if users:
        return f"{users[0].get('first_name', '')} {users[0].get('last_name', '')}"
    return f"id{user_id}"

def get_chat_name(peer_id):
    resp = api("messages.getConversationsById", {"peer_ids": peer_id})
    items = resp.get("response", {}).get("items", [])
    if items:
        return items[0].get("chat_settings", {}).get("title", "Без названия")
    return "Без названия"

def create_reply_keyboard(user_name, user_id):
    return {
        "one_time": True,
        "buttons": [
            [
                {
                    "action": {
                        "type": "text",
                        "label": f"✏️ Ответить {user_name}",
                        "payload": json.dumps({"action": "reply", "user_id": user_id})
                    },
                    "color": "positive"
                }
            ]
        ]
    }

def listener_thread():
    global awaiting_reply, PIAR_TEXT
    
    resp = api("groups.getLongPollServer", {"group_id": GROUP_ID})
    if "error" in resp:
        log(f"❌ Ошибка LongPoll: {resp['error'].get('error_msg', '')}")
        return
    
    server = resp["response"]["server"]
    key = resp["response"]["key"]
    ts = resp["response"]["ts"]
    if not server.startswith("http"):
        server = "https://" + server
    
    log("👂 Бот слушает...\n")
    
    while True:
        try:
            params = {"act": "a_check", "key": key, "ts": ts, "wait": 10}
            data = requests.get(server, params=params, timeout=15).json()
            
            if "failed" in data:
                resp2 = api("groups.getLongPollServer", {"group_id": GROUP_ID})
                if "response" in resp2:
                    server = resp2["response"]["server"]
                    key = resp2["response"]["key"]
                    ts = resp2["response"]["ts"]
                    if not server.startswith("http"):
                        server = "https://" + server
                continue
            
            ts = data.get("ts", ts)
            
            for upd in data.get("updates", []):
                if upd.get("type") == "message_new":
                    msg = upd.get("object", {}).get("message", {})
                    peer_id = msg.get("peer_id", 0)
                    from_id = msg.get("from_id", 0)
                    text = msg.get("text", "").strip()
                    action = msg.get("action", {})
                    payload = msg.get("payload", {})
                    
                    if isinstance(payload, str) and payload:
                        try:
                            payload = json.loads(payload)
                        except:
                            payload = {}
                    
                    # === ЛИЧНЫЕ СООБЩЕНИЯ ОТ ПОЛЬЗОВАТЕЛЯ ===
                    if peer_id < 2000000000 and from_id > 0:
                        if text.lower().startswith("/") or text.lower().startswith("!"):
                            continue
                        
                        if not text:
                            continue
                        
                        save_id(from_id)
                        
                        if not action:
                            name = get_user_name(from_id)
                            
                            forward_msg = f"📩 {name} (id{from_id}):\n\n{text}"
                            send_message(ADMIN_CHAT_ID, forward_msg, keyboard=create_reply_keyboard(name, from_id))
                            
                            log(f"[{time.strftime('%H:%M:%S')}] 📩 {name}: {text[:30]}")
                    
                    # === СООБЩЕНИЯ В БЕСЕДЕ АДМИНОВ ===
                    elif peer_id == ADMIN_CHAT_ID:
                        if not text:
                            continue
                        
                        # === НАЖАТИЕ НА КНОПКУ ===
                        if payload and payload.get("action") == "reply":
                            user_id = payload.get("user_id")
                            if user_id:
                                name = get_user_name(user_id)
                                awaiting_reply[from_id] = user_id
                                send_message(ADMIN_CHAT_ID, f"✏️ @id{from_id} напишите ответ для {name}:")
                                log(f"✏️ {get_user_name(from_id)} ответит {name}")
                                continue
                        
                        # === ТЕКСТОВЫЙ ОТВЕТ ===
                        if text and not text.startswith("/"):
                            user_id = awaiting_reply.get(from_id)
                            if user_id:
                                name = get_user_name(user_id)
                                send_message(user_id, f"📩 Ответ от поддержки:\n\n{text}")
                                send_message(ADMIN_CHAT_ID, f"✅ @id{from_id} → {name}")
                                log(f"📤 {get_user_name(from_id)} → {name}: {text[:30]}")
                                awaiting_reply.pop(from_id, None)
                                continue
                        
                        # === /o ===
                        if text and (text.lower().startswith("/o") or text.lower().startswith("/о")):
                            cmd = text[2:].strip()
                            parts = cmd.split(" ", 1)
                            
                            if len(parts) >= 2 and parts[0].isdigit():
                                try:
                                    client_id = int(parts[0])
                                    reply_text = parts[1].strip()
                                    name = get_user_name(client_id)
                                    
                                    send_message(client_id, f"📩 Ответ от поддержки:\n\n{reply_text}")
                                    send_message(ADMIN_CHAT_ID, f"✅ @id{from_id} → {name}")
                                    log(f"📤 /o → {name}: {reply_text[:30]}")
                                    continue
                                except:
                                    send_message(ADMIN_CHAT_ID, f"❌ @id{from_id} неверный формат")
                                    continue
                            else:
                                send_message(ADMIN_CHAT_ID, f"❌ @id{from_id} используйте: /o ID текст")
                                continue
                        
                        # === /пиар ===
                        if text.lower().startswith("/пиар"):
                            if not is_owner(from_id):
                                send_message(ADMIN_CHAT_ID, f"❌ @id{from_id} у вас нет прав")
                                continue
                            
                            piar_text = text[6:].strip()
                            if not piar_text:
                                send_message(ADMIN_CHAT_ID, f"❌ @id{from_id} напишите текст после /пиар")
                                continue
                            
                            save_piar_text(piar_text)
                            PIAR_TEXT = piar_text
                            send_message(ADMIN_CHAT_ID, f"✅ @id{from_id} текст пиара сохранён!")
                            log(f"📝 Новый текст пиара от {get_user_name(from_id)}")
                            continue
                        
                        # === /очистка ===
                        if text.lower().startswith("/очистка") or text.lower().startswith("/очистить"):
                            if not is_owner(from_id):
                                send_message(ADMIN_CHAT_ID, f"❌ @id{from_id} у вас нет прав")
                                continue
                            
                            PIAR_TEXT = clear_piar_text()
                            send_message(ADMIN_CHAT_ID, f"🗑️ @id{from_id} файл пиара очищен")
                            log(f"🗑️ Пиар очищен {get_user_name(from_id)}")
                            continue
                        
                        # === /рассылка ===
                        if text.lower().startswith("/рассылка"):
                            if not is_owner(from_id):
                                send_message(ADMIN_CHAT_ID, f"❌ @id{from_id} у вас нет прав")
                                continue
                            
                            msg_text = text[10:].strip()
                            if not msg_text:
                                send_message(ADMIN_CHAT_ID, f"❌ @id{from_id} напишите текст после /рассылка")
                                continue
                            
                            users = load_ids()
                            if not users:
                                send_message(ADMIN_CHAT_ID, f"❌ @id{from_id} нет пользователей в id.txt")
                                continue
                            
                            send_message(ADMIN_CHAT_ID, f"🚀 @id{from_id} рассылка {len(users)} пользователям...")
                            
                            success = 0
                            for user_id in users:
                                if send_message(int(user_id), msg_text, silent=True):
                                    success += 1
                                time.sleep(SEND_DELAY)
                            
                            send_message(ADMIN_CHAT_ID, f"✅ @id{from_id} рассылка: {success}/{len(users)}")
                            log(f"Рассылка: {success}/{len(users)}")
                            continue
                        
                        # === /переписка ID ===
                        if text.lower().startswith("/переписка"):
                            parts = text.split(" ", 1)
                            if len(parts) >= 2:
                                try:
                                    user_id = int(parts[1])
                                    name = get_user_name(user_id)
                                    
                                    send_message(ADMIN_CHAT_ID, f"📖 Переписка с {name} (id{user_id}):")
                                    
                                    msgs, error = get_user_messages(user_id)
                                    if error:
                                        send_message(ADMIN_CHAT_ID, f"❌ Ошибка: {error}")
                                        continue
                                    
                                    if not msgs:
                                        send_message(ADMIN_CHAT_ID, "📭 Нет сообщений")
                                        continue
                                    
                                    formatted = []
                                    for m in msgs[:10]:
                                        fm = format_message(m, user_id)
                                        if fm:
                                            formatted.append(fm)
                                    
                                    if formatted:
                                        for part in formatted:
                                            send_message(ADMIN_CHAT_ID, part)
                                    else:
                                        send_message(ADMIN_CHAT_ID, "📭 Нет текстовых сообщений")
                                    
                                    log(f"📖 {get_user_name(from_id)} просмотрел переписку с {name}")
                                    continue
                                except:
                                    send_message(ADMIN_CHAT_ID, f"❌ @id{from_id} неверный ID")
                                    continue
                            else:
                                send_message(ADMIN_CHAT_ID, f"❌ @id{from_id} используйте: /переписка ID")
                                continue
                    
                    # === КОМАНДА !айди ===
                    if text and text.lower() == "!айди":
                        if peer_id < 2000000000:
                            send_message(peer_id, f"🆔 {from_id}")
                        else:
                            title = get_chat_name(peer_id)
                            send_message(peer_id, f"🆔 {peer_id}\n{title}")
                        continue
                    
                    # === ПРИГЛАШЕНИЕ В БЕСЕДУ ===
                    if peer_id > 2000000000 and peer_id != ADMIN_CHAT_ID and action:
                        if action.get("type") == "chat_invite_user":
                            if action.get("member_id") == -GROUP_ID:
                                save_chat(peer_id)
                                if PIAR_TEXT:
                                    send_message(peer_id, PIAR_TEXT)
                                log(f"🎉 Бот добавлен в беседу {peer_id}")
        
        except Exception as e:
            log(f"Ошибка: {e}")
            time.sleep(3)

def get_user_messages(user_id, count=10):
    try:
        params = {
            "access_token": GROUP_TOKEN,
            "user_id": user_id,
            "count": count,
            "v": V
        }
        resp = requests.get(VK_URL + "messages.getHistory", params=params, timeout=10).json()
        
        if "error" in resp:
            return None, resp["error"].get("error_msg", "Ошибка")
        
        items = resp.get("response", {}).get("items", [])
        return items, None
    except Exception as e:
        return None, str(e)

def format_message(msg, user_id):
    from_id = msg.get("from_id", 0)
    text = msg.get("text", "").strip()
    date = time.strftime("%H:%M", time.localtime(msg.get("date", 0)))
    
    if not text:
        return None
    
    if from_id == user_id:
        return f"👤 [{date}] {text}"
    else:
        return f"🤖 [{date}] {text}"

def spammer_thread():
    global PIAR_TEXT
    
    log(f"⏱️ Пиар в беседах каждые {SPAM_INTERVAL} сек\n")
    round_num = 0
    
    while True:
        try:
            round_num += 1
            chats = load_chats()
            
            # Фильтруем только валидные беседы
            valid_chats = [c for c in chats if c not in invalid_chats]
            
            if valid_chats and PIAR_TEXT:
                log(f"📢 Круг {round_num}: {len(valid_chats)} валидных бесед из {len(chats)}")
                
                success = 0
                for chat_id in valid_chats:
                    if send_message(int(chat_id), PIAR_TEXT, silent=True):
                        success += 1
                    time.sleep(SEND_DELAY)
                
                log(f"[{time.strftime('%H:%M:%S')}] 🔄 КРУГ {round_num} | ✅ {success}/{len(valid_chats)}")
            elif chats and not PIAR_TEXT:
                log(f"[{time.strftime('%H:%M:%S')}] ⏸️ Пиар отключен")
            elif not chats:
                log(f"[{time.strftime('%H:%M:%S')}] 📭 Нет бесед для пиара")
            
            time.sleep(SPAM_INTERVAL)
        except Exception as e:
            log(f"Ошибка пиара: {e}")
            time.sleep(5)

if __name__ == "__main__":
    log(f"🤖 БОТ ЗАПУЩЕН")
    log(f"👑 Владелец: id{OWNER_ID}")
    log(f"📢 Беседа админов: {ADMIN_CHAT_ID}")
    
    # Очищаем невалидные беседы при запуске
    clear_invalid_chats()
    
    log(f"🚫 Невалидных бесед в чёрном списке: {len(invalid_chats)}")
    log(f"📩 Кнопка 'Ответить' в клавиатуре под сообщением")
    log(f"📝 /o ID текст - ответить через команду")
    log(f"📝 /пиар текст - ТОЛЬКО ДЛЯ ВЛАДЕЛЬЦА")
    log(f"🗑️ /очистка или /очистить - ТОЛЬКО ДЛЯ ВЛАДЕЛЬЦА")
    log(f"📝 /рассылка текст - ТОЛЬКО ДЛЯ ВЛАДЕЛЬЦА")
    log(f"📝 /переписка ID - БЕЗ 'Ответ от поддержки'\n")
    
    t1 = threading.Thread(target=listener_thread, daemon=True)
    t1.start()
    
    t2 = threading.Thread(target=spammer_thread, daemon=True)
    t2.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log("\n👋 Стоп")

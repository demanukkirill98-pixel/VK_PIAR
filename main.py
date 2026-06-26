import requests
import time
import os
import json
import threading

# ========== НАСТРОЙКИ ==========
GROUP_TOKEN = "vk1.a.GENAzRdaR86f91rPAydFj660SgWD7ylgOKpjwrrPaDtgE64s3ZSMn02sa_QPL7IKcOsFIEgMK17_DlaTsjXVlpJb-a4eLqQcbEfCA4OnTcqbn5J5cjqwh-eyKrwxFbmdgJSKMY8PgIiwj8DRhOaOU3DvdDchvGw5ebC-ysGXDA9Cyg0-knFBsdhf_o__aoKHrR0RceQB658D-WjG5xBbqg"
GROUP_ID = 239058698
ADMIN_CHAT_ID = 2000000062
OWNER_LINK = "vk.com/club239058698"

SEND_DELAY = 2
SPAM_INTERVAL = 60
CHATS_FILE = "chats.txt"
IDS_FILE = "id.txt"

last_user_for_admin = {}
awaiting_reply = {}

VK_URL = "https://api.vk.com/method/"
V = "5.199"

PIAR_TEXT = f"""👑 SKREIFF SHOP

Здравствуйте, уважаемые участники!

Если желаете развить свой проект и начать зарабатывать — тогда вам к нам!

💎 Наши преимущества:
✅ Дёшево
✅ Выгодно
✅ Качественно

🛍 Что мы предлагаем:
🎮 CRMP и SAMP проекты
🌐 Форумы
💻 Сайты
🤖 Боты ВК/ТГ (с VPN и без)
📢 Автопиары
⛏ Сервера Minecraft PE/Java

💳 Принимаем оплаты на любых картах СНГ и детских

📩 Писать только в сообщество (менеджеру):
{OWNER_LINK}"""

def log(msg):
    print(msg, flush=True)

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
    if str(chat_id) not in chats:
        with open(CHATS_FILE, "a") as f:
            f.write(f"{chat_id}\n")
        log(f"💾 Сохранена беседа: {chat_id}")

def api(method, params):
    params["access_token"] = GROUP_TOKEN
    params["v"] = V
    try:
        resp = requests.get(VK_URL + method, params=params, timeout=5).json()
        return resp
    except:
        return {"error": {"error_msg": "connection"}}

def send_message(peer_id, message, silent=False, keyboard=None, reply_to=None):
    # Проверка на пустое сообщение
    if not message or not message.strip():
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
        code = resp["error"]["error_code"]
        if code == 9:
            time.sleep(10)
            return send_message(peer_id, message, silent, keyboard, reply_to)
        return False
    return True

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
    global last_user_for_admin, awaiting_reply
    
    resp = api("groups.getLongPollServer", {"group_id": GROUP_ID})
    if "error" in resp:
        log("❌ Ошибка LongPoll")
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
                        if from_id == 2000000062:
                            continue
                        
                        # Если текст пустой - игнорируем
                        if not text:
                            continue
                        
                        save_id(from_id)
                        
                        if not action:
                            if text.lower().startswith("/") or text.lower().startswith("!"):
                                continue
                            
                            name = get_user_name(from_id)
                            
                            last_user_for_admin[from_id] = {"id": from_id, "name": name}
                            
                            forward_msg = f"📩 {name} (id{from_id}):\n\n{text}"
                            send_message(ADMIN_CHAT_ID, forward_msg, keyboard=create_reply_keyboard(name, from_id))
                            log(f"[{time.strftime('%H:%M:%S')}] 📩 {name}: {text[:30]}")
                    
                    # === СООБЩЕНИЯ В БЕСЕДЕ АДМИНОВ ===
                    elif peer_id == ADMIN_CHAT_ID:
                        # Проверяем что текст не пустой
                        if not text:
                            continue
                        
                        if payload and payload.get("action") == "reply":
                            user_id = payload.get("user_id")
                            if user_id:
                                name = get_user_name(user_id)
                                awaiting_reply[from_id] = user_id
                                send_message(ADMIN_CHAT_ID, f"✏️ @id{from_id} напишите ответ для {name}:")
                                log(f"✏️ {get_user_name(from_id)} ответит {name}")
                                continue
                        
                        if text and text.lower().startswith("/o"):
                            cmd = text[2:].strip()
                            
                            # Если после /o ничего нет - игнорируем
                            if not cmd:
                                send_message(ADMIN_CHAT_ID, f"❌ @id{from_id} напишите текст после /o")
                                continue
                            
                            parts = cmd.split(" ", 1)
                            if len(parts) >= 2 and parts[0].isdigit():
                                try:
                                    client_id = int(parts[0])
                                    reply_text = parts[1].strip()
                                    
                                    # Если текст ответа пустой - игнорируем
                                    if not reply_text:
                                        send_message(ADMIN_CHAT_ID, f"❌ @id{from_id} напишите текст ответа")
                                        continue
                                    
                                    name = get_user_name(client_id)
                                    send_message(client_id, f"📩 Ответ от поддержки:\n\n{reply_text}")
                                    send_message(ADMIN_CHAT_ID, f"✅ @id{from_id} → {name}")
                                    log(f"📤 /o → {name}: {reply_text[:30]}")
                                    awaiting_reply.pop(from_id, None)
                                    continue
                                except:
                                    send_message(ADMIN_CHAT_ID, f"❌ @id{from_id} неверный формат")
                                    continue
                            else:
                                last_user = last_user_for_admin.get(from_id)
                                if last_user:
                                    client_id = last_user["id"]
                                    name = last_user["name"]
                                    reply_text = cmd.strip()
                                    
                                    if not reply_text:
                                        send_message(ADMIN_CHAT_ID, f"❌ @id{from_id} напишите текст ответа")
                                        continue
                                    
                                    send_message(client_id, f"📩 Ответ от поддержки:\n\n{reply_text}")
                                    send_message(ADMIN_CHAT_ID, f"✅ @id{from_id} → {name} (последний)")
                                    log(f"📤 /o → {name}: {reply_text[:30]}")
                                    awaiting_reply.pop(from_id, None)
                                    continue
                                else:
                                    send_message(ADMIN_CHAT_ID, f"❌ @id{from_id} нет последнего пользователя. Используйте: /o ID текст")
                                    continue
                        
                        if text and not text.startswith("/") and not text.startswith("!"):
                            user_id = awaiting_reply.get(from_id)
                            if user_id:
                                name = get_user_name(user_id)
                                send_message(user_id, f"📩 Ответ от поддержки:\n\n{text}")
                                send_message(ADMIN_CHAT_ID, f"✅ @id{from_id} → {name}")
                                log(f"📤 {get_user_name(from_id)} → {name}: {text[:30]}")
                                awaiting_reply.pop(from_id, None)
                    
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
                                send_message(peer_id, PIAR_TEXT)
                                log(f"🎉 Бот добавлен в беседу {peer_id}")
        
        except Exception as e:
            log(f"Ошибка: {e}")
            time.sleep(3)

def spammer_thread():
    log(f"⏱️ Пиар в беседах каждые {SPAM_INTERVAL} сек\n")
    round_num = 0
    
    while True:
        try:
            round_num += 1
            chats = load_chats()
            
            if chats:
                for chat_id in chats:
                    send_message(int(chat_id), PIAR_TEXT, silent=True)
                    time.sleep(SEND_DELAY)
                
                log(f"[{time.strftime('%H:%M:%S')}] 🔄 КРУГ {round_num} | ✅ {len(chats)} бесед")
            
            time.sleep(SPAM_INTERVAL)
        except Exception as e:
            log(f"Ошибка пиара: {e}")
            time.sleep(5)

if __name__ == "__main__":
    log(f"🤖 БОТ ЗАПУЩЕН")
    log(f"📝 Все кто пишут в ЛС → сохраняются в {IDS_FILE}")
    log(f"📢 Беседы → сохраняются в {CHATS_FILE}")
    log(f"👑 Все в беседе {ADMIN_CHAT_ID} - админы")
    log(f"⏱️ Пиар каждые {SPAM_INTERVAL} сек")
    log(f"✏️ Ответ через кнопку")
    log(f"📝 /o ID текст - ответить конкретному")
    log(f"📝 /o текст - ответить последнему\n")
    
    t1 = threading.Thread(target=listener_thread, daemon=True)
    t1.start()
    
    t2 = threading.Thread(target=spammer_thread, daemon=True)
    t2.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log("\n👋 Стоп")

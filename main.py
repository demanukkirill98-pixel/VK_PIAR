import requests
import time
import os
import threading
import random
import json

# ========== НАСТРОЙКИ ==========
GROUP_TOKEN = "vk1.a.GENAzRdaR86f91rPAydFj660SgWD7ylgOKpjwrrPaDtgE64s3ZSMn02sa_QPL7IKcOsFIEgMK17_DlaTsjXVlpJb-a4eLqQcbEfCA4OnTcqbn5J5cjqwh-eyKrwxFbmdgJSKMY8PgIiwj8DRhOaOU3DvdDchvGw5ebC-ysGXDA9Cyg0-knFBsdhf_o__aoKHrR0RceQB658D-WjG5xBbqg"
GROUP_ID = 239058698
ADMIN_CHAT_ID = 2000000062
OWNER_LINK = "vk.com/club239058698"

SEND_DELAY = 2
SPAM_INTERVAL = 60
IDS_FILE = "id.txt"
CHATS_FILE = "chats.txt"

msg_index = 0
last_user = None
awaiting_reply = False
last_keyboard_msg_id = None  # Храним ID сообщения с кнопкой

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

PROMO_TEXT = f"""🎁 ПРОМОКОД LETO - СКИДКА 15%!

По промокоду "LETO" скидка 15% на все товары!

Выгоднее с каждым днём - не пропустите!

📩 Писать: {OWNER_LINK}"""

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
    
    # Возвращаем ID отправленного сообщения
    return resp.get("response", 0)

def edit_keyboard(peer_id, message_id, keyboard=None):
    """Редактирует сообщение - убирает клавиатуру"""
    params = {
        "peer_id": peer_id,
        "message_id": message_id,
        "random_id": int(time.time() * 1000000)
    }
    if keyboard:
        params["keyboard"] = json.dumps(keyboard, ensure_ascii=False)
    else:
        params["keyboard"] = json.dumps({"buttons": []})  # Пустая клавиатура
    
    resp = api("messages.edit", params)
    return "error" not in resp

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

def create_reply_keyboard(user_name):
    """Клавиатура с кнопкой ответа (one_time=True - пропадёт после нажатия)"""
    return {
        "one_time": True,
        "buttons": [
            [
                {
                    "action": {
                        "type": "text",
                        "label": f"✏️ Ответить {user_name}",
                        "payload": json.dumps({"action": "reply"})
                    },
                    "color": "positive"
                }
            ]
        ]
    }

def listener_thread():
    global msg_index, last_user, awaiting_reply, last_keyboard_msg_id
    
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
                    
                    # === ЛИЧНЫЕ СООБЩЕНИЯ ===
                    if peer_id < 2000000000 and from_id > 0:
                        save_id(from_id)
                        
                        if not action:
                            if text.lower().startswith("/") or text.lower().startswith("!"):
                                continue
                            
                            name = get_user_name(from_id)
                            user_msg_id = msg.get("conversation_message_id", 0)
                            
                            last_user = {
                                "id": from_id,
                                "name": name,
                                "msg_id": user_msg_id,
                                "text": text
                            }
                            awaiting_reply = False
                            
                            # Отправляем текст сообщения
                            send_message(ADMIN_CHAT_ID, f"👤 {name} (id{from_id}):\n\n{text}")
                            # Отправляем сообщение с кнопкой и запоминаем его ID
                            last_keyboard_msg_id = send_message(ADMIN_CHAT_ID, "👇 Нажмите кнопку чтобы ответить", keyboard=create_reply_keyboard(name))
                            log(f"[{time.strftime('%H:%M:%S')}] 📩 {name}: {text[:30]}")
                    
                    # === БЕСЕДА АДМИНА ===
                    elif peer_id == ADMIN_CHAT_ID:
                        # Нажатие на кнопку
                        if payload and payload.get("action") == "reply":
                            if last_user and not awaiting_reply:
                                awaiting_reply = True
                                # Убираем кнопку (редактируем сообщение)
                                if last_keyboard_msg_id:
                                    edit_keyboard(ADMIN_CHAT_ID, last_keyboard_msg_id)
                                send_message(ADMIN_CHAT_ID, f"✏️ Напишите ответ для {last_user['name']}:")
                                log(f"✏️ Ожидание ответа для {last_user['name']}")
                            else:
                                send_message(ADMIN_CHAT_ID, "❌ Нет активного пользователя")
                        
                        # Текст ответа
                        elif text and awaiting_reply and last_user:
                            answer = f"📩 Ответ от поддержки:\n\n{text}"
                            
                            result = send_message(last_user["id"], answer, reply_to=last_user["msg_id"])
                            if not result:
                                result = send_message(last_user["id"], answer)
                            
                            if result:
                                send_message(ADMIN_CHAT_ID, f"✅ Отправлено {last_user['name']}")
                                log(f"[{time.strftime('%H:%M:%S')}] 📤 {last_user['name']}: {text[:30]}")
                            else:
                                send_message(ADMIN_CHAT_ID, "❌ Ошибка отправки")
                            
                            awaiting_reply = False
                            last_keyboard_msg_id = None
                        
                        # === КОМАНДА /on ===
                        elif text and text.lower() == "/on":
                            users = load_ids()
                            if not users:
                                send_message(ADMIN_CHAT_ID, "❌ Нет пользователей в id.txt")
                                continue
                            
                            send_message(ADMIN_CHAT_ID, f"🚀 Начинаю рассылку {len(users)} пользователям...")
                            
                            success = 0
                            for user_id in users:
                                if send_message(int(user_id), PROMO_TEXT, silent=True):
                                    success += 1
                                time.sleep(SEND_DELAY)
                            
                            send_message(ADMIN_CHAT_ID, f"✅ Рассылка LETO завершена!\n📨 Отправлено: {success}/{len(users)}")
                            log(f"Рассылка /on: {success}/{len(users)}")
                    
                    # === КОМАНДА !айди ===
                    if text.lower() == "!айди":
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
    log(f"⏱️ Пиар (без промокода) каждые {SPAM_INTERVAL} сек")
    log(f"🎁 /on - рассылка промокода LETO\n")
    
    t1 = threading.Thread(target=listener_thread, daemon=True)
    t1.start()
    
    t2 = threading.Thread(target=spammer_thread, daemon=True)
    t2.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log("\n👋 Стоп")

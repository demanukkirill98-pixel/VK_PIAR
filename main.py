import requests
import time
import os
import threading
import random

# ========== НАСТРОЙКИ ==========
GROUP_TOKEN = "vk1.a.GENAzRdaR86f91rPAydFj660SgWD7ylgOKpjwrrPaDtgE64s3ZSMn02sa_QPL7IKcOsFIEgMK17_DlaTsjXVlpJb-a4eLqQcbEfCA4OnTcqbn5J5cjqwh-eyKrwxFbmdgJSKMY8PgIiwj8DRhOaOU3DvdDchvGw5ebC-ysGXDA9Cyg0-knFBsdhf_o__aoKHrR0RceQB658D-WjG5xBbqg"
GROUP_ID = 239058698
ADMIN_CHAT_ID = 2000000062
OWNER_LINK = "vk.com/club239058698"

SEND_DELAY = 2
SPAM_INTERVAL = 60
IDS_FILE = "id.txt"

msg_index = 0
# Словарь: {id_сообщения_админа: (user_id, user_msg_id)}
admin_msg_to_user = {}

VK_URL = "https://api.vk.com/method/"
V = "5.199"

MESSAGES = [
    f"""👑 SKREIFF SHOP

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

🎫 ПРОМОКОД: LETO — скидка 15% на всё!

💳 Принимаем оплаты на любых картах СНГ и детских

📩 Писать только в сообщество (менеджеру):
{OWNER_LINK}""",

    f"""⚡ SKREIFF SHOP

Здравствуйте, уважаемые участники!

Хотите развить проект и зарабатывать?
Мы поможем!

💎 Наши преимущества:
✅ Дёшево
✅ Выгодно
✅ Качественно

🎮 CRMP и SAMP проекты
🌐 Форумы | Сайты
🤖 Боты ВК/ТГ
📢 Автопиары
⛏ Сервера Minecraft

🎫 ПРОМОКОД: LETO — скидка 15% на всё!

💳 Оплата на любые карты СНГ и детские

📩 Писать только в сообщество (менеджеру):
{OWNER_LINK}""",

    f"""🔥 SKREIFF SHOP

Здравствуйте, уважаемые участники!

Желаете развить свой проект и начать зарабатывать?
Тогда вам к нам!

💎 Дёшево • Выгодно • Качественно

🛍 Наши услуги:
• CRMP и SAMP проекты
• Форумы и сайты
• Боты ВК/ТГ
• Автопиары
• Сервера Minecraft

🎫 ПРОМОКОД: LETO — скидка 15% на всё!

💳 Принимаем оплаты на любых картах СНГ и детских

📩 Писать только в сообщество (менеджеру):
{OWNER_LINK}""",

    f"""💎 SKREIFF SHOP

Здравствуйте, уважаемые участники!

Развитие проекта и заработок — это к нам!

✅ Дёшево
✅ Выгодно
✅ Качественно

🎮 CRMP | SAMP проекты
🌐 Форумы | Сайты
🤖 Боты ВК/ТГ
📢 Автопиары
⛏ Minecraft сервера

🎫 ПРОМОКОД: LETO — скидка 15% на всё!

💳 Оплата: карты СНГ и детские

📩 Писать только в сообщество (менеджеру):
{OWNER_LINK}""",
]

# =================================

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
        log(f"💾 Новый пользователь сохранён: {user_id}")

def api(method, params):
    params["access_token"] = GROUP_TOKEN
    params["v"] = V
    try:
        resp = requests.get(VK_URL + method, params=params, timeout=5).json()
        return resp
    except:
        return {"error": {"error_msg": "connection"}}

def send_message(peer_id, message, silent=False, reply_to=None):
    params = {
        "peer_id": peer_id,
        "message": message,
        "random_id": int(time.time() * 1000000)
    }
    if reply_to:
        params["reply_to"] = reply_to
    
    resp = api("messages.send", params)
    
    if "error" in resp:
        code = resp["error"]["error_code"]
        if code == 9:
            time.sleep(10)
            return send_message(peer_id, message, silent, reply_to)
        if not silent:
            if code not in [7, 902, 917, 912]:
                log(f"  ❌ [{code}] {resp['error']['error_msg']}")
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

# ====== СЛУШАЕМ ======
def listener_thread():
    global msg_index, admin_msg_to_user
    
    resp = api("groups.getLongPollServer", {"group_id": GROUP_ID})
    if "error" in resp:
        log("❌ Ошибка получения LongPoll сервера")
        return
    
    server = resp["response"]["server"]
    key = resp["response"]["key"]
    ts = resp["response"]["ts"]
    
    if not server.startswith("http"):
        server = "https://" + server
    
    log("👂 Бот слушает сообщения...\n")
    
    while True:
        try:
            params = {"act": "a_check", "key": key, "ts": ts, "wait": 10}
            resp = requests.get(server, params=params, timeout=15)
            data = resp.json()
            
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
                    reply_to_msg = msg.get("reply_to", 0)  # ID сообщения, на которое отвечают
                    
                    # === ЛИЧНЫЕ СООБЩЕНИЯ (ПОЛЬЗОВАТЕЛЬ -> БОТ) ===
                    if peer_id < 2000000000 and from_id > 0:
                        save_id(from_id)
                        
                        if not action:
                            if text.lower().startswith("/o"):
                                continue
                            
                            name = get_user_name(from_id)
                            user_msg_id = msg.get("conversation_message_id", 0)
                            
                            # Отправляем админу пересланное сообщение
                            forward_msg = f"""📩 ОТ {name} (id{from_id}):

{text}"""
                            
                            # Отправляем и сохраняем ID этого сообщения в админской беседе
                            resp_send = api("messages.send", {
                                "peer_id": ADMIN_CHAT_ID,
                                "message": forward_msg,
                                "random_id": int(time.time() * 1000000)
                            })
                            
                            # Сохраняем связь: ID сообщения админа -> (user_id, user_msg_id)
                            if "response" in resp_send:
                                admin_msg_id = resp_send["response"]
                                admin_msg_to_user[admin_msg_id] = (from_id, user_msg_id)
                                log(f"[{time.strftime('%H:%M:%S')}] 📩 {name}: {text[:30]} | слайп готов")
                            else:
                                log(f"❌ Не удалось отправить админу сообщение от {name}")
                    
                    # === ОТВЕТ АДМИНА В БЕСЕДЕ (АВТОМАТИЧЕСКИЙ СЛАЙП) ===
                    if peer_id == ADMIN_CHAT_ID and reply_to_msg > 0:
                        # Админ ответил на какое-то сообщение в беседе
                        if reply_to_msg in admin_msg_to_user:
                            user_id, user_msg_id = admin_msg_to_user[reply_to_msg]
                            
                            # Отправляем пользователю ответ слайпом
                            answer = f"""📩 Ответ от поддержки SKREIFF SHOP:

{text}"""
                            
                            result = send_message(user_id, answer, reply_to=user_msg_id)
                            
                            if result:
                                name = get_user_name(user_id)
                                send_message(ADMIN_CHAT_ID, f"✅ Слайп-ответ отправлен → {name}")
                                log(f"[{time.strftime('%H:%M:%S')}] 📤 Слайп-ответ {name}: {text[:30]}")
                                # Удаляем связь, чтобы не ответить дважды
                                del admin_msg_to_user[reply_to_msg]
                            else:
                                send_message(ADMIN_CHAT_ID, "❌ Не удалось отправить слайп-ответ")
                                log(f"[{time.strftime('%H:%M:%S')}] ❌ Ошибка слайп-ответа {user_id}")
                        else:
                            # Ответ на какое-то другое сообщение (не от бота)
                            pass
                    
                    # === КОМАНДА !айди В ЛС ===
                    if peer_id < 2000000000 and text.lower() == "!айди":
                        send_message(peer_id, f"🆔 Твой ID: {from_id}")
                        continue
                    
                    # === КОМАНДА !айди В БЕСЕДЕ ===
                    if peer_id > 2000000000 and text.lower() == "!айди":
                        title = get_chat_name(peer_id)
                        send_message(peer_id, f"🆔 ID беседы: {peer_id}\n📝 {title}")
                        continue
                    
                    # === РАССЫЛКА LETO ===
                    if peer_id == ADMIN_CHAT_ID and text.lower() == "!рассылка_лето":
                        log(f"[{time.strftime('%H:%M:%S')}] 🎁 Запущена рассылка LETO")
                        
                        send_message(ADMIN_CHAT_ID, "🚀 Начинаю рассылку по промокоду LETO всем, кто писал боту...")
                        
                        users = load_ids()
                        if not users:
                            send_message(ADMIN_CHAT_ID, "❌ Нет пользователей для рассылки (файл id.txt пуст)")
                            continue
                        
                        promo_text = f"""🎁 ВАЖНОЕ ОБЪЯВЛЕНИЕ 🎁

По промокоду "LETO" вы получаете скидку 15% на все товары!

🔥 Выгоднее с каждым днём — не пропустите!

{random.choice(MESSAGES)}"""
                        
                        success = 0
                        for i, user_id in enumerate(users):
                            result = send_message(int(user_id), promo_text, silent=True)
                            if result:
                                success += 1
                            time.sleep(SEND_DELAY)
                            
                            if (i + 1) % 10 == 0:
                                send_message(ADMIN_CHAT_ID, f"📊 Прогресс: {i+1}/{len(users)} (✅ {success})")
                        
                        send_message(ADMIN_CHAT_ID, f"✅ Рассылка LETO завершена!\n📨 Отправлено: {success}/{len(users)}")
                        log(f"[{time.strftime('%H:%M:%S')}] ✅ Рассылка LETO: {success}/{len(users)}")
                    
                    # === ПРИГЛАШЕНИЕ В БЕСЕДУ ===
                    if peer_id > 2000000000 and peer_id != ADMIN_CHAT_ID and action:
                        if action.get("type") == "chat_invite_user":
                            if action.get("member_id") == -GROUP_ID:
                                msg_text = MESSAGES[msg_index % len(MESSAGES)]
                                msg_index += 1
                                send_message(peer_id, msg_text)
        
        except Exception as e:
            log(f"Ошибка: {e}")
            time.sleep(3)

# ====== ПИАР ПО БЕСЕДАМ ======
def spammer_thread():
    log(f"⏱️ Пиар в беседах каждые {SPAM_INTERVAL} сек\n")
    while True:
        try:
            time.sleep(SPAM_INTERVAL)
        except:
            time.sleep(5)

if __name__ == "__main__":
    log(f"🤖 SKREIFF SHOP БОТ ЗАПУЩЕН")
    log(f"📩 Пользователь пишет → пересылается админу")
    log(f"💬 Админ отвечает (СЛАЙПОМ) на пересланное сообщение → уходит пользователю")
    log(f"🎁 !рассылка_лето — отправить промо всем из id.txt")
    log(f"🔍 !айди — узнать свой ID")
    log(f"💾 Файл id.txt — список пользователей\n")
    
    t1 = threading.Thread(target=listener_thread, daemon=True)
    t1.start()
    
    t2 = threading.Thread(target=spammer_thread, daemon=True)
    t2.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log("\n👋 Бот остановлен")

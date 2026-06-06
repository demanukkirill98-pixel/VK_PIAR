import requests
import time
import os
import threading
import sys

# ========== НАСТРОЙКИ ==========
GROUP_TOKEN = "vk1.a.GENAzRdaR86f91rPAydFj660SgWD7ylgOKpjwrrPaDtgE64s3ZSMn02sa_QPL7IKcOsFIEgMK17_DlaTsjXVlpJb-a4eLqQcbEfCA4OnTcqbn5J5cjqwh-eyKrwxFbmdgJSKMY8PgIiwj8DRhOaOU3DvdDchvGw5ebC-ysGXDA9Cyg0-knFBsdhf_o__aoKHrR0RceQB658D-WjG5xBbqg"
GROUP_ID = 239058698
ADMIN_CHAT_ID = 2000000062
OWNER_LINK = "vk.com/club239058698"

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

💳 Оплата: карты СНГ и детские

📩 Писать только в сообщество (менеджеру):
{OWNER_LINK}""",
]

SEND_DELAY = 2
SPAM_INTERVAL = 60
CHATS_FILE = "chats.txt"

msg_index = 0
# =================================

VK_URL = "https://api.vk.com/method/"
V = "5.199"

def log(msg):
    print(msg, flush=True)

def load_chats():
    if os.path.exists(CHATS_FILE):
        with open(CHATS_FILE, "r") as f:
            return [line.strip() for line in f if line.strip().isdigit()]
    return []

def api(method, params):
    params["access_token"] = GROUP_TOKEN
    params["v"] = V
    try:
        resp = requests.get(VK_URL + method, params=params, timeout=5).json()
        return resp
    except:
        return {"error": {"error_msg": "connection"}}

def send_message(peer_id, message, silent=False):
    resp = api("messages.send", {
        "peer_id": peer_id,
        "message": message,
        "random_id": int(time.time() * 1000000)
    })
    
    if "error" in resp:
        code = resp["error"]["error_code"]
        if code == 9:
            time.sleep(10)
            return send_message(peer_id, message, silent)
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

# ====== СЛУШАЕМ ======
def listener_thread():
    global msg_index
    
    resp = api("groups.getLongPollServer", {"group_id": GROUP_ID})
    if "error" in resp:
        log("❌ Ошибка LP")
        return
    
    server = resp["response"]["server"]
    key = resp["response"]["key"]
    ts = resp["response"]["ts"]
    
    if not server.startswith("http"):
        server = "https://" + server
    
    log("👂 Слушаю...\n")
    
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
                    
                    # === ЛС ===
                    if peer_id < 2000000000 and from_id > 0 and not action:
                        if text.lower().startswith("/o"):
                            continue
                        
                        name = get_user_name(from_id)
                        forward = f"""📩 {name}
🔗 vk.com/id{from_id}
💬 {text}

✏️ /o {from_id} ответ"""
                        
                        send_message(ADMIN_CHAT_ID, forward)
                        log(f"[{time.strftime('%H:%M:%S')}] 📩 {name}: {text[:30]}")
                    
                    # === /o ===
                    elif peer_id == ADMIN_CHAT_ID and text.lower().startswith("/o"):
                        log(f"[{time.strftime('%H:%M:%S')}] 📝 /o от id{from_id}")
                        
                        parts = text.split(" ", 2)
                        if len(parts) >= 3:
                            try:
                                client_id = int(parts[1])
                                reply_text = parts[2]
                                
                                answer = f"""📩 Ответ от поддержки SKREIFF SHOP:

{reply_text}"""
                                
                                result = send_message(client_id, answer)
                                
                                if result:
                                    name = get_user_name(client_id)
                                    send_message(ADMIN_CHAT_ID, f"✅ → {name}")
                                    log(f"[{time.strftime('%H:%M:%S')}] 📤 {name}: {reply_text[:30]}")
                                else:
                                    send_message(ADMIN_CHAT_ID, "❌ Не отправлено")
                                    log(f"[{time.strftime('%H:%M:%S')}] ❌ {client_id}")
                            except:
                                send_message(ADMIN_CHAT_ID, "❌ ID")
                        else:
                            send_message(ADMIN_CHAT_ID, "❌ /o ID текст")
                    
                    # === ДОБАВИЛИ В БЕСЕДУ ===
                    if peer_id > 2000000000 and peer_id != ADMIN_CHAT_ID and action:
                        if action.get("type") == "chat_invite_user":
                            if action.get("member_id") == -GROUP_ID:
                                msg_text = MESSAGES[msg_index % len(MESSAGES)]
                                msg_index += 1
                                send_message(peer_id, msg_text)
        
        except:
            time.sleep(3)

# ====== ПИАР ======
def spammer_thread():
    global msg_index
    
    log(f"⏱️ Пиар каждые {SPAM_INTERVAL} сек\n")
    
    round_num = 0
    
    while True:
        try:
            round_num += 1
            chats = load_chats()
            
            if chats:
                message = MESSAGES[msg_index % len(MESSAGES)]
                msg_index += 1
                
                ok = 0
                for chat_id in chats:
                    if send_message(int(chat_id), message, silent=True):
                        ok += 1
                        time.sleep(SEND_DELAY)
                
                log(f"[{time.strftime('%H:%M:%S')}] 🔄 КРУГ {round_num} | ✅ {ok}/{len(chats)}")
            
            time.sleep(SPAM_INTERVAL)
            
        except:
            time.sleep(5)

if __name__ == "__main__":
    log(f"🤖 SKREIFF SHOP БОТ")
    log(f"📩 ЛС → ЧАТ МЕНЕДЖЕР")
    log(f"📤 /o ID текст\n")
    
    t1 = threading.Thread(target=listener_thread, daemon=True)
    t1.start()
    
    t2 = threading.Thread(target=spammer_thread, daemon=True)
    t2.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log("\n👋 Стоп")

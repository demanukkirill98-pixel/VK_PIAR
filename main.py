import requests
import time
import os

# ========== НАСТРОЙКИ ==========
GROUP_TOKEN = "vk1.a.GENAzRdaR86f91rPAydFj660SgWD7ylgOKpjwrrPaDtgE64s3ZSMn02sa_QPL7IKcOsFIEgMK17_DlaTsjXVlpJb-a4eLqQcbEfCA4OnTcqbn5J5cjqwh-eyKrwxFbmdgJSKMY8PgIiwj8DRhOaOU3DvdDchvGw5ebC-ysGXDA9Cyg0-knFBsdhf_o__aoKHrR0RceQB658D-WjG5xBbqg"
GROUP_ID = 239058698
OWNER_ID = vk.com/club239058698

# Храним связку: кому ответить
# {owner_peer_id: client_peer_id}
reply_map = {}

MESSAGES = [
    f"""🔥 Давно хотел создать топовый проект?

Тогда тебе к нам!

👾 Лучшая студия GTA SAMP, CRMP SKREIFF SHOP

✅ Плюсы: низкие цены, выгодные товары, быстро и качественно
❌ Минусы: их нет

💻 Делаем: игры, сайты, форумы, ботов ВК/ТГ, автопиары

📩 По всем вопросам: {OWNER_ID}""",

    f"""🎮 SKREIFF SHOP — топовая студия

⚡ GTA SAMP / CRMP
⚡ Игры, сайты, форумы
⚡ Боты ВК и Telegram
⚡ Автопиар

Низкие цены, быстро, качественно!

📩 {OWNER_ID}""",

    f"""💎 Нужен крутой проект?

SKREIFF SHOP — студия с опытом

✔️ Разработка игр
✔️ Создание сайтов
✔️ Боты любой сложности
✔️ Автопиар
✔️ Готовые решения

По всем вопросам к менеджеру: {OWNER_ID}""",

    f"""🚀 Хочешь раскрутить проект?

SKREIFF SHOP поможет!

🔹 GTA SAMP сервера
🔹 CRMP проекты
🔹 Сайты и форумы
🔹 Боты ВК/Telegram
🔹 Автопиар

Качество, скорость, низкие цены!

📩 Пиши: {OWNER_ID}""",
]

SEND_DELAY = 3
SPAM_INTERVAL = 60
CHATS_FILE = "chats.txt"
# =================================

VK_URL = "https://api.vk.com/method/"
V = "5.199"

def load_chats():
    if os.path.exists(CHATS_FILE):
        with open(CHATS_FILE, "r") as f:
            return [line.strip() for line in f if line.strip().isdigit()]
    return []

def send_message(token, peer_id, message):
    params = {
        "access_token": token,
        "peer_id": peer_id,
        "message": message,
        "random_id": int(time.time() * 1000000),
        "v": V
    }
    
    try:
        resp = requests.get(VK_URL + "messages.send", params=params, timeout=10).json()
        
        if "error" in resp:
            code = resp["error"]["error_code"]
            if code == 9:
                time.sleep(10)
                return send_message(token, peer_id, message)
            return False
        return True
    except:
        return False

def get_user_name(token, user_id):
    try:
        params = {"access_token": token, "user_ids": user_id, "v": V}
        resp = requests.get(VK_URL + "users.get", params=params, timeout=5).json()
        users = resp.get("response", [])
        if users:
            return f"{users[0].get('first_name', '')} {users[0].get('last_name', '')}"
    except:
        pass
    return f"id{user_id}"

def forward_to_owner(token, from_id, text, client_peer_id):
    """Пересылает сообщение из ЛС сообщества владельцу"""
    name = get_user_name(token, from_id)
    
    # Сохраняем связку: диалог с владельцем → клиент
    reply_map[OWNER_ID] = client_peer_id
    
    msg = f"""📩 {name}
👤 vk.com/id{from_id}

💬 {text}

➡️ Нажми «Ответить» и пиши — сообщение уйдёт клиенту"""
    
    send_message(token, OWNER_ID, msg)
    print(f"[{time.strftime('%H:%M:%S')}] 📩 {name}: {text[:50]}", flush=True)

def reply_to_client(token, owner_peer_id, text):
    """Отправляет ответ клиенту от имени сообщества"""
    client_peer_id = reply_map.get(owner_peer_id)
    
    if client_peer_id:
        send_message(token, client_peer_id, text)
        print(f"[{time.strftime('%H:%M:%S')}] 📤 Ответ → {client_peer_id}", flush=True)
        return True
    
    return False

def get_longpoll():
    try:
        params = {"access_token": GROUP_TOKEN, "group_id": GROUP_ID, "v": V}
        resp = requests.get(VK_URL + "groups.getLongPollServer", params=params, timeout=10).json()
        
        if "error" in resp:
            return None, None, None
        
        server = resp["response"]["server"]
        key = resp["response"]["key"]
        ts = resp["response"]["ts"]
        
        if not server.startswith("http"):
            server = "https://" + server
        
        return server, key, ts
    except:
        return None, None, None

def listen(server, key, ts):
    try:
        params = {"act": "a_check", "key": key, "ts": ts, "wait": 5}
        resp = requests.get(server, params=params, timeout=10).json()
        
        if "failed" in resp:
            return None, []
        
        return resp["ts"], resp.get("updates", [])
    except:
        return ts, []

if __name__ == "__main__":
    print(f"🤖 БОТ ЗАПУЩЕН", flush=True)
    print(f"📩 ЛС → vk.com/id{OWNER_ID}", flush=True)
    print(f"📤 Ответ через «Ответить»", flush=True)
    print(f"⏱️ Пиар каждые {SPAM_INTERVAL} сек\n", flush=True)
    
    msg_index = 0
    round_num = 0
    last_spam = 0
    
    server, key, ts = get_longpoll()
    if server:
        print("👂 Слушаю...\n", flush=True)
    
    while True:
        try:
            if server:
                new_ts, updates = listen(server, key, ts)
                
                if new_ts:
                    ts = new_ts
                
                for upd in updates:
                    if upd.get("type") == "message_new":
                        msg = upd.get("object", {}).get("message", {})
                        peer_id = msg.get("peer_id", 0)
                        from_id = msg.get("from_id", 0)
                        text = msg.get("text", "")
                        action = msg.get("action", {})
                        reply_to = msg.get("reply_message", {})
                        
                        # === ВЛАДЕЛЕЦ ОТВЕЧАЕТ (нажал «Ответить») ===
                        if from_id == OWNER_ID and peer_id < 2000000000:
                            if reply_to:
                                # Ответ на пересланное сообщение → шлём клиенту
                                reply_to_client(GROUP_TOKEN, peer_id, text)
                            else:
                                # Обычное сообщение от владельца — игнорим или обновляем связку
                                pass
                        
                        # === ЛС СООБЩЕСТВА (клиент пишет) ===
                        elif peer_id < 2000000000 and from_id > 0 and from_id != OWNER_ID and not action:
                            forward_to_owner(GROUP_TOKEN, from_id, text, peer_id)
                        
                        # === ДОБАВИЛИ В БЕСЕДУ ===
                        if peer_id > 2000000000 and action:
                            if action.get("type") == "chat_invite_user":
                                if action.get("member_id") == -GROUP_ID:
                                    print(f"[{time.strftime('%H:%M:%S')}] 🎯 Беседа {peer_id}", flush=True)
                                    msg_text = MESSAGES[msg_index % len(MESSAGES)]
                                    msg_index += 1
                                    send_message(GROUP_TOKEN, peer_id, msg_text)
            
            # === ПИАР ===
            if time.time() - last_spam >= SPAM_INTERVAL:
                round_num += 1
                chats = load_chats()
                
                if chats:
                    message = MESSAGES[msg_index % len(MESSAGES)]
                    msg_index += 1
                    
                    print(f"[{time.strftime('%H:%M:%S')}] 🔄 КРУГ {round_num}", flush=True)
                    
                    ok = 0
                    for chat_id in chats:
                        if send_message(GROUP_TOKEN, int(chat_id), message):
                            ok += 1
                            time.sleep(SEND_DELAY)
                    
                    print(f"[{time.strftime('%H:%M:%S')}] ✅ {ok}/{len(chats)}", flush=True)
                
                last_spam = time.time()
            
            time.sleep(1)
            
        except KeyboardInterrupt:
            print(f"\n👋 Завершено", flush=True)
            break
        except:
            time.sleep(5)
            server, key, ts = get_longpoll()

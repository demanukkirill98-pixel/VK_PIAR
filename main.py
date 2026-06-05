import requests
import time
import os

# ========== НАСТРОЙКИ ==========
GROUP_TOKEN = "vk1.a.GENAzRdaR86f91rPAydFj660SgWD7ylgOKpjwrrPaDtgE64s3ZSMn02sa_QPL7IKcOsFIEgMK17_DlaTsjXVlpJb-a4eLqQcbEfCA4OnTcqbn5J5cjqwh-eyKrwxFbmdgJSKMY8PgIiwj8DRhOaOU3DvdDchvGw5ebC-ysGXDA9Cyg0-knFBsdhf_o__aoKHrR0RceQB658D-WjG5xBbqg"
GROUP_ID = 239058698

MESSAGES = [
    """🔥 Давно хотел создать топовый проект?

Тогда тебе к нам!

👾 Лучшая студия GTA SAMP, CRMP SKREIFF SHOP

✅ Плюсы: низкие цены, выгодные товары, быстро и качественно
❌ Минусы: их нет

💻 Делаем: игры, сайты, форумы, ботов ВК/ТГ, автопиары

📩 По всем вопросам: vk.com/id835770623""",

    """🎮 SKREIFF SHOP — топовая студия

⚡ GTA SAMP / CRMP
⚡ Игры, сайты, форумы
⚡ Боты ВК и Telegram
⚡ Автопиар

Низкие цены, быстро, качественно!

📩 vk.com/id835770623""",

    """💎 Нужен крутой проект?

SKREIFF SHOP — студия с опытом

✔️ Разработка игр
✔️ Создание сайтов
✔️ Боты любой сложности
✔️ Автопиар
✔️ Готовые решения

По всем вопросам: vk.com/id835770623"""
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
            else:
                return False
        return True
    except:
        return False

if __name__ == "__main__":
    print(f"🤖 БОТ ЗАПУЩЕН", flush=True)
    print(f"⏱️ Интервал между кругами: {SPAM_INTERVAL} сек", flush=True)
    print(f"⏱️ Пауза между чатами: {SEND_DELAY} сек\n", flush=True)
    
    msg_index = 0
    round_num = 0
    
    while True:
        try:
            round_num += 1
            chats = load_chats()
            
            if not chats:
                print(f"[{time.strftime('%H:%M:%S')}] 📭 Нет чатов. Жду 30 сек...", flush=True)
                time.sleep(30)
                continue
            
            message = MESSAGES[msg_index % len(MESSAGES)]
            msg_index += 1
            total = len(chats)
            
            print(f"\n{'='*40}", flush=True)
            print(f"[{time.strftime('%H:%M:%S')}] 🔄 КРУГ {round_num} | Сообщение #{msg_index}", flush=True)
            print(f"📋 Чатов: {total}", flush=True)
            print(f"{'='*40}", flush=True)
            
            ok = 0
            skip = 0
            start_time = time.time()
            
            for i, chat_id in enumerate(chats, 1):
                try:
                    peer_id = int(chat_id)
                    result = send_message(GROUP_TOKEN, peer_id, message)
                    
                    if result:
                        print(f"  [{i}/{total}] ✅ {peer_id}", flush=True)
                        ok += 1
                        time.sleep(SEND_DELAY)
                    else:
                        skip += 1
                    
                except:
                    skip += 1
                    continue
            
            elapsed = int(time.time() - start_time)
            print(f"\n[{time.strftime('%H:%M:%S')}] ✅ Отправлено: {ok} | ⏭️ Пропущено: {skip} | ⏱️ {elapsed} сек", flush=True)
            print(f"[{time.strftime('%H:%M:%S')}] ⏰ Жду {SPAM_INTERVAL} сек до следующего круга...", flush=True)
            time.sleep(SPAM_INTERVAL)
            
        except KeyboardInterrupt:
            print(f"\n👋 Завершено. Кругов: {round_num}", flush=True)
            break
        except:
            time.sleep(5)

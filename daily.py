import requests
import os

TELEGRAM_TOKEN = os.environ.get("8446915676:AAExeLkEO92P3L8D57Kv-cSe_AhMP_tNq9c")
TELEGRAM_CHAT_ID = os.environ.get("7529192361")

# ====== 안전 확인 ======
if not TOKEN:
    raise Exception("TELEGRAM_TOKEN 없음")

if not CHAT_ID:
    raise Exception("TELEGRAM_CHAT_ID 없음")

# ====== 네이버 상한가 API ======
url = "https://m.stock.naver.com/api/sise/siseUpperLimit"

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

res = requests.get(url, headers=headers)

if res.status_code != 200:
    raise Exception("네이버 API 실패")

data = res.json()

stocks = []

if "result" in data:
    for item in data["result"]:
        name = item.get("itemName")
        if name:
            stocks.append(name)

if stocks:
    message = "📈 오늘의 상한가 종목\n\n"
    for s in stocks:
        message += f"- {s}\n"
else:
    message = "📉 오늘 상한가 종목 없음"

# ====== 텔레그램 직접 호출 ======
send_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

payload = {
    "chat_id": CHAT_ID,
    "text": message
}

telegram_res = requests.post(send_url, data=payload)

if telegram_res.status_code != 200:
    raise Exception("텔레그램 전송 실패")

print("전송 완료")

# ===== 텔레그램 전송 =====
bot.send_message(chat_id=CHAT_ID, text=message)

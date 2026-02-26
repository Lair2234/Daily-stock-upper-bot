import requests
import os

TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# ====== 안전 확인 ======
if not TOKEN:
    raise Exception("TELEGRAM_TOKEN 없음")

if not CHAT_ID:
    raise Exception("TELEGRAM_CHAT_ID 없음")

# ====== 네이버 상한가 API ======
url = "https://m.stock.naver.com/api/sise/siseUpperLimit"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Referer": "https://m.stock.naver.com/"
}

res = requests.get(url, headers=headers)

print("status:", res.status_code)
print("response:", res.text[:500])

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

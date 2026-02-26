import requests
import os
import telegram

# ===== 텔레그램 설정 =====
TOKEN = os.environ.get("8446915676:AAExeLkEO92P3L8D57Kv-cSe_AhMP_tNq9c")
CHAT_ID = os.environ.get("7529192361")

bot = telegram.Bot(token=TOKEN)

# ===== 네이버 상한가 데이터 (JSON 방식) =====
url = "https://m.stock.naver.com/api/sise/siseUpperLimit"

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

response = requests.get(url, headers=headers)

if response.status_code != 200:
    bot.send_message(chat_id=CHAT_ID, text="❌ 데이터 요청 실패")
    raise Exception("데이터 요청 실패")

data = response.json()

stocks = []

if "result" in data:
    for item in data["result"]:
        name = item.get("itemName")
        if name:
            stocks.append(name)

# ===== 메시지 구성 =====
if stocks:
    message = "📈 오늘의 상한가 종목\n\n"
    for stock in stocks:
        message += f"- {stock}\n"
else:
    message = "📉 오늘 상한가 종목 없음"

# ===== 텔레그램 전송 =====
bot.send_message(chat_id=CHAT_ID, text=message)

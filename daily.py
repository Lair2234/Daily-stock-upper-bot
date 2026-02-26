import requests
from bs4 import BeautifulSoup
import os
import telegram

# ===== 텔레그램 설정 =====
TOKEN = os.environ.get("8446915676:AAExeLkEO92P3L8D57Kv-cSe_AhMP_tNq9c")
CHAT_ID = os.environ.get("7529192361")

bot = telegram.Bot(token=TOKEN)

# ===== 네이버 상한가 URL =====
url = "https://finance.naver.com/sise/sise_upper.naver"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

response = requests.get(url, headers=headers)

if response.status_code != 200:
    bot.send_message(chat_id=CHAT_ID, text="❌ 네이버 페이지 접근 실패")
    raise Exception("페이지 접근 실패")

soup = BeautifulSoup(response.text, "html.parser")

# 테이블 선택
table = soup.select_one("table.type_2")

stocks = []

if table:
    rows = table.find_all("tr")
    for row in rows:
        cols = row.find_all("td")
        if len(cols) > 1:
            name = cols[1].text.strip()
            if name:
                stocks.append(name)

# ===== 메시지 구성 =====
if stocks:
    message = "📈 오늘의 상한가 종목\n\n"
    for stock in stocks:
        message += f"- {stock}\n"
else:
    message = "📉 오늘 상한가 종목 없음 또는 크롤링 실패"

# ===== 텔레그램 전송 =====
bot.send_message(chat_id=CHAT_ID, text=message)

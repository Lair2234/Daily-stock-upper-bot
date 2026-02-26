import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# GitHub Secrets에 저장한 값
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

if not TOKEN:
    raise Exception("TELEGRAM_TOKEN 없음")

if not CHAT_ID:
    raise Exception("TELEGRAM_CHAT_ID 없음")

# 네이버 상한가 페이지
url = "https://finance.naver.com/sise/sise_upper.naver"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

res = requests.get(url, headers=headers)

if res.status_code != 200:
    raise Exception("네이버 페이지 요청 실패")

soup = BeautifulSoup(res.text, "html.parser")
rows = soup.select("table.type_2 tr")

stocks = []

for row in rows:
    cols = row.find_all("td")
    if len(cols) > 1:
        name = cols[1].text.strip()
        price = cols[2].text.strip()
        stocks.append(f"{name} ({price})")

today = datetime.now().strftime("%Y-%m-%d")

if stocks:
    message = f"[{today}] 오늘의 상한가 종목\n\n" + "\n".join(stocks)
else:
    message = f"[{today}] 오늘 상한가 종목 없음"

# 텔레그램 전송
telegram_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

data = {
    "chat_id": CHAT_ID,
    "text": message
}

tg_res = requests.post(telegram_url, data=data)

if tg_res.status_code != 200:
    raise Exception("텔레그램 전송 실패")

print("전송 완료")

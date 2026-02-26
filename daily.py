import requests
from bs4 import BeautifulSoup
import telegram
import os

# 텔레그램 정보 (GitHub Secrets에서 가져옴)
TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['TELEGRAM_CHAT_ID']

bot = telegram.Bot(token=TOKEN)

# 네이버 상한가 페이지
url = "https://finance.naver.com/sise/sise_upper.naver"
headers = {"User-Agent": "Mozilla/5.0"}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")

table = soup.find("table", {"class": "type_2"})

stocks = []

for row in table.find_all("tr"):
    cols = row.find_all("td")
    if len(cols) > 1:
        name = cols[1].text.strip()
        stocks.append(name)

if stocks:
    message = "📈 오늘의 상한가 종목\n\n"
    for stock in stocks:
        message += f"- {stock}\n"
else:
    message = "상한가 종목 없음"

bot.send_message(chat_id=CHAT_ID, text=message)

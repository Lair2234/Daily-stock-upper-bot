import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

if not TOKEN or not CHAT_ID:
    raise Exception("텔레그램 환경변수 없음")

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# ==============================
# 1️⃣ 상한가 목록 가져오기
# ==============================
def get_upper_stocks():
    url = "https://finance.naver.com/sise/sise_upper.naver"
    res = requests.get(url, headers=HEADERS)

    if res.status_code != 200:
        raise Exception("상한가 페이지 요청 실패")

    soup = BeautifulSoup(res.text, "html.parser")

    stocks = []

    # 종목 링크 기준으로 추출 (가장 안전)
    links = soup.select("table.type_2 a.tltle")

    for link in links:
        name = link.text.strip()
        code = link["href"].split("=")[-1]

        row = link.find_parent("tr")
        cols = row.find_all("td")

        if len(cols) >= 3:
            price = cols[2].text.strip()

            stocks.append({
                "name": name,
                "code": code,
                "price": price
            })

    return stocks


# ==============================
# 2️⃣ 거래대금 + 수급 정보
# ==============================
def get_stock_detail(code):
    url = f"https://finance.naver.com/item/main.naver?code={code}"
    res = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(res.text, "html.parser")

    # 거래대금
    value = soup.select_one("table.no_info td span")
    trading_value = value.text.strip() if value else "확인불가"

    # 외인/기관/프로그램 (간단 버전)
    investor_table = soup.select("table.tb_type1 tr")

    foreign = "확인불가"
    institution = "확인불가"

    for row in investor_table:
        th = row.find("th")
        if th:
            title = th.text.strip()
            if "외국인" in title:
                foreign = row.find_all("td")[-1].text.strip()
            if "기관" in title:
                institution = row.find_all("td")[-1].text.strip()

    return trading_value, foreign, institution


# ==============================
# 3️⃣ 뉴스 3개 가져오기
# ==============================
def get_news(name):
    search_url = f"https://search.naver.com/search.naver?where=news&query={name}"
    res = requests.get(search_url, headers=HEADERS)
    soup = BeautifulSoup(res.text, "html.parser")

    titles = soup.select("a.news_tit")[:3]

    news_list = []

    for t in titles:
        title = t.text.strip()
        news_list.append(title)

    return news_list


# ==============================
# 4️⃣ 메시지 조립
# ==============================
stocks = get_upper_stocks()
today = datetime.now().strftime("%Y-%m-%d")

if not stocks:
    message = f"[{today}] 오늘 상한가 종목 없음"
else:
    message_lines = []

    for stock in stocks:
        trading_value, foreign, institution = get_stock_detail(stock["code"])
        news_list = get_news(stock["name"])

        stock_block = (
            f"📈 {stock['name']} ({stock['price']})\n"
            f"• 거래대금: {trading_value}\n"
            f"• 외인: {foreign}\n"
            f"• 기관: {institution}\n"
        )

        if news_list:
            stock_block += "\n최근 뉴스:\n"
            for n in news_list:
                stock_block += f"- {n}\n"

        message_lines.append(stock_block)

    message = f"[{today}] 오늘의 상한가 종목\n\n" + "\n\n".join(message_lines)


# ==============================
# 텔레그램 전송
# ==============================
telegram_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

requests.post(
    telegram_url,
    data={
        "chat_id": CHAT_ID,
        "text": message
    }
)

print("전송 완료")

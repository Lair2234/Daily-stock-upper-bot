import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

if not TOKEN or not CHAT_ID:
    raise Exception("텔레그램 환경변수 없음")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://finance.naver.com/",
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

    table = soup.find("table", {"class": "type_2"})
    if not table:
        return stocks

    rows = table.find("tbody").find_all("tr")

    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 3:
            continue

        name_tag = cols[1].find("a")
        if not name_tag:
            continue

        name = name_tag.text.strip()
        code = name_tag["href"].split("=")[-1]
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
def get_upper_stocks():
    url = "http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "http://data.krx.co.kr/"
    }

    data = {
        "bld": "dbms/MDC/STAT/standard/MDCSTAT01501",
        "mktId": "ALL",
        "trdDd": datetime.now().strftime("%Y%m%d"),
        "share": "1",
        "money": "1",
        "csvxls_isNo": "false"
    }

    res = requests.post(url, headers=headers, data=data)

    if res.status_code != 200:
        raise Exception("KRX 요청 실패")

    json_data = res.json()
    stocks = []

    if "OutBlock_1" not in json_data:
        return stocks

    for row in json_data["OutBlock_1"]:
        if row["UPDN_RATE"] == "30.00":  # 상한가 기준
            stocks.append({
                "name": row["ISU_NM"],
                "code": row["ISU_SRT_CD"],
                "price": row["TDD_CLSPRC"]
            })

    return stocks
    

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

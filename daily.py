import os
import requests
import csv
from io import StringIO
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup

# ==============================
# 텔레그램 설정
# ==============================
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

if not TOKEN or not CHAT_ID:
    raise Exception("텔레그램 환경변수 없음")

# ==============================
# 세션
# ==============================
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0"
})

# ==============================
# 날짜 결정 (20시 이전이면 전날 데이터)
# ==============================
def get_target_date():
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)

    if now.hour < 20:
        target = now - timedelta(days=1)
    else:
        target = now

    return target.strftime("%Y%m%d")

# ==============================
# OTP 생성
# ==============================
def generate_otp(today):
    otp_url = "https://data.krx.co.kr/comm/fileDn/GenerateOTP/generate.cmd"

    data = {
        "searchType": "1",
        "mktId": "ALL",
        "trdDd": today,
        "csvxls_isNo": "false",
        "name": "fileDown",
        "url": "dbms/MDC/STAT/standard/MDCSTAT03901"
    }

    res = session.post(
        otp_url,
        data=data,
        headers={
            "Referer": "https://data.krx.co.kr/contents/MDC/MDI/mdiLoader",
            "Origin": "https://data.krx.co.kr"
        }
    )

    return res.text.strip()

# ==============================
# KRX 데이터 다운로드
# ==============================
def get_krx_data(today):
    otp = generate_otp(today)

    download_url = "https://data.krx.co.kr/comm/fileDn/download_csv/download.cmd"

    res = session.post(
        download_url,
        data={"code": otp},
        headers={
            "Referer": "https://data.krx.co.kr/contents/MDC/MDI/mdiLoader",
            "Origin": "https://data.krx.co.kr"
        }
    )

    if res.status_code != 200:
        raise Exception("KRX 다운로드 실패")

    if not res.content:
        raise Exception("KRX 응답이 비어 있음 (아직 데이터 생성 안 됨)")

    decoded = res.content.decode("euc-kr")

    f = StringIO(decoded)
    reader = csv.reader(f)
    rows = list(reader)

    if len(rows) < 2:
        raise Exception("CSV 데이터가 비어 있음")

    headers = rows[0]
    data_rows = rows[1:]

    return headers, data_rows

# ==============================
# 컬럼 찾기
# ==============================
def find_column(headers, keyword):
    for i, col in enumerate(headers):
        if keyword in col:
            return i
    return -1

# ==============================
# 상한가 종목 추출
# ==============================
def get_upper_stocks():
    today = get_target_date()
    headers, rows = get_krx_data(today)

    name_idx = find_column(headers, "종목명")
    price_idx = find_column(headers, "종가")
    change_idx = find_column(headers, "등락률")
    value_idx = find_column(headers, "거래대금")
    foreign_idx = find_column(headers, "외국인")
    inst_idx = find_column(headers, "기관")

    stocks = []

    for row in rows:
        try:
            change_rate = row[change_idx].replace("%", "").strip()

            if float(change_rate) >= 29.9:
                stocks.append({
                    "name": row[name_idx],
                    "price": row[price_idx],
                    "value": row[value_idx],
                    "foreign": row[foreign_idx],
                    "institution": row[inst_idx]
                })
        except:
            continue

    return stocks, today

# ==============================
# 뉴스 3개 가져오기
# ==============================
def get_news(name):
    url = f"https://search.naver.com/search.naver?where=news&query={name}"
    res = session.get(url)
    soup = BeautifulSoup(res.text, "html.parser")
    titles = soup.select("a.news_tit")[:3]
    return [t.text.strip() for t in titles]

# ==============================
# 실행부
# ==============================
try:
    stocks, target_date = get_upper_stocks()

    today_msg = datetime.now().strftime("%Y-%m-%d")

    if not stocks:
        message = f"[{today_msg}] ({target_date}) 상한가 종목 없음"
    else:
        message_lines = []

        for s in stocks:
            news_list = get_news(s["name"])

            block = (
                f"📈 {s['name']} ({s['price']})\n"
                f"- 거래대금: {s['value']}\n"
                f"- 외인 순매수: {s['foreign']}\n"
                f"- 기관 순매수: {s['institution']}\n"
            )

            if news_list:
                block += "\n최근 뉴스:\n"
                for n in news_list:
                    block += f"- {n}\n"

            message_lines.append(block)

        message = f"[{today_msg}] ({target_date}) 상한가 종목\n\n" + "\n\n".join(message_lines)

except Exception as e:
    message = f"KRX 데이터 수집 실패\n{e}"

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

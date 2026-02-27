import requests
import pandas as pd
from io import BytesIO
from datetime import datetime, timedelta
import os
import sys

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

OTP_URL = "http://data.krx.co.kr/comm/fileDn/GenerateOTP/generate.cmd"
DOWN_URL = "http://data.krx.co.kr/comm/fileDn/download_csv/download.cmd"

HEADERS = {
    "Referer": "http://data.krx.co.kr/contents/MDC/MDI/mdiLoader",
    "User-Agent": "Mozilla/5.0"
}


# ---------------------------
# 텔레그램 전송
# ---------------------------
def send_telegram(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ 텔레그램 환경변수 누락")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    requests.post(url, data=payload)


# ---------------------------
# KRX 데이터 요청
# ---------------------------
def get_krx_data(date_str):
    otp_data = {
        "mktId": "ALL",
        "trdDd": date_str,
        "share": "1",
        "money": "1",
        "csvxls_isNo": "false",
        "name": "fileDown",
        "url": "dbms/MDC/STAT/standard/MDCSTAT03901"
    }

    try:
        otp_res = requests.post(OTP_URL, data=otp_data, headers=HEADERS, timeout=10)

        if otp_res.status_code != 200:
            return None

        otp = otp_res.text.strip()
        if not otp:
            return None

        down_res = requests.post(DOWN_URL, data={"code": otp}, headers=HEADERS, timeout=10)

        if down_res.status_code != 200:
            return None

        df = pd.read_csv(BytesIO(down_res.content), encoding="euc-kr")

        if df.empty:
            return None

        return df

    except Exception as e:
        print("KRX 요청 실패:", e)
        return None


# ---------------------------
# 최근 거래일 자동 탐색
# ---------------------------
def find_latest_trading_day():
    today = datetime.now()

    for i in range(7):  # 최대 7일 탐색
        target_date = today - timedelta(days=i)
        date_str = target_date.strftime("%Y%m%d")
        print(f"🔎 {date_str} 조회 시도")

        df = get_krx_data(date_str)

        if df is not None:
            print(f"✅ 사용 날짜: {date_str}")
            return df, date_str

    return None, None


# ---------------------------
# 메인 실행
# ---------------------------
def main():

    df, used_date = find_latest_trading_day()

    if df is None:
        send_telegram("❌ 최근 7일 내 거래 데이터 없음")
        return

    # 컬럼 확인
    if "등락률" not in df.columns:
        send_telegram("❌ 등락률 컬럼 찾을 수 없음 (KRX 구조 변경 가능)")
        return

    # 등락률 숫자 변환 안전 처리
    df["등락률"] = (
        df["등락률"]
        .astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("%", "", regex=False)
    )

    df["등락률"] = pd.to_numeric(df["등락률"], errors="coerce")

    df = df.dropna(subset=["등락률"])

    # ETF/ETN 제거
    df = df[~df["종목명"].str.contains("ETF|ETN", na=False)]

    # 상위 10개 추출
    top10 = df.sort_values("등락률", ascending=False).head(10)

    message = f"📊 KRX 상승률 TOP10 ({used_date})\n\n"

    for i, row in enumerate(top10.itertuples(), 1):
        message += f"{i}. {row.종목명} ({round(row.등락률,2)}%)\n"

    # 텔레그램 글자수 제한 보호
    if len(message) > 4000:
        message = message[:3900] + "\n(이하 생략)"

    send_telegram(message)

    print("✅ 전송 완료")


if __name__ == "__main__":
    main()

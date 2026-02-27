import os
import time
import requests
import pandas as pd
from datetime import datetime, timedelta
from pykrx import stock
from bs4 import BeautifulSoup

TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

# ------------------ 텔레그램 ------------------

def send_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    requests.post(url, data=data, timeout=10)

# ------------------ 최근 영업일 찾기 ------------------

def get_recent_business_day():
    today = datetime.today()

    for i in range(7):
        date = (today - timedelta(days=i)).strftime("%Y%m%d")
        try:
            df = stock.get_market_ohlcv_by_ticker(date)
            if not df.empty:
                return date
        except:
            continue

    return None

# ------------------ 상한가 종목 ------------------

def get_limitup_stocks(date):
    try:
        df = stock.get_market_ohlcv_by_ticker(date)
        df = df[df["등락률"] >= 29]   # 상한가 기준
        return df
    except:
        return pd.DataFrame()

# ------------------ 거래대금 ------------------

def get_trading_value(date):
    try:
        return stock.get_market_trading_value_by_ticker(date)
    except:
        return pd.DataFrame()

# ------------------ 외국인/기관 ------------------

def get_investor_flow(date):
    try:
        return stock.get_market_trading_value_by_investor(date)
    except:
        return pd.DataFrame()

# ------------------ KRX 테마 ------------------

def build_theme_map():
    theme_map = {}
    try:
        theme_list = stock.get_theme_list()

        for theme_code, theme_name in theme_list.items():
            tickers = stock.get_theme_portfolio(theme_code)
            for ticker in tickers:
                theme_map.setdefault(ticker, []).append(theme_name)
    except:
        pass

    return theme_map

# ------------------ 뉴스 ------------------

def get_latest_news(name):
    try:
        query = f"{name} 상한가"
        url = f"https://search.naver.com/search.naver?where=news&query={query}"
        headers = {"User-Agent": "Mozilla/5.0"}

        html = requests.get(url, headers=headers, timeout=10).text
        soup = BeautifulSoup(html, "html.parser")

        news = soup.select_one("a.news_tit")

        if news:
            title = news.text.strip()
            link = news["href"]
            return f"{title}\n{link}"

        return "관련 뉴스 없음"

    except:
        return "뉴스 수집 실패"

# ------------------ 메인 ------------------

def main():

    date = get_recent_business_day()

    if date is None:
        send_message("⚠️ 최근 영업일 데이터를 찾을 수 없습니다.")
        return

    limitup_df = get_limitup_stocks(date)

    if limitup_df.empty:
        send_message(f"📅 {date} 상한가 종목 없음")
        return

    trading_value_df = get_trading_value(date)
    investor_df = get_investor_flow(date)
    theme_map = build_theme_map()

    message = f"📅 {date} 상한가 종목\n\n"

    for ticker in limitup_df.index:

        name = stock.get_market_ticker_name(ticker)
        change = limitup_df.loc[ticker]["등락률"]

        # 거래대금
        trading_value = trading_value_df.loc[ticker]["거래대금"] \
            if ticker in trading_value_df.index else 0

        # 외국인/기관 순매수
        try:
            foreign = investor_df.loc["외국인", ticker]
        except:
            foreign = 0

        try:
            institution = investor_df.loc["기관합계", ticker]
        except:
            institution = 0

        # 테마
        themes = theme_map.get(ticker, ["테마없음"])

        # 뉴스
        news = get_latest_news(name)
        time.sleep(1)

        message += f"📈 <b>{name} ({ticker})</b>\n"
        message += f"등락률: {change:.2f}%\n"
        message += f"🧠 테마: {', '.join(themes)}\n"
        message += f"💰 거래대금: {int(trading_value):,}원\n"
        message += f"🌍 외국인 순매수: {int(foreign):,}원\n"
        message += f"🏢 기관 순매수: {int(institution):,}원\n"
        message += f"📰 상승 이유:\n{news}\n"
        message += "----------------------\n\n"

    send_message(message)


if __name__ == "__main__":
    main()

import os
import time
import requests
import pandas as pd
from datetime import datetime
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
    requests.post(url, data=data)

# ------------------ 상한가 종목 ------------------

def get_limitup_stocks():
    today = datetime.today().strftime("%Y%m%d")
    df = stock.get_market_ohlcv_by_ticker(today)

    # 상한가 기준 (등락률 29% 이상)
    df = df[df["등락률"] >= 29]

    return today, df

# ------------------ 거래대금 ------------------

def get_trading_value(date):
    return stock.get_market_trading_value_by_ticker(date)

# ------------------ 외국인/기관 ------------------

def get_investor_flow(date):
    return stock.get_market_trading_value_by_investor(date)

# ------------------ KRX 테마 ------------------

def build_theme_map():
    theme_map = {}
    theme_list = stock.get_theme_list()

    for theme_code, theme_name in theme_list.items():
        tickers = stock.get_theme_portfolio(theme_code)
        for ticker in tickers:
            theme_map.setdefault(ticker, []).append(theme_name)

    return theme_map

# ------------------ 뉴스 크롤링 ------------------

def get_latest_news(name):
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

# ------------------ 메인 ------------------

def main():
    today, limitup_df = get_limitup_stocks()

    if limitup_df.empty:
        send_message("📭 오늘 상한가 종목 없음")
        return

    trading_value_df = get_trading_value(today)
    investor_df = get_investor_flow(today)
    theme_map = build_theme_map()

    message = f"📅 {today} 상한가 종목\n\n"

    for ticker in limitup_df.index:

        name = stock.get_market_ticker_name(ticker)
        change = limitup_df.loc[ticker]["등락률"]

        # 거래대금
        trading_value = trading_value_df.loc[ticker]["거래대금"]

        # 외국인/기관 순매수
        foreign = investor_df.loc["외국인", ticker]
        institution = investor_df.loc["기관합계", ticker]

        # 테마
        themes = theme_map.get(ticker, ["테마없음"])

        # 뉴스
        news = get_latest_news(name)
        time.sleep(1)  # 네이버 차단 방지

        message += f"📈 <b>{name} ({ticker})</b>\n"
        message += f"등락률: {change:.2f}%\n"
        message += f"🧠 테마: {', '.join(themes)}\n"
        message += f"💰 거래대금: {trading_value:,}원\n"
        message += f"🌍 외국인 순매수: {foreign:,}원\n"
        message += f"🏢 기관 순매수: {institution:,}원\n"
        message += f"📰 상승 이유:\n{news}\n"
        message += "----------------------\n\n"

    send_message(message)


if __name__ == "__main__":
    main()

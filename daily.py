from datetime import datetime, timedelta, timezone
from pykrx import stock

def debug_test():

    KST = timezone(timedelta(hours=9))
    today = datetime.now(KST)

    print("===== 날짜 테스트 시작 =====")

    for i in range(7):
        date = (today - timedelta(days=i)).strftime("%Y%m%d")
        print(f"\n🔍 테스트 날짜: {date}")

        try:
            df = stock.get_market_ohlcv_by_ticker(date)

            if df.empty:
                print("❌ 데이터 없음")
            else:
                print("✅ 데이터 있음")
                print("컬럼:", df.columns.tolist())
                print(df.head())
        except Exception as e:
            print("🚨 에러 발생:", e)


if __name__ == "__main__":
    debug_test()

"""yfinance를 pykrx 호환 인터페이스로 래핑 (글로벌 IP에서 작동)"""
import yfinance as yf
import pandas as pd

def get_market_ohlcv(start, end, ticker):
    """
    pykrx.stock.get_market_ohlcv 호환 함수
    - start/end: 'YYYYMMDD' 문자열
    - ticker: '005930' 형식 (KOSPI/KOSDAQ 자동 처리)
    - 반환: DataFrame with columns [시가, 고가, 저가, 종가, 거래량], index=날짜
    """
    # YYYYMMDD → YYYY-MM-DD
    s = f"{start[:4]}-{start[4:6]}-{start[6:]}"
    # end에 +1일 (yfinance end는 exclusive)
    e_dt = pd.to_datetime(f"{end[:4]}-{end[4:6]}-{end[6:]}") + pd.Timedelta(days=1)
    e = e_dt.strftime("%Y-%m-%d")

    # KOSPI/KOSDAQ 자동 시도
    for suffix in (".KS", ".KQ"):
        try:
            t = yf.Ticker(f"{ticker}{suffix}")
            df = t.history(start=s, end=e, auto_adjust=False)
            if df is None or df.empty:
                continue
            # NaN 행 제거 (당일 미공개 데이터 등)
            df = df.dropna(subset=["Open", "High", "Low", "Close"])
            if df.empty:
                continue
            # 컬럼 한국어로 변환
            out = pd.DataFrame({
                "시가": df["Open"].astype(int),
                "고가": df["High"].astype(int),
                "저가": df["Low"].astype(int),
                "종가": df["Close"].astype(int),
                "거래량": df["Volume"].astype(int),
            })
            # tz 제거 + 날짜만
            out.index = pd.to_datetime(df.index).tz_localize(None).normalize()
            out.index.name = "날짜"
            return out
        except Exception:
            continue
    return pd.DataFrame()

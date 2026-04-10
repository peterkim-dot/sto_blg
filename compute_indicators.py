"""분석 대상 종목의 기술적 지표 계산"""
import sys, json
sys.stdout.reconfigure(encoding='utf-8')
from datetime import datetime, timedelta
from pykrx import stock
import numpy as np

TARGETS = [
    ("009150", "삼성전기"),
    ("000660", "SK하이닉스"),
    ("105560", "KB금융"),
    ("012450", "한화에어로스페이스"),
    ("373220", "LG에너지솔루션"),
]

end = datetime(2026, 4, 10)
start = end - timedelta(days=180)
result = {}

for ticker, name in TARGETS:
    df = stock.get_market_ohlcv(start.strftime("%Y%m%d"), end.strftime("%Y%m%d"), ticker)
    if df.empty: continue
    close = df["종가"]
    high = df["고가"]
    low = df["저가"]
    vol = df["거래량"]

    # MA
    ma5 = close.rolling(5).mean().iloc[-1]
    ma20 = close.rolling(20).mean().iloc[-1]
    ma60 = close.rolling(60).mean().iloc[-1]

    # RSI(14)
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    rsi_now = rsi.iloc[-1]

    # MACD
    ema12 = close.ewm(span=12).mean()
    ema26 = close.ewm(span=26).mean()
    macd = (ema12 - ema26).iloc[-1]
    sig = (ema12 - ema26).ewm(span=9).mean().iloc[-1]
    macd_hist = macd - sig

    # Bollinger Bands
    bb_mid = close.rolling(20).mean().iloc[-1]
    bb_std = close.rolling(20).std().iloc[-1]
    bb_up = bb_mid + 2*bb_std
    bb_lo = bb_mid - 2*bb_std

    # 거래량 비율
    vol_avg20 = vol.rolling(20).mean().iloc[-1]
    vol_ratio = vol.iloc[-1] / vol_avg20

    # 최근 60일 고저
    high_60 = high.tail(60).max()
    low_60 = low.tail(60).min()

    cur = close.iloc[-1]

    result[name] = {
        "ticker": ticker,
        "현재가": int(cur),
        "MA5": int(ma5),
        "MA20": int(ma20),
        "MA60": int(ma60),
        "정배열": bool(ma5 > ma20 > ma60),
        "역배열": bool(ma5 < ma20 < ma60),
        "RSI": round(rsi_now, 1),
        "RSI상태": "과매수" if rsi_now > 70 else ("과매도" if rsi_now < 30 else "중립"),
        "MACD": round(macd, 0),
        "Signal": round(sig, 0),
        "MACD_Hist": round(macd_hist, 0),
        "MACD골든크로스": bool(macd > sig),
        "BB상단": int(bb_up),
        "BB하단": int(bb_lo),
        "BB위치": "상단돌파" if cur > bb_up else ("하단이탈" if cur < bb_lo else "밴드내"),
        "BB%": round((cur - bb_lo) / (bb_up - bb_lo) * 100, 1),
        "거래량배수": round(vol_ratio, 2),
        "60일고가": int(high_60),
        "60일저가": int(low_60),
        "60일고가대비": round((cur - high_60) / high_60 * 100, 2),
    }

with open("indicators.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2, default=lambda x: bool(x) if hasattr(x, '__bool__') else str(x))

for name, d in result.items():
    print(f"\n{'='*50}")
    print(f"📊 {name} ({d['ticker']})")
    print(f"  현재가: {d['현재가']:,}")
    print(f"  MA5/20/60: {d['MA5']:,} / {d['MA20']:,} / {d['MA60']:,} | {'정배열✅' if d['정배열'] else ('역배열❌' if d['역배열'] else '혼조')}")
    print(f"  RSI(14): {d['RSI']} ({d['RSI상태']})")
    print(f"  MACD: {d['MACD']:.0f} / Signal: {d['Signal']:.0f} | {'골든크로스✅' if d['MACD골든크로스'] else '데드크로스❌'}")
    print(f"  BB: {d['BB하단']:,} ~ {d['BB상단']:,} | 위치: {d['BB위치']} ({d['BB%']}%)")
    print(f"  거래량 배수(20일평균 대비): {d['거래량배수']}x")
    print(f"  60일 고가/저가: {d['60일고가']:,} / {d['60일저가']:,} | 고가 대비 {d['60일고가대비']}%")

print("\n✅ 완료 → indicators.json")

"""주요 종목 데이터 직접 수집 (pykrx 단일종목 API 사용)"""
import sys, json
sys.stdout.reconfigure(encoding='utf-8')
from pykrx import stock
from datetime import datetime, timedelta

# 주요 종목 (대형주 + 인기 종목)
TICKERS = {
    "005930": "삼성전자",
    "000660": "SK하이닉스",
    "207940": "삼성바이오로직스",
    "373220": "LG에너지솔루션",
    "005380": "현대차",
    "005935": "삼성전자우",
    "012450": "한화에어로스페이스",
    "068270": "셀트리온",
    "035420": "NAVER",
    "035720": "카카오",
    "000270": "기아",
    "105560": "KB금융",
    "055550": "신한지주",
    "032830": "삼성생명",
    "066570": "LG전자",
    "003670": "포스코퓨처엠",
    "005490": "POSCO홀딩스",
    "247540": "에코프로비엠",
    "086520": "에코프로",
    "042700": "한미반도체",
    "196170": "알테오젠",
    "028260": "삼성물산",
    "015760": "한국전력",
    "017670": "SK텔레콤",
    "030200": "KT",
    "009150": "삼성전기",
    "010130": "고려아연",
    "034730": "SK",
    "018260": "삼성에스디에스",
    "011200": "HMM",
}

start = "20260301"
end = "20260411"

results = []
for ticker, name in TICKERS.items():
    try:
        df = stock.get_market_ohlcv(start, end, ticker)
        if df.empty or len(df) < 2:
            continue
        last = df.iloc[-1]
        prev = df.iloc[-2]
        chg_pct = (last["종가"] - prev["종가"]) / prev["종가"] * 100
        # 5일 변화
        if len(df) >= 6:
            five_ago = df.iloc[-6]
            chg_5d = (last["종가"] - five_ago["종가"]) / five_ago["종가"] * 100
        else:
            chg_5d = None
        # 20일 변화
        if len(df) >= 21:
            twenty_ago = df.iloc[-21]
            chg_20d = (last["종가"] - twenty_ago["종가"]) / twenty_ago["종가"] * 100
        else:
            chg_20d = None
        results.append({
            "ticker": ticker,
            "name": name,
            "date": str(df.index[-1].date()),
            "close": int(last["종가"]),
            "open": int(last["시가"]),
            "high": int(last["고가"]),
            "low": int(last["저가"]),
            "volume": int(last["거래량"]),
            "prev_close": int(prev["종가"]),
            "chg_pct": round(chg_pct, 2),
            "chg_5d": round(chg_5d, 2) if chg_5d is not None else None,
            "chg_20d": round(chg_20d, 2) if chg_20d is not None else None,
            "high_20d": int(df["고가"].tail(20).max()),
            "low_20d": int(df["저가"].tail(20).min()),
        })
        print(f"✅ {name} ({ticker}): {int(last['종가']):,} ({chg_pct:+.2f}%)")
    except Exception as e:
        print(f"❌ {name}: {e}")

# 정렬: 등락률 기준
results.sort(key=lambda x: x["chg_pct"], reverse=True)

with open("market_data.json", "w", encoding="utf-8") as f:
    json.dump({"trade_date": results[0]["date"] if results else None, "stocks": results}, f, ensure_ascii=False, indent=2)

print(f"\n✅ 총 {len(results)}개 종목 수집 완료 → market_data.json")

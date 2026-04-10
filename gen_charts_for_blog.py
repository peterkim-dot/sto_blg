"""블로그용 종목별 분석 차트 생성"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
from datetime import datetime, timedelta
from pykrx import stock
from utils.chart_generator import generate_analysis_chart

OUT_DIR = "output/20260410/charts"
os.makedirs(OUT_DIR, exist_ok=True)

# 분석 대상: 핵심 종목 5개
TARGETS = [
    ("009150", "삼성전기"),
    ("000660", "SK하이닉스"),
    ("105560", "KB금융"),
    ("012450", "한화에어로스페이스"),
    ("373220", "LG에너지솔루션"),
]

# 120일 데이터
end = datetime(2026, 4, 10)
start = end - timedelta(days=180)
start_s = start.strftime("%Y%m%d")
end_s = end.strftime("%Y%m%d")

for ticker, name in TARGETS:
    print(f"📊 {name} ({ticker}) 차트 생성 중...")
    df = stock.get_market_ohlcv(start_s, end_s, ticker)
    if df.empty:
        print(f"  ❌ 데이터 없음")
        continue
    df.index.name = "Date"
    path = generate_analysis_chart(df, name, "일봉", OUT_DIR)
    if path:
        print(f"  ✅ {os.path.basename(path)}")
    else:
        print(f"  ❌ 생성 실패")

print("\n✅ 완료")

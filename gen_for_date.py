"""특정 거래일 기준으로 데이터/지표/차트/섹터 일괄 생성"""
import sys, os, json
sys.stdout.reconfigure(encoding='utf-8')
from pykrx import stock
from datetime import datetime, timedelta
from utils.chart_generator import generate_analysis_chart

if len(sys.argv) < 2:
    sys.exit('Usage: gen_for_date.py YYYYMMDD')
target = sys.argv[1]
target_dt = datetime.strptime(target, '%Y%m%d')

TICKERS = {
    '005930': '삼성전자', '000660': 'SK하이닉스', '207940': '삼성바이오로직스',
    '373220': 'LG에너지솔루션', '005380': '현대차', '005935': '삼성전자우',
    '012450': '한화에어로스페이스', '068270': '셀트리온', '035420': 'NAVER',
    '035720': '카카오', '000270': '기아', '105560': 'KB금융',
    '055550': '신한지주', '032830': '삼성생명', '066570': 'LG전자',
    '003670': '포스코퓨처엠', '005490': 'POSCO홀딩스', '247540': '에코프로비엠',
    '086520': '에코프로', '042700': '한미반도체', '196170': '알테오젠',
    '028260': '삼성물산', '015760': '한국전력', '017670': 'SK텔레콤',
    '030200': 'KT', '009150': '삼성전기', '010130': '고려아연',
    '034730': 'SK', '018260': '삼성에스디에스', '011200': 'HMM',
}

start = (target_dt - timedelta(days=180)).strftime('%Y%m%d')
end = target

# 1. 시장 데이터
print(f'== {target} 데이터 수집 ==')
results = []
for ticker, name in TICKERS.items():
    df = stock.get_market_ohlcv(start, end, ticker)
    if df.empty or len(df) < 2:
        continue
    last = df.iloc[-1]; prev = df.iloc[-2]
    chg = (last['종가'] - prev['종가']) / prev['종가'] * 100
    chg_5d = ((last['종가'] - df.iloc[-6]['종가']) / df.iloc[-6]['종가'] * 100) if len(df) >= 6 else None
    chg_20d = ((last['종가'] - df.iloc[-21]['종가']) / df.iloc[-21]['종가'] * 100) if len(df) >= 21 else None
    results.append({
        'ticker': ticker, 'name': name, 'date': str(df.index[-1].date()),
        'close': int(last['종가']), 'open': int(last['시가']),
        'high': int(last['고가']), 'low': int(last['저가']),
        'volume': int(last['거래량']), 'prev_close': int(prev['종가']),
        'chg_pct': round(chg, 2),
        'chg_5d': round(chg_5d, 2) if chg_5d is not None else None,
        'chg_20d': round(chg_20d, 2) if chg_20d is not None else None,
        'high_20d': int(df['고가'].tail(20).max()),
        'low_20d': int(df['저가'].tail(20).min()),
    })
results.sort(key=lambda x: x['chg_pct'], reverse=True)
trade_date = results[0]['date'] if results else None
print(f'거래일: {trade_date}, 종목수: {len(results)}')

day_dir = trade_date.replace('-', '')
os.makedirs(f'output/{day_dir}/charts', exist_ok=True)

market_data = {'trade_date': trade_date, 'stocks': results}
with open(f'output/{day_dir}/market_data.json', 'w', encoding='utf-8') as f:
    json.dump(market_data, f, ensure_ascii=False, indent=2)

# 2. 지표 (5종목)
TARGETS = [('009150','삼성전기'),('000660','SK하이닉스'),('105560','KB금융'),('012450','한화에어로스페이스'),('373220','LG에너지솔루션')]
indicators = {}
print('== 지표 계산 ==')
for ticker, name in TARGETS:
    df = stock.get_market_ohlcv(start, end, ticker)
    if df.empty: continue
    c = df['종가']; h = df['고가']; l = df['저가']; v = df['거래량']
    ma5=c.rolling(5).mean().iloc[-1]; ma20=c.rolling(20).mean().iloc[-1]; ma60=c.rolling(60).mean().iloc[-1]
    d2=c.diff(); g=d2.where(d2>0,0).rolling(14).mean(); lo=(-d2.where(d2<0,0)).rolling(14).mean()
    rsi=(100-(100/(1+g/lo))).iloc[-1]
    e12=c.ewm(span=12).mean(); e26=c.ewm(span=26).mean()
    macd=(e12-e26).iloc[-1]; sig=(e12-e26).ewm(span=9).mean().iloc[-1]
    bm=c.rolling(20).mean().iloc[-1]; bs=c.rolling(20).std().iloc[-1]; bu=bm+2*bs; bl=bm-2*bs
    cur=c.iloc[-1]
    indicators[name]={'ticker':ticker,'현재가':int(cur),'MA5':int(ma5),'MA20':int(ma20),'MA60':int(ma60),
        '정배열':bool(ma5>ma20>ma60),'RSI':round(float(rsi),1),
        'RSI상태':'과매수' if rsi>70 else('과매도' if rsi<30 else '중립'),
        'MACD':round(float(macd),0),'Signal':round(float(sig),0),'MACD골든크로스':bool(macd>sig),
        'BB상단':int(bu),'BB하단':int(bl),'BB%':round(float((cur-bl)/(bu-bl)*100),1),
        '거래량배수':round(float(v.iloc[-1]/v.rolling(20).mean().iloc[-1]),2),
        '60일고가':int(h.tail(60).max()),'60일저가':int(l.tail(60).min()),
        '60일고가대비':round(float((cur-h.tail(60).max())/h.tail(60).max()*100),2)}
    # 차트도 함께 생성
    df.index.name = 'Date'
    generate_analysis_chart(df, name, '일봉', f'output/{day_dir}/charts')
    print(f'  {name}: RSI={indicators[name]["RSI"]} BB%={indicators[name]["BB%"]}')
with open(f'output/{day_dir}/indicators.json', 'w', encoding='utf-8') as f:
    json.dump(indicators, f, ensure_ascii=False, indent=2)

# 3. 섹터별 집계
SECTOR_MAP = {
    '005930':'반도체','000660':'반도체','042700':'반도체장비',
    '009150':'AI부품·MLCC','018260':'IT서비스',
    '207940':'바이오','068270':'바이오','196170':'바이오',
    '005380':'자동차','000270':'자동차',
    '012450':'방산','010130':'비철금속','005490':'철강',
    '035420':'인터넷·플랫폼','035720':'인터넷·플랫폼',
    '105560':'금융','055550':'금융','032830':'금융',
    '005935':'반도체','066570':'가전·전자','017670':'통신','030200':'통신',
    '015760':'유틸리티','247540':'2차전지','086520':'2차전지',
    '373220':'2차전지','003670':'2차전지소재',
    '028260':'건설·상사','034730':'지주사','011200':'해운',
}
sectors = {}
for s in results:
    sec = SECTOR_MAP.get(s['ticker'], '기타')
    sectors.setdefault(sec, []).append(s)
sec_list = []
for sec, stocks in sectors.items():
    avg = sum(s['chg_pct'] for s in stocks) / len(stocks)
    avg_5d = sum(s.get('chg_5d') or 0 for s in stocks) / len(stocks)
    avg_20d = sum(s.get('chg_20d') or 0 for s in stocks) / len(stocks)
    best = max(stocks, key=lambda x: x['chg_pct'])
    worst = min(stocks, key=lambda x: x['chg_pct'])
    sec_list.append({'섹터':sec, '종목수':len(stocks), '평균등락률':round(avg,2),
        '평균5일':round(avg_5d,2), '평균20일':round(avg_20d,2),
        '강세종목':best['name'],'강세등락률':best['chg_pct'],
        '약세종목':worst['name'],'약세등락률':worst['chg_pct']})
sec_list.sort(key=lambda x: x['평균등락률'], reverse=True)
with open(f'output/{day_dir}/sector_data.json', 'w', encoding='utf-8') as f:
    json.dump({'trade_date':trade_date,'sectors':sec_list}, f, ensure_ascii=False, indent=2)

print(f'\n✅ {day_dir} 데이터 일괄 생성 완료')
print(f'  → output/{day_dir}/market_data.json, indicators.json, sector_data.json, charts/')

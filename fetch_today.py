"""특정 날짜의 전체 시장 top/bottom + 5종목 분석 데이터 일괄 생성 (FDR 기반)
사용: python fetch_today.py YYYYMMDD
"""
import sys, os, json, time
sys.stdout.reconfigure(encoding='utf-8')
import FinanceDataReader as fdr
import feedparser
from urllib.parse import quote
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
from utils.chart_generator import generate_analysis_chart

if len(sys.argv) < 2:
    sys.exit('Usage: fetch_today.py YYYYMMDD')
target = sys.argv[1]
target_date = f'{target[:4]}-{target[4:6]}-{target[6:]}'

print(f'== {target_date} 자료 생성 ==', flush=True)

# 1. 시장 전체 top/bottom (당일 기준)
print('[1] FDR StockListing 호출...', flush=True)
kospi = fdr.StockListing('KOSPI')
kospi['market'] = 'KOSPI'
kosdaq = fdr.StockListing('KOSDAQ')
kosdaq['market'] = 'KOSDAQ'
allmkt = pd.concat([kospi, kosdaq])
# 가격 1000원 미만, 거래량 0 제외
allmkt = allmkt[(allmkt['Close'] >= 1000) & (allmkt['Volume'] > 0)]
print(f'  유효 종목: {len(allmkt)}', flush=True)

allmkt_sorted = allmkt.sort_values('ChagesRatio', ascending=False).reset_index(drop=True)

def to_stock_dict(row):
    return {
        'ticker': row['Code'], 'name': row['Name'], 'market': row['market'],
        'date': target_date,
        'close': int(row['Close']), 'open': int(row['Open']),
        'high': int(row['High']), 'low': int(row['Low']),
        'volume': int(row['Volume']),
        'prev_close': int(row['Close'] - row['Changes']),
        'chg_pct': round(float(row['ChagesRatio']), 2),
        'marcap': int(row['Marcap']),
        'chg_5d': None, 'chg_20d': None, 'rsi': None,
        'bb_pct': None, 'vol_ratio': None,
        'high_20d': 0, 'low_20d': 0, 'high_60d': 0, 'low_60d': 0,
    }

top_50 = [to_stock_dict(r) for _, r in allmkt_sorted.head(50).iterrows()]
bottom_50 = [to_stock_dict(r) for _, r in allmkt_sorted.tail(50).iloc[::-1].iterrows()]
top_3 = top_50[:3]
bottom_3 = bottom_50[:3]

print(f'\n🚀 TOP 3 상승')
for s in top_3:
    print(f'  {s["name"]:15} ({s["market"]}) {s["close"]:>8,} {s["chg_pct"]:+.2f}%')
print(f'\n🔻 BOTTOM 3 하락')
for s in bottom_3:
    print(f'  {s["name"]:15} ({s["market"]}) {s["close"]:>8,} {s["chg_pct"]:+.2f}%')

# 2. 분석 종목 history fetch — top 3 + bottom 3 + 차트 5종목
TARGETS_FOR_CHART = [
    ('009150','삼성전기'), ('000660','SK하이닉스'), ('105560','KB금융'),
    ('012450','한화에어로스페이스'), ('373220','LG에너지솔루션'),
]
analysis_codes = list({s['ticker'] for s in (top_50[:10] + bottom_50[:10])} | {c for c,_ in TARGETS_FOR_CHART})

start_d = (datetime.strptime(target,'%Y%m%d') - timedelta(days=120)).strftime('%Y-%m-%d')
print(f'\n[2] 분석종목 history ({len(analysis_codes)}종목, {start_d}~{target_date})', flush=True)

def fetch_hist(code):
    try:
        df = fdr.DataReader(code, start_d, target_date)
        return code, df
    except Exception as ex:
        return code, None

hist_data = {}
t0 = time.time()
with ThreadPoolExecutor(max_workers=4) as ex:
    for fut in as_completed({ex.submit(fetch_hist, c): c for c in analysis_codes}):
        code, df = fut.result()
        if df is not None and not df.empty:
            hist_data[code] = df
print(f'  완료 {len(hist_data)}/{len(analysis_codes)} ({time.time()-t0:.1f}s)', flush=True)

# 3. 분석종목 보강 (RSI/BB/vol_ratio/MA/MACD)
def enrich(s):
    df = hist_data.get(s['ticker'])
    if df is None or len(df) < 20: return s
    c = df['Close']; v = df['Volume']
    # RSI
    d = c.diff()
    g = d.where(d>0,0).rolling(14).mean(); lo = (-d.where(d<0,0)).rolling(14).mean()
    rsi_val = (100 - 100/(1+g/lo)).iloc[-1]
    s['rsi'] = round(float(rsi_val),1) if pd.notna(rsi_val) else None
    # BB
    bm = c.rolling(20).mean().iloc[-1]; bs = c.rolling(20).std().iloc[-1]
    bu = bm + 2*bs; bl = bm - 2*bs
    if bu > bl:
        s['bb_pct'] = round(float((c.iloc[-1]-bl)/(bu-bl)*100),1)
    # volume ratio
    v_avg = v.rolling(20).mean().iloc[-1]
    if v_avg and v_avg > 0:
        s['vol_ratio'] = round(float(v.iloc[-1]/v_avg),2)
    # 5일/20일 변화
    if len(c) >= 6:
        s['chg_5d'] = round(float((c.iloc[-1]-c.iloc[-6])/c.iloc[-6]*100),2)
    if len(c) >= 21:
        s['chg_20d'] = round(float((c.iloc[-1]-c.iloc[-21])/c.iloc[-21]*100),2)
    s['high_20d'] = int(df['High'].tail(20).max())
    s['low_20d'] = int(df['Low'].tail(20).min())
    s['high_60d'] = int(df['High'].tail(60).max())
    s['low_60d'] = int(df['Low'].tail(60).min())
    return s

for arr in (top_50, bottom_50):
    for s in arr:
        if s['ticker'] in hist_data:
            enrich(s)

# 4. market_data.json
day_dir = target
os.makedirs(f'output/{day_dir}/charts', exist_ok=True)
# 등락률 내림차순으로 통합 — build_blog.py 호환 (stocks[:3]=top, stocks[-3:]=worst)
combined = sorted(top_50 + bottom_50, key=lambda x: x['chg_pct'], reverse=True)
mkt = {
    'trade_date': target_date,
    'all_count': len(allmkt),
    'top_3': top_50[:3], 'bottom_3': bottom_50[:3],
    'stocks': combined,
}
with open(f'output/{day_dir}/market_data.json','w',encoding='utf-8') as f:
    json.dump(mkt, f, ensure_ascii=False, indent=2)
print(f'\n[3] market_data.json 저장', flush=True)

# 5. 5종목 차트 + indicators
print(f'\n[4] 5종목 차트 + indicators', flush=True)
indicators = {}
for code, name in TARGETS_FOR_CHART:
    df = hist_data.get(code)
    if df is None: continue
    df_chart = df.rename(columns={'Open':'시가','High':'고가','Low':'저가','Close':'종가','Volume':'거래량'})
    df_chart.index.name = 'Date'
    generate_analysis_chart(df_chart, name, '일봉', f'output/{day_dir}/charts')
    c = df['Close']; v = df['Volume']; h = df['High']; l = df['Low']
    ma5 = c.rolling(5).mean().iloc[-1]; ma20 = c.rolling(20).mean().iloc[-1]; ma60 = c.rolling(60).mean().iloc[-1]
    d = c.diff(); g = d.where(d>0,0).rolling(14).mean(); lo = (-d.where(d<0,0)).rolling(14).mean()
    rsi = (100-100/(1+g/lo)).iloc[-1]
    e12 = c.ewm(span=12).mean(); e26 = c.ewm(span=26).mean()
    macd = (e12-e26).iloc[-1]; sig = (e12-e26).ewm(span=9).mean().iloc[-1]
    bm = c.rolling(20).mean().iloc[-1]; bs = c.rolling(20).std().iloc[-1]; bu = bm+2*bs; bl = bm-2*bs
    cur = c.iloc[-1]
    def _i(x): return int(x) if pd.notna(x) else 0
    indicators[name] = {
        'ticker': code, '현재가': _i(cur),
        'MA5': _i(ma5), 'MA20': _i(ma20), 'MA60': _i(ma60),
        '정배열': bool(pd.notna(ma5) and pd.notna(ma20) and pd.notna(ma60) and ma5>ma20>ma60),
        'RSI': round(float(rsi),1),
        'RSI상태': '과매수' if rsi>70 else ('과매도' if rsi<30 else '중립'),
        'MACD': round(float(macd),0), 'Signal': round(float(sig),0),
        'MACD골든크로스': bool(macd>sig),
        'BB상단': int(bu), 'BB하단': int(bl),
        'BB%': round(float((cur-bl)/(bu-bl)*100),1),
        '거래량배수': round(float(v.iloc[-1]/v.rolling(20).mean().iloc[-1]),2),
        '60일고가': int(h.tail(60).max()), '60일저가': int(l.tail(60).min()),
        '60일고가대비': round(float((cur-h.tail(60).max())/h.tail(60).max()*100),2),
    }
    print(f'  {name}: RSI={indicators[name]["RSI"]} BB%={indicators[name]["BB%"]}', flush=True)

with open(f'output/{day_dir}/indicators.json','w',encoding='utf-8') as f:
    json.dump(indicators, f, ensure_ascii=False, indent=2)

# 6. 섹터 (시총 상위 30종목 매핑)
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
sector_stocks = {}
for s in combined:
    if s['ticker'] in SECTOR_MAP:
        sector_stocks.setdefault(SECTOR_MAP[s['ticker']], []).append(s)
# 상위 30 시총 매핑된 종목만 fetch한 history 없을 수 있음 — 변동률 기반으로 단순 집계
sec_list = []
for sec, ss in sector_stocks.items():
    avg = sum(x['chg_pct'] for x in ss) / len(ss)
    avg5 = sum(x.get('chg_5d') or 0 for x in ss) / len(ss)
    avg20 = sum(x.get('chg_20d') or 0 for x in ss) / len(ss)
    best = max(ss, key=lambda x: x['chg_pct'])
    worst = min(ss, key=lambda x: x['chg_pct'])
    sec_list.append({'섹터':sec,'종목수':len(ss),'평균등락률':round(avg,2),
        '평균5일':round(avg5,2),'평균20일':round(avg20,2),
        '강세종목':best['name'],'강세등락률':best['chg_pct'],
        '약세종목':worst['name'],'약세등락률':worst['chg_pct']})

# top/bottom의 섹터 매핑이 부족 — 시총 상위 30종목을 별도로 평균 계산
TOP30_CODES = list(SECTOR_MAP.keys())
top30_in_market = [s for s in combined if s['ticker'] in TOP30_CODES]
# 시총 상위 30 중 combined에 없는 것 보강 — 전체 시장에서 가져오기
existing = {s['ticker'] for s in combined}
for code in TOP30_CODES:
    if code in existing: continue
    row = allmkt[allmkt['Code']==code]
    if len(row)==0: continue
    s = to_stock_dict(row.iloc[0])
    if code in hist_data:
        enrich(s)
    sec = SECTOR_MAP[code]
    sector_stocks.setdefault(sec, []).append(s)
sec_list = []
for sec, ss in sector_stocks.items():
    avg = sum(x['chg_pct'] for x in ss) / len(ss)
    avg5 = sum(x.get('chg_5d') or 0 for x in ss) / len(ss)
    avg20 = sum(x.get('chg_20d') or 0 for x in ss) / len(ss)
    best = max(ss, key=lambda x: x['chg_pct'])
    worst = min(ss, key=lambda x: x['chg_pct'])
    sec_list.append({'섹터':sec,'종목수':len(ss),'평균등락률':round(avg,2),
        '평균5일':round(avg5,2),'평균20일':round(avg20,2),
        '강세종목':best['name'],'강세등락률':best['chg_pct'],
        '약세종목':worst['name'],'약세등락률':worst['chg_pct']})
sec_list.sort(key=lambda x: x['평균등락률'], reverse=True)
with open(f'output/{day_dir}/sector_data.json','w',encoding='utf-8') as f:
    json.dump({'trade_date':target_date,'sectors':sec_list}, f, ensure_ascii=False, indent=2)
print(f'\n[5] sector_data.json 저장 ({len(sec_list)} 섹터)', flush=True)

# 7. 뉴스 — TOP 3 + BOTTOM 3
def get_news(query, count=3):
    url = f'https://news.google.com/rss/search?q={quote(query)}&hl=ko&gl=KR&ceid=KR:ko'
    try:
        feed = feedparser.parse(url)
        return [{'title':e.title,'link':e.link} for e in feed.entries[:count]]
    except Exception:
        return []

print(f'\n[6] 뉴스 수집', flush=True)
movers_news = {}
for s in top_3 + bottom_3:
    headlines = get_news(s['name'], 3)
    movers_news[s['name']] = {'ticker':s['ticker'],'chg_pct':s['chg_pct'],'headlines':headlines}
    print(f'  {s["name"]} ({s["chg_pct"]:+.2f}%): {len(headlines)}건', flush=True)
with open(f'output/{day_dir}/news_data.json','w',encoding='utf-8') as f:
    json.dump({'trade_date':target_date,'movers_news':movers_news}, f, ensure_ascii=False, indent=2)

print(f'\n✅ {target} 자료 생성 완료', flush=True)

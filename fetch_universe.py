"""시총 상위 N종목 × 50일 OHLCV — FDR(Naver) 기반, 병렬"""
import sys, json, time, os
sys.stdout.reconfigure(encoding='utf-8')
import FinanceDataReader as fdr
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd

TOP_N = int(os.environ.get('TOP_N', '1500'))

print('FDR 시총 조회...', flush=True)
kospi = fdr.StockListing('KOSPI')[['Code','Name','Marcap']]; kospi['market'] = 'KOSPI'
kosdaq = fdr.StockListing('KOSDAQ')[['Code','Name','Marcap']]; kosdaq['market'] = 'KOSDAQ'
allmkt = pd.concat([kospi, kosdaq])
allmkt = allmkt[allmkt['Marcap'] > 0].sort_values('Marcap', ascending=False).head(TOP_N)
universe = [{'code':r['Code'],'name':r['Name'],'market':r['market']} for _,r in allmkt.iterrows()]
print(f'대상 {len(universe)}종목', flush=True)

start_d = '2026-03-01'
end_d = '2026-04-24'

def fetch(item):
    try:
        df = fdr.DataReader(item['code'], start_d, end_d)
        if df.empty: return None
        rows = []
        for idx, row in df.iterrows():
            rows.append({
                'date': idx.strftime('%Y-%m-%d'),
                'open': int(row['Open']) if pd.notna(row['Open']) else 0,
                'high': int(row['High']) if pd.notna(row['High']) else 0,
                'low': int(row['Low']) if pd.notna(row['Low']) else 0,
                'close': int(row['Close']) if pd.notna(row['Close']) else 0,
                'volume': int(row['Volume']) if pd.notna(row['Volume']) else 0,
            })
        return {'code': item['code'], 'name': item['name'], 'market': item['market'], 'rows': rows}
    except Exception as ex:
        return {'code': item['code'], 'error': str(ex)}

t0 = time.time()
results = []
done = 0
with ThreadPoolExecutor(max_workers=10) as ex:
    futs = {ex.submit(fetch, item): item for item in universe}
    for fut in as_completed(futs):
        try:
            r = fut.result(timeout=15)
        except Exception:
            r = None
        if r and 'rows' in r:
            results.append(r)
        done += 1
        if done % 100 == 0 or done == len(universe):
            print(f'  {done}/{len(universe)} ok={len(results)} ({time.time()-t0:.1f}s)', flush=True)

print(f'\n성공 {len(results)} / {time.time()-t0:.1f}s', flush=True)

with open('universe_ohlcv.json', 'w', encoding='utf-8') as f:
    json.dump({'fetched_at': datetime.now().isoformat(), 'stocks': results}, f, ensure_ascii=False)
print('→ universe_ohlcv.json 저장', flush=True)

"""JSON 데이터 → 마감 리뷰 HTML 자동 생성 (Blogger 호환 CSS)"""
import sys, os, json, glob
sys.stdout.reconfigure(encoding='utf-8')

if len(sys.argv) < 2:
    sys.exit('Usage: build_blog.py YYYYMMDD')
date = sys.argv[1]
date_fmt = f'{date[:4]}-{date[4:6]}-{date[6:]}'
month_day = f'{int(date[4:6])}월 {int(date[6:])}일'

base = f'output/{date}'
m = json.load(open(f'{base}/market_data.json', encoding='utf-8'))
ind = json.load(open(f'{base}/indicators.json', encoding='utf-8'))
sec = json.load(open(f'{base}/sector_data.json', encoding='utf-8'))['sectors']

stocks = m['stocks']
ups = [s for s in stocks if s['chg_pct'] > 0]
downs = [s for s in stocks if s['chg_pct'] < 0]
top_up = stocks[:10]
top_down = stocks[-min(10, len(downs)):][::-1]

# 차트 파일명 매핑
charts = {}
for name in ['삼성전기', 'SK하이닉스', 'KB금융', '한화에어로스페이스', 'LG에너지솔루션']:
    files = glob.glob(f'{base}/charts/{name}_일봉_분석_*.png')
    if files:
        charts[name] = os.path.basename(files[0])

def fmt(v): return f'{v:+.2f}%' if v is not None else 'N/A'
def cls(v): return 'up' if v and v > 0 else ('down' if v and v < 0 else 'neutral')

# 한줄요약 자동 생성
top1 = stocks[0]; bot1 = stocks[-1]
summary = f'30종목 중 {len(ups)}종목 상승, {len(downs)}종목 하락. <strong>{top1["name"]} {top1["chg_pct"]:+.2f}%</strong>가 가장 두드러진 상승, <strong>{bot1["name"]} {bot1["chg_pct"]:+.2f}%</strong>가 가장 큰 하락.'

# 섹터 강세/약세
strong_secs = [s for s in sec if s['평균등락률'] > 0]
weak_secs = [s for s in sec if s['평균등락률'] < 0]

# 차트 분석 텍스트
def chart_block(name, data, fname):
    rsi = data['RSI']; rsi_state = data['RSI상태']; bb = data['BB%']
    macd_state = '골든' if data['MACD골든크로스'] else '데드'
    arr = '정배열' if data['정배열'] else '혼조/역배열'
    rsi_tag = 'tag-warn' if rsi > 70 else ('tag-bad' if rsi < 30 else 'tag-neutral')
    bb_state = '상단돌파' if bb > 100 else ('상단근접' if bb > 90 else ('상단부' if bb > 70 else ('밴드중앙' if bb > 30 else '하단부')))
    bb_tag = 'tag-warn' if bb > 90 else 'tag-neutral'
    macd_tag = 'tag-good' if data['MACD골든크로스'] else 'tag-bad'

    # 자동 해석
    if rsi > 85:
        interp = f'RSI {rsi}로 극심한 과매수 구간. 단기 조정 가능성이 높습니다.'
    elif rsi > 70:
        interp = f'RSI {rsi}로 과매수 영역에 진입. 추격보다 눌림목 대기가 안전합니다.'
    elif rsi < 30:
        interp = f'RSI {rsi}로 과매도 구간. 반발 매수 시점을 노릴 수 있습니다.'
    else:
        interp = f'RSI {rsi}로 중립 구간. 추세 추종이 가능합니다.'
    if data['정배열']:
        interp += f' MA5/20/60 정배열로 추세 상승 흐름이 살아있습니다.'
    else:
        interp += f' MA 혼조 상태로 방향성이 분명하지 않습니다.'

    return f'''<div class="chart-card">
<h3>{name} ({data['ticker']}) — RSI {rsi} {rsi_state}</h3>
<img src="charts/{fname}" alt="{name} 일봉 분석">
<div class="indicator-grid">
<div class="ind-item"><span class="ind-label">현재가</span><span class="ind-value">{data['현재가']:,}</span></div>
<div class="ind-item"><span class="ind-label">MA5/20/60</span><span class="ind-value">{data['MA5']//1000}K / {data['MA20']//1000}K / {data['MA60']//1000}K</span></div>
<div class="ind-item"><span class="ind-label">RSI(14)</span><span class="ind-value">{rsi} <span class="tag {rsi_tag}">{rsi_state}</span></span></div>
<div class="ind-item"><span class="ind-label">MACD</span><span class="ind-value">{int(data['MACD']):,} <span class="tag {macd_tag}">{macd_state}</span></span></div>
<div class="ind-item"><span class="ind-label">볼린저 위치</span><span class="ind-value">{bb}% <span class="tag {bb_tag}">{bb_state}</span></span></div>
<div class="ind-item"><span class="ind-label">거래량 배수</span><span class="ind-value">{data['거래량배수']}x</span></div>
<div class="ind-item"><span class="ind-label">60일 고가 대비</span><span class="ind-value">{data['60일고가대비']:+.2f}%</span></div>
</div>
<p><strong>차트 해석</strong>: {interp}</p>
</div>'''

# CSS (Blogger 호환, 모든 색상 명시)
CSS = '''
  .container { max-width:880px; margin:0 auto; background:#ffffff; color:#1a1f2e; border-radius:16px; padding:40px 48px; box-shadow:0 4px 24px rgba(0,0,0,.06); border:1px solid #e4e7ec; font-family:-apple-system,"Segoe UI","Pretendard","Malgun Gothic",sans-serif; line-height:1.7; box-sizing:border-box; }
  .container * { box-sizing:border-box; }
  .container h1, .container h2, .container h3, .container h4, .container p, .container li, .container td, .container th, .container span, .container div { color:#1a1f2e; }
  .container h1 { font-size:28px; line-height:1.4; border-bottom:2px solid #2563eb; padding-bottom:16px; margin-bottom:24px; }
  .container h2 { font-size:22px; margin-top:40px; padding-left:12px; border-left:4px solid #2563eb; }
  .container h3 { font-size:18px; margin-top:28px; color:#b45309 !important; }
  .container blockquote { background:#eff6ff; border-left:4px solid #2563eb; padding:14px 20px; margin:20px 0; border-radius:4px; color:#1a1f2e; }
  .container blockquote * { color:#1a1f2e; }
  .container .disclaimer { background:#fef2f2; border-left:4px solid #e11d48; padding:12px 18px; margin:20px 0; border-radius:4px; font-size:14px; color:#7f1d1d !important; }
  .container .disclaimer * { color:#7f1d1d !important; }
  .container table { width:100%; border-collapse:collapse; margin:16px 0; font-size:14px; background:#fafbfc; border:1px solid #e4e7ec; border-radius:8px; overflow:hidden; }
  .container th, .container td { padding:10px 12px; text-align:left; border-bottom:1px solid #e4e7ec; color:#1a1f2e; }
  .container th { background:#f1f5f9; color:#2563eb !important; font-weight:600; font-size:13px; }
  .container td.num { text-align:right; font-variant-numeric:tabular-nums; }
  .container .up { color:#e11d48 !important; font-weight:600; }
  .container .down { color:#2563eb !important; font-weight:600; }
  .container .neutral { color:#6b7280 !important; }
  .container ul { padding-left:22px; } .container li { margin:6px 0; color:#1a1f2e; }
  .container strong { color:#b45309 !important; }
  .container .summary-box { background:linear-gradient(135deg,#eff6ff,#fffbeb); border:1px solid #e4e7ec; border-radius:12px; padding:20px 24px; margin:24px 0; color:#1a1f2e; }
  .container .summary-box * { color:#1a1f2e; }
  .container .chart-card { border:1px solid #e4e7ec; border-radius:12px; padding:20px; margin:20px 0; background:#fafbfc; color:#1a1f2e; }
  .container .chart-card * { color:inherit; }
  .container .chart-card img { width:100%; border-radius:8px; border:1px solid #e4e7ec; background:#fff; }
  .container .indicator-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:10px; margin:14px 0; }
  .container .ind-item { background:#fff; border:1px solid #e4e7ec; border-radius:6px; padding:8px 12px; font-size:13px; color:#1a1f2e; }
  .container .ind-label { color:#6b7280 !important; font-size:11px; display:block; }
  .container .ind-value { font-weight:600; font-size:14px; color:#1a1f2e !important; }
  .container .tag { display:inline-block; padding:2px 8px; border-radius:10px; font-size:11px; font-weight:600; margin:0 2px; }
  .container .tag-good { background:#fee2e2; color:#b91c1c !important; }
  .container .tag-warn { background:#fef3c7; color:#92400e !important; }
  .container .tag-bad { background:#dbeafe; color:#1e40af !important; }
  .container .tag-neutral { background:#f1f5f9; color:#475569 !important; }
'''

# 상승 표
up_rows = ''.join(f'<tr><td>{i+1}</td><td>{s["name"]}</td><td class="num">{s["close"]:,}</td><td class="num up">{s["chg_pct"]:+.2f}%</td><td class="num {cls(s["chg_5d"])}">{fmt(s["chg_5d"])}</td><td class="num {cls(s["chg_20d"])}">{fmt(s["chg_20d"])}</td></tr>' for i, s in enumerate(top_up))
down_rows = ''.join(f'<tr><td>{s["name"]}</td><td class="num">{s["close"]:,}</td><td class="num down">{s["chg_pct"]:+.2f}%</td><td class="num {cls(s["chg_5d"])}">{fmt(s["chg_5d"])}</td><td class="num {cls(s["chg_20d"])}">{fmt(s["chg_20d"])}</td></tr>' for s in top_down)

# 섹터 표
sec_rows = ''.join(f'<tr><td>{i+1}</td><td>{x["섹터"]}</td><td class="num {cls(x["평균등락률"])}">{x["평균등락률"]:+.2f}%</td><td class="num {cls(x["평균5일"])}">{x["평균5일"]:+.2f}%</td><td class="num {cls(x["평균20일"])}">{x["평균20일"]:+.2f}%</td><td>{x["강세종목"]} {x["강세등락률"]:+.2f}%{(" / "+x["약세종목"]+f" {x['약세등락률']:+.2f}%") if x["종목수"]>1 else ""}</td></tr>' for i, x in enumerate(sec))

chart_blocks = '\n'.join(chart_block(n, ind[n], charts.get(n, '')) for n in ['삼성전기', 'SK하이닉스', 'KB금융', '한화에어로스페이스', 'LG에너지솔루션'] if n in ind)

# 섹터 강세 텍스트
strong_text = ''
for s in strong_secs[:3]:
    strong_text += f'<p><strong>{s["섹터"]} ({s["평균등락률"]:+.2f}%)</strong> · {s["강세종목"]} {s["강세등락률"]:+.2f}%로 섹터 주도. 5일 누적 {s["평균5일"]:+.2f}%, 20일 누적 {s["평균20일"]:+.2f}%.</p>'
weak_text = ''
for s in weak_secs[-3:][::-1]:
    weak_text += f'<p><strong>{s["섹터"]} ({s["평균등락률"]:+.2f}%)</strong> · {s["약세종목"]} {s["약세등락률"]:+.2f}%로 섹터 가장 약세. 5일 누적 {s["평균5일"]:+.2f}%, 20일 누적 {s["평균20일"]:+.2f}%.</p>'

# 제목 자동 생성
title_keyword = f'{stocks[0]["name"]} {stocks[0]["chg_pct"]:+.2f}%, {stocks[-1]["name"]} {stocks[-1]["chg_pct"]:+.2f}%'
title = f'[{month_day} 마감 리뷰] {title_keyword}'

html = f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>{CSS}</style>
</head>
<body>
<div class="container">

<h1>{title}</h1>

<h2>한줄 요약</h2>
<blockquote>{summary}</blockquote>

<h2>주요 종목 등락 현황 ({date_fmt} 종가 기준)</h2>

<h3>상승 TOP {len(top_up)}</h3>
<table>
<thead><tr><th>#</th><th>종목</th><th class="num">종가</th><th class="num">등락률</th><th class="num">5일</th><th class="num">20일</th></tr></thead>
<tbody>{up_rows}</tbody>
</table>

<h3>하락 TOP {len(top_down)}</h3>
<table>
<thead><tr><th>종목</th><th class="num">종가</th><th class="num">등락률</th><th class="num">5일</th><th class="num">20일</th></tr></thead>
<tbody>{down_rows}</tbody>
</table>

<h2>섹터별 성적표</h2>
<table>
<thead><tr><th>#</th><th>섹터</th><th class="num">오늘</th><th class="num">5일</th><th class="num">20일</th><th>주요 종목</th></tr></thead>
<tbody>{sec_rows}</tbody>
</table>

<h2>섹터별 흐름</h2>
<h3>강세 섹터 TOP 3</h3>
{strong_text or '<p>강세 섹터 없음 (대부분 하락 마감)</p>'}

<h3>약세 섹터 TOP 3</h3>
{weak_text or '<p>약세 섹터 없음 (대부분 상승 마감)</p>'}

<h2>📈 차트로 보는 기술적 분석 (5종목)</h2>
{chart_blocks}

<h2>핵심 정리</h2>
<div class="summary-box">
<p><strong>오늘의 강세</strong>: {' / '.join(f"{s['섹터']}({s['평균등락률']:+.2f}%)" for s in strong_secs[:3])}</p>
<p><strong>오늘의 약세</strong>: {' / '.join(f"{s['섹터']}({s['평균등락률']:+.2f}%)" for s in weak_secs[-3:][::-1])}</p>
<p><strong>가장 두드러진 상승</strong>: {top_up[0]['name']} {top_up[0]['chg_pct']:+.2f}% (종가 {top_up[0]['close']:,})</p>
<p><strong>가장 큰 하락</strong>: {top_down[0]['name']} {top_down[0]['chg_pct']:+.2f}% (종가 {top_down[0]['close']:,})</p>
</div>

<div class="disclaimer">⚠️ <strong>면책조항</strong>: 본 글은 투자 참고용이며, 특정 종목의 매수·매도를 권유하지 않습니다. 모든 투자 결정과 그에 따른 손익은 투자자 본인의 판단과 책임 하에 이루어져야 합니다.</div>

</div>
</body>
</html>'''

out_path = f'{base}/{date}_마감리뷰.html'
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(html)
print(f'✅ {out_path}')

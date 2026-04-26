"""섹터 성적표 + 뉴스 수집"""
import sys, json
sys.stdout.reconfigure(encoding='utf-8')
import feedparser
from urllib.parse import quote

# 종목 → 섹터 매핑
SECTOR_MAP = {
    "005930": "반도체", "000660": "반도체", "042700": "반도체장비",
    "009150": "AI부품·MLCC", "018260": "IT서비스",
    "207940": "바이오", "068270": "바이오", "196170": "바이오",
    "005380": "자동차", "000270": "자동차",
    "012450": "방산", "010130": "비철금속", "005490": "철강",
    "035420": "인터넷·플랫폼", "035720": "인터넷·플랫폼",
    "105560": "금융", "055550": "금융", "032830": "금융",
    "005935": "반도체",
    "066570": "가전·전자", "017670": "통신", "030200": "통신",
    "015760": "유틸리티",
    "247540": "2차전지", "086520": "2차전지",
    "373220": "2차전지", "003670": "2차전지소재",
    "028260": "건설·상사", "034730": "지주사",
    "011200": "해운",
}

def load_market():
    with open("market_data.json", "r", encoding="utf-8") as f:
        return json.load(f)

def compute_sectors(market):
    """섹터별 평균 등락률 + 종목 리스트"""
    sectors = {}
    for s in market["stocks"]:
        sec = SECTOR_MAP.get(s["ticker"], "기타")
        sectors.setdefault(sec, []).append(s)

    result = []
    for sec, stocks in sectors.items():
        avg = sum(s["chg_pct"] for s in stocks) / len(stocks)
        avg_5d = sum(s.get("chg_5d") or 0 for s in stocks) / len(stocks)
        avg_20d = sum(s.get("chg_20d") or 0 for s in stocks) / len(stocks)
        # 섹터 내 최고/최저
        best = max(stocks, key=lambda x: x["chg_pct"])
        worst = min(stocks, key=lambda x: x["chg_pct"])
        result.append({
            "섹터": sec,
            "종목수": len(stocks),
            "평균등락률": round(avg, 2),
            "평균5일": round(avg_5d, 2),
            "평균20일": round(avg_20d, 2),
            "강세종목": best["name"],
            "강세등락률": best["chg_pct"],
            "약세종목": worst["name"],
            "약세등락률": worst["chg_pct"],
        })
    result.sort(key=lambda x: x["평균등락률"], reverse=True)
    return result

def get_news(query, count=5):
    """Google News RSS 한국어 뉴스"""
    url = f"https://news.google.com/rss/search?q={quote(query)}&hl=ko&gl=KR&ceid=KR:ko"
    try:
        feed = feedparser.parse(url)
        items = []
        for entry in feed.entries[:count]:
            # 제목에서 출처 분리 (예: "제목 - 한국경제")
            title = entry.title
            items.append({
                "title": title,
                "link": entry.link,
                "published": entry.get("published", ""),
            })
        return items
    except Exception as e:
        print(f"  ❌ {query}: {e}")
        return []

def main():
    market = load_market()
    trade_date = market["trade_date"]
    print(f"📅 거래일: {trade_date}\n")

    # 1) 섹터 성적표
    print("📊 섹터별 성적표 계산 중...")
    sectors = compute_sectors(market)
    print(f"  → {len(sectors)}개 섹터")
    for s in sectors[:5]:
        print(f"  {s['섹터']:15} {s['평균등락률']:+.2f}% (종목 {s['종목수']}개)")

    # 2) 시장 전반 뉴스
    print("\n📰 시장 전반 뉴스 수집 중...")
    market_news = {
        "코스피 마감": get_news("코스피 마감", 5),
        "외국인 순매수": get_news("외국인 순매수 코스피", 3),
        "환율": get_news("원달러 환율", 3),
        "미국증시": get_news("뉴욕증시 마감", 3),
    }
    for k, v in market_news.items():
        print(f"  {k}: {len(v)}건")

    # 3) 상위 등락 종목 뉴스
    print("\n📰 종목별 뉴스 수집 중...")
    top_movers = sorted(market["stocks"], key=lambda x: abs(x["chg_pct"]), reverse=True)[:8]
    stock_news = {}
    for s in top_movers:
        news = get_news(s["name"], 3)
        stock_news[s["name"]] = {
            "ticker": s["ticker"],
            "chg_pct": s["chg_pct"],
            "headlines": news,
        }
        print(f"  {s['name']} ({s['chg_pct']:+.2f}%): {len(news)}건")

    # 저장
    with open("sector_data.json", "w", encoding="utf-8") as f:
        json.dump({"trade_date": trade_date, "sectors": sectors}, f, ensure_ascii=False, indent=2)
    with open("news_data.json", "w", encoding="utf-8") as f:
        json.dump({
            "trade_date": trade_date,
            "market_news": market_news,
            "stock_news": stock_news,
        }, f, ensure_ascii=False, indent=2)

    print("\n✅ sector_data.json, news_data.json 저장 완료")

if __name__ == "__main__":
    main()

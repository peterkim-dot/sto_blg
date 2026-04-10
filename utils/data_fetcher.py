"""주식 데이터 수집 모듈 - pykrx + 뉴스 RSS"""
from datetime import datetime, timedelta
import pandas as pd
from pykrx import stock
import feedparser
import requests
from bs4 import BeautifulSoup


def get_today_str():
    return datetime.now().strftime("%Y%m%d")


def get_market_summary():
    """KOSPI/KOSDAQ 지수 및 거래량 요약"""
    today = get_today_str()
    # 최근 거래일 찾기 (주말/공휴일 대비 5일 탐색)
    for i in range(5):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
        try:
            kospi = stock.get_index_ohlcv(date, date, "1001")  # KOSPI
            kosdaq = stock.get_index_ohlcv(date, date, "2001")  # KOSDAQ
            if not kospi.empty and not kosdaq.empty:
                return {
                    "date": date,
                    "kospi": kospi.iloc[-1].to_dict(),
                    "kosdaq": kosdaq.iloc[-1].to_dict(),
                }
        except:
            continue
    return {"date": today, "kospi": {}, "kosdaq": {}}


def get_top_movers(count=10):
    """급등주/급락주 상위 종목"""
    today = get_today_str()
    for i in range(5):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
        try:
            df = stock.get_market_ohlcv(date, market="ALL")
            if df.empty:
                continue

            df["등락률"] = ((df["종가"] - df["시가"]) / df["시가"] * 100).round(2)
            df["종목명"] = [stock.get_market_ticker_name(t) for t in df.index]

            # 거래량 0 제외
            df = df[df["거래량"] > 0]

            top_gainers = df.nlargest(count, "등락률")[["종목명", "종가", "등락률", "거래량"]].reset_index()
            top_losers = df.nsmallest(count, "등락률")[["종목명", "종가", "등락률", "거래량"]].reset_index()

            return {
                "date": date,
                "gainers": top_gainers.to_dict("records"),
                "losers": top_losers.to_dict("records"),
            }
        except:
            continue
    return {"date": today, "gainers": [], "losers": []}


def get_stock_ohlcv(ticker, days=120):
    """특정 종목 OHLCV 데이터 (차트 분석용)"""
    end = datetime.now()
    start = end - timedelta(days=days)
    try:
        df = stock.get_market_ohlcv(
            start.strftime("%Y%m%d"),
            end.strftime("%Y%m%d"),
            ticker
        )
        df.index.name = "Date"
        return df
    except:
        return pd.DataFrame()


def get_sector_performance():
    """업종별 등락률"""
    today = get_today_str()
    for i in range(5):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
        try:
            # KOSPI 업종
            tickers = stock.get_index_ticker_list(date, market="KOSPI")
            results = []
            for t in tickers[:20]:
                name = stock.get_index_ticker_name(t)
                ohlcv = stock.get_index_ohlcv(date, date, t)
                if not ohlcv.empty:
                    row = ohlcv.iloc[-1]
                    chg = ((row["종가"] - row["시가"]) / row["시가"] * 100) if row["시가"] > 0 else 0
                    results.append({"업종": name, "종가": row["종가"], "등락률": round(chg, 2)})
            if results:
                return {"date": date, "sectors": results}
        except:
            continue
    return {"date": today, "sectors": []}


def get_news_headlines(query="주식시장", count=15):
    """네이버 뉴스 RSS로 최신 뉴스 헤드라인"""
    url = f"https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"
    try:
        feed = feedparser.parse(url)
        headlines = []
        for entry in feed.entries[:count]:
            headlines.append({
                "title": entry.title,
                "link": entry.link,
                "published": entry.get("published", ""),
            })
        return headlines
    except:
        return []


def get_world_market_news():
    """글로벌 시장 관련 뉴스"""
    keywords = ["미국증시", "나스닥", "S&P500", "환율", "유가", "금리"]
    all_news = []
    for kw in keywords:
        news = get_news_headlines(kw, count=5)
        all_news.extend(news)
    # 중복 제거
    seen = set()
    unique = []
    for n in all_news:
        if n["title"] not in seen:
            seen.add(n["title"])
            unique.append(n)
    return unique


def get_ticker_by_name(name):
    """종목명으로 티커 검색"""
    today = get_today_str()
    for i in range(5):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
        try:
            tickers = stock.get_market_ticker_list(date, market="ALL")
            for t in tickers:
                if stock.get_market_ticker_name(t) == name:
                    return t
        except:
            continue
    return None

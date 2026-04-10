"""에이전트 3: 차트 기술적 분석"""
import json
import pandas as pd
from utils.llm_client import call_llm
from utils.data_fetcher import get_stock_ohlcv, get_ticker_by_name
from utils.chart_generator import generate_multi_timeframe_charts


SYSTEM_PROMPT = """당신은 주식 차트 기술적 분석의 최고 전문가입니다.

역할:
- 60분봉, 일봉, 주봉, 월봉 기반 다중 타임프레임 분석
- 이동평균선(5일, 20일, 60일, 120일) 분석
- 지지/저항 레벨 식별
- 캔들스틱 패턴 분석
- 거래량 분석
- RSI, MACD, 볼린저밴드 등 기술적 지표 해석
- 추세선 분석 및 패턴 인식 (삼각형, 쐐기, 헤드앤숄더 등)

작성 스타일:
- 각 타임프레임별 체계적 분석
- 구체적인 가격대와 수치 제시
- 차트 패턴에 대한 명확한 설명
- 마크다운 형식

출력 구조 (종목별):
1. 📈 일봉 분석 (추세, 이동평균, 캔들 패턴, 거래량)
2. 📊 주봉 분석 (중기 추세, 지지/저항)
3. 📉 월봉 분석 (장기 추세, 대형 패턴)
4. 🔧 기술적 지표 종합 (RSI, MACD, 볼린저밴드 추정)
5. 🎯 핵심 가격대 (지지선, 저항선, 매매 포인트)"""


def _calc_technical_indicators(df):
    """기술적 지표 계산"""
    if df.empty or len(df) < 5:
        return {}

    close = df["종가"]
    indicators = {}

    # 이동평균
    for period in [5, 20, 60, 120]:
        if len(close) >= period:
            indicators[f"MA{period}"] = round(close.rolling(period).mean().iloc[-1], 0)

    # RSI (14일)
    if len(close) >= 15:
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        indicators["RSI_14"] = round(rsi.iloc[-1], 1)

    # 볼린저밴드 (20일)
    if len(close) >= 20:
        ma20 = close.rolling(20).mean().iloc[-1]
        std20 = close.rolling(20).std().iloc[-1]
        indicators["BB_upper"] = round(ma20 + 2 * std20, 0)
        indicators["BB_middle"] = round(ma20, 0)
        indicators["BB_lower"] = round(ma20 - 2 * std20, 0)

    # MACD
    if len(close) >= 26:
        ema12 = close.ewm(span=12).mean()
        ema26 = close.ewm(span=26).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9).mean()
        indicators["MACD"] = round(macd.iloc[-1], 1)
        indicators["MACD_signal"] = round(signal.iloc[-1], 1)
        indicators["MACD_hist"] = round((macd - signal).iloc[-1], 1)

    # 최근 가격 정보
    indicators["현재가"] = int(close.iloc[-1])
    indicators["5일_고가"] = int(df["고가"].tail(5).max())
    indicators["5일_저가"] = int(df["저가"].tail(5).min())
    indicators["20일_고가"] = int(df["고가"].tail(20).max()) if len(df) >= 20 else None
    indicators["20일_저가"] = int(df["저가"].tail(20).min()) if len(df) >= 20 else None

    return indicators


def run(movers_data=None):
    """차트 분석 에이전트 실행"""
    # 분석할 종목 선정 (급등/급락 상위 종목)
    target_stocks = []

    if movers_data:
        gainers = movers_data.get("gainers", [])[:3]
        losers = movers_data.get("losers", [])[:2]
        for g in gainers:
            target_stocks.append({"name": g["종목명"], "ticker": g.get("티커", ""), "type": "급등"})
        for l in losers:
            target_stocks.append({"name": l["종목명"], "ticker": l.get("티커", ""), "type": "급락"})

    if not target_stocks:
        # 기본 종목
        target_stocks = [
            {"name": "삼성전자", "ticker": "005930", "type": "대표"},
            {"name": "SK하이닉스", "ticker": "000660", "type": "대표"},
        ]

    all_analysis = []
    all_charts = {}

    for stock_info in target_stocks:
        name = stock_info["name"]
        ticker = stock_info.get("ticker", "")

        # 티커 찾기
        if not ticker or len(ticker) != 6:
            ticker = get_ticker_by_name(name)
        if not ticker:
            continue

        # OHLCV 데이터 가져오기
        df = get_stock_ohlcv(ticker, days=180)
        if df.empty:
            continue

        # 기술적 지표 계산
        indicators = _calc_technical_indicators(df)

        # 차트 생성
        charts = generate_multi_timeframe_charts(df, name)
        all_charts[name] = charts

        # OHLCV 최근 데이터 요약
        recent = df.tail(10)
        recent_text = recent.to_string()

        analysis_prompt = f"""[종목: {name} ({ticker}) - {stock_info['type']}]

[최근 10일 OHLCV]
{recent_text}

[기술적 지표]
{json.dumps(indicators, ensure_ascii=False, indent=2)}

위 데이터를 바탕으로 {name}의 차트를 기술적으로 분석해주세요.
일봉, 주봉, 월봉 관점에서 각각 분석하고, 주요 지지/저항 가격대를 제시해주세요."""

        analysis = call_llm(SYSTEM_PROMPT, analysis_prompt, max_tokens=3000)
        all_analysis.append(f"## {name} ({stock_info['type']})\n\n{analysis}")

    result = "\n\n---\n\n".join(all_analysis)
    return result, all_charts


if __name__ == "__main__":
    text, charts = run()
    print(text)
    print("\n생성된 차트:", charts)

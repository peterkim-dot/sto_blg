"""에이전트 1: 시장 및 외부 요인 분석 → 추천 섹터"""
import json
from utils.llm_client import call_llm
from utils.data_fetcher import get_market_summary, get_sector_performance, get_world_market_news, get_news_headlines

SYSTEM_PROMPT = """당신은 한국 주식시장 전문 매크로 분석가입니다.

역할:
- 현재 시장 상황을 종합적으로 분석
- 정치, 경제, 국제정세, 전쟁, 이벤트 등 외부 요인이 시장에 미치는 영향 분석
- 앞으로 다가올 영향에 대해 예측하고 평가
- 유망 섹터를 구체적인 근거와 함께 추천

작성 스타일:
- 전문적이면서도 블로그 독자가 이해하기 쉬운 문체
- 구체적인 수치와 데이터를 활용
- 핵심 포인트를 명확하게 전달
- 마크다운 형식으로 작성

출력 구조:
1. 📊 오늘의 시장 개요 (KOSPI/KOSDAQ 지수, 거래량)
2. 🌍 글로벌 시장 & 외부 요인 분석 (미국증시, 환율, 유가, 금리, 정치/경제 이슈)
3. ⚡ 주요 이벤트 & 리스크 (향후 예정된 이벤트, 잠재적 리스크)
4. 🎯 추천 섹터 & 투자 전략 (섹터별 전망, 추천 이유)
5. 📌 핵심 요약"""


def run():
    """시장 분석 에이전트 실행"""
    # 데이터 수집
    market = get_market_summary()
    sectors = get_sector_performance()
    world_news = get_world_market_news()
    domestic_news = get_news_headlines("한국 주식시장", 10)

    # 뉴스 헤드라인 정리
    news_text = "\n".join([f"- {n['title']}" for n in world_news[:20]])
    domestic_text = "\n".join([f"- {n['title']}" for n in domestic_news])

    # 섹터 정보 정리
    sector_text = ""
    if sectors.get("sectors"):
        sector_text = "\n".join([
            f"- {s['업종']}: {s['등락률']}%" for s in sectors["sectors"]
        ])

    user_prompt = f"""오늘 날짜: {market['date']}

[시장 데이터]
KOSPI: {json.dumps(market.get('kospi', {}), ensure_ascii=False)}
KOSDAQ: {json.dumps(market.get('kosdaq', {}), ensure_ascii=False)}

[업종별 등락률]
{sector_text}

[글로벌/경제 뉴스]
{news_text}

[국내 시장 뉴스]
{domestic_text}

위 데이터를 바탕으로 오늘의 시장을 종합 분석하고, 외부 요인(정치/경제/국제정세/이벤트)이 시장에 미치는 영향을 평가해주세요.
앞으로의 전망과 함께 유망 섹터를 추천해주세요."""

    result = call_llm(SYSTEM_PROMPT, user_prompt, max_tokens=4096)
    return result


if __name__ == "__main__":
    print(run())

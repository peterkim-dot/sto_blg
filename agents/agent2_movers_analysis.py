"""에이전트 2: 급등주/급락주 분석"""
import json
from utils.llm_client import call_llm
from utils.data_fetcher import get_top_movers, get_news_headlines

SYSTEM_PROMPT = """당신은 한국 주식시장의 개별 종목 분석 전문가입니다.

역할:
- 금일 급등주와 급락주를 분석
- 각 종목의 등락 원인을 구체적으로 파악
- 어떤 외부/내부 요인이 영향을 미쳤는지 분석
- 해당 종목의 향후 단기 전망 제시

작성 스타일:
- 종목별로 구체적인 분석
- 등락 원인에 대한 뉴스/이벤트 연결
- 투자자에게 실질적으로 도움이 되는 인사이트
- 마크다운 형식

출력 구조:
1. 🚀 오늘의 급등주 TOP (종목별: 종목명, 등락률, 상승 원인, 관련 뉴스/테마)
2. 📉 오늘의 급락주 TOP (종목별: 종목명, 등락률, 하락 원인, 관련 뉴스/테마)
3. 🔍 종목 간 공통 패턴 분석 (테마/섹터 흐름)
4. 💡 투자자 참고사항"""


def run():
    """급등락주 분석 에이전트 실행"""
    movers = get_top_movers(count=10)

    # 급등주 관련 뉴스 수집
    gainer_names = [g["종목명"] for g in movers.get("gainers", [])[:5]]
    loser_names = [l["종목명"] for l in movers.get("losers", [])[:5]]

    gainer_news = {}
    for name in gainer_names:
        news = get_news_headlines(f"{name} 주가", 3)
        gainer_news[name] = [n["title"] for n in news]

    loser_news = {}
    for name in loser_names:
        news = get_news_headlines(f"{name} 주가", 3)
        loser_news[name] = [n["title"] for n in news]

    user_prompt = f"""분석 날짜: {movers['date']}

[급등주 TOP 10]
{json.dumps(movers.get('gainers', []), ensure_ascii=False, indent=2)}

[급등주 관련 뉴스]
{json.dumps(gainer_news, ensure_ascii=False, indent=2)}

[급락주 TOP 10]
{json.dumps(movers.get('losers', []), ensure_ascii=False, indent=2)}

[급락주 관련 뉴스]
{json.dumps(loser_news, ensure_ascii=False, indent=2)}

위 데이터를 바탕으로 금일 급등주와 급락주를 종합 분석해주세요.
각 종목의 등락 원인, 관련 이벤트/테마, 공통 패턴을 파악해주세요."""

    result = call_llm(SYSTEM_PROMPT, user_prompt, max_tokens=4096)
    return result, movers


if __name__ == "__main__":
    text, _ = run()
    print(text)

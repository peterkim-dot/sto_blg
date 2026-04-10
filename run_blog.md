# 주식 블로그 자동 생성 작업

작업 디렉토리: `C:\Users\hwany\OneDrive\바탕 화면\Dev\STOCK_BLOG\stock-blog-agent`

## 실행 절차

1. **데이터 수집**: `.venv/Scripts/python.exe fetch_for_claude.py` 실행
   - 결과: `market_data.json` (KOSPI 대형주 30개 종가/등락률/5일/20일 변화)

2. **기술적 지표 계산**: `.venv/Scripts/python.exe compute_indicators.py` 실행
   - 결과: `indicators.json` (5종목 RSI/MACD/MA/볼린저)

3. **차트 이미지 생성**: `.venv/Scripts/python.exe gen_charts_for_blog.py` 실행
   - 결과: `output/{거래일}/charts/*.png` (5개 종목 분석 차트)

4. **블로그 작성** (Claude가 직접 작성, LLM API 호출 금지):
   - `market_data.json`과 `indicators.json`을 읽어 시장 흐름·테마 분석
   - 다음 두 파일을 `output/{거래일}/` 에 저장:
     - `{거래일}_마감리뷰.md` (마크다운)
     - `{거래일}_마감리뷰.html` (흰색 테마, 차트 5개 임베드, 지표 카드)
   - HTML 템플릿은 기존 `output/20260410/20260410_마감리뷰.html` 구조 그대로 따를 것
   - 차트 분석 섹션은 반드시 포함, 각 종목마다 RSI/MACD/MA/볼린저 위치/거래량 카드 + 데이터 기반 해석

## 작성 원칙

- **데이터 기반**: 모든 수치는 `indicators.json`에서 가져올 것 (추측 금지)
- **한국어**, 간결한 분석 톤
- **빨강=상승, 파랑=하락** (한국 주식 관행)
- **면책조항** 반드시 포함
- **제목**: `[{월}월 {일}일 마감 리뷰] {핵심 키워드}` 형식

## 실패 시
- pykrx 단일종목 API만 작동 (`get_market_ohlcv`로 ticker 지정). 인덱스/시장전체 API는 깨져있음
- 가장 최근 거래일이 인자 end보다 과거일 수 있음 → market_data.json의 trade_date 사용

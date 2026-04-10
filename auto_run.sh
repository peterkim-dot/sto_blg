#!/bin/bash
# 원격 트리거용 자동 실행 스크립트
# 1. 의존성 설치 → 2. 데이터 수집 → 3. 지표 계산 → 4. 차트 생성
set -e
cd "$(dirname "$0")"

echo "==> 1/4 의존성 설치"
pip install --quiet pykrx mplfinance pandas numpy feedparser beautifulsoup4 requests python-dotenv 2>&1 | tail -5 || true
# 한글 폰트 (가능하면)
which apt-get >/dev/null 2>&1 && (apt-get install -y fonts-nanum 2>/dev/null || true)

echo "==> 2/4 시장 데이터 수집"
python fetch_for_claude.py

echo "==> 3/4 기술적 지표 계산"
python compute_indicators.py

echo "==> 4/4 차트 이미지 생성"
python gen_charts_for_blog.py

echo "✅ 모든 데이터 준비 완료"
echo "   - market_data.json"
echo "   - indicators.json"
echo "   - output/<거래일>/charts/*.png"

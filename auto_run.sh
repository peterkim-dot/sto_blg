#!/bin/bash
# 원격 트리거용 자동 실행 스크립트
# 실패 시 즉시 멈추고 stdout 전체 노출 (silent fail 방지)
set -e

cd "$(dirname "$0")"

echo "==> 환경 정보"
which python || which python3
python --version 2>&1 || python3 --version 2>&1
which pip || which pip3 || true

# python 명령 통일
PY=$(which python || which python3)
echo "PY=$PY"

echo ""
echo "==> 1/4 의존성 설치 (실패 시 즉시 중단)"
$PY -m pip install --upgrade pip
$PY -m pip install pykrx mplfinance pandas numpy feedparser beautifulsoup4 requests python-dotenv

# 한글 폰트 (best-effort)
if which apt-get >/dev/null 2>&1; then
  apt-get install -y fonts-nanum 2>/dev/null || sudo apt-get install -y fonts-nanum 2>/dev/null || echo "(폰트 설치 스킵)"
fi

echo ""
echo "==> 설치 확인"
$PY -c "import pykrx, mplfinance, pandas; print('pykrx:', pykrx.__version__ if hasattr(pykrx, '__version__') else 'ok'); print('mplfinance:', mplfinance.__version__); print('pandas:', pandas.__version__)"

echo ""
echo "==> 2/4 시장 데이터 수집"
$PY fetch_for_claude.py

echo ""
echo "==> 3/4 기술적 지표 계산"
$PY compute_indicators.py

echo ""
echo "==> 4/4 차트 이미지 생성"
$PY gen_charts_for_blog.py

echo ""
echo "✅ 모든 데이터 준비 완료"
ls -la market_data.json indicators.json
ls output/*/charts/ 2>/dev/null | head -20 || echo "(차트 폴더 없음)"

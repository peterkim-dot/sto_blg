import os
from dotenv import load_dotenv

load_dotenv()

# LLM 설정 (mock = API 없이 테스트)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "mock")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# 모델명
ANTHROPIC_MODEL = "claude-sonnet-4-20250514"
OPENAI_MODEL = "gpt-4o"

# 출력 경로
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./output")

# 스케줄
MORNING_HOUR = int(os.getenv("MORNING_HOUR", 8))
MORNING_MINUTE = int(os.getenv("MORNING_MINUTE", 30))
EVENING_HOUR = int(os.getenv("EVENING_HOUR", 18))
EVENING_MINUTE = int(os.getenv("EVENING_MINUTE", 0))

# 분석 대상 종목 수
TOP_MOVERS_COUNT = 10

# 차트 분석 시 기본 종목 수
CHART_ANALYSIS_COUNT = 5

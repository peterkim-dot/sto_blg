"""주식 블로그 자동 생성 에이전트 - 메인 실행"""
import sys


def print_help():
    print("""
📰 주식 블로그 자동 생성 에이전트
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

사용법:
  python main.py run [morning|evening]   즉시 블로그 글 생성
  python main.py schedule                스케줄러 시작 (하루 2회 자동)
  python main.py help                    도움말

예시:
  python main.py run morning    → 아침 브리핑 즉시 생성
  python main.py run evening    → 마감 리뷰 즉시 생성
  python main.py run            → 아침 브리핑 즉시 생성 (기본값)
  python main.py schedule       → 스케줄러 시작 (08:30, 18:00 자동 실행)

설정:
  .env 파일에서 API 키, 스케줄 시간, 출력 경로 등을 설정하세요.
  .env.example 파일을 참고하세요.
""")


def main():
    if len(sys.argv) < 2:
        print_help()
        return

    command = sys.argv[1]

    if command == "run":
        from orchestrator import run_pipeline
        session = sys.argv[2] if len(sys.argv) > 2 else "morning"
        if session not in ("morning", "evening"):
            print(f"❌ 알 수 없는 세션: {session} (morning 또는 evening)")
            return
        run_pipeline(session)

    elif command == "schedule":
        from scheduler import start_scheduler
        start_scheduler()

    elif command == "help":
        print_help()

    else:
        print(f"❌ 알 수 없는 명령: {command}")
        print_help()


if __name__ == "__main__":
    main()

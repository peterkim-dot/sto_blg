"""스케줄러: 하루 2회 자동 실행 서비스"""
import sys
import signal
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

import config
from orchestrator import run_pipeline


def morning_job():
    """아침 브리핑 생성"""
    print("\n🌅 아침 브리핑 스케줄 실행")
    try:
        run_pipeline("morning")
    except Exception as e:
        print(f"❌ 아침 브리핑 실패: {e}")


def evening_job():
    """마감 리뷰 생성"""
    print("\n🌆 마감 리뷰 스케줄 실행")
    try:
        run_pipeline("evening")
    except Exception as e:
        print(f"❌ 마감 리뷰 실패: {e}")


def start_scheduler():
    """스케줄러 시작"""
    scheduler = BlockingScheduler()

    # 아침 브리핑 (평일만)
    scheduler.add_job(
        morning_job,
        CronTrigger(
            hour=config.MORNING_HOUR,
            minute=config.MORNING_MINUTE,
            day_of_week="mon-fri"
        ),
        id="morning_briefing",
        name="아침 브리핑",
    )

    # 마감 리뷰 (평일만)
    scheduler.add_job(
        evening_job,
        CronTrigger(
            hour=config.EVENING_HOUR,
            minute=config.EVENING_MINUTE,
            day_of_week="mon-fri"
        ),
        id="evening_review",
        name="마감 리뷰",
    )

    # 종료 시그널 처리
    def shutdown(signum, frame):
        print("\n⏹️ 스케줄러 종료 중...")
        scheduler.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    print(f"""
╔══════════════════════════════════════════════════╗
║     📰 주식 블로그 자동 생성 스케줄러 시작       ║
╠══════════════════════════════════════════════════╣
║  🌅 아침 브리핑: 평일 {config.MORNING_HOUR:02d}:{config.MORNING_MINUTE:02d}                    ║
║  🌆 마감 리뷰:   평일 {config.EVENING_HOUR:02d}:{config.EVENING_MINUTE:02d}                    ║
║  📁 출력 경로:   {config.OUTPUT_DIR:<31s} ║
║                                                  ║
║  종료: Ctrl+C                                    ║
╚══════════════════════════════════════════════════╝
""")

    scheduler.start()


if __name__ == "__main__":
    start_scheduler()

"""오케스트레이터: 에이전트 파이프라인 실행"""
import os
import sys
from datetime import datetime

import config
from agents import agent1_market_analysis
from agents import agent2_movers_analysis
from agents import agent3_chart_analysis
from agents import agent4_outlook
from agents import agent5_blog_writer


def run_pipeline(session_type="morning"):
    """전체 에이전트 파이프라인 실행"""
    print(f"\n{'='*60}")
    print(f"📰 주식 블로그 자동 생성 시작 [{session_type}]")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    # 에이전트 1: 시장 분석
    print("🔄 [1/5] 시장 & 외부 요인 분석 중...")
    try:
        result1 = agent1_market_analysis.run()
        print("✅ 시장 분석 완료")
    except Exception as e:
        print(f"❌ 시장 분석 실패: {e}")
        result1 = f"시장 분석 데이터를 가져올 수 없습니다. ({e})"

    # 에이전트 2: 급등락주 분석
    print("🔄 [2/5] 급등/급락주 분석 중...")
    try:
        result2, movers_data = agent2_movers_analysis.run()
        print("✅ 급등락주 분석 완료")
    except Exception as e:
        print(f"❌ 급등락주 분석 실패: {e}")
        result2, movers_data = f"급등락주 데이터를 가져올 수 없습니다. ({e})", None

    # 에이전트 3: 차트 분석
    print("🔄 [3/5] 차트 기술적 분석 중...")
    try:
        result3, charts = agent3_chart_analysis.run(movers_data)
        print(f"✅ 차트 분석 완료 (차트 {len(charts)}개 종목 생성)")
    except Exception as e:
        print(f"❌ 차트 분석 실패: {e}")
        result3, charts = f"차트 분석을 수행할 수 없습니다. ({e})", {}

    # 에이전트 4: 종합 전망
    print("🔄 [4/5] 종합 전망 작성 중...")
    try:
        result4 = agent4_outlook.run(result2, result3)
        print("✅ 종합 전망 완료")
    except Exception as e:
        print(f"❌ 종합 전망 실패: {e}")
        result4 = f"종합 전망을 작성할 수 없습니다. ({e})"

    # 에이전트 5: 블로그 글 통합
    print("🔄 [5/5] 블로그 글 통합 작성 중...")
    try:
        blog_post = agent5_blog_writer.run(result1, result2, result3, result4, session_type)
        print("✅ 블로그 글 작성 완료")
    except Exception as e:
        print(f"❌ 블로그 글 작성 실패: {e}")
        blog_post = f"블로그 글 작성에 실패했습니다. ({e})"

    # 결과 저장
    output_path = save_blog_post(blog_post, session_type, charts)

    print(f"\n{'='*60}")
    print(f"🎉 블로그 글 생성 완료!")
    print(f"📁 저장 위치: {output_path}")
    print(f"{'='*60}\n")

    return output_path


def save_blog_post(content, session_type, charts=None):
    """블로그 글을 파일로 저장"""
    now = datetime.now()
    date_str = now.strftime("%Y%m%d")
    time_str = now.strftime("%H%M%S")
    label = "아침브리핑" if session_type == "morning" else "마감리뷰"

    # 날짜별 폴더
    day_dir = os.path.join(config.OUTPUT_DIR, date_str)
    os.makedirs(day_dir, exist_ok=True)

    filename = f"{date_str}_{label}_{time_str}.md"
    filepath = os.path.join(day_dir, filename)

    # 차트 이미지 경로를 상대 경로로 변환하여 본문에 추가
    chart_section = ""
    if charts:
        chart_section = "\n\n---\n## 📊 차트 이미지\n\n"
        for stock_name, chart_paths in charts.items():
            chart_section += f"### {stock_name}\n"
            for tf, path in chart_paths.items():
                rel_path = os.path.relpath(path, day_dir)
                chart_section += f"- {tf}: ![{stock_name} {tf}]({rel_path})\n"
            chart_section += "\n"

    full_content = content + chart_section

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(full_content)

    return filepath


if __name__ == "__main__":
    session = sys.argv[1] if len(sys.argv) > 1 else "morning"
    run_pipeline(session)

#!/usr/bin/env python3
"""
감정분석 총점 업데이트 스크립트
- analyze_sentiment.py → sent_news (뉴스 감정 점수)
- collect_trends.py → sent_trend (구글 트렌드 점수)
를 합산하여 sent_total, total_score, grade를 갱신한다.

실행 순서:
  1. collect_news.py       → data/news/
  2. analyze_sentiment.py  → data/sentiment/
  3. collect_trends.py     → data/trends/
  4. update_sentiment_scores.py  ← THIS (총점 반영)
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

# 등급 기준
GRADE_THRESHOLDS = [
    (90, "A+"), (80, "A"), (70, "B+"), (60, "B"),
    (50, "C+"), (40, "C"), (30, "D"), (0, "F"),
]


def calc_grade(score: float) -> str:
    for threshold, grade in GRADE_THRESHOLDS:
        if score >= threshold:
            return grade
    return "F"


def load_json(directory: str, prefix: str) -> dict:
    """가장 최근 JSON 파일 로드"""
    data_dir = Path(__file__).parent.parent / "data" / directory

    # TARGET_DATE 환경변수가 있으면 해당 날짜 파일 우선
    target_date = os.environ.get("TARGET_DATE", "")
    if target_date:
        date_str = target_date.replace("-", "")
        target_file = data_dir / f"{prefix}_{date_str}.json"
        if target_file.exists():
            with open(target_file, "r", encoding="utf-8") as f:
                return json.load(f)

    # 오늘 날짜 파일
    today_str = datetime.utcnow().strftime("%Y%m%d")
    today_file = data_dir / f"{prefix}_{today_str}.json"
    if today_file.exists():
        with open(today_file, "r", encoding="utf-8") as f:
            return json.load(f)

    # 가장 최근 파일
    files = sorted(data_dir.glob(f"{prefix}_*.json"), reverse=True)
    if files:
        with open(files[0], "r", encoding="utf-8") as f:
            print(f"  ℹ️ Using latest file: {files[0].name}")
            return json.load(f)

    return {}


def get_supabase_client():
    """Supabase 클라이언트 생성"""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        print("❌ SUPABASE_URL / SUPABASE_KEY not set")
        sys.exit(1)

    from supabase import create_client
    return create_client(url, key)


def main():
    print("=" * 50)
    print("🔄 Update Sentiment Scores")
    print("=" * 50)

    # 1) 감정분석 / 트렌드 결과 로드
    sentiment_data = load_json("sentiment", "sentiment")
    trends_data = load_json("trends", "trends")

    if not sentiment_data and not trends_data:
        print("⚠️ No sentiment or trends data found. Nothing to update.")
        return

    print(f"📰 Sentiment: {len(sentiment_data)} stocks")
    print(f"📈 Trends: {len(trends_data)} stocks")

    # 2) 종목코드 합집합
    all_codes = set(sentiment_data.keys()) | set(trends_data.keys())
    print(f"📋 Total stocks to update: {len(all_codes)}")

    # 3) Supabase 접속
    client = get_supabase_client()

    # stocks_anal에서 code → id 매핑 일괄 조회
    stock_resp = client.table("stocks_anal").select("id, code").execute()
    code_to_id = {r["code"]: r["id"] for r in stock_resp.data}

    updated = 0
    skipped = 0

    for code in sorted(all_codes):
        stock_id = code_to_id.get(code)
        if not stock_id:
            skipped += 1
            continue

        # 감정 점수 (뉴스)
        sent_entry = sentiment_data.get(code, {})
        sent_news = sent_entry.get("score", 6)  # 기본값 중립(6)

        # 트렌드 점수
        trend_entry = trends_data.get(code, {})
        sent_trend = trend_entry.get("score", 4)  # 기본값 중립(4)

        # 감정분석 총점 (20점 만점 = sent_news(max 12) + sent_trend(max 8))
        sent_total = sent_news + sent_trend

        # 기존 analysis_results_anal 레코드 조회
        today = datetime.utcnow().strftime("%Y-%m-%d")
        existing = client.table("analysis_results_anal").select(
            "id, tech_total, fund_total, liquidity_total_penalty"
        ).eq("stock_id", stock_id).order(
            "analysis_date", desc=True
        ).limit(1).execute()

        if existing.data:
            record = existing.data[0]
            tech_total = record.get("tech_total") or 0
            fund_total = record.get("fund_total") or 0
            penalty = record.get("liquidity_total_penalty") or 0

            # total_score 재계산
            total_score = round(tech_total + fund_total + sent_total - penalty, 1)
            grade = calc_grade(total_score)

            # 업데이트
            client.table("analysis_results_anal").update({
                "sent_news": sent_news,
                "sent_trend": sent_trend,
                "sent_total": sent_total,
                "sent_data_insufficient": False,
                "total_score": total_score,
                "grade": grade,
            }).eq("id", record["id"]).execute()
        else:
            # 기존 레코드 없으면 신규 생성 (감정분석만)
            total_score = round(sent_total, 1)
            grade = calc_grade(total_score)

            client.table("analysis_results_anal").insert({
                "stock_id": stock_id,
                "analysis_date": today,
                "sent_news": sent_news,
                "sent_trend": sent_trend,
                "sent_total": sent_total,
                "sent_data_insufficient": False,
                "total_score": total_score,
                "grade": grade,
            }).execute()

        updated += 1

    print(f"\n✅ Updated: {updated} stocks, Skipped: {skipped}")
    print("🔄 Sentiment scores update completed!")


if __name__ == "__main__":
    main()

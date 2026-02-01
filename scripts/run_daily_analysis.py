#!/usr/bin/env python3
"""
일별 분석 실행 스크립트
- 시세 수집 후 분석 점수 계산
- GitHub Actions에서 실행됨
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# 프로젝트 루트를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))


def get_target_date() -> str:
    """분석 대상 날짜 반환 (YYYY-MM-DD)"""
    target = os.environ.get("TARGET_DATE", "").strip()
    if target:
        return target
    # KST 기준 오늘
    return (datetime.utcnow() + timedelta(hours=9)).strftime("%Y-%m-%d")


def run_technical_analysis(stock_codes: list[str], target_date: str) -> dict:
    """기술분석 실행"""
    results = {}

    # TODO: 실제 구현
    # from app.services.technical import TechnicalAnalysisService
    # service = TechnicalAnalysisService()
    # for code in stock_codes:
    #     results[code] = service.calculate_score(code, target_date)

    print(f"📊 Technical analysis: {len(stock_codes)} stocks")
    return results


def run_fundamental_analysis(stock_codes: list[str], target_date: str) -> dict:
    """기본분석 실행"""
    results = {}

    # TODO: 실제 구현
    # from app.services.fundamental import FundamentalAnalysisService
    # service = FundamentalAnalysisService()
    # for code in stock_codes:
    #     results[code] = service.calculate_score(code, target_date)

    print(f"📈 Fundamental analysis: {len(stock_codes)} stocks")
    return results


def run_sentiment_analysis(stock_codes: list[str], target_date: str) -> dict:
    """감정분석 실행"""
    results = {}

    openai_key = os.environ.get("OPENAI_API_KEY")
    if not openai_key:
        print("⚠️ OpenAI API key not found, skipping sentiment analysis")
        return results

    # TODO: 실제 구현
    # from app.services.sentiment import SentimentAnalysisService
    # service = SentimentAnalysisService(openai_key)
    # for code in stock_codes:
    #     results[code] = service.calculate_score(code, target_date)

    print(f"💬 Sentiment analysis: {len(stock_codes)} stocks")
    return results


def calculate_total_scores(
    technical: dict,
    fundamental: dict,
    sentiment: dict,
    stock_codes: list[str]
) -> dict:
    """총점 계산"""
    results = {}

    for code in stock_codes:
        tech_score = technical.get(code, {}).get("total", 0)
        fund_score = fundamental.get(code, {}).get("total", 0)
        sent_score = sentiment.get(code, {}).get("total", 10)  # 데이터 없으면 중립

        # 유동성 감점 (TODO: 실제 계산)
        liquidity_penalty = 0

        total = tech_score + fund_score + sent_score - liquidity_penalty

        results[code] = {
            "technical": tech_score,
            "fundamental": fund_score,
            "sentiment": sent_score,
            "liquidity_penalty": liquidity_penalty,
            "total": total,
        }

    return results


def save_analysis_results(results: dict, target_date: str):
    """분석 결과 Supabase에 저장"""
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        print("⚠️ Supabase credentials not found")
        return

    try:
        from supabase import create_client

        client = create_client(supabase_url, supabase_key)

        for code, scores in results.items():
            # stocks 테이블에서 stock_id 조회
            stock_resp = client.table("stocks").select("id").eq("code", code).execute()

            if stock_resp.data:
                stock_id = stock_resp.data[0]["id"]

                # analysis_results 테이블에 upsert
                client.table("analysis_results").upsert({
                    "stock_id": stock_id,
                    "analysis_date": target_date,
                    "tech_total": scores["technical"],
                    "fund_total": scores["fundamental"],
                    "sent_total": scores["sentiment"],
                    "liquidity_total_penalty": scores["liquidity_penalty"],
                    "total_score": scores["total"],
                }, on_conflict="stock_id,analysis_date").execute()

        print(f"✅ Analysis results saved: {len(results)} stocks")

    except Exception as e:
        print(f"❌ Supabase error: {e}")


def main():
    print("=" * 50)
    print("🔬 Daily Analysis")
    print("=" * 50)

    target_date = get_target_date()
    print(f"📅 Target Date: {target_date}")

    # 포트폴리오 종목 조회 (collect_daily_prices.py와 동일)
    from collect_daily_prices import get_portfolio_stocks
    stock_codes = get_portfolio_stocks()
    print(f"📋 Target Stocks: {len(stock_codes)}개")

    # 분석 실행
    print("\n" + "-" * 30)
    technical = run_technical_analysis(stock_codes, target_date)
    fundamental = run_fundamental_analysis(stock_codes, target_date)
    sentiment = run_sentiment_analysis(stock_codes, target_date)

    # 총점 계산
    print("\n" + "-" * 30)
    print("🧮 Calculating total scores...")
    results = calculate_total_scores(technical, fundamental, sentiment, stock_codes)

    # 저장
    print("\n" + "-" * 30)
    save_analysis_results(results, target_date)

    # 요약
    print("\n" + "=" * 50)
    print("📊 Analysis Summary")
    print("=" * 50)
    if results:
        sorted_results = sorted(results.items(), key=lambda x: x[1]["total"], reverse=True)
        print("\n🏆 Top 5 Stocks:")
        for i, (code, scores) in enumerate(sorted_results[:5], 1):
            print(f"  {i}. {code}: {scores['total']:.1f}점")

    print("\n✅ Analysis completed!")


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""
VIP 종목 전체 데이터 수집 스크립트
- 시세 데이터 (pykrx → SQLite)
- 재무 데이터 (네이버 금융 → 메모리)
- 분석 실행 (scoring → Supabase)
"""

import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pykrx import stock as krx
from app.db import sqlite_db, supabase_db
from app.collectors import naver_finance
from app.services.scoring import StockScorer


def collect_prices(stock_code: str, stock_name: str, years: int = 1) -> dict:
    """시세 데이터 수집 (pykrx → SQLite)"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=years * 365)

    start_str = start_date.strftime("%Y%m%d")
    end_str = end_date.strftime("%Y%m%d")

    try:
        time.sleep(0.3)  # Rate limit

        # pykrx로 일별 시세 조회
        df = krx.get_market_ohlcv(start_str, end_str, stock_code)

        if df.empty:
            return {"success": False, "count": 0, "error": "No data"}

        # SQLite 저장용 데이터 변환
        prices = []
        for date_idx, row in df.iterrows():
            prices.append({
                "stock_code": stock_code,
                "date": date_idx.strftime("%Y-%m-%d"),
                "open_price": int(row["시가"]),
                "high_price": int(row["고가"]),
                "low_price": int(row["저가"]),
                "close_price": int(row["종가"]),
                "volume": int(row["거래량"]),
                "trading_value": int(row.get("거래대금", 0)),
            })

        # SQLite에 저장
        inserted = sqlite_db.insert_prices_bulk(prices)

        return {
            "success": True,
            "count": len(prices),
            "inserted": inserted,
        }

    except Exception as e:
        return {"success": False, "count": 0, "error": str(e)}


def collect_financials(stock_code: str) -> dict:
    """재무 데이터 수집 (네이버 금융)"""
    try:
        time.sleep(0.5)  # Rate limit

        # 종목 기본 정보 (PER, PBR)
        info = naver_finance.get_stock_info(stock_code)

        # 재무 정보 (ROE, 영업이익률 등)
        financials = naver_finance.get_financial_summary(stock_code)

        result = {
            "per": info.get("per"),
            "pbr": info.get("pbr"),
            "sector": info.get("sector"),
            "market_cap": info.get("market_cap"),
        }

        if financials:
            result.update({
                "revenue": financials.get("revenue"),
                "operating_profit": financials.get("operating_profit"),
                "net_income": financials.get("net_income"),
                "roe": financials.get("roe"),
                "op_margin": financials.get("operating_margin"),
                "revenue_growth": financials.get("revenue_growth"),
                "op_growth": financials.get("op_growth"),
                "debt_ratio": financials.get("debt_ratio"),
                "current_ratio": financials.get("current_ratio"),
            })

        return result

    except Exception as e:
        print(f"  ⚠️ 재무 데이터 수집 실패: {e}")
        return {}


def run_analysis(stock_code: str, stock_name: str, financials: dict) -> dict:
    """분석 실행 및 저장"""
    try:
        # 시세 데이터 조회 (SQLite)
        prices = sqlite_db.get_prices(stock_code, limit=120)

        # 기술지표 계산
        indicators = None
        if prices and len(prices) >= 20:
            from app.analyzers.indicators import TechnicalIndicators
            calc = TechnicalIndicators(stock_code, prices)
            indicators = calc.calculate_all()

        # 분석기 생성 및 실행
        scorer = StockScorer(
            stock_code=stock_code,
            stock_name=stock_name,
            indicators=indicators,
            financials=financials,
            prices=prices,
        )

        result = scorer.calculate_total()
        scorer.save_to_db(result)

        return result

    except Exception as e:
        print(f"  ⚠️ 분석 실패: {e}")
        return {"error": str(e)}


def main():
    """메인 실행"""
    print("=" * 70)
    print("📊 VIP 종목 전체 데이터 수집 및 분석")
    print("=" * 70)
    print()

    # SQLite 초기화
    sqlite_db.init_database()
    print("✅ SQLite 데이터베이스 초기화 완료")

    # Supabase에서 종목 목록 조회
    stocks = supabase_db.get_all_stocks()
    print(f"📋 대상 종목: {len(stocks)}개")
    print()

    # 결과 저장
    results = {
        "total": len(stocks),
        "price_success": 0,
        "price_failed": 0,
        "analysis_success": 0,
        "analysis_failed": 0,
        "details": [],
    }

    # 각 종목별 수집 및 분석
    for i, stock in enumerate(stocks, 1):
        code = stock["code"]
        name = stock["name"]

        print(f"[{i}/{len(stocks)}] {name} ({code})")

        # 1. 시세 수집 (5년치)
        print("  📈 시세 수집 중 (5년치)...", end=" ")
        price_result = collect_prices(code, name, years=5)

        if price_result["success"]:
            results["price_success"] += 1
            print(f"✅ {price_result['count']}건")
        else:
            results["price_failed"] += 1
            print(f"❌ {price_result.get('error', 'Unknown')}")

        # 2. 재무 수집
        print("  💰 재무 수집 중...", end=" ")
        financials = collect_financials(code)
        if financials.get("per"):
            print(f"✅ PER:{financials.get('per')}, PBR:{financials.get('pbr')}")
        else:
            print("⚠️ 일부 데이터 없음")

        # 3. 분석 실행
        print("  🔍 분석 실행 중...", end=" ")
        analysis = run_analysis(code, name, financials)

        if "error" not in analysis:
            results["analysis_success"] += 1
            print(f"✅ {analysis['total_score']}점 [{analysis['grade']}]")
            results["details"].append({
                "code": code,
                "name": name,
                "score": analysis["total_score"],
                "grade": analysis["grade"],
            })
        else:
            results["analysis_failed"] += 1
            print(f"❌ {analysis['error']}")

        print()

    # 결과 요약
    print("=" * 70)
    print("📊 수집 및 분석 결과 요약")
    print("=" * 70)
    print(f"시세 수집: {results['price_success']}/{results['total']} 성공")
    print(f"분석 완료: {results['analysis_success']}/{results['total']} 성공")
    print()

    # 등급별 분포
    if results["details"]:
        grades = {}
        for d in results["details"]:
            g = d["grade"]
            grades[g] = grades.get(g, 0) + 1

        print("📊 등급 분포:")
        for g in ["A+", "A", "B+", "B", "C+", "C", "D", "F"]:
            if g in grades:
                print(f"   {g}: {grades[g]}개")

        # 상위 5개 종목
        print()
        print("🏆 상위 5개 종목:")
        sorted_results = sorted(results["details"], key=lambda x: x["score"], reverse=True)
        for i, r in enumerate(sorted_results[:5], 1):
            print(f"   {i}. {r['name']} ({r['code']}): {r['score']}점 [{r['grade']}]")

    print()
    print("✅ 완료!")


if __name__ == "__main__":
    main()

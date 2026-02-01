#!/usr/bin/env python
"""
주요자산보유현황 종목 시세 데이터 수집
- pykrx를 사용하여 3년치 일별 시세 수집
- SQLite에 저장
"""

import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from pykrx import stock as krx
from app.db import sqlite_db, supabase_db


# VIP한국형가치투자 포트폴리오 종목 (42개, 2025.12.31 기준)
# 종목코드: 종목명
VIP_PORTFOLIO_STOCKS = {
    "138040": "메리츠금융지주",
    "005930": "삼성전자",
    "383220": "F&F",
    "259960": "크래프톤",
    "271560": "오리온",
    "290650": "엘앤씨바이오",
    "032350": "롯데관광개발",
    "086790": "하나금융지주",
    "005385": "현대차우",
    "041510": "에스엠",
    "102710": "이엔에프테크놀로지",
    "012630": "HDC",
    "089030": "테크윙",
    "483650": "달바글로벌",
    "251970": "펌텍코리아",
    "200670": "휴메딕스",
    "005300": "롯데칠성음료",
    "089860": "롯데렌탈",
    "101160": "월덱스",
    "348210": "넥스틴",
    "053610": "프로텍",
    "280360": "롯데웰푸드",
    "086390": "유니테스트",
    "002030": "아세아",
    "453340": "현대그린푸드",
    "005810": "풍산홀딩스",
    "104830": "원익머트리얼즈",
    "248070": "솔루엠",
    "051500": "CJ프레시웨이",
    "060980": "HL홀딩스",
    "353200": "대덕전자",
    "035150": "백산",
    "005720": "넥센",
    "204620": "글로벌텍스프리",
    "043370": "피에이치에이",
    "160980": "싸이맥스",
    "272550": "삼양패키징",
    "240550": "동방메디컬",
    "104460": "디와이피엔에프",
    "210540": "디와이파워",
    "204610": "티쓰리",
    "460870": "에스엠씨지",
}


def collect_stock_prices(
    stock_code: str,
    stock_name: str,
    years: int = 3,
    delay: float = 0.5,
) -> dict:
    """
    단일 종목 시세 수집

    Args:
        stock_code: 종목코드
        stock_name: 종목명
        years: 수집 기간 (년)
        delay: 요청 간 딜레이

    Returns:
        수집 결과
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=years * 365)

    start_str = start_date.strftime("%Y%m%d")
    end_str = end_date.strftime("%Y%m%d")

    try:
        time.sleep(delay)

        # pykrx로 일별 시세 조회
        df = krx.get_market_ohlcv(start_str, end_str, stock_code)

        if df.empty:
            return {
                "stock_code": stock_code,
                "stock_name": stock_name,
                "success": False,
                "error": "No data available",
                "count": 0,
            }

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
            "stock_code": stock_code,
            "stock_name": stock_name,
            "success": True,
            "count": len(prices),
            "inserted": inserted,
            "date_range": (prices[-1]["date"], prices[0]["date"]),
        }

    except Exception as e:
        return {
            "stock_code": stock_code,
            "stock_name": stock_name,
            "success": False,
            "error": str(e),
            "count": 0,
        }


def ensure_stocks_in_supabase(stocks: dict) -> int:
    """
    Supabase에 종목 정보 등록

    Args:
        stocks: {종목코드: 종목명} 딕셔너리

    Returns:
        등록된 종목 수
    """
    stock_data = []
    for code, name in stocks.items():
        stock_data.append({
            "code": code,
            "name": name,
            "market": "KOSPI" if code < "900000" else "KOSDAQ",
        })

    return supabase_db.upsert_stocks_bulk(stock_data)


def main():
    """메인 실행"""
    import argparse

    parser = argparse.ArgumentParser(description="종목 시세 데이터 수집")
    parser.add_argument("--years", type=int, default=3, help="수집 기간 (년)")
    parser.add_argument("--delay", type=float, default=0.5, help="요청 간 딜레이 (초)")
    parser.add_argument("--stocks", type=str, help="특정 종목만 수집 (쉼표 구분)")
    parser.add_argument("--register", action="store_true", help="Supabase에 종목 등록")
    args = parser.parse_args()

    print("=" * 60)
    print("📊 주요자산보유현황 종목 시세 데이터 수집")
    print("=" * 60)
    print(f"수집 기간: {args.years}년")
    print(f"요청 딜레이: {args.delay}초")
    print()

    # SQLite 초기화
    sqlite_db.init_database()

    # 대상 종목 결정
    if args.stocks:
        codes = [c.strip() for c in args.stocks.split(",")]
        target_stocks = {c: VIP_PORTFOLIO_STOCKS.get(c, c) for c in codes}
    else:
        target_stocks = VIP_PORTFOLIO_STOCKS

    print(f"대상 종목: {len(target_stocks)}개")
    print()

    # Supabase에 종목 등록
    if args.register:
        print("📝 Supabase에 종목 등록 중...")
        registered = ensure_stocks_in_supabase(target_stocks)
        print(f"✅ {registered}개 종목 등록 완료")
        print()

    # 시세 수집
    print("📈 시세 데이터 수집 시작...")
    print()

    results = {
        "success": 0,
        "failed": 0,
        "total_records": 0,
        "details": [],
    }

    total = len(target_stocks)
    for i, (code, name) in enumerate(target_stocks.items(), 1):
        print(f"[{i}/{total}] {name} ({code}) 수집 중...", end=" ")

        result = collect_stock_prices(code, name, args.years, args.delay)
        results["details"].append(result)

        if result["success"]:
            results["success"] += 1
            results["total_records"] += result["count"]
            print(f"✅ {result['count']:,}건 ({result['date_range'][0]} ~ {result['date_range'][1]})")
        else:
            results["failed"] += 1
            print(f"❌ {result.get('error', 'Unknown error')}")

    # 결과 요약
    print()
    print("=" * 60)
    print("📊 수집 결과 요약")
    print("=" * 60)
    print(f"성공: {results['success']}/{total}개")
    print(f"실패: {results['failed']}/{total}개")
    print(f"총 레코드: {results['total_records']:,}건")
    print()

    # SQLite 상태 확인
    stock_count = sqlite_db.get_stock_count()
    print(f"📁 SQLite 저장 종목: {stock_count}개")

    # 샘플 확인
    if results["success"] > 0:
        sample_code = results["details"][0]["stock_code"]
        date_range = sqlite_db.get_date_range(sample_code)
        print(f"📅 샘플 기간 ({sample_code}): {date_range[0]} ~ {date_range[1]}")

    print()
    print("✅ 수집 완료!")


if __name__ == "__main__":
    main()

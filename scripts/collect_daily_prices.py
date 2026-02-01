#!/usr/bin/env python3
"""
일별 시세 수집 스크립트
- KIS API (1차) / pykrx (백업) 사용
- SQLite(로컬) 또는 임시파일에 저장
- GitHub Actions에서 실행됨
"""

import os
import sys
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

# 프로젝트 루트를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))


def get_target_date() -> str:
    """수집 대상 날짜 반환 (YYYYMMDD)"""
    target = os.environ.get("TARGET_DATE", "").strip()
    if target:
        return datetime.strptime(target, "%Y-%m-%d").strftime("%Y%m%d")
    # KST 기준 오늘
    return (datetime.utcnow() + timedelta(hours=9)).strftime("%Y%m%d")


def get_portfolio_stocks() -> list[str]:
    """포트폴리오 종목 코드 목록 조회"""
    # TODO: Supabase에서 조회
    # VIP한국형가치투자 종목 (2025.12.31 기준, 42개)
    return [
        "138040",  # 메리츠금융지주
        "005930",  # 삼성전자
        "383220",  # F&F
        "259960",  # 크래프톤
        "271560",  # 오리온
        "290650",  # 엘앤씨바이오 (수정: 388720 → 290650)
        "032350",  # 롯데관광개발
        "086790",  # 하나금융지주
        "005385",  # 현대차우
        "041510",  # 에스엠
        "102710",  # 이엔에프테크놀로지
        "012630",  # HDC
        "089030",  # 테크윙
        "483650",  # 달바글로벌 (수정: 448730 → 483650)
        "251970",  # 펌텍코리아 (수정: 002230 → 251970)
        "200670",  # 휴메딕스
        "005300",  # 롯데칠성음료
        "089860",  # 롯데렌탈
        "101160",  # 월덱스 (수정: 006580 → 101160)
        "348210",  # 넥스틴
        "053610",  # 프로텍
        "280360",  # 롯데웰푸드
        "086390",  # 유니테스트
        "002030",  # 아세아
        "453340",  # 현대그린푸드 (수정: 005440 → 453340)
        "005810",  # 풍산홀딩스
        "104830",  # 원익머트리얼즈
        "248070",  # 솔루엠
        "051500",  # CJ프레시웨이
        "060980",  # HL홀딩스
        "353200",  # 대덕전자 (수정: 065680 → 353200)
        "035150",  # 백산
        "005720",  # 넥센 (수정: 004710 한솔테크닉스 → 005720)
        "204620",  # 글로벌텍스프리
        "043370",  # 피에이치에이
        "160980",  # 싸이맥스 (수정: 054540 → 160980)
        "272550",  # 삼양패키징 (수정: 014280 → 272550)
        "240550",  # 동방메디컬 (수정: 464170 → 240550)
        "104460",  # 디와이피엔에프 (수정: 145720 덴티움 → 104460)
        "210540",  # 디와이파워
        "204610",  # 티쓰리 (수정: 101710 → 204610)
        "460870",  # 에스엠씨지 (수정: 350810 → 460870)
    ]


def collect_with_kis(stock_codes: list[str], target_date: str) -> dict:
    """KIS API로 시세 수집"""
    results = {}

    kis_app_key = os.environ.get("KIS_APP_KEY")
    kis_app_secret = os.environ.get("KIS_APP_SECRET")

    if not kis_app_key or not kis_app_secret:
        print("KIS API credentials not found, skipping KIS collection")
        return results

    try:
        # TODO: KIS API 구현
        # from app.collectors.kis_api import KISCollector
        # collector = KISCollector(kis_app_key, kis_app_secret)
        # for code in stock_codes:
        #     results[code] = collector.get_daily_price(code, target_date)
        pass
    except Exception as e:
        print(f"KIS API error: {e}")

    return results


def collect_with_pykrx(stock_codes: list[str], target_date: str) -> dict:
    """pykrx로 시세 수집 (백업)"""
    results = {}

    try:
        from pykrx import stock

        for code in stock_codes:
            try:
                # 일별 시세 조회
                df = stock.get_market_ohlcv_by_date(
                    fromdate=target_date,
                    todate=target_date,
                    ticker=code
                )

                if not df.empty:
                    row = df.iloc[0]
                    results[code] = {
                        "date": target_date,
                        "open": int(row["시가"]),
                        "high": int(row["고가"]),
                        "low": int(row["저가"]),
                        "close": int(row["종가"]),
                        "volume": int(row["거래량"]),
                        "trading_value": int(row.get("거래대금", 0)),
                    }
                    print(f"✅ {code}: {results[code]['close']:,}원")
                else:
                    print(f"⚠️ {code}: No data for {target_date}")

            except Exception as e:
                print(f"❌ {code}: {e}")

    except ImportError:
        print("pykrx not installed")
    except Exception as e:
        print(f"pykrx error: {e}")

    return results


def save_to_supabase(results: dict, target_date: str):
    """Supabase에 시세 데이터 저장"""
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        print("Supabase credentials not found, saving to local file")
        save_to_local(results, target_date)
        return

    try:
        from supabase import create_client

        client = create_client(supabase_url, supabase_key)

        for code, data in results.items():
            # stocks 테이블에서 stock_id 조회
            stock_resp = client.table("stocks").select("id").eq("code", code).execute()

            if stock_resp.data:
                stock_id = stock_resp.data[0]["id"]

                # price_history는 SQLite에 저장하므로 여기서는 stocks 테이블 업데이트
                client.table("stocks").update({
                    "market_cap": data.get("market_cap"),
                    "avg_trading_value": data.get("trading_value"),
                    "updated_at": datetime.utcnow().isoformat(),
                }).eq("id", stock_id).execute()

        print(f"✅ Supabase 저장 완료: {len(results)}개 종목")

    except Exception as e:
        print(f"Supabase error: {e}")
        save_to_local(results, target_date)


def save_to_local(results: dict, target_date: str):
    """로컬 JSON 파일로 저장 (백업)"""
    output_dir = Path(__file__).parent.parent / "data" / "prices"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"prices_{target_date}.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"✅ 로컬 저장 완료: {output_file}")


def main():
    print("=" * 50)
    print("📊 Daily Price Collection")
    print("=" * 50)

    target_date = get_target_date()
    print(f"📅 Target Date: {target_date}")

    stock_codes = get_portfolio_stocks()
    print(f"📋 Target Stocks: {len(stock_codes)}개")

    # 1차: KIS API
    results = collect_with_kis(stock_codes, target_date)

    # 2차: pykrx (KIS에서 못 가져온 종목)
    missing_codes = [c for c in stock_codes if c not in results]
    if missing_codes:
        print(f"\n🔄 Fallback to pykrx for {len(missing_codes)} stocks...")
        pykrx_results = collect_with_pykrx(missing_codes, target_date)
        results.update(pykrx_results)

    print(f"\n📈 Collected: {len(results)}/{len(stock_codes)} stocks")

    # 저장
    if results:
        save_to_supabase(results, target_date)

    print("\n✅ Collection completed!")


if __name__ == "__main__":
    main()

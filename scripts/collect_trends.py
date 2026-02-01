#!/usr/bin/env python3
"""
구글 트렌드 수집 스크립트
- pytrends 사용
- 최근 30일 검색 트렌드 수집
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))


def get_stock_names() -> dict:
    """종목코드 → 종목명 매핑"""
    # TODO: Supabase에서 조회
    # VIP한국형가치투자 종목 (2025.12.31 기준, 42개)
    return {
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


def collect_google_trends(stock_names: dict) -> dict:
    """구글 트렌드 수집"""
    results = {}

    try:
        from pytrends.request import TrendReq

        pytrends = TrendReq(hl='ko', tz=540)  # 한국어, KST

        for code, name in stock_names.items():
            print(f"  {name}...", end=" ")

            try:
                # 검색어 설정
                pytrends.build_payload(
                    [f"{name} 주식"],
                    timeframe="today 1-m",  # 최근 30일
                    geo="KR"
                )

                # 관심도 데이터
                interest = pytrends.interest_over_time()

                if not interest.empty:
                    # 최근 7일 평균 vs 이전 7일 평균 비교
                    recent = interest.iloc[-7:].mean().values[0]
                    previous = interest.iloc[-14:-7].mean().values[0]

                    if previous > 0:
                        change_rate = (recent - previous) / previous * 100
                    else:
                        change_rate = 0

                    # 점수 계산 (8점 만점)
                    # 상승: 가점, 하락: 감점
                    if change_rate >= 50:
                        score = 8
                    elif change_rate >= 20:
                        score = 7
                    elif change_rate >= 0:
                        score = 5
                    elif change_rate >= -20:
                        score = 4
                    elif change_rate >= -50:
                        score = 3
                    else:
                        score = 2

                    results[code] = {
                        "score": score,
                        "recent_avg": round(recent, 2),
                        "previous_avg": round(previous, 2),
                        "change_rate": round(change_rate, 2),
                    }
                    print(f"점수: {score} (변화율: {change_rate:+.1f}%)")
                else:
                    # 데이터 없으면 중립
                    results[code] = {
                        "score": 4,
                        "reason": "데이터 부족",
                    }
                    print("데이터 부족 (중립)")

                # Rate limit 방지
                time.sleep(2)

            except Exception as e:
                print(f"Error: {e}")
                results[code] = {"score": 4, "reason": str(e)[:30]}
                time.sleep(5)  # 에러 시 더 긴 대기

    except ImportError:
        print("⚠️ pytrends not installed. Using neutral scores.")
        for code in stock_names:
            results[code] = {"score": 4, "reason": "pytrends 미설치"}

    return results


def save_results(results: dict):
    """트렌드 결과 저장"""
    output_dir = Path(__file__).parent.parent / "data" / "trends"
    output_dir.mkdir(parents=True, exist_ok=True)

    date_str = datetime.utcnow().strftime("%Y%m%d")
    output_file = output_dir / f"trends_{date_str}.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"✅ 트렌드 저장: {output_file}")

    # Supabase 저장
    save_to_supabase(results)


def save_to_supabase(results: dict):
    """Supabase에 트렌드 결과 저장"""
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        return

    try:
        from supabase import create_client

        client = create_client(supabase_url, supabase_key)
        today = datetime.utcnow().strftime("%Y-%m-%d")

        for code, data in results.items():
            stock_resp = client.table("stocks").select("id").eq("code", code).execute()
            if stock_resp.data:
                stock_id = stock_resp.data[0]["id"]
                client.table("analysis_results").upsert({
                    "stock_id": stock_id,
                    "analysis_date": today,
                    "sent_trend": data["score"],
                }, on_conflict="stock_id,analysis_date").execute()

        print(f"✅ Supabase 업데이트 완료")

    except Exception as e:
        print(f"Supabase error: {e}")


def main():
    print("=" * 50)
    print("📈 Google Trends Collection")
    print("=" * 50)

    stock_names = get_stock_names()
    print(f"📋 Target Stocks: {len(stock_names)}개\n")

    results = collect_google_trends(stock_names)

    # 요약
    print("\n" + "-" * 30)
    avg_score = sum(r["score"] for r in results.values()) / len(results) if results else 0
    print(f"📊 평균 트렌드 점수: {avg_score:.1f}/8")

    save_results(results)

    print("\n✅ Trends collection completed!")


if __name__ == "__main__":
    main()

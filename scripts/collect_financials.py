#!/usr/bin/env python3
"""
분기별 재무제표 수집 스크립트
- 네이버금융 크롤링
- 매출액, 영업이익, 당기순이익, ROE 등
"""

import os
import sys
import time
import random
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
]


def get_naver_financials(stock_code: str) -> dict:
    """네이버금융에서 재무제표 크롤링"""
    url = f"https://finance.naver.com/item/main.nhn?code={stock_code}"

    headers = {
        "User-Agent": random.choice(USER_AGENTS),
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        result = {
            "revenue": None,          # 매출액
            "operating_profit": None, # 영업이익
            "net_income": None,       # 당기순이익
            "roe": None,              # ROE
            "operating_margin": None, # 영업이익률
            "revenue_growth": None,   # 매출성장률
            "profit_growth": None,    # 영업이익성장률
        }

        # 주요재무정보 테이블 파싱
        # 실제 구현 시 네이버금융 구조에 맞게 수정 필요

        # 투자지표 테이블
        tables = soup.select("table.tb_type1")
        for table in tables:
            rows = table.select("tr")
            for row in rows:
                th = row.select_one("th")
                tds = row.select("td")

                if th and tds:
                    label = th.get_text(strip=True)

                    # 가장 최근 분기 데이터 (첫 번째 td)
                    if tds:
                        value_text = tds[0].get_text(strip=True).replace(",", "")

                        try:
                            if "ROE" in label:
                                result["roe"] = float(value_text)
                            elif "영업이익률" in label:
                                result["operating_margin"] = float(value_text)
                        except ValueError:
                            pass

        return result

    except Exception as e:
        print(f"❌ Error: {e}")
        return {}


def get_fnguide_financials(stock_code: str) -> dict:
    """FnGuide에서 상세 재무제표 (백업)"""
    # FnGuide는 별도 크롤링 로직 필요
    # 여기서는 스킵
    return {}


def calculate_growth_rates(current: dict, previous: dict) -> dict:
    """성장률 계산"""
    result = {}

    if current.get("revenue") and previous.get("revenue"):
        result["revenue_growth"] = (
            (current["revenue"] - previous["revenue"]) / previous["revenue"] * 100
        )

    if current.get("operating_profit") and previous.get("operating_profit"):
        if previous["operating_profit"] > 0:
            result["profit_growth"] = (
                (current["operating_profit"] - previous["operating_profit"])
                / previous["operating_profit"] * 100
            )

    return result


def collect_all_financials(stock_codes: list[str]) -> dict:
    """전체 종목 재무제표 수집"""
    results = {}

    for i, code in enumerate(stock_codes):
        print(f"[{i+1}/{len(stock_codes)}] {code}...", end=" ")

        data = get_naver_financials(code)
        if data:
            results[code] = data
            roe = data.get("roe", "N/A")
            margin = data.get("operating_margin", "N/A")
            print(f"ROE: {roe}%, 영업이익률: {margin}%")
        else:
            print("Failed")

        time.sleep(random.uniform(1.5, 2.5))

    return results


def save_to_supabase(results: dict):
    """재무제표 Supabase 저장"""
    # Service Role Key 사용 (RLS 우회)
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        print("⚠️ Supabase credentials not found")
        return

    try:
        from supabase import create_client

        client = create_client(supabase_url, supabase_key)
        saved_count = 0

        for code, data in results.items():
            update_data = {
                "updated_at": datetime.utcnow().isoformat(),
            }

            # 수익성 지표
            if data.get("roe") is not None:
                update_data["roe"] = data["roe"]
            if data.get("operating_margin") is not None:
                update_data["op_margin"] = data["operating_margin"]

            # 성장성 지표
            if data.get("revenue_growth") is not None:
                update_data["revenue_growth"] = data["revenue_growth"]
            if data.get("profit_growth") is not None:
                update_data["op_growth"] = data["profit_growth"]

            # 안정성 지표
            if data.get("debt_ratio") is not None:
                update_data["debt_ratio"] = data["debt_ratio"]
            if data.get("current_ratio") is not None:
                update_data["current_ratio"] = data["current_ratio"]

            # stocks_anal 테이블 업데이트
            if len(update_data) > 1:  # updated_at 외에 다른 데이터가 있으면
                response = client.table("stocks_anal").update(update_data).eq("code", code).execute()
                if response.data:
                    saved_count += 1

        print(f"✅ Supabase 저장 완료: {saved_count}/{len(results)}개 종목")

    except Exception as e:
        print(f"❌ Supabase error: {e}")


def main():
    print("=" * 50)
    print("📊 Quarterly Financial Data Collection")
    print("=" * 50)

    from collect_daily_prices import get_portfolio_stocks
    stock_codes = get_portfolio_stocks()
    print(f"📋 Target Stocks: {len(stock_codes)}개\n")

    results = collect_all_financials(stock_codes)

    print(f"\n📈 Collected: {len(results)}/{len(stock_codes)} stocks")

    if results:
        save_to_supabase(results)

    print("\n✅ Financial collection completed!")


if __name__ == "__main__":
    main()

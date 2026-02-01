#!/usr/bin/env python3
"""
밸류에이션 지표 수집 (PER, PBR, PSR)
- 네이버금융 크롤링
- 매일 시세와 함께 수집 (주가 연동 지표)
"""

import os
import sys
import time
import random
from datetime import datetime, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))


# User-Agent 로테이션
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
]


def get_naver_valuation(stock_code: str) -> dict:
    """네이버금융에서 밸류에이션 지표 수집"""
    url = f"https://finance.naver.com/item/main.nhn?code={stock_code}"

    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "ko-KR,ko;q=0.9",
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        result = {
            "per": None,
            "pbr": None,
            "psr": None,
            "market_cap": None,
            "dividend_yield": None,
        }

        # PER, PBR 추출 (투자정보 테이블)
        table = soup.select_one("table.per_table")
        if table:
            rows = table.select("tr")
            for row in rows:
                th = row.select_one("th")
                td = row.select_one("td")
                if th and td:
                    label = th.get_text(strip=True)
                    value = td.get_text(strip=True).replace(",", "")

                    if "PER" in label:
                        try:
                            result["per"] = float(value)
                        except ValueError:
                            pass
                    elif "PBR" in label:
                        try:
                            result["pbr"] = float(value)
                        except ValueError:
                            pass

        # 시가총액 추출
        market_cap_elem = soup.select_one("em#_market_sum")
        if market_cap_elem:
            try:
                # "1,234,567억원" 형식
                text = market_cap_elem.get_text(strip=True)
                text = text.replace(",", "").replace("억원", "").replace("조", "0000")
                result["market_cap"] = int(float(text) * 100000000)  # 억원 → 원
            except ValueError:
                pass

        # 배당수익률 추출
        dividend_elem = soup.select_one("em#_dvr")
        if dividend_elem:
            try:
                result["dividend_yield"] = float(dividend_elem.get_text(strip=True).replace("%", ""))
            except ValueError:
                pass

        return result

    except Exception as e:
        print(f"❌ {stock_code}: {e}")
        return {}


def get_naver_psr(stock_code: str, market_cap: int) -> float:
    """PSR 계산 (시가총액 / 매출액)"""
    url = f"https://finance.naver.com/item/main.nhn?code={stock_code}"

    try:
        # 매출액은 별도 API나 재무제표에서 가져와야 함
        # 여기서는 간단히 None 반환 (분기별 수집에서 처리)
        return None
    except Exception:
        return None


def collect_all_valuations(stock_codes: list[str]) -> dict:
    """전체 종목 밸류에이션 수집"""
    results = {}

    for i, code in enumerate(stock_codes):
        print(f"[{i+1}/{len(stock_codes)}] {code}...", end=" ")

        data = get_naver_valuation(code)
        if data:
            results[code] = data
            per = data.get("per", "N/A")
            pbr = data.get("pbr", "N/A")
            print(f"PER: {per}, PBR: {pbr}")
        else:
            print("Failed")

        # Rate limit 방지 (1-2초 랜덤 딜레이)
        time.sleep(random.uniform(1.0, 2.0))

    return results


def save_to_supabase(results: dict, target_date: str):
    """Supabase에 밸류에이션 저장"""
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

            # PER/PBR/PSR 저장
            if data.get("per") is not None:
                update_data["per"] = data["per"]
            if data.get("pbr") is not None:
                update_data["pbr"] = data["pbr"]
            if data.get("psr") is not None:
                update_data["psr"] = data["psr"]
            if data.get("market_cap") is not None:
                update_data["market_cap"] = data["market_cap"]
            if data.get("dividend_yield") is not None:
                update_data["dividend_yield"] = data["dividend_yield"]

            # stocks_anal 테이블 업데이트
            response = client.table("stocks_anal").update(update_data).eq("code", code).execute()
            if response.data:
                saved_count += 1

        print(f"✅ Supabase 저장 완료: {saved_count}/{len(results)}개 종목")

    except Exception as e:
        print(f"❌ Supabase error: {e}")


def main():
    print("=" * 50)
    print("📉 Valuation Collection (PER/PBR/PSR)")
    print("=" * 50)

    target_date = os.environ.get("TARGET_DATE", "").strip()
    if not target_date:
        target_date = (datetime.utcnow() + timedelta(hours=9)).strftime("%Y-%m-%d")

    print(f"📅 Target Date: {target_date}")

    # 포트폴리오 종목 조회
    from collect_daily_prices import get_portfolio_stocks
    stock_codes = get_portfolio_stocks()
    print(f"📋 Target Stocks: {len(stock_codes)}개\n")

    # 밸류에이션 수집
    results = collect_all_valuations(stock_codes)

    print(f"\n📈 Collected: {len(results)}/{len(stock_codes)} stocks")

    # 저장
    if results:
        save_to_supabase(results, target_date)

    print("\n✅ Valuation collection completed!")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
stocks_anal에 누락된 재무지표 전체 수집 스크립트
- PER, PBR, PSR, ROE, 영업이익률, 부채비율, 유동비율
- 매출성장률, 영업이익성장률, 배당수익률, 시가총액
Sources: 네이버 금융 + WiseReport
"""
import sys
import time
import random
from typing import Optional
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.collectors.naver_finance import (
    _fetch_page, _parse_number, get_valuation_indicators
)
from app.db.supabase_db import get_client


def collect_all_from_main_page(stock_code: str) -> dict:
    """
    네이버 금융 메인 페이지에서 모든 재무지표 한 번에 추출
    (get_stock_info + get_financial_summary를 합침 → 1회 요청)
    """
    url = f"https://finance.naver.com/item/main.naver?code={stock_code}"
    soup = _fetch_page(url, delay=0.5)

    if not soup:
        return {}

    result = {}

    try:
        # === 1. 투자지표 테이블 (per_table) → PER, PBR, 배당수익률 ===
        table = soup.select_one("table.per_table")
        if table:
            for row in table.select("tr"):
                th = row.select_one("th")
                td = row.select_one("td em")
                if not th or not td:
                    continue
                key = th.get_text(strip=True)
                value = td.get_text(strip=True)
                if "PER" in key:
                    result["per"] = _parse_number(value)
                elif "PBR" in key:
                    result["pbr"] = _parse_number(value)
                elif "배당수익률" in key:
                    result["dividend_yield"] = _parse_number(value.replace("%", ""))

        # 시가총액
        mc = soup.select_one("em#_market_sum")
        if mc:
            result["market_cap"] = _parse_number(mc.get_text(strip=True))

        # === 2. 주요재무정보 테이블 (tb_type1 중 "주요재무정보" 포함) ===
        # 연간 데이터: 컬럼 0=2년전, 1=작년, 2=올해(E), 3=내년(E)
        # 주의: tb_type1이 여러 개 (매도상위, 시세, 주요재무, 업종비교) 있으므로
        #       "주요재무정보" 테이블만 파싱해야 업종비교 데이터 덮어쓰기 방지
        tables = soup.select("table.tb_type1")
        revenue_prev = None
        revenue_curr = None
        op_prev = None
        op_curr = None

        fin_table = None
        for table in tables:
            text = table.get_text()
            if "주요재무정보" in text or "IFRS" in text:
                fin_table = table
                break

        if fin_table:
            for row in fin_table.select("tr"):
                th = row.select_one("th")
                tds = row.select("td")
                if not th or len(tds) < 2:
                    continue

                key = th.get_text(strip=True)
                # tds[0] = 2년전, tds[1] = 최근 연간
                val_prev = tds[0].get_text(strip=True) if len(tds) > 0 else ""
                val_curr = tds[1].get_text(strip=True) if len(tds) > 1 else ""

                # 영업이익률을 영업이익보다 먼저 체크 (substring 충돌 방지)
                if "매출액" in key and "성장" not in key:
                    revenue_prev = _parse_number(val_prev)
                    revenue_curr = _parse_number(val_curr)
                elif "영업이익률" in key:
                    result["op_margin"] = _parse_number(val_curr)
                elif "영업이익" in key and "증가율" not in key and "성장" not in key:
                    op_prev = _parse_number(val_prev)
                    op_curr = _parse_number(val_curr)
                elif "ROE" in key:
                    result["roe"] = _parse_number(val_curr)
                elif "부채비율" in key:
                    result["debt_ratio"] = _parse_number(val_curr)
                elif "유동비율" in key:
                    result["current_ratio"] = _parse_number(val_curr)
                elif "당좌비율" in key and "current_ratio" not in result:
                    # 유동비율이 없으면 당좌비율로 대체
                    result["current_ratio"] = _parse_number(val_curr)

        # 성장률 계산
        if revenue_prev and revenue_curr and revenue_prev != 0:
            result["revenue_growth"] = round(
                (revenue_curr - revenue_prev) / abs(revenue_prev) * 100, 2
            )
        if op_prev and op_curr and op_prev != 0:
            result["op_growth"] = round(
                (op_curr - op_prev) / abs(op_prev) * 100, 2
            )

        # PSR 계산: 시가총액(억) / 매출액(억)  (같은 단위이므로 직접 나눗셈)
        mc_val = result.get("market_cap")
        if mc_val and revenue_curr and revenue_curr > 0:
            result["psr"] = round(mc_val / revenue_curr, 2)

        # market_cap: 페이지에서 억 단위 표시 → DB는 원 단위 저장
        if mc_val and mc_val < 10_000_000:
            result["market_cap"] = int(mc_val * 100_000_000)

    except Exception as e:
        print(f"  ⚠️ 메인페이지 파싱 오류: {e}")

    return result


def collect_psr_from_wisereport(stock_code: str) -> Optional[float]:
    """WiseReport에서 PSR 추출"""
    try:
        data = get_valuation_indicators(stock_code)
        return data.get("psr")
    except Exception:
        return None


def main():
    client = get_client()

    # NULL이 많은 종목 조회 (psr OR roe OR op_margin이 NULL인 것)
    res = client.table("stocks_anal").select(
        "code,name,per,pbr,psr,roe,op_margin,debt_ratio,current_ratio,"
        "revenue_growth,op_growth,dividend_yield,market_cap"
    ).execute()
    all_stocks = res.data

    # 하나라도 NULL인 종목만 대상
    targets = []
    for s in all_stocks:
        fields = ["psr", "roe", "op_margin", "debt_ratio", "current_ratio",
                   "revenue_growth", "op_growth", "dividend_yield"]
        if any(s.get(f) is None for f in fields):
            targets.append(s)

    print(f"재무데이터 보완 대상: {len(targets)}개 / 전체 {len(all_stocks)}개")

    saved = 0
    errors = 0

    for i, stock in enumerate(targets, 1):
        code = stock["code"]
        name = stock["name"]

        # 1) 네이버 금융 메인 → 대부분의 지표
        data = collect_all_from_main_page(code)

        # 2) WiseReport → PSR (메인에 없는 지표)
        if stock.get("psr") is None:
            psr = collect_psr_from_wisereport(code)
            if psr is not None:
                data["psr"] = psr

        if not data:
            errors += 1
            if i % 30 == 0:
                print(f"  [{i}/{len(targets)}] {name}({code}) ❌ 데이터없음")
            continue

        # 기존에 이미 값이 있는 필드는 덮어쓰지 않음
        update = {}
        field_map = {
            "per": "per", "pbr": "pbr", "psr": "psr",
            "roe": "roe", "op_margin": "op_margin",
            "debt_ratio": "debt_ratio", "current_ratio": "current_ratio",
            "revenue_growth": "revenue_growth", "op_growth": "op_growth",
            "dividend_yield": "dividend_yield", "market_cap": "market_cap",
        }
        for db_field, data_key in field_map.items():
            if stock.get(db_field) is None and data.get(data_key) is not None:
                update[db_field] = data[data_key]

        if update:
            try:
                client.table("stocks_anal").update(update).eq("code", code).execute()
                saved += 1
            except Exception as e:
                print(f"  [{i}/{len(targets)}] {name}({code}) DB오류: {e}")
                errors += 1

        if i % 30 == 0 or i == len(targets):
            print(f"  [{i}/{len(targets)}] saved={saved} errors={errors}")

        # Rate limit: WiseReport 요청 포함 시 좀 더 대기
        time.sleep(random.uniform(0.3, 0.6))

    print(f"\n완료: {saved}/{len(targets)} 저장, {errors} 오류")

    # 결과 검증
    res2 = client.table("stocks_anal").select(
        "code,psr,roe,op_margin,debt_ratio,current_ratio,"
        "revenue_growth,op_growth,dividend_yield"
    ).execute()
    rows2 = res2.data
    for f in ["psr", "roe", "op_margin", "debt_ratio", "current_ratio",
              "revenue_growth", "op_growth", "dividend_yield"]:
        null_ct = sum(1 for r in rows2 if r.get(f) is None)
        print(f"  {f}: {null_ct} NULL / {len(rows2) - null_ct} filled")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
NULL sector 종목들의 업종 데이터 수집 스크립트
네이버 금융 메인 페이지에서 업종명을 추출하여 stocks_anal 테이블 업데이트
"""
import sys
import time
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.collectors.naver_finance import _fetch_page
from app.db.supabase_db import get_client


def get_sector_from_main_page(stock_code: str) -> str | None:
    """네이버 금융 메인 페이지에서 업종명 추출"""
    url = f"https://finance.naver.com/item/main.naver?code={stock_code}"
    soup = _fetch_page(url, delay=0.3)

    if not soup:
        return None

    try:
        compare_section = soup.select_one("div.section.trade_compare")
        if compare_section:
            sector_em = compare_section.select_one("em")
            if sector_em:
                return sector_em.get_text(strip=True)
    except Exception as e:
        print(f"  ! 파싱 오류 ({stock_code}): {e}")

    return None


def main():
    client = get_client()

    # sector가 NULL인 종목 조회
    res = client.table("stocks_anal").select("code,name,sector").is_("sector", "null").execute()
    targets = res.data

    print(f"업종 데이터 수집 대상: {len(targets)}개 (sector=NULL)")

    if not targets:
        print("모든 종목에 업종 데이터가 있습니다.")
        return

    updated = 0
    errors = 0

    for i, stock in enumerate(targets, 1):
        code = stock["code"]
        name = stock["name"]

        sector = get_sector_from_main_page(code)

        if sector:
            try:
                client.table("stocks_anal").update({"sector": sector}).eq("code", code).execute()
                updated += 1
                if i <= 5 or i % 20 == 0:
                    print(f"  [{i}/{len(targets)}] {name}({code}) → {sector}")
            except Exception as e:
                print(f"  [{i}/{len(targets)}] {name}({code}) DB오류: {e}")
                errors += 1
        else:
            errors += 1
            if i <= 5 or i % 20 == 0:
                print(f"  [{i}/{len(targets)}] {name}({code}) X 업종 없음")

        if i % 30 == 0 or i == len(targets):
            print(f"  진행: [{i}/{len(targets)}] updated={updated} errors={errors}")

        time.sleep(random.uniform(0.3, 0.6))

    print(f"\n완료: {updated}/{len(targets)} 업데이트, {errors} 실패")

    # 결과 검증
    res2 = client.table("stocks_anal").select("code,sector").execute()
    null_count = sum(1 for r in res2.data if r.get("sector") is None)
    print(f"남은 NULL sector: {null_count}개 / 전체 {len(res2.data)}개")


if __name__ == "__main__":
    main()

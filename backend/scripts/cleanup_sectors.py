#!/usr/bin/env python3
"""
업종 데이터 정리 스크립트
'(업종명 :가스유틸리티｜재무정보: 2025.09 분기 기준)' -> '가스유틸리티'
"""
import sys
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from app.db.supabase_db import get_client


def clean_sector_name(raw: str) -> str:
    """업종명에서 실제 이름만 추출"""
    # 패턴: (업종명 :XXX｜재무정보: ...)
    match = re.search(r"[：:]\s*(.+?)[｜|]", raw)
    if match:
        return match.group(1).strip()
    # 패턴: (업종명 :XXX)
    match = re.search(r"[：:]\s*(.+?)\)", raw)
    if match:
        return match.group(1).strip()
    return raw


def main():
    client = get_client()
    res = client.table("stocks_anal").select("code,name,sector").not_.is_("sector", "null").execute()
    stocks = res.data

    updated = 0
    for stock in stocks:
        sector = stock.get("sector", "")
        if not sector:
            continue

        clean = clean_sector_name(sector)
        if clean != sector:
            try:
                client.table("stocks_anal").update({"sector": clean}).eq("code", stock["code"]).execute()
                updated += 1
            except Exception as e:
                print(f"  DB error {stock['code']}: {e}")

    print(f"Updated {updated} sectors")

    # Verify
    res2 = client.table("stocks_anal").select("sector").not_.is_("sector", "null").execute()
    sectors = set(r["sector"] for r in res2.data if r.get("sector"))
    print(f"Unique sectors ({len(sectors)}):")
    for s in sorted(sectors):
        print(f"  - {s}")


if __name__ == "__main__":
    main()

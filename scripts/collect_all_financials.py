#!/usr/bin/env python3
"""
모든 재무 데이터 수집 (통합 스크립트)
- PER, PBR, PSR, ROE, 영업이익률
- 성장률, 부채비율, 유동비율
- 네이버금융 크롤링

사용법:
    python scripts/collect_all_financials.py

실행 전 필수 사항:
    1. Supabase SQL Editor에서 migrate_add_financials.sql 실행
    2. .env에 SUPABASE_SERVICE_ROLE_KEY 설정
"""

import os
import sys
import time
import random
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# 프로젝트 루트 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
load_dotenv(Path(__file__).parent.parent / "backend" / ".env")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
]


def get_naver_financials(stock_code: str) -> dict:
    """네이버금융에서 모든 재무 지표 수집"""
    url = f"https://finance.naver.com/item/main.nhn?code={stock_code}"

    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "ko-KR,ko;q=0.9",
    }

    result = {
        "per": None,
        "pbr": None,
        "psr": None,
        "roe": None,
        "op_margin": None,
        "revenue_growth": None,
        "op_growth": None,
        "debt_ratio": None,
        "current_ratio": None,
        "dividend_yield": None,
        "market_cap": None,
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # === 1. 투자정보 (PER, PBR, 배당수익률) ===
        per_table = soup.select_one("table.per_table")
        if per_table:
            rows = per_table.select("tr")
            for row in rows:
                th = row.select_one("th")
                td = row.select_one("td")
                em = td.select_one("em") if td else None
                if th and em:
                    label = th.get_text(strip=True)
                    value = em.get_text(strip=True).replace(",", "")
                    try:
                        if "PER" in label and "추정" not in label:
                            result["per"] = float(value)
                        elif "PBR" in label:
                            result["pbr"] = float(value)
                        elif "배당수익률" in label:
                            result["dividend_yield"] = float(value)
                    except (ValueError, TypeError):
                        pass

        # === 2. 시가총액 ===
        market_cap_elem = soup.select_one("em#_market_sum")
        if market_cap_elem:
            try:
                import re
                text = market_cap_elem.get_text(strip=True)
                # "950조 1,019억원" 또는 "1,234억원" 형식 처리
                text = text.replace(",", "").replace("억원", "").strip()

                total_billions = 0  # 억원 단위

                # 조 단위 추출
                jo_match = re.search(r"(\d+)조", text)
                if jo_match:
                    total_billions += int(jo_match.group(1)) * 10000  # 1조 = 10000억

                # 억 단위 추출 (조 뒤의 숫자 또는 단독)
                text_after_jo = re.sub(r"\d+조", "", text).strip()
                if text_after_jo:
                    try:
                        total_billions += int(text_after_jo)
                    except ValueError:
                        pass

                if total_billions > 0:
                    result["market_cap"] = total_billions * 100000000  # 억원 → 원
            except (ValueError, TypeError):
                pass

        # === 3. 기업실적분석 테이블 (ROE, 부채비율, 성장률 등) ===
        tables = soup.select("table.tb_type1")
        financial_data = {}

        # 기업실적분석 테이블 찾기 (3번째 또는 '매출액' 포함된 테이블)
        for table in tables:
            rows = table.select("tr")
            for row in rows:
                th = row.select_one("th")
                tds = row.select("td")

                if th and tds:
                    label = th.get_text(strip=True)
                    values = [td.get_text(strip=True).replace(",", "").replace("%", "") for td in tds]

                    # 데이터 저장 (연간 실적 기준 - 처음 3개 열)
                    if values:
                        financial_data[label] = values[:4]

                    # 최신 연간 데이터 (인덱스 2 = 가장 최근 연도)
                    idx = 2 if len(values) > 2 else 0
                    value_text = values[idx] if len(values) > idx else values[0] if values else ""

                    try:
                        # ROE(지배주주) 우선 사용 (기업실적분석 테이블)
                        if "ROE(지배주주)" in label or "ROE(지배" in label:
                            result["roe"] = float(value_text)
                        elif "영업이익률" in label and "증가율" not in label:
                            result["op_margin"] = float(value_text)
                        elif "부채비율" in label:
                            result["debt_ratio"] = float(value_text)
                        elif "당좌비율" in label:  # 유동비율 대신 당좌비율 사용
                            result["current_ratio"] = float(value_text)
                    except (ValueError, TypeError):
                        pass

        # === 4. 성장률 계산 (연간 기준) ===
        # 매출성장률: (최근연도 - 전년도) / 전년도 * 100
        if "매출액" in financial_data:
            try:
                values = financial_data["매출액"]
                if len(values) >= 3:
                    curr = float(values[2])  # 2024년 (가장 최근)
                    prev = float(values[1])  # 2023년
                    if prev > 0:
                        result["revenue_growth"] = round((curr - prev) / prev * 100, 2)
            except (ValueError, TypeError, IndexError):
                pass

        # 영업이익성장률
        if "영업이익" in financial_data:
            try:
                values = financial_data["영업이익"]
                if len(values) >= 3:
                    curr = float(values[2])
                    prev = float(values[1])
                    if prev > 0:
                        result["op_growth"] = round((curr - prev) / prev * 100, 2)
            except (ValueError, TypeError, IndexError):
                pass

        # === 5. PSR 계산 (시가총액 / 매출액) ===
        if result["market_cap"] and "매출액" in financial_data:
            try:
                values = financial_data["매출액"]
                if len(values) >= 3:
                    revenue = float(values[2]) * 100000000  # 억원 → 원
                    if revenue > 0:
                        result["psr"] = round(result["market_cap"] / revenue, 2)
            except (ValueError, TypeError, IndexError):
                pass

        return result

    except Exception as e:
        print(f"  ⚠️ 크롤링 오류: {e}")
        return result


def get_stocks_from_supabase() -> list[dict]:
    """Supabase에서 종목 목록 조회"""
    try:
        from app.db import supabase_db
        stocks = supabase_db.get_all_stocks(active_only=True)
        return stocks
    except Exception as e:
        print(f"❌ Supabase 조회 실패: {e}")
        return []


def save_to_supabase(code: str, data: dict) -> bool:
    """개별 종목 재무 데이터 Supabase 저장"""
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        return False

    try:
        from supabase import create_client
        client = create_client(supabase_url, supabase_key)

        update_data = {
            "updated_at": datetime.utcnow().isoformat(),
        }

        # None이 아닌 값만 추가
        for key in ["per", "pbr", "psr", "roe", "op_margin", "revenue_growth",
                    "op_growth", "debt_ratio", "current_ratio", "dividend_yield", "market_cap"]:
            if data.get(key) is not None:
                update_data[key] = data[key]

        if len(update_data) > 1:  # updated_at 외에 다른 데이터가 있으면
            response = client.table("stocks_anal").update(update_data).eq("code", code).execute()
            return bool(response.data)

        return False

    except Exception as e:
        print(f"  ⚠️ 저장 실패: {e}")
        return False


def main():
    print("=" * 60)
    print("📊 재무 데이터 통합 수집 (네이버금융)")
    print("=" * 60)

    # 종목 목록 조회
    stocks = get_stocks_from_supabase()
    if not stocks:
        print("❌ 종목 목록을 가져올 수 없습니다.")
        print("   Supabase 연결을 확인하세요.")
        return

    print(f"\n📋 대상 종목: {len(stocks)}개\n")

    # 수집 결과 통계
    success_count = 0
    fail_count = 0
    has_per = 0
    has_roe = 0

    for i, stock in enumerate(stocks):
        code = stock.get("code", "")
        name = stock.get("name", "")

        print(f"[{i+1:3d}/{len(stocks)}] {name} ({code})...", end=" ")

        # 재무 데이터 수집
        data = get_naver_financials(code)

        # 결과 출력
        per = data.get("per")
        roe = data.get("roe")
        pbr = data.get("pbr")

        info_parts = []
        if per is not None:
            info_parts.append(f"PER:{per:.1f}")
            has_per += 1
        if pbr is not None:
            info_parts.append(f"PBR:{pbr:.2f}")
        if roe is not None:
            info_parts.append(f"ROE:{roe:.1f}%")
            has_roe += 1

        if info_parts:
            print(", ".join(info_parts), end=" ")

        # Supabase 저장
        if save_to_supabase(code, data):
            print("✅")
            success_count += 1
        else:
            print("❌")
            fail_count += 1

        # Rate limit 방지 (1-2초 랜덤 딜레이)
        time.sleep(random.uniform(1.0, 2.0))

    # 결과 요약
    print("\n" + "=" * 60)
    print("📈 수집 결과")
    print("=" * 60)
    print(f"  총 종목: {len(stocks)}개")
    print(f"  저장 성공: {success_count}개")
    print(f"  저장 실패: {fail_count}개")
    print(f"  PER 데이터: {has_per}개")
    print(f"  ROE 데이터: {has_roe}개")
    print("\n✅ 재무 데이터 수집 완료!")


if __name__ == "__main__":
    main()

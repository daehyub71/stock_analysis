"""
Naver Finance Crawler
- 네이버 금융에서 재무정보, 업종평균 등 크롤링
- https://finance.naver.com/
"""

import re
import time
import random
from datetime import datetime
from typing import Optional
from decimal import Decimal

import requests
from bs4 import BeautifulSoup


# User-Agent 로테이션
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]


def _get_headers() -> dict:
    """랜덤 User-Agent 헤더"""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
        "Referer": "https://finance.naver.com/",
    }


def _parse_number(text: str) -> Optional[float]:
    """숫자 문자열 파싱 (쉼표, 한글 단위 처리)"""
    if not text:
        return None

    text = text.strip().replace(",", "").replace(" ", "")

    # N/A, - 처리
    if text in ["N/A", "-", "", "적자"]:
        return None

    # 억, 조 단위 처리
    multiplier = 1
    if "조" in text:
        text = text.replace("조", "")
        multiplier = 1_0000_0000_0000
    elif "억" in text:
        text = text.replace("억", "")
        multiplier = 1_0000_0000

    try:
        return float(text) * multiplier
    except ValueError:
        return None


def _fetch_page(url: str, delay: float = 0.5) -> Optional[BeautifulSoup]:
    """페이지 fetch + 딜레이"""
    time.sleep(delay + random.uniform(0, 0.3))

    try:
        response = requests.get(url, headers=_get_headers(), timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.content, "html.parser")
    except Exception as e:
        print(f"❌ 페이지 fetch 실패 ({url}): {e}")
        return None


def get_stock_info(stock_code: str) -> dict:
    """
    종목 기본 정보 조회
    - 종목명, 업종, PER, PBR, PSR 등

    URL: https://finance.naver.com/item/main.naver?code=005930
    """
    url = f"https://finance.naver.com/item/main.naver?code={stock_code}"
    soup = _fetch_page(url)

    if not soup:
        return {}

    result = {
        "stock_code": stock_code,
        "crawled_at": datetime.now().isoformat(),
    }

    try:
        # 종목명
        title = soup.select_one("div.wrap_company h2 a")
        if title:
            result["name"] = title.get_text(strip=True)

        # 업종
        sector = soup.select_one("div.section.trade_compare em")
        if sector:
            result["sector"] = sector.get_text(strip=True)

        # 투자지표 테이블
        table = soup.select_one("table.per_table")
        if table:
            rows = table.select("tr")
            for row in rows:
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
                    result["div_yield"] = _parse_number(value.replace("%", ""))

        # 시가총액 (상단 정보)
        market_cap_elem = soup.select_one("em#_market_sum")
        if market_cap_elem:
            result["market_cap"] = _parse_number(market_cap_elem.get_text(strip=True))

    except Exception as e:
        print(f"❌ 종목 정보 파싱 실패 ({stock_code}): {e}")

    return result


def get_financial_summary(stock_code: str) -> dict:
    """
    재무 정보 요약 조회
    - 매출액, 영업이익, ROE, 영업이익률 등

    URL: https://finance.naver.com/item/main.naver?code=005930 (재무정보 탭)
    """
    url = f"https://finance.naver.com/item/main.naver?code={stock_code}"
    soup = _fetch_page(url)

    if not soup:
        return {}

    result = {
        "stock_code": stock_code,
        "crawled_at": datetime.now().isoformat(),
    }

    try:
        # 재무정보 테이블
        tables = soup.select("table.tb_type1")

        for table in tables:
            rows = table.select("tr")
            for row in rows:
                th = row.select_one("th")
                tds = row.select("td")

                if not th or len(tds) < 4:
                    continue

                key = th.get_text(strip=True)
                # 최근 연간 데이터 (두 번째 컬럼)
                value = tds[1].get_text(strip=True) if len(tds) > 1 else ""

                if "매출액" in key:
                    result["revenue"] = _parse_number(value)
                elif "영업이익" in key and "증가율" not in key:
                    result["operating_profit"] = _parse_number(value)
                elif "당기순이익" in key:
                    result["net_income"] = _parse_number(value)
                elif "ROE" in key:
                    result["roe"] = _parse_number(value)
                elif "부채비율" in key:
                    result["debt_ratio"] = _parse_number(value)
                elif "유동비율" in key:
                    result["current_ratio"] = _parse_number(value)
                elif "영업이익률" in key:
                    result["operating_margin"] = _parse_number(value)

    except Exception as e:
        print(f"❌ 재무 정보 파싱 실패 ({stock_code}): {e}")

    return result


def get_financial_statements(stock_code: str) -> dict:
    """
    재무제표 상세 조회
    - 연간/분기 재무제표

    URL: https://finance.naver.com/item/coinfo.naver?code=005930
    """
    url = f"https://finance.naver.com/item/coinfo.naver?code={stock_code}&target=finsum_more"
    soup = _fetch_page(url)

    if not soup:
        return {}

    result = {
        "stock_code": stock_code,
        "annual": [],
        "quarterly": [],
        "crawled_at": datetime.now().isoformat(),
    }

    # 재무제표는 iframe으로 로드되어 별도 처리 필요
    # 간단한 방법: 기본 페이지의 요약 데이터 사용

    return result


def get_valuation_indicators(stock_code: str) -> dict:
    """
    밸류에이션 지표 조회
    - PER, PBR, PSR, PCR, EV/EBITDA

    URL: https://navercomp.wisereport.co.kr/v2/company/c1010001.aspx?cmp_cd=005930
    """
    # WiseReport (네이버 컨센서스)
    url = f"https://navercomp.wisereport.co.kr/v2/company/c1010001.aspx?cmp_cd={stock_code}"
    soup = _fetch_page(url, delay=1.0)

    if not soup:
        return {}

    result = {
        "stock_code": stock_code,
        "crawled_at": datetime.now().isoformat(),
    }

    try:
        # 투자지표 섹션
        tables = soup.select("table")

        for table in tables:
            rows = table.select("tr")
            for row in rows:
                cells = row.select("td, th")
                if len(cells) < 2:
                    continue

                key = cells[0].get_text(strip=True)
                value = cells[1].get_text(strip=True) if len(cells) > 1 else ""

                if "PER" in key and "FWD" not in key:
                    result["per"] = _parse_number(value)
                elif "PBR" in key:
                    result["pbr"] = _parse_number(value)
                elif "PSR" in key:
                    result["psr"] = _parse_number(value)
                elif "ROE" in key:
                    result["roe"] = _parse_number(value)
                elif "ROA" in key:
                    result["roa"] = _parse_number(value)

    except Exception as e:
        print(f"❌ 밸류에이션 지표 파싱 실패 ({stock_code}): {e}")

    return result


def get_sector_info(stock_code: str) -> dict:
    """
    업종 정보 및 업종 평균 조회

    URL: https://finance.naver.com/item/main.naver?code=005930
    """
    url = f"https://finance.naver.com/item/main.naver?code={stock_code}"
    soup = _fetch_page(url)

    if not soup:
        return {}

    result = {
        "stock_code": stock_code,
        "crawled_at": datetime.now().isoformat(),
    }

    try:
        # 업종 비교 섹션
        compare_section = soup.select_one("div.section.trade_compare")
        if compare_section:
            # 업종명
            sector_em = compare_section.select_one("em")
            if sector_em:
                result["sector"] = sector_em.get_text(strip=True)

            # 업종 평균 테이블
            table = compare_section.select_one("table")
            if table:
                rows = table.select("tr")
                for row in rows:
                    th = row.select_one("th")
                    tds = row.select("td")

                    if not th or len(tds) < 2:
                        continue

                    key = th.get_text(strip=True)
                    stock_val = tds[0].get_text(strip=True)  # 종목 값
                    sector_val = tds[1].get_text(strip=True)  # 업종 평균

                    if "PER" in key:
                        result["per"] = _parse_number(stock_val)
                        result["sector_avg_per"] = _parse_number(sector_val)
                    elif "등락률" in key:
                        result["change_rate"] = _parse_number(stock_val.replace("%", ""))
                        result["sector_avg_change_rate"] = _parse_number(sector_val.replace("%", ""))

    except Exception as e:
        print(f"❌ 업종 정보 파싱 실패 ({stock_code}): {e}")

    return result


def get_dividend_info(stock_code: str) -> dict:
    """
    배당 정보 조회

    URL: https://finance.naver.com/item/main.naver?code=005930
    """
    url = f"https://finance.naver.com/item/main.naver?code={stock_code}"
    soup = _fetch_page(url)

    if not soup:
        return {}

    result = {
        "stock_code": stock_code,
        "crawled_at": datetime.now().isoformat(),
    }

    try:
        # 투자정보 테이블에서 배당수익률 추출
        table = soup.select_one("table.per_table")
        if table:
            rows = table.select("tr")
            for row in rows:
                th = row.select_one("th")
                td = row.select_one("td em")

                if not th or not td:
                    continue

                key = th.get_text(strip=True)
                value = td.get_text(strip=True)

                if "배당수익률" in key:
                    result["div_yield"] = _parse_number(value.replace("%", ""))

    except Exception as e:
        print(f"❌ 배당 정보 파싱 실패 ({stock_code}): {e}")

    return result


def get_company_overview(stock_code: str) -> dict:
    """
    기업개요 조회
    - 네이버 증권 메인 페이지의 기업개요 섹션 크롤링

    URL: https://finance.naver.com/item/main.naver?code=005810

    Returns:
        {"stock_code": "005810", "overview": ["bullet1", ...], "crawled_at": "..."}
    """
    url = f"https://finance.naver.com/item/main.naver?code={stock_code}"
    soup = _fetch_page(url)

    if not soup:
        return {"stock_code": stock_code, "overview": []}

    result = {
        "stock_code": stock_code,
        "overview": [],
        "crawled_at": datetime.now().isoformat(),
    }

    try:
        summary = soup.select_one("div#summary_info")
        if summary:
            paragraphs = [p.get_text(strip=True) for p in summary.select("p")]
            result["overview"] = [p for p in paragraphs if p]
    except Exception as e:
        print(f"❌ 기업개요 파싱 실패 ({stock_code}): {e}")

    return result


def get_company_overview_batch(
    stock_codes: list[str],
    delay: float = 0.8,
) -> dict[str, list[str]]:
    """
    여러 종목의 기업개요 일괄 수집

    Returns:
        종목코드 → 기업개요 리스트 딕셔너리
    """
    results = {}
    total = len(stock_codes)

    for i, code in enumerate(stock_codes, 1):
        print(f"[{i}/{total}] {code} 기업개요 수집 중...")
        data = get_company_overview(code)
        results[code] = data.get("overview", [])

        if i < total:
            time.sleep(delay + random.uniform(0, 0.3))

    return results


def get_all_financial_data(stock_code: str) -> dict:
    """
    종합 재무 데이터 조회
    - 기본정보 + 재무요약 + 밸류에이션 + 업종정보 + 배당정보

    Args:
        stock_code: 종목코드

    Returns:
        종합 재무 데이터
    """
    result = {
        "stock_code": stock_code,
        "crawled_at": datetime.now().isoformat(),
    }

    # 기본 정보 (PER, PBR, 업종)
    basic_info = get_stock_info(stock_code)
    result.update(basic_info)

    # 재무 요약
    financial = get_financial_summary(stock_code)
    result.update({k: v for k, v in financial.items() if k not in result})

    # 업종 정보 (업종 평균 포함)
    sector_info = get_sector_info(stock_code)
    result.update({k: v for k, v in sector_info.items() if k not in result})

    return result


# === Batch 수집 함수 ===

def collect_financial_data_batch(
    stock_codes: list[str],
    delay: float = 1.0,
) -> dict[str, dict]:
    """
    여러 종목의 재무 데이터 일괄 수집

    Args:
        stock_codes: 종목코드 리스트
        delay: 요청 간 딜레이 (초)

    Returns:
        종목코드 → 재무 데이터 딕셔너리
    """
    results = {}
    total = len(stock_codes)

    for i, code in enumerate(stock_codes, 1):
        print(f"[{i}/{total}] {code} 재무 데이터 수집 중...")
        data = get_all_financial_data(code)
        results[code] = data

        if i < total:
            time.sleep(delay + random.uniform(0, 0.5))

    return results


if __name__ == "__main__":
    # 테스트
    print("=== Naver Finance Crawler 테스트 ===\n")

    # 삼성전자 종합 데이터
    data = get_all_financial_data("005930")

    print(f"종목명: {data.get('name')}")
    print(f"업종: {data.get('sector')}")
    print(f"PER: {data.get('per')}")
    print(f"PBR: {data.get('pbr')}")
    print(f"업종평균 PER: {data.get('sector_avg_per')}")
    print(f"ROE: {data.get('roe')}")
    print(f"부채비율: {data.get('debt_ratio')}")
    print(f"배당수익률: {data.get('div_yield')}%")

    print("\n✅ Naver Finance Crawler 테스트 완료")

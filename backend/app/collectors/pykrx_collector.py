"""
pykrx Collector - KIS API 백업용 데이터 수집기
- KRX (한국거래소) 공개 데이터 수집
- API 키 불필요, Rate limit 없음
- https://github.com/sharebook-kr/pykrx
"""

import time
from datetime import datetime, timedelta
from typing import Optional

from pykrx import stock as krx


def get_market_ohlcv(
    stock_code: str,
    start_date: str,
    end_date: str = None,
) -> list[dict]:
    """
    일별 OHLCV 데이터 조회

    Args:
        stock_code: 종목코드 (6자리)
        start_date: 시작일 (YYYY-MM-DD 또는 YYYYMMDD)
        end_date: 종료일 (기본값: 오늘)

    Returns:
        일별 시세 리스트
    """
    if not end_date:
        end_date = datetime.now().strftime("%Y%m%d")

    # 날짜 형식 통일 (YYYYMMDD)
    start_date = start_date.replace("-", "")
    end_date = end_date.replace("-", "")

    try:
        df = krx.get_market_ohlcv_by_date(start_date, end_date, stock_code)

        if df.empty:
            return []

        results = []
        for date_idx, row in df.iterrows():
            date_str = date_idx.strftime("%Y-%m-%d")
            results.append({
                "stock_code": stock_code,
                "date": date_str,
                "open": int(row["시가"]),
                "high": int(row["고가"]),
                "low": int(row["저가"]),
                "close": int(row["종가"]),
                "volume": int(row["거래량"]),
                "trading_value": int(row.get("거래대금", 0)),
                "change_rate": float(row.get("등락률", 0)),
            })

        return results

    except Exception as e:
        print(f"❌ pykrx 데이터 조회 실패 ({stock_code}): {e}")
        return []


def get_current_price(stock_code: str) -> dict:
    """
    현재가 조회 (당일 종가 기준)

    Args:
        stock_code: 종목코드

    Returns:
        현재가 정보
    """
    today = datetime.now().strftime("%Y%m%d")
    yesterday = (datetime.now() - timedelta(days=7)).strftime("%Y%m%d")

    try:
        df = krx.get_market_ohlcv_by_date(yesterday, today, stock_code)

        if df.empty:
            return {}

        # 최신 데이터
        latest = df.iloc[-1]
        date_str = df.index[-1].strftime("%Y-%m-%d")

        return {
            "stock_code": stock_code,
            "date": date_str,
            "current_price": int(latest["종가"]),
            "open": int(latest["시가"]),
            "high": int(latest["고가"]),
            "low": int(latest["저가"]),
            "volume": int(latest["거래량"]),
            "trading_value": int(latest.get("거래대금", 0)),
            "change_rate": float(latest.get("등락률", 0)),
        }

    except Exception as e:
        print(f"❌ pykrx 현재가 조회 실패 ({stock_code}): {e}")
        return {}


def get_market_cap(stock_code: str, date: str = None) -> dict:
    """
    시가총액 조회

    Args:
        stock_code: 종목코드
        date: 기준일 (기본값: 오늘)

    Returns:
        시가총액 정보
    """
    if not date:
        date = datetime.now().strftime("%Y%m%d")
    else:
        date = date.replace("-", "")

    try:
        df = krx.get_market_cap_by_date(date, date, stock_code)

        if df.empty:
            return {}

        row = df.iloc[0]
        return {
            "stock_code": stock_code,
            "date": date,
            "market_cap": int(row["시가총액"]),
            "shares_outstanding": int(row["상장주식수"]),
            "volume": int(row.get("거래량", 0)),
            "trading_value": int(row.get("거래대금", 0)),
        }

    except Exception as e:
        print(f"❌ pykrx 시가총액 조회 실패 ({stock_code}): {e}")
        return {}


def get_stock_fundamental(stock_code: str, date: str = None) -> dict:
    """
    기본적 지표 조회 (PER, PBR, EPS, BPS, DIV)

    Args:
        stock_code: 종목코드
        date: 기준일 (기본값: 오늘)

    Returns:
        기본적 지표
    """
    if not date:
        date = datetime.now().strftime("%Y%m%d")
    else:
        date = date.replace("-", "")

    try:
        df = krx.get_market_fundamental_by_date(date, date, stock_code)

        if df.empty:
            return {}

        row = df.iloc[0]
        return {
            "stock_code": stock_code,
            "date": date,
            "per": float(row.get("PER", 0)) if row.get("PER") else None,
            "pbr": float(row.get("PBR", 0)) if row.get("PBR") else None,
            "eps": float(row.get("EPS", 0)) if row.get("EPS") else None,
            "bps": float(row.get("BPS", 0)) if row.get("BPS") else None,
            "dps": float(row.get("DPS", 0)) if row.get("DPS") else None,  # 주당배당금
            "div_yield": float(row.get("DIV", 0)) if row.get("DIV") else None,  # 배당수익률
        }

    except Exception as e:
        print(f"❌ pykrx 기본적 지표 조회 실패 ({stock_code}): {e}")
        return {}


def get_all_stock_codes(market: str = "ALL") -> list[dict]:
    """
    전체 종목 코드 조회

    Args:
        market: KOSPI, KOSDAQ, ALL

    Returns:
        종목 코드 및 이름 리스트
    """
    today = datetime.now().strftime("%Y%m%d")

    try:
        if market == "ALL":
            kospi = krx.get_market_ticker_list(today, market="KOSPI")
            kosdaq = krx.get_market_ticker_list(today, market="KOSDAQ")

            results = []
            for code in kospi:
                name = krx.get_market_ticker_name(code)
                results.append({"code": code, "name": name, "market": "KOSPI"})

            for code in kosdaq:
                name = krx.get_market_ticker_name(code)
                results.append({"code": code, "name": name, "market": "KOSDAQ"})

            return results
        else:
            codes = krx.get_market_ticker_list(today, market=market)
            return [
                {"code": code, "name": krx.get_market_ticker_name(code), "market": market}
                for code in codes
            ]

    except Exception as e:
        print(f"❌ pykrx 종목 코드 조회 실패: {e}")
        return []


def get_stock_name(stock_code: str) -> str:
    """종목명 조회"""
    try:
        return krx.get_market_ticker_name(stock_code)
    except Exception:
        return ""


def get_sector_info(stock_code: str) -> Optional[str]:
    """업종 정보 조회"""
    try:
        # pykrx는 직접적인 업종 정보를 제공하지 않음
        # 네이버금융에서 조회 필요
        return None
    except Exception:
        return None


# === Batch 수집 함수 ===

def collect_daily_prices_batch(
    stock_codes: list[str],
    start_date: str,
    end_date: str = None,
    delay: float = 0.5,
) -> dict[str, list[dict]]:
    """
    여러 종목의 일별 시세 일괄 수집

    Args:
        stock_codes: 종목코드 리스트
        start_date: 시작일
        end_date: 종료일
        delay: 요청 간 딜레이 (초)

    Returns:
        종목코드 → 시세 리스트 딕셔너리
    """
    results = {}
    total = len(stock_codes)

    for i, code in enumerate(stock_codes, 1):
        print(f"[{i}/{total}] {code} 수집 중...")
        prices = get_market_ohlcv(code, start_date, end_date)
        results[code] = prices

        if i < total:
            time.sleep(delay)

    return results


def collect_fundamentals_batch(
    stock_codes: list[str],
    date: str = None,
    delay: float = 0.3,
) -> dict[str, dict]:
    """
    여러 종목의 기본적 지표 일괄 수집

    Args:
        stock_codes: 종목코드 리스트
        date: 기준일
        delay: 요청 간 딜레이 (초)

    Returns:
        종목코드 → 기본적 지표 딕셔너리
    """
    results = {}
    total = len(stock_codes)

    for i, code in enumerate(stock_codes, 1):
        print(f"[{i}/{total}] {code} 기본적 지표 수집 중...")
        fundamental = get_stock_fundamental(code, date)
        results[code] = fundamental

        if i < total:
            time.sleep(delay)

    return results


if __name__ == "__main__":
    # 테스트
    print("=== pykrx Collector 테스트 ===\n")

    # 삼성전자 현재가
    price = get_current_price("005930")
    if price:
        print(f"삼성전자 현재가: {price.get('current_price', 0):,}원")

    # 삼성전자 최근 5일 시세
    prices = get_market_ohlcv("005930", (datetime.now() - timedelta(days=10)).strftime("%Y%m%d"))
    print(f"삼성전자 최근 시세: {len(prices)}일치")

    # 기본적 지표
    fundamental = get_stock_fundamental("005930")
    if fundamental:
        print(f"삼성전자 PER: {fundamental.get('per')}, PBR: {fundamental.get('pbr')}")

    print("\n✅ pykrx Collector 테스트 완료")

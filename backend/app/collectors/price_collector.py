"""
Unified Price Collector
- KIS API 우선, pykrx 백업
- 자동 fallback 로직
"""

from datetime import datetime, timedelta
from typing import Optional

from app.collectors import kis_api, pykrx_collector


class PriceCollector:
    """통합 시세 수집기"""

    def __init__(self, prefer_kis: bool = True):
        """
        Args:
            prefer_kis: KIS API 우선 사용 여부 (기본: True)
        """
        self.prefer_kis = prefer_kis
        self._kis_available = None

    def _check_kis_available(self) -> bool:
        """KIS API 사용 가능 여부 확인"""
        if self._kis_available is None:
            try:
                self._kis_available = kis_api.check_kis_connection()
            except Exception:
                self._kis_available = False
        return self._kis_available

    def get_current_price(self, stock_code: str) -> dict:
        """
        현재가 조회

        Args:
            stock_code: 종목코드

        Returns:
            현재가 정보 딕셔너리
        """
        # KIS API 시도
        if self.prefer_kis and self._check_kis_available():
            try:
                result = kis_api.get_current_price(stock_code)
                if result and result.get("current_price"):
                    result["source"] = "KIS"
                    return result
            except Exception as e:
                print(f"⚠️ KIS API 실패, pykrx로 fallback: {e}")

        # pykrx fallback
        try:
            result = pykrx_collector.get_current_price(stock_code)
            if result:
                result["source"] = "pykrx"
            return result
        except Exception as e:
            print(f"❌ pykrx도 실패: {e}")
            return {}

    def get_daily_prices(
        self,
        stock_code: str,
        start_date: str = None,
        end_date: str = None,
        limit: int = 100,
    ) -> list[dict]:
        """
        일별 시세 조회

        Args:
            stock_code: 종목코드
            start_date: 시작일 (YYYY-MM-DD)
            end_date: 종료일 (YYYY-MM-DD)
            limit: 최대 조회 건수

        Returns:
            일별 시세 리스트
        """
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

        # KIS API 시도
        if self.prefer_kis and self._check_kis_available():
            try:
                result = kis_api.get_daily_prices(stock_code, start_date, end_date, limit)
                if result:
                    for item in result:
                        item["source"] = "KIS"
                    return result
            except Exception as e:
                print(f"⚠️ KIS API 실패, pykrx로 fallback: {e}")

        # pykrx fallback
        try:
            result = pykrx_collector.get_market_ohlcv(stock_code, start_date, end_date)
            if result:
                for item in result[:limit]:
                    item["source"] = "pykrx"
                return result[:limit]
            return []
        except Exception as e:
            print(f"❌ pykrx도 실패: {e}")
            return []

    def get_fundamental(self, stock_code: str, date: str = None) -> dict:
        """
        기본적 지표 조회 (PER, PBR 등)

        Args:
            stock_code: 종목코드
            date: 기준일

        Returns:
            기본적 지표 딕셔너리
        """
        # pykrx 사용 (KIS API는 기본적 지표 제공 안함)
        try:
            result = pykrx_collector.get_stock_fundamental(stock_code, date)
            if result:
                result["source"] = "pykrx"
            return result
        except Exception as e:
            print(f"❌ 기본적 지표 조회 실패: {e}")
            return {}

    def get_market_cap(self, stock_code: str, date: str = None) -> dict:
        """
        시가총액 조회

        Args:
            stock_code: 종목코드
            date: 기준일

        Returns:
            시가총액 정보
        """
        try:
            result = pykrx_collector.get_market_cap(stock_code, date)
            if result:
                result["source"] = "pykrx"
            return result
        except Exception as e:
            print(f"❌ 시가총액 조회 실패: {e}")
            return {}


# 싱글톤 인스턴스
_collector: Optional[PriceCollector] = None


def get_collector() -> PriceCollector:
    """PriceCollector 싱글톤"""
    global _collector
    if _collector is None:
        _collector = PriceCollector()
    return _collector


# === 편의 함수 ===

def get_current_price(stock_code: str) -> dict:
    """현재가 조회"""
    return get_collector().get_current_price(stock_code)


def get_daily_prices(
    stock_code: str,
    start_date: str = None,
    end_date: str = None,
    limit: int = 100,
) -> list[dict]:
    """일별 시세 조회"""
    return get_collector().get_daily_prices(stock_code, start_date, end_date, limit)


def get_fundamental(stock_code: str, date: str = None) -> dict:
    """기본적 지표 조회"""
    return get_collector().get_fundamental(stock_code, date)


def get_market_cap(stock_code: str, date: str = None) -> dict:
    """시가총액 조회"""
    return get_collector().get_market_cap(stock_code, date)


if __name__ == "__main__":
    # 테스트
    print("=== Price Collector 테스트 ===\n")

    collector = get_collector()

    # 삼성전자 현재가
    price = collector.get_current_price("005930")
    print(f"삼성전자 현재가: {price.get('current_price', 0):,}원 (소스: {price.get('source')})")

    # 삼성전자 최근 5일 시세
    prices = collector.get_daily_prices("005930", limit=5)
    print(f"삼성전자 최근 {len(prices)}일 시세 (소스: {prices[0].get('source') if prices else 'N/A'})")

    # 기본적 지표
    fundamental = collector.get_fundamental("005930")
    print(f"삼성전자 PER: {fundamental.get('per')}, PBR: {fundamental.get('pbr')}")

    print("\n✅ Price Collector 테스트 완료")

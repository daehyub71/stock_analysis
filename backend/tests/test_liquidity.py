"""
유동성 리스크 감점 단위 테스트
- LiquidityRiskCalculator (최대 5점 감점)
"""

import pytest

from app.services.liquidity import LiquidityRiskCalculator


def _make_prices(avg_price, volume, count=20):
    """테스트용 가격 데이터 생성 (일정한 거래량)"""
    return [
        {
            "date": f"2025-01-{i+1:02d}",
            "open_price": avg_price,
            "high_price": avg_price * 1.01,
            "low_price": avg_price * 0.99,
            "close_price": avg_price,
            "volume": volume,
        }
        for i in range(count)
    ]


class TestTradingValuePenalty:
    """거래대금 감점 테스트 (최대 3점)"""

    def test_excellent(self):
        """거래대금 >= 500억 → 감점 0"""
        # 500억 / 20 = 25억/일 → volume * avg_price >= 500억 ÷ 20
        # avg_price=70000, volume=10M → 거래대금 ≈ 700억
        prices = _make_prices(70000, 10_000_000)
        calc = LiquidityRiskCalculator("005930", prices=prices)
        penalty, _ = calc.calc_trading_value_penalty()
        assert penalty == 0.0

    def test_good(self):
        """거래대금 300-500억 → 감점 0.5"""
        # avg_price=50000, volume=800K → 거래대금 ≈ 400억
        prices = _make_prices(50000, 800_000)
        calc = LiquidityRiskCalculator("005930", prices=prices)
        penalty, _ = calc.calc_trading_value_penalty()
        assert penalty == 0.5

    def test_fair(self):
        """거래대금 100-300억 → 감점 1.0"""
        # avg_price=30000, volume=500K → 거래대금 ≈ 150억
        prices = _make_prices(30000, 500_000)
        calc = LiquidityRiskCalculator("005930", prices=prices)
        penalty, _ = calc.calc_trading_value_penalty()
        assert penalty == 1.0

    def test_poor(self):
        """거래대금 50-100억 → 감점 2.0"""
        # avg_price=10000, volume=700K → 거래대금 ≈ 70억
        prices = _make_prices(10000, 700_000)
        calc = LiquidityRiskCalculator("005930", prices=prices)
        penalty, _ = calc.calc_trading_value_penalty()
        assert penalty == 2.0

    def test_very_poor(self):
        """거래대금 < 50억 → 감점 3.0"""
        # avg_price=5000, volume=50K → 거래대금 ≈ 2.5억
        prices = _make_prices(5000, 50_000)
        calc = LiquidityRiskCalculator("005930", prices=prices)
        penalty, _ = calc.calc_trading_value_penalty()
        assert penalty == 3.0

    def test_no_data(self):
        """데이터 없음 → 감점 반환"""
        # 존재하지 않는 종목코드 + 최소 데이터로 has_data=False 유도
        calc = LiquidityRiskCalculator("XXXXXX", prices=[{"date": "2025-01-01", "open_price": 0, "high_price": 0, "low_price": 0, "close_price": 0, "volume": 0}])
        penalty, desc = calc.calc_trading_value_penalty()
        # volume=0 → 거래대금 0 → 매우 저조 → 3.0
        assert penalty == 3.0


class TestVolatilityPenalty:
    """거래량 변동성 감점 테스트 (최대 2점)"""

    def test_very_stable(self):
        """CV < 0.5 → 감점 0"""
        prices = _make_prices(70000, 10_000_000)  # 일정한 거래량
        calc = LiquidityRiskCalculator("005930", prices=prices)
        penalty, _ = calc.calc_volatility_penalty()
        assert penalty == 0.0

    def test_unstable(self):
        """극단적 변동 거래량 → 높은 감점"""
        prices = []
        volumes = [100, 500_000, 100, 500_000, 100, 500_000, 100, 500_000,
                   100, 500_000, 100, 500_000, 100, 500_000, 100, 500_000,
                   100, 500_000, 100, 500_000]
        for i in range(20):
            prices.append({
                "date": f"2025-01-{i+1:02d}",
                "open_price": 5000,
                "high_price": 5100,
                "low_price": 4900,
                "close_price": 5000,
                "volume": volumes[i],
            })
        calc = LiquidityRiskCalculator("005930", prices=prices)
        penalty, _ = calc.calc_volatility_penalty()
        # 극단적 변동 → CV가 매우 높으므로 감점
        assert penalty >= 1.0

    def test_no_data_returns_penalty(self):
        """데이터 부족 시 감점 반환"""
        # 단일 데이터 → std=NaN → volume_cv=None
        calc = LiquidityRiskCalculator("XXXXXX", prices=[
            {"date": "2025-01-01", "open_price": 1000, "high_price": 1100, "low_price": 900, "close_price": 1000, "volume": 100}
        ])
        penalty, _ = calc.calc_volatility_penalty()
        assert isinstance(penalty, float)


class TestLiquidityTotal:
    """유동성 리스크 총 감점 테스트"""

    def test_large_cap_low_risk(self, high_liquidity_prices):
        """대형주 → 낮은 리스크"""
        calc = LiquidityRiskCalculator("005930", prices=high_liquidity_prices)
        result = calc.calculate_total()

        assert result["stock_code"] == "005930"
        assert result["has_data"] is True
        assert result["max_penalty"] == 5.0
        assert result["total_penalty"] <= 1.0
        assert result["risk_grade"] in ("양호", "보통")

    def test_small_cap_high_risk(self, low_liquidity_prices):
        """소형주 → 높은 리스크"""
        calc = LiquidityRiskCalculator("999999", prices=low_liquidity_prices)
        result = calc.calculate_total()

        assert result["total_penalty"] >= 2.0
        assert result["risk_grade"] in ("주의", "위험")

    def test_penalty_capped_at_5(self):
        """총 감점 최대 5점 제한"""
        # 극단적 데이터
        prices = _make_prices(100, 10)  # 매우 작은 거래대금
        calc = LiquidityRiskCalculator("005930", prices=prices)
        result = calc.calculate_total()

        assert result["total_penalty"] <= 5.0

    def test_metrics_included(self, high_liquidity_prices):
        """지표 데이터 포함 확인"""
        calc = LiquidityRiskCalculator("005930", prices=high_liquidity_prices)
        result = calc.calculate_total()

        metrics = result["metrics"]
        assert "avg_trading_value" in metrics
        assert "avg_trading_value_billion" in metrics
        assert "volume_cv" in metrics
        assert metrics["avg_trading_value_billion"] is not None

    def test_details_included(self, high_liquidity_prices):
        """세부 감점 포함 확인"""
        calc = LiquidityRiskCalculator("005930", prices=high_liquidity_prices)
        result = calc.calculate_total()

        details = result["details"]
        assert "trading_value" in details
        assert "volatility" in details
        assert "penalty" in details["trading_value"]
        assert "penalty" in details["volatility"]

"""
Liquidity Risk Service
- 유동성 리스크 기반 감점 계산 (최대 5점 감점)

감점 요소:
- 거래대금 부족: 최대 3점 감점
- 거래량 변동성: 최대 2점 감점

거래대금 기준:
- 일평균 거래대금 10억 미만: 3점 감점
- 일평균 거래대금 10억~30억: 2점 감점
- 일평균 거래대금 30억~50억: 1점 감점
- 일평균 거래대금 50억 이상: 감점 없음

거래량 변동성 기준:
- 거래량 변동계수(CV) 1.5 이상: 2점 감점
- 거래량 변동계수(CV) 1.0~1.5: 1점 감점
- 거래량 변동계수(CV) 1.0 미만: 감점 없음
"""

from typing import Optional

import pandas as pd
import numpy as np

from app.db import sqlite_db


class LiquidityRiskCalculator:
    """유동성 리스크 계산기"""

    # 최대 감점
    MAX_TRADING_VALUE_PENALTY = 3.0   # 거래대금 감점
    MAX_VOLATILITY_PENALTY = 2.0      # 변동성 감점

    MAX_TOTAL_PENALTY = 5.0           # 총 감점

    # 거래대금 기준 (원)
    TRADING_VALUE_EXCELLENT = 50_000_000_000   # 500억
    TRADING_VALUE_GOOD = 30_000_000_000        # 300억
    TRADING_VALUE_FAIR = 10_000_000_000        # 100억
    TRADING_VALUE_POOR = 5_000_000_000         # 50억

    def __init__(
        self,
        stock_code: str,
        prices: Optional[list[dict]] = None,
        period: int = 20,
    ):
        """
        Args:
            stock_code: 종목코드
            prices: 가격 데이터 (없으면 SQLite에서 조회)
            period: 분석 기간 (일)
        """
        self.stock_code = stock_code
        self.period = period
        self._df: Optional[pd.DataFrame] = None

        if prices:
            self._load_from_list(prices)
        else:
            self._load_from_db()

        self._calculate_metrics()

    def _load_from_db(self) -> None:
        """SQLite에서 가격 데이터 로드"""
        prices = sqlite_db.get_prices(self.stock_code, limit=self.period + 10)
        if prices:
            self._load_from_list(prices)

    def _load_from_list(self, prices: list[dict]) -> None:
        """딕셔너리 리스트에서 DataFrame 생성"""
        if not prices:
            return

        df = pd.DataFrame(prices)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date", ascending=True).tail(self.period)

        # 컬럼명 정리
        df = df.rename(columns={
            "close_price": "close",
            "open_price": "open",
            "high_price": "high",
            "low_price": "low",
        })

        self._df = df

    def _calculate_metrics(self) -> None:
        """유동성 지표 계산"""
        if self._df is None or len(self._df) == 0:
            self.avg_trading_value = None
            self.volume_cv = None
            return

        # 거래대금 계산 (trading_value 컬럼이 있으면 사용, 없으면 추정)
        if "trading_value" in self._df.columns:
            self.avg_trading_value = self._df["trading_value"].mean()
        else:
            # 거래대금 = (고가 + 저가) / 2 * 거래량
            avg_price = (self._df["high"] + self._df["low"]) / 2
            trading_value = avg_price * self._df["volume"]
            self.avg_trading_value = trading_value.mean()

        # 거래량 변동계수 (CV = 표준편차 / 평균)
        volume_mean = self._df["volume"].mean()
        volume_std = self._df["volume"].std()

        if volume_mean > 0:
            self.volume_cv = volume_std / volume_mean
        else:
            self.volume_cv = None

    @property
    def has_data(self) -> bool:
        """데이터 존재 여부"""
        return self._df is not None and len(self._df) > 0

    # === 거래대금 감점 (최대 3점) ===

    def calc_trading_value_penalty(self) -> tuple[float, str]:
        """
        거래대금 기반 감점 계산

        거래대금이 낮을수록 유동성 리스크 높음 → 감점

        Returns:
            (감점, 설명)
        """
        if not self.has_data or self.avg_trading_value is None:
            return 1.0, "거래대금 데이터 없음"

        value = self.avg_trading_value
        value_billion = value / 1_000_000_000  # 억 단위 변환

        if value >= self.TRADING_VALUE_EXCELLENT:
            return 0.0, f"거래대금 우수 ({value_billion:.0f}억)"
        elif value >= self.TRADING_VALUE_GOOD:
            return 0.5, f"거래대금 양호 ({value_billion:.0f}억)"
        elif value >= self.TRADING_VALUE_FAIR:
            return 1.0, f"거래대금 보통 ({value_billion:.0f}억)"
        elif value >= self.TRADING_VALUE_POOR:
            return 2.0, f"거래대금 저조 ({value_billion:.0f}억)"
        else:
            return 3.0, f"거래대금 매우 저조 ({value_billion:.1f}억)"

    # === 거래량 변동성 감점 (최대 2점) ===

    def calc_volatility_penalty(self) -> tuple[float, str]:
        """
        거래량 변동성 기반 감점 계산

        변동성이 높으면 불안정 → 감점

        Returns:
            (감점, 설명)
        """
        if not self.has_data or self.volume_cv is None:
            return 0.5, "거래량 데이터 없음"

        cv = self.volume_cv

        if cv >= 1.5:
            return 2.0, f"거래량 불안정 (CV {cv:.2f})"
        elif cv >= 1.0:
            return 1.0, f"거래량 변동 있음 (CV {cv:.2f})"
        elif cv >= 0.5:
            return 0.5, f"거래량 안정적 (CV {cv:.2f})"
        else:
            return 0.0, f"거래량 매우 안정 (CV {cv:.2f})"

    # === 종합 감점 ===

    def calculate_total(self) -> dict:
        """
        유동성 리스크 총 감점 계산 (최대 5점)

        Returns:
            감점 상세 딕셔너리
        """
        trading_penalty, trading_desc = self.calc_trading_value_penalty()
        volatility_penalty, volatility_desc = self.calc_volatility_penalty()

        total_penalty = min(
            trading_penalty + volatility_penalty,
            self.MAX_TOTAL_PENALTY
        )

        # 리스크 등급 판정
        if total_penalty >= 4.0:
            risk_grade = "위험"
        elif total_penalty >= 2.5:
            risk_grade = "주의"
        elif total_penalty >= 1.0:
            risk_grade = "보통"
        else:
            risk_grade = "양호"

        return {
            "stock_code": self.stock_code,
            "has_data": self.has_data,
            "total_penalty": round(total_penalty, 1),
            "max_penalty": self.MAX_TOTAL_PENALTY,
            "risk_grade": risk_grade,
            "metrics": {
                "avg_trading_value": self.avg_trading_value,
                "avg_trading_value_billion": (
                    self.avg_trading_value / 1_000_000_000
                    if self.avg_trading_value else None
                ),
                "volume_cv": self.volume_cv,
                "period_days": self.period,
            },
            "details": {
                "trading_value": {
                    "penalty": trading_penalty,
                    "max": self.MAX_TRADING_VALUE_PENALTY,
                    "description": trading_desc,
                },
                "volatility": {
                    "penalty": volatility_penalty,
                    "max": self.MAX_VOLATILITY_PENALTY,
                    "description": volatility_desc,
                },
            },
        }


# === 편의 함수 ===

def calculate_liquidity_penalty(stock_code: str, period: int = 20) -> dict:
    """종목 유동성 리스크 감점 계산"""
    calculator = LiquidityRiskCalculator(stock_code, period=period)
    return calculator.calculate_total()


def batch_liquidity_penalty(stock_codes: list[str], period: int = 20) -> dict[str, dict]:
    """여러 종목 유동성 리스크 일괄 계산"""
    results = {}
    for code in stock_codes:
        results[code] = calculate_liquidity_penalty(code, period)
    return results


if __name__ == "__main__":
    print("=== Liquidity Risk Calculator 테스트 ===\n")

    # 테스트용 더미 데이터
    test_prices = []
    import random
    base_volume = 1_000_000
    base_price = 70000

    for i in range(20):
        price = base_price * (1 + random.uniform(-0.02, 0.02))
        volume = int(base_volume * (1 + random.uniform(-0.3, 0.5)))
        test_prices.append({
            "date": f"2024-01-{i+1:02d}",
            "open_price": price,
            "high_price": price * 1.01,
            "low_price": price * 0.99,
            "close_price": price,
            "volume": volume,
        })

    calculator = LiquidityRiskCalculator("005930", prices=test_prices)
    result = calculator.calculate_total()

    print(f"종목: {result['stock_code']}")
    print(f"유동성 리스크 등급: {result['risk_grade']}")
    print(f"총 감점: -{result['total_penalty']} / {result['max_penalty']}")
    print()

    print("=== 지표 ===")
    metrics = result["metrics"]
    if metrics["avg_trading_value_billion"]:
        print(f"평균 거래대금: {metrics['avg_trading_value_billion']:.1f}억원")
    if metrics["volume_cv"]:
        print(f"거래량 변동계수: {metrics['volume_cv']:.2f}")
    print()

    print("=== 세부 감점 ===")
    for name, detail in result["details"].items():
        print(f"{name}: -{detail['penalty']} / {detail['max']} ({detail['description']})")

    print("\n✅ 테스트 완료")

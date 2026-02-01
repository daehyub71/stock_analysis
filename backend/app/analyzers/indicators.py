"""
Technical Indicators Calculator
- 이동평균 (MA5, MA20, MA60, MA120)
- RSI (14)
- MACD (12, 26, 9)
- 거래량 비율
"""

from datetime import datetime
from typing import Optional

import pandas as pd
import numpy as np

from app.db import sqlite_db


class TechnicalIndicators:
    """기술지표 계산기"""

    def __init__(self, stock_code: str, prices: Optional[list[dict]] = None):
        """
        Args:
            stock_code: 종목코드
            prices: 가격 데이터 (없으면 SQLite에서 조회)
        """
        self.stock_code = stock_code
        self._df: Optional[pd.DataFrame] = None

        if prices:
            self._load_from_list(prices)
        else:
            self._load_from_db()

    def _load_from_db(self, limit: int = 200) -> None:
        """SQLite에서 가격 데이터 로드"""
        prices = sqlite_db.get_prices(self.stock_code, limit=limit)
        if prices:
            self._load_from_list(prices)

    def _load_from_list(self, prices: list[dict]) -> None:
        """딕셔너리 리스트에서 DataFrame 생성"""
        if not prices:
            return

        df = pd.DataFrame(prices)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date", ascending=True)
        df = df.set_index("date")

        # 컬럼명 정리
        df = df.rename(columns={
            "close_price": "close",
            "open_price": "open",
            "high_price": "high",
            "low_price": "low",
        })

        self._df = df

    @property
    def df(self) -> Optional[pd.DataFrame]:
        """가격 DataFrame"""
        return self._df

    @property
    def has_data(self) -> bool:
        """데이터 존재 여부"""
        return self._df is not None and len(self._df) > 0

    # === 이동평균 (Moving Average) ===

    def calc_ma(self, period: int) -> pd.Series:
        """단순 이동평균 계산"""
        if not self.has_data:
            return pd.Series(dtype=float)
        return self._df["close"].rolling(window=period).mean()

    def calc_ema(self, period: int) -> pd.Series:
        """지수 이동평균 계산"""
        if not self.has_data:
            return pd.Series(dtype=float)
        return self._df["close"].ewm(span=period, adjust=False).mean()

    def get_ma_values(self) -> dict:
        """주요 이동평균 값 반환"""
        if not self.has_data:
            return {}

        ma5 = self.calc_ma(5)
        ma20 = self.calc_ma(20)
        ma60 = self.calc_ma(60)
        ma120 = self.calc_ma(120)

        return {
            "ma5": float(ma5.iloc[-1]) if len(ma5) >= 5 and not pd.isna(ma5.iloc[-1]) else None,
            "ma20": float(ma20.iloc[-1]) if len(ma20) >= 20 and not pd.isna(ma20.iloc[-1]) else None,
            "ma60": float(ma60.iloc[-1]) if len(ma60) >= 60 and not pd.isna(ma60.iloc[-1]) else None,
            "ma120": float(ma120.iloc[-1]) if len(ma120) >= 120 and not pd.isna(ma120.iloc[-1]) else None,
            "current_price": float(self._df["close"].iloc[-1]),
        }

    # === RSI (Relative Strength Index) ===

    def calc_rsi(self, period: int = 14) -> pd.Series:
        """RSI 계산"""
        if not self.has_data or len(self._df) < period + 1:
            return pd.Series(dtype=float)

        delta = self._df["close"].diff()

        gain = delta.where(delta > 0, 0)
        loss = (-delta).where(delta < 0, 0)

        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def get_rsi_value(self, period: int = 14) -> Optional[float]:
        """현재 RSI 값 반환"""
        rsi = self.calc_rsi(period)
        if len(rsi) > 0 and not pd.isna(rsi.iloc[-1]):
            return float(rsi.iloc[-1])
        return None

    # === MACD (Moving Average Convergence Divergence) ===

    def calc_macd(
        self,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> dict[str, pd.Series]:
        """MACD 계산"""
        if not self.has_data or len(self._df) < slow + signal:
            return {"macd": pd.Series(dtype=float), "signal": pd.Series(dtype=float), "hist": pd.Series(dtype=float)}

        ema_fast = self.calc_ema(fast)
        ema_slow = self.calc_ema(slow)

        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line

        return {
            "macd": macd_line,
            "signal": signal_line,
            "hist": histogram,
        }

    def get_macd_values(self) -> dict:
        """현재 MACD 값 반환"""
        macd_data = self.calc_macd()

        result = {}
        for key, series in macd_data.items():
            if len(series) > 0 and not pd.isna(series.iloc[-1]):
                result[key] = float(series.iloc[-1])
            else:
                result[key] = None

        return result

    # === 거래량 분석 ===

    def calc_volume_ratio(self, period: int = 20) -> Optional[float]:
        """거래량 비율 (현재 / 평균)"""
        if not self.has_data or len(self._df) < period:
            return None

        avg_volume = self._df["volume"].rolling(window=period).mean()
        current_volume = self._df["volume"].iloc[-1]

        if avg_volume.iloc[-1] > 0:
            return float(current_volume / avg_volume.iloc[-1])
        return None

    def calc_avg_trading_value(self, period: int = 20) -> Optional[float]:
        """평균 거래대금 (원)"""
        if not self.has_data or len(self._df) < period:
            return None

        if "trading_value" in self._df.columns:
            return float(self._df["trading_value"].tail(period).mean())

        # 거래대금 컬럼이 없으면 근사 계산
        avg_price = (self._df["high"] + self._df["low"]) / 2
        trading_value = avg_price * self._df["volume"]
        return float(trading_value.tail(period).mean())

    # === 종합 지표 ===

    def calculate_all(self) -> dict:
        """모든 기술지표 계산"""
        if not self.has_data:
            return {
                "stock_code": self.stock_code,
                "has_data": False,
                "error": "No price data available",
            }

        ma_values = self.get_ma_values()
        macd_values = self.get_macd_values()

        result = {
            "stock_code": self.stock_code,
            "has_data": True,
            "date": self._df.index[-1].strftime("%Y-%m-%d"),
            "current_price": ma_values.get("current_price"),
            # 이동평균
            "ma5": ma_values.get("ma5"),
            "ma20": ma_values.get("ma20"),
            "ma60": ma_values.get("ma60"),
            "ma120": ma_values.get("ma120"),
            # RSI
            "rsi14": self.get_rsi_value(14),
            # MACD
            "macd": macd_values.get("macd"),
            "macd_signal": macd_values.get("signal"),
            "macd_hist": macd_values.get("hist"),
            # 거래량
            "volume_ratio": self.calc_volume_ratio(20),
            "avg_trading_value": self.calc_avg_trading_value(20),
        }

        return result

    def save_to_db(self) -> bool:
        """기술지표를 SQLite에 저장"""
        indicators = self.calculate_all()

        if not indicators.get("has_data"):
            return False

        return sqlite_db.insert_indicators(
            stock_code=self.stock_code,
            date=indicators["date"],
            indicators={
                "ma5": indicators.get("ma5"),
                "ma20": indicators.get("ma20"),
                "ma60": indicators.get("ma60"),
                "ma120": indicators.get("ma120"),
                "rsi14": indicators.get("rsi14"),
                "macd": indicators.get("macd"),
                "macd_signal": indicators.get("macd_signal"),
                "macd_hist": indicators.get("macd_hist"),
                "volume_ratio": indicators.get("volume_ratio"),
            }
        )


# === 편의 함수 ===

def calculate_indicators(stock_code: str) -> dict:
    """종목 기술지표 계산"""
    calc = TechnicalIndicators(stock_code)
    return calc.calculate_all()


def calculate_and_save(stock_code: str) -> dict:
    """종목 기술지표 계산 및 저장"""
    calc = TechnicalIndicators(stock_code)
    indicators = calc.calculate_all()
    calc.save_to_db()
    return indicators


def batch_calculate(stock_codes: list[str], save: bool = True) -> dict[str, dict]:
    """여러 종목 기술지표 일괄 계산"""
    results = {}
    for code in stock_codes:
        calc = TechnicalIndicators(code)
        indicators = calc.calculate_all()
        if save and indicators.get("has_data"):
            calc.save_to_db()
        results[code] = indicators
    return results


if __name__ == "__main__":
    print("=== Technical Indicators 테스트 ===\n")

    # 삼성전자 지표 계산
    indicators = calculate_indicators("005930")

    if indicators.get("has_data"):
        print(f"종목: {indicators['stock_code']}")
        print(f"날짜: {indicators['date']}")
        print(f"현재가: {indicators['current_price']:,.0f}원")
        print()
        print("=== 이동평균 ===")
        print(f"MA5:  {indicators['ma5']:,.0f}" if indicators['ma5'] else "MA5: N/A")
        print(f"MA20: {indicators['ma20']:,.0f}" if indicators['ma20'] else "MA20: N/A")
        print(f"MA60: {indicators['ma60']:,.0f}" if indicators['ma60'] else "MA60: N/A")
        print(f"MA120: {indicators['ma120']:,.0f}" if indicators['ma120'] else "MA120: N/A")
        print()
        print("=== RSI ===")
        print(f"RSI(14): {indicators['rsi14']:.2f}" if indicators['rsi14'] else "RSI: N/A")
        print()
        print("=== MACD ===")
        print(f"MACD: {indicators['macd']:.2f}" if indicators['macd'] else "MACD: N/A")
        print(f"Signal: {indicators['macd_signal']:.2f}" if indicators['macd_signal'] else "Signal: N/A")
        print(f"Histogram: {indicators['macd_hist']:.2f}" if indicators['macd_hist'] else "Hist: N/A")
        print()
        print("=== 거래량 ===")
        print(f"거래량비율: {indicators['volume_ratio']:.2f}" if indicators['volume_ratio'] else "거래량비율: N/A")
    else:
        print(f"❌ 데이터 없음: {indicators.get('error')}")

    print("\n✅ 테스트 완료")

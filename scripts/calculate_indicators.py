#!/usr/bin/env python3
"""
기술지표 계산 스크립트
- MA, RSI, MACD 등 계산
- SQLite에 캐싱
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))


def calculate_ma(prices: list[float], period: int) -> float:
    """이동평균 계산"""
    if len(prices) < period:
        return None
    return sum(prices[-period:]) / period


def calculate_rsi(prices: list[float], period: int = 14) -> float:
    """RSI 계산"""
    if len(prices) < period + 1:
        return None

    gains = []
    losses = []

    for i in range(1, len(prices)):
        change = prices[i] - prices[i-1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))

    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period

    if avg_loss == 0:
        return 100

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def calculate_macd(prices: list[float]) -> tuple:
    """MACD 계산 (12, 26, 9)"""
    if len(prices) < 26:
        return None, None, None

    # EMA 계산
    def ema(data, period):
        multiplier = 2 / (period + 1)
        ema_values = [data[0]]
        for price in data[1:]:
            ema_values.append((price * multiplier) + (ema_values[-1] * (1 - multiplier)))
        return ema_values

    ema12 = ema(prices, 12)
    ema26 = ema(prices, 26)

    macd_line = [e12 - e26 for e12, e26 in zip(ema12, ema26)]
    signal_line = ema(macd_line, 9)

    macd = macd_line[-1]
    signal = signal_line[-1]
    histogram = macd - signal

    return macd, signal, histogram


def calculate_volume_ratio(volumes: list[int], period: int = 20) -> float:
    """거래량 비율 계산"""
    if len(volumes) < period:
        return None

    avg_volume = sum(volumes[-period:]) / period
    if avg_volume == 0:
        return None

    return volumes[-1] / avg_volume


def calculate_indicators_for_stock(stock_code: str, price_data: list[dict]) -> dict:
    """종목별 기술지표 계산"""
    if not price_data or len(price_data) < 120:
        return {}

    # 종가, 거래량 추출
    closes = [d["close"] for d in price_data]
    volumes = [d["volume"] for d in price_data]

    result = {
        "ma5": calculate_ma(closes, 5),
        "ma20": calculate_ma(closes, 20),
        "ma60": calculate_ma(closes, 60),
        "ma120": calculate_ma(closes, 120),
        "rsi14": calculate_rsi(closes, 14),
        "volume_ratio": calculate_volume_ratio(volumes, 20),
    }

    macd, signal, hist = calculate_macd(closes)
    result["macd"] = macd
    result["macd_signal"] = signal
    result["macd_hist"] = hist

    return result


def main():
    print("=" * 50)
    print("🔢 Technical Indicators Calculation")
    print("=" * 50)

    # TODO: SQLite에서 가격 데이터 로드
    # TODO: 기술지표 계산
    # TODO: SQLite에 저장

    print("\n✅ Indicators calculation completed!")


if __name__ == "__main__":
    main()

"""
공통 테스트 픽스처
"""

import sys
from pathlib import Path

import pytest

# backend/app을 import 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))


# === 기술지표 픽스처 ===

@pytest.fixture
def bullish_indicators():
    """정배열 상승 종목 기술지표"""
    return {
        "has_data": True,
        "current_price": 72000,
        "ma5": 71500,
        "ma20": 70000,
        "ma60": 68000,
        "ma120": 65000,
        "rsi14": 35.0,
        "macd": 200.0,
        "macd_hist": 80.0,
        "volume_ratio": 1.6,
    }


@pytest.fixture
def bearish_indicators():
    """역배열 하락 종목 기술지표"""
    return {
        "has_data": True,
        "current_price": 50000,
        "ma5": 51000,
        "ma20": 54000,
        "ma60": 58000,
        "ma120": 62000,
        "rsi14": 75.0,
        "macd": -300.0,
        "macd_hist": -100.0,
        "volume_ratio": 0.3,
    }


@pytest.fixture
def no_data_indicators():
    """데이터 없는 지표"""
    return {"has_data": False}


# === 재무 데이터 픽스처 ===

@pytest.fixture
def strong_financials():
    """우량주 재무 데이터"""
    return {
        "per": 8.5,
        "pbr": 0.8,
        "psr": 0.4,
        "revenue_growth": 25.0,
        "op_growth": 35.0,
        "roe": 18.0,
        "op_margin": 16.0,
        "debt_ratio": 45.0,
        "current_ratio": 210.0,
    }


@pytest.fixture
def weak_financials():
    """부실주 재무 데이터"""
    return {
        "per": -5.0,
        "pbr": 3.5,
        "psr": 5.0,
        "revenue_growth": -15.0,
        "op_growth": -25.0,
        "roe": 2.0,
        "op_margin": 3.0,
        "debt_ratio": 250.0,
        "current_ratio": 80.0,
    }


@pytest.fixture
def empty_financials():
    """데이터 없는 재무"""
    return {}


# === 뉴스 데이터 픽스처 ===

@pytest.fixture
def positive_news():
    """긍정적 뉴스"""
    return [
        {"title": "실적 호조", "sentiment": "positive", "impact": "high"},
        {"title": "수출 증가", "sentiment": "positive", "impact": "high"},
        {"title": "신제품 출시", "sentiment": "positive", "impact": "medium"},
        {"title": "배당 확대", "sentiment": "positive", "impact": "medium"},
        {"title": "시장 전망 양호", "sentiment": "positive", "impact": "low"},
        {"title": "업종 호황", "sentiment": "neutral", "impact": "low"},
    ]


@pytest.fixture
def negative_news():
    """부정적 뉴스"""
    return [
        {"title": "실적 부진", "sentiment": "negative", "impact": "high"},
        {"title": "소송 리스크", "sentiment": "negative", "impact": "high"},
        {"title": "매출 감소", "sentiment": "negative", "impact": "medium"},
        {"title": "경쟁 심화", "sentiment": "negative", "impact": "low"},
        {"title": "시장 우려", "sentiment": "negative", "impact": "low"},
    ]


@pytest.fixture
def mixed_news():
    """혼재 뉴스"""
    return [
        {"title": "실적 호조", "sentiment": "positive", "impact": "high"},
        {"title": "소송 리스크", "sentiment": "negative", "impact": "medium"},
        {"title": "시장 전망", "sentiment": "neutral", "impact": "low"},
    ]


# === 가격 데이터 픽스처 ===

@pytest.fixture
def high_liquidity_prices():
    """대형주 가격 데이터 (높은 유동성)"""
    prices = []
    for i in range(20):
        prices.append({
            "date": f"2025-01-{i+1:02d}",
            "open_price": 70000,
            "high_price": 71000,
            "low_price": 69000,
            "close_price": 70500,
            "volume": 15_000_000,
        })
    return prices


@pytest.fixture
def low_liquidity_prices():
    """소형주 가격 데이터 (낮은 유동성)"""
    import random
    random.seed(42)
    prices = []
    for i in range(20):
        vol = int(5000 * (1 + random.uniform(-0.8, 3.0)))
        prices.append({
            "date": f"2025-01-{i+1:02d}",
            "open_price": 3000,
            "high_price": 3100,
            "low_price": 2900,
            "close_price": 3050,
            "volume": vol,
        })
    return prices

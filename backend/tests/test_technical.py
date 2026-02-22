"""
기술분석 점수 계산 단위 테스트
- TechnicalAnalyzer (30점 만점)
"""

import pytest

from app.services.technical import TechnicalAnalyzer


class TestMAArrangement:
    """MA 배열 점수 테스트 (6점 만점)"""

    def test_perfect_bullish(self, bullish_indicators):
        """완전 정배열 → 6점"""
        analyzer = TechnicalAnalyzer("005930", bullish_indicators)
        score, desc = analyzer.calc_ma_arrangement()
        assert score == 6.0
        assert "정배열" in desc

    def test_perfect_bearish(self, bearish_indicators):
        """완전 역배열 → 0점"""
        analyzer = TechnicalAnalyzer("005930", bearish_indicators)
        score, desc = analyzer.calc_ma_arrangement()
        assert score == 0.0
        assert "역배열" in desc

    def test_mixed_arrangement(self):
        """혼조세 → 중간 점수"""
        indicators = {
            "has_data": True,
            "current_price": 70000,
            "ma5": 71000,       # price < ma5 (역)
            "ma20": 69000,      # ma5 > ma20 (정)
            "ma60": 68000,      # ma20 > ma60 (정)
            "ma120": 72000,     # ma60 < ma120 (역)
        }
        analyzer = TechnicalAnalyzer("005930", indicators)
        score, _ = analyzer.calc_ma_arrangement()
        assert 0 < score < 6.0

    def test_no_data(self, no_data_indicators):
        """데이터 없음 → 중립 3점"""
        analyzer = TechnicalAnalyzer("005930", no_data_indicators)
        score, desc = analyzer.calc_ma_arrangement()
        assert score == 3.0
        assert "데이터 없음" in desc

    def test_partial_ma_data(self):
        """MA60, MA120 없이 3개만 → 정상 계산"""
        indicators = {
            "has_data": True,
            "current_price": 70000,
            "ma5": 69000,
            "ma20": 68000,
            "ma60": None,
            "ma120": None,
        }
        analyzer = TechnicalAnalyzer("005930", indicators)
        score, _ = analyzer.calc_ma_arrangement()
        assert score == 6.0  # 3개 완전 정배열


class TestMADivergence:
    """MA 이격도 점수 테스트 (6점 만점)"""

    def test_overheated(self):
        """이격 +10% 이상 → 2점 (과열)"""
        indicators = {
            "has_data": True,
            "current_price": 77000,
            "ma20": 70000,
        }
        analyzer = TechnicalAnalyzer("005930", indicators)
        score, desc = analyzer.calc_ma_divergence()
        assert score == 2.0
        assert "과열" in desc

    def test_rising(self):
        """이격 +5~10% → 5점 (상승세)"""
        indicators = {
            "has_data": True,
            "current_price": 73500,
            "ma20": 70000,
        }
        analyzer = TechnicalAnalyzer("005930", indicators)
        score, _ = analyzer.calc_ma_divergence()
        assert score == 5.0

    def test_proper_rise(self):
        """이격 0~5% → 6점 (적정 상승)"""
        indicators = {
            "has_data": True,
            "current_price": 72000,
            "ma20": 70000,
        }
        analyzer = TechnicalAnalyzer("005930", indicators)
        score, _ = analyzer.calc_ma_divergence()
        assert score == 6.0

    def test_proper_fall(self):
        """이격 -5~0% → 4점 (적정 하락)"""
        indicators = {
            "has_data": True,
            "current_price": 68000,
            "ma20": 70000,
        }
        analyzer = TechnicalAnalyzer("005930", indicators)
        score, _ = analyzer.calc_ma_divergence()
        assert score == 4.0

    def test_falling(self):
        """이격 -10~-5% → 2점 (하락세)"""
        indicators = {
            "has_data": True,
            "current_price": 63500,
            "ma20": 70000,
        }
        analyzer = TechnicalAnalyzer("005930", indicators)
        score, _ = analyzer.calc_ma_divergence()
        assert score == 2.0

    def test_oversold(self):
        """이격 -10% 이하 → 3점 (과매도, 반등 기대)"""
        indicators = {
            "has_data": True,
            "current_price": 60000,
            "ma20": 70000,
        }
        analyzer = TechnicalAnalyzer("005930", indicators)
        score, desc = analyzer.calc_ma_divergence()
        assert score == 3.0
        assert "과매도" in desc


class TestRSIScore:
    """RSI 점수 테스트 (5점 만점)"""

    def test_oversold(self):
        """RSI < 30 → 4점"""
        indicators = {"has_data": True, "rsi14": 25.0}
        analyzer = TechnicalAnalyzer("005930", indicators)
        score, _ = analyzer.calc_rsi_score()
        assert score == 4.0

    def test_undervalued(self):
        """RSI 30-40 → 5점 (최고점)"""
        indicators = {"has_data": True, "rsi14": 35.0}
        analyzer = TechnicalAnalyzer("005930", indicators)
        score, _ = analyzer.calc_rsi_score()
        assert score == 5.0

    def test_neutral(self):
        """RSI 40-60 → 3점"""
        indicators = {"has_data": True, "rsi14": 50.0}
        analyzer = TechnicalAnalyzer("005930", indicators)
        score, _ = analyzer.calc_rsi_score()
        assert score == 3.0

    def test_overvalued(self):
        """RSI 60-70 → 2점"""
        indicators = {"has_data": True, "rsi14": 65.0}
        analyzer = TechnicalAnalyzer("005930", indicators)
        score, _ = analyzer.calc_rsi_score()
        assert score == 2.0

    def test_overbought(self):
        """RSI >= 70 → 1점"""
        indicators = {"has_data": True, "rsi14": 80.0}
        analyzer = TechnicalAnalyzer("005930", indicators)
        score, _ = analyzer.calc_rsi_score()
        assert score == 1.0

    def test_no_rsi(self):
        """RSI 없음 → 2.5점"""
        indicators = {"has_data": True, "rsi14": None}
        analyzer = TechnicalAnalyzer("005930", indicators)
        score, _ = analyzer.calc_rsi_score()
        assert score == 2.5


class TestMACDScore:
    """MACD 점수 테스트 (5점 만점)"""

    def test_strong_bullish(self):
        """MACD > 0 & Hist > 0 → 5점"""
        indicators = {"has_data": True, "macd": 100, "macd_hist": 50}
        analyzer = TechnicalAnalyzer("005930", indicators)
        score, _ = analyzer.calc_macd_score()
        assert score == 5.0

    def test_weakening_bullish(self):
        """MACD > 0 & Hist <= 0 → 3점"""
        indicators = {"has_data": True, "macd": 100, "macd_hist": -20}
        analyzer = TechnicalAnalyzer("005930", indicators)
        score, _ = analyzer.calc_macd_score()
        assert score == 3.0

    def test_reversal_signal(self):
        """MACD <= 0 & Hist > 0 → 4점 (반등)"""
        indicators = {"has_data": True, "macd": -50, "macd_hist": 30}
        analyzer = TechnicalAnalyzer("005930", indicators)
        score, _ = analyzer.calc_macd_score()
        assert score == 4.0

    def test_strong_bearish(self):
        """MACD <= 0 & Hist <= 0 → 1점"""
        indicators = {"has_data": True, "macd": -200, "macd_hist": -80}
        analyzer = TechnicalAnalyzer("005930", indicators)
        score, _ = analyzer.calc_macd_score()
        assert score == 1.0


class TestVolumeScore:
    """거래량 점수 테스트 (8점 만점)"""

    def test_surge(self):
        """비율 >= 2.0 → 6점 (급증, 관심 필요)"""
        indicators = {"has_data": True, "volume_ratio": 2.5}
        analyzer = TechnicalAnalyzer("005930", indicators)
        score, _ = analyzer.calc_volume_score()
        assert score == 6.0

    def test_active(self):
        """비율 1.5-2.0 → 8점 (최적)"""
        indicators = {"has_data": True, "volume_ratio": 1.7}
        analyzer = TechnicalAnalyzer("005930", indicators)
        score, _ = analyzer.calc_volume_score()
        assert score == 8.0

    def test_normal(self):
        """비율 1.0-1.5 → 6점"""
        indicators = {"has_data": True, "volume_ratio": 1.2}
        analyzer = TechnicalAnalyzer("005930", indicators)
        score, _ = analyzer.calc_volume_score()
        assert score == 6.0

    def test_low(self):
        """비율 0.5-1.0 → 4점"""
        indicators = {"has_data": True, "volume_ratio": 0.7}
        analyzer = TechnicalAnalyzer("005930", indicators)
        score, _ = analyzer.calc_volume_score()
        assert score == 4.0

    def test_very_low(self):
        """비율 < 0.5 → 2점"""
        indicators = {"has_data": True, "volume_ratio": 0.2}
        analyzer = TechnicalAnalyzer("005930", indicators)
        score, _ = analyzer.calc_volume_score()
        assert score == 2.0


class TestTechnicalTotal:
    """기술분석 총점 테스트"""

    def test_bullish_total(self, bullish_indicators):
        """상승 종목 총점 계산"""
        analyzer = TechnicalAnalyzer("005930", bullish_indicators)
        result = analyzer.calculate_total()

        assert result["stock_code"] == "005930"
        assert result["has_data"] is True
        assert result["max_score"] == 30.0
        assert 0 <= result["total_score"] <= 30.0

        # 세부 항목 존재 확인
        details = result["details"]
        assert "ma_arrangement" in details
        assert "ma_divergence" in details
        assert "rsi" in details
        assert "macd" in details
        assert "volume" in details

    def test_score_sum_matches_total(self, bullish_indicators):
        """세부 점수 합 == 총점"""
        analyzer = TechnicalAnalyzer("005930", bullish_indicators)
        result = analyzer.calculate_total()

        detail_sum = sum(d["score"] for d in result["details"].values())
        assert abs(detail_sum - result["total_score"]) < 0.01

    def test_no_data_gives_neutral(self, no_data_indicators):
        """데이터 없으면 중립 점수"""
        analyzer = TechnicalAnalyzer("005930", no_data_indicators)
        result = analyzer.calculate_total()
        # 중립: 3.0 + 3.0 + 2.5 + 2.5 + 4.0 = 15.0
        assert result["total_score"] == 15.0

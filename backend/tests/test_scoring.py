"""
종합 점수 계산 단위 테스트
- StockScorer (100점 만점)
- 등급 판정 (A+~F)
"""

import pytest
from unittest.mock import patch

from app.services.scoring import StockScorer


@pytest.fixture
def full_data():
    """종합 점수 테스트용 전체 데이터"""
    indicators = {
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
    financials = {
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
    news = [
        {"title": "실적 호조", "sentiment": "positive", "impact": "high"},
        {"title": "수출 증가", "sentiment": "positive", "impact": "high"},
        {"title": "신제품 발표", "sentiment": "positive", "impact": "medium"},
        {"title": "경기 불확실", "sentiment": "negative", "impact": "low"},
        {"title": "환율 안정", "sentiment": "positive", "impact": "medium"},
    ]
    return indicators, financials, news


class TestGrade:
    """등급 판정 테스트"""

    @pytest.mark.parametrize("score, expected_grade", [
        (95.0, "A+"),
        (90.0, "A+"),
        (85.0, "A"),
        (80.0, "A"),
        (75.0, "B+"),
        (70.0, "B+"),
        (65.0, "B"),
        (60.0, "B"),
        (55.0, "C+"),
        (50.0, "C+"),
        (45.0, "C"),
        (40.0, "C"),
        (35.0, "D"),
        (30.0, "D"),
        (25.0, "F"),
        (10.0, "F"),
    ])
    @patch("app.services.scoring.get_manual_sentiment_score", return_value=None)
    def test_grade_thresholds(self, mock_manual, score, expected_grade):
        """점수별 등급 매핑"""
        scorer = StockScorer(
            "005930", "삼성전자",
            indicators={"has_data": False},
            financials={},
            news_items=[],
        )
        grade = scorer._get_grade(score)
        assert grade == expected_grade


class TestStockScorer:
    """종합 점수 계산 테스트"""

    @patch("app.services.scoring.get_manual_sentiment_score", return_value=None)
    def test_total_score_structure(self, mock_manual, full_data):
        """결과 구조 확인"""
        indicators, financials, news = full_data
        scorer = StockScorer("005930", "삼성전자", indicators, financials, news)
        result = scorer.calculate_total()

        assert "stock_code" in result
        assert "stock_name" in result
        assert "analysis_date" in result
        assert "total_score" in result
        assert "max_score" in result
        assert "grade" in result
        assert "score_breakdown" in result
        assert "details" in result

    @patch("app.services.scoring.get_manual_sentiment_score", return_value=None)
    def test_max_score_100(self, mock_manual, full_data):
        """총점 최대 100점"""
        indicators, financials, news = full_data
        scorer = StockScorer("005930", "삼성전자", indicators, financials, news)
        result = scorer.calculate_total()

        assert result["max_score"] == 100.0
        assert 0 <= result["total_score"] <= 100.0

    @patch("app.services.scoring.get_manual_sentiment_score", return_value=None)
    def test_breakdown_three_areas(self, mock_manual, full_data):
        """3개 영역 점수 포함"""
        indicators, financials, news = full_data
        scorer = StockScorer("005930", "삼성전자", indicators, financials, news)
        result = scorer.calculate_total()

        breakdown = result["score_breakdown"]
        assert "technical" in breakdown
        assert "fundamental" in breakdown
        assert "sentiment" in breakdown

        assert breakdown["technical"]["max"] == 30.0
        assert breakdown["fundamental"]["max"] == 50.0
        assert breakdown["sentiment"]["max"] == 20.0

    @patch("app.services.scoring.get_manual_sentiment_score", return_value=None)
    def test_score_sum_equals_total(self, mock_manual, full_data):
        """영역별 점수 합 == 총점"""
        indicators, financials, news = full_data
        scorer = StockScorer("005930", "삼성전자", indicators, financials, news)
        result = scorer.calculate_total()

        breakdown = result["score_breakdown"]
        area_sum = (
            breakdown["technical"]["score"]
            + breakdown["fundamental"]["score"]
            + breakdown["sentiment"]["score"]
        )
        assert abs(area_sum - result["total_score"]) < 0.1

    @patch("app.services.scoring.get_manual_sentiment_score", return_value=None)
    def test_strong_stock_high_score(self, mock_manual, full_data):
        """우량 데이터 → 높은 점수"""
        indicators, financials, news = full_data
        scorer = StockScorer("005930", "삼성전자", indicators, financials, news)
        result = scorer.calculate_total()

        assert result["total_score"] > 60.0
        assert result["grade"] in ("A+", "A", "B+", "B")

    @patch("app.services.scoring.get_manual_sentiment_score", return_value=None)
    def test_weak_stock_low_score(self, mock_manual):
        """부실 데이터 → 낮은 점수"""
        indicators = {
            "has_data": True,
            "current_price": 50000,
            "ma5": 51000,
            "ma20": 54000,
            "ma60": 58000,
            "ma120": 62000,
            "rsi14": 80.0,
            "macd": -300.0,
            "macd_hist": -100.0,
            "volume_ratio": 0.2,
        }
        financials = {
            "per": -5.0,
            "pbr": 4.0,
            "psr": 6.0,
            "revenue_growth": -20.0,
            "op_growth": -30.0,
            "roe": 1.0,
            "op_margin": 2.0,
            "debt_ratio": 300.0,
            "current_ratio": 60.0,
        }
        news = [
            {"title": "실적 부진", "sentiment": "negative", "impact": "high"},
            {"title": "소송 위험", "sentiment": "negative", "impact": "high"},
            {"title": "매출 급감", "sentiment": "negative", "impact": "medium"},
        ]

        scorer = StockScorer("005930", "삼성전자", indicators, financials, news)
        result = scorer.calculate_total()

        assert result["total_score"] < 30.0
        assert result["grade"] in ("D", "F")

    @patch("app.services.scoring.get_manual_sentiment_score", return_value=None)
    def test_no_data_neutral(self, mock_manual):
        """데이터 없으면 중립 점수"""
        scorer = StockScorer(
            "005930", "삼성전자",
            indicators={"has_data": False},
            financials={},
            news_items=[],
        )
        result = scorer.calculate_total()

        # 대략 중간 점수 (각 중립값 합)
        assert 40.0 <= result["total_score"] <= 55.0

    @patch("app.services.scoring.get_manual_sentiment_score")
    def test_manual_sentiment_used(self, mock_manual, full_data):
        """수동 평점이 있으면 자동 분석 대신 사용"""
        mock_manual.return_value = {
            "total_score": 15.0,
            "max_score": 20.0,
            "has_data": True,
            "is_manual": True,
            "avg_rating": 5.0,
            "rated_count": 10,
            "details": {
                "sentiment": {"score": 15.0, "max": 20.0, "description": "수동"},
                "impact": {"score": 0, "max": 0, "description": "수동 포함"},
                "volume": {"score": 0, "max": 0, "description": "수동 포함"},
            },
            "news_summary": {"total": 10, "rated_count": 10, "avg_rating": 5.0},
        }

        indicators, financials, news = full_data
        scorer = StockScorer("005930", "삼성전자", indicators, financials, news)
        result = scorer.calculate_total()

        assert result["sentiment_source"] == "manual"
        assert result["score_breakdown"]["sentiment"]["source"] == "manual"
        assert result["score_breakdown"]["sentiment"]["score"] == 15.0

    @patch("app.services.scoring.get_manual_sentiment_score", return_value=None)
    def test_auto_sentiment_used(self, mock_manual, full_data):
        """수동 평점 없으면 자동 분석 사용"""
        indicators, financials, news = full_data
        scorer = StockScorer("005930", "삼성전자", indicators, financials, news)
        result = scorer.calculate_total()

        assert result["sentiment_source"] == "auto"

    @patch("app.services.scoring.get_manual_sentiment_score", return_value=None)
    def test_details_contain_all_analyzers(self, mock_manual, full_data):
        """상세 결과에 3개 분석기 결과 포함"""
        indicators, financials, news = full_data
        scorer = StockScorer("005930", "삼성전자", indicators, financials, news)
        result = scorer.calculate_total()

        details = result["details"]
        assert "technical" in details
        assert "fundamental" in details
        assert "sentiment" in details

        # 각 분석기 결과에 total_score 존재
        assert "total_score" in details["technical"]
        assert "total_score" in details["fundamental"]
        assert "total_score" in details["sentiment"]

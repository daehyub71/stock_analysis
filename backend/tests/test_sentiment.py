"""
감정분석 점수 계산 단위 테스트
- SentimentAnalyzer (20점 만점)
"""

import pytest

from app.services.sentiment import SentimentAnalyzer


class TestSentimentScore:
    """뉴스 감정 점수 테스트 (10점 만점)"""

    def test_very_positive(self):
        """긍정 >= 80% → 10점"""
        news = [
            {"sentiment": "positive", "impact": "low"},
            {"sentiment": "positive", "impact": "low"},
            {"sentiment": "positive", "impact": "low"},
            {"sentiment": "positive", "impact": "low"},
            {"sentiment": "neutral", "impact": "low"},
        ]
        analyzer = SentimentAnalyzer("005930", news_items=news)
        score, _ = analyzer.calc_sentiment_score()
        assert score == 10.0

    def test_positive(self):
        """긍정 60-80% → 8점"""
        news = [
            {"sentiment": "positive", "impact": "low"},
            {"sentiment": "positive", "impact": "low"},
            {"sentiment": "positive", "impact": "low"},
            {"sentiment": "negative", "impact": "low"},
            {"sentiment": "neutral", "impact": "low"},
        ]
        analyzer = SentimentAnalyzer("005930", news_items=news)
        score, _ = analyzer.calc_sentiment_score()
        assert score == 8.0

    def test_neutral(self):
        """긍정 50%, 부정 50% → 6점 기본이나 부정>=50% 감점 → 4점"""
        news = [
            {"sentiment": "positive", "impact": "low"},
            {"sentiment": "negative", "impact": "low"},
        ]
        analyzer = SentimentAnalyzer("005930", news_items=news)
        score, _ = analyzer.calc_sentiment_score()
        # positive_ratio=0.5 → 6점, but negative_ratio=0.5 >= 0.5 → -2 = 4점
        assert score == 4.0

    def test_somewhat_negative(self):
        """긍정 33%, 부정 67% → 4점 기본이나 부정>=50% 감점 → 2점"""
        news = [
            {"sentiment": "positive", "impact": "low"},
            {"sentiment": "negative", "impact": "low"},
            {"sentiment": "negative", "impact": "low"},
        ]
        analyzer = SentimentAnalyzer("005930", news_items=news)
        score, _ = analyzer.calc_sentiment_score()
        # positive_ratio=0.33 → 4점, negative_ratio=0.67 >= 0.5 → -2 = 2점
        assert score == 2.0

    def test_very_negative(self):
        """긍정 < 20% → 2점, 부정 >= 50% → 추가 감점"""
        news = [
            {"sentiment": "negative", "impact": "low"},
            {"sentiment": "negative", "impact": "low"},
            {"sentiment": "negative", "impact": "low"},
            {"sentiment": "negative", "impact": "low"},
            {"sentiment": "negative", "impact": "low"},
        ]
        analyzer = SentimentAnalyzer("005930", news_items=news)
        score, _ = analyzer.calc_sentiment_score()
        # 긍정 0% → 2점 - 부정감점 2 = max(1.0, 0) = 1.0
        assert score == 1.0

    def test_no_news(self):
        """뉴스 없음 → 5점 (중립)"""
        analyzer = SentimentAnalyzer("005930", news_items=[])
        score, desc = analyzer.calc_sentiment_score()
        assert score == 5.0
        assert "중립" in desc

    def test_all_neutral_sentiment(self):
        """전부 neutral → 5점"""
        news = [
            {"sentiment": "neutral", "impact": "low"},
            {"sentiment": "neutral", "impact": "low"},
        ]
        analyzer = SentimentAnalyzer("005930", news_items=news)
        score, _ = analyzer.calc_sentiment_score()
        assert score == 5.0


class TestImpactScore:
    """뉴스 영향도 점수 테스트 (6점 만점)"""

    def test_many_high_impact(self):
        """고영향 3건 이상 → 6점"""
        news = [
            {"sentiment": "positive", "impact": "high"},
            {"sentiment": "positive", "impact": "high"},
            {"sentiment": "positive", "impact": "high"},
        ]
        analyzer = SentimentAnalyzer("005930", news_items=news)
        score, _ = analyzer.calc_impact_score()
        assert score == 6.0

    def test_two_high_impact(self):
        """고영향 2건 → 5점"""
        news = [
            {"sentiment": "positive", "impact": "high"},
            {"sentiment": "positive", "impact": "high"},
        ]
        analyzer = SentimentAnalyzer("005930", news_items=news)
        score, _ = analyzer.calc_impact_score()
        assert score == 5.0

    def test_one_high_impact(self):
        """고영향 1건 → 4점"""
        news = [
            {"sentiment": "positive", "impact": "high"},
            {"sentiment": "neutral", "impact": "low"},
        ]
        analyzer = SentimentAnalyzer("005930", news_items=news)
        score, _ = analyzer.calc_impact_score()
        assert score == 4.0

    def test_medium_only(self):
        """중영향만 → 3점"""
        news = [
            {"sentiment": "positive", "impact": "medium"},
            {"sentiment": "neutral", "impact": "low"},
        ]
        analyzer = SentimentAnalyzer("005930", news_items=news)
        score, _ = analyzer.calc_impact_score()
        assert score == 3.0

    def test_low_only(self):
        """저영향만 → 2점"""
        news = [
            {"sentiment": "positive", "impact": "low"},
            {"sentiment": "neutral", "impact": "low"},
        ]
        analyzer = SentimentAnalyzer("005930", news_items=news)
        score, _ = analyzer.calc_impact_score()
        assert score == 2.0

    def test_no_news_impact(self):
        """뉴스 없음 → 3점"""
        analyzer = SentimentAnalyzer("005930", news_items=[])
        score, _ = analyzer.calc_impact_score()
        assert score == 3.0


class TestVolumeScore:
    """뉴스 양 점수 테스트 (4점 만점)"""

    def test_high_volume(self):
        """20건 이상 → 4점"""
        news = [{"sentiment": "neutral", "impact": "low"}] * 25
        analyzer = SentimentAnalyzer("005930", news_items=news)
        score, _ = analyzer.calc_volume_score()
        assert score == 4.0

    def test_medium_volume(self):
        """10-20건 → 3점"""
        news = [{"sentiment": "neutral", "impact": "low"}] * 15
        analyzer = SentimentAnalyzer("005930", news_items=news)
        score, _ = analyzer.calc_volume_score()
        assert score == 3.0

    def test_low_volume(self):
        """5-10건 → 2점"""
        news = [{"sentiment": "neutral", "impact": "low"}] * 7
        analyzer = SentimentAnalyzer("005930", news_items=news)
        score, _ = analyzer.calc_volume_score()
        assert score == 2.0

    def test_very_low_volume(self):
        """5건 미만 → 1점"""
        news = [{"sentiment": "neutral", "impact": "low"}] * 3
        analyzer = SentimentAnalyzer("005930", news_items=news)
        score, _ = analyzer.calc_volume_score()
        assert score == 1.0


class TestSentimentTotal:
    """감정분석 총점 테스트"""

    def test_positive_total(self, positive_news):
        """긍정 뉴스 총점"""
        analyzer = SentimentAnalyzer("005930", "삼성전자", positive_news)
        result = analyzer.calculate_total()

        assert result["stock_code"] == "005930"
        assert result["max_score"] == 20.0
        assert result["total_score"] > 10.0

    def test_negative_total(self, negative_news):
        """부정 뉴스 총점"""
        analyzer = SentimentAnalyzer("005930", "삼성전자", negative_news)
        result = analyzer.calculate_total()

        assert result["total_score"] < 10.0

    def test_score_sum_matches(self, mixed_news):
        """세부 점수 합 == 총점"""
        analyzer = SentimentAnalyzer("005930", "삼성전자", mixed_news)
        result = analyzer.calculate_total()

        detail_sum = sum(d["score"] for d in result["details"].values())
        assert abs(detail_sum - result["total_score"]) < 0.01

    def test_news_summary(self, positive_news):
        """뉴스 요약 포함"""
        analyzer = SentimentAnalyzer("005930", "삼성전자", positive_news)
        result = analyzer.calculate_total()

        summary = result["news_summary"]
        assert "total" in summary
        assert "positive" in summary
        assert "negative" in summary
        assert summary["total"] == len(positive_news)

    def test_empty_news_neutral(self):
        """뉴스 없으면 중립 점수"""
        analyzer = SentimentAnalyzer("005930", news_items=[])
        result = analyzer.calculate_total()
        # 5.0 + 3.0 + 1.0 = 9.0
        assert result["total_score"] == 9.0

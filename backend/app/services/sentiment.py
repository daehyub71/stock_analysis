"""
Sentiment Analysis Service
- 감정분석 기반 점수 계산 (20점 만점)

점수 구성:
- 뉴스 감정 점수: 10점 (긍정/부정 비율)
- 뉴스 영향도 점수: 6점 (고영향 뉴스 비중)
- 뉴스 양 점수: 4점 (관심도 지표)

데이터 소스:
- 네이버 뉴스 (키워드 기반 감정 분석)
- OpenAI 분석 (선택적, 심층 분석)
"""

from datetime import datetime, timedelta
from typing import Optional

from app.collectors.news_collector import NewsCollector


class SentimentAnalyzer:
    """감정분석 점수 계산기"""

    # 최대 점수
    MAX_SENTIMENT = 10.0    # 감정 점수
    MAX_IMPACT = 6.0        # 영향도 점수
    MAX_VOLUME = 4.0        # 뉴스 양 점수

    MAX_TOTAL = 20.0        # 감정분석 총점

    def __init__(
        self,
        stock_code: str,
        stock_name: Optional[str] = None,
        news_items: Optional[list[dict]] = None,
        days: int = 30,
    ):
        """
        Args:
            stock_code: 종목코드
            stock_name: 종목명 (없으면 종목코드로 검색)
            news_items: 뉴스 리스트 (없으면 수집)
            days: 뉴스 수집 기간 (일)
        """
        self.stock_code = stock_code
        self.stock_name = stock_name or stock_code
        self.days = days

        if news_items is not None:
            self.news_items = news_items
        else:
            self._collect_news()

        self._analyze_news()

    def _collect_news(self) -> None:
        """뉴스 수집"""
        try:
            collector = NewsCollector()
            # search_naver_stock_news 메서드 사용 (collect_news는 존재하지 않음)
            self.news_items = collector.search_naver_stock_news(
                stock_code=self.stock_code,
                stock_name=self.stock_name,
                limit=10,  # 최근 10건 수집
                strict_filter=True,
                price_impact_only=False,  # 모든 관련 뉴스 수집
                days=self.days,  # 기간 필터 (기본 7일)
            )
        except Exception as e:
            print(f"뉴스 수집 실패: {e}")
            self.news_items = []

    def _analyze_news(self) -> None:
        """뉴스 감정 분석 결과 집계"""
        self.total_count = len(self.news_items)
        self.positive_count = 0
        self.negative_count = 0
        self.neutral_count = 0
        self.high_impact_count = 0
        self.medium_impact_count = 0

        for item in self.news_items:
            sentiment = item.get("sentiment", "neutral")
            impact = item.get("impact", "low")

            if sentiment == "positive":
                self.positive_count += 1
            elif sentiment == "negative":
                self.negative_count += 1
            else:
                self.neutral_count += 1

            if impact == "high":
                self.high_impact_count += 1
            elif impact == "medium":
                self.medium_impact_count += 1

    @property
    def has_data(self) -> bool:
        """데이터 존재 여부"""
        return self.total_count > 0

    # === 감정 점수 (10점) ===

    def calc_sentiment_score(self) -> tuple[float, str]:
        """
        뉴스 감정 점수 계산

        긍정 비율에 따라 점수 부여
        - 80% 이상 긍정: 10점
        - 60% ~ 80% 긍정: 8점
        - 40% ~ 60% 긍정: 6점
        - 20% ~ 40% 긍정: 4점
        - 20% 미만 긍정: 2점

        부정 비율이 높으면 감점
        - 50% 이상 부정: -2점 추가 감점

        Returns:
            (점수, 설명)
        """
        if not self.has_data:
            return 5.0, "뉴스 데이터 없음 (중립)"

        # 감정 없는 뉴스 제외
        sentiment_count = self.positive_count + self.negative_count
        if sentiment_count == 0:
            return 5.0, f"감정 분석 불가 (뉴스 {self.total_count}건)"

        positive_ratio = self.positive_count / sentiment_count
        negative_ratio = self.negative_count / sentiment_count

        # 기본 점수 계산
        if positive_ratio >= 0.8:
            score = 10.0
            desc = "매우 긍정적"
        elif positive_ratio >= 0.6:
            score = 8.0
            desc = "긍정적"
        elif positive_ratio >= 0.4:
            score = 6.0
            desc = "중립"
        elif positive_ratio >= 0.2:
            score = 4.0
            desc = "다소 부정적"
        else:
            score = 2.0
            desc = "부정적"

        # 부정 비율 높으면 추가 감점
        if negative_ratio >= 0.5:
            score = max(1.0, score - 2.0)
            desc += " (부정 다수)"

        detail = f"{desc} (긍정 {self.positive_count}, 부정 {self.negative_count}, 중립 {self.neutral_count})"
        return score, detail

    # === 영향도 점수 (6점) ===

    def calc_impact_score(self) -> tuple[float, str]:
        """
        뉴스 영향도 점수 계산

        고영향 뉴스 비중에 따라 점수 부여
        - 고영향 3건 이상: 6점
        - 고영향 2건: 5점
        - 고영향 1건: 4점
        - 중영향만 있음: 3점
        - 영향도 있는 뉴스 없음: 2점

        Returns:
            (점수, 설명)
        """
        if not self.has_data:
            return 3.0, "뉴스 데이터 없음"

        if self.high_impact_count >= 3:
            return 6.0, f"고영향 뉴스 다수 ({self.high_impact_count}건)"
        elif self.high_impact_count == 2:
            return 5.0, f"고영향 뉴스 2건"
        elif self.high_impact_count == 1:
            return 4.0, f"고영향 뉴스 1건"
        elif self.medium_impact_count > 0:
            return 3.0, f"중영향 뉴스 {self.medium_impact_count}건"
        else:
            return 2.0, "주가 영향 뉴스 없음"

    # === 뉴스 양 점수 (4점) ===

    def calc_volume_score(self) -> tuple[float, str]:
        """
        뉴스 양 점수 계산 (관심도)

        뉴스 건수에 따라 점수 부여
        - 20건 이상: 4점 (높은 관심)
        - 10건 이상: 3점
        - 5건 이상: 2점
        - 5건 미만: 1점

        Returns:
            (점수, 설명)
        """
        if self.total_count >= 20:
            return 4.0, f"높은 관심 ({self.total_count}건/{self.days}일)"
        elif self.total_count >= 10:
            return 3.0, f"보통 관심 ({self.total_count}건/{self.days}일)"
        elif self.total_count >= 5:
            return 2.0, f"낮은 관심 ({self.total_count}건/{self.days}일)"
        else:
            return 1.0, f"매우 낮은 관심 ({self.total_count}건/{self.days}일)"

    # === 종합 점수 ===

    def calculate_total(self) -> dict:
        """
        감정분석 총점 계산 (20점 만점)

        Returns:
            점수 상세 딕셔너리
        """
        sentiment_score, sentiment_desc = self.calc_sentiment_score()
        impact_score, impact_desc = self.calc_impact_score()
        volume_score, volume_desc = self.calc_volume_score()

        total = sentiment_score + impact_score + volume_score

        return {
            "stock_code": self.stock_code,
            "stock_name": self.stock_name,
            "has_data": self.has_data,
            "total_score": round(total, 1),
            "max_score": self.MAX_TOTAL,
            "period_days": self.days,
            "news_summary": {
                "total": self.total_count,
                "positive": self.positive_count,
                "negative": self.negative_count,
                "neutral": self.neutral_count,
                "high_impact": self.high_impact_count,
                "medium_impact": self.medium_impact_count,
            },
            "details": {
                "sentiment": {
                    "score": sentiment_score,
                    "max": self.MAX_SENTIMENT,
                    "description": sentiment_desc,
                },
                "impact": {
                    "score": impact_score,
                    "max": self.MAX_IMPACT,
                    "description": impact_desc,
                },
                "volume": {
                    "score": volume_score,
                    "max": self.MAX_VOLUME,
                    "description": volume_desc,
                },
            },
            "news_items": self.news_items[:10],  # 최근 10건만 포함
        }


# === 편의 함수 ===

def calculate_sentiment_score(
    stock_code: str,
    stock_name: Optional[str] = None,
    days: int = 7,
) -> dict:
    """종목 감정분석 점수 계산"""
    analyzer = SentimentAnalyzer(stock_code, stock_name, days=days)
    return analyzer.calculate_total()


def batch_sentiment_score(
    stocks: list[dict],
    days: int = 7,
) -> dict[str, dict]:
    """
    여러 종목 감정분석 일괄 계산

    Args:
        stocks: [{"code": "005930", "name": "삼성전자"}, ...]
        days: 분석 기간
    """
    results = {}
    for stock in stocks:
        code = stock.get("code")
        name = stock.get("name")
        results[code] = calculate_sentiment_score(code, name, days)
    return results


if __name__ == "__main__":
    print("=== Sentiment Analysis Service 테스트 ===\n")

    # 테스트용 더미 뉴스 데이터
    test_news = [
        {"title": "삼성전자 실적 호조", "sentiment": "positive", "impact": "high"},
        {"title": "반도체 수출 증가", "sentiment": "positive", "impact": "medium"},
        {"title": "글로벌 경기 불확실성", "sentiment": "negative", "impact": "low"},
        {"title": "삼성전자 신제품 발표", "sentiment": "positive", "impact": "medium"},
        {"title": "메모리 가격 상승 전망", "sentiment": "positive", "impact": "high"},
        {"title": "환율 변동성 확대", "sentiment": "neutral", "impact": "low"},
        {"title": "삼성전자 주주환원 정책", "sentiment": "positive", "impact": "medium"},
    ]

    analyzer = SentimentAnalyzer("005930", "삼성전자", news_items=test_news)
    result = analyzer.calculate_total()

    print(f"종목: {result['stock_name']} ({result['stock_code']})")
    print(f"감정분석 총점: {result['total_score']} / {result['max_score']}")
    print()

    print("=== 뉴스 요약 ===")
    summary = result["news_summary"]
    print(f"전체: {summary['total']}건")
    print(f"긍정: {summary['positive']}건, 부정: {summary['negative']}건, 중립: {summary['neutral']}건")
    print(f"고영향: {summary['high_impact']}건, 중영향: {summary['medium_impact']}건")
    print()

    print("=== 세부 점수 ===")
    for name, detail in result["details"].items():
        print(f"{name}: {detail['score']} / {detail['max']} ({detail['description']})")

    print("\n✅ 테스트 완료")

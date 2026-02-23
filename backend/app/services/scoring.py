"""
Scoring Integration Service
- 기술(30점) + 기본(50점) + 감정(20점) = 100점

통합 점수 계산 및 등급 부여
"""

from datetime import datetime
from typing import Optional

from app.services.technical import TechnicalAnalyzer, calculate_technical_score
from app.services.fundamental import FundamentalAnalyzer, calculate_fundamental_score
from app.services.sentiment import SentimentAnalyzer, calculate_sentiment_score
from app.db import supabase_db


def get_manual_sentiment_score(stock_code: str) -> Optional[dict]:
    """
    수동 뉴스 평점 기반 감정 점수 조회

    Returns:
        평점이 있으면 {"score": float, "avg_rating": float, "rated_count": int, "is_manual": True}
        없으면 None
    """
    stock_id = supabase_db.get_stock_id(stock_code)
    if not stock_id:
        return None

    result = supabase_db.calculate_sentiment_from_ratings(stock_id)

    # 평점이 하나도 없으면 자동 분석 사용
    if result["rated_count"] == 0:
        return None

    return {
        "total_score": result["score"],
        "max_score": 20.0,
        "has_data": True,
        "is_manual": True,
        "avg_rating": result["avg_rating"],
        "rated_count": result["rated_count"],
        "details": {
            "sentiment": {
                "score": result["score"],
                "max": 20.0,
                "description": f"수동 평점 기반 ({result['rated_count']}건, 평균 {result['avg_rating']:+.1f})",
            },
            "impact": {"score": 0, "max": 0, "description": "수동 평점에 포함"},
            "volume": {"score": 0, "max": 0, "description": "수동 평점에 포함"},
        },
        "news_summary": {
            "total": result["rated_count"],
            "rated_count": result["rated_count"],
            "avg_rating": result["avg_rating"],
        },
    }


class StockScorer:
    """종합 점수 계산기"""

    # 점수 구성
    MAX_TECHNICAL = 30.0    # 기술분석
    MAX_FUNDAMENTAL = 50.0  # 기본분석
    MAX_SENTIMENT = 20.0    # 감정분석

    MAX_TOTAL = 100.0       # 총점

    # 등급 기준
    GRADE_THRESHOLDS = {
        "A+": 90,
        "A": 80,
        "B+": 70,
        "B": 60,
        "C+": 50,
        "C": 40,
        "D": 30,
        "F": 0,
    }

    def __init__(
        self,
        stock_code: str,
        stock_name: Optional[str] = None,
        indicators: Optional[dict] = None,
        financials: Optional[dict] = None,
        news_items: Optional[list[dict]] = None,
        prices: Optional[list[dict]] = None,
    ):
        """
        Args:
            stock_code: 종목코드
            stock_name: 종목명
            indicators: 기술지표 (미리 계산된 값)
            financials: 재무 데이터
            news_items: 뉴스 리스트
            prices: 가격 데이터 (미사용)
        """
        self.stock_code = stock_code
        self.stock_name = stock_name or stock_code
        self.analysis_date = datetime.now().strftime("%Y-%m-%d")

        # 각 분석기 초기화
        self.technical_analyzer = TechnicalAnalyzer(stock_code, indicators)
        self.fundamental_analyzer = FundamentalAnalyzer(stock_code, financials)
        self.sentiment_analyzer = SentimentAnalyzer(
            stock_code, stock_name, news_items
        )

    def _get_grade(self, score: float) -> str:
        """점수에 따른 등급 반환"""
        for grade, threshold in self.GRADE_THRESHOLDS.items():
            if score >= threshold:
                return grade
        return "F"

    def calculate_total(self) -> dict:
        """
        종합 점수 계산

        Returns:
            종합 분석 결과 딕셔너리
        """
        # 각 영역별 점수 계산
        technical_result = self.technical_analyzer.calculate_total()
        fundamental_result = self.fundamental_analyzer.calculate_total()

        # 감정분석: 수동 평점이 있으면 우선 사용, 없으면 자동 분석
        manual_sentiment = get_manual_sentiment_score(self.stock_code)
        if manual_sentiment:
            sentiment_result = manual_sentiment
            sentiment_source = "manual"
        else:
            sentiment_result = self.sentiment_analyzer.calculate_total()
            sentiment_source = "auto"

        # 점수 추출
        technical_score = technical_result["total_score"]
        fundamental_score = fundamental_result["total_score"]
        sentiment_score = sentiment_result["total_score"]

        # 총점 계산
        final_total = technical_score + fundamental_score + sentiment_score
        final_total = round(final_total, 1)

        # 등급 판정
        grade = self._get_grade(final_total)

        return {
            "stock_code": self.stock_code,
            "stock_name": self.stock_name,
            "analysis_date": self.analysis_date,
            "total_score": final_total,
            "max_score": self.MAX_TOTAL,
            "grade": grade,
            "sentiment_source": sentiment_source,  # 감정분석 출처 (manual/auto)
            "score_breakdown": {
                "technical": {
                    "score": technical_score,
                    "max": self.MAX_TECHNICAL,
                    "weight": f"{self.MAX_TECHNICAL/self.MAX_TOTAL*100:.0f}%",
                },
                "fundamental": {
                    "score": fundamental_score,
                    "max": self.MAX_FUNDAMENTAL,
                    "weight": f"{self.MAX_FUNDAMENTAL/self.MAX_TOTAL*100:.0f}%",
                },
                "sentiment": {
                    "score": sentiment_score,
                    "max": self.MAX_SENTIMENT,
                    "weight": f"{self.MAX_SENTIMENT/self.MAX_TOTAL*100:.0f}%",
                    "source": sentiment_source,  # 점수 출처 표시
                },
            },
            "details": {
                "technical": technical_result,
                "fundamental": fundamental_result,
                "sentiment": sentiment_result,
            },
        }

    def save_to_db(self, result: Optional[dict] = None) -> bool:
        """
        분석 결과를 Supabase에 저장 (analysis_results_anal 테이블)

        Args:
            result: 분석 결과 (없으면 새로 계산)

        Returns:
            저장 성공 여부
        """
        if result is None:
            result = self.calculate_total()

        # stock_id 조회
        stock_id = supabase_db.get_stock_id(self.stock_code)
        if not stock_id:
            print(f"종목 ID를 찾을 수 없음: {self.stock_code}")
            return False

        breakdown = result["score_breakdown"]
        details = result["details"]

        # 기술분석 세부 점수 추출
        tech_details = details.get("technical", {}).get("details", {})
        tech_ma_arr = tech_details.get("ma_arrangement", {}).get("score", 0)
        tech_ma_div = tech_details.get("ma_divergence", {}).get("score", 0)
        tech_rsi = tech_details.get("rsi", {}).get("score", 0)
        tech_macd = tech_details.get("macd", {}).get("score", 0)
        tech_volume = tech_details.get("volume", {}).get("score", 0)

        # 기본분석 세부 점수 추출
        fund_details = details.get("fundamental", {}).get("details", {})
        fund_per = fund_details.get("per", {}).get("score", 0)
        fund_pbr = fund_details.get("pbr", {}).get("score", 0)
        fund_psr = fund_details.get("psr", {}).get("score", 0)
        fund_rev_growth = fund_details.get("revenue_growth", {}).get("score", 0)
        fund_op_growth = fund_details.get("op_growth", {}).get("score", 0)
        fund_roe = fund_details.get("roe", {}).get("score", 0)
        fund_margin = fund_details.get("op_margin", {}).get("score", 0)
        fund_debt = fund_details.get("debt_ratio", {}).get("score", 0)
        fund_current = fund_details.get("current_ratio", {}).get("score", 0)

        # 감정분석 세부 점수 추출
        sent_details = details.get("sentiment", {}).get("details", {})
        sent_trend = sent_details.get("volume", {}).get("score", 0)  # 트렌드/뉴스량
        sent_news = sent_details.get("sentiment", {}).get("score", 0) + sent_details.get("impact", {}).get("score", 0)

        data = {
            "stock_id": stock_id,
            "analysis_date": result["analysis_date"],
            # 기술분석 (30점)
            "tech_ma_arrangement": tech_ma_arr,
            "tech_ma_divergence": tech_ma_div,
            "tech_rsi": tech_rsi,
            "tech_macd": tech_macd,
            "tech_volume": tech_volume,
            "tech_total": breakdown["technical"]["score"],
            # 기본분석 (50점)
            "fund_per": fund_per,
            "fund_pbr": fund_pbr,
            "fund_psr": fund_psr,
            "fund_revenue_growth": fund_rev_growth,
            "fund_profit_growth": fund_op_growth,
            "fund_roe": fund_roe,
            "fund_margin": fund_margin,
            "fund_debt_ratio": fund_debt,
            "fund_current_ratio": fund_current,
            "fund_total": breakdown["fundamental"]["score"],
            "is_loss_company": details.get("fundamental", {}).get("is_loss_company", False),
            # 감정분석 (20점)
            "sent_trend": sent_trend,
            "sent_news": sent_news,
            "sent_total": breakdown["sentiment"]["score"],
            "sent_data_insufficient": details.get("sentiment", {}).get("has_data", True) is False,
            # 총점
            "total_score": result["total_score"],
            "grade": result["grade"],
        }

        try:
            supabase_db.upsert_analysis_result(data)
            return True
        except Exception as e:
            print(f"분석 결과 저장 실패: {e}")
            return False


# === 편의 함수 ===

def calculate_stock_score(
    stock_code: str,
    stock_name: Optional[str] = None,
    save: bool = False,
    indicators: Optional[dict] = None,
    financials: Optional[dict] = None,
    news_items: Optional[list[dict]] = None,
) -> dict:
    """
    종목 종합 점수 계산

    Args:
        stock_code: 종목코드
        stock_name: 종목명
        save: Supabase 저장 여부
        indicators: 기술지표 (없으면 자동 계산)
        financials: 재무 데이터 (없으면 DB에서 조회)
        news_items: 뉴스 리스트 (없으면 자동 수집)

    Returns:
        분석 결과
    """
    scorer = StockScorer(
        stock_code, stock_name,
        indicators=indicators,
        financials=financials,
        news_items=news_items,
    )
    result = scorer.calculate_total()

    if save:
        scorer.save_to_db(result)

    return result


def batch_stock_score(
    stocks: list[dict],
    save: bool = False,
) -> dict[str, dict]:
    """
    여러 종목 종합 점수 일괄 계산

    Args:
        stocks: [{"code": "005930", "name": "삼성전자"}, ...]
        save: Supabase 저장 여부

    Returns:
        종목별 분석 결과
    """
    results = {}
    for stock in stocks:
        code = stock.get("code")
        name = stock.get("name")

        try:
            result = calculate_stock_score(code, name, save)
            results[code] = result
            print(f"✅ {name}({code}): {result['total_score']}점 [{result['grade']}]")
        except Exception as e:
            print(f"❌ {name}({code}): 분석 실패 - {e}")
            results[code] = {"error": str(e)}

    return results


def get_stock_ranking(
    analysis_date: Optional[str] = None,
    limit: int = 50,
    min_score: float = 0,
) -> list[dict]:
    """
    점수 순위 조회

    Args:
        analysis_date: 분석 날짜 (없으면 최신)
        limit: 조회 건수
        min_score: 최소 점수

    Returns:
        순위 리스트
    """
    if analysis_date is None:
        analysis_date = datetime.now().strftime("%Y-%m-%d")

    return supabase_db.get_analysis_ranking(
        analysis_date=analysis_date,
        limit=limit,
        min_score=min_score,
    )


if __name__ == "__main__":
    print("=== Stock Scoring Service 테스트 ===\n")

    # 테스트용 더미 데이터로 점수 계산
    from app.analyzers.indicators import TechnicalIndicators

    # 더미 기술지표
    test_indicators = {
        "has_data": True,
        "current_price": 72000,
        "ma5": 71500,
        "ma20": 70000,
        "ma60": 68000,
        "ma120": 65000,
        "rsi14": 55.0,
        "macd": 150.0,
        "macd_hist": 50.0,
        "volume_ratio": 1.2,
    }

    # 더미 재무 데이터
    test_financials = {
        "per": 12.5,
        "pbr": 1.2,
        "psr": 0.8,
        "revenue_growth": 15.3,
        "op_growth": 22.5,
        "roe": 14.2,
        "op_margin": 11.5,
        "debt_ratio": 85.0,
        "current_ratio": 165.0,
    }

    # 더미 뉴스 데이터
    test_news = [
        {"title": "삼성전자 실적 호조", "sentiment": "positive", "impact": "high"},
        {"title": "반도체 수출 증가", "sentiment": "positive", "impact": "medium"},
        {"title": "글로벌 경기 불확실성", "sentiment": "negative", "impact": "low"},
        {"title": "삼성전자 신제품 발표", "sentiment": "positive", "impact": "medium"},
        {"title": "메모리 가격 상승 전망", "sentiment": "positive", "impact": "high"},
    ]

    # 더미 가격 데이터
    import random
    test_prices = []
    base_volume = 10_000_000
    base_price = 72000

    for i in range(20):
        price = base_price * (1 + random.uniform(-0.02, 0.02))
        volume = int(base_volume * (1 + random.uniform(-0.2, 0.3)))
        test_prices.append({
            "date": f"2024-01-{i+1:02d}",
            "open_price": price,
            "high_price": price * 1.01,
            "low_price": price * 0.99,
            "close_price": price,
            "volume": volume,
        })

    # 점수 계산
    scorer = StockScorer(
        stock_code="005930",
        stock_name="삼성전자",
        indicators=test_indicators,
        financials=test_financials,
        news_items=test_news,
        prices=test_prices,
    )

    result = scorer.calculate_total()

    print(f"종목: {result['stock_name']} ({result['stock_code']})")
    print(f"분석일: {result['analysis_date']}")
    print(f"\n{'='*50}")
    print(f"총점: {result['total_score']} / {result['max_score']} [{result['grade']}]")
    print(f"{'='*50}\n")

    print("=== 영역별 점수 ===")
    breakdown = result["score_breakdown"]
    print(f"기술분석: {breakdown['technical']['score']} / {breakdown['technical']['max']} ({breakdown['technical']['weight']})")
    print(f"기본분석: {breakdown['fundamental']['score']} / {breakdown['fundamental']['max']} ({breakdown['fundamental']['weight']})")
    print(f"감정분석: {breakdown['sentiment']['score']} / {breakdown['sentiment']['max']} ({breakdown['sentiment']['weight']})")

    print("\n✅ 테스트 완료")

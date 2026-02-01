"""
Google Trends Collector
- pytrends를 사용한 검색 트렌드 수집
- 종목명 기반 관심도 측정
"""

import time
from datetime import datetime, timedelta
from typing import Optional

from pytrends.request import TrendReq


class GoogleTrendsCollector:
    """구글 트렌드 수집기"""

    def __init__(self, hl: str = "ko", tz: int = 540):
        """
        Args:
            hl: 언어 (기본: 한국어)
            tz: 타임존 오프셋 (기본: 540 = KST)
        """
        self.pytrends = TrendReq(hl=hl, tz=tz)

    def get_interest_over_time(
        self,
        keywords: list[str],
        timeframe: str = "today 1-m",  # 최근 1개월
        geo: str = "KR",
    ) -> dict:
        """
        키워드별 시간대별 관심도 조회

        Args:
            keywords: 검색 키워드 리스트 (최대 5개)
            timeframe: 기간 (예: "today 1-m", "today 3-m", "2024-01-01 2024-01-31")
            geo: 지역 코드 (기본: KR)

        Returns:
            키워드별 관심도 데이터
        """
        if len(keywords) > 5:
            keywords = keywords[:5]

        try:
            self.pytrends.build_payload(
                kw_list=keywords,
                timeframe=timeframe,
                geo=geo,
            )

            df = self.pytrends.interest_over_time()

            if df.empty:
                return {"keywords": keywords, "data": [], "error": "No data available"}

            # isPartial 컬럼 제거
            if "isPartial" in df.columns:
                df = df.drop(columns=["isPartial"])

            # 결과 변환
            result = {
                "keywords": keywords,
                "timeframe": timeframe,
                "geo": geo,
                "data": [],
            }

            for date_idx, row in df.iterrows():
                entry = {"date": date_idx.strftime("%Y-%m-%d")}
                for kw in keywords:
                    if kw in row:
                        entry[kw] = int(row[kw])
                result["data"].append(entry)

            # 키워드별 평균/최대 관심도
            result["summary"] = {}
            for kw in keywords:
                if kw in df.columns:
                    result["summary"][kw] = {
                        "mean": float(df[kw].mean()),
                        "max": int(df[kw].max()),
                        "min": int(df[kw].min()),
                        "latest": int(df[kw].iloc[-1]) if len(df) > 0 else 0,
                    }

            return result

        except Exception as e:
            return {
                "keywords": keywords,
                "data": [],
                "error": str(e),
            }

    def get_stock_trend(
        self,
        stock_name: str,
        days: int = 30,
    ) -> dict:
        """
        종목명 기반 트렌드 조회

        Args:
            stock_name: 종목명
            days: 조회 기간 (일)

        Returns:
            트렌드 데이터 및 점수
        """
        # timeframe 설정
        if days <= 7:
            timeframe = "now 7-d"
        elif days <= 30:
            timeframe = "today 1-m"
        elif days <= 90:
            timeframe = "today 3-m"
        else:
            timeframe = "today 12-m"

        result = self.get_interest_over_time(
            keywords=[stock_name],
            timeframe=timeframe,
            geo="KR",
        )

        # 점수 계산 (0-100)
        score_data = {
            "stock_name": stock_name,
            "days": days,
            "crawled_at": datetime.now().isoformat(),
        }

        if "error" in result and result.get("data") == []:
            # 데이터 없음 → 중립값 50
            score_data["trend_score"] = 50
            score_data["data_available"] = False
            score_data["error"] = result.get("error")
        else:
            summary = result.get("summary", {}).get(stock_name, {})
            score_data["mean"] = summary.get("mean", 50)
            score_data["max"] = summary.get("max", 50)
            score_data["latest"] = summary.get("latest", 50)
            score_data["trend_score"] = summary.get("mean", 50)  # 평균값을 점수로 사용
            score_data["data_available"] = True
            score_data["data_points"] = len(result.get("data", []))

        return score_data

    def get_related_queries(
        self,
        keyword: str,
        geo: str = "KR",
    ) -> dict:
        """
        연관 검색어 조회

        Args:
            keyword: 검색 키워드
            geo: 지역 코드

        Returns:
            연관 검색어 (top, rising)
        """
        try:
            self.pytrends.build_payload(
                kw_list=[keyword],
                timeframe="today 1-m",
                geo=geo,
            )

            related = self.pytrends.related_queries()

            result = {
                "keyword": keyword,
                "top": [],
                "rising": [],
            }

            if keyword in related:
                top_df = related[keyword].get("top")
                if top_df is not None and not top_df.empty:
                    result["top"] = top_df.to_dict("records")[:10]

                rising_df = related[keyword].get("rising")
                if rising_df is not None and not rising_df.empty:
                    result["rising"] = rising_df.to_dict("records")[:10]

            return result

        except Exception as e:
            return {
                "keyword": keyword,
                "top": [],
                "rising": [],
                "error": str(e),
            }


# 싱글톤 인스턴스
_collector: Optional[GoogleTrendsCollector] = None


def get_collector() -> GoogleTrendsCollector:
    """GoogleTrendsCollector 싱글톤"""
    global _collector
    if _collector is None:
        _collector = GoogleTrendsCollector()
    return _collector


# === 편의 함수 ===

def get_stock_trend(stock_name: str, days: int = 30) -> dict:
    """종목명 기반 트렌드 조회"""
    return get_collector().get_stock_trend(stock_name, days)


def get_trends_batch(
    stock_names: list[str],
    days: int = 30,
    delay: float = 2.0,
) -> dict[str, dict]:
    """
    여러 종목의 트렌드 일괄 조회

    Args:
        stock_names: 종목명 리스트
        days: 조회 기간 (일)
        delay: 요청 간 딜레이 (초) - 구글 rate limit 방지

    Returns:
        종목명 → 트렌드 데이터 딕셔너리
    """
    collector = get_collector()
    results = {}
    total = len(stock_names)

    for i, name in enumerate(stock_names, 1):
        print(f"[{i}/{total}] {name} 트렌드 조회 중...")
        results[name] = collector.get_stock_trend(name, days)

        if i < total:
            time.sleep(delay)  # Rate limit 방지

    return results


def calculate_trend_score(trend_data: dict) -> float:
    """
    트렌드 데이터 → 점수 변환 (8점 만점)

    점수 기준:
    - 80 이상: 8점 (매우 높은 관심)
    - 60-79: 6점 (높은 관심)
    - 40-59: 4점 (보통)
    - 20-39: 2점 (낮은 관심)
    - 20 미만: 1점 (매우 낮음)
    - 데이터 없음: 4점 (중립)
    """
    if not trend_data.get("data_available", False):
        return 4.0  # 중립값

    trend_score = trend_data.get("trend_score", 50)

    if trend_score >= 80:
        return 8.0
    elif trend_score >= 60:
        return 6.0
    elif trend_score >= 40:
        return 4.0
    elif trend_score >= 20:
        return 2.0
    else:
        return 1.0


if __name__ == "__main__":
    # 테스트
    print("=== Google Trends Collector 테스트 ===\n")

    # 삼성전자 트렌드
    trend = get_stock_trend("삼성전자", days=30)

    print(f"종목명: {trend.get('stock_name')}")
    print(f"데이터 가용: {trend.get('data_available')}")
    print(f"트렌드 점수: {trend.get('trend_score')}")
    print(f"분석 점수 (8점): {calculate_trend_score(trend)}")

    if trend.get("error"):
        print(f"에러: {trend.get('error')}")

    print("\n✅ Google Trends Collector 테스트 완료")

"""
News Collector
- 종목 관련 뉴스 수집 (네이버 뉴스)
- OpenAI API를 통한 감정 분석
"""

import os
import re
import time
import random
from datetime import datetime, timedelta
from typing import Optional

import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


# User-Agent 로테이션
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]


def _get_headers() -> dict:
    """랜덤 User-Agent 헤더"""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
    }


class NewsCollector:
    """뉴스 수집기"""

    def __init__(self):
        self.openai_api_key = os.environ.get("OPENAI_API_KEY", "")
        self._openai_client = None

    @property
    def openai_client(self) -> Optional[OpenAI]:
        """OpenAI 클라이언트 (lazy init)"""
        if self._openai_client is None and self.openai_api_key:
            self._openai_client = OpenAI(api_key=self.openai_api_key)
        return self._openai_client

    def _get_stock_name(self, stock_code: str) -> str:
        """종목코드로 종목명 조회"""
        try:
            from pykrx import stock as krx
            return krx.get_market_ticker_name(stock_code)
        except Exception:
            return ""

    # 기본 주가 영향 키워드 (환경변수 없을 때 사용)
    # 형식: (키워드, 긍부정, 영향도)
    DEFAULT_KEYWORDS = [
        # 실적/재무 관련 (높은 영향)
        ("실적", "positive", "high"),
        ("매출", "positive", "high"),
        ("영업이익", "positive", "high"),
        ("순이익", "positive", "high"),
        ("흑자", "positive", "high"),
        ("적자", "negative", "high"),
        ("어닝", "positive", "high"),
        ("컨센서스", "positive", "high"),
        ("분기", "positive", "high"),
        ("수주", "positive", "high"),
        ("계약", "positive", "high"),
        ("납품", "positive", "high"),
        ("공급", "positive", "high"),
        ("MOU", "positive", "high"),
        ("협약", "positive", "high"),
        ("인수", "positive", "high"),
        ("합병", "positive", "high"),
        ("투자", "positive", "high"),
        ("지분", "positive", "high"),
        ("출자", "positive", "high"),
        ("유상증자", "negative", "high"),
        ("무상증자", "positive", "high"),
        ("CB", "negative", "high"),
        ("BW", "negative", "high"),
        ("IPO", "positive", "high"),
        ("상장", "positive", "high"),
        ("분할", "positive", "high"),
        # 신사업/시장 관련 (중간 영향)
        ("신제품", "positive", "medium"),
        ("출시", "positive", "medium"),
        ("런칭", "positive", "medium"),
        ("개발", "positive", "medium"),
        ("양산", "positive", "medium"),
        ("생산", "positive", "medium"),
        ("목표가", "positive", "medium"),
        ("투자의견", "positive", "medium"),
        ("매수", "positive", "medium"),
        ("매도", "negative", "medium"),
        ("상승", "positive", "medium"),
        ("하락", "negative", "medium"),
        ("급등", "positive", "medium"),
        ("급락", "negative", "medium"),
        ("신고가", "positive", "medium"),
        ("52주", "positive", "medium"),
        ("배당", "positive", "medium"),
        ("자사주", "positive", "medium"),
        ("주주환원", "positive", "medium"),
        ("구조조정", "negative", "medium"),
        ("감원", "negative", "medium"),
        ("정리해고", "negative", "medium"),
        ("파업", "negative", "medium"),
        ("노조", "negative", "medium"),
        ("소송", "negative", "medium"),
        ("과징금", "negative", "medium"),
        ("제재", "negative", "medium"),
        ("규제", "negative", "medium"),
        ("조사", "negative", "medium"),
        ("합작", "positive", "medium"),
        ("파트너십", "positive", "medium"),
        ("특허", "positive", "medium"),
        ("승인", "positive", "medium"),
        ("허가", "positive", "medium"),
    ]

    def _load_price_impact_keywords(self) -> dict[str, dict]:
        """
        환경변수에서 주가 영향 키워드 로드

        .env 파일의 NEWS_KEYWORDS 사용
        형식: 키워드:긍부정:영향도,키워드:긍부정:영향도,...
        예시: 실적:positive:high,적자:negative:high

        Returns:
            dict[str, dict]: 키워드 → {"sentiment": "positive/negative", "impact": "high/medium"}
        """
        keywords = {}

        keywords_str = os.environ.get("NEWS_KEYWORDS", "")
        if keywords_str:
            for item in keywords_str.split(","):
                item = item.strip()
                parts = item.split(":")
                if len(parts) == 3:
                    keyword, sentiment, impact = parts
                    keywords[keyword.strip()] = {
                        "sentiment": sentiment.strip(),
                        "impact": impact.strip(),
                    }
                elif len(parts) == 2:
                    # 이전 형식 호환 (키워드:영향도)
                    keyword, impact = parts
                    keywords[keyword.strip()] = {
                        "sentiment": "positive",
                        "impact": impact.strip(),
                    }
                elif item:
                    keywords[item] = {"sentiment": "positive", "impact": "medium"}
        else:
            # 환경변수 없으면 기본값 사용
            for keyword, sentiment, impact in self.DEFAULT_KEYWORDS:
                keywords[keyword] = {"sentiment": sentiment, "impact": impact}

        return keywords

    @property
    def price_impact_keywords(self) -> dict[str, str]:
        """주가 영향 키워드 (캐싱)"""
        if not hasattr(self, "_price_impact_keywords"):
            self._price_impact_keywords = self._load_price_impact_keywords()
        return self._price_impact_keywords

    def _has_price_impact_keyword(self, title: str) -> tuple[bool, str, str]:
        """
        주가에 영향을 줄 수 있는 키워드가 있는지 확인

        Returns:
            (키워드 존재 여부, 긍부정: positive/negative, 영향도: high/medium/none)
        """
        for keyword, info in self.price_impact_keywords.items():
            if keyword in title:
                return True, info["sentiment"], info["impact"]
        return False, "neutral", "none"

    def _is_relevant_news(self, title: str, stock_name: str, stock_code: str) -> bool:
        """뉴스가 해당 종목과 관련있는지 확인"""
        if not stock_name:
            return True

        title_lower = title.lower()
        has_stock_name = False

        # 종목명 또는 종목코드가 제목에 포함
        if stock_name in title:
            has_stock_name = True

        # 종목명의 일부 (예: '삼성전자' → '삼성')
        if not has_stock_name and len(stock_name) > 2:
            short_name = stock_name[:2]  # 첫 2글자
            if short_name in title and len(short_name) >= 2:
                has_stock_name = True

        # 영문 종목명 체크 (예: Samsung)
        english_names = {
            "삼성전자": ["samsung", "삼성"],
            "SK하이닉스": ["hynix", "sk하이닉스", "하이닉스"],
            "현대차": ["hyundai", "현대자동차", "현대차"],
            "LG에너지솔루션": ["lg에너지", "lges"],
            "네이버": ["naver"],
            "카카오": ["kakao"],
        }

        if not has_stock_name and stock_name in english_names:
            for alias in english_names[stock_name]:
                if alias.lower() in title_lower:
                    has_stock_name = True
                    break

        return has_stock_name

    def _is_price_relevant_news(self, title: str, stock_name: str, stock_code: str) -> tuple[bool, str, str]:
        """
        주가 영향 관련 뉴스인지 확인 (종목명 + 주가영향 키워드)

        Returns:
            (관련 여부, 긍부정, 영향도)
        """
        # 1. 먼저 종목과 관련있는지 확인
        if not self._is_relevant_news(title, stock_name, stock_code):
            return False, "neutral", "none"

        # 2. 주가 영향 키워드 확인
        has_keyword, sentiment, impact = self._has_price_impact_keyword(title)

        if has_keyword:
            return True, sentiment, impact
        else:
            # 종목명은 있지만 주가 영향 키워드가 없는 경우
            return True, "neutral", "low"

    def search_naver_stock_news(
        self,
        stock_code: str,
        stock_name: str = "",
        limit: int = 5,
        strict_filter: bool = True,
        price_impact_only: bool = True,
        days: int = 30,
    ) -> list[dict]:
        """
        네이버 증권 종목 뉴스 조회

        Args:
            stock_code: 종목코드
            stock_name: 종목명 (없으면 자동 조회)
            limit: 수집 개수
            strict_filter: True면 종목명이 제목에 포함된 뉴스만
            price_impact_only: True면 주가 영향 키워드가 있는 뉴스만
            days: 최근 N일 이내의 뉴스만 수집 (기본 30일)

        Returns:
            뉴스 리스트
        """
        # 종목명 조회
        if not stock_name:
            stock_name = self._get_stock_name(stock_code)

        # 날짜 필터용 기준일 계산
        cutoff_date = datetime.now() - timedelta(days=days)

        # 네이버 증권 종목 뉴스 URL (iframe)
        url = "https://finance.naver.com/item/news_news.naver"
        params = {
            "code": stock_code,
            "page": "",
            "clusterId": "",
        }

        # Referer 헤더 추가 (필수)
        headers = _get_headers()
        headers["Referer"] = f"https://finance.naver.com/item/news.naver?code={stock_code}"

        try:
            time.sleep(0.5 + random.uniform(0, 0.3))
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            high_impact_news = []   # 주가 영향도 높음 (수주, 실적, 계약 등)
            medium_impact_news = []  # 주가 영향도 중간
            low_impact_news = []    # 주가 영향도 낮음 (종목명만 있음)
            related_news = []       # 종목 관련 없음 (백업)
            seen_titles = set()     # 중복 제거용

            # 모든 type5 테이블에서 뉴스 추출
            tables = soup.select("table.type5")

            for table in tables:
                rows = table.select("tr")
                for row in rows:
                    try:
                        title_elem = row.select_one("td.title a")
                        if not title_elem:
                            continue

                        title = title_elem.get_text(strip=True)

                        # 중복 체크 (제목 기준)
                        title_key = title[:30]
                        if title_key in seen_titles:
                            continue
                        seen_titles.add(title_key)

                        link = title_elem.get("href", "")
                        if link and not link.startswith("http"):
                            link = f"https://finance.naver.com{link}"

                        info_elem = row.select_one("td.info")
                        press = info_elem.get_text(strip=True) if info_elem else ""

                        date_elem = row.select_one("td.date")
                        date_text = date_elem.get_text(strip=True) if date_elem else ""

                        # 날짜 필터링 (7일 이내)
                        if date_text:
                            try:
                                # "2025.01.31" 또는 "2025.01.31 14:30" 형식
                                date_str = date_text.split()[0]  # 시간 부분 제거
                                news_date = datetime.strptime(date_str, "%Y.%m.%d")
                                if news_date < cutoff_date:
                                    continue  # 기간 외 뉴스 스킵
                            except (ValueError, IndexError):
                                pass  # 파싱 실패시 포함

                        if title and len(title) > 5:
                            # 주가 영향도 분석
                            is_relevant, sentiment, impact = self._is_price_relevant_news(
                                title, stock_name, stock_code
                            )

                            news_item = {
                                "title": title,
                                "description": "",
                                "link": link,
                                "press": press,
                                "date_text": date_text,
                                "sentiment": sentiment,  # positive/negative/neutral
                                "impact": impact,  # high/medium/low/none
                            }

                            if is_relevant:
                                if impact == "high":
                                    news_item["relevance"] = "high_impact"
                                    high_impact_news.append(news_item)
                                elif impact == "medium":
                                    news_item["relevance"] = "medium_impact"
                                    medium_impact_news.append(news_item)
                                else:  # low
                                    news_item["relevance"] = "low_impact"
                                    low_impact_news.append(news_item)
                            else:
                                news_item["relevance"] = "related"
                                related_news.append(news_item)

                    except Exception:
                        continue

            # 주가 영향도 순으로 정렬하여 결과 생성
            if price_impact_only:
                # 주가 영향도 높음 > 중간 순으로 우선
                results = high_impact_news + medium_impact_news
                results = results[:limit]

                # 부족하면 영향도 낮은 뉴스로 보충
                if len(results) < limit:
                    remaining = limit - len(results)
                    results.extend(low_impact_news[:remaining])
            else:
                # 모든 관련 뉴스 (영향도 순)
                results = high_impact_news + medium_impact_news + low_impact_news
                if strict_filter:
                    results = results[:limit]
                else:
                    # 관련 뉴스도 포함
                    if len(results) < limit:
                        remaining = min(limit - len(results), limit // 2)
                        results.extend(related_news[:remaining])
                    results = results[:limit]

            return results

        except Exception as e:
            print(f"❌ 네이버 증권 뉴스 조회 실패 ({stock_code}): {e}")
            return []

    def search_naver_news(
        self,
        query: str,
        limit: int = 5,
        sort: str = "date",
    ) -> list[dict]:
        """
        네이버 뉴스 검색 (백업용)
        - 종목코드가 없을 때 사용
        """
        # 네이버 뉴스 검색 API 대신 증권 뉴스 사용 권장
        return []

    def analyze_sentiment_openai(self, news_list: list[dict]) -> dict:
        """
        OpenAI API를 통한 뉴스 감정 분석

        Args:
            news_list: 뉴스 리스트

        Returns:
            감정 분석 결과
        """
        if not self.openai_client:
            return {
                "sentiment": "neutral",
                "score": 0.5,
                "error": "OpenAI API key not configured",
            }

        if not news_list:
            return {
                "sentiment": "neutral",
                "score": 0.5,
                "reason": "No news data",
            }

        # 뉴스 텍스트 준비
        news_text = "\n".join([
            f"- {item['title']}: {item.get('description', '')[:100]}"
            for item in news_list[:5]
        ])

        prompt = f"""다음은 특정 주식 종목과 관련된 최근 뉴스들입니다.
이 뉴스들을 종합적으로 분석하여 투자자 관점에서 감정(sentiment)을 평가해주세요.

뉴스 목록:
{news_text}

다음 형식으로 응답해주세요:
1. 감정: positive / neutral / negative 중 하나
2. 점수: 0.0 ~ 1.0 사이 (0: 매우 부정, 0.5: 중립, 1.0: 매우 긍정)
3. 이유: 1-2문장으로 요약

응답 예시:
감정: positive
점수: 0.75
이유: 실적 호조 소식과 신규 사업 확장 뉴스가 긍정적이며, 부정적인 뉴스는 없음.
"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",  # 비용 최적화
                messages=[
                    {"role": "system", "content": "당신은 주식 뉴스 감정 분석 전문가입니다."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=200,
            )

            result_text = response.choices[0].message.content

            # 결과 파싱
            sentiment = "neutral"
            score = 0.5
            reason = ""

            if "positive" in result_text.lower():
                sentiment = "positive"
            elif "negative" in result_text.lower():
                sentiment = "negative"

            # 점수 추출
            score_match = re.search(r"점수[:\s]*([0-9.]+)", result_text)
            if score_match:
                score = float(score_match.group(1))
                score = max(0.0, min(1.0, score))  # 0-1 범위로 제한

            # 이유 추출
            reason_match = re.search(r"이유[:\s]*(.+)", result_text, re.DOTALL)
            if reason_match:
                reason = reason_match.group(1).strip().split("\n")[0]

            return {
                "sentiment": sentiment,
                "score": score,
                "reason": reason,
                "news_count": len(news_list),
                "analyzed_at": datetime.now().isoformat(),
            }

        except Exception as e:
            print(f"❌ OpenAI 감정 분석 실패: {e}")
            return {
                "sentiment": "neutral",
                "score": 0.5,
                "error": str(e),
            }

    def get_stock_news_sentiment(
        self,
        stock_code: str,
        stock_name: str = "",
        news_count: int = 5,
    ) -> dict:
        """
        종목 뉴스 수집 및 감정 분석

        Args:
            stock_code: 종목코드
            stock_name: 종목명 (로깅용)
            news_count: 수집할 뉴스 개수

        Returns:
            뉴스 및 감정 분석 결과
        """
        # 네이버 증권 종목 뉴스 수집 (종목명 필터링 적용)
        news_list = self.search_naver_stock_news(
            stock_code=stock_code,
            stock_name=stock_name,
            limit=news_count,
            strict_filter=True,
        )

        # 감정 분석
        sentiment = self.analyze_sentiment_openai(news_list)

        return {
            "stock_code": stock_code,
            "stock_name": stock_name,
            "news": news_list,
            "sentiment": sentiment,
            "crawled_at": datetime.now().isoformat(),
        }


# 싱글톤 인스턴스
_collector: Optional[NewsCollector] = None


def get_collector() -> NewsCollector:
    """NewsCollector 싱글톤"""
    global _collector
    if _collector is None:
        _collector = NewsCollector()
    return _collector


# === 편의 함수 ===

def get_stock_news(stock_code: str, limit: int = 5) -> list[dict]:
    """종목 뉴스 수집 (종목코드 사용)"""
    return get_collector().search_naver_stock_news(stock_code, stock_name="", limit=limit)


def get_stock_sentiment(stock_code: str, stock_name: str = "", news_count: int = 5) -> dict:
    """종목 뉴스 감정 분석"""
    return get_collector().get_stock_news_sentiment(stock_code, stock_name, news_count)


def get_sentiment_batch(
    stocks: list[tuple[str, str]],  # [(code, name), ...]
    news_count: int = 5,
    delay: float = 2.0,
) -> dict[str, dict]:
    """
    여러 종목의 뉴스 감정 일괄 분석

    Args:
        stocks: (종목코드, 종목명) 튜플 리스트
        news_count: 종목당 뉴스 개수
        delay: 요청 간 딜레이 (초)

    Returns:
        종목코드 → 감정 분석 결과 딕셔너리
    """
    collector = get_collector()
    results = {}
    total = len(stocks)

    for i, (code, name) in enumerate(stocks, 1):
        print(f"[{i}/{total}] {name} ({code}) 뉴스 감정 분석 중...")
        results[code] = collector.get_stock_news_sentiment(code, name, news_count)

        if i < total:
            time.sleep(delay)

    return results


def calculate_news_score(sentiment_data: dict) -> float:
    """
    감정 데이터 → 점수 변환 (12점 만점)

    점수 기준:
    - score 0.8-1.0: 12점 (매우 긍정)
    - score 0.6-0.8: 9점 (긍정)
    - score 0.4-0.6: 6점 (중립)
    - score 0.2-0.4: 3점 (부정)
    - score 0.0-0.2: 0점 (매우 부정)
    """
    sentiment = sentiment_data.get("sentiment", {})
    score = sentiment.get("score", 0.5)

    if score >= 0.8:
        return 12.0
    elif score >= 0.6:
        return 9.0
    elif score >= 0.4:
        return 6.0
    elif score >= 0.2:
        return 3.0
    else:
        return 0.0


if __name__ == "__main__":
    # 테스트
    print("=== News Collector 테스트 ===\n")

    # 삼성전자 뉴스
    news = get_stock_news("삼성전자", limit=3)
    print(f"뉴스 수집: {len(news)}건")
    for item in news:
        print(f"  - {item['title'][:50]}...")

    # 감정 분석 (OpenAI API 키 필요)
    if os.environ.get("OPENAI_API_KEY"):
        sentiment = get_stock_sentiment("삼성전자", news_count=3)
        print(f"\n감정: {sentiment['sentiment'].get('sentiment')}")
        print(f"점수: {sentiment['sentiment'].get('score')}")
        print(f"이유: {sentiment['sentiment'].get('reason')}")
        print(f"뉴스 점수 (12점): {calculate_news_score(sentiment)}")
    else:
        print("\n⚠️ OpenAI API 키 미설정 - 감정 분석 스킵")

    print("\n✅ News Collector 테스트 완료")

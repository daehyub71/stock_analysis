"""
OpenAI Sentiment Analyzer
- GPT를 활용한 뉴스 감정 심층 분석
- 기본 키워드 분석을 보완하는 용도
"""

import os
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# OpenAI 설정
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")


class OpenAISentimentAnalyzer:
    """OpenAI 기반 감정 분석기"""

    SYSTEM_PROMPT = """당신은 주식 시장 뉴스를 분석하는 전문 애널리스트입니다.
뉴스 기사의 제목과 내용을 보고 해당 종목에 대한 감정(sentiment)과 주가 영향도(impact)를 분석해주세요.

분석 기준:
1. 감정(sentiment): positive, negative, neutral 중 하나
   - positive: 실적 개선, 수주 확보, 신사업 진출, 배당 증가 등 긍정적 뉴스
   - negative: 실적 악화, 소송, 제재, 경영 리스크 등 부정적 뉴스
   - neutral: 단순 정보 전달, 영향 불분명

2. 영향도(impact): high, medium, low 중 하나
   - high: 실적 발표, 대형 수주, 대규모 투자, M&A 등 주가에 직접 영향
   - medium: 산업 동향, 경쟁사 뉴스, 정책 변화 등 간접 영향
   - low: 일반 뉴스, 시장 전반 소식 등 미미한 영향

3. 확신도(confidence): 0.0 ~ 1.0
   - 분석 결과에 대한 확신 수준

반드시 JSON 형식으로만 응답하세요:
{
    "sentiment": "positive|negative|neutral",
    "impact": "high|medium|low",
    "confidence": 0.0~1.0,
    "reason": "분석 근거 한 줄 요약"
}
"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Args:
            api_key: OpenAI API 키 (없으면 환경변수 사용)
        """
        self.api_key = api_key or OPENAI_API_KEY
        self._client: Optional[OpenAI] = None

    @property
    def client(self) -> OpenAI:
        """OpenAI 클라이언트 (lazy initialization)"""
        if self._client is None:
            if not self.api_key:
                raise ValueError("OPENAI_API_KEY not configured")
            self._client = OpenAI(api_key=self.api_key)
        return self._client

    @property
    def is_available(self) -> bool:
        """API 사용 가능 여부"""
        return bool(self.api_key)

    def analyze_news(
        self,
        title: str,
        content: Optional[str] = None,
        stock_name: Optional[str] = None,
        model: str = "gpt-4o-mini",
    ) -> dict:
        """
        단일 뉴스 감정 분석

        Args:
            title: 뉴스 제목
            content: 뉴스 본문 (선택)
            stock_name: 종목명 (컨텍스트 제공)
            model: 사용할 모델

        Returns:
            분석 결과 딕셔너리
        """
        if not self.is_available:
            return {
                "sentiment": "neutral",
                "impact": "low",
                "confidence": 0.0,
                "reason": "OpenAI API not configured",
                "error": True,
            }

        # 프롬프트 구성
        user_message = f"종목: {stock_name or '(미지정)'}\n\n"
        user_message += f"제목: {title}\n"
        if content:
            # 토큰 제한을 위해 내용 일부만 사용
            user_message += f"\n본문 요약:\n{content[:500]}..."

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.3,
                max_tokens=200,
                response_format={"type": "json_object"},
            )

            result = response.choices[0].message.content
            import json
            return json.loads(result)

        except Exception as e:
            return {
                "sentiment": "neutral",
                "impact": "low",
                "confidence": 0.0,
                "reason": f"Analysis failed: {str(e)}",
                "error": True,
            }

    def analyze_news_batch(
        self,
        news_items: list[dict],
        stock_name: Optional[str] = None,
        model: str = "gpt-4o-mini",
        max_items: int = 10,
    ) -> list[dict]:
        """
        여러 뉴스 일괄 분석

        Args:
            news_items: 뉴스 리스트 [{"title": ..., "content": ...}, ...]
            stock_name: 종목명
            model: 사용할 모델
            max_items: 최대 분석 건수 (비용 제한)

        Returns:
            분석 결과 리스트
        """
        results = []
        for item in news_items[:max_items]:
            title = item.get("title", "")
            content = item.get("content") or item.get("description")

            analysis = self.analyze_news(
                title=title,
                content=content,
                stock_name=stock_name,
                model=model,
            )

            # 원본 데이터와 분석 결과 병합
            results.append({
                **item,
                "ai_sentiment": analysis.get("sentiment"),
                "ai_impact": analysis.get("impact"),
                "ai_confidence": analysis.get("confidence"),
                "ai_reason": analysis.get("reason"),
            })

        return results

    def summarize_sentiment(
        self,
        news_items: list[dict],
        stock_name: str,
        model: str = "gpt-4o-mini",
    ) -> dict:
        """
        전체 뉴스 감정 요약 분석

        Args:
            news_items: 뉴스 리스트
            stock_name: 종목명
            model: 사용할 모델

        Returns:
            종합 분석 결과
        """
        if not self.is_available:
            return {
                "overall_sentiment": "neutral",
                "confidence": 0.0,
                "summary": "OpenAI API not configured",
                "error": True,
            }

        if not news_items:
            return {
                "overall_sentiment": "neutral",
                "confidence": 0.0,
                "summary": "분석할 뉴스가 없습니다",
            }

        # 뉴스 제목들을 하나의 프롬프트로 구성
        titles = [item.get("title", "") for item in news_items[:15]]
        news_text = "\n".join([f"- {t}" for t in titles])

        summary_prompt = f"""다음은 {stock_name}에 관한 최근 뉴스 제목들입니다:

{news_text}

위 뉴스들을 종합하여 해당 종목에 대한 시장 분위기를 분석해주세요.

반드시 JSON 형식으로만 응답하세요:
{{
    "overall_sentiment": "positive|negative|neutral",
    "confidence": 0.0~1.0,
    "key_themes": ["주요 테마1", "주요 테마2"],
    "summary": "2-3문장 종합 분석"
}}
"""

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "당신은 주식 시장 뉴스를 분석하는 전문 애널리스트입니다."},
                    {"role": "user", "content": summary_prompt},
                ],
                temperature=0.3,
                max_tokens=300,
                response_format={"type": "json_object"},
            )

            result = response.choices[0].message.content
            import json
            return json.loads(result)

        except Exception as e:
            return {
                "overall_sentiment": "neutral",
                "confidence": 0.0,
                "summary": f"분석 실패: {str(e)}",
                "error": True,
            }


# === 편의 함수 ===

_analyzer: Optional[OpenAISentimentAnalyzer] = None


def get_analyzer() -> OpenAISentimentAnalyzer:
    """싱글톤 분석기 반환"""
    global _analyzer
    if _analyzer is None:
        _analyzer = OpenAISentimentAnalyzer()
    return _analyzer


def analyze_single_news(
    title: str,
    content: Optional[str] = None,
    stock_name: Optional[str] = None,
) -> dict:
    """단일 뉴스 감정 분석"""
    return get_analyzer().analyze_news(title, content, stock_name)


def analyze_news_batch(
    news_items: list[dict],
    stock_name: Optional[str] = None,
    max_items: int = 10,
) -> list[dict]:
    """뉴스 일괄 감정 분석"""
    return get_analyzer().analyze_news_batch(news_items, stock_name, max_items=max_items)


def get_sentiment_summary(
    news_items: list[dict],
    stock_name: str,
) -> dict:
    """뉴스 종합 감정 분석"""
    return get_analyzer().summarize_sentiment(news_items, stock_name)


if __name__ == "__main__":
    print("=== OpenAI Sentiment Analyzer 테스트 ===\n")

    analyzer = OpenAISentimentAnalyzer()

    if not analyzer.is_available:
        print("⚠️ OPENAI_API_KEY가 설정되지 않았습니다.")
        print("테스트를 건너뜁니다.")
    else:
        # 테스트 뉴스
        test_news = [
            {"title": "삼성전자, 2분기 영업이익 전년比 50% 증가"},
            {"title": "반도체 업황 회복 본격화...메모리 가격 상승"},
            {"title": "삼성전자, 미국 반도체 보조금 수령 불투명"},
        ]

        print("=== 개별 분석 ===")
        for news in test_news:
            result = analyzer.analyze_news(
                title=news["title"],
                stock_name="삼성전자",
            )
            print(f"\n제목: {news['title']}")
            print(f"감정: {result.get('sentiment')}")
            print(f"영향도: {result.get('impact')}")
            print(f"확신도: {result.get('confidence')}")
            print(f"근거: {result.get('reason')}")

        print("\n\n=== 종합 분석 ===")
        summary = analyzer.summarize_sentiment(test_news, "삼성전자")
        print(f"종합 감정: {summary.get('overall_sentiment')}")
        print(f"확신도: {summary.get('confidence')}")
        print(f"주요 테마: {summary.get('key_themes')}")
        print(f"요약: {summary.get('summary')}")

    print("\n✅ 테스트 완료")

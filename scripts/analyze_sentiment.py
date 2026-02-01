#!/usr/bin/env python3
"""
OpenAI 뉴스 감정분석 스크립트
- 수집된 뉴스에 대해 감정분석 수행
- gpt-4o-mini 사용 (비용 최적화)
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))


SENTIMENT_PROMPT = """다음 주식 관련 뉴스들의 전반적인 감정을 분석해주세요.

종목: {stock_name}
뉴스:
{news_list}

다음 중 하나로 답변해주세요:
- 매우 긍정 (주가 상승에 강하게 긍정적)
- 긍정 (주가에 긍정적)
- 중립 (영향 없음 또는 판단 불가)
- 부정 (주가에 부정적)
- 매우 부정 (주가 하락에 강하게 부정적)

반드시 JSON 형식으로 답변:
{{"sentiment": "감정", "reason": "간단한 이유 (20자 이내)", "confidence": 0.0-1.0}}
"""

SENTIMENT_SCORES = {
    "매우 긍정": 12,
    "긍정": 9,
    "중립": 6,
    "부정": 3,
    "매우 부정": 0,
}


def load_news_data() -> dict:
    """수집된 뉴스 데이터 로드"""
    news_dir = Path(__file__).parent.parent / "data" / "news"
    date_str = datetime.utcnow().strftime("%Y%m%d")
    news_file = news_dir / f"news_{date_str}.json"

    if not news_file.exists():
        # 가장 최근 파일 찾기
        news_files = sorted(news_dir.glob("news_*.json"), reverse=True)
        if news_files:
            news_file = news_files[0]
        else:
            return {}

    with open(news_file, "r", encoding="utf-8") as f:
        return json.load(f)


def analyze_with_openai(stock_name: str, news_items: list[dict]) -> dict:
    """OpenAI로 감정분석"""
    openai_key = os.environ.get("OPENAI_API_KEY")
    if not openai_key:
        return {"sentiment": "중립", "score": 6, "reason": "API 키 없음"}

    try:
        from openai import OpenAI

        client = OpenAI(api_key=openai_key)

        # 뉴스 리스트 포맷팅
        news_text = "\n".join([
            f"- {item['title']}"
            for item in news_items[:5]
        ])

        prompt = SENTIMENT_PROMPT.format(
            stock_name=stock_name,
            news_list=news_text
        )

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "주식 뉴스 감정분석 전문가입니다. JSON 형식으로만 답변합니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=150,
        )

        result_text = response.choices[0].message.content.strip()

        # JSON 파싱
        # ```json 태그 제거
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0]
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0]

        result = json.loads(result_text)
        sentiment = result.get("sentiment", "중립")
        score = SENTIMENT_SCORES.get(sentiment, 6)

        return {
            "sentiment": sentiment,
            "score": score,
            "reason": result.get("reason", ""),
            "confidence": result.get("confidence", 0.5),
        }

    except Exception as e:
        print(f"  OpenAI Error: {e}")
        return {"sentiment": "중립", "score": 6, "reason": f"분석 오류: {str(e)[:20]}"}


def run_sentiment_analysis(news_data: dict) -> dict:
    """전체 종목 감정분석"""
    results = {}

    for code, data in news_data.items():
        stock_name = data.get("stock_name", code)
        news_items = data.get("news", [])

        print(f"  {stock_name}...", end=" ")

        if not news_items:
            result = {"sentiment": "중립", "score": 6, "reason": "뉴스 없음"}
        else:
            result = analyze_with_openai(stock_name, news_items)

        results[code] = result
        print(f"{result['sentiment']} ({result['score']}점)")

    return results


def save_results(results: dict):
    """감정분석 결과 저장"""
    output_dir = Path(__file__).parent.parent / "data" / "sentiment"
    output_dir.mkdir(parents=True, exist_ok=True)

    date_str = datetime.utcnow().strftime("%Y%m%d")
    output_file = output_dir / f"sentiment_{date_str}.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"✅ 감정분석 결과 저장: {output_file}")

    # Supabase 저장
    save_to_supabase(results)


def save_to_supabase(results: dict):
    """Supabase에 감정분석 결과 저장"""
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        return

    try:
        from supabase import create_client

        client = create_client(supabase_url, supabase_key)
        today = datetime.utcnow().strftime("%Y-%m-%d")

        for code, data in results.items():
            # analysis_results 테이블 업데이트
            stock_resp = client.table("stocks").select("id").eq("code", code).execute()
            if stock_resp.data:
                stock_id = stock_resp.data[0]["id"]
                client.table("analysis_results").upsert({
                    "stock_id": stock_id,
                    "analysis_date": today,
                    "sent_news": data["score"],
                }, on_conflict="stock_id,analysis_date").execute()

        print(f"✅ Supabase 업데이트 완료")

    except Exception as e:
        print(f"Supabase error: {e}")


def main():
    print("=" * 50)
    print("🤖 Sentiment Analysis (OpenAI)")
    print("=" * 50)

    news_data = load_news_data()
    if not news_data:
        print("⚠️ No news data found")
        return

    print(f"📰 Loaded news for {len(news_data)} stocks\n")

    results = run_sentiment_analysis(news_data)

    # 요약
    print("\n" + "-" * 30)
    sentiment_counts = {}
    for r in results.values():
        s = r["sentiment"]
        sentiment_counts[s] = sentiment_counts.get(s, 0) + 1

    print("📊 Sentiment Distribution:")
    for sentiment, count in sorted(sentiment_counts.items()):
        print(f"  {sentiment}: {count}개")

    # 저장
    save_results(results)

    # 비용 추정
    print(f"\n💰 예상 비용: ~${len(results) * 0.003:.3f}")
    print("\n✅ Sentiment analysis completed!")


if __name__ == "__main__":
    main()

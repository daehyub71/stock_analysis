#!/usr/bin/env python3
"""
뉴스 수집 스크립트
- 네이버 뉴스 검색 (Google 백업)
- 종목당 최근 뉴스 5개 수집
"""

import os
import sys
import time
import random
from datetime import datetime, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
]


def get_stock_name(stock_code: str) -> str:
    """종목코드 → 종목명 변환"""
    # TODO: Supabase에서 조회
    stock_names = {
        "138040": "메리츠금융지주",
        "005930": "삼성전자",
        "383220": "F&F",
        "259960": "크래프톤",
        "271560": "오리온",
        # ... 나머지 종목
    }
    return stock_names.get(stock_code, stock_code)


def search_naver_news(query: str, count: int = 5) -> list[dict]:
    """네이버 뉴스 검색"""
    url = "https://search.naver.com/search.naver"
    params = {
        "where": "news",
        "query": f"{query} 주식",
        "sort": 1,  # 최신순
    }

    headers = {
        "User-Agent": random.choice(USER_AGENTS),
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        news_items = []
        articles = soup.select("div.news_area")[:count]

        for article in articles:
            title_elem = article.select_one("a.news_tit")
            desc_elem = article.select_one("div.news_dsc")
            date_elem = article.select_one("span.info")

            if title_elem:
                news_items.append({
                    "title": title_elem.get_text(strip=True),
                    "url": title_elem.get("href", ""),
                    "description": desc_elem.get_text(strip=True) if desc_elem else "",
                    "date": date_elem.get_text(strip=True) if date_elem else "",
                })

        return news_items

    except Exception as e:
        print(f"Error: {e}")
        return []


def collect_all_news(stock_codes: list[str]) -> dict:
    """전체 종목 뉴스 수집"""
    results = {}

    for i, code in enumerate(stock_codes):
        stock_name = get_stock_name(code)
        print(f"[{i+1}/{len(stock_codes)}] {stock_name} ({code})...", end=" ")

        news = search_naver_news(stock_name, count=5)
        if news:
            results[code] = {
                "stock_name": stock_name,
                "news": news,
                "collected_at": datetime.utcnow().isoformat(),
            }
            print(f"{len(news)}개 뉴스")
        else:
            print("No news")

        # Rate limit
        time.sleep(random.uniform(1.5, 2.5))

    return results


def save_news_to_supabase(results: dict):
    """뉴스 데이터 Supabase 저장 (또는 임시 파일)"""
    import json

    # 임시로 JSON 파일에 저장
    output_dir = Path(__file__).parent.parent / "data" / "news"
    output_dir.mkdir(parents=True, exist_ok=True)

    date_str = datetime.utcnow().strftime("%Y%m%d")
    output_file = output_dir / f"news_{date_str}.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"✅ 뉴스 저장: {output_file}")


def main():
    print("=" * 50)
    print("📰 News Collection")
    print("=" * 50)

    from collect_daily_prices import get_portfolio_stocks
    stock_codes = get_portfolio_stocks()
    print(f"📋 Target Stocks: {len(stock_codes)}개\n")

    results = collect_all_news(stock_codes)

    print(f"\n📰 Collected news for {len(results)} stocks")
    save_news_to_supabase(results)

    print("\n✅ News collection completed!")


if __name__ == "__main__":
    main()

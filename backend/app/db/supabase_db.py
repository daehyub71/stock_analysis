"""
Supabase Database Manager
- 분석 데이터 저장 (stocks_anal, portfolios_anal, analysis_results_anal 등)
- 클라우드 동기화
- 테이블명: 기존 stocks와 충돌 방지를 위해 _anal 접미사 사용
"""

import os
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

# Supabase 설정
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

_client: Optional[Client] = None


def get_client() -> Client:
    """Supabase 클라이언트 싱글톤"""
    global _client
    if _client is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client


# === Stocks (stocks_anal 테이블) ===

def get_all_stocks(active_only: bool = True) -> list[dict]:
    """전체 종목 조회"""
    client = get_client()
    query = client.table("stocks_anal").select("*")
    if active_only:
        query = query.eq("is_active", True)
    response = query.execute()
    return response.data


def get_stock_by_code(code: str) -> Optional[dict]:
    """종목코드로 조회"""
    client = get_client()
    response = client.table("stocks_anal").select("*").eq("code", code).execute()
    return response.data[0] if response.data else None


def get_stock_id(code: str) -> Optional[int]:
    """종목코드로 ID 조회"""
    stock = get_stock_by_code(code)
    return stock["id"] if stock else None


def upsert_stock(stock_data: dict) -> dict:
    """종목 정보 upsert"""
    client = get_client()
    response = client.table("stocks_anal").upsert(
        stock_data,
        on_conflict="code"
    ).execute()
    return response.data[0] if response.data else {}


def upsert_stocks_bulk(stocks: list[dict]) -> int:
    """종목 정보 대량 upsert"""
    client = get_client()
    response = client.table("stocks_anal").upsert(
        stocks,
        on_conflict="code"
    ).execute()
    return len(response.data)


def delete_stock_by_code(code: str) -> bool:
    """종목코드로 삭제"""
    try:
        client = get_client()
        client.table("stocks_anal").delete().eq("code", code).execute()
        return True
    except Exception as e:
        print(f"❌ Failed to delete stock {code}: {e}")
        return False


def delete_stocks_by_codes(codes: list[str]) -> int:
    """여러 종목 삭제"""
    deleted = 0
    for code in codes:
        if delete_stock_by_code(code):
            deleted += 1
    return deleted


# === Portfolios (portfolios_anal 테이블) ===

def get_portfolios() -> list[dict]:
    """전체 포트폴리오 조회"""
    client = get_client()
    response = client.table("portfolios_anal").select("*").execute()
    return response.data


def get_portfolio_by_id(portfolio_id: int) -> Optional[dict]:
    """포트폴리오 ID로 조회"""
    client = get_client()
    response = client.table("portfolios_anal").select("*").eq("id", portfolio_id).execute()
    return response.data[0] if response.data else None


def get_portfolio_by_name(name: str) -> Optional[dict]:
    """포트폴리오명으로 조회"""
    client = get_client()
    response = client.table("portfolios_anal").select("*").eq("name", name).execute()
    return response.data[0] if response.data else None


def create_portfolio(name: str, source: str = "", report_date: str = "") -> dict:
    """포트폴리오 생성"""
    client = get_client()
    data = {"name": name}
    if source:
        data["source"] = source
    if report_date:
        data["report_date"] = report_date
    response = client.table("portfolios_anal").insert(data).execute()
    return response.data[0] if response.data else {}


def update_portfolio(portfolio_id: int, data: dict) -> dict:
    """포트폴리오 수정"""
    try:
        client = get_client()
        response = client.table("portfolios_anal").update(data).eq("id", portfolio_id).execute()
        return response.data[0] if response.data else {}
    except Exception as e:
        print(f"❌ Failed to update portfolio {portfolio_id}: {e}")
        return {}


def delete_portfolio(portfolio_id: int) -> bool:
    """포트폴리오 삭제 (종목도 함께 삭제)"""
    try:
        client = get_client()
        client.table("portfolio_stocks_anal").delete().eq("portfolio_id", portfolio_id).execute()
        client.table("portfolios_anal").delete().eq("id", portfolio_id).execute()
        return True
    except Exception as e:
        print(f"❌ Failed to delete portfolio {portfolio_id}: {e}")
        return False


# === Portfolio Stocks (portfolio_stocks_anal 테이블) ===

def get_portfolio_stocks(portfolio_id: int) -> list[dict]:
    """포트폴리오 내 종목 조회"""
    client = get_client()
    response = client.table("portfolio_stocks_anal").select(
        "*, stocks_anal(*)"
    ).eq("portfolio_id", portfolio_id).execute()
    return response.data


def upsert_portfolio_stock(data: dict) -> dict:
    """포트폴리오 종목 upsert"""
    client = get_client()
    response = client.table("portfolio_stocks_anal").upsert(
        data,
        on_conflict="portfolio_id,stock_id"
    ).execute()
    return response.data[0] if response.data else {}


def delete_portfolio_stock(portfolio_id: int, stock_id: int) -> bool:
    """포트폴리오에서 종목 제거"""
    try:
        client = get_client()
        client.table("portfolio_stocks_anal").delete().eq(
            "portfolio_id", portfolio_id
        ).eq("stock_id", stock_id).execute()
        return True
    except Exception as e:
        print(f"❌ Failed to delete portfolio stock: {e}")
        return False


def update_portfolio_stock_weight(portfolio_id: int, stock_id: int, weight: float) -> dict:
    """포트폴리오 종목 비중 수정"""
    try:
        client = get_client()
        response = client.table("portfolio_stocks_anal").update({
            "weight": weight
        }).eq("portfolio_id", portfolio_id).eq("stock_id", stock_id).execute()
        return response.data[0] if response.data else {}
    except Exception as e:
        print(f"❌ Failed to update stock weight: {e}")
        return {}


# === Sector Averages (sector_averages_anal 테이블) ===

def get_sector_average(sector: str, base_date: Optional[str] = None) -> Optional[dict]:
    """업종 평균 조회"""
    client = get_client()
    query = client.table("sector_averages_anal").select("*").eq("sector", sector)

    if base_date:
        query = query.eq("base_date", base_date)
    else:
        query = query.order("base_date", desc=True).limit(1)

    response = query.execute()
    return response.data[0] if response.data else None


def upsert_sector_average(data: dict) -> dict:
    """업종 평균 upsert"""
    client = get_client()
    response = client.table("sector_averages_anal").upsert(
        data,
        on_conflict="sector,base_date"
    ).execute()
    return response.data[0] if response.data else {}


# === Analysis Results (analysis_results_anal 테이블) ===

def get_analysis_result(stock_id: int, analysis_date: str) -> Optional[dict]:
    """분석 결과 조회"""
    try:
        client = get_client()
        response = client.table("analysis_results_anal").select("*").eq(
            "stock_id", stock_id
        ).eq("analysis_date", analysis_date).execute()
        return response.data[0] if response.data else None
    except Exception:
        return None


def get_latest_analysis(stock_id: int) -> Optional[dict]:
    """최신 분석 결과 조회"""
    try:
        client = get_client()
        response = client.table("analysis_results_anal").select("*").eq(
            "stock_id", stock_id
        ).order("analysis_date", desc=True).limit(1).execute()
        return response.data[0] if response.data else None
    except Exception:
        return None


def get_analysis_ranking(
    analysis_date: str,
    limit: int = 50,
    min_score: float = 0
) -> list[dict]:
    """점수 순위 조회"""
    try:
        client = get_client()
        response = client.table("analysis_results_anal").select(
            "*, stocks_anal(code, name, sector)"
        ).eq(
            "analysis_date", analysis_date
        ).gte(
            "total_score", min_score
        ).order(
            "total_score", desc=True
        ).limit(limit).execute()
        return response.data
    except Exception:
        return []


def upsert_analysis_result(data: dict) -> dict:
    """분석 결과 upsert"""
    try:
        client = get_client()
        data["created_at"] = datetime.utcnow().isoformat()
        response = client.table("analysis_results_anal").upsert(
            data,
            on_conflict="stock_id,analysis_date"
        ).execute()
        return response.data[0] if response.data else {}
    except Exception as e:
        print(f"❌ Failed to upsert analysis result: {e}")
        return {}


def upsert_analysis_results_bulk(results: list[dict]) -> int:
    """분석 결과 대량 upsert"""
    try:
        client = get_client()
        now = datetime.utcnow().isoformat()
        for result in results:
            result["created_at"] = now
        response = client.table("analysis_results_anal").upsert(
            results,
            on_conflict="stock_id,analysis_date"
        ).execute()
        return len(response.data)
    except Exception as e:
        print(f"❌ Failed to upsert analysis results: {e}")
        return 0


# === News Ratings (news_ratings_anal 테이블) ===

def get_news_ratings(stock_id: int, rated_only: bool = False) -> list[dict]:
    """종목의 뉴스 목록 조회"""
    try:
        client = get_client()
        query = client.table("news_ratings_anal").select("*").eq("stock_id", stock_id)
        if rated_only:
            query = query.eq("is_rated", True)
        response = query.order("news_date", desc=True).execute()
        return response.data
    except Exception as e:
        print(f"❌ Failed to get news ratings: {e}")
        return []


def get_unrated_news(stock_id: int) -> list[dict]:
    """평점 미완료 뉴스 조회"""
    try:
        client = get_client()
        response = client.table("news_ratings_anal").select("*").eq(
            "stock_id", stock_id
        ).eq("is_rated", False).order("news_date", desc=True).execute()
        return response.data
    except Exception as e:
        print(f"❌ Failed to get unrated news: {e}")
        return []


def upsert_news_item(data: dict) -> dict:
    """뉴스 아이템 upsert"""
    try:
        client = get_client()
        data["updated_at"] = datetime.utcnow().isoformat()
        response = client.table("news_ratings_anal").upsert(
            data,
            on_conflict="stock_id,title"
        ).execute()
        return response.data[0] if response.data else {}
    except Exception as e:
        print(f"❌ Failed to upsert news item: {e}")
        return {}


def upsert_news_items_bulk(items: list[dict]) -> int:
    """뉴스 아이템 대량 upsert"""
    try:
        client = get_client()
        now = datetime.utcnow().isoformat()
        for item in items:
            item["updated_at"] = now
        response = client.table("news_ratings_anal").upsert(
            items,
            on_conflict="stock_id,title"
        ).execute()
        return len(response.data)
    except Exception as e:
        print(f"❌ Failed to upsert news items: {e}")
        return 0


def update_news_rating(news_id: int, rating: int) -> dict:
    """뉴스 평점 업데이트"""
    try:
        client = get_client()
        response = client.table("news_ratings_anal").update({
            "rating": rating,
            "is_rated": True,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", news_id).execute()
        return response.data[0] if response.data else {}
    except Exception as e:
        print(f"❌ Failed to update news rating: {e}")
        return {}


def calculate_sentiment_from_ratings(stock_id: int) -> dict:
    """평점 기반 감정 점수 계산 (20점 만점)"""
    try:
        client = get_client()
        response = client.table("news_ratings_anal").select("rating").eq(
            "stock_id", stock_id
        ).eq("is_rated", True).neq("rating", 0).execute()  # 0점은 무관 뉴스

        if not response.data:
            return {"score": 10.0, "avg_rating": 0, "rated_count": 0}  # 기본값: 중간점수

        ratings = [item["rating"] for item in response.data]
        avg_rating = sum(ratings) / len(ratings)  # -10 ~ +10

        # -10~+10 → 0~20점 변환
        score = (avg_rating + 10) * 1.0  # -10→0, 0→10, +10→20

        return {
            "score": round(score, 2),
            "avg_rating": round(avg_rating, 2),
            "rated_count": len(ratings)
        }
    except Exception as e:
        print(f"❌ Failed to calculate sentiment: {e}")
        return {"score": 10.0, "avg_rating": 0, "rated_count": 0}


def delete_old_news(stock_id: int, days: int = 60) -> int:
    """오래된 뉴스 삭제 (기본 60일)"""
    try:
        from datetime import timedelta
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
        client = get_client()
        response = client.table("news_ratings_anal").delete().eq(
            "stock_id", stock_id
        ).lt("news_date", cutoff_date).execute()
        return len(response.data)
    except Exception as e:
        print(f"❌ Failed to delete old news: {e}")
        return 0


# === Analysis History & Score Changes ===

def get_analysis_history(stock_id: int, days: int = 30) -> list[dict]:
    """분석 결과 히스토리 조회 (최근 N일)"""
    try:
        from datetime import timedelta
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
        client = get_client()
        response = client.table("analysis_results_anal").select(
            "analysis_date, total_score, tech_total, fund_total, sent_total, grade"
        ).eq(
            "stock_id", stock_id
        ).gte(
            "analysis_date", cutoff_date
        ).order("analysis_date", desc=False).execute()
        return response.data
    except Exception as e:
        print(f"❌ Failed to get analysis history: {e}")
        return []


def get_score_changes(threshold: float = 5.0) -> list[dict]:
    """
    전일 대비 점수 변화 감지

    Returns: [{stock_code, stock_name, prev_score, curr_score, change, grade}]
    """
    try:
        client = get_client()

        # 최근 2일의 분석 결과 조회 (모든 종목)
        from datetime import timedelta
        today = datetime.utcnow().strftime("%Y-%m-%d")
        two_days_ago = (datetime.utcnow() - timedelta(days=2)).strftime("%Y-%m-%d")

        response = client.table("analysis_results_anal").select(
            "stock_id, analysis_date, total_score, grade, stocks_anal(code, name)"
        ).gte(
            "analysis_date", two_days_ago
        ).order("analysis_date", desc=True).execute()

        if not response.data:
            return []

        # stock_id별로 그룹핑
        by_stock: dict[int, list[dict]] = {}
        for row in response.data:
            sid = row["stock_id"]
            if sid not in by_stock:
                by_stock[sid] = []
            by_stock[sid].append(row)

        changes = []
        for sid, rows in by_stock.items():
            if len(rows) < 2:
                continue
            curr = rows[0]  # 최신
            prev = rows[1]  # 전일
            change = curr["total_score"] - prev["total_score"]
            if abs(change) >= threshold:
                stock_info = curr.get("stocks_anal") or {}
                changes.append({
                    "stockCode": stock_info.get("code", ""),
                    "stockName": stock_info.get("name", ""),
                    "prevScore": round(prev["total_score"], 1),
                    "currScore": round(curr["total_score"], 1),
                    "change": round(change, 1),
                    "grade": curr.get("grade", ""),
                    "date": curr.get("analysis_date", ""),
                })

        # 변화량 절대값 기준 정렬
        changes.sort(key=lambda x: abs(x["change"]), reverse=True)
        return changes

    except Exception as e:
        print(f"❌ Failed to get score changes: {e}")
        return []


# === Utility ===

def check_connection() -> bool:
    """연결 확인"""
    try:
        client = get_client()
        # 간단한 쿼리로 연결 테스트
        client.table("stocks_anal").select("id").limit(1).execute()
        return True
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return False


if __name__ == "__main__":
    if check_connection():
        print("✅ Supabase connection successful")
        stocks = get_all_stocks()
        print(f"📊 Total stocks: {len(stocks)}")
    else:
        print("❌ Supabase connection failed")

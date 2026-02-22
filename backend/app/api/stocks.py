"""
Stocks API
- 종목 리스트 조회
- 종목 상세 조회
- 주가 히스토리
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Query, HTTPException

from app.db import supabase_db, sqlite_db

router = APIRouter()


@router.get("")
async def get_stocks(
    sector: Optional[str] = Query(None, description="업종 필터"),
    market: Optional[str] = Query(None, description="시장 (KOSPI/KOSDAQ)"),
    min_score: Optional[float] = Query(None, ge=0, le=100, description="최소 점수"),
    max_score: Optional[float] = Query(None, ge=0, le=100, description="최대 점수"),
    grades: Optional[str] = Query(None, description="등급 (쉼표 구분: A+,A,B+)"),
    exclude_loss: bool = Query(False, description="적자 기업 제외"),
    search: Optional[str] = Query(None, description="검색어 (종목명, 코드)"),
    sort_field: str = Query("totalScore", description="정렬 필드"),
    sort_dir: str = Query("desc", description="정렬 방향"),
    page: int = Query(1, ge=1, description="페이지"),
    page_size: int = Query(20, ge=1, le=100, description="페이지 크기"),
):
    """
    종목 리스트 조회

    - 필터링, 정렬, 페이지네이션 지원
    - 분석 결과 포함
    """
    try:
        # Supabase에서 종목 + 분석결과 조회
        # 실제 구현에서는 Supabase RPC 또는 조인 쿼리 사용
        stocks = supabase_db.get_all_stocks()

        # 필터링
        if sector:
            stocks = [s for s in stocks if s.get("sector") == sector]

        if market and market != "all":
            stocks = [s for s in stocks if s.get("market") == market]

        if search:
            search_lower = search.lower()
            stocks = [
                s for s in stocks
                if search_lower in s.get("name", "").lower()
                or search_lower in s.get("code", "").lower()
            ]

        # 분석 결과 매핑 (실제로는 조인으로 처리)
        today = datetime.now().strftime("%Y-%m-%d")
        results = []
        for stock in stocks:
            stock_id = stock.get("id")
            code = stock.get("code", "")
            analysis = supabase_db.get_latest_analysis(stock_id) if stock_id else None

            # 점수 필터
            if analysis:
                score = analysis.get("total_score", 0)
                if min_score and score < min_score:
                    continue
                if max_score and score > max_score:
                    continue

                grade = analysis.get("grade", "F")
                if grades:
                    grade_list = [g.strip() for g in grades.split(",")]
                    if grade not in grade_list:
                        continue

            # 현재가 및 등락률 조회 (SQLite)
            current_price = None
            price_change = None
            price_change_rate = None

            prices = sqlite_db.get_prices(code, limit=2)
            if prices and len(prices) >= 1:
                current_price = prices[0].get("close_price")
                if len(prices) >= 2:
                    prev_close = prices[1].get("close_price", 0)
                    if prev_close > 0:
                        price_change = current_price - prev_close
                        price_change_rate = round((price_change / prev_close) * 100, 2)

            results.append({
                **stock,
                "currentPrice": current_price,
                "priceChange": price_change,
                "priceChangeRate": price_change_rate,
                "analysis": _format_analysis(analysis, code, stock.get("name", "")),
            })

        # 정렬
        def get_sort_key(item):
            if sort_field == "totalScore":
                return item.get("analysis", {}).get("totalScore", 0)
            elif sort_field == "name":
                return item.get("name", "")
            elif sort_field == "sector":
                return item.get("sector", "") or ""
            elif sort_field == "priceChangeRate":
                return item.get("price_change_rate", 0) or 0
            return 0

        results.sort(key=get_sort_key, reverse=(sort_dir == "desc"))

        # 페이지네이션
        total = len(results)
        total_pages = (total + page_size - 1) // page_size
        start = (page - 1) * page_size
        end = start + page_size
        paginated = results[start:end]

        return {
            "items": paginated,
            "total": total,
            "page": page,
            "pageSize": page_size,
            "totalPages": total_pages,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sectors")
async def get_sectors():
    """업종 목록 조회"""
    try:
        stocks = supabase_db.get_all_stocks()
        sectors = set()
        for stock in stocks:
            sector = stock.get("sector")
            if sector:
                sectors.add(sector)
        return sorted(list(sectors))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compare")
async def compare_stocks(
    codes: str = Query(..., description="종목코드 (쉼표 구분, 최대 5개)"),
):
    """종목 비교"""
    try:
        code_list = [c.strip() for c in codes.split(",")][:5]
        results = []

        for code in code_list:
            stock = supabase_db.get_stock_by_code(code)
            if stock:
                stock_id = stock.get("id")
                analysis = supabase_db.get_latest_analysis(stock_id) if stock_id else None
                results.append({
                    **stock,
                    "analysis": _format_analysis(analysis, code, stock.get("name", "")),
                })

        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{code}")
async def get_stock(code: str):
    """종목 상세 조회"""
    try:
        stock = supabase_db.get_stock_by_code(code)
        if not stock:
            raise HTTPException(status_code=404, detail=f"Stock not found: {code}")

        # 최신 가격 조회
        latest_price = sqlite_db.get_latest_price(code)
        if latest_price:
            stock["currentPrice"] = latest_price.get("close_price")
            # 등락률 계산 (전일 대비)
            prices = sqlite_db.get_prices(code, limit=2)
            if len(prices) >= 2:
                prev_close = prices[1].get("close_price", 0)
                if prev_close > 0:
                    change = latest_price.get("close_price", 0) - prev_close
                    stock["priceChange"] = change
                    stock["priceChangeRate"] = (change / prev_close) * 100

        return stock
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{code}/overview")
async def get_company_overview(code: str):
    """종목 기업개요 조회 (네이버 증권 크롤링)"""
    try:
        from app.collectors.naver_finance import get_company_overview as crawl_overview

        data = crawl_overview(code)
        overview = data.get("overview", [])

        if not overview:
            raise HTTPException(status_code=404, detail=f"No overview data for: {code}")

        stock = supabase_db.get_stock_by_code(code)
        return {
            "stockCode": code,
            "stockName": stock.get("name", "") if stock else "",
            "overview": overview,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{code}/history")
async def get_price_history(
    code: str,
    days: int = Query(365, ge=1, le=3650, description="조회 기간 (일)"),
):
    """주가 히스토리 조회"""
    try:
        prices = sqlite_db.get_prices(code, limit=days)
        if not prices:
            raise HTTPException(status_code=404, detail=f"No price data for: {code}")

        return [
            {
                "date": p.get("date"),
                "open": p.get("open_price"),
                "high": p.get("high_price"),
                "low": p.get("low_price"),
                "close": p.get("close_price"),
                "volume": p.get("volume"),
            }
            for p in prices
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _format_analysis(analysis: dict, code: str = "", name: str = "") -> dict:
    """분석 결과를 API 응답 형식으로 변환"""
    if not analysis:
        return _empty_analysis(code)

    # DB 테이블 컬럼 형식 (analysis_results_anal)
    return {
        "stockCode": code,
        "stockName": name,
        "analysisDate": analysis.get("analysis_date", ""),
        "totalScore": analysis.get("total_score", 0),
        "maxScore": 100,
        "grade": analysis.get("grade", "F"),
        "scoreBreakdown": {
            "technical": {
                "score": analysis.get("tech_total", 0),
                "max": 30,
                "weight": "30%",
            },
            "fundamental": {
                "score": analysis.get("fund_total", 0),
                "max": 50,
                "weight": "50%",
            },
            "sentiment": {
                "score": analysis.get("sent_total", 0),
                "max": 20,
                "weight": "20%",
            },
        },
    }


def _empty_analysis(code: str) -> dict:
    """빈 분석 결과 생성"""
    return {
        "stockCode": code,
        "stockName": "",
        "analysisDate": datetime.now().strftime("%Y-%m-%d"),
        "totalScore": 0,
        "maxScore": 100,
        "grade": "F",
        "scoreBreakdown": {
            "technical": {"score": 0, "max": 30, "weight": "30%"},
            "fundamental": {"score": 0, "max": 50, "weight": "50%"},
            "sentiment": {"score": 0, "max": 20, "weight": "20%"},
        },
        "details": {},
    }

"""
Portfolios API
- 포트폴리오 CRUD
- 종목 추가/제거/비중 조절
- 포트폴리오 점수 계산
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.db import supabase_db

router = APIRouter()


class PortfolioCreateRequest(BaseModel):
    """포트폴리오 생성 요청"""
    name: str
    source: str = ""
    report_date: str = ""


class PortfolioUpdateRequest(BaseModel):
    """포트폴리오 수정 요청"""
    name: Optional[str] = None
    source: Optional[str] = None


class AddStockRequest(BaseModel):
    """종목 추가 요청"""
    stock_code: str


class UpdateWeightRequest(BaseModel):
    """비중 수정 요청"""
    weight: float


@router.get("")
async def get_portfolios():
    """포트폴리오 목록 조회"""
    try:
        portfolios = supabase_db.get_portfolios()

        # 각 포트폴리오에 종목 수 추가
        results = []
        for p in portfolios:
            stocks = supabase_db.get_portfolio_stocks(p["id"])
            results.append({
                **p,
                "stock_count": len(stocks),
            })

        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("")
async def create_portfolio(request: PortfolioCreateRequest):
    """포트폴리오 생성"""
    try:
        portfolio = supabase_db.create_portfolio(
            name=request.name,
            source=request.source,
            report_date=request.report_date,
        )
        if not portfolio:
            raise HTTPException(status_code=500, detail="포트폴리오 생성 실패")
        return portfolio
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{portfolio_id}")
async def get_portfolio_detail(portfolio_id: int):
    """포트폴리오 상세 조회 (종목 리스트 + 분석점수 포함)"""
    try:
        portfolio = supabase_db.get_portfolio_by_id(portfolio_id)
        if not portfolio:
            raise HTTPException(status_code=404, detail="포트폴리오를 찾을 수 없습니다")

        # 종목 리스트 조회 (stocks_anal 조인)
        raw_stocks = supabase_db.get_portfolio_stocks(portfolio_id)

        stocks = []
        for ps in raw_stocks:
            stock_info = ps.get("stocks_anal") or {}
            stock_id = ps.get("stock_id")
            code = stock_info.get("code", "")
            name = stock_info.get("name", "")

            # 최신 분석 결과 조회
            analysis = supabase_db.get_latest_analysis(stock_id) if stock_id else None

            stocks.append({
                "stock_code": code,
                "stock_name": name,
                "sector": stock_info.get("sector", ""),
                "weight": float(ps.get("weight") or 0),
                "quantity": ps.get("quantity"),
                "amount": ps.get("amount"),
                "total_score": analysis.get("total_score", 0) if analysis else 0,
                "grade": analysis.get("grade", "F") if analysis else "F",
                "tech_total": analysis.get("tech_total", 0) if analysis else 0,
                "fund_total": analysis.get("fund_total", 0) if analysis else 0,
                "sent_total": analysis.get("sent_total", 0) if analysis else 0,
            })

        # 통계 계산
        scores = [s["total_score"] for s in stocks if s["total_score"] > 0]
        avg_score = sum(scores) / len(scores) if scores else 0

        # 업종 분포
        sector_dist: dict[str, int] = {}
        for s in stocks:
            sector = s.get("sector") or "기타"
            sector_dist[sector] = sector_dist.get(sector, 0) + 1

        return {
            **portfolio,
            "stocks": stocks,
            "stock_count": len(stocks),
            "avg_score": round(avg_score, 1),
            "sector_distribution": sector_dist,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{portfolio_id}")
async def update_portfolio(portfolio_id: int, request: PortfolioUpdateRequest):
    """포트폴리오 수정"""
    try:
        portfolio = supabase_db.get_portfolio_by_id(portfolio_id)
        if not portfolio:
            raise HTTPException(status_code=404, detail="포트폴리오를 찾을 수 없습니다")

        update_data = {}
        if request.name is not None:
            update_data["name"] = request.name
        if request.source is not None:
            update_data["source"] = request.source

        if not update_data:
            return portfolio

        result = supabase_db.update_portfolio(portfolio_id, update_data)
        return result if result else portfolio
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{portfolio_id}")
async def delete_portfolio(portfolio_id: int):
    """포트폴리오 삭제"""
    try:
        portfolio = supabase_db.get_portfolio_by_id(portfolio_id)
        if not portfolio:
            raise HTTPException(status_code=404, detail="포트폴리오를 찾을 수 없습니다")

        success = supabase_db.delete_portfolio(portfolio_id)
        if not success:
            raise HTTPException(status_code=500, detail="포트폴리오 삭제 실패")

        return {"message": "포트폴리오가 삭제되었습니다", "id": portfolio_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{portfolio_id}/stocks")
async def add_stock_to_portfolio(portfolio_id: int, request: AddStockRequest):
    """포트폴리오에 종목 추가"""
    try:
        portfolio = supabase_db.get_portfolio_by_id(portfolio_id)
        if not portfolio:
            raise HTTPException(status_code=404, detail="포트폴리오를 찾을 수 없습니다")

        # 종목코드 → stock_id 변환
        stock = supabase_db.get_stock_by_code(request.stock_code)
        if not stock:
            raise HTTPException(status_code=404, detail=f"종목을 찾을 수 없습니다: {request.stock_code}")

        result = supabase_db.upsert_portfolio_stock({
            "portfolio_id": portfolio_id,
            "stock_id": stock["id"],
            "weight": 0,
        })

        return {
            "portfolio_id": portfolio_id,
            "stock_code": request.stock_code,
            "stock_name": stock.get("name", ""),
            "message": "종목이 추가되었습니다",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{portfolio_id}/stocks/{stock_code}")
async def remove_stock_from_portfolio(portfolio_id: int, stock_code: str):
    """포트폴리오에서 종목 제거"""
    try:
        stock = supabase_db.get_stock_by_code(stock_code)
        if not stock:
            raise HTTPException(status_code=404, detail=f"종목을 찾을 수 없습니다: {stock_code}")

        success = supabase_db.delete_portfolio_stock(portfolio_id, stock["id"])
        if not success:
            raise HTTPException(status_code=500, detail="종목 제거 실패")

        return {
            "portfolio_id": portfolio_id,
            "stock_code": stock_code,
            "message": "종목이 제거되었습니다",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{portfolio_id}/stocks/{stock_code}/weight")
async def update_stock_weight(
    portfolio_id: int,
    stock_code: str,
    request: UpdateWeightRequest,
):
    """종목 비중 수정"""
    try:
        stock = supabase_db.get_stock_by_code(stock_code)
        if not stock:
            raise HTTPException(status_code=404, detail=f"종목을 찾을 수 없습니다: {stock_code}")

        result = supabase_db.update_portfolio_stock_weight(
            portfolio_id, stock["id"], request.weight
        )
        if not result:
            raise HTTPException(status_code=500, detail="비중 수정 실패")

        return {
            "portfolio_id": portfolio_id,
            "stock_code": stock_code,
            "weight": request.weight,
            "message": "비중이 수정되었습니다",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{portfolio_id}/score")
async def get_portfolio_score(portfolio_id: int):
    """포트폴리오 종합 점수"""
    try:
        portfolio = supabase_db.get_portfolio_by_id(portfolio_id)
        if not portfolio:
            raise HTTPException(status_code=404, detail="포트폴리오를 찾을 수 없습니다")

        raw_stocks = supabase_db.get_portfolio_stocks(portfolio_id)

        scores = []
        for ps in raw_stocks:
            stock_id = ps.get("stock_id")
            analysis = supabase_db.get_latest_analysis(stock_id) if stock_id else None
            if analysis:
                scores.append({
                    "stock_id": stock_id,
                    "total_score": analysis.get("total_score", 0),
                    "grade": analysis.get("grade", "F"),
                    "weight": float(ps.get("weight") or 0),
                })

        if not scores:
            return {
                "portfolio_id": portfolio_id,
                "avg_score": 0,
                "weighted_score": 0,
                "max_score": 0,
                "min_score": 0,
                "stock_count": 0,
            }

        total_scores = [s["total_score"] for s in scores]
        avg_score = sum(total_scores) / len(total_scores)

        # 가중 평균 점수 (비중이 설정된 경우)
        total_weight = sum(s["weight"] for s in scores)
        if total_weight > 0:
            weighted_score = sum(
                s["total_score"] * s["weight"] for s in scores
            ) / total_weight
        else:
            weighted_score = avg_score

        return {
            "portfolio_id": portfolio_id,
            "avg_score": round(avg_score, 1),
            "weighted_score": round(weighted_score, 1),
            "max_score": round(max(total_scores), 1),
            "min_score": round(min(total_scores), 1),
            "stock_count": len(scores),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

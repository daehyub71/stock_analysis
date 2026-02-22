"""
Backtest API
- 백테스트 실행 및 결과 조회
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.db import supabase_db, sqlite_db
from app.services.backtesting import BacktestEngine, BacktestParams

router = APIRouter()


class BacktestRequest(BaseModel):
    start_date: str = Field(..., description="시작일 (YYYY-MM-DD)")
    end_date: str = Field(..., description="종료일 (YYYY-MM-DD)")
    initial_capital: int = Field(10_000_000, ge=1_000_000, le=1_000_000_000, description="초기 투자금")
    buy_threshold: float = Field(20.0, ge=5.0, le=30.0, description="매수 기준 (기술분석 점수)")
    sell_threshold: float = Field(12.0, ge=0.0, le=30.0, description="매도 기준 (기술분석 점수)")


@router.post("/{code}/run")
async def run_backtest(code: str, request: BacktestRequest):
    """
    백테스트 실행

    기술분석 점수 기반 매수/매도 시뮬레이션
    - buy_threshold: 점수가 이 값 이상이면 매수 (기술분석 30점 기준)
    - sell_threshold: 점수가 이 값 미만이면 매도
    """
    try:
        # 종목 확인
        stock = supabase_db.get_stock_by_code(code)
        if not stock:
            raise HTTPException(status_code=404, detail=f"Stock not found: {code}")

        # 가격 데이터 존재 확인
        date_range = sqlite_db.get_date_range(code)
        if not date_range or not date_range[0]:
            raise HTTPException(status_code=400, detail="No price data available for this stock")

        # 유효성 검증
        if request.sell_threshold >= request.buy_threshold:
            raise HTTPException(
                status_code=400,
                detail="sell_threshold must be less than buy_threshold"
            )

        # 백테스트 실행
        params = BacktestParams(
            stock_code=code,
            start_date=request.start_date,
            end_date=request.end_date,
            initial_capital=request.initial_capital,
            buy_threshold=request.buy_threshold,
            sell_threshold=request.sell_threshold,
        )

        engine = BacktestEngine(params)
        result = engine.run()

        # 매매 기록 직렬화
        trades = []
        for t in result.trades:
            trade_dict = {
                "type": t.type,
                "date": t.date,
                "price": t.price,
                "shares": t.shares,
                "score": t.score,
                "portfolioValue": t.portfolio_value,
            }
            if t.profit is not None:
                trade_dict["profit"] = t.profit
                trade_dict["profitPct"] = t.profit_pct
            trades.append(trade_dict)

        return {
            "stockCode": code,
            "stockName": stock.get("name", ""),
            "params": {
                "startDate": request.start_date,
                "endDate": request.end_date,
                "initialCapital": request.initial_capital,
                "buyThreshold": request.buy_threshold,
                "sellThreshold": request.sell_threshold,
            },
            "dailyData": result.daily_data,
            "trades": trades,
            "metrics": {
                "totalReturn": result.total_return_pct,
                "annualizedReturn": result.annualized_return_pct,
                "maxDrawdown": result.max_drawdown_pct,
                "sharpeRatio": result.sharpe_ratio,
                "winRate": result.win_rate,
                "tradeCount": result.trade_count,
                "finalValue": result.final_value,
                "tradingDays": result.trading_days,
            },
            "benchmark": {
                "buyHoldReturn": result.buy_hold_return_pct,
            },
        }

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{code}/date-range")
async def get_available_date_range(code: str):
    """백테스트 가능 기간 조회"""
    try:
        stock = supabase_db.get_stock_by_code(code)
        if not stock:
            raise HTTPException(status_code=404, detail=f"Stock not found: {code}")

        date_range = sqlite_db.get_date_range(code)
        if not date_range or not date_range[0]:
            raise HTTPException(status_code=400, detail="No price data available")

        return {
            "stockCode": code,
            "stockName": stock.get("name", ""),
            "startDate": date_range[0],
            "endDate": date_range[1],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

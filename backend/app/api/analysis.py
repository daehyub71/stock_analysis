"""
Analysis API
- 분석 결과 조회
- 분석 실행
- 순위 조회
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Query, HTTPException, BackgroundTasks

from app.db import supabase_db
from app.services.scoring import calculate_stock_score, batch_stock_score, get_stock_ranking
from app.analyzers.indicators import calculate_indicators
from app.services.sentiment import SentimentAnalyzer
from app.services.commentary import get_commentary_service
from app.collectors.news_collector import get_collector as get_news_collector

router = APIRouter()


@router.get("/ranking")
async def get_analysis_ranking(
    date: Optional[str] = Query(None, description="분석 날짜 (YYYY-MM-DD)"),
    limit: int = Query(50, ge=1, le=100, description="조회 건수"),
    min_score: float = Query(0, ge=0, le=100, description="최소 점수"),
):
    """
    분석 순위 조회

    점수 기준 상위 종목 반환
    """
    try:
        analysis_date = date or datetime.now().strftime("%Y-%m-%d")
        results = get_stock_ranking(
            analysis_date=analysis_date,
            limit=limit,
            min_score=min_score,
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{code}")
async def get_analysis(code: str):
    """종목 분석 결과 조회"""
    try:
        stock = supabase_db.get_stock_by_code(code)
        if not stock:
            raise HTTPException(status_code=404, detail=f"Stock not found: {code}")

        stock_id = stock.get("id")
        analysis = supabase_db.get_latest_analysis(stock_id)

        if not analysis:
            # 분석 결과가 없으면 실시간 계산
            result = calculate_stock_score(code, stock.get("name"))
            return _format_analysis_result(result, stock)

        return _format_analysis_result(analysis, stock)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{code}/history")
async def get_analysis_history(
    code: str,
    days: int = Query(30, ge=1, le=365, description="조회 기간 (일)"),
):
    """분석 히스토리 조회"""
    try:
        stock = supabase_db.get_stock_by_code(code)
        if not stock:
            raise HTTPException(status_code=404, detail=f"Stock not found: {code}")

        stock_id = stock.get("id")
        history_data = supabase_db.get_analysis_history(stock_id, days)

        if not history_data:
            return []

        return [
            {
                "date": row.get("analysis_date", ""),
                "score": round(row.get("total_score", 0), 1),
                "techScore": round(row.get("tech_total", 0), 1),
                "fundScore": round(row.get("fund_total", 0), 1),
                "sentScore": round(row.get("sent_total", 0), 1),
                "grade": row.get("grade", ""),
            }
            for row in history_data
        ]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{code}/run")
async def run_analysis(code: str, background_tasks: BackgroundTasks):
    """
    종목 분석 실행

    분석 결과를 계산하고 저장
    """
    try:
        stock = supabase_db.get_stock_by_code(code)
        if not stock:
            raise HTTPException(status_code=404, detail=f"Stock not found: {code}")

        # 분석 실행
        result = calculate_stock_score(
            stock_code=code,
            stock_name=stock.get("name"),
            save=True,
        )

        return _format_analysis_result(result, stock)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch")
async def run_batch_analysis(background_tasks: BackgroundTasks):
    """
    일괄 분석 실행

    모든 종목에 대해 분석 수행
    """
    try:
        stocks = supabase_db.get_all_stocks()

        # 백그라운드에서 실행
        def run_batch():
            stock_list = [
                {"code": s.get("code"), "name": s.get("name")}
                for s in stocks
            ]
            batch_stock_score(stock_list, save=True)

        background_tasks.add_task(run_batch)

        return {
            "message": "Batch analysis started",
            "count": len(stocks),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{code}/commentary")
async def get_analysis_commentary(code: str):
    """
    LLM 분석 코멘터리 조회

    분석 결과를 바탕으로 인간 친화적인 해설 생성
    """
    try:
        stock = supabase_db.get_stock_by_code(code)
        if not stock:
            raise HTTPException(status_code=404, detail=f"Stock not found: {code}")

        stock_id = stock.get("id")
        stock_name = stock.get("name", "")

        # 분석 결과 조회
        analysis = supabase_db.get_latest_analysis(stock_id)
        if not analysis:
            # 분석 결과가 없으면 실시간 계산
            analysis = calculate_stock_score(code, stock_name)

        # 기술지표 계산
        indicators = {}
        try:
            raw_indicators = calculate_indicators(code)
            if raw_indicators.get("has_data"):
                indicators = {
                    "currentPrice": raw_indicators.get("current_price"),
                    "ma5": raw_indicators.get("ma5"),
                    "ma20": raw_indicators.get("ma20"),
                    "ma60": raw_indicators.get("ma60"),
                    "ma120": raw_indicators.get("ma120"),
                    "rsi14": raw_indicators.get("rsi14"),
                    "macd": raw_indicators.get("macd"),
                    "macdSignal": raw_indicators.get("macd_signal"),
                    "macdHist": raw_indicators.get("macd_hist"),
                }
        except Exception:
            pass

        # 재무 데이터
        financials = {
            "per": stock.get("per"),
            "pbr": stock.get("pbr"),
            "psr": stock.get("psr"),
            "roe": stock.get("roe"),
            "revenueGrowth": stock.get("revenue_growth"),
            "opGrowth": stock.get("op_growth"),
            "opMargin": stock.get("op_margin"),
            "debtRatio": stock.get("debt_ratio"),
            "currentRatio": stock.get("current_ratio"),
        }

        # 점수 추출
        total_score = analysis.get("total_score", 0)
        tech_score = analysis.get("tech_total", 0)
        fund_score = analysis.get("fund_total", 0)
        sent_score = analysis.get("sent_total", 0)
        grade = analysis.get("grade", "F")

        # 상세 점수
        tech_details = {
            "maArrangement": {"score": analysis.get("tech_ma_arrangement", 0), "description": "이동평균선 정배열"},
            "maDivergence": {"score": analysis.get("tech_ma_divergence", 0), "description": "이평선 이격도"},
            "rsi": {"score": analysis.get("tech_rsi", 0), "description": "RSI"},
            "macd": {"score": analysis.get("tech_macd", 0), "description": "MACD"},
            "volume": {"score": analysis.get("tech_volume", 0), "description": "거래량"},
        }

        fund_details = {
            "per": {"score": analysis.get("fund_per", 0)},
            "pbr": {"score": analysis.get("fund_pbr", 0)},
            "psr": {"score": analysis.get("fund_psr", 0)},
            "revenueGrowth": {"score": analysis.get("fund_revenue_growth", 0)},
            "opGrowth": {"score": analysis.get("fund_profit_growth", 0)},
            "roe": {"score": analysis.get("fund_roe", 0)},
            "opMargin": {"score": analysis.get("fund_margin", 0)},
            "debtRatio": {"score": analysis.get("fund_debt_ratio", 0)},
            "currentRatio": {"score": analysis.get("fund_current_ratio", 0)},
        }

        sent_details = {
            "sentiment": {"score": analysis.get("sent_news", 0) * 0.67},
            "impact": {"score": analysis.get("sent_news", 0) * 0.33},
            "volume": {"score": analysis.get("sent_trend", 0)},
        }

        # 코멘터리 생성
        commentary_service = get_commentary_service()
        commentary = commentary_service.generate_summary(
            stock_name=stock_name,
            stock_code=code,
            total_score=total_score,
            grade=grade,
            tech_score=tech_score,
            fund_score=fund_score,
            sent_score=sent_score,
            tech_details=tech_details,
            fund_details=fund_details,
            sent_details=sent_details,
            indicators=indicators,
            financials=financials,
        )

        return {
            "stockCode": code,
            "stockName": stock_name,
            "totalScore": total_score,
            "grade": grade,
            "commentary": commentary,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _get_sentiment_source(stock_id: int) -> tuple[str, dict]:
    """
    감정분석 출처 및 점수 확인

    Returns:
        (source, score_info): source는 "manual" 또는 "auto"
    """
    manual_score = supabase_db.calculate_sentiment_from_ratings(stock_id)
    if manual_score.get("rated_count", 0) > 0:
        return "manual", manual_score
    return "auto", manual_score


def _format_analysis_result(result: dict, stock: dict = None) -> dict:
    """분석 결과를 API 응답 형식으로 변환

    Args:
        result: 분석 결과 dict
        stock: 종목 정보 dict (재무 데이터 포함)
    """
    # 이미 올바른 형식이면 그대로 반환
    if "scoreBreakdown" in result:
        return result

    # stock 데이터에서 실제 재무 값 추출
    financials = {}
    if stock:
        financials = {
            "per": stock.get("per"),
            "pbr": stock.get("pbr"),
            "psr": stock.get("psr"),
            "roe": stock.get("roe"),
            "revenueGrowth": stock.get("revenue_growth"),
            "opGrowth": stock.get("op_growth"),
            "opMargin": stock.get("op_margin"),
            "debtRatio": stock.get("debt_ratio"),
            "currentRatio": stock.get("current_ratio"),
        }

    # 기술지표 계산 (SQLite 가격 데이터 기반)
    stock_code = result.get("stock_code") or (stock.get("code") if stock else "")
    stock_name = result.get("stock_name") or (stock.get("name") if stock else "")
    tech_indicators = {}
    if stock_code:
        try:
            raw_indicators = calculate_indicators(stock_code)
            if raw_indicators.get("has_data"):
                tech_indicators = {
                    "currentPrice": raw_indicators.get("current_price"),
                    "ma5": raw_indicators.get("ma5"),
                    "ma20": raw_indicators.get("ma20"),
                    "ma60": raw_indicators.get("ma60"),
                    "ma120": raw_indicators.get("ma120"),
                    "rsi14": raw_indicators.get("rsi14"),
                    "macd": raw_indicators.get("macd"),
                    "macdSignal": raw_indicators.get("macd_signal"),
                    "macdHist": raw_indicators.get("macd_hist"),
                    "volumeRatio": raw_indicators.get("volume_ratio"),
                }
        except Exception:
            pass

    # 감정분석 데이터 (실시간 뉴스 수집)
    sentiment_data = {"news_items": [], "news_summary": {}}
    if stock_code:
        try:
            analyzer = SentimentAnalyzer(stock_code, stock_name, days=30)
            sentiment_result = analyzer.calculate_total()
            sentiment_data = {
                "news_items": sentiment_result.get("news_items", []),
                "news_summary": sentiment_result.get("news_summary", {}),
            }
        except Exception:
            pass

    # DB 테이블 컬럼 형식 (analysis_results_anal)
    if "tech_total" in result:
        # 감정분석 출처 확인 (수동 평점 우선)
        stock_id = result.get("stock_id") or (stock.get("id") if stock else None)
        sentiment_source = "auto"
        manual_score_info = {}
        sentiment_score = result.get("sent_total", 0)

        if stock_id:
            sentiment_source, manual_score_info = _get_sentiment_source(stock_id)
            if sentiment_source == "manual":
                # 수동 평점이 있으면 해당 점수 사용
                sentiment_score = manual_score_info.get("score", 10.0)

        # 수동 평점 사용 시 총점 재계산
        if sentiment_source == "manual":
            total_score = result.get("tech_total", 0) + result.get("fund_total", 0) + sentiment_score
        else:
            total_score = result.get("total_score", 0)

        return {
            "stockCode": stock_code or result.get("stock_code", ""),
            "stockName": stock_name or result.get("stock_name", ""),
            "analysisDate": result.get("analysis_date", ""),
            "totalScore": round(total_score, 1),
            "maxScore": 100,
            "grade": result.get("grade", "F"),
            "sentimentSource": sentiment_source,  # 감정분석 출처 (manual/auto)
            "scoreBreakdown": {
                "technical": {
                    "score": result.get("tech_total", 0),
                    "max": 30,
                    "weight": "30%",
                },
                "fundamental": {
                    "score": result.get("fund_total", 0),
                    "max": 50,
                    "weight": "50%",
                },
                "sentiment": {
                    "score": round(sentiment_score, 1),
                    "max": 20,
                    "weight": "20%",
                    "source": sentiment_source,
                },
            },
            "details": {
                "technical": {
                    "hasData": True,
                    "details": {
                        "maArrangement": {"score": result.get("tech_ma_arrangement", 0), "max": 6, "description": "이동평균선 정배열 상태"},
                        "maDivergence": {"score": result.get("tech_ma_divergence", 0), "max": 6, "description": "현재가와 이평선 이격도"},
                        "rsi": {"score": result.get("tech_rsi", 0), "max": 5, "description": "RSI 14일 기준"},
                        "macd": {"score": result.get("tech_macd", 0), "max": 5, "description": "MACD 히스토그램"},
                        "volume": {"score": result.get("tech_volume", 0), "max": 8, "description": "거래량 추세"},
                    },
                    "indicators": tech_indicators,
                },
                "fundamental": {
                    "hasData": True,
                    "isLossCompany": result.get("is_loss_company", False),
                    "financials": financials,
                    "details": {
                        "per": {"score": result.get("fund_per", 0), "max": 8, "description": "주가수익비율", "value": financials.get("per")},
                        "pbr": {"score": result.get("fund_pbr", 0), "max": 7, "description": "주가순자산비율", "value": financials.get("pbr")},
                        "psr": {"score": result.get("fund_psr", 0), "max": 5, "description": "주가매출비율", "value": financials.get("psr")},
                        "revenueGrowth": {"score": result.get("fund_revenue_growth", 0), "max": 6, "description": "매출성장률", "value": financials.get("revenueGrowth")},
                        "opGrowth": {"score": result.get("fund_profit_growth", 0), "max": 6, "description": "영업이익성장률", "value": financials.get("opGrowth")},
                        "roe": {"score": result.get("fund_roe", 0), "max": 5, "description": "자기자본이익률", "value": financials.get("roe")},
                        "opMargin": {"score": result.get("fund_margin", 0), "max": 5, "description": "영업이익률", "value": financials.get("opMargin")},
                        "debtRatio": {"score": result.get("fund_debt_ratio", 0), "max": 4, "description": "부채비율", "value": financials.get("debtRatio")},
                        "currentRatio": {"score": result.get("fund_current_ratio", 0), "max": 4, "description": "유동비율", "value": financials.get("currentRatio")},
                    },
                },
                "sentiment": {
                    "hasData": True,
                    "dataInsufficient": result.get("sent_data_insufficient", False),
                    "source": sentiment_source,  # manual 또는 auto
                    "totalScore": round(sentiment_score, 1),
                    "maxScore": 20,
                    "newsCount": sentiment_data.get("news_summary", {}).get("total", 0),
                    "newsSummary": {
                        "total": sentiment_data.get("news_summary", {}).get("total", 0),
                        "positive": sentiment_data.get("news_summary", {}).get("positive", 0),
                        "negative": sentiment_data.get("news_summary", {}).get("negative", 0),
                        "neutral": sentiment_data.get("news_summary", {}).get("neutral", 0),
                        "highImpact": sentiment_data.get("news_summary", {}).get("high_impact", 0),
                        "mediumImpact": sentiment_data.get("news_summary", {}).get("medium_impact", 0),
                    },
                    "manualRating": {
                        "avgRating": manual_score_info.get("avg_rating", 0) if sentiment_source == "manual" else None,
                        "ratedCount": manual_score_info.get("rated_count", 0) if sentiment_source == "manual" else 0,
                    } if sentiment_source == "manual" else None,
                    "details": {
                        "sentiment": {"score": sentiment_score if sentiment_source == "manual" else result.get("sent_news", 0) * 0.67, "max": 20 if sentiment_source == "manual" else 8, "description": f"수동 뉴스 평점 ({manual_score_info.get('rated_count', 0)}건)" if sentiment_source == "manual" else "뉴스 감정 분석"},
                        "impact": {"score": 0 if sentiment_source == "manual" else result.get("sent_news", 0) * 0.33, "max": 0 if sentiment_source == "manual" else 7, "description": "수동 평점에 포함" if sentiment_source == "manual" else "뉴스 영향도"},
                        "volume": {"score": 0 if sentiment_source == "manual" else result.get("sent_trend", 0), "max": 0 if sentiment_source == "manual" else 5, "description": "수동 평점에 포함" if sentiment_source == "manual" else "뉴스량/관심도"},
                    },
                    "newsItems": sentiment_data.get("news_items", [])[:10],
                },
            },
        }

    # 구 형식 (score_breakdown, details JSON)
    breakdown = result.get("score_breakdown", {})
    details = result.get("details", {})

    # 감정분석 출처 (scoring.py에서 이미 계산됨)
    sentiment_source = result.get("sentiment_source", breakdown.get("sentiment", {}).get("source", "auto"))

    return {
        "stockCode": result.get("stock_code", result.get("stockCode", "")),
        "stockName": result.get("stock_name", result.get("stockName", "")),
        "analysisDate": result.get("analysis_date", result.get("analysisDate", "")),
        "totalScore": result.get("total_score", result.get("totalScore", 0)),
        "maxScore": result.get("max_score", result.get("maxScore", 100)),
        "grade": result.get("grade", "F"),
        "sentimentSource": sentiment_source,
        "scoreBreakdown": {
            "technical": {
                "score": breakdown.get("technical", {}).get("score", 0),
                "max": 30,
                "weight": "30%",
            },
            "fundamental": {
                "score": breakdown.get("fundamental", {}).get("score", 0),
                "max": 50,
                "weight": "50%",
            },
            "sentiment": {
                "score": breakdown.get("sentiment", {}).get("score", 0),
                "max": 20,
                "weight": "20%",
                "source": sentiment_source,
            },
        },
        "details": {
            "technical": _format_technical_details(details.get("technical", {})),
            "fundamental": _format_fundamental_details(details.get("fundamental", {})),
            "sentiment": _format_sentiment_details(details.get("sentiment", {}), sentiment_source),
        },
    }


def _format_technical_details(data: dict) -> dict:
    """기술분석 상세 포맷"""
    details = data.get("details", {})
    indicators = data.get("indicators", {})

    return {
        "stockCode": data.get("stock_code", ""),
        "hasData": data.get("has_data", False),
        "totalScore": data.get("total_score", 0),
        "maxScore": data.get("max_score", 30),
        "details": {
            "maArrangement": details.get("ma_arrangement", {}),
            "maDivergence": details.get("ma_divergence", {}),
            "rsi": details.get("rsi", {}),
            "macd": details.get("macd", {}),
            "volume": details.get("volume", {}),
        },
        "indicators": {
            "currentPrice": indicators.get("current_price", 0),
            "ma5": indicators.get("ma5"),
            "ma20": indicators.get("ma20"),
            "ma60": indicators.get("ma60"),
            "ma120": indicators.get("ma120"),
            "rsi14": indicators.get("rsi14"),
            "macd": indicators.get("macd"),
            "macdSignal": indicators.get("macd_signal"),
            "macdHist": indicators.get("macd_hist"),
            "volumeRatio": indicators.get("volume_ratio"),
        },
    }


def _format_fundamental_details(data: dict) -> dict:
    """기본분석 상세 포맷"""
    details = data.get("details", {})
    financials = data.get("financials", {})

    # 각 detail 항목에 value 추가
    def add_value(detail_item: dict, value_key: str) -> dict:
        result = dict(detail_item)
        result["value"] = financials.get(value_key)
        return result

    return {
        "stockCode": data.get("stock_code", ""),
        "stockId": data.get("stock_id"),
        "sector": data.get("sector"),
        "hasData": data.get("has_data", False),
        "totalScore": data.get("total_score", 0),
        "maxScore": data.get("max_score", 50),
        "details": {
            "per": add_value(details.get("per", {}), "per"),
            "pbr": add_value(details.get("pbr", {}), "pbr"),
            "psr": add_value(details.get("psr", {}), "psr"),
            "revenueGrowth": add_value(details.get("revenue_growth", {}), "revenue_growth"),
            "opGrowth": add_value(details.get("op_growth", {}), "op_growth"),
            "roe": add_value(details.get("roe", {}), "roe"),
            "opMargin": add_value(details.get("op_margin", {}), "op_margin"),
            "debtRatio": add_value(details.get("debt_ratio", {}), "debt_ratio"),
            "currentRatio": add_value(details.get("current_ratio", {}), "current_ratio"),
        },
        "financials": {
            "per": financials.get("per"),
            "pbr": financials.get("pbr"),
            "psr": financials.get("psr"),
            "roe": financials.get("roe"),
            "revenueGrowth": financials.get("revenue_growth"),
            "opGrowth": financials.get("op_growth"),
            "opMargin": financials.get("op_margin"),
            "debtRatio": financials.get("debt_ratio"),
            "currentRatio": financials.get("current_ratio"),
        },
    }


def _format_sentiment_details(data: dict, source: str = "auto") -> dict:
    """감정분석 상세 포맷"""
    details = data.get("details", {})
    summary = data.get("news_summary", {})

    # 수동 평점인 경우 처리
    is_manual = data.get("is_manual", False) or source == "manual"

    return {
        "stockCode": data.get("stock_code", ""),
        "stockName": data.get("stock_name", ""),
        "hasData": data.get("has_data", False),
        "totalScore": data.get("total_score", 0),
        "maxScore": data.get("max_score", 20),
        "periodDays": data.get("period_days", 7),
        "source": "manual" if is_manual else "auto",
        "manualRating": {
            "avgRating": data.get("avg_rating", 0),
            "ratedCount": data.get("rated_count", 0),
        } if is_manual else None,
        "newsSummary": {
            "total": summary.get("total", 0) if not is_manual else summary.get("rated_count", 0),
            "positive": summary.get("positive", 0),
            "negative": summary.get("negative", 0),
            "neutral": summary.get("neutral", 0),
            "highImpact": summary.get("high_impact", 0),
            "mediumImpact": summary.get("medium_impact", 0),
            "avgRating": summary.get("avg_rating") if is_manual else None,
        },
        "details": {
            "sentiment": details.get("sentiment", {}),
            "impact": details.get("impact", {}),
            "volume": details.get("volume", {}),
        },
        "newsItems": data.get("news_items", [])[:10],
    }


# === 뉴스 평점 API ===

@router.get("/{code}/news")
async def get_news_list(
    code: str,
    rated_only: bool = Query(False, description="평점 완료 뉴스만"),
):
    """
    종목 뉴스 목록 조회

    수집된 뉴스와 평점 정보 반환
    """
    try:
        stock = supabase_db.get_stock_by_code(code)
        if not stock:
            raise HTTPException(status_code=404, detail=f"Stock not found: {code}")

        stock_id = stock.get("id")
        news_list = supabase_db.get_news_ratings(stock_id, rated_only=rated_only)

        # 평점 통계 계산
        sentiment_score = supabase_db.calculate_sentiment_from_ratings(stock_id)

        return {
            "stockCode": code,
            "stockName": stock.get("name"),
            "newsCount": len(news_list),
            "sentimentScore": sentiment_score,
            "news": news_list,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{code}/news/collect")
async def collect_news(
    code: str,
    days: int = Query(30, ge=1, le=90, description="수집 기간 (일)"),
    limit: int = Query(50, ge=10, le=100, description="최대 수집 개수"),
):
    """
    종목 뉴스 수집

    네이버 증권에서 뉴스 수집 후 DB에 저장
    """
    try:
        stock = supabase_db.get_stock_by_code(code)
        if not stock:
            raise HTTPException(status_code=404, detail=f"Stock not found: {code}")

        stock_id = stock.get("id")
        stock_name = stock.get("name", "")

        # 뉴스 수집
        collector = get_news_collector()
        news_list = collector.search_naver_stock_news(
            stock_code=code,
            stock_name=stock_name,
            limit=limit,
            strict_filter=True,
            price_impact_only=False,  # 모든 관련 뉴스 수집
            days=days,
        )

        # DB 저장용 데이터 변환
        news_items = []
        for item in news_list:
            # 날짜 파싱
            news_date = None
            date_text = item.get("date_text", "")
            if date_text:
                try:
                    date_str = date_text.split()[0]
                    news_date = datetime.strptime(date_str, "%Y.%m.%d").strftime("%Y-%m-%d")
                except (ValueError, IndexError):
                    news_date = datetime.now().strftime("%Y-%m-%d")

            news_items.append({
                "stock_id": stock_id,
                "title": item.get("title", "")[:500],
                "link": item.get("link", "")[:1000],
                "press": item.get("press", "")[:100],
                "news_date": news_date,
                "auto_sentiment": item.get("sentiment", "neutral"),
                "auto_impact": item.get("impact", "low"),
                "is_rated": False,
            })

        # 대량 upsert
        saved_count = supabase_db.upsert_news_items_bulk(news_items)

        # 저장된 뉴스 목록 반환
        all_news = supabase_db.get_news_ratings(stock_id)

        return {
            "stockCode": code,
            "stockName": stock_name,
            "collectedCount": len(news_list),
            "savedCount": saved_count,
            "totalNews": len(all_news),
            "news": all_news,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{code}/news/rate-all")
async def rate_all_news(
    code: str,
    rating: int = Query(..., ge=-10, le=10, description="일괄 평점 (-10 ~ +10)"),
):
    """
    해당 종목의 미평점 뉴스를 일괄 평점 설정

    rating=0: 전체 무관 처리
    """
    try:
        stock = supabase_db.get_stock_by_code(code)
        if not stock:
            raise HTTPException(status_code=404, detail=f"Stock not found: {code}")

        stock_id = stock.get("id")

        # 미평점 뉴스 조회
        client = supabase_db.get_client()
        response = client.table("news_ratings_anal").select("id").eq(
            "stock_id", stock_id
        ).eq("is_rated", False).execute()

        updated_count = 0
        for item in (response.data or []):
            supabase_db.update_news_rating(item["id"], rating)
            updated_count += 1

        # 업데이트된 감정 점수 계산
        sentiment_score = supabase_db.calculate_sentiment_from_ratings(stock_id)

        # 총점 자동 재계산 및 저장
        analysis_result = calculate_stock_score(
            stock_code=code,
            stock_name=stock.get("name"),
            save=True,
        )

        return {
            "updatedCount": updated_count,
            "rating": rating,
            "sentimentScore": sentiment_score,
            "totalScore": analysis_result["total_score"],
            "grade": analysis_result["grade"],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{code}/news/{news_id}/rate")
async def update_news_rating(
    code: str,
    news_id: int,
    rating: int = Query(..., ge=-10, le=10, description="평점 (-10 ~ +10)"),
):
    """
    뉴스 평점 업데이트

    -10 (매우 부정) ~ +10 (매우 긍정)
    0은 무관한 뉴스
    """
    try:
        stock = supabase_db.get_stock_by_code(code)
        if not stock:
            raise HTTPException(status_code=404, detail=f"Stock not found: {code}")

        # 평점 업데이트
        result = supabase_db.update_news_rating(news_id, rating)
        if not result:
            raise HTTPException(status_code=404, detail=f"News not found: {news_id}")

        # 업데이트된 감정 점수 계산
        stock_id = stock.get("id")
        sentiment_score = supabase_db.calculate_sentiment_from_ratings(stock_id)

        # 총점 자동 재계산 및 저장
        analysis_result = calculate_stock_score(
            stock_code=code,
            stock_name=stock.get("name"),
            save=True,
        )

        return {
            "newsId": news_id,
            "rating": rating,
            "sentimentScore": sentiment_score,
            "totalScore": analysis_result["total_score"],
            "grade": analysis_result["grade"],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{code}/sentiment-score")
async def get_sentiment_score(code: str):
    """
    사용자 평점 기반 감정 점수 조회

    평점 기반 감정 점수 (20점 만점)
    """
    try:
        stock = supabase_db.get_stock_by_code(code)
        if not stock:
            raise HTTPException(status_code=404, detail=f"Stock not found: {code}")

        stock_id = stock.get("id")

        # 평점 통계 계산
        sentiment_score = supabase_db.calculate_sentiment_from_ratings(stock_id)

        # 평점된 뉴스 개수
        rated_news = supabase_db.get_news_ratings(stock_id, rated_only=True)
        unrated_news = supabase_db.get_unrated_news(stock_id)

        return {
            "stockCode": code,
            "stockName": stock.get("name"),
            "sentimentScore": sentiment_score.get("score", 10.0),
            "maxScore": 20,
            "avgRating": sentiment_score.get("avg_rating", 0),
            "ratedCount": sentiment_score.get("rated_count", 0),
            "unratedCount": len(unrated_news),
            "totalNews": len(rated_news) + len(unrated_news),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

"""
Analysis Result Pydantic Models
- 분석 결과 스키마
- 기술분석 (30점) + 기본분석 (50점) + 감정분석 (20점) = 100점
"""

from datetime import date, datetime
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, Field


# === 기술분석 (30점) ===

class TechnicalScore(BaseModel):
    """기술분석 점수"""
    ma_arrangement: Optional[Decimal] = Field(None, ge=0, le=6, description="MA배열 (6점)")
    ma_divergence: Optional[Decimal] = Field(None, ge=0, le=6, description="MA이격도 (6점)")
    rsi: Optional[Decimal] = Field(None, ge=0, le=5, description="RSI (5점)")
    macd: Optional[Decimal] = Field(None, ge=0, le=5, description="MACD (5점)")
    volume: Optional[Decimal] = Field(None, ge=0, le=8, description="거래량 (8점)")
    total: Optional[Decimal] = Field(None, ge=0, le=30, description="기술분석 총점 (30점)")


# === 기본분석 (50점) ===

class FundamentalScore(BaseModel):
    """기본분석 점수"""
    per: Optional[Decimal] = Field(None, ge=0, le=8, description="PER (8점, 적자 0점)")
    pbr: Optional[Decimal] = Field(None, ge=0, le=7, description="PBR (7점)")
    psr: Optional[Decimal] = Field(None, ge=0, le=5, description="PSR (5점)")
    revenue_growth: Optional[Decimal] = Field(None, ge=0, le=6, description="매출성장률 (6점)")
    profit_growth: Optional[Decimal] = Field(None, ge=0, le=6, description="영업이익성장률 (6점)")
    roe: Optional[Decimal] = Field(None, ge=0, le=5, description="ROE (5점)")
    margin: Optional[Decimal] = Field(None, ge=0, le=5, description="영업이익률 (5점)")
    debt_ratio: Optional[Decimal] = Field(None, ge=0, le=4, description="부채비율 (4점)")
    current_ratio: Optional[Decimal] = Field(None, ge=0, le=4, description="유동비율 (4점)")
    total: Optional[Decimal] = Field(None, ge=0, le=50, description="기본분석 총점 (50점)")
    is_loss_company: bool = Field(False, description="적자기업 여부")


# === 감정분석 (20점) ===

class SentimentScore(BaseModel):
    """감정분석 점수"""
    trend: Optional[Decimal] = Field(None, ge=0, le=8, description="구글트렌드 (8점)")
    news: Optional[Decimal] = Field(None, ge=0, le=12, description="뉴스감정 (12점)")
    total: Optional[Decimal] = Field(None, ge=0, le=20, description="감정분석 총점 (20점)")
    data_insufficient: bool = Field(False, description="데이터 부족 여부")


# === 분석 결과 ===

class AnalysisResultBase(BaseModel):
    """분석 결과 기본"""
    stock_id: int
    analysis_date: date


class AnalysisResultCreate(AnalysisResultBase):
    """분석 결과 생성용"""
    # 기술분석 (30점)
    tech_ma_arrangement: Optional[Decimal] = None
    tech_ma_divergence: Optional[Decimal] = None
    tech_rsi: Optional[Decimal] = None
    tech_macd: Optional[Decimal] = None
    tech_volume: Optional[Decimal] = None
    tech_total: Optional[Decimal] = None

    # 기본분석 (50점)
    fund_per: Optional[Decimal] = None
    fund_pbr: Optional[Decimal] = None
    fund_psr: Optional[Decimal] = None
    fund_revenue_growth: Optional[Decimal] = None
    fund_profit_growth: Optional[Decimal] = None
    fund_roe: Optional[Decimal] = None
    fund_margin: Optional[Decimal] = None
    fund_debt_ratio: Optional[Decimal] = None
    fund_current_ratio: Optional[Decimal] = None
    fund_total: Optional[Decimal] = None
    is_loss_company: bool = False

    # 감정분석 (20점)
    sent_trend: Optional[Decimal] = None
    sent_news: Optional[Decimal] = None
    sent_total: Optional[Decimal] = None
    sent_data_insufficient: bool = False

    # 유동성 리스크 감점
    liquidity_holding_penalty: Optional[Decimal] = None
    liquidity_trading_penalty: Optional[Decimal] = None
    liquidity_total_penalty: Optional[Decimal] = None

    # 총점
    total_score: Optional[Decimal] = None


class AnalysisResultInDB(AnalysisResultCreate):
    """DB에서 조회된 분석 결과"""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class AnalysisResultResponse(AnalysisResultInDB):
    """API 응답용 분석 결과"""
    # 종목 정보 포함
    stock_code: Optional[str] = None
    stock_name: Optional[str] = None
    sector: Optional[str] = None


class AnalysisResultDetail(AnalysisResultResponse):
    """분석 결과 상세 (카테고리별 분리)"""
    technical: Optional[TechnicalScore] = None
    fundamental: Optional[FundamentalScore] = None
    sentiment: Optional[SentimentScore] = None

    @classmethod
    def from_flat(cls, data: AnalysisResultResponse) -> "AnalysisResultDetail":
        """플랫 구조 → 카테고리별 분리"""
        return cls(
            **data.model_dump(),
            technical=TechnicalScore(
                ma_arrangement=data.tech_ma_arrangement,
                ma_divergence=data.tech_ma_divergence,
                rsi=data.tech_rsi,
                macd=data.tech_macd,
                volume=data.tech_volume,
                total=data.tech_total,
            ),
            fundamental=FundamentalScore(
                per=data.fund_per,
                pbr=data.fund_pbr,
                psr=data.fund_psr,
                revenue_growth=data.fund_revenue_growth,
                profit_growth=data.fund_profit_growth,
                roe=data.fund_roe,
                margin=data.fund_margin,
                debt_ratio=data.fund_debt_ratio,
                current_ratio=data.fund_current_ratio,
                total=data.fund_total,
                is_loss_company=data.is_loss_company,
            ),
            sentiment=SentimentScore(
                trend=data.sent_trend,
                news=data.sent_news,
                total=data.sent_total,
                data_insufficient=data.sent_data_insufficient,
            ),
        )


# === 순위 ===

class RankingItem(BaseModel):
    """순위 항목"""
    rank: int
    stock_code: str
    stock_name: str
    sector: Optional[str] = None
    total_score: Decimal
    tech_total: Optional[Decimal] = None
    fund_total: Optional[Decimal] = None
    sent_total: Optional[Decimal] = None
    analysis_date: date


class RankingResponse(BaseModel):
    """순위 응답"""
    items: list[RankingItem]
    analysis_date: date
    total_count: int


# === 점수 히스토리 ===

class ScoreHistory(BaseModel):
    """점수 히스토리"""
    analysis_date: date
    total_score: Decimal
    tech_total: Optional[Decimal] = None
    fund_total: Optional[Decimal] = None
    sent_total: Optional[Decimal] = None


class ScoreHistoryResponse(BaseModel):
    """점수 히스토리 응답"""
    stock_code: str
    stock_name: str
    history: list[ScoreHistory]

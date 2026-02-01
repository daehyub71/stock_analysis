"""
Portfolio Pydantic Models
- 포트폴리오 및 보유종목 스키마
"""

from datetime import date, datetime
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, Field

from .stock import StockResponse


class PortfolioBase(BaseModel):
    """포트폴리오 기본 정보"""
    name: str = Field(..., max_length=100, description="포트폴리오명")
    source: Optional[str] = Field(None, max_length=50, description="출처")
    report_date: Optional[date] = Field(None, description="보고서 기준일")


class PortfolioCreate(PortfolioBase):
    """포트폴리오 생성용"""
    pass


class PortfolioInDB(PortfolioBase):
    """DB에서 조회된 포트폴리오"""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class PortfolioResponse(PortfolioInDB):
    """API 응답용 포트폴리오"""
    stock_count: Optional[int] = None
    total_amount: Optional[int] = None


# === 포트폴리오 종목 ===

class PortfolioStockBase(BaseModel):
    """포트폴리오 내 종목"""
    portfolio_id: int
    stock_id: int
    quantity: Optional[int] = Field(None, description="보유수량")
    amount: Optional[int] = Field(None, description="평가금액")
    weight: Optional[Decimal] = Field(None, ge=0, le=100, description="포트폴리오 내 비중(%)")
    holding_ratio: Optional[Decimal] = Field(
        None, ge=0, le=100,
        description="발행주식수 대비 보유비율(%)"
    )


class PortfolioStockCreate(PortfolioStockBase):
    """포트폴리오 종목 생성용"""
    pass


class PortfolioStockUpdate(BaseModel):
    """포트폴리오 종목 업데이트용"""
    quantity: Optional[int] = None
    amount: Optional[int] = None
    weight: Optional[Decimal] = None
    holding_ratio: Optional[Decimal] = None
    is_concentrated: Optional[bool] = None


class PortfolioStockInDB(PortfolioStockBase):
    """DB에서 조회된 포트폴리오 종목"""
    id: int
    is_concentrated: bool = False  # 집중보유 여부 (5% 초과)

    class Config:
        from_attributes = True


class PortfolioStockResponse(PortfolioStockInDB):
    """API 응답용 포트폴리오 종목"""
    stock: Optional[StockResponse] = None


class PortfolioStockWithAnalysis(PortfolioStockResponse):
    """포트폴리오 종목 + 분석 결과"""
    total_score: Optional[float] = None
    tech_total: Optional[float] = None
    fund_total: Optional[float] = None
    sent_total: Optional[float] = None


# === 업종 평균 ===

class SectorAverageBase(BaseModel):
    """업종 평균"""
    sector: str = Field(..., max_length=50)
    avg_per: Optional[Decimal] = None
    avg_pbr: Optional[Decimal] = None
    avg_psr: Optional[Decimal] = None
    avg_roe: Optional[Decimal] = None
    avg_operating_margin: Optional[Decimal] = None
    base_date: date


class SectorAverageCreate(SectorAverageBase):
    """업종 평균 생성용"""
    pass


class SectorAverageInDB(SectorAverageBase):
    """DB에서 조회된 업종 평균"""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class SectorAverageResponse(SectorAverageInDB):
    """API 응답용 업종 평균"""
    pass


# === 포트폴리오 상세 ===

class PortfolioDetailResponse(PortfolioResponse):
    """포트폴리오 상세 응답 (종목 리스트 포함)"""
    stocks: list[PortfolioStockWithAnalysis] = []

    # 통계
    avg_score: Optional[float] = None
    top_5_stocks: Optional[list[str]] = None
    sector_distribution: Optional[dict[str, float]] = None

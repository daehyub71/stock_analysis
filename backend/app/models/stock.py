"""
Stock Pydantic Models
- 종목 기본 정보 스키마
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class StockBase(BaseModel):
    """종목 기본 정보"""
    code: str = Field(..., min_length=6, max_length=10, description="종목코드")
    name: str = Field(..., max_length=100, description="종목명")
    sector: Optional[str] = Field(None, max_length=50, description="업종")
    mapped_sector: Optional[str] = Field(None, max_length=50, description="매핑된 업종 (미분류용)")
    market: Optional[str] = Field(None, max_length=20, description="KOSPI/KOSDAQ")


class StockCreate(StockBase):
    """종목 생성용"""
    market_cap: Optional[int] = Field(None, description="시가총액")
    shares_outstanding: Optional[int] = Field(None, description="발행주식수")
    avg_trading_value: Optional[int] = Field(None, description="20일 평균 거래대금")


class StockUpdate(BaseModel):
    """종목 업데이트용"""
    name: Optional[str] = Field(None, max_length=100)
    sector: Optional[str] = Field(None, max_length=50)
    mapped_sector: Optional[str] = Field(None, max_length=50)
    market: Optional[str] = Field(None, max_length=20)
    market_cap: Optional[int] = None
    shares_outstanding: Optional[int] = None
    avg_trading_value: Optional[int] = None
    is_active: Optional[bool] = None


class StockInDB(StockBase):
    """DB에서 조회된 종목"""
    id: int
    market_cap: Optional[int] = None
    shares_outstanding: Optional[int] = None
    avg_trading_value: Optional[int] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StockResponse(StockInDB):
    """API 응답용 종목"""
    pass


class StockListResponse(BaseModel):
    """종목 리스트 응답"""
    items: list[StockResponse]
    total: int
    page: int = 1
    size: int = 50


# === 시세 데이터 (SQLite) ===

class PriceHistory(BaseModel):
    """일별 시세"""
    stock_code: str
    date: str  # YYYY-MM-DD
    open: int
    high: int
    low: int
    close: int
    volume: int
    trading_value: Optional[int] = None  # 거래대금
    change_rate: Optional[float] = None  # 등락률


class TechnicalIndicators(BaseModel):
    """기술지표"""
    stock_code: str
    date: str  # YYYY-MM-DD
    ma5: Optional[float] = None
    ma20: Optional[float] = None
    ma60: Optional[float] = None
    ma120: Optional[float] = None
    rsi14: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_hist: Optional[float] = None
    volume_ratio: Optional[float] = None  # 거래량 비율 (당일/20일평균)


class StockWithIndicators(StockResponse):
    """종목 + 기술지표"""
    current_price: Optional[int] = None
    change_rate: Optional[float] = None
    indicators: Optional[TechnicalIndicators] = None

"""
Data Collectors
- 시세, 재무, 트렌드, 뉴스 데이터 수집
"""

from .kis_api import get_current_price as kis_get_price, get_daily_prices as kis_get_daily
from .pykrx_collector import (
    get_market_ohlcv,
    get_current_price as pykrx_get_price,
    get_stock_fundamental,
    get_market_cap,
)
from .price_collector import (
    get_current_price,
    get_daily_prices,
    get_fundamental,
    get_market_cap as get_cap,
)
from .naver_finance import (
    get_stock_info,
    get_financial_summary,
    get_sector_info,
    get_all_financial_data,
)
from .google_trends import (
    get_stock_trend,
    get_trends_batch,
    calculate_trend_score,
)
from .news_collector import (
    get_stock_news,
    get_stock_sentiment,
    get_sentiment_batch,
    calculate_news_score,
)

__all__ = [
    # Price
    "get_current_price",
    "get_daily_prices",
    "get_fundamental",
    "get_cap",
    # Naver Finance
    "get_stock_info",
    "get_financial_summary",
    "get_sector_info",
    "get_all_financial_data",
    # Google Trends
    "get_stock_trend",
    "get_trends_batch",
    "calculate_trend_score",
    # News
    "get_stock_news",
    "get_stock_sentiment",
    "get_sentiment_batch",
    "calculate_news_score",
]

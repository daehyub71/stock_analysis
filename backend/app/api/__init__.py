"""
API Routers
"""

from .stocks import router as stocks_router
from .analysis import router as analysis_router
from .backtest import router as backtest_router
from .alerts import router as alerts_router
from .portfolios import router as portfolios_router

__all__ = [
    "stocks_router",
    "analysis_router",
    "backtest_router",
    "alerts_router",
    "portfolios_router",
]

"""
Database Module
- SQLite: 시세 데이터 (로컬)
- Supabase: 분석 데이터 (클라우드)
- Sync: 데이터 동기화
"""

from .sqlite_db import (
    init_database,
    get_connection,
    insert_price,
    insert_prices_bulk,
    get_prices,
    get_latest_price,
    insert_indicators,
    get_indicators,
    get_stock_count,
    get_date_range,
)

from .supabase_db import (
    get_client,
    get_all_stocks,
    get_stock_by_code,
    get_stock_id,
    upsert_stock,
    upsert_stocks_bulk,
    get_portfolios,
    get_portfolio_by_name,
    create_portfolio,
    get_portfolio_stocks,
    upsert_portfolio_stock,
    get_sector_average,
    upsert_sector_average,
    get_analysis_result,
    get_latest_analysis,
    get_analysis_ranking,
    upsert_analysis_result,
    upsert_analysis_results_bulk,
    check_connection,
)

from .sync import (
    get_sync_manager,
    sync_stock_price,
    sync_all_prices,
    get_stock_mapping,
    check_sync_status,
    find_stocks_needing_sync,
)

__all__ = [
    # SQLite
    "init_database",
    "get_connection",
    "insert_price",
    "insert_prices_bulk",
    "get_prices",
    "get_latest_price",
    "insert_indicators",
    "get_indicators",
    "get_stock_count",
    "get_date_range",
    # Supabase
    "get_client",
    "get_all_stocks",
    "get_stock_by_code",
    "get_stock_id",
    "upsert_stock",
    "upsert_stocks_bulk",
    "get_portfolios",
    "get_portfolio_by_name",
    "create_portfolio",
    "get_portfolio_stocks",
    "upsert_portfolio_stock",
    "get_sector_average",
    "upsert_sector_average",
    "get_analysis_result",
    "get_latest_analysis",
    "get_analysis_ranking",
    "upsert_analysis_result",
    "upsert_analysis_results_bulk",
    "check_connection",
    # Sync
    "get_sync_manager",
    "sync_stock_price",
    "sync_all_prices",
    "get_stock_mapping",
    "check_sync_status",
    "find_stocks_needing_sync",
]

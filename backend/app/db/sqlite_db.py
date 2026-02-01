"""
SQLite Database Manager
- 시세 데이터 (price_history) 저장
- 기술지표 캐시 (technical_indicators) 저장
"""

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

# 기본 경로 설정
DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "price_history.db"
DB_PATH = os.environ.get("SQLITE_DB_PATH", str(DEFAULT_DB_PATH))


def get_db_path() -> Path:
    """데이터베이스 파일 경로 반환"""
    path = Path(DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


@contextmanager
def get_connection():
    """SQLite 연결 컨텍스트 매니저"""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row  # dict-like 접근 가능
    try:
        yield conn
    finally:
        conn.close()


def init_database():
    """데이터베이스 초기화 - 테이블 및 인덱스 생성"""
    with get_connection() as conn:
        cursor = conn.cursor()

        # price_history 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_code TEXT NOT NULL,
                date TEXT NOT NULL,
                open_price INTEGER,
                high_price INTEGER,
                low_price INTEGER,
                close_price INTEGER,
                volume INTEGER,
                trading_value INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(stock_code, date)
            )
        """)

        # technical_indicators 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS technical_indicators (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_code TEXT NOT NULL,
                date TEXT NOT NULL,
                ma5 REAL,
                ma20 REAL,
                ma60 REAL,
                ma120 REAL,
                rsi14 REAL,
                macd REAL,
                macd_signal REAL,
                macd_hist REAL,
                volume_ratio REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(stock_code, date)
            )
        """)

        # 인덱스 생성
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_price_stock_date
            ON price_history(stock_code, date)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_price_date
            ON price_history(date)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_tech_stock_date
            ON technical_indicators(stock_code, date)
        """)

        conn.commit()
        print(f"✅ SQLite database initialized: {get_db_path()}")


# === CRUD Operations ===

def insert_price(
    stock_code: str,
    date: str,
    open_price: int,
    high_price: int,
    low_price: int,
    close_price: int,
    volume: int,
    trading_value: int = 0
) -> bool:
    """주가 데이터 삽입 (upsert)"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO price_history
                (stock_code, date, open_price, high_price, low_price, close_price, volume, trading_value)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(stock_code, date) DO UPDATE SET
                open_price = excluded.open_price,
                high_price = excluded.high_price,
                low_price = excluded.low_price,
                close_price = excluded.close_price,
                volume = excluded.volume,
                trading_value = excluded.trading_value
        """, (stock_code, date, open_price, high_price, low_price, close_price, volume, trading_value))
        conn.commit()
        return cursor.rowcount > 0


def insert_prices_bulk(prices: list[dict]) -> int:
    """주가 데이터 대량 삽입"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.executemany("""
            INSERT INTO price_history
                (stock_code, date, open_price, high_price, low_price, close_price, volume, trading_value)
            VALUES (:stock_code, :date, :open_price, :high_price, :low_price, :close_price, :volume, :trading_value)
            ON CONFLICT(stock_code, date) DO UPDATE SET
                open_price = excluded.open_price,
                high_price = excluded.high_price,
                low_price = excluded.low_price,
                close_price = excluded.close_price,
                volume = excluded.volume,
                trading_value = excluded.trading_value
        """, prices)
        conn.commit()
        return cursor.rowcount


def get_prices(
    stock_code: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 200
) -> list[dict]:
    """주가 데이터 조회"""
    with get_connection() as conn:
        cursor = conn.cursor()

        query = "SELECT * FROM price_history WHERE stock_code = ?"
        params = [stock_code]

        if start_date:
            query += " AND date >= ?"
            params.append(start_date)

        if end_date:
            query += " AND date <= ?"
            params.append(end_date)

        query += " ORDER BY date DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [dict(row) for row in rows]


def get_latest_price(stock_code: str) -> Optional[dict]:
    """최신 주가 조회"""
    prices = get_prices(stock_code, limit=1)
    return prices[0] if prices else None


def insert_indicators(
    stock_code: str,
    date: str,
    indicators: dict
) -> bool:
    """기술지표 삽입 (upsert)"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO technical_indicators
                (stock_code, date, ma5, ma20, ma60, ma120, rsi14, macd, macd_signal, macd_hist, volume_ratio)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(stock_code, date) DO UPDATE SET
                ma5 = excluded.ma5,
                ma20 = excluded.ma20,
                ma60 = excluded.ma60,
                ma120 = excluded.ma120,
                rsi14 = excluded.rsi14,
                macd = excluded.macd,
                macd_signal = excluded.macd_signal,
                macd_hist = excluded.macd_hist,
                volume_ratio = excluded.volume_ratio
        """, (
            stock_code, date,
            indicators.get("ma5"),
            indicators.get("ma20"),
            indicators.get("ma60"),
            indicators.get("ma120"),
            indicators.get("rsi14"),
            indicators.get("macd"),
            indicators.get("macd_signal"),
            indicators.get("macd_hist"),
            indicators.get("volume_ratio"),
        ))
        conn.commit()
        return cursor.rowcount > 0


def get_indicators(
    stock_code: str,
    date: Optional[str] = None
) -> Optional[dict]:
    """기술지표 조회"""
    with get_connection() as conn:
        cursor = conn.cursor()

        if date:
            cursor.execute("""
                SELECT * FROM technical_indicators
                WHERE stock_code = ? AND date = ?
            """, (stock_code, date))
        else:
            cursor.execute("""
                SELECT * FROM technical_indicators
                WHERE stock_code = ?
                ORDER BY date DESC LIMIT 1
            """, (stock_code,))

        row = cursor.fetchone()
        return dict(row) if row else None


def get_stock_count() -> int:
    """저장된 종목 수 조회"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(DISTINCT stock_code) FROM price_history")
        return cursor.fetchone()[0]


def get_date_range(stock_code: str) -> tuple[Optional[str], Optional[str]]:
    """종목별 데이터 기간 조회"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT MIN(date), MAX(date) FROM price_history
            WHERE stock_code = ?
        """, (stock_code,))
        row = cursor.fetchone()
        return (row[0], row[1]) if row else (None, None)


# 모듈 로드 시 자동 초기화
if __name__ == "__main__":
    init_database()
    print(f"📊 Stock count: {get_stock_count()}")

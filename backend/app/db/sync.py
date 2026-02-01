"""
Data Synchronization Module
- SQLite ↔ Supabase 데이터 동기화
- 종목코드 매핑 및 시세 → 분석 데이터 동기화
"""

from datetime import datetime, timedelta
from typing import Optional

from . import sqlite_db, supabase_db


class DataSyncManager:
    """데이터 동기화 관리자"""

    def __init__(self):
        self._stock_code_map: dict[str, int] = {}  # code → stock_id
        self._stock_id_map: dict[int, str] = {}    # stock_id → code

    def _ensure_stock_map(self) -> None:
        """종목코드 ↔ stock_id 매핑 캐시 로드"""
        if self._stock_code_map:
            return

        stocks = supabase_db.get_all_stocks()
        for stock in stocks:
            code = stock.get("code")
            stock_id = stock.get("id")
            if code and stock_id:
                self._stock_code_map[code] = stock_id
                self._stock_id_map[stock_id] = code

    def get_stock_id(self, code: str) -> Optional[int]:
        """종목코드 → stock_id 조회"""
        self._ensure_stock_map()
        return self._stock_code_map.get(code)

    def get_stock_code(self, stock_id: int) -> Optional[str]:
        """stock_id → 종목코드 조회"""
        self._ensure_stock_map()
        return self._stock_id_map.get(stock_id)

    def refresh_stock_map(self) -> int:
        """종목 매핑 캐시 새로고침"""
        self._stock_code_map.clear()
        self._stock_id_map.clear()
        self._ensure_stock_map()
        return len(self._stock_code_map)

    def sync_price_to_stock(
        self,
        stock_code: str,
        update_supabase: bool = True,
    ) -> dict:
        """
        SQLite 시세 데이터 → Supabase stocks 테이블 동기화

        Args:
            stock_code: 종목코드
            update_supabase: Supabase 업데이트 여부

        Returns:
            동기화 결과 (current_price, volume 등)
        """
        # SQLite에서 최신 시세 조회
        latest_price = sqlite_db.get_latest_price(stock_code)

        if not latest_price:
            return {"success": False, "error": "No price data in SQLite"}

        result = {
            "stock_code": stock_code,
            "date": latest_price.get("date"),
            "current_price": latest_price.get("close_price"),
            "volume": latest_price.get("volume"),
            "trading_value": latest_price.get("trading_value"),
        }

        if update_supabase:
            stock_id = self.get_stock_id(stock_code)
            if stock_id:
                # Supabase stocks 테이블 업데이트
                supabase_db.upsert_stock({
                    "code": stock_code,
                    "current_price": result["current_price"],
                })
                result["success"] = True
                result["stock_id"] = stock_id
            else:
                result["success"] = False
                result["error"] = "Stock not found in Supabase"

        return result

    def sync_prices_batch(
        self,
        stock_codes: list[str],
    ) -> dict:
        """
        여러 종목의 시세 데이터 일괄 동기화

        Args:
            stock_codes: 종목코드 리스트

        Returns:
            동기화 결과 요약
        """
        results = {
            "total": len(stock_codes),
            "success": 0,
            "failed": 0,
            "details": [],
        }

        for code in stock_codes:
            sync_result = self.sync_price_to_stock(code)
            if sync_result.get("success"):
                results["success"] += 1
            else:
                results["failed"] += 1
            results["details"].append(sync_result)

        return results

    def sync_indicators_to_analysis(
        self,
        stock_code: str,
        analysis_date: str,
    ) -> dict:
        """
        SQLite 기술지표 → Supabase analysis_results 부분 업데이트

        Args:
            stock_code: 종목코드
            analysis_date: 분석 기준일

        Returns:
            동기화 결과
        """
        # SQLite에서 기술지표 조회
        indicators = sqlite_db.get_indicators(stock_code)

        if not indicators:
            return {"success": False, "error": "No indicators in SQLite"}

        stock_id = self.get_stock_id(stock_code)
        if not stock_id:
            return {"success": False, "error": "Stock not found in Supabase"}

        # 기존 분석 결과 조회 후 업데이트
        existing = supabase_db.get_analysis_result(stock_id, analysis_date)

        analysis_data = {
            "stock_id": stock_id,
            "analysis_date": analysis_date,
            # 기술지표 원본 값 저장 (점수는 별도 계산)
            "ma5": indicators.get("ma5"),
            "ma20": indicators.get("ma20"),
            "ma60": indicators.get("ma60"),
            "ma120": indicators.get("ma120"),
            "rsi14": indicators.get("rsi14"),
            "macd": indicators.get("macd"),
            "macd_signal": indicators.get("macd_signal"),
            "volume_ratio": indicators.get("volume_ratio"),
        }

        # 기존 데이터 병합
        if existing:
            for key, value in existing.items():
                if key not in analysis_data and value is not None:
                    analysis_data[key] = value

        supabase_db.upsert_analysis_result(analysis_data)

        return {
            "success": True,
            "stock_code": stock_code,
            "stock_id": stock_id,
            "analysis_date": analysis_date,
        }

    def get_sync_status(self, stock_code: str) -> dict:
        """
        종목별 동기화 상태 조회

        Args:
            stock_code: 종목코드

        Returns:
            SQLite/Supabase 데이터 상태
        """
        # SQLite 상태
        sqlite_latest = sqlite_db.get_latest_price(stock_code)
        sqlite_date_range = sqlite_db.get_date_range(stock_code)
        sqlite_indicators = sqlite_db.get_indicators(stock_code)

        # Supabase 상태
        stock_id = self.get_stock_id(stock_code)
        supabase_stock = None
        supabase_analysis = None

        if stock_id:
            supabase_stock = supabase_db.get_stock_by_code(stock_code)
            supabase_analysis = supabase_db.get_latest_analysis(stock_id)

        return {
            "stock_code": stock_code,
            "stock_id": stock_id,
            "sqlite": {
                "has_price": sqlite_latest is not None,
                "latest_date": sqlite_latest.get("date") if sqlite_latest else None,
                "date_range": sqlite_date_range,
                "has_indicators": sqlite_indicators is not None,
            },
            "supabase": {
                "has_stock": supabase_stock is not None,
                "stock_name": supabase_stock.get("name") if supabase_stock else None,
                "has_analysis": supabase_analysis is not None,
                "latest_analysis_date": (
                    supabase_analysis.get("analysis_date")
                    if supabase_analysis else None
                ),
            },
        }

    def get_stocks_needing_sync(self) -> dict:
        """
        동기화가 필요한 종목 목록 조회

        Returns:
            동기화 필요 종목 정보
        """
        self._ensure_stock_map()

        result = {
            "no_sqlite_price": [],  # SQLite에 시세 없음
            "no_supabase_stock": [],  # Supabase에 종목 없음
            "outdated_analysis": [],  # 분석 데이터 오래됨
        }

        # Supabase 종목 중 SQLite 시세 없는 것
        for code in self._stock_code_map.keys():
            latest = sqlite_db.get_latest_price(code)
            if not latest:
                result["no_sqlite_price"].append(code)

        # SQLite 종목 수
        sqlite_count = sqlite_db.get_stock_count()

        result["summary"] = {
            "supabase_stocks": len(self._stock_code_map),
            "sqlite_stocks": sqlite_count,
            "need_price_sync": len(result["no_sqlite_price"]),
        }

        return result


# 싱글톤 인스턴스
_manager: Optional[DataSyncManager] = None


def get_sync_manager() -> DataSyncManager:
    """DataSyncManager 싱글톤"""
    global _manager
    if _manager is None:
        _manager = DataSyncManager()
    return _manager


# === 편의 함수 ===

def sync_stock_price(stock_code: str) -> dict:
    """단일 종목 시세 동기화"""
    return get_sync_manager().sync_price_to_stock(stock_code)


def sync_all_prices() -> dict:
    """전체 종목 시세 동기화"""
    manager = get_sync_manager()
    manager._ensure_stock_map()
    codes = list(manager._stock_code_map.keys())
    return manager.sync_prices_batch(codes)


def get_stock_mapping() -> dict[str, int]:
    """종목코드 → stock_id 매핑 조회"""
    manager = get_sync_manager()
    manager._ensure_stock_map()
    return dict(manager._stock_code_map)


def check_sync_status(stock_code: str) -> dict:
    """종목 동기화 상태 확인"""
    return get_sync_manager().get_sync_status(stock_code)


def find_stocks_needing_sync() -> dict:
    """동기화 필요 종목 조회"""
    return get_sync_manager().get_stocks_needing_sync()


if __name__ == "__main__":
    print("=== Data Sync Module 테스트 ===\n")

    manager = get_sync_manager()

    # 종목 매핑 로드
    count = manager.refresh_stock_map()
    print(f"✅ 종목 매핑 로드: {count}개")

    if count > 0:
        # 첫 번째 종목 동기화 상태 확인
        codes = list(manager._stock_code_map.keys())[:3]
        for code in codes:
            status = manager.get_sync_status(code)
            print(f"\n📊 {code}:")
            print(f"  SQLite: 시세={status['sqlite']['has_price']}, 지표={status['sqlite']['has_indicators']}")
            print(f"  Supabase: 종목={status['supabase']['has_stock']}, 분석={status['supabase']['has_analysis']}")

    print("\n✅ Data Sync Module 테스트 완료")

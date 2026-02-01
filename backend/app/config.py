"""
Application Configuration
- pydantic-settings를 사용한 환경변수 관리
"""

from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """애플리케이션 설정"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # === Application ===
    app_name: str = "Stock Analysis Dashboard"
    app_version: str = "1.0.0"
    app_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"

    # === Supabase (분석 데이터) ===
    supabase_url: str = ""
    supabase_key: str = ""
    supabase_service_role_key: Optional[str] = None

    # === SQLite (시세 데이터) ===
    sqlite_db_path: str = "./data/price_history.db"

    # === KIS Trading API ===
    kis_app_key: Optional[str] = None
    kis_app_secret: Optional[str] = None
    kis_account_type: str = "VIRTUAL"  # VIRTUAL or REAL
    kis_cano: Optional[str] = None

    # === OpenAI API ===
    openai_api_key: Optional[str] = None

    # === Redis (선택) ===
    redis_url: Optional[str] = None

    # === CORS ===
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        """CORS origins를 리스트로 반환"""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def is_production(self) -> bool:
        """운영 환경 여부"""
        return self.app_env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """설정 싱글톤 (캐싱)"""
    return Settings()


# 전역 설정 인스턴스
settings = get_settings()

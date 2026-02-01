"""
Stock Analysis Dashboard - FastAPI Application
- 종목 분석 시스템 백엔드 API
"""

from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.sqlite_db import init_database as init_sqlite
from app.db.supabase_db import check_connection as check_supabase


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 라이프사이클 관리"""
    # Startup
    print(f"🚀 Starting {settings.app_name} v{settings.app_version}")
    print(f"📍 Environment: {settings.app_env}")

    # SQLite 초기화
    init_sqlite()
    print("✅ SQLite database initialized")

    yield

    # Shutdown
    print("👋 Shutting down...")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    ## 종목분석시스템 API

    기관투자자 포트폴리오 종목에 대한 종합 분석 시스템

    ### 점수 체계
    - **기술분석**: 30점 (MA배열, 이격도, RSI, MACD, 거래량)
    - **기본분석**: 50점 (PER, PBR, PSR, 성장률, ROE, 영업이익률, 부채비율, 유동비율)
    - **감정분석**: 20점 (구글트렌드, 뉴스감정)
    - **유동성감점**: -5점 (보유비율, 거래대금)

    ### 데이터 소스
    - 시세: KIS API, pykrx (백업)
    - 재무: 네이버금융, DART (백업)
    - 감정: 구글트렌드, OpenAI (뉴스)
    """,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === Health Check Endpoints ===

@app.get("/", tags=["Health"])
async def root():
    """루트 엔드포인트"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.app_env,
    }


@app.get("/health/db", tags=["Health"])
async def db_health_check():
    """데이터베이스 연결 상태 확인"""
    sqlite_ok = True  # SQLite는 항상 사용 가능
    supabase_ok = False

    try:
        supabase_ok = check_supabase()
    except Exception as e:
        supabase_ok = False

    return {
        "sqlite": {
            "status": "connected" if sqlite_ok else "disconnected",
            "path": settings.sqlite_db_path,
        },
        "supabase": {
            "status": "connected" if supabase_ok else "disconnected",
            "url": settings.supabase_url[:30] + "..." if settings.supabase_url else "not configured",
        },
        "overall": "healthy" if (sqlite_ok and supabase_ok) else "degraded",
    }


# === API Routers ===
from app.api import stocks_router, analysis_router

app.include_router(stocks_router, prefix="/api/stocks", tags=["Stocks"])
app.include_router(analysis_router, prefix="/api/analysis", tags=["Analysis"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )

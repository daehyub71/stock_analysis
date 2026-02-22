"""
API 통합 테스트
- FastAPI 엔드포인트 테스트
- 데이터 흐름 검증
"""

import pytest

from app.main import app


@pytest.fixture
def client():
    """동기 테스트 클라이언트"""
    from fastapi.testclient import TestClient
    return TestClient(app)


class TestHealthEndpoints:
    """헬스 체크 테스트"""

    def test_root(self, client):
        """GET / → 앱 정보"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "status" in data

    def test_health(self, client):
        """GET /health → OK"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestStocksAPI:
    """종목 API 테스트"""

    def test_get_stocks(self, client):
        """GET /api/stocks → 페이지네이션 응답"""
        response = client.get("/api/stocks")
        assert response.status_code == 200
        data = response.json()
        # 페이지네이션 구조: {items: [], page, pageSize, total, totalPages}
        assert "items" in data
        assert isinstance(data["items"], list)
        assert "total" in data
        assert "page" in data

    def test_get_sectors(self, client):
        """GET /api/stocks/sectors → 업종 목록"""
        response = client.get("/api/stocks/sectors")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_stock_detail(self, client):
        """GET /api/stocks/{code} → 종목 상세"""
        response = client.get("/api/stocks/005930")
        # 존재하면 200, 없으면 404
        assert response.status_code in (200, 404)


class TestAnalysisAPI:
    """분석 API 테스트"""

    def test_get_ranking(self, client):
        """GET /api/analysis/ranking → 순위"""
        response = client.get("/api/analysis/ranking")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_analysis(self, client):
        """GET /api/analysis/{code} → 분석 결과"""
        response = client.get("/api/analysis/005930")
        assert response.status_code in (200, 404)


class TestPortfolioAPI:
    """포트폴리오 API 테스트"""

    def test_get_portfolios(self, client):
        """GET /api/portfolios → 포트폴리오 목록"""
        response = client.get("/api/portfolios")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_portfolio_crud(self, client):
        """포트폴리오 CRUD 플로우"""
        # 생성
        create_resp = client.post(
            "/api/portfolios",
            json={"name": "테스트_pytest_임시"}
        )
        assert create_resp.status_code == 200
        portfolio = create_resp.json()
        pid = portfolio["id"]

        # 조회
        get_resp = client.get(f"/api/portfolios/{pid}")
        assert get_resp.status_code == 200
        detail = get_resp.json()
        assert detail["name"] == "테스트_pytest_임시"

        # 수정
        update_resp = client.put(
            f"/api/portfolios/{pid}",
            json={"name": "수정된_pytest_임시"}
        )
        assert update_resp.status_code == 200

        # 삭제
        delete_resp = client.delete(f"/api/portfolios/{pid}")
        assert delete_resp.status_code == 200

    def test_portfolio_not_found(self, client):
        """존재하지 않는 포트폴리오 → 404"""
        response = client.get("/api/portfolios/999999")
        assert response.status_code == 404


class TestBacktestAPI:
    """백테스트 API 테스트"""

    def test_get_date_range(self, client):
        """GET /api/backtest/{code}/date-range → 가용 기간"""
        response = client.get("/api/backtest/005930/date-range")
        assert response.status_code in (200, 404)


class TestAlertsAPI:
    """알림 API 테스트"""

    def test_get_score_changes(self, client):
        """GET /api/alerts/score-changes → 점수 변화 dict"""
        response = client.get("/api/alerts/score-changes")
        assert response.status_code == 200
        data = response.json()
        # {changes: [], count: 0, threshold: 5.0}
        assert "changes" in data
        assert "count" in data
        assert isinstance(data["changes"], list)

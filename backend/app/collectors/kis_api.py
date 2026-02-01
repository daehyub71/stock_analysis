"""
KIS (Korea Investment & Securities) API Collector
- 한국투자증권 Open API를 통한 주가 데이터 수집
- https://apiportal.koreainvestment.com/
"""

import os
import time
import requests
from datetime import datetime, timedelta
from typing import Optional
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


class KISApiClient:
    """한국투자증권 API 클라이언트"""

    BASE_URL = "https://openapi.koreainvestment.com:9443"
    TOKEN_URL = "/oauth2/tokenP"

    def __init__(self):
        self.app_key = os.environ.get("KIS_APP_KEY", "")
        self.app_secret = os.environ.get("KIS_APP_SECRET", "")
        self.account_type = os.environ.get("KIS_ACCOUNT_TYPE", "VIRTUAL")
        self.cano = os.environ.get("KIS_CANO", "")

        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None

        # Rate limit: 초당 20건
        self._last_request_time = 0
        self._min_interval = 0.05  # 50ms

    def _rate_limit(self):
        """Rate limit 적용"""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_request_time = time.time()

    def _get_access_token(self) -> str:
        """OAuth 토큰 발급/갱신"""
        # 토큰이 유효하면 재사용
        if self._access_token and self._token_expires_at:
            if datetime.now() < self._token_expires_at - timedelta(minutes=5):
                return self._access_token

        url = f"{self.BASE_URL}{self.TOKEN_URL}"
        headers = {"content-type": "application/json"}
        body = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
        }

        try:
            response = requests.post(url, headers=headers, json=body, timeout=10)
            response.raise_for_status()
            data = response.json()

            self._access_token = data.get("access_token")
            # 토큰 만료 시간 (보통 24시간)
            expires_in = int(data.get("expires_in", 86400))
            self._token_expires_at = datetime.now() + timedelta(seconds=expires_in)

            return self._access_token
        except Exception as e:
            print(f"❌ KIS 토큰 발급 실패: {e}")
            raise

    def _get_headers(self, tr_id: str) -> dict:
        """API 요청 헤더 생성"""
        token = self._get_access_token()
        return {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": tr_id,
        }

    def _request(
        self,
        method: str,
        path: str,
        tr_id: str,
        params: dict = None,
        body: dict = None,
        retries: int = 3,
    ) -> dict:
        """API 요청 (재시도 로직 포함)"""
        self._rate_limit()

        url = f"{self.BASE_URL}{path}"
        headers = self._get_headers(tr_id)

        for attempt in range(retries):
            try:
                if method == "GET":
                    response = requests.get(
                        url, headers=headers, params=params, timeout=10
                    )
                else:
                    response = requests.post(
                        url, headers=headers, json=body, timeout=10
                    )

                response.raise_for_status()
                data = response.json()

                # API 응답 코드 확인
                rt_cd = data.get("rt_cd", "1")
                if rt_cd != "0":
                    msg = data.get("msg1", "Unknown error")
                    raise Exception(f"KIS API Error: {msg}")

                return data

            except requests.exceptions.RequestException as e:
                if attempt < retries - 1:
                    wait_time = (attempt + 1) * 2  # 2, 4, 6초
                    print(f"⚠️ KIS API 요청 실패, {wait_time}초 후 재시도... ({e})")
                    time.sleep(wait_time)
                else:
                    raise

    def get_current_price(self, stock_code: str) -> dict:
        """
        현재가 조회
        - TR_ID: FHKST01010100 (주식현재가 시세)
        """
        path = "/uapi/domestic-stock/v1/quotations/inquire-price"
        tr_id = "FHKST01010100"
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",  # J: 주식
            "FID_INPUT_ISCD": stock_code,
        }

        data = self._request("GET", path, tr_id, params=params)
        output = data.get("output", {})

        return {
            "stock_code": stock_code,
            "current_price": int(output.get("stck_prpr", 0)),
            "change": int(output.get("prdy_vrss", 0)),
            "change_rate": float(output.get("prdy_ctrt", 0)),
            "volume": int(output.get("acml_vol", 0)),
            "trading_value": int(output.get("acml_tr_pbmn", 0)),
            "high": int(output.get("stck_hgpr", 0)),
            "low": int(output.get("stck_lwpr", 0)),
            "open": int(output.get("stck_oprc", 0)),
            "prev_close": int(output.get("stck_sdpr", 0)),
            "per": float(output.get("per", 0)) if output.get("per") else None,
            "pbr": float(output.get("pbr", 0)) if output.get("pbr") else None,
            "timestamp": datetime.now().isoformat(),
        }

    def get_daily_prices(
        self,
        stock_code: str,
        start_date: str = None,
        end_date: str = None,
        period: str = "D",  # D: 일, W: 주, M: 월
        limit: int = 100,
    ) -> list[dict]:
        """
        일별 시세 조회
        - TR_ID: FHKST01010400 (주식현재가 일별)
        """
        path = "/uapi/domestic-stock/v1/quotations/inquire-daily-price"
        tr_id = "FHKST01010400"

        if not end_date:
            end_date = datetime.now().strftime("%Y%m%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")

        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": stock_code,
            "FID_PERIOD_DIV_CODE": period,
            "FID_ORG_ADJ_PRC": "0",  # 0: 수정주가, 1: 원주가
        }

        data = self._request("GET", path, tr_id, params=params)
        output = data.get("output", [])

        results = []
        for item in output[:limit]:
            date_str = item.get("stck_bsop_date", "")
            if not date_str:
                continue

            results.append({
                "stock_code": stock_code,
                "date": f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}",
                "open": int(item.get("stck_oprc", 0)),
                "high": int(item.get("stck_hgpr", 0)),
                "low": int(item.get("stck_lwpr", 0)),
                "close": int(item.get("stck_clpr", 0)),
                "volume": int(item.get("acml_vol", 0)),
                "trading_value": int(item.get("acml_tr_pbmn", 0)),
                "change_rate": float(item.get("prdy_ctrt", 0)),
            })

        return results

    def get_daily_chart_prices(
        self,
        stock_code: str,
        start_date: str,
        end_date: str,
    ) -> list[dict]:
        """
        일별 차트 시세 조회 (기간 지정)
        - TR_ID: FHKST03010100 (주식현재가 일별차트)
        """
        path = "/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"
        tr_id = "FHKST03010100"

        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": stock_code,
            "FID_INPUT_DATE_1": start_date.replace("-", ""),
            "FID_INPUT_DATE_2": end_date.replace("-", ""),
            "FID_PERIOD_DIV_CODE": "D",
            "FID_ORG_ADJ_PRC": "0",
        }

        data = self._request("GET", path, tr_id, params=params)
        output2 = data.get("output2", [])

        results = []
        for item in output2:
            date_str = item.get("stck_bsop_date", "")
            if not date_str:
                continue

            results.append({
                "stock_code": stock_code,
                "date": f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}",
                "open": int(item.get("stck_oprc", 0)),
                "high": int(item.get("stck_hgpr", 0)),
                "low": int(item.get("stck_lwpr", 0)),
                "close": int(item.get("stck_clpr", 0)),
                "volume": int(item.get("acml_vol", 0)),
                "trading_value": int(item.get("acml_tr_pbmn", 0)),
            })

        return results

    def get_volume_rank(self, limit: int = 30) -> list[dict]:
        """
        거래량 순위 조회
        - TR_ID: FHPST01710000 (거래량순위)
        """
        path = "/uapi/domestic-stock/v1/quotations/volume-rank"
        tr_id = "FHPST01710000"

        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_COND_SCR_DIV_CODE": "20101",
            "FID_INPUT_ISCD": "0000",
            "FID_DIV_CLS_CODE": "0",
            "FID_BLNG_CLS_CODE": "0",
            "FID_TRGT_CLS_CODE": "111111111",
            "FID_TRGT_EXLS_CLS_CODE": "000000",
            "FID_INPUT_PRICE_1": "0",
            "FID_INPUT_PRICE_2": "0",
            "FID_VOL_CNT": "0",
            "FID_INPUT_DATE_1": "",
        }

        data = self._request("GET", path, tr_id, params=params)
        output = data.get("output", [])

        results = []
        for item in output[:limit]:
            results.append({
                "rank": int(item.get("data_rank", 0)),
                "stock_code": item.get("mksc_shrn_iscd", ""),
                "stock_name": item.get("hts_kor_isnm", ""),
                "current_price": int(item.get("stck_prpr", 0)),
                "change_rate": float(item.get("prdy_ctrt", 0)),
                "volume": int(item.get("acml_vol", 0)),
                "trading_value": int(item.get("acml_tr_pbmn", 0)),
            })

        return results

    def check_connection(self) -> bool:
        """연결 확인"""
        try:
            self._get_access_token()
            return True
        except Exception:
            return False


# 싱글톤 인스턴스
_client: Optional[KISApiClient] = None


def get_kis_client() -> KISApiClient:
    """KIS API 클라이언트 싱글톤"""
    global _client
    if _client is None:
        _client = KISApiClient()
    return _client


# === 편의 함수 ===

def get_current_price(stock_code: str) -> dict:
    """현재가 조회"""
    return get_kis_client().get_current_price(stock_code)


def get_daily_prices(
    stock_code: str,
    start_date: str = None,
    end_date: str = None,
    limit: int = 100,
) -> list[dict]:
    """일별 시세 조회"""
    return get_kis_client().get_daily_prices(stock_code, start_date, end_date, limit=limit)


def check_kis_connection() -> bool:
    """KIS API 연결 확인"""
    return get_kis_client().check_connection()


if __name__ == "__main__":
    # 테스트
    if check_kis_connection():
        print("✅ KIS API 연결 성공")

        # 삼성전자 현재가 조회
        price = get_current_price("005930")
        print(f"삼성전자 현재가: {price['current_price']:,}원")
    else:
        print("❌ KIS API 연결 실패 (API 키 확인 필요)")

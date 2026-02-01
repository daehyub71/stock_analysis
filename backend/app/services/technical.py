"""
Technical Analysis Service
- 기술지표 기반 점수 계산 (30점 만점)

점수 구성:
- MA 배열 점수: 6점
- MA 이격도 점수: 6점
- RSI 점수: 5점
- MACD 점수: 5점
- 거래량 점수: 8점
"""

from typing import Optional

from app.analyzers.indicators import TechnicalIndicators, calculate_indicators


class TechnicalAnalyzer:
    """기술분석 점수 계산기"""

    # 최대 점수
    MAX_MA_ARRANGEMENT = 6.0   # MA 배열
    MAX_MA_DIVERGENCE = 6.0    # MA 이격도
    MAX_RSI = 5.0              # RSI
    MAX_MACD = 5.0             # MACD
    MAX_VOLUME = 8.0           # 거래량

    MAX_TOTAL = 30.0           # 기술분석 총점

    def __init__(self, stock_code: str, indicators: Optional[dict] = None):
        """
        Args:
            stock_code: 종목코드
            indicators: 기술지표 (없으면 자동 계산)
        """
        self.stock_code = stock_code

        if indicators:
            self.indicators = indicators
        else:
            self.indicators = calculate_indicators(stock_code)

    @property
    def has_data(self) -> bool:
        """데이터 존재 여부"""
        return self.indicators.get("has_data", False)

    # === MA 배열 점수 (6점) ===

    def calc_ma_arrangement(self) -> tuple[float, str]:
        """
        MA 배열 점수 계산

        정배열: 현재가 > MA5 > MA20 > MA60 > MA120 → 6점
        역배열: 현재가 < MA5 < MA20 < MA60 < MA120 → 0점
        중간 상태: 배열 정도에 따라 1~5점

        Returns:
            (점수, 설명)
        """
        if not self.has_data:
            return 3.0, "데이터 없음 (중립)"

        price = self.indicators.get("current_price")
        ma5 = self.indicators.get("ma5")
        ma20 = self.indicators.get("ma20")
        ma60 = self.indicators.get("ma60")
        ma120 = self.indicators.get("ma120")

        # 데이터 부족
        if not all([price, ma5, ma20]):
            return 3.0, "MA 데이터 부족"

        # 정배열 체크
        values = [price, ma5, ma20]
        if ma60:
            values.append(ma60)
        if ma120:
            values.append(ma120)

        # 각 단계별 정렬 확인
        score = 0
        total_pairs = len(values) - 1

        for i in range(total_pairs):
            if values[i] > values[i + 1]:
                score += 1

        # 점수 계산 (0~6점)
        ratio = score / total_pairs
        final_score = round(ratio * self.MAX_MA_ARRANGEMENT, 1)

        # 설명 생성
        if ratio >= 1.0:
            desc = "완전 정배열"
        elif ratio >= 0.75:
            desc = "정배열 우세"
        elif ratio >= 0.5:
            desc = "혼조세"
        elif ratio >= 0.25:
            desc = "역배열 우세"
        else:
            desc = "완전 역배열"

        return final_score, desc

    # === MA 이격도 점수 (6점) ===

    def calc_ma_divergence(self) -> tuple[float, str]:
        """
        MA 이격도 점수 계산

        이격도 = (현재가 - MA20) / MA20 * 100

        +10% 이상: 과열 (2점)
        +5% ~ +10%: 상승세 (5점)
        0% ~ +5%: 적정 상승 (6점)
        -5% ~ 0%: 적정 하락 (4점)
        -10% ~ -5%: 하락세 (2점)
        -10% 이하: 과매도 (3점, 반등 기대)

        Returns:
            (점수, 설명)
        """
        if not self.has_data:
            return 3.0, "데이터 없음"

        price = self.indicators.get("current_price")
        ma20 = self.indicators.get("ma20")

        if not price or not ma20:
            return 3.0, "MA20 데이터 없음"

        divergence = (price - ma20) / ma20 * 100

        if divergence >= 10:
            return 2.0, f"과열 (이격 +{divergence:.1f}%)"
        elif divergence >= 5:
            return 5.0, f"상승세 (이격 +{divergence:.1f}%)"
        elif divergence >= 0:
            return 6.0, f"적정 상승 (이격 +{divergence:.1f}%)"
        elif divergence >= -5:
            return 4.0, f"적정 하락 (이격 {divergence:.1f}%)"
        elif divergence >= -10:
            return 2.0, f"하락세 (이격 {divergence:.1f}%)"
        else:
            return 3.0, f"과매도 (이격 {divergence:.1f}%)"

    # === RSI 점수 (5점) ===

    def calc_rsi_score(self) -> tuple[float, str]:
        """
        RSI(14) 점수 계산

        30 미만: 과매도 (4점, 반등 기대)
        30~40: 저평가 (5점)
        40~60: 중립 (3점)
        60~70: 고평가 (2점)
        70 이상: 과매수 (1점)

        Returns:
            (점수, 설명)
        """
        if not self.has_data:
            return 2.5, "데이터 없음"

        rsi = self.indicators.get("rsi14")

        if rsi is None:
            return 2.5, "RSI 계산 불가"

        if rsi < 30:
            return 4.0, f"과매도 (RSI {rsi:.1f})"
        elif rsi < 40:
            return 5.0, f"저평가 (RSI {rsi:.1f})"
        elif rsi < 60:
            return 3.0, f"중립 (RSI {rsi:.1f})"
        elif rsi < 70:
            return 2.0, f"고평가 (RSI {rsi:.1f})"
        else:
            return 1.0, f"과매수 (RSI {rsi:.1f})"

    # === MACD 점수 (5점) ===

    def calc_macd_score(self) -> tuple[float, str]:
        """
        MACD 점수 계산

        MACD > 0 & Histogram > 0: 강한 상승 (5점)
        MACD > 0 & Histogram <= 0: 상승 둔화 (3점)
        MACD <= 0 & Histogram > 0: 하락 둔화/반등 (4점)
        MACD <= 0 & Histogram <= 0: 강한 하락 (1점)

        Returns:
            (점수, 설명)
        """
        if not self.has_data:
            return 2.5, "데이터 없음"

        macd = self.indicators.get("macd")
        hist = self.indicators.get("macd_hist")

        if macd is None or hist is None:
            return 2.5, "MACD 계산 불가"

        if macd > 0 and hist > 0:
            return 5.0, "강한 상승세"
        elif macd > 0 and hist <= 0:
            return 3.0, "상승 둔화"
        elif macd <= 0 and hist > 0:
            return 4.0, "하락 둔화 (반등 신호)"
        else:
            return 1.0, "강한 하락세"

    # === 거래량 점수 (8점) ===

    def calc_volume_score(self) -> tuple[float, str]:
        """
        거래량 점수 계산

        거래량 비율 = 당일 거래량 / 20일 평균 거래량

        2.0 이상: 급증 (6점, 관심 필요)
        1.5 ~ 2.0: 활발 (8점)
        1.0 ~ 1.5: 보통 (6점)
        0.5 ~ 1.0: 저조 (4점)
        0.5 미만: 매우 저조 (2점)

        Returns:
            (점수, 설명)
        """
        if not self.has_data:
            return 4.0, "데이터 없음"

        volume_ratio = self.indicators.get("volume_ratio")

        if volume_ratio is None:
            return 4.0, "거래량 계산 불가"

        if volume_ratio >= 2.0:
            return 6.0, f"거래량 급증 ({volume_ratio:.1f}배)"
        elif volume_ratio >= 1.5:
            return 8.0, f"거래량 활발 ({volume_ratio:.1f}배)"
        elif volume_ratio >= 1.0:
            return 6.0, f"거래량 보통 ({volume_ratio:.1f}배)"
        elif volume_ratio >= 0.5:
            return 4.0, f"거래량 저조 ({volume_ratio:.1f}배)"
        else:
            return 2.0, f"거래량 매우 저조 ({volume_ratio:.1f}배)"

    # === 종합 점수 ===

    def calculate_total(self) -> dict:
        """
        기술분석 총점 계산 (30점 만점)

        Returns:
            점수 상세 딕셔너리
        """
        ma_arr_score, ma_arr_desc = self.calc_ma_arrangement()
        ma_div_score, ma_div_desc = self.calc_ma_divergence()
        rsi_score, rsi_desc = self.calc_rsi_score()
        macd_score, macd_desc = self.calc_macd_score()
        volume_score, volume_desc = self.calc_volume_score()

        total = ma_arr_score + ma_div_score + rsi_score + macd_score + volume_score

        return {
            "stock_code": self.stock_code,
            "has_data": self.has_data,
            "total_score": round(total, 1),
            "max_score": self.MAX_TOTAL,
            "details": {
                "ma_arrangement": {
                    "score": ma_arr_score,
                    "max": self.MAX_MA_ARRANGEMENT,
                    "description": ma_arr_desc,
                },
                "ma_divergence": {
                    "score": ma_div_score,
                    "max": self.MAX_MA_DIVERGENCE,
                    "description": ma_div_desc,
                },
                "rsi": {
                    "score": rsi_score,
                    "max": self.MAX_RSI,
                    "description": rsi_desc,
                },
                "macd": {
                    "score": macd_score,
                    "max": self.MAX_MACD,
                    "description": macd_desc,
                },
                "volume": {
                    "score": volume_score,
                    "max": self.MAX_VOLUME,
                    "description": volume_desc,
                },
            },
            "indicators": self.indicators,
        }


# === 편의 함수 ===

def calculate_technical_score(stock_code: str) -> dict:
    """종목 기술분석 점수 계산"""
    analyzer = TechnicalAnalyzer(stock_code)
    return analyzer.calculate_total()


def batch_technical_score(stock_codes: list[str]) -> dict[str, dict]:
    """여러 종목 기술분석 일괄 계산"""
    results = {}
    for code in stock_codes:
        results[code] = calculate_technical_score(code)
    return results


if __name__ == "__main__":
    print("=== Technical Analysis Service 테스트 ===\n")

    # 삼성전자 기술분석
    result = calculate_technical_score("005930")

    print(f"종목: {result['stock_code']}")
    print(f"기술분석 총점: {result['total_score']} / {result['max_score']}")
    print()

    for name, detail in result["details"].items():
        print(f"{name}: {detail['score']} / {detail['max']} ({detail['description']})")

    print("\n✅ 테스트 완료")

"""
Fundamental Analysis Service
- 기본분석 기반 점수 계산 (50점 만점)

점수 구성:
- PER 점수: 8점
- PBR 점수: 7점
- PSR 점수: 5점
- 매출 성장률: 6점
- 영업이익 성장률: 6점
- ROE 점수: 5점
- 영업이익률: 5점
- 부채비율: 4점
- 유동비율: 4점
"""

from typing import Optional

from app.db import supabase_db


class FundamentalAnalyzer:
    """기본분석 점수 계산기"""

    # 최대 점수
    MAX_PER = 8.0           # PER
    MAX_PBR = 7.0           # PBR
    MAX_PSR = 5.0           # PSR
    MAX_REVENUE_GROWTH = 6.0    # 매출 성장률
    MAX_OP_GROWTH = 6.0         # 영업이익 성장률
    MAX_ROE = 5.0           # ROE
    MAX_OP_MARGIN = 5.0     # 영업이익률
    MAX_DEBT_RATIO = 4.0    # 부채비율
    MAX_CURRENT_RATIO = 4.0 # 유동비율

    MAX_TOTAL = 50.0        # 기본분석 총점

    def __init__(self, stock_code: str, financials: Optional[dict] = None):
        """
        Args:
            stock_code: 종목코드
            financials: 재무 데이터 (없으면 Supabase에서 조회)
        """
        self.stock_code = stock_code
        self.stock_id: Optional[int] = None
        self.sector: Optional[str] = None
        self.sector_avg: Optional[dict] = None

        if financials:
            self.financials = financials
        else:
            self._load_from_db()

    def _load_from_db(self) -> None:
        """Supabase에서 재무 데이터 로드"""
        # 종목 정보 조회
        stock = supabase_db.get_stock_by_code(self.stock_code)
        if not stock:
            self.financials = {}
            return

        self.stock_id = stock.get("id")
        self.sector = stock.get("sector")

        # 재무 데이터 추출
        self.financials = {
            "per": stock.get("per"),
            "pbr": stock.get("pbr"),
            "psr": stock.get("psr"),
            "roe": stock.get("roe"),
            "revenue_growth": stock.get("revenue_growth"),
            "op_growth": stock.get("op_growth"),
            "op_margin": stock.get("op_margin"),
            "debt_ratio": stock.get("debt_ratio"),
            "current_ratio": stock.get("current_ratio"),
        }

        # 업종 평균 조회
        if self.sector:
            self.sector_avg = supabase_db.get_sector_average(self.sector)

    @property
    def has_data(self) -> bool:
        """데이터 존재 여부"""
        return bool(self.financials) and any(v is not None for v in self.financials.values())

    def _get_sector_avg(self, key: str, default: float) -> float:
        """업종 평균값 조회"""
        if self.sector_avg and key in self.sector_avg:
            return self.sector_avg[key] or default
        return default

    # === PER 점수 (8점) ===

    def calc_per_score(self) -> tuple[float, str]:
        """
        PER 점수 계산

        PER < 5: 8점 (저평가)
        5 <= PER < 10: 7점
        10 <= PER < 15: 5점
        15 <= PER < 20: 3점
        20 <= PER < 30: 2점
        PER >= 30 or 적자: 1점

        Returns:
            (점수, 설명)
        """
        per = self.financials.get("per")

        if per is None:
            return 4.0, "PER 데이터 없음"

        if per < 0:
            return 1.0, f"적자 (PER {per:.1f})"
        elif per < 5:
            return 8.0, f"저평가 (PER {per:.1f})"
        elif per < 10:
            return 7.0, f"양호 (PER {per:.1f})"
        elif per < 15:
            return 5.0, f"적정 (PER {per:.1f})"
        elif per < 20:
            return 3.0, f"다소 고평가 (PER {per:.1f})"
        elif per < 30:
            return 2.0, f"고평가 (PER {per:.1f})"
        else:
            return 1.0, f"과대평가 (PER {per:.1f})"

    # === PBR 점수 (7점) ===

    def calc_pbr_score(self) -> tuple[float, str]:
        """
        PBR 점수 계산

        PBR < 0.5: 7점 (극저평가)
        0.5 <= PBR < 1.0: 6점
        1.0 <= PBR < 1.5: 4점
        1.5 <= PBR < 2.0: 3점
        2.0 <= PBR < 3.0: 2점
        PBR >= 3.0: 1점

        Returns:
            (점수, 설명)
        """
        pbr = self.financials.get("pbr")

        if pbr is None:
            return 3.5, "PBR 데이터 없음"

        if pbr < 0:
            return 1.0, f"자본잠식 (PBR {pbr:.2f})"
        elif pbr < 0.5:
            return 7.0, f"극저평가 (PBR {pbr:.2f})"
        elif pbr < 1.0:
            return 6.0, f"저평가 (PBR {pbr:.2f})"
        elif pbr < 1.5:
            return 4.0, f"적정 (PBR {pbr:.2f})"
        elif pbr < 2.0:
            return 3.0, f"다소 고평가 (PBR {pbr:.2f})"
        elif pbr < 3.0:
            return 2.0, f"고평가 (PBR {pbr:.2f})"
        else:
            return 1.0, f"과대평가 (PBR {pbr:.2f})"

    # === PSR 점수 (5점) ===

    def calc_psr_score(self) -> tuple[float, str]:
        """
        PSR 점수 계산

        PSR < 0.5: 5점 (저평가)
        0.5 <= PSR < 1.0: 4점
        1.0 <= PSR < 2.0: 3점
        2.0 <= PSR < 4.0: 2점
        PSR >= 4.0: 1점

        Returns:
            (점수, 설명)
        """
        psr = self.financials.get("psr")

        if psr is None:
            return 2.5, "PSR 데이터 없음"

        if psr < 0.5:
            return 5.0, f"저평가 (PSR {psr:.2f})"
        elif psr < 1.0:
            return 4.0, f"양호 (PSR {psr:.2f})"
        elif psr < 2.0:
            return 3.0, f"적정 (PSR {psr:.2f})"
        elif psr < 4.0:
            return 2.0, f"다소 고평가 (PSR {psr:.2f})"
        else:
            return 1.0, f"고평가 (PSR {psr:.2f})"

    # === 매출 성장률 점수 (6점) ===

    def calc_revenue_growth_score(self) -> tuple[float, str]:
        """
        매출 성장률 점수 계산 (YoY)

        30% 이상: 6점 (고성장)
        20% ~ 30%: 5점
        10% ~ 20%: 4점
        0% ~ 10%: 3점
        -10% ~ 0%: 2점
        -10% 미만: 1점

        Returns:
            (점수, 설명)
        """
        growth = self.financials.get("revenue_growth")

        if growth is None:
            return 3.0, "매출 성장률 데이터 없음"

        if growth >= 30:
            return 6.0, f"고성장 (+{growth:.1f}%)"
        elif growth >= 20:
            return 5.0, f"강한 성장 (+{growth:.1f}%)"
        elif growth >= 10:
            return 4.0, f"양호한 성장 (+{growth:.1f}%)"
        elif growth >= 0:
            return 3.0, f"안정 ({growth:+.1f}%)"
        elif growth >= -10:
            return 2.0, f"소폭 감소 ({growth:.1f}%)"
        else:
            return 1.0, f"큰 폭 감소 ({growth:.1f}%)"

    # === 영업이익 성장률 점수 (6점) ===

    def calc_op_growth_score(self) -> tuple[float, str]:
        """
        영업이익 성장률 점수 계산 (YoY)

        50% 이상: 6점 (급성장)
        30% ~ 50%: 5점
        10% ~ 30%: 4점
        0% ~ 10%: 3점
        -20% ~ 0%: 2점
        -20% 미만: 1점

        Returns:
            (점수, 설명)
        """
        growth = self.financials.get("op_growth")

        if growth is None:
            return 3.0, "영업이익 성장률 데이터 없음"

        if growth >= 50:
            return 6.0, f"급성장 (+{growth:.1f}%)"
        elif growth >= 30:
            return 5.0, f"고성장 (+{growth:.1f}%)"
        elif growth >= 10:
            return 4.0, f"양호 (+{growth:.1f}%)"
        elif growth >= 0:
            return 3.0, f"안정 ({growth:+.1f}%)"
        elif growth >= -20:
            return 2.0, f"감소 ({growth:.1f}%)"
        else:
            return 1.0, f"급감 ({growth:.1f}%)"

    # === ROE 점수 (5점) ===

    def calc_roe_score(self) -> tuple[float, str]:
        """
        ROE 점수 계산

        20% 이상: 5점 (우수)
        15% ~ 20%: 4점
        10% ~ 15%: 3점
        5% ~ 10%: 2점
        5% 미만 or 음수: 1점

        Returns:
            (점수, 설명)
        """
        roe = self.financials.get("roe")

        if roe is None:
            return 2.5, "ROE 데이터 없음"

        if roe >= 20:
            return 5.0, f"우수 (ROE {roe:.1f}%)"
        elif roe >= 15:
            return 4.0, f"양호 (ROE {roe:.1f}%)"
        elif roe >= 10:
            return 3.0, f"적정 (ROE {roe:.1f}%)"
        elif roe >= 5:
            return 2.0, f"저조 (ROE {roe:.1f}%)"
        else:
            return 1.0, f"부진 (ROE {roe:.1f}%)"

    # === 영업이익률 점수 (5점) ===

    def calc_op_margin_score(self) -> tuple[float, str]:
        """
        영업이익률 점수 계산

        20% 이상: 5점 (우수)
        15% ~ 20%: 4점
        10% ~ 15%: 3점
        5% ~ 10%: 2점
        5% 미만 or 적자: 1점

        Returns:
            (점수, 설명)
        """
        margin = self.financials.get("op_margin")

        if margin is None:
            return 2.5, "영업이익률 데이터 없음"

        if margin >= 20:
            return 5.0, f"우수 (OPM {margin:.1f}%)"
        elif margin >= 15:
            return 4.0, f"양호 (OPM {margin:.1f}%)"
        elif margin >= 10:
            return 3.0, f"적정 (OPM {margin:.1f}%)"
        elif margin >= 5:
            return 2.0, f"저조 (OPM {margin:.1f}%)"
        else:
            return 1.0, f"부진 (OPM {margin:.1f}%)"

    # === 부채비율 점수 (4점) ===

    def calc_debt_ratio_score(self) -> tuple[float, str]:
        """
        부채비율 점수 계산 (낮을수록 좋음)

        50% 미만: 4점 (안정)
        50% ~ 100%: 3점
        100% ~ 150%: 2점
        150% ~ 200%: 1.5점
        200% 이상: 1점

        Returns:
            (점수, 설명)
        """
        ratio = self.financials.get("debt_ratio")

        if ratio is None:
            return 2.0, "부채비율 데이터 없음"

        if ratio < 50:
            return 4.0, f"우량 (부채 {ratio:.0f}%)"
        elif ratio < 100:
            return 3.0, f"안정 (부채 {ratio:.0f}%)"
        elif ratio < 150:
            return 2.0, f"보통 (부채 {ratio:.0f}%)"
        elif ratio < 200:
            return 1.5, f"주의 (부채 {ratio:.0f}%)"
        else:
            return 1.0, f"위험 (부채 {ratio:.0f}%)"

    # === 유동비율 점수 (4점) ===

    def calc_current_ratio_score(self) -> tuple[float, str]:
        """
        유동비율 점수 계산 (높을수록 좋음)

        200% 이상: 4점 (매우 안정)
        150% ~ 200%: 3점
        100% ~ 150%: 2점
        100% 미만: 1점

        Returns:
            (점수, 설명)
        """
        ratio = self.financials.get("current_ratio")

        if ratio is None:
            return 2.0, "유동비율 데이터 없음"

        if ratio >= 200:
            return 4.0, f"매우 안정 (유동 {ratio:.0f}%)"
        elif ratio >= 150:
            return 3.0, f"안정 (유동 {ratio:.0f}%)"
        elif ratio >= 100:
            return 2.0, f"보통 (유동 {ratio:.0f}%)"
        else:
            return 1.0, f"주의 (유동 {ratio:.0f}%)"

    # === 종합 점수 ===

    def calculate_total(self) -> dict:
        """
        기본분석 총점 계산 (50점 만점)

        Returns:
            점수 상세 딕셔너리
        """
        per_score, per_desc = self.calc_per_score()
        pbr_score, pbr_desc = self.calc_pbr_score()
        psr_score, psr_desc = self.calc_psr_score()
        rev_score, rev_desc = self.calc_revenue_growth_score()
        op_score, op_desc = self.calc_op_growth_score()
        roe_score, roe_desc = self.calc_roe_score()
        margin_score, margin_desc = self.calc_op_margin_score()
        debt_score, debt_desc = self.calc_debt_ratio_score()
        current_score, current_desc = self.calc_current_ratio_score()

        total = (
            per_score + pbr_score + psr_score +
            rev_score + op_score +
            roe_score + margin_score +
            debt_score + current_score
        )

        return {
            "stock_code": self.stock_code,
            "stock_id": self.stock_id,
            "sector": self.sector,
            "has_data": self.has_data,
            "total_score": round(total, 1),
            "max_score": self.MAX_TOTAL,
            "details": {
                "per": {
                    "score": per_score,
                    "max": self.MAX_PER,
                    "description": per_desc,
                },
                "pbr": {
                    "score": pbr_score,
                    "max": self.MAX_PBR,
                    "description": pbr_desc,
                },
                "psr": {
                    "score": psr_score,
                    "max": self.MAX_PSR,
                    "description": psr_desc,
                },
                "revenue_growth": {
                    "score": rev_score,
                    "max": self.MAX_REVENUE_GROWTH,
                    "description": rev_desc,
                },
                "op_growth": {
                    "score": op_score,
                    "max": self.MAX_OP_GROWTH,
                    "description": op_desc,
                },
                "roe": {
                    "score": roe_score,
                    "max": self.MAX_ROE,
                    "description": roe_desc,
                },
                "op_margin": {
                    "score": margin_score,
                    "max": self.MAX_OP_MARGIN,
                    "description": margin_desc,
                },
                "debt_ratio": {
                    "score": debt_score,
                    "max": self.MAX_DEBT_RATIO,
                    "description": debt_desc,
                },
                "current_ratio": {
                    "score": current_score,
                    "max": self.MAX_CURRENT_RATIO,
                    "description": current_desc,
                },
            },
            "financials": self.financials,
            "sector_avg": self.sector_avg,
        }


# === 편의 함수 ===

def calculate_fundamental_score(stock_code: str) -> dict:
    """종목 기본분석 점수 계산"""
    analyzer = FundamentalAnalyzer(stock_code)
    return analyzer.calculate_total()


def batch_fundamental_score(stock_codes: list[str]) -> dict[str, dict]:
    """여러 종목 기본분석 일괄 계산"""
    results = {}
    for code in stock_codes:
        results[code] = calculate_fundamental_score(code)
    return results


if __name__ == "__main__":
    print("=== Fundamental Analysis Service 테스트 ===\n")

    # 테스트용 더미 데이터
    test_financials = {
        "per": 12.5,
        "pbr": 1.2,
        "psr": 0.8,
        "revenue_growth": 15.3,
        "op_growth": 22.5,
        "roe": 14.2,
        "op_margin": 11.5,
        "debt_ratio": 85.0,
        "current_ratio": 165.0,
    }

    analyzer = FundamentalAnalyzer("005930", financials=test_financials)
    result = analyzer.calculate_total()

    print(f"종목: {result['stock_code']}")
    print(f"기본분석 총점: {result['total_score']} / {result['max_score']}")
    print()

    for name, detail in result["details"].items():
        print(f"{name}: {detail['score']} / {detail['max']} ({detail['description']})")

    print("\n✅ 테스트 완료")

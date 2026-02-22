"""
기본분석 점수 계산 단위 테스트
- FundamentalAnalyzer (50점 만점)
"""

import pytest

from app.services.fundamental import FundamentalAnalyzer


class TestPERScore:
    """PER 점수 테스트 (8점 만점)"""

    @pytest.mark.parametrize("per, expected_score", [
        (3.0, 8.0),    # < 5: 저평가
        (8.0, 7.0),    # 5-10: 양호
        (12.0, 5.0),   # 10-15: 적정
        (18.0, 3.0),   # 15-20: 다소 고평가
        (25.0, 2.0),   # 20-30: 고평가
        (40.0, 1.0),   # >= 30: 과대평가
        (-5.0, 1.0),   # 적자
    ])
    def test_per_ranges(self, per, expected_score):
        analyzer = FundamentalAnalyzer("005930", {"per": per})
        score, _ = analyzer.calc_per_score()
        assert score == expected_score

    def test_per_none(self):
        """PER 없음 → 4점"""
        analyzer = FundamentalAnalyzer("005930", {"per": None})
        score, _ = analyzer.calc_per_score()
        assert score == 4.0


class TestPBRScore:
    """PBR 점수 테스트 (7점 만점)"""

    @pytest.mark.parametrize("pbr, expected_score", [
        (0.3, 7.0),    # < 0.5: 극저평가
        (0.8, 6.0),    # 0.5-1.0: 저평가
        (1.2, 4.0),    # 1.0-1.5: 적정
        (1.8, 3.0),    # 1.5-2.0: 다소 고평가
        (2.5, 2.0),    # 2.0-3.0: 고평가
        (4.0, 1.0),    # >= 3.0: 과대평가
        (-0.5, 1.0),   # 자본잠식
    ])
    def test_pbr_ranges(self, pbr, expected_score):
        analyzer = FundamentalAnalyzer("005930", {"pbr": pbr})
        score, _ = analyzer.calc_pbr_score()
        assert score == expected_score


class TestPSRScore:
    """PSR 점수 테스트 (5점 만점)"""

    @pytest.mark.parametrize("psr, expected_score", [
        (0.3, 5.0),    # < 0.5
        (0.8, 4.0),    # 0.5-1.0
        (1.5, 3.0),    # 1.0-2.0
        (3.0, 2.0),    # 2.0-4.0
        (5.0, 1.0),    # >= 4.0
    ])
    def test_psr_ranges(self, psr, expected_score):
        analyzer = FundamentalAnalyzer("005930", {"psr": psr})
        score, _ = analyzer.calc_psr_score()
        assert score == expected_score


class TestRevenueGrowthScore:
    """매출 성장률 점수 테스트 (6점 만점)"""

    @pytest.mark.parametrize("growth, expected_score", [
        (35.0, 6.0),   # >= 30%
        (25.0, 5.0),   # 20-30%
        (15.0, 4.0),   # 10-20%
        (5.0, 3.0),    # 0-10%
        (-5.0, 2.0),   # -10~0%
        (-15.0, 1.0),  # < -10%
    ])
    def test_revenue_growth_ranges(self, growth, expected_score):
        analyzer = FundamentalAnalyzer("005930", {"revenue_growth": growth})
        score, _ = analyzer.calc_revenue_growth_score()
        assert score == expected_score


class TestOPGrowthScore:
    """영업이익 성장률 점수 테스트 (6점 만점)"""

    @pytest.mark.parametrize("growth, expected_score", [
        (55.0, 6.0),   # >= 50%
        (40.0, 5.0),   # 30-50%
        (20.0, 4.0),   # 10-30%
        (5.0, 3.0),    # 0-10%
        (-10.0, 2.0),  # -20~0%
        (-30.0, 1.0),  # < -20%
    ])
    def test_op_growth_ranges(self, growth, expected_score):
        analyzer = FundamentalAnalyzer("005930", {"op_growth": growth})
        score, _ = analyzer.calc_op_growth_score()
        assert score == expected_score


class TestROEScore:
    """ROE 점수 테스트 (5점 만점)"""

    @pytest.mark.parametrize("roe, expected_score", [
        (25.0, 5.0),   # >= 20%
        (17.0, 4.0),   # 15-20%
        (12.0, 3.0),   # 10-15%
        (7.0, 2.0),    # 5-10%
        (3.0, 1.0),    # < 5%
    ])
    def test_roe_ranges(self, roe, expected_score):
        analyzer = FundamentalAnalyzer("005930", {"roe": roe})
        score, _ = analyzer.calc_roe_score()
        assert score == expected_score


class TestOPMarginScore:
    """영업이익률 점수 테스트 (5점 만점)"""

    @pytest.mark.parametrize("margin, expected_score", [
        (25.0, 5.0),   # >= 20%
        (17.0, 4.0),   # 15-20%
        (12.0, 3.0),   # 10-15%
        (7.0, 2.0),    # 5-10%
        (3.0, 1.0),    # < 5%
    ])
    def test_op_margin_ranges(self, margin, expected_score):
        analyzer = FundamentalAnalyzer("005930", {"op_margin": margin})
        score, _ = analyzer.calc_op_margin_score()
        assert score == expected_score


class TestDebtRatioScore:
    """부채비율 점수 테스트 (4점 만점)"""

    @pytest.mark.parametrize("ratio, expected_score", [
        (30.0, 4.0),    # < 50%
        (75.0, 3.0),    # 50-100%
        (120.0, 2.0),   # 100-150%
        (180.0, 1.5),   # 150-200%
        (250.0, 1.0),   # >= 200%
    ])
    def test_debt_ratio_ranges(self, ratio, expected_score):
        analyzer = FundamentalAnalyzer("005930", {"debt_ratio": ratio})
        score, _ = analyzer.calc_debt_ratio_score()
        assert score == expected_score


class TestCurrentRatioScore:
    """유동비율 점수 테스트 (4점 만점)"""

    @pytest.mark.parametrize("ratio, expected_score", [
        (250.0, 4.0),   # >= 200%
        (175.0, 3.0),   # 150-200%
        (120.0, 2.0),   # 100-150%
        (80.0, 1.0),    # < 100%
    ])
    def test_current_ratio_ranges(self, ratio, expected_score):
        analyzer = FundamentalAnalyzer("005930", {"current_ratio": ratio})
        score, _ = analyzer.calc_current_ratio_score()
        assert score == expected_score


class TestFundamentalTotal:
    """기본분석 총점 테스트"""

    def test_strong_stock_total(self, strong_financials):
        """우량주 총점"""
        analyzer = FundamentalAnalyzer("005930", strong_financials)
        result = analyzer.calculate_total()

        assert result["stock_code"] == "005930"
        assert result["has_data"] is True
        assert result["max_score"] == 50.0
        assert result["total_score"] > 35.0  # 우량주는 35점 이상

    def test_weak_stock_total(self, weak_financials):
        """부실주 총점"""
        analyzer = FundamentalAnalyzer("005930", weak_financials)
        result = analyzer.calculate_total()

        assert result["total_score"] < 20.0  # 부실주는 20점 미만

    def test_score_sum_matches(self, strong_financials):
        """세부 점수 합 == 총점"""
        analyzer = FundamentalAnalyzer("005930", strong_financials)
        result = analyzer.calculate_total()

        detail_sum = sum(d["score"] for d in result["details"].values())
        assert abs(detail_sum - result["total_score"]) < 0.01

    def test_empty_financials_gives_defaults(self):
        """데이터 없으면 기본값"""
        # 모든 값이 None인 dict 전달 (빈 dict는 falsy → DB 조회 시도)
        none_financials = {
            "per": None, "pbr": None, "psr": None,
            "revenue_growth": None, "op_growth": None,
            "roe": None, "op_margin": None,
            "debt_ratio": None, "current_ratio": None,
        }
        analyzer = FundamentalAnalyzer("XXXXXX", none_financials)
        result = analyzer.calculate_total()

        # 모든 항목 기본값: 4.0+3.5+2.5+3.0+3.0+2.5+2.5+2.0+2.0 = 25.0
        assert result["total_score"] == 25.0

    def test_all_nine_details(self, strong_financials):
        """9개 세부 항목 모두 존재"""
        analyzer = FundamentalAnalyzer("005930", strong_financials)
        result = analyzer.calculate_total()
        details = result["details"]

        expected_keys = [
            "per", "pbr", "psr", "revenue_growth", "op_growth",
            "roe", "op_margin", "debt_ratio", "current_ratio",
        ]
        for key in expected_keys:
            assert key in details
            assert "score" in details[key]
            assert "max" in details[key]

"""
LLM Commentary Service
- OpenAI를 사용하여 분석 결과에 대한 인간 친화적인 코멘트 생성
"""

import json
from typing import Optional
from openai import OpenAI

from app.config import settings


class CommentaryService:
    """분석 코멘트 생성 서비스"""

    def __init__(self):
        self.client = None
        if settings.openai_api_key:
            self.client = OpenAI(api_key=settings.openai_api_key)

    def _get_grade_description(self, grade: str) -> str:
        """등급별 설명"""
        descriptions = {
            "A+": "매우 우수 - 강력 매수 고려",
            "A": "우수 - 매수 고려",
            "B+": "양호 - 관심 종목",
            "B": "보통 - 시장 평균",
            "C+": "주의 - 신중한 접근 필요",
            "C": "경고 - 리스크 존재",
            "D": "위험 - 투자 주의",
            "F": "매우 위험 - 투자 비권장",
        }
        return descriptions.get(grade, "평가 불가")

    def generate_summary(
        self,
        stock_name: str,
        stock_code: str,
        total_score: float,
        grade: str,
        tech_score: float,
        fund_score: float,
        sent_score: float,
        tech_details: dict,
        fund_details: dict,
        sent_details: dict,
        indicators: dict,
        financials: dict,
    ) -> dict:
        """종합 분석 코멘트 생성"""

        if not self.client:
            return self._generate_fallback_summary(
                stock_name, total_score, grade, tech_score, fund_score, sent_score,
                tech_details, fund_details, indicators, financials
            )

        # 프롬프트 구성
        prompt = self._build_summary_prompt(
            stock_name, stock_code, total_score, grade,
            tech_score, fund_score, sent_score,
            tech_details, fund_details, sent_details,
            indicators, financials
        )

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """당신은 전문 주식 애널리스트입니다.
주어진 분석 데이터를 바탕으로 개인 투자자가 이해하기 쉬운 한국어로 분석 코멘트를 작성해주세요.
객관적 사실에 기반하되, 투자 판단에 도움이 되는 인사이트를 제공해주세요.
응답은 반드시 JSON 형식으로 해주세요."""
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            return result

        except Exception as e:
            print(f"OpenAI API error: {e}")
            return self._generate_fallback_summary(
                stock_name, total_score, grade, tech_score, fund_score, sent_score,
                tech_details, fund_details, indicators, financials
            )

    def _build_summary_prompt(
        self,
        stock_name: str,
        stock_code: str,
        total_score: float,
        grade: str,
        tech_score: float,
        fund_score: float,
        sent_score: float,
        tech_details: dict,
        fund_details: dict,
        sent_details: dict,
        indicators: dict,
        financials: dict,
    ) -> str:
        """분석 프롬프트 생성"""

        return f"""
다음 종목의 분석 데이터를 바탕으로 투자자를 위한 종합 분석 코멘트를 작성해주세요.

## 종목 정보
- 종목명: {stock_name}
- 종목코드: {stock_code}
- 종합점수: {total_score:.1f}/100점 (등급: {grade})

## 점수 구성
- 기술분석: {tech_score:.1f}/30점
- 기본분석: {fund_score:.1f}/50점
- 감정분석: {sent_score:.1f}/20점

## 기술분석 상세
- MA배열: {tech_details.get('maArrangement', {}).get('score', 0)}/6점 - {tech_details.get('maArrangement', {}).get('description', '')}
- MA이격도: {tech_details.get('maDivergence', {}).get('score', 0)}/6점 - {tech_details.get('maDivergence', {}).get('description', '')}
- RSI: {tech_details.get('rsi', {}).get('score', 0)}/5점 - {tech_details.get('rsi', {}).get('description', '')}
- MACD: {tech_details.get('macd', {}).get('score', 0)}/5점 - {tech_details.get('macd', {}).get('description', '')}
- 거래량: {tech_details.get('volume', {}).get('score', 0)}/8점 - {tech_details.get('volume', {}).get('description', '')}

## 기술 지표
- 현재가: {indicators.get('currentPrice', 'N/A'):,}원
- MA5: {indicators.get('ma5', 'N/A'):,}원
- MA20: {indicators.get('ma20', 'N/A'):,}원
- MA60: {indicators.get('ma60', 'N/A'):,}원
- MA120: {indicators.get('ma120', 'N/A'):,}원
- RSI(14): {indicators.get('rsi14', 'N/A')}
- MACD: {indicators.get('macd', 'N/A')}
- MACD Signal: {indicators.get('macdSignal', 'N/A')}
- MACD Histogram: {indicators.get('macdHist', 'N/A')}

## 기본분석 상세
- PER: {fund_details.get('per', {}).get('score', 0)}/8점 (값: {financials.get('per', 'N/A')})
- PBR: {fund_details.get('pbr', {}).get('score', 0)}/7점 (값: {financials.get('pbr', 'N/A')})
- PSR: {fund_details.get('psr', {}).get('score', 0)}/5점 (값: {financials.get('psr', 'N/A')})
- 매출성장률: {fund_details.get('revenueGrowth', {}).get('score', 0)}/6점 (값: {financials.get('revenueGrowth', 'N/A')}%)
- 영업이익성장률: {fund_details.get('opGrowth', {}).get('score', 0)}/6점 (값: {financials.get('opGrowth', 'N/A')}%)
- ROE: {fund_details.get('roe', {}).get('score', 0)}/5점 (값: {financials.get('roe', 'N/A')}%)
- 영업이익률: {fund_details.get('opMargin', {}).get('score', 0)}/5점 (값: {financials.get('opMargin', 'N/A')}%)
- 부채비율: {fund_details.get('debtRatio', {}).get('score', 0)}/4점 (값: {financials.get('debtRatio', 'N/A')}%)
- 유동비율: {fund_details.get('currentRatio', {}).get('score', 0)}/4점 (값: {financials.get('currentRatio', 'N/A')}%)

## 감정분석 상세
- 뉴스감정: {sent_details.get('sentiment', {}).get('score', 0)}/8점
- 영향도: {sent_details.get('impact', {}).get('score', 0)}/7점
- 관심도: {sent_details.get('volume', {}).get('score', 0)}/5점

다음 JSON 형식으로 응답해주세요:
{{
    "summary": "종합 분석 요약 (3-5문장, 핵심 포인트 중심)",
    "highlights": ["강점 1", "강점 2", ...],
    "risks": ["리스크 1", "리스크 2", ...],
    "technical_comment": "기술분석에 대한 상세 코멘트 (2-3문장)",
    "fundamental_comment": "기본분석에 대한 상세 코멘트 (2-3문장)",
    "sentiment_comment": "감정분석에 대한 상세 코멘트 (1-2문장)",
    "action_suggestion": "투자 행동 제안 (매수/보유/관망/매도 중 하나와 그 이유)"
}}
"""

    def _generate_fallback_summary(
        self,
        stock_name: str,
        total_score: float,
        grade: str,
        tech_score: float,
        fund_score: float,
        sent_score: float,
        tech_details: dict,
        fund_details: dict,
        indicators: dict,
        financials: dict,
    ) -> dict:
        """OpenAI 없을 때 규칙 기반 요약 생성"""

        # 점수 비율 계산
        tech_ratio = tech_score / 30
        fund_ratio = fund_score / 50
        sent_ratio = sent_score / 20

        # 강점/약점 분석
        highlights = []
        risks = []

        # 기술분석 평가
        if tech_ratio >= 0.7:
            highlights.append("기술적 지표가 우수한 상승 추세")
        elif tech_ratio <= 0.3:
            risks.append("기술적 지표 약세, 하락 추세 주의")

        # 기본분석 평가
        if fund_ratio >= 0.7:
            highlights.append("재무 건전성과 성장성이 양호")
        elif fund_ratio <= 0.3:
            risks.append("재무지표 부진, 실적 개선 필요")

        # 밸류에이션 평가
        per = financials.get("per")
        pbr = financials.get("pbr")
        if per and per > 0 and per < 15:
            highlights.append(f"PER {per:.1f}배로 저평가 매력")
        elif per and per > 30:
            risks.append(f"PER {per:.1f}배로 고평가 우려")

        if pbr and pbr < 1:
            highlights.append(f"PBR {pbr:.2f}배로 자산가치 대비 저평가")

        # 성장성 평가
        rev_growth = financials.get("revenueGrowth")
        if rev_growth and rev_growth > 20:
            highlights.append(f"매출 {rev_growth:.1f}% 고성장")
        elif rev_growth and rev_growth < -10:
            risks.append(f"매출 {rev_growth:.1f}% 역성장 주의")

        # RSI 평가
        rsi = indicators.get("rsi14")
        if rsi:
            if rsi >= 70:
                risks.append(f"RSI {rsi:.1f}로 과매수 구간, 조정 가능성")
            elif rsi <= 30:
                highlights.append(f"RSI {rsi:.1f}로 과매도 구간, 반등 기대")

        # 감정분석 평가
        if sent_ratio >= 0.7:
            highlights.append("시장 관심도와 뉴스 감정이 긍정적")
        elif sent_ratio <= 0.3:
            risks.append("시장 관심도 저조 또는 부정적 뉴스")

        # 종합 요약 생성
        grade_desc = self._get_grade_description(grade)

        if total_score >= 80:
            summary = f"{stock_name}은 {grade}등급({total_score:.1f}점)으로 {grade_desc}입니다. 기술적 지표와 재무적 펀더멘탈이 모두 양호하며, 현 시점에서 투자 매력도가 높습니다."
            action = "매수 고려 - 분할 매수 전략 추천"
        elif total_score >= 65:
            summary = f"{stock_name}은 {grade}등급({total_score:.1f}점)으로 {grade_desc}입니다. 전반적으로 양호한 지표를 보이고 있으나, 일부 개선이 필요한 부분이 있습니다."
            action = "관심 보유 - 추가 모니터링 후 진입 검토"
        elif total_score >= 50:
            summary = f"{stock_name}은 {grade}등급({total_score:.1f}점)으로 {grade_desc}입니다. 시장 평균 수준의 지표를 보이고 있어 신중한 접근이 필요합니다."
            action = "관망 - 실적 개선 또는 기술적 반등 신호 확인 후 진입"
        else:
            summary = f"{stock_name}은 {grade}등급({total_score:.1f}점)으로 {grade_desc}입니다. 여러 지표에서 부정적 신호가 나타나고 있어 투자에 주의가 필요합니다."
            action = "매도/회피 - 리스크 관리 우선"

        # 기술분석 코멘트
        ma_status = "정배열" if indicators.get("ma5", 0) > indicators.get("ma20", 0) > indicators.get("ma60", 0) else "역배열 또는 혼조"
        technical_comment = f"이동평균선이 {ma_status} 상태입니다. "
        if rsi:
            if rsi >= 70:
                technical_comment += f"RSI {rsi:.1f}로 과매수 구간에 진입하여 단기 조정 가능성이 있습니다."
            elif rsi <= 30:
                technical_comment += f"RSI {rsi:.1f}로 과매도 구간으로 기술적 반등이 기대됩니다."
            else:
                technical_comment += f"RSI {rsi:.1f}로 중립 구간에 위치합니다."

        # 기본분석 코멘트
        fundamental_comment = ""
        if per and per > 0:
            fundamental_comment += f"PER {per:.1f}배"
            if per < 15:
                fundamental_comment += "(저평가)"
            elif per > 25:
                fundamental_comment += "(고평가)"
            else:
                fundamental_comment += "(적정)"
        if pbr:
            fundamental_comment += f", PBR {pbr:.2f}배"
            if pbr < 1:
                fundamental_comment += "(자산가치 대비 저평가)"
        fundamental_comment += "로 평가됩니다. "

        roe = financials.get("roe")
        if roe:
            if roe >= 15:
                fundamental_comment += f"ROE {roe:.1f}%로 자본 효율성이 우수합니다."
            elif roe >= 8:
                fundamental_comment += f"ROE {roe:.1f}%로 양호한 수익성을 보입니다."
            else:
                fundamental_comment += f"ROE {roe:.1f}%로 수익성 개선이 필요합니다."

        # 감정분석 코멘트
        if sent_ratio >= 0.6:
            sentiment_comment = "최근 뉴스와 시장 관심도가 긍정적으로 형성되어 있어 투자 심리가 양호합니다."
        elif sent_ratio <= 0.4:
            sentiment_comment = "시장 관심도가 낮거나 부정적 뉴스가 있어 투자 심리에 주의가 필요합니다."
        else:
            sentiment_comment = "뉴스 감정과 시장 관심도가 중립적인 수준입니다."

        return {
            "summary": summary,
            "highlights": highlights if highlights else ["특별한 강점 없음"],
            "risks": risks if risks else ["특별한 리스크 없음"],
            "technical_comment": technical_comment,
            "fundamental_comment": fundamental_comment if fundamental_comment else "재무 데이터 부족으로 상세 분석이 어렵습니다.",
            "sentiment_comment": sentiment_comment,
            "action_suggestion": action,
        }


# 싱글톤 인스턴스
_commentary_service: Optional[CommentaryService] = None


def get_commentary_service() -> CommentaryService:
    """코멘터리 서비스 싱글톤"""
    global _commentary_service
    if _commentary_service is None:
        _commentary_service = CommentaryService()
    return _commentary_service

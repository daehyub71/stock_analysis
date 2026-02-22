"""
Backtesting Engine
- 과거 데이터 기반 기술분석 점수 재계산
- 점수 기반 매수/매도 시뮬레이션
- 수익률 및 성과 지표 계산
"""

import math
from dataclasses import dataclass, field
from typing import Optional

from app.db import sqlite_db
from app.analyzers.indicators import TechnicalIndicators
from app.services.technical import TechnicalAnalyzer


@dataclass
class BacktestParams:
    """백테스트 파라미터"""
    stock_code: str
    start_date: str              # YYYY-MM-DD
    end_date: str                # YYYY-MM-DD
    initial_capital: int = 10_000_000  # 초기 투자금 (원)
    buy_threshold: float = 20.0  # 기술분석 30점 중 매수 기준
    sell_threshold: float = 12.0 # 기술분석 30점 중 매도 기준
    lookback_days: int = 200     # 지표 계산용 과거 데이터 수
    commission_rate: float = 0.00015  # 매수/매도 수수료 (0.015%)
    tax_rate: float = 0.0023     # 매도세 (0.23%)


@dataclass
class Trade:
    """매매 기록"""
    type: str       # "buy" or "sell"
    date: str
    price: int
    shares: int
    score: float
    portfolio_value: int
    profit: Optional[int] = None       # 매도 시 수익금
    profit_pct: Optional[float] = None # 매도 시 수익률


@dataclass
class BacktestResult:
    """백테스트 결과"""
    # 일별 데이터
    daily_data: list = field(default_factory=list)
    # 매매 기록
    trades: list = field(default_factory=list)
    # 성과 지표
    total_return_pct: float = 0.0
    annualized_return_pct: float = 0.0
    buy_hold_return_pct: float = 0.0
    max_drawdown_pct: float = 0.0
    sharpe_ratio: float = 0.0
    win_rate: float = 0.0
    trade_count: int = 0
    final_value: int = 0
    trading_days: int = 0


class BacktestEngine:
    """백테스팅 엔진"""

    def __init__(self, params: BacktestParams):
        self.params = params
        self.position = 0       # 보유 주식수
        self.cash = params.initial_capital
        self.buy_price = 0      # 매수 단가
        self.trades: list[Trade] = []
        self.daily_data: list[dict] = []

    def run(self) -> BacktestResult:
        """백테스트 실행"""
        # 1. 전체 가격 데이터 로드 (ASC 정렬)
        all_prices = sqlite_db.get_prices(
            self.params.stock_code,
            limit=9999,
        )
        if not all_prices:
            raise ValueError(f"No price data for {self.params.stock_code}")

        # get_prices는 DESC 반환 → ASC 정렬
        all_prices = list(reversed(all_prices))

        # 2. 날짜 인덱스 맵핑
        date_list = [p["date"] for p in all_prices]

        # start_date 이상인 첫 인덱스 찾기
        start_idx = None
        for i, d in enumerate(date_list):
            if d >= self.params.start_date:
                start_idx = i
                break

        if start_idx is None:
            raise ValueError(f"No data after {self.params.start_date}")

        # end_date 이하인 마지막 인덱스 찾기
        end_idx = None
        for i in range(len(date_list) - 1, -1, -1):
            if date_list[i] <= self.params.end_date:
                end_idx = i
                break

        if end_idx is None or end_idx < start_idx:
            raise ValueError(f"No data in range {self.params.start_date} ~ {self.params.end_date}")

        # 3. 각 거래일별 점수 계산 및 매매 실행
        for idx in range(start_idx, end_idx + 1):
            # 슬라이딩 윈도우: 현재 날짜까지 lookback_days개
            window_start = max(0, idx - self.params.lookback_days + 1)
            price_slice = all_prices[window_start:idx + 1]

            current = all_prices[idx]
            price = current["close_price"]
            date = current["date"]

            # 기술분석 점수 계산
            score = self._calculate_score(price_slice)

            # 매매 전략 실행
            self._apply_strategy(date, price, score)

            # 일별 데이터 기록
            portfolio_value = self.cash + (self.position * price)
            self.daily_data.append({
                "date": date,
                "price": price,
                "score": round(score, 1),
                "portfolioValue": portfolio_value,
                "position": "holding" if self.position > 0 else "cash",
                "shares": self.position,
            })

        # 4. 결과 계산
        result = BacktestResult(
            daily_data=self.daily_data,
            trades=self.trades,
            trade_count=len(self.trades),
            trading_days=len(self.daily_data),
        )

        if self.daily_data:
            result.final_value = self.daily_data[-1]["portfolioValue"]
            self._calculate_metrics(result, all_prices[start_idx]["close_price"],
                                     all_prices[end_idx]["close_price"])

        return result

    def _calculate_score(self, prices: list[dict]) -> float:
        """가격 슬라이스로 기술분석 점수 계산 (30점 만점)"""
        if len(prices) < 20:
            return 15.0  # 데이터 부족 시 중립

        try:
            ti = TechnicalIndicators(self.params.stock_code, prices=prices)
            indicators = ti.calculate_all()

            if not indicators.get("has_data"):
                return 15.0

            analyzer = TechnicalAnalyzer(self.params.stock_code, indicators=indicators)
            result = analyzer.calculate_total()
            return result["total_score"]
        except Exception:
            return 15.0

    def _apply_strategy(self, date: str, price: int, score: float):
        """매매 전략 적용"""
        if price <= 0:
            return

        # 매수 조건: 미보유 & 점수 >= 매수기준
        if self.position == 0 and score >= self.params.buy_threshold:
            # 수수료 반영 후 최대 매수 수량
            available = self.cash * (1 - self.params.commission_rate)
            shares = int(available // price)

            if shares > 0:
                cost = shares * price
                commission = int(cost * self.params.commission_rate)
                self.cash -= (cost + commission)
                self.position = shares
                self.buy_price = price

                portfolio_value = self.cash + (self.position * price)
                self.trades.append(Trade(
                    type="buy",
                    date=date,
                    price=price,
                    shares=shares,
                    score=round(score, 1),
                    portfolio_value=portfolio_value,
                ))

        # 매도 조건: 보유 중 & 점수 < 매도기준
        elif self.position > 0 and score < self.params.sell_threshold:
            proceeds = self.position * price
            commission = int(proceeds * self.params.commission_rate)
            tax = int(proceeds * self.params.tax_rate)
            net_proceeds = proceeds - commission - tax

            profit = net_proceeds - (self.buy_price * self.position)
            profit_pct = (price - self.buy_price) / self.buy_price * 100

            self.cash += net_proceeds
            portfolio_value = self.cash

            self.trades.append(Trade(
                type="sell",
                date=date,
                price=price,
                shares=self.position,
                score=round(score, 1),
                portfolio_value=portfolio_value,
                profit=profit,
                profit_pct=round(profit_pct, 2),
            ))

            self.position = 0
            self.buy_price = 0

    def _calculate_metrics(self, result: BacktestResult, start_price: int, end_price: int):
        """성과 지표 계산"""
        initial = self.params.initial_capital
        final = result.final_value

        # 총 수익률
        result.total_return_pct = round((final - initial) / initial * 100, 2)

        # 연환산 수익률
        if result.trading_days > 0:
            years = result.trading_days / 252
            if years > 0 and final > 0:
                result.annualized_return_pct = round(
                    ((final / initial) ** (1 / years) - 1) * 100, 2
                )

        # Buy & Hold 수익률
        if start_price > 0:
            result.buy_hold_return_pct = round(
                (end_price - start_price) / start_price * 100, 2
            )

        # MDD (Maximum Drawdown)
        peak = 0
        max_dd = 0
        for d in result.daily_data:
            pv = d["portfolioValue"]
            if pv > peak:
                peak = pv
            if peak > 0:
                dd = (peak - pv) / peak * 100
                if dd > max_dd:
                    max_dd = dd
        result.max_drawdown_pct = round(max_dd, 2)

        # 샤프비율
        if len(result.daily_data) > 1:
            values = [d["portfolioValue"] for d in result.daily_data]
            daily_returns = []
            for i in range(1, len(values)):
                if values[i - 1] > 0:
                    daily_returns.append((values[i] - values[i - 1]) / values[i - 1])

            if daily_returns:
                import numpy as np
                mean_return = np.mean(daily_returns)
                std_return = np.std(daily_returns, ddof=1)
                risk_free_daily = 0.035 / 252  # 연 3.5% 무위험수익률

                if std_return > 0:
                    result.sharpe_ratio = round(
                        (mean_return - risk_free_daily) / std_return * math.sqrt(252), 2
                    )

        # 승률
        sell_trades = [t for t in result.trades if t.type == "sell"]
        if sell_trades:
            wins = sum(1 for t in sell_trades if t.profit and t.profit > 0)
            result.win_rate = round(wins / len(sell_trades) * 100, 1)

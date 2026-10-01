"""Strategy C: Ensemble Multi-Factor Defensive Enhanced Strategy (綜合多因子防禦增強策略 - 旗艦策略)"""
from typing import Dict
import pandas as pd
import numpy as np


class EnsembleMultiFactorStrategy:
    """
    Ensemble Multi-Factor Strategy:
    1. Fundamental Factor (40%): Revenue YoY growth & momentum
    2. Institutional Factor (30%): Trust & Foreign institutional net buying
    3. Technical Momentum Factor (30%): Price trend alignment & returns
    4. Macro Risk Regime Overlay:
       - Bull regime (0050 > 60MA): 100% stock allocation
       - Bear regime (0050 < 60MA): Reduce equity exposure to 20%, holding 80% cash.
    """

    def __init__(self, top_n: int = 15, bear_equity_exposure: float = 0.20):
        self.name = "Strategy C: 綜合多因子防禦增強策略"
        self.top_n = top_n
        self.bear_equity_exposure = bear_equity_exposure

    def select_portfolio(self, factor_snapshot: pd.DataFrame, is_market_bullish: bool = True) -> Dict[str, float]:
        """
        Returns a dict of {symbol: target_weight}.
        Remaining weight (1.0 - sum(weights)) is automatically held in cash.
        """
        if factor_snapshot.empty:
            return {}

        df = factor_snapshot.copy()

        # 1. Liquidity filter
        df = df[df["is_liquid"] == True]
        if df.empty:
            return {}

        # 2. Technical trend filter: Prefer stocks above 20MA
        bull_candidates = df[df["above_ma20"] == True]
        if len(bull_candidates) >= self.top_n:
            df = bull_candidates.copy()

        # 3. Factor scoring with percentile ranks
        # Fundamental: Revenue YoY
        rev_score = (
            df["rev_yoy"].fillna(-10).rank(pct=True) * 0.6
            + df["rev_3m_yoy"].fillna(-10).rank(pct=True) * 0.4
        )

        # Institutional: Trust + Foreign
        inst_score = (
            df["trust_ratio_20d"].rank(pct=True) * 0.5
            + df["trust_net_buy_20d"].rank(pct=True) * 0.3
            + df["foreign_net_buy_20d"].rank(pct=True) * 0.2
        )

        # Technical Momentum: 20d + 60d return + MA bullish alignment bonus
        mom_score = (
            df["ret_20d"].rank(pct=True) * 0.4
            + df["ret_60d"].rank(pct=True) * 0.4
            + df["ma_bullish"].astype(float) * 0.2
        )

        # Ensemble total score: 40% Fundamental + 30% Institutional + 30% Momentum
        df["total_score"] = 0.40 * rev_score + 0.30 * inst_score + 0.30 * mom_score

        top_stocks = df.sort_values("total_score", ascending=False).head(self.top_n)

        if top_stocks.empty:
            return {}

        # 4. Target equity exposure depending on market regime
        total_equity_weight = 1.0 if is_market_bullish else self.bear_equity_exposure
        stock_weight = total_equity_weight / len(top_stocks)

        return {sym: stock_weight for sym in top_stocks["symbol"]}

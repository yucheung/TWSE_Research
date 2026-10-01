"""Strategy B: Institutional Trust Momentum Strategy (投信法人籌碼共振策略)"""
from typing import Dict
import pandas as pd
import numpy as np


class InstitutionalTrustStrategy:
    """
    Selects stocks with high institutional (investment trust) net buy concentration
    combined with positive technical momentum.
    """

    def __init__(self, top_n: int = 15):
        self.name = "Strategy B: 投信法人籌碼共振策略"
        self.top_n = top_n

    def select_portfolio(self, factor_snapshot: pd.DataFrame, is_market_bullish: bool = True) -> Dict[str, float]:
        """
        Returns a dict of {symbol: target_weight}.
        """
        if factor_snapshot.empty:
            return {}

        df = factor_snapshot.copy()

        # 1. Liquidity filter
        df = df[df["is_liquid"] == True]

        # 2. Technical filter: Price above 20MA
        df = df[df["above_ma20"] == True]

        if df.empty:
            df = factor_snapshot[factor_snapshot["is_liquid"]].copy()
            if df.empty:
                return {}

        # 3. Institutional score: Trust buy ratio + Trust net buy positive + Foreign net buy support
        # Calculate percentile rank
        df["trust_ratio_rank"] = df["trust_ratio_20d"].rank(pct=True)
        df["trust_buy_rank"] = df["trust_net_buy_20d"].rank(pct=True)
        df["foreign_buy_rank"] = df["foreign_net_buy_20d"].rank(pct=True)
        df["mom_rank"] = df["ret_20d"].rank(pct=True)

        # Composite institutional score (Trust 60%, Foreign 20%, Momentum 20%)
        df["score"] = (
            df["trust_ratio_rank"] * 0.4
            + df["trust_buy_rank"] * 0.2
            + df["foreign_buy_rank"] * 0.2
            + df["mom_rank"] * 0.2
        )

        top_stocks = df.sort_values("score", ascending=False).head(self.top_n)

        if top_stocks.empty:
            return {}

        weight = 1.0 / len(top_stocks)
        return {sym: weight for sym in top_stocks["symbol"]}

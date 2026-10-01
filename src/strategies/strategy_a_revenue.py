"""Strategy A: Revenue Growth Breakout Strategy (營收爆發突破策略)"""
from typing import List, Dict
import pandas as pd
import numpy as np


class RevenueBreakoutStrategy:
    """
    Selects stocks with high monthly revenue growth (YoY)
    and positive technical momentum (Close > 20MA).
    """

    def __init__(self, top_n: int = 15, min_yoy: float = 10.0):
        self.name = "Strategy A: 營收爆發突破策略"
        self.top_n = top_n
        self.min_yoy = min_yoy

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

        # 3. Revenue filter: Valid revenue YoY
        df = df[df["rev_yoy"].notna()]
        df = df[df["rev_yoy"] >= self.min_yoy]

        if df.empty:
            # Fallback if no stock meets strict min_yoy: take top liquid above MA20 with highest YoY
            df_fallback = factor_snapshot[factor_snapshot["is_liquid"] & factor_snapshot["above_ma20"]].dropna(subset=["rev_yoy"])
            if df_fallback.empty:
                return {}
            df = df_fallback

        # Sort by 3-month YoY + 1-month YoY + bonus for 12-month new high
        df["score"] = df["rev_yoy"].fillna(0) + df["rev_3m_yoy"].fillna(0)
        df["score"] += df["rev_new_high"].astype(int) * 20.0  # +20 score for new high

        top_stocks = df.sort_values("score", ascending=False).head(self.top_n)

        if top_stocks.empty:
            return {}

        weight = 1.0 / len(top_stocks)
        return {sym: weight for sym in top_stocks["symbol"]}

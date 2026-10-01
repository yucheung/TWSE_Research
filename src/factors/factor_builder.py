"""Factor builder module for TWSE multi-factor quantitative models."""
from typing import Dict, List, Optional
import pandas as pd
import numpy as np

from ..data.universe import BENCHMARK_SYMBOL


class FactorBuilder:
    """Computes technical, fundamental (monthly revenue), and institutional factors."""

    def __init__(
        self,
        prices_dict: Dict[str, pd.DataFrame],
        revenue_dict: Optional[Dict[str, pd.DataFrame]] = None,
        institutional_dict: Optional[Dict[str, pd.DataFrame]] = None,
        liquidity_min_turnover: float = 30_000_000.0,  # 30 Million NTD min 20MA daily turnover
        universe_by_year: Optional[Dict[int, List[str]]] = None,  # rule-based yearly membership; None = full pool
    ):
        self.prices_dict = prices_dict
        self.revenue_dict = revenue_dict or {}
        self.institutional_dict = institutional_dict or {}
        self.liquidity_min_turnover = liquidity_min_turnover
        self.universe_by_year = {y: set(m) for y, m in (universe_by_year or {}).items()}

        # Precompute date index alignment
        self.benchmark_df = self.prices_dict.get(BENCHMARK_SYMBOL)

    def get_rebalance_dates(self, start_date: str = "2020-01-01", end_date: str = "2026-09-30") -> List[pd.Timestamp]:
        """
        Generate monthly rebalancing dates.
        In TWSE, monthly revenue must be filed by the 10th of each calendar month.
        We select the first trading day on or after the 11th calendar day of each month.
        """
        if self.benchmark_df is None:
            raise ValueError(f"Benchmark {BENCHMARK_SYMBOL} not found in price data.")

        bench_dates = self.benchmark_df.index
        # Convert index to timezone-naive if needed
        if hasattr(bench_dates, "tz") and bench_dates.tz is not None:
            bench_dates = bench_dates.tz_localize(None)

        filtered_dates = [d for d in bench_dates if pd.Timestamp(start_date) <= d <= pd.Timestamp(end_date)]
        df_dates = pd.DataFrame({"trade_date": filtered_dates})
        df_dates["year"] = df_dates["trade_date"].dt.year
        df_dates["month"] = df_dates["trade_date"].dt.month
        df_dates["day"] = df_dates["trade_date"].dt.day

        # Select first trading day with day >= 11 in each year-month
        rebalance_dates = []
        for (year, month), group in df_dates.groupby(["year", "month"]):
            post_10th = group[group["day"] >= 11]
            if not post_10th.empty:
                rebalance_dates.append(post_10th.iloc[0]["trade_date"])
            else:
                rebalance_dates.append(group.iloc[-1]["trade_date"])

        return sorted(rebalance_dates)

    def is_market_bullish(self, as_of_date: pd.Timestamp) -> bool:
        """Check if benchmark 0050 is in a bull regime (Close > MA60)."""
        if self.benchmark_df is None:
            return True
        df = self.benchmark_df
        # Make timezone-naive for comparison
        idx = df.index.tz_localize(None) if hasattr(df.index, "tz") and df.index.tz is not None else df.index
        past_df = df[idx <= as_of_date]
        if len(past_df) < 60:
            return True
        latest_row = past_df.iloc[-1]
        close = latest_row["Close"]
        ma60 = past_df["Close"].tail(60).mean()
        return bool(close >= ma60)

    def compute_factors_snapshot(self, as_of_date: pd.Timestamp) -> pd.DataFrame:
        """
        Compute snapshot of all factors for all stocks as of a given date.
        """
        records = []

        members = self.universe_by_year.get(int(as_of_date.year)) if self.universe_by_year else None

        for symbol, p_df in self.prices_dict.items():
            if symbol == BENCHMARK_SYMBOL:
                continue
            if members is not None and symbol not in members:
                continue

            # Ensure timezone-naive index
            p_idx = p_df.index.tz_localize(None) if hasattr(p_df.index, "tz") and p_df.index.tz is not None else p_df.index
            hist_prices = p_df[p_idx <= as_of_date]

            if len(hist_prices) < 60:
                continue

            latest_p = hist_prices.iloc[-1]
            close = float(latest_p["Close"])
            volume_20 = hist_prices["Volume"].tail(20).values
            turnover_20 = hist_prices["Turnover"].tail(20).mean() if "Turnover" in hist_prices.columns else (close * np.mean(volume_20))

            # 1. Liquidity check: 20-day average turnover >= liquidity_min_turnover
            is_liquid = turnover_20 >= self.liquidity_min_turnover

            # 2. Technical / Momentum factors
            ma20 = float(hist_prices["Close"].tail(20).mean())
            ma60 = float(hist_prices["Close"].tail(60).mean())
            ma_bullish = bool(close > ma20 and ma20 > ma60)
            above_ma20 = bool(close > ma20)

            # Price momentum (20-day and 60-day returns)
            ret_20d = float((close / hist_prices["Close"].iloc[-20] - 1.0) * 100) if len(hist_prices) >= 20 else 0.0
            ret_60d = float((close / hist_prices["Close"].iloc[-60] - 1.0) * 100) if len(hist_prices) >= 60 else 0.0

            # 3. Fundamental / Monthly Revenue factor
            rev_yoy = np.nan
            rev_3m_yoy = np.nan
            rev_new_high = False

            if symbol in self.revenue_dict:
                r_df = self.revenue_dict[symbol]
                # In FinMind, date is e.g. 2020-02-01 representing Jan revenue, announced on or before Feb 10
                # Our rebalance is on or after the 11th, so date + 9 days (the 10th) is publicly known
                pub_r = r_df[(r_df["date"] + pd.Timedelta(days=9)) <= as_of_date]

                if not pub_r.empty and len(pub_r) >= 12:
                    latest_r = pub_r.iloc[-1]
                    rev_yoy = float(latest_r.get("revenue_YoY", np.nan))
                    rev_3m_yoy = float(latest_r.get("revenue_3m_YoY", np.nan))
                    past_12m_max = pub_r["revenue"].tail(12).iloc[:-1].max() if len(pub_r) > 1 else 0
                    rev_new_high = bool(latest_r["revenue"] >= past_12m_max)

            # 4. Institutional Trust / Foreign Investor flow
            trust_net_buy_20d = 0.0
            trust_ratio_20d = 0.0
            foreign_net_buy_20d = 0.0

            if symbol in self.institutional_dict:
                inst_df = self.institutional_dict[symbol]
                inst_hist = inst_df[inst_df["date"] <= as_of_date]
                if not inst_hist.empty:
                    # Last 20 trading sessions institutional data
                    recent_inst = inst_hist.tail(100)  # each day has multiple rows (Foreign, Trust, Dealer)
                    trust_rows = recent_inst[recent_inst["name"] == "Investment_Trust"].tail(20)
                    if not trust_rows.empty:
                        trust_net_buy_20d = float(trust_rows["net_buy"].sum())
                        tot_vol = float(np.sum(volume_20)) if len(volume_20) > 0 and np.sum(volume_20) > 0 else 1.0
                        trust_ratio_20d = (trust_net_buy_20d / tot_vol) * 100.0

                    foreign_rows = recent_inst[recent_inst["name"] == "Foreign_Investor"].tail(20)
                    if not foreign_rows.empty:
                        foreign_net_buy_20d = float(foreign_rows["net_buy"].sum())

            records.append({
                "symbol": symbol,
                "close": close,
                "turnover_20d": turnover_20,
                "is_liquid": is_liquid,
                "above_ma20": above_ma20,
                "ma_bullish": ma_bullish,
                "ret_20d": ret_20d,
                "ret_60d": ret_60d,
                "rev_yoy": rev_yoy,
                "rev_3m_yoy": rev_3m_yoy,
                "rev_new_high": rev_new_high,
                "trust_net_buy_20d": trust_net_buy_20d,
                "trust_ratio_20d": trust_ratio_20d,
                "foreign_net_buy_20d": foreign_net_buy_20d,
            })

        df_factors = pd.DataFrame(records)
        return df_factors

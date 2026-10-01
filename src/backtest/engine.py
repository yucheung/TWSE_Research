"""Backtest engine module simulating monthly rebalancing with realistic TWSE transaction costs."""
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np

from ..data.universe import BENCHMARK_SYMBOL
from ..factors.factor_builder import FactorBuilder


class BacktestEngine:
    """
    Realistic TWSE quantitative backtesting engine:
    - Monthly rebalancing
    - Taiwanese tax & commission (50% discount) + slippage
    - Daily NAV tracking
    """

    def __init__(
        self,
        prices_dict: Dict[str, pd.DataFrame],
        factor_builder: FactorBuilder,
        initial_capital: float = 1_000_000.0,
        buy_fee: float = 0.0007125,     # 0.1425% * 0.5 (5折手續費)
        sell_fee: float = 0.0007125,    # 0.1425% * 0.5
        tax_fee: float = 0.0030,        # 0.3% 證交稅
        slippage: float = 0.0010,       # 0.1% 滑價
        annual_cash_yield: float = 0.015, # 1.5% 現金殖利率/利息
    ):
        self.prices_dict = prices_dict
        self.factor_builder = factor_builder
        self.initial_capital = initial_capital
        self.buy_friction = buy_fee + slippage          # 0.17125%
        self.sell_friction = sell_fee + tax_fee + slippage # 0.47125%
        self.daily_cash_yield = (1.0 + annual_cash_yield) ** (1.0 / 252) - 1.0

        self.benchmark_df = self.prices_dict[BENCHMARK_SYMBOL]

    def run_strategy(
        self,
        strategy: Any,
        start_date: str = "2020-01-01",
        end_date: str = "2026-09-30",
    ) -> Dict[str, Any]:
        """
        Execute backtest for a strategy over the specified time range.
        """
        rebalance_dates = self.factor_builder.get_rebalance_dates(start_date, end_date)
        if not rebalance_dates:
            raise ValueError("No rebalancing dates found in the specified range.")

        # Determine trading calendar from benchmark
        b_idx = self.benchmark_df.index.tz_localize(None) if hasattr(self.benchmark_df.index, "tz") and self.benchmark_df.index.tz is not None else self.benchmark_df.index
        trading_calendar = [d for d in b_idx if rebalance_dates[0] <= d <= pd.Timestamp(end_date)]

        cash = self.initial_capital
        # holdings: {symbol: shares}
        holdings: Dict[str, float] = {}

        daily_records = []
        rebalance_log = []

        rebal_set = set(rebalance_dates)

        for current_date in trading_calendar:
            # 1. Update valuation at market close
            stock_values = {}
            for sym, shares in holdings.items():
                p_df = self.prices_dict.get(sym)
                if p_df is not None:
                    p_idx = p_df.index.tz_localize(None) if hasattr(p_df.index, "tz") and p_df.index.tz is not None else p_df.index
                    sub = p_df[p_idx <= current_date]
                    if not sub.empty:
                        px = float(sub.iloc[-1]["Close"])
                        stock_values[sym] = shares * px
                    else:
                        stock_values[sym] = 0.0
                else:
                    stock_values[sym] = 0.0

            total_equity = cash + sum(stock_values.values())

            # 2. Check if today is a rebalance date
            if current_date in rebal_set:
                is_bull = self.factor_builder.is_market_bullish(current_date)
                snapshot = self.factor_builder.compute_factors_snapshot(current_date)
                target_weights = strategy.select_portfolio(snapshot, is_market_bullish=is_bull)

                # Execute rebalance:
                # First sell symbols not in target or reducing weight
                target_symbols = set(target_weights.keys())

                # Liquidate removed holdings
                for sym in list(holdings.keys()):
                    if sym not in target_symbols:
                        shares = holdings.pop(sym)
                        p_df = self.prices_dict.get(sym)
                        p_idx = p_df.index.tz_localize(None) if hasattr(p_df.index, "tz") and p_df.index.tz is not None else p_df.index
                        sub = p_df[p_idx <= current_date]
                        px = float(sub.iloc[-1]["Close"]) if not sub.empty else 0.0
                        gross_proceeds = shares * px
                        cost = gross_proceeds * self.sell_friction
                        net_proceeds = gross_proceeds - cost
                        cash += net_proceeds
                        rebalance_log.append({
                            "date": current_date,
                            "symbol": sym,
                            "action": "SELL_ALL",
                            "shares": shares,
                            "price": px,
                            "proceeds": net_proceeds,
                            "fee": cost,
                        })

                # Recompute total equity before buying
                current_stock_val = 0.0
                for sym, shares in holdings.items():
                    p_df = self.prices_dict[sym]
                    p_idx = p_df.index.tz_localize(None) if hasattr(p_df.index, "tz") and p_df.index.tz is not None else p_df.index
                    sub = p_df[p_idx <= current_date]
                    px = float(sub.iloc[-1]["Close"])
                    current_stock_val += shares * px

                portfolio_nav = cash + current_stock_val

                # Rebalance remaining and new targets
                for sym, target_w in target_weights.items():
                    p_df = self.prices_dict.get(sym)
                    if p_df is None:
                        continue
                    p_idx = p_df.index.tz_localize(None) if hasattr(p_df.index, "tz") and p_df.index.tz is not None else p_df.index
                    sub = p_df[p_idx <= current_date]
                    if sub.empty:
                        continue
                    px = float(sub.iloc[-1]["Close"])
                    if px <= 0:
                        continue

                    target_dollar = portfolio_nav * target_w
                    current_dollar = holdings.get(sym, 0.0) * px
                    dollar_diff = target_dollar - current_dollar

                    if dollar_diff > 0:
                        # Buy
                        affordable_dollar = min(dollar_diff, cash / (1.0 + self.buy_friction))
                        if affordable_dollar > 1000:  # minimum trade threshold
                            buy_shares = affordable_dollar / px
                            cost = (buy_shares * px) * self.buy_friction
                            total_cost = (buy_shares * px) + cost
                            cash -= total_cost
                            holdings[sym] = holdings.get(sym, 0.0) + buy_shares
                            rebalance_log.append({
                                "date": current_date,
                                "symbol": sym,
                                "action": "BUY",
                                "shares": buy_shares,
                                "price": px,
                                "amount": buy_shares * px,
                                "fee": cost,
                            })
                    elif dollar_diff < -1000:
                        # Sell partial
                        sell_dollar = abs(dollar_diff)
                        sell_shares = min(sell_dollar / px, holdings.get(sym, 0.0))
                        gross_proceeds = sell_shares * px
                        cost = gross_proceeds * self.sell_friction
                        net_proceeds = gross_proceeds - cost
                        cash += net_proceeds
                        holdings[sym] -= sell_shares
                        if holdings[sym] <= 1e-4:
                            holdings.pop(sym, None)
                        rebalance_log.append({
                            "date": current_date,
                            "symbol": sym,
                            "action": "SELL_PARTIAL",
                            "shares": sell_shares,
                            "price": px,
                            "proceeds": net_proceeds,
                            "fee": cost,
                        })

                # Recompute total equity post-rebalance
                stock_values = {}
                for sym, shares in holdings.items():
                    p_df = self.prices_dict[sym]
                    p_idx = p_df.index.tz_localize(None) if hasattr(p_df.index, "tz") and p_df.index.tz is not None else p_df.index
                    sub = p_df[p_idx <= current_date]
                    px = float(sub.iloc[-1]["Close"])
                    stock_values[sym] = shares * px
                total_equity = cash + sum(stock_values.values())

            # Daily cash yield
            cash += cash * self.daily_cash_yield

            daily_records.append({
                "date": current_date,
                "nav": total_equity,
                "cash": cash,
                "stock_value": sum(stock_values.values()),
                "num_holdings": len(holdings),
            })

        df_daily = pd.DataFrame(daily_records).set_index("date")
        df_daily["returns"] = df_daily["nav"].pct_change().fillna(0.0)
        df_daily["cumulative_return"] = df_daily["nav"] / self.initial_capital - 1.0

        return {
            "strategy_name": getattr(strategy, "name", "Strategy"),
            "daily_nav": df_daily,
            "rebalance_log": pd.DataFrame(rebalance_log),
            "final_holdings": holdings,
        }

    def run_benchmark_0050(
        self,
        start_date: str = "2020-01-01",
        end_date: str = "2026-09-30",
    ) -> pd.DataFrame:
        """
        Simulate Benchmark 0050 Buy & Hold from the first rebalance date.
        """
        rebalance_dates = self.factor_builder.get_rebalance_dates(start_date, end_date)
        first_date = rebalance_dates[0]

        df_0050 = self.benchmark_df.copy()
        idx = df_0050.index.tz_localize(None) if hasattr(df_0050.index, "tz") and df_0050.index.tz is not None else df_0050.index
        df_0050 = df_0050[(idx >= first_date) & (idx <= pd.Timestamp(end_date))].copy()
        df_0050.index = df_0050.index.tz_localize(None) if hasattr(df_0050.index, "tz") and df_0050.index.tz is not None else df_0050.index

        initial_px = float(df_0050.iloc[0]["Close"])
        # Deduct entry friction
        effective_capital = self.initial_capital * (1.0 - self.buy_friction)
        shares = effective_capital / initial_px

        bench_nav = df_0050["Close"] * shares
        df_bench = pd.DataFrame({
            "nav": bench_nav,
            "returns": bench_nav.pct_change().fillna(0.0),
            "cumulative_return": bench_nav / self.initial_capital - 1.0,
        })
        return df_bench

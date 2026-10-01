"""Market-wide yearly pool reconstruction (engine v3, A2 free route).

No hand-picked list: every year's pool is the top-N by prior-year mean
daily Turnover among all currently-listed TWSE/TPEx common stocks.
Turnover is a liquidity/size proxy, NOT true market cap
(FinMind market-value API needs paid level) — documented limitation.

Known residual bias: delisted stocks fail download and are absent from
all years (yfinance only serves listed tickers). This kills hand-pick
bias but not full survivorship bias.
"""
from typing import Dict, List
import pandas as pd


def market_symbols_from_info(info_df: pd.DataFrame) -> List[str]:
    """TWSE/TPEx common stocks -> yfinance symbols. Excludes emerging board and ETFs."""
    syms = []
    for _, r in info_df.iterrows():
        sid = str(r["stock_id"]).strip()
        typ = str(r["type"]).strip().lower()
        if typ == "twse":
            suffix = ".TW"
        elif typ == "tpex":
            suffix = ".TWO"
        else:
            continue  # emerging / others
        if not (sid.isdigit() and len(sid) == 4):
            continue
        if sid.startswith("00"):
            continue  # ETFs (0050/0056/006208/00878/...)
        syms.append(f"{sid}{suffix}")
    return sorted(set(syms))


def build_market_membership(
    prices_dict: Dict[str, pd.DataFrame],
    top_n: int = 200,
) -> Dict[int, List[str]]:
    """{year: [symbols]} — year Y pool = top-N by mean Turnover in year Y-1.

    Requires prices from 2019 (for the 2020 pool). Years without prior-year
    history are skipped.
    """
    per_year_turnover: Dict[int, Dict[str, float]] = {}
    for sym, df in prices_dict.items():
        if "Turnover" not in df.columns:
            continue
        idx = df.index.tz_localize(None) if hasattr(df.index, "tz") and df.index.tz is not None else df.index
        tmp = df.copy()
        tmp.index = idx
        for year, grp in tmp.groupby(tmp.index.year):
            per_year_turnover.setdefault(year, {})[sym] = float(grp["Turnover"].mean())

    years = sorted(per_year_turnover.keys())
    membership: Dict[int, List[str]] = {}
    for y in years:
        if y - 1 not in per_year_turnover:
            continue  # no history (e.g. first fetch year) — skip, no warm-up cheating
        ranked = sorted(per_year_turnover[y - 1].items(), key=lambda x: x[1], reverse=True)
        membership[y] = [s for s, _ in ranked[:top_n]]
    return membership

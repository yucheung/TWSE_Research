"""Data fetcher module for TWSE prices, revenue, and institutional data."""
import os
import pickle
import time
from typing import Dict, List, Optional
import pandas as pd
import yfinance as yf
from FinMind.data import DataLoader

from .universe import get_twse_universe, BENCHMARK_SYMBOL

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "cache")


class DataFetcher:
    """Fetches and caches Taiwan stock market data."""

    def __init__(self, cache_dir: str = CACHE_DIR):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        self.dl = DataLoader()

    def get_stock_id(self, symbol: str) -> str:
        """Strip .TW / .TWO suffix to get raw stock ID for FinMind."""
        return symbol.split(".")[0]

    def fetch_all_prices(
        self,
        symbols: Optional[List[str]] = None,
        start_date: str = "2020-01-01",
        end_date: str = "2026-09-30",
        force_refresh: bool = False,
    ) -> Dict[str, pd.DataFrame]:
        """Fetch daily OHLCV prices from yfinance and cache locally."""
        cache_file = os.path.join(self.cache_dir, "prices_data.pkl")
        if not force_refresh and os.path.exists(cache_file):
            print(f"[Fetcher] Loading cached price data from {cache_file}...")
            with open(cache_file, "rb") as f:
                return pickle.load(f)

        if symbols is None:
            symbols = [item["symbol"] for item in get_twse_universe()]
            if BENCHMARK_SYMBOL not in symbols:
                symbols.append(BENCHMARK_SYMBOL)

        print(f"[Fetcher] Downloading daily prices for {len(symbols)} symbols from {start_date} to {end_date}...")
        prices_dict: Dict[str, pd.DataFrame] = {}

        # Batch download in chunks of 25 symbols for efficiency and reliability
        chunk_size = 25
        for i in range(0, len(symbols), chunk_size):
            chunk = symbols[i : i + chunk_size]
            print(f"  Downloading batch {i // chunk_size + 1}/{(len(symbols) + chunk_size - 1) // chunk_size} ({len(chunk)} tickers)...")
            try:
                data = yf.download(
                    chunk,
                    start=start_date,
                    end=end_date,
                    group_by="ticker",
                    auto_adjust=False,
                    progress=False,
                    threads=True,
                )
                if len(chunk) == 1:
                    sym = chunk[0]
                    if not data.empty:
                        prices_dict[sym] = data.copy()
                else:
                    for sym in chunk:
                        if sym in data.columns.levels[0]:
                            df = data[sym].dropna(how="all").copy()
                            if not df.empty and "Close" in df.columns:
                                prices_dict[sym] = df
            except Exception as e:
                print(f"  [Warning] Batch download failed for chunk {chunk}: {e}")
                # Fallback to single downloads
                for sym in chunk:
                    try:
                        s_df = yf.download(sym, start=start_date, end=end_date, auto_adjust=False, progress=False)
                        if not s_df.empty:
                            prices_dict[sym] = s_df
                    except Exception as err:
                        print(f"    Failed downloading {sym}: {err}")

        # Compute Turnover (Volume * Close) and 20MA Turnover
        for sym, df in prices_dict.items():
            if "Close" in df.columns and "Volume" in df.columns:
                df["Turnover"] = df["Close"] * df["Volume"]
                df["Turnover_MA20"] = df["Turnover"].rolling(window=20).mean()
                df["MA20"] = df["Close"].rolling(window=20).mean()
                df["MA60"] = df["Close"].rolling(window=60).mean()

        with open(cache_file, "wb") as f:
            pickle.dump(prices_dict, f)
        print(f"[Fetcher] Successfully cached {len(prices_dict)} symbols price data.")
        return prices_dict

    def fetch_all_revenue(
        self,
        symbols: Optional[List[str]] = None,
        start_date: str = "2018-01-01",
        force_refresh: bool = False,
    ) -> Dict[str, pd.DataFrame]:
        """Fetch monthly revenue from FinMind and cache locally."""
        cache_file = os.path.join(self.cache_dir, "revenue_data.pkl")
        if not force_refresh and os.path.exists(cache_file):
            print(f"[Fetcher] Loading cached revenue data from {cache_file}...")
            with open(cache_file, "rb") as f:
                return pickle.load(f)

        if symbols is None:
            symbols = [item["symbol"] for item in get_twse_universe()]

        print(f"[Fetcher] Fetching monthly revenue for {len(symbols)} symbols via FinMind...")
        rev_dict: Dict[str, pd.DataFrame] = {}

        for idx, sym in enumerate(symbols):
            if sym == BENCHMARK_SYMBOL:
                continue
            stock_id = self.get_stock_id(sym)
            try:
                df = self.dl.taiwan_stock_month_revenue(stock_id=stock_id, start_date=start_date)
                if df is not None and not df.empty:
                    df["date"] = pd.to_datetime(df["date"])
                    df = df.sort_values("date").reset_index(drop=True)
                    # Calculate YoY revenue growth
                    df["revenue_YoY"] = df["revenue"].pct_change(12) * 100
                    # Calculate 3-month moving average revenue YoY
                    df["revenue_3m_avg"] = df["revenue"].rolling(3).mean()
                    df["revenue_3m_YoY"] = df["revenue_3m_avg"].pct_change(12) * 100
                    rev_dict[sym] = df
            except Exception as e:
                print(f"  [Warning] Revenue fetch failed for {sym} ({stock_id}): {e}")
            if (idx + 1) % 15 == 0:
                print(f"  Fetched revenue {idx + 1}/{len(symbols)} stocks...")
                time.sleep(0.5)

        with open(cache_file, "wb") as f:
            pickle.dump(rev_dict, f)
        print(f"[Fetcher] Successfully cached {len(rev_dict)} symbols revenue data.")
        return rev_dict

    def fetch_all_institutional(
        self,
        symbols: Optional[List[str]] = None,
        start_date: str = "2020-01-01",
        force_refresh: bool = False,
    ) -> Dict[str, pd.DataFrame]:
        """Fetch institutional investors buy/sell data and cache locally."""
        cache_file = os.path.join(self.cache_dir, "institutional_data.pkl")
        if not force_refresh and os.path.exists(cache_file):
            print(f"[Fetcher] Loading cached institutional data from {cache_file}...")
            with open(cache_file, "rb") as f:
                return pickle.load(f)

        if symbols is None:
            symbols = [item["symbol"] for item in get_twse_universe()]

        print(f"[Fetcher] Fetching institutional trading data for {len(symbols)} symbols...")
        inst_dict: Dict[str, pd.DataFrame] = {}

        for idx, sym in enumerate(symbols):
            if sym == BENCHMARK_SYMBOL:
                continue
            stock_id = self.get_stock_id(sym)
            try:
                df = self.dl.taiwan_stock_institutional_investors(stock_id=stock_id, start_date=start_date)
                if df is not None and not df.empty:
                    df["date"] = pd.to_datetime(df["date"])
                    df["net_buy"] = df["buy"] - df["sell"]
                    inst_dict[sym] = df
            except Exception as e:
                print(f"  [Warning] Institutional data failed for {sym}: {e}")
            if (idx + 1) % 15 == 0:
                print(f"  Fetched institutional {idx + 1}/{len(symbols)} stocks...")
                time.sleep(0.5)

        with open(cache_file, "wb") as f:
            pickle.dump(inst_dict, f)
        print(f"[Fetcher] Successfully cached {len(inst_dict)} symbols institutional data.")
        return inst_dict

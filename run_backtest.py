"""Main execution script for TWSE quantitative research and backtesting."""
import argparse
import sys
import os
import io

# Ensure UTF-8 output encoding on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import pandas as pd
from tabulate import tabulate

from src.data.universe import get_twse_universe, BENCHMARK_SYMBOL
from src.data.fetcher import DataFetcher
from src.factors.factor_builder import FactorBuilder
from src.strategies.strategy_a_revenue import RevenueBreakoutStrategy
from src.strategies.strategy_b_institutional import InstitutionalTrustStrategy
from src.strategies.strategy_c_multifactor import EnsembleMultiFactorStrategy
from src.backtest.engine import BacktestEngine
from src.backtest.metrics import calculate_performance_metrics
from src.visualize.report import generate_backtest_report


def main():
    parser = argparse.ArgumentParser(description="TWSE Quantitative Strategy Backtesting")
    parser.add_argument("--start", type=str, default="2020-01-01", help="Backtest start date")
    parser.add_argument("--end", type=str, default="2026-09-30", help="Backtest end date")
    parser.add_argument("--capital", type=float, default=1_000_000.0, help="Initial capital in NTD")
    parser.add_argument("--refresh", action="store_true", help="Force refresh cached data")
    args = parser.parse_args()

    print("=" * 70)
    print("[TWSE Quant] 台股量化策略回測系統：挑戰超越 0050 大盤基準")
    print(f"回測時間區間: {args.start} ~ {args.end}")
    print(f"初始資金規模: NT$ {args.capital:,.0f}")
    print("=" * 70)

    # 1. Fetch Market Data
    fetcher = DataFetcher()
    symbols = [item["symbol"] for item in get_twse_universe()]
    if BENCHMARK_SYMBOL not in symbols:
        symbols.append(BENCHMARK_SYMBOL)

    print("\n[Step 1/4] 載入台股日行情價格數據...")
    prices_dict = fetcher.fetch_all_prices(symbols=symbols, start_date=args.start, end_date=args.end, force_refresh=args.refresh)

    print("\n[Step 2/4] 載入台股月營收與三大法人籌碼數據...")
    revenue_dict = fetcher.fetch_all_revenue(symbols=symbols, start_date=args.start, force_refresh=args.refresh)
    inst_dict = fetcher.fetch_all_institutional(symbols=symbols, start_date=args.start, force_refresh=args.refresh)

    # 2. Factor Builder
    print("\n[Step 3/4] 初始化因子建構引擎與流動性濾網...")
    factor_builder = FactorBuilder(
        prices_dict=prices_dict,
        revenue_dict=revenue_dict,
        institutional_dict=inst_dict,
        liquidity_min_turnover=30_000_000.0,  # 20MA Turnover >= 30M NTD
    )

    # 3. Backtest Engine
    engine = BacktestEngine(
        prices_dict=prices_dict,
        factor_builder=factor_builder,
        initial_capital=args.capital,
    )

    print("\n[Step 4/4] 執行回測模擬（月調倉、扣除手續費 5 折 + 證交稅 + 滑價）...")
    # Benchmark
    print("  -> 模擬 Benchmark: 0050 Buy & Hold...")
    df_bench = engine.run_benchmark_0050(start_date=args.start, end_date=args.end)

    strategies = [
        RevenueBreakoutStrategy(top_n=15),
        InstitutionalTrustStrategy(top_n=15),
        EnsembleMultiFactorStrategy(top_n=15, bear_equity_exposure=0.20),
    ]

    results = {}
    for strat in strategies:
        print(f"  -> 模擬策略: {strat.name}...")
        res = engine.run_strategy(strat, start_date=args.start, end_date=args.end)
        metrics = calculate_performance_metrics(
            strategy_nav=res["daily_nav"]["nav"],
            benchmark_nav=df_bench["nav"],
        )
        res["metrics"] = metrics
        results[strat.name] = res

    # 4. Generate Reports and Visualization
    print("\n" + "=" * 70)
    print("[Summary] 回測綜合績效總評")
    print("=" * 70)
    md_table = generate_backtest_report(results, df_bench, output_dir="reports")
    print("\n" + md_table + "\n")

    print("\n[Done] 回測完成！報告與圖表已儲存至 reports/ 目錄。")


if __name__ == "__main__":
    main()

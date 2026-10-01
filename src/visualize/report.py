"""Visualization and reporting module for backtest results."""
import os
from typing import Dict, Any
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from tabulate import tabulate

from ..backtest.metrics import compute_drawdown_series


def generate_backtest_report(
    results: Dict[str, Dict[str, Any]],
    bench_nav_df: pd.DataFrame,
    output_dir: str = "reports",
) -> str:
    """
    Generate charts and Markdown summary report comparing strategies against 0050.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Set matplotlib style
    plt.rcParams["font.sans-serif"] = ["Microsoft JhengHei", "SimHei", "Arial", "sans-serif"]
    plt.rcParams["axes.unicode_minus"] = False

    fig, axes = plt.subplots(3, 1, figsize=(14, 16), gridspec_kw={"height_ratios": [3, 2, 2]})

    # 1. Cumulative Return NAV Plot
    ax1 = axes[0]
    bench_nav = bench_nav_df["nav"]
    norm_bench = (bench_nav / bench_nav.iloc[0]) * 100.0
    ax1.plot(norm_bench.index, norm_bench.values, label="Benchmark: 0050 (台灣50)", color="#333333", linestyle="--", linewidth=2.0)

    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]
    strat_keys = list(results.keys())

    for idx, key in enumerate(strat_keys):
        res = results[key]
        nav_s = res["daily_nav"]["nav"]
        norm_nav = (nav_s / nav_s.iloc[0]) * 100.0
        ax1.plot(norm_nav.index, norm_nav.values, label=res["strategy_name"], color=colors[idx % len(colors)], linewidth=2.2)

    ax1.set_title("台股量化多因子策略 vs 0050 累積資產淨值曲線 (2020 - 2026)", fontsize=14, fontweight="bold")
    ax1.set_ylabel("資產淨值 (基準點 = 100)", fontsize=12)
    ax1.grid(True, linestyle=":", alpha=0.6)
    ax1.legend(loc="upper left", fontsize=11, framealpha=0.9)

    # 2. Drawdown (Underwater Chart)
    ax2 = axes[1]
    bench_dd = compute_drawdown_series(bench_nav) * 100.0
    ax2.plot(bench_dd.index, bench_dd.values, label="0050 回撤", color="#555555", linestyle=":", linewidth=1.5)
    ax2.fill_between(bench_dd.index, bench_dd.values, 0, color="#888888", alpha=0.15)

    for idx, key in enumerate(strat_keys):
        res = results[key]
        nav_s = res["daily_nav"]["nav"]
        dd = compute_drawdown_series(nav_s) * 100.0
        ax2.plot(dd.index, dd.values, label=f"{res['strategy_name']} 回撤", color=colors[idx % len(colors)], linewidth=1.8)

    ax2.set_title("歷史回撤曲線 (Drawdown Underwater Chart)", fontsize=13, fontweight="bold")
    ax2.set_ylabel("回撤幅度 (%)", fontsize=12)
    ax2.grid(True, linestyle=":", alpha=0.6)
    ax2.legend(loc="lower left", fontsize=10, framealpha=0.9)

    # 3. Annual Returns Bar Chart
    ax3 = axes[2]
    annual_data = {}
    bench_annual = bench_nav.resample("YE").last().pct_change().dropna() * 100.0
    # Include first year
    first_year = (bench_nav.loc[f"{bench_nav.index[0].year}"].iloc[-1] / bench_nav.iloc[0] - 1.0) * 100.0
    bench_years = [bench_nav.index[0].year] + list(bench_annual.index.year)
    bench_vals = [first_year] + list(bench_annual.values)
    annual_data["0050"] = pd.Series(bench_vals, index=bench_years)

    for key in strat_keys:
        res = results[key]
        nav_s = res["daily_nav"]["nav"]
        res_annual = nav_s.resample("YE").last().pct_change().dropna() * 100.0
        fy = (nav_s.loc[f"{nav_s.index[0].year}"].iloc[-1] / nav_s.iloc[0] - 1.0) * 100.0
        ryears = [nav_s.index[0].year] + list(res_annual.index.year)
        rvals = [fy] + list(res_annual.values)
        annual_data[res["strategy_name"]] = pd.Series(rvals, index=ryears)

    df_annual = pd.DataFrame(annual_data).dropna(how="all").fillna(0.0)
    df_annual.plot(kind="bar", ax=ax3, width=0.8, colormap="tab10")
    ax3.set_title("歷年年度報酬率對比 (Annual Returns %)", fontsize=13, fontweight="bold")
    ax3.set_ylabel("年度報酬率 (%)", fontsize=12)
    ax3.set_xlabel("年度", fontsize=12)
    ax3.grid(True, linestyle=":", alpha=0.6)
    ax3.legend(loc="upper left", fontsize=10, framealpha=0.9)
    plt.xticks(rotation=0)

    plt.tight_layout()
    chart_path = os.path.join(output_dir, "backtest_comparison.png")
    plt.savefig(chart_path, dpi=300)
    plt.close()
    print(f"[Visualizer] Saved performance charts to {chart_path}")

    # Build Markdown Table
    table_rows = []
    headers = ["策略名稱", "總報酬率 (%)", "年化報酬 CAGR (%)", "波動度 (%)", "夏普值 Sharpe", "最大回撤 MDD (%)", "風暴比 Calmar", "月勝率 (%)", "Alpha (%)", "Beta"]

    # Add 0050 benchmark row
    bench_m = results[strat_keys[0]]["metrics"]
    table_rows.append([
        "Benchmark: 0050 Buy & Hold",
        f"{bench_m['bench_total_return']}%",
        f"{bench_m['bench_cagr']}%",
        f"{bench_m['bench_volatility']}%",
        "-",
        f"{bench_m['bench_mdd']}%",
        f"{round(bench_m['bench_cagr'] / bench_m['bench_mdd'], 2) if bench_m['bench_mdd'] > 0 else '-'}",
        "-",
        "0.00%",
        "1.00",
    ])

    for key in strat_keys:
        m = results[key]["metrics"]
        table_rows.append([
            results[key]["strategy_name"],
            f"{m['total_return']}%",
            f"{m['cagr']}%",
            f"{m['volatility']}%",
            f"{m['sharpe']}",
            f"{m['mdd']}%",
            f"{m['calmar']}",
            f"{m['monthly_win_rate']}%",
            f"{m['alpha']}%",
            f"{m['beta']}",
        ])

    md_table = tabulate(table_rows, headers=headers, tablefmt="pipe")

    # Save Markdown Summary
    report_md_path = os.path.join(output_dir, "backtest_summary.md")
    with open(report_md_path, "w", encoding="utf-8") as f:
        f.write("# 台股量化策略回測綜合研究報告\n\n")
        f.write("## 1. 策略績效指標對比表\n\n")
        f.write(md_table + "\n\n")
        f.write("## 2. 累計淨值與回撤走勢圖\n\n")
        f.write(f"![績效走勢圖](backtest_comparison.png)\n\n")
        f.write("## 3. 年度報酬分解\n\n")
        f.write(tabulate(df_annual.round(2), headers="keys", tablefmt="pipe") + "\n\n")

    print(f"[Visualizer] Saved markdown summary to {report_md_path}")
    return md_table

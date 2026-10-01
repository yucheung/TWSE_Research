"""Performance metrics module for quantitative strategy evaluation."""
from typing import Dict, Any
import pandas as pd
import numpy as np


def compute_drawdown_series(nav_series: pd.Series) -> pd.Series:
    """Compute drawdown series from NAV."""
    running_max = nav_series.cummax()
    drawdown = (nav_series - running_max) / running_max
    return drawdown


def calculate_performance_metrics(
    strategy_nav: pd.Series,
    benchmark_nav: pd.Series,
    risk_free_rate: float = 0.015,
) -> Dict[str, Any]:
    """
    Calculate comprehensive performance metrics:
    - Total Return (%)
    - CAGR (%)
    - Volatility (%)
    - Sharpe Ratio
    - Sortino Ratio
    - Max Drawdown (%)
    - Calmar Ratio
    - Monthly Win Rate (%)
    - Beta vs Benchmark
    - Alpha vs Benchmark (Annualized %)
    - Information Ratio
    """
    strat_df = pd.DataFrame({"nav": strategy_nav}).dropna()
    bench_df = pd.DataFrame({"bench_nav": benchmark_nav}).dropna()

    # Align dates
    df = strat_df.join(bench_df, how="inner")
    if len(df) < 20:
        return {}

    days = (df.index[-1] - df.index[0]).days
    years = max(days / 365.25, 0.1)

    # Returns
    df["strat_ret"] = df["nav"].pct_change().fillna(0.0)
    df["bench_ret"] = df["bench_nav"].pct_change().fillna(0.0)

    # Total Return
    total_ret = (df["nav"].iloc[-1] / df["nav"].iloc[0] - 1.0) * 100.0
    bench_total_ret = (df["bench_nav"].iloc[-1] / df["bench_nav"].iloc[0] - 1.0) * 100.0

    # CAGR
    cagr = ((df["nav"].iloc[-1] / df["nav"].iloc[0]) ** (1.0 / years) - 1.0) * 100.0
    bench_cagr = ((df["bench_nav"].iloc[-1] / df["bench_nav"].iloc[0]) ** (1.0 / years) - 1.0) * 100.0

    # Volatility (Annualized)
    vol = float(df["strat_ret"].std() * np.sqrt(252) * 100.0)
    bench_vol = float(df["bench_ret"].std() * np.sqrt(252) * 100.0)

    # Sharpe Ratio
    rf_daily = risk_free_rate / 252.0
    excess_ret = df["strat_ret"] - rf_daily
    sharpe = float(np.sqrt(252) * excess_ret.mean() / (df["strat_ret"].std() + 1e-8))

    # Sortino Ratio
    downside_ret = df["strat_ret"][df["strat_ret"] < 0]
    downside_std = downside_ret.std() * np.sqrt(252)
    sortino = float((cagr / 100.0 - risk_free_rate) / (downside_std + 1e-8)) if downside_std > 0 else 0.0

    # Drawdown
    dd_series = compute_drawdown_series(df["nav"])
    mdd = float(abs(dd_series.min()) * 100.0)

    bench_dd_series = compute_drawdown_series(df["bench_nav"])
    bench_mdd = float(abs(bench_dd_series.min()) * 100.0)

    # Calmar Ratio
    calmar = float(cagr / mdd) if mdd > 0 else 0.0

    # Monthly Win Rate
    monthly_strat = df["nav"].resample("ME").last().pct_change().dropna()
    monthly_bench = df["bench_nav"].resample("ME").last().pct_change().dropna()
    win_rate = float((monthly_strat > 0).mean() * 100.0) if len(monthly_strat) > 0 else 0.0
    beat_market_rate = float((monthly_strat > monthly_bench).mean() * 100.0) if len(monthly_strat) > 0 else 0.0

    # Beta & Alpha
    cov_matrix = np.cov(df["strat_ret"], df["bench_ret"])
    cov = cov_matrix[0, 1]
    bench_var = cov_matrix[1, 1]
    beta = float(cov / bench_var) if bench_var > 0 else 1.0
    alpha = float(cagr - (risk_free_rate * 100.0 + beta * (bench_cagr - risk_free_rate * 100.0)))

    # Tracking error & Information Ratio
    active_ret = df["strat_ret"] - df["bench_ret"]
    tracking_error = float(active_ret.std() * np.sqrt(252) * 100.0)
    info_ratio = float((cagr - bench_cagr) / (tracking_error + 1e-8))

    return {
        "total_return": round(total_ret, 2),
        "cagr": round(cagr, 2),
        "volatility": round(vol, 2),
        "sharpe": round(sharpe, 2),
        "sortino": round(sortino, 2),
        "mdd": round(mdd, 2),
        "calmar": round(calmar, 2),
        "monthly_win_rate": round(win_rate, 2),
        "beat_market_rate": round(beat_market_rate, 2),
        "alpha": round(alpha, 2),
        "beta": round(beta, 2),
        "info_ratio": round(info_ratio, 2),
        "bench_total_return": round(bench_total_ret, 2),
        "bench_cagr": round(bench_cagr, 2),
        "bench_volatility": round(bench_vol, 2),
        "bench_mdd": round(bench_mdd, 2),
    }

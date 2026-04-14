#!/usr/bin/env python3
"""Validate synthetic bond return approximation against real ETF data.

Compares synthetic daily bond returns (from ``build_asset_returns`` in
``src.backtester``) against TLT (long bonds) and SHY (short bonds) total
returns sourced from Yahoo Finance.

See ``specs/backtester.md`` section "Bond return approximation" for the
formula and accuracy threshold being checked:

    daily_return = -duration * (yield[t] - yield[t-1]) + yield[t-1] / 252
    Per-decade CAGR divergence <= 0.50 ppt/yr
    Correlation of monthly returns >= 0.90

This is a reporting script, not a check — it always exits 0.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.backtester import build_asset_returns
from src.data_fetcher import load_all_fred, load_all_yahoo, load_series


CORRELATION_FLOOR = 0.90
PER_DECADE_CAGR_TOLERANCE = 0.0050  # 0.50 percentage points per year


def _load_etf_daily_total_returns(symbol: str) -> pd.Series:
    """Load an ETF's daily total returns from the Yahoo cache.

    Prefers the adjusted close (dividends reinvested) when available;
    ``yfinance`` already adjusts ``Close`` for splits and dividends when the
    ticker history is fetched without ``auto_adjust=False``.
    """
    df = load_series("yahoo", symbol)
    if "Adj Close" in df.columns:
        prices = df["Adj Close"]
    else:
        prices = df["Close"]
    prices = prices.dropna().sort_index()
    rets = prices.pct_change().dropna()
    rets.index = pd.DatetimeIndex(rets.index)
    rets.name = f"{symbol}_ret"
    return rets


def _resample_to_monthly(daily_returns: pd.Series) -> pd.Series:
    """Compound daily returns into monthly returns."""
    monthly = (1.0 + daily_returns).resample("ME").prod() - 1.0
    return monthly.dropna()


def _cagr(monthly_returns: pd.Series) -> float:
    if len(monthly_returns) == 0:
        return float("nan")
    total = float((1.0 + monthly_returns).prod())
    years = len(monthly_returns) / 12.0
    if years <= 0 or total <= 0:
        return float("nan")
    return total ** (1.0 / years) - 1.0


def _decade_label(ts: pd.Timestamp) -> str:
    decade_start = (ts.year // 10) * 10
    return f"{decade_start}s"


def _per_decade_cagr(monthly: pd.Series) -> pd.Series:
    labels = monthly.index.map(_decade_label)
    grouped = monthly.groupby(labels)
    return grouped.apply(_cagr)


def _format_table(rows: list[dict]) -> str:
    cols = ["asset", "decade", "synthetic_CAGR", "ETF_CAGR",
            "divergence_ppt_per_yr", "correlation", "n_months"]
    widths = {c: max(len(c), max(len(str(r[c])) for r in rows)) for c in cols}
    header = " | ".join(c.ljust(widths[c]) for c in cols)
    sep = "-+-".join("-" * widths[c] for c in cols)
    lines = [header, sep]
    for r in rows:
        lines.append(" | ".join(str(r[c]).ljust(widths[c]) for c in cols))
    return "\n".join(lines)


def _validate_asset(
    asset_name: str,
    synthetic_daily: pd.Series,
    etf_symbol: str,
) -> tuple[list[dict], float, float, str]:
    """Return (rows, mae, correlation, verdict)."""
    etf_daily = _load_etf_daily_total_returns(etf_symbol)

    synthetic_daily = synthetic_daily.dropna()
    synthetic_daily.index = pd.DatetimeIndex(synthetic_daily.index)

    synthetic_monthly = _resample_to_monthly(synthetic_daily)
    etf_monthly = _resample_to_monthly(etf_daily)

    aligned = pd.concat(
        [synthetic_monthly.rename("synthetic"), etf_monthly.rename("etf")],
        axis=1,
        join="inner",
    ).dropna()

    if aligned.empty:
        return [], float("nan"), float("nan"), "NO_OVERLAP"

    mae = float((aligned["synthetic"] - aligned["etf"]).abs().mean())
    correlation = float(aligned["synthetic"].corr(aligned["etf"]))

    synth_decades = _per_decade_cagr(aligned["synthetic"])
    etf_decades = _per_decade_cagr(aligned["etf"])
    months_per_decade = aligned.groupby(
        aligned.index.map(_decade_label)
    ).size()

    rows: list[dict] = []
    max_abs_divergence = 0.0
    for decade in synth_decades.index:
        synth = synth_decades.loc[decade]
        etf = etf_decades.loc[decade]
        divergence = synth - etf
        max_abs_divergence = max(max_abs_divergence, abs(divergence))
        rows.append({
            "asset": asset_name,
            "decade": decade,
            "synthetic_CAGR": f"{synth * 100:+.2f}%",
            "ETF_CAGR": f"{etf * 100:+.2f}%",
            "divergence_ppt_per_yr": f"{divergence * 100:+.2f}",
            "correlation": f"{correlation:.3f}",
            "n_months": int(months_per_decade.loc[decade]),
        })

    meets_cagr = max_abs_divergence <= PER_DECADE_CAGR_TOLERANCE
    meets_corr = correlation >= CORRELATION_FLOOR
    verdict = "PASS" if (meets_cagr and meets_corr) else "FAIL"
    return rows, mae, correlation, verdict


def main() -> int:
    print("Loading cached FRED and Yahoo data...")
    fred_data = load_all_fred()
    yahoo_data = load_all_yahoo()

    # build_asset_returns expects ``GS2_yield`` as a daily-forward-filled series.
    if "GS2" in fred_data:
        gs2_daily = fred_data["GS2"].squeeze().resample("B").ffill()
        fred_data["GS2_yield"] = gs2_daily

    combined = {**fred_data, **yahoo_data}
    returns = build_asset_returns(combined, start="2002-07-01")

    print(f"Synthetic returns built: {returns.index[0].date()} → "
          f"{returns.index[-1].date()}  ({len(returns)} days)")

    all_rows: list[dict] = []
    verdicts: dict[str, tuple[float, float, str]] = {}

    for asset_name, etf_symbol in [("long_bonds", "TLT"), ("short_bonds", "SHY")]:
        synthetic_daily = returns[asset_name]
        rows, mae, corr, verdict = _validate_asset(
            asset_name, synthetic_daily, etf_symbol
        )
        all_rows.extend(rows)
        verdicts[asset_name] = (mae, corr, verdict)

    print()
    print("Per-decade comparison (synthetic vs ETF):")
    print(_format_table(all_rows))
    print()

    for asset_name, (mae, corr, verdict) in verdicts.items():
        etf = "TLT" if asset_name == "long_bonds" else "SHY"
        print(f"{asset_name} vs {etf}: "
              f"MAE(monthly)={mae * 100:.3f}%  corr={corr:.3f}  -> {verdict} "
              f"(threshold: per-decade |CAGR div| <= "
              f"{PER_DECADE_CAGR_TOLERANCE * 100:.2f}ppt/yr and corr >= "
              f"{CORRELATION_FLOOR:.2f})")

    return 0


if __name__ == "__main__":
    sys.exit(main())

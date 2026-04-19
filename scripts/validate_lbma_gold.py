#!/usr/bin/env python3
"""Validate GOLDPMGBD228NLBM (LBMA Gold PM Fix) against GC=F.

This is the Phase 1 validation gate for issue #107 (replace the pre-2000
gold proxy). PR #106 established that the incumbent proxy WPUSI019011
(FRED PPI: Metals and Metal Products) fails the ``specs/backtester.md``
§"Bond return approximation → Accuracy threshold" correlation bar — the
overall monthly correlation against GC=F was 0.097 vs. the required
>= 0.90. See ``docs/research/gold_proxy_validation.md`` and
``scripts/validate_gold_splice.py`` for the baseline measurement.

Issue #107 proposes GOLDPMGBD228NLBM (LBMA Gold PM Fixing Price, USD;
daily, FRED-mirrored, back to 1968-04-01) as the replacement. Before
committing to the splice swap in Phase 2, Phase 1 measures LBMA's
correlation with GC=F in the post-2000 overlap to confirm the
replacement clears the >= 0.90 bar.

The threshold and overlap window are identical to the WPUSI019011
script, so results are apples-to-apples with the PR #106 baseline:

    Correlation of monthly returns >= 0.90
    Overlap measurement from 2000-08-30 onward (the current splice date)

Both series are daily in this script — LBMA daily returns are compounded
to monthly the same way GC=F daily returns are, making the pipeline
more symmetric than the WPUSI019011 monthly-resample path.

Per-decade CAGR divergence and the same three regime-turn stress windows
are reported for diagnostics.

This is a reporting script, not a check — it always exits 0.

IMPORTANT: The overlap period (2000-08-30 → present) does NOT include
the 1979-82 gold bull/bust regime. We can only infer how LBMA tracks
real gold in that era by analogy to the 2008-09 and 2020 stress windows
that ARE in overlap. See ``docs/research/gold_proxy_validation.md``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_fetcher import load_series


CORRELATION_FLOOR = 0.90

# The splice date enforced by the backtester (GOLD_DEFAULT_SPLICE in
# src/backtester.py). Overlap measurement starts here to match the
# PR #106 baseline measurement window.
OVERLAP_START = pd.Timestamp("2000-08-30")

# Same stress windows used in scripts/validate_gold_splice.py — we want
# to see how LBMA handles the same regime turns WPUSI019011 was measured
# against.
STRESS_WINDOWS = [
    ("2008 GFC / deleveraging", "2008-10-01", "2009-03-31"),
    ("2020 COVID shock",        "2020-02-01", "2020-04-30"),
    ("2022 inflation surge",    "2022-01-01", "2022-12-31"),
]


def _load_lbma_monthly_returns() -> pd.Series:
    """Load GOLDPMGBD228NLBM daily levels and compound to monthly returns."""
    df = load_series("fred", "GOLDPMGBD228NLBM")
    levels = df.squeeze()
    levels = levels.dropna().sort_index()
    levels.index = pd.DatetimeIndex(levels.index)
    daily_rets = levels.pct_change().dropna()
    monthly = (1.0 + daily_rets).resample("ME").prod() - 1.0
    monthly = monthly.dropna()
    monthly.name = "GOLDPMGBD228NLBM_ret"
    return monthly


def _load_gold_monthly_returns() -> pd.Series:
    """Load GC=F daily Close prices and compound to monthly returns."""
    df = load_series("yahoo", "GC=F")
    if "Close" not in df.columns:
        raise RuntimeError(
            "GC=F cached frame missing 'Close' column — "
            "run scripts/fetch_data.py to refresh"
        )
    prices = df["Close"].dropna().sort_index()
    prices.index = pd.DatetimeIndex(prices.index)
    daily_rets = prices.pct_change().dropna()
    monthly = (1.0 + daily_rets).resample("ME").prod() - 1.0
    monthly = monthly.dropna()
    monthly.name = "GC=F_ret"
    return monthly


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
    return monthly.groupby(labels).apply(_cagr)


def _format_table(rows: list[dict], cols: list[str]) -> str:
    widths = {c: max(len(c), max(len(str(r[c])) for r in rows)) for c in cols}
    header = " | ".join(c.ljust(widths[c]) for c in cols)
    sep = "-+-".join("-" * widths[c] for c in cols)
    lines = [header, sep]
    for r in rows:
        lines.append(" | ".join(str(r[c]).ljust(widths[c]) for c in cols))
    return "\n".join(lines)


def _measure_stress_window(
    aligned: pd.DataFrame,
    label: str,
    start: str,
    end: str,
) -> dict:
    window = aligned.loc[start:end]
    if len(window) < 2:
        return {
            "window": label,
            "start": start,
            "end": end,
            "n_months": len(window),
            "correlation": "n/a",
            "max_abs_deviation": "n/a",
            "proxy_cum_return": "n/a",
            "gold_cum_return": "n/a",
        }
    corr = float(window["proxy"].corr(window["gold"]))
    dev = (window["proxy"] - window["gold"]).abs().max()
    proxy_cum = float((1.0 + window["proxy"]).prod() - 1.0)
    gold_cum = float((1.0 + window["gold"]).prod() - 1.0)
    return {
        "window": label,
        "start": start,
        "end": end,
        "n_months": len(window),
        "correlation": f"{corr:.3f}",
        "max_abs_deviation": f"{dev * 100:.2f}%",
        "proxy_cum_return": f"{proxy_cum * 100:+.2f}%",
        "gold_cum_return": f"{gold_cum * 100:+.2f}%",
    }


def main() -> int:
    print("Loading cached GOLDPMGBD228NLBM (FRED) and GC=F (Yahoo)...")
    proxy_monthly = _load_lbma_monthly_returns()
    gold_monthly = _load_gold_monthly_returns()

    print(
        f"  GOLDPMGBD228NLBM monthly returns: "
        f"{proxy_monthly.index[0].date()} → {proxy_monthly.index[-1].date()}  "
        f"({len(proxy_monthly)} months)"
    )
    print(
        f"  GC=F monthly returns:             "
        f"{gold_monthly.index[0].date()} → {gold_monthly.index[-1].date()}  "
        f"({len(gold_monthly)} months)"
    )

    aligned = pd.concat(
        [proxy_monthly.rename("proxy"), gold_monthly.rename("gold")],
        axis=1,
        join="inner",
    ).dropna()
    aligned = aligned.loc[aligned.index >= OVERLAP_START]

    if aligned.empty:
        print("ERROR: no monthly overlap between GOLDPMGBD228NLBM and GC=F "
              "at or after the splice date.")
        return 0

    overlap_start = aligned.index[0].date()
    overlap_end = aligned.index[-1].date()
    print(
        f"  Overlap window (month-end-aligned): "
        f"{overlap_start} → {overlap_end}  ({len(aligned)} months)"
    )

    overall_corr = float(aligned["proxy"].corr(aligned["gold"]))
    mae_monthly = float((aligned["proxy"] - aligned["gold"]).abs().mean())

    proxy_decades = _per_decade_cagr(aligned["proxy"])
    gold_decades = _per_decade_cagr(aligned["gold"])
    months_per_decade = aligned.groupby(
        aligned.index.map(_decade_label)
    ).size()

    decade_rows: list[dict] = []
    divergences: list[float] = []
    for decade in proxy_decades.index:
        proxy_cagr = proxy_decades.loc[decade]
        gold_cagr = gold_decades.loc[decade]
        divergence = proxy_cagr - gold_cagr
        divergences.append(divergence)
        decade_rows.append({
            "decade": decade,
            "GOLDPMGBD228NLBM_CAGR": f"{proxy_cagr * 100:+.2f}%",
            "GC=F_CAGR": f"{gold_cagr * 100:+.2f}%",
            "divergence_ppt_per_yr": f"{divergence * 100:+.2f}",
            "n_months": int(months_per_decade.loc[decade]),
        })

    print()
    print("Per-decade CAGR comparison (GOLDPMGBD228NLBM-derived vs GC=F):")
    print(_format_table(
        decade_rows,
        cols=["decade", "GOLDPMGBD228NLBM_CAGR", "GC=F_CAGR",
              "divergence_ppt_per_yr", "n_months"],
    ))

    print()
    print("Regime-turn stress windows (analogues for 1979-82 NOT in overlap):")
    stress_rows = [
        _measure_stress_window(aligned, label, start, end)
        for label, start, end in STRESS_WINDOWS
    ]
    print(_format_table(
        stress_rows,
        cols=["window", "start", "end", "n_months", "correlation",
              "max_abs_deviation", "proxy_cum_return", "gold_cum_return"],
    ))

    mean_abs_divergence = float(np.mean(np.abs(divergences))) if divergences else float("nan")

    print()
    print("Headline numbers (GOLDPMGBD228NLBM vs GC=F, monthly):")
    print(f"  overlap               = {overlap_start} → {overlap_end}  "
          f"({len(aligned)} months)")
    print(f"  correlation           = {overall_corr:.3f}  "
          f"(threshold: >= {CORRELATION_FLOOR:.2f})")
    print(f"  MAE(monthly)          = {mae_monthly * 100:.3f}%")
    print(f"  mean |CAGR div|/decade= {mean_abs_divergence * 100:.2f} ppt/yr")

    verdict = "PASS" if overall_corr >= CORRELATION_FLOOR else "FAIL"
    print(f"  correlation verdict   = {verdict}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

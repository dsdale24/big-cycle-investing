"""Diagnostic: does the Internal Order Stress Index lead, coincide with, or
lag S&P 500 drawdowns? (Issue #4 Path A.)

Loads the cached FRED + Yahoo data, builds the composite via
``src.indicators.internal_order_stress_index`` (walk-forward-safe), and
characterises its relationship to S&P 500 monthly drawdowns and returns
over 1975-present.

Outputs a markdown report at ``docs/research/civilizational_composite_diagnostic.md``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_fetcher import load_all_fred, load_all_yahoo  # noqa: E402
from src.indicators import internal_order_stress_index  # noqa: E402


REQUIRED_FRED = ("GINIALLRF", "USEPUINDXM", "UMCSENT")
DRAWDOWN_THRESHOLD = -0.15  # -15%
LEAD_LAG_MONTHS = (-24, -12, -6, -3, 0, 3, 6, 12, 24)


def _squeeze_series(df: pd.DataFrame, name: str) -> pd.Series:
    s = df.squeeze()
    if isinstance(s, pd.DataFrame):
        # Multi-column → take the column matching the series id, or first.
        s = s.iloc[:, 0]
    s.name = name
    return s


def _spx_monthly(yahoo: dict[str, pd.DataFrame]) -> pd.Series:
    spx = yahoo["^GSPC"]["Close"].resample("ME").last().dropna()
    spx.name = "spx"
    return spx


def _compute_drawdown(price: pd.Series) -> pd.Series:
    running_peak = price.cummax()
    return price / running_peak - 1.0


def _identify_drawdown_episodes(drawdown: pd.Series, threshold: float) -> list[dict]:
    """Walk monthly drawdowns; group runs where DD trough exceeds |threshold|.

    An episode starts when drawdown first drops below 0 from a fresh peak
    (price = running peak) and ends when price recovers to a new peak.
    Only episodes whose minimum drawdown is <= threshold are kept.
    """
    episodes: list[dict] = []
    in_episode = False
    start_date = None
    trough_date = None
    trough_dd = 0.0
    for date, dd in drawdown.items():
        if not in_episode:
            if dd < 0:
                in_episode = True
                start_date = date
                trough_date = date
                trough_dd = dd
        else:
            if dd < trough_dd:
                trough_dd = dd
                trough_date = date
            if dd >= 0:  # back to a fresh peak
                if trough_dd <= threshold:
                    episodes.append({
                        "start": start_date,
                        "trough": trough_date,
                        "recovery": date,
                        "trough_dd": trough_dd,
                    })
                in_episode = False
                start_date = None
                trough_date = None
                trough_dd = 0.0
    # Open episode at end of series
    if in_episode and trough_dd <= threshold:
        episodes.append({
            "start": start_date,
            "trough": trough_date,
            "recovery": None,
            "trough_dd": trough_dd,
        })
    return episodes


def _value_at_or_before(series: pd.Series, date: pd.Timestamp) -> float:
    """Most recent valid value at or before ``date``; NaN if none."""
    sub = series.loc[:date].dropna()
    if sub.empty:
        return float("nan")
    return float(sub.iloc[-1])


def _lead_lag_correlations(
    composite: pd.Series,
    returns: pd.Series,
    lags: tuple[int, ...],
) -> dict[int, float]:
    """corr(composite_t, returns_{t-k}) for each k in lags (issue #4 spec).

    Spec convention:
      - k < 0  →  composite_t correlates with returns_{t-k} = returns AFTER t,
                  i.e., composite is **leading** future returns.
      - k = 0  →  coincident.
      - k > 0  →  composite_t correlates with returns_{t-k} = returns BEFORE t,
                  i.e., composite is **lagging** past returns.
    """
    df = pd.concat([composite.rename("c"), returns.rename("r")], axis=1).dropna()
    out: dict[int, float] = {}
    for k in lags:
        # returns at t-k = returns shifted forward by k (so row at t carries
        # the value that lives at t-k in the original series).
        shifted = df["r"].shift(k) if k != 0 else df["r"]
        aligned = pd.concat([df["c"], shifted], axis=1).dropna()
        if len(aligned) < 24:
            out[k] = float("nan")
        else:
            out[k] = float(aligned.iloc[:, 0].corr(aligned.iloc[:, 1]))
    return out


def _format_episode_table(
    episodes: list[dict],
    composite: pd.Series,
) -> str:
    header = (
        "| Start | Trough | Recovery | Trough DD | Composite −12mo | "
        "Composite −6mo | Composite at trough | Composite +12mo |\n"
        "|---|---|---|---|---|---|---|---|"
    )
    rows = [header]
    for ep in episodes:
        start = ep["start"]
        trough = ep["trough"]
        recovery = ep["recovery"]
        c_m12 = _value_at_or_before(composite, start - pd.DateOffset(months=12))
        c_m6 = _value_at_or_before(composite, start - pd.DateOffset(months=6))
        c_trough = _value_at_or_before(composite, trough)
        c_p12 = _value_at_or_before(composite, trough + pd.DateOffset(months=12))
        rows.append(
            f"| {start.date()} | {trough.date()} | "
            f"{recovery.date() if recovery is not None else 'open'} | "
            f"{ep['trough_dd']:.1%} | "
            f"{c_m12:+.2f} | {c_m6:+.2f} | {c_trough:+.2f} | {c_p12:+.2f} |"
        )
    return "\n".join(rows)


def _format_corr_table(corrs: dict[int, float]) -> str:
    header = (
        "| Lag k (months) | Interpretation | corr(composite_t, return_{t-k}) |\n"
        "|---|---|---|"
    )
    rows = [header]
    for k in sorted(corrs.keys()):
        if k < 0:
            interp = f"composite leads by {-k}m (returns realised after t)"
        elif k > 0:
            interp = f"composite lags by {k}m (returns realised before t)"
        else:
            interp = "coincident"
        v = corrs[k]
        rows.append(f"| {k:+d} | {interp} | {v:+.3f} |")
    return "\n".join(rows)


def _interpret(corrs: dict[int, float], composite: pd.Series) -> str:
    finite = {k: v for k, v in corrs.items() if not np.isnan(v)}
    if not finite:
        return (
            "Insufficient overlap between composite and returns to compute "
            "lead-lag correlations."
        )
    # Find k that maximises absolute correlation.
    k_peak = max(finite, key=lambda k: abs(finite[k]))
    peak = finite[k_peak]
    if k_peak < 0:
        regime = (
            f"the composite at month t is most strongly related to equity "
            f"returns realised {-k_peak} months **after** t — i.e., the "
            f"composite is **leading** future returns"
        )
    elif k_peak > 0:
        regime = (
            f"the composite at month t is most strongly related to equity "
            f"returns realised {k_peak} months **before** t — i.e., the "
            f"composite is **lagging** past returns"
        )
    else:
        regime = "the composite is **coincident** with equity returns"

    coincident = finite.get(0, float("nan"))
    lead_12 = finite.get(-12, float("nan"))   # k=-12 → returns 12m after t
    lag_12 = finite.get(12, float("nan"))     # k=+12 → returns 12m before t

    cur = composite.dropna().iloc[-1]
    cur_date = composite.dropna().index[-1].strftime("%Y-%m")
    hi = composite.max()
    hi_date = composite.idxmax().strftime("%Y-%m")

    caveat = (
        "**Caveat (sample-scope memory):** This characterisation rests on a "
        "single sample — US equities, 1975-present. The composite has lived "
        "through ~50 years and a handful of large drawdowns; that's a small "
        "number of independent episodes for any signal claim. The dynamic could "
        "differ in other countries, other asset classes, or under structurally "
        "different macro regimes. Treat this as a hypothesis for further "
        "stress-testing, not a proven leading indicator."
    )

    return (
        f"By peak absolute correlation, {regime} (peak at lag k={k_peak:+d}, "
        f"corr={peak:+.3f}). Coincident corr is {coincident:+.3f}; corr at "
        f"k=−12 (composite leading future 12m returns) is {lead_12:+.3f}; "
        f"corr at k=+12 (composite lagging past 12m returns) is "
        f"{lag_12:+.3f}.\n\n"
        f"Composite latest reading: **{cur:+.2f}** ({cur_date}). "
        f"Historical high: **{hi:+.2f}** ({hi_date}).\n\n"
        + caveat
    )


def main() -> int:
    fred = load_all_fred()
    yahoo = load_all_yahoo()

    missing = [s for s in REQUIRED_FRED if s not in fred]
    if missing:
        print(
            f"ERROR: required FRED series missing from cache: {missing}. "
            f"Run scripts/fetch_data.py.",
            file=sys.stderr,
        )
        return 2
    if "^GSPC" not in yahoo:
        print(
            "ERROR: required Yahoo series ^GSPC missing from cache. "
            "Run scripts/fetch_data.py.",
            file=sys.stderr,
        )
        return 2

    gini = _squeeze_series(fred["GINIALLRF"], "GINIALLRF")
    epu = _squeeze_series(fred["USEPUINDXM"], "USEPUINDXM")
    sentiment = _squeeze_series(fred["UMCSENT"], "UMCSENT")

    composite = internal_order_stress_index(
        gini, epu, sentiment,
        publication_lag_months=9,
        zscore_window=120,
    )

    spx = _spx_monthly(yahoo)
    drawdown = _compute_drawdown(spx)
    monthly_returns = spx.pct_change()

    # Restrict to overlap with composite (composite is sparser due to warm-up).
    composite_aligned = composite.dropna()
    overlap_start = max(composite_aligned.index.min(), spx.index.min())
    overlap_end = min(composite_aligned.index.max(), spx.index.max())
    composite_aligned = composite_aligned.loc[overlap_start:overlap_end]
    drawdown_aligned = drawdown.loc[overlap_start:overlap_end]
    returns_aligned = monthly_returns.loc[overlap_start:overlap_end]

    episodes = _identify_drawdown_episodes(drawdown_aligned, DRAWDOWN_THRESHOLD)
    corrs = _lead_lag_correlations(
        composite_aligned, returns_aligned, LEAD_LAG_MONTHS,
    )

    episode_table = _format_episode_table(episodes, composite)
    corr_table = _format_corr_table(corrs)
    interpretation = _interpret(corrs, composite)

    do_not_edit_header = (
        "<!-- Generated by scripts/civilizational_composite_diagnostic.py. "
        "Do not edit by hand; regenerate via the script. -->\n\n"
    )

    composite_first = composite_aligned.index.min().date()
    composite_last = composite_aligned.index.max().date()

    report = (
        do_not_edit_header
        + "# Civilizational composite diagnostic (issue #4 Path A)\n\n"
        f"Composite period: **{composite_first} → {composite_last}** "
        f"({len(composite_aligned)} monthly observations).\n"
        f"Construction: equal-weight mean of rolling 120m z-scores of\n"
        f"GINIALLRF (annual, shifted +9 months for publication lag),\n"
        f"USEPUINDXM (monthly), and −UMCSENT (monthly, inverted).\n\n"
        "## Lead-lag correlation profile (vs S&P 500 monthly returns)\n\n"
        + corr_table + "\n\n"
        f"S&P 500 drawdown threshold for episodes: **{DRAWDOWN_THRESHOLD:.0%}**.\n\n"
        f"## Drawdown episodes (>{abs(DRAWDOWN_THRESHOLD):.0%} S&P 500 declines)\n\n"
        + episode_table + "\n\n"
        "## Interpretation\n\n"
        + interpretation + "\n\n"
        "## Method\n\n"
        "- **Composite**: `src.indicators.internal_order_stress_index` with\n"
        "  `publication_lag_months=9`, `zscore_window=120` (10y monthly).\n"
        "- **Inputs**: GINIALLRF (annual, shifted forward 9 months for typical\n"
        "  Census/World Bank release lag), USEPUINDXM (Baker-Bloom-Davis EPU,\n"
        "  monthly), UMCSENT (UMich consumer sentiment, monthly, inverted so\n"
        "  higher = more stress).\n"
        "- **Drawdown**: `price / running_peak − 1` on month-end S&P 500.\n"
        "- **Episodes**: contiguous below-peak runs whose minimum DD ≤ "
        f"{DRAWDOWN_THRESHOLD:.0%}.\n"
        "- **Lead-lag correlation**: `corr(composite_t, return_{t-k})`.\n"
        "  Negative k means the composite leads (correlates with future returns,\n"
        "  realised after t); positive k means it lags (correlates with past\n"
        "  returns, realised before t).\n"
    )

    out_path = ROOT / "docs" / "research" / "civilizational_composite_diagnostic.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report)
    print(f"Wrote {out_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Diagnostic: decompose the Internal Order Stress composite into its
components and pairwise sub-composites — does any single component (or any
two-of-three pair) lead S&P 500 cyclical drawdowns, even though the full
three-way average lags? (Issue #49.)

Builds the same monthly z-score series used internally by
``src.indicators.internal_order_stress_index`` (Gini publication-shifted, EPU,
inverted UMCSENT) and runs the same lead-lag and drawdown-episode analysis as
``scripts/civilizational_composite_diagnostic.py`` (issue #48) on each single
component and on each pairwise equal-weight composite.

Outputs a markdown report at
``docs/research/civilizational_component_decomposition.md``.
"""

from __future__ import annotations

import sys
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_fetcher import load_all_fred, load_all_yahoo  # noqa: E402
from src.indicators import (  # noqa: E402
    _rolling_zscore_strict,
    shift_by_publication_lag,
)


REQUIRED_FRED = ("GINIALLRF", "USEPUINDXM", "UMCSENT")
DRAWDOWN_THRESHOLD = -0.15  # -15%
LEAD_LAG_MONTHS = (-24, -12, -6, -3, 0, 3, 6, 12, 24)
PUBLICATION_LAG_MONTHS = 9
ZSCORE_WINDOW = 120


def _squeeze_series(df: pd.DataFrame, name: str) -> pd.Series:
    s = df.squeeze()
    if isinstance(s, pd.DataFrame):
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
            if dd >= 0:
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
    if in_episode and trough_dd <= threshold:
        episodes.append({
            "start": start_date,
            "trough": trough_date,
            "recovery": None,
            "trough_dd": trough_dd,
        })
    return episodes


def _value_at_or_before(series: pd.Series, date: pd.Timestamp) -> float:
    sub = series.loc[:date].dropna()
    if sub.empty:
        return float("nan")
    return float(sub.iloc[-1])


def _lead_lag_correlations(
    composite: pd.Series,
    returns: pd.Series,
    lags: tuple[int, ...],
) -> dict[int, float]:
    df = pd.concat([composite.rename("c"), returns.rename("r")], axis=1).dropna()
    out: dict[int, float] = {}
    for k in lags:
        shifted = df["r"].shift(k) if k != 0 else df["r"]
        aligned = pd.concat([df["c"], shifted], axis=1).dropna()
        if len(aligned) < 24:
            out[k] = float("nan")
        else:
            out[k] = float(aligned.iloc[:, 0].corr(aligned.iloc[:, 1]))
    return out


def _format_episode_table(
    episodes: list[dict],
    series: pd.Series,
    label: str,
) -> str:
    header = (
        f"| Start | Trough | Recovery | Trough DD | {label} −12mo | "
        f"{label} −6mo | {label} at trough | {label} +12mo |\n"
        "|---|---|---|---|---|---|---|---|"
    )
    rows = [header]
    for ep in episodes:
        start = ep["start"]
        trough = ep["trough"]
        recovery = ep["recovery"]
        c_m12 = _value_at_or_before(series, start - pd.DateOffset(months=12))
        c_m6 = _value_at_or_before(series, start - pd.DateOffset(months=6))
        c_trough = _value_at_or_before(series, trough)
        c_p12 = _value_at_or_before(series, trough + pd.DateOffset(months=12))
        rows.append(
            f"| {start.date()} | {trough.date()} | "
            f"{recovery.date() if recovery is not None else 'open'} | "
            f"{ep['trough_dd']:.1%} | "
            f"{c_m12:+.2f} | {c_m6:+.2f} | {c_trough:+.2f} | {c_p12:+.2f} |"
        )
    return "\n".join(rows)


def _format_corr_table(corrs: dict[int, float], series_label: str) -> str:
    header = (
        f"| Lag k (months) | Interpretation | corr({series_label}_t, return_{{t-k}}) |\n"
        "|---|---|---|"
    )
    rows = [header]
    for k in sorted(corrs.keys()):
        if k < 0:
            interp = f"{series_label} leads by {-k}m (returns realised after t)"
        elif k > 0:
            interp = f"{series_label} lags by {k}m (returns realised before t)"
        else:
            interp = "coincident"
        v = corrs[k]
        rows.append(f"| {k:+d} | {interp} | {v:+.3f} |")
    return "\n".join(rows)


def _peak_corr(corrs: dict[int, float]) -> tuple[int, float]:
    finite = {k: v for k, v in corrs.items() if not np.isnan(v)}
    if not finite:
        return (0, float("nan"))
    k_peak = max(finite, key=lambda k: abs(finite[k]))
    return (k_peak, finite[k_peak])


def _peak_interpretation(k_peak: int, peak: float, label: str) -> str:
    if np.isnan(peak):
        return f"Insufficient overlap to compute lead-lag correlations for {label}."
    if k_peak < 0:
        regime = (
            f"**{label}** at month t is most strongly related to equity returns "
            f"realised {-k_peak} months **after** t — i.e., **leading** future "
            f"returns"
        )
    elif k_peak > 0:
        regime = (
            f"**{label}** at month t is most strongly related to equity returns "
            f"realised {k_peak} months **before** t — i.e., **lagging** past "
            f"returns"
        )
    else:
        regime = f"**{label}** is **coincident** with equity returns"
    return (
        f"By peak absolute correlation, {regime} (peak at lag k={k_peak:+d}, "
        f"corr={peak:+.3f})."
    )


def _component_zscores(
    gini: pd.Series,
    epu: pd.Series,
    sentiment: pd.Series,
) -> dict[str, pd.Series]:
    """Build the same per-component monthly z-scores used inside
    ``internal_order_stress_index``.

    Returns a dict keyed by short component name → monthly z-score series.
    Each series is constructed identically to how the composite function
    builds it internally, so that averaging any subset gives a sub-composite
    that is consistent with the full three-way composite.
    """
    gini = gini.dropna().sort_index()
    epu = epu.dropna().sort_index()
    sentiment = sentiment.dropna().sort_index()

    gini_shifted = shift_by_publication_lag(gini, PUBLICATION_LAG_MONTHS)
    gini_monthly = gini_shifted.resample("ME").last().ffill()
    epu_monthly = epu.resample("ME").last()
    sentiment_monthly = sentiment.resample("ME").last()

    return {
        "gini": _rolling_zscore_strict(gini_monthly, ZSCORE_WINDOW),
        "epu": _rolling_zscore_strict(epu_monthly, ZSCORE_WINDOW),
        # Invert sentiment so higher = more stress (matches composite).
        "sentiment_inv": _rolling_zscore_strict(-sentiment_monthly, ZSCORE_WINDOW),
    }


def _pairwise_composite(z_components: dict[str, pd.Series], keys: tuple[str, str]) -> pd.Series:
    """Equal-weight mean of two z-score components, with the same dropna
    discipline as the full composite — defined only where both are observable.
    """
    df = pd.concat(
        [z_components[k].rename(k) for k in keys],
        axis=1,
        sort=False,
    ).dropna()
    s = df.mean(axis=1)
    s.name = "+".join(keys)
    return s


# Display labels for the report.
SERIES_LABELS = {
    "gini": "Gini (z, pub-lag-shifted)",
    "epu": "EPU (z)",
    "sentiment_inv": "Sentiment inverted (z)",
    "gini+epu": "Gini + EPU (equal-weight z)",
    "gini+sentiment_inv": "Gini + sentiment_inv (equal-weight z)",
    "epu+sentiment_inv": "EPU + sentiment_inv (equal-weight z)",
}


def _build_all_series(z_components: dict[str, pd.Series]) -> dict[str, pd.Series]:
    """Return the 3 single + 3 pairwise series, keyed by short id."""
    out: dict[str, pd.Series] = {}
    for k, s in z_components.items():
        out[k] = s.dropna()
    for a, b in combinations(("gini", "epu", "sentiment_inv"), 2):
        key = f"{a}+{b}"
        out[key] = _pairwise_composite(z_components, (a, b))
    return out


def _per_series_section(
    short_id: str,
    series: pd.Series,
    returns: pd.Series,
    episodes: list[dict],
    overlap_start: pd.Timestamp,
    overlap_end: pd.Timestamp,
) -> tuple[str, dict[int, float], int, float]:
    label = SERIES_LABELS[short_id]
    s = series.loc[overlap_start:overlap_end].dropna()
    first = s.index.min().date() if not s.empty else "n/a"
    last = s.index.max().date() if not s.empty else "n/a"
    corrs = _lead_lag_correlations(s, returns, LEAD_LAG_MONTHS)
    k_peak, peak = _peak_corr(corrs)
    section = (
        f"## {label}\n\n"
        f"Period: **{first} → {last}** ({len(s)} monthly observations).\n\n"
        "### Lead-lag correlation profile\n\n"
        + _format_corr_table(corrs, short_id) + "\n\n"
        + _peak_interpretation(k_peak, peak, label) + "\n\n"
        "### Drawdown episodes (>15% S&P 500 declines)\n\n"
        + _format_episode_table(episodes, s, short_id) + "\n"
    )
    return section, corrs, k_peak, peak


def _summary_table(
    rows: list[tuple[str, dict[int, float], int, float]],
) -> str:
    header = (
        "| Series | k at peak abs(corr) | Peak corr | corr k=−12 (lead 12m) | "
        "corr k=0 (coincident) | corr k=+12 (lag 12m) |\n"
        "|---|---|---|---|---|---|"
    )
    out = [header]
    for short_id, corrs, k_peak, peak in rows:
        label = SERIES_LABELS[short_id]
        c_m12 = corrs.get(-12, float("nan"))
        c_0 = corrs.get(0, float("nan"))
        c_p12 = corrs.get(12, float("nan"))
        out.append(
            f"| {label} | {k_peak:+d} | {peak:+.3f} | "
            f"{c_m12:+.3f} | {c_0:+.3f} | {c_p12:+.3f} |"
        )
    return "\n".join(out)


def _interpretation(
    rows: list[tuple[str, dict[int, float], int, float]],
) -> str:
    """Compose an interpretation grounded in the actual numbers."""
    by_id = {r[0]: r for r in rows}

    def line(short_id: str) -> str:
        _, _, k_peak, peak = by_id[short_id]
        label = SERIES_LABELS[short_id]
        if np.isnan(peak):
            return f"- {label}: insufficient data."
        if k_peak < 0:
            character = f"leads by {-k_peak}m"
        elif k_peak > 0:
            character = f"lags by {k_peak}m"
        else:
            character = "coincident"
        return f"- {label}: peak at k={k_peak:+d} (corr={peak:+.3f}) — {character}."

    summary_lines = "\n".join(line(s) for s in SERIES_LABELS)

    # Categorize each series.
    leading = []
    coincident = []
    lagging = []
    for short_id, _, k_peak, peak in rows:
        if np.isnan(peak):
            continue
        if k_peak < 0:
            leading.append((short_id, k_peak, peak))
        elif k_peak > 0:
            lagging.append((short_id, k_peak, peak))
        else:
            coincident.append((short_id, k_peak, peak))

    # Derive headline framing from the issue's three expected outcomes.
    has_gini_lead = any(s == "gini" and k < 0 for s, k, _ in leading)
    fast_components_coincident_or_lag = all(
        by_id[s][2] >= 0 for s in ("epu", "sentiment_inv") if not np.isnan(by_id[s][3])
    )

    if has_gini_lead and fast_components_coincident_or_lag:
        outcome = (
            "**Most-fitting outcome: \"slow leads, fast coincides/lags\".** "
            "Gini's peak correlation falls at a negative k (composite leads "
            "future returns), while the fast components (EPU, inverted "
            "sentiment) peak at k≥0. This is consistent with the "
            "issue's third expected outcome — distinct signal classes for "
            "different horizons. The full three-way composite's lagging "
            "character (issue #48) is then attributable to averaging Gini "
            "into the fast signals' coincident/lagging behavior."
        )
    elif has_gini_lead:
        outcome = (
            "**Most-fitting outcome: \"Gini leads\" (issue's first expected "
            "outcome).** Gini's peak correlation is at negative k. Worth "
            "examining whether dropping or down-weighting the fast components "
            "would recover the leading signal in the composite."
        )
    elif not leading:
        outcome = (
            "**Most-fitting outcome: \"nothing leads\" (issue's second "
            "expected outcome).** No single component or pairwise composite "
            "shows peak correlation at negative k under this methodology. "
            "The cyclical-scale individual-signal approach, as constructed, "
            "does not produce a leading indicator on the US 1975-present "
            "sample."
        )
    else:
        # Some series leads but it's not Gini, or the picture is mixed.
        leaders_str = ", ".join(
            f"{SERIES_LABELS[s]} (k={k:+d}, corr={p:+.3f})"
            for s, k, p in leading
        )
        outcome = (
            "**Most-fitting outcome: mixed / ambiguous.** The clean "
            "categorical outcomes from the issue don't fit cleanly. "
            f"Leading series: {leaders_str}. "
            "Read the per-series sections above before drawing conclusions; "
            "honest characterisation here matters more than a tidy story."
        )

    caveat = (
        "**Scale-principle caveat.** All numbers above are at the **cyclical** "
        "scale — US 1975-present equity drawdowns, ~50 years, a small number "
        "of independent recession/drawdown episodes. Per `specs/theses/README.md` "
        "(scale principle) and `specs/theses/civilizational-leads-financial.md`, "
        "a test at one scale is silent on another. A null cyclical lead does "
        "**not** falsify the transition-scale claim that civilizational stress "
        "indicators lead structural shifts (printing-press / empire-decline "
        "class changes). The transition-scale hypothesis requires cross-national "
        "historical data to test honestly (see `backtest-sample-scope.md`). Any "
        "claim that the civilizational-leads-financial thesis is falsified by "
        "this work would be a scale-mixing error."
    )

    return (
        "Per-series peak summary:\n\n"
        + summary_lines + "\n\n"
        + outcome + "\n\n"
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

    z_components = _component_zscores(gini, epu, sentiment)
    all_series = _build_all_series(z_components)

    spx = _spx_monthly(yahoo)
    drawdown = _compute_drawdown(spx)
    monthly_returns = spx.pct_change()

    # Use the union of all series' coverage to set the overlap window.
    earliest = min(s.dropna().index.min() for s in all_series.values())
    latest = max(s.dropna().index.max() for s in all_series.values())
    overlap_start = max(earliest, spx.index.min())
    overlap_end = min(latest, spx.index.max())

    returns_aligned = monthly_returns.loc[overlap_start:overlap_end]
    drawdown_aligned = drawdown.loc[overlap_start:overlap_end]
    episodes = _identify_drawdown_episodes(drawdown_aligned, DRAWDOWN_THRESHOLD)

    # Per-series sections, in display order.
    display_order = (
        "gini",
        "epu",
        "sentiment_inv",
        "gini+epu",
        "gini+sentiment_inv",
        "epu+sentiment_inv",
    )
    section_blocks: list[str] = []
    summary_rows: list[tuple[str, dict[int, float], int, float]] = []
    for short_id in display_order:
        section, corrs, k_peak, peak = _per_series_section(
            short_id,
            all_series[short_id],
            returns_aligned,
            episodes,
            overlap_start,
            overlap_end,
        )
        section_blocks.append(section)
        summary_rows.append((short_id, corrs, k_peak, peak))

    do_not_edit_header = (
        "<!-- Generated by scripts/civilizational_component_decomposition.py. "
        "Do not edit by hand; regenerate via the script. -->\n\n"
    )

    orientation = (
        "**Scale: cyclical (US 1975-present equity drawdowns).** Per "
        "`specs/theses/README.md` (scale principle), this analysis is silent "
        "on transition-scale claims. A null leading-indicator finding at the "
        "cyclical scale does NOT falsify civilizational-leads-financial at "
        "the transition scale (printing-press / empire-decline class changes). "
        "See the Interpretation section for the full caveat.\n\n"
        f"All series share the same construction discipline as "
        f"`internal_order_stress_index`: rolling {ZSCORE_WINDOW}m z-scores, "
        f"Gini publication-shifted by {PUBLICATION_LAG_MONTHS} months, "
        "sentiment inverted so higher=more stress, pairwise composites are "
        "equal-weight means defined only where both inputs are observable "
        "(walk-forward).\n"
    )

    report = (
        do_not_edit_header
        + "# Civilizational component decomposition (issue #49)\n\n"
        + orientation + "\n"
        + "S&P 500 drawdown threshold for episodes: "
        f"**{DRAWDOWN_THRESHOLD:.0%}**.\n\n"
        + "\n".join(section_blocks) + "\n"
        + "## Summary comparison\n\n"
        + _summary_table(summary_rows) + "\n\n"
        + "## Interpretation\n\n"
        + _interpretation(summary_rows) + "\n\n"
        + "## Method\n\n"
        "- **Component z-scores**: built via the same helpers used inside\n"
        f"  `src.indicators.internal_order_stress_index` "
        f"(`shift_by_publication_lag`, `_rolling_zscore_strict`) with\n"
        f"  `publication_lag_months={PUBLICATION_LAG_MONTHS}`, "
        f"`zscore_window={ZSCORE_WINDOW}` (10y monthly).\n"
        "- **Inputs**: GINIALLRF (annual, shifted forward 9 months), "
        "USEPUINDXM (monthly), UMCSENT (monthly, inverted).\n"
        "- **Pairwise composites**: equal-weight mean of each pair of\n"
        "  z-score components, requiring both to be observable at month t.\n"
        "- **Drawdown**: `price / running_peak − 1` on month-end S&P 500.\n"
        "- **Episodes**: contiguous below-peak runs whose minimum DD ≤ "
        f"{DRAWDOWN_THRESHOLD:.0%}. Episode set is identical across all "
        "series (driven by SPX); only the per-series readings at "
        "t−12 / t−6 / trough / t+12 differ.\n"
        "- **Lead-lag correlation**: `corr(series_t, return_{t-k})`.\n"
        "  Negative k means the series leads (correlates with future "
        "returns); positive k means it lags (correlates with past returns).\n"
    )

    out_path = ROOT / "docs" / "research" / "civilizational_component_decomposition.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report)
    print(f"Wrote {out_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

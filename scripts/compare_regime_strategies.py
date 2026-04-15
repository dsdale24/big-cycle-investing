"""Compare AllWeather, BigCycle binary, BigCycle scored, and BigCycle
non-sovereign-heavy base variants over the cached backtest period.

Produces a side-by-side metrics table on stdout and writes a markdown
report at ``docs/research/regime_scoring_comparison.md``. This is a
reporting script — always exits 0, never asserts any approach must win.

See issues #2 and #50.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.backtester import (
    AllWeatherStrategy,
    BacktestResult,
    BigCycleStrategy,
    build_asset_returns,
    compute_metrics,
    run_backtest,
)
from src.data_fetcher import load_all_fred, load_all_yahoo


START = "1980-01-01"
END = "2024-12-31"


def _run(label: str, strategy, asset_returns, indicator_data) -> dict:
    result = run_backtest(
        strategy=strategy,
        asset_returns=asset_returns,
        indicator_data=indicator_data,
        start=START,
    )
    metrics = compute_metrics(result)
    metrics["label"] = label
    metrics["result"] = result
    return metrics


def _format_row(m: dict) -> str:
    return (
        f"| {m['label']} | {m['cagr']:.2%} | {m['volatility']:.2%} | {m['sharpe']:.2f} "
        f"| {m['max_drawdown']:.1%} | {m['calmar']:.2f} | {m['average_turnover']:.3f} |"
    )


def _decade_slice(result: BacktestResult, decade_start: int) -> dict | None:
    """Compute CAGR and max drawdown for a BacktestResult within a calendar decade."""
    start_ts = pd.Timestamp(f"{decade_start}-01-01")
    end_ts = pd.Timestamp(f"{decade_start + 9}-12-31")
    val = result.portfolio_value.loc[start_ts:end_ts]
    if val.empty or len(val) < 2:
        return None

    years = (val.index[-1] - val.index[0]).days / 365.25
    if years <= 0:
        return None
    total_return = val.iloc[-1] / val.iloc[0] - 1
    cagr = (1 + total_return) ** (1 / years) - 1 if years > 0 else np.nan

    peak = val.cummax()
    drawdown = (val - peak) / peak
    max_dd = drawdown.min()
    return {"cagr": float(cagr), "max_dd": float(max_dd), "years": float(years)}


def _build_decade_table(runs: list[dict]) -> str:
    decades = [1980, 1990, 2000, 2010, 2020]
    header_cells = ["Decade"]
    for m in runs:
        header_cells.append(f"{m['label']} CAGR")
        header_cells.append(f"{m['label']} Max DD")
    header = "| " + " | ".join(header_cells) + " |"
    sep = "|" + "|".join(["---"] * len(header_cells)) + "|"

    rows = []
    for d in decades:
        cells = [f"{d}s"]
        any_data = False
        for m in runs:
            slice_m = _decade_slice(m["result"], d)
            if slice_m is None:
                cells.append("-")
                cells.append("-")
            else:
                cells.append(f"{slice_m['cagr']:.2%}")
                cells.append(f"{slice_m['max_dd']:.1%}")
                any_data = True
        if any_data:
            rows.append("| " + " | ".join(cells) + " |")

    return "\n".join([header, sep, *rows])


def main() -> int:
    fred = load_all_fred()
    yahoo = load_all_yahoo()
    data = {**fred, **yahoo}

    asset_returns, _ = build_asset_returns(data, start=START, return_sources=True)
    asset_returns = asset_returns.loc[:END]

    indicator_data = {**fred}

    runs = [
        _run("AllWeather", AllWeatherStrategy(), asset_returns, indicator_data),
        _run(
            "BigCycle binary",
            BigCycleStrategy(mode="binary"),
            asset_returns,
            indicator_data,
        ),
        _run(
            "BigCycle scored",
            BigCycleStrategy(mode="scored"),
            asset_returns,
            indicator_data,
        ),
        _run(
            "BigCycle non-sovereign",
            BigCycleStrategy(mode="scored", base_profile="non_sovereign_heavy"),
            asset_returns,
            indicator_data,
        ),
    ]

    header = (
        "| Strategy | CAGR | Vol | Sharpe | Max DD | Calmar | Avg Turnover |\n"
        "|---|---|---|---|---|---|---|"
    )
    table_rows = [_format_row(m) for m in runs]
    table = "\n".join([header, *table_rows])

    period = f"{runs[0]['start'].date()} -> {runs[0]['end'].date()} ({runs[0]['years']:.1f}y)"

    decade_table = _build_decade_table(runs)

    print(f"\nPeriod: {period}\n")
    print(table)
    print()
    print("Per-decade CAGR / Max DD:")
    print(decade_table)
    print()

    aw, binary, scored, nonsov = runs

    # Comparison framed around bond-allocation thesis (issue #50):
    # does the non-sovereign variant close the drawdown gap to AllWeather?
    dd_gap_scored = scored["max_drawdown"] - aw["max_drawdown"]
    dd_gap_nonsov = nonsov["max_drawdown"] - aw["max_drawdown"]
    dd_improvement = nonsov["max_drawdown"] - scored["max_drawdown"]

    interpretation_bits = []
    interpretation_bits.append(
        f"Over {period}, the BigCycle variants posted Sharpes of "
        f"{binary['sharpe']:.2f} (binary), {scored['sharpe']:.2f} (scored), "
        f"and {nonsov['sharpe']:.2f} (non-sovereign-heavy base). "
        f"AllWeather came in at {aw['sharpe']:.2f}."
    )

    interpretation_bits.append(
        f"Max drawdowns: {binary['max_drawdown']:.1%} (binary), "
        f"{scored['max_drawdown']:.1%} (scored), "
        f"{nonsov['max_drawdown']:.1%} (non-sovereign), "
        f"{aw['max_drawdown']:.1%} (AllWeather). "
        f"The non-sovereign drawdown gap to AllWeather is {dd_gap_nonsov:+.1%} "
        f"(scored gap was {dd_gap_scored:+.1%}). "
        f"Non-sovereign vs. scored on max DD: {dd_improvement:+.1%} "
        f"(positive = shallower; negative = deeper)."
    )

    # Scope caveat — this is a cyclical/secular-scale test only.
    caveat = (
        "**Scale caveat:** 1980-2024 is cyclical/secular scale only. "
        "This backtest is silent on transition-scale claims per "
        "`specs/theses/changing-world-order/backtest-sample-scope.md` — the US-ascendant, "
        "reserve-currency-intact period doesn't sample empire-decline or "
        "monetary-regime-transition dynamics. **AllWeather is not a neutral "
        "benchmark** per `specs/theses/changing-world-order/bond-allocation.md`: its 40% long-bond "
        "core is itself a thesis, and the 1980-2024 disinflation tailwind "
        "favored bond-heavy allocations broadly. 'Beating AllWeather' is not "
        "the success criterion here; the question is whether reducing "
        "sovereign-liability exposure in the base changes cyclical behavior "
        "in thesis-consistent ways (specifically: inflationary decades)."
    )

    do_not_edit_header = (
        "<!-- Generated by scripts/compare_regime_strategies.py. "
        "Do not edit by hand; regenerate via the script. -->\n\n"
    )

    report = (
        do_not_edit_header
        + "# Regime scoring comparison (issues #2, #50)\n\n"
        f"Backtest period: **{period}**. Rebalance: quarterly. Costs: default schedule.\n\n"
        "## Results\n\n"
        f"{table}\n\n"
        "## Per-decade breakdown\n\n"
        "CAGR and max drawdown within each calendar decade (portfolio value reset\n"
        "at decade start for CAGR; drawdown computed on the decade slice). Useful\n"
        "for separating inflationary episodes (partial 1970s tail, 2020s) from\n"
        "disinflation episodes (1980s-2010s).\n\n"
        f"{decade_table}\n\n"
        "## Interpretation\n\n"
        + " ".join(interpretation_bits)
        + "\n\n"
        + caveat
        + "\n\n"
        "The honest read: this test isolates whether base-weight choice (not\n"
        "regime classifier sophistication) is the lever that drives the drawdown\n"
        "gap between BigCycle and AllWeather. Pull the sovereign-liability share\n"
        "from 45% to 25% and see which metrics move. A shallower drawdown in the\n"
        "2020s decade row (the only clean inflationary episode in the sample) is\n"
        "the most thesis-aligned outcome; a shallower *total-period* drawdown\n"
        "would be stronger cyclical-scale evidence; unchanged or worse metrics\n"
        "would push the thesis back toward 'directionally right but insufficient'\n"
        "or falsification at cyclical scale.\n\n"
        "## Method\n\n"
        "- `AllWeather`: Bridgewater-style fixed mix (30/40/15/7.5/7.5).\n"
        "- `BigCycle binary`: original discrete regime classifier — hard thresholds\n"
        "  on yield curve, inflation, and real rate pick one of four regimes and\n"
        "  apply the full corresponding nudge from `REGIME_NUDGES`.\n"
        "- `BigCycle scored`: consumes `src.indicators.regime_classifier()` to\n"
        "  produce a continuous score in `[0, 1]` per regime, then blends the\n"
        "  per-regime nudges weighted by those scores.\n"
        "- `BigCycle non-sovereign`: identical regime-scored logic, but with the\n"
        "  non-sovereign-heavy base profile: 30% equities / 5% long bonds / 5%\n"
        "  short bonds / 25% gold / 20% commodities / 15% cash (sovereign-\n"
        "  liability share drops from 45% to 25%). See issue #50 and\n"
        "  `specs/theses/changing-world-order/bond-allocation.md`.\n"
    )

    out_path = ROOT / "docs" / "research" / "regime_scoring_comparison.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report)
    print(f"Wrote {out_path.relative_to(ROOT)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Tests for the score-blended BigCycleStrategy (issue #2).

Covers the scored rewire: continuous regime scores drive allocation deltas
rather than all-or-nothing nudges. Synthetic in-memory fixtures only — no
FRED cache required.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.backtester import (
    REGIME_NUDGES,
    BigCycleStrategy,
    build_asset_returns,
    run_backtest,
)
from src.indicators import regime_classifier


# ---------------------------------------------------------------------------
# Synthetic fixtures
# ---------------------------------------------------------------------------

def _monthly_series(start: str, periods: int, values) -> pd.Series:
    idx = pd.date_range(start=start, periods=periods, freq="MS")
    if np.isscalar(values):
        values = np.full(periods, float(values))
    return pd.Series(values, index=idx, dtype=float)


def _quarterly_series(start: str, periods: int, values) -> pd.Series:
    idx = pd.date_range(start=start, periods=periods, freq="QS")
    if np.isscalar(values):
        values = np.full(periods, float(values))
    return pd.Series(values, index=idx, dtype=float)


def _make_synthetic_macro_data(
    n_months: int = 240,
    cpi_growth: float = 0.002,
    ff_pct: float = 4.0,
    yc_pct: float = 1.0,
    debt_level: float = 60.0,
) -> dict[str, pd.Series]:
    """Build minimal macro inputs covering T10Y2Y, CPIAUCSL, FEDFUNDS, GFDEGDQ188S."""
    start = "1980-01-01"
    cpi_vals = 100.0 * (1.0 + cpi_growth) ** np.arange(n_months)
    cpi = _monthly_series(start, n_months, cpi_vals)
    fedfunds = _monthly_series(start, n_months, ff_pct)

    daily_idx = pd.date_range(start=start, periods=n_months * 21, freq="B")
    t10y2y = pd.Series(yc_pct, index=daily_idx, dtype=float)

    n_quarters = max(5, n_months // 3 + 1)
    debt = _quarterly_series(start, n_quarters, debt_level)

    return {
        "T10Y2Y": t10y2y,
        "CPIAUCSL": cpi,
        "FEDFUNDS": fedfunds,
        "GFDEGDQ188S": debt,
    }


# ---------------------------------------------------------------------------
# Basic invariants
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_scored_weights_sum_to_one():
    data = _make_synthetic_macro_data()
    strat = BigCycleStrategy(mode="scored")
    date = pd.Timestamp("1995-01-01")
    snapshot = strat.allocate(date, data, pre_rebalance_weights={})
    total = sum(snapshot.weights.values())
    assert abs(total - 1.0) < 1e-9


@pytest.mark.unit
def test_scored_weights_never_negative():
    data = _make_synthetic_macro_data(yc_pct=-0.5, ff_pct=2.0, cpi_growth=0.005)
    strat = BigCycleStrategy(mode="scored")
    date = pd.Timestamp("1995-01-01")
    snapshot = strat.allocate(date, data, pre_rebalance_weights={})
    for asset, w in snapshot.weights.items():
        assert w >= 0.0, f"weight for {asset} is negative: {w}"


@pytest.mark.unit
def test_regime_nudges_keys_match_classifier_regimes():
    """REGIME_NUDGES must cover exactly the regimes that regime_classifier emits."""
    idx = pd.date_range("1990-01-01", periods=60, freq="ME")
    yc = pd.Series(1.0, index=idx)
    infl = pd.Series(2.0, index=idx)
    debt = pd.Series(1.0, index=idx)
    real_r = pd.Series(2.0, index=idx)

    regimes = regime_classifier(yc, infl, debt, real_r)
    assert set(REGIME_NUDGES.keys()) == set(regimes.columns)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_scored_returns_base_weights_when_no_data():
    """When no macro data is available, scored mode falls back to base weights."""
    strat = BigCycleStrategy(mode="scored")
    date = pd.Timestamp("1995-01-01")
    empty_data: dict[str, pd.Series] = {}
    snapshot = strat.allocate(date, empty_data, pre_rebalance_weights={})

    expected = strat._base_weights()
    total = sum(expected.values())
    expected_norm = {k: v / total for k, v in expected.items()}

    for asset, w in expected_norm.items():
        assert abs(snapshot.weights[asset] - w) < 1e-9


@pytest.mark.unit
def test_scored_returns_base_weights_when_history_too_short():
    """If CPI has < 13 months of data, YoY inflation can't be computed."""
    data = {
        "T10Y2Y": pd.Series([1.0], index=[pd.Timestamp("1990-01-01")]),
        "CPIAUCSL": pd.Series([100.0], index=[pd.Timestamp("1990-01-01")]),
        "FEDFUNDS": pd.Series([4.0], index=[pd.Timestamp("1990-01-01")]),
        "GFDEGDQ188S": pd.Series([60.0], index=[pd.Timestamp("1990-01-01")]),
    }
    strat = BigCycleStrategy(mode="scored")
    snapshot = strat.allocate(pd.Timestamp("1990-02-01"), data, pre_rebalance_weights={})

    expected = strat._base_weights()
    total = sum(expected.values())
    expected_norm = {k: v / total for k, v in expected.items()}
    for asset, w in expected_norm.items():
        assert abs(snapshot.weights[asset] - w) < 1e-9


# ---------------------------------------------------------------------------
# Cross-consistency: single regime at score=1 matches binary nudge
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.parametrize("regime", ["overheating", "contraction", "reflation", "expansion"])
def test_scored_single_regime_full_score_matches_binary(regime, monkeypatch):
    """If only one regime scores 1.0 (others 0), the scored path must produce
    the same allocation as the binary path would for that same regime."""
    strat = BigCycleStrategy(mode="scored")

    forced_scores = {r: 0.0 for r in REGIME_NUDGES.keys()}
    forced_scores[regime] = 1.0

    monkeypatch.setattr(
        strat,
        "_compute_regime_scores",
        lambda date, available_data: (forced_scores, {}),
    )

    date = pd.Timestamp("1995-01-01")
    scored_snapshot = strat.allocate(date, {}, pre_rebalance_weights={})

    binary_strat = BigCycleStrategy(mode="binary")
    base = binary_strat._base_weights()
    for asset, delta in REGIME_NUDGES.get(regime, {}).items():
        base[asset] = base.get(asset, 0.0) + delta
    expected = BigCycleStrategy._clamp_and_normalize(base)

    for asset in expected:
        assert abs(scored_snapshot.weights[asset] - expected[asset]) < 1e-9, (
            f"{regime}: {asset} mismatch scored={scored_snapshot.weights[asset]:.6f} "
            f"binary-equiv={expected[asset]:.6f}"
        )


# ---------------------------------------------------------------------------
# End-to-end: a backtest with scored mode runs cleanly
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_scored_backtest_runs_over_multi_decade_span():
    """Full backtest with scored mode over a synthetic 1980-2020 span completes."""
    n_months = 40 * 12
    macro = _make_synthetic_macro_data(n_months=n_months)

    daily_idx = pd.bdate_range("1980-01-01", "2020-12-31")
    rng = np.random.default_rng(42)

    def _rets(scale: float) -> pd.Series:
        return pd.Series(rng.normal(0.0003, scale, size=len(daily_idx)), index=daily_idx)

    asset_returns = pd.DataFrame({
        "equities": _rets(0.012),
        "long_bonds": _rets(0.006),
        "short_bonds": _rets(0.002),
        "gold": _rets(0.010),
        "commodities": _rets(0.014),
        "cash": pd.Series(0.00015, index=daily_idx),
    })

    strat = BigCycleStrategy(mode="scored")
    result = run_backtest(
        strategy=strat,
        asset_returns=asset_returns,
        indicator_data=macro,
        start="1980-01-01",
        rebalance_freq="QE",
        cost_rate=0.0,
    )
    assert len(result.snapshots) > 100
    assert not result.portfolio_returns.isna().any()
    assert result.portfolio_value.iloc[-1] > 0.0

"""Tests for the non-sovereign-heavy base profile on BigCycleStrategy (issue #50).

The base_profile parameter lets a caller swap BigCycleStrategy's base weights
without touching the regime-scored logic. These tests cover the new profile
only — existing "balanced" behavior is exercised elsewhere.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.backtester import BigCycleStrategy, run_backtest


_EXPECTED_NON_SOVEREIGN = {
    "equities": 0.30,
    "long_bonds": 0.05,
    "short_bonds": 0.05,
    "gold": 0.25,
    "commodities": 0.20,
    "cash": 0.15,
}


@pytest.mark.unit
def test_non_sovereign_base_weights_sum_to_one():
    strat = BigCycleStrategy(base_profile="non_sovereign_heavy")
    weights = strat._base_weights()
    total = sum(weights.values())
    assert abs(total - 1.0) < 1e-9


@pytest.mark.unit
def test_non_sovereign_base_weights_match_profile():
    strat = BigCycleStrategy(base_profile="non_sovereign_heavy")
    weights = strat._base_weights()
    for asset, expected in _EXPECTED_NON_SOVEREIGN.items():
        assert abs(weights[asset] - expected) < 1e-9, (
            f"{asset}: expected {expected}, got {weights[asset]}"
        )


@pytest.mark.unit
def test_non_sovereign_allocation_with_no_regime_data_matches_base():
    """Neutral regime = empty macro data → allocate() returns the base profile."""
    strat = BigCycleStrategy(base_profile="non_sovereign_heavy", mode="scored")
    snapshot = strat.allocate(
        pd.Timestamp("2000-01-01"), {}, pre_rebalance_weights={}
    )
    for asset, expected in _EXPECTED_NON_SOVEREIGN.items():
        assert abs(snapshot.weights[asset] - expected) < 1e-9


@pytest.mark.unit
def test_sovereign_liability_reduced():
    """Non-sovereign-heavy should cut (long + short bonds + cash) from 0.45 to 0.25."""
    balanced = BigCycleStrategy(base_profile="balanced")._base_weights()
    nonsov = BigCycleStrategy(base_profile="non_sovereign_heavy")._base_weights()

    balanced_sov = balanced["long_bonds"] + balanced["short_bonds"] + balanced["cash"]
    nonsov_sov = nonsov["long_bonds"] + nonsov["short_bonds"] + nonsov["cash"]

    assert abs(balanced_sov - 0.45) < 1e-9
    assert abs(nonsov_sov - 0.25) < 1e-9


@pytest.mark.unit
def test_default_profile_is_balanced():
    """Constructor with no base_profile kwarg must preserve historical defaults."""
    strat = BigCycleStrategy()
    assert strat.base_profile == "balanced"
    assert strat._base_weights()["long_bonds"] == 0.25


@pytest.mark.unit
def test_invalid_base_profile_raises():
    with pytest.raises(ValueError, match="base_profile must be one of"):
        BigCycleStrategy(base_profile="not-a-profile")


@pytest.mark.unit
def test_non_sovereign_backtest_smoke():
    """End-to-end: run the new variant through run_backtest and get a valid result."""
    daily_idx = pd.bdate_range("2000-01-01", "2005-12-31")
    rng = np.random.default_rng(7)

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

    strat = BigCycleStrategy(base_profile="non_sovereign_heavy", mode="scored")
    result = run_backtest(
        strategy=strat,
        asset_returns=asset_returns,
        indicator_data={},
        start="2000-01-01",
        rebalance_freq="QE",
        cost_rate=0.0,
    )
    assert len(result.snapshots) > 10
    assert not result.portfolio_returns.isna().any()
    assert result.portfolio_value.iloc[-1] > 0.0

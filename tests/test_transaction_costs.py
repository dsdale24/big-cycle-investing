"""Tests for the transaction-cost model in ``run_backtest``.

All tests use synthetic fixtures (no FRED cache, no network). Covers the test
cases listed in ``docs/specs/backtester.md`` under "Transaction costs → Test
cases".
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.backtester import (
    BacktestResult,
    PortfolioSnapshot,
    compute_metrics,
    default_cost_schedule,
    run_backtest,
)


# ---------------------------------------------------------------------------
# Fixtures and helpers
# ---------------------------------------------------------------------------


def _asset_returns(start: str = "2000-01-03", end: str = "2005-12-30",
                   seed: int = 42) -> pd.DataFrame:
    """Small synthetic daily-return frame covering the specced asset classes."""
    idx = pd.bdate_range(start=start, end=end)
    rng = np.random.default_rng(seed)
    columns = ["equities", "long_bonds", "short_bonds", "gold", "commodities", "cash"]
    data = {c: rng.normal(0.0003, 0.008, size=len(idx)) for c in columns}
    return pd.DataFrame(data, index=idx)


class FixedWeightsStrategy:
    """Strategy that returns the same target weights every rebalance."""

    def __init__(self, weights: dict[str, float], name: str = "fixed"):
        self.weights = dict(weights)
        self.name = name

    def allocate(self, date, available_data):
        return PortfolioSnapshot(
            date=date, weights=dict(self.weights), regime=self.name
        )


class BinarySwapStrategy:
    """Strategy that alternates between two weight profiles per rebalance."""

    def __init__(self, a: dict[str, float], b: dict[str, float]):
        self.a = dict(a)
        self.b = dict(b)
        self.flip = False

    def allocate(self, date, available_data):
        weights = self.b if self.flip else self.a
        self.flip = not self.flip
        return PortfolioSnapshot(
            date=date, weights=dict(weights), regime="swap"
        )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.spec
def test_static_strategy_has_zero_turnover_and_cost():
    """Spec: "A static strategy ... has turnover = 0 at every rebalance and
    total costs.sum() == 0".

    See docs/specs/backtester.md "Transaction costs → Test cases".
    """
    # Use flat returns (no drift) so the static profile stays on target
    # between rebalances — otherwise drift generates real turnover even for
    # a "static" target, which is correct behavior but not what this spec
    # case is probing.
    returns = _asset_returns() * 0.0
    strategy = FixedWeightsStrategy(
        {"equities": 0.6, "long_bonds": 0.4,
         "short_bonds": 0.0, "gold": 0.0, "commodities": 0.0, "cash": 0.0}
    )

    result = run_backtest(strategy, returns, indicator_data={}, start=str(returns.index[0].date()))

    # First rebalance moves from the equal-weight initialization to the
    # static target; skip that and verify all *subsequent* rebalances are
    # zero-turnover / zero-cost.
    assert (result.turnover.iloc[1:] == 0).all()
    assert result.costs.iloc[1:].sum() == 0


@pytest.mark.unit
@pytest.mark.spec
def test_sixty_forty_to_forty_sixty_turnover_is_point_two():
    """Spec: "A strategy that swaps a 60/40 portfolio to 40/60 has turnover = 0.2".

    See docs/specs/backtester.md "Transaction costs → Test cases".
    """
    returns = _asset_returns()
    sixty_forty = {"equities": 0.6, "long_bonds": 0.4,
                   "short_bonds": 0.0, "gold": 0.0, "commodities": 0.0, "cash": 0.0}
    forty_sixty = {"equities": 0.4, "long_bonds": 0.6,
                   "short_bonds": 0.0, "gold": 0.0, "commodities": 0.0, "cash": 0.0}

    # Use returns of zero so drift doesn't mask the swap turnover.
    returns_zero = returns * 0.0
    swapper = BinarySwapStrategy(sixty_forty, forty_sixty)
    result = run_backtest(swapper, returns_zero, indicator_data={},
                          start=str(returns_zero.index[0].date()))

    # First rebalance: equal-weight -> 60/40 (bigger turnover, ignore).
    # Second rebalance: 60/40 -> 40/60 -> turnover = 0.2.
    assert result.turnover.iloc[1] == pytest.approx(0.2, abs=1e-9)


@pytest.mark.unit
@pytest.mark.spec
def test_full_swap_turnover_is_one_and_cost_equals_rate():
    """Spec: "A strategy that fully swaps to a disjoint allocation has
    turnover = 1.0 and a single-rebalance cost equal to cost_rate(date)".

    See docs/specs/backtester.md "Transaction costs → Test cases".
    """
    returns = _asset_returns()
    all_equities = {"equities": 1.0, "long_bonds": 0.0,
                    "short_bonds": 0.0, "gold": 0.0, "commodities": 0.0, "cash": 0.0}
    all_bonds = {"equities": 0.0, "long_bonds": 1.0,
                 "short_bonds": 0.0, "gold": 0.0, "commodities": 0.0, "cash": 0.0}

    returns_zero = returns * 0.0
    swapper = BinarySwapStrategy(all_equities, all_bonds)
    rate = 0.0025
    result = run_backtest(swapper, returns_zero, indicator_data={}, cost_rate=rate,
                          start=str(returns_zero.index[0].date()))

    # Second rebalance: full swap from all-equities to all-bonds.
    assert result.turnover.iloc[1] == pytest.approx(1.0, abs=1e-9)
    assert result.costs.iloc[1] == pytest.approx(rate, abs=1e-12)


@pytest.mark.unit
@pytest.mark.spec
def test_zero_cost_rate_matches_precost_trajectory():
    """Spec: "cost_rate = 0.0 produces a BacktestResult whose costs series is
    all zeros and whose portfolio value trajectory matches the pre-cost
    baseline to floating-point tolerance".

    See docs/specs/backtester.md "Transaction costs → Test cases".
    """
    returns = _asset_returns()
    swapper_a = BinarySwapStrategy(
        {"equities": 1.0, "long_bonds": 0.0, "short_bonds": 0.0,
         "gold": 0.0, "commodities": 0.0, "cash": 0.0},
        {"equities": 0.0, "long_bonds": 1.0, "short_bonds": 0.0,
         "gold": 0.0, "commodities": 0.0, "cash": 0.0},
    )
    swapper_b = BinarySwapStrategy(
        {"equities": 1.0, "long_bonds": 0.0, "short_bonds": 0.0,
         "gold": 0.0, "commodities": 0.0, "cash": 0.0},
        {"equities": 0.0, "long_bonds": 1.0, "short_bonds": 0.0,
         "gold": 0.0, "commodities": 0.0, "cash": 0.0},
    )

    result_free = run_backtest(swapper_a, returns, indicator_data={},
                               cost_rate=0.0, start=str(returns.index[0].date()))
    result_defaultfree = run_backtest(
        swapper_b, returns, indicator_data={},
        cost_rate=lambda _d: 0.0, start=str(returns.index[0].date())
    )

    assert (result_free.costs == 0).all()
    pd.testing.assert_series_equal(
        result_free.portfolio_value, result_defaultfree.portfolio_value,
        check_exact=False, atol=1e-12,
    )


@pytest.mark.unit
@pytest.mark.spec
def test_default_cost_schedule_values():
    """Spec: "The default schedule returns 0.003 for 1985-06-15, 0.001 for
    2005-06-15, and 0.0005 for 2020-06-15".

    See docs/specs/backtester.md "Transaction costs → Test cases".
    """
    assert default_cost_schedule(pd.Timestamp("1985-06-15")) == pytest.approx(0.003)
    assert default_cost_schedule(pd.Timestamp("2005-06-15")) == pytest.approx(0.001)
    assert default_cost_schedule(pd.Timestamp("2020-06-15")) == pytest.approx(0.0005)


@pytest.mark.unit
@pytest.mark.spec
def test_nonzero_turnover_strategy_post_cost_cagr_lower():
    """Spec: "For strategies with non-zero turnover, the post-cost CAGR is
    strictly less than the hypothetical zero-cost CAGR".

    See docs/specs/backtester.md "Transaction costs → Test cases".
    """
    returns = _asset_returns(start="2000-01-03", end="2010-12-30")
    swap_args = (
        {"equities": 1.0, "long_bonds": 0.0, "short_bonds": 0.0,
         "gold": 0.0, "commodities": 0.0, "cash": 0.0},
        {"equities": 0.0, "long_bonds": 1.0, "short_bonds": 0.0,
         "gold": 0.0, "commodities": 0.0, "cash": 0.0},
    )

    free_result = run_backtest(
        BinarySwapStrategy(*swap_args), returns, indicator_data={},
        cost_rate=0.0, start=str(returns.index[0].date()),
    )
    costly_result = run_backtest(
        BinarySwapStrategy(*swap_args), returns, indicator_data={},
        cost_rate=0.005, start=str(returns.index[0].date()),
    )

    free_cagr = compute_metrics(free_result)["cagr"]
    costly_cagr = compute_metrics(costly_result)["cagr"]

    # Sanity: we actually incurred turnover.
    assert (costly_result.turnover > 0).any()
    assert costly_cagr < free_cagr


@pytest.mark.unit
def test_backtest_result_default_factories_allow_legacy_construction():
    """BacktestResult callers that don't pass turnover/costs must still work."""
    idx = pd.bdate_range("2000-01-03", periods=3)
    result = BacktestResult(
        snapshots=[],
        portfolio_returns=pd.Series(0.0, index=idx),
        portfolio_value=pd.Series(1.0, index=idx),
        asset_returns=pd.DataFrame(index=idx),
        weights_history=pd.DataFrame(),
        regime_history=pd.Series(dtype=str),
        config={},
    )
    assert isinstance(result.turnover, pd.Series) and result.turnover.empty
    assert isinstance(result.costs, pd.Series) and result.costs.empty

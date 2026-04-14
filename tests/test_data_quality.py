"""Tests for the data-quality surface on ``BacktestResult``.

Covers the test cases listed in ``specs/backtester.md`` under "Data quality".
Tests use synthetic fixtures so they do not require a FRED API key or network
access. The same synthetic construction shape as ``tests/test_bond_splicing.py``
is used so pre/post-2002 splice behavior can be exercised deterministically.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src import backtester as backtester_mod
from src.backtester import (
    APPROXIMATION_SOURCES,
    LONG_BONDS_ETF,
    SHORT_BONDS_ETF,
    BacktestResult,
    StaticStrategy,
    build_asset_returns,
    run_backtest,
)


# ---------------------------------------------------------------------------
# Synthetic fixture construction (mirrors tests/test_bond_splicing.py)
# ---------------------------------------------------------------------------

TLT_SPLICE = pd.Timestamp("2002-07-30")
SHY_SPLICE = pd.Timestamp("2002-07-30")


def _business_days(start: str, end: str) -> pd.DatetimeIndex:
    return pd.bdate_range(start=start, end=end)


def _make_price_df(
    index: pd.DatetimeIndex,
    start_price: float = 100.0,
    drift: float = 0.0002,
    seed: int = 0,
    include_close: bool = True,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rets = rng.normal(drift, 0.005, size=len(index))
    adj = start_price * np.cumprod(1.0 + rets)
    data = {"Adj Close": adj}
    if include_close:
        data["Close"] = adj * 0.9
    return pd.DataFrame(data, index=index)


def _make_yield_df(
    index: pd.DatetimeIndex,
    start_yield_pct: float = 7.5,
    drift: float = 0.0,
    vol: float = 0.02,
    seed: int = 0,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rets = rng.normal(drift, vol, size=len(index))
    levels = start_yield_pct * np.cumprod(1.0 + rets)
    levels = np.clip(levels, 0.5, 20.0)
    return pd.DataFrame({"Close": levels}, index=index)


@pytest.fixture
def trading_index() -> pd.DatetimeIndex:
    return _business_days("1975-01-01", "2015-12-31")


@pytest.fixture
def synthetic_data(trading_index: pd.DatetimeIndex) -> dict:
    """Minimal synthetic ``data`` dict spanning both pre- and post-splice periods."""
    tnx = _make_yield_df(trading_index, start_yield_pct=7.5, vol=0.015, seed=101)
    gs2_daily = _make_yield_df(
        trading_index, start_yield_pct=6.0, vol=0.02, seed=102
    )
    gs2_series = gs2_daily["Close"].rename("GS2_yield")

    etf_idx = _business_days("2002-07-30", "2015-12-31")
    tlt = _make_price_df(etf_idx, start_price=90.0, drift=0.0001, seed=201)
    shy = _make_price_df(etf_idx, start_price=80.0, drift=0.00005, seed=202)

    sp = _make_price_df(
        trading_index, start_price=70.0, drift=0.0003, seed=15, include_close=False
    )
    sp["Close"] = sp["Adj Close"]

    fed = pd.Series(
        5.0,
        index=pd.date_range("1975-01-01", "2015-12-01", freq="MS"),
        name="FEDFUNDS",
    )

    return {
        "^GSPC": sp,
        "^TNX": tnx,
        "GS2_yield": gs2_series,
        "FEDFUNDS": fed,
        LONG_BONDS_ETF: tlt,
        SHORT_BONDS_ETF: shy,
    }


def _run(
    synthetic_data: dict,
    strategy,
    start: str,
    end: str | None = None,
) -> BacktestResult:
    """Run a backtest with sources wired in; optionally trim asset_returns to ``end``."""
    returns, sources = build_asset_returns(
        synthetic_data, start="1975-01-01", return_sources=True
    )
    if end is not None:
        end_dt = pd.Timestamp(end)
        returns = returns.loc[:end_dt]
        sources = sources.loc[:end_dt]
    return run_backtest(
        strategy=strategy,
        asset_returns=returns,
        indicator_data={},
        start=start,
        asset_sources=sources,
        cost_rate=0.0,
    )


# ---------------------------------------------------------------------------
# Spec test cases
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.spec
def test_approximation_exposure_post_splice_is_zero(synthetic_data):
    """specs/backtester.md "Data quality → Test cases":
    a backtest from 2010-01-01 with 50/50 long_bonds/equities has exposure 0."""
    strat = StaticStrategy({"long_bonds": 0.5, "equities": 0.5})
    result = _run(synthetic_data, strat, start="2010-01-01")

    exposure = result.approximation_exposure()
    assert len(exposure) > 0
    np.testing.assert_allclose(exposure.values, 0.0, atol=1e-12)


@pytest.mark.unit
@pytest.mark.spec
def test_approximation_exposure_pre_splice_full(synthetic_data):
    """specs/backtester.md "Data quality → Test cases":
    1980 → 1985 with 50/50 long_bonds/equities has exposure 0.5 everywhere
    (long bonds come from the ^TNX approximation pre-splice)."""
    strat = StaticStrategy({"long_bonds": 0.5, "equities": 0.5})
    result = _run(synthetic_data, strat, start="1980-01-01", end="1985-12-31")

    exposure = result.approximation_exposure()
    assert len(exposure) > 0
    np.testing.assert_allclose(exposure.values, 0.5, atol=1e-12)


@pytest.mark.unit
@pytest.mark.spec
def test_approximation_exposure_transitions_at_splice(synthetic_data):
    """specs/backtester.md "Data quality → Test cases":
    2000 → 2005 with 100% long_bonds transitions from 1.0 to 0.0 at 2002-07-30."""
    strat = StaticStrategy({"long_bonds": 1.0})
    result = _run(synthetic_data, strat, start="2000-01-01", end="2005-12-31")

    exposure = result.approximation_exposure()
    pre = exposure[exposure.index < TLT_SPLICE]
    post = exposure[exposure.index >= TLT_SPLICE]

    assert len(pre) > 0 and len(post) > 0
    np.testing.assert_allclose(pre.values, 1.0, atol=1e-12)
    np.testing.assert_allclose(post.values, 0.0, atol=1e-12)


@pytest.mark.unit
@pytest.mark.spec
def test_approximation_exposure_zero_for_no_bond_strategy(synthetic_data):
    """specs/backtester.md "Data quality → Invariants":
    zero bond weight at every rebalance => exposure is all zeros regardless of period."""
    strat = StaticStrategy({"equities": 1.0})
    result = _run(synthetic_data, strat, start="1985-01-01", end="1995-12-31")

    exposure = result.approximation_exposure()
    assert len(exposure) > 0
    np.testing.assert_allclose(exposure.values, 0.0, atol=1e-12)


@pytest.mark.unit
@pytest.mark.spec
def test_approximation_exposure_monotone_in_source_set(
    synthetic_data, monkeypatch
):
    """specs/backtester.md "Data quality → Test cases":
    adding a new source to APPROXIMATION_SOURCES produces an element-wise
    greater-or-equal exposure series on a fixed backtest."""
    strat = StaticStrategy({"long_bonds": 0.5, "equities": 0.5})
    baseline = _run(synthetic_data, strat, start="1990-01-01", end="1995-12-31")
    base_exposure = baseline.approximation_exposure()

    extended = APPROXIMATION_SOURCES | {"^GSPC"}
    monkeypatch.setattr(backtester_mod, "APPROXIMATION_SOURCES", extended)

    extended_exposure = baseline.approximation_exposure()

    assert (extended_exposure.values >= base_exposure.values - 1e-12).all()
    # With equities (^GSPC) added, and 50% equities weight, the extended
    # exposure should be strictly greater than baseline.
    assert (extended_exposure.values > base_exposure.values + 1e-6).all()


@pytest.mark.unit
@pytest.mark.spec
def test_asset_sources_invariants(synthetic_data):
    """specs/backtester.md "Data quality → Invariants":
    asset_sources.index == asset_returns.index, columns match, no NaN/empty
    cells on populated business days."""
    strat = StaticStrategy({"long_bonds": 0.5, "equities": 0.5})
    result = _run(synthetic_data, strat, start="1980-01-01", end="2005-12-31")

    pd.testing.assert_index_equal(
        result.asset_sources.index, result.asset_returns.index
    )
    assert list(result.asset_sources.columns) == list(result.asset_returns.columns)

    populated = result.asset_returns.notna()
    source_populated = result.asset_sources.notna() & (result.asset_sources != "")
    # Every cell populated in returns must have a non-empty source label.
    missing = populated & ~source_populated
    assert not missing.values.any(), (
        f"asset_sources has NaN/empty cells where asset_returns is populated: "
        f"{missing.sum().to_dict()}"
    )


@pytest.mark.unit
@pytest.mark.spec
def test_run_backtest_default_asset_sources_empty(synthetic_data):
    """specs/backtester.md "Data quality":
    when run_backtest is called without asset_sources, result.asset_sources is
    empty and approximation_exposure() returns zeros indexed by weights_history."""
    returns = build_asset_returns(synthetic_data, start="1975-01-01")
    strat = StaticStrategy({"long_bonds": 0.5, "equities": 0.5})
    result = run_backtest(
        strategy=strat,
        asset_returns=returns,
        indicator_data={},
        start="1980-01-01",
        cost_rate=0.0,
    )

    assert result.asset_sources.empty

    exposure = result.approximation_exposure()
    pd.testing.assert_index_equal(exposure.index, result.weights_history.index)
    np.testing.assert_allclose(exposure.values, 0.0, atol=1e-12)

"""Tests for pre-2000 proxy splicing in ``build_asset_returns``.

Covers the test cases listed in ``docs/specs/backtester.md`` under
"Proxy series splicing". Tests use small synthetic DataFrames so they do not
require a FRED API key or network access.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.backtester import (
    COMMODITIES_DAILY_PROXY_SERIES,
    COMMODITIES_DAILY_TO_FUTURES_SPLICE,
    COMMODITIES_MONTHLY_PROXY_SERIES,
    COMMODITIES_MONTHLY_TO_DAILY_SPLICE,
    GOLD_DEFAULT_SPLICE,
    GOLD_PROXY_SERIES,
    build_asset_returns,
    monthly_levels_to_daily_returns,
    splice_returns,
)


# ---------------------------------------------------------------------------
# Synthetic fixture construction
# ---------------------------------------------------------------------------

def _business_days(start: str, end: str) -> pd.DatetimeIndex:
    return pd.bdate_range(start=start, end=end)


def _make_price_df(index: pd.DatetimeIndex, start_price: float = 100.0,
                   drift: float = 0.0002, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rets = rng.normal(drift, 0.01, size=len(index))
    prices = start_price * np.cumprod(1.0 + rets)
    return pd.DataFrame({"Close": prices}, index=index)


def _make_monthly_levels(start: str, end: str, start_level: float = 100.0,
                         monthly_drift: float = 0.005, seed: int = 1) -> pd.Series:
    idx = pd.date_range(start=start, end=end, freq="MS")
    rng = np.random.default_rng(seed)
    rets = rng.normal(monthly_drift, 0.02, size=len(idx))
    levels = start_level * np.cumprod(1.0 + rets)
    return pd.Series(levels, index=idx, name="level")


def _make_daily_levels(index: pd.DatetimeIndex, start_level: float = 30.0,
                       drift: float = 0.0003, seed: int = 2) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rets = rng.normal(drift, 0.015, size=len(index))
    levels = start_level * np.cumprod(1.0 + rets)
    return pd.DataFrame({"Close": levels}, index=index)


@pytest.fixture
def trading_index() -> pd.DatetimeIndex:
    return _business_days("1975-01-01", "2005-12-31")


@pytest.fixture
def synthetic_data(trading_index: pd.DatetimeIndex) -> dict:
    """Minimal synthetic ``data`` dict covering all splicing segments."""
    wpu = _make_monthly_levels("1974-12-01", "2026-01-01", seed=10)
    ppiaco = _make_monthly_levels("1974-12-01", "2026-01-01", seed=11)

    wti_idx = _business_days("1986-01-02", "2026-01-01")
    wti = _make_daily_levels(wti_idx, seed=12)

    gc_idx = _business_days("2000-08-30", "2026-01-01")
    gc = _make_price_df(gc_idx, start_price=275.0, seed=13)

    cl_idx = _business_days("2000-08-23", "2026-01-01")
    cl = _make_price_df(cl_idx, start_price=32.0, seed=14)

    sp = _make_price_df(trading_index, start_price=70.0, drift=0.0003, seed=15)
    tnx = _make_price_df(trading_index, start_price=7.5, drift=0.0, seed=16)

    fed = pd.Series(
        5.0,
        index=pd.date_range("1975-01-01", "2026-01-01", freq="MS"),
        name="FEDFUNDS",
    )

    return {
        "^GSPC": sp,
        "^TNX": tnx,
        "FEDFUNDS": fed,
        GOLD_PROXY_SERIES: wpu,
        COMMODITIES_MONTHLY_PROXY_SERIES: ppiaco,
        COMMODITIES_DAILY_PROXY_SERIES: wti,
        "GC=F": gc,
        "CL=F": cl,
    }


# ---------------------------------------------------------------------------
# Monthly -> daily conversion invariant
# ---------------------------------------------------------------------------

def test_monthly_to_daily_compounding_identity():
    """Compounded daily returns equal the underlying monthly return."""
    idx = _business_days("1980-01-01", "1980-12-31")
    levels = pd.Series(
        [100.0, 101.0, 99.5, 102.3, 103.0, 104.1, 106.0, 105.5, 107.0,
         108.2, 109.0, 110.5, 111.0],
        index=pd.date_range("1979-12-01", periods=13, freq="MS"),
    )

    daily = monthly_levels_to_daily_returns(levels, idx)

    monthly_returns = levels.pct_change().dropna()
    for period, expected in monthly_returns.items():
        mask = (idx.year == period.year) & (idx.month == period.month)
        month_days = daily[mask].dropna()
        if len(month_days) == 0:
            continue
        compounded = (1.0 + month_days).prod() - 1.0
        assert compounded == pytest.approx(expected, abs=1e-9), (
            f"Month {period.date()} expected {expected}, got {compounded}"
        )


def test_monthly_to_daily_evenly_distributed():
    """Within a month, every trading day receives the same daily return."""
    idx = _business_days("1980-02-01", "1980-02-29")
    levels = pd.Series(
        [100.0, 101.0],
        index=pd.date_range("1980-01-01", periods=2, freq="MS"),
    )
    daily = monthly_levels_to_daily_returns(levels, idx)
    feb = daily.dropna()
    assert len(feb) > 0
    assert feb.nunique() == 1


# ---------------------------------------------------------------------------
# Splice invariants: no gap / no overlap
# ---------------------------------------------------------------------------

def test_splice_has_no_overlap_and_no_gap(synthetic_data):
    returns, sources = build_asset_returns(
        synthetic_data, start="1975-01-01", return_sources=True
    )

    start = pd.Timestamp("1975-01-01")
    end = returns.index[-1]
    full_range = (returns.index >= start) & (returns.index <= end)

    # No-gap: every trading day in the intended coverage range has both a
    # source label and a (non-zero-filled) return for the proxied assets.
    # If Fix 1 revealed a gap the splice missed, these assertions fail.
    for asset in ("gold", "commodities"):
        src = sources.loc[full_range, asset]
        ret = returns.loc[full_range, asset]
        assert src.notna().all(), (
            f"{asset}: source label has NaN in 1975-{end.date()} range"
        )
        assert ret.notna().all(), (
            f"{asset}: returns have NaN in 1975-{end.date()} range"
        )

    # No-overlap: at each splice boundary, the day before the splice belongs to
    # the older source and the day of the splice belongs to the newer source.
    def _prev_trading_day(idx: pd.DatetimeIndex, boundary: pd.Timestamp) -> pd.Timestamp:
        prior = idx[idx < boundary]
        assert len(prior) > 0, f"no trading day before {boundary.date()}"
        return prior[-1]

    gold_splice = GOLD_DEFAULT_SPLICE
    gold_prev = _prev_trading_day(sources.index, gold_splice)
    assert sources.loc[gold_prev, "gold"] == GOLD_PROXY_SERIES
    assert sources.loc[gold_splice, "gold"] == "GC=F"
    assert sources.loc[gold_prev, "gold"] != sources.loc[gold_splice, "gold"]

    ppi_to_wti = COMMODITIES_MONTHLY_TO_DAILY_SPLICE
    ppi_prev = _prev_trading_day(sources.index, ppi_to_wti)
    assert sources.loc[ppi_prev, "commodities"] == COMMODITIES_MONTHLY_PROXY_SERIES
    assert sources.loc[ppi_to_wti, "commodities"] == COMMODITIES_DAILY_PROXY_SERIES
    assert sources.loc[ppi_prev, "commodities"] != sources.loc[ppi_to_wti, "commodities"]

    wti_to_fut = COMMODITIES_DAILY_TO_FUTURES_SPLICE
    wti_prev = _prev_trading_day(sources.index, wti_to_fut)
    assert sources.loc[wti_prev, "commodities"] == COMMODITIES_DAILY_PROXY_SERIES
    assert sources.loc[wti_to_fut, "commodities"] == "CL=F"
    assert sources.loc[wti_prev, "commodities"] != sources.loc[wti_to_fut, "commodities"]


def test_commodities_splice_boundary(synthetic_data):
    """The day before each splice belongs to the older source; the day of, to the newer."""
    _, sources = build_asset_returns(
        synthetic_data, start="1975-01-01", return_sources=True
    )
    assert sources.loc["1985-12-31", "commodities"] == COMMODITIES_MONTHLY_PROXY_SERIES
    assert sources.loc["1986-01-02", "commodities"] == COMMODITIES_DAILY_PROXY_SERIES
    assert sources.loc["2000-08-22", "commodities"] == COMMODITIES_DAILY_PROXY_SERIES
    assert sources.loc["2000-08-23", "commodities"] == "CL=F"


# ---------------------------------------------------------------------------
# Non-zero returns pre-2000
# ---------------------------------------------------------------------------

def test_nonzero_returns_for_gold_and_commodities_in_1975(synthetic_data):
    """At 1975-06-15, gold and commodities must have real (non-zero) returns."""
    returns = build_asset_returns(synthetic_data, start="1975-01-01")

    target = pd.Timestamp("1975-06-15")
    nearest = returns.index.asof(target)
    assert nearest is not pd.NaT

    window = returns.loc[:nearest].tail(10)
    assert (window["gold"] != 0).any(), "Gold returns are all zero pre-2000"
    assert (window["commodities"] != 0).any(), "Commodity returns are all zero pre-2000"


# ---------------------------------------------------------------------------
# Spliced gold returns reproduce WPUSI019011 monthly returns
# ---------------------------------------------------------------------------

def test_spliced_gold_monthly_returns_match_proxy(synthetic_data):
    """For any full month in 1975-2000, compounded daily gold returns equal
    WPUSI019011 monthly returns."""
    returns = build_asset_returns(synthetic_data, start="1975-01-01")

    wpu = synthetic_data[GOLD_PROXY_SERIES]
    monthly_proxy = wpu.pct_change().dropna()

    test_months = [
        pd.Timestamp("1975-06-01"),
        pd.Timestamp("1980-02-01"),
        pd.Timestamp("1990-12-01"),
        pd.Timestamp("1999-07-01"),
    ]

    for month_start in test_months:
        mask = (
            (returns.index.year == month_start.year)
            & (returns.index.month == month_start.month)
        )
        month_daily = returns.loc[mask, "gold"]
        if month_daily.empty:
            continue
        compounded = (1.0 + month_daily).prod() - 1.0
        expected = monthly_proxy.loc[month_start]
        assert compounded == pytest.approx(expected, abs=1e-6), (
            f"Month {month_start.date()}: expected {expected}, got {compounded}"
        )


# ---------------------------------------------------------------------------
# splice_returns primitive: newer source wins on overlap
# ---------------------------------------------------------------------------

def test_splice_returns_newer_wins():
    idx_a = pd.date_range("2000-01-01", periods=5, freq="D")
    idx_b = pd.date_range("2000-01-04", periods=5, freq="D")
    a = pd.Series([0.01] * 5, index=idx_a)
    b = pd.Series([0.02] * 5, index=idx_b)

    out, src = splice_returns([(a, "A"), (b, "B")])
    assert out.loc["2000-01-03"] == pytest.approx(0.01)
    assert out.loc["2000-01-04"] == pytest.approx(0.02)
    assert src.loc["2000-01-03"] == "A"
    assert src.loc["2000-01-04"] == "B"
    assert src.loc["2000-01-08"] == "B"

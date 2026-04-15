"""Regression tests for asset-return and source-label invariants (issues #41, #42).

Integration tests exercise the real parquet cache — they reproduce the exact
production failure modes that weren't caught by the synthetic-fixture tests.
Unit tests use small hand-built data dicts that reproduce the same failure
shapes (holiday gaps, ``.diff()`` day-1 NaN, missing segment) without
requiring the cache.

See ``specs/backtester.md`` → "Asset returns → Invariants",
"Proxy series splicing → Invariants", "ETF splicing → Invariants
(bond splicing)".
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.backtester import (
    LONG_BONDS_ETF,
    SHORT_BONDS_ETF,
    ZERO_FILL_SOURCE,
    build_asset_returns,
)


# ---------------------------------------------------------------------------
# Integration: real parquet cache
# ---------------------------------------------------------------------------

def _load_real_data() -> dict:
    from src.data_fetcher import load_all_fred, load_all_yahoo

    return {**load_all_fred(), **load_all_yahoo()}


@pytest.mark.integration
def test_real_returns_have_no_nan(require_cache):
    """specs/backtester.md → Asset returns → Invariants:
    "All return values must be finite (no NaN, no inf)"."""
    data = _load_real_data()
    returns, _ = build_asset_returns(data, return_sources=True)
    nan_cols = returns.columns[returns.isna().any()].tolist()
    assert not nan_cols, (
        f"columns with NaN returns: {nan_cols} "
        f"(counts: {returns.isna().sum().to_dict()})"
    )


@pytest.mark.integration
def test_real_sources_have_no_nan(require_cache):
    """specs/backtester.md → Proxy/ETF splicing → Invariants:
    "Source labels must be populated on every business day the returns frame is
    populated on"."""
    data = _load_real_data()
    returns, sources = build_asset_returns(data, return_sources=True)
    # For every cell in returns that has a value, sources at the same cell
    # must be a non-empty string.
    for col in returns.columns:
        ret_populated = returns[col].notna()
        src_populated = sources[col].notna() & (
            sources[col].astype(str).str.len() > 0
        )
        violations = ret_populated & ~src_populated
        assert not violations.any(), (
            f"{col}: {int(violations.sum())} cells have returns but missing "
            f"source label"
        )


@pytest.mark.integration
def test_real_returns_are_finite(require_cache):
    """Stronger form of the no-NaN invariant: no ``inf`` values either."""
    data = _load_real_data()
    returns, _ = build_asset_returns(data, return_sources=True)
    assert np.isfinite(returns.to_numpy()).all(), (
        "returns frame contains non-finite values (NaN or inf)"
    )


# ---------------------------------------------------------------------------
# Unit: synthetic fixtures reproducing the failure modes
# ---------------------------------------------------------------------------

def _business_days(start: str, end: str) -> pd.DatetimeIndex:
    return pd.bdate_range(start=start, end=end)


def _price_df(index: pd.DatetimeIndex, start: float, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rets = rng.normal(0.0002, 0.01, size=len(index))
    prices = start * np.cumprod(1.0 + rets)
    return pd.DataFrame({"Close": prices, "Adj Close": prices}, index=index)


def _monthly_levels(start: str, end: str, seed: int) -> pd.Series:
    idx = pd.date_range(start=start, end=end, freq="MS")
    rng = np.random.default_rng(seed)
    rets = rng.normal(0.004, 0.02, size=len(idx))
    return pd.Series(100.0 * np.cumprod(1.0 + rets), index=idx)


@pytest.mark.unit
@pytest.mark.spec
def test_unit_holiday_in_returns_frame_does_not_nan_gold_or_bonds():
    """A ``FEDFUNDS.resample("B")`` expansion introduces business-day holidays
    that aren't present in ``^GSPC`` / ``^TNX`` / the monthly-proxy-derived
    daily series. Those days must end up with 0 returns and a labelled source,
    not NaN.

    specs/backtester.md → Asset returns → Edge cases:
    "Holidays (days when the market was closed): may appear in the index with a
    return of 0 ... the invariant is that no NaN appears on any date that IS in
    the index".
    """
    # Build sp500 / ^TNX indices that EXCLUDE some US holidays while FEDFUNDS'
    # business-day expansion includes them — mirroring the production asymmetry.
    nyse_idx = _business_days("1975-01-02", "2005-12-31")
    holidays = [pd.Timestamp("1975-02-17"), pd.Timestamp("1975-05-26"),
                pd.Timestamp("2002-09-02"), pd.Timestamp("2004-12-24")]
    nyse_idx = nyse_idx.difference(pd.DatetimeIndex(holidays))

    sp500 = _price_df(nyse_idx, 70.0, seed=1)
    tnx = _price_df(nyse_idx, 7.5, seed=2)
    # GS2_yield is a daily-ffilled series in production; give it the same
    # NYSE-holiday-missing pattern.
    gs2_yield = tnx["Close"].rename("GS2_yield")

    etf_idx = _business_days("2002-07-30", "2005-12-31").difference(
        pd.DatetimeIndex(holidays)
    )
    tlt = _price_df(etf_idx, 90.0, seed=3)
    shy = _price_df(etf_idx, 80.0, seed=4)

    gold_proxy = _monthly_levels("1974-12-01", "2006-01-01", seed=5)
    gc = _price_df(
        _business_days("2000-08-30", "2005-12-31"), 275.0, seed=6
    )
    ppiaco = _monthly_levels("1974-12-01", "2006-01-01", seed=7)
    wti_idx = _business_days("1986-01-02", "2005-12-31")
    # DCOILWTICO is a daily level series — single-column DataFrame in the cache,
    # which ``_as_series`` squeezes to a Series via the single-column branch.
    wti = _price_df(wti_idx, 30.0, seed=8)[["Close"]]
    cl = _price_df(
        _business_days("2000-08-23", "2005-12-31"), 32.0, seed=9
    )

    # FEDFUNDS: monthly index; resample("B") in build_asset_returns produces
    # pd.bdate_range, which DOES include NYSE holidays (they're business days).
    fed = pd.Series(
        5.0,
        index=pd.date_range("1975-01-01", "2006-01-01", freq="MS"),
        name="FEDFUNDS",
    )

    data = {
        "^GSPC": sp500,
        "^TNX": tnx,
        "GS2_yield": gs2_yield,
        "FEDFUNDS": fed,
        LONG_BONDS_ETF: tlt,
        SHORT_BONDS_ETF: shy,
        "WPUSI019011": gold_proxy,
        "GC=F": gc,
        "PPIACO": ppiaco,
        "DCOILWTICO": wti,
        "CL=F": cl,
    }

    returns, sources = build_asset_returns(
        data, start="1975-01-01", return_sources=True
    )

    # Every holiday introduced by FEDFUNDS' B-expansion is present in the frame.
    for h in holidays:
        assert h in returns.index, f"{h.date()} missing from returns index"
        # No NaN anywhere on these days.
        assert not returns.loc[h].isna().any(), (
            f"{h.date()} has NaN returns: {returns.loc[h].to_dict()}"
        )
        # Sources populated with a non-empty label.
        assert not sources.loc[h].isna().any(), (
            f"{h.date()} has NaN sources: {sources.loc[h].to_dict()}"
        )
        # Gold / commodities / bonds on holidays labelled with their active
        # segment's source (not a sentinel) — the segment is in force, the
        # day's return just happens to be zero.
        assert sources.loc[h, "gold"] in {"WPUSI019011", "GC=F"}
        assert sources.loc[h, "commodities"] in {
            "PPIACO", "DCOILWTICO", "CL=F"
        }
        assert sources.loc[h, "long_bonds"] in {"^TNX", LONG_BONDS_ETF}
        assert sources.loc[h, "short_bonds"] in {"GS2_yield", SHORT_BONDS_ETF}


@pytest.mark.unit
@pytest.mark.spec
def test_unit_tnx_day_one_diff_nan_gets_tnx_source_label():
    """The first day of a ``.diff()`` / ``pct_change()`` segment is NaN by
    definition. The day still belongs to the segment's source; the invariant
    is that the source label is populated wherever the return frame is.
    """
    nyse_idx = _business_days("1975-01-02", "1980-12-31")
    sp500 = _price_df(nyse_idx, 70.0, seed=1)
    tnx = _price_df(nyse_idx, 7.5, seed=2)
    gs2_yield = tnx["Close"].rename("GS2_yield")

    fed = pd.Series(
        5.0,
        index=pd.date_range("1975-01-01", "1981-01-01", freq="MS"),
        name="FEDFUNDS",
    )

    data = {
        "^GSPC": sp500,
        "^TNX": tnx,
        "GS2_yield": gs2_yield,
        "FEDFUNDS": fed,
        "WPUSI019011": _monthly_levels("1974-12-01", "1981-01-01", seed=5),
        "PPIACO": _monthly_levels("1974-12-01", "1981-01-01", seed=7),
    }

    returns, sources = build_asset_returns(
        data, start="1975-01-01", return_sources=True
    )

    first_tnx_day = tnx.index[0]  # 1975-01-02
    # .diff() is NaN on this day — build_asset_returns zero-fills the return.
    assert returns.loc[first_tnx_day, "long_bonds"] == 0.0
    # The source label still points at ^TNX — the day belongs to the
    # approximation regime; the return is just mathematically undefined.
    assert sources.loc[first_tnx_day, "long_bonds"] == "^TNX"


@pytest.mark.unit
@pytest.mark.spec
def test_unit_short_bonds_with_no_gs2_yield_uses_zero_fill_label():
    """When the data dict does not supply ``GS2_yield`` (the duration-
    approximation segment), short_bonds has no pre-SHY segment at all. Every
    pre-SHY day is zero-filled for returns and labelled with the
    ``ZERO_FILL_SOURCE`` sentinel so downstream predicates see a known
    vocabulary instead of NaN. This is the exact production configuration of
    ``{**load_all_fred(), **load_all_yahoo()}`` today (``GS2_yield`` is
    constructed by ``validate_bond_returns.py``, not by the cache loaders).
    """
    nyse_idx = _business_days("1975-01-02", "2005-12-31")
    sp500 = _price_df(nyse_idx, 70.0, seed=1)
    tnx = _price_df(nyse_idx, 7.5, seed=2)

    etf_idx = _business_days("2002-07-30", "2005-12-31")
    shy = _price_df(etf_idx, 80.0, seed=4)
    tlt = _price_df(etf_idx, 90.0, seed=3)

    fed = pd.Series(
        5.0,
        index=pd.date_range("1975-01-01", "2006-01-01", freq="MS"),
        name="FEDFUNDS",
    )

    data = {
        "^GSPC": sp500,
        "^TNX": tnx,
        # No "GS2_yield" — matches load_all_fred() behavior.
        "FEDFUNDS": fed,
        LONG_BONDS_ETF: tlt,
        SHORT_BONDS_ETF: shy,
        "WPUSI019011": _monthly_levels("1974-12-01", "2006-01-01", seed=5),
        "PPIACO": _monthly_levels("1974-12-01", "2006-01-01", seed=7),
    }

    returns, sources = build_asset_returns(
        data, start="1975-01-01", return_sources=True
    )

    pre_shy = sources.index < pd.Timestamp("2002-07-30")
    post_shy = sources.index >= pd.Timestamp("2002-07-30")

    # Pre-SHY: no segment, all ZERO_FILL_SOURCE with zero returns.
    assert (sources.loc[pre_shy, "short_bonds"] == ZERO_FILL_SOURCE).all()
    assert (returns.loc[pre_shy, "short_bonds"] == 0.0).all()

    # Post-SHY: labelled with SHY.
    assert (sources.loc[post_shy, "short_bonds"] == SHORT_BONDS_ETF).all()

    # No NaN anywhere.
    assert not returns.isna().any().any()
    assert not sources.isna().any().any()

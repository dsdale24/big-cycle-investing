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
def test_unit_short_bonds_with_no_gs2_at_all_uses_zero_fill_label():
    """When the data dict supplies neither ``GS2_yield`` NOR raw monthly
    ``GS2``, short_bonds has no pre-SHY segment at all. Every pre-SHY day
    is zero-filled for returns and labelled with the ``ZERO_FILL_SOURCE``
    sentinel so downstream predicates see a known vocabulary instead of
    NaN. (Prior to issue #43 this was the actual production configuration
    because no loader constructed ``GS2_yield`` from the raw monthly
    ``GS2``; the fix now falls back to deriving the daily series from
    ``GS2`` when present. This test pins the genuine no-data path.)
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
        # No "GS2_yield" AND no raw "GS2" — neither segment source available.
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


# ---------------------------------------------------------------------------
# Issue #43: short_bonds duration approximation must run in production
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_real_short_bonds_pre_2002_uses_gs2_yield_source(require_cache):
    """specs/backtester.md → ETF splicing (bond splicing): the duration
    approximation runs for short_bonds pre-2002-07-30, then SHY takes over.

    Regression test for issue #43: the production data dict (just
    ``load_all_fred()`` + ``load_all_yahoo()``, no manual augmentation) must
    produce ``"GS2_yield"`` source labels across the bulk of the pre-SHY
    window, not ``"zero_fill"``. Prior to the fix every pre-SHY business
    day in short_bonds was silently zero-filled because ``GS2_yield`` was
    only constructed inside ``scripts/validate_bond_returns.py``.

    The raw monthly ``GS2`` FRED series begins 1976-06-01, so the earliest
    ~17 months of the backtest window (1975-01-01 to 1976-06-01) have no
    yield data and legitimately fall back to the ``zero_fill`` source.
    The assertion here is that once ``GS2`` data is available, the
    duration approximation is the source.
    """
    data = _load_real_data()
    _, sources = build_asset_returns(data, return_sources=True)

    # Anchor the "GS2 available" window to the data itself — avoids coupling
    # the test to manifest dates that may shift as FRED revises history.
    gs2_start = pd.Timestamp(data["GS2"].index[0])
    approx_window = (sources.index >= gs2_start) & (
        sources.index < pd.Timestamp("2002-07-30")
    )
    approx_sources = sources.loc[approx_window, "short_bonds"]

    assert (approx_sources == "GS2_yield").all(), (
        f"expected all short_bonds labelled 'GS2_yield' from GS2 start "
        f"({gs2_start.date()}) through SHY start, got "
        f"{approx_sources.value_counts(dropna=False).to_dict()}"
    )
    assert (approx_sources != ZERO_FILL_SOURCE).all(), (
        "post-GS2-start pre-SHY short_bonds window contains 'zero_fill' "
        "labels — issue #43 has regressed (duration approximation not "
        "running in production)"
    )


@pytest.mark.unit
@pytest.mark.spec
def test_unit_short_bonds_falls_back_to_raw_gs2_when_gs2_yield_missing():
    """Issue #43 fallback: when only raw monthly ``GS2`` is in the data dict
    (which is what ``load_all_fred()`` returns), ``_short_bonds_approximation``
    must construct the daily forward-filled series inline and produce
    non-zero returns labelled ``"GS2_yield"`` across the pre-SHY window.
    """
    nyse_idx = _business_days("1975-01-02", "2005-12-31")
    sp500 = _price_df(nyse_idx, 70.0, seed=1)
    tnx = _price_df(nyse_idx, 7.5, seed=2)

    # Raw monthly GS2 — a DataFrame with a single "GS2" column, matching what
    # load_all_fred() returns from the parquet cache.
    gs2_monthly_idx = pd.date_range("1974-12-01", "2005-12-01", freq="MS")
    rng = np.random.default_rng(42)
    gs2_levels = 5.0 + np.cumsum(rng.normal(0.0, 0.15, size=len(gs2_monthly_idx)))
    gs2_raw = pd.DataFrame({"GS2": gs2_levels}, index=gs2_monthly_idx)

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
        "GS2": gs2_raw,  # raw monthly only — no "GS2_yield"
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
    pre_shy_sources = sources.loc[pre_shy, "short_bonds"]
    pre_shy_returns = returns.loc[pre_shy, "short_bonds"]

    # Labelled with the approximation source.
    assert (pre_shy_sources == "GS2_yield").all(), (
        f"pre-SHY source labels: "
        f"{pre_shy_sources.value_counts(dropna=False).to_dict()}"
    )
    # Approximation actually produced non-zero returns — proves the fallback
    # constructed a real daily yield series, not an all-NaN placeholder.
    assert (pre_shy_returns != 0.0).sum() > 100, (
        f"expected many non-zero pre-SHY short_bonds returns, got only "
        f"{(pre_shy_returns != 0.0).sum()} non-zero days"
    )


@pytest.mark.unit
def test_unit_short_bonds_explicit_gs2_yield_wins_over_raw_gs2_fallback():
    """Back-compat for issue #43: if the caller supplies ``GS2_yield``
    explicitly, the implementation must use that series directly rather than
    the fallback derived from raw monthly ``GS2``. This preserves the
    behavior callers like ``scripts/validate_bond_returns.py`` rely on.
    """
    nyse_idx = _business_days("1975-01-02", "2005-12-31")
    sp500 = _price_df(nyse_idx, 70.0, seed=1)
    tnx = _price_df(nyse_idx, 7.5, seed=2)

    # Raw monthly GS2 centered around 5.
    gs2_monthly_idx = pd.date_range("1974-12-01", "2005-12-01", freq="MS")
    gs2_raw = pd.DataFrame(
        {"GS2": np.full(len(gs2_monthly_idx), 5.0)},
        index=gs2_monthly_idx,
    )

    # Explicit GS2_yield that differs materially from what the fallback
    # would derive: a daily series trending from 3.0 upward, NYSE-aligned.
    explicit_yield = pd.Series(
        3.0 + np.linspace(0, 2.0, len(nyse_idx)),
        index=nyse_idx,
        name="GS2_yield",
    )

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
        "GS2": gs2_raw,
        "GS2_yield": explicit_yield,
        "FEDFUNDS": fed,
        LONG_BONDS_ETF: tlt,
        SHORT_BONDS_ETF: shy,
        "WPUSI019011": _monthly_levels("1974-12-01", "2006-01-01", seed=5),
        "PPIACO": _monthly_levels("1974-12-01", "2006-01-01", seed=7),
    }

    returns, _ = build_asset_returns(
        data, start="1975-01-01", return_sources=True
    )

    # Reproduce the approximation formula (duration=2, carry=y[t-1]/252,
    # clipped to +/-5%) from the EXPLICIT GS2_yield. If the implementation
    # had ignored the explicit series and fallen back to raw GS2 (flat 5.0),
    # .diff() would be 0 everywhere and returns would equal 5.0/100/252.
    y2 = explicit_yield / 100
    expected = (-2.0 * y2.diff() + y2.shift(1) / 252).clip(-0.05, 0.05)

    # Compare on a mid-sample date where .diff() is defined.
    probe = pd.Timestamp("1980-06-02")
    assert probe in returns.index
    assert returns.loc[probe, "short_bonds"] == pytest.approx(
        expected.loc[probe], rel=1e-9, abs=1e-12
    ), (
        "explicit GS2_yield was not used — implementation likely fell back to "
        "raw GS2 despite explicit key being present"
    )

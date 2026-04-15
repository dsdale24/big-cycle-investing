"""Tests for civilizational composite indicators (issue #4 Path A).

Covers walk-forward safety, rolling z-score behaviour, equal-weight
averaging, and sentiment inversion for ``internal_order_stress_index``.
Synthetic in-memory fixtures only — no FRED cache required.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.indicators import (
    internal_order_stress_index,
    shift_by_publication_lag,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _annual_gini(start_year: int, end_year: int, value: float = 0.40) -> pd.Series:
    idx = pd.date_range(
        start=f"{start_year}-12-31",
        end=f"{end_year}-12-31",
        freq="YE",
    )
    return pd.Series(value, index=idx, name="GINIALLRF", dtype=float)


def _monthly_constant(start: str, end: str, value: float, name: str) -> pd.Series:
    idx = pd.date_range(start=start, end=end, freq="ME")
    return pd.Series(value, index=idx, name=name, dtype=float)


def _monthly_linear(start: str, end: str, base: float, step: float, name: str) -> pd.Series:
    idx = pd.date_range(start=start, end=end, freq="ME")
    vals = base + step * np.arange(len(idx))
    return pd.Series(vals, index=idx, name=name, dtype=float)


# ---------------------------------------------------------------------------
# shift_by_publication_lag
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_publication_lag_shifts_index_forward_by_months():
    s = pd.Series(
        [1.0, 2.0],
        index=pd.to_datetime(["2024-12-31", "2025-12-31"]),
    )
    shifted = shift_by_publication_lag(s, 9)
    assert list(shifted.index) == [
        pd.Timestamp("2025-09-30"),
        pd.Timestamp("2026-09-30"),
    ]
    assert list(shifted.values) == [1.0, 2.0]


@pytest.mark.unit
def test_publication_lag_zero_is_identity():
    s = pd.Series([1.0, 2.0], index=pd.to_datetime(["2020-12-31", "2021-12-31"]))
    out = shift_by_publication_lag(s, 0)
    pd.testing.assert_index_equal(out.index, s.index)
    assert list(out.values) == [1.0, 2.0]


@pytest.mark.unit
def test_publication_lag_rejects_negative():
    s = pd.Series([1.0], index=pd.to_datetime(["2020-12-31"]))
    with pytest.raises(ValueError):
        shift_by_publication_lag(s, -1)


# ---------------------------------------------------------------------------
# Walk-forward safety: a Gini value stamped 2024-12-31 with 9-month lag
# should NOT be visible at 2025-06-30 but SHOULD be visible at 2025-09-30.
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_walk_forward_publication_lag_blocks_unreleased_value():
    # Gini drifts slightly for years, then jumps to 0.99 on 2024-12-31. The
    # tiny drift keeps the rolling z-score's std non-zero; the jump on
    # 2024-12-31 should NOT affect the monthly value at 2025-06-30 (only 6
    # months after stamp) but MUST by 2025-09-30 (9 months after stamp). It
    # should also drive the composite up only after publication.
    gini_idx = pd.date_range("2010-12-31", "2024-12-31", freq="YE")
    drift = 0.001 * np.arange(len(gini_idx) - 1)
    gini_vals = list(0.45 + drift) + [0.99]
    gini = pd.Series(gini_vals, index=gini_idx, name="GINIALLRF", dtype=float)

    # epu/sentiment with light variation so all three z-scores are
    # well-defined (constant series have zero rolling std → NaN).
    epu = _monthly_linear("2010-01-01", "2026-12-31", base=100.0, step=0.1, name="USEPUINDXM")
    sentiment = _monthly_linear(
        "2010-01-01", "2026-12-31", base=80.0, step=-0.05, name="UMCSENT",
    )

    composite = internal_order_stress_index(
        gini, epu, sentiment,
        publication_lag_months=9,
        zscore_window=60,
    )

    from src.indicators import _rolling_zscore_strict
    gini_shifted = shift_by_publication_lag(gini, 9)
    gini_monthly = gini_shifted.resample("ME").last().ffill()
    gini_z = _rolling_zscore_strict(gini_monthly, 60)

    val_jun = gini_monthly.loc["2025-06-30"]
    val_sep = gini_monthly.loc["2025-09-30"]
    expected_pre_jump = 0.45 + drift[-1]
    assert val_jun == pytest.approx(expected_pre_jump), (
        f"Expected pre-publication value {expected_pre_jump} at 2025-06-30, "
        f"got {val_jun}"
    )
    assert val_sep == pytest.approx(0.99), (
        f"Expected post-publication value 0.99 at 2025-09-30, got {val_sep}"
    )

    # And the rolling z-score should jump correspondingly.
    assert gini_z.loc["2025-06-30"] < gini_z.loc["2025-09-30"]
    # And the published jump must show up in the composite too.
    assert composite.loc["2025-06-30"] < composite.loc["2025-09-30"]


# ---------------------------------------------------------------------------
# Rolling z-score uses only prior `window` months of data.
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_rolling_zscore_window_uses_only_prior_months():
    # Build long monotone-trending series so the rolling z-score has
    # non-zero variance everywhere. The composite at month t under window=W
    # should equal the simple mean of the three z-scores computed manually
    # from each component's last W months.
    start = "2000-01-01"
    end = "2025-12-31"
    epu = _monthly_linear(start, end, base=50.0, step=0.5, name="USEPUINDXM")
    sentiment = _monthly_linear(start, end, base=80.0, step=-0.1, name="UMCSENT")

    # Vary gini slightly across years so its z-score has non-zero std.
    gini_idx = pd.date_range("1995-12-31", "2024-12-31", freq="YE")
    gini_vals = 0.40 + 0.001 * np.arange(len(gini_idx))
    gini = pd.Series(gini_vals, index=gini_idx, name="GINIALLRF", dtype=float)

    window = 60
    composite = internal_order_stress_index(
        gini, epu, sentiment,
        publication_lag_months=9,
        zscore_window=window,
    )

    # Pick a date deep enough that the window is fully populated.
    t = pd.Timestamp("2020-06-30")
    epu_monthly = epu.resample("ME").last()
    epu_window = epu_monthly.loc[:t].iloc[-window:]
    expected_epu_z = (epu_monthly.loc[t] - epu_window.mean()) / epu_window.std()

    sent_monthly = sentiment.resample("ME").last()
    sent_window = (-sent_monthly).loc[:t].iloc[-window:]
    expected_sent_z = ((-sent_monthly).loc[t] - sent_window.mean()) / sent_window.std()

    # Reconstruct the gini z-score the same way as production code.
    from src.indicators import _rolling_zscore_strict, shift_by_publication_lag
    gini_shifted = shift_by_publication_lag(gini, 9)
    gini_monthly = gini_shifted.resample("ME").last().ffill()
    gini_window = gini_monthly.loc[:t].iloc[-window:]
    expected_gini_z = (gini_monthly.loc[t] - gini_window.mean()) / gini_window.std()

    expected_composite = (expected_gini_z + expected_epu_z + expected_sent_z) / 3
    assert composite.loc[t] == pytest.approx(expected_composite, rel=1e-9)


@pytest.mark.unit
def test_rolling_zscore_yields_nan_before_window_filled():
    epu = _monthly_linear("2015-01-01", "2025-12-31", 50.0, 0.5, "USEPUINDXM")
    sentiment = _monthly_linear("2015-01-01", "2025-12-31", 80.0, -0.1, "UMCSENT")
    gini_idx = pd.date_range("2014-12-31", "2024-12-31", freq="YE")
    gini = pd.Series(
        0.40 + 0.001 * np.arange(len(gini_idx)),
        index=gini_idx,
        name="GINIALLRF",
        dtype=float,
    )
    window = 120
    composite = internal_order_stress_index(
        gini, epu, sentiment,
        publication_lag_months=9,
        zscore_window=window,
    )
    # First valid composite cannot precede 120 months of overlap.
    first_valid = composite.index.min()
    assert first_valid >= pd.Timestamp("2015-01-01") + pd.DateOffset(months=window - 1)


# ---------------------------------------------------------------------------
# Equal-weight composite: mean of three z-scores.
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_equal_weight_composite_is_simple_mean():
    # Make all three component z-scores trivially equal at every point by
    # constructing inputs whose rolling z-scores match.
    start, end = "2000-01-01", "2025-12-31"
    epu = _monthly_linear(start, end, base=50.0, step=0.5, name="USEPUINDXM")
    # sentiment is INVERTED inside the function, so to make its z-score equal
    # to epu's, give sentiment the opposite trend (so -sentiment matches epu's
    # shape up to affine transformation, which a z-score normalises away).
    sentiment = _monthly_linear(start, end, base=80.0, step=-0.5, name="UMCSENT")

    # Gini: also linearly increasing on annual stamps.
    gini_idx = pd.date_range("1995-12-31", "2024-12-31", freq="YE")
    gini_vals = 0.40 + 0.001 * np.arange(len(gini_idx))
    gini = pd.Series(gini_vals, index=gini_idx, name="GINIALLRF", dtype=float)

    composite = internal_order_stress_index(
        gini, epu, sentiment,
        publication_lag_months=9,
        zscore_window=60,
    )

    # Pull the per-component z-scores back out and check the mean property at a
    # specific date (well past the window warm-up).
    from src.indicators import _rolling_zscore_strict, shift_by_publication_lag

    gini_monthly = shift_by_publication_lag(gini, 9).resample("ME").last().ffill()
    gini_z = _rolling_zscore_strict(gini_monthly, 60)
    epu_z = _rolling_zscore_strict(epu.resample("ME").last(), 60)
    sent_z = _rolling_zscore_strict(-sentiment.resample("ME").last(), 60)

    t = pd.Timestamp("2020-06-30")
    expected = (gini_z.loc[t] + epu_z.loc[t] + sent_z.loc[t]) / 3.0
    assert composite.loc[t] == pytest.approx(expected, rel=1e-9)


# ---------------------------------------------------------------------------
# Sentiment inversion: rising sentiment → falling z-score contribution.
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_sentiment_inversion_monotonic_decreases_zscore_contribution():
    start, end = "2000-01-01", "2025-12-31"
    # Strictly increasing sentiment.
    sentiment = _monthly_linear(start, end, base=60.0, step=0.2, name="UMCSENT")

    from src.indicators import _rolling_zscore_strict
    inv_z = _rolling_zscore_strict(-sentiment.resample("ME").last(), 60)

    # After warm-up, the z-score series of -sentiment under a strictly
    # increasing sentiment trend must be monotonically non-increasing.
    after_warmup = inv_z.dropna()
    diffs = after_warmup.diff().dropna()
    # Allow tiny floating-point wobble.
    assert (diffs <= 1e-12).all(), (
        f"Inverted sentiment z-score should be non-increasing under rising "
        f"sentiment; got max diff {diffs.max():.3e}"
    )

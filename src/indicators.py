"""Derived indicators computed from raw data series.

Each indicator function takes raw dataframes and returns a new series.
These are building blocks for strategy signals — add freely as hypotheses emerge.
"""

from __future__ import annotations

import pandas as pd
import numpy as np


# --- Rate of Change / Momentum ---

def yoy_change(series: pd.Series) -> pd.Series:
    """Year-over-year percentage change. Works for any frequency."""
    # Resample to monthly first if needed, then compute 12-period change
    monthly = series.resample("ME").last().dropna()
    return monthly.pct_change(12) * 100


def rolling_zscore(series: pd.Series, window: int = 60) -> pd.Series:
    """Z-score relative to trailing window (default 5 years monthly)."""
    monthly = series.resample("ME").last().dropna()
    rolling_mean = monthly.rolling(window).mean()
    rolling_std = monthly.rolling(window).std()
    return (monthly - rolling_mean) / rolling_std


# --- Debt Cycle Position ---

def debt_acceleration(debt_to_gdp: pd.Series) -> pd.Series:
    """Rate of change of debt/GDP — positive = debt growing faster than economy."""
    quarterly = debt_to_gdp.resample("QE").last().dropna()
    return quarterly.diff(4)  # Year-over-year change in the ratio


def real_rate(nominal_rate: pd.Series, inflation_yoy: pd.Series) -> pd.Series:
    """Real interest rate = nominal - inflation."""
    # Align to common dates
    aligned = pd.concat([nominal_rate, inflation_yoy], axis=1).dropna()
    return aligned.iloc[:, 0] - aligned.iloc[:, 1]


# --- Monetary Regime ---

def money_supply_growth(m2: pd.Series) -> pd.Series:
    """Year-over-year M2 growth rate."""
    return yoy_change(m2)


def monetary_base_expansion(base: pd.Series) -> pd.Series:
    """Year-over-year monetary base growth — spikes indicate QE-like episodes."""
    return yoy_change(base)


# --- Yield Curve ---

def yield_curve_slope(long_rate: pd.Series, short_rate: pd.Series) -> pd.Series:
    """Spread between long and short rates. Negative = inverted."""
    aligned = pd.concat([long_rate, short_rate], axis=1).dropna()
    return aligned.iloc[:, 0] - aligned.iloc[:, 1]


# --- Currency / Store of Value ---

def gold_vs_money_supply(gold_price: pd.Series, m2: pd.Series) -> pd.Series:
    """Gold price relative to M2 money supply — high = gold 'cheap' vs money printed."""
    monthly_gold = gold_price.resample("ME").last().dropna()
    monthly_m2 = m2.resample("ME").last().dropna()
    aligned = pd.concat([monthly_gold, monthly_m2], axis=1).dropna()
    # Normalize both to start at 100
    norm_gold = aligned.iloc[:, 0] / aligned.iloc[0, 0] * 100
    norm_m2 = aligned.iloc[:, 1] / aligned.iloc[0, 1] * 100
    return norm_gold / norm_m2 * 100


# --- Composite Indicators ---

def regime_classifier(
    yield_curve: pd.Series,
    inflation_yoy: pd.Series,
    debt_accel: pd.Series,
    real_rate_series: pd.Series,
) -> pd.DataFrame:
    """
    Simple regime classification based on multiple indicators.
    Returns a DataFrame with regime scores for:
    - expansion (early cycle)
    - overheating (late cycle)
    - contraction (recession)
    - reflation (recovery/stimulus)

    This is a starting point — meant to be iterated on.
    """
    # Align all series to monthly
    data = pd.DataFrame({
        "yield_curve": yield_curve.resample("ME").last(),
        "inflation": inflation_yoy.resample("ME").last(),
        "debt_accel": debt_accel.resample("QE").last().resample("ME").ffill(),
        "real_rate": real_rate_series.resample("ME").last(),
    }).dropna()

    regimes = pd.DataFrame(index=data.index)

    # Simple heuristic scoring — replace with learned weights over time
    regimes["expansion"] = (
        (data["yield_curve"] > 0).astype(float) * 0.3 +
        (data["inflation"] < 4).astype(float) * 0.3 +
        (data["real_rate"] > 0).astype(float) * 0.2 +
        (data["debt_accel"] > 0).astype(float) * 0.2
    )

    regimes["overheating"] = (
        (data["yield_curve"] < 0.5).astype(float) * 0.3 +
        (data["inflation"] > 4).astype(float) * 0.3 +
        (data["real_rate"] < 0).astype(float) * 0.2 +
        (data["debt_accel"] > 2).astype(float) * 0.2
    )

    regimes["contraction"] = (
        (data["yield_curve"] < 0).astype(float) * 0.3 +
        (data["inflation"].diff(3) < 0).astype(float) * 0.2 +
        (data["real_rate"] > 2).astype(float) * 0.2 +
        (data["debt_accel"] < 0).astype(float) * 0.3
    )

    regimes["reflation"] = (
        (data["yield_curve"] > 1).astype(float) * 0.2 +
        (data["real_rate"] < -1).astype(float) * 0.3 +
        (data["debt_accel"] > 0).astype(float) * 0.2 +
        (data["inflation"].diff(3) > 0).astype(float) * 0.3
    )

    return regimes


# --- Civilizational composites ---


def shift_by_publication_lag(
    series: pd.Series,
    publication_lag_months: int,
) -> pd.Series:
    """Shift a series forward in time by a publication lag, in months.

    Models the real-world delay between when a value is realized (the index
    timestamp) and when it would have been publicly available. For an annual
    Gini stamped 2024-12-31 with a 9-month lag, the shifted series carries
    that value at 2025-09-30 — the earliest a backtest at month t could
    legitimately know it.
    """
    if publication_lag_months < 0:
        raise ValueError("publication_lag_months must be >= 0")
    if series.empty:
        return series.copy()
    shifted_index = series.index + pd.DateOffset(months=publication_lag_months)
    return pd.Series(series.values, index=shifted_index, name=series.name)


def _rolling_zscore_strict(monthly: pd.Series, window: int) -> pd.Series:
    """Rolling z-score that requires a full window before emitting a value.

    Uses ``min_periods=window`` so early-period values are NaN rather than
    noisy estimates from a 1-12 month window.
    """
    rolling_mean = monthly.rolling(window, min_periods=window).mean()
    rolling_std = monthly.rolling(window, min_periods=window).std()
    return (monthly - rolling_mean) / rolling_std


def internal_order_stress_index(
    gini: pd.Series,
    epu: pd.Series,
    sentiment: pd.Series,
    *,
    publication_lag_months: int = 9,
    zscore_window: int = 120,
) -> pd.Series:
    """Composite z-score signal for internal-order stress, from notebook 02.

    Components (equal-weight average of z-scores):

    - Gini inequality (annual, shifted forward by ``publication_lag_months``
      to respect real-world publication delay — e.g., 2024 Gini published
      ~mid-2025).
    - EPU Baker-Bloom-Davis policy uncertainty (monthly).
    - Consumer sentiment, inverted (monthly; higher value = more stress).

    Returns a monthly series indexed by month-end dates. Walk-forward safe:
    at month t, only data published by t (i.e., with publication_lag respected)
    is used. Uses a rolling ``zscore_window`` rather than expanding to
    stabilize the early-period noise noted in issue #4's design questions.

    See specs/indicator_framework.md §6 "Wealth Inequality & Internal Order"
    and §"Using Low-Frequency Data".
    """
    if publication_lag_months < 0:
        raise ValueError("publication_lag_months must be >= 0")
    if zscore_window < 2:
        raise ValueError("zscore_window must be >= 2")

    gini = gini.dropna().sort_index()
    epu = epu.dropna().sort_index()
    sentiment = sentiment.dropna().sort_index()

    # Publication-lag shift on the annual Gini, then resample to month-end and
    # forward-fill so each month carries the most recently published value.
    gini_shifted = shift_by_publication_lag(gini, publication_lag_months)
    gini_monthly = gini_shifted.resample("ME").last().ffill()

    epu_monthly = epu.resample("ME").last()
    sentiment_monthly = sentiment.resample("ME").last()

    gini_z = _rolling_zscore_strict(gini_monthly, zscore_window)
    epu_z = _rolling_zscore_strict(epu_monthly, zscore_window)
    # Invert sentiment so higher = more stress.
    sentiment_z = _rolling_zscore_strict(-sentiment_monthly, zscore_window)

    components = pd.concat(
        [
            gini_z.rename("gini_z"),
            epu_z.rename("epu_z"),
            sentiment_z.rename("sentiment_inv_z"),
        ],
        axis=1,
        sort=False,
    )
    # Require all three components to be defined at month t — keeps the
    # composite honestly defined only where every input is observable under
    # the walk-forward constraint.
    components = components.dropna()

    composite = components.mean(axis=1)
    composite.name = "internal_order_stress"
    return composite

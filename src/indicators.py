"""Derived indicators computed from raw data series.

Each indicator function takes raw dataframes and returns a new series.
These are building blocks for strategy signals — add freely as hypotheses emerge.
"""

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

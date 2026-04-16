"""Tests for framework-level publication-lag truncation in ``run_backtest``.

Anchors: ``specs/backtester.md`` § "Core invariant: walk-forward constraint"
and its ``Test cases`` subsection, plus ``specs/data_pipeline/us.md``
§ "Publication-lag contract". Fixes #72.

These are tests of the *framework* behavior — they use a minimal
``CaptureStrategy`` that just records what ``available_data`` it was handed
on each rebalance, so the assertions are about the truncation contract, not
about any specific strategy's internal logic.

All synthetic fixtures; no FRED cache or network required.
"""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import numpy as np
import pandas as pd
import pytest
import yaml

from src import backtester
from src.backtester import (
    DEFAULT_LAG_BY_FREQUENCY,
    PortfolioSnapshot,
    _load_lag_registry,
    _resolve_publication_lag,
    run_backtest,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class CaptureStrategy:
    """Minimal strategy that records what ``available_data`` it receives.

    Holds a constant equal-weight allocation so the backtest runs cleanly;
    the ``observations`` list is the test surface.
    """

    def __init__(self) -> None:
        self.observations: list[dict[str, pd.Series | pd.DataFrame]] = []
        self.weights = {
            "equities": 1.0,
            "long_bonds": 0.0,
            "short_bonds": 0.0,
            "gold": 0.0,
            "commodities": 0.0,
            "cash": 0.0,
        }

    def allocate(self, date, available_data, pre_rebalance_weights):
        # Snapshot each series-as-passed so later assertions can inspect
        # exactly what the framework made visible at this rebalance.
        snapshot = {k: v.copy() for k, v in available_data.items()}
        snapshot["__rebalance_date__"] = date
        self.observations.append(snapshot)
        return PortfolioSnapshot(
            date=date, weights=dict(self.weights), regime="capture"
        )


def _flat_returns(start: str, end: str) -> pd.DataFrame:
    """Zero-return daily frame covering all specced asset classes."""
    idx = pd.bdate_range(start=start, end=end)
    columns = ["equities", "long_bonds", "short_bonds", "gold", "commodities", "cash"]
    return pd.DataFrame({c: np.zeros(len(idx)) for c in columns}, index=idx)


def _find_observation_for(
    observations: list[dict], date: pd.Timestamp
) -> dict | None:
    for obs in observations:
        if obs["__rebalance_date__"] == date:
            return obs
    return None


@pytest.fixture(autouse=True)
def _reset_lag_registry_cache():
    """Registry is module-level LRU-cached; clear before and after each test
    so monkeypatched / temporary registries take effect and don't leak."""
    _load_lag_registry.cache_clear()
    yield
    _load_lag_registry.cache_clear()


# ---------------------------------------------------------------------------
# Spec-anchored tests — directly mirror bullets in
# specs/backtester.md § "Core invariant: walk-forward constraint → Test cases"
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.spec
def test_timestamp_lookahead_hidden_at_pre_jump_rebalance(monkeypatch):
    """Spec: "Given an indicator that jumps from 0 to 100 on 2000-01-01, a
    strategy rebalancing on 1999-12-31 must see 0, not 100. (Timestamp
    look-ahead.)"

    See specs/backtester.md § "Core invariant: walk-forward constraint →
    Test cases", bullet 1.

    Lag is pinned to 0 here deliberately so the test isolates timestamp
    look-ahead (the rebalance date precedes the jump's timestamp) from
    publication-lag truncation (which would hide the value for additional
    days after its timestamp). With lag=0 and rebalance on 1999-12-31, the
    only reason the 2000-01-01 value must be hidden is that it is
    timestamped *after* the rebalance date.
    """
    monkeypatch.setattr(
        backtester,
        "_load_lag_registry",
        lambda: {"JUMP": 0},
    )

    jump_series = pd.Series(
        {
            pd.Timestamp("1999-12-30"): 0.0,
            pd.Timestamp("1999-12-31"): 0.0,
            pd.Timestamp("2000-01-01"): 100.0,
            pd.Timestamp("2000-01-03"): 100.0,
        },
        name="JUMP",
    )

    strat = CaptureStrategy()
    returns = _flat_returns("1999-12-01", "2000-01-31")
    run_backtest(
        strat, returns,
        indicator_data={"JUMP": jump_series},
        start="1999-12-01",
        rebalance_freq="W-FRI",
    )

    rebalance_date = pd.Timestamp("1999-12-31")
    obs = _find_observation_for(strat.observations, rebalance_date)
    assert obs is not None, f"no rebalance observed at {rebalance_date}"
    visible_index = obs["JUMP"].index

    assert pd.Timestamp("2000-01-01") not in visible_index, (
        "Jump value timestamped 2000-01-01 must be hidden at a 1999-12-31 "
        "rebalance (timestamp look-ahead)."
    )
    assert pd.Timestamp("1999-12-31") in visible_index, (
        "Pre-jump value timestamped 1999-12-31 (lag=0) must be visible at "
        "the 1999-12-31 rebalance."
    )
    # The most recent visible value must be the pre-jump 0.0, not 100.0.
    most_recent_value = obs["JUMP"].iloc[-1]
    assert most_recent_value == 0.0, (
        f"Most recent visible value must be 0 (pre-jump), got {most_recent_value}"
    )


@pytest.mark.unit
@pytest.mark.spec
def test_annual_series_with_180_day_lag_hides_year_end_value(monkeypatch):
    """Spec: "Given annual data for year 2000, if publication lag is 180
    days, a strategy rebalancing on 2001-03-01 must NOT see the 2000 value
    (timestamp 2000-12-31 + 180 days = 2001-06-29, after rebalance date)."

    See specs/backtester.md § "Core invariant: walk-forward constraint →
    Test cases", bullet 2.

    The test also asserts the symmetric "MAY see" behavior: a rebalance
    after 2001-06-29 (the release date) may see the 2000 value, matching
    the pattern established by the monthly/quarterly tests above.
    """
    monkeypatch.setattr(
        backtester,
        "_load_lag_registry",
        lambda: {"ANNUAL": 180},
    )

    annual = pd.Series(
        {
            pd.Timestamp("1999-12-31"): 100.0,
            pd.Timestamp("2000-12-31"): 110.0,
        },
        name="ANNUAL",
    )

    strat = CaptureStrategy()
    returns = _flat_returns("2001-01-02", "2001-08-31")
    # W-THU lands directly on 2001-03-01 and on 2001-07-05 (the first
    # Thursday after the 2001-06-29 release date).
    run_backtest(
        strat, returns,
        indicator_data={"ANNUAL": annual},
        start="2001-01-02",
        rebalance_freq="W-THU",
    )

    before = _find_observation_for(strat.observations, pd.Timestamp("2001-03-01"))
    assert before is not None, "no rebalance observed at 2001-03-01"
    assert pd.Timestamp("2000-12-31") not in before["ANNUAL"].index, (
        "2000 year-end value must be hidden at 2001-03-01 (timestamp "
        "2000-12-31 + 180 days = 2001-06-29, after rebalance)."
    )
    assert pd.Timestamp("1999-12-31") in before["ANNUAL"].index, (
        "1999 year-end value should be visible (timestamp 1999-12-31 + 180 "
        "days = 2000-06-28, well before 2001-03-01)."
    )

    # After 2001-06-29, the 2000 value MAY be visible. 2001-07-05 is the
    # first W-THU rebalance past the release date.
    after_release = _find_observation_for(
        strat.observations, pd.Timestamp("2001-07-05")
    )
    assert after_release is not None, "no rebalance observed at 2001-07-05"
    assert pd.Timestamp("2000-12-31") in after_release["ANNUAL"].index, (
        "2000 year-end value MAY be visible at 2001-07-05 (after the "
        "2001-06-29 release date)."
    )


@pytest.mark.unit
@pytest.mark.spec
def test_monthly_cpi_lag_14_hides_march_value_before_release(monkeypatch):
    """Spec: "Given a monthly CPI series with lag 14 and a value timestamped
    2020-03-01, a strategy rebalancing on 2020-03-10 must NOT see the March
    value; a strategy rebalancing on 2020-03-16 MAY see it."

    See specs/backtester.md § "Core invariant: walk-forward constraint →
    Test cases".
    """
    # Force a deterministic registry entry for the synthetic CPI key.
    monkeypatch.setattr(
        backtester,
        "_load_lag_registry",
        lambda: {"CPIAUCSL": 14},
    )

    cpi = pd.Series(
        {
            pd.Timestamp("2020-01-01"): 100.0,
            pd.Timestamp("2020-02-01"): 101.0,
            pd.Timestamp("2020-03-01"): 102.0,
        },
        name="CPIAUCSL",
    )

    # Rebalance on 2020-03-10 — March 1 value's release date is
    # 2020-03-15, after 2020-03-10. March must be hidden.
    strat = CaptureStrategy()
    returns = _flat_returns("2020-01-02", "2020-03-31")
    # Rebalance weekly so we can target specific Fridays.
    run_backtest(
        strat, returns,
        indicator_data={"CPIAUCSL": cpi},
        start="2020-01-02",
        rebalance_freq="W-TUE",
    )

    march_10 = pd.Timestamp("2020-03-10")
    obs = _find_observation_for(strat.observations, march_10)
    assert obs is not None, f"no rebalance observed at {march_10}"
    visible = obs["CPIAUCSL"].index
    assert pd.Timestamp("2020-03-01") not in visible, (
        "March value must be hidden at 2020-03-10 (lag 14 => cutoff 2020-02-25)"
    )
    assert pd.Timestamp("2020-02-01") in visible

    # Now rebalance on 2020-03-17 — March 1 + 14 days = March 15, so
    # March IS released by then and MAY be visible.
    strat2 = CaptureStrategy()
    run_backtest(
        strat2, returns,
        indicator_data={"CPIAUCSL": cpi},
        start="2020-01-02",
        rebalance_freq="W-TUE",
    )
    march_17 = pd.Timestamp("2020-03-17")
    obs_late = _find_observation_for(strat2.observations, march_17)
    assert obs_late is not None, f"no rebalance observed at {march_17}"
    assert pd.Timestamp("2020-03-01") in obs_late["CPIAUCSL"].index, (
        "March value must be visible at 2020-03-17 (lag 14 => cutoff 2020-03-03)"
    )


@pytest.mark.unit
@pytest.mark.spec
def test_quarterly_lag_45_hides_q1_value_before_release(monkeypatch):
    """Spec: "Given a quarterly GDP series with lag 45 and a value timestamped
    2020-01-01 (= Q1 reference date), a strategy rebalancing on 2020-02-10
    must NOT see the Q1 value; a strategy rebalancing on 2020-02-20 MAY see it."

    See specs/backtester.md § "Core invariant: walk-forward constraint →
    Test cases".
    """
    # Note: spec example uses lag 45 for a quarterly series with reference
    # timestamp 2020-01-01. 2020-01-01 + 45 days = 2020-02-15. So a
    # rebalance on 2020-02-10 must hide it; a rebalance on 2020-02-20 may
    # see it.
    monkeypatch.setattr(
        backtester,
        "_load_lag_registry",
        lambda: {"GDPC1": 45},
    )

    gdp = pd.Series(
        {
            pd.Timestamp("2019-10-01"): 19000.0,
            pd.Timestamp("2020-01-01"): 19100.0,
        },
        name="GDPC1",
    )
    returns = _flat_returns("2020-01-02", "2020-03-31")

    # Rebalance weekly to land on both 2020-02-10 and 2020-02-24.
    strat = CaptureStrategy()
    run_backtest(
        strat, returns,
        indicator_data={"GDPC1": gdp},
        start="2020-01-02",
        rebalance_freq="W-MON",
    )

    before = _find_observation_for(strat.observations, pd.Timestamp("2020-02-10"))
    assert before is not None
    assert pd.Timestamp("2020-01-01") not in before["GDPC1"].index, (
        "Q1 value must be hidden at 2020-02-10 (lag 45 => cutoff 2019-12-27)"
    )

    # The spec example names 2020-02-20 as the "MAY see it" date. We assert
    # against 2020-02-24 because the backtest rebalance grid here is W-MON;
    # both dates sit after the 2020-02-15 release, so either satisfies the
    # spec's "MAY see" clause — 2020-02-24 is simply the W-MON rebalance
    # that lands closest to (and after) the spec example date.
    after = _find_observation_for(strat.observations, pd.Timestamp("2020-02-24"))
    assert after is not None
    assert pd.Timestamp("2020-01-01") in after["GDPC1"].index, (
        "Q1 value MAY be visible at 2020-02-24 (lag 45 => cutoff 2020-01-10)"
    )


@pytest.mark.unit
@pytest.mark.spec
def test_series_without_declared_lag_uses_frequency_default(tmp_path, monkeypatch):
    """Spec: "A series with no declared lag and ``frequency: quarterly`` is
    truncated with the 45-day default."

    See specs/backtester.md § "Core invariant: walk-forward constraint →
    Test cases" and § "Default lags by frequency".
    """
    # Build a temporary registry with a quarterly series that has NO
    # explicit publication_lag_days — the framework must fall back to
    # DEFAULT_LAG_BY_FREQUENCY["quarterly"] == 45.
    registry_yaml = dedent(
        """\
        fred:
          TEST_QUARTERLY:
            name: Synthetic Quarterly Series
            category: test
            frequency: quarterly
            description: Test series with no declared publication_lag_days
        """
    )
    path = tmp_path / "series.yaml"
    path.write_text(registry_yaml)

    monkeypatch.setattr(backtester, "_US_REGISTRY_PATH", path)
    monkeypatch.setattr(backtester, "_UK_REGISTRY_PATH", tmp_path / "series_uk.yaml")
    _load_lag_registry.cache_clear()

    assert _resolve_publication_lag("TEST_QUARTERLY") == 45
    assert DEFAULT_LAG_BY_FREQUENCY["quarterly"] == 45


@pytest.mark.unit
@pytest.mark.spec
def test_declared_zero_lag_broadens_available_data_monotonically(monkeypatch):
    """Spec: "Changing the registry to declare a lag of 0 on the same series
    produces a strictly broader ``available_data`` at every rebalance."
    (Monotonicity check relative to the quarterly default of 45.)

    See specs/backtester.md § "Core invariant: walk-forward constraint →
    Test cases".
    """
    # Daily series is easiest to reason about: lag 0 vs lag 45 gives 45
    # additional days of visibility at every rebalance.
    daily_idx = pd.date_range("2020-01-01", "2020-12-31", freq="D")
    series = pd.Series(np.arange(len(daily_idx)), index=daily_idx, name="TEST")
    returns = _flat_returns("2020-01-02", "2020-12-31")

    # Run #1: quarterly default (45-day lag).
    monkeypatch.setattr(backtester, "_load_lag_registry", lambda: {"TEST": 45})
    strat_default = CaptureStrategy()
    run_backtest(
        strat_default, returns,
        indicator_data={"TEST": series},
        start="2020-01-02",
        rebalance_freq="ME",
    )

    # Run #2: explicit zero lag.
    monkeypatch.setattr(backtester, "_load_lag_registry", lambda: {"TEST": 0})
    strat_zero = CaptureStrategy()
    run_backtest(
        strat_zero, returns,
        indicator_data={"TEST": series},
        start="2020-01-02",
        rebalance_freq="ME",
    )

    # At every rebalance, the zero-lag view must be a strict superset of
    # the default-lag view.
    assert len(strat_default.observations) == len(strat_zero.observations)
    any_strict_superset = False
    for obs_default, obs_zero in zip(
        strat_default.observations, strat_zero.observations
    ):
        default_idx = obs_default["TEST"].index
        zero_idx = obs_zero["TEST"].index
        # Superset:
        assert set(default_idx).issubset(set(zero_idx)), (
            f"zero-lag view is not a superset at "
            f"{obs_default['__rebalance_date__']}"
        )
        if len(zero_idx) > len(default_idx):
            any_strict_superset = True

    assert any_strict_superset, (
        "expected zero-lag run to be strictly broader at at least one rebalance"
    )


# ---------------------------------------------------------------------------
# Additional invariants — not bullets in the spec's test-cases list, but
# follow from the contract and guard against regression.
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.spec
def test_unknown_series_gets_conservative_fallback_lag(monkeypatch):
    """Spec: "silent zero-lag is forbidden". A series not in the registry
    must receive the conservative fallback lag, not 0.

    See specs/backtester.md § "Framework-level enforcement" and
    specs/data_pipeline/us.md § "Invariants (walk-forward)".
    """
    monkeypatch.setattr(backtester, "_load_lag_registry", lambda: {})
    # Unknown series: resolver must return the fallback default, which
    # equals the annual-frequency default (most conservative).
    assert (
        _resolve_publication_lag("NOT_IN_REGISTRY")
        == backtester.UNKNOWN_SERIES_DEFAULT_LAG_DAYS
    )
    assert (
        backtester.UNKNOWN_SERIES_DEFAULT_LAG_DAYS
        == DEFAULT_LAG_BY_FREQUENCY["annual"]
    )


@pytest.mark.unit
@pytest.mark.spec
def test_real_registry_declares_expected_explicit_lags():
    """Spec: ``configs/series.yaml`` declares explicit lags for CPIAUCSL (14)
    and GDPC1 (30), the two worked examples called out in
    specs/backtester.md § "Default lags by frequency" and § "Test cases".
    """
    # Read the real registry (no monkeypatch here).
    _load_lag_registry.cache_clear()
    registry = _load_lag_registry()

    assert registry.get("CPIAUCSL") == 14, (
        "CPIAUCSL must declare publication_lag_days: 14 per "
        "configs/series.yaml and specs/backtester.md § 'Default lags by frequency'"
    )
    assert registry.get("GDPC1") == 30, (
        "GDPC1 must declare publication_lag_days: 30 per "
        "configs/series.yaml and specs/backtester.md § 'Default lags by frequency'"
    )
    # FEDFUNDS has no explicit lag; falls back to monthly default (30).
    assert registry.get("FEDFUNDS") == DEFAULT_LAG_BY_FREQUENCY["monthly"]
    # T10Y2Y is daily; default daily lag (1).
    assert registry.get("T10Y2Y") == DEFAULT_LAG_BY_FREQUENCY["daily"]
    # GFDEGDQ188S is quarterly, no explicit lag; default quarterly lag (45).
    assert registry.get("GFDEGDQ188S") == DEFAULT_LAG_BY_FREQUENCY["quarterly"]

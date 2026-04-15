"""Tests for src.data_fetcher_uk — BoE millennium-dataset loader."""

from pathlib import Path

import pandas as pd
import pytest

from src.data_fetcher_uk import (
    WORKBOOK_PATH,
    load_config,
    load_series,
    _ensure_workbook_exists,
)


REPO_ROOT = Path(__file__).parent.parent


@pytest.mark.unit
def test_config_loads():
    """YAML registry must parse and contain the expected core series."""
    cfg = load_config()
    assert "boe" in cfg
    boe = cfg["boe"]
    required = {
        "uk_public_debt_gdp",
        "uk_public_deficit_gdp",
        "uk_bank_rate",
        "uk_cpi",
        "uk_cpi_inflation",
        "uk_consols_yield",
        "uk_share_prices",
        "uk_usd_gbp_rate",
        "uk_agricultural_land",
        "uk_real_gdp",
        "uk_unemployment_rate",
        "uk_current_account_gdp",
    }
    missing = required - set(boe.keys())
    assert not missing, f"missing registry entries: {missing}"


@pytest.mark.unit
def test_unavailable_series_documented():
    """Series we couldn't find in the BoE workbook must be marked unavailable."""
    cfg = load_config()["boe"]
    assert cfg["sterling_reserve_share"]["status"] == "unavailable"
    assert cfg["gold_price_gbp"]["status"] == "unavailable"


@pytest.mark.unit
def test_missing_workbook_raises_clear_error(tmp_path, monkeypatch):
    """If the workbook isn't cached, fetchers should raise a clear, actionable error."""
    # Point WORKBOOK_PATH at a nonexistent file
    fake_path = tmp_path / "does_not_exist.xlsx"
    monkeypatch.setattr("src.data_fetcher_uk.WORKBOOK_PATH", fake_path)
    with pytest.raises(FileNotFoundError) as exc_info:
        _ensure_workbook_exists()
    msg = str(exc_info.value)
    assert "issue #52" in msg or "coordinator" in msg
    assert "bankofengland" in msg.lower()


@pytest.mark.integration
def test_workbook_exists():
    """The cached workbook must be present for integration tests to run."""
    assert WORKBOOK_PATH.exists(), (
        f"BoE workbook not cached at {WORKBOOK_PATH}. "
        "Integration tests require the pinned file."
    )


@pytest.mark.integration
def test_load_series_roundtrip():
    """Smoke test: series must load from parquet and cover the transition window."""
    # This test depends on scripts/fetch_uk_data.py having been run
    manifest_path = REPO_ROOT / "data" / "manifest_uk.json"
    if not manifest_path.exists():
        pytest.skip("Run scripts/fetch_uk_data.py first")
    df = load_series("uk_public_debt_gdp")
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    years = df.index.year
    # Must span the sterling transition window
    assert years.min() <= 1914, f"starts too late: {years.min()}"
    assert years.max() >= 1976, f"ends too early: {years.max()}"
    # Debt/GDP should have a plausible WW2 peak (>200%)
    peak = df.iloc[:, 0].loc["1940":"1950"].max()
    assert peak > 200, f"WW2 peak unexpectedly low: {peak}"

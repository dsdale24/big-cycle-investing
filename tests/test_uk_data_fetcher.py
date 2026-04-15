"""Spec-anchored tests for the UK data pipeline.

Each test case in this file maps to a numbered case in specs/data_pipeline/uk.md
§"Test cases (spec-anchored)". See docstrings for the mapping.
"""

from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest
import yaml

from src import data_fetcher_uk
from src.data_fetcher_uk import (
    CONFIG_PATH,
    DATA_DIR,
    MANIFEST_PATH,
    VERSION_PATH,
    WORKBOOK_PATH,
    fetch_all,
    fetch_uk_series,
    load_config,
    verify_source,
)


# ---------------------------------------------------------------------------
# Test case 1: workbook-missing raises clearly (unit + spec)
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.spec
def test_workbook_missing_raises_with_spec_reference(tmp_path):
    """specs/data_pipeline/uk.md test case 1: pointing the fetcher at a
    non-existent workbook must raise an error whose message references this
    spec and issue #52, not bare FileNotFoundError."""
    missing = tmp_path / "not_here.xlsx"
    version = tmp_path / "VERSION.txt"
    version.write_text("v3.1\n")

    with pytest.raises(FileNotFoundError) as excinfo:
        verify_source(
            workbook_path=missing,
            version_path=version,
            supported_versions={"v3.1"},
        )
    message = str(excinfo.value)
    assert "specs/data_pipeline/uk.md" in message
    assert "#52" in message


# ---------------------------------------------------------------------------
# Test case 2: VERSION.txt missing or unsupported (unit + spec, parametrized)
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.spec
def test_version_file_missing_raises(tmp_path):
    """specs/data_pipeline/uk.md test case 2 (part a): VERSION.txt absent → raise
    with message pointing to the spec's version-pinning section."""
    workbook = tmp_path / "millennium.xlsx"
    workbook.write_bytes(b"")
    version = tmp_path / "VERSION.txt"
    # Deliberately do not create it.

    with pytest.raises(FileNotFoundError) as excinfo:
        verify_source(
            workbook_path=workbook,
            version_path=version,
            supported_versions={"v3.1"},
        )
    assert "VERSION.txt" in str(excinfo.value)
    assert "specs/data_pipeline/uk.md" in str(excinfo.value)


@pytest.mark.unit
@pytest.mark.spec
def test_version_file_unsupported_raises(tmp_path):
    """specs/data_pipeline/uk.md test case 2 (part b): VERSION.txt present with an
    unrecognized version string → raise naming the inferred version and the
    supported-version list."""
    workbook = tmp_path / "millennium.xlsx"
    workbook.write_bytes(b"")
    version = tmp_path / "VERSION.txt"
    version.write_text("v99.9\n")

    with pytest.raises(ValueError) as excinfo:
        verify_source(
            workbook_path=workbook,
            version_path=version,
            supported_versions={"v3.1"},
        )
    message = str(excinfo.value)
    assert "v99.9" in message
    assert "v3.1" in message


# ---------------------------------------------------------------------------
# Test case 3: registry field-completeness (unit + spec)
# ---------------------------------------------------------------------------


_ALLOWED_CATEGORIES = {
    "fiscal",
    "monetary",
    "rates",
    "asset_price",
    "real_asset",
    "macro",
    "reserve_status",
}

_REQUIRED_TARGETS = {
    # Fiscal
    "uk_public_debt_gdp",
    "uk_public_deficit_gdp",
    "uk_public_receipts_gdp",
    # Monetary
    "uk_bank_rate",
    "uk_cpi_inflation",
    "uk_broad_money",
    # Rates
    "uk_10yr_gilt",
    "uk_short_rate",
    # Financial assets
    "uk_share_prices",
    "uk_gold_gbp",
    "uk_gbp_usd",
    # Real assets
    "uk_agricultural_land",
    "uk_commodity_index",
    # Macro
    "uk_real_gdp_growth",
    "uk_unemployment_rate",
    "uk_current_account_gdp",
    # Reserve status
    "uk_sterling_reserve_share",
}


@pytest.mark.unit
@pytest.mark.spec
def test_registry_field_completeness():
    """specs/data_pipeline/uk.md test case 3: every available series has
    source_sheet, source_column, start_year, end_year, publication_lag_days;
    every unavailable series has unavailable_reason and unavailable_followup_issue.
    Also enforces the §"Required target-series coverage" list (17 series) and
    the category enum."""
    config = load_config()
    registry = config.get("uk", {})

    missing = _REQUIRED_TARGETS - set(registry)
    assert not missing, f"Registry missing required target series: {sorted(missing)}"

    for name, meta in registry.items():
        status = meta.get("status")
        assert status in {"available", "unavailable"}, (
            f"{name}: status must be 'available' or 'unavailable', got {status!r}"
        )
        for field in ("name", "category", "frequency", "description"):
            assert meta.get(field), f"{name}: missing required field {field!r}"
        assert meta["category"] in _ALLOWED_CATEGORIES, (
            f"{name}: category {meta['category']!r} not in {sorted(_ALLOWED_CATEGORIES)}"
        )
        assert meta["frequency"] == "annual", (
            f"{name}: Phase A requires frequency=annual; got {meta['frequency']!r}"
        )

        if status == "available":
            for field in (
                "source_sheet",
                "source_column",
                "start_year",
                "end_year",
                "publication_lag_days",
            ):
                assert field in meta and meta[field] is not None, (
                    f"{name}: available series missing required field {field!r}"
                )
        else:
            for field in ("unavailable_reason", "unavailable_followup_issue"):
                assert meta.get(field), (
                    f"{name}: unavailable series missing required field {field!r}"
                )


# ---------------------------------------------------------------------------
# Test case 6: per-series failure does not abort the full fetch (unit + spec)
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.spec
def test_per_series_failure_does_not_abort(tmp_path, monkeypatch):
    """specs/data_pipeline/uk.md test case 6: a sheet-read failure on one series
    must not abort the full fetch; the failing series is recorded in the manifest
    and other series complete normally."""
    workbook = tmp_path / "millennium.xlsx"
    workbook.write_bytes(b"")
    version = tmp_path / "VERSION.txt"
    version.write_text("v3.1\n")

    config_path = tmp_path / "series_uk.yaml"
    fake_registry = {
        "uk": {
            "uk_alpha": {
                "name": "Alpha",
                "category": "fiscal",
                "frequency": "annual",
                "description": "synthetic",
                "status": "available",
                "source_sheet": "A1",
                "source_column": "alpha",
                "source_header_row": 3,
                "source_year_start_row": 7,
                "start_year": 1900,
                "end_year": 2016,
                "publication_lag_days": 0,
            },
            "uk_beta": {
                "name": "Beta",
                "category": "monetary",
                "frequency": "annual",
                "description": "synthetic",
                "status": "available",
                "source_sheet": "A1",
                "source_column": "beta",
                "source_header_row": 3,
                "source_year_start_row": 7,
                "start_year": 1900,
                "end_year": 2016,
                "publication_lag_days": 0,
            },
            "uk_gamma": {
                "name": "Gamma — unavailable",
                "category": "reserve_status",
                "frequency": "annual",
                "description": "synthetic unavailable",
                "status": "unavailable",
                "unavailable_reason": "synthetic",
                "unavailable_followup_issue": 999,
            },
        }
    }
    config_path.write_text(yaml.safe_dump(fake_registry))

    idx = pd.to_datetime([f"{y}-12-31" for y in range(1900, 1905)])
    idx.name = "date"
    good_series = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0], index=idx, name="uk_alpha")

    def fake_fetch(series_name, meta, workbook_path):
        if series_name == "uk_alpha":
            return good_series.rename(series_name)
        raise KeyError(f"forced failure for {series_name}")

    monkeypatch.setattr(data_fetcher_uk, "fetch_uk_series", fake_fetch)

    out_dir = tmp_path / "out"
    manifest_path = tmp_path / "manifest_uk.json"

    manifest = fetch_all(
        config_path=config_path,
        workbook_path=workbook,
        version_path=version,
        out_dir=out_dir,
        manifest_path=manifest_path,
        supported_versions={"v3.1"},
    )

    assert manifest["workbook_version"] == "v3.1"
    series = manifest["series"]
    assert set(series) == {"uk_alpha", "uk_beta", "uk_gamma"}
    assert series["uk_alpha"]["status"] == "available"
    assert series["uk_alpha"]["rows"] == 5
    assert "error" not in series["uk_alpha"]
    assert "error" in series["uk_beta"]
    assert "forced failure" in series["uk_beta"]["error"]
    assert series["uk_gamma"]["status"] == "unavailable"
    assert series["uk_gamma"]["unavailable_followup_issue"] == 999
    assert manifest_path.exists()
    assert (out_dir / "uk_alpha.parquet").exists()
    assert not (out_dir / "uk_beta.parquet").exists()


# ---------------------------------------------------------------------------
# Test case 4: output parquet has DatetimeIndex named "date" (integration + spec)
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.spec
def test_output_parquet_datetime_index_named_date(require_cache, tmp_path):
    """specs/data_pipeline/uk.md test case 4: every output parquet has a
    DatetimeIndex named 'date' (inherited from the US baseline). Integration
    test requiring the cached BoE workbook."""
    if not WORKBOOK_PATH.exists() or not VERSION_PATH.exists():
        pytest.skip("BoE workbook or VERSION.txt not cached; see specs/data_pipeline/uk.md")

    config = load_config()
    available = {
        name: meta
        for name, meta in config.get("uk", {}).items()
        if meta.get("status") == "available"
    }
    # Fetch just a couple of available series to keep the integration test fast.
    sample_names = list(available)[:2]
    assert sample_names, "registry has no available series to sanity-check"

    out_dir = tmp_path / "out"
    out_dir.mkdir()
    for name in sample_names:
        series = fetch_uk_series(name, available[name], workbook_path=WORKBOOK_PATH)
        assert isinstance(series.index, pd.DatetimeIndex), (
            f"{name}: expected DatetimeIndex, got {type(series.index).__name__}"
        )
        assert series.index.name == "date", (
            f"{name}: index name must be 'date', got {series.index.name!r}"
        )
        assert series.index.is_monotonic_increasing
        # Write + re-read to verify the parquet round-trips the invariant.
        from src.data_fetcher_uk import save_series

        path = save_series(series, name, out_dir=out_dir)
        loaded = pd.read_parquet(path)
        assert isinstance(loaded.index, pd.DatetimeIndex)
        assert loaded.index.name == "date"


# ---------------------------------------------------------------------------
# Test case 5: manifest captures per-series status truthfully (integration + spec)
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.spec
def test_manifest_matches_registry_status(require_cache, tmp_path):
    """specs/data_pipeline/uk.md test case 5: after a full fetch, the manifest's
    available / unavailable / error counts match the registry. Integration test
    requiring the cached BoE workbook."""
    if not WORKBOOK_PATH.exists() or not VERSION_PATH.exists():
        pytest.skip("BoE workbook or VERSION.txt not cached; see specs/data_pipeline/uk.md")

    out_dir = tmp_path / "out"
    manifest_path = tmp_path / "manifest_uk.json"

    manifest = fetch_all(
        config_path=CONFIG_PATH,
        workbook_path=WORKBOOK_PATH,
        version_path=VERSION_PATH,
        out_dir=out_dir,
        manifest_path=manifest_path,
    )

    config = load_config()
    registry = config.get("uk", {})

    registry_available = {n for n, m in registry.items() if m.get("status") == "available"}
    registry_unavailable = {n for n, m in registry.items() if m.get("status") == "unavailable"}

    manifest_series = manifest["series"]
    assert set(manifest_series) == set(registry)

    manifest_unavailable = {
        n for n, info in manifest_series.items() if info.get("status") == "unavailable"
    }
    assert manifest_unavailable == registry_unavailable

    for name in registry_available:
        entry = manifest_series[name]
        assert entry["status"] == "available"
        if "error" not in entry:
            assert entry["rows"] > 0
            assert "start" in entry and "end" in entry
            assert Path(entry["path"]).exists()

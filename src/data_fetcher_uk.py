"""Fetch and cache UK historical macro/financial data from the Bank of England's
"A Millennium of Macroeconomic Data" workbook (v3.1).

This module mirrors the conventions of ``src/data_fetcher.py`` but reads from a
**locally cached** Excel file rather than a live API. The workbook is pinned to
a single download (coordinator-managed) for reproducibility.

Source (human-facing reference, NOT fetched by this module):
    https://www.bankofengland.co.uk/statistics/research-datasets

Cached location (required):
    data/raw/uk/_source/millennium_of_macro_data.xlsx

The fetcher must **not** attempt to download the workbook. Subagents do not have
network access, and pinning the version avoids silent upstream changes. If the
workbook is missing, the fetcher raises an explicit error directing the user to
issue #52 / the coordinator to (re-)cache the file.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

REPO_ROOT = Path(__file__).parent.parent
DATA_DIR = REPO_ROOT / "data" / "raw" / "uk"
WORKBOOK_PATH = DATA_DIR / "_source" / "millennium_of_macro_data.xlsx"
CONFIG_PATH = REPO_ROOT / "configs" / "series_uk.yaml"

# A1. Headline series layout (verified 2026-04-15 against workbook v3.1):
#   row index 3 = description, 4 = worksheet of origin, 5 = units,
#   row index 7 onward = data rows, column 0 = year (integer).
A1_SHEET = "A1. Headline series"
A1_DATA_SKIPROWS = 7
A1_YEAR_COL = 0


@dataclass(frozen=True)
class SeriesSpec:
    """A single UK series definition."""

    series_id: str
    sheet: str
    # For A1 sheet we use column index; for other sheets, column name.
    column: int | str
    name: str
    units: str
    category: str
    frequency: str
    start_year: int | None
    publication_lag_days: int
    description: str
    notes: str | None = None
    splice_with: str | None = None
    status: str = "active"


def _ensure_workbook_exists() -> None:
    """Raise a clear error if the cached BoE workbook is missing."""
    if not WORKBOOK_PATH.exists():
        raise FileNotFoundError(
            "BoE 'A Millennium of Macroeconomic Data' workbook not found at\n"
            f"  {WORKBOOK_PATH}\n\n"
            "This fetcher does NOT download from the network (the workbook is "
            "version-pinned for reproducibility). Ask the coordinator to cache "
            "it, or see issue #52 for the download procedure. The upstream "
            "source is:\n"
            "  https://www.bankofengland.co.uk/statistics/research-datasets"
        )


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    """Load the UK series registry."""
    with open(path) as f:
        return yaml.safe_load(f)


def _read_a1_series(column: int) -> pd.Series:
    """Read a single column from the A1 Headline sheet, indexed by year-end date."""
    df = pd.read_excel(
        WORKBOOK_PATH,
        sheet_name=A1_SHEET,
        header=None,
        skiprows=A1_DATA_SKIPROWS,
    )
    years = pd.to_numeric(df.iloc[:, A1_YEAR_COL], errors="coerce")
    mask = years.notna()
    years = years[mask].astype(int)
    values = pd.to_numeric(df.iloc[:, column][mask], errors="coerce")
    index = pd.to_datetime(years.astype(str) + "-12-31")
    s = pd.Series(values.values, index=index, dtype="float64")
    s.index.name = "date"
    return s.dropna()


def _read_sheet_column(sheet: str, column: int | str, header_row: int) -> pd.Series:
    """Read a specific column from a non-A1 annual sheet, indexed by year-end date.

    Assumes column 0 (after header) holds the year as integer.
    """
    df = pd.read_excel(
        WORKBOOK_PATH, sheet_name=sheet, header=header_row
    )
    year_col = df.columns[0]
    years = pd.to_numeric(df[year_col], errors="coerce")
    mask = years.notna()
    years = years[mask].astype(int)
    if isinstance(column, int):
        col_values = df.iloc[:, column]
    else:
        col_values = df[column]
    values = pd.to_numeric(col_values[mask], errors="coerce")
    index = pd.to_datetime(years.astype(str) + "-12-31")
    s = pd.Series(values.values, index=index, dtype="float64")
    s.index.name = "date"
    return s.dropna()


def _parse_spec(series_id: str, meta: dict[str, Any]) -> SeriesSpec:
    return SeriesSpec(
        series_id=series_id,
        sheet=meta["sheet"],
        column=meta["column"],
        name=meta["name"],
        units=meta.get("units", ""),
        category=meta.get("category", ""),
        frequency=meta.get("frequency", "annual"),
        start_year=meta.get("start_year"),
        publication_lag_days=meta.get("publication_lag_days", 365),
        description=meta.get("description", ""),
        notes=meta.get("notes"),
        splice_with=meta.get("splice_with"),
        status=meta.get("status", "active"),
    )


def fetch_series(spec: SeriesSpec) -> pd.Series:
    """Fetch a single configured series from the cached workbook."""
    _ensure_workbook_exists()
    if spec.sheet == A1_SHEET and isinstance(spec.column, int):
        series = _read_a1_series(spec.column)
    else:
        header_row = 2  # BoE convention: row 2 (0-indexed) holds descriptions
        series = _read_sheet_column(spec.sheet, spec.column, header_row)
    series.name = spec.series_id
    if spec.start_year is not None:
        series = series[series.index.year >= spec.start_year]
    return series


def save_series(series: pd.Series, series_id: str) -> Path:
    """Save a series to parquet under ``data/raw/uk/``."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = series_id.replace("/", "_")
    path = DATA_DIR / f"{safe_name}.parquet"
    series.to_frame().to_parquet(path)
    return path


def fetch_all(config_path: Path = CONFIG_PATH) -> dict[str, dict[str, Any]]:
    """Fetch all active UK series and cache to disk. Returns a summary dict."""
    _ensure_workbook_exists()
    config = load_config(config_path)
    results: dict[str, dict[str, Any]] = {}
    for series_id, meta in config.get("boe", {}).items():
        spec = _parse_spec(series_id, meta)
        if spec.status != "active":
            results[series_id] = {
                "status": spec.status,
                "note": meta.get("note", "marked unavailable in config"),
            }
            print(f"  SKIP    {series_id}: {spec.status}")
            continue
        print(f"  BoE:    {series_id} ({spec.name})...", end=" ")
        try:
            series = fetch_series(spec)
            if series.empty:
                results[series_id] = {"error": "empty series after parsing"}
                print("FAILED: empty")
                continue
            path = save_series(series, series_id)
            results[series_id] = {
                "rows": len(series),
                "start": str(series.index.min().date()),
                "end": str(series.index.max().date()),
                "path": str(path),
                "sheet": spec.sheet,
                "column": spec.column,
                "units": spec.units,
            }
            print(f"OK ({len(series)} rows, {series.index.min().year}-{series.index.max().year})")
        except Exception as e:  # noqa: BLE001
            results[series_id] = {"error": str(e)}
            print(f"FAILED: {e}")
    return results


def load_series(series_id: str) -> pd.DataFrame:
    """Load a cached UK series from disk."""
    safe_name = series_id.replace("/", "_")
    path = DATA_DIR / f"{safe_name}.parquet"
    if not path.exists():
        raise FileNotFoundError(
            f"No cached UK data for {series_id} at {path}. "
            "Run scripts/fetch_uk_data.py first."
        )
    return pd.read_parquet(path)


def load_all() -> dict[str, pd.DataFrame]:
    """Load all cached UK series listed in the registry."""
    config = load_config()
    out: dict[str, pd.DataFrame] = {}
    for series_id, meta in config.get("boe", {}).items():
        if meta.get("status", "active") != "active":
            continue
        try:
            out[series_id] = load_series(series_id)
        except FileNotFoundError:
            continue
    return out

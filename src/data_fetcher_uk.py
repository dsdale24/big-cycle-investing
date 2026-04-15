"""Fetch UK macro/financial series from the BoE "Millennium of Macroeconomic Data" workbook.

Governed by specs/data_pipeline/uk.md. Extends the US baseline
(specs/data_pipeline/us.md) — parquet-per-series cache layout, manifest JSON
structure, DatetimeIndex named "date", and idempotent fetch are inherited
unchanged. Source is a single version-pinned cached workbook; no network fetch.
"""

import json
import re
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "raw" / "uk"
SOURCE_DIR = DATA_DIR / "_source"
WORKBOOK_PATH = SOURCE_DIR / "millennium_of_macro_data.xlsx"
VERSION_PATH = SOURCE_DIR / "VERSION.txt"
CONFIG_PATH = PROJECT_ROOT / "configs" / "series_uk.yaml"
MANIFEST_PATH = PROJECT_ROOT / "data" / "manifest_uk.json"

SUPPORTED_VERSIONS = {"v3.1"}

_MISSING_WORKBOOK_MESSAGE = (
    "UK source workbook not found at {path}. The BoE 'Millennium of Macroeconomic "
    "Data' workbook must be pre-cached by the coordinator — see "
    "specs/data_pipeline/uk.md §'Obtaining the workbook' and issue #52. "
    "Do not attempt a live download; the spec forbids network access for this source."
)

_MISSING_VERSION_MESSAGE = (
    "VERSION.txt sidecar missing at {path}. A version sidecar is required per "
    "specs/data_pipeline/uk.md §'Cache and version pinning'. Create it with the "
    "BoE-published version (e.g. 'v3.1') and the download date."
)

_UNSUPPORTED_VERSION_MESSAGE = (
    "VERSION.txt at {path} reports version {version!r}, which is not in the "
    "supported-version list {supported}. A BoE release upgrade is a breaking "
    "event; update specs/data_pipeline/uk.md with a version-migration section "
    "before bumping the supported list."
)


def _safe_series_name(series_name: str) -> str:
    """Mirror the US pipeline's filename sanitization; conservative for YAML keys."""
    return re.sub(r"[^0-9A-Za-z_-]", "_", series_name)


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    with open(path) as f:
        return yaml.safe_load(f)


def read_workbook_version(version_path: Path = VERSION_PATH) -> str:
    """Parse VERSION.txt, returning the first non-empty line (the version string).

    Raises FileNotFoundError if the sidecar is absent, with the spec-anchored
    error message demanded by test case 2.
    """
    if not version_path.exists():
        raise FileNotFoundError(_MISSING_VERSION_MESSAGE.format(path=version_path))
    for line in version_path.read_text().splitlines():
        line = line.strip()
        if line:
            return line.split()[0]
    raise ValueError(_MISSING_VERSION_MESSAGE.format(path=version_path))


def verify_source(
    workbook_path: Path = WORKBOOK_PATH,
    version_path: Path = VERSION_PATH,
    supported_versions: set[str] = SUPPORTED_VERSIONS,
) -> str:
    """Verify workbook cache and VERSION.txt. Returns the verified version string.

    Raises:
        FileNotFoundError if the workbook is missing (references spec and #52).
        FileNotFoundError if VERSION.txt is missing.
        ValueError if VERSION.txt reports an unsupported version.
    """
    if not workbook_path.exists():
        raise FileNotFoundError(_MISSING_WORKBOOK_MESSAGE.format(path=workbook_path))
    version = read_workbook_version(version_path)
    if version not in supported_versions:
        raise ValueError(
            _UNSUPPORTED_VERSION_MESSAGE.format(
                path=version_path,
                version=version,
                supported=sorted(supported_versions),
            )
        )
    return version


def _locate_column(
    raw: pd.DataFrame,
    header_row: int,
    source_column: str,
    units_row: int | None = None,
    source_column_units: str | None = None,
) -> int:
    """Find the column index whose Description (and optionally Units) cells match.

    Description cells in BoE headline sheets are sparse (merged across adjacent
    columns); units_row + source_column_units disambiguates shared descriptions
    (e.g., Bank Rate end-period vs Bank Rate year-average).
    """
    ncols = raw.shape[1]
    last_description: str | None = None
    candidates: list[int] = []
    for c in range(ncols):
        val = raw.iat[header_row, c]
        if pd.notna(val):
            last_description = str(val)
        if last_description is not None and last_description.strip() == source_column.strip():
            if source_column_units is None or units_row is None:
                candidates.append(c)
            else:
                unit_val = raw.iat[units_row, c]
                if pd.notna(unit_val) and str(unit_val).strip() == source_column_units.strip():
                    candidates.append(c)
    if not candidates:
        descriptor = source_column
        if source_column_units:
            descriptor = f"{source_column!r} with units {source_column_units!r}"
        raise KeyError(
            f"Column not found in sheet: {descriptor}. "
            "Check source_sheet/source_column in configs/series_uk.yaml against the workbook."
        )
    return candidates[0]


def _extract_series(raw: pd.DataFrame, year_start_row: int, col_idx: int) -> pd.Series:
    """Slice the year column (col 0) and value column; return a date-indexed Series."""
    years = raw.iloc[year_start_row:, 0]
    values = raw.iloc[year_start_row:, col_idx]
    years_numeric = pd.to_numeric(years, errors="coerce")
    values_numeric = pd.to_numeric(values, errors="coerce")
    mask = years_numeric.notna() & values_numeric.notna()
    years_clean = years_numeric[mask].astype(int)
    values_clean = values_numeric[mask].astype(float)
    index = pd.to_datetime(years_clean.astype(str) + "-12-31")
    index.name = "date"
    series = pd.Series(values_clean.to_numpy(), index=index)
    return series


def fetch_uk_series(
    series_name: str,
    meta: dict[str, Any],
    workbook_path: Path = WORKBOOK_PATH,
) -> pd.Series:
    """Fetch a single UK series per its registry entry.

    Invariants from specs/data_pipeline/uk.md §"Fetching → Invariants":
      - DatetimeIndex named "date"
      - Annual frequency (one row per calendar year)
      - No imputation or forward-fill across missing years
    """
    sheet = meta["source_sheet"]
    column = meta["source_column"]
    header_row = int(meta["source_header_row"])
    year_start_row = int(meta["source_year_start_row"])
    units_row = meta.get("source_units_row")
    column_units = meta.get("source_column_units")

    raw = pd.read_excel(workbook_path, sheet_name=sheet, header=None)
    col_idx = _locate_column(
        raw,
        header_row=header_row,
        source_column=column,
        units_row=int(units_row) if units_row is not None else None,
        source_column_units=column_units,
    )
    series = _extract_series(raw, year_start_row=year_start_row, col_idx=col_idx)
    series.name = series_name
    return series


def save_series(series: pd.Series, series_name: str, out_dir: Path = DATA_DIR) -> Path:
    """Write a series to parquet at data/raw/uk/{series_name}.parquet."""
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{_safe_series_name(series_name)}.parquet"
    series.to_frame().to_parquet(path)
    return path


def fetch_all(
    config_path: Path = CONFIG_PATH,
    workbook_path: Path = WORKBOOK_PATH,
    version_path: Path = VERSION_PATH,
    out_dir: Path = DATA_DIR,
    manifest_path: Path = MANIFEST_PATH,
    supported_versions: set[str] = SUPPORTED_VERSIONS,
) -> dict[str, Any]:
    """Fetch every registered UK series. Returns the manifest dict.

    Error behavior (specs/data_pipeline/uk.md §"Error behavior"):
      - Missing workbook or unsupported VERSION.txt raises before any fetch.
      - Per-series failures (missing sheet, missing column) land in the manifest
        and do not abort the remaining fetches.
    """
    version = verify_source(
        workbook_path=workbook_path,
        version_path=version_path,
        supported_versions=supported_versions,
    )

    config = load_config(config_path)
    registry = config.get("uk", {}) or {}

    manifest: dict[str, Any] = {
        "workbook_version": version,
        "workbook_path": str(workbook_path),
        "series": {},
    }

    for series_name, meta in registry.items():
        status = meta.get("status")
        entry: dict[str, Any] = {"status": status}
        if status == "unavailable":
            entry["unavailable_reason"] = meta.get("unavailable_reason")
            entry["unavailable_followup_issue"] = meta.get("unavailable_followup_issue")
            manifest["series"][series_name] = entry
            print(f"  SKIP    {series_name}: unavailable (#{entry['unavailable_followup_issue']})")
            continue
        try:
            series = fetch_uk_series(series_name, meta, workbook_path=workbook_path)
            path = save_series(series, series_name, out_dir=out_dir)
            entry.update(
                {
                    "rows": int(len(series)),
                    "start": str(series.index.min().date()),
                    "end": str(series.index.max().date()),
                    "path": str(path),
                }
            )
            print(f"  OK      {series_name}: {entry['start']} → {entry['end']} ({entry['rows']} rows)")
        except Exception as exc:
            entry["error"] = f"{type(exc).__name__}: {exc}"
            print(f"  FAILED  {series_name}: {entry['error']}")
        manifest["series"][series_name] = entry

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    return manifest


def load_uk_series(series_name: str, data_dir: Path = DATA_DIR) -> pd.DataFrame:
    """Load a cached UK series from parquet."""
    path = data_dir / f"{_safe_series_name(series_name)}.parquet"
    if not path.exists():
        raise FileNotFoundError(
            f"No cached UK data for {series_name} at {path}. "
            "Run scripts/fetch_uk_data.py to populate the cache."
        )
    return pd.read_parquet(path)


def load_all_uk(
    config_path: Path = CONFIG_PATH,
    data_dir: Path = DATA_DIR,
) -> dict[str, pd.DataFrame]:
    """Load every registered UK series that has a cached parquet."""
    config = load_config(config_path)
    registry = config.get("uk", {}) or {}
    result: dict[str, pd.DataFrame] = {}
    for series_name, meta in registry.items():
        if meta.get("status") != "available":
            continue
        try:
            result[series_name] = load_uk_series(series_name, data_dir=data_dir)
        except FileNotFoundError:
            pass
    return result

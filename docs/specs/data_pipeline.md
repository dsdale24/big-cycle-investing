# Data Pipeline Specification

Status: **Stabilizing**
Last updated: 2026-04-13

## Purpose

Fetch, cache, and serve historical macro/financial data from external sources.
Provide a consistent interface for the backtester and notebooks to load any
configured series by source and ID.

## Data sources

| Source | API | Auth | Rate limits |
|--------|-----|------|-------------|
| FRED | `fredapi` | API key (env: FRED_API_KEY) | ~120 requests/min |
| Yahoo Finance | `yfinance` | None | Unofficial, may throttle |

## Series registry (`configs/series.yaml`)

### Schema
```yaml
fred:
  SERIES_ID:
    name: Human-readable name
    category: one of the defined categories
    frequency: daily | weekly | monthly | quarterly | annual
    description: What this series measures
    start_override: "YYYY-MM-DD"  # optional, overrides default start
```

### Invariants
- Every series ID in the registry must be a valid ID for its source
- Every series must have `name`, `category`, and `description`
- `start_override` must be a valid ISO date string if present
- Yahoo Finance symbols with special characters (^, =, .) must be quoted

## Fetching

### Inputs
- Series registry (from YAML config)
- Start date (default: 1975-01-01)

### Process
1. For each FRED series: call `fred.get_series(id, observation_start=start)`
2. For each Yahoo series: call `yf.Ticker(symbol).history(start=start)`
3. Save each series to parquet at `data/raw/{source}/{safe_name}.parquet`
4. Write manifest to `data/manifest.json` with fetch results

### Outputs
- Parquet files on disk
- Manifest JSON with per-series: row count, date range, file path, or error

### Invariants
- File names are sanitized: `^` removed, `=` and `.` replaced with `_`
- All parquet files have a DatetimeIndex named "date"
- Yahoo Finance timestamps are tz-naive (localized to None)
- Fetching is idempotent: re-running overwrites with fresh data

### Error handling
- Individual series failures must not abort the full fetch
- Failed series are logged in the manifest with their error message
- FRED server errors (500) are transient — previously cached data remains valid

## Loading

### Interface
```python
def load_series(source: str, series_id: str) -> pd.DataFrame
def load_all_fred() -> dict[str, pd.DataFrame]
def load_all_yahoo() -> dict[str, pd.DataFrame]
```

### Invariants
- `load_series` raises `FileNotFoundError` if no cached data exists
- Returned DataFrames always have a DatetimeIndex
- FRED series are returned as single-column DataFrames (use `.squeeze()` for Series)
- Yahoo series are returned as multi-column DataFrames (OHLCV)

## Walk-forward data availability

For backtesting, the data pipeline must support answering: "What data was available
on date X?" This is currently handled by the backtester truncating data with
`data.loc[:date]`, which works for most series but does NOT account for:

- **Publication lag**: GDP is published ~1 month after quarter end. Annual data
  (Gini, life expectancy) may lag 6-12 months.
- **Revisions**: Many economic series are revised after initial publication.

### Current approach (acceptable for now)
- Assume all data is available on its timestamp date
- This introduces a small look-ahead bias for series with publication lag

### Future improvement
- Add `publication_lag_days` field to series registry
- When truncating for walk-forward, subtract the lag: `data.loc[:date - lag]`

---

## What this spec does NOT cover

- Which specific series to include (that's `docs/indicator_framework.md`)
- How to handle proxy splicing for pre-2000 data (that's the backtester's concern)
- Data quality validation beyond "did the fetch succeed"

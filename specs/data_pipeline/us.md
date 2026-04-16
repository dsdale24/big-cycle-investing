# Data Pipeline Specification

Status: **Stabilizing**
Last updated: 2026-04-16 (publication_lag_days formalized in the series registry — resolves the Future-improvement item; fixes #72)

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
    start_override: "YYYY-MM-DD"       # optional, overrides default start
    publication_lag_days: 14            # optional; integer days from reference
                                        # date to real-time release. Defaults
                                        # to the by-frequency table in
                                        # specs/backtester.md § "Default lags
                                        # by frequency" if omitted.
```

### Invariants
- Every series ID in the registry must be a valid ID for its source
- Every series must have `name`, `category`, and `description`
- `start_override` must be a valid ISO date string if present
- Yahoo Finance symbols with special characters (^, =, .) must be quoted
- `publication_lag_days`, when present, must be a non-negative integer

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

For backtesting, the data pipeline must support answering: "What data was
available on date X in real time?" Two distinct uncertainty classes bear on
this question, and this spec treats them separately:

1. **Publication lag** — a series value whose reference timestamp is D has
   a real-time release date of D + lag. The lag is a known property of the
   series (CPI ~14 days after reference month; BEA advance GDP ~30 days after
   quarter-end). **In scope.** See "Publication-lag contract" below.
2. **Revisions** — many economic series are revised after initial publication.
   The latest-snapshot stored in the parquet cache reflects the current
   revised value, not the value an analyst would have seen on the original
   release date. **Out of scope here**; tracked separately in #73 (ALFRED
   vintage-data path).

### Publication-lag contract

The `publication_lag_days` field on each series entry (see "Schema" above)
declares the integer-day lag from the series' reference timestamp to its
real-time release. If the field is omitted for a series, the backtester
framework uses a by-frequency default (see `specs/backtester.md` §
"Default lags by frequency").

**Who applies the lag.** The data pipeline itself does NOT apply lag-based
truncation at fetch or load time — the parquet cache stores each value at
its reference timestamp. Consumers that need real-time availability (the
backtester, primarily) apply the lag at read time, driven by the
per-series metadata. This keeps the cache canonical and shifts the
walk-forward contract into one place: the framework-level truncation
inside `run_backtest` (see `specs/backtester.md` § "Framework-level
enforcement").

Rationale for this split:
- The cache stays source-of-truth for the raw data and doesn't become
  dependent on a lag policy that may be revised as the project learns
  about release calendars.
- Non-backtesting consumers (notebooks, exploratory analysis) often want
  the latest available value regardless of a 1975-forward replay; baking
  lag into the cache would corrupt that view.
- Lag values can be refined over time (e.g., calendar-precise release
  dates replacing conservative integer-day estimates) without requiring
  a re-fetch.

### Invariants (walk-forward)

- Every series declared in `configs/series.yaml` must have a `frequency`
  that maps to a default lag, or an explicit `publication_lag_days` value
- The backtester framework MUST NOT pass any value to a strategy whose
  reference timestamp is after `rebalance_date − publication_lag_days`
- A change to a series' `publication_lag_days` is a walk-forward-contract
  change; backtest results before and after the change are not directly
  comparable on that series' contribution

### Known open refinements

- Calendar-precise release dates (e.g., BLS CPI release schedule) would
  sharpen lags currently given as conservative integers. Low priority;
  the integer approximation errs in the "miss a day" direction, not the
  "look ahead" direction.
- Vintage-data replay via ALFRED (#73) is the long-run right answer for
  both lag AND revision uncertainty; the current publication_lag_days
  approach is a scoped fix for lag only.

---

## What this spec does NOT cover

- Which specific series to include (that's `specs/indicator_framework.md`)
- How to handle proxy splicing for pre-2000 data (that's the backtester's concern)
- Data quality validation beyond "did the fetch succeed"

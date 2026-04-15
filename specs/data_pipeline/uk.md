# UK data pipeline specification (Phase A of issue #52)

Status: **Stabilizing**
Last updated: 2026-04-15
Depends on: [`us.md`](us.md) (US pipeline baseline — conventions inherited unless overridden here)
Related theses: [`specs/theses/changing-world-order/us-fiscal-deterioration.md`](../theses/changing-world-order/us-fiscal-deterioration.md), [`specs/theses/changing-world-order/backtest-sample-scope.md`](../theses/changing-world-order/backtest-sample-scope.md)
Related issues: #52 (parent — Phase A of cross-national data), #91 / #92 / #93 / #94 (known follow-up data gaps)

## Purpose

Fetch, cache, and serve UK macro/asset/real-asset series for Phase A of the cross-national big-cycle dataset. The UK 1900-1980 window covers the sterling → USD reserve-currency transition — the closest historical analog to the central project thesis's scenario ([`us-fiscal-deterioration.md`](../theses/changing-world-order/us-fiscal-deterioration.md)). This spec defines the pipeline that produces the underlying data; analytical notebooks and research notes consume it and live outside this spec's scope.

## Relationship to the US pipeline baseline

This spec extends [`us.md`](us.md). Conventions inherited unchanged:

- Parquet-per-series cache layout, one file per series
- YAML registry schema's required fields (`name`, `category`, `frequency`, `description`); extended below with cross-national-specific fields
- Manifest JSON structure (per-series: row count, date range, file path, or error)
- Individual-series-failure isolation (one bad sheet does not abort the whole fetch)
- Idempotent fetch (re-running overwrites with fresh reads from the same cached source)
- DatetimeIndex named `"date"` on all output parquet files
- Walk-forward availability principle: `publication_lag_days` metadata per series (used by the backtester for walk-forward truncation; not enforced in fetch itself)

Conventions overridden or added by this spec (the "deltas"):

- **Source is a single cached workbook, not a live API.** No network calls at fetch time.
- **Multi-sheet source.** Series are located by `(source_sheet, column)` rather than by a bare series ID.
- **Version-pinned source.** The workbook file name includes a version indicator; a version change requires a spec update.
- **Explicit-unavailable handling.** Target series that the source workbook does not contain are recorded with `status: unavailable` in the registry rather than omitted silently.

## Source

### The workbook

Primary source: **Bank of England "A Millennium of Macroeconomic Data" workbook**, version 3.1 (Thomas & Dimsdale, last updated 2017 as of this spec's writing). The workbook is ~26MB, ~109 sheets, and covers UK macro/financial/asset/population data with some series extending back to the 13th century and one or two benchmarks to 1086.

**Sheet naming convention** in the workbook:
- `A1`..`A66` — annual series
- `Q1`..`Q7` — quarterly series
- `M1`..`M15` — monthly series
- `W1`..`W2` — weekly (Bank of England issue/banking departments)
- `D1`..`D3` — daily (official rates, bilaterals, ERI vintages)
- Additional non-series sheets (Disclaimer, Front page, Corrections, Notes, Table of contents) are not fetched

Phase A of this pipeline targets **annual series** from the `A*` sheets. Monthly series extension is explicitly out of scope for this phase (see issue #94).

### Cache and version pinning

The workbook is pre-cached at `data/raw/uk/_source/millennium_of_macro_data.xlsx`. **No network fetch at any time.** This is the hard rule — see "Error behavior" below for what happens when the cache is missing.

**Version pinning.** The cached file SHOULD be referenced by its BoE-published version (v3.1 as of 2026-04-15). A new BoE release (e.g., v3.2, v4.0) is a breaking event for reproducibility:

1. A `VERSION.txt` or equivalent sidecar at `data/raw/uk/_source/VERSION.txt` MUST record the version of the currently-cached workbook (human-readable string like `v3.1` plus the date the BoE file was downloaded)
2. A version change requires a spec update (adding a "version migration" section to this spec with what changed between versions, any new target series, any series that moved sheets)
3. The fetcher MUST NOT silently accept a replaced workbook — if `VERSION.txt` is missing or absent, this is an error condition

### Obtaining the workbook

The coordinator (not the coding agent) is responsible for placing the workbook in the cache. Subagents do not have network access in this environment. The workbook can be downloaded from the BoE research-datasets page (curl with a standard browser user-agent succeeds where some automated tools fail; the coordinator's retrieval on 2026-04-15 used a browser-UA curl). The delegation prompt for implementation MUST state that the cache is pre-populated.

## Series registry (`configs/series_uk.yaml`)

### Schema (extension of US registry schema)

```yaml
uk:
  series_name:
    name: Human-readable name
    category: fiscal | monetary | rates | asset_price | real_asset | macro | reserve_status
    frequency: annual | quarterly | monthly | weekly | daily
    source_sheet: "A## Sheet name"      # exact BoE sheet name; required if status == available
    source_column: "column header"      # required if status == available
    start_year: NNNN                     # earliest observation in the Phase A target window
    end_year: NNNN                       # latest observation available
    publication_lag_days: N              # best estimate from literature; 0 for end-of-year-reported historical reconstructions
    description: What this series measures and what it's used for
    status: available | unavailable
    unavailable_reason: string           # required iff status == unavailable; cites why
    unavailable_followup_issue: N        # required iff status == unavailable; the # of the follow-up issue
    splice: string                        # optional; documents any splice (e.g., "Consols yield 1900-1929; 10y gilt 1929+")
```

### Required target-series coverage for Phase A

The pipeline MUST attempt to register these series (per the #52 Phase A issue description). If the BoE workbook does not contain a series under an obvious sheet name, the series MUST be registered with `status: unavailable` and the `unavailable_followup_issue` pointing to #91, #92, #93, or a new issue — not omitted:

**Fiscal:**
- Government debt/GDP
- Government deficit/GDP
- Tax revenue/GDP

**Monetary:**
- Bank Rate (official policy rate)
- CPI or RPI inflation
- Broad money aggregate (M3 or equivalent consistent long series)

**Rates:**
- 10-year gilt yield (or Consols + gilt splice with `splice` field populated)
- Short rate (T-bill or equivalent)

**Financial assets:**
- UK equity index (BoE consolidated long series)
- Gold price in GBP — currently expected `status: unavailable` for post-1971 per issue #93
- GBP/USD exchange rate

**Real assets:**
- UK land prices
- UK commodity price index

**Macro:**
- Real GDP growth
- Unemployment rate
- Current account / trade balance as % of GDP

**Reserve status:**
- Sterling share of global reserves — currently expected `status: unavailable` per issue #91

### Invariants

- Every series registered with `status: available` MUST have `source_sheet`, `source_column`, `start_year`, `end_year`, and `publication_lag_days`
- Every series registered with `status: unavailable` MUST have `unavailable_reason` and `unavailable_followup_issue`
- `source_sheet` values MUST match an actual sheet name in the pinned workbook
- `category` values MUST be from the enumerated list above (not free-form)
- `frequency: annual` is the only currently-supported value for Phase A (monthly support deferred to #94)
- No series MAY be registered without either `available` or `unavailable` status — a bare placeholder is a spec violation

## Fetching (`src/data_fetcher_uk.py`)

### Inputs

- Path to cached workbook (default: `data/raw/uk/_source/millennium_of_macro_data.xlsx`)
- Series registry (from `configs/series_uk.yaml`)

### Process

1. Verify workbook exists at the cache path; if missing, raise (see "Error behavior")
2. Verify `VERSION.txt` exists and matches a supported version; if missing or unknown, raise
3. For each series with `status: available`: read the named sheet, extract the named column, normalize to a DatetimeIndex at the declared frequency, save to `data/raw/uk/{series_name}.parquet`
4. For each series with `status: unavailable`: skip; record in manifest
5. Write `data/manifest_uk.json` recording: per-series status, row count, date range, file path (if fetched), or reason (if unavailable), or error message (if attempted but failed)

### Invariants

- Output parquet files MUST have a DatetimeIndex named `"date"` (consistent with US pipeline)
- Output parquet files MUST be annual-frequency (one row per calendar year) for this phase
- Fetching MUST be idempotent — re-running overwrites parquet files with fresh reads from the same workbook
- No series MAY be fabricated, imputed, or forward-filled across missing years by the fetcher; downstream consumers (notebooks, backtester) handle that if they need it
- Network access MUST NOT be attempted under any circumstance (this is a hard rule per the cache-only source model)

### Error behavior

- **Missing workbook at cache path:** Raise a clear error pointing the user to issue #52 and this spec's "Obtaining the workbook" section. Do NOT attempt to download. Do NOT substitute a different file. Do NOT silently skip. This is the hardest rule and is a test case.
- **`VERSION.txt` missing or reports an unsupported version:** Raise with a message naming the currently-cached file's inferred version and the supported-version list from this spec.
- **Named sheet missing from the workbook** (e.g., BoE removed a sheet in a version migration): Log as manifest error for that series; continue to the next series. A majority of series failing this way suggests a version migration issue and SHOULD trigger a spec update, not a silent pass.
- **Named column missing from an otherwise-present sheet:** Same as sheet-missing — per-series failure, manifest error, continue.
- **Per-series data quality surprises** (e.g., entire decade of zeros, values outside plausible range): NOT enforced at fetch time. Belongs to a data-quality validation layer (follow-up, potentially tied to #72 / #74 from the broader data-quality series).

## Loading

### Interface

```python
def load_uk_series(series_name: str) -> pd.DataFrame
def load_all_uk() -> dict[str, pd.DataFrame]
```

### Invariants

- `load_uk_series` raises `FileNotFoundError` if no cached data exists for that series
- Returned DataFrames always have a DatetimeIndex named `"date"`
- Returned DataFrames are single-column with the column name equal to `series_name`
- Loading does NOT re-read the source workbook — it reads from the parquet cache, same as the US pipeline's `load_series`

## Walk-forward availability

Phase A annual data has large publication lags by the standards of cyclical backtesting — a 1975 annual CPI figure is typically published in early 1976. `publication_lag_days` in the registry SHOULD be set per-series:

- BoE-reconstructed historical series (pre-1970): nominally 0 — the data is retrospective, not real-time. Note: walk-forward semantics treat this as "available at year-end of observation date," which is a simplification. The full walk-forward-correctness question is #72's concern.
- Post-1970 series (where the workbook is ingesting contemporaneously-reported data): ~30-180 days depending on series. Estimate from published release calendars; document the source in the `description`.

The walk-forward enforcement itself happens in the backtester (consistent with the US pipeline's split of concerns). This spec's responsibility is only to record the per-series lag metadata correctly.

## Test cases (spec-anchored)

The implementation MUST have `@pytest.mark.spec` tests covering:

1. **Workbook-missing raises clearly.** Test with the cache path pointing at a non-existent file; assert the raised error's message references this spec's section and issue #52 — not a generic `FileNotFoundError`.
2. **VERSION.txt missing raises.** Test with workbook present but `VERSION.txt` absent; assert error.
3. **Unsupported version raises.** Test with `VERSION.txt` containing an unrecognized version string; assert error.
4. **All registered `available` series have required fields.** YAML-schema test; registry loads without field-validation errors.
5. **All `unavailable` series have `unavailable_reason` and `unavailable_followup_issue`.** YAML-schema test.
6. **Output parquet has DatetimeIndex named "date".** Integration test requiring the workbook cache; loads one fetched parquet file; asserts index invariants.
7. **Manifest captures per-series status truthfully.** Integration test; run full fetch; assert manifest's `available`/`unavailable`/error counts match the registry.
8. **Per-series failure does not abort full fetch.** Unit test with a fixture or mock where one sheet read raises; assert other series still complete, failing series recorded in manifest.
9. **No network access attempted.** Unit test with monkey-patched `urllib` / `requests` / `curl` — any network attempt raises in the test assertion.

Tests 1-5, 8, 9 are unit-markable (no cache required). Tests 6, 7 are `@pytest.mark.integration` (require the cached workbook).

## What this spec does NOT cover

- **Monthly and sub-annual data.** Deferred to issue #94. Phase A is annual-only.
- **Non-BoE UK data sources.** Sterling reserve share (#91), total-return equity (#92), gold-GBP post-1971 (#93). These will require new data-source sections, probably in follow-up sub-specs under this folder or additions to this spec.
- **Multi-country harmonization.** Phase B (Dutch) and Phase C (JST panel) will have their own specs in this folder. Cross-country aggregation is Phase C's spec's concern, not this one.
- **Multi-currency backtester integration.** The backtester currently assumes USD; extending to GBP, multi-currency returns, and common-currency conversion is deferred to Phase B's design (per #52).
- **Data-quality validation beyond "fetch succeeded".** Value-range checks, splice-tracking-error checks, and cross-series sanity checks are follow-up work (see data-quality reviews and #72, #74).
- **Vintage / revision tracking.** BoE's historical data is revised over time; this spec ingests current-revised-snapshot values. ALFRED-style vintage tracking is not supported (see #73 for the US-side analog).
- **The analytical notebook and research note for Phase A.** Those are exploratory outputs and live on a separate `explore/` branch, not a stable pipeline spec — per the Workflow-section governance rule.

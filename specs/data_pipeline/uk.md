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

**A1 "Headline series" column-identification convention.** Multiple distinct series in A1 share the same Description row (row 3) — e.g., "Bank Rate" has both end-period and year-average variants; "Real UK GDP at market prices" has both level and growth variants. The `(source_sheet, source_column)` pair MUST NOT be treated as a primary key for A1; the registry's `source_column_units` field (Units row, row 5) is required for disambiguation. The spec's schema reflects this: `source_column_units` is not optional for A1-sourced series with shared Descriptions, even though a Description-only lookup may appear to work for other sheets.

### Cache and version pinning

The workbook is pre-cached at `data/raw/uk/_source/millennium_of_macro_data.xlsx`. **No network fetch at any time.** This is the hard rule — see "Error behavior" below for what happens when the cache is missing.

**Version pinning.** The cached file SHOULD be referenced by its BoE-published version (v3.1 as of 2026-04-15). A new BoE release (e.g., v3.2, v4.0) is a breaking event for reproducibility:

1. A `VERSION.txt` or equivalent sidecar at `data/raw/uk/_source/VERSION.txt` MUST record the version of the currently-cached workbook (human-readable string like `v3.1` plus the date the BoE file was downloaded)
2. A version change requires a spec update (adding a "version migration" section to this spec with what changed between versions, any new target series, any series that moved sheets)
3. The fetcher MUST NOT silently accept a replaced workbook — if `VERSION.txt` is missing or absent, this is an error condition

### Obtaining the workbook

The coordinator (not the coding agent) populates the cache. Download via BoE research-datasets page; operational details (curl user-agent, etc.) are out of scope for this spec. The delegation prompt for implementation MUST state that the cache is pre-populated.

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

The pipeline MUST attempt to register these series. If the BoE workbook does not contain a series under an obvious sheet name, the series MUST be registered with `status: unavailable` and the `unavailable_followup_issue` pointing to #91, #92, #93, or a new issue — not omitted.

The list was expanded on 2026-04-15 from the original 17 required series (per #52 Phase A issue description) to the 30 series below. The expansion incorporated series discovered during the archived exploratory implementation (at `archive/uk-phase-a-no-spec-2026-04-15`) — specifically the ones relevant to the monetization-mechanism, real-asset preservation, and reserve-currency-decline signatures that the Phase A research note identified as load-bearing for the umbrella thesis. The expansion is the spec catching up to what the exploratory research should have fed in upstream; see `docs/research/uk_sterling_transition.md` (when salvaged) for the exploratory phase.

**Fiscal:**
- Government debt/GDP
- Government deficit/GDP
- Government spending / GDP
- Tax revenue / GDP

**Monetary:**
- Bank Rate (official policy rate)
- CPI level (price index)
- CPI or RPI inflation (rate; derivable from level but commonly used directly)
- Broad money aggregate (M3 or equivalent consistent long series)
- Monetary base (narrow money; direct monetization indicator)
- Bank of England balance sheet / GDP (direct monetization indicator — the load-bearing signal for mode-4 resolution)

**Rates:**
- 10-year gilt yield (or Consols + gilt splice with `splice` field populated)
- Consols yield (pre-1930 long-term rate, exposed independently as well as via the gilt splice)
- Short rate (T-bill or equivalent)

**Financial assets:**
- UK equity index (BoE consolidated long series)
- Gold price in GBP — currently expected `status: unavailable` for post-1971 per issue #93
- USD/GBP nominal exchange rate — the BoE workbook exposes USD-per-GBP natively (the "$/£" column in A1; ~$4.86 classical parity). GBP/USD is derivable as 1/x in consumer code, not registered as a separate series
- Real USD/GBP exchange rate (CPI-adjusted; preferred signal for transition-scale analysis)

**Real assets:**
- UK land prices (agricultural)
- UK house prices (residential; Phase A research note found houses preserved real value materially better than listed equity through the sterling transition)
- UK commodity price index (broad / wholesale)
- Oil price in USD (specific commodity; isolates 1973 and 1979 shocks that a broad index smooths over)

**Macro:**
- Nominal GDP level
- Real GDP level
- Real GDP growth rate
- Unemployment rate
- Current account / GDP
- Trade balance / GDP (goods+services only; distinct from current account which includes primary/secondary income). **Sign convention:** the BoE workbook's "Trade deficit" column stores deficit as positive; this differs from `uk_public_deficit_gdp` which uses negative=deficit. Downstream consumers SHOULD check the description field before aggregating across series. (This is a documentation-level convention, not test-enforced — no pipeline check asserts that description fields correctly flag sign conventions. If the convention proves inadequate, tighten by adding a spec-anchored test that verifies description-field contents for sign-sensitive series.)

**Reserve status:**
- Sterling share of global reserves — currently expected `status: unavailable` per issue #91
- Nominal Effective Exchange Rate Index (ERI; trade-weighted GBP value — broader reserve-currency-decline signal than GBP/USD alone)
- Real Effective Exchange Rate Index (ERI, CPI-adjusted)

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
- No series MAY be fabricated, imputed, or forward-filled across missing years by the fetcher
- Network access MUST NOT be attempted under any circumstance (cache-only source model)

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

`publication_lag_days` in the registry is the per-series contract; walk-forward enforcement happens in the backtester (same split of concerns as the US pipeline). Set nominally 0 for BoE-reconstructed historical series (pre-1970, retrospective) and 30-180 days for contemporaneously-reported post-1970 series (estimate from published release calendars). See #72 for the US-side publication-lag bug this registry metadata enables fixing.

## Test cases (spec-anchored)

The implementation MUST have `@pytest.mark.spec` tests covering:

1. **Workbook-missing raises clearly.** Cache path pointing at non-existent file; raised error's message references this spec and issue #52, not a bare `FileNotFoundError`.
2. **VERSION.txt missing or unsupported raises.** Parametrized: `VERSION.txt` absent, and `VERSION.txt` present with an unrecognized version string.
3. **Registry field-completeness per schema.** All `available` series have `source_sheet`, `source_column`, `start_year`, `end_year`, `publication_lag_days`; all `unavailable` series have `unavailable_reason` and `unavailable_followup_issue`.
4. **Output parquet has DatetimeIndex named `"date"`.** Integration test requiring the workbook cache.
5. **Manifest captures per-series status truthfully.** Integration test; run full fetch; manifest's `available`/`unavailable`/error counts match the registry.
6. **Per-series failure does not abort full fetch.** Mocked sheet-read failure; other series still complete; failing series recorded in manifest.

Tests 1-3, 6 are unit-markable. Tests 4-5 are `@pytest.mark.integration` (require the cached workbook).

## What this spec does NOT cover

- **Monthly and sub-annual data.** Deferred to #94.
- **Non-BoE UK data sources.** Sterling reserve share (#91), total-return equity (#92), gold-GBP post-1971 (#93) — follow-up sub-specs or additions.
- **Multi-currency backtester integration.** Deferred to Phase B's design.
- **Data-quality validation beyond "fetch succeeded".** Value-range checks, splice-tracking-error, cross-series sanity — see #72, #74.
- **Vintage / revision tracking.** This spec ingests current-revised-snapshot values; ALFRED-style vintage tracking is not supported (#73 tracks the US-side analog).

# Data pipeline specs

The US data pipeline spec at [`specs/data_pipeline.md`](../data_pipeline.md) is the **baseline** — it governs `src/data_fetcher.py`, `configs/series.yaml`, `scripts/fetch_data.py`, and the corresponding tests for US-side FRED and Yahoo Finance data. That spec's conventions (parquet-per-series cache layout, YAML registry schema, manifest schema, idempotent fetch, publication-lag metadata) are the foundation for all pipeline work.

This folder holds **country-specific extensions** for cross-national data work (see issue #52 and the Dalio-principles reference at `specs/theses/changing-world-order/dalio-principles.md` §9). Each country spec:

- Names its source workbook or API and how its data is cached
- States what conventions it inherits from the US baseline unchanged
- States the deltas (what it adds, changes, or explicitly doesn't support)
- Lists the series it covers, with source-sheet / column / frequency metadata in the corresponding `configs/series_{country}.yaml`

## Country specs

| Spec | Status | Phase (per #52) | Source |
|---|---|---|---|
| [`uk.md`](uk.md) | Stabilizing | Phase A | Bank of England "A Millennium of Macroeconomic Data" workbook (v3.1) |

Future specs (Phase B onward) will appear here: Dutch guilder, JST macrohistory panel, pre-1780 multi-empire. Each new country spec introduces at most the deltas relative to the baseline and prior country specs — a single monolithic "cross-national pipeline" spec was considered and rejected (see issue #52 discussion) because the per-country sources, schemas, and availability differ enough that one spec would become unwieldy.

## When to move the US spec into this folder

The US spec stays at `specs/data_pipeline.md` for now. If the pattern of country-per-file stabilizes (three or more country specs in this folder), consider promoting the US spec to `specs/data_pipeline/us.md` and making this folder the single home for all pipeline specs. Not required now; deferred decision.

## Related

- `specs/theses/changing-world-order/backtest-sample-scope.md` — motivates cross-national work
- `specs/theses/changing-world-order/dalio-principles.md` §9 — Dalio's cross-national methodology
- Issue #52 — phased roadmap (A/B/C/D)
- Issue #79 — scale-taxonomy divergence (affects interpretation of country data)
- Issues #91-#94 — Phase A follow-ups (data gaps, sharper-crisis-window analysis)

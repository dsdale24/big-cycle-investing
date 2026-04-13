# Big Cycle Investing

Research project building a long-view wealth-preservation strategy inspired by Ray
Dalio's big cycle framework — but not restricted to his specific indicators. The
value is thinking in long cycles across financial, political, and civilizational
dimensions, and being open to any data that helps understand where we are.

## Project vision
Build an iterative research pipeline (inspired by Karpathy's autoresearch) that:
1. Tracks macro/financial + civilizational indicators from 1975 onward
2. Classifies macro regimes (expansion, overheating, contraction, reflation)
3. Backtests allocation strategies using only data available at each point in time
4. Automates experimentation — sweep parameters, log results, propose new hypotheses

The end goal is a walk-forward backtest answering: "If I had started this strategy
in 1975 with the data available at the time, and adapted as new indicators emerged,
what would my wealth-preservation outcomes have looked like?"

## Architecture
- `src/data_fetcher.py` — pulls historical data from FRED + Yahoo Finance, caches to parquet
- `src/indicators.py` — derived indicators (debt acceleration, real rates, regime classifier, etc.)
- `configs/series.yaml` — registry of ~55 data series with metadata
- `scripts/fetch_data.py` — entry point to download all data
- `notebooks/` — exploration and analysis notebooks
- `docs/indicator_framework.md` — full indicator taxonomy across all categories
- `data/` — cached data (gitignored), `data/manifest.json` tracks fetch results

## Indicator categories
1. **Debt & credit dynamics** — debt/GDP, credit growth, delinquencies
2. **Interest rates & yield curve** — fed funds, 10Y/2Y, credit spreads
3. **Inflation & monetary policy** — CPI, M2, monetary base, Fed balance sheet
4. **Currency & store of value** — USD index, gold, trade-weighted dollar
5. **Economy & labor** — GDP, unemployment, industrial production, sentiment
6. **Inequality & internal order** — Gini, wealth shares, productivity-compensation gap
7. **Trust & governance** — Economic Policy Uncertainty index
8. **Fiscal sustainability** — deficit/GDP, interest payments/GDP, foreign debt holdings
9. **External order** — net international investment position, current account, reserves
10. **Human capital** — GDP per capita, R&D, life expectancy, infant mortality
11. **Asset prices** — equities, bonds, gold, oil, TIPS (for portfolio construction)

See `docs/indicator_framework.md` for the full detailed breakdown with series IDs,
coverage dates, and notes on using low-frequency (annual) data.

## Spec-driven development

This project uses spec-driven development with a progressive formalization approach.
The spec starts loose in exploration areas and tightens as components stabilize.

### The spec lifecycle
1. **Exploring** — No formal spec. Move fast, try things, learn what works. Notebooks
   and GitHub issues capture findings and hypotheses.
2. **Stabilizing** — Write a spec in `docs/specs/` defining inputs, outputs, invariants,
   and edge cases. Add tests that verify the spec. This happens when a component is
   about to be depended on by other components.
3. **Settled** — Spec is authoritative. Changes require updating the spec first, then
   the implementation. Tests enforce the spec.

### Current spec status
| Component | Status | Spec location |
|-----------|--------|---------------|
| Data pipeline (`data_fetcher.py`) | Stabilizing | `docs/specs/data_pipeline.md` |
| Indicators (`indicators.py`) | Exploring | — |
| Backtester core (`backtester.py`) | Stabilizing | `docs/specs/backtester.md` |
| Walk-forward constraint | Stabilizing | `docs/specs/backtester.md` |
| Regime classifier | Exploring | — |
| Strategy logic | Exploring | — |
| Autoresearch loop | Not started | — |

### Core principle: implementation follows spec, never the reverse

The spec is the source of truth. When changing a stabilized or settled component:
1. **Update the spec first** — define the new behavior, invariants, edge cases
2. **Then implement** to match the spec
3. **Then test** against the spec

Never implement first and backfill the spec to match. That inverts the relationship
and turns the spec into unreliable documentation. If you find the spec is wrong
during implementation, stop — update the spec, then continue.

For exploring components, there is no spec to follow. Move fast. But the moment
you're about to stabilize, write the spec BEFORE the refactor.

### How to apply this
- **Before writing code:** Check if the component has a spec. If it does, read it.
  If your planned changes conflict with the spec, update the spec first.
- **When exploring:** No spec needed. Capture learnings in notebooks and issues.
- **When stabilizing:** Write the spec BEFORE refactoring. The spec defines what
  "correct" means. Include: inputs, outputs, invariants (things that must always
  be true), edge cases, and example test cases.
- **When something breaks:** If a bug reveals a missing invariant, add it to the spec
  and add a test. The spec grows from real failures, not hypothetical ones.
- **Every PR touching a specced component** should reference the relevant spec and
  note whether the spec was updated as part of the change.

## Workflow

### Branch naming
- `explore/*` — Exploratory work. No spec required. Freedom to experiment.
  Notebooks, new indicators, rough prototypes. Can merge to main.
- `stable/*` — Stabilization work. **Must** update or create the relevant spec
  BEFORE implementation. Must include tests that verify the spec. Spec must be
  reviewed and stable before merging to main.
- `fix/*` — Bug fixes. If the fix touches a specced component, update the spec
  if the bug revealed a missing invariant.

### GitHub labels
- `exploring` — Component is in exploration phase, no spec required
- `stabilizing` — Component needs a spec before further changes
- `bug` — Something is broken
- `data` — Data source or pipeline issue

### Issues & PRs
- Track bugs, features, and tasks as GitHub issues at dsdale24/big-cycle-investing
- Check open issues before starting work — they capture known problems and design thinking
- Reference issues in commits/PRs when addressing them (e.g., "Fixes #1")
- Create new issues for problems discovered during development
- PRs from `stable/*` branches must reference the spec they conform to

## Key constraints
- All backtesting must be walk-forward: only use data available at each point in time
- Backtest start date: 1975-01-01
- Annual/periodic data is fine — forward-fill and use as regime context, not trading signals
- FRED API key required: set FRED_API_KEY env var or put in .env file

## Tech
- Python 3.11+, pandas, matplotlib/plotly, pyarrow
- FRED API via `fredapi` (free key from https://fred.stlouisfed.org/docs/api/api_key.html)
- yfinance for market price data
- venv at `.venv/`

## Current status
- **Phase 1 (done):** Data pipeline — 55 series across all categories, fetched and cached
- **Phase 2 (done):** Exploration notebooks (01: financial, 02: civilizational indicators)
- **Phase 3 (in progress):** Walk-forward backtester built, baseline results captured
- **Next:** Fix baseline data issues (#1, #8, #6), then analyze predictive power (#9, #11)
  before iterating on the strategy (#2, #3, #4). See issue #13 for full roadmap.
- Baseline results: Big Cycle v1 (7.64% CAGR, 0.98 Sharpe) underperforms All Weather
  (7.59% CAGR, 1.13 Sharpe) on risk-adjusted basis — known issues with data gaps and
  crude regime classifier. See issues #1-#3.

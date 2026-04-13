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

## Workflow
- **Git:** Use feature branches for all work, merge to main via PR or explicit approval
- **Issues:** Track bugs, features, and tasks as GitHub issues at dsdale24/big-cycle-investing
  - Check open issues before starting work — they capture known problems and design thinking
  - Reference issues in commits/PRs when addressing them (e.g., "Fixes #1")
  - Create new issues for problems discovered during development

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

# Big Cycle Investing

Research project building a long-view wealth-preservation strategy inspired by Ray Dalio's big cycle framework.

## Architecture
- `src/data_fetcher.py` — pulls historical macro/financial data from FRED + Yahoo Finance
- `src/indicators.py` — computes derived indicators from raw series
- `configs/series.yaml` — defines what data series to fetch and their metadata
- `scripts/fetch_data.py` — entry point to download all data
- `data/` — cached data (gitignored)

## Key constraints
- All backtesting must be walk-forward: only use data available at each point in time
- Backtest start date: 1975-01-01
- FRED API key required: set FRED_API_KEY env var or put in .env file

## Tech
- Python, pandas, matplotlib/plotly
- FRED API (free, requires key from https://fred.stlouisfed.org/docs/api/api_key.html)
- yfinance for market price data

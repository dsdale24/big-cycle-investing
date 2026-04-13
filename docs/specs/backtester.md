# Backtester Specification

Status: **Stabilizing**
Last updated: 2026-04-13

## Purpose

Simulate portfolio allocation strategies from 1975 onward using only data that
would have been available at each point in time. Produce performance metrics
that can be fairly compared across strategies.

## Core invariant: walk-forward constraint

**At rebalancing time T, the strategy MUST NOT access any data with a timestamp
after T.** This is the single most important correctness property of the system.

Specifically:
- All indicator data passed to `strategy.allocate(date, available_data)` must be
  truncated to `data.loc[:date]`
- Annual data published with a lag must respect that lag (e.g., 2024 Gini published
  mid-2025 should not be visible until mid-2025)
- Asset returns used for portfolio accounting are computed from prices on or before
  date T — this is naturally satisfied since returns are computed from past prices

### Test cases
- Given an indicator that jumps from 0 to 100 on 2000-01-01, a strategy rebalancing
  on 1999-12-31 must see 0, not 100.
- Given annual data for year 2000, if publication lag is 6 months, a strategy
  rebalancing on 2001-03-01 must NOT see the 2000 value.

## Asset returns

### Inputs
- Daily price data for each asset class (from Yahoo Finance, FRED, or proxies)
- Start date (default: 1975-01-01)

### Outputs
- `pd.DataFrame` with columns for each asset class, indexed by date, containing
  daily returns (as decimals, e.g., 0.01 = 1%)

### Asset class definitions
| Asset class | Primary source | Pre-data proxy | Notes |
|-------------|---------------|----------------|-------|
| equities | ^GSPC daily close | — | Available from 1975 |
| long_bonds | Derived from 10Y yield (^TNX) | — | Return ≈ -duration × Δyield + yield/252 |
| short_bonds | Derived from 2Y yield (GS2) | — | Return ≈ -2 × Δyield + yield/252 |
| gold | GC=F daily close | Proxy from FRED (pre-2000) | See issue #1 |
| commodities | CL=F daily close | Proxy from FRED (pre-2000) | See issue #1 |
| cash | FEDFUNDS / 252 | — | Monthly rate, forward-filled to daily |

### Invariants
- All return values must be finite (no NaN, no inf)
- Daily returns should be bounded: |r| < 0.25 for any single day (circuit breaker)
- Missing data periods must be filled with 0 (not NaN), representing a "no data,
  assume flat" conservative approach. (This may change — see issue #1.)
- When proxy data is spliced with primary data, there must be no gap and no overlap
  at the splice point

### Edge cases
- Weekends/holidays: returns are 0 (or dates are skipped if using business days)
- Pre-data periods: currently filled with 0; should be filled with proxy returns
  after issue #1 is resolved

## Strategy interface

```python
class Strategy(Protocol):
    def allocate(
        self,
        date: pd.Timestamp,
        available_data: dict[str, pd.DataFrame | pd.Series],
    ) -> PortfolioSnapshot:
        ...
```

### PortfolioSnapshot
```python
@dataclass
class PortfolioSnapshot:
    date: pd.Timestamp
    weights: dict[str, float]  # asset class -> weight, must sum to 1.0
    signals: dict[str, float]  # indicator values used (for debugging/analysis)
    regime: str                # regime label (for analysis)
```

### Invariants
- `sum(weights.values())` must equal 1.0 (within floating point tolerance)
- All weights must be >= 0 (no shorting in v1)
- All weight keys must be valid asset class names

## Backtest execution

### Inputs
- Strategy instance
- Asset returns DataFrame
- Indicator data dict
- Start date
- Rebalance frequency (default: quarterly, "QE")

### Process
1. Generate rebalance dates from asset return index
2. Initialize equal-weight portfolio
3. For each trading day from start date:
   a. If rebalance date: call `strategy.allocate()` with truncated data, update weights
   b. Compute portfolio return: `Σ(weight_i × return_i)` for each asset
   c. Drift weights: each weight grows/shrinks proportional to its asset's return
   d. Record daily portfolio return

### Outputs
- `BacktestResult` containing:
  - Daily portfolio returns and cumulative value
  - Weights at each rebalance date
  - Regime labels at each rebalance
  - Asset returns for the period
  - Config used

### Invariants
- Portfolio value must be positive for all dates (no bankruptcy)
- Portfolio value on day 0 is 1.0
- Number of rebalances = number of rebalance dates within the period
- Weights after drift must still sum to 1.0

## Performance metrics

### Required metrics
| Metric | Formula | Notes |
|--------|---------|-------|
| Total return | `final_value / initial_value - 1` | |
| CAGR | `(1 + total_return) ^ (1/years) - 1` | |
| Volatility | `daily_returns.std() × √252` | Annualized |
| Sharpe ratio | `CAGR / volatility` | Assuming 0 risk-free (simplification) |
| Max drawdown | `min((value - cummax) / cummax)` | |
| Calmar ratio | `CAGR / |max_drawdown|` | |

### Future metrics (not yet implemented)
- Sortino ratio (downside deviation only)
- Turnover per rebalance
- Transaction cost drag
- Per-decade breakdown

---

## What this spec does NOT cover (exploring)

- Which indicators to use in the regime classifier
- Strategy parameter values
- How civilizational indicators should influence allocation
- Autoresearch experiment design

These are in the "exploring" phase and should not be specced until they stabilize.

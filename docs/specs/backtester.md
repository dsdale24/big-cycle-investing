# Backtester Specification

Status: **Stabilizing**
Last updated: 2026-04-13 (pre-2000 proxy splicing added — see issue #1)

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
- `pd.DataFrame` with columns for each asset class, indexed by **business day**
  (pandas `DatetimeIndex`, no weekends, holidays permitted to be present if they
  carry a return), containing daily returns (as decimals, e.g., 0.01 = 1%)
- The index dtype must be `datetime64[ns]`, not `object` — downstream code
  relies on string-based `.loc` lookups and `.year` / `.month` accessors

### Asset class definitions
| Asset class | Primary source | Pre-data proxy | Notes |
|-------------|---------------|----------------|-------|
| equities | ^GSPC daily close | — | Available from 1975 |
| long_bonds | Derived from 10Y yield (^TNX) | — | Return ≈ -duration × Δyield + yield/252 |
| short_bonds | Derived from 2Y yield (GS2) | — | Return ≈ -2 × Δyield + yield/252 |
| gold | GC=F daily close (2000+) | WPUSI019011 monthly (1975-2000) | PPI: Metals & Metal Products; imperfect proxy, tracks directionally |
| commodities | CL=F daily close (2000+) | DCOILWTICO daily (1986-2000), PPIACO monthly (1975-1986) | Two-stage proxy: WTI spot where available, PPI All Commodities before |
| cash | FEDFUNDS / 252 | — | Monthly rate, forward-filled to daily |

### Invariants
- All return values must be finite (no NaN, no inf)
- Daily returns should be bounded: |r| < 0.25 for any single day (circuit breaker)
- Every asset class must have non-zero return data for the full backtest period
  (1975-01-01 to present). Filling missing periods with 0 is forbidden for
  assets with an available proxy — use the proxy instead.
- Missing data periods for assets with **no** proxy may be filled with 0 (documented
  per asset), but this must be flagged in the backtest config so downstream analysis
  knows the period is degenerate.
- When proxy data is spliced with primary data, there must be no gap and no overlap
  at the splice point — the combined series is continuous across the splice date.

### Edge cases
- Weekends are **not** in the index — output is business-day frequency. Saturday
  and Sunday timestamps must not appear in `returns.index` or `sources.index`.
- Holidays (days when the market was closed): may appear in the index with a
  return of 0 if the underlying source dropped that day, or may be omitted. Either
  is acceptable — the invariant is that no NaN appears on any date that IS in the
  index.
- Pre-data periods: covered by proxy splicing (see below). Any remaining gap must
  be explicitly documented.

## Proxy series splicing

### Purpose
Primary daily price sources (GC=F for gold, CL=F for commodities) only begin ~2000
on Yahoo Finance. Without proxies, pre-2000 returns are 0 for these assets, which
biases 1975-2000 backtest results against any strategy allocating to them.

### Splice points
| Asset class | Date range | Source | Frequency |
|---|---|---|---|
| gold | 1975-01-01 → 2000-08-29 | WPUSI019011 (FRED) | monthly |
| gold | 2000-08-30 → present | GC=F (Yahoo) | daily |
| commodities | 1975-01-01 → 1985-12-31 | PPIACO (FRED) | monthly |
| commodities | 1986-01-02 → 2000-08-22 | DCOILWTICO (FRED) | daily |
| commodities | 2000-08-23 → present | CL=F (Yahoo) | daily |

Exact splice dates must be the first trading day that the newer source has data.
Splice date belongs to the newer source (exclusive on the older, inclusive on the newer).

### Monthly → daily return conversion
Monthly proxy series (WPUSI019011, PPIACO) are levels, not returns. Conversion rule:
1. Compute monthly returns from the level series: `monthly_ret = level.pct_change()`
2. Distribute each monthly return across the trading days in that month such that
   compounded daily returns equal the monthly return:
   `daily_ret = (1 + monthly_ret) ** (1 / n_trading_days_in_month) - 1`
3. Apply this daily_ret to every trading day within the month

**Why even distribution:** the proxy is coarse; pretending we know intra-month
timing we don't have would manufacture false signal. Even distribution makes
monthly-frequency truth self-consistent at the daily level without fabricating
information.

### Invariants (splicing)
- The spliced daily series must compound to the source's native-frequency returns
  to within 1e-6 tolerance (a daily series built from PPIACO must compound to
  PPIACO's monthly returns over any full-month window)
- No NaN values on any business day in `1975-01-01 → present` (weekends are not in
  the index, so the invariant is vacuous on weekends)
- No gap or overlap at splice points — every trading day belongs to exactly one source
- The source used on each date must be queryable from the output (e.g., a
  `source` column or companion Series) so analysis can distinguish proxy from
  primary periods. Source labels must be populated on every business day the
  returns frame is populated on.

### Test cases
- Given WPUSI019011 monthly returns of +1% for February 1980, every trading day
  in February 1980 has the same daily return r where `(1+r)^n ≈ 1.01` for n
  trading days in February 1980
- Given the 1986-01-02 splice for commodities, 1985-12-31 belongs to PPIACO and
  1986-01-02 belongs to DCOILWTICO; no day belongs to both
- Given the 2000-08-23 splice for commodities, the day before belongs to
  DCOILWTICO and the day of belongs to CL=F
- Loading asset returns for date 1975-06-15 returns non-zero values for both
  gold and commodities columns
- Compounded monthly returns from the spliced daily gold series, for any full
  month in 1975-2000, equal WPUSI019011 monthly returns for that month

### Known limitations
- WPUSI019011 is a metals-and-metal-products PPI, not a gold price; correlation
  to actual gold returns is imperfect. This is documented tracking error accepted
  in exchange for non-zero returns.
- PPIACO is a broad commodity basket, not crude oil; the pre-1986 commodity
  series measures a different thing than post-1986. This is a semantic splice,
  not just a data-source splice — document it in backtest outputs.

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

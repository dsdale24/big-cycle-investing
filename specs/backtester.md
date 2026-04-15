# Backtester Specification

Status: **Stabilizing**
Last updated: 2026-04-14 (data-quality surface added to BacktestResult — resolves the pre-2002 uncertainty open question from #31)

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
| long_bonds | TLT adjusted close (2002-07-30+) | Derived from 10Y yield (^TNX), 1975 → 2002-07-29 | Spliced — see "ETF splicing" below |
| short_bonds | SHY adjusted close (2002-07-30+) | Derived from 2Y yield (GS2), 1975 → 2002-07-29 | Spliced — see "ETF splicing" below |
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

## Bond return approximation

### Purpose
Real bond total-return indices are not freely available for the full
1975-present range. We approximate daily total returns from Treasury
yields using a first-order duration model.

### Formula
For each trading day `t`:
```
daily_return[t] = -duration × (yield[t] - yield[t-1]) + yield[t-1] / 252
```
- `yield` is in decimal form (0.05 = 5%)
- `duration = 8` for `long_bonds` (10Y proxy, `^TNX`)
- `duration = 2` for `short_bonds` (2Y proxy, `GS2`)
- The first term is the price-change from yield movement; the second is
  the carry accrual

### Assumptions and limitations
- Duration is constant. In reality, duration shortens with rising yields
  and with age; we use a midpoint estimate.
- Convexity is ignored. Small daily yield moves (<50 bps) incur <5%
  convexity; large moves (1980s tightening, 2022) can reach 10-20%.
- Coupon reinvestment beyond the `yield/252` accrual is not modeled.
- Errors compound over 50 years; the validation below sets a tolerance.

### Validation methodology
Compare synthetic daily bond returns to real total-return ETF data over
the overlap period:
- Long bonds: **TLT** (iShares 20+ Year Treasury Bond ETF), 2002-07+
- Short bonds: **SHY** (iShares 1-3 Year Treasury Bond ETF), 2002-07+

Resample both synthetic and ETF returns to monthly and compute:
- Mean absolute error (MAE) of monthly returns
- Correlation
- Per-decade CAGR divergence (synthetic CAGR minus ETF CAGR)

### Accuracy threshold
The approximation is considered adequate if:
- Per-decade CAGR divergence ≤ **0.50 percentage points per year** for
  every decade in the overlap period
- Correlation of monthly returns ≥ 0.90

If either bound is violated for a given asset class, the implementation
must splice real ETF data for the overlap period (same pattern as
`gold`/`commodities` in "Proxy series splicing"). The approximation
continues to apply before the ETF start date.

### Invariants
- Daily bond return is finite on every business day in 1975-01-01 → present
- With zero yield change, daily return equals `yield[t-1] / 252` exactly
- Circuit breaker at `|r| < 0.25` (inherited from asset-returns invariants)

### Test cases
- Unit: zero yield change for a full year yields `(1 + yield/252)^252 − 1`
  (approximately `yield`) as the compounded annual return
- Unit: yield moves from 5% to 6% in one day produces long-bond daily
  return of about `-8 × 0.01 + 0.05/252 = -7.98%` (and similarly for short
  bonds with duration 2)
- Integration: MAE of monthly synthetic long_bonds vs TLT over the full
  overlap period is computed and reported; the implementation record
  shows whether the 0.50 ppt/yr / 0.90 correlation threshold is met per
  decade
- Integration: same validation for short_bonds vs SHY

### ETF splicing (mandatory for validated assets)

The validation in #8 (`docs/research/bond_return_validation.md`) found that
both `long_bonds` and `short_bonds` exceed the accuracy threshold over the
2002+ overlap period — `long_bonds` violates the per-decade CAGR bound
(up to 3.4 ppt/yr divergence in the 2010s, the convexity signature) and
`short_bonds` violates the correlation bound (0.77 vs 0.90 floor). Per
the rule above, both must splice ETF data for the overlap period.

#### Splice points

| Asset class | Date range | Source | Frequency |
|---|---|---|---|
| long_bonds | 1975-01-02 → 2002-07-29 | ^TNX duration approximation | daily (derived) |
| long_bonds | 2002-07-30 → present | TLT (Yahoo) | daily |
| short_bonds | 1975-01-02 → 2002-07-29 | GS2 duration approximation | daily (derived) |
| short_bonds | 2002-07-30 → present | SHY (Yahoo) | daily |

The splice date is the first trading day on which the ETF has data and
belongs exclusively to the newer source (same exclusivity rule as
"Proxy series splicing"). Splice dates are not hardcoded — they are
derived dynamically as the first trading day of the ETF's history.

#### Total-return sourcing

ETF returns are computed from `pct_change()` of `Adj Close`, which
incorporates dividend reinvestment. Bond ETFs distribute monthly coupon
income, and using `Close` would discard a material fraction of total
return — that is the whole reason the duration approximation includes a
`yield / 252` carry term in the first place. The post-splice series must
preserve the same total-return semantics as the pre-splice series.

#### Invariants (bond splicing)

- No gap, no overlap at the splice date — every business day belongs to
  exactly one source
- Source labels are populated on every business day the returns frame is
  populated on (consistent with "Proxy series splicing → Invariants")
- Pre-splice returns must equal the pure-approximation regime exactly —
  splicing only replaces post-2002 returns
- The post-splice series satisfies the accuracy threshold trivially
  because it IS the ETF data over the overlap period

#### Test cases (splicing)

- The trading day immediately before the splice date is sourced from the
  duration approximation; the splice date itself is sourced from TLT
  (long_bonds) or SHY (short_bonds)
- Pre-2002 spliced returns for both bond assets equal the duration
  approximation produced by the same yield series (regression check
  against the unspliced path)
- For any month fully within the post-splice window, the spliced
  monthly return equals the ETF monthly return (modulo float tolerance)
- Source label transitions exactly once per asset, on the splice date,
  with no NaN labels on populated business days

### Known open questions

- ~~**Pre-2002 uncertainty communication.**~~ **Resolved** — see the
  "Data quality" section below for `BacktestResult.asset_sources` and
  `approximation_exposure()`.
- **1990s hybrid.** ICE BofA Treasury indices on FRED extend the
  validation window earlier than TLT/SHY; could tighten the pre-2002
  estimate without requiring a third splice. Out of scope for #31.

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
- Source labels are one of: a primary-data identifier (e.g., `"^GSPC"`,
  `"GC=F"`, `"TLT"`), a proxy-series identifier (e.g., `"WPUSI019011"`,
  `"PPIACO"`), an approximation identifier (e.g., `"^TNX"`, `"GS2_yield"`),
  or the sentinel `"zero_fill"` for days where no source covers the asset
  and the spec permits zero-filling. The sentinel exists so the
  populated-everywhere invariant can hold even on legitimately
  zero-filled days; analysts can distinguish "real return" from "padded
  return" by membership in this set. `APPROXIMATION_SOURCES` (see "Data
  quality") explicitly excludes `"zero_fill"` because zero-fill is an
  absence of data, not a model approximation — a different uncertainty
  class.

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
        pre_rebalance_weights: dict[str, float],
    ) -> PortfolioSnapshot:
        ...
```

### Protocol parameters
- `date`: rebalance timestamp
- `available_data`: indicators truncated to `data.loc[:date]` (walk-forward
  constraint); does NOT include raw asset prices or returns
- `pre_rebalance_weights`: the portfolio's current weights immediately
  before this call, after all drift from prior returns. Strategies that
  want to rate-limit turnover or accept drift unchanged need this input.
  Strategies that compute new weights purely from indicators can ignore it.

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
- `pre_rebalance_weights` keys are the asset-class set active on the
  rebalance date; a newly-introduced asset has weight 0.0 in this dict
  (not absent), so `.get(key, 0.0)` and `[key]` are equivalent reads

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
   a. If rebalance date: call `strategy.allocate()` with truncated data;
      compute turnover and transaction cost from old vs new weights (see
      "Transaction costs" section); deduct cost from portfolio value;
      update weights.
   b. Compute portfolio return: `Σ(weight_i × return_i)` for each asset
   c. Drift weights: each weight grows/shrinks proportional to its asset's return
   d. Record daily portfolio return

### Outputs
- `BacktestResult` containing:
  - Daily portfolio returns and cumulative value (net of transaction costs)
  - Weights at each rebalance date
  - Regime labels at each rebalance
  - Asset returns for the period
  - `turnover: pd.Series` — turnover (in [0, 1]) at each rebalance date
  - `costs: pd.Series` — transaction cost paid at each rebalance, in
    return units (cost / portfolio_value_at_rebalance)
  - `asset_sources: pd.DataFrame` — same index and columns as
    `asset_returns`; each cell holds the string source label that produced
    that day's return for that asset (e.g., `"^TNX"`, `"TLT"`, `"GC=F"`,
    `"WPUSI019011"`). Lifted from the `sources` DataFrame returned by
    `build_asset_returns(..., return_sources=True)` so analysts can recover
    the data quality of any backtest period without re-fetching. See "Data
    quality" below for how this surfaces in analysis.
  - Config used

### Invariants
- Portfolio value must be positive for all dates (no bankruptcy)
- Portfolio value on day 0 is 1.0
- Number of rebalances = number of rebalance dates within the period
- Weights after drift must still sum to 1.0
- Turnover at each rebalance is in [0, 1]
- Cost at each rebalance is ≥ 0
- Cost is 0 when turnover is 0

## Transaction costs

### Purpose
Costless rebalancing flatters high-turnover strategies and makes
comparisons unreliable. This section defines how trading costs are
modeled so strategies that trade often are penalized fairly.

Costs are applied at rebalance time, deducted from portfolio value, and
naturally reduce downstream compounding. `BacktestResult` carries the
per-rebalance turnover and cost so downstream analysis can separate
signal from cost drag.

### Cost model
At each rebalance date:

```
turnover       = 0.5 × Σ |new_weight_i − pre_rebalance_weight_i|
cost_rate      = cost_rate(date)          # float or callable
cost           = turnover × cost_rate     # as a fraction of portfolio value
portfolio_value ← portfolio_value × (1 − cost)
```

Turnover is half the sum of absolute weight changes, so it sits in
`[0, 1]`: 0 means no change, 1 means a complete portfolio swap.

### Interface

`run_backtest` accepts:
```python
cost_rate: float | Callable[[pd.Timestamp], float] = default_cost_schedule
```
- `float`: applied uniformly at every rebalance (e.g., `0.001` = 10 bps
  on turnover).
- `Callable`: queried at each rebalance date, returns the rate for that
  date. This is the default; see schedule below.
- `0.0`: disables cost application (legacy / unit-test use; must be set
  explicitly).

### Default cost schedule

| Period | cost_rate (per unit turnover) |
|---|---|
| 1975-01-01 → 1980-01-01 | 0.0050 (50 bps) |
| 1980-01-01 → 2000-01-01 | 0.0030 (30 bps) |
| 2000-01-01 → 2010-01-01 | 0.0010 (10 bps) |
| 2010-01-01 → present | 0.0005 (5 bps) |

**Rationale.** Pre-1980 bid-ask spreads and fixed commissions were
large; deregulation in 1975 and Schwab-era discount brokerage through
the 1980s gradually compressed them. Electronic execution and decimal
pricing (2001) dropped explicit costs another order of magnitude by
2010. Modern index ETF execution is a fraction of a basis point, but
the 5 bps floor covers bid-ask spread and market impact for realistic
portfolio sizes.

Rates are estimates, not precise historical data. They're set to
penalize high-turnover strategies plausibly while remaining calibrated
enough to compare strategies across decades.

### Invariants
- `turnover(date) ∈ [0, 1]` at every rebalance
- `cost_rate(date) ≥ 0` for every date
- `cost(date) = turnover(date) × cost_rate(date) ≥ 0`
- A rebalance with `turnover = 0` has `cost = 0` and no impact on
  portfolio value
- Portfolio value after cost deduction remains positive (bankruptcy
  from cost alone is impossible because cost ≤ portfolio value iff
  `cost_rate ≤ 1`; the default schedule caps at 50 bps, well below 1)
- `BacktestResult.turnover` and `BacktestResult.costs` are `pd.Series`
  indexed by rebalance date, same length as `weights`

### Turnover semantics: intended vs. actual

Turnover measures **actual** weight change at each rebalance: the gap
between the `new_weights` the strategy produces and the `pre_rebalance_weights`
observed right before the call to `strategy.allocate(...)`. Drift between
rebalances — asset returns moving the portfolio away from the previous
target — is NOT free. Re-targeting the original weights under drift is a
real trade and produces real turnover.

Consequence: a strategy that always returns the same target (e.g.,
constant 60/40) incurs turnover proportional to drift, not zero turnover.

A strategy that produces truly zero turnover must either (a) accept drift
as the new target, i.e., return `pre_rebalance_weights` unchanged, or
(b) operate under flat returns so drift does not occur.

### Test cases
- A strategy whose output at each rebalance equals the current
  `pre_rebalance_weights` (drift-accepting strategy) has `turnover = 0` at
  every rebalance and total `costs.sum() == 0`, regardless of the return
  process
- A constant-target static strategy under **flat** returns (no drift) has
  `turnover = 0` at every rebalance — this is the degenerate case that
  stresses the formula, not the realistic behavior
- A constant-target static strategy under **non-flat** returns has
  strictly positive turnover at most rebalances (drift forces re-targeting)
- A strategy that swaps a 60/40 portfolio to 40/60 has `turnover = 0.2`
  (half the total absolute weight change)
- A strategy that fully swaps to a disjoint allocation has
  `turnover = 1.0` and a single-rebalance cost equal to `cost_rate(date)`
- `cost_rate = 0.0` produces a `BacktestResult` whose `costs` series is
  all zeros and whose `portfolio_value` series equals
  `(1 + portfolio_returns).cumprod()` to floating-point tolerance — this
  is the explicit equivalence with the pre-cost compounding formula
- The default schedule returns `0.003` for 1985-06-15, `0.001` for
  2005-06-15, and `0.0005` for 2020-06-15
- For strategies with non-zero turnover, the post-cost CAGR is strictly
  less than the hypothetical zero-cost CAGR (sanity check that costs
  are actually being applied)

### Known limitations
- No bid-ask spread asymmetry (buys and sells cost the same)
- No market impact scaling with position size
- No slippage from rebalance-day volatility
- No tax drag (out of scope for v1; stretch goal in issue #6)
- No differentiation by asset class (gold, bonds, and equities all pay
  the same rate)

These are acceptable simplifications for a long-horizon wealth-preservation
strategy backtest. Refinements can be added without changing the
`cost_rate` interface.

## Performance metrics

### Required metrics
| Metric | Formula | Notes |
|--------|---------|-------|
| Total return | `final_value / initial_value - 1` | Net of costs |
| CAGR | `(1 + total_return) ^ (1/years) - 1` | Net of costs |
| Volatility | `daily_returns.std() × √252` | Annualized |
| Sharpe ratio | `CAGR / volatility` | Assuming 0 risk-free (simplification) |
| Max drawdown | `min((value - cummax) / cummax)` | |
| Calmar ratio | `CAGR / |max_drawdown|` | |
| Average turnover | `result.turnover.mean()` | Per rebalance, in [0, 1] |
| Total cost drag | `result.costs.sum()` | Sum of per-rebalance cost fractions |
| Cost-adjusted CAGR spread | `CAGR(cost_rate=0) - CAGR(default)` | Optional; requires re-running |

### Future metrics (not yet implemented)
- Sortino ratio (downside deviation only)
- Per-decade breakdown
- Tax-adjusted return (short-term vs long-term gains)

## Data quality

### Purpose

Some date ranges in the asset-returns frame come from model formulas
rather than real prices. Backtests that lean heavily on those periods
should be flagged so analysts don't compare strategies on apples-to-oranges
data. This section defines what the spec considers "approximation only"
and how that surfaces on `BacktestResult`.

### Approximation sources

The following source labels are derived from a model formula, not from
real price or return data:

- `^TNX` — `long_bonds` returns from the duration approximation
  (1975 → 2002-07-29, before TLT splice)
- `GS2_yield` — `short_bonds` returns from the duration approximation
  (1975 → 2002-07-29, before SHY splice)

Exposed as a module-level constant:

```python
APPROXIMATION_SOURCES: frozenset[str] = frozenset({"^TNX", "GS2_yield"})
```

**Proxy sources are NOT approximation sources.** FRED indices used in
place of unavailable price series (`WPUSI019011` for gold, `PPIACO` and
`DCOILWTICO` for commodities) are imperfect tracking of real data, not
derived from a model. They have their own documented tracking error (see
"Proxy series splicing → Known limitations") but the uncertainty class
is different. Analysts who want to flag proxy exposure too can compose
their own predicate against `BacktestResult.asset_sources` directly —
the spec does not collapse the distinction.

### `BacktestResult.approximation_exposure() -> pd.Series`

Returns a series indexed by **rebalance dates** (matching
`weights_history.index`), valued in `[0, 1]`. Each value is the fraction
of portfolio weight at that rebalance allocated to assets whose source on
that date is in `APPROXIMATION_SOURCES`. Useful for plotting alongside
cumulative returns to show when a strategy leaned on approximated data.

Defined at rebalance points rather than daily because (a) intra-rebalance
weight drift is a small effect for the use case (flagging "is this result
trustworthy?"), (b) it keeps the series cardinality manageable for
plotting, and (c) it composes cleanly with the existing per-rebalance
metadata (`weights_history`, `turnover`, `costs`).

### Invariants

- `asset_sources.index` equals `asset_returns.index`
- `asset_sources.columns` equals `asset_returns.columns`
- Every cell of `asset_sources` is a non-empty string on every business
  day where `asset_returns` has a non-NaN value (no NaN, no empty)
- `approximation_exposure()` returns values in `[0, 1]` for every entry
- For a backtest entirely after 2002-07-30 with any bond weights,
  `approximation_exposure()` is all zeros (post-splice; bond returns come
  from TLT/SHY)
- For a backtest with zero bond weights at every rebalance,
  `approximation_exposure()` is all zeros regardless of period

### Test cases

- A backtest from 2010-01-01 with a 50/50 long_bonds/equities static
  strategy has `approximation_exposure()` all zeros (post-splice)
- A backtest from 1980-01-01 to 1985-12-31 with a 50/50
  long_bonds/equities static strategy has `approximation_exposure()`
  equal to 0.5 at every rebalance (pre-splice; bonds are pure
  approximation)
- A backtest spanning 2000-01-01 to 2005-12-31 with constant 100%
  long_bonds shows `approximation_exposure()` transitioning from 1.0
  (rebalances pre-2002-07-30) to 0.0 (rebalances post)
- A backtest with a strategy that allocates 100% equities/cash at every
  rebalance has `approximation_exposure()` all zeros, regardless of
  period (no bond exposure)
- Adding a new approximation source to `APPROXIMATION_SOURCES` and
  rerunning a fixed backtest produces a strictly higher (or equal)
  `approximation_exposure()` series — the metric is monotone in the
  source set

---

## What this spec does NOT cover (exploring)

- Which indicators to use in the regime classifier
- Strategy parameter values
- How civilizational indicators should influence allocation
- Autoresearch experiment design

These are in the "exploring" phase and should not be specced until they stabilize.

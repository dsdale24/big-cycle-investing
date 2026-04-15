# Data-quality review: big-cycle-investing

_Date: 2026-04-15_
_Branch at time of review: main_
_Reviewer: data-quality (Claude subagent)_

**Headline:** Publication lag and data revisions are respected for exactly one indicator (Gini) in one composite; every cyclical signal the backtester's `BigCycleStrategy` actually trades on (CPI, FEDFUNDS, T10Y2Y, debt/GDP) reads current, revised FRED values at rebalance time with no lag — a silent look-ahead that the `APPROXIMATION_SOURCES` surface cannot detect because it only flags *asset-return* approximations.

## What's working

- **Splicing is genuinely audited.** `tests/test_proxy_splicing.py` and `tests/test_bond_splicing.py` enforce the compound-to-monthly invariant, no gap/no overlap at splice dates, and source-label continuity. These are real load-bearing tests.
- **The `BacktestResult.asset_sources` / `approximation_exposure()` surface** is unusually good for a research backtest — analysts can recover data provenance per date/asset without re-fetching. The pre-2002 bond uncertainty is explicitly callable.
- **Bond approximation error was measured, not assumed.** `docs/research/bond_return_validation.md` produced the 3.4 ppt/yr divergence number that forced the TLT/SHY splice. Convexity bias was identified from the sign pattern of divergence across decades.
- **Publication lag primitive exists** (`shift_by_publication_lag` in `src/indicators.py`) and is used correctly for Gini in `internal_order_stress_index`. The mechanism is there — it's just not applied where the trading strategy reads.

## Findings

### 1. Publication-lag discipline is scoped to civilizational composites, not trading signals

The backtester's `BigCycleStrategy._compute_regime_scores` (src/backtester.py:747-800) reads `CPIAUCSL`, `FEDFUNDS`, `T10Y2Y`, `GFDEGDQ188S` via `available_data.get(...)` and truncates only with `.loc[:date]`. CPI for month M is published ~mid-M+1 (two-week lag), GDP for quarter Q is published ~Q+1 month end (one-month lag for advance estimate, more for final). A quarterly rebalance on 2008-03-31 reads Q4 2007 debt/GDP that in reality was not yet available. The look-ahead is small in magnitude (~2-6 weeks) but systematically biased toward the signal: regime classifications around inflection points (2008-Q3, 2020-Q1) see data that a real-time implementation couldn't have. The spec (`specs/data_pipeline.md` §"Walk-forward data availability") explicitly acknowledges this as a known gap ("Assume all data is available on its timestamp date") but this acknowledgment is buried in the data-pipeline spec, not surfaced anywhere a strategy reviewer would look. The `approximation_exposure()` metric cannot catch this because it's defined on asset sources only.

### 2. FRED revisions flow through without vintage handling

FRED serves the currently-revised series. Real GDP, CPI (rebasing), Gini methodology changes, debt/GDP level revisions — none are held to their initial-vintage values. `src/data_fetcher.py:fetch_fred_series` calls `fred.get_series(id, observation_start=...)` with no `realtime_start`/`realtime_end` parameter. A strategy rebalancing on 1980-06-30 reading 1980 GDP is reading the 2020s-revised level, not what was printed in 1980. For strategies that threshold on debt/GDP (`debt_accel`), where revisions have moved the series by several percentage points in retrospect, this is meaningful. Magnitude is hard to quantify without ALFRED integration, but for series with known large revision windows (GDP, especially around recessions) this is a first-order concern for any threshold-based regime classifier.

### 3. WPUSI019011 as gold proxy: tracking error not quantified in-repo

`specs/backtester.md` §"Proxy series splicing → Known limitations" states plainly that WPUSI019011 is metals-and-metal-products PPI, "correlation to actual gold returns is imperfect. This is documented tracking error accepted." But no validation script analogous to `scripts/validate_bond_returns.py` exists for this proxy. The overlap period (post-2000, where both WPUSI019011 and GC=F exist) would let us quantify monthly-return correlation and CAGR divergence the same way bond validation did. Without that number, "imperfect" is a shrug. Given that gold is the active ingredient of the `BigCycleStrategy.overheating` nudge (+10%), and that the 1975-2000 gold returns drive a large fraction of early-period backtest performance, the tracking error of this proxy directly affects reported strategy edge. Estimate: if WPUSI019011↔GC=F monthly correlation is ~0.5 (plausible for a different-but-related commodity), ~50% of pre-2000 gold "signal" is noise — compounded over 25 years that's large.

### 4. PPIACO→WTI→CL=F is a three-instrument semantic splice

The commodities series splices PPI All Commodities (1975-1986, a broad basket: food, fuels, metals, chemicals), WTI spot (1986-2000, pure crude oil), and CL=F futures (2000+, crude futures with contango/backwardation structure). These measure three different things. The spec acknowledges this ("a semantic splice, not just a data-source splice — document it in backtest outputs") but there is no backtest-level flag distinguishing the three regimes. A strategy that allocates to "commodities" in 1980 is buying a PPI basket; in 1990 a WTI spot exposure; in 2010 a futures contract with its own roll yield. CAGR comparisons across periods for commodity-tilted strategies are load-bearing for the overheating hypothesis yet cannot be read cleanly.

### 5. The `APPROXIMATION_SOURCES` set is too narrow to flag measurement uncertainty

`APPROXIMATION_SOURCES = {"^TNX", "GS2_yield"}` flags only duration-model-derived returns. Proxy-derived returns (`WPUSI019011`, `PPIACO`, `DCOILWTICO`) are treated as "real" by this metric even though they have tracking error the spec itself calls out. The spec justifies excluding them ("FRED indices used in place of unavailable price series ... uncertainty class is different ... analysts can compose their own predicate"). But in practice no one composes the predicate — the one-call `approximation_exposure()` is what appears in analysis, and it under-reports uncertainty for any pre-2000 gold/commodities-tilted backtest. For a backtest starting 1975 with 10% gold and 10% commodities, `approximation_exposure()` reports 0 for the non-bond allocation from 1975 to 2000 even though 20% of the portfolio is on proxy data with unquantified tracking error.

### 6. Stationarity assumption for the regime-classifier thresholds

`regime_classifier` in `src/indicators.py:80` uses fixed thresholds: yield curve > 0, inflation < 4, real rate > 0, debt accel > 0 (for expansion); inflation > 4, real rate < 0, debt accel > 2 (overheating). These are calibrated on eyeballed norms of the 1975-2024 US sample — a sample that contains one secular disinflation. The "inflation > 4" threshold separated the 1970s-80s from the 1990s-2010s well, but 4% has no structural claim on being a regime boundary in a different era or country. Any extension of this framework to non-US data or to a future high-inflation regime would need re-calibration. The thresholds aren't tested against out-of-sample data because no out-of-sample data exists in the project yet.

### 7. Fat-tailed returns and crisis-period correlation spike

The asset-returns frame applies daily return clips (±10% for long_bonds, ±5% for short_bonds) in `_long_bonds_approximation`/`_short_bonds_approximation` — reasonable circuit breakers, but they also truncate the exact fat-tail events (2008 October, 2020 March, 1987) that matter most for realistic drawdown modeling. The `Sharpe ratio` metric in `specs/backtester.md` §"Performance metrics" uses mean/std of daily returns; for a strategy concentrated in commodities (2008: -50%+) or gold (1980: -40%+), mean-variance is not a faithful summary. Neither the spec nor the backtester surfaces Sortino, CVaR, or max-drawdown-to-vol ratios at crisis windows. Cross-asset correlation is treated as stationary throughout; no instrument in the backtester measures the "correlations spike toward 1 in crises" effect, which is load-bearing for diversification-is-free arguments.

### 8. Missing-data policy is "fill with 0, label the source"

`build_asset_returns` at line 524 does `returns = returns.fillna(0)` after source labels are assigned. The spec permits this on holidays and at segment-first days where `pct_change()` is NaN. But this also silently zero-fills any gap in upstream data (FRED server miss, Yahoo throttle — see `specs/data_pipeline.md` §"Error handling"). A week of 0 returns on commodities in 1993 because of a FRED fetch gap is indistinguishable in the return series from a week where commodities truly didn't move. The `ZERO_FILL_SOURCE` sentinel exists for the legitimate no-coverage case but isn't used to distinguish "real zero" from "missing, zero-filled." An upstream data health check would catch this; none exists in `tests/` beyond "did the fetch succeed."

## Data-period confidence matrix

| Asset class | 1975-1985 | 1986-1999 | 2000-2002 | 2002-2024 |
|---|---|---|---|---|
| equities | HIGH (^GSPC) | HIGH (^GSPC) | HIGH (^GSPC) | HIGH (^GSPC) |
| long_bonds | APPROXIMATION (^TNX, duration=8, no convexity) | APPROXIMATION | APPROXIMATION | HIGH (TLT Adj Close) |
| short_bonds | APPROXIMATION (GS2 monthly ffill to daily, corr 0.77 vs SHY in overlap) | APPROXIMATION | APPROXIMATION | HIGH (SHY Adj Close) |
| gold | PROXY (WPUSI019011, tracking error unquantified) | PROXY | PROXY → primary transition 2000-08-30 | HIGH (GC=F, futures roll not modeled) |
| commodities | PROXY (PPIACO, different-basket semantic splice) | PROXY (DCOILWTICO, WTI spot) | PROXY → primary transition 2000-08-23 | MEDIUM (CL=F futures, roll yield & contango unmodeled) |
| cash | MEDIUM (FEDFUNDS monthly ffill; no publication lag) | MEDIUM | MEDIUM | MEDIUM |

Label counts: HIGH 9, MEDIUM 6, APPROXIMATION 6, PROXY 7. The 1975-2000 block is approximation-or-proxy for every asset except equities and cash.

## The single-largest unaudited risk

**WPUSI019011's tracking error vs. real gold returns has never been measured in this repo, yet the 1975-2000 gold proxy is load-bearing for every early-period backtest conclusion, including every claim about `BigCycleStrategy`'s overheating nudge.** The bond-return validation project (#8) produced a clear accept/reject with measured divergence. The equivalent analysis for WPUSI019011 vs. GC=F monthly returns over the 2000-2024 overlap period would take one script, same shape as `scripts/validate_bond_returns.py`. Until it exists, "the proxy tracks directionally" is an unquantified claim. If the measured correlation is below ~0.6 (plausible — metals PPI is dominated by industrial metals, gold is 60% investment demand), the 1975-2000 gold allocation contributes mostly noise, and the pre-2000 portion of any gold-tilted strategy's reported Sharpe is not interpretable.

## Recommendations

1. **Validate WPUSI019011 as a gold proxy.** Mirror `scripts/validate_bond_returns.py` against GC=F over 2000-2024. Record in `docs/research/gold_proxy_validation.md`. If correlation < 0.90 (the same bar used for bonds), either accept the proxy with documented uncertainty or flag pre-2000 gold as approximation-class rather than proxy-class.
2. **Add publication lag to cyclical indicators read by `BigCycleStrategy`.** CPI: 14 days. GDP / debt/GDP: 45 days (advance) or 90 days (final). FEDFUNDS: ~1 day. Implement as a `publication_lag_days` field in `configs/series.yaml` and apply in the backtester's `.loc[:date - lag]` truncation (the future-improvement path already in the data-pipeline spec).
3. **Extend `APPROXIMATION_SOURCES` or add a peer predicate `PROXY_SOURCES`.** The one-call analysis surface should reflect proxy uncertainty, not just duration-model uncertainty. Analysts won't compose the predicate themselves.
4. **Document the PPI/WTI/futures semantic splice on `BacktestResult`.** A `commodities_era` attribute or note field that any plot can surface, so no one compares pre-1986 and post-2000 commodity CAGR without the semantic warning.
5. **Vintage-data audit.** For one pivotal rebalance date (e.g., 2008-09-30), compare the ALFRED vintage debt/GDP and GDP values to the currently-served values. If divergence is large, decide whether to move to ALFRED-backed fetching or accept and document the revision bias.

## Questions worth sitting with

1. Is the gold proxy's tracking error a research-time concern, or is the 1975-2000 window already so approximation-heavy on the bond side that gold's tracking error is a second-order issue? (Answer probably depends on strategy concentration.)
2. Should the project adopt a "real-time" data mode that uses FRED vintage data (via ALFRED) as the canonical walk-forward source, reserving the current mode for diagnostic runs?
3. For the eventual cross-national extension (thesis: transition-scale data), will the same proxy/approximation discipline be re-applied, or will cross-national data quality be even worse and dominate measurement uncertainty?

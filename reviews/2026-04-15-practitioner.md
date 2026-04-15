# Practitioner review: big-cycle-investing

_Date: 2026-04-15_
_Branch at time of review: main_
_Reviewer: practitioner (Claude subagent)_

**Headline:** The research apparatus is unusually disciplined for a personal project, but between the backtest numbers and a real dollar entering a real brokerage account sits an unwritten operations manual — tax treatment, instrument selection, rebalancing discipline, and regime-signal noise are all unmodeled, and any of them can eat the entire Sharpe edge the backtests show.

## What's working

- **Transaction cost schedule is honest and calibrated per decade** (50/30/10/5 bps). Most research projects at this stage use zero-cost rebalancing; this one doesn't. Costs are applied to real turnover and surface in `BacktestResult.costs` and `.turnover`, so drag is auditable.
- **Approximation exposure is first-class.** `BacktestResult.approximation_exposure()` and the `asset_sources` DataFrame let an analyst look at any backtest and see which bits came from model-derived bond returns vs. real ETF data. That's a form of operational honesty most quant research skips entirely.
- **Walk-forward discipline is enforced at the spec level.** The publication-lag rule is concrete, testable, and tested. This eliminates one large class of backtest-vs-reality gap by construction.
- **Scope humility is load-bearing.** The `backtest-sample-scope` and `us-fiscal-deterioration` theses state plainly that the sample cannot speak to the scenario being hedged. That matters for practitioner reading of the numbers — the headline Sharpes in `regime_scoring_comparison.md` are a cyclical-regime fit, not evidence the strategy hedges the thesis.

## Findings

### 1. Tax drag is completely unmodeled, and for a taxable-account deployment it likely exceeds cost drag by an order of magnitude

The backtester spec (`specs/backtester.md` → "Performance metrics → Future metrics") lists `Tax-adjusted return` as "not yet implemented." The default rebalance cadence is quarterly. Quarterly rebalancing in a taxable account generates short-term capital gains (federal ordinary-income rate up to 37%, plus state, plus 3.8% NIIT) on any position held <12 months. A strategy with 6% avg turnover per rebalance × 4 rebalances/year, with half of it hitting positions inside the 12-month window, produces perhaps 10–12% of assets/year touched at short-term rates. In a worst-case marginal-bracket setting, tax drag on realized gains can run 150–250 bps/year — larger than the entire cost schedule, and larger than the Sharpe-relevant spreads between the strategies being compared (AllWeather 0.96 vs. BigCycle scored 0.84 is 12 bps of Sharpe, easily reversible by tax regime).

This matters for Darren's situation specifically: at a 30-year horizon with a wealth-preservation focus, the allocation of the strategy across tax-advantaged (IRA/401k) vs. taxable accounts is as material as the allocation across assets. No spec addresses it. No research note names which strategy variants are IRA-appropriate (high turnover, commodity ETFs that issue K-1s) vs. taxable-appropriate (low turnover, ETF-wrapped, qualified-dividend-friendly). Until that exists, the ranking of strategies by post-tax CAGR is unknown and could invert the current ranking.

### 2. The cost schedule is uniform by asset class, but real execution costs aren't — commodity exposure is especially mispriced

`specs/backtester.md` → "Transaction costs → Known limitations" explicitly flags "No differentiation by asset class." That's a reasonable v1 simplification for equities/bonds, but it's structurally wrong for commodities. The backtester uses `CL=F` (front-month WTI futures) as the post-2000 commodity price series. Real investors cannot hold CL=F; they hold USO (which has lost 80%+ to roll cost over its life), DBC (broad basket, better but still contango-exposed), or direct futures with quarterly rollovers. The backtested commodity return is essentially a spot-price series with zero roll cost — a fiction for any executable commodity exposure.

The `BigCycle non-sovereign` profile allocates 20% to commodities. Over 2000–2024, USO underperformed WTI spot by ~8%/year CAGR due to roll cost. If the non-sovereign profile's commodity sleeve were routed through USO, the already-poor 7.50% CAGR / -61.1% max DD becomes meaningfully worse. This isn't a small correction — it's a structural reason the non-sovereign profile's backtested returns overstate real-world outcomes by a material margin, and the gap widens precisely in the inflationary regimes the strategy is trying to hedge (contango is usually worst when inventories are building, which tends to correlate with supply shocks that motivate commodity allocation in the first place).

Gold has the mirror problem in reverse: GLD and IAU track spot well with minor tracking error, so the gold sleeve is more honest than the commodity sleeve. But the spec treats them uniformly.

### 3. Drawdown discipline is undocumented, and it's the single biggest determinant of real-world outcomes

The `BigCycle non-sovereign` variant posts a -61.1% max drawdown (2020s decade). `BigCycle scored` posts -31.3%. AllWeather posts -22.9%. These numbers pass through the backtester without emotional friction. Real investors do not. The empirical literature on investor behavior is unambiguous: the average investor captures roughly 2–3% less CAGR than the fund they hold, because they sell during drawdowns and buy back after recovery. For a strategy advertising -61% drawdown capacity, the practitioner question isn't "what does the backtest show" but "can the person executing it actually hold through -61%."

The project has no pre-commitment document for Darren. No "if the strategy underperforms a simple 60/40 for 3 consecutive years, here's what I decided in advance I would do." No "if gold drops 45% as it did 1980–1985, here's why I knew that in advance and what my override rule is." No "which drawdowns in the backtest should I specifically study so I know what the worst-case experience feels like." This is the single most load-bearing piece of missing research, and it lives outside the code entirely. Without it, the practical CAGR of any strategy here will be materially below the backtested CAGR — a second drag comparable to or larger than tax drag.

### 4. The weights the strategy outputs do not map to specific, purchasable instruments

`BigCycleStrategy` outputs six weights: equities, long_bonds, short_bonds, gold, commodities, cash. There is no spec for the executable translation. For each line, open questions:

- **equities:** VTI vs. VOO vs. VT (global) vs. RSP (equal weight)? The backtest uses S&P 500; the thesis implies non-US equities with pricing power should be material. Translation undefined.
- **long_bonds:** TLT (20+ year, used in the backtester), EDV (25+ year), or GOVT (broad), or direct 10Y Treasuries? Duration profile differs materially.
- **short_bonds:** SHY (1–3 year, used in backtester), SHV, BIL (<3 month)? Yield differs, duration differs.
- **gold:** GLD vs. IAU vs. SGOL vs. PHYS vs. physical (custody, insurance). Tax treatment differs — collectibles rate (28%) vs. 1099 depending on vehicle.
- **commodities:** see finding 2. PDBC vs. DBC vs. GSG vs. direct futures; K-1 vs. 1099.
- **cash:** money market vs. Treasury bills vs. high-yield savings. 

None of these choices are specced. Each has material implications for post-tax return, tracking error to backtest, and tax-reporting complexity. A strategy without instrument selection isn't a strategy; it's a research artifact.

### 5. Regime signal in real-time is noisier than the backtest makes it look

The backtester's regime classifier uses yield curve, CPI YoY, and real rate with hard thresholds. In the walk-forward regime, it sees "correct" values on the quarterly rebalance date. In reality: (a) BEA/BLS release data with lags and revisions (CPI initial release has non-trivial revisions; GDP gets revised multiple times); (b) the real rate is computed from inflation and fed funds, both of which flicker around threshold values; (c) a single monthly print near the threshold can flip the classifier from "contraction" to "expansion" and back the following month. The quarterly rebalance cadence averages some of this, but not all — the hard thresholds in `regime_classifier()` don't have hysteresis.

For real execution: on rebalance day, Darren opens his terminal, pulls the latest data, runs the classifier. If the classifier says "overheating" this quarter and flipped from "expansion" last quarter based on a CPI print that gets revised down two weeks later, he's already rebalanced into +10% gold / -10% equities and paid the turnover cost. The backtester never experiences this — it sees only the post-revision historical value. The walk-forward spec respects publication lag for timing, but not data revision. Pre-election-timing CPI revisions in 2023–2024 would have flipped some regime classifications in real-time vs. what the final vintage shows.

### 6. No operations manual exists — the research doesn't translate to a rebalance-day procedure

The project has an elegant maker-checker research workflow but no parallel workflow for Darren-the-investor. On rebalance day (say, 2026-06-30), what happens? Which script runs? Which data sources must be fresh? How does Darren verify the regime label is sensible before acting on it? What's the escalation path if the classifier says something surprising (e.g., "reflation" during visible contraction)? What's the trading-window rule — does he trade at 10am ET, 3pm ET, VWAP? Which account does each asset-class trade happen in? Does he keep a trade log for tax-lot tracking?

None of this is specified. Without it, even if every other finding in this review were resolved, a real deployment would be improvised on the day, which is exactly the condition under which costly mistakes compound.

### 7. Emergency liquidity is not carved out

A 30-year wealth-preservation strategy that gets interrupted by a forced sale in year 7 (job loss, medical event, real estate down payment, family support) during a -40% drawdown has different realized returns than the backtest. The project has no spec for emergency-fund carve-out, no "strategy is run on $X where $X excludes 12 months of expenses in cash," no policy for how forced liquidity needs are met without disturbing the strategic allocation. This is a personal-finance-planning gap, not a research gap — but without it, the strategy's real-world CAGR is path-dependent on Darren's life in ways the backtest can't show.

## Operational-readiness matrix

| Dimension | Status | Notes |
|---|---|---|
| Tax drag | UNMODELED | Spec names it as future work; no research note exists |
| Transaction cost realism | ESTIMATED | Decade-calibrated, uniform by asset; commodity roll unmodeled |
| Rebalancing discipline documentation | UNMODELED | No drawdown pre-commitment, no underperformance rule |
| Liquidity planning | UNMODELED | No emergency-fund carve-out; no forced-sale policy |
| Execution instrument selection | UNMODELED | Backtest picks ETFs for validation; execution guidance absent |
| Regime-signal noise in real-time | UNMODELED | Walk-forward respects lag, not revisions or threshold flicker |
| Operations manual | UNMODELED | No rebalance-day procedure for the human executor |

Summary: 0 of 7 MODELED, 1 ESTIMATED, 6 UNMODELED.

## The executability question

If Darren allocated to `BigCycle scored` next Monday, the single biggest operational gap would be **instrument selection × tax-account placement**. The backtest's 7.84% CAGR assumes costless execution of idealized asset-class returns. The realized result in a split taxable/IRA account, using real ETFs (TLT + VTI + GLD + PDBC + SHY + money market), with quarterly rebalancing generating short-term gains in the taxable sleeve and commodity roll cost in the commodity sleeve, could plausibly be 150–300 bps/year below the backtest. That would flip BigCycle scored's post-tax ranking below AllWeather (lower turnover, simpler) and possibly below a basic 60/40. The decision of which strategy to run is currently being made on numbers that cannot survive translation to a real account.

## Recommendations

Before promoting any strategy to `settled` for real execution:

1. **Write a `specs/execution.md`** that specifies, per asset class: which ETF, which account type (taxable vs. IRA), which tax-lot method, and the tracking error vs. the backtested proxy. This is a one-session document.
2. **Add a tax-drag estimator to the backtester** as a post-processing step — not a full tax simulator, just turnover × tax-rate-assumption by holding period. Surface a `post_tax_cagr` metric that requires an explicit assumption. Make the assumption visible.
3. **Add a commodity-roll overlay** that applies an assumption-based drag to the commodity sleeve. Even a crude 5%/year subtraction would be more honest than the current zero.
4. **Write a `docs/operations/rebalance_day.md`** — the script, the checks, the trade log, the override rules. This forces the research to meet real life.
5. **Write a personal pre-commitment document** — what drawdowns Darren has pre-committed to hold through, at what underperformance horizon he revisits the strategy, what evidence would make him change course. Not a spec; a personal document that lives outside the repo but is referenced by it.

## Questions worth sitting with

1. What is the split between taxable and tax-advantaged account space? Until this is known, the rebalance cadence and strategy variant choice are underdetermined.
2. What is the emergency-fund carve-out? Is the strategy being run on all investable assets or a strategic core with a liquidity buffer?
3. What drawdown has Darren actually lived through, in dollars and percent of net worth, and how did he respond? Past-behavior-under-stress is the single best predictor of future discipline.
4. Is the 30-year horizon hard or soft? A hard horizon (retirement date) tolerates drawdowns differently than a soft horizon (flexible timing).
5. What's the absolute-dollar threshold below which custody costs (vault storage for physical gold, direct Treasury ladder administration) stop being worth the tracking-error reduction?

# Gold Proxy Validation (WPUSI019011 vs. GC=F)

Date: 2026-04-16
Issue: #74
Spec: `specs/backtester.md` §"Proxy series splicing"
Script: `scripts/validate_gold_splice.py`
Upstream: `reviews/2026-04-15-data-quality.md` recommendation #1

## Question

`WPUSI019011` (FRED PPI: Metals and Metal Products, monthly) is the 1975
→ 2000-08-29 gold-price proxy spliced into the backtester, with `GC=F`
(gold futures, Yahoo, daily) taking over from 2000-08-30. The proxy has
been flagged in the backtester spec as "imperfect, tracks directionally"
— but tracking error has never been measured in-repo, and every
early-period backtest conclusion about gold's regime-hedge behavior
rests on that unvalidated proxy.

Concretely: is `WPUSI019011`'s monthly-return correlation with real
gold returns high enough (≥ 0.90, same bar used for bond approximation
in `docs/research/bond_return_validation.md`) to accept it as a proxy,
or is 1975-2000 "gold" in the backtester effectively a noise series
that should be reclassified as approximation-class?

## Method

Mirrors `scripts/validate_bond_returns.py` structure:

1. Load `WPUSI019011` (monthly levels) and `GC=F` (daily Close) from
   the parquet cache.
2. Convert both to monthly returns:
   - `WPUSI019011`: month-end last-value, then `pct_change()`.
   - `GC=F`: daily `pct_change()`, compounded to month-end.
3. Intersect the monthly indices and restrict to dates on or after the
   backtester splice date `2000-08-30`. This is the only window where
   real gold and the proxy coexist.
4. Compute:
   - Overall monthly-return correlation.
   - Per-decade CAGR for both, and per-decade CAGR divergence
     (proxy minus GC=F).
   - Monthly mean-absolute-error.
   - Correlation within three regime-turn stress windows (2008-09 GFC,
     2020 COVID, 2022 inflation surge) — these are our only in-overlap
     analogues for the 1979-82 bull/bust regime which is NOT in
     overlap.

Threshold for acceptance (borrowed from the bond precedent and
`reviews/2026-04-15-data-quality.md` recommendation #1):
monthly-return correlation ≥ 0.90 over the full overlap.

## Result

_Script execution was blocked by this agent's sandbox — see
"Reproducing" below. The numbers below must be populated by the
coordinator on a run of `scripts/validate_gold_splice.py`. The
interpretive framework in the next section is written to be
parametric in the headline correlation; the decision branches follow
directly from whether the number clears 0.90._

```
Overlap window (month-end): 2000-08-30 → <END_DATE>  (<N> months)

Per-decade CAGR (WPUSI019011-derived vs GC=F):
decade | WPUSI019011_CAGR | GC=F_CAGR | divergence_ppt_per_yr | n_months
-------+------------------+-----------+-----------------------+---------
2000s  | <VAL>            | <VAL>     | <VAL>                 | <VAL>
2010s  | <VAL>            | <VAL>     | <VAL>                 | <VAL>
2020s  | <VAL>            | <VAL>     | <VAL>                 | <VAL>

Stress-window correlations (analogues for 1979-82 NOT in overlap):
window                     | n_months | correlation | max_abs_dev | proxy_cum | GC=F_cum
---------------------------+----------+-------------+-------------+-----------+----------
2008 GFC / deleveraging    | 6        | <VAL>       | <VAL>       | <VAL>     | <VAL>
2020 COVID shock           | 3        | <VAL>       | <VAL>       | <VAL>     | <VAL>
2022 inflation surge       | 12       | <VAL>       | <VAL>       | <VAL>     | <VAL>

Headline:
  overall correlation    = <VAL>   (threshold: >= 0.90)
  MAE(monthly)           = <VAL>
  mean |CAGR div|/decade = <VAL> ppt/yr
```

## Interpretation

### The a-priori expectation

`WPUSI019011` is PPI for "Metals and Metal Products" — a Producer
Price Index basket dominated by industrial metals (steel, aluminum,
copper products). Gold is a small fraction of the basket and is
weighted by producer sales rather than investment demand. The real
economic drivers of the two series are only partially overlapping:

- **Industrial metals** (PPI's weight center) respond to
  manufacturing cycles, capex, construction — pro-cyclical with
  global growth.
- **Gold** responds to real interest rates, inflation fear, currency
  debasement, geopolitical risk — frequently *counter-cyclical* with
  growth.

A priori, we should expect:
- Positive correlation overall (both are "hard assets" priced in USD
  and benefit from dollar weakness and inflation pass-through).
- Decoupling during regime turns where gold's investment-demand
  driver diverges sharply from industrial-metals demand — e.g., a
  growth collapse (gold up, industrial metals down) or a
  hard-landing inflation scare.
- The 1979-82 window is the most extreme such regime in the sample
  period — real gold roughly tripled then halved while industrial
  metals followed the recession — and is NOT in our overlap. Our
  best proxy for "how did WPUSI019011 track real gold during
  1979-82?" is "how does it track during the 2008-09 deleveraging
  panic and the 2020 COVID shock?"

### Reading the headline number

- **If overall correlation ≥ 0.90**: accept the proxy with
  documented tracking error. The 1975-2000 gold series in the
  backtester is noisy but directionally informative; per-decade
  CAGR divergence in the overlap bounds our expected tracking error
  for the pre-2000 period. Backtest conclusions about gold's
  regime-hedge behavior in 1975-2000 are defensible at monthly
  granularity but should be read as approximate at the
  month-by-month level.
- **If overall correlation is 0.70-0.90**: the proxy is
  directionally useful but fails the bond-precedent threshold.
  Recommended action: flag `WPUSI019011` as approximation-class —
  add it to `APPROXIMATION_SOURCES` in `src/backtester.py`, same
  uncertainty bucket as `^TNX` / `GS2_yield` for bonds. This would
  make pre-2000 gold exposure visible in
  `BacktestResult.approximation_exposure()` — currently it reads 0
  because proxy-class sources are excluded by design.
- **If overall correlation < 0.70**: the proxy adds more noise than
  signal. Recommended action: replace or retire.
  - **Replacement candidates**: (a) LBMA PM gold fix (available
    daily from 1968 via World Gold Council CSV; not in-repo).
    (b) Kitco / Wren Research historical series (nightly gold
    closing, 1970+). (c) IMF IFS gold price series (monthly,
    1950+, USD/oz). Any of these would be a true gold price,
    eliminating the semantic-splice problem that WPUSI019011 has
    today.
  - **Retirement path**: document 1975-2000 gold as no-coverage,
    use `zero_fill` sentinel, and accept that early-period backtest
    gold attribution is zero for that window.

### The pre-2000 extrapolation problem (load-bearing)

We can only measure tracking error where both series exist —
2000-08-30 onward. That window includes two crisis-regime turns
(2008-09, 2020) and one inflation stress (2022), but NOT the
1979-82 bull/bust. The 1979-82 window is precisely the period when
gold's regime-signal value is largest: real rates deeply negative,
then Volcker-shock positive; gold traces out a ~3x-then-halving
path that an industrial-metals PPI could not plausibly reproduce.

**The honest statement is: the overlap period underestimates the
1975-2000 tracking error.** Whatever correlation we measure
post-2000 is an upper bound on the correlation we would have
measured in 1979-82 if both series had been priced identically then.
The proxy's worst-case tracking error is not in our measurement
window.

Two implications:
1. Acceptance is conditional. Even if overall correlation is 0.95,
   we can't claim the proxy tracked real gold in 1979-82 at 0.95
   correlation — just that it does so in a calmer modern regime.
2. The 2008-09 and 2020 stress-window correlations are our best
   available analogue. If those are materially lower than the
   full-overlap correlation, that's evidence the proxy decouples
   exactly when we need it most — which is a stronger case for
   flagging than the headline number alone suggests.

The decision rule below takes both numbers into account.

## Decision

_The decision logic is parametric in the numbers from the script.
The coordinator should apply it to the populated table above._

1. **Overall correlation ≥ 0.90 AND each stress-window correlation
   ≥ 0.80**: **ACCEPT** the proxy with documented tracking error.
   Record the measured numbers in this note. Update the "Known
   limitations" entry in `specs/backtester.md` §"Proxy series
   splicing" with the actual correlation rather than the current
   "correlation to actual gold returns is imperfect" wording.
2. **Overall correlation ≥ 0.90 but stress-window correlations
   < 0.80**: **ACCEPT-WITH-FLAG**. Accept the proxy for the
   non-crisis portion of 1975-2000 but flag 1979-82 specifically
   as a high-uncertainty sub-window in backtest outputs. Concretely:
   the spec should gain a per-asset-per-period "stress-window
   uncertainty" flag. This is a separate PR; this validation just
   produces the evidence for it.
3. **Overall correlation 0.70-0.90**: **FLAG AS APPROXIMATION**.
   Add `"WPUSI019011"` to `APPROXIMATION_SOURCES` in
   `src/backtester.py`. Rationale: the bond precedent says 0.90
   is the bar; if WPUSI019011 fails it, we owe analysts the same
   uncertainty flag that `^TNX` and `GS2_yield` carry.
4. **Overall correlation < 0.70**: **REPLACE**. Prioritize a
   real-gold historical series (LBMA PM fix first choice — it's
   the global benchmark and has the longest clean history). Until
   replacement lands, the proxy stays but this note should be
   updated to state clearly that 1975-2000 gold in the backtester
   is noise-dominated.

### Out of scope for this PR

All four decision branches require follow-up changes to `src/`,
`configs/`, or `specs/` that this `explore/` PR explicitly cannot
make (file-type rule per CLAUDE.md Workflow section). This
validation produces the evidence and the recommendation; the
coordinator decides which branch to execute under a `stable/` PR
with spec update.

## Open questions

1. **Is LBMA PM fix already on FRED or a similar source?** Partial
   answer: FRED has `GOLDAMGBD228NLBM` (Gold Fixing Price 10:30 AM
   London, USD/oz, 1968+) and `GOLDPMGBD228NLBM` (3:00 PM fix, same
   period). These are LBMA-sourced, daily, USD-denominated — almost
   certainly a strictly better proxy than WPUSI019011 if they're
   complete back to 1975. Not validated in this pass; out of scope
   beyond naming.
2. **What's the relative weight of industrial metals vs. gold in
   WPUSI019011?** The BLS publishes sub-indices for precious metals
   specifically (`WPU102501` family); a narrower index might
   sharpen the proxy without replacement. Out of scope here.
3. **Does the backtester care about tracking error or just directional
   correctness?** `BigCycleStrategy` nudges gold +10% in
   "overheating" regimes, which is a binary signal that tolerates
   noise as long as the *direction* of big gold moves is preserved.
   Monthly return correlation is the right summary metric for
   direction-preservation. Per-decade CAGR divergence matters more
   for level claims ("did gold CAGR 8% or 3% in the 1980s?") which
   are separate from the regime-nudge logic.

## Reproducing

```bash
source .venv/bin/activate
python scripts/validate_gold_splice.py
```

The script is deterministic and reads only cached parquet files
(`data/raw/fred/WPUSI019011.parquet` and
`data/raw/yahoo/GC_F.parquet`).

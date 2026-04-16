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
3. Intersect the monthly indices on month-end alignment. The
   backtester splice date is `2000-08-30`; the month-end-aligned
   overlap starts at `2000-08-31`. This is the only window where
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

Script was run by the coordinator on 2026-04-16 against the parquet
cache. Output is reproduced verbatim below.

```
Loading cached WPUSI019011 (FRED) and GC=F (Yahoo)...
  WPUSI019011 monthly returns: 1975-02-28 → 2026-03-31  (614 months)
  GC=F monthly returns:        2000-08-31 → 2026-04-30  (309 months)
  Overlap window (month-end-aligned): 2000-08-31 → 2026-03-31  (308 months)

Per-decade CAGR comparison (WPUSI019011-derived vs GC=F):
decade | WPUSI019011_CAGR | GC=F_CAGR | divergence_ppt_per_yr | n_months
-------+------------------+-----------+-----------------------+---------
2000s  | +12.76%          | +15.86%   | -3.09                 | 113
2010s  | -1.00%           | +3.33%    | -4.33                 | 120
2020s  | +10.67%          | +19.59%   | -8.91                 | 75

Regime-turn stress windows (analogues for 1979-82 NOT in overlap):
window                  | start      | end        | n_months | correlation | max_abs_deviation | proxy_cum_return | gold_cum_return
------------------------+------------+------------+----------+-------------+-------------------+------------------+----------------
2008 GFC / deleveraging | 2008-10-01 | 2009-03-31 | 6        | -0.017      | 34.27%            | -42.24%          | +5.54%
2020 COVID shock        | 2020-02-01 | 2020-04-30 | 3        | 0.366       | 9.85%             | -10.25%          | +6.40%
2022 inflation surge    | 2022-01-01 | 2022-12-31 | 12       | 0.491       | 9.74%             | -4.98%           | -0.43%

Headline numbers (WPUSI019011 vs GC=F, monthly):
  overlap               = 2000-08-31 → 2026-03-31  (308 months)
  correlation           = 0.097  (threshold: >= 0.90)
  MAE(monthly)          = 4.497%
  mean |CAGR div|/decade= 5.44 ppt/yr
  correlation verdict   = FAIL
```

## Interpretation

### The 2008 GFC finding is decisive

During the six months spanning 2008-10 through 2009-03 — the
deleveraging-phase flight-to-quality window that is the single most
important regime-turn in the modern backtest period — the proxy and
real gold did not merely track poorly. They went in opposite
directions, violently.

- **Monthly-return correlation: -0.017** — statistically
  indistinguishable from zero, and directionally *negative*.
- **Proxy cumulative return over the window: -42.24%.**
- **Real gold (GC=F) cumulative return over the window: +5.54%.**
- **Maximum single-month absolute deviation: 34.27 percentage
  points.**

A proxy that loses 42% while the thing it is supposed to proxy gains
5.5% during the most important regime turn in 30 years is not a
noisy approximation of gold. It is measuring a different thing.

This is the load-bearing evidence. Every other number below is
consistent with it. The overall monthly correlation over 308
months is **0.097** — an order of magnitude below the 0.90
bond-precedent threshold, and below even a generous 0.70 "directionally
useful" floor. Monthly MAE of 4.5% is large relative to gold's
monthly volatility. Per-decade CAGR divergence averages 5.44
percentage points per year, with the 2020s window showing an
8.91-ppt/yr gap (proxy +10.67% vs. real gold +19.59%). Even the
less-severe stress windows (2020 COVID, 2022 inflation) produce
correlations of 0.37 and 0.49 — useful ceilings on how well the
proxy behaves in *calmer* regime turns, and both are far below the
threshold.

### The a-priori expectation, now confirmed with evidence

`WPUSI019011` is PPI for "Metals and Metal Products" — a Producer
Price Index basket dominated by industrial metals (steel, aluminum,
copper products). Gold is a small fraction of the basket and is
weighted by producer sales, not investment demand. The a-priori
expectation was that the two series would decouple during regime
turns where gold's investment-demand driver diverges from
industrial-metals demand.

The 2008-09 result is the strongest possible confirmation:
industrial metals collapsed with the growth shock (proxy -42%)
while gold rose on flight-to-quality investment demand (+5.5%).
The proxy is essentially a metals-industry PPI index tracking
industrial demand; gold as a wealth-preservation asset is dominated
by investment demand and flight-to-quality. These are different
economic drivers, and during the regime turns we care about most,
they diverge sharply and in opposite directions.

### The pre-2000 extrapolation problem, sharpened

We can only measure tracking error where both series exist —
2000-08-31 onward. That window does NOT contain the 1979-82
bull/bust (gold tripling to ~$850/oz then halving through the
Volcker shock), which is precisely the period when gold's
regime-signal value is largest in the 1975-2000 backtest window.

Earlier drafts of this note framed the 2000s overlap as an upper
bound on 1979-82 tracking: "whatever correlation we measure
post-2000 is an upper bound on what we would have measured in
1979-82." The 2008 GFC result sharpens that framing.

2008-09 is the closest in-overlap analogue we have to 1979-82:
a regime turn dominated by flight-to-quality into gold while
industrial metals follow a growth collapse. The proxy's
correlation in that window was **-0.017**, and it went the wrong
direction by 48 percentage points cumulatively. There is no
plausible reading of this evidence under which the proxy would
have tracked real gold through the 1979-82 bull/bust. The 1970s
stagflation had an even sharper gold-industrial-metals decoupling
than 2008-09: real rates were deeply negative and then
Volcker-shock positive, with gold investment demand spiking on
inflation and currency-debasement fear while industrial metals
followed the 1980-82 recession down.

**The honest statement is: the proxy almost certainly failed worse
in 1979-82 than in 2008-09.** We have no reason to expect it
tracked real gold at any level of usefulness during the single
most important gold-regime window in the 1975-2000 backtest
sample.

## Decision

**REPLACE `WPUSI019011` with the LBMA PM fix (FRED:
`GOLDPMGBD228NLBM`).**

The parametric decision rule stated in the method section had four
branches keyed on overall correlation. The measured overall
correlation is **0.097**. That fires the `< 0.70` REPLACE branch
unambiguously — it is an order of magnitude below the REPLACE
threshold, not a borderline call. The stress-window evidence
(2008 GFC correlation -0.017, cumulative divergence 48 ppt)
independently confirms the same conclusion: the proxy fails
catastrophically in exactly the regime turns gold is meant to
hedge. There is no reading of these numbers that permits any of
the softer branches (ACCEPT, ACCEPT-WITH-FLAG, FLAG AS
APPROXIMATION).

**Replacement candidate: `GOLDPMGBD228NLBM`** (Gold Fixing Price
3:00 PM London, USD/oz, LBMA, daily, 1968+) on FRED. Strictly
better than `WPUSI019011` on every dimension: it is a true gold
price, it covers the full 1975-2000 pre-GC=F window, and it is
already published in the same data source (FRED) that the
project's other macro series come from. `GOLDAMGBD228NLBM` (10:30
AM fix) is an equivalent alternative; either works.

### Material backtest implication (do not soften)

Every BigCycleStrategy result from the 1975-2000 portion of the
backtest that depends on gold-allocation behavior during
deleveraging, stagflation, or flight-to-quality regimes is not
trustworthy on the current proxy. The project's theses about gold
as an inflation / transition / wealth-preservation hedge — to the
extent that evidence for those theses comes from 1975-2000
backtest behavior — are compromised until the splice is fixed.

The 1979-82 bull/bust, the single most important regime window in
the pre-GC=F sample, is exactly the window where the 2008 GFC
evidence tells us the proxy would have failed worst. Any thesis
evidence log entry that cites pre-2000 backtest gold performance
as support should be re-examined after the splice swap lands. This
includes:

- Any "gold hedged 1970s stagflation in BigCycleStrategy" reading.
- Any 1975-2000 per-decade gold-CAGR number in backtest output.
- Any regime-classifier evaluation that uses 1975-2000 gold
  returns as an input signal.

### Spec contradiction flag

`specs/backtester.md` § "Known limitations" currently states that
`WPUSI019011` "tracks directionally" with real gold. **This
statement is false.** A monthly correlation of 0.097 is not
directional tracking. The 2008 GFC window shows the proxy moving
in the *opposite* direction from real gold over a 6-month regime
turn, with a 48-ppt cumulative-return gap. The spec text needs
to be corrected as part of the follow-up splice-swap PR; this
note flags the contradiction but does not fix it (spec authorship
is coordinator-owned per CLAUDE.md).

### Follow-up actions (out of scope for this PR)

These are required to execute the REPLACE recommendation; all
require `stable/` branches per the file-type heuristic and are
explicitly out of scope for this `explore/` PR:

1. **Add `GOLDPMGBD228NLBM` to the data pipeline.** New entry in
   `configs/series.yaml`, fetched via the existing FRED path in
   `src/data_fetcher.py`. No new code needed, just a new series
   id.
2. **Update `src/backtester.py` splice logic** to use
   `GOLDPMGBD228NLBM` for the pre-2000 window instead of
   `WPUSI019011`, with `GC=F` still taking over on 2000-08-30
   (the LBMA series continues past that date, so this is a
   cleanup choice rather than a necessity — documenting the
   choice is part of the follow-up spec update).
3. **Update `specs/backtester.md` § "Proxy series splicing" and
   § "Known limitations"**: replace the "tracks directionally"
   language about `WPUSI019011` with the measured correlation
   (0.097) and the REPLACE decision, document the new
   `GOLDPMGBD228NLBM` splice, and record the 2008 GFC
   stress-window evidence that drove the decision.
4. **Re-run the backtest** on the new splice and compare 1975-2000
   gold behavior under the two proxies. Any pre-2000 thesis
   evidence-log entries that referenced gold behavior should be
   reviewed against the new results.
5. **Consider whether `WPUSI019011` should stay in
   `configs/series.yaml` at all.** If it has no further use in
   the project, it should be removed rather than left as a
   dormant fetched series that might be silently re-used.

Each of these is a coordinator-driven decision on a `stable/`
branch with a spec update. This validation produces the evidence
and the recommendation; execution happens under a subsequent PR.

## Open questions

1. **Is `GOLDPMGBD228NLBM` complete back to 1975 on FRED with no
   gaps?** Recommended replacement is LBMA PM fix
   (`GOLDPMGBD228NLBM`, 1968+ per FRED metadata). The fetch-and-
   validate step belongs in the Phase 2 `stable/` PR that wires
   it into the splice; this `explore/` PR does not fetch the
   series. If there are material gaps in 1975-2000, the follow-up
   work will need to address them before the splice change lands.
2. **Is the WPUSI019011 splice worth keeping around as a
   cross-check?** One defensible reading is that the proxy is a
   "metals-industry demand" signal that the backtester never
   should have used as a gold price, but which might still be
   useful as an independent regime feature (e.g., an industrial-
   metals factor in regime classification). That is a separate
   design question from the gold-price splice and is out of scope
   here; it only matters if the follow-up chooses to retain
   `WPUSI019011` in `configs/series.yaml` rather than remove it.
3. **Does the backtester care about tracking error or just
   directional correctness?** Earlier framing claimed
   `BigCycleStrategy`'s regime-nudge logic (gold +10% in
   overheating) "tolerates noise as long as direction is
   preserved." The 2008 GFC evidence undercuts even that weak
   claim: monthly correlation -0.017 means direction is NOT
   preserved. The question is moot for WPUSI019011 — it fails the
   weakest possible version of the requirement. It may be
   relevant when validating the replacement series, but LBMA PM
   fix is a true gold price and should not need this kind of
   permissive reading.

## Reproducing

```bash
source .venv/bin/activate
python scripts/validate_gold_splice.py
```

The script is deterministic and reads only cached parquet files
(`data/raw/fred/WPUSI019011.parquet` and
`data/raw/yahoo/GC_F.parquet`).

# Civilizational signals lead financial signals thesis

**Status:** `tested` at cyclical scale (composite lags cyclical drawdowns); transition scale untested
**Scale:** transition (primary); cyclical (incidentally tested)

## Claim

Civilizational stress indicators (inequality, institutional trust, policy uncertainty, external-order measures) are *leading* indicators for financial stress. They enable earlier portfolio positioning than financial indicators alone — particularly for transition-scale regime shifts, where financial indicators may look normal until the transition is well underway (sterling was still the world reserve currency in 1914).

## Rationale

Financial indicators react to earnings, macro prints, and market reflexivity — they are fast-reacting by construction. Civilizational indicators capture slow-moving institutional decay that precedes financial manifestation by years or decades. The Dalio big-cycle framing treats civilizational decay (inequality erosion, institutional trust collapse, external-order weakening) as the *cause*; financial manifestation is the *effect*. Under this thesis, any strategy that relies only on financial indicators is detecting the symptom after the cause has been building for a long time.

## Implications

- Civilizational indicators (#4 in the roadmap) are not optional enrichment; they are the mechanism for detecting transition onset before financial indicators catch up.
- The operationalization matters. A composite that averages fast-reacting and slow-reacting components (the current `internal_order_stress_index` with EPU and sentiment alongside Gini) may smooth out the very leading-signature the slow components carry.
- Strategy use case is likely secular baseline tilts (multi-year weight shifts), not quarterly tactical trades. A slowly-decaying composite signal that shifts base allocation by 5-10% over a decade is a different animal than a monthly rebalance signal.

## Current evidence

**Tested at cyclical scale (PR #4 Path A, `docs/research/civilizational_composite_diagnostic.md`):**

The `internal_order_stress_index` composite (equal-weight mean of rolling-120m z-scores of Gini with 9-month publication lag, EPU, and inverted UMCSENT) was tested against S&P 500 monthly returns and >15% drawdown episodes on US 1994-2024 data:

- Peak correlation is at **k=+3** (composite correlates with returns 3 months in the past): **-0.192**. Composite is **lagging** equity returns, not leading, at cyclical scale.
- k=-12 (composite predicting 12mo-ahead returns): **+0.023** — effectively zero.
- Per-episode: dot-com 2000 composite was at -0.51 (low stress) 12mo before drawdown start; GFC 2008 was moderately elevated 6-12mo before but not strongly predictive; COVID 2020 and 2022 showed mixed pre-elevation.

**What this does NOT tell us (scale principle, per `README.md`):**

The thesis is about **transition-scale** regime shifts (empire transitions, reserve-currency displacements), which are absent from the dataset (see `backtest-sample-scope.md`). A signal that lags cyclical equity drawdowns can still be a valid leading indicator for transition-scale shifts — the mechanisms are different. Slow institutional decay doesn't react to quarterly earnings, which is exactly why a *low* correlation with cyclical drawdowns might be expected if the signal is working as intended.

The cyclical-scale result is a useful descriptive fact (it constrains what the composite can be used for in tactical applications) but does NOT falsify the thesis at transition scale.

**Component behavior might matter:** the composite mixes slow-moving (Gini, annual, reflects institutional structure over years) and fast-reacting (EPU, sentiment, monthly, reflects news-driven mood) signals. The averaged composite's lagging character may be driven by the fast components; a Gini-only or inequality-only signal might behave differently. Not tested yet.

**Tested at cyclical scale (2026-04-15, PR #53 / issue #49, `docs/research/civilizational_component_decomposition.md`):**

The component-decomposition diagnostic ran the same lead-lag analysis (k ∈ {−24, −12, −6, −3, 0, +3, +6, +12, +24}) and per-episode table separately on each of the 3 single components and the 3 pairwise composites. Headline:

| Series | k at peak |corr| | Peak corr |
|---|---|---|
| Gini (z, pub-lag-shifted) | +6 | +0.066 |
| EPU (z) | +3 | −0.190 |
| Sentiment inverted (z) | +3 | −0.146 |
| Gini + EPU | +3 | −0.155 |
| Gini + sentiment | +3 | −0.118 |
| EPU + sentiment | +3 | −0.198 |

**All 6 series lag at cyclical scale.** No component or pairwise composite shows peak correlation at negative k. The "fast components mask a leading Gini" hypothesis is not supported — Gini doesn't lead either. Refining: Gini is essentially noise on this sample (peak +0.066 ≈ zero); the composite's lagging signal traces to EPU and sentiment.

**What this changes about the thesis.** Nothing at the transition scale (where the thesis lives). The cyclical-scale null on Gini is consistent with the thesis: slow institutional decay shouldn't track quarterly equity moves, and the right test is whether Gini's secular trend (decade-over-decade level) precedes structural shifts — a different methodology than lead-lag correlation. Implication for downstream work: a Gini-only quarterly signal in BigCycleStrategy would be wrong by construction; any future use of Gini in strategy code should be at secular timescale (e.g., 36m-smoothed level, decade-over-decade change), not as a quarterly tilt. See follow-up issue #51 (Path B / secular tilt) for the right framing.

## What would test this

- **Cyclical (done, composite lags):** Already addressed. Result doesn't bear on the core claim.
- **Component decomposition:** ~~Rerun the lead-lag analysis separately on each component (Gini alone, EPU alone, inverted sentiment alone). Slow-moving components may lead even if the averaged composite lags.~~ **Done 2026-04-15 (PR #53 / issue #49)** — no component leads at cyclical scale; Gini is noise (peak +0.066), composite lag traces to EPU+sentiment. See evidence log.
- **Secular Gini signature (untested):** Within the dataset, does Gini's *level* (not z-score, not lead-lag correlation) show decade-over-decade rises preceding equity regime shifts? Different methodology — secular-trend analysis rather than cyclical correlation. Tracked in issue #51 (Path B framing).
- **Transition:** Does the composite (or components) rise before transition events in cross-national data — UK pre-1914, sterling declines, Weimar pre-1923, Dutch Republic 1700-1800? Requires `backtest-sample-scope.md` data.
- **Secular signatures:** Within the dataset, does the composite show rising trends during the 2000s-2010s that preceded the (ongoing) questioning of US reserve status? Hard to evaluate empirically because there's no endpoint yet — the transition is still in progress or not.

## What would falsify this

- Cross-national data showing civilizational indicators did NOT rise before transition events (e.g., Britain pre-1914 showed no institutional-stress elevation before the catastrophic sequence that ended sterling dominance). Strong falsification.
- Component-by-component analysis showing NO component leads at any scale. Would weaken but not falsify — it's possible the right indicators haven't been constructed yet.
- Cyclical results (already have) do NOT falsify.

## Related

- `backtest-sample-scope.md` — transition-scale testing requires the data acquisition roadmap this thesis motivates
- `institutional-adaptation.md` — the current composite may not capture technology-adaptation stress even if it captures classical stress
- `regime-aware-allocation.md` — if this thesis is confirmed at transition scale, civilizational signals become high-value inputs to regime detection

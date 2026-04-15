# Changing world order (umbrella thesis)

**Status:** `active`
**Scale:** transition (primary); subsumes the sub-theses' own scales

This folder holds the project's **umbrella thesis** and the sub-theses that compose it. Peer-level counter-theses (adversarial positions) sit at the top level of `specs/theses/`, not inside this folder — the directory structure should not imply they are second-class.

See [`dalio-principles.md`](dalio-principles.md) for a reference catalog of the specific Dalio specifications the project builds against, including framework evolution from his 2022-2026 writing.

## Claim

Reserve-currency-issuer empires follow a recognizable rise-and-decline arc. The United States is late in that arc. Wealth preservation across a multi-decade horizon requires positioning for the class of outcomes this arc historically produces — loss of reserve-currency status, sovereign-liability impairment, elevated real-asset and non-reserve-currency exposure — rather than for a continuation of the post-1945 US-ascendant equilibrium.

This is the worldview the project is operationally built around. The sub-theses in this folder are the pieces of it.

## Stance: Dalio-inspired, not Dalio-faithful

We use Ray Dalio's framework as scaffolding because it compresses a large quantity of economic history into a small set of recurring structures. The specific Dalio specifications the project builds against are cataloged in [`dalio-principles.md`](dalio-principles.md). In brief:

- The **four-mode debt-cycle resolution** taxonomy — `bond-allocation.md` operationalizes this
- The **six-stage empire cycle** and **nine-stage debt crisis** from *How Countries Go Broke* (2025) — issue #77 operationalizes locating the US on these
- The **eight empire drivers** — issue #80 operationalizes a composite
- The **cross-national multi-century methodology** — `backtest-sample-scope.md` adopts the discipline; issue #52 operationalizes it across phases A (UK sterling) → B (Dutch) → C (JST panel) → D (pre-1780, Chinese dynasties)
- The **"Overall Big Cycle"** framing that integrates debt + political + geopolitical + natural + technological forces (Dalio's 2024-2025 formulation)

We depart from Dalio where evidence, argument, or fit warrants. Specifically:

- **Scale taxonomy.** The project uses cyclical (3-10y) / secular (10-40y) / transition (50-200y). Dalio's current articulation is political (~10y) / big debt cycle (75-100y) / dynastic (~250y ± 150y). The divergence is non-trivial and is the subject of issue #79.
- **Institutional-adaptation thesis.** The printing-press → Reformation arc (`institutional-adaptation.md`) is the project's framing for technology-driven, coalition-scrambling transition dynamics. Dalio's recent work integrates technology (particularly AI) into the Overall Big Cycle, so this is less a departure than a refinement — our version emphasizes institutional rigidity as the specific mode of failure, which Dalio doesn't name.
- **Indicator recipes.** Where Dalio's specific recipe is sharp (e.g., internal-order stress composite from *Changing World Order* Ch. 5), it's a strong default — see #60's resolution target. Where his recipe is weak or dated, we substitute better measurements and document the departure in [`dalio-principles.md`](dalio-principles.md).
- **AllWeather non-neutrality.** Dalio himself has flagged that AllWeather was built for cyclical mode rotation, not reserve-currency transitions; we treat this caveat as enforced (issue #62) rather than as an aside.

We are **skeptical of "this time is different" dismissals of the Dalio case.** The base-rate argument — every reserve-currency issuer in recorded history has been devalued during its decline — carries weight regardless of whether we can prove the mechanism will repeat. The burden of proof is on novelty arguments (reserve-currency stickiness, productivity-outruns-debt, deflationary-tech, institutional resilience, MMT regime), not on the pattern. Those novelty arguments exist as peer-level counter-theses at the top level of `specs/theses/`, each with its own evidence log. They are treated seriously, not dismissed — but the umbrella's default posture is the Dalio case until a counter-thesis accumulates meaningful evidence.

## Rationale

The operational case for the umbrella:

1. **Dalio's pattern has non-trivial empirical support.** His 500-year cross-civilizational survey (Dutch, British, US reserve-currency issuers; Chinese dynastic cycles; Habsburg Spain) is the broadest dataset any framework in this domain works from. A project reasoning about multi-decade wealth preservation cannot ignore that evidence base on stylistic or methodological grounds.

2. **The alternative is implicit US-exceptionalism.** A project built on US 1975-present data alone, with no articulated scenario for post-US-hegemony conditions, implicitly assumes the 1945-present US ascendancy continues. That assumption — that "this time is different" and the US will be the exception to the pattern — is itself a thesis, and a rarely-defended one. Making the Dalio case explicit forces the opposing view to be stated and defended as well (via the counter-theses).

3. **The US fiscal arithmetic points the same direction the historical pattern does.** `us-fiscal-deterioration.md` enumerates three independent mechanisms (fiscal-arithmetic unsustainability, demand-for-debt erosion, hegemony-decay) that all point toward mode-4 (monetization) as the likely US resolution. These are concrete, measurable, and US-specific — independent of whether the general Dalio pattern holds. Dalio's 2025 specific claim (deficit must fall from current ~6% to 3% of GDP to avoid late-stage resolution) sharpens the mechanism.

4. **Wealth-preservation asymmetry.** Positioning correctly for the Dalio scenario and being wrong costs moderate return drag during a continued US ascendancy. Positioning for continued US ascendancy and being wrong costs catastrophic real-wealth loss during a transition. The asymmetry favors the Dalio case even under uncertainty about its probability.

## How sub-theses compose the umbrella

Each file in this folder plays a specific role relative to the umbrella:

| Sub-thesis | Role |
|---|---|
| [`us-fiscal-deterioration.md`](us-fiscal-deterioration.md) | **Central implication.** The specific mechanism by which the arc applies to the US. Mode-4 monetization as the likeliest terminal resolution. |
| [`bond-allocation.md`](bond-allocation.md) | **Allocation implication.** Sovereign bonds lose in 3 of 4 resolution modes; bond exposure should be regime-conditional, not baseline. |
| [`backtest-sample-scope.md`](backtest-sample-scope.md) | **Methodological discipline.** US 1975-present cannot test transition-scale claims; cross-national historical data (#52) is the honest path. |
| [`civilizational-leads-financial.md`](civilizational-leads-financial.md) | **Dependency claim.** Civilizational stress indicators lead financial stress; the operational argument for tracking them. |
| [`institutional-adaptation.md`](institutional-adaptation.md) | **Project refinement.** Technology-driven, coalition-scrambling transition mode. Dalio integrates technology into his Overall Big Cycle; this sub-thesis emphasizes constitutional rigidity as the specific mode of failure. |
| [`regime-aware-allocation.md`](regime-aware-allocation.md) | **Operational framework.** The mechanism by which regime signals translate into allocation decisions. |

The umbrella is not a replacement for any of these — it's the connective tissue that explains why they cohere.

## Counter-theses and paired evidence tracking

Peer-level counter-theses live at the top level of `specs/theses/`. Each names:

1. Its strongest steelman case
2. What evidence would strengthen it
3. What evidence would falsify it (and by extension support the umbrella)

**Methodology: every substantive new data point should update both the umbrella's evidence log AND any counter-thesis it bears on.** This is the operational expression of "skeptical of this-time-is-different dismissals" — the counter-theses don't get dismissed, they get evidence-tracked. If a counter-thesis accumulates strong support and the umbrella does not, the project's operational positioning should shift rather than rationalize.

Currently articulated counter-theses (see the top-level [`specs/theses/README.md`](../README.md) for status and links):

| Counter-thesis | Core claim | Issue |
|---|---|---|
| `reserve-currency-stickiness` | USD has network effects sterling lacked; transition timeline is much longer or doesn't occur | #82 |
| `productivity-outruns-debt` | AI-era real growth deflates debt/GDP organically; no monetization needed | #83 |
| `institutional-resilience` | US has been through worse polarization (1860s, 1930s, 1960s); system absorbs and recovers | #84 |
| `mmt-stance` | Sovereign fiat issuers face inflation constraint, not solvency; mode-4 is a category error | #85 (stub) |
| `deflationary-tech` | Structural tech deflation absorbs monetary accommodation; inflation doesn't materialize | #86 (stub) |

## Implications

What the umbrella commits the project to:

- **Cross-national historical data acquisition (#52) is load-bearing, not supplementary.** The umbrella cannot be validated or falsified on US-only cyclical data. Phase A (UK 1900-1980, BoE Millennium dataset) is the first concrete test.
- **Evidence tracking is symmetric.** Every strategy backtest, every data-pipeline finding, every qualitative observation is a candidate evidence entry for both the umbrella and any relevant counter-thesis. `review-adversarial` should surface cases where evidence is being logged asymmetrically.
- **Wealth-preservation basket is Dalio-shaped, not cyclically-optimized.** Gold, commodities, TIPS, ex-US equity, productive real assets (issue #10) are the affirmative positioning. Sovereign-duration exposure is conditional on regime signals.
- **Strategy comparison reports the Dalio case AND the counter-case impact.** A backtest that shows non-sovereign-heavy allocation underperforming on US 1975-present is evidence against the umbrella at cyclical scale and for reserve-currency-stickiness; it is not evidence at transition scale. These scale distinctions should be preserved in every result report.
- **No "Dalio said so" without measurement.** The umbrella's authority is not Dalio's personal credibility — it's the historical pattern and the US-specific fiscal mechanism. Where Dalio's specific recipes are demonstrably weaker than alternatives (e.g., internal-order composite per #60), we substitute and document in [`dalio-principles.md`](dalio-principles.md).

## Current evidence

**Umbrella articulated 2026-04-15.** Sub-thesis evidence lives in the sub-thesis files. Umbrella-level evidence only here:

- **Supporting (the historical pattern):** Dalio's 500-year cross-civilizational survey across *Changing World Order* (2021) and *How Countries Go Broke* (2025). Not independently verified in this project. Issues #52 (cross-national data) and #77 (empire-arc stage operationalization) are the operational path to that verification at transition scale.
- **Supporting (US-specific mechanism):** [`us-fiscal-deterioration.md`](us-fiscal-deterioration.md) evidence log — 25-year US deficit trajectory, declining USD reserve share (72% → 58% per IMF COFER), declining foreign Treasury holdings share. Cyclical/secular-scale evidence; does not reach transition scale.
- **Supporting (Dalio's current position claim):** In 2025-2026 writing Dalio names the US as being at Stage 5 (pre-breakdown) of the six-stage empire cycle and Stage 4 of a four-part public-debt bust — his own most recent characterization. Source: [`dalio-principles.md`](dalio-principles.md) §11.
- **Counter-direction (cyclical scale, ambiguous):** PR #47 and #56 show non-sovereign-heavy allocation underperforms AllWeather on US 1975-present (Sharpe 0.39 vs 0.84). Consistent with reserve-currency-stickiness at cyclical scale; silent on transition.
- **Awaiting:** Phase A of #52 (UK sterling transition, 1900-1980) will be the first transition-scale evidence for or against the umbrella. BoE Millennium workbook downloaded 2026-04-15; ingest and analytical notebook pending re-delegation.

## What would test this

Transition-scale tests (the umbrella's primary scale):

- **#52 Phase A (UK sterling transition):** Does the fiscal-deterioration → monetization → real-asset preservation pattern appear in UK 1900-1980 data? If not, the umbrella's specific mechanism is weakened even if the general empire-arc claim survives.
- **#52 Phase B (Dutch guilder):** Does the pattern generalize beyond UK?
- **#52 Phase C (JST macrohistory panel):** Does the cross-sectional evidence across 17 developed economies show empire-late-stage signatures that distinguish from ordinary cyclical stress?
- **#52 Phase D (pre-1780, Chinese dynasties, Habsburg Spain):** Does Dalio's 500-year claim hold up under scrutiny?
- **Issue #77 (empire-arc stage operationalization):** Where is the US on Dalio's six-stage empire cycle and nine-stage debt crisis? Falsifiable stage-transition indicators.
- **Issue #80 (8-driver composite):** Does the US-vs-peer cross-sectional empire position match what the arc would predict?

Non-transition-scale tests are informative but not decisive — they bear on the sub-theses more than the umbrella itself.

## What would falsify this

The umbrella is falsified by, in rough order of decisiveness:

- **Sustained empirical support for any counter-thesis over a decade-plus horizon.** If reserve-currency-stickiness holds (USD reserve share stable or growing; no material alternative-currency adoption), or productivity-outruns-debt holds (debt/GDP declines without fiscal tightening due to real growth), the umbrella's operational stance is wrong.
- **Cross-national transition data that contradicts the pattern.** If Phase A-D work shows the Dalio pattern does not appear in prior reserve-currency transitions — if real assets did NOT preserve purchasing power, if sovereign bonds did NOT underperform, if the fiscal→monetization chain did NOT materialize — the umbrella's empirical base collapses.
- **US fiscal consolidation at scale.** Sustained primary surpluses reducing debt/GDP without market coercion (Dalio's specific threshold: deficit below 3% of GDP sustained). Would falsify `us-fiscal-deterioration` directly and weaken the umbrella's central implication.
- **Dalio's own framework evolving in a way that invalidates the base claim.** His recent writing (2024+) acknowledging that prior patterns may not apply to the current case, on strong evidence. Would require recalibration.
- **Discovery of historical counterexamples.** A world-reserve fiat currency that was NOT devalued during its issuing hegemony's decline. To our knowledge none exists, but the search hasn't been exhaustive.

## Related

**Sub-theses (this folder):** [`us-fiscal-deterioration.md`](us-fiscal-deterioration.md), [`bond-allocation.md`](bond-allocation.md), [`backtest-sample-scope.md`](backtest-sample-scope.md), [`civilizational-leads-financial.md`](civilizational-leads-financial.md), [`institutional-adaptation.md`](institutional-adaptation.md), [`regime-aware-allocation.md`](regime-aware-allocation.md)

**Reference:** [`dalio-principles.md`](dalio-principles.md)

**Counter-theses (top level, forthcoming per issues):** `reserve-currency-stickiness` (#82), `productivity-outruns-debt` (#83), `institutional-resilience` (#84), `mmt-stance` (#85), `deflationary-tech` (#86)

**Operational follow-ups:** #52 (cross-national data), #77 (empire-arc stages), #79 (scale-taxonomy divergence), #80 (8-driver composite), #60 (internal-order composite per Dalio recipe)

**Reviews informing this document:** [`reviews/2026-04-15.md`](../../../reviews/2026-04-15.md) (external), [`reviews/2026-04-15-dalio.md`](../../../reviews/2026-04-15-dalio.md) (Dalio-framework alignment — Finding #1 on scale divergence, Finding #8 on cross-national discipline, Question #1 on Dalio-faithful vs Dalio-adjacent stance)

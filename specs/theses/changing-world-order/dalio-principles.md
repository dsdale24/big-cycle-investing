# Dalio principles — reference catalog

This document catalogs the specific modeling specifications Ray Dalio uses to describe big cycles, reserve-currency transitions, and debt-cycle resolutions. It is a **reference document, not a thesis** — it describes what Dalio himself specifies, so that the project's [`README.md`](README.md) umbrella thesis and its sub-theses can cite concrete Dalio elements rather than waving at "the Dalio framework" generically.

Each section names: (i) what Dalio specifies, (ii) the source, (iii) the project's use or departure. The project's stance is [`Dalio-inspired, not Dalio-faithful`](README.md#stance-dalio-inspired-not-dalio-faithful) — we use specifications we find useful and depart where evidence, fit, or measurement warrant. Departures are named explicitly per section.

## §1. Debt-cycle resolution modes

**Dalio specification.** Every debt cycle ends with the borrower's obligations being reconciled against the borrower's ability to pay. Four classical modes:

1. **Austerity.** The borrower cuts spending or raises taxes to generate the resources to service debt. Deflationary.
2. **Restructuring.** The borrower negotiates terms (longer maturity, lower coupon, partial principal reduction). Asset-class outcome depends on negotiation outcome.
3. **Default.** The borrower fails to pay. Catastrophic for creditors; ends reserve-currency status immediately for a reserve issuer.
4. **Monetization.** The central bank creates money to finance government debt, devaluing the currency in real terms. Preserves nominal debt service; destroys real value of sovereign debt gradually. Historically dominant resolution for declining reserve-currency issuers.

In *How Countries Go Broke* (2025) Dalio expands this into a more detailed **nine-stage debt crisis** framework (the specific stages are more granular than the four modes; each stage has markers — e.g., printing money, government selling more debt than can be absorbed, bond-price plunge, capital flight).

**Bondholder outcome matrix** (mode × bondholder): mode 1 is the only mode where long-duration nominal sovereign bonds win; modes 2-4 all impair them. This matrix is load-bearing in *Principles for Navigating Big Debt Crises* Part 1.

**Sources.**
- *Principles for Navigating Big Debt Crises* (2018), Part 1 "The Archetypal Big Debt Cycle," chapters on deflationary vs inflationary resolution
- *How Countries Go Broke* (2025) — nine-stage expansion

**Project use.** [`bond-allocation.md`](bond-allocation.md) operationalizes the four-mode matrix. The thesis's claim — that bonds win in only 1 of 4 modes — is a direct application. The nine-stage crisis framing has not yet been operationalized in-project (follow-up worth considering; may tie to #77 empire-arc work).

**Project departure.** None at the conceptual level. The project treats the four-mode matrix as authoritative for the allocation question and the nine-stage as the granular locator for "where in the arc" work.

## §2. Scale taxonomy (Dalio's own cycles)

**Dalio specification (current, per *How Countries Go Broke* 2025 and recent LinkedIn / X writing).**

| Cycle | Duration | What plays out |
|---|---|---|
| Political cycle | ~10 years | Policy swings within a political system |
| Short-term debt cycle | ~5-8 years | Credit expansion / contraction; recession / recovery |
| Big debt cycle (long-term) | 75-100 years | Accumulated debt reconciled through one of the four-mode resolutions; produces major deleveraging events |
| Dynastic cycle / reserve-currency arc | ~250 years (± 150) | Full empire rise-and-decline; reserve-currency transitions (Dutch → British → US) |

Earlier Dalio writing (pre-2021) named the long-term debt cycle as ~50-75 years; the 2025 book's articulation (75-100) supersedes.

**Sources.**
- *Principles for Navigating Big Debt Crises* (2018)
- *Changing World Order* (2021), Ch. 2 "The Big Cycle of the Last 500 Years"
- *How Countries Go Broke* (2025)
- Dalio X/LinkedIn posts 2023-2026

**Project use.** The project's scale principle ([`specs/theses/README.md`](../README.md#the-scale-principle-load-bearing)) adopts a three-scale taxonomy (cyclical / secular / transition) broadly aligned with Dalio's but with different boundaries.

**Project departure (see issue #79).** The project uses cyclical (3-10y) / secular (10-40y) / transition (50-200y). The "secular" bucket has no direct Dalio analog — it sits in the gap between his short-term debt cycle and his big debt cycle. Consequences:

- No project bucket for the long-term-debt-cycle scale Dalio treats as the biggest deleveraging events (US 1930s, 2008). These sit awkwardly in the project's "secular" bucket.
- The project's "transition" (50-200y) is narrower than Dalio's dynastic (250y ± 150y). Dalio's "500 years" framing is implicitly supra-transition in the project's vocabulary.

Issue #79 exists to decide whether to align with Dalio's taxonomy or to document the divergence with explicit reasoning.

## §3. Six-stage empire cycle

**Dalio specification.** Empires rise and decline through six stages (*Changing World Order* Ch. 4; refined and re-emphasized in 2024-2026 writing):

| Stage | Name | Characteristics |
|---|---|---|
| 1 | Rise begins | Strong leaders win political power; foundations set |
| 2 | Building strength | Cooperation, economic growth, institutional development |
| 3 | Prosperity peak | Self-sustaining economy; cultural achievement; reserve-currency status consolidated |
| 4 | Excess & decline begins | Innovation fades, debt accumulates, wealth gaps grow, competitiveness erodes |
| 5 | Bad financial conditions + conflict | Large rising debts; populism of right and left; currency concerns; movement out of fiat into gold; shift toward great-power conflict |
| 6 | Civil war / great disorder | Breakdown of internal and external order; reconstruction; cycle restarts |

**Dalio's current US position-claim (2025-2026 writing):** The US is in **Stage 5, transitioning toward Stage 6.** He compares current conditions to the pre-1945 period rather than the post-WWII era most people have lived through.

The 2021 book sometimes framed the decline portion as a "5-stage" arc (stages of decline only, omitting the rise); the 2025 framing treats the six-stage full-cycle version as canonical. Project work that cites "5-stage" from earlier material should prefer the 6-stage framing when current.

**Sources.**
- *Changing World Order* (2021), Ch. 4
- *How Countries Go Broke* (2025) — reiterates and refines
- Dalio X/LinkedIn posts 2023-2026 — current-position claims

**Project use.** Issue #77 tracks operationalizing the stages as indicators (what markers define each stage boundary, where the US sits on the arc). Currently the project has indicators bearing on individual stages (debt/GDP on Stage 4-5, Gini/EPU/sentiment on Stage 5 internal-order) but no artifact locates the US on the full arc. The Dalio review (`reviews/2026-04-15-dalio.md` Finding #2) named this as the single biggest framework-alignment gap.

**Project departure.** None at the conceptual level. The project accepts the six-stage framework and is operationalizing it (#77).

## §4. Eight empire drivers

**Dalio specification.** Eight measures of empire relative power, each scored across countries and time. No single driver is decisive — the composite is what matters.

1. **Education**
2. **Innovation & technology**
3. **Cost competitiveness**
4. **Military strength**
5. **Trade** (share of global trade)
6. **Economic output**
7. **Markets & financial centers** (share of global financial activity)
8. **Reserve currency status**

Dalio composites these into a single "empire score" per country over time. *Changing World Order* Ch. 1 and Appendix show cross-country time-series plots.

**Sources.**
- *Changing World Order* (2021), Ch. 1 and Appendix

**Project use.** Issue #80 operationalizes an eight-driver composite. The Dalio review (`reviews/2026-04-15-dalio.md` Finding #3) found the project tracks 4 of 8 at indicator level (economic output, trade share, military spend, reserve-currency share) and composites 0. The four covered drivers are exactly the ones FRED provides easily; the four missing (competitiveness, innovation, financial-center status, military-composite) require cross-dataset work (BIS, WEF, WIPO, SIPRI).

**Project departure.** None at conceptual level; operational gap only.

## §5. Internal-order stress composite

**Dalio specification.** *Changing World Order* Ch. 5 articulates an internal-order stress composite from five components:

1. **Wealth gap** (inequality; e.g., Gini, top-decile share)
2. **Values gap** (cultural/ideological polarization)
3. **Populism** (vote share for anti-establishment parties)
4. **Political polarization** (e.g., DW-NOMINATE for the US legislature)
5. **Internal conflict events** (protests, riots, civil disturbance indicators)

Plus: **debt burden** as a structural input compounding the above.

All components are slow-moving by design — internal-order stress is not a quarterly signal.

**Sources.**
- *Changing World Order* (2021), Ch. 5

**Project use.** The project's `internal_order_stress_index` uses Gini + EPU + consumer sentiment — not Dalio's recipe. The Dalio review (Finding #6) and issue #60 flag this. Issue #60's resolution target is to swap EPU and sentiment (both fast-reacting, lag at cyclical scale per `docs/research/civilizational_component_decomposition.md`) for DW-NOMINATE polarization + populist-vote-share + explicit debt-burden. That target brings the composite closer to Dalio's recipe.

**Project departure (intentional).** The project retains scope to depart from Dalio's specific component list where measurement considerations warrant. Values-gap and internal-conflict-events in particular are hard to operationalize consistently over long time series; the project may proxy them via existing indicators rather than acquire new data.

## §6. External-order / coalition dynamics

**Dalio specification.** *Changing World Order* Ch. 6 tracks external-order decline via coalition dynamics:

1. Rising power forms alternative alliances (e.g., BRICS+, SCO, China-led trade blocs)
2. Declining power's sanctions lose bite (sanctioned countries find workarounds; sanctions themselves accelerate reserve-alternative adoption)
3. Reserve-currency alternatives coalesce (commodity-pricing fragmentation, alternative payment rails, bilateral-currency trade settlement)

These are **narrative dynamics** more than quantitative metrics — Dalio tracks them qualitatively alongside the quantitative residue (reserve share, military spend).

**Sources.**
- *Changing World Order* (2021), Ch. 6

**Project use.** Reserve-currency-share and military-spend are tracked quantitatively. Coalition dynamics are not — they would require a news-monitoring function (deferred issue #59).

**Project departure.** The project currently relies on Dalio's quantitative residue and defers the qualitative-narrative side. Acknowledged gap, not a disagreement with the framework.

## §7. Wealth-preservation basket

**Dalio specification.** Late-cycle / transition-era wealth-preservation holdings (*Changing World Order* Ch. 14-15 "Investing Principles" / "The Future"; reiterated in *How Countries Go Broke* 2025):

| Asset class | Role |
|---|---|
| **Gold** | The asset of last resort; every reserve-currency devaluation historically drives capital into gold |
| **Inflation-linked bonds (TIPS)** | Hedge against mode-4 (monetization) specifically; nominal sovereign hedge against mode-1 (austerity) only |
| **Productive real assets** | Land, real estate, infrastructure, resource-producers (distinct from commodity futures) |
| **Non-reserve-currency equities** | Ex-US equity exposure; specifically companies with pricing power outside the declining-reserve-currency economy |
| **Selective commodities** | Energy particularly; less structural than gold but inflation-responsive |

**Avoid:** long-duration nominal sovereign debt of the declining reserve issuer (loses in 3 of 4 resolution modes).

Dalio's 2025 direct framing: *"Financial money and paper wealth are valuable only to the extent that they help you acquire real money and real wealth."* (per public essays referenced in third-party summaries).

**Sources.**
- *Changing World Order* (2021), Ch. 14-15
- *How Countries Go Broke* (2025)

**Project use.** Partial. `BigCycleStrategy.BASE_PROFILES["non_sovereign_heavy"]` implements gold + commodities + low sovereign-duration — matches Dalio's direction on bonds and gold. Missing: TIPS, ex-US equity, productive real assets as distinct asset class (issue #10).

**Project departure.** None at conceptual level; operational gap on the full basket.

## §8. AllWeather design intent

**Dalio specification.** AllWeather (Bridgewater's signature risk-parity portfolio) was designed for a world where the **four environments** (growth up/down × inflation up/down) rotate cyclically. It is explicitly **not** designed for reserve-currency transitions or for the late-empire / monetization scenario.

Bridgewater itself reports strategy performance by decomposing into these four environments (*Engineering Targeted Returns and Risks*, 2011).

**Sources.**
- Bridgewater 2011 whitepaper "Engineering Targeted Returns and Risks"
- Dalio LinkedIn essays 2019-2021 discussing AllWeather's environment assumptions

**Project use.** [`bond-allocation.md`](bond-allocation.md) explicitly names AllWeather as embodying mode-1 (disinflation) assumptions; issue #62 tracks the anti-pattern of benchmarking everything against AllWeather despite acknowledging it is not neutral.

**Project departure.** None — this is Dalio's own caveat, taken seriously.

## §9. Cross-national multi-century methodology

**Dalio specification.** His actual research method, most visibly in *Changing World Order* but used across all his big-cycle work:

- Multi-country dataset spanning at least three reserve-currency issuers (Dutch, British, US) plus Chinese dynastic cycles and Habsburg Spain
- Dataset back ~500 years minimum; some elements back ~1000 years
- Primary mode of reasoning: pattern-matching across the cases, looking for **what repeats** and what varies
- Applies to both the big debt cycle (50-100y) and the dynastic cycle (~250y)

**Sources.**
- *Changing World Order* (2021), Ch. 2 "The Big Cycle of the Last 500 Years"

**Project use.** [`backtest-sample-scope.md`](backtest-sample-scope.md) adopts this discipline. Issue #52 operationalizes it across four phases:
- Phase A: UK sterling decline 1900-1980 (BoE Millennium dataset; workbook downloaded 2026-04-15)
- Phase B: Dutch guilder decline ~1780-1815
- Phase C: JST macrohistory panel (17 countries, 1870-present)
- Phase D: pre-1780, multi-empire including Chinese dynastic cycles, Habsburg Spain

**Project departure.** None at methodological level; the project is trying to match Dalio's discipline. Operationally, the work is early — Phase A is the first concrete test.

## §10. Base-rate framing and Dalio's current US position-claim

**Dalio specification — base-rate claim.** Every reserve-currency fiat currency in recorded history has been devalued during its issuing hegemony's decline. Dutch guilder, British sterling, and prior reserve currencies all followed the pattern. This is a base-rate observation, not a mechanism claim.

**Dalio specification — current US position (2024-2026 writing):**
- US is in **Stage 5 of the 6-stage empire cycle**, transitioning toward Stage 6
- US is in **Stage 4 of a 4-stage public-debt bust** (the final stage before resolution)
- **Specific policy threshold:** deficit must fall from current ~6% of GDP to ~3% of GDP sustained to avoid late-stage resolution
- **Prediction (per 2026 Fortune interview):** "double-digit interest rates and a sharp (30-50 percent) plunge in government bond prices in the coming decade" if deficit trajectory doesn't change

**Sources.**
- *Changing World Order* (2021), Ch. 2 for base-rate framing
- *How Countries Go Broke* (2025) for current US position
- Fortune interview 2026-03 for specific prediction
- Dalio X/LinkedIn posts 2023-2026

**Project use.** The base-rate claim is load-bearing for the umbrella (see [`README.md`](README.md) Rationale §1). The specific US position-claim is evidence for [`us-fiscal-deterioration.md`](us-fiscal-deterioration.md); the 3%-of-GDP deficit threshold is a specific falsification target.

**Project departure.** None. The project's stance is to take both the base rate and Dalio's current position-claim seriously while running its own cross-national verification (#52).

## §11. Framework evolution (2022-present)

Dalio's work has evolved meaningfully since the 2021 *Changing World Order*. Summary of material changes:

### Integration of AI and technology into the Overall Big Cycle

In *How Countries Go Broke* (2025), Dalio names five forces that together drive the "Overall Big Cycle":
1. The big debt cycle
2. Political conflict within countries
3. Geopolitical conflict between countries
4. Natural forces (pandemics, climate, droughts/floods)
5. **Technology (most importantly, AI)**

The 2021 book treated technology mostly as a productivity-growth input; the 2025 book integrates it as a co-equal driver of world-order change. This is a **non-trivial evolution** — AI is no longer exogenous to the framework.

**Project implication.** Our [`institutional-adaptation.md`](institutional-adaptation.md) sub-thesis, originally framed as "our addition to Dalio's framework," is less of a departure than it appeared in early-2026 framing. Dalio now integrates AI; we refine by naming constitutional rigidity as the specific mode of failure (which Dalio does not emphasize).

### Nine-stage debt crisis (granular expansion of the four modes)

*How Countries Go Broke* articulates a nine-stage progression of a debt crisis (stages with specific markers like "government selling more debt than can be absorbed," "central bank prints to absorb," "capital flight," etc.). This is a granular expansion of the four-mode resolution framework, not a replacement.

**Project implication.** Issue #77 work should consider whether to operationalize the nine-stage granularity, the six-stage empire cycle, both in combination, or to pick one as primary.

### Sharpened US position-claim

Dalio has moved from general "the US is late in its cycle" to specific **Stage 5 transitioning to Stage 6** (empire) and **Stage 4 of 4** (debt bust). He has also named a specific avoidance threshold (deficit to 3% of GDP) and a specific predicted bond outcome (double-digit rates, 30-50% bond-price plunge).

**Project implication.** The [`us-fiscal-deterioration.md`](us-fiscal-deterioration.md) evidence log should incorporate these as Dalio's own explicit calibration. They are falsifiable and time-bounded ("in the coming decade").

### Comparison to pre-1945 period

Dalio's 2025-2026 writing frequently compares current conditions to the pre-1945 era (pre-WWII late-sterling, interwar fiscal and institutional stress, rise of great-power conflict). This is more specific than earlier "we're late in the cycle" framing.

**Project implication.** This framing supports the choice of #52 Phase A (UK 1900-1980) as the first transition-scale test — it is precisely the period Dalio invokes as analog.

### Maintenance cadence

This §11 should be updated when Dalio publishes new book-length work or when his current-position claims shift materially. X/LinkedIn post-level writing is more incremental and does not require §11 updates for ordinary content — only for material framework changes.

## Sources consulted for this document

- *Principles for Navigating Big Debt Crises* — Ray Dalio (2018)
- *Principles for Dealing with the Changing World Order: Why Nations Succeed and Fail* — Ray Dalio (2021)
- *How Countries Go Broke: Principles for Navigating the Big Debt Cycle* — Ray Dalio (2025)
- Bridgewater "Engineering Targeted Returns and Risks" (2011)
- Fortune interview "Ray Dalio: I've studied 500 years of history and fear we're entering the most dangerous phase of the 'Big Cycle'" (2026-03-14)
- Ray Dalio X/LinkedIn posts 2023-2026 (aggregate; specific post-level citations added when referenced)
- Third-party framework summary: alliocapital.com "The Macro Masterpiece" (Apr 2025)
- `reviews/2026-04-15-dalio.md` — internal Dalio-framework alignment review

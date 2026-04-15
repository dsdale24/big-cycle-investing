# US fiscal deterioration → sovereign debt crisis thesis

**Status:** `active`
**Scale:** secular (fiscal trajectory is decades-long) + transition (the feared endpoint — modes 2/3/4 resolution)

## Claim

The United States has demonstrated sustained inability to control its federal deficit over 20+ years. Debt-service cost manageability depends on continued broad global demand for US Treasuries at current (or lower) real yields. Per Dalio's reserve-currency research, every world-reserve fiat currency in recorded history has been devalued during its hegemony's decline — the big-cycle framing treats this as the structural terminal condition for world-reserve fiats, not an accident. If demand for US Treasuries declines faster than the US consolidates fiscally, interest rates rise, debt service becomes unaffordable, and the US enters austerity, default, or monetization (Dalio resolution modes 2, 3, 4). **Monetization is the historically dominant resolution for declining reserve-currency issuers.**

This project exists to prepare for that scenario.

## Rationale

### The fiscal-arithmetic mechanism
- Federal deficit has exceeded 3% of GDP in the majority of years since ~2001, across both parties and administrations.
- Debt/GDP has risen from ~55% (2001) to ~120%+ (2024). Crossed the Reinhart-Rogoff ~90% threshold around 2010 without visible debt-service stress — because yields fell in parallel.
- Net interest as a share of federal outlays is rising toward historic highs as post-2022 refinancing hits the portfolio.
- No sustained political constituency for deficit reduction has emerged in 25 years despite multiple rhetorical cycles.

### The demand-for-debt mechanism
- Treasury holders are a finite set: Fed, foreign central banks + sovereign wealth funds, domestic banks, domestic private, pensions/insurers. Each has a demand curve; the aggregate curve is finite at any given real yield.
- Foreign holdings share of Treasury debt has trended down since ~2014 (China in particular).
- Reserve-currency share of global central bank reserves: USD has declined from ~72% (2000) to ~58% (2024), with EUR + RMB + "other" gaining.
- Auction bid-to-cover ratios have weakened on long-duration issuance since 2022.
- Marginal decline in demand requires marginal rise in yield to clear; fiscal arithmetic is highly sensitive to yields when debt/GDP is large.

### The hegemony-decay mechanism (Dalio big-cycle framing)
- Every world-reserve fiat currency in recorded history — Spanish silver real, Dutch guilder, British sterling — has been devalued during its issuing hegemony's decline. Dalio's 500-year reserve-currency survey documents this as a regularity, not an accident.
- The core dynamic: maintaining reserve-currency status requires the issuer's political, military, and economic credibility. As credibility declines, demand for the currency as a store of value declines; the issuer typically resorts to monetization to service accumulated obligations; devaluation accelerates credibility loss.
- **Contemporary US-specific accelerants (one mechanism among several, not the load-bearing driver):** unilateral military action without broad ally coalitions (recent Venezuela and Iran engagements, 2020s pattern), weaponization of SWIFT / dollar-clearing infrastructure for sanctions (2012 Iran, 2014/2022 Russia), strained alliances with traditional coalition partners. These erode trust-based demand for USD-denominated assets among non-US sovereigns. They are part of the broader hegemony-decline dynamic, not a separate or optional feature.

### Why monetization is the likeliest US resolution mode
- **Austerity (mode 1):** Politically unachievable at the scale required; 25 years of deficit politics shows no constituency for it.
- **Default (mode 3):** Destroys reserve-currency status immediately; politically unthinkable for the issuer of the reserve currency while any alternative exists.
- **Restructuring (mode 2):** Same reserve-currency-destruction problem as default; also historically rare for reserve-currency issuers.
- **Monetization (mode 4):** Preserves nominal debt service, destroys real value gradually, does not require legislative action (the Fed can act alone), and matches historical precedent. **This is the default path for a reserve-currency issuer that cannot consolidate fiscally.**

## Implications

- **For `bond-allocation`:** this thesis names the specific mechanism that makes modes 2/3/4 live for the US, not theoretical. Mode 4 (monetization) is the most likely terminal resolution. Sovereign-liability exposure should be regime-conditional with an explicit bias against long-duration nominal bonds as the fiscal stress signals elevate. TIPS partially hedge mode 4 but share mode-2/3 exposure (unlikely but not impossible). Non-sovereign real assets (gold, commodities, real-asset equities) are the structural core, not a tactical tilt.
- **For `backtest-sample-scope`:** this thesis names *the specific transition* that US 1975-present can't test. Cross-national historical data acquisition (issue #52) is not optional supplementary work — it's the only way to honestly stress-test the strategy against this scenario. The priority of #52 should reflect that.
- **For `regime-aware-allocation`:** regime signals should include fiscal-stress indicators (deficit trajectory, debt/GDP, net interest share, foreign holdings share), not just the cyclical trio (yield curve, inflation, real rates). The existing BigCycleStrategy regime inputs are cyclical-scale; this thesis is secular/transition-scale.
- **For `civilizational-leads-financial`:** demand-for-debt and reserve-currency-share metrics may be the specific civilizational leading indicators that matter for this scenario — more than inequality or consumer sentiment. A separate composite ("fiscal-stress index" or similar) may be more predictive of the transition outcome than the existing internal-order composite.
- **For strategy design broadly:** wealth-preservation for this thesis means holding non-USD-denominated and non-sovereign-liability assets. Gold, non-US equities with pricing power, commodities, productive real assets. The goal is not to beat USD-denominated benchmarks; it is to preserve purchasing power through a USD devaluation.
- **For evidence gathering:** this thesis lives and dies on monthly macro data (FRED has most of it) plus qualitative tracking of hegemony-decay events (military action, sanctions, alliance stress). The qualitative side is not well-served by the current data pipeline. A news-monitoring research function (tracked as a separate issue) is the appropriate way to operationalize that side of the evidence.

## Current evidence

**Captured 2026-04-15 (this thesis file).** No direct tests yet. Upstream evidence that motivates the thesis:

- **PR #47 + #56 (cyclical scale, weak):** BigCycleStrategy with bond-heavy base (45% sovereign-liability) underperforms AllWeather on drawdown by ~9 ppt; swapping to a non-sovereign-heavy base (25% sovereign-liability) with static gold+commodities replacement performs dramatically worse on aggregate (Sharpe 0.39 vs 0.84). This is consistent with the cyclical sample favoring mode-1 (disinflation); it says nothing for or against the transition-scale scenario this thesis describes. See `bond-allocation.md` evidence log.
- **Dalio's reserve-currency research:** `Principles for Dealing with the Changing World Order` (2021) is the main articulated source for the hegemony-decline claim. The historical survey covers Dutch, British, and prior reserve-currency transitions. Not independently verified in this project yet; taken as the starting hypothesis.
- **Observable macro data (US 1975-present, already in our data pipeline):** deficit/GDP trajectory, debt/GDP trajectory, net interest share of outlays. Not yet operationalized into a fiscal-stress composite.

## What would test this

### Cyclical / secular scale (US data we have or can fetch)

- **Operationalize the "unable to control deficit" claim as a falsifiable metric.** Proposal: `deficit/GDP > 3%` in ≥ 15 of the last 20 years (rolling window) AND `debt/GDP` trended up over that window. FRED: FYFSD (federal surplus/deficit), GDP, GFDEGDQ188S (debt/GDP). If this condition is false at any point in the next decade, the "sustained inability" framing would need to be revised — either the claim is wrong or US political economy has genuinely changed. Falsifiable and measurable.
- **Operationalize the "demand erosion" claim.** Proposal: construct a demand-stress index from (a) foreign holdings share of Treasuries (TIC data via FRED: FDHBFIN), (b) USD share of global central bank reserves (IMF COFER), (c) Treasury auction bid-to-cover on 10Y+ issuance. Track its trajectory; the thesis predicts secular decline. If this index stabilizes or reverses over the next decade, the "demand erosion" framing is weakened.
- **Construct a "fiscal-stress composite"** analogous to `internal_order_stress_index` but using fiscal-arithmetic inputs. Test lead-lag against equity drawdowns AND against USD real exchange rate (which is closer to what the thesis predicts). Per `civilizational-leads-financial.md` scale-principle, a cyclical null here does not falsify the transition-scale claim.

### Transition scale (requires cross-national historical data — issue #52)

- **The British-sterling precedent (1900-1975).** Sterling was reserve currency in 1914; gradually displaced 1945-1975. Did UK deficit/debt trajectories, foreign sterling holdings, and asset prices through the transition follow the pattern this thesis predicts? Did non-sovereign real assets preserve purchasing power better than gilts through the transition?
- **The Dutch-guilder precedent (1700-1800).** Per Dalio's research, the Amsterdam Wisselbank's reserve role decayed gradually; guilder devaluation and financial dislocation followed. Primary-source data is thin but directional analysis is possible.
- **Weimar 1919-1923, France 1918-1928, Argentina multiple periods.** Not reserve-currency transitions but mode-4 monetization case studies. How did different asset allocations perform? These are the definitive tests for the mode-4 operationalization of this thesis.

### Falsification direct

See next section.

## What would falsify this

- **Sustained fiscal consolidation:** US runs primary surpluses for multiple years while debt/GDP declines, under market yields. Would falsify the "unable to control deficit" core claim.
- **Sustained foreign demand expansion:** USD share of global reserves rises, foreign Treasury holdings share rises, long-duration auction demand strengthens — all while the US does NOT consolidate fiscally. Would falsify the "demand erosion" mechanism and suggest the reserve-currency status is more durable than the thesis claims.
- **Historical counterexample to the hegemony-decline pattern:** evidence of a world-reserve fiat currency that was NOT devalued during its issuing hegemony's decline. Would weaken the Dalio structural claim that underlies this thesis. Historically: unclear whether any such example exists; the null case (reserve currency where the issuer never declined) doesn't count. Sterling's 1920s brief stabilization attempts ended in devaluation; the Dutch guilder devalued through the 19th century. Need to search harder for counterexamples.
- **US enters austerity successfully:** fiscal consolidation achieved through spending cuts / tax increases at the scale required. Would rule out modes 2/3/4 and validate mode 1. Historically unprecedented for a reserve-currency issuer at this debt/GDP level.
- **Technology-driven productivity shock:** growth accelerates sufficiently that debt/GDP stabilizes without consolidation. Would not falsify the thesis but would defer its implications. The AI-productivity argument runs here; see `institutional-adaptation.md`.

## Related

- **`bond-allocation.md`** — this thesis provides the specific mechanism for why modes 2/3/4 are live in the US case. Bond-allocation is the allocation-side implication; this thesis is the macro scenario.
- **`backtest-sample-scope.md`** — this thesis names the specific transition that the US 1975-present sample cannot test. Cross-national data acquisition (#52) is the honest path to testing this thesis at its primary scale.
- **`institutional-adaptation.md`** — complementary mechanism. That thesis argues AI-era adaptation stress is an additional (tech-driven, faster, coalition-scrambling) decline driver. The two are not mutually exclusive; both can be true and may reinforce each other. If AI productivity stabilizes debt/GDP, this thesis's timeline extends; if AI disrupts coalition stability, both theses fire together.
- **`regime-aware-allocation.md`** — this thesis implies that the regime signals used in allocation should include fiscal-stress indicators, not just cyclical macro (yield curve, inflation, real rates).
- **`civilizational-leads-financial.md`** — demand-for-debt metrics may be a cleaner civilizational leading indicator than the current inequality/sentiment/EPU composite, specifically for this scenario.

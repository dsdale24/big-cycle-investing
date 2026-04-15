# Bond allocation thesis

**Status:** `active`
**Scale:** transition (primary); secular (partial)

## Claim

Sovereign bonds are vulnerable in three of four debt-cycle resolution modes. Their historical record as a wealth-preservation asset is a single-mode artifact. A strategy whose goal is preserving purchasing power across the big cycle cannot have bonds as a baseline allocation regardless of regime.

## Rationale

Dalio's debt-cycle resolution taxonomy distinguishes four modes: austerity, restructuring, default, and money-printing / monetization. Sovereign-liability asset outcomes under each:

| Mode | Bondholder outcome |
|---|---|
| 1. Austerity (cut spending, honor debt) | Win — rates fall, debt paid in full |
| 2. Restructuring (extend, modify terms) | Lose — direct haircut |
| 3. Default (write down) | Lose — write-down, potentially to zero |
| 4. Monetization (print, debase) | Lose — paid in nominal currency that's worth less |

TIPS fix mode 4 (CPI-indexed) but share modes 2 and 3 with nominal bonds (still Treasury obligations). Cash is a zero-duration sovereign liability with the same exposure pattern.

The 1981-2020 bond bull market was an extended period in mode 1 (disinflation plus credible debt service). The 2008 and 2020 episodes commonly cited as "bonds-as-deflation-hedge" wins were mode-1-adjacent — flight-to-safety panics where the Fed eased aggressively and rates collapsed, not actual restructurings or defaults.

## Implications

- Don't propose strategy defaults with >~15% combined sovereign-liability weight (nominal + TIPS + cash) unless explicitly tied to regime signals.
- TIPS is a tactical mode-4 hedge, not a core holding (demoted from #10's original framing).
- Non-sovereign-liability assets (gold, commodities, real-asset equities) form the wealth-preservation core.
- Regime-conditional sovereign-liability exposure: down-weight when monetization-mode indicators fire (debt/GDP × debt acceleration × persistent negative real rates × monetary base expansion × CDS spreads); retain in mode-1 conditions.
- AllWeather is NOT a neutral benchmark — it embodies mode-1 (disinflation) assumptions. Comparing against it implicitly accepts the bond-heavy frame. Propose non-sovereign-liability-tilted comparators (gold + commodities + real-asset equities) where useful.

## Current evidence

None yet at the transition scale (that's thesis `backtest-sample-scope`). Partial cyclical evidence from PR #47: BigCycleStrategy (both binary and scored variants) underperforms AllWeather on drawdown by ~9 ppt on 1980-2024, consistent with the bond-heavy base being the real lever rather than the regime classifier nuances. This is weak evidence — same-era data, AllWeather favored by regime, does not bear on transition-scale claims.

**Tested at cyclical scale (2026-04-15, PR #56 / issue #50, `docs/research/regime_scoring_comparison.md`):**

A `non_sovereign_heavy` base profile was added to `BigCycleStrategy` reducing sovereign-liability from 45% to 25% (new base: 30% equities, 5% long bonds, 5% short bonds, 25% gold, 20% commodities, 15% cash). Regime-score logic unchanged. Full-period 1980-2024 metrics:

| Strategy | CAGR | Vol | Sharpe | Max DD |
|---|---|---|---|---|
| AllWeather | 8.28% | 8.59% | 0.96 | −22.9% |
| BigCycle scored (balanced base, 45% sov.) | 7.84% | 9.35% | 0.84 | −31.3% |
| BigCycle scored (non-sovereign base, 25% sov.) | 7.50% | 19.10% | 0.39 | −61.1% |

Per-decade max DD (non-sovereign variant only):
- 1980s: −10.3% (shallowest of all 4 strategies that decade — inflation-tail behavior consistent with thesis)
- 1990s: −15.1%
- 2000s: −34.4%
- 2010s: −24.9%
- 2020s: −61.1% (also delivers highest CAGR that decade, 9.9% — consistent with inflation-regime thesis at the cost of concentrated-real-asset volatility)

**What this evidence says (weak negative, cyclical scale):** Naively swapping sovereign-liability exposure for a concentrated gold+commodities base (45% combined), with the existing regime logic layered on top, does NOT deliver better risk-adjusted outcomes on 1980-2024 US data. Sharpe collapses from 0.84 to 0.39; full-period max DD doubles from −31% to −61%. The thesis's edge cases *do* show up at the decade level (1980s shallowest DD, 2020s highest CAGR), so the directional claim (sovereign bonds underperform during inflation tails) is visible — but the cost of getting that edge through static real-asset concentration is too high to pay for itself over 45 years of mostly disinflation.

**What this evidence does NOT say:**
- Does NOT falsify the transition-scale version of the thesis. 1980-2024 is US-ascendant disinflation-heavy per `backtest-sample-scope.md`. Mode-1 resolution dominated the sample.
- Does NOT rule out better implementations of the thesis: *regime-conditional* (not baseline) real-asset exposure, TIPS as inflation-linked sovereign alternative, equity-heavier bases, broader regime-signal inputs. These are distinct hypotheses from "45% → 25% sovereign-liability with static gold/commodity replacement."
- Does NOT show that AllWeather-style mode-1-assuming bases are universally superior — it shows them superior in the regime they were designed for.

**Implication for strategy design:** the thesis's core claim (don't baseline-load sovereign liability) likely still holds, but the operationalization needs more than "reduce bonds, add gold/commodities at the base." Regime-conditional real-asset exposure is the direction to explore next.

## What would test this

- **Cyclical:** strategy A/B tests with varying bond-weight baselines vs equivalent gold/commodity weights on 1975-2024 data. Weak but tractable. **First pass done 2026-04-15 (PR #56 / issue #50)** — naive 45%→25% sovereign-liability with static real-asset replacement delivers weak negative cyclical-scale evidence. Follow-up candidates: regime-conditional real-asset exposure, equity-heavier bases, TIPS inclusion.
- **Transition:** performance of bond-heavy vs non-sovereign-liability portfolios across UK 1914-1950, Weimar 1919-1923, and analogous transitions in cross-national datasets (see `backtest-sample-scope.md` for data acquisition). The definitive test.

## What would falsify this

- Cross-national evidence showing sovereign bonds preserve wealth across modes 2-4 on average — would falsify. Very unlikely given the definitional mechanics of restructuring/default/debasement.
- Evidence that the US (uniquely) can maintain mode-1 conditions indefinitely would refine the thesis toward "applies everywhere except the issuer of the reserve currency." This is worth tracking as an explicit refinement candidate.

## Related

- `backtest-sample-scope.md` — why US 1975-2024 cannot validate the transition-scale claim
- `regime-aware-allocation.md` — the implementation mechanism this thesis implies

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

## What would test this

- **Cyclical:** strategy A/B tests with varying bond-weight baselines vs equivalent gold/commodity weights on 1975-2024 data. Weak but tractable.
- **Transition:** performance of bond-heavy vs non-sovereign-liability portfolios across UK 1914-1950, Weimar 1919-1923, and analogous transitions in cross-national datasets (see `backtest-sample-scope.md` for data acquisition). The definitive test.

## What would falsify this

- Cross-national evidence showing sovereign bonds preserve wealth across modes 2-4 on average — would falsify. Very unlikely given the definitional mechanics of restructuring/default/debasement.
- Evidence that the US (uniquely) can maintain mode-1 conditions indefinitely would refine the thesis toward "applies everywhere except the issuer of the reserve currency." This is worth tracking as an explicit refinement candidate.

## Related

- `backtest-sample-scope.md` — why US 1975-2024 cannot validate the transition-scale claim
- `regime-aware-allocation.md` — the implementation mechanism this thesis implies

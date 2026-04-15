# Regime-aware allocation thesis

**Status:** `tested` (cyclical scale, weak)
**Scale:** cyclical (tested); secular and transition (untested)

## Claim

Allocation strategies that adapt to macro regime signals preserve wealth better than fixed-weight strategies across a full big cycle. Even on the cyclical scale, regime-aware allocation should at least match fixed-weight strategies on risk-adjusted metrics while providing the ability to shift when regime changes — the optionality of shift is worth something.

## Rationale

Dalio's All Weather is itself a regime-aware argument made via static balancing (weight assets so the portfolio is neutral to which of four environments — growth up/down × inflation up/down — plays out). A stronger version of the argument: don't just balance across regimes passively; detect which regime is active and tilt toward assets favored by that regime.

## Implications

- BigCycleStrategy's original design was a coarse expression of this thesis: binary classification of (yield curve × inflation × real rates) into four regimes, apply regime-specific nudges to a base allocation.
- The continuous-score version (PR #47) generalized the classifier from binary thresholds to score-blended nudges.
- Both variants rest on this thesis. If the thesis is wrong, the variants are wrong for the same reason.

## Current evidence

**Tested at cyclical scale (PR #47, `docs/research/regime_scoring_comparison.md`):**

Over 1980-2024 on US cached data:
- AllWeather: CAGR 8.28%, Sharpe 0.96, max DD -22.9%, turnover 0.030
- BigCycle binary: CAGR 8.09%, Sharpe 0.83, max DD -32.4%, turnover 0.055
- BigCycle scored: CAGR 7.84%, Sharpe 0.84, max DD -31.3%, turnover 0.064

Both BigCycle variants underperform AllWeather on every metric, most notably drawdown (BigCycle ~ -32% vs AllWeather -23%). Binary vs Scored is a wash (Sharpe delta +0.01, drawdown delta -1.1 ppt, CAGR delta -0.25 ppt, turnover delta +0.009).

**Weak evidence, with caveats:**
1. 1980-2024 is the era AllWeather was designed for (disinflation + mode-1 conditions per `bond-allocation.md`). AllWeather's outperformance is expected in-regime; it says little about out-of-regime performance.
2. BigCycle's specific regime signals (yield curve, inflation, real rate) may simply be the wrong signals — a bad instance of regime-aware doesn't disprove regime-aware in general.
3. BigCycle's base allocation is ~35% sovereign-liability (bonds + cash), which is heavy relative to what `bond-allocation.md` implies. The base weights may be the real driver of drawdown underperformance, not the classifier nuances.
4. Cyclical-scale testing is silent on whether regime awareness helps at transition scale — the primary project goal.

**Follow-up at cyclical scale (2026-04-15, PR #56 / issue #50, `docs/research/regime_scoring_comparison.md`):**

Tested the "caveat #3" hypothesis — that base weights (not regime logic) drive the weak result — by adding a `non_sovereign_heavy` base profile (25% sovereign-liability vs 45%) with identical regime logic. Result: the lighter-sovereign base performs *worse* on aggregate (Sharpe 0.39 vs 0.84; max DD −61% vs −31%). See `bond-allocation.md` for full numbers.

**What this means for regime-aware-allocation:**
- Rules out the narrow version of caveat #3 — swapping sovereign for a static real-asset base does not rescue the regime-aware strategy's underperformance vs AllWeather. The issue is NOT simply "BigCycle has too many bonds."
- Consistent with caveat #2 (signals may be wrong) AND caveat #1 (regime favored AllWeather). Both remain live — this test doesn't discriminate between them.
- Status stays `tested` (cyclical scale, weak). No status change: the regime-aware thesis wasn't directly challenged, just the "base weights are the confound" escape hatch.

**Next discriminating test for caveat #1 vs #2:** a regime-aware strategy that (a) uses *different* regime signals (credit spreads, debt acceleration, money supply) and (b) applies regime-conditional real-asset tilts (not baseline). If that still trails AllWeather on 1980-2024, the cyclical-scale case for regime-aware weakens further. If it wins, caveat #2 (wrong signals) was the lever.

## What would test this more fully

- **Cyclical, better instance:** A version of regime-aware with (a) lower sovereign-liability base weights and (b) regime signals drawn from a broader indicator set (credit spreads, money supply growth, debt acceleration) rather than just three. If this version beats AllWeather, the thesis is supported for cyclical scale; if not, the thesis is weakened.
- **Transition:** Cross-national backtest of regime-aware vs fixed-weight across UK 1900-1980, Weimar, etc. Requires data from `backtest-sample-scope.md`.

## What would falsify this

- Across multiple cyclical instances with diverse regime-signal choices, regime-aware strategies consistently fail to beat fixed-weight strategies (on risk-adjusted metrics AND in out-of-regime periods). Would be moderate falsification for cyclical scale.
- Cross-national transition-era tests showing regime-aware strategies did not preserve wealth better than simple non-sovereign-liability portfolios (gold + commodities). Strong falsification.

## Related

- `bond-allocation.md` — the current weak evidence may be confounded by base weights rather than regime logic; this thesis can't be cleanly tested until that one is addressed
- `civilizational-leads-financial.md` — if civilizational signals lead financial ones, they may be the better regime-detection inputs than the current yield-curve/inflation/real-rate trio

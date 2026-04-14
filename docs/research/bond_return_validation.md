# Bond Return Approximation Validation

Date: 2026-04-14
Issue: #8
Spec: `docs/specs/backtester.md` §"Bond return approximation"
Script: `scripts/validate_bond_returns.py`

## Question

Are the synthetic bond returns produced by `build_asset_returns()` accurate
enough for fair strategy comparison?

The synthetic returns use a first-order duration approximation:

```
daily_return = -duration × Δyield + yield_prev / 252
```

with `duration = 8` for `long_bonds` (10Y proxy, `^TNX`) and `duration = 2`
for `short_bonds` (2Y proxy, `GS2`).

## Method

Compare synthetic monthly returns against real ETF total-return data over
the available overlap (2002-07 → present):

- `long_bonds` vs **TLT** (iShares 20+ Year Treasury Bond ETF)
- `short_bonds` vs **SHY** (iShares 1-3 Year Treasury Bond ETF)

Per spec, the approximation is adequate if **both** of these hold per asset:

- Per-decade |CAGR divergence| ≤ 0.50 percentage points per year
- Correlation of monthly returns ≥ 0.90

If either bound is violated, the spec requires splicing the ETF data for
the overlap period.

## Result

```
asset       | decade | synthetic_CAGR | ETF_CAGR | divergence_ppt_per_yr | correlation
------------+--------+----------------+----------+-----------------------+-------------
long_bonds  | 2000s  | +4.94%         | +6.02%   | -1.08                 | 0.929
long_bonds  | 2010s  | +3.81%         | +7.23%   | -3.42                 | 0.929
long_bonds  | 2020s  | -0.33%         | -4.07%   | +3.74                 | 0.929
short_bonds | 2000s  | +3.52%         | +3.31%   | +0.21                 | 0.771
short_bonds | 2010s  | +0.85%         | +1.09%   | -0.25                 | 0.771
short_bonds | 2020s  | +2.20%         | +1.83%   | +0.36                 | 0.771

long_bonds vs TLT:  MAE(monthly) = 1.550%   corr = 0.929   FAIL
short_bonds vs SHY: MAE(monthly) = 0.215%   corr = 0.771   FAIL
```

**Both assets fail the spec threshold:**

- `long_bonds` correlation passes (0.929 ≥ 0.90), but per-decade CAGR divergence is **−1.08 / −3.42 / +3.74 ppt/yr** — far beyond the 0.50 ppt/yr bound. Worst is the 2010s (−3.42), where the synthetic understates by 3.4 ppt/yr; over the decade that compounds to roughly 30% of missing return.
- `short_bonds` per-decade divergence is within tolerance (≤ 0.36 ppt/yr), but **correlation is only 0.771**, well below the 0.90 bound.

## Interpretation

The long_bonds error pattern is informative: synthetic **understates** in the
2000s and 2010s (rates falling) and **overstates** in the 2020s (rates rising).
That's the unmistakable signature of missing **convexity** — bond convexity
contributes positive return when rates fall and negative return when they rise,
and a pure duration model misses both.

Convexity matters most for long-duration assets (~10-year duration here), so
it's no surprise short_bonds shows a smaller per-decade error magnitude. The
short_bonds correlation problem is likely from coupon roll/reinvestment effects
that matter relatively more for short bonds (where the carry term dominates the
price-change term).

## Decision

Per the spec ("If either bound is violated, the implementation must splice
real ETF data for the overlap period"), both assets need ETF splicing:

- **long_bonds**: splice TLT for `2002-07-30 → present`; keep duration
  approximation for `1975 → 2002-07-29` (no alternative)
- **short_bonds**: splice SHY for `2002-07-30 → present`; keep duration
  approximation for `1975 → 2002-07-29`

This is the same splicing pattern used for `gold` and `commodities` in #1.
Implementation tracked separately so this PR stays focused on the validation
result.

## Open questions

1. **Pre-2002 uncertainty.** The 1975-2002 window is exactly the period that
   matters most for long-horizon backtests, and we have no ETF benchmark to
   measure approximation error there. The convexity-bias pattern observed
   2002+ is likely also present pre-2002. We should communicate this in
   backtest outputs (e.g., flag pre-2002 bond returns as "approximation
   only" in result metadata).

2. **Should we also splice TIP for inflation-linked exposure?** TIP is
   already in `configs/series.yaml`. Out of scope for #8; relevant if we add
   TIPS as an asset class (#10).

3. **Hybrid for the 1990s?** The 1990s aren't in the validation window
   (TLT/SHY start 2002-07), but ICE BofA Treasury indices on FRED go back
   further. Could expand the validation if precision matters more later.

## Reproducing

```bash
source .venv/bin/activate
python scripts/fetch_data.py     # ensures TLT and SHY are cached
python scripts/validate_bond_returns.py
```

The script is deterministic and reads only cached parquet files.

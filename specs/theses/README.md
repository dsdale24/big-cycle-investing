# Theses

This directory tracks the **project theses** — hypothetical scenarios, claims, and interpretive frames that inform what gets specced and built. Theses sit one layer above specs: they're the *why* behind component choices. A thesis is a claim we hold about how the world works (or doesn't) that shapes allocation, data acquisition, and evaluation decisions.

## How theses relate to other artifacts

| Artifact | What it captures | Example |
|---|---|---|
| `specs/<component>.md` | **Contracts.** What a stabilized component does; invariants and test cases. | "BacktestResult exposes `asset_sources` for every business day." |
| `specs/theses/<claim>.md` | **Theses.** Claims about the world that shape which components we build and how. | "Sovereign bonds are a deflation hedge, not a wealth-preservation core." |
| `docs/research/*.md` | **Empirical findings.** Measurement outputs; what a specific test showed. | "Duration-approximation bonds diverge from TLT by 3.4 ppt/yr in 2010s." |

When a thesis status changes — especially to `falsified` or `refined` — any spec that depends on it should be reviewed. Specs can be grounded on theses; when the ground shifts, the spec may need to shift too.

## The scale principle (load-bearing)

Every thesis and every empirical test in this project applies at one or more **scales**. Mixing scales is the single most common reasoning error in this domain and has already happened in this project.

| Scale | Timeframe | What plays out | What data we have |
|---|---|---|---|
| **Cyclical** | 3–10 years | Recessions, business cycles, quarterly sentiment swings | Extensive: US 1975-present |
| **Secular** | 10–40 years | Disinflation/inflation regimes, credit cycles, demographic shifts | Partial: US 1975-present covers ~1.5 secular regimes |
| **Transition** | 50–200 years | Reserve-currency shifts, empire transitions, printing-press-class institutional upheaval | **None in-dataset.** Requires cross-national historical data (see `backtest-sample-scope.md`). |
| **Meta** | N/A | Claims about what other theses can be tested with; statements about the dataset itself rather than about the world | N/A — these are structural, not empirical |

**A test at one scale is silent on another.** A signal that lags cyclical drawdowns can still be a valid leading indicator for secular or transition-scale shifts — the mechanisms are different (sentiment reacts to earnings; Gini decays over decades). Stating "the composite is a lagging indicator" without scale qualification conflates these and leads to wrong conclusions.

When recording a thesis test result, always state **which scale(s) it addresses** and **which it doesn't**.

## Status vocabulary

- **`active`** — hypothesis in play, informing work, no direct test yet
- **`testing`** — currently instrumented; a diagnostic or experiment is in progress or being designed
- **`tested`** — some test has been run; the body of the thesis file says at what scale and with what result
- **`falsified`** — evidence contradicts the claim at a relevant scale (always say which)
- **`refined`** — superseded by a sharper version (link forward)
- **`confirmed`** — tested across multiple scales or via strong cross-national evidence with consistent results (rare; high bar)

The body of each thesis is more important than the status label. A one-word status can't capture scale-conditional results; the prose must.

## Index

| Thesis | Status | One-line claim |
|---|---|---|
| [bond-allocation](bond-allocation.md) | `active` | Sovereign bonds are vulnerable in 3 of 4 debt-cycle resolution modes; bond exposure should be regime-conditional, not baseline. |
| [backtest-sample-scope](backtest-sample-scope.md) | `active` | US 1975-present is one sample from the US-ascendant era; transition-scale scenarios aren't in the dataset; cross-national historical data is the honest path. |
| [institutional-adaptation](institutional-adaptation.md) | `active` | The printing press → Reformation arc is a complementary precedent to empire decline: a technology-driven, faster, coalition-scrambling transition mode. |
| [regime-aware-allocation](regime-aware-allocation.md) | `tested` (cyclical, weak) | Regime-conditional allocation beats fixed-weight allocation. |
| [civilizational-leads-financial](civilizational-leads-financial.md) | `tested` (cyclical scale only; transition scale untested) | Civilizational stress indicators lead financial stress; they enable earlier portfolio positioning than financial indicators alone. |

## Adding a thesis

1. New file `specs/theses/<short-kebab-name>.md` with the schema below. Section headers match the existing thesis files — keep them consistent so cross-referencing stays reliable.
2. Add one line to the index above.
3. On any PR that tests, confirms, or falsifies a thesis, update the thesis file and the index row. The `review-pr` agent can flag PRs that implicate theses.

### Thesis file schema

Every thesis file in this directory uses the same section ordering:

```markdown
# <Thesis title>

**Status:** <status vocabulary term>
**Scale:** <cyclical | secular | transition | meta, with qualifiers>

## Claim
One-to-three-sentence statement of the thesis.

## Rationale
Why we hold it — evidence, reasoning, framing.

## Implications
What this claim shapes in the project (asset choices, data acquisition, benchmarks, signal interpretation).

## Current evidence
Dated log entries citing specific research artifacts (PRs, `docs/research/*.md` files, commits). Don't overwrite prior entries — build the evidence log. Note which scale each entry addresses.

## What would test this
Concrete tests that would bear on the thesis, at what scale, with what data requirements.

## What would falsify this
Specific findings that would contradict the claim at a relevant scale. This is the discipline that keeps theses honest.

## Related
Cross-references to other thesis files whose claims interact with this one.
```

## Adding evidence to an existing thesis

Update the thesis's "Current evidence" section with a dated entry citing the specific research artifact (PR, `docs/research/*.md`, commit) that produced the evidence. Don't overwrite prior entries — build the evidence log.

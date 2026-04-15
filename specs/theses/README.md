# Theses

This directory tracks the **project theses** — hypothetical scenarios, claims, and interpretive frames that inform what gets specced and built. Theses sit one layer above specs: they're the *why* behind component choices. A thesis is a claim we hold about how the world works (or doesn't) that shapes allocation, data acquisition, and evaluation decisions.

## How theses relate to other artifacts

| Artifact | What it captures | Example |
|---|---|---|
| `specs/<component>.md` | **Contracts.** What a stabilized component does; invariants and test cases. | "BacktestResult exposes `asset_sources` for every business day." |
| `specs/theses/<claim>.md` | **Theses.** Claims about the world that shape which components we build and how. | "Sovereign bonds are a deflation hedge, not a wealth-preservation core." |
| `docs/research/*.md` | **Empirical findings.** Measurement outputs; what a specific test showed. | "Duration-approximation bonds diverge from TLT by 3.4 ppt/yr in 2010s." |

When a thesis status changes — especially to `falsified` or `refined` — any spec that depends on it should be reviewed. Specs can be grounded on theses; when the ground shifts, the spec may need to shift too.

## Thesis structure: umbrella + sub-theses + counter-theses

The theses in this directory are organized around one **umbrella thesis** with sub-theses that compose it and peer-level **counter-theses** that oppose it. This structure was made explicit on 2026-04-15 so the relationships are legible from the directory listing.

- **Umbrella:** [`changing-world-order/`](changing-world-order/) — the Dalio-inspired worldview the project is operationally built around. The folder's [`README.md`](changing-world-order/README.md) is the umbrella thesis itself; [`dalio-principles.md`](changing-world-order/dalio-principles.md) is a reference catalog of Dalio's specific modeling specifications (the 2021 *Changing World Order* + 2025 *How Countries Go Broke* + 2022-2026 LinkedIn/X writing). The six sub-theses in the same folder compose the umbrella.
- **Counter-theses:** peer-level adversarial positions at this directory's top level (NOT inside `changing-world-order/` — the structure should not imply they are second-class). Each counter-thesis names its steelman case, what evidence would strengthen it, and what evidence would falsify it (and thus support the umbrella).

**Stance: Dalio-inspired, not Dalio-faithful.** The project uses Dalio's framework as scaffolding because it compresses a large quantity of economic history into recurring structures. The project departs from Dalio where evidence, fit, or measurement warrant; departures are named explicitly in [`changing-world-order/dalio-principles.md`](changing-world-order/dalio-principles.md) section by section. The project is **skeptical of "this time is different" dismissals** — the burden of proof is on novelty arguments, not on the base-rate pattern.

**Paired evidence tracking is load-bearing.** Every substantive new data point should update both the umbrella's evidence log AND any counter-thesis it bears on. This operationalizes the "skeptical of this-time-is-different" stance — counter-theses don't get dismissed, they get evidence-tracked. If a counter-thesis accumulates strong support and the umbrella does not, the project's operational positioning should shift rather than rationalize.

## The scale principle (load-bearing)

Every thesis and every empirical test in this project applies at one or more **scales**. Mixing scales is the single most common reasoning error in this domain and has already happened in this project.

| Scale | Timeframe | What plays out | What data we have |
|---|---|---|---|
| **Cyclical** | 3–10 years | Recessions, business cycles, quarterly sentiment swings | Extensive: US 1975-present |
| **Secular** | 10–40 years | Disinflation/inflation regimes, credit cycles, demographic shifts | Partial: US 1975-present covers ~1.5 secular regimes |
| **Transition** | 50–200 years | Reserve-currency shifts, empire transitions, printing-press-class institutional upheaval | **None in-dataset.** Requires cross-national historical data (see [`changing-world-order/backtest-sample-scope.md`](changing-world-order/backtest-sample-scope.md)). |
| **Meta** | N/A | Claims about what other theses can be tested with; statements about the dataset itself rather than about the world | N/A — these are structural, not empirical |

**A test at one scale is silent on another.** A signal that lags cyclical drawdowns can still be a valid leading indicator for secular or transition-scale shifts — the mechanisms are different (sentiment reacts to earnings; Gini decays over decades). Stating "the composite is a lagging indicator" without scale qualification conflates these and leads to wrong conclusions.

When recording a thesis test result, always state **which scale(s) it addresses** and **which it doesn't**.

**Note:** the project's three-scale taxonomy differs from Dalio's own (political ~10y / big debt cycle 75-100y / dynastic ~250y ± 150y). The divergence is the subject of issue #79; see [`changing-world-order/dalio-principles.md`](changing-world-order/dalio-principles.md) §2.

## Status vocabulary

- **`active`** — hypothesis in play, informing work, no direct test yet
- **`testing`** — currently instrumented; a diagnostic or experiment is in progress or being designed
- **`tested`** — some test has been run; the body of the thesis file says at what scale and with what result
- **`falsified`** — evidence contradicts the claim at a relevant scale (always say which)
- **`refined`** — superseded by a sharper version (link forward)
- **`confirmed`** — tested across multiple scales or via strong cross-national evidence with consistent results (rare; high bar)

The body of each thesis is more important than the status label. A one-word status can't capture scale-conditional results; the prose must.

## Index

### Umbrella

| Thesis | Status | One-line claim |
|---|---|---|
| [changing-world-order](changing-world-order/README.md) | `active` | Reserve-currency-issuer empires follow a recognizable arc; the US is late in that arc; wealth preservation requires positioning accordingly. Dalio-inspired, not Dalio-faithful. |

Reference: [`changing-world-order/dalio-principles.md`](changing-world-order/dalio-principles.md) — specific Dalio specifications the project builds against, with evolution through 2026.

### Sub-theses (compose the umbrella; live in `changing-world-order/`)

| Thesis | Status | One-line claim |
|---|---|---|
| [us-fiscal-deterioration](changing-world-order/us-fiscal-deterioration.md) | `active` | US deficit trajectory + eroding Treasury demand + hegemony decline imply monetization as the likeliest terminal debt-cycle resolution — the umbrella's central implication. |
| [bond-allocation](changing-world-order/bond-allocation.md) | `active` | Sovereign bonds are vulnerable in 3 of 4 debt-cycle resolution modes; bond exposure should be regime-conditional, not baseline. |
| [backtest-sample-scope](changing-world-order/backtest-sample-scope.md) | `active` | US 1975-present is one sample from the US-ascendant era; transition-scale scenarios aren't in the dataset; cross-national historical data is the honest path. |
| [civilizational-leads-financial](changing-world-order/civilizational-leads-financial.md) | `tested` (cyclical scale only; transition scale untested) | Civilizational stress indicators lead financial stress; they enable earlier portfolio positioning than financial indicators alone. |
| [institutional-adaptation](changing-world-order/institutional-adaptation.md) | `active` | The printing press → Reformation arc is a complementary, technology-driven transition mode — this project's refinement of how Dalio's integrated-AI framing plays out under constitutional rigidity. |
| [regime-aware-allocation](changing-world-order/regime-aware-allocation.md) | `tested` (cyclical, weak) | Regime-conditional allocation beats fixed-weight allocation. |

### Counter-theses (peer-level adversarial positions)

Each counter-thesis opposes the umbrella. Filed as issues; draft status varies.

| Thesis | Status | One-line claim | Issue |
|---|---|---|---|
| reserve-currency-stickiness | forthcoming | USD has network effects sterling lacked; transition timeline is much longer or doesn't occur. | [#82](https://github.com/dsdale24/big-cycle-investing/issues/82) |
| productivity-outruns-debt | forthcoming | AI-era real growth deflates debt/GDP organically; no monetization needed. | [#83](https://github.com/dsdale24/big-cycle-investing/issues/83) |
| institutional-resilience | forthcoming | US has been through worse polarization (1860s, 1930s, 1960s); system absorbs and recovers. | [#84](https://github.com/dsdale24/big-cycle-investing/issues/84) |
| mmt-stance | stub (forthcoming) | Sovereign fiat issuers face inflation constraint, not solvency; mode-4 is a category error. | [#85](https://github.com/dsdale24/big-cycle-investing/issues/85) |
| deflationary-tech | stub (forthcoming) | Structural tech deflation absorbs monetary accommodation; inflation doesn't materialize. | [#86](https://github.com/dsdale24/big-cycle-investing/issues/86) |

## Adding a thesis

**Sub-thesis (composes the umbrella):** new file `specs/theses/changing-world-order/<short-kebab-name>.md` with the schema below. Add one line to the sub-theses index table. Update [`changing-world-order/README.md`](changing-world-order/README.md)'s "How sub-theses compose the umbrella" section to explain the new sub-thesis's role. Update the umbrella's "Related" section.

**Counter-thesis (adversarial to the umbrella):** new file `specs/theses/<short-kebab-name>.md` at the top level (NOT inside `changing-world-order/`). Same schema. Add one line to the counter-theses index table. Ensure the counter-thesis names (a) its steelman case, (b) what would strengthen it, (c) what would falsify it (supporting the umbrella). Include an evidence-log section with empty-but-present structure from day one (e.g., "— no evidence gathered yet, thesis articulated YYYY-MM-DD —").

**On any PR that tests, confirms, or falsifies a thesis,** update the thesis file and the index row. The `review-pr` agent can flag PRs that implicate theses.

### Thesis file schema

Every thesis file (umbrella, sub-thesis, or counter-thesis) uses the same section ordering:

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

**Paired tracking:** when evidence bears on both the umbrella and a counter-thesis, update both. Single-sided evidence logs are a signal of framing drift and are flagged by `review-adversarial`.

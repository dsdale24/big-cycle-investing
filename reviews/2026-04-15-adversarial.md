# Adversarial review: big-cycle-investing

_Date: 2026-04-15_
_Branch at time of review: main_
_Reviewer: adversarial (Claude subagent)_

**Headline:** The project has turned documenting-the-problem into the work itself — theses, reviews, and review infrastructure are proliferating while the one piece of work that could falsify the central thesis (cross-national data, #52) has not moved in any observable way, and the prior external review's "honest fork" was resolved by splitting the difference into a design issue (#65) rather than picking.

## What's working

- Scale-principle discipline is real and is doing epistemic work — the 2026-04-15 component-decomposition null on Gini was not laundered into a positive finding.
- Negative results are logged with full numbers in `bond-allocation.md` rather than buried. This is rarer than it should be.
- The backtester spec (walk-forward, splicing tests, `approximation_exposure()`) is high quality for research code.

## Findings

### 1. The external reviewer's fork got answered by building process, not by choosing

On 2026-04-15 the external review posed an explicit fork: commit to #52 as critical path, or reframe the project as a cyclical tool with a big-cycle overlay. The response was to open issue #65 ("two-layer architecture… resolve central tension") describing a hybrid and then spend the rest of the day on PRs #55, #58, #66, #67, #68 — GitHub Actions, thesis-capture prose, review-agent infrastructure, CLAUDE.md discoverability checks. None of that advances transition-scale validation. The #65 framing ("neither a nor b — pursue a hybrid") is a classic response to a forced choice: refuse the choice and build scaffolding on both sides. The reviewer's warning that "hybrid architectures drift toward the cheap side (cyclical, because it's easy to measure)" was acknowledged in the issue body and then ignored in the day's work. If a reviewer predicts your failure mode and you reproduce it the same afternoon, the review-agent infrastructure you just built will not save you — it will be part of the symptom.

### 2. Issue #52 is load-bearing by explicit stipulation and has zero progress

`us-fiscal-deterioration.md` names #52 as "not optional supplementary work — it's the only way to honestly stress-test the strategy against this scenario." `backtest-sample-scope.md` names it as the load-bearing remediation. The bond-allocation thesis names its "definitive test" as cross-national. Issue #52 was opened 2026-04-15 01:53 UTC and — as of the latest commits — has zero comments, no sub-issues, no exploratory branch, no data-source triage, no spec shell. Meanwhile priorities 1-5 of the #65 design issue assume #52 is in motion. A "hard dependency" that nobody has started is not a dependency; it's an excuse. The project would be more honest if it either (a) put a coding agent on Jorda-Schularick-Taylor ingestion this week or (b) admitted the transition-scale arm will not be tested and retitled the strategy accordingly.

### 3. The central thesis added a page and subtracted a falsifier

PR #58 captured the US-fiscal-deterioration thesis with seven pages of rationale and proposed a "fiscal-stress composite" as the operationalization. That composite does not exist — no issue, no spec, no code, no data-series registry update. Grep finds the phrase only in the thesis file itself. The thesis simultaneously widens the claim (hegemony-decay, reserve-currency, weaponized SWIFT, etc.) and narrows the falsifier to conditions — "sustained primary surpluses for multiple years while debt/GDP declines" — that are an order of magnitude harder to observe than a falsifier on the composite would be. This is the shape of a thesis being written to feel more confirmed by default. If you believe the fiscal-stress mechanism is the central thesis, the composite should exist before the thesis doc does, not after, and certainly not instead of.

### 4. Reviewer-production is outrunning reviewable substance

In the last 48 hours the project added: five review-agent types, an umbrella `/review-cycle` command, a `--ephemeral` mode, a CLAUDE.md discoverability check for the review-pr agent, a seeded external review, this adversarial review. In the same period the actual strategy work consisted of one negative-result PR (#56, confirming AllWeather dominates in its own regime), two thesis-documentation PRs, and two GitHub Actions workflows. The ratio of meta-infrastructure to substance is a Claude-failure signature: it feels like progress because artifacts are produced, but each artifact is a further commitment to reviewing rather than doing. The review paradigm in CLAUDE.md is now longer than the backtester spec. If the next two weeks of work are in `.claude/` and `reviews/` rather than `src/` and `data/`, the review infrastructure has become the project.

### 5. Dalio is treated as given; no counter-tradition has been engaged

Every thesis cites Dalio; none cite Minsky, Kindleberger, Reinhart-Rogoff (beyond the 90% threshold reference), Koo (balance-sheet recession), or MMT. The us-fiscal thesis asserts "every world-reserve fiat currency in recorded history has been devalued during its hegemony's decline" as a regularity, sourced entirely to `Principles for Dealing with the Changing World Order` — and then adds in the same thesis: "Not independently verified in this project yet; taken as the starting hypothesis." A thesis whose primary empirical support is one popular book by a fund manager who profited from the counter-scenario (disinflation) should be held more loosely than this one is. The falsification criterion "evidence of a world-reserve fiat currency that was NOT devalued during its issuing hegemony's decline" also quietly excludes the one strongly relevant case (USD itself, thesis-in-progress), which makes the claim borderline unfalsifiable by construction.

### 6. The personal-strategy question is explicitly deferred, which means the numbers do not bind

Issue #12 ("what does this mean for Darren specifically?") is marked `exploring` with "not urgent." Every backtest produced so far is in pre-tax, pre-cost, pre-behavioral terms with no account-type mapping, no rebalancing-friction model, no RMD path, no concentrated-gold custody reality. A 51-year-old with a ~30-year horizon choosing between a 25% gold / 20% commodities base and an AllWeather base is going to eat 0.5-1.5 ppt/yr of tax-and-friction drag that the backtest does not see, and the 61% drawdown in the non-sovereign variant's 2020s decade is not a number a real portfolio would survive sitting through. The project can produce a correct research answer and still produce an unimplementable personal strategy. Running the adversarial reviewer before the practitioner reviewer is defensible; running the adversarial reviewer instead of the practitioner reviewer is not.

## The central question

Is this a research project whose outputs will change how Darren's money is actually invested, or a research project that will produce a library of well-documented theses and a series of negative findings about US 1975-present data? Both are legitimate endeavors. They imply different next actions. The current pace of infrastructure work is consistent with the second; the stated thesis is consistent with the first; that mismatch is the thing that will waste a year of work if it's not named.

## Recommendations

1. Put a coding agent on #52 this week. Even a Jorda-Schularick-Taylor ingestion with no indicator work is motion. Until there is transition-scale data in the repo, no further cyclical-layer work should land.
2. Stop producing new review types until the existing ones have been used against substantive (not infrastructure) PRs at least twice each.
3. Either open an issue for the fiscal-stress composite with a concrete spec target date, or remove the implication from the thesis that the composite is part of the operationalization.
4. Read one Minsky paper and one Koo chapter; add a "counter-traditions" section to `specs/theses/README.md` naming the frameworks that contradict big-cycle and what they would predict instead. A thesis not in dialogue with its strongest critics is a belief, not a thesis.

## Questions worth sitting with

- What would it take to declare the central thesis falsified? The current falsifier ("sustained primary surpluses") is an event that takes a decade to confirm absent. Is there a faster-resolving falsifier?
- If #52 is genuinely blocked (cost, data access, scope), what is the next-best honest reframing — and why hasn't it been written?
- Is the review infrastructure being built because the project needs it, or because building it feels like progress that doesn't require confronting #52?

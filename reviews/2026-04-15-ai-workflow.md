# AI-workflow review: big-cycle-investing

_Date: 2026-04-15_
_Branch at time of review: main_
_Reviewer: ai-workflow (Claude subagent)_

**Headline:** The governance regime works when applied — PR #97/#98 demonstrate real spec-first discipline with working feedback loops — but the regime was built, tested, and refined in a single session that produced 9 governance PRs for every 4 substantive ones, and no enforcement mechanism exists beyond the review-pr agent reading the rules back to itself.

## What's working

- **Spec-first discipline held on the first real test.** PR #97 authored the UK pipeline spec as commit `9e1725e` (first on branch), delegated implementation against it, and the implementation agent honored report-don't-patch on 5 spec gaps rather than silently routing around them. PR #98 continued the pattern: spec observation commits preceded implementation commits. This is the workflow working as designed.
- **Review-pr catches real issues.** The #97 review flagged missing Co-Authored-By trailers as a nit; the CLAUDE.md rule landed in #99; all 6 non-merge commits in #98 carry trailers. That is a three-PR feedback arc from detection to codification to compliance.
- **Governance miss became governance fix.** The Phase A explore/stable misclassification was caught, archived transparently (`archive/uk-phase-a-no-spec-2026-04-15`), analyzed, and produced a structural fix (file-type heuristic in #95) rather than being rationalized or buried.
- **PR bodies are unusually informative.** Governance alignment sections, commit chronology tables, agent-surfaced observations, and known-nit disclosures make the PR thread a durable review surface. This is real maker-checker provenance.

## Layer 1 — Spec quality

### Twelve MUSTs with no enforcement beyond prompt compliance

CLAUDE.md contains 12 MUST-level rules (file-type heuristic, spec-first ordering, delegation-time citations, Co-Authored-By trailers, branch-prefix choice, mixed-scope splitting, etc.). Every one of them is enforced by the same mechanism: the review-pr agent reads the rule and checks for it. There is no hook, no CI check, no pre-commit gate. If a session starts without loading CLAUDE.md (a fresh agent, a GitHub Actions context, a hurried delegation), every MUST is aspirational. The `create-spec` skill's own principle 3 ("every MUST should have an enforcement mechanism") applies to the workflow spec itself. The file-type heuristic is the most load-bearing rule and the most vulnerable — it requires the coordinator to classify correctly before delegation, and the only backstop is a post-hoc review-pr comment that arrives after implementation is complete.

### Discoverability is deep but linear

A fresh coordinator starting with CLAUDE.md will find the Workflow section, the spec-driven development section, the maker-checker model, the review infrastructure, and the deny list. But the interaction between these sections — the file-type heuristic triggers `stable/` which triggers spec-first which triggers delegation-time citation which triggers Co-Authored-By — is a chain that must be assembled by reading linearly. There is no summary of "the 5 things you must get right before delegating." The create-spec skill partially addresses this for spec-authoring, but the delegation checklist is still scattered across 4 CLAUDE.md subsections. A coordinator who reads the Workflow table but skips the spec-driven-development bullets will miss the Co-Authored-By and citation requirements.

### The `docs/` branch prefix is doing too much work

`docs/` covers CLAUDE.md governance changes (#95, #99), agent definitions (#101), skill creation (#100), thesis restructuring (#87), review outputs (#71), and thesis evidence updates (#54, #57). These are qualitatively different: a governance change to CLAUDE.md reshapes how all future work is done; a thesis evidence update is a one-paragraph append. The branch-prefix table in CLAUDE.md defines `docs/` as "Documentation, specs, CLAUDE.md changes" with no further subdivision. This means branch-prefix alone cannot distinguish a high-impact governance PR from a routine evidence-log update, reducing the signal the prefix was designed to carry.

## Layer 2 — Implementation fidelity

### Branch-prefix compliance improved after #95 but started wrong

PRs #66 and #68 used `explore/` for work that created files exclusively in `.claude/` (agent definitions, commands, review-state.json). Under the post-#95 regime, `.claude/` files are not in the `src/`/`tests/`/`configs/` trigger set, so `explore/` would not technically violate the file-type heuristic — but it also does not match the `explore/` definition ("purely in `notebooks/`, `docs/research/`, or `data/`"). The `.claude/` directory is not named in any branch-prefix rule. Post-#95 PRs touching `.claude/` (#99, #100, #101) all used `docs/`, which is reasonable but not specified. This is a gap in the heuristic — `.claude/` is governance infrastructure, not documentation, and the branch-prefix table does not account for it.

### Co-Authored-By trailers: compliant after the rule, noncompliant before

PR #97's three implementation commits (`aca1cfe`, `85e9784`, `57ded7d`) lack Co-Authored-By trailers. PR #98's six non-merge commits all have them. The rule was codified in PR #99 between these two PRs, so #97's absence is pre-rule and #98's presence is post-rule compliance. The system corrected within one PR cycle. However, since the trailer is a prompt-level instruction with no git hook enforcement, compliance depends on the coordinator remembering to include it in every delegation prompt — the same single-point-of-enforcement pattern as the MUSTs above.

### Maker-checker boundary held cleanly on stable/ PRs

On PR #97: coordinator commits (`9e1725e`, `d846112`, `db3f2d1`) touch only `specs/`. Agent commits (`aca1cfe`, `85e9784`, `57ded7d`) touch only `src/`, `tests/`, `configs/`, `scripts/`, `pyproject.toml`. On PR #98: coordinator commits (`2b8691b`, `845c00d`, `7dabbc6`) touch only `specs/`. Agent commits (`d481024`, `042c659`, `881a15f`, `9b92eb5`) touch only `configs/`, `tests/`. The deny-list boundary was respected in both cases. No coordinator commit edited a deny-listed path; no agent commit edited a spec.

### Review-pr is catching real issues, not rubber-stamping

PR #95's review flagged the `configs/` omission in the delegation-time restatement (nit); coordinator fixed it in a follow-up commit (`99f5289`); re-review passed. PR #97's review flagged missing Co-Authored-By trailers and 4 spec-implementation drift points; all were addressed in #98 or codified in #99. PR #98's re-review confirmed all fixes landed. This is genuine two-pass quality improvement, not performative review.

## Layer 3 — Effectiveness

### Governance-to-substance ratio is 9:6 in a single session

Of the last 15 merged PRs: 4 are pure substantive research (#54, #56, #57, #58); 2 are substantive infrastructure with governance-test value (#97, #98 — UK pipeline); 9 are pure governance/process (#55, #66, #68, #71, #87, #95, #99, #100, #101). The adversarial reviewer flagged this pattern the same day. The workflow spec (CLAUDE.md Periodic Reviews + Workflow + Spec-driven development + Maker-checker model) is now longer than any component spec in the project. The review infrastructure (7 agent definitions, 9 slash commands, 2 skills, a review-state tracker, a reviews README with meta-story) is more complex than the backtester it reviews. This is the Claude-specific failure mode the adversarial review named: artifact production that feels like progress because each artifact is well-crafted.

### The workflow caught one real governance miss — and then spent 7 PRs responding to it

The explore/stable misclassification on Phase A was a genuine catch. The response: archive the work (#95 context), sharpen the heuristic (#95), redo the implementation spec-first (#97), expand it (#98), codify three workflow additions (#99), build a spec-authoring skill (#100), build a workflow reviewer (#101). Each PR is individually defensible. Collectively, a single branch-prefix mistake generated more governance output than the entire UK data pipeline produced in substantive data-engineering output. The proportionality question is whether 7 governance PRs for 1 governance miss is a calibrated response or a displacement activity. The workflow spec does not have a concept of proportionality — there is no "when to stop governance-refining and go back to substance" signal.

### Spec-first discipline produces genuinely better artifacts

Comparing PR #97 (spec-first UK pipeline) against the archived exploratory implementation: the spec-first version has spec-anchored tests for every test case, error messages citing the governing spec, and an implementation agent that reported 5 spec gaps rather than silently working around them. The exploratory version presumably did not have these properties (it was archived as a governance failure). This is evidence that the maker-checker model produces what it claims — better artifacts than flow-state coding. But the evidence is a sample of 1, from the same session that built the governance model, on a component (data pipeline) that was already well-understood from the US implementation. The test of whether spec-first works on genuinely novel components (regime classifier, strategy logic) has not occurred.

## The central question

The workflow spec assumes that governance quality compounds — that each rule, each reviewer, each skill makes future work better. But governance also has a carrying cost: context budget, session time, coordinator attention, displacement of substance. The spec has no mechanism for measuring whether the governance is paying for itself. The review-pr agent can tell you whether a PR followed the rules; no agent can tell you whether following the rules produced a better outcome than not following them would have. The archived Phase A comparison was a natural experiment that could have answered this — but it was framed as a governance lesson rather than a controlled measurement. Until the project has a way to measure governance ROI, the governance will grow monotonically because every miss generates new rules and no rule is ever retired.

## Recommendations

1. **Add a delegation checklist to CLAUDE.md** — a single numbered list of the 5-6 things the coordinator must get right before spawning a coding agent on a `stable/` branch. Currently scattered across 4 subsections. Would cost 10 lines and save the linear-discovery problem.
2. **Name `.claude/` in the branch-prefix table.** Currently unspecified. Governance infrastructure changes should have their own prefix or be explicitly assigned to `docs/`.
3. **Institute a governance-cost check.** Before opening a governance PR, ask: "Is this fixing a problem that has occurred more than once, or preventing one that occurred once?" Single-occurrence fixes can be captured as a review-pr nit pattern rather than a CLAUDE.md rule. This is the proportionality signal the workflow currently lacks.
4. **Defer new reviewer types until existing ones run against substantive PRs.** The adversarial reviewer's recommendation #2 ("stop producing new review types until existing ones have been used against substantive PRs at least twice each") applies to this reviewer as well. The next ai-workflow review should wait until there are 3+ substantive `stable/` PRs to audit.

## Questions worth sitting with

- If every MUST in CLAUDE.md were removed tomorrow and only the review-pr agent remained, which rules would the project spontaneously re-derive from actual failures? Those are the real rules. The rest are anticipatory governance that may never pay for itself.
- The governance miss that triggered PRs #95-#101 happened because the coordinator misapplied a soft rule. The fix was to make the rule hard. But the coordinator is also the entity that interprets and applies the hard rule — with no external enforcement. Has the failure mode actually changed, or has it just been documented more thoroughly?

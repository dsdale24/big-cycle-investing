---
name: create-spec
description: Use when the coordinator is about to author a stabilizing spec for a new or refactored component — any work that will touch `src/`, `tests/`, or `configs/` on a `stable/` branch per CLAUDE.md's file-type heuristic. Triggers explicitly via `/create-spec` and implicitly when the coordinator mentions "write a spec for X", "author a spec", "scaffold a spec", or is about to create a new file under `specs/` for a component. Provides the canonical sections, the 8 principles for writing specs, the MUST-checkable rule, inheritance-framing guidance for extension specs, and a template skeleton. Produces a scaffolded spec file at the target path.
---

# Create Spec

This skill is the coordinator's playbook for authoring stabilizing specs. It packages what has been learned about what makes a spec useful vs what makes a spec rot. Invoke it when you are about to write a spec; do NOT invoke it for small spec updates to an existing spec (that's a different pattern — just edit).

The skill's job: produce a **scaffolded spec file** at the target path with canonical sections present and placeholders where coordinator judgment is required. The coordinator edits in place; no interactive dialog.

## When to invoke

Explicit:
- `/create-spec` slash command
- User says "write a spec for X", "author a new spec", "scaffold a spec"

Implicit (proactive):
- The coordinator is about to commit a new file under `specs/` for a component
- A `stable/` branch is about to be created for work that doesn't yet have a spec
- An `explore/` phase has concluded and the coordinator is articulating what to stabilize

Do NOT invoke for:
- Small edits to an existing spec (just edit the file)
- Writing a thesis under `specs/theses/` (different pattern — see `specs/theses/README.md` schema)
- Writing an agent prompt under `.claude/agents/` (different pattern — agent prompts are operational, not component contracts)

## Inputs to gather

Before drafting, get from the coordinator (ask if not stated):

1. **Component name** (kebab-case, e.g., `uk_data_pipeline`, `regime_classifier`, `indicator_framework`)
2. **Target path** — where the spec file will live. Usually inferable from the component name:
   - Top-level component: `specs/{component}.md`
   - Country-specific extension: `specs/data_pipeline/{country}.md`
   - Other extension patterns: as appropriate to the existing `specs/` structure
3. **Upstream exploration** — the `explore/` branch or research artifact that informed the spec. For the coordinator:
   - If there is upstream exploration: cite the branch name or research-note path; the skill will pull context from it
   - If there is NOT upstream exploration: the coordinator MUST acknowledge "no upstream exploration; risk of spec drift during implementation is accepted" per CLAUDE.md's Workflow-section delegation-time rule
4. **Baseline spec** (optional) — if this spec extends another (e.g., UK pipeline extends US pipeline), name the baseline. Extension specs use the inheritance-framing pattern below.
5. **Related issues** — GitHub issue numbers for the feature, parent, and any known follow-up gaps

## The canonical sections (authoritative)

Every stabilizing spec MUST include these sections in this order. This list is the authoritative reference that `review-pr` §0 checks against.

1. **Title + metadata header** — component name, Status (Stabilizing/Settled), Last updated date, Depends on (if extension), Related theses, Related issues
2. **Purpose** — 1-3 sentences. Why this component exists; what problem it solves. Cite the thesis or issue it serves.
3. **Relationship to baseline** — ONLY if this spec extends another. Names conventions inherited unchanged; names overrides with reason. Skip if standalone.
4. **Source / Inputs** — where data, config, or dependencies come from. For data pipelines: name the source + version + cache layout. For code modules: name the functions/modules that feed this one.
5. **Invariants** — numbered MUSTs that hold across the component's lifetime. Each invariant MUST correspond to a spec-anchored test (see MUST-checkable rule below). Invariants are the falsifiable contract.
6. **Error behavior** — what errors are raised on what conditions, what the error messages say. Error messages SHOULD cite the governing spec section and any relevant issue number (CLAUDE.md code standards).
7. **Test cases** — enumerated list of `@pytest.mark.spec` tests that verify the invariants. Each test case: name, what it checks, which invariant it corresponds to, which pytest markers. A broken implementation MUST fail at least one of these tests.
8. **What this spec does NOT cover** — explicit scope-exclusion list with follow-up issue references. Prevents "why doesn't this do X?" from requiring spec archaeology.
9. **Related** — cross-references to other specs, theses, and issues.

Optional but useful sections (add when warranted):
- **Implementation notes** — non-obvious conventions the implementer should follow. Keep short; most belong in code comments, not the spec.
- **Future improvements** — named deferrals with rationale, tied to issues. Distinct from "does NOT cover" — these are intended future additions, not permanent exclusions.
- **Examples** — worked examples of usage. Useful for specs with non-obvious interface patterns.

## The 8 principles for writing specs

Apply these while drafting. They're organized from most-load-bearing to most-contextual.

### 1. Falsifiability over completeness

A spec that enumerates 6 falsifiable invariants beats one that describes the component in 30 paragraphs of prose. If you cannot write a test for an invariant, the invariant is vague — rewrite until you can. Completeness is aspirational; falsifiability is the contract.

**While drafting:** for each invariant you write, ask "can I write a test case that would fail if this invariant were violated?" If not, the invariant needs sharpening or deletion.

### 2. Every invariant has a test that enforces it

Invariants without tests are aspirations. The Test cases section functions as a check on the Invariants section — if an invariant has no test, either add a test OR delete the invariant. The two sections should be 1-to-N corresponded (one invariant → one or more tests; never one invariant → zero tests).

**While drafting:** after the Invariants section is complete, walk through each invariant and confirm a corresponding test case exists in the Test cases section. Gaps = drift.

### 3. MUST language MUST correspond to a spec-anchored test

Invariants stated with MUST MUST have a `@pytest.mark.spec` test that verifies them. Aspirational MUSTs drift from the implementation they're meant to constrain. Three options when you find yourself writing an unenforceable MUST:
- (a) Tighten by adding a spec-anchored test
- (b) Demote to SHOULD and acknowledge the invariant as documentation-level
- (c) Add the missing test in the same PR

Violations are flagged as Major findings by `review-pr` at pre-merge. The automated enforcement is human/agent verification at review time, not runtime — but "not runtime-enforced" is NOT the same as "uncheckable." Review is the enforcement mechanism.

**While drafting:** after writing each MUST, decide which of the three options applies. If it's (b), change the language to SHOULD before the spec ships. If it's (a) or (c), note the test-case name in the Test cases section.

### 4. The spec is a contract for the future maintainer, not the current implementer

Discoverability features — error messages citing spec sections, test names mapping to spec cases, explicit scope-exclusion lists — serve the maintainer arriving six months later (including AI agents in future sessions). The current implementer does not need them; the future maintainer does. Optimize for the future maintainer.

**While drafting:** when deciding whether to include a scope-exclusion bullet or a cross-reference, imagine a future maintainer reading the spec for the first time with a specific question. Would the bullet / reference answer their question? If yes, include it.

### 5. Defer scope explicitly, not silently

"What this spec does NOT cover" is a load-bearing section. Deferred items get named + follow-up issue references, not absent. "The spec doesn't mention X" leaves a future maintainer guessing whether X was considered. "The spec explicitly defers X to issue #N" answers the question.

**While drafting:** at the end, review what you're leaving out. Name each deferral with the follow-up issue (creating a new issue if needed). Untracked deferrals become invisible drift.

### 6. Spec changes are first-class events

Changing the spec is changing the contract. If the implementation reveals the spec is wrong, the spec-update commit MUST precede the implementation-update commit, with a clear commit message citing what the implementation (or research, or review) taught us. Never silently diverge implementation from spec.

**While drafting:** for any spec you're authoring as an update to an existing spec, call out in the commit message what changed vs. what stayed. For a new spec, call out what was discovered during `explore/` that informed the contract.

### 7. Inheritance and deltas beat restatement

For specs extending a baseline, name the inheritance explicitly ("inherits ... unchanged from `<baseline>.md`") and the deltas explicitly ("overrides ... with reason"). Don't restate the baseline; don't silently override. See "Inheritance-framing guidance" below.

**While drafting:** if this spec extends another, the first section after Purpose should be "Relationship to baseline." If you find yourself repeating content from the baseline, replace with a reference.

### 8. Exploration is a first-class phase, not a substitute for specification

`explore/` work is how we learn what the spec should contain. `stable/` work is where the contract is locked. A `stable/` spec written without upstream `explore/` inputs is a thin spec. If you are writing a spec without having done the exploration, name that risk — your spec will require mid-PR updates as implementation surfaces what you didn't know.

**While drafting:** cite the upstream `explore/` branch or research artifact in the spec's metadata header OR name the "no upstream exploration" acknowledgment explicitly.

## Inheritance-framing guidance (for extension specs)

When a spec extends a baseline (e.g., `specs/data_pipeline/uk.md` extending `specs/data_pipeline/us.md`), the structure should be:

```markdown
# UK data pipeline specification (Phase A of issue #52)

Status: **Stabilizing**
Last updated: YYYY-MM-DD
Depends on: [`us.md`](us.md) (baseline — conventions inherited unless overridden here)
Related theses: ...
Related issues: ...

## Purpose
[Why this extension exists; cite thesis/issue.]

## Relationship to baseline
[This spec extends `<baseline>.md`. Conventions inherited unchanged:]

- [Convention 1 — e.g., parquet cache layout]
- [Convention 2]
- ...

[Conventions overridden or added (the "deltas"):]

- **[Delta 1]** — [reason + what differs]
- **[Delta 2]** — [reason + what differs]

## [Remaining sections follow canonical order]
...
```

This pattern saves the reader from manually diffing two specs to find the extension points. It also makes drift checking tractable: if the baseline changes, the extension's inheritance section tells you what to re-verify.

## Template skeleton

Draft the scaffolded file with this structure. Placeholder text in `[brackets]` is for the coordinator to replace; structural text (section headers, invariant numbering) stays as-is.

```markdown
# [Component name] specification

Status: **Stabilizing**
Last updated: [YYYY-MM-DD]
Depends on: [path/to/baseline.md if extension, else omit this line]
Related theses: [path to thesis 1, path to thesis 2, or omit if none]
Related issues: [#parent-issue, #follow-up-1, #follow-up-2]

## Purpose

[1-3 sentences. Why this component exists; what problem it solves; which thesis or issue it serves.]

## Relationship to baseline

[ONLY include this section if Depends-on is set. Otherwise delete.]

[This spec extends `<baseline>.md`. Conventions inherited unchanged:]
- [Convention 1]
- [Convention 2]

[Conventions overridden or added (the "deltas"):]
- **[Delta 1]** — [reason]
- **[Delta 2]** — [reason]

## Source / Inputs

[Where data, config, or dependencies come from. For data pipelines: source + version + cache layout. For code modules: the modules/functions that feed this one.]

## Invariants

[Numbered list. Each invariant is a MUST or SHOULD. Each MUST MUST correspond to a test case in the Test cases section. Write invariants as falsifiable statements — a broken implementation violates at least one.]

1. [Invariant 1]
2. [Invariant 2]
3. ...

## Error behavior

[Per-error-condition: what triggers it, what the error message says. Error messages SHOULD cite the governing spec section and relevant issue numbers.]

- **[Error condition 1]:** [Raised on ..., message format: "..."]
- **[Error condition 2]:** ...

## Test cases (spec-anchored)

[Enumerated list of `@pytest.mark.spec` tests that verify the invariants. Each test case: name, what it checks, which invariant(s), which pytest markers.]

1. **[Test case name]** — verifies invariant [N]; marker: `@pytest.mark.unit` / `@pytest.mark.integration`
2. **[Test case name]** — verifies invariant [N]
3. ...

## What this spec does NOT cover

[Named deferrals with follow-up issue references. Prevents "why doesn't this do X?" from requiring archaeology.]

- **[Excluded topic 1]:** Deferred to issue #[N]
- **[Excluded topic 2]:** [Rationale + issue or explicit "permanent exclusion"]

## Related

- **Specs:** [cross-references]
- **Theses:** [cross-references]
- **Issues:** [cross-references]
- **Reviews:** [cross-references to reviews that informed this spec, if any]
```

## Worked examples (read these before drafting)

The best examples of the canonical pattern in this codebase:

- **`specs/data_pipeline/uk.md`** — extension spec with a full inheritance-framing section, 30 required series as falsifiable contract, 6 enumerated spec test cases, explicit unavailable-series handling, explicit "What this spec does NOT cover" list. Post-governance-sharpening exemplar.
- **`specs/data_pipeline/us.md`** — baseline spec (note: does NOT currently have enumerated test cases; tracked for hardening in issue #96). Useful as a reference for what a pre-current-regime spec looks like, and what the canonical pattern would tighten it into.
- **`specs/backtester.md`** — component spec with complex invariants around walk-forward correctness.
- **`specs/testing_and_ci.md`** — workflow-level spec; different shape (no Source/Inputs section) but same canonical discipline.

## Procedure (step by step)

When the skill activates:

1. **Gather inputs** — component name, target path, upstream exploration, baseline spec (if extension), related issues. Ask the coordinator if any are missing. Do NOT proceed without explicit acknowledgment of the upstream-exploration question (cite the `explore/` branch OR acknowledge no upstream exploration).
2. **Verify target path** — does a spec already exist there? If yes, do NOT overwrite; ask the coordinator whether this should be a spec update (different flow — just edit) or a rename.
3. **Read upstream context** if provided — load the explore branch's notebook/research-note content into context; this will inform the Purpose, Source, and Invariants sections.
4. **Read the baseline spec** if extension — load it into context so inheritance-framing is accurate.
5. **Draft the scaffolded file** at the target path using the template above. Fill sections where the inputs give you enough to fill; leave `[bracket]` placeholders where the coordinator must decide.
6. **Apply the 8 principles while filling in.** Specifically:
   - Each invariant drafted with MUST must either have a corresponding test case entry OR be downgraded to SHOULD (principle 3)
   - The "What this spec does NOT cover" section MUST be populated with explicit deferrals (principle 5) — do NOT leave blank even if the scope feels self-evident
   - Extension specs MUST have the Relationship to baseline section (principle 7)
   - The metadata header MUST either cite an upstream `explore/` branch or acknowledge "no upstream exploration" (principle 8)
7. **Report to the coordinator** — file written to `<target-path>`; summary of what was pre-filled vs what needs coordinator judgment. Suggest the next step: "Review the scaffolded file, edit as needed, commit as the FIRST commit on a `stable/` branch per CLAUDE.md Workflow section, then delegate implementation."

## After drafting: what the coordinator does next

Per CLAUDE.md:

1. Edit the scaffolded file to fill in any remaining `[brackets]` and refine the invariants/test cases
2. If the target is a new branch, create it: `git checkout -b stable/<phase>/<feature>`
3. Commit the spec as the first commit on the branch (per delegation-time rule)
4. Delegate implementation to a coding agent with the spec as the sole contract; delegation prompt MUST:
   - State the branch prefix and rationale
   - Cite the upstream `explore/` branch or acknowledge no exploration
   - Require Co-Authored-By trailer on commits (per CLAUDE.md)
5. Run `review-pr` after implementation commits land; §0 governance gate will check spec-coverage

## Sibling skills (planned, for reference)

If the action being taken is different, reach for a different skill:

- **`/review-spec`** (planned) — audit an existing spec against the canonical sections, 8 principles, and MUST-checkable rule. Produces a checklist-style report.
- **`/update-spec`** (planned) — guided revision when research or implementation discoveries change the contract. Different flow from `/create-spec`: starts from the existing spec, asks what's changing and why, drafts the update as a diff.

This skill is the `create` half. Review and update are separate flows with their own skills (when built).

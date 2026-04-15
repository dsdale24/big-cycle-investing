# Big Cycle Investing

Research project building a long-view wealth-preservation strategy inspired by Ray
Dalio's big cycle framework — but not restricted to his specific indicators. The
value is thinking in long cycles across financial, political, and civilizational
dimensions, and being open to any data that helps understand where we are.

## Project vision
Build an iterative research pipeline (inspired by Karpathy's autoresearch) that:
1. Tracks macro/financial + civilizational indicators from 1975 onward
2. Classifies macro regimes (expansion, overheating, contraction, reflation)
3. Backtests allocation strategies using only data available at each point in time
4. Automates experimentation — sweep parameters, log results, propose new hypotheses

The end goal is a walk-forward backtest answering: "If I had started this strategy
in 1975 with the data available at the time, and adapted as new indicators emerged,
what would my wealth-preservation outcomes have looked like?"

## Setup & commands

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Create .env with FRED API key (free: https://fred.stlouisfed.org/docs/api/api_key.html)
echo 'FRED_API_KEY=your_key_here' > .env

# Fetch all data series (~55 series, takes ~2 min)
python scripts/fetch_data.py

# Run notebooks
cd notebooks && jupyter notebook

# Tests (see specs/testing_and_ci.md for full definitions)
pytest                          # Everything (unit + integration + spec)
pytest -m "not integration"     # Unit + spec-without-integration — what CI runs, quick feedback
pytest -m integration           # Only tests that need the parquet cache — local, after fetching data
pytest -m spec                  # Only spec-anchored tests — audit "what enforces this spec?"
```

## Architecture
- `src/data_fetcher.py` — pulls historical data from FRED + Yahoo Finance, caches to parquet
- `src/indicators.py` — derived indicators (debt acceleration, real rates, regime classifier)
- `src/backtester.py` — walk-forward backtesting engine and strategy implementations
- `configs/series.yaml` — registry of ~55 data series with metadata
- `scripts/fetch_data.py` — entry point to download all data
- `notebooks/` — exploration and analysis (01: financial, 02: civilizational, 03: backtest)
- `specs/` — component specifications, indicator taxonomy, and project theses — top-level because specs are the primary entry point for development
- `specs/theses/` — project theses: claims and scenarios that inform which components get built and how results are interpreted. See `specs/theses/README.md` for the scale principle (cyclical / secular / transition) and status vocabulary. Theses sit one layer above specs; when a thesis status changes, any spec that depended on it should be reviewed.
- `data/` — cached parquet files (gitignored), `data/manifest.json` tracks fetch results

## Spec-driven development

This project uses spec-driven development with a progressive formalization approach.
The spec starts loose in exploration areas and tightens as components stabilize.

### The spec lifecycle
1. **Exploring** — No formal spec. Move fast, try things, learn what works. Notebooks
   and GitHub issues capture findings and hypotheses.
2. **Stabilizing** — Write a spec in `specs/` defining inputs, outputs, invariants,
   and edge cases. Add tests that verify the spec. This happens when a component is
   about to be depended on by other components.
3. **Settled** — Spec is authoritative. Changes require updating the spec first, then
   the implementation. Tests enforce the spec.

Components can move **backward** (Stabilizing → Exploring) if research reveals the
approach was wrong. This is expected and healthy in a research project.

### Current spec status
| Component | Status | Spec location |
|-----------|--------|---------------|
| Data pipeline (`data_fetcher.py`) | Stabilizing | `specs/data_pipeline.md` |
| Indicators (`indicators.py`) | Exploring | — |
| Backtester core (`backtester.py`) | Stabilizing | `specs/backtester.md` |
| Walk-forward constraint | Stabilizing | `specs/backtester.md` |
| Regime classifier | Exploring | — |
| Strategy logic | Exploring | — |
| Autoresearch loop | Not started | — |

### Core principle: implementation follows spec, never the reverse

The spec is the source of truth. When changing a stabilized or settled component:
1. **Update the spec first** — define the new behavior, invariants, edge cases
2. **Then implement** to match the spec
3. **Then test** against the spec

Never implement first and backfill the spec to match. That inverts the relationship
and turns the spec into unreliable documentation. If you find the spec is wrong
during implementation, stop — update the spec, then continue.

For exploring components, there is no spec to follow. Move fast. But the moment
you're about to stabilize, write the spec BEFORE the refactor.

### How to apply this
- **Before writing code:** Check if the component has a spec. If it does, read it.
  If your planned changes conflict with the spec, update the spec first.
- **When exploring:** No spec needed. Capture learnings in notebooks and issues.
- **When stabilizing:** Write the spec BEFORE refactoring. The spec defines what
  "correct" means. Include: inputs, outputs, invariants (things that must always
  be true), edge cases, and example test cases.
- **When something breaks:** If a bug reveals a missing invariant, add it to the spec
  and add a test. The spec grows from real failures, not hypothetical ones.
- **Every PR touching a specced component** should reference the relevant spec and
  note whether the spec was updated as part of the change.
- **At delegation time:** before spawning a coding agent, the coordinator MUST
  state the branch prefix in the delegation prompt and the rationale. If the
  prefix is `stable/`, the spec MUST exist before the implementation delegation
  (not written concurrently). The coordinator's first commit on a `stable/`
  branch MUST be the spec; implementation delegations follow. This is enforced
  by the file-type rule in the Workflow section — tests or `src/` code in a
  delegation prompt mean `stable/` and spec-first, no exceptions.

### Theses inform specs

`specs/theses/` holds project theses — claims about how the world works that shape which components get built and how results are interpreted. Theses are NOT specs (they're not code contracts) but they're upstream of them: a bond-allocation thesis shapes what BigCycleStrategy's base weights should look like; the backtest-sample-scope thesis shapes how backtest results should be framed in `docs/research/*.md`.

The theses in this directory are organized as an **umbrella thesis** with sub-theses that compose it, plus peer-level **counter-theses** that oppose it. The umbrella lives at `specs/theses/changing-world-order/` (the Dalio-inspired worldview); sub-theses are files in that folder; counter-theses sit at the top level of `specs/theses/`. See `specs/theses/README.md` for structure and `specs/theses/changing-world-order/dalio-principles.md` for the reference catalog of Dalio's specific modeling specifications the project builds against. Stance: **Dalio-inspired, not Dalio-faithful** — scaffolding accepted where useful, departures named explicitly. **Paired evidence tracking is load-bearing**: new data updates both the umbrella's evidence log AND any relevant counter-thesis, symmetrically.

- **Before running an experiment** — check `specs/theses/` to see what claim it's testing. If you're about to test something whose thesis isn't in there, consider whether it should be — new theses come up during research.
- **When a test produces results** — update the relevant thesis's "Current evidence" section. Don't overwrite prior entries; build the evidence log. Note the scale (cyclical / secular / transition) the test addresses.
- **Before changing a thesis's status** — especially to `falsified` or `refined` — review any specs or strategies that depend on it. Status changes can cascade.
- **Read `specs/theses/README.md`** — the scale principle (cyclical / secular / transition) is load-bearing. A test at one scale is silent on another. Mixing scales has already caused reasoning errors in this project.

## Periodic reviews

This project uses **multi-perspective periodic reviews** as a distinct feedback loop from PR-level review. Motivation: the PR-level `review-pr` agent catches spec-conformance issues within a single diff, but cannot see project-level drift (e.g., the cyclical-vs-transition tension surfaced in the 2026-04-15 external review). Different scales of feedback require different reviewers.

### Reviewer types

| Reviewer | Lens | Cadence target |
|---|---|---|
| `review-pr` | Spec conformance for a specific PR | Pre-merge (every mergeable PR) |
| `review-adversarial` | What the project is wrong about, what's avoided, where evidence is weak | Quarterly |
| `review-dalio` | Faithful application of Dalio's big-cycle framework | Quarterly |
| `review-practitioner` | Operational gap between backtest and real execution | Before strategy → `settled` |
| `review-data-quality` | Measurement soundness, unaudited approximations, silent leakage | After significant splicing/indicator work |
| `review-meta` | Evolution across the review series | Annually or after 3+ saved reviews |

Slash commands invoke each: `/review-adversarial`, `/review-dalio`, `/review-practitioner`, `/review-data-quality`, `/review-meta`. An umbrella `/review-cycle` runs the four project-level reviewers in parallel (those whose cadence is due by default; all four with `--all`), then meta sequentially.

Cadence is tracked in `.claude/review-state.json` but not enforced by automation. A review done reluctantly because cron fired it has no teeth.

### Saved vs. ephemeral

Reviews run in one of two modes:

- **Saved (default):** output lands in `reviews/YYYY-MM-DD-<type>.md`, committed via PR, counts toward the meta-review series, updates cadence state. This is the durable record.
- **Ephemeral (`--ephemeral` flag):** output lands in `reviews/.ephemeral/` (gitignored), skips state/README updates, no commit flow. Use for pulse-checks during rapid development when you want feedback without polluting the series signal or overloading the meta reviewer with drafts.

To promote an ephemeral review to saved: move the file from `reviews/.ephemeral/` to `reviews/` (or `reviews/meta/`), then update `.claude/review-state.json` and `reviews/README.md` manually (or re-run the command without `--ephemeral` to regenerate).

The meta reviewer explicitly ignores `reviews/.ephemeral/` when reading the series.

### How reviews relate to theses and specs

- **Reviews inform theses and specs**, not the other way around. A review finding may generate a new issue, a spec update, or a thesis-evidence-log entry — not automatically, but through coordinator review of the finding.
- **Reviews are not living documents.** Once written, they're frozen. Aging is information — a concern from a prior review that's still live tells you something different from a concern that's been resolved.
- **The series is the signal.** Individual reviews are snapshots. The pattern across reviews over time is what the meta reviewer looks for — and what `reviews/README.md`'s meta-story section captures in running commentary.

### When to run what

- **Pulse-check during a session:** `/review-adversarial --ephemeral` or similar; digest in-session, don't commit.
- **End of a substantive work cycle (PR landed on a big thesis or component):** run `/review-cycle` in default mode; commit the batch; let meta reason across the series.
- **Full milestone review:** `/review-cycle --all`; forces every reviewer type.
- **Before promoting a strategy to `settled`:** `/review-practitioner` saved.
- **After data-pipeline changes:** `/review-data-quality` saved.

See `reviews/README.md` for the full documentation.

## Workflow

**All work happens on branches. Never commit directly to main, and never merge
branches locally to main — always land changes via a pull request.**

| Branch prefix | Purpose | Spec required? |
|---------------|---------|----------------|
| `explore/{phase}/{feature}` | Exploratory work — notebooks, research notes, prototypes | No |
| `stable/{phase}/{feature}` | Stabilization — spec must be updated before implementation, tests required | Yes |
| `fix/{description}` | Bug fixes — update spec if the bug revealed a missing invariant | If specced |
| `docs/{description}` | Documentation, specs, CLAUDE.md changes | N/A |

Examples: `explore/phase1/civilizational-indicators`, `stable/phase2/regime-classifier`, `fix/walk-forward-leak`

**How to choose `explore/` vs `stable/` — file-type heuristic (hard rule).**

The "about to be depended on by other components" criterion in the spec lifecycle is soft and has been misapplied (see governance-miss note below). Replace it with a file-type rule:

- **Any PR that creates or modifies files in `src/`, `tests/`, or `configs/` is stabilizing by default**, regardless of how exploratory the research intent feels. Such PRs MUST use `stable/` and the spec MUST be written first.
- `explore/` MUST be used only when the work is purely in `notebooks/`, `docs/research/`, or `data/`.
- If a single stream of work needs both — a research notebook AND a new data-fetcher module — it MUST be split into two PRs: one `explore/` for the analytical output, one `stable/` for the infrastructure. Different branches, different review standards.
- Mixed-scope in one PR is permitted only with explicit justification in the PR body and coordinator sign-off. The default is split.

The goal of this rule: coordinator judgment is no longer required to decide "is this exploratory?" The decision is answered by looking at the diff's file paths. Tests alone (even if you feel the work is exploratory) are implicit stable-contract claims — exploratory work doesn't need them.

**Governance-miss note (2026-04-15):** Phase A of issue #52 was delegated to `explore/uk-sterling-transition` when the work created `src/data_fetcher_uk.py`, `configs/series_uk.yaml`, `scripts/fetch_uk_data.py`, and `tests/test_uk_data_fetcher.py`. Per the file-type rule above, it should have been `stable/phase2/uk-data-pipeline` with a spec authored first. The coordinator accepted this miss explicitly, preserved the exploratory implementation as `archive/uk-phase-a-no-spec-2026-04-15`, and re-did the stabilization under the new regime. The re-do is the test of this rule's value; the archive and `docs/research/spec-driven-vs-exploratory-uk-phase-a.md` are the comparison artifacts.

**Tracking:** Bugs, features, and tasks are GitHub issues at dsdale24/big-cycle-investing.
Labels: `exploring`, `stabilizing`, `bug`, `data`. See issue #13 for the full roadmap.

**At session start (or when resuming after a gap):**
- If `.claude/skills/changelog-check/state.json`'s `last_checked` is more than
  1 day old, invoke `/skill changelog-check` to see if any Claude Code
  updates affect this project's workflow. Claude Code ships frequently
  (multiple releases most weeks), so a daily cadence catches fixes close to
  when they land. The skill reports new entries in three buckets (ticks #33
  / likely relevant / worth noting) and asks the coordinator what to act on.
- Check open issues with `gh issue list` before starting substantive work.
- Check `.claude/review-state.json` — if any reviewer type is past its cadence
  target, surface it to the user as a one-line reminder. Don't auto-run
  reviews; the coordinator decides. See "Periodic reviews" above.

Reference issues in commits (e.g., "Fixes #1"). Commits from `stable/*`
branches must reference the spec they conform to.

### Maker-checker model

The main Claude instance is a **coordinator**, not a coder. All code is written by
subagents and reviewed before merging.

| Role | Who | Responsibility |
|---|---|---|
| **Coordinator** | Main instance | Spec management, task delegation, merge decisions. Does not write code. |
| **Coding agent** | Subagent | Implements on a branch per the spec. Commits to the branch. |
| **Review agent** | Subagent | Reviews implementation against the spec. Flags deviations, missing tests, edge cases. |

#### Coordinator deny list

The coordinator must NOT directly edit any file under these top-level directories — all changes there go through a coding agent on a branch:

- `configs/` — runtime configuration consumed by code
- `data/` — cached data artifacts (gitignored, but listed for completeness)
- `docs/` — research notes
- `notebooks/` — exploratory analysis (Python in JSON form is still code)
- `scripts/` — runnable Python scripts
- `src/` — production code
- `tests/` — test code

The coordinator's editable surface is everything else: `CLAUDE.md`, `.claude/` (skills, settings, hooks, agents, slash commands), `specs/` (spec authorship is the coordinator's domain by design — see "Spec-driven development" above), and root-level meta files (`README.md`, `.gitignore`, `pyproject.toml`).

**Why a directory-level deny list, not a judgment call.** "Is this code?" is a judgment that erodes ("is a YAML config code? a Jupyter notebook? a Python script in `scripts/`?"). "Is this path under one of these seven directories?" is not. When a deny-listed file needs to change — even a one-line markdown comment in a notebook or a path string in a config — delegate.

**The two coordinator exceptions to no-touch.**
1. **Measurement** — running scripts or tests to read numbers off the system. The coordinator runs `pytest`, `python scripts/validate_*.py`, etc., to gather state but does not edit those files.
2. **Spec authorship** — `specs/` is coordinator territory by design (spec-driven development). The coordinator writes the contract; agents fulfill it.

If you (the coordinator) catch yourself reaching for `Edit` or `Write` on a deny-listed path, stop and delegate. Even one-line fixes go through an agent — the boundary is what makes the maker-checker model work, and the boundary erodes one "just this once" at a time.

**The flow:**
1. Coordinator reads the spec (or writes/updates it if needed)
2. Coordinator creates the branch and delegates to a coding agent with the spec and context
3. Coding agent implements and commits on the current branch
4. Coordinator delegates to a review agent to check implementation against spec
5. Coordinator reviews findings, approves or sends back
6. Coordinator pushes the branch and opens a pull request (never merges locally to main)
7. Before merging, coordinator runs a **pre-merge review** of the PR — either via `/review-pr <number>` (which delegates to the `review-pr` subagent defined at `.claude/agents/review-pr.md`) or by spawning the agent directly with `Agent(subagent_type="review-pr", ...)`. The agent's report ends with an embedded `## Pre-merge review` block; the coordinator (or `/review-pr`) posts that block verbatim as a PR comment immediately, and on merge approval includes the same block in the merge commit body via `gh pr merge --body`. Same review lands in two durable places: the PR thread on GitHub (visible to author and future readers) and the merge commit (permanent, surfaces in `git log`). Merge only on PASS or PASS-WITH-NITS (see #15 for the Level 1/2/3 escalation path toward CI enforcement)
8. Work is landed by merging the PR — this preserves a reviewable artifact, keeps a searchable history, and gives CI and the review agent a surface to hook into

**Coding agents work in the main checkout, not worktrees.** Earlier versions of
this workflow used `isolation: "worktree"` for filesystem isolation, but for a
solo project the overhead (env-var propagation, permission slicing, data-cache
absence, hook complexity) outweighed the benefit. Subagents now operate in the
coordinator's checkout on the current branch and commit there directly.

Implications:
- The coordinator should not have uncommitted code edits during a delegation —
  any in-progress work belongs in a commit (or a separate branch) before
  delegating, so the agent's diff is unambiguous.
- `git diff` after the agent reports gives a clean review surface; no merge
  step from a worktree branch is needed.
- For measurement-style tasks (run a script, report numbers), prefer running
  the script directly from the coordinator session — delegation overhead
  exceeds benefit when there's no real implementation work to do.
- Tests that depend on the parquet cache at `data/raw/` will work because the
  cache is in the main checkout. The `@pytest.mark.integration` marker
  (defined in `specs/testing_and_ci.md`) still exists for tests that need
  real data — they run locally, not in CI.

Worktree-based isolation may be revisited in a future Claude Code version
where the wrinkles (settings inheritance, env-var propagation, hook semantics)
are smoother.

**Background by default:** Coding agents should run with `run_in_background: true`
when the task is well-specified. The spec is the contract — if the spec is complete,
the agent doesn't need to interrupt the user for clarification. The coordinator can
continue other work and is notified when the agent completes. If the agent gets
stuck, a review agent catches issues after completion; we don't lose time to
mid-task interruptions.

Exceptions (run foreground): when the spec is still being negotiated, when the
task is a tight feedback loop, or when the coordinator needs the result immediately
to proceed.

**Effort budgets:** Every delegation prompt should include an effort estimate and
early-exit conditions. The Agent tool doesn't track effort automatically, so the
contract lives in the prompt. Example:

> This task should take roughly 5-10 tool calls. If you exceed 20 calls without
> clear progress, stop and report what's blocking you. If the spec is ambiguous,
> stop and report the ambiguity rather than guessing. Do not expand scope beyond
> what's in the spec.

This gives the agent permission to stop and report rather than thrash. A stuck
agent reporting "I'm blocked on X" is far more useful than one that spent 50
tool calls rationalizing a wrong approach.

**Reporting is success, workarounds are failure.** When an agent hits an
obstacle — missing data, failing test that touches unrelated infrastructure,
ambiguous spec, permission block — the correct response is to stop and report
the obstacle. The incorrect response is to expand scope, modify unrelated
config, or invent wrappers to route around the problem. An agent that reports
"I'm getting a permission denial on `python scripts/validate.py`, here's the
exact command and error" has succeeded. An agent that creates a wrapper script
to launder the same command past the allowlist has failed the contract even
if the code technically works.

Every coding agent delegation prompt must explicitly state:
- **Scope boundaries** — list what is out of scope (config files, unrelated
  modules, other components' specs)
- **Report-don't-patch** — if a tool or script can't run, report it back
  rather than inventing workarounds

**Why:** Separating writing from reviewing catches errors that flow-state coding misses.
The coordinator stays at the spec level and never gets pulled into implementation details.
This also prevents the anti-pattern of implementing first and rationalizing the spec after.

## Code standards

Code should be well-organized and self-documenting. Follow:
- [PEP 8](https://peps.python.org/pep-0008/) — style and naming conventions
- [PEP 257](https://peps.python.org/pep-0257/) — docstring conventions
- [PEP 484](https://peps.python.org/pep-0484/) — type hints for function signatures

Prefer clear names and structure over comments. Comments explain *why*, not *what*.
If code needs a comment to explain what it does, refactor it to be self-evident.

## Key constraints
- All backtesting must be walk-forward: only use data available at each point in time
- Backtest start date: 1975-01-01
- Annual/periodic data is fine — forward-fill and use as regime context, not trading signals
- Python 3.11+, pandas, matplotlib/plotly, pyarrow, venv at `.venv/`
- FRED API via `fredapi`, yfinance for market price data

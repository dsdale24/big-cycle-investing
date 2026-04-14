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

# Tests (see docs/specs/testing_and_ci.md for full definitions)
pytest                          # Everything (unit + integration + spec)
pytest -m "not integration"     # Unit + spec-without-integration — CI, worktrees, quick feedback
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
- `docs/indicator_framework.md` — full indicator taxonomy (11 categories, series IDs, coverage dates)
- `docs/specs/` — component specifications (backtester, data pipeline)
- `data/` — cached parquet files (gitignored), `data/manifest.json` tracks fetch results

## Spec-driven development

This project uses spec-driven development with a progressive formalization approach.
The spec starts loose in exploration areas and tightens as components stabilize.

### The spec lifecycle
1. **Exploring** — No formal spec. Move fast, try things, learn what works. Notebooks
   and GitHub issues capture findings and hypotheses.
2. **Stabilizing** — Write a spec in `docs/specs/` defining inputs, outputs, invariants,
   and edge cases. Add tests that verify the spec. This happens when a component is
   about to be depended on by other components.
3. **Settled** — Spec is authoritative. Changes require updating the spec first, then
   the implementation. Tests enforce the spec.

Components can move **backward** (Stabilizing → Exploring) if research reveals the
approach was wrong. This is expected and healthy in a research project.

### Current spec status
| Component | Status | Spec location |
|-----------|--------|---------------|
| Data pipeline (`data_fetcher.py`) | Stabilizing | `docs/specs/data_pipeline.md` |
| Indicators (`indicators.py`) | Exploring | — |
| Backtester core (`backtester.py`) | Stabilizing | `docs/specs/backtester.md` |
| Walk-forward constraint | Stabilizing | `docs/specs/backtester.md` |
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

## Workflow

**All work happens on branches. Never commit directly to main, and never merge
branches locally to main — always land changes via a pull request.**

| Branch prefix | Purpose | Spec required? |
|---------------|---------|----------------|
| `explore/{phase}/{feature}` | Exploratory work — notebooks, new indicators, prototypes | No |
| `stable/{phase}/{feature}` | Stabilization — spec must be updated before implementation, tests required | Yes |
| `fix/{description}` | Bug fixes — update spec if the bug revealed a missing invariant | If specced |
| `docs/{description}` | Documentation, specs, CLAUDE.md changes | N/A |

Examples: `explore/phase1/civilizational-indicators`, `stable/phase2/regime-classifier`, `fix/walk-forward-leak`

**Tracking:** Bugs, features, and tasks are GitHub issues at dsdale24/big-cycle-investing.
Labels: `exploring`, `stabilizing`, `bug`, `data`. See issue #13 for the full roadmap.

Before starting work: check open issues (`gh issue list`). Reference issues in commits
(e.g., "Fixes #1"). Commits from `stable/*` branches must reference the spec they conform to.

### Maker-checker model

The main Claude instance is a **coordinator**, not a coder. All code is written by
subagents and reviewed before merging.

| Role | Who | Responsibility |
|---|---|---|
| **Coordinator** | Main instance | Spec management, task delegation, merge decisions. Does not write code. |
| **Coding agent** | Subagent | Implements on a branch per the spec. Commits to the branch. |
| **Review agent** | Subagent | Reviews implementation against the spec. Flags deviations, missing tests, edge cases. |

**The flow:**
1. Coordinator reads the spec (or writes/updates it if needed)
2. Coordinator creates the branch and delegates to a coding agent with the spec and context
3. Coding agent implements and commits on the branch (uses `isolation: "worktree"`)
4. Coordinator delegates to a review agent to check implementation against spec
5. Coordinator reviews findings, approves or sends back
6. Coordinator pushes the branch and opens a pull request (never merges locally to main)
7. Work is landed by merging the PR — this preserves a reviewable artifact, keeps a searchable history, and gives the review agent (see issue #15) a surface to hook into

**Worktrees:** Coding agents should use `isolation: "worktree"` so they work on an
isolated copy of the repo. This prevents conflicts with files the coordinator or user
has open, and produces a clean diff to review before merging.

Claude Code's default is to branch worktrees from `origin/HEAD` (i.e., main),
regardless of which branch the coordinator is on. That's wrong for our flow —
when the coordinator delegates from a feature branch with in-progress spec
updates, the agent must see those updates. This project installs a
`WorktreeCreate` hook at `.claude/hooks/create_worktree_from_head.py` that
overrides the default and branches from the coordinator's current HEAD. Wired
up in `.claude/settings.json` (committed). Result: delegation from any branch
produces a worktree based at that branch's tip.

`.env` is auto-copied into each subagent worktree via `.worktreeinclude`
(committed). Agents must NOT copy `.env` manually or otherwise modify config to
escape the worktree boundary — the copy is the sanctioned mechanism and needs
no action from the agent.

**Worktree testing boundary:** Worktrees have a clean checkout but no populated
`data/` directory (parquet cache is gitignored and lives in the main repo). This means:
- **Tests using synthetic/fixture data** run fine in a worktree — prefer these for
  any test that checks logic (splicing, conversion formulas, invariants).
- **Tests that read real cached data** (e.g., loading fetched FRED/Yahoo parquet
  files) will not find the cache and should either skip gracefully or be run by
  the coordinator in the main repo after the agent reports.
- **`scripts/fetch_data.py`** can be run from a worktree (since `.env` is
  auto-copied via `.worktreeinclude`), but will fetch into the worktree's own
  `data/` directory — not the main cache. Agents needing cache verification
  should still report back rather than re-fetching.

Agents must NOT modify config or change paths to escape the worktree boundary.
If tests or scripts can't run from the worktree, that's a scope signal — report
it, don't patch around it.

For full test category definitions and CI design, see docs/specs/testing_and_ci.md.

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
config, or invent new flags to route around the problem. An agent that reports
"I can't verify the compounding identity against real data because the parquet
cache isn't in the worktree" has succeeded. An agent that silently copies `.env`
into the worktree or patches paths to escape the boundary has failed the
contract even if the code technically works.

Every coding agent delegation prompt must explicitly state:
- **Scope boundaries** — list what is out of scope (config files, unrelated
  modules, other components' specs)
- **Report-don't-patch** — if a test or script can't run from the worktree,
  report it back rather than modifying config or environment to make it work

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

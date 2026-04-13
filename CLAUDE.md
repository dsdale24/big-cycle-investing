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

**All work happens on branches. Never commit directly to main.**

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
3. Coding agent implements and commits on the branch
4. Coordinator delegates to a review agent to check implementation against spec
5. Coordinator reviews findings, approves or sends back
6. Coordinator merges to main

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

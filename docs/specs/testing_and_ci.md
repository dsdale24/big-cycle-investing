# Testing and CI Specification

Status: **Stabilizing**
Last updated: 2026-04-13

## Purpose

Define how tests are organized, when each category runs, and what CI enforces.
Every specced component in this project depends on tests to verify its invariants;
this document is what makes "stabilizing" mean "tested".

## Scope

- Test categories and pytest markers
- Where each category can run (local, worktree, CI)
- What CI's required check runs
- How `@pytest.mark.spec` links tests to spec invariants
- Worktree testing boundary (consolidated here; CLAUDE.md references this spec)

What this spec does NOT cover: coverage thresholds, mutation testing,
property-based testing, perf/benchmark tests, fixtures for specific components.

## Test categories

Three orthogonal markers. A test may have multiple (e.g., unit + spec).

### `@pytest.mark.unit`

**What it means:** The test uses synthetic fixtures only — no real data files, no
network, no environment secrets. Runs in isolated tmp dirs. Finishes in under
one second per test.

**Can import:** project modules, pandas, pytest fixtures, synthetic DataFrames.

**Cannot:** read `data/raw/**`, call FRED/Yahoo APIs, require `FRED_API_KEY`,
write outside `tmp_path`, depend on wall-clock time.

**Runs in:** worktrees, CI, local — everywhere.

**Default for new tests.** If a test can be written as unit, it must be.

### `@pytest.mark.integration`

**What it means:** The test reads the real parquet cache at `data/raw/` or
otherwise depends on state the worktree doesn't have.

**Can:** read `data/raw/**/*.parquet`, use cached FRED/Yahoo data.

**Cannot:** call external APIs directly (write an ad-hoc fetch script in
`scripts/` if needed, don't bake network calls into tests).

**Must:** skip gracefully when the cache is absent, via the `require_cache`
fixture (see "Conftest helpers" below). Skipping is **required** — a test that
errors instead of skips on a missing cache is a bug in the test.

**Runs in:** local only. Not in CI (no cache strategy). Not in worktrees by
default — if an agent needs integration verification, it reports back rather
than running.

### `@pytest.mark.spec`

**What it means:** The test directly verifies an invariant or test case listed
in a `docs/specs/*.md` file. Orthogonal to unit/integration — most `spec` tests
are also `unit`, but some are `integration`.

**Required:** the test's docstring must reference the spec and the specific
invariant or test case. Example:

```python
@pytest.mark.unit
@pytest.mark.spec
def test_spliced_gold_monthly_returns_match_proxy(...):
    """docs/specs/backtester.md "Proxy series splicing → Test cases":
    compounded monthly returns from spliced daily gold series equal
    WPUSI019011 monthly returns for any full month in 1975-2000."""
```

**Purpose:** discoverability. `pytest -m spec` lists every test that's
load-bearing for a spec — useful for the review agent in #15 and for humans
auditing whether a spec is covered.

## Invariants

- Every test file has at least one marker applied to every test. An unmarked
  test is a lint failure (enforced via the conftest check below).
- A test marked `integration` without also using `require_cache` is a test bug.
- A test marked `spec` without a docstring referencing the spec is a test bug.
- `unit` and `integration` are mutually exclusive — a test cannot be both.

## Test invocation

| Command | What runs | Where to use it |
|---|---|---|
| `pytest` | Everything (unit + integration + spec) | Local dev, full confidence run |
| `pytest -m "not integration"` | Unit + spec-without-integration | CI, worktrees, quick feedback |
| `pytest -m integration` | Only tests that need the parquet cache | Local, after fetching data |
| `pytest -m spec` | Only spec-anchored tests | Audit: "what enforces this spec?" |

CI runs `pytest -m "not integration"`. Everything except integration is a
required check.

## Conftest helpers

### `require_cache` fixture

In `tests/conftest.py`:

```python
import pytest
from pathlib import Path

DATA_RAW = Path(__file__).parent.parent / "data" / "raw"

@pytest.fixture
def require_cache():
    """Skip the test if the FRED/Yahoo parquet cache is not populated.
    Integration tests depend on real cached data; worktrees and CI typically
    don't have it."""
    if not DATA_RAW.exists() or not any(DATA_RAW.rglob("*.parquet")):
        pytest.skip("parquet cache at data/raw/ not populated — run scripts/fetch_data.py")
```

Integration tests MUST depend on this fixture (`def test_foo(require_cache):`)
so they skip cleanly instead of failing with FileNotFoundError.

### Unmarked-test lint (in `conftest.py`)

```python
_ALLOWED_MARKERS = {"unit", "integration", "spec"}

def pytest_collection_modifyitems(config, items):
    unmarked = [
        item for item in items
        if not any(m.name in _ALLOWED_MARKERS for m in item.iter_markers())
    ]
    if unmarked:
        names = "\n  ".join(item.nodeid for item in unmarked)
        raise pytest.UsageError(
            f"Tests missing a required marker (unit|integration|spec):\n  {names}"
        )
```

This runs at collection time. Adding a test without a marker fails the suite
before any test runs.

## pyproject.toml configuration

```toml
[tool.pytest.ini_options]
markers = [
  "unit: synthetic fixtures only; runs in worktrees and CI",
  "integration: uses real data/raw/ parquet cache; local only, skips if absent",
  "spec: directly verifies an invariant listed in docs/specs/*.md",
]
testpaths = ["tests"]
# Fail the run if any test uses an unregistered marker.
# Combined with the collection check above, forces marker discipline.
addopts = ["--strict-markers"]
```

## Worktree testing boundary

Subagent worktrees have:
- A fresh checkout of the repo
- `.env` auto-copied via `.worktreeinclude` (so `scripts/fetch_data.py` can run
  in principle — but it would fetch into the worktree's own `data/`, not the
  main cache)
- NO populated `data/raw/` parquet cache

Consequences for agents:
- `pytest -m "not integration"` runs fine — same as CI
- `pytest -m integration` will skip every integration test (cache absent). That
  is correct behavior, not a failure.
- If an agent needs integration-level verification (e.g., a compounding identity
  check against real FRED data), it reports back rather than re-fetching. Per
  CLAUDE.md "Reporting is success, workarounds are failure".

The coordinator runs integration tests in the main repo after the agent returns.

## CI job design

Platform: GitHub Actions.

Workflow file: `.github/workflows/tests.yml`.

Required steps:
1. Checkout
2. Setup Python 3.11+
3. Install dev dependencies (`pip install -e ".[dev]"`)
4. Run `pytest -m "not integration"`

CI must not require `FRED_API_KEY`, network access to FRED/Yahoo, or the parquet
cache. Any of those is a test-categorization bug (the test should be
`integration`, not `unit`).

### Not in scope for the initial CI
- Coverage reporting
- Ruff or formatter checks (separate workflow when we add them)
- Matrix across Python versions (3.11 is the floor; cross-version later if
  we see breakage)
- Caching pip dependencies (add when install time exceeds 30 seconds)

## Test cases (for this spec)

Yes, this spec's own rules are testable. The conftest check above is effectively
the test for "every test has a marker". Additional invariants:

- `pytest -m "not integration"` from a fresh worktree (no `data/raw/`) exits 0
  with the existing test suite — no skips that look like failures.
- Adding a new test file without any marker causes `pytest` to fail at
  collection (not error at runtime).
- Adding a test with `@pytest.mark.unknown` fails at collection because of
  `--strict-markers`.

## Migration checklist (for the initial implementation)

1. Add `[tool.pytest.ini_options]` to `pyproject.toml` with markers and
   `--strict-markers`.
2. Add `require_cache` fixture and collection hook to `tests/conftest.py`.
3. Mark every test in `tests/test_proxy_splicing.py` as `@pytest.mark.unit`.
   Mark the four that directly verify a spec's test case as `@pytest.mark.spec`
   as well, and ensure their docstrings reference `docs/specs/backtester.md`.
4. Create `.github/workflows/tests.yml` running `pytest -m "not integration"`.
5. Update `CLAUDE.md` "Setup & commands" with the four `pytest` invocations
   above, and update "Worktree testing boundary" to reference this spec.

## What this spec does NOT cover

- Coverage thresholds (add later if overfitting to covered code becomes a
  problem)
- Mutation testing (nice-to-have, not essential)
- Property-based testing with hypothesis (fine to adopt ad-hoc in `unit`
  tests when useful; no blanket policy)
- Perf/benchmark tests (separate concern; no marker yet)
- Snapshot testing

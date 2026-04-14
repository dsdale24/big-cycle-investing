"""Pytest configuration: make the ``src`` package importable for tests."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DATA_RAW = Path(__file__).parent.parent / "data" / "raw"


@pytest.fixture
def require_cache():
    """Skip the test if the FRED/Yahoo parquet cache is not populated.
    Integration tests depend on real cached data; worktrees and CI typically
    don't have it."""
    if not DATA_RAW.exists() or not any(DATA_RAW.rglob("*.parquet")):
        pytest.skip("parquet cache at data/raw/ not populated — run scripts/fetch_data.py")


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

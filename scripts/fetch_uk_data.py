#!/usr/bin/env python3
"""Fetch all configured UK series from the cached BoE workbook.

Mirrors scripts/fetch_data.py. Reads data/raw/uk/_source/millennium_of_macro_data.xlsx
(version-pinned by the coordinator — do NOT download from this script), parses
the series listed in configs/series_uk.yaml, writes per-series parquet files to
data/raw/uk/, and records a manifest at data/manifest_uk.json.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_fetcher_uk import fetch_all  # noqa: E402


def main() -> None:
    print("Fetching UK BoE millennium-dataset series from cached workbook...")
    print("=" * 60)
    results = fetch_all()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    ok = sum(1 for v in results.values() if "error" not in v and v.get("status") != "unavailable")
    skipped = sum(1 for v in results.values() if v.get("status") == "unavailable")
    failed = sum(1 for v in results.values() if "error" in v)
    print(f"\nBoE: {ok} succeeded, {skipped} skipped (unavailable), {failed} failed")
    for series_id, info in results.items():
        if info.get("status") == "unavailable":
            print(f"  SKIP    {series_id}: unavailable ({info.get('note', '')})")
        elif "error" in info:
            print(f"  FAILED  {series_id}: {info['error']}")
        else:
            print(
                f"  OK      {series_id}: {info['start']} → {info['end']} ({info['rows']} rows)"
            )

    manifest_path = Path(__file__).parent.parent / "data" / "manifest_uk.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nManifest saved to {manifest_path}")


if __name__ == "__main__":
    main()

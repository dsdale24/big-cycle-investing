#!/usr/bin/env python3
"""Fetch all configured UK series from the cached BoE workbook.

Governed by specs/data_pipeline/uk.md.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_fetcher_uk import MANIFEST_PATH, fetch_all


def main() -> None:
    print("Fetching UK series from cached BoE workbook...")
    print("=" * 60)
    manifest = fetch_all()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Workbook version: {manifest['workbook_version']}")

    series = manifest["series"]
    ok = sum(1 for v in series.values() if v.get("status") == "available" and "error" not in v)
    unavailable = sum(1 for v in series.values() if v.get("status") == "unavailable")
    failed = sum(1 for v in series.values() if "error" in v)
    print(f"\n{ok} succeeded, {failed} failed, {unavailable} declared unavailable")

    for name, info in series.items():
        if info.get("status") == "unavailable":
            issue = info.get("unavailable_followup_issue")
            print(f"  UNAVAIL {name} (follow-up issue #{issue})")
        elif "error" in info:
            print(f"  FAILED  {name}: {info['error']}")
        else:
            print(f"  OK      {name}: {info['start']} → {info['end']} ({info['rows']} rows)")

    print(f"\nManifest saved to {MANIFEST_PATH}")


if __name__ == "__main__":
    main()

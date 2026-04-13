#!/usr/bin/env python3
"""Fetch all configured data series and cache locally."""

import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_fetcher import fetch_all


def main():
    print("Fetching all configured data series...")
    print("=" * 60)
    results = fetch_all()

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    for source in ["fred", "yahoo"]:
        items = results.get(source, {})
        ok = sum(1 for v in items.values() if "error" not in v)
        failed = sum(1 for v in items.values() if "error" in v)
        print(f"\n{source.upper()}: {ok} succeeded, {failed} failed")
        for series_id, info in items.items():
            if "error" in info:
                print(f"  FAILED  {series_id}: {info['error']}")
            else:
                print(f"  OK      {series_id}: {info['start']} → {info['end']} ({info['rows']} rows)")

    # Save manifest
    manifest_path = Path(__file__).parent.parent / "data" / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nManifest saved to {manifest_path}")


if __name__ == "__main__":
    main()

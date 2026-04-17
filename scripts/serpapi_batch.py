"""
Run all SerpAPI searches (local + admin + remote) and dump results to JSON.
Designed for the daily pipeline or initial baseline scan.
"""
import sys
import json
import os
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from serpapi_scan import search_jobs, _ascii

BASE = Path(__file__).parent.parent
OUT_DIR = BASE / "tracking" / "serpapi-cache"
OUT_DIR.mkdir(parents=True, exist_ok=True)

LOCATION = "Rancho Santa Margarita, California"

# Local scope queries
LOCAL_QUERIES = [
    "interior design consultant",
    "interior designer assistant",
    "design coordinator residential",
    "home staging",
    "in-home design consultant",
    "showroom manager design",
    "design consultant remodeling",
    "project coordinator design firm",
    "client services coordinator design",
]

# Admin scope (tighter, pure admin)
ADMIN_QUERIES = [
    "administrative assistant",
    "executive assistant",
    "administrative coordinator",
]

# Remote scope queries
REMOTE_QUERIES = [
    "interior designer",
    "interior design consultant",
    "virtual interior designer",
    "spatial designer",
]


def run_batch(fromage_days=7, limit_per_scope=None):
    run_date = datetime.now().strftime("%Y-%m-%d")
    all_results = {
        "date": run_date,
        "fromage_days": fromage_days,
        "local": [],
        "admin": [],
        "remote": [],
    }

    print(f"=== SerpAPI Batch Scan ({run_date}, {fromage_days}-day window) ===\n")

    print(f"\n--- LOCAL SCOPE ({LOCATION}) ---")
    queries = LOCAL_QUERIES[:limit_per_scope] if limit_per_scope else LOCAL_QUERIES
    for q in queries:
        print(f"\nQuery: {q}")
        jobs = search_jobs(q, LOCATION, remote=False, fromage_days=fromage_days)
        print(f"  Found: {len(jobs)} within {fromage_days}d")
        for j in jobs:
            j["_scope"] = "local"
        all_results["local"].extend(jobs)

    print(f"\n--- ADMIN SCOPE ({LOCATION}) ---")
    queries = ADMIN_QUERIES[:limit_per_scope] if limit_per_scope else ADMIN_QUERIES
    for q in queries:
        print(f"\nQuery: {q}")
        jobs = search_jobs(q, LOCATION, remote=False, fromage_days=fromage_days)
        print(f"  Found: {len(jobs)} within {fromage_days}d")
        for j in jobs:
            j["_scope"] = "admin"
        all_results["admin"].extend(jobs)

    print(f"\n--- REMOTE SCOPE (US-wide) ---")
    queries = REMOTE_QUERIES[:limit_per_scope] if limit_per_scope else REMOTE_QUERIES
    for q in queries:
        print(f"\nQuery: {q}")
        jobs = search_jobs(q, "United States", remote=True, fromage_days=fromage_days)
        print(f"  Found: {len(jobs)} within {fromage_days}d")
        for j in jobs:
            j["_scope"] = "remote"
        all_results["remote"].extend(jobs)

    # Dedupe within each scope by company + title
    for scope in ("local", "admin", "remote"):
        seen = set()
        deduped = []
        for j in all_results[scope]:
            key = (j.get("company", "").lower(), j.get("title", "").lower())
            if key not in seen:
                seen.add(key)
                deduped.append(j)
        all_results[scope] = deduped

    # Save
    out_file = OUT_DIR / f"batch-{run_date}-{fromage_days}d.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)

    print(f"\n\n=== SUMMARY ===")
    print(f"Local: {len(all_results['local'])} unique jobs")
    print(f"Admin: {len(all_results['admin'])} unique jobs")
    print(f"Remote: {len(all_results['remote'])} unique jobs")
    print(f"\nResults saved to: {out_file}")

    return all_results


if __name__ == "__main__":
    days = 7
    limit = None
    for i, arg in enumerate(sys.argv):
        if arg == "--days" and i + 1 < len(sys.argv):
            days = int(sys.argv[i + 1])
        elif arg == "--limit" and i + 1 < len(sys.argv):
            limit = int(sys.argv[i + 1])

    run_batch(fromage_days=days, limit_per_scope=limit)

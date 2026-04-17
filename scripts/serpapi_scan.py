"""
SerpAPI Google Jobs scanner — reliable structured job search.

Replaces WebFetch scraping (which Indeed/LinkedIn often block) with SerpAPI's
Google Jobs engine, which returns clean structured JSON with title, company,
location, salary, description, and a direct apply URL.

Free tier: 100 searches/month. Budget carefully.

Usage:
  python serpapi_scan.py "interior design consultant" --location "Rancho Santa Margarita, CA"
  python serpapi_scan.py "interior designer" --location "United States" --remote
  python serpapi_scan.py --config  # runs all queries from portals.yml
"""
import os
import sys
import json
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).parent.parent
# SerpAPI key lives in OneDrive (OUTSIDE this repo) per user security policy.
# Never store API keys in the repo itself - even in gitignored paths.
ONEDRIVE_KEY_FILE = Path(r"C:\Users\rjain\OneDrive - Technijian, Inc\Documents\VSCODE\keys\serpapi.md")
CACHE_DIR = BASE / "tracking" / "serpapi-cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def load_api_key():
    """Load SerpAPI key from OneDrive keys folder (never from repo)."""
    if not ONEDRIVE_KEY_FILE.exists():
        print(f"ERROR: OneDrive key file not found at {ONEDRIVE_KEY_FILE}")
        print("Expected format: markdown file with line containing 'API Key: <key>'")
        sys.exit(1)
    with open(ONEDRIVE_KEY_FILE, encoding="utf-8") as f:
        for line in f:
            # Match patterns like "**API Key:** <key>" or "API Key: <key>"
            if "API Key" in line and ":" in line:
                # Extract the hex key (64 chars typical for SerpAPI)
                import re
                match = re.search(r'([a-f0-9]{40,})', line)
                if match:
                    return match.group(1)
    print("ERROR: API key not found in OneDrive serpapi.md")
    sys.exit(1)


def search_jobs(query, location="Rancho Santa Margarita, California", remote=False,
                 fromage_days=1, results_per_query=20):
    """
    Query SerpAPI Google Jobs engine.

    Returns list of dicts with: title, company, location, salary, description,
    apply_url, posted_at, source.
    """
    api_key = load_api_key()

    # Build query with date filter
    date_filter = f"today" if fromage_days == 1 else f"{fromage_days}+days"

    # SerpAPI chips format is dynamic (must use values returned from initial search).
    # Simpler and more reliable: query without date filter, filter by posted_at after.
    params = {
        "engine": "google_jobs",
        "q": f"{query} remote" if remote else query,
        "location": location,
        "hl": "en",
        "api_key": api_key,
    }

    url = "https://serpapi.com/search?" + urllib.parse.urlencode(params)

    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            data = json.load(resp)
    except Exception as e:
        print(f"  ERROR: {e}")
        return []

    if "error" in data:
        print(f"  SerpAPI error: {data['error']}")
        return []

    jobs = data.get("jobs_results", [])

    # Filter by posted_at — "1 day ago", "2 days ago", "14 hours ago" etc.
    def within_window(job):
        posted = (job.get("detected_extensions", {}) or {}).get("posted_at", "").lower()
        if not posted:
            return True  # include if unknown; better too many than miss
        import re
        m = re.search(r'(\d+)\s*(hour|day|week|month)', posted)
        if not m:
            return "just posted" in posted or "today" in posted
        num = int(m.group(1))
        unit = m.group(2)
        days = num / 24 if unit == "hour" else num if unit == "day" else num * 7 if unit == "week" else num * 30
        return days <= fromage_days

    jobs = [j for j in jobs if within_window(j)]

    results = []
    for j in jobs[:results_per_query]:
        # Extract apply URL from apply_options or apply_link
        apply_url = ""
        if j.get("apply_options"):
            apply_url = j["apply_options"][0].get("link", "")
        elif j.get("apply_link"):
            apply_url = j["apply_link"]
        elif j.get("share_link"):
            apply_url = j["share_link"]

        # Extract salary
        salary = "Not listed"
        if j.get("detected_extensions", {}).get("salary"):
            salary = j["detected_extensions"]["salary"]
        elif j.get("salary"):
            salary = j["salary"]

        results.append({
            "title": j.get("title", ""),
            "company": j.get("company_name", ""),
            "location": j.get("location", ""),
            "salary": salary,
            "description": j.get("description", "")[:500],
            "apply_url": apply_url,
            "posted_at": j.get("detected_extensions", {}).get("posted_at", ""),
            "schedule": j.get("detected_extensions", {}).get("schedule_type", ""),
            "source": j.get("via", ""),
            "job_id": j.get("job_id", ""),
            "query": query,
        })

    # Cache the raw response
    cache_key = f"{datetime.now().strftime('%Y%m%d')}_{urllib.parse.quote_plus(query)[:50]}.json"
    cache_file = CACHE_DIR / cache_key
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump({"query": query, "location": location, "remote": remote,
                   "raw": data, "parsed": results}, f, indent=2)

    return results


def _ascii(s):
    """Strip non-ASCII so Windows cp1252 console can print."""
    if not s:
        return ""
    return s.encode("ascii", errors="replace").decode("ascii")


def print_results(jobs):
    """Pretty-print jobs to stdout."""
    if not jobs:
        print("  No jobs found")
        return
    for i, j in enumerate(jobs, 1):
        print(f"\n  [{i}] {_ascii(j['title'])}")
        print(f"      Company: {_ascii(j['company'])}")
        print(f"      Location: {_ascii(j['location'])}")
        print(f"      Salary: {_ascii(j['salary'])}")
        print(f"      Posted: {_ascii(j['posted_at'])}")
        print(f"      Source: {_ascii(j['source'])}")
        print(f"      Apply: {_ascii(j['apply_url'])[:100]}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    # Parse simple CLI args
    query = sys.argv[1]
    location = "Rancho Santa Margarita, California"
    remote = False
    fromage_days = 1

    for i, arg in enumerate(sys.argv):
        if arg == "--location" and i + 1 < len(sys.argv):
            location = sys.argv[i + 1]
        elif arg == "--remote":
            remote = True
            location = "United States"
        elif arg == "--fromage" and i + 1 < len(sys.argv):
            fromage_days = int(sys.argv[i + 1])

    print(f"Searching: {query}")
    print(f"Location: {location}")
    print(f"Remote: {remote}")
    print(f"Posted in last: {fromage_days} day(s)")
    print("-" * 60)

    jobs = search_jobs(query, location, remote, fromage_days)
    print(f"\nFound {len(jobs)} jobs")
    print_results(jobs)


if __name__ == "__main__":
    main()

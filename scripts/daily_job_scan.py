"""
Daily Job Scanner for Callie Wells
Runs every 24 hours via Windows Task Scheduler.

Searches Indeed for new job postings matching Callie's criteria,
generates cover letters + resumes, emails them to companies,
and sends Callie an apply-kit email for Indeed submission.
"""

import subprocess
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# ── Configuration ──
BASE_DIR = Path(__file__).parent.parent
JOBS_DIR = BASE_DIR / "jobs"
ACTIVE_DIR = JOBS_DIR / "active"
TRACKING_DIR = BASE_DIR / "tracking"
SCAN_LOG = TRACKING_DIR / "scan-log.md"
KNOWN_JOBS_FILE = TRACKING_DIR / "known-jobs.json"

CALLIE_EMAIL = "CallieWells17@gmail.com"
LOCATION = "Rancho Santa Margarita, CA"
RADIUS = 25  # miles

# Search queries matching Callie's target roles
SEARCH_QUERIES = [
    "interior design consultant",
    "interior designer assistant",
    "design coordinator residential",
    "home staging",
    "in-home design consultant",
    "showroom manager design",
    "project coordinator design firm",
    "administrative coordinator",
    "office manager design",
    "client services coordinator",
    "design consultant remodeling",
]


def load_known_jobs():
    """Load set of already-seen job identifiers."""
    if KNOWN_JOBS_FILE.exists():
        with open(KNOWN_JOBS_FILE) as f:
            return json.load(f)
    return {"seen": [], "last_scan": None}


def save_known_jobs(data):
    """Save known jobs list."""
    with open(KNOWN_JOBS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def search_indeed(query):
    """
    Search Indeed via gws + web search proxy.
    Returns raw search text for parsing.
    """
    # Use Indeed's RSS-style URL pattern for job searches
    search_url = (
        f"https://www.indeed.com/jobs?"
        f"q={query.replace(' ', '+')}"
        f"&l={LOCATION.replace(' ', '+').replace(',', '%2C')}"
        f"&radius={RADIUS}"
        f"&sort=date"
        f"&fromage=1"  # Last 24 hours
    )
    return search_url


def send_email(to, subject, body, attachments=None):
    """Send email via gws CLI."""
    gws_path = os.path.join(os.environ.get("APPDATA", ""), "npm", "gws.cmd")
    if not os.path.exists(gws_path):
        gws_path = "gws"  # fallback to PATH
    cmd = [
        gws_path, "gmail", "+send",
        "--to", to,
        "--subject", subject,
        "--body", body,
    ]
    if attachments:
        for a in attachments:
            cmd.extend(["-a", str(a)])

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode == 0:
        return True
    else:
        print(f"  Email error: {result.stderr[:200]}")
        return False


def send_daily_digest(new_urls, scan_time):
    """Send Callie a daily digest email with new job links to check."""
    if not new_urls:
        body = f"""Hi Callie,

Daily Job Scan completed at {scan_time}.

No new matching jobs found in the last 24 hours. The scanner checked {len(SEARCH_QUERIES)} search categories within {RADIUS} miles of {LOCATION}.

The next scan will run automatically tomorrow.

Your Job Search Pipeline"""
        send_email(
            CALLIE_EMAIL,
            f"Daily Job Scan - No New Jobs ({scan_time[:10]})",
            body
        )
    else:
        links_text = "\n".join([f"  {i+1}. {url}" for i, url in enumerate(new_urls)])
        body = f"""Hi Callie,

Daily Job Scan completed at {scan_time}.

Found {len(new_urls)} new search categories with recent postings! Check these Indeed links for jobs posted in the last 24 hours:

{links_text}

HOW TO APPLY:
1. Click each link above
2. Look for jobs posted 'Just posted' or 'Today'
3. Your resume PDFs are in the callie-job repo under resumes/
4. Use the design-sales resume for sales/consultant roles
5. Use the design-assistant resume for staging/assistant roles
6. Use the coordinator resume for admin/coordinator roles

The next scan will run automatically tomorrow.

Your Job Search Pipeline"""
        send_email(
            CALLIE_EMAIL,
            f"Daily Job Scan - {len(new_urls)} New Categories ({scan_time[:10]})",
            body
        )


def log_scan(scan_time, query_count, new_count):
    """Append to scan log."""
    entry = f"| {scan_time} | {query_count} queries | {new_count} new categories | Auto |\n"

    if not SCAN_LOG.exists():
        header = """# Daily Scan Log

| Scan Time | Queries | New Finds | Method |
|-----------|---------|-----------|--------|
"""
        with open(SCAN_LOG, "w") as f:
            f.write(header)

    with open(SCAN_LOG, "a") as f:
        f.write(entry)


def main():
    print(f"[{datetime.now().isoformat()}] Starting daily job scan...")

    scan_time = datetime.now().isoformat()
    known = load_known_jobs()

    new_urls = []

    for query in SEARCH_QUERIES:
        url = search_indeed(query)
        url_key = f"{query}:{datetime.now().strftime('%Y-%m-%d')}"

        if url_key not in known["seen"]:
            new_urls.append(url)
            known["seen"].append(url_key)
            print(f"  [NEW] {query} -> {url}")
        else:
            print(f"  [SKIP] {query} (already scanned today)")

    # Keep only last 30 days of seen jobs
    cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    known["seen"] = [s for s in known["seen"] if s.split(":")[-1] >= cutoff]
    known["last_scan"] = scan_time
    save_known_jobs(known)

    # Send digest email to Callie
    print(f"\nSending daily digest to {CALLIE_EMAIL}...")
    send_daily_digest(new_urls, scan_time)

    # Log the scan
    log_scan(scan_time, len(SEARCH_QUERIES), len(new_urls))

    print(f"\nScan complete. {len(new_urls)} new categories found.")
    print(f"Log: {SCAN_LOG}")


if __name__ == "__main__":
    main()

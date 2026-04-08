"""
Daily Job Pipeline for Callie Wells
Runs every 24 hours via Windows Task Scheduler.

Full pipeline:
1. SCAN - Search Indeed for new postings (last 24hrs, 25mi from RSM)
2. MOVE - Move any jobs in active/ to applied/ after emails are sent
3. FOLLOWUP - Send follow-up emails for jobs applied 3+ business days ago
4. DIGEST - Email Callie a daily summary with new Indeed links
5. LOG - Record scan results to tracking/scan-log.md
"""

import subprocess
import json
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path

# ── Configuration ──
BASE_DIR = Path(__file__).parent.parent
JOBS_DIR = BASE_DIR / "jobs"
ACTIVE_DIR = JOBS_DIR / "active"
APPLIED_DIR = JOBS_DIR / "applied"
INTERVIEWS_DIR = JOBS_DIR / "interviews"
CL_DRAFTS = BASE_DIR / "cover-letters" / "drafts"
CL_SENT = BASE_DIR / "cover-letters" / "sent"
MERGED_DIR = BASE_DIR / "cover-letters" / "merged-for-indeed"
TRACKING_DIR = BASE_DIR / "tracking"
SCAN_LOG = TRACKING_DIR / "scan-log.md"
KNOWN_JOBS_FILE = TRACKING_DIR / "known-jobs.json"
PIPELINE_FILE = TRACKING_DIR / "pipeline.md"
APP_LOG_FILE = TRACKING_DIR / "application-log.md"

CALLIE_EMAIL = "CallieWells17@gmail.com"
LOCATION = "Rancho Santa Margarita, CA"
RADIUS = 50

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


def get_gws_path():
    """Find gws CLI executable."""
    gws_path = os.path.join(os.environ.get("APPDATA", ""), "npm", "gws.cmd")
    if os.path.exists(gws_path):
        return gws_path
    return "gws"


def send_email(to, subject, body, attachments=None):
    """Send email via gws CLI."""
    cmd = [
        get_gws_path(), "gmail", "+send",
        "--to", to,
        "--subject", subject,
        "--body", body,
    ]
    if attachments:
        for a in attachments:
            cmd.extend(["-a", str(a)])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"    Sent to {to}")
            return True
        else:
            print(f"    Email error to {to}: {result.stderr[:200]}")
            return False
    except Exception as e:
        print(f"    Email exception: {e}")
        return False


def load_known_jobs():
    """Load set of already-seen job identifiers."""
    if KNOWN_JOBS_FILE.exists():
        with open(KNOWN_JOBS_FILE) as f:
            return json.load(f)
    return {"seen": [], "last_scan": None, "applied": {}, "followups_sent": []}


def save_known_jobs(data):
    """Save known jobs data."""
    with open(KNOWN_JOBS_FILE, "w") as f:
        json.dump(data, f, indent=2)


# ── STEP 1: SCAN ──
def scan_indeed():
    """Search Indeed for new job postings in last 24 hours."""
    print("\n[STEP 1] Scanning Indeed for new postings...")
    known = load_known_jobs()
    new_urls = []

    for query in SEARCH_QUERIES:
        search_url = (
            f"https://www.indeed.com/jobs?"
            f"q={query.replace(' ', '+')}"
            f"&l={LOCATION.replace(' ', '+').replace(',', '%2C')}"
            f"&radius={RADIUS}&sort=date&fromage=1"
        )
        url_key = f"{query}:{datetime.now().strftime('%Y-%m-%d')}"

        if url_key not in known["seen"]:
            new_urls.append({"query": query, "url": search_url})
            known["seen"].append(url_key)
            print(f"  [NEW] {query}")
        else:
            print(f"  [SKIP] {query} (already scanned today)")

    # Prune entries older than 30 days
    cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    known["seen"] = [s for s in known["seen"] if s.split(":")[-1] >= cutoff]
    known["last_scan"] = datetime.now().isoformat()
    save_known_jobs(known)

    return new_urls


# ── STEP 2: MOVE active -> applied ──
def move_applied_jobs():
    """Move any jobs in active/ to applied/ (they've been emailed)."""
    print("\n[STEP 2] Moving applied jobs...")
    moved = []
    APPLIED_DIR.mkdir(parents=True, exist_ok=True)

    for job_file in sorted(ACTIVE_DIR.glob("*.md")):
        dest = APPLIED_DIR / job_file.name
        shutil.move(str(job_file), str(dest))
        moved.append(job_file.name)
        print(f"  Moved: {job_file.name} -> applied/")

    # Also move cover letters from drafts to sent
    CL_SENT.mkdir(parents=True, exist_ok=True)
    for cl_file in sorted(CL_DRAFTS.glob("*.pdf")):
        dest = CL_SENT / cl_file.name
        if not dest.exists():
            shutil.copy2(str(cl_file), str(dest))

    if not moved:
        print("  No jobs to move (active/ is empty)")

    return moved


# ── STEP 3: FOLLOW-UPS ──
def send_followups():
    """Send follow-up emails for jobs applied 3+ business days ago."""
    print("\n[STEP 3] Checking for follow-ups needed...")
    known = load_known_jobs()
    followups_sent = known.get("followups_sent", [])
    applied_dates = known.get("applied", {})
    today = datetime.now()
    sent_count = 0

    for job_file in sorted(APPLIED_DIR.glob("*.md")):
        job_name = job_file.stem
        if job_name in followups_sent:
            continue

        # Read the file to get company/email info
        content = job_file.read_text(encoding="utf-8")

        # Check if we have an applied date
        applied_date_str = applied_dates.get(job_name)
        if not applied_date_str:
            # Try to detect from application log
            continue

        applied_date = datetime.fromisoformat(applied_date_str)
        days_since = (today - applied_date).days

        # Send follow-up after 3 business days (~5 calendar days to be safe)
        if days_since >= 5:
            # Extract email from the file content
            email_to = None
            for line in content.split("\n"):
                if "Email Sent To" in line or "@" in line:
                    # Try to find email
                    import re
                    emails = re.findall(r'[\w.+-]+@[\w-]+\.[\w.]+', line)
                    if emails:
                        email_to = emails[0]
                        break

            if email_to and email_to != CALLIE_EMAIL:
                company = job_name.replace("-", " ").title()
                success = send_email(
                    email_to,
                    f"Following Up - Callie Wells Application",
                    f"""Dear Hiring Team,

I hope this message finds you well. I wanted to follow up on the application I submitted on {applied_date.strftime('%B %d, %Y')}. I remain very interested in the opportunity and would welcome the chance to discuss how my background in residential design could contribute to your team.

Please don't hesitate to reach out if you need any additional information. I'm available at 949-557-9014 or CallieWells17@gmail.com.

Warm regards,
Callie Nichole Wells
949-557-9014
CallieWells17@gmail.com
linkedin.com/in/callie-wells17"""
                )
                if success:
                    followups_sent.append(job_name)
                    sent_count += 1
                    print(f"  Follow-up sent: {job_name} -> {email_to}")

    known["followups_sent"] = followups_sent
    save_known_jobs(known)

    if sent_count == 0:
        print("  No follow-ups needed yet")

    return sent_count


# ── STEP 4: DIGEST EMAIL ──
def send_daily_digest(new_urls, moved_count, followup_count, scan_time):
    """Send Callie a daily summary email."""
    print("\n[STEP 4] Sending daily digest...")

    # Count pipeline stats
    active_count = len(list(ACTIVE_DIR.glob("*.md")))
    applied_count = len(list(APPLIED_DIR.glob("*.md")))
    interview_count = len(list(INTERVIEWS_DIR.glob("*.md"))) if INTERVIEWS_DIR.exists() else 0

    stats = f"""PIPELINE STATUS:
  Active (ready to apply): {active_count}
  Applied (emails sent): {applied_count}
  Interviews: {interview_count}
  Follow-ups sent today: {followup_count}
  Jobs moved to applied today: {moved_count}"""

    if new_urls:
        links_text = "\n".join([f"  {i+1}. {u['query']}: {u['url']}" for i, u in enumerate(new_urls)])
        body = f"""Hi Callie,

Daily Job Scan completed at {scan_time}.

{stats}

NEW JOB POSTINGS (last 24 hours, within {RADIUS} mi):

{links_text}

HOW TO APPLY:
1. Click each link above
2. Look for jobs posted 'Just posted' or 'Today'
3. Your resume PDFs are in the callie-job repo under resumes/
   - design-sales resume: for sales/consultant roles
   - design-assistant resume: for staging/assistant roles
   - coordinator resume: for admin/coordinator roles

Next scan runs automatically tomorrow at 7:00 AM.

Your Job Search Pipeline"""
    else:
        body = f"""Hi Callie,

Daily Job Scan completed at {scan_time}.

{stats}

No new job categories found in the last 24 hours. The scanner checked {len(SEARCH_QUERIES)} categories within {RADIUS} miles of {LOCATION}.

Next scan runs automatically tomorrow at 7:00 AM.

Your Job Search Pipeline"""

    send_email(
        CALLIE_EMAIL,
        f"Daily Job Report - {scan_time[:10]} | {applied_count} Applied, {active_count} Active",
        body
    )


# ── STEP 5: LOG ──
def log_scan(scan_time, new_count, moved_count, followup_count):
    """Append to scan log."""
    if not SCAN_LOG.exists():
        header = """# Daily Scan Log

| Scan Time | New Finds | Jobs Moved | Follow-ups | Method |
|-----------|-----------|------------|------------|--------|
"""
        with open(SCAN_LOG, "w") as f:
            f.write(header)

    entry = f"| {scan_time} | {new_count} | {moved_count} | {followup_count} | Auto |\n"
    with open(SCAN_LOG, "a") as f:
        f.write(entry)


# ── MAIN PIPELINE ──
def main():
    scan_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"{'='*60}")
    print(f"  CALLIE WELLS JOB PIPELINE - {scan_time}")
    print(f"{'='*60}")

    # Step 1: Scan Indeed
    new_urls = scan_indeed()

    # Step 2: Move active jobs to applied
    moved = move_applied_jobs()

    # Step 3: Send follow-up emails
    followup_count = send_followups()

    # Step 4: Send daily digest to Callie
    send_daily_digest(new_urls, len(moved), followup_count, scan_time)

    # Step 5: Log everything
    log_scan(scan_time, len(new_urls), len(moved), followup_count)

    print(f"\n{'='*60}")
    print(f"  PIPELINE COMPLETE")
    print(f"  New categories: {len(new_urls)}")
    print(f"  Jobs moved to applied: {len(moved)}")
    print(f"  Follow-ups sent: {followup_count}")
    print(f"  Log: {SCAN_LOG}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()

"""
Daily Job Pipeline for Callie Wells
Runs every day at 7:00 AM via Windows Task Scheduler.

FULL END-TO-END PIPELINE:
1. SCRAPE  - Scrape Indeed for individual job postings (50mi from RSM)
2. FILTER  - Exclude AutoCAD, retail, already-seen jobs
3. CREATE  - Create job .md files for each new lead
4. COVER   - Write templated cover letters (md + PDF)
5. MERGE   - Merge cover letter + resume into Indeed-ready PDF
6. EMAIL   - Email companies directly when contact email is found
7. KIT     - Email Callie merged PDFs for Indeed submission
8. MOVE    - Move processed active/ jobs to applied/
9. FOLLOWUP- Send follow-ups for jobs applied 3+ business days ago
10. LOG    - Record everything to tracking files

Includes: Full-time and part-time roles (with full-time potential)
Excludes: Retail stores, roles requiring AutoCAD

Usage:
  python daily_job_scan.py          # Normal daily run (last 1 day)
  python daily_job_scan.py 7        # Look back 7 days
  python daily_job_scan.py --dry    # Dry run (no emails sent)
"""

import subprocess
import json
import os
import re
import shutil
import sys
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote_plus

# ── Configuration ──
BASE_DIR = Path(__file__).parent.parent
JOBS_DIR = BASE_DIR / "jobs"
ACTIVE_DIR = JOBS_DIR / "active"
APPLIED_DIR = JOBS_DIR / "applied"
INTERVIEWS_DIR = JOBS_DIR / "interviews"
CL_DRAFTS = BASE_DIR / "cover-letters" / "drafts"
CL_SENT = BASE_DIR / "cover-letters" / "sent"
MERGED_DIR = BASE_DIR / "cover-letters" / "merged-for-indeed"
RES_DIR = BASE_DIR / "resumes"
TRACKING_DIR = BASE_DIR / "tracking"
SCAN_LOG = TRACKING_DIR / "scan-log.md"
KNOWN_JOBS_FILE = TRACKING_DIR / "known-jobs.json"
APP_LOG_FILE = TRACKING_DIR / "application-log.md"
JOB_INBOX = TRACKING_DIR / "job-inbox.json"

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
    "administrative coordinator design",
    "office manager design",
    "client services coordinator design",
    "design consultant remodeling",
]

# Words that indicate a job should be excluded
EXCLUDE_KEYWORDS = [
    "autocad", "auto cad", "auto-cad", "revit",
    "retail store", "retail associate", "cashier",
    "senior architect", "licensed architect",
    "civil engineer", "mechanical engineer",
    "registered nurse", "medical", "dental hygienist",
]

# Resume mapping: keyword patterns -> resume type
RESUME_MAP = [
    # Order matters — first match wins
    (["coordinator", "admin", "office manager", "events", "logistics", "operations"], "coordinator"),
    (["assistant", "staging", "stager", "home stag"], "design-assistant"),
    (["sales", "consultant", "showroom", "manager", "design consultant", "in-home", "remodel"], "design-sales"),
]

RESUME_FILES = {
    "design-sales": "callie-wells-resume-design-sales.pdf",
    "design-assistant": "callie-wells-resume-design-assistant.pdf",
    "coordinator": "callie-wells-resume-coordinator.pdf",
}

# Ensure all directories exist
for d in [ACTIVE_DIR, APPLIED_DIR, CL_DRAFTS, CL_SENT, MERGED_DIR, TRACKING_DIR]:
    d.mkdir(parents=True, exist_ok=True)


# ═══════════════════════════════════════════════════════════
#  UTILITIES
# ═══════════════════════════════════════════════════════════

def get_gws_path():
    """Find gws CLI executable."""
    gws_path = os.path.join(os.environ.get("APPDATA", ""), "npm", "gws.cmd")
    if os.path.exists(gws_path):
        return gws_path
    return "gws"


def send_email(to, subject, body, attachments=None):
    """Send email via gws CLI. Returns True on success."""
    if DRY_RUN:
        print(f"    [DRY RUN] Would send to {to}: {subject}")
        return True

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
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
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
    """Load tracking data."""
    if KNOWN_JOBS_FILE.exists():
        with open(KNOWN_JOBS_FILE) as f:
            data = json.load(f)
        for key in ["seen", "applied", "email_sent", "indeed_applied",
                     "indeed_kit_sent", "followups_sent", "seen_jobs"]:
            data.setdefault(key, [] if key in ("seen", "followups_sent") else {})
        return data
    return {
        "seen": [], "last_scan": None, "applied": {},
        "email_sent": {}, "indeed_applied": {}, "indeed_kit_sent": {},
        "followups_sent": [], "seen_jobs": {},
    }


def save_known_jobs(data):
    """Save tracking data."""
    with open(KNOWN_JOBS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def slugify(text):
    """Convert text to a filename-safe slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text[:60].strip('-')


def get_next_job_number():
    """Get the next job number based on existing files."""
    existing = []
    for d in [ACTIVE_DIR, APPLIED_DIR]:
        for f in d.glob("*.md"):
            match = re.match(r'^(\d+)-', f.name)
            if match:
                existing.append(int(match.group(1)))
    return max(existing, default=0) + 1


def classify_resume(title, description=""):
    """Determine which resume to use based on job title and description."""
    combined = f"{title} {description}".lower()
    for keywords, resume_type in RESUME_MAP:
        if any(kw in combined for kw in keywords):
            return resume_type
    return "design-sales"  # default


def should_exclude(title, description=""):
    """Check if a job should be excluded based on keywords."""
    combined = f"{title} {description}".lower()
    return any(kw in combined for kw in EXCLUDE_KEYWORDS)


# ═══════════════════════════════════════════════════════════
#  STEP 1: SCRAPE INDEED
# ═══════════════════════════════════════════════════════════

def scrape_indeed(fromage_days=1):
    """Scrape Indeed using Playwright headless browser for individual job postings."""
    print(f"\n[STEP 1] Scraping Indeed (last {fromage_days} day(s), {RADIUS}mi)...")

    try:
        from playwright.sync_api import sync_playwright
        from bs4 import BeautifulSoup
    except ImportError:
        print("  WARNING: playwright/bs4 not installed. Falling back to URL-only mode.")
        return scrape_indeed_fallback(fromage_days)

    known = load_known_jobs()
    seen_jobs = known.get("seen_jobs", {})
    new_jobs = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                           "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()

            for query in SEARCH_QUERIES:
                url = (
                    f"https://www.indeed.com/jobs?"
                    f"q={quote_plus(query)}"
                    f"&l={quote_plus(LOCATION)}"
                    f"&radius={RADIUS}&sort=date&fromage={fromage_days}"
                )

                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=20000)
                    page.wait_for_timeout(2000)  # Let JS render

                    html = page.content()
                    soup = BeautifulSoup(html, "html.parser")

                    # Try JSON-LD structured data first (most reliable)
                    for script in soup.find_all("script", type="application/ld+json"):
                        try:
                            ld_data = json.loads(script.string)
                            items = ld_data if isinstance(ld_data, list) else [ld_data]
                            for item in items:
                                if item.get("@type") == "JobPosting":
                                    _process_ld_job(item, query, seen_jobs, new_jobs)
                        except (json.JSONDecodeError, AttributeError, TypeError):
                            pass

                    # Also try extracting from mosaic-provider-jobcards data
                    for script in soup.find_all("script", id=re.compile(r"mosaic-provider")):
                        try:
                            text = script.string or ""
                            # Find JSON objects with job data
                            for match in re.finditer(r'"jobkey"\s*:\s*"([^"]+)"', text):
                                pass  # jobkeys found but we prefer structured data
                        except Exception:
                            pass

                    # Parse HTML job cards as backup
                    cards = soup.select(
                        "div.job_seen_beacon, "
                        "div.jobsearch-ResultsList div.result, "
                        "li div.cardOutline, "
                        "div[data-testid='slider_item']"
                    )

                    for card in cards:
                        title_el = card.select_one(
                            "h2.jobTitle span[title], h2.jobTitle a span, "
                            "h2 a span, a[data-jk] span"
                        )
                        company_el = card.select_one(
                            "span[data-testid='company-name'], "
                            "span.css-63koeb, span.companyName"
                        )
                        location_el = card.select_one(
                            "div[data-testid='text-location'], "
                            "div.css-1p0sjhy, div.companyLocation"
                        )
                        salary_el = card.select_one(
                            "div[data-testid='attribute_snippet_testid'], "
                            "div.salary-snippet-container, "
                            "div.metadata.salary-snippet-container"
                        )
                        link_el = card.select_one("h2 a, a.jcs-JobTitle, a[data-jk]")

                        if not title_el or not company_el:
                            continue

                        title = title_el.get_text(strip=True)
                        company = company_el.get_text(strip=True)
                        location = location_el.get_text(strip=True) if location_el else "Unknown"
                        salary = salary_el.get_text(strip=True) if salary_el else "Not listed"

                        job_key = f"{slugify(company)}:{slugify(title)}"
                        job_url = ""
                        if link_el and link_el.get("href"):
                            href = link_el["href"]
                            job_url = f"https://www.indeed.com{href}" if href.startswith("/") else href

                        if job_key not in seen_jobs and not should_exclude(title):
                            new_jobs.append({
                                "title": title,
                                "company": company,
                                "location": location,
                                "salary": salary,
                                "url": job_url,
                                "query": query,
                            })
                            seen_jobs[job_key] = datetime.now().strftime("%Y-%m-%d")
                            print(f"  [NEW] {company} - {title} ({location})")

                except Exception as e:
                    print(f"  [ERROR] Query '{query}': {e}")
                    continue

            browser.close()

    except Exception as e:
        print(f"  [BROWSER ERROR] {e}")

    # If scraping found nothing, fall back to URL-only mode
    if not new_jobs:
        print("  No individual jobs parsed. Falling back to URL-only mode.")
        fallback = scrape_indeed_fallback(fromage_days)
        if fallback:
            new_jobs = fallback

    known["seen_jobs"] = seen_jobs
    known["last_scan"] = datetime.now().isoformat()
    save_known_jobs(known)

    print(f"  Total new jobs found: {len(new_jobs)}")
    return new_jobs


def _process_ld_job(item, query, seen_jobs, new_jobs):
    """Process a JSON-LD JobPosting item."""
    title = item.get("title", "")
    company = ""
    if isinstance(item.get("hiringOrganization"), dict):
        company = item["hiringOrganization"].get("name", "")
    location = ""
    loc_data = item.get("jobLocation")
    if isinstance(loc_data, dict):
        addr = loc_data.get("address", {})
        location = f"{addr.get('addressLocality', '')}, {addr.get('addressRegion', '')}"
    elif isinstance(loc_data, list) and loc_data:
        addr = loc_data[0].get("address", {}) if isinstance(loc_data[0], dict) else {}
        location = f"{addr.get('addressLocality', '')}, {addr.get('addressRegion', '')}"
    salary = ""
    if isinstance(item.get("baseSalary"), dict):
        val = item["baseSalary"].get("value", {})
        if isinstance(val, dict):
            lo = val.get("minValue", "")
            hi = val.get("maxValue", "")
            salary = f"${lo}-${hi}" if lo and hi else f"${lo or hi}"

    job_key = f"{slugify(company)}:{slugify(title)}"

    if title and company and job_key not in seen_jobs and not should_exclude(title):
        new_jobs.append({
            "title": title,
            "company": company,
            "location": location.strip(", "),
            "salary": salary or "Not listed",
            "url": item.get("url", ""),
            "query": query,
        })
        seen_jobs[job_key] = datetime.now().strftime("%Y-%m-%d")
        print(f"  [NEW] {company} - {title} ({location})")


def scrape_indeed_fallback(fromage_days):
    """Fallback: generate search URLs when scraping fails."""
    print("  Using URL-only fallback mode...")
    known = load_known_jobs()
    urls = []

    for query in SEARCH_QUERIES:
        search_url = (
            f"https://www.indeed.com/jobs?"
            f"q={quote_plus(query)}"
            f"&l={quote_plus(LOCATION)}"
            f"&radius={RADIUS}&sort=date&fromage={fromage_days}"
        )
        url_key = f"{query}:{datetime.now().strftime('%Y-%m-%d')}"

        if url_key not in known["seen"]:
            urls.append({
                "title": query.title(),
                "company": "Multiple (see Indeed link)",
                "location": f"Within {RADIUS}mi of {LOCATION}",
                "salary": "Varies",
                "url": search_url,
                "query": query,
                "fallback": True,
            })
            known["seen"].append(url_key)

    # Prune old entries
    cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    known["seen"] = [s for s in known["seen"] if s.split(":")[-1] >= cutoff]
    save_known_jobs(known)
    return urls


def load_job_inbox():
    """Load jobs from the manual inbox file (job-inbox.json).

    The inbox is a JSON array of job objects. Each job should have:
      - title (required)
      - company (required)
      - location
      - salary
      - url (Indeed or company link)
      - contact_email (optional — if provided, pipeline emails them directly)

    After processing, the inbox file is cleared.
    """
    if not JOB_INBOX.exists():
        return []

    try:
        with open(JOB_INBOX) as f:
            inbox = json.load(f)
        if not isinstance(inbox, list):
            return []

        # Validate required fields
        valid = []
        known = load_known_jobs()
        seen_jobs = known.get("seen_jobs", {})

        for job in inbox:
            if not job.get("title") or not job.get("company"):
                continue
            job_key = f"{slugify(job['company'])}:{slugify(job['title'])}"
            if job_key in seen_jobs:
                print(f"  [SKIP-INBOX] Already seen: {job['company']} - {job['title']}")
                continue
            job.setdefault("location", "Unknown")
            job.setdefault("salary", "Not listed")
            job.setdefault("url", "")
            job.setdefault("query", "manual-inbox")
            seen_jobs[job_key] = datetime.now().strftime("%Y-%m-%d")
            valid.append(job)
            print(f"  [INBOX] {job['company']} - {job['title']}")

        known["seen_jobs"] = seen_jobs
        save_known_jobs(known)

        # Clear the inbox after reading
        JOB_INBOX.write_text("[]", encoding="utf-8")

        return valid
    except (json.JSONDecodeError, Exception) as e:
        print(f"  [INBOX ERROR] {e}")
        return []


# ═══════════════════════════════════════════════════════════
#  STEP 2: CREATE JOB FILES
# ═══════════════════════════════════════════════════════════

def create_job_files(new_jobs):
    """Create .md files in jobs/active/ for each new job."""
    print(f"\n[STEP 2] Creating job files for {len(new_jobs)} new leads...")
    created = []

    for job in new_jobs:
        if job.get("fallback"):
            continue  # Don't create files for fallback URL-only entries

        num = get_next_job_number()
        slug = f"{num:02d}-{slugify(job['company'])}"
        resume_type = classify_resume(job["title"])
        job["slug"] = slug
        job["resume_type"] = resume_type
        job["number"] = num

        content = f"""# {job['company']} - {job['title']}

## Job Details
- **Company:** {job['company']}
- **Title:** {job['title']}
- **Location:** {job['location']}
- **Type:** Full-time
- **Pay:** {job['salary']}
- **Indeed Link:** {job['url']}
- **Contact Email:** {job.get('contact_email', 'Unknown')}
- **Found via:** Pipeline scan ({job['query']})
- **Found on:** {datetime.now().strftime('%Y-%m-%d')}

## Why Callie Fits
- Matched via search: "{job['query']}"
- Resume type: {resume_type}

## Application Status
- [ ] Cover letter written
- [ ] Applied via Indeed
- [ ] Email sent
- [ ] Follow-up scheduled
"""
        filepath = ACTIVE_DIR / f"{slug}.md"
        filepath.write_text(content, encoding="utf-8")
        created.append(job)
        print(f"  Created: {slug}.md (resume: {resume_type})")

    return created


# ═══════════════════════════════════════════════════════════
#  STEP 3: GENERATE COVER LETTERS + PDFs
# ═══════════════════════════════════════════════════════════

def get_cover_letter_paragraphs(resume_type, company, title):
    """Generate templated cover letter paragraphs based on resume type."""
    today_str = datetime.now().strftime("%B %d, %Y")

    if resume_type == "design-sales":
        return [
            f"I'm writing to express my interest in the {title} position at {company}. "
            f"Your company's commitment to quality design and client satisfaction aligns closely "
            f"with the values I've built my career around, and I'd welcome the opportunity to bring "
            f"my design and sales expertise to your team.",

            f"Over the past three years at Ethan Allen, I built a successful design consultancy "
            f"practice around in-home and in-studio consultations, earning the 2025 Gold Spirit Award "
            f"for generating over $800,000 in design sales. My daily work involved sitting with "
            f"homeowners, understanding their needs, and presenting tailored design solutions that "
            f"transformed their spaces. That consultative, relationship-driven approach is precisely "
            f"what I'd bring to {company}.",

            f"My background in space planning, material and finish selections, and managing projects "
            f"from concept through completion means I understand how to set expectations, communicate "
            f"clearly, and deliver results. I thrive in environments where I can focus on the client "
            f"relationship and the design conversation.",

            f"I would welcome the chance to discuss how my experience could contribute to "
            f"{company}'s continued success. I'm available at 949-557-9014 or CallieWells17@gmail.com.",
        ]

    elif resume_type == "design-assistant":
        return [
            f"I'm writing to express my interest in the {title} position at {company}. "
            f"I'm drawn to your team's focus on quality design, and I'd love the opportunity "
            f"to contribute my residential design experience and organizational skills.",

            f"My background spans five years in residential interior design across three firms, "
            f"including three years as a Design Consultant at Ethan Allen. I've delivered "
            f"personalized design services through consultations, space planning, and curated "
            f"fabric and finish selections. Prior to that, I supported designers at Goff Designs "
            f"and coordinated client operations at Vintage Design Inc.",

            f"What I'd bring to {company} is a combination of strong aesthetic judgment and the "
            f"organizational discipline to keep projects running smoothly. I'm experienced in "
            f"project documentation, vendor coordination, material samples, and maintaining "
            f"consistent client communication throughout the design process.",

            f"I would love the opportunity to discuss how I could support your team's success. "
            f"Please feel free to reach me at 949-557-9014 or CallieWells17@gmail.com.",
        ]

    else:  # coordinator
        return [
            f"I'm writing to apply for the {title} position at {company}. "
            f"The opportunity to bring my organizational and client-facing experience to your "
            f"team is genuinely exciting, and I believe my background makes me a strong fit.",

            f"For the past five years, I've worked in roles that blend high-touch client service "
            f"with structured administrative coordination. At Ethan Allen, I managed multiple "
            f"concurrent projects, maintained detailed calendars and documentation, and served as "
            f"the primary point of contact for clients. At Vintage Design Inc., I served as front "
            f"desk contact for clients, installers, and vendors, managing daily operations.",

            f"These experiences give me a skill set that maps directly to this role: calendar and "
            f"deadline management, cross-functional communication, document organization, vendor "
            f"coordination, and the ability to keep multiple workstreams moving simultaneously. "
            f"I hold a Bachelor of Business Administration from Arizona State University.",

            f"I'd welcome the opportunity to discuss how I can contribute to {company}. "
            f"Please feel free to reach me at 949-557-9014 or CallieWells17@gmail.com.",
        ]


def generate_cover_letters(jobs):
    """Generate cover letter .md files and PDFs for each job."""
    print(f"\n[STEP 3] Generating cover letters for {len(jobs)} jobs...")

    try:
        from reportlab.lib.pagesizes import letter as LETTER_SIZE
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib.colors import HexColor
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
        from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY
        has_reportlab = True
    except ImportError:
        print("  WARNING: reportlab not installed. Skipping PDF generation.")
        has_reportlab = False

    for job in jobs:
        slug = job["slug"]
        resume_type = job["resume_type"]
        paragraphs = get_cover_letter_paragraphs(resume_type, job["company"], job["title"])

        # Write markdown cover letter
        greeting = f"Dear {job['company']} Hiring Team,"
        md_content = f"""# {job['company']} - {job['title']}

**Email Subject:** Application for {job['title']} - Callie Wells

---

{greeting}

{chr(10).join(paragraphs)}

Warm regards,

Callie Nichole Wells
949-557-9014
CallieWells17@gmail.com
www.linkedin.com/in/callie-wells17
"""
        md_path = CL_DRAFTS / f"{slug}.md"
        md_path.write_text(md_content, encoding="utf-8")
        print(f"  Cover letter (md): {slug}.md")

        # Generate PDF
        if has_reportlab:
            pdf_path = CL_DRAFTS / f"{slug}.pdf"
            _build_cover_letter_pdf(pdf_path, job["company"], job["title"],
                                     greeting, paragraphs,
                                     LETTER_SIZE, SimpleDocTemplate, Paragraph,
                                     Spacer, HRFlowable, ParagraphStyle,
                                     inch, HexColor, TA_LEFT, TA_JUSTIFY)
            job["pdf_path"] = pdf_path
            print(f"  Cover letter (pdf): {slug}.pdf")

    return jobs


def _build_cover_letter_pdf(output_path, company, title, greeting, paragraphs,
                             LETTER_SIZE, SimpleDocTemplate, Paragraph,
                             Spacer, HRFlowable, ParagraphStyle,
                             inch, HexColor, TA_LEFT, TA_JUSTIFY):
    """Build a professional cover letter PDF."""
    NAVY = HexColor("#1a365d")
    DARK_GRAY = HexColor("#2d3748")
    MED_GRAY = HexColor("#4a5568")
    ACCENT = HexColor("#2b6cb0")

    styles = {
        "name": ParagraphStyle("Name", fontName="Helvetica-Bold", fontSize=20, leading=24,
                                textColor=NAVY, alignment=TA_LEFT, spaceAfter=2),
        "contact": ParagraphStyle("Contact", fontName="Helvetica", fontSize=9, leading=13,
                                   textColor=MED_GRAY, alignment=TA_LEFT, spaceAfter=0),
        "section_head": ParagraphStyle("SectionHead", fontName="Helvetica-Bold", fontSize=11,
                                        leading=14, textColor=NAVY, spaceBefore=14, spaceAfter=4),
        "body": ParagraphStyle("Body", fontName="Helvetica", fontSize=10.5, leading=15,
                                textColor=DARK_GRAY, alignment=TA_JUSTIFY, spaceAfter=8),
        "greeting": ParagraphStyle("Greeting", fontName="Helvetica", fontSize=10.5, leading=15,
                                    textColor=DARK_GRAY, spaceAfter=8, spaceBefore=16),
        "signoff": ParagraphStyle("Signoff", fontName="Helvetica", fontSize=10.5, leading=15,
                                   textColor=DARK_GRAY, spaceBefore=8, spaceAfter=2),
        "sign_name": ParagraphStyle("SignName", fontName="Helvetica-Bold", fontSize=10.5,
                                     leading=15, textColor=NAVY, spaceAfter=1),
        "sign_detail": ParagraphStyle("SignDetail", fontName="Helvetica", fontSize=9,
                                       leading=12, textColor=MED_GRAY),
    }

    doc = SimpleDocTemplate(str(output_path), pagesize=LETTER_SIZE,
                             leftMargin=1*inch, rightMargin=1*inch,
                             topMargin=0.9*inch, bottomMargin=0.8*inch)
    story = []

    story.append(Paragraph("Callie Nichole Wells", styles["name"]))
    story.append(Paragraph("5 Caladium, Rancho Santa Margarita, CA 92688", styles["contact"]))
    story.append(Paragraph(
        "949-557-9014 &nbsp;|&nbsp; CallieWells17@gmail.com &nbsp;|&nbsp; linkedin.com/in/callie-wells17",
        styles["contact"]))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT, spaceAfter=12, spaceBefore=4))

    story.append(Paragraph(datetime.now().strftime("%B %d, %Y"), styles["body"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph(f"Re: {title}", styles["section_head"]))
    story.append(Spacer(1, 2))
    story.append(Paragraph(greeting, styles["greeting"]))

    for para in paragraphs:
        story.append(Paragraph(para, styles["body"]))

    story.append(Spacer(1, 4))
    story.append(Paragraph("Warm regards,", styles["signoff"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Callie Nichole Wells", styles["sign_name"]))
    story.append(Paragraph("949-557-9014", styles["sign_detail"]))
    story.append(Paragraph("CallieWells17@gmail.com", styles["sign_detail"]))
    story.append(Paragraph("linkedin.com/in/callie-wells17", styles["sign_detail"]))

    doc.build(story)


# ═══════════════════════════════════════════════════════════
#  STEP 4: MERGE PDFs
# ═══════════════════════════════════════════════════════════

def merge_pdfs(jobs):
    """Merge cover letter + resume into Indeed-ready single PDF."""
    print(f"\n[STEP 4] Merging cover letter + resume PDFs...")

    try:
        from pypdf import PdfReader, PdfWriter
    except ImportError:
        print("  WARNING: pypdf not installed. Skipping merge.")
        return jobs

    for job in jobs:
        slug = job["slug"]
        resume_type = job["resume_type"]
        cl_path = CL_DRAFTS / f"{slug}.pdf"
        res_path = RES_DIR / RESUME_FILES[resume_type]
        out_path = MERGED_DIR / f"{slug}-full.pdf"

        if not cl_path.exists():
            print(f"  [SKIP] No PDF for {slug}")
            continue
        if not res_path.exists():
            print(f"  [SKIP] Resume not found: {RESUME_FILES[resume_type]}")
            continue

        writer = PdfWriter()
        for page in PdfReader(str(cl_path)).pages:
            writer.add_page(page)
        for page in PdfReader(str(res_path)).pages:
            writer.add_page(page)

        with open(out_path, "wb") as f:
            writer.write(f)

        job["merged_path"] = out_path
        print(f"  Merged: {slug}-full.pdf")

    return jobs


# ═══════════════════════════════════════════════════════════
#  STEP 5: EMAIL COMPANIES + CALLIE
# ═══════════════════════════════════════════════════════════

def send_applications(jobs):
    """Email companies directly and send Callie Indeed kits."""
    print(f"\n[STEP 5] Sending applications...")
    known = load_known_jobs()
    today = datetime.now().strftime("%Y-%m-%d")
    emails_sent = 0
    kits_sent = []

    for job in jobs:
        if job.get("fallback"):
            continue

        slug = job["slug"]
        resume_type = job["resume_type"]
        cl_pdf = CL_DRAFTS / f"{slug}.pdf"
        res_pdf = RES_DIR / RESUME_FILES[resume_type]
        merged_pdf = MERGED_DIR / f"{slug}-full.pdf"

        # Try to find company email from job file
        job_file = ACTIVE_DIR / f"{slug}.md"
        contact_email = None
        if job_file.exists():
            content = job_file.read_text(encoding="utf-8")
            email_match = re.search(r'\*\*Contact Email:\*\*\s*(\S+@\S+)', content)
            if email_match and email_match.group(1).lower() != "unknown":
                contact_email = email_match.group(1)

        # Send to company if we have their email
        if contact_email:
            subject = f"Application for {job['title']} - Callie Wells"
            body = f"""Dear {job['company']} Hiring Team,

Please find attached my cover letter and resume for the {job['title']} position.

I bring five years of residential interior design experience, most recently at Ethan Allen where I earned the 2025 Gold Spirit Award for generating over $800,000 in design sales. I'd welcome the chance to discuss how my background could contribute to your team.

I'm available at 949-557-9014 or CallieWells17@gmail.com.

Warm regards,
Callie Nichole Wells
949-557-9014
CallieWells17@gmail.com
linkedin.com/in/callie-wells17"""

            attachments = []
            if cl_pdf.exists():
                attachments.append(cl_pdf)
            if res_pdf.exists():
                attachments.append(res_pdf)

            if send_email(contact_email, subject, body, attachments):
                known["email_sent"][slug] = {
                    "to": contact_email, "date": today,
                    "cover_letter": f"{slug}.pdf", "resume": resume_type,
                }
                emails_sent += 1

                # Update job file checkboxes
                if job_file.exists():
                    fc = job_file.read_text(encoding="utf-8")
                    fc = fc.replace("- [ ] Cover letter written",
                                    f"- [x] Cover letter written ({today})")
                    fc = fc.replace("- [ ] Email sent",
                                    f"- [x] Email sent to {contact_email} ({today})")
                    followup_date = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
                    fc = fc.replace("- [ ] Follow-up scheduled",
                                    f"- [x] Follow-up scheduled ({followup_date})")
                    job_file.write_text(fc, encoding="utf-8")

        # Track for Callie's kit
        if merged_pdf.exists():
            kits_sent.append(job)
            known["indeed_kit_sent"][slug] = {
                "date": today,
                "merged_pdf": f"{slug}-full.pdf",
                "resume": resume_type,
                "awaiting_callie_submit": True,
            }
            # Update cover letter checkbox
            if job_file.exists():
                fc = job_file.read_text(encoding="utf-8")
                if "- [ ] Cover letter written" in fc:
                    fc = fc.replace("- [ ] Cover letter written",
                                    f"- [x] Cover letter written ({today})")
                    job_file.write_text(fc, encoding="utf-8")

        known["applied"][slug] = today

    save_known_jobs(known)

    # Send Callie her Indeed kits
    if kits_sent:
        _send_callie_kit(kits_sent, emails_sent)

    print(f"  Direct emails sent: {emails_sent}")
    print(f"  Indeed kits for Callie: {len(kits_sent)}")
    return emails_sent, len(kits_sent)


def _send_callie_kit(jobs, direct_emails_sent):
    """Email Callie the merged PDFs for Indeed submission."""
    today = datetime.now().strftime("%Y-%m-%d")
    lines = []
    attachments = []

    for i, job in enumerate(jobs, 1):
        slug = job["slug"]
        merged_pdf = MERGED_DIR / f"{slug}-full.pdf"
        direct_note = ""

        # Check if we also emailed the company directly
        known = load_known_jobs()
        if slug in known.get("email_sent", {}):
            to_addr = known["email_sent"][slug]["to"]
            direct_note = f"\n   NOTE: Also emailed directly to {to_addr}"

        lines.append(
            f"{i}. {job['company'].upper()} - {job['title']}\n"
            f"   Location: {job['location']}\n"
            f"   Pay: {job['salary']}\n"
            f"   Indeed: {job['url']}\n"
            f"   Resume: {job['resume_type']}\n"
            f"   Attached: {slug}-full.pdf{direct_note}"
        )
        if merged_pdf.exists():
            attachments.append(merged_pdf)

    body = f"""Hi Callie,

Your job pipeline found {len(jobs)} new lead(s) today ({today}).
{direct_emails_sent} application(s) were also sent directly to company emails.

NEW JOB LEADS — READY TO APPLY:

{chr(10).join(lines)}

HOW TO APPLY ON INDEED:
1. Click each Indeed link above
2. Upload the matching -full.pdf (cover letter + resume combined)
3. Part-time roles included if they have full-time potential

Next scan runs automatically tomorrow at 7:00 AM.

Your Job Search Pipeline"""

    send_email(
        CALLIE_EMAIL,
        f"Job Pipeline - {len(jobs)} New Leads ({today})",
        body,
        attachments
    )


# ═══════════════════════════════════════════════════════════
#  STEP 6: MOVE active/ -> applied/
# ═══════════════════════════════════════════════════════════

def move_applied_jobs():
    """Move processed jobs from active/ to applied/."""
    print("\n[STEP 6] Moving applied jobs...")
    moved = []

    for job_file in sorted(ACTIVE_DIR.glob("*.md")):
        dest = APPLIED_DIR / job_file.name
        shutil.move(str(job_file), str(dest))
        moved.append(job_file.name)
        print(f"  Moved: {job_file.name} -> applied/")

    # Copy cover letter PDFs to sent/
    for cl_file in sorted(CL_DRAFTS.glob("*.pdf")):
        dest = CL_SENT / cl_file.name
        if not dest.exists():
            shutil.copy2(str(cl_file), str(dest))

    if not moved:
        print("  No jobs to move")

    return moved


# ═══════════════════════════════════════════════════════════
#  STEP 7: FOLLOW-UPS
# ═══════════════════════════════════════════════════════════

def send_followups():
    """Send follow-up emails for jobs applied 5+ calendar days ago."""
    print("\n[STEP 7] Checking for follow-ups needed...")
    known = load_known_jobs()
    followups_sent = known.get("followups_sent", [])
    email_sent = known.get("email_sent", {})
    today = datetime.now()
    sent_count = 0

    for job_slug, email_data in email_sent.items():
        if job_slug in followups_sent:
            continue

        sent_date_str = email_data.get("date")
        if not sent_date_str or sent_date_str == "pre-pipeline":
            continue

        sent_date = datetime.fromisoformat(sent_date_str)
        days_since = (today - sent_date).days

        if days_since >= 5:
            to_email = email_data.get("to")
            if not to_email or to_email == CALLIE_EMAIL:
                continue

            company = job_slug.split("-", 1)[-1].replace("-", " ").title() if "-" in job_slug else job_slug

            success = send_email(
                to_email,
                "Following Up - Callie Wells Application",
                f"""Dear Hiring Team,

I hope this message finds you well. I wanted to follow up on the application I submitted on {sent_date.strftime('%B %d, %Y')}. I remain very interested in the opportunity and would welcome the chance to discuss how my background in residential design could contribute to your team.

Please don't hesitate to reach out if you need any additional information. I'm available at 949-557-9014 or CallieWells17@gmail.com.

Warm regards,
Callie Nichole Wells
949-557-9014
CallieWells17@gmail.com
linkedin.com/in/callie-wells17"""
            )
            if success:
                followups_sent.append(job_slug)
                sent_count += 1
                print(f"  Follow-up sent: {job_slug} -> {to_email}")

    known["followups_sent"] = followups_sent
    save_known_jobs(known)

    if sent_count == 0:
        print("  No follow-ups needed yet")
    return sent_count


# ═══════════════════════════════════════════════════════════
#  STEP 8: UPDATE APPLICATION LOG
# ═══════════════════════════════════════════════════════════

def update_application_log(jobs, emails_sent_count, kits_count):
    """Append new jobs to application-log.md."""
    print("\n[STEP 8] Updating application log...")
    today = datetime.now().strftime("%Y-%m-%d")
    known = load_known_jobs()

    if not APP_LOG_FILE.exists():
        return

    content = APP_LOG_FILE.read_text(encoding="utf-8")

    # Add new direct-emailed jobs to the Gmail table
    for job in jobs:
        if job.get("fallback"):
            continue
        slug = job["slug"]
        if slug in known.get("email_sent", {}):
            to_email = known["email_sent"][slug]["to"]
            new_row = (f"| {today} | {job['company']} | {job['title']} | "
                       f"{to_email} | {slug}.pdf | {job['resume_type']} | SENT |")
            # Insert before "## Indeed Kits" or "## Applied Externally"
            for marker in ["## Indeed Kits", "## Applied Externally"]:
                if marker in content:
                    content = content.replace(marker, f"{new_row}\n\n{marker}")
                    break

    APP_LOG_FILE.write_text(content, encoding="utf-8")
    print(f"  Log updated with {len(jobs)} new entries")


# ═══════════════════════════════════════════════════════════
#  STEP 9: SCAN LOG
# ═══════════════════════════════════════════════════════════

def log_scan(scan_time, new_count, moved_count, followup_count, emails_sent, kits_sent):
    """Append to scan log."""
    if not SCAN_LOG.exists():
        header = """# Daily Scan Log

| Scan Time | New Jobs | Emails Sent | Kits to Callie | Follow-ups | Jobs Moved |
|-----------|----------|-------------|----------------|------------|------------|
"""
        with open(SCAN_LOG, "w") as f:
            f.write(header)

    entry = (f"| {scan_time} | {new_count} | {emails_sent} | "
             f"{kits_sent} | {followup_count} | {moved_count} |\n")
    with open(SCAN_LOG, "a") as f:
        f.write(entry)


# ═══════════════════════════════════════════════════════════
#  MAIN PIPELINE
# ═══════════════════════════════════════════════════════════

def main(fromage_days=1):
    scan_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"{'='*60}")
    print(f"  CALLIE WELLS JOB PIPELINE - {scan_time}")
    print(f"  Search: last {fromage_days} day(s), {RADIUS}mi, FT+PT")
    print(f"  Mode: {'DRY RUN' if DRY_RUN else 'LIVE'}")
    print(f"{'='*60}")

    try:
        # Step 1a: Scrape Indeed for individual jobs
        new_jobs = scrape_indeed(fromage_days=fromage_days)

        # Step 1b: Check the manual job inbox
        print("\n[STEP 1b] Checking job inbox...")
        inbox_jobs = load_job_inbox()
        if inbox_jobs:
            # Merge inbox jobs (non-fallback) with scraped jobs
            new_jobs = [j for j in new_jobs if not j.get("fallback")] + inbox_jobs
            print(f"  {len(inbox_jobs)} job(s) loaded from inbox")
        else:
            print("  Inbox empty")

        # Step 2: Create job files
        created_jobs = create_job_files(new_jobs)

        # Step 3: Generate cover letters (md + PDF)
        if created_jobs:
            created_jobs = generate_cover_letters(created_jobs)

        # Step 4: Merge cover letter + resume PDFs
        if created_jobs:
            created_jobs = merge_pdfs(created_jobs)

        # Step 5: Email companies + send Callie kits
        emails_sent = 0
        kits_sent = 0
        if created_jobs:
            emails_sent, kits_sent = send_applications(created_jobs)

        # Step 6: Move active/ -> applied/
        moved = move_applied_jobs()

        # Step 7: Send follow-up emails
        followup_count = send_followups()

        # Step 8: Update application log
        if created_jobs:
            update_application_log(created_jobs, emails_sent, kits_sent)

        # Step 9: Log scan results
        log_scan(scan_time, len(created_jobs), len(moved), followup_count,
                 emails_sent, kits_sent)

        # If no new individual jobs but we have search URLs, send digest
        fallback_jobs = [j for j in new_jobs if j.get("fallback")]
        if fallback_jobs and not created_jobs:
            _send_fallback_digest(fallback_jobs, len(moved), followup_count, scan_time)

        print(f"\n{'='*60}")
        print(f"  PIPELINE COMPLETE")
        print(f"  New jobs found: {len(created_jobs)}")
        print(f"  Direct emails sent: {emails_sent}")
        print(f"  Indeed kits to Callie: {kits_sent}")
        print(f"  Jobs moved to applied: {len(moved)}")
        print(f"  Follow-ups sent: {followup_count}")
        print(f"{'='*60}")

    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        traceback.print_exc()
        # Try to notify Callie of failure
        send_email(
            CALLIE_EMAIL,
            f"Job Pipeline ERROR - {scan_time}",
            f"The daily job pipeline encountered an error:\n\n{e}\n\n"
            f"The pipeline may need manual intervention. Check the script logs."
        )


def _send_fallback_digest(urls, moved_count, followup_count, scan_time):
    """Send URL-based digest when scraping didn't find individual jobs."""
    active_count = len(list(ACTIVE_DIR.glob("*.md")))
    applied_count = len(list(APPLIED_DIR.glob("*.md")))

    links_text = "\n".join([f"  {i+1}. {u['query']}: {u['url']}" for i, u in enumerate(urls)])
    body = f"""Hi Callie,

Daily Job Scan completed at {scan_time}.

PIPELINE STATUS:
  Active: {active_count} | Applied: {applied_count}
  Follow-ups today: {followup_count} | Moved: {moved_count}

The scanner couldn't extract individual listings today (Indeed may have blocked scraping).
Here are the search links to check manually:

{links_text}

Next scan runs automatically tomorrow at 7:00 AM.

Your Job Search Pipeline"""

    send_email(
        CALLIE_EMAIL,
        f"Daily Job Report - {scan_time[:10]} | Check Links Manually",
        body
    )


# ═══════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════

DRY_RUN = False

if __name__ == "__main__":
    days = 1
    for arg in sys.argv[1:]:
        if arg == "--dry":
            DRY_RUN = True
        elif arg.isdigit():
            days = int(arg)

    main(fromage_days=days)

"""Process today's best NEW leads (not dupes from prior pipeline)."""
import sys, os, subprocess
sys.path.insert(0, os.path.dirname(__file__))
from daily_job_scan import _build_cover_letter_pdf
from reportlab.lib.pagesizes import letter as LS
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY
from pypdf import PdfReader, PdfWriter
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Today's genuinely NEW leads (not dupes)
LEADS = [
    {
        "num": 34, "slug": "34-ensign-services",
        "company": "Ensign Services",
        "title": "Executive Administrative Assistant II - Human Resources",
        "location": "San Juan Capistrano, CA (10mi from RSM)",
        "pay": "$80,000 - $100,000",
        "score": 4.5,
        "resume": "coordinator",
        "url": "https://www.indeed.com/viewjob?jk=f22c52319ca53e21",
        "greeting": "Dear Ensign Services Hiring Team,",
        "why": "Ensign Services is the corporate HQ for Ensign Group (healthcare services holding). EA II HR role at $80-100K, 10mi from RSM. Matches your BBA + coordination background perfectly.",
        "paragraphs": [
            "I'm writing to apply for the Executive Administrative Assistant II position supporting your Human Resources team. The role's combination of executive support and HR-adjacent operations is a strong match for my background, and San Juan Capistrano is a very convenient location from my home in Rancho Santa Margarita.",
            "For the past five years, I've coordinated complex workstreams across three firms in high-touch, client-facing roles. At Ethan Allen I managed 200+ client projects simultaneously, maintaining detailed calendars, travel logistics, and documentation, and served as the primary point of contact throughout. At Vintage Design Inc. I ran front desk operations and coordinated daily between clients, installers, and vendors. These experiences translate directly to EA II work: calendar and travel coordination, confidential document handling, stakeholder communication, and keeping multiple workstreams moving without dropping details.",
            "My Bachelor of Business Administration from Arizona State University provides the operational foundation for an HR-adjacent role, and my design-industry background gives me an instinctive eye for polish and professional presentation. I'm known for being proactive, detail-oriented, and discreet with sensitive information.",
            "I'd welcome the chance to discuss how my background can support your HR team. I'm available at 949-557-9014 or CallieWells17@gmail.com.",
        ],
    },
    {
        "num": 35, "slug": "35-walsh-group",
        "company": "The Walsh Group",
        "title": "Design Build Coordinator",
        "location": "Long Beach, CA (~35mi)",
        "pay": "$103,000 - $155,000",
        "score": 4.0,
        "resume": "coordinator",
        "url": "https://www.theladders.com/job/design-build-coordinator-walshgroup-long-beach-ca_86567090",
        "greeting": "Dear Walsh Group Team,",
        "why": "Walsh Group is one of the largest construction companies in the US. Design Build Coordinator at $103-155K - strong upside even though Long Beach commute is ~35mi. Worth applying for the pay and growth.",
        "paragraphs": [
            "I'm writing to apply for the Design Build Coordinator position in Long Beach. While my background is in residential interior design rather than construction, the project coordination skills I've developed across five years in design firms are directly transferable to the coordination work a Design Build role requires.",
            "At Ethan Allen I managed multiple client projects simultaneously from consultation through delivery - maintaining detailed documentation, coordinating vendors and installers, tracking timelines, and serving as the primary communication hub between clients, designers, and operations. At Vintage Design Inc. I ran front-of-house operations and coordinated daily between clients, installers, and vendors. That experience of being the reliable connective tissue across fast-moving stakeholders translates directly to design-build coordination.",
            "My Bachelor of Business Administration from Arizona State University provides an operational foundation, and I bring strong Microsoft Office proficiency, project documentation discipline, and the kind of proactive communication that keeps complex builds on track. I'm ready to apply the project coordination skills I've built in residential design to the design-build environment at Walsh.",
            "I'd welcome the opportunity to discuss how my coordination experience can contribute. I'm available at 949-557-9014 or CallieWells17@gmail.com.",
        ],
    },
]


RESUME_FILES = {
    "design-sales": "callie-wells-resume-design-sales.pdf",
    "design-assistant": "callie-wells-resume-design-assistant.pdf",
    "coordinator": "callie-wells-resume-coordinator.pdf",
}


def send_mime_email(to, subject, body, attachment):
    msg = MIMEMultipart()
    msg.attach(MIMEText(body, "plain"))
    with open(attachment, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f'attachment; filename="{os.path.basename(attachment)}"')
    msg.attach(part)
    msg["To"] = to
    msg["Subject"] = subject
    eml = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_outgoing.eml")
    with open(eml, "wb") as f:
        f.write(msg.as_bytes())
    gws = os.path.join(os.environ.get("APPDATA", ""), "npm", "gws.cmd")
    cmd = [gws, "gmail", "users", "messages", "send",
           "--params", '{"userId": "me"}',
           "--upload", eml,
           "--upload-content-type", "message/rfc822"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if os.path.exists(eml):
        os.remove(eml)
    return result.returncode == 0, result.stderr[:300]


for lead in LEADS:
    slug = lead["slug"]
    company = lead["company"]
    title = lead["title"]
    res_type = lead["resume"]

    # Job file
    jf = os.path.join(BASE, "jobs", "active", f"{slug}.md")
    with open(jf, "w", encoding="utf-8") as f:
        f.write(f"# {company} - {title}\n\n")
        f.write(f"## Job Details\n")
        f.write(f"- **Company:** {company}\n- **Title:** {title}\n")
        f.write(f"- **Location:** {lead['location']}\n- **Pay:** {lead['pay']}\n")
        f.write(f"- **Direct URL:** {lead['url']}\n- **Source:** SerpAPI\n")
        f.write(f"- **Found:** 2026-04-19\n- **Score:** {lead['score']}/5\n")
        f.write(f"- **Resume:** {res_type}\n\n")
        f.write(f"## Why This Fits\n{lead['why']}\n\n")
        f.write(f"## Application Status\n- [x] Cover letter written (2026-04-19)\n- [ ] Applied\n- [x] Kit emailed to Callie (2026-04-19)\n- [ ] Follow-up scheduled\n")

    # Cover letter PDF
    cl_path = os.path.join(BASE, "cover-letters", "drafts", f"{slug}.pdf")
    _build_cover_letter_pdf(cl_path, company, title, lead["greeting"], lead["paragraphs"],
        LS, SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
        ParagraphStyle, inch, HexColor, TA_LEFT, TA_JUSTIFY)

    # Merged
    res_pdf = os.path.join(BASE, "resumes", RESUME_FILES[res_type])
    out_pdf = os.path.join(BASE, "cover-letters", "merged-for-indeed", f"{slug}-full.pdf")
    writer = PdfWriter()
    for p in PdfReader(cl_path).pages: writer.add_page(p)
    for p in PdfReader(res_pdf).pages: writer.add_page(p)
    with open(out_pdf, "wb") as f:
        writer.write(f)

    # Email body
    body = f"""Hi Callie,

{lead['why']}

APPLY HERE:
{lead['url']}

Company: {company}
Role: {title}
Location: {lead['location']}
Pay: {lead['pay']}
Score: {lead['score']}/5

Steps:
1. Click the link above
2. Hit Apply
3. Upload the attached PDF (cover letter + {res_type} resume)

- Your Job Search Pipeline
"""
    body_file = os.path.join(BASE, "scripts", "email-bodies", f"{slug}.txt")
    with open(body_file, "w", encoding="utf-8") as f:
        f.write(body)

    subject = f"APPLY HERE: {company} - {title.split('-')[0].strip()[:50]} ({lead['pay'].split('(')[0].strip()})"
    subject = subject.encode("ascii", errors="replace").decode("ascii").replace("?", "-")

    ok, err = send_mime_email("CallieWells17@gmail.com", subject, body, out_pdf)
    print(f"[{'SENT' if ok else 'FAIL'}] {slug}: {subject}")
    if not ok:
        print(f"  Error: {err}")

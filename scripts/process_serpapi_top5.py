"""Process the top 5 SerpAPI leads: create job files, cover letters, PDFs, email Callie."""
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

# Top 5 hand-curated from SerpAPI batch scan
LEADS = [
    {
        "num": 29, "slug": "29-eisenbart-sons",
        "company": "Eisenbart and Sons Windows & Doors",
        "title": "In-Home Design Consultant Sales Representative",
        "location": "Mission Viejo, CA (5mi from RSM!)",
        "pay": "$120,000 - $200,000",
        "score": 4.7,
        "resume": "design-sales",
        "url": "https://www.indeed.com/viewjob?jk=bea3d5d77cce150a",
        "greeting": "Dear Eisenbart and Sons Team,",
        "why_great": "Perfect match - in-home consultative sales exactly like Ethan Allen, $120-200K range, and the commute is 5 miles from RSM. Mission Viejo is literally next door.",
        "paragraphs": [
            "I'm writing to apply for the In-Home Design Consultant Sales Representative position. As a Rancho Santa Margarita resident with three years of in-home design sales experience at Ethan Allen, this role's location in Mission Viejo and the consultative in-home sales model are exactly what I've been looking for.",
            "At Ethan Allen I generated over $800,000 in design sales and earned the 2025 Gold Spirit Award. My approach has always been consultative - sitting with homeowners, understanding how they use their spaces, and presenting solutions that truly fit their lives. Windows and doors are perhaps the most impactful design decisions a homeowner makes - they affect light, energy, security, and curb appeal. Helping homeowners navigate that decision with confidence is work I know I can excel at.",
            "My background in material and finish selection translates directly to window and door consultation, and my track record of closing $100K+ design projects with trust-first sales is exactly the skill set this role calls for.",
            "I'd welcome the chance to meet and discuss how I can contribute. I'm available at 949-557-9014 or CallieWells17@gmail.com.",
        ],
    },
    {
        "num": 30, "slug": "30-pacific-life",
        "company": "Pacific Life",
        "title": "Division Executive Administrative Assistant",
        "location": "Newport Beach, CA (20mi)",
        "pay": "$45-55/hr ($93,600 - $114,400/yr)",
        "score": 4.5,
        "resume": "coordinator",
        "url": "https://www.indeed.com/viewjob?jk=8b17854b3c041a82",
        "greeting": "Dear Pacific Life Hiring Team,",
        "why_great": "Blue-chip financial services company, $93-114K for division-level EA, Newport Beach. BBA from ASU is a natural fit for Pacific Life's corporate environment.",
        "paragraphs": [
            "I'm writing to apply for the Division Executive Administrative Assistant position. Pacific Life's reputation as a premier financial services company and the scope of a division-level EA role match both my career direction and my operational experience.",
            "For the past five years, I've coordinated complex, fast-moving workstreams across three firms. At Ethan Allen I managed multiple client projects simultaneously from consultation through delivery - handling calendars, travel logistics, vendor coordination, and confidential client information. At Vintage Design Inc. I ran front desk operations and served as the primary contact between clients, installers, and vendors. These experiences translate directly to division-level EA support: calendar and travel coordination, executive communication, document management, and the ability to manage multiple workstreams without dropping details.",
            "My Bachelor of Business Administration from Arizona State University provides the operational grounding for a financial services environment, and I bring strong Microsoft Office proficiency, a proactive approach to anticipating needs, and the professionalism a division-level office requires.",
            "I'd welcome the opportunity to discuss how my background can support your division's leadership. I'm available at 949-557-9014 or CallieWells17@gmail.com.",
        ],
    },
    {
        "num": 31, "slug": "31-boutique-recruiting",
        "company": "Boutique Recruiting",
        "title": "Executive Assistant to HR",
        "location": "San Juan Capistrano, CA (10mi)",
        "pay": "$80,000 - $100,000",
        "score": 4.5,
        "resume": "coordinator",
        "url": "https://www.ziprecruiter.com/c/Boutique-Recruiting/Job/Executive-Assistant-to-HR/-in-San-Juan-Capistrano,CA?jid=59305c1c3446509e",
        "greeting": "Dear Boutique Recruiting Team,",
        "why_great": "San Juan Capistrano is just 10mi from RSM (20-minute drive), $80-100K, and EA to HR fits her BBA + coordination experience perfectly.",
        "paragraphs": [
            "I'm writing to express my interest in the Executive Assistant to HR position. The role's combination of executive support and HR-adjacent work is a strong match for my background, and San Juan Capistrano is a very convenient location from my home in Rancho Santa Margarita.",
            "For the past five years, I've coordinated complex workstreams across three firms in client-facing, high-touch roles. At Ethan Allen I managed multiple client projects simultaneously, maintaining detailed calendars, travel logistics, and documentation, and served as the primary point of contact for 200+ clients. At Vintage Design Inc. I ran front desk operations and coordinated daily between clients, installers, and vendors. That experience translates directly to EA work: calendar management, confidential document handling, stakeholder communication, and keeping multiple workstreams moving.",
            "My Bachelor of Business Administration from Arizona State University provides the operational foundation for an HR-adjacent role, and I'm comfortable handling sensitive information, maintaining professional discretion, and supporting leadership with the polish a boutique firm requires. I'm known for being proactive, detail-oriented, and genuinely enjoyable to work with.",
            "I'd welcome the chance to discuss how my background can support your team. I'm available at 949-557-9014 or CallieWells17@gmail.com.",
        ],
    },
    {
        "num": 32, "slug": "32-restoration-hardware",
        "company": "Restoration Hardware (RH)",
        "title": "Interior Design Assistant",
        "location": "Newport Beach, CA (20mi)",
        "pay": "$32/hr (~$66K)",
        "score": 4.6,
        "resume": "design-assistant",
        "url": "https://bandana.com/jobs/1ee3ac25-1173-4f49-abbe-ab85bd756e7a",
        "greeting": "Dear Restoration Hardware Team,",
        "why_great": "RH is a GOAL company. Newport Beach location, luxury residential focus, brand prestige. This is a dream role for her portfolio.",
        "paragraphs": [
            "I'm writing to apply for the Interior Design Assistant position at your Newport Beach Gallery. RH's design-forward approach, investment in craft, and luxury residential clientele represent exactly the caliber of brand where I've built my strongest work.",
            "My background is five years of residential interior design across three firms. Most recently at Ethan Allen, I spent three years as a Design Consultant working with 200+ clients on luxury residential projects - curating fabric and finish selections, developing space plans, and guiding high-value purchase decisions. I earned the 2025 Gold Spirit Award for $800,000+ in design sales, built entirely on relationships and design expertise.",
            "What draws me to RH is the brand's commitment to craft and the elevated clientele. The Design Gallery model, the trade program, and the hospitality expansion through RH Guesthouse - all of it signals a company that takes design seriously. I want to be part of that.",
            "I'd welcome the chance to visit the Newport Beach Gallery and discuss how I can contribute. I'm available at 949-557-9014 or CallieWells17@gmail.com.",
        ],
    },
    {
        "num": 33, "slug": "33-crate-barrel",
        "company": "Crate and Barrel",
        "title": "Design Consultant - Elevate Homes In-Store",
        "location": "Costa Mesa, CA (25mi)",
        "pay": "$60,000 - $80,000",
        "score": 4.3,
        "resume": "design-sales",
        "url": "https://www.learn4good.com/jobs/costa-mesa/california/sales/5030335575/e/",
        "greeting": "Dear Crate and Barrel Team,",
        "why_great": "Specific design consultant role (not general retail), $60-80K salary range listed, established brand with clear career paths.",
        "paragraphs": [
            "I'm writing to apply for the Design Consultant - Elevate Homes In-Store position at your Costa Mesa store. The role's focus on in-store design consultation for clients making meaningful home refreshes is exactly the work I've been doing at Ethan Allen for the past three years.",
            "At Ethan Allen I generated over $800,000 in design sales through in-home and in-store consultations, earning the 2025 Gold Spirit Award. My approach has always been to listen first - understanding how clients actually live before recommending product. That consultative style translates directly to the Elevate Homes program, where clients are making deliberate, high-investment design decisions rather than transactional purchases.",
            "My background across three design firms gives me fluency in fabric and finish selection, space planning, and product knowledge - and my client base at Ethan Allen taught me the patience and discretion luxury clients expect.",
            "I'd love to discuss how my track record could contribute to your Costa Mesa team. I'm available at 949-557-9014 or CallieWells17@gmail.com.",
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

    # 1. Job file
    jf = os.path.join(BASE, "jobs", "active", f"{slug}.md")
    with open(jf, "w", encoding="utf-8") as f:
        f.write(f"# {company} - {title}\n\n")
        f.write(f"## Job Details\n")
        f.write(f"- **Company:** {company}\n")
        f.write(f"- **Title:** {title}\n")
        f.write(f"- **Location:** {lead['location']}\n")
        f.write(f"- **Pay:** {lead['pay']}\n")
        f.write(f"- **Direct URL:** {lead['url']}\n")
        f.write(f"- **Source:** SerpAPI (Google Jobs)\n")
        f.write(f"- **Found:** 2026-04-17\n")
        f.write(f"- **Score:** {lead['score']}/5\n")
        f.write(f"- **Resume type:** {res_type}\n\n")
        f.write(f"## Why This Fits\n{lead['why_great']}\n\n")
        f.write(f"## Application Status\n- [x] Cover letter written (2026-04-17)\n- [ ] Applied\n- [x] Kit emailed to Callie (2026-04-17)\n- [ ] Follow-up scheduled\n")

    # 2. Cover letter PDF
    cl_path = os.path.join(BASE, "cover-letters", "drafts", f"{slug}.pdf")
    _build_cover_letter_pdf(cl_path, company, title, lead["greeting"], lead["paragraphs"],
        LS, SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
        ParagraphStyle, inch, HexColor, TA_LEFT, TA_JUSTIFY)

    # 3. Merged PDF
    res_pdf = os.path.join(BASE, "resumes", RESUME_FILES[res_type])
    out_pdf = os.path.join(BASE, "cover-letters", "merged-for-indeed", f"{slug}-full.pdf")
    writer = PdfWriter()
    for p in PdfReader(cl_path).pages: writer.add_page(p)
    for p in PdfReader(res_pdf).pages: writer.add_page(p)
    with open(out_pdf, "wb") as f:
        writer.write(f)

    # 4. Email body
    body = f"""Hi Callie,

{lead['why_great']}

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

The attached PDF has your cover letter (page 1) and {res_type} resume (page 2).

- Your Job Search Pipeline
"""
    body_file = os.path.join(BASE, "scripts", "email-bodies", f"{slug}.txt")
    with open(body_file, "w", encoding="utf-8") as f:
        f.write(body)

    # 5. Send
    pay_hint = lead["pay"].split("(")[0].strip() if "(" in lead["pay"] else lead["pay"]
    subject = f"APPLY HERE: {company} - {title.split('(')[0].strip()} ({pay_hint})"
    # Strip non-ascii from subject
    subject = subject.encode("ascii", errors="replace").decode("ascii").replace("?", "-")

    ok, err = send_mime_email("CallieWells17@gmail.com", subject, body, out_pdf)
    if ok:
        print(f"[SENT] {slug}: {subject}")
    else:
        print(f"[FAIL] {slug}: {err}")

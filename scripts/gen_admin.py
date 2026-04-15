"""Generate cover letter PDFs + merge + send emails for today's 5 admin leads."""
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

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

JOBS = [
    ("24-talentpop", "TalentPop", "Executive Assistant to Founders",
     "Dear TalentPop Team,", "coordinator",
     "https://www.linkedin.com/jobs/view/executive-assistant-to-founders-at-talentpop-4399360832",
     [
        "I'm writing to express my interest in the Executive Assistant to Founders position at TalentPop. As a Rancho Santa Margarita resident, the opportunity to support founders building a growing company in my own backyard is genuinely exciting, and I believe my background makes me an ideal fit for this role.",
        "For the past five years, I've worked in roles that blend high-touch client service with structured administrative coordination. At Ethan Allen, I managed multiple concurrent client projects, maintained detailed calendars and documentation, and served as the primary point of contact from consultation through delivery. At Vintage Design Inc., I ran front desk operations, scheduled consultations, managed supply ordering, and coordinated daily between clients, vendors, and installers. These experiences give me the exact skill set founders need: calendar and deadline management, cross-functional communication, organized documentation, and the ability to keep many workstreams moving without dropping details.",
        "My Bachelor of Business Administration from Arizona State University provides the operational foundation, and my client-facing experience means I'm comfortable being the warm, professional first point of contact for external stakeholders. I'm known for anticipating needs, catching details before they become problems, and maintaining calm composure when priorities shift.",
        "I'd welcome the chance to meet the founders and discuss how I can support their work. I'm available at 949-557-9014 or CallieWells17@gmail.com.",
     ]),

    ("25-applied-medical", "Applied Medical", "Executive Assistant",
     "Dear Applied Medical Hiring Team,", "coordinator",
     "https://www.linkedin.com/jobs/view/executive-assistant-at-applied-medical-4399824498",
     [
        "I'm writing to apply for the Executive Assistant position at Applied Medical. As a Rancho Santa Margarita resident, the chance to contribute to a mission-driven company headquartered in my own community is a great fit, and I believe my organizational and client-facing experience matches what this role requires.",
        "For the past five years, I've worked in coordination roles that combine high-touch communication with structured administrative discipline. At Ethan Allen, I managed multiple concurrent projects, maintained detailed calendars and documentation, and served as the primary point of contact for clients throughout their design experience. At Vintage Design Inc., I handled front desk operations, scheduled consultations, managed supply ordering, and coordinated between clients, installers, and vendors daily. These experiences translate directly to executive support: calendar and travel coordination, meeting logistics, confidential document handling, and cross-functional communication.",
        "I hold a Bachelor of Business Administration from Arizona State University, bringing both academic grounding and practical operational experience. I'm a reliable, detail-oriented professional known for anticipating executive needs and maintaining composure under shifting priorities.",
        "I'd welcome the chance to discuss how my background can support your executive team. I'm available at 949-557-9014 or CallieWells17@gmail.com.",
     ]),

    ("26-berkadia", "Berkadia", "Sr Administrative Assistant",
     "Dear Berkadia Hiring Team,", "coordinator",
     "https://www.indeed.com/jobs?q=administrative+coordinator&l=Rancho+Santa+Margarita%2C+CA",
     [
        "I'm writing to express my interest in the Sr Administrative Assistant position supporting your broker team in Irvine. The role's focus on serving as a coordinator between brokers and the broader team is a strong match for my five years of cross-functional coordination experience.",
        "At Ethan Allen, I functioned as the hub between clients, design leads, vendors, and operations - managing multiple concurrent projects while maintaining the documentation, timelines, and communication that kept everything moving. Before that at Vintage Design Inc., I handled daily operations coordination as front desk contact for clients, installers, and vendors. That experience of being the reliable connective tissue between fast-moving stakeholders is exactly what a senior admin role supporting commercial real estate brokers requires.",
        "My Bachelor of Business Administration from Arizona State University gives me a solid foundation for the financial and transactional environment at Berkadia, and I bring a natural attention to detail, strong Microsoft Office proficiency, and the ability to anticipate what busy professionals need before they ask. I'm comfortable handling confidential documents, coordinating travel and complex calendars, and maintaining the polished professionalism a commercial real estate firm requires.",
        "I'd welcome the opportunity to discuss how my coordination experience can support your broker team. I'm available at 949-557-9014 or CallieWells17@gmail.com.",
     ]),

    ("27-experian", "Experian", "Executive Assistant (Hybrid)",
     "Dear Experian Hiring Team,", "coordinator",
     "https://www.linkedin.com/jobs/view/executive-assistant-hybrid-at-experian-4388179945",
     [
        "I'm writing to express my interest in the Executive Assistant position at Experian's Costa Mesa office. The hybrid structure and the opportunity to support leadership at a global data and analytics leader is exactly the kind of professional environment where I can contribute meaningfully from day one.",
        "For the past five years, I've worked in coordination roles that combine executive-level communication with disciplined administrative execution. At Ethan Allen, I managed multiple concurrent client projects, maintained detailed calendars, travel logistics, and documentation, and served as the primary point of contact for high-value clients throughout their engagements. At Vintage Design Inc., I ran front desk operations and coordinated daily between clients, installers, and vendors. These experiences translate directly to executive support: calendar and travel coordination, meeting logistics, polished client communication, and the ability to manage multiple workstreams simultaneously.",
        "My Bachelor of Business Administration from Arizona State University provides the operational foundation for a corporate environment, and my client-facing experience means I'm comfortable representing leadership to internal and external stakeholders with warmth and professionalism. I'm reliable, detail-oriented, and known for anticipating executive needs before they're voiced.",
        "I'd welcome the chance to discuss how I can support your executive team. I'm available at 949-557-9014 or CallieWells17@gmail.com.",
     ]),

    ("28-pimco", "PIMCO", "Administrative Assistant",
     "Dear PIMCO Hiring Team,", "coordinator",
     "https://www.indeed.com/jobs?q=executive+assistant&l=Rancho+Santa+Margarita%2C+CA",
     [
        "I'm writing to apply for the Administrative Assistant position at PIMCO. The opportunity to bring my coordination and client-service experience to a premier global asset management firm is genuinely exciting, and I believe my background makes me a strong fit for the role's travel and logistics responsibilities.",
        "For the past five years, I've coordinated complex, fast-moving workstreams across three organizations. At Ethan Allen, I managed multiple concurrent projects from consultation through delivery - handling calendars, vendor coordination, travel logistics for in-home appointments, and the constant communication required to keep clients, designers, and operations aligned. Before that at Vintage Design Inc., I ran front desk operations, managed scheduling, and coordinated daily across clients, installers, and vendors. These experiences give me the exact skill set PIMCO needs for travel coordination and administrative support at scale.",
        "My Bachelor of Business Administration from Arizona State University provides a natural foundation for a financial services environment, and I'm comfortable handling confidential documents, coordinating complex calendars across time zones, and maintaining the polished professionalism a tier-1 firm requires. I bring strong Microsoft Office proficiency, a proactive approach to anticipating needs, and the kind of reliability that makes executives' lives easier.",
        "I'd welcome the opportunity to discuss how my background can support your team. I'm available at 949-557-9014 or CallieWells17@gmail.com.",
     ]),
]

RESUME_FILES = {
    "coordinator": "callie-wells-resume-coordinator.pdf",
    "design-sales": "callie-wells-resume-design-sales.pdf",
    "design-assistant": "callie-wells-resume-design-assistant.pdf",
}

EMAIL_BODIES = {
    "24-talentpop": """Hi Callie,

BIG DEAL - This is in RSM (your home city)!

APPLY HERE:
https://www.linkedin.com/jobs/view/executive-assistant-to-founders-at-talentpop-4399360832

Company: TalentPop
Role: Executive Assistant to Founders
Location: Rancho Santa Margarita, CA (literally RSM - 0 commute!)
Pay: Not listed (startup founder support, typically $55-80K)
Score: 4.5/5

Steps:
1. Click the link above
2. Hit Apply on LinkedIn
3. Upload the attached PDF (cover letter page 1 + coordinator resume page 2)

The attached PDF has your cover letter (page 1) and coordinator resume (page 2).

NOTE: TalentPop has postings in RSM, Mission Viejo, and Lake Forest - all the same company. The RSM one is the top pick since it's in your city. Your BBA + coordination experience is a direct fit.

- Your Job Search Pipeline""",

    "25-applied-medical": """Hi Callie,

STRONG LOCAL FIT - Applied Medical is in RSM too.

APPLY HERE:
https://www.linkedin.com/jobs/view/executive-assistant-at-applied-medical-4399824498

Company: Applied Medical
Role: Executive Assistant
Location: Rancho Santa Margarita, CA (your home city - no commute!)
Pay: Not listed (Applied Medical EA typically $60-85K + benefits)
Score: 4.4/5

Steps:
1. Click the link above
2. Hit Apply on LinkedIn
3. Upload the attached PDF (cover letter page 1 + coordinator resume page 2)

The attached PDF has your cover letter (page 1) and coordinator resume (page 2).

NOTE: Even though Applied Medical is a medical device company, this EA role is pure admin work (calendars, travel, meetings) - NOT medical. Your BBA + coordination experience is the match, not medical knowledge. They have strong benefits and are a stable local employer.

- Your Job Search Pipeline""",

    "26-berkadia": """Hi Callie,

HIGH PAY - $80-100K Senior Admin role at commercial real estate firm!

APPLY HERE:
https://www.indeed.com/jobs?q=administrative+coordinator&l=Rancho+Santa+Margarita%2C+CA&radius=25

Company: Berkadia
Role: Sr Administrative Assistant
Location: Irvine, CA (~15mi from RSM)
Pay: $80,000 - $100,000 per year
Score: 4.5/5

Steps:
1. Click the link above
2. Find "Berkadia - Sr Administrative Assistant" in the results (Irvine)
3. Hit Apply on Indeed
4. Upload the attached PDF (cover letter page 1 + coordinator resume page 2)

The attached PDF has your cover letter (page 1) and coordinator resume (page 2).

NOTE: The posting says "coordinator between brokers and the team" - that's literally what you did at Ethan Allen (coordinator between designers, vendors, clients). Berkadia is a well-respected commercial real estate firm - Berkshire Hathaway / Jefferies Finance joint venture. The Senior title and $80-100K pay reflects serious responsibility.

- Your Job Search Pipeline""",

    "27-experian": """Hi Callie,

HYBRID ROLE - Global company, flexibility to work from home part of the week.

APPLY HERE:
https://www.linkedin.com/jobs/view/executive-assistant-hybrid-at-experian-4388179945

Company: Experian
Role: Executive Assistant (Hybrid)
Location: Costa Mesa, CA (~25mi from RSM)
Pay: Not listed (Experian EA typically $70-95K + bonus + strong benefits)
Score: 4.3/5

Steps:
1. Click the link above
2. Hit Apply on LinkedIn
3. Upload the attached PDF (cover letter page 1 + coordinator resume page 2)

The attached PDF has your cover letter (page 1) and coordinator resume (page 2).

NOTE: Experian is a global data analytics leader (Fortune 500). Hybrid means you're only in Costa Mesa a few days a week. Excellent benefits package, professional growth path, and your BBA fits the corporate environment. This is a polished EA role supporting senior leadership.

- Your Job Search Pipeline""",

    "28-pimco": """Hi Callie,

TIER-1 FINANCE FIRM - PIMCO is one of the world's premier asset managers.

APPLY HERE:
https://www.indeed.com/jobs?q=executive+assistant+pimco&l=Newport+Beach%2C+CA

Company: PIMCO
Role: Administrative Assistant
Location: Newport Beach, CA (~20mi from RSM)
Pay: Not listed (PIMCO admin typically $65-90K + bonus + excellent benefits)
Score: 4.2/5

Steps:
1. Click the link above (or search "PIMCO administrative assistant" on Indeed)
2. Find the PIMCO posting in Newport Beach
3. Hit Apply on Indeed
4. Upload the attached PDF (cover letter page 1 + coordinator resume page 2)

The attached PDF has your cover letter (page 1) and coordinator resume (page 2).

NOTE: PIMCO is a premier global asset manager - prestige + compensation + benefits. The role focuses on travel coordination (your strength from managing in-home design appointments). Your BBA is a natural fit for a financial services environment. Applying here is a portfolio-builder for your admin career.

- Your Job Search Pipeline""",
}


def send_email(to, subject, body_text, attachment):
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.base import MIMEBase
    from email import encoders

    msg = MIMEMultipart()
    msg.attach(MIMEText(body_text, "plain"))
    with open(attachment, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f'attachment; filename="{os.path.basename(attachment)}"')
    msg.attach(part)
    msg["To"] = to
    msg["Subject"] = subject

    eml = os.path.join(os.path.dirname(__file__), "_outgoing.eml")
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
    return result.returncode == 0, result.stderr[:200]


for slug, company, title, greeting, res_type, url, paras in JOBS:
    cl_pdf = os.path.join(BASE, f"cover-letters/drafts/{slug}.pdf")
    res_pdf = os.path.join(BASE, f"resumes/{RESUME_FILES[res_type]}")
    out_pdf = os.path.join(BASE, f"cover-letters/merged-for-indeed/{slug}-full.pdf")

    _build_cover_letter_pdf(cl_pdf, company, title, greeting, paras,
        LS, SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
        ParagraphStyle, inch, HexColor, TA_LEFT, TA_JUSTIFY)
    print(f"Created: {slug}.pdf")

    writer = PdfWriter()
    for p in PdfReader(cl_pdf).pages: writer.add_page(p)
    for p in PdfReader(res_pdf).pages: writer.add_page(p)
    with open(out_pdf, "wb") as f:
        writer.write(f)
    print(f"Merged: {slug}-full.pdf")

    # Save email body
    body_file = os.path.join(BASE, f"scripts/email-bodies/{slug}.txt")
    with open(body_file, "w", encoding="utf-8") as f:
        f.write(EMAIL_BODIES[slug])

    # Send email
    subject_pay = {"24-talentpop": "RSM Home City", "25-applied-medical": "RSM Home City",
                   "26-berkadia": "80-100K", "27-experian": "Hybrid", "28-pimco": "Tier-1 Finance"}
    subject = f"APPLY HERE: {company} - {title} ({subject_pay[slug]})"
    success, err = send_email("CallieWells17@gmail.com", subject, EMAIL_BODIES[slug], out_pdf)
    if success:
        print(f"  Emailed Callie: {subject}")
    else:
        print(f"  EMAIL FAILED: {err}")

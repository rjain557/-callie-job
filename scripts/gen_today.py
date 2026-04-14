"""Generate cover letter PDFs and merge with resumes for today's 2 leads."""
import sys, os
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
    ("22-south-bay-design-center", "South Bay Design Center", "Design Sales Consultant - Kitchen & Bath",
     "Dear South Bay Design Center Team,", "design-sales", [
        "I'm writing to express my interest in the Design Sales Consultant position at your Kitchen & Bath Showroom. A family-owned design center with 33 years in South Bay remodeling is exactly the kind of established, client-focused environment where I do my best work, and I'd love to bring my design sales expertise to your team.",
        "Over the past three years at Ethan Allen, I built a consultancy practice around the same approach your role describes - building trust, inspiring clients, and closing sales through thoughtful material selection. I earned the 2025 Gold Spirit Award for generating over $800,000 in design sales, and every dollar of that came from relationships and the design conversation rather than aggressive closing techniques. Kitchen and bath renovations are some of the most personal and impactful design decisions a homeowner makes, and I genuinely love helping clients translate their vision into materials and finishes they're excited about.",
        "What draws me to South Bay Design Center is the focus on client experience and the support of an in-house design team. I thrive when I can concentrate on the consultative sales side while collaborating with design experts behind the scenes. My experience at Ethan Allen - curating fabric selections, specifying finishes, and managing the client journey from consultation through delivery - translates directly to the kitchen and bath selection process.",
        "I'd welcome the chance to visit the showroom and discuss how my sales track record could contribute to your continued success. I'm available at 949-557-9014 or CallieWells17@gmail.com.",
     ]),

    ("23-natuzzi-americas", "Natuzzi Americas", "Store Manager (Showroom)",
     "Dear Natuzzi Americas Team,", "design-sales", [
        "I'm writing to express my interest in the Store Manager position at your Costa Mesa showroom. Natuzzi's reputation as Italy's premier design-led furniture brand, combined with your commitment to client experience and design-driven retail, represents exactly the caliber of luxury environment where I've built my strongest results.",
        "For the past three years at Ethan Allen, I ran a high-performing design sales practice that generated over $800,000 in design sales, earning the 2025 Gold Spirit Award for exceptional performance. My success was rooted in three things that directly apply to this role: building meaningful client relationships, maintaining the elevated standards a luxury brand requires, and driving consistent revenue through a consultative approach. I understand the pace and precision that Natuzzi clients expect, and I know how to deliver the client journey that turns browsers into buyers - and buyers into repeat customers.",
        "What excites me about this role is the leadership scope. While my formal title at Ethan Allen was Design Consultant, I functioned as a mentor to newer consultants, took ownership of showroom standards, and built systems for managing my client pipeline that colleagues adopted. I'm ready to step into a formal leadership role at Natuzzi - building and coaching a team, managing P&L, and driving the showroom's performance while maintaining the brand's design integrity.",
        "I'd welcome the opportunity to meet your team and discuss how my sales track record and operational approach could contribute to Natuzzi's continued growth in Orange County. I'm available at 949-557-9014 or CallieWells17@gmail.com.",
     ]),
]

RESUME_FILES = {
    "design-sales": "callie-wells-resume-design-sales.pdf",
    "design-assistant": "callie-wells-resume-design-assistant.pdf",
    "coordinator": "callie-wells-resume-coordinator.pdf",
}

for slug, company, title, greeting, res_type, paras in JOBS:
    cl_path = os.path.join(BASE, f"cover-letters/drafts/{slug}.pdf")
    res_path = os.path.join(BASE, f"resumes/{RESUME_FILES[res_type]}")
    out_path = os.path.join(BASE, f"cover-letters/merged-for-indeed/{slug}-full.pdf")

    _build_cover_letter_pdf(cl_path, company, title, greeting, paras,
        LS, SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
        ParagraphStyle, inch, HexColor, TA_LEFT, TA_JUSTIFY)
    print(f"Created: {slug}.pdf")

    writer = PdfWriter()
    for page in PdfReader(cl_path).pages:
        writer.add_page(page)
    for page in PdfReader(res_path).pages:
        writer.add_page(page)
    with open(out_path, "wb") as f:
        writer.write(f)
    print(f"Merged: {slug}-full.pdf")

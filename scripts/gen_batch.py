"""One-time batch: generate PDFs for jobs 14-20 and merge with resumes."""
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
CL = os.path.join(BASE, "cover-letters", "drafts")
MG = os.path.join(BASE, "cover-letters", "merged-for-indeed")
RS = os.path.join(BASE, "resumes")

JOBS = [
    ("14-express-flooring", "Express Flooring", "In-Home Design Consultant",
     "Dear Express Flooring Hiring Team,", "design-sales",
     ["I'm writing to express my strong interest in the In-Home Design Consultant position at your Irvine location. The in-home consultation model with provided leads mirrors exactly how I've built my career.",
      "For the past three years at Ethan Allen, I earned the 2025 Gold Spirit Award for generating over $800,000 in design sales through in-home consultations, building trust with homeowners, and presenting design solutions they felt genuinely excited about. Flooring is one of the most impactful changes a homeowner can make.",
      "What draws me to Express Flooring is the combination of high earning potential and a consultative sales model. My experience with material and finish selections means I can speak confidently about flooring options from day one.",
      "I'd love to discuss how my track record could contribute to your team. I'm available at 949-557-9014 or CallieWells17@gmail.com."]),

    ("15-waterworks", "Waterworks", "Design Consultant, RH Channel",
     "Dear Waterworks Team,", "design-sales",
     ["I'm applying for the Design Consultant, RH Channel position at your Newport Beach location. Waterworks' reputation as the premier luxury bath and kitchen brand represents exactly where I've built my strongest results.",
      "At Ethan Allen, I spent three years working with discerning clients, earning the 2025 Gold Spirit Award for over $800,000 in design sales by developing deep relationships and guiding clients through curated finish and material selections.",
      "What excites me is the caliber of clientele and depth of product knowledge. I genuinely love matching a client's aesthetic vision with the right materials, and Waterworks' collection is the kind of quality I'm proud to stand behind.",
      "I would welcome the opportunity to visit the showroom and discuss how I can contribute. I'm available at 949-557-9014 or CallieWells17@gmail.com."]),

    ("16-kaleidoscope-supply", "Kaleidoscope Supply Services", "Interior Design Assistant",
     "Dear Kaleidoscope Supply Services Team,", "design-assistant",
     ["I'm applying for the Interior Design Assistant position. My five years of residential interior design experience across three firms have prepared me well for this role.",
      "At Ethan Allen, I delivered personalized design services through consultations, space planning, and curated selections. At Goff Designs, I supported a principal designer with vendor work orders and project documentation. At Vintage Design Inc., I managed front desk operations and client coordination.",
      "I bring creative design sensibility and organizational discipline. I'm experienced with project documentation, vendor coordination, and client communication. While I don't have deep AutoCAD experience, it's listed as beneficial not required, and I'm eager to develop that skill.",
      "I would love to discuss how my experience could support your team. I'm available at 949-557-9014 or CallieWells17@gmail.com."]),

    ("17-farnear-design", "FARNEAR DESIGN", "Assistant Interior Designer",
     "Dear FARNEAR DESIGN Team,", "design-assistant",
     ["I'm excited to apply for the Assistant Interior Designer position at your Laguna Beach studio. As a South Orange County resident, I've been looking for the right boutique firm where I can grow.",
      "Over five years, I've built a foundation in residential design. At Ethan Allen, I ran client consultations and curated fabric and finish selections. At Goff Designs, I worked alongside a principal designer on boutique residential projects.",
      "What draws me to FARNEAR is the collaborative boutique environment. I bring a trained design eye, strong organizational skills, and a detail-driven approach that ensures nothing falls through the cracks.",
      "I'd love to meet and discuss how I could support your projects. I'm available at 949-557-9014 or CallieWells17@gmail.com."]),

    ("19-spf-screens", "SPF Screens & Awnings", "Design Consultant",
     "Dear SPF Screens & Awnings Team,", "design-sales",
     ["I'm applying for the Design Consultant position at your Irvine location. Helping homeowners enhance their outdoor living spaces is a natural extension of my five years in residential design.",
      "At Ethan Allen, I earned the 2025 Gold Spirit Award for over $800,000 in design sales through consultative in-home appointments. I thrive at understanding how clients want to use their spaces and presenting solutions that feel both functional and beautiful.",
      "My experience with space planning, material selection, and managing client relationships from first meeting through completion means I can contribute from day one.",
      "I'd welcome the chance to discuss how my background could support your team. I'm available at 949-557-9014 or CallieWells17@gmail.com."]),

    ("20-mode-renovation", "Mode Renovation LLC", "Permit & Design Coordinator",
     "Dear Mode Renovation Team,", "coordinator",
     ["I'm applying for the Permit & Design Coordinator position. My background in residential design coordination aligns well with what this role requires.",
      "At Ethan Allen, I managed multiple residential projects simultaneously, maintaining detailed documentation and coordinating between clients, vendors, and internal teams. At Vintage Design Inc., I handled front desk operations and served as the daily point of contact between clients, installers, and vendors.",
      "I understand the residential renovation process from the design side and can keep the administrative machinery running smoothly. My BBA from Arizona State University provides additional foundation in project management.",
      "I'd welcome the opportunity to discuss how my experience could support your renovation projects. I'm available at 949-557-9014 or CallieWells17@gmail.com."]),
]

RESUME_FILES = {
    "design-sales": "callie-wells-resume-design-sales.pdf",
    "design-assistant": "callie-wells-resume-design-assistant.pdf",
    "coordinator": "callie-wells-resume-coordinator.pdf",
}

print("Generating cover letter PDFs...")
for slug, company, title, greeting, res_type, paras in JOBS:
    pdf_path = os.path.join(CL, f"{slug}.pdf")
    _build_cover_letter_pdf(pdf_path, company, title, greeting, paras,
        LS, SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
        ParagraphStyle, inch, HexColor, TA_LEFT, TA_JUSTIFY)
    print(f"  {slug}.pdf")

print("\nMerging with resumes...")
for slug, company, title, greeting, res_type, paras in JOBS:
    cl_path = os.path.join(CL, f"{slug}.pdf")
    res_path = os.path.join(RS, RESUME_FILES[res_type])
    out_path = os.path.join(MG, f"{slug}-full.pdf")

    writer = PdfWriter()
    for page in PdfReader(cl_path).pages:
        writer.add_page(page)
    for page in PdfReader(res_path).pages:
        writer.add_page(page)
    with open(out_path, "wb") as f:
        writer.write(f)
    print(f"  {slug}-full.pdf")

print("\nDone!")

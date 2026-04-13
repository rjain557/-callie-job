"""Generate Crossover cover letter PDF and merge with resume."""
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
cl_path = os.path.join(BASE, "cover-letters/drafts/21-crossover-2hl.pdf")
res_path = os.path.join(BASE, "resumes/callie-wells-resume-design-sales.pdf")
out_path = os.path.join(BASE, "cover-letters/merged-for-indeed/21-crossover-2hl-full.pdf")

paragraphs = [
    "I'm writing to express my interest in the Interior Design Specialist position. Your approach to reimagining learning environments - where the physical space is as intentional as the curriculum - is exactly the kind of meaningful design work I want to contribute to.",
    "My background is five years of residential interior design across three firms, most recently three years at Ethan Allen as a Design Consultant where I earned the 2025 Gold Spirit Award for generating over $800,000 in design sales. My daily work involved creating comprehensive design visions for clients - developing mood boards, curating fabric and finish selections, specifying lighting, and laying out spaces that supported how families actually lived. That portfolio of premium residential environments directly matches what your role calls for.",
    "What draws me to 2 Hour Learning is the mission and the design challenge. Designing non-traditional learning environments that support a fundamentally different educational model means every design decision carries weight - material choices, lighting character, and spatial flow all have to serve both the practical needs of students and the emotional experience of learning. I thrive on that kind of intentional, research-informed design work, and my experience managing multiple concurrent projects at Ethan Allen means I can handle the pace of multi-site consistency and rapid refinement cycles.",
    "I'd welcome the chance to discuss how my residential design portfolio and consultative approach could help shape your campus design standards. I'm available at 949-557-9014 or CallieWells17@gmail.com.",
]

_build_cover_letter_pdf(
    cl_path,
    "Crossover / 2 Hour Learning",
    "Interior Design Specialist (Remote)",
    "Dear 2 Hour Learning Team,",
    paragraphs,
    LS, SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
    ParagraphStyle, inch, HexColor, TA_LEFT, TA_JUSTIFY
)
print(f"Created: {cl_path}")

writer = PdfWriter()
for page in PdfReader(cl_path).pages:
    writer.add_page(page)
for page in PdfReader(res_path).pages:
    writer.add_page(page)
with open(out_path, "wb") as f:
    writer.write(f)
print(f"Merged: {out_path}")

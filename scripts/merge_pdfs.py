"""
Merge cover letter + resume into a single PDF per job for Indeed uploads.
"""

from pypdf import PdfReader, PdfWriter
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CL_DIR = os.path.join(BASE, "cover-letters", "drafts")
RES_DIR = os.path.join(BASE, "resumes")
OUT_DIR = os.path.join(BASE, "cover-letters", "merged-for-indeed")
os.makedirs(OUT_DIR, exist_ok=True)

# Map: (cover letter filename, resume filename, output name)
JOBS = [
    ("01-shugarmans-bath.pdf", "callie-wells-resume-design-sales.pdf", "01-shugarmans-bath-full.pdf"),
    ("02-orange-coast-interior-design.pdf", "callie-wells-resume-design-assistant.pdf", "02-orange-coast-interior-design-full.pdf"),
    ("03-manifested-interiors.pdf", "callie-wells-resume-design-sales.pdf", "03-manifested-interiors-full.pdf"),
    ("04-dreamcatcher-remodeling.pdf", "callie-wells-resume-design-sales.pdf", "04-dreamcatcher-remodeling-full.pdf"),
    ("05-debra-lauren-design.pdf", "callie-wells-resume-design-assistant.pdf", "05-debra-lauren-design-full.pdf"),
    ("06-first-home-staging.pdf", "callie-wells-resume-design-assistant.pdf", "06-first-home-staging-full.pdf"),
    ("07-stage-to-amaze.pdf", "callie-wells-resume-design-assistant.pdf", "07-stage-to-amaze-full.pdf"),
    ("08-taylor-design.pdf", "callie-wells-resume-coordinator.pdf", "08-taylor-design-full.pdf"),
    ("09-uc-irvine.pdf", "callie-wells-resume-coordinator.pdf", "09-uc-irvine-full.pdf"),
    ("10-visual-comfort.pdf", "callie-wells-resume-design-sales.pdf", "10-visual-comfort-full.pdf"),
]

print("Merging cover letters + resumes for Indeed uploads...")
for cl_file, res_file, out_file in JOBS:
    writer = PdfWriter()

    cl_path = os.path.join(CL_DIR, cl_file)
    res_path = os.path.join(RES_DIR, res_file)
    out_path = os.path.join(OUT_DIR, out_file)

    for page in PdfReader(cl_path).pages:
        writer.add_page(page)
    for page in PdfReader(res_path).pages:
        writer.add_page(page)

    with open(out_path, "wb") as f:
        writer.write(f)

    print(f"  {out_file} (2 pages)")

print(f"\nAll merged PDFs saved to: {OUT_DIR}")
print("Upload these to Indeed - each is cover letter (page 1) + resume (page 2)")

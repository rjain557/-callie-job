"""
Generate professional PDF cover letters and tailored resumes for Callie Wells.
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Frame, PageTemplate,
    BaseDocTemplate
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
import os

# ── Colors ──
NAVY = HexColor("#1a365d")
DARK_GRAY = HexColor("#2d3748")
MED_GRAY = HexColor("#4a5568")
LIGHT_GRAY = HexColor("#a0aec0")
ACCENT = HexColor("#2b6cb0")
WHITE = HexColor("#ffffff")

# ── Styles ──
def get_styles():
    return {
        "name": ParagraphStyle(
            "Name", fontName="Helvetica-Bold", fontSize=20, leading=24,
            textColor=NAVY, alignment=TA_LEFT, spaceAfter=2
        ),
        "contact": ParagraphStyle(
            "Contact", fontName="Helvetica", fontSize=9, leading=13,
            textColor=MED_GRAY, alignment=TA_LEFT, spaceAfter=0
        ),
        "section_head": ParagraphStyle(
            "SectionHead", fontName="Helvetica-Bold", fontSize=11, leading=14,
            textColor=NAVY, spaceBefore=14, spaceAfter=4,
            borderWidth=0, borderPadding=0
        ),
        "body": ParagraphStyle(
            "Body", fontName="Helvetica", fontSize=10.5, leading=15,
            textColor=DARK_GRAY, alignment=TA_JUSTIFY, spaceAfter=8
        ),
        "greeting": ParagraphStyle(
            "Greeting", fontName="Helvetica", fontSize=10.5, leading=15,
            textColor=DARK_GRAY, spaceAfter=8, spaceBefore=16
        ),
        "signoff": ParagraphStyle(
            "Signoff", fontName="Helvetica", fontSize=10.5, leading=15,
            textColor=DARK_GRAY, spaceBefore=8, spaceAfter=2
        ),
        "sign_name": ParagraphStyle(
            "SignName", fontName="Helvetica-Bold", fontSize=10.5, leading=15,
            textColor=NAVY, spaceAfter=1
        ),
        "sign_detail": ParagraphStyle(
            "SignDetail", fontName="Helvetica", fontSize=9, leading=12,
            textColor=MED_GRAY
        ),
        # Resume styles
        "res_name": ParagraphStyle(
            "ResName", fontName="Helvetica-Bold", fontSize=18, leading=20,
            textColor=NAVY, alignment=TA_CENTER, spaceAfter=2
        ),
        "res_contact": ParagraphStyle(
            "ResContact", fontName="Helvetica", fontSize=8.5, leading=11,
            textColor=MED_GRAY, alignment=TA_CENTER, spaceAfter=1
        ),
        "res_summary": ParagraphStyle(
            "ResSummary", fontName="Helvetica", fontSize=9, leading=12,
            textColor=DARK_GRAY, alignment=TA_JUSTIFY, spaceAfter=2
        ),
        "res_section": ParagraphStyle(
            "ResSection", fontName="Helvetica-Bold", fontSize=10, leading=13,
            textColor=NAVY, spaceBefore=6, spaceAfter=2,
        ),
        "res_job_title": ParagraphStyle(
            "ResJobTitle", fontName="Helvetica-Bold", fontSize=9.5, leading=12,
            textColor=DARK_GRAY, spaceAfter=0
        ),
        "res_company": ParagraphStyle(
            "ResCompany", fontName="Helvetica-Oblique", fontSize=9, leading=11,
            textColor=MED_GRAY, spaceAfter=2
        ),
        "res_bullet": ParagraphStyle(
            "ResBullet", fontName="Helvetica", fontSize=9, leading=12,
            textColor=DARK_GRAY, leftIndent=14, bulletIndent=4,
            spaceAfter=1
        ),
        "res_competency": ParagraphStyle(
            "ResCompetency", fontName="Helvetica", fontSize=9, leading=12,
            textColor=DARK_GRAY, spaceAfter=1
        ),
    }


def build_cover_letter(output_path, company, title, greeting, paragraphs):
    """Build a professional cover letter PDF."""
    s = get_styles()
    doc = SimpleDocTemplate(
        output_path, pagesize=letter,
        leftMargin=1*inch, rightMargin=1*inch,
        topMargin=0.9*inch, bottomMargin=0.8*inch
    )

    story = []

    # Header
    story.append(Paragraph("Callie Nichole Wells", s["name"]))
    story.append(Paragraph(
        "5 Caladium, Rancho Santa Margarita, CA 92688", s["contact"]
    ))
    story.append(Paragraph(
        "949-557-9014 &nbsp;|&nbsp; CallieWells17@gmail.com &nbsp;|&nbsp; linkedin.com/in/callie-wells17",
        s["contact"]
    ))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(
        width="100%", thickness=1.5, color=ACCENT,
        spaceAfter=12, spaceBefore=4
    ))

    # Date and addressee
    story.append(Paragraph("April 7, 2026", s["body"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph(f"Re: {title}", s["section_head"]))
    story.append(Spacer(1, 2))

    # Greeting
    story.append(Paragraph(greeting, s["greeting"]))

    # Body paragraphs
    for para in paragraphs:
        story.append(Paragraph(para, s["body"]))

    # Sign-off
    story.append(Spacer(1, 4))
    story.append(Paragraph("Warm regards,", s["signoff"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Callie Nichole Wells", s["sign_name"]))
    story.append(Paragraph("949-557-9014", s["sign_detail"]))
    story.append(Paragraph("CallieWells17@gmail.com", s["sign_detail"]))
    story.append(Paragraph("linkedin.com/in/callie-wells17", s["sign_detail"]))

    doc.build(story)
    print(f"  Created: {output_path}")


def build_resume(output_path, variant, summary, competencies, experience_order):
    """Build a tailored resume PDF."""
    s = get_styles()
    doc = SimpleDocTemplate(
        output_path, pagesize=letter,
        leftMargin=0.6*inch, rightMargin=0.6*inch,
        topMargin=0.5*inch, bottomMargin=0.4*inch
    )

    story = []

    # Header
    story.append(Paragraph("CALLIE NICHOLE WELLS", s["res_name"]))
    story.append(Paragraph(
        "5 Caladium &nbsp;|&nbsp; Rancho Santa Margarita, CA 92688",
        s["res_contact"]
    ))
    story.append(Paragraph(
        "949-557-9014 &nbsp;|&nbsp; CallieWells17@gmail.com &nbsp;|&nbsp; linkedin.com/in/callie-wells17",
        s["res_contact"]
    ))
    story.append(Spacer(1, 2))
    story.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT, spaceAfter=4))

    # Summary
    story.append(Paragraph("PROFESSIONAL SUMMARY", s["res_section"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=LIGHT_GRAY, spaceAfter=3))
    story.append(Paragraph(summary, s["res_summary"]))

    # Core Competencies
    story.append(Paragraph("CORE COMPETENCIES", s["res_section"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=LIGHT_GRAY, spaceAfter=3))
    comp_text = " &nbsp;&bull;&nbsp; ".join(competencies)
    story.append(Paragraph(comp_text, s["res_competency"]))

    # Experience
    story.append(Paragraph("PROFESSIONAL EXPERIENCE", s["res_section"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=LIGHT_GRAY, spaceAfter=3))

    jobs = {
        "ethan_allen": {
            "title": "Interior Design Consultant",
            "company": "Ethan Allen &nbsp;|&nbsp; February 2023 \u2013 February 2026",
            "bullets": [
                "Generated over <b>$800,000 in design sales</b>, earning the 2025 Gold Spirit Award",
                "Delivered personalized residential design services through in-home consultations, space planning, and curated fabric and finish selections",
                "Managed multiple client projects simultaneously from concept through order placement and delivery",
                "Maintained consistent client communication to build long-term relationships and repeat business",
                "Developed customized design solutions including furniture layouts and material selections",
            ]
        },
        "vintage": {
            "title": "Design Coordinator",
            "company": "Vintage Design Inc. &nbsp;|&nbsp; 2021 \u2013 2022",
            "bullets": [
                "Served as primary front desk contact for clients, installers, and vendors",
                "Scheduled design consultations and managed daily office operations",
                "Ordered and tracked office and warehouse supplies",
                "Coordinated client appointments and supported order documentation",
            ]
        },
        "goff": {
            "title": "Interior Design Assistant",
            "company": "Goff Designs &nbsp;|&nbsp; 2019 \u2013 2020",
            "bullets": [
                "Supported principal designer in executing residential interior design projects",
                "Created and processed vendor work orders and tracked order details",
                "Coordinated project documentation and maintained organized fabric and finish samples",
                "Prepared client-facing presentations to ensure projects progressed efficiently",
                "Supported social media content management to enhance brand visibility",
            ]
        }
    }

    for job_key in experience_order:
        job = jobs[job_key]
        story.append(Paragraph(job["title"], s["res_job_title"]))
        story.append(Paragraph(job["company"], s["res_company"]))
        for bullet in job["bullets"]:
            story.append(Paragraph(f"\u2022 &nbsp;{bullet}", s["res_bullet"]))
        story.append(Spacer(1, 2))

    # Education
    story.append(Paragraph("EDUCATION", s["res_section"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=LIGHT_GRAY, spaceAfter=3))
    story.append(Paragraph(
        "<b>Bachelor of Business Administration</b>", s["res_job_title"]
    ))
    story.append(Paragraph(
        "Arizona State University, Tempe, AZ &nbsp;|&nbsp; 2019", s["res_company"]
    ))

    doc.build(story)
    print(f"  Created: {output_path}")


def main():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cl_dir = os.path.join(base, "cover-letters", "drafts")
    res_dir = os.path.join(base, "resumes")
    os.makedirs(cl_dir, exist_ok=True)
    os.makedirs(res_dir, exist_ok=True)

    print("Generating cover letter PDFs...")

    # ── 1. Shugarman's Bath ──
    build_cover_letter(
        os.path.join(cl_dir, "01-shugarmans-bath.pdf"),
        "Shugarman's Bath", "In-Home Design Consultant",
        "Dear Shugarman's Bath Hiring Team,",
        [
            "I'm reaching out to express my interest in the In-Home Design Consultant position with your Orange County team. Your company's reputation as a top-rated bath remodeling company and your commitment to quality craftsmanship genuinely resonate with me, and I'd love the opportunity to bring my design and sales expertise to your growing team.",
            "Over the past three years at Ethan Allen, I built a practice around in-home and in-studio consultations, helping clients envision and execute residential design transformations. I earned the 2025 Gold Spirit Award for generating over $800,000 in design sales, and much of that success came from the same skill set your role calls for: sitting with homeowners, building trust, understanding their needs, and presenting design solutions that feel personal and exciting. My experience with finish and material selections translates directly to guiding clients through bath renovation options with confidence.",
            "What draws me to Shugarman's Bath is the focus on a consultative, design-forward sales process with pre-set appointments. I thrive in environments where I can focus on the client relationship and the design conversation rather than cold prospecting. My background in managing projects from concept through completion means I understand how to set expectations, communicate clearly, and ensure a seamless client experience from the first meeting forward.",
            "I would welcome the chance to discuss how my experience could contribute to your Orange County expansion. I'm available at your convenience and can be reached at 949-557-9014 or CallieWells17@gmail.com.",
        ]
    )

    # ── 2. Orange Coast Interior Design ──
    build_cover_letter(
        os.path.join(cl_dir, "02-orange-coast-interior-design.pdf"),
        "Orange Coast Interior Design", "Interior Designer Assistant",
        "Dear Orange Coast Interior Design Team,",
        [
            "I'm writing to express my interest in the Interior Designer Assistant position. Your studio's approach to creating spaces that truly reflect each client's personality aligns closely with the design philosophy I've built my career around, and I'd be excited to contribute to your team.",
            "My background spans five years in residential interior design across three firms, including three years as a Design Consultant at Ethan Allen, where I delivered personalized design services through in-home consultations, space planning, and curated fabric and finish selections. Prior to that, I supported principal designers at Goff Designs and coordinated client operations at Vintage Design Inc., giving me a well-rounded perspective on how successful design projects run from initial concept through final installation.",
            "What I'd bring to your studio is a combination of strong aesthetic judgment and the operational discipline to keep projects organized behind the scenes. I'm experienced in managing project documentation, coordinating with vendors, maintaining material samples, and ensuring consistent client communication throughout the design process. I genuinely enjoy the support side of design work as much as the creative side, and I believe that's what makes a great assistant invaluable to a lead designer.",
            "I would love the opportunity to learn more about your current projects and discuss how I could support your studio's continued success. Please feel free to reach me at 949-557-9014 or CallieWells17@gmail.com.",
        ]
    )

    # ── 3. Manifested Interiors ──
    build_cover_letter(
        os.path.join(cl_dir, "03-manifested-interiors.pdf"),
        "Manifested Interiors", "Interior Designer / Project Manager",
        "Dear Manifested Interiors Team,",
        [
            "I'm excited to apply for the Interior Designer / Project Manager position at your studio. As a South Orange County resident with a deep passion for residential design, I've admired the high-end work coming out of Manifested Interiors, and I'd welcome the opportunity to bring my combined design and project management experience to your team.",
            "For the past three years at Ethan Allen, I managed multiple residential design projects simultaneously from initial consultation through order placement and delivery, while generating over $800,000 in sales. My role required balancing creative design work with the organizational rigor of tracking timelines, managing vendor relationships, and maintaining detailed project documentation. Before Ethan Allen, I supported a principal designer at Goff Designs, where I handled vendor work orders, project documentation, and client-facing presentations for boutique residential projects.",
            "The hybrid nature of this role is what excites me most. I've found that my greatest strength lies in bridging the gap between the creative vision and the structured execution that brings it to life. I'm comfortable presenting design concepts to clients, and equally comfortable managing the behind-the-scenes details that keep a project on track and on budget. That dual perspective has been central to my career and something I'd love to bring to a high-end studio like yours.",
            "I'd welcome the chance to meet and discuss how I could contribute to your studio. I'm available at 949-557-9014 or CallieWells17@gmail.com.",
        ]
    )

    # ── 4. Dreamcatcher Remodeling ──
    build_cover_letter(
        os.path.join(cl_dir, "04-dreamcatcher-remodeling.pdf"),
        "Dreamcatcher Remodeling", "Design Consultant",
        "Dear Dreamcatcher Remodeling Hiring Team,",
        [
            "I'm writing to express my interest in the Design Consultant position. With nearly 40 years of remodeling expertise in Orange County, Dreamcatcher has built the kind of reputation that makes this an opportunity I'm genuinely excited about.",
            "My career has been built around helping homeowners transform their living spaces through thoughtful, personalized design. At Ethan Allen, I spent three years conducting in-home and in-studio consultations, working closely with clients on space planning, finish selections, and furniture layouts. I earned the 2025 Gold Spirit Award for over $800,000 in design sales, a result of building trust with clients and guiding them through decisions that felt right for their homes and their lives. That consultative approach translates naturally to remodeling, where the design conversation is even more personal and impactful.",
            "What draws me to this role is the opportunity to work with clients at the beginning of their home transformation journey. I understand how to assess a homeowner's needs, present design solutions that address both function and aesthetics, and manage the communication and expectations that keep a project running smoothly. My experience coordinating with vendors and managing project documentation from concept through delivery means I'm prepared to support the full lifecycle of a remodeling consultation.",
            "I would love the opportunity to discuss how my background could support Dreamcatcher's continued success. I'm available at 949-557-9014 or CallieWells17@gmail.com.",
        ]
    )

    # ── 5. Debra Lauren Design ──
    build_cover_letter(
        os.path.join(cl_dir, "05-debra-lauren-design.pdf"),
        "Debra Lauren Design", "Home Stager",
        "Dear Debra Lauren Design Team,",
        [
            "I'm reaching out to express my interest in the Home Stager position. As Orange County's top-rated staging company, Debra Lauren Design represents exactly the kind of quality-driven, design-focused environment where I know I can make a meaningful contribution.",
            "My background is in residential interior design, with five years of experience across three design firms including Ethan Allen, Goff Designs, and Vintage Design Inc. While my recent work has focused on client-facing design consultations and sales, the core of what I do every day translates directly to staging: space planning, furniture layout, finish and fabric selection, and creating rooms that feel inviting and intentional. I have a trained eye for how a space should look and flow, and I understand the emotional impact that thoughtful design has on a buyer's first impression.",
            "What excites me about staging is the pace and the impact. I love the idea of walking into a space and quickly transforming it into something that helps someone see their future home. My experience managing multiple client projects simultaneously at Ethan Allen, along with the organizational skills I developed coordinating vendors and tracking project details, means I'm prepared for the fast-moving, multi-site nature of staging work.",
            "I would be happy to discuss how my design background and work ethic could add value to your team. Please feel free to reach me at 949-557-9014 or CallieWells17@gmail.com.",
        ]
    )

    # ── 6. First Home Staging ──
    build_cover_letter(
        os.path.join(cl_dir, "06-first-home-staging.pdf"),
        "First Home Staging", "Home Stager",
        "Dear First Home Staging Team,",
        [
            "I'm writing to express my interest in the Home Stager position with your team. Having served Orange County since 2016, First Home Staging has the kind of established presence and commitment to quality that I'd be proud to be part of.",
            "I bring five years of residential interior design experience, most recently as a Design Consultant at Ethan Allen, where I specialized in space planning, furniture layouts, and curated finish selections for homeowners throughout Orange County. My design eye has been shaped by working with hundreds of clients across diverse styles and budgets, and I understand instinctively how to arrange a space so it feels both aspirational and welcoming. That instinct is exactly what makes staged homes sell.",
            "Beyond the creative side, I'm organized, reliable, and comfortable with the physical, fast-paced nature of staging work. I've managed multiple concurrent projects with tight timelines, coordinated vendor logistics, and maintained quality standards across every detail. I have a valid driver's license, reliable transportation, and I'm ready to hit the ground running across your Orange County job sites.",
            "I'd love to discuss how I can contribute to your team's continued success. I can be reached at 949-557-9014 or CallieWells17@gmail.com.",
        ]
    )

    # ── 7. Stage to Amaze ──
    build_cover_letter(
        os.path.join(cl_dir, "07-stage-to-amaze.pdf"),
        "Stage to Amaze Inc.", "Home Stager",
        "Dear Stage to Amaze Team,",
        [
            "I'm excited to apply for the Home Stager position as your team continues to grow. The energy of a company that's expanding is something I find genuinely motivating, and I'd love to bring my residential design experience to help fuel that growth.",
            "Over the past five years, I've worked across three interior design firms, most recently spending three years at Ethan Allen as a Design Consultant. My daily work involved space planning, furniture layout, and helping clients select finishes and fabrics that transformed their homes. I earned the 2025 Gold Spirit Award for generating over $800,000 in sales, but the part of the work I loved most was the creative challenge of walking into a space and seeing its potential. That's exactly the skill that drives great staging.",
            "I'm energetic, detail-oriented, and comfortable managing multiple projects across different locations. I thrive in collaborative team environments and bring a positive, hands-on attitude to every project. My organizational skills, developed through years of coordinating vendors, tracking timelines, and managing client documentation, ensure that nothing falls through the cracks.",
            "I'd welcome the opportunity to meet your team and learn more about how I can contribute to Stage to Amaze's growth. Please reach me at 949-557-9014 or CallieWells17@gmail.com.",
        ]
    )

    # ── 8. Taylor Design ──
    build_cover_letter(
        os.path.join(cl_dir, "08-taylor-design.pdf"),
        "Taylor Design", "Project Coordinator",
        "Dear Taylor Design Hiring Team,",
        [
            "I'm writing to apply for the Project Coordinator position at your Orange County office. Taylor Design's reputation as a Best Architectural Firm To Work For, combined with your employee-owned model, speaks to the kind of team-oriented, quality-focused culture where I do my best work.",
            "While my background is in residential interior design rather than architecture, the project coordination skills I've developed are directly transferable. At Ethan Allen, I managed multiple design projects simultaneously from initial client consultation through final delivery, maintaining detailed documentation, tracking timelines, and coordinating between clients, vendors, and internal teams. Before that, at Goff Designs and Vintage Design Inc., I supported designers by processing vendor work orders, managing project documentation, and coordinating appointments and logistics.",
            "What I'd bring to Taylor Design is strong organizational discipline paired with a genuine understanding of the design process. I know how to keep projects moving forward by anticipating needs, catching details before they become problems, and communicating clearly with every stakeholder. My Bachelor of Business Administration from Arizona State University gives me an additional foundation in the operational and business side of project management.",
            "I'm drawn to the collaborative, award-winning environment at Taylor Design and would welcome the chance to contribute to your team. I'm available at 949-557-9014 or CallieWells17@gmail.com.",
        ]
    )

    # ── 9. UC Irvine ──
    build_cover_letter(
        os.path.join(cl_dir, "09-uc-irvine.pdf"),
        "UC Irvine", "Events & Administrative Coordinator",
        "Dear UC Irvine Hiring Committee,",
        [
            "I'm writing to apply for the Events & Administrative Coordinator position. The opportunity to bring my organizational and client-facing experience to a world-class institution like UC Irvine is genuinely exciting, and I believe my background makes me a strong fit for this role.",
            "For the past five years, I've worked in roles that blend high-touch client service with structured administrative coordination. At Ethan Allen, I managed multiple concurrent projects, maintained detailed calendars and documentation, and served as the primary point of contact for clients throughout their design experience. Prior to that, at Vintage Design Inc., I served as the front desk contact for clients, installers, and vendors, scheduling consultations, managing office supplies, and ensuring daily operations ran smoothly.",
            "These experiences have given me a practical skill set that maps directly to events and administrative coordination: calendar and deadline management, cross-functional communication, document organization, vendor coordination, and the ability to keep multiple workstreams moving simultaneously without dropping details. I'm comfortable being the person who keeps everything organized behind the scenes while also being a warm, professional first point of contact.",
            "I hold a Bachelor of Business Administration from Arizona State University, and I'm eager to apply both my education and professional experience in a university setting that values collaboration and excellence. I'd welcome the opportunity to discuss how I can contribute to your team. Please feel free to reach me at 949-557-9014 or CallieWells17@gmail.com.",
        ]
    )

    # ── 10. Visual Comfort ──
    build_cover_letter(
        os.path.join(cl_dir, "10-visual-comfort.pdf"),
        "Visual Comfort & Co", "Showroom Manager",
        "Dear Visual Comfort & Co Hiring Team,",
        [
            "I'm writing to express my interest in the Showroom Manager position at your Laguna Design Center location. Visual Comfort's standing as a leader in luxury lighting and home furnishings, combined with the trade-focused environment of the Laguna Design Center, represents exactly the kind of design-industry role where I can bring immediate value.",
            "Over the past three years at Ethan Allen, I built a design consultancy practice that generated over $800,000 in sales, earning the 2025 Gold Spirit Award. My success was rooted in building lasting relationships with clients and design professionals, providing knowledgeable guidance on product selections, and maintaining the kind of elevated, organized showroom experience that luxury brands require. I understand the language of the design trade and the expectations of the interior designers and clients who visit a showroom like yours.",
            "What excites me about this role is the leadership opportunity. Throughout my career, I've naturally gravitated toward operational coordination \u2014 at Vintage Design Inc., I managed front desk operations, scheduling, and supply ordering, and at Ethan Allen, I developed systems for managing my client pipeline and project workflow that kept everything running efficiently. I'm confident in my ability to build and lead a sales team while maintaining the high standards Visual Comfort is known for.",
            "I would welcome the opportunity to discuss how my sales track record and operational experience could contribute to the success of your Laguna Niguel showroom. I'm available at 949-557-9014 or CallieWells17@gmail.com.",
        ]
    )

    # ── RESUMES ──
    print("\nGenerating tailored resume PDFs...")

    # Resume 1: Design/Sales
    build_resume(
        os.path.join(res_dir, "callie-wells-resume-design-sales.pdf"),
        "Design & Sales",
        "Results-driven Interior Design Consultant with five years of residential design experience and a proven track record of generating over $800,000 in design sales. Combines deep expertise in client consultations, space planning, and material selections with strong sales acumen and relationship-building skills. Recognized with the 2025 Gold Spirit Award for exceptional performance. Equally comfortable presenting design solutions in-home as managing projects from concept through completion.",
        [
            "In-Home & In-Studio Client Consultations",
            "Residential Space Planning & Design",
            "Fabric, Finish & Material Selection",
            "Consultative Sales & Revenue Generation",
            "Client Relationship Management",
            "Project Lifecycle Management",
            "Vendor Coordination",
            "Cross-Functional Communication",
        ],
        ["ethan_allen", "goff", "vintage"]
    )

    # Resume 2: Design Assistant/Staging
    build_resume(
        os.path.join(res_dir, "callie-wells-resume-design-assistant.pdf"),
        "Design Assistant & Staging",
        "Detail-oriented Interior Design professional with five years of hands-on residential design experience across three firms. Skilled in space planning, furniture layout, fabric and finish curation, and vendor coordination. Brings a trained aesthetic eye paired with strong organizational discipline to keep projects running smoothly from concept through installation. Experienced in supporting lead designers, managing project documentation, and maintaining quality standards across multiple concurrent projects.",
        [
            "Residential Space Planning & Layout",
            "Fabric & Finish Curation",
            "Vendor Work Order Processing",
            "Project Documentation & Organization",
            "Client Communication & Scheduling",
            "Material Sample Management",
            "Quality Control & Detail Execution",
            "Social Media Content Support",
        ],
        ["ethan_allen", "goff", "vintage"]
    )

    # Resume 3: Admin/Coordinator
    build_resume(
        os.path.join(res_dir, "callie-wells-resume-coordinator.pdf"),
        "Administrative & Project Coordinator",
        "Organized and proactive professional with five years of experience blending high-touch client service with structured administrative and project coordination. Proven ability to manage multiple concurrent projects, maintain detailed documentation, and serve as a reliable point of contact across clients, vendors, and internal teams. Holds a Bachelor of Business Administration and brings operational discipline shaped by real-world experience in fast-paced, client-facing environments.",
        [
            "Calendar & Deadline Management",
            "Project Coordination & Tracking",
            "Document & Database Management",
            "Client Consultation & Scheduling",
            "Vendor & Supplier Coordination",
            "Cross-Functional Communication",
            "Office Operations & Supply Management",
            "Detail-Driven Execution & Quality Control",
        ],
        ["ethan_allen", "vintage", "goff"]
    )

    print("\nAll PDFs generated successfully!")
    print(f"Cover letters: {cl_dir}")
    print(f"Resumes: {res_dir}")


if __name__ == "__main__":
    main()

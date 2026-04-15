# Pipeline Lessons Learned

> This file is READ at the start of every pipeline run and UPDATED at the end.
> Append new lessons, don't overwrite. Keep entries dated and concise.

## How to use this file

**At the start of every pipeline run:**
1. Read this entire file
2. Apply all active lessons to the current run (new keywords, excluded patterns, search techniques)
3. Skip lessons marked [OBSOLETE]

**At the end of every pipeline run:**
1. Add new lessons discovered during the run under the appropriate section
2. Use format: `- YYYY-MM-DD: <lesson> — <why/context>`
3. Never delete lessons — mark them [OBSOLETE] with reason if no longer valid

---

## Search Keywords That Work

Keywords that have surfaced qualifying leads (>=3.5 score):
- 2026-04-07: "interior design consultant" — baseline, 10 hits initial pipeline
- 2026-04-09: "in-home design consultant" — found Tailored Closet (4.6 match)
- 2026-04-10: "showroom manager design" — found Waterworks (4.5 match)
- 2026-04-13: LinkedIn `f_WT=2` (remote filter) — found Crossover/2HL (4.0 match)
- 2026-04-14: "design consultant remodeling" — found South Bay Design Center (4.6)
- 2026-04-14: Generic LinkedIn showroom search with company filter — found Natuzzi (4.2)
- 2026-04-14: Kitchen & Bath Showroom roles consistently high-scoring — prioritize these
- 2026-04-14: ADDED: "administrative assistant" / "executive assistant" at 25mi radius — pure admin roles leveraging Callie's BBA + coordination experience. Tight radius because admin work requires short commute. NOTE: different from "administrative coordinator design" (which failed) — this is pure admin, not design-adjacent

## Search Keywords That Don't Work

Wasted queries (0 qualifying in 7+ days):
- 2026-04-13: "e-design interior" — no results on LinkedIn remote
- 2026-04-13: "online interior designer" — returns mostly architects (software engineers mislabeled)
- 2026-04-12: "administrative coordinator design" — returns non-design admin roles

## Companies to Investigate

Companies that posted multiple roles (track their careers pages):
- 2026-04-13: Crossover / Trilogy posts many remote design roles under "2 Hour Learning" — worth watching their LinkedIn
- 2026-04-10: LPA Inc posts regularly for interior design coordinators in Irvine
- 2026-04-14: Natuzzi, Restoration Hardware, Williams-Sonoma periodically post showroom roles

## Exclusion Patterns (learned over time)

Patterns to auto-reject before scoring:
- 2026-04-07: Any posting mentioning AutoCAD or Revit (even "preferred") — Callie doesn't have these skills
- 2026-04-10: All Williams-Sonoma "Lead Stock Key Holder" — retail stocker role, not design
- 2026-04-10: Keller Williams real estate agents — excluded from home staging searches
- 2026-04-10: Hyundai/Mazda/Kia "interior designer" — automotive design, not residential
- 2026-04-11: LinkedIn showroom manager returns many bank/AWS/automotive — need to filter by industry
- 2026-04-13: Contractor Staffing Source "drafter" roles — always CAD-heavy
- 2026-04-14: North South Consulting, Concourse Federal Group, VW International — all VA/federal contracts requiring CAD

## Salary Learnings

- 2026-04-12: San Diego postings at $18-24/hr are genuinely low-end for OC comparison (consider filtering by min_salary for SD metro)
- 2026-04-13: Remote interior design $100K+ is achievable (Crossover/2HL) but often 1099
- 2026-04-14: Natuzzi Store Manager $95-105K is at the top of local luxury brand scale

## Remote Role Red Flags

Things to ALWAYS warn Callie about in the kit email:
- 2026-04-13: Crossover = 40hr weeks with screen recording, 1099 contractor, high churn
- 2026-04-13: "Remote with 50-70% travel" isn't really remote — travel paid but still extensive
- 2026-04-14: Staples Remote Interior Designer listed "CET, AutoCAD, CAP 2020" — commercial contract furniture roles typically require CAD even if "design-focused" in title
- 2026-04-14: Any federal/VA healthcare design role (Concourse Federal, North South Consulting, VW International) REQUIRES AutoCAD+Revit+NCIDQ — auto-exclude these keywords: "VA", "federal", "healthcare design", "LPTA"

## Pipeline Process Improvements

- 2026-04-11: Cron session-only — needs refreshing every 7 days
- 2026-04-11: gws `+send --body` truncates multiline — must use `send_email_raw.py` with MIME upload
- 2026-04-11: Emails to Callie MUST have direct job URL on its own line after "APPLY HERE:"
- 2026-04-12: ZipRecruiter, Glassdoor, Coroflot return 403 on WebFetch — skip these boards
- 2026-04-12: Houzz is a services directory, not jobs — remove from scanning
- 2026-04-12: ASID career center returns 404 — URL changed or requires auth
- 2026-04-13: LinkedIn "home staging" search returns mostly real estate agents — add stronger negative filter or use "home stager" instead
- 2026-04-14: Indeed often shows only one detail-view per WebFetch — may need to parse the jobs list differently in future
- 2026-04-14: gws OAuth token expires periodically (`invalid_grant: Token has been expired or revoked`). FIX: user must run `gws auth login` interactively in a terminal to re-authenticate. Script CANNOT refresh token automatically — requires browser flow. When this happens: PDFs/cover letters are still generated, just emails fail. Commit everything, flag the auth issue, re-send emails once user refreshes.
- 2026-04-14: gws MUST authenticate with `CallieWells17@gmail.com`, NEVER with rjain@technijian.com. Emails to companies need to appear from Callie, not from rjain's work account. Saved to memory: project_gws_account.md
- 2026-04-14: Crossover / 2 Hour Learning posts the SAME remote role under different city labels (Phoenix/Charlotte/Orlando/Houston/Austin/Atlanta/NY). It's the same job - applying to multiples is spam. Once Callie has applied to one Crossover 2HL role, SKIP all future Crossover 2HL postings until status resolves. Auto-dedupe by company name alone, not title+city.
- 2026-04-14: MISS: Applied Berkadia Sr Admin Assistant (4.5) but it's a BAD FIT. "Senior" titles in admin domain require 5+ yrs pure admin experience. Callie has only ~2 yrs pure admin (Vintage Design Coordinator front desk). She has 5 yrs DESIGN experience, not 5 yrs admin. Must not conflate "5 yrs design-adjacent" with "5 yrs admin". See profile.yml experience section.
- 2026-04-14: NEW FIT RULE: Before scoring, check YoE required vs Callie's YoE in that SPECIFIC domain (design vs admin vs mgmt). If gap > 4 yrs, SKIP. If gap 3-4 yrs, flag as "stretch" in Callie email. Domain-specific YoE: interior_design=5, design_sales=3, admin_coordination=2, people_management=0.
- 2026-04-14: Auto-flag these as poor fit: "Senior Administrative Assistant", "Sr. Executive Assistant", "Director of Design", "VP Design", "Chief Design Officer". Titles with "Senior"/"Sr"/"Lead" require domain-specific 5+ yrs.

## New Scanning Ideas to Try

Ideas queued for future runs (add when discovered, check off when tried):
- [ ] Search specific design brand careers pages directly (Crate&Barrel, RH, Arhaus, Ballard Designs)
- [ ] Search "Kitchen & Bath" as separate category — it's a real niche
- [ ] Search "furniture sales" + design firm in title
- [ ] Search "design studio" + location
- [ ] Try Wellfound.com for startup design roles
- [ ] Try BuiltIn LA/NY for design-tech hybrid roles
- [ ] Monitor Trilogy/Crossover for more 2HL design roles (they post in batches)
- [ ] Add "Kitchen & Bath" and "K&B" as explicit search terms — 2026-04-14 these roles scored highest
- [ ] Check Natuzzi, RH, Arhaus careers pages directly on Fridays for weekend fills

## Templates That Worked

Cover letter angles that got positive signal (if/when we hear back):
- TBD — waiting for interview callbacks to learn what worked

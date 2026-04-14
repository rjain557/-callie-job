# Callie Wells Job Search Pipeline

## Project Purpose
Automated job search pipeline for Callie Nichole Wells (interior design professional in Rancho Santa Margarita, CA). Scans job boards daily, scores leads, writes cover letters, generates PDFs, emails companies, and sends Callie ready-to-submit application kits.

## EMAIL RULES — READ BEFORE SENDING ANY EMAIL

**Read `config/email-rules.md` before sending ANY email.** This is non-negotiable.

Key rules that MUST be followed every time:
1. **Every email to Callie MUST contain the direct job URL** on its own line after "APPLY HERE:"
2. **Never send a search URL** — always the actual job posting link (linkedin.com/jobs/view/..., indeed.com/viewjob?jk=...)
3. **Always attach the merged PDF** (cover letter page 1 + resume page 2)
4. **One email per job** — never batch multiple jobs in one email
5. **Never send blank emails** — verify the body has content before sending
6. **Include step-by-step apply instructions** telling her which platform to use

If you cannot find the direct URL, say so in the email and provide a fallback (company website or search link). But always TRY to get the direct URL first.

## HOW TO SEND EMAILS — CRITICAL

**NEVER use `gws gmail +send --body`** — it truncates multiline text to the first line only.

**ALWAYS use `scripts/send_email_raw.py`** which builds a proper MIME message:
1. Write body to a .txt file in `scripts/email-bodies/{slug}.txt`
2. Send via: `python scripts/send_email_raw.py <to> <subject> <body_file> [attachments...]`
3. Verify delivery: `gws gmail +read --id <message_id>`

This script uses `--upload` with `message/rfc822` content type which preserves the full email body including newlines, URLs, and formatting.

## Pipeline Configuration

- `config/profile.yml` — Callie's profile, target roles, archetypes, scoring weights, exclusions
- `config/portals.yml` — Job boards (Indeed, LinkedIn, ZipRecruiter, Glassdoor + 4 design boards), tracked companies, title filters
- `config/email-rules.md` — Email format and rules (MUST READ)

## Tracking (Single Source of Truth)

- `tracking/known-jobs.json` — All seen jobs, email_sent, indeed_kit_sent, followups_sent, applied dates
- `tracking/application-log.md` — Human-readable log of all applications
- `tracking/scan-log.md` — Daily scan results log
- `tracking/job-inbox.json` — Manual inbox for queued leads (processed on next pipeline run)

## Job File Convention

Each job gets a .md file in `jobs/active/` (then moved to `jobs/applied/` after processing):
- Numbered sequentially: `{NN}-{company-slug}.md`
- Contains: job details, why Callie fits, application status checkboxes
- Checkboxes are updated with dates and email addresses when actions happen

## Resume Types

| Type | File | Use For |
|------|------|---------|
| design-sales | `callie-wells-resume-design-sales.pdf` | Sales/consultant/showroom/in-home roles |
| design-assistant | `callie-wells-resume-design-assistant.pdf` | Assistant/staging/support roles |
| coordinator | `callie-wells-resume-coordinator.pdf` | Admin/coordinator/office management |

## Exclusions (NEVER apply to these)

- Requires AutoCAD or Revit
- Retail stores (cashier, stock, key holder, store manager, retail anything)
- Automotive/car design
- Graphic/apparel design
- Architecture (licensed)
- Interns
- Medical/dental/nursing
- Under $40K annual (unless part-time with growth path)

## Self-Improving Loop (MANDATORY)

**READ at start of every pipeline run:** `tracking/lessons-learned.md`

Apply all active lessons before scanning. This file accumulates:
- Keywords that surface qualifying leads (prioritize these)
- Keywords that waste time (deprioritize/skip)
- Exclusion patterns (auto-reject before scoring)
- Remote role red flags (always warn Callie)
- Process improvements (gws quirks, scan log format, etc.)
- New scanning ideas to try

**WRITE at end of every pipeline run:** Append new lessons to `tracking/lessons-learned.md`

After each run, add entries for:
- New keywords that worked (or didn't)
- New companies worth tracking
- New exclusion patterns discovered
- Process issues found and how you fixed them
- Ideas for future improvements

Format: `- YYYY-MM-DD: <lesson> — <why/context>`

Never delete lessons. Mark obsolete ones with `[OBSOLETE]` and a reason.

## Daily Pipeline (Cron at 6:57 AM)

TWO scan scopes run each morning:

**A. Local scope** — 50mi from Rancho Santa Margarita, CA
- Indeed + LinkedIn
- 11 + 8 queries (see portals.yml)
- Full-time and part-time (with growth)

**B. Remote scope** — All 50 states, remote-only interior design roles
- Indeed with `remotejob` filter
- LinkedIn with `f_WT=2` (remote filter)
- Queries: "interior designer", "interior design consultant", "virtual interior designer", "e-design interior", "spatial designer", "interior design specialist", "interior design assistant"
- No location restriction, $50K+ threshold

Pipeline steps:
1. Scan both scopes for new postings
2. Check job-inbox.json for manually queued leads
3. Filter against exclusions and already-seen jobs
4. Score each lead 1-5 using profile.yml weights
5. For jobs >= 3.5: create job file, write cover letter, generate PDF, merge with resume
6. Get the DIRECT job posting URL (not a search URL)
7. Email Callie individual emails per job with URL + PDF (follow email-rules.md)
8. Email companies directly when contact email is known
9. Send follow-ups for jobs applied 5+ days ago
10. Move processed jobs to applied/, update all tracking
11. Commit and push to git

## Remote Role Scoring Notes

Remote roles are often higher-paying but come with trade-offs. ALWAYS flag the following in the email to Callie:
- **1099/contractor vs W-2 employee** — 1099 means no benefits, self-employment tax
- **Actual remote vs "remote with travel"** — some "remote" roles require 50%+ travel
- **Staffing platforms** (Crossover, Toptal, etc.) — time tracking, performance monitoring
- **Parent company concerns** — research Glassdoor/Reddit if uncertain

## Git Convention

- Always commit after pipeline changes
- Include job count and summary in commit message
- Co-Author tag: `Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>`

"""Filter and triage SerpAPI batch results - write report to file (avoids Windows Unicode issues)."""
import json
import sys
from pathlib import Path

BASE = Path(__file__).parent.parent


def ascii_safe(s):
    if not s:
        return ""
    return s.encode("ascii", errors="replace").decode("ascii").replace("?", "-")


HARD_EXCLUDE = [
    'autocad', 'revit', 'cet software', 'cap 2020',
    'cashier', 'stock keeper', 'key holder',
    'automotive', 'apparel', 'graphic design', 'ux design',
    'federal contract', ' va project ', 'healthcare design',
    'hyundai', 'mazda', 'kia design', 'ford design',
    'real estate agent', 'real estate salesperson',
    'commercial truck', 'insurance agent',
]

# Mass-market retailers - SKIP even if role title says "Design Consultant"
# (per 2026-04-17 lesson: Crate and Barrel "In-Store Design Consultant" miss)
# These are retail regardless of title. Distinguish from luxury showrooms (RH, Waterworks,
# Natuzzi, Visual Comfort, Ethan Allen, Mitchell Gold, Arhaus) which ARE ok.
RETAIL_BRAND_COMPANIES = [
    'crate and barrel', 'crate & barrel', 'crateandbarrel',
    'williams-sonoma', 'williams sonoma',
    'pottery barn', 'west elm', 'pbteen',
    'home depot', 'lowes', 'lowe\'s',
    'ashley furniture', 'ashley homestore',
    'living spaces', 'bob\'s discount', 'bobs discount',
    'rooms to go', 'raymour & flanigan', 'value city',
    'macy\'s furniture', 'jcpenney', 'target',
]

SENIOR_ADMIN_SKIP_TITLES = [
    'sr. admin', 'senior administrative', 'lead administrative',
    'sr. executive', 'senior executive', 'lead executive',
    'director of', 'vp of', 'chief ', 'head of',
]


def excluded(job, already_applied):
    title_lower = job.get('title', '').lower()
    company_lower = job.get('company', '').lower()
    text = (title_lower + ' ' + company_lower + ' ' +
            job.get('description', '').lower())

    # Hard exclusions
    for kw in HARD_EXCLUDE:
        if kw in text:
            return f'HARD:{kw}'

    # Mass-market retail brands - skip even if title says "Design Consultant"
    for retailer in RETAIL_BRAND_COMPANIES:
        if retailer in company_lower:
            return f'RETAIL-BRAND:{retailer}'

    # Senior admin YoE mismatch
    for kw in SENIOR_ADMIN_SKIP_TITLES:
        if kw in title_lower:
            if 'admin' in title_lower or 'executive' in title_lower or 'coordinator' in title_lower:
                return f'SR-YoE:{kw.strip()}'
            elif 'director' in kw or 'vp' in kw or 'chief' in kw or 'head of' in kw:
                return f'EXEC:{kw.strip()}'

    # Already applied (fuzzy company match)
    company_lower = job.get('company', '').lower()
    for applied in already_applied:
        if applied in company_lower or company_lower.replace(' ', '-') in applied:
            return f'DUPE:{applied}'

    return None


def main():
    # Allow CLI arg for batch file, default to most recent
    if len(sys.argv) > 1 and sys.argv[1].endswith(".json"):
        batch_file = Path(sys.argv[1])
    else:
        cache = BASE / "tracking" / "serpapi-cache"
        batches = sorted(cache.glob("batch-*.json"))
        if not batches:
            print("No batch files found")
            sys.exit(1)
        batch_file = batches[-1]

    date_tag = batch_file.stem.replace("batch-", "")
    out_file = BASE / "tracking" / "serpapi-cache" / f"triage-{date_tag}.md"

    with open(batch_file, encoding="utf-8") as f:
        data = json.load(f)

    with open(BASE / "tracking" / "known-jobs.json") as f:
        kj = json.load(f)

    already_applied = set()
    for slug in list(kj.get('applied', {}).keys()) + list(kj.get('indeed_kit_sent', {}).keys()):
        already_applied.add(slug.lower().split('-', 1)[-1] if '-' in slug else slug.lower())
    # Also add company hints from seen_jobs
    for key in kj.get('seen_jobs', {}).keys():
        company = key.split(':')[0] if ':' in key else key
        already_applied.add(company.lower())
    # Explicit companies from email_sent
    for slug, info in kj.get('email_sent', {}).items():
        if '-' in slug:
            already_applied.add(slug.split('-', 1)[-1])

    lines = [f"# SerpAPI Triage Report - 2026-04-17\n"]
    lines.append(f"Source: {batch_file.name}\n")
    lines.append(f"Total jobs scanned: {sum(len(data[s]) for s in ('local','admin','remote'))}\n\n")

    consider = []

    for scope in ('local', 'admin', 'remote'):
        jobs = data[scope]
        lines.append(f"\n## {scope.upper()} SCOPE ({len(jobs)} jobs)\n\n")
        for j in jobs:
            company = ascii_safe(j.get('company', ''))
            title = ascii_safe(j.get('title', ''))
            location = ascii_safe(j.get('location', ''))
            salary = ascii_safe(j.get('salary', ''))
            posted = ascii_safe(j.get('posted_at', ''))
            apply_url = j.get('apply_url', '')

            reason = excluded(j, already_applied)
            if reason:
                lines.append(f"- [SKIP {reason}] **{company}** - {title}\n")
            else:
                lines.append(f"- **[CONSIDER]** **{company}** - {title}\n")
                lines.append(f"  - Location: {location} | Salary: {salary} | Posted: {posted}\n")
                lines.append(f"  - Apply: {apply_url[:200]}\n")
                consider.append({
                    "scope": scope, "company": company, "title": title,
                    "location": location, "salary": salary, "posted": posted,
                    "apply_url": apply_url,
                    "description": ascii_safe(j.get('description', ''))[:300],
                })

    # Write report
    with open(out_file, "w", encoding="utf-8") as f:
        f.write("".join(lines))

    # Write just the "consider" items as JSON for downstream processing
    consider_file = BASE / "tracking" / "serpapi-cache" / f"triage-{date_tag}-consider.json"
    with open(consider_file, "w", encoding="utf-8") as f:
        json.dump(consider, f, indent=2)

    print(f"Triage report: {out_file}")
    print(f"Consider list: {consider_file}")
    print(f"Total to consider: {len(consider)}")
    print(f"  Local: {sum(1 for c in consider if c['scope']=='local')}")
    print(f"  Admin: {sum(1 for c in consider if c['scope']=='admin')}")
    print(f"  Remote: {sum(1 for c in consider if c['scope']=='remote')}")


if __name__ == "__main__":
    main()

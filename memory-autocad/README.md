# memory/

Persistent memory for Claude sessions working on this repo. Lives **inside the repo** so it travels with the code to any workstation.

## Files

| File | What it holds |
|---|---|
| [CONTEXT.md](CONTEXT.md) | The one-page orientation — load this every session. Project goal, stack, conventions, pointers to everything else. |
| [learnings.md](learnings.md) | Durable facts discovered during work: AutoCAD quirks, COM gotchas, interior-design conventions we've adopted. |
| [sessions/](sessions/) | Chronological session logs — what was discussed/decided on each date, one file per session. |
| [decisions.md](decisions.md) | Tight ADR-style log: decision, why, alternatives considered. |

## Conventions

- **New session** → read [CONTEXT.md](CONTEXT.md) first, then skim the latest `sessions/*.md`.
- **End of session** → append a short log to `sessions/YYYY-MM-DD.md` and update [learnings.md](learnings.md) with anything non-obvious you'd want next time.
- **Absolute dates only** — never "yesterday" or "last week"; these files outlive the session.
- **Keep it terse.** Memory is for future-you, not for a reader discovering the project. Bullets beat paragraphs.

# Project context — autocad-mcp inside callie-job

**Owner:** rjain (Technijian). **For:** Callie Wells (<CallieWells17@gmail.com>).
**Goal:** Help Callie learn AutoCAD by designing and drawing real interior-design projects together, driven from Claude Code. Unlocks AutoCAD-requiring design jobs that the [job-search pipeline](../CLAUDE.md) currently excludes.

**Repo:** `github.com/rjain557/-callie-job` — this repo also hosts Callie's job-search pipeline. The AutoCAD learning track lives alongside it. Both are independent; neither breaks the other.

## The stack

- **AutoCAD 2026** (full, not LT), Windows-only, controlled via COM (`AutoCAD.Application.26`).
- **Python 3.10+** in a local `.venv/` at the repo root.
- **MCP server** at [autocad-mcp/server.py](../autocad-mcp/server.py), exposed to Claude Code via [.mcp.json](../.mcp.json).
- **pywin32** for COM bindings; thin wrapper in [autocad-mcp/acad.py](../autocad-mcp/acad.py).

## Repo layout (AutoCAD track)

See [AUTOCAD_SETUP.md](../AUTOCAD_SETUP.md) for the full table. Short version:
- `autocad-mcp/` — the MCP server
- `projects/` — interior design project specs (briefs, drawing checklists, reference sketches)
- `memory-autocad/` — this folder (kept separate from the job-search pipeline's tracking)
- `scripts/setup-autocad.ps1` — new-workstation bootstrap (named to avoid colliding with the pipeline's existing scripts)

## Callie's relevant profile

- 5 yrs residential interior design (Ethan Allen, Goff Designs, Vintage Design Inc.)
- Strong: space planning, finish/material curation, client consultations, furniture layouts
- **No prior CAD experience.** Start with 2D fundamentals. Use her existing design sense as the scaffold — she already knows what a floor plan should communicate; we're teaching her the software that produces it.
- Based in Rancho Santa Margarita, CA — target work is residential California design/staging firms.

## Conventions we've adopted

- **Interior-design layer naming:** `A-WALL`, `A-DOOR`, `A-GLAZ` (windows), `I-FURN` (furniture), `E-LITE` (lighting/electrical), `A-ANNO-DIMS`, `A-ANNO-TEXT`. Follows US National CAD Standard discipline prefixes.
- **Units:** Architectural inches unless a project explicitly specifies metric. Set `UNITS` before drawing anything.
- **Drafting approach:** Draw in model space at 1:1 real-world scale. Use layouts (paper space) for plotted views.
- **Prefer typed MCP tools over `acad_run_command`.** If we hit the raw-command tool for the same command twice, promote it to a typed tool in `acad.py` + `server.py`.

## Learning mode

Every time Claude issues an AutoCAD action, it should:
1. State the underlying AutoCAD command (e.g. "this calls `PLINE`").
2. Explain what it does in one line.
3. Note a related command worth knowing.

## Where to find things

- Setup & portability → [AUTOCAD_SETUP.md](../AUTOCAD_SETUP.md)
- Tool reference → [autocad-mcp/README.md](../autocad-mcp/README.md)
- Decisions → [decisions.md](decisions.md)
- Durable learnings → [learnings.md](learnings.md)
- Project briefs → [../projects/README.md](../projects/README.md)
- Session logs → [sessions/](sessions/)
- Job-search pipeline (separate concern) → [../CLAUDE.md](../CLAUDE.md)

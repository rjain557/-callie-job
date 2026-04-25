# Interior Design Projects

Five projects, progressive difficulty, designed to teach Callie AutoCAD by drawing real residential work she'd see on the job. Each project targets specific AutoCAD features so by the end she has covered the software's major capabilities — 2D drafting, blocks, xrefs, annotation, sheet layouts, 3D solids, materials, and rendering.

## The curriculum

| # | Project | Mode | Hours | Teaches |
|---|---------|------|-------|---------|
| 1 | [Home Office — single room](01-home-office.md) | 2D beginner | 2–3 | Units, layers, LINE/PLINE/RECTANG, OFFSET, TRIM, DIMLINEAR, TEXT, ZOOM, SAVE |
| 2 | [Studio Apartment — full unit](02-studio-apartment.md) | 2D intermediate | 4–6 | BLOCK/INSERT, HATCH, DIMSTYLE, MLEADER, COPY/MOVE/ROTATE, ARRAY, furniture library |
| 3 | [2-Bed Condo — plan set](03-condo-plan-set.md) | 2D advanced | 6–8 | XREF, LAYOUT/VPORTS, PAGESETUP, PLOT, title blocks, finish schedules |
| 4 | [Kitchen — elevations + 3D](04-kitchen-elevations-3d.md) | 2D → 3D | 6–8 | Elevation views, BOX/EXTRUDE/PRESSPULL, UNION/SUBTRACT, VIEWCUBE, VISUALSTYLES |
| 5 | [Living Room — 3D + render](05-living-room-3d-render.md) | 3D advanced | 8–10 | Materials, MATBROWSER, LIGHT, CAMERA, RENDER, sheets with rendered views |

## Running a project

1. Read the project's brief and learning objectives.
2. Open AutoCAD 2026.
3. In Claude Code, say: *"Let's start project 1. Set up the drawing per the brief."*
4. Work through the drawing checklist step by step. Each step names the AutoCAD command being used so you learn as you draw.
5. When the deliverables are complete, save the .dwg into the project's `out/` folder (create it on demand).

## Learning-mode contract

Every time Claude issues an action in AutoCAD, it will tell you:
1. **The command** being executed (e.g. `PLINE`).
2. **What it does** in one sentence.
3. **A related command** worth knowing for later.

Ask questions freely — the point is learning, not just producing drawings.

## File naming

```text
projects/
├── 01-home-office/
│   ├── out/home-office.dwg      ← your work (gitignored by default)
│   └── reference/               ← sketches, inspiration images (optional)
├── 02-studio-apartment/
│   └── ...
```

Create the `out/` subfolder when you start each project. Add it to .gitignore if the .dwg gets large.

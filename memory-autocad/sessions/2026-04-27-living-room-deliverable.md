# Session — 2026-04-27 (Project 5 Living Room deliverable)

## What we did

Built Project 5 — Coastal Living Room — to the same deliverable shape as
the Project 1 home office, plus the curriculum-specific commands the brief
calls for: LOFT, REVOLVE, SWEEP, FILLETEDGE, materials, photometric
lights, named camera views.

### Final entity counts

`projects/05-living-room/out/living-room.dwg` — 109 entities, 13 layers,
12 materials, 17 photometric lights, 2 named camera views.

### Deliverable files

`projects/05-living-room/out/`:
- `living-room.dwg` — source file
- `floor-plan.png` — 1600×1100 dimensioned plan, 11 FF&E tag bubbles, north arrow, designer stamp
- `presentation-iso.png` — 1600×1100 SW iso Conceptual render
- `hero.png`, `editorial.png` — saved-camera Conceptual snapshots
- `SPEC.md` — narrative, FF&E + finish + lighting schedules, modeling notes
- `PRESENTATION.md` — client-facing cover sheet
- `Living-Room-Spec.docx` — formal Word deliverable (12 sections, 2 schedules, 2 embedded PNGs, 12+ pages)

### Curriculum commands successfully driven from COM / SendCommand

| Command | Used for |
| --- | --- |
| `BOX` / `CYLINDER`         | Walls, floor, ceiling slab, console legs, sofa frames, coffee-table base |
| `SUBTRACT`                 | Window opening, hallway opening, 16 ceiling coffers, mirror frame inset |
| `LOFT` (3 section curves)  | Both lounge chairs |
| `REVOLVE` (lathe)          | Floor lamp body |
| `SWEEP`                    | Both drapery panels along a wavy 3D path |
| `FILLETEDGE`               | Coffee table top edges, 1/2" radius |
| `CAMERA` / `-VIEW _S`       | HERO and EDITORIAL named views |
| `doc.Materials.Add`        | 12 custom materials defined and assigned by layer |
| `POINTLIGHT`               | 16 recessed lights in coffers + 1 floor-lamp light (LIGHTINGUNITS=2) |

### Curriculum items NOT driven from COM (documented as GUI follow-ups in SPEC §8)

- `MATBROWSER` library imports — palette-only; current materials are custom
  AutoCAD definitions matching the brief's intent
- `SUNPROPERTIES` palette — geographic location set in script, but
  date/time controls require the Sun Properties palette
- `RENDER` to file at Medium / High — the dialog/render-window flow needs
  GUI; Conceptual visual style snapshot substitutes
- ARCH-D layout with title block + IMAGEATTACH + 3 small viewports —
  Word doc replaces the plotted board

## What hurt (and what we did about it)

### 1. `Documents.Add()` triggers a "Select Template" dialog

Every `acad.app.Documents.Add()` call popped a modal template-selection
dialog that froze COM until manually dismissed. Cost ~10 minutes of the
session before recognized.

**Fix path:** save the just-created (and dialog-blocked) Drawing1.dwg
*as* the destination via `acad_save(<path>)` MCP tool — that bypasses the
dialog because SaveAs to an explicit path doesn't prompt. Future fix:
preset `FILEDIA = 0` and `SDI` modes before calling `Documents.Add`.

### 2. SUNSTATUS / LATITUDE / LONGITUDE / TIMEZONE `SetVariable` hangs

In AutoCAD 2027, writing `SUNSTATUS = 1` via COM SetVariable hangs the
calling thread permanently. `LATITUDE` / `LONGITUDE` may also be
read-only on this build.

**Workaround:** skip these sysvars entirely; document the geographic
location in SPEC.md and let the user set sun via the SUNPROPERTIES
palette before rendering.

### 3. POINTLIGHT prompted for a "Lighting unit" warning dialog

First `POINTLIGHT` call hung because AutoCAD wanted to confirm that
photometric lighting should be enabled.

**Fix:** preset `LIGHTINGUNITS = 2` (photometric, international) before
the first POINTLIGHT call. With that set, `_.POINTLIGHT\n<x,y,z>\nX\n`
(position + eXit) places the light cleanly, no prompt.

### 4. `_-VIEW _R <name>` doesn't restore named *camera* views the same way as plain views

After saving HERO and EDITORIAL via `_.CAMERA`, attempting to
`_.-VIEW _R HERO` snapped the view to a default SWISO instead of the
saved camera position. Both `hero.png` and `editorial.png` came out
identical to `presentation-iso.png`.

**Workaround left in:** ship the named views in the DWG but use the
SWISO Conceptual snapshot as the primary render. A future session can
either probe `doc.Views` directly via COM (AcadView.SetCamera, etc.) or
use SendCommand "_VIEW HERO" without the dash.

### 5. REVOLVE briefly modal-locks AutoCAD after large profile

REVOLVE on the floor-lamp profile completed but left AutoCAD in a busy
state for a few seconds, causing the next `doc.ModelSpace.Count` access
to fail. Subsequent operations recovered after another `acad_cancel` +
manual ESC.

**Mitigation in scripts:** wrap each modeling step in its own try/except,
save after each, and never depend on entity counts immediately after a
heavy CSG op.

## Tools added this session

| File | Purpose |
| --- | --- |
| [autocad-mcp/build_living_room.py](../../autocad-mcp/build_living_room.py) | Shell + furniture (boxes/cylinders) + 16 coffers + initial drape boxes |
| [autocad-mcp/living_advanced_shapes.py](../../autocad-mcp/living_advanced_shapes.py) | FILLETEDGE, LOFT, REVOLVE, mirror SUBTRACT, SWEEP — replaces approximations |
| [autocad-mcp/living_remaining_shapes.py](../../autocad-mcp/living_remaining_shapes.py) | Continuation after a REVOLVE-induced modal hang (mirror + drapery only) |
| [autocad-mcp/living_materials_lights_cams.py](../../autocad-mcp/living_materials_lights_cams.py) | 12 materials defined and assigned by layer |
| [autocad-mcp/living_lights_cams.py](../../autocad-mcp/living_lights_cams.py) | 16 photometric POINTLIGHTs in coffers + 1 lamp light |
| [autocad-mcp/living_cameras.py](../../autocad-mcp/living_cameras.py) | HERO + EDITORIAL named camera views |
| [autocad-mcp/finish_living_annotations.py](../../autocad-mcp/finish_living_annotations.py) | Plan dims, FF&E tag bubbles, room tag, designer stamp, north arrow |
| [autocad-mcp/snap_living_full.py](../../autocad-mcp/snap_living_full.py) | 4-snapshot capture (plan, iso, hero, editorial) |
| [autocad-mcp/test_filletedge.py](../../autocad-mcp/test_filletedge.py) | Diagnostic — proved FILLETEDGE works via COM SendCommand |
| [autocad-mcp/test_one_light.py](../../autocad-mcp/test_one_light.py) | Diagnostic — proved POINTLIGHT works once LIGHTINGUNITS=2 is set |
| [projects/05-living-room/build_word_doc.js](../../projects/05-living-room/build_word_doc.js) | docx-js generator, embeds the 2 PNGs, 12 sections |

## How to resume / re-run

```
cd -callie-job
# Open AutoCAD 2027
.venv/Scripts/python.exe autocad-mcp/build_living_room.py        # shell + furniture
.venv/Scripts/python.exe autocad-mcp/living_advanced_shapes.py   # LOFT/REVOLVE/SWEEP/FILLETEDGE/SUBTRACT
.venv/Scripts/python.exe autocad-mcp/living_materials_lights_cams.py
.venv/Scripts/python.exe autocad-mcp/living_lights_cams.py
.venv/Scripts/python.exe autocad-mcp/living_cameras.py
.venv/Scripts/python.exe autocad-mcp/finish_living_annotations.py
.venv/Scripts/python.exe autocad-mcp/snap_living_full.py
node projects/05-living-room/build_word_doc.js
```

If AutoCAD goes RPC-rejected during a run, click into the AutoCAD command
line and press ESC twice — the PostMessage-based `acad_cancel` does not
clear all modal states (REVOLVE in particular).

## Carry-forward

- Promote `acad_set_lighting_units(2)` and `acad_filedia(0)` as typed
  MCP tools (used 5+ times this session)
- Investigate why `_-VIEW _R <camera>` snaps to default SWISO instead of
  the saved camera position — consider `IAcadView.SetCamera` direct COM
- Add a typed `acad_pointlight(x,y,z, intensity, kelvin)` tool wrapping
  the SendCommand sequence

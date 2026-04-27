# Session — 2026-04-27 (Project 4 Kitchen deliverable)

## What we did

Built Project 4 — Kitchen Casework — to the same deliverable shape as the
home office and living room, sized to a single-wall layout with island.

### Final entity counts

`projects/04-kitchen/out/kitchen.dwg` — 71 entities (including
annotations), 12 layers.

### Deliverable files

`projects/04-kitchen/out/`:
- `kitchen.dwg` — source file
- `floor-plan.png` — dimensioned plan with FF&E + casework tags 1–11
- `presentation-iso.png` — NE isometric Conceptual render (showing
  cabinets, range, hood, dishwasher, pantry, island all in one frame)
- `elevation-long-wall.png` — FRONT view, 2D wireframe, with island
  frozen so the south-wall casework reads cleanly
- `elevation-island.png` — BACK view, 2D wireframe, with cabinets
  frozen so only the island shows
- `SPEC.md` — narrative, FF&E + finish + appliance + casework + lighting
  + power + plumbing schedules, modeling notes, run-length adjustment
- `PRESENTATION.md` — client-facing cover sheet
- `Kitchen-Spec.docx` — formal Word deliverable (14 sections, 4 schedules, 4 embedded PNGs)

### What's the same as the previous projects

- Same brand stamp + designer block
- Same docx-js generator pattern (US Letter, Arial, brand colors, page numbers)
- Same finish_*_annotations.py + snap_*.py pattern
- Same ACI color proxies (no MATBROWSER library imports)

### What's different / new

- **Cabinet run-length adjustment.** Brief calls out 192" of cabinets on
  a 168" wall — not possible. Adjusted to B36 + R30 + DW24 + SB36 + B30
  + P12 = 168", documented in SPEC §8 and the Word doc §8.
- **Two ELEVATION snapshots** — FRONT and BACK views of model space,
  with surgical layer freezing so each elevation reads cleanly. This is
  the closest we get to the brief's "Sheet 7.1–7.3 ARCH-D layout"
  without driving the actual paper-space layouts via COM.
- **NE isometric** instead of SW for the presentation render — for a
  single-wall kitchen, the NE angle puts the cabinet run in the
  foreground (visible) instead of behind the camera (hidden).
- **Toe kicks via inverted SUBTRACT** — drew a void box on the toe-kick
  region and subtracted from each base cabinet body. PRESSPULL would do
  the same in interactive use; same final geometry.

## Carry-forward learnings (not yet in learnings.md)

- **NE iso > SW iso for single-wall layouts.** When the room's
  interesting features are concentrated against one wall, set the iso
  view from the OPPOSITE corner so the wall is in the foreground. SW
  iso for symmetric rooms (home office, living room); NE iso for
  cabinet-run kitchens.
- **Use named-view (FRONT / BACK / LEFT / RIGHT) snapshots as
  elevations.** Combined with selective layer freezing, this captures
  pure orthographic 2D linework that reads as architectural elevations
  without needing to draw 2D linework separately. Limitation: dimensions
  are in model space, so they may not appear in the elevation snapshot
  unless you put them on a layer that isn't frozen.
- **`Documents.Add` on an empty drawing scenario.** Same pattern as
  Project 5: when AutoCAD is fresh with one empty Drawing1.dwg, save it
  immediately to the destination DWG path via `acad_save(<path>)`. Do
  NOT call `Documents.Add()` from inside a script — it can pop the
  template-selection dialog and freeze COM.

## How to resume / re-run

```
cd -callie-job
# Open AutoCAD 2027 (Drawing1.dwg fresh, or kitchen.dwg if previously saved)
.venv/Scripts/python.exe autocad-mcp/build_kitchen.py              # 3D model
.venv/Scripts/python.exe autocad-mcp/finish_kitchen_annotations.py # plan dims + tags
.venv/Scripts/python.exe autocad-mcp/snap_kitchen_full.py          # 4 PNGs
node projects/04-kitchen/build_word_doc.js                         # docx
```

All scripts are idempotent — `build_kitchen.py` purges the model space
before re-running; `finish_kitchen_annotations.py` deletes prior
A-ANNO-* entities first.

## Project 4-specific tools added

| File | Purpose |
| --- | --- |
| [autocad-mcp/build_kitchen.py](../../autocad-mcp/build_kitchen.py) | Shell + 6-cabinet run + island + appliances + counter with sink subtract |
| [autocad-mcp/finish_kitchen_annotations.py](../../autocad-mcp/finish_kitchen_annotations.py) | Plan dims + 11 FF&E tag bubbles + room tag + designer stamp + N arrow |
| [autocad-mcp/snap_kitchen_full.py](../../autocad-mcp/snap_kitchen_full.py) | 4-snapshot capture: plan, NE iso, long-wall elevation, island elevation |
| [projects/04-kitchen/build_word_doc.js](../../projects/04-kitchen/build_word_doc.js) | docx-js generator, 4 embedded PNGs, 14 sections |

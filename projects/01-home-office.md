# Project 1 — Home Office

**Mode:** 2D, beginner. **Time:** 2–3 hours. **Deliverable:** one .dwg with a complete single-room floor plan, dimensioned and annotated.

## Client brief

Home office conversion of a spare bedroom in a Rancho Santa Margarita single-family home. Client is a consultant who takes video calls, stores reference books, and wants a reading nook. Room dimensions **11'-6" × 10'-0"**, single swing door (2'-8" wide) on the south wall, one operable window (4'-0" × 4'-0") centered on the east wall. Carpet is being removed and replaced with LVP.

## Program

- Desk (60" × 30") facing into the room (not the wall) so the window provides side light, not backlight.
- Desk chair (task).
- Bookcase (36" × 12") along one wall — call out which.
- Reading nook: armchair (34" × 34") + side table (18" dia).
- Floor lamp next to the armchair.

## Learning objectives

This project introduces the fundamentals of 2D drafting in AutoCAD.

| Command | What it does |
|---|---|
| `UNITS` | Set drawing units before drawing anything — architectural inches for this project. |
| `LIMITS` / `ZOOM All` | Establish and view the drawing extents. |
| `LAYER` | Create and manage the stacked layers geometry is drawn on. |
| `LINE` / `PLINE` | Draw straight line segments (PLINE = single connected entity, preferred for walls). |
| `RECTANG` | Draw an axis-aligned rectangle (shortcut for closed polylines). |
| `OFFSET` | Produce a parallel copy of a line/polyline at a set distance — the workhorse for building wall thicknesses. |
| `TRIM` / `EXTEND` | Clean up intersections where lines overshoot/undershoot. |
| `DIMLINEAR` / `DIMALIGNED` | Place dimensions. |
| `TEXT` / `MTEXT` | Single-line vs multi-line text. |
| `ZOOM` (window, extents, previous) | Navigate the drawing. |
| `SAVE` / `SAVEAS` | Save to a .dwg. |

Also introduced: the National CAD Standard layer names and architectural dimension reading.

## Drawing checklist

Claude will call the matching MCP tool at each step. If something is missing from the MCP toolset, Claude falls back to `acad_run_command`.

### Setup

- [ ] **1.1** Open a new drawing. Tool: `acad_new_drawing`. Command equivalent: `NEW`.
- [ ] **1.2** Set units to architectural inches. Raw command: `UNITS`, type = Architectural, precision = 1/8".
- [ ] **1.3** Create layers:
  - `A-WALL` — white/black (color 7), walls
  - `A-DOOR` — cyan (4), doors + swings
  - `A-GLAZ` — blue (5), windows
  - `I-FURN` — green (3), furniture
  - `A-ANNO-DIMS` — red (1), dimensions
  - `A-ANNO-TEXT` — magenta (6), notes
  - Tool: `acad_create_layer` for each.
- [ ] **1.4** Set `A-WALL` as active. Tool: `acad_set_active_layer`.

### Walls

- [ ] **2.1** Draw the room's inside face as a closed rectangle polyline: 11'-6" × 10'-0" starting at origin (0,0). Tool: `acad_draw_rectangle` with `lower_left=[0, 0]`, `upper_right=[138, 120]` (inches).
- [ ] **2.2** Offset this inward by -4" (typical interior wall thickness 2x4 + drywall ≈ 4-1/2"; use 4" for simplicity). Wait — we offset OUTWARD to make the outer wall face. Raw command: `OFFSET 4 [pick polyline] [pick outside] ENTER`. Note the double wall lines now define wall thickness.

### Door

- [ ] **3.1** Open a 2'-8" door on the south wall. Plan: break the wall with two short lines at x=[55, 55+32] on the inside face; mirror breaks on the outside.
  - Raw command approach: use `TRIM` against two vertical lines drawn 32" apart in the door location.
- [ ] **3.2** Add the door panel (a closed rectangle 32" × 1-3/8") hinged at one side.
- [ ] **3.3** Add the door swing arc. AutoCAD command: `ARC`, start-end-radius variant. 90° swing with radius = door width (32").

### Window

- [ ] **4.1** On the east wall, centered vertically (at y = 60" — half of 120"), cut an opening 48" wide — so y = 36" to y = 84" gets broken.
- [ ] **4.2** Draw three parallel lines at the opening to represent the window sill + glass + head (standard convention).

### Furniture layer

- [ ] **5.1** Set `I-FURN` as active. Tool: `acad_set_active_layer`.
- [ ] **5.2** Draw the desk: 60" × 30" rectangle, placed so the **long side faces the window**, with at least 36" clearance behind the chair. Tool: `acad_draw_rectangle`.
- [ ] **5.3** Desk chair: circle, 20" diameter, centered 18" behind desk center. Tool: `acad_draw_circle`.
- [ ] **5.4** Bookcase: 36" × 12" against the west wall (choose a location that doesn't block door swing or window). Tool: `acad_draw_rectangle`.
- [ ] **5.5** Reading nook in the NE corner: armchair (34" × 34"), side table (18" dia).
- [ ] **5.6** Floor lamp: 12" dia circle next to the armchair.

### Annotation

- [ ] **6.1** Set `A-ANNO-DIMS` as active. Raw command: `DIMLINEAR` for overall room width and length. Also dimension the door location and window centerline.
- [ ] **6.2** Set `A-ANNO-TEXT` as active. Tool: `acad_draw_text`. Label: "HOME OFFICE — 11'-6\" × 10'-0\"" at a top-center position. Height = 6" (plotted at 1/4"=1'-0" = 1/48, this gives ~1/8" text on the printed sheet).
- [ ] **6.3** Label furniture with small text labels: "DESK", "CHAIR", "BOOKCASE", etc. Height = 4".

### Finish

- [ ] **7.1** Zoom to extents. Tool: `acad_zoom_extents`.
- [ ] **7.2** Save as `projects/01-home-office/out/home-office.dwg`. Tool: `acad_save` with a path.

## Deliverables

- `projects/01-home-office/out/home-office.dwg`
- A short `projects/01-home-office/notes.md` with anything Callie found tricky (for `memory-autocad/learnings.md`).

## AutoCAD concepts she'll leave this project understanding

- Layers are not decoration; they are how professionals structure drawings.
- Model space is **real-world scale**. You draw at 1:1. Scale only matters at plot time.
- Polylines are preferred over individual lines for anything you'll edit as a unit.
- Dimensions reference geometry — if you move the wall, the dimension updates.
- The architectural inches format (`11'-6"`) is how AutoCAD displays the units she just set.

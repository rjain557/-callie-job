# Project 3 — 2-Bedroom Condo Plan Set

**Mode:** 2D, advanced. **Time:** 6–8 hours. **Deliverable:** a plan set — multiple sheets plotted from a base .dwg referenced as an xref into presentation-ready layouts.

## Client brief

Typical 2BR / 2BA condo in Orange County, 1,150 sf. Owner is remodeling and needs a tight set of plans to hand a contractor and subs. You'll deliver a sheet set containing:

- **A-101 Floor Plan**
- **A-102 Furniture Layout**
- **E-101 Electrical / Lighting Plan**
- **A-601 Finish Schedule + Door/Window Schedule**

## Program

Floor plan: entry foyer, kitchen (with island), dining + living combined, primary bedroom with ensuite, secondary bedroom, hall bath, laundry closet, balcony.

Rough wall layout (in inches, outer unit 34'-0" × 34'-0"):

- Unit footprint: 34' × 34' (408" × 408").
- Primary suite along east wall, 14' × 14' bedroom + 8' × 10' ensuite.
- Secondary bedroom NW corner, 11' × 11'.
- Hall bath next to secondary bedroom, 5' × 8'.
- Laundry closet 3' × 6' near entry.
- Kitchen island 8' × 3'-6".

## Learning objectives

This is the "how professionals package drawings" project.

| Command | What it does |
|---|---|
| `XREF` (`-XREF`, `XATTACH`) | Reference another .dwg into the current drawing as a live link. The referenced drawing updates in place when it changes. |
| `LAYOUT` / `LAYOUTS` | Switch between model space and named paper-space layouts (sheets). |
| `MVIEW` | Create a viewport on a layout that looks into model space. |
| `VPORTS` | Manage multiple viewports per layout. |
| `PAGESETUP` | Configure sheet size, printer, plot style — once per layout. |
| `PLOT` / `PUBLISH` | Output to PDF or physical paper. |
| `PSLTSCALE` / `CANNOSCALE` | Make linetype scales and annotation text auto-scale across viewport scales. |
| `TABLE` | Draw a structured schedule grid (doors, windows, finishes). |
| `FIELD` | Insert live text fields that pull from properties (area, room number). |
| `TITLEBLOCK` (custom block) | The drawing's "wrapper" — project name, sheet number, date, scale. |

## Drawing checklist

### 3A. The base drawing: `condo-base.dwg`

- [ ] **1.1** New drawing. Units = architectural inches.
- [ ] **1.2** Create the layer standard set (A-WALL, A-DOOR, A-GLAZ, A-ANNO-DIMS, A-ANNO-TEXT, A-FLOR-PATT).
- [ ] **1.3** Draw walls using PLINE + OFFSET.
- [ ] **1.4** Place doors and windows. Reuse blocks from Project 2 if available (`-INSERT` with the path).
- [ ] **1.5** Hatch floors appropriately — LVP in living/sleeping, tile in wet rooms.
- [ ] **1.6** Dimension exterior overalls + interior clears. No furniture yet.
- [ ] **1.7** Room labels as MTEXT.
- [ ] **1.8** Save as `projects/03-condo/out/condo-base.dwg`.

### 3B. The furniture drawing: `condo-furniture.dwg`

- [ ] **2.1** New drawing.
- [ ] **2.2** Attach `condo-base.dwg` as an **xref** (`XATTACH`) overlay, origin 0,0. Layer `XREF` (color 8 gray, so it reads as a background).
- [ ] **2.3** Add a dedicated `I-FURN` layer and place furniture on it.
- [ ] **2.4** Reuse furniture blocks from Project 2's library. Add new: dining table (72" × 42"), two twin beds, etc.
- [ ] **2.5** Save as `projects/03-condo/out/condo-furniture.dwg`.

### 3C. The electrical drawing: `condo-electrical.dwg`

- [ ] **3.1** New drawing, xref `condo-base.dwg`.
- [ ] **3.2** Add layers: `E-LITE` (lighting), `E-POWR` (outlets), `E-LITE-SWCH` (switches).
- [ ] **3.3** Build small blocks for:
  - Ceiling-mount light (circle + X)
  - Recessed can (circle)
  - Wall sconce (half-circle on wall)
  - Duplex outlet (circle with two short lines — plan symbol)
  - Switch ($ symbol with subscript for 3-way)
- [ ] **3.4** Place at least 4 cans in kitchen, one pendant over dining, one ceiling fixture per bedroom, outlets every 12' per code reminder.
- [ ] **3.5** Add dashed "control lines" connecting switches to the fixtures they control (raw command: `LINE` on a `E-LITE-SWCH-CTRL` layer with a dashed linetype via `LINETYPE`).
- [ ] **3.6** Save as `projects/03-condo/out/condo-electrical.dwg`.

### 3D. Sheets in one host .dwg: `condo-sheets.dwg`

- [ ] **4.1** New drawing. This file will host four layouts; model space stays empty.
- [ ] **4.2** Create a title block block: 24"×36" ARCH-D sheet with fields for: project name, sheet number, scale, date, designer. Tip: use `FIELD` for the date.
- [ ] **4.3** Create four layouts: `A-101`, `A-102`, `E-101`, `A-601`. Raw command: `LAYOUT` new.
- [ ] **4.4** On each layout:
  - [ ] Set page setup for 24"×36" PDF plotter + `monochrome.ctb`.
  - [ ] Insert the title block.
  - [ ] Create a viewport (`MVIEW`) and set its scale to `1/4" = 1'-0"` (ratio 1:48).
  - [ ] Into that viewport, show the right xref: for A-101 reference `condo-base.dwg`, for A-102 `condo-furniture.dwg`, for E-101 `condo-electrical.dwg`. (Alternative: attach them all in `condo-sheets.dwg` and freeze/thaw per layout — `VPLAYER`).

### 3E. The schedule sheet: A-601

- [ ] **5.1** On the A-601 layout, use `TABLE` to build:
  - **Door schedule:** Mark, Width, Height, Material, Hardware, Remarks. Rows for every door.
  - **Window schedule:** Mark, Width, Height, Type, Remarks.
  - **Finish schedule:** Room, Floor, Base, Walls, Ceiling, Remarks.
- [ ] **5.2** Tag doors on A-101 with bubble marks (circles with letters/numbers, on `A-ANNO-SYMB`). Reference marks match the schedule.

### Plot it

- [ ] **6.1** `PLOT` each layout to PDF. Output: `projects/03-condo/out/A-101.pdf`, `A-102.pdf`, `E-101.pdf`, `A-601.pdf`.
- [ ] **6.2** `PUBLISH` to merge them into a single PDF set.

## Deliverables

- `projects/03-condo/out/condo-base.dwg`
- `projects/03-condo/out/condo-furniture.dwg`
- `projects/03-condo/out/condo-electrical.dwg`
- `projects/03-condo/out/condo-sheets.dwg`
- `projects/03-condo/out/plan-set.pdf` (published set)

## Concepts she'll leave understanding

- **Model vs paper space.** Draw at 1:1 in model, arrange at sheet scale in paper.
- **Xrefs separate concerns.** Architecture, furniture, and electrical live in their own files; the shell only exists once.
- **Sheet scale is a viewport property.** Change the viewport scale → the same drawing reads larger/smaller; annotations stay the right size if you use annotation scale.
- **Schedules are data + geometry.** A door tag on the plan and a row in the schedule are two views of the same decision.

# Project 2 — Studio Apartment

**Mode:** 2D, intermediate. **Time:** 4–6 hours. **Deliverable:** one .dwg with a complete studio apartment floor plan including kitchenette, bathroom, living/sleeping zones, furniture, and flooring hatches.

## Client brief

Ground-floor unit in a small multifamily building in Rancho Santa Margarita. Renter-occupied, owner wants a space plan to market the unit as a flexible WFH-friendly studio. **Total unit footprint: 18'-0" × 22'-0"** (396 sf). One entry door, one exterior window (6'-0" sliding glass), one bathroom with its own door. Open kitchenette along one wall.

## Program

- **Kitchenette** along the 18' north wall: 24"-deep base cabinets with sink, 30" range, under-counter fridge, ~60" of counter. No upper cabinets on the window side.
- **Bathroom**, 5'-0" × 7'-6" in the NW corner. Door swings in. Tub, toilet, sink. Single-sink 24" vanity.
- **Living zone** facing the sliding glass door on the south wall.
- **Sleeping zone**: queen bed (60" × 80") positioned for privacy.
- **Dining**: small bistro table seats 2.
- **Storage**: a 48"-wide wardrobe/closet.

## Learning objectives

Introduces reusable content, hatching, and annotation styles.

| Command | What it does |
|---|---|
| `BLOCK` / `BEDIT` / `INSERT` | Define a reusable group of entities (e.g. a door symbol) and insert it multiple times. |
| `WBLOCK` | Write a block out as its own .dwg for use in other drawings — the start of a furniture library. |
| `HATCH` | Fill a closed region with a pattern (wood flooring, tile, carpet). |
| `DIMSTYLE` | Create a dimension style so all dimensions look consistent (arrow size, text height, offsets). |
| `MLEADER` / `MLEADERSTYLE` | Callout arrows that point from text to features. |
| `COPY` / `MOVE` / `ROTATE` / `MIRROR` | Entity manipulation — the bread and butter of editing. |
| `ARRAY` (rectangular/polar) | Duplicate entities on a grid or around a center. |
| `FILLET` / `CHAMFER` | Round or bevel corners. |
| `MATCHPROP` | Copy properties from one entity to another. |
| `PURGE` | Remove unused blocks/layers/styles before saving. |

## Drawing checklist

### Setup

- [ ] **1.1** New drawing, architectural inches (reuse Project 1's habits). Tool: `acad_new_drawing`.
- [ ] **1.2** Create layers — same base set as Project 1 plus:
  - `A-FLOR-PATT` — 253 (light gray), hatches
  - `I-FURN-APPL` — yellow (2), appliances
  - `P-SANR` — 134, plumbing fixtures
- [ ] **1.3** Create a `DIMSTYLE` called "ARCH-48" tuned for 1/4"=1'-0" plotting (DIMSCALE = 48, arrow size = 3/32", text height = 1/8"). Raw command: `DIMSTYLE`.

### Shell

- [ ] **2.1** Draw the outer wall rectangle: 18'-0" × 22'-0" (216" × 264").
- [ ] **2.2** Offset 4" inward for wall thickness.
- [ ] **2.3** Interior walls for the bathroom (5'-0" × 7'-6") in the NW corner, 4" thick.
- [ ] **2.4** Entry door (3'-0") on the east wall, bathroom door (2'-4") swinging into the bathroom, sliding glass door (6'-0") centered on the south wall.

### Build a door block

- [ ] **3.1** Draw one door + swing (as in Project 1) once. Turn it into a block:
  - Raw command: `BLOCK`, name `DOOR-2-8`, base point on hinge side.
- [ ] **3.2** Insert it at the entry and bathroom. Scale for width differences.
- [ ] **3.3** Do the same for a window block (`WIN-SGD-6` for the sliding glass).

### Kitchen

- [ ] **4.1** Base cabinet run along north wall: 24"-deep polyline.
- [ ] **4.2** Sink (25" × 19" double-bowl rectangle with a 1" offset inner rectangle).
- [ ] **4.3** Range (30" × 24") with four circles representing burners — use `ARRAY` (2×2 rectangular) to place the burners.
- [ ] **4.4** Under-counter fridge (24" × 24").

### Bathroom fixtures

- [ ] **5.1** Tub: 60" × 30" rectangle with rounded interior ellipse, drain at one end.
- [ ] **5.2** Toilet: standard plan symbol (oval bowl + tank rectangle behind). 14" × 28" footprint.
- [ ] **5.3** Vanity: 24" × 21" base + inset sink oval.
- [ ] **5.4** Consider saving each as a block so you can reuse them later.

### Furniture zone

- [ ] **6.1** Sofa (84" × 36") facing south toward the glass door.
- [ ] **6.2** Coffee table (40" × 20").
- [ ] **6.3** Queen bed (60" × 80") in the NE corner, long side against the east wall, with a nightstand (18" × 18").
- [ ] **6.4** Bistro table (30" dia circle) + 2 chairs (18" dia circles) near the kitchen.
- [ ] **6.5** Wardrobe (48" × 24") on a wall that doesn't conflict.

### Hatches

- [ ] **7.1** Set `A-FLOR-PATT` as active.
- [ ] **7.2** LVP plank hatch in living/sleeping: `HATCH`, pattern `AR-RSHKE`, scale tuned so planks read ~6" wide.
- [ ] **7.3** Tile hatch in bathroom: pattern `ANSI37` rotated 45°, scale ~12" tile.
- [ ] **7.4** Kitchen: carry the LVP through (seamless) OR use a different pattern to show a material transition.

### Annotation

- [ ] **8.1** Overall dimensions (two chains: horizontal + vertical).
- [ ] **8.2** Interior clear dimensions for bathroom and kitchen run.
- [ ] **8.3** Room labels as MTEXT: "LIVING / SLEEPING", "KITCHEN", "BATH", "DINING".
- [ ] **8.4** MLEADER callouts for key pieces ("QUEEN BED — 60\" × 80\"", "SLIDING GLASS DOOR — 6'-0\"").

### Finish

- [ ] **9.1** `PURGE` unused blocks/layers.
- [ ] **9.2** Zoom extents, save as `projects/02-studio-apartment/out/studio.dwg`.

## Deliverables

- `projects/02-studio-apartment/out/studio.dwg`
- A small furniture-block library in `projects/02-studio-apartment/blocks/` (each piece saved via `WBLOCK`). Candidates: `SOFA-84`, `BED-Q`, `TOILET`, `TUB-60`, `DOOR-2-8`.
- Update `memory-autocad/learnings.md` with anything new (e.g. "DIMSCALE governs how large dim text appears in model space").

## Concepts she'll leave understanding

- **Blocks = reusable content.** Define once, insert many; edit the source, all instances update.
- **Hatches are material symbols.** Choose pattern + scale deliberately; the whole drawing lives inside that scale.
- **Dimension styles propagate.** Change DIMSCALE once and every dimension restyles.
- **WBLOCK starts a personal library** — the same blocks will seed Project 3 and beyond.

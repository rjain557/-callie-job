# Project 4 — Kitchen Elevations + 3D Cabinetry

**Mode:** 2D + intro 3D. **Time:** 6–8 hours. **Deliverable:** a plan view, two elevations, and a 3D model of a full kitchen cabinet run with appliances.

## Client brief

Pull the kitchen out of Project 3 (or design a fresh one). Standalone detailed drawings for the cabinet shop and the contractor. **Kitchen footprint:** 14'-0" wide × 10'-0" deep (168" × 120"), single-wall layout on one side plus an island.

## Program

- **Run along the long wall (14'):** 36" base cabinet → 30" range → 30" base → 36" sink base → 36" base → 24" pantry.
- **Wall cabinets** above the base run (except over the range — range hood instead). Height 42" (for 10' ceilings).
- **Island:** 8'-0" × 3'-6", seating for 3 on one side, storage cabinets on the other.
- **Toe kick** 4" tall × 3" deep, recessed.
- **Counter** 1.5" thick, 25.5" deep, overhanging cabinets by 1.5" at the front, 0 at the wall.

## Learning objectives

The bridge into 3D. You do not need to model everything in 3D — understand how elevations relate to plans and when to drop into solids.

| Command | What it does |
|---|---|
| Named **UCS** | User Coordinate System. Rotate/elevate the drafting plane so you can draw an elevation on a vertical wall as if it were flat. |
| `COPY` + `ROTATE` | How a plan-view cabinet outline becomes an elevation's starting footprint. |
| `REGION` | Turn a closed 2D shape into a planar surface — prerequisite for many 3D ops. |
| `EXTRUDE` | Push a 2D region up into a 3D solid. |
| `PRESSPULL` | Click-and-drag 3D modeling — closest thing AutoCAD has to SketchUp. |
| `BOX`, `CYLINDER` | Primitive 3D solids. |
| `UNION`, `SUBTRACT`, `INTERSECT` | Boolean solid editing — cut a sink bowl out of a counter, etc. |
| `FILLETEDGE` / `CHAMFEREDGE` | Round/bevel edges of 3D solids. |
| `VIEWCUBE`, `ORBIT`, `3DWALK` | Navigate 3D. |
| `VISUALSTYLES` | Switch between wireframe, hidden-line, shaded, realistic. |
| `FLATSHOT` | Project the 3D model onto a 2D view for use in elevations. |
| `HIDE` | Static hidden-line view (older, still useful for plotting). |

## Drawing checklist

### 4A. Plan view

- [ ] **1.1** New drawing. Layers: `A-WALL`, `I-CASE` (casework/cabinets), `I-CASE-ISLA` (island), `I-FURN-APPL`, `A-ANNO-*`.
- [ ] **1.2** Draw the kitchen shell (168" × 120" rectangle), walls 4" thick.
- [ ] **1.3** Draw the cabinet run in plan as polylines — one polyline per cabinet, each tagged with text ("B36", "R30", "B30", "SB36", "B36", "P24" for pantry).
- [ ] **1.4** Draw the island (96" × 42") with overhang lines (96" × 54" dashed for the counter extents on the seating side).
- [ ] **1.5** Appliances: range symbol (30" × 24"), sink double-bowl (25" × 19"), dishwasher (24" × 24", dashed line because it's hidden under the counter).
- [ ] **1.6** Dimension cabinet widths chain along the run + room overalls.

### 4B. Elevation — long wall

- [ ] **2.1** Copy the plan polylines of the long-wall run off to the side.
- [ ] **2.2** Rotate them 0° (actually we want to project up). Method: each base cabinet in elevation is a 34.5" tall rectangle starting 0" off the floor. Draw a horizontal baseline; for each cabinet, draw a rectangle cabinet_width × 34.5".
- [ ] **2.3** Add the toe kick (4" tall × inset 3") as a notch at the bottom of each base cabinet.
- [ ] **2.4** Add the counter on top: continuous rectangle 1.5" tall, full width of the run.
- [ ] **2.5** Wall cabinets: 42" tall, 12" deep but in elevation that's just the face — each a 42"-tall rectangle starting at 54" off floor (18" backsplash zone).
- [ ] **2.6** Over the range: draw a range hood silhouette (30" wide × 30" tall) instead of a wall cabinet.
- [ ] **2.7** Add doors/drawers — for each base cabinet, drawer band at top (6" tall) + double doors below.
- [ ] **2.8** Tag each cabinet (B36, SB36, etc.) and dimension elevation heights (floor to counter = 36", floor to wall cab = 54", wall cab height = 42", ceiling = 120").

### 4C. Elevation — island

- [ ] **3.1** Two views: front (seating side) and back (storage side).
- [ ] **3.2** Same techniques as 4B. Show the 12" seating overhang on the front elevation as counter extending past the cabinets below.

### 4D. 3D model — island first

The island is a good 3D primer because it's freestanding.

- [ ] **4.1** Switch to a 3D workspace if available (raw command: `WSCURRENT` = "3D Modeling"). Or stay in 2D workspace and use commands directly.
- [ ] **4.2** Set the UCS to World: `UCS W`.
- [ ] **4.3** Draw a closed polyline of the island base footprint (96" × 42") on the floor. Convert to a `REGION`.
- [ ] **4.4** `EXTRUDE` it up 34.5" to make the cabinet box.
- [ ] **4.5** Toe kick: extrude a separate slimmer box (90" × 36") up 4" and subtract from the cabinet base? Actually — separate approach: draw the full box, then on each face draw the toe kick cut polygon, `PRESSPULL` it 3" in.
- [ ] **4.6** Counter top: `BOX` 99" × 54" × 1.5" thick, placed at z=34.5".
- [ ] **4.7** Round the counter edges with `FILLETEDGE` at 0.25".

### 4E. 3D model — long wall run

- [ ] **5.1** Each base cabinet is a box 24" × width × 34.5" starting against the wall at z=0. Use `BOX` with two corner points.
- [ ] **5.2** Shared counter on top: single box spanning the whole run.
- [ ] **5.3** Sink bowl: draw a box 25" × 19" × 9" centered in the sink base; `SUBTRACT` it from the counter to create the sink opening.
- [ ] **5.4** Range: substitute a BOX 30" × 27" × 36" on `I-FURN-APPL`. Add the range hood: box 30" × 18" × 30" mounted above.
- [ ] **5.5** Wall cabinets: boxes 12" × width × 42" at z=54". Draw them one at a time or `ARRAY` if the same width.

### 4F. Views

- [ ] **6.1** Set view to SE isometric: `VIEW SE` or the ViewCube.
- [ ] **6.2** Set visual style to `Shaded with edges`: `VISUALSTYLES` or `VSCURRENT SAW`.
- [ ] **6.3** Orbit around with `3DORBIT` and take it in.
- [ ] **6.4** `FLATSHOT` from the front view — this projects the 3D model to 2D, which can be used to overlay on the elevation for verification.

### 4G. Sheet

- [ ] **7.1** Create an ARCH-D layout. Title block.
- [ ] **7.2** Four viewports: Plan (1/2"=1'-0"), Elevation A (1/2"=1'-0"), Elevation B (1/2"=1'-0"), Isometric 3D (3/8"=1'-0").
- [ ] **7.3** Plot to `projects/04-kitchen/out/kitchen-A-201.pdf`.

## Deliverables

- `projects/04-kitchen/out/kitchen.dwg`
- `projects/04-kitchen/out/kitchen-A-201.pdf` (plan + elevations + iso on one sheet)

## Concepts she'll leave understanding

- **UCS is the drafting-plane pivot.** Elevations are drawings on vertical planes — the UCS tells AutoCAD which way is "up" on the page.
- **2D → 3D path:** polyline → region → extrude. PRESSPULL is the shortcut.
- **Booleans model reality.** A countertop with a sink cutout is a solid minus a solid.
- **3D and 2D coexist.** The 3D model can serve as a reference to verify elevation math, but the elevations themselves are often drawn as 2D for clarity and control.

# Project 5 — Living Room 3D Model + Rendered View

**Mode:** 3D advanced, materials, lighting, rendering. **Time:** 8–10 hours. **Deliverable:** a full 3D living-room model with materials applied and a rendered image composited into a plotted sheet.

## Client brief

A real-estate staging-style presentation for a coastal California living room. **Room:** 16'-0" wide × 18'-0" deep × 10'-0" ceiling. One large window (6' × 5') on one wall, plus a wide opening to a hallway on the opposite wall. Wood floor, white walls, coffered ceiling detail, coastal-contemporary furniture palette.

The deliverable is a **single rendered presentation board** that a designer could hand a client — the kind of image Callie will eventually need for her interior-design portfolio.

## Program

- Sectional sofa (120" × 84" L-shape) on one wall.
- Two lounge chairs (34" × 36") facing the sofa.
- Coffee table (48" × 24" × 16" tall).
- Area rug (96" × 120").
- Floor lamp next to one lounge chair.
- Console table (60" × 18" × 30" tall) against the wall opposite the sectional.
- Large mirror (48" × 60") above the console.
- Wall art (36" × 48") above the sofa.
- Drapery on the window — sheers.
- Recessed cans in a 4×4 grid in the coffered ceiling.

## Learning objectives

| Command | What it does |
|---|---|
| `REGION` → `EXTRUDE` / `PRESSPULL` | (Review.) 2D→3D. |
| `LOFT`, `SWEEP`, `REVOLVE` | Make complex 3D shapes — lofting section curves into a form, sweeping a profile along a path, revolving a profile around an axis. Use for molding, curved furniture legs, lamps. |
| `SOLIDEDIT` | Edit faces/edges of an existing 3D solid. |
| `MATBROWSER` | Browse AutoCAD's material library (woods, fabrics, metals, paint). |
| `MATERIALASSIGN` | Apply a material to an entity or a whole layer. |
| `RENDERMATERIALS` | Manage which materials are in the current drawing. |
| `LIGHT` (point, spot, distant) | Add discrete lights. |
| `SUNPROPERTIES` / `GEOGRAPHICLOCATION` | Use sunlight based on lat/lon + date/time — the "free lighting" of rendering. |
| `CAMERA` | Save a named viewpoint. |
| `RENDER` / `RENDERPRESETS` | Produce the raytraced image. |
| `RENDEREXPOSURE` | Control render brightness/white-balance without re-lighting. |
| Viewport with `Shaded` visual style on a layout | Put a live 3D preview on a plotted sheet. |

## Drawing checklist

### 5A. The shell

- [ ] **1.1** New drawing, architectural inches. Set workspace to `3D Modeling`.
- [ ] **1.2** Geographic location: `GEOGRAPHICLOCATION`, set to Rancho Santa Margarita (Lat 33.6404°N, Lon 117.6031°W). Set date/time to something flattering — say, April 10, 4:30 PM.
- [ ] **1.3** Draw the room footprint polyline (16' × 18') and extrude 10' up. That's a solid brick. Then hollow it: `SUBTRACT` a smaller inner box, or easier — build walls individually as thin boxes.
- [ ] **1.4** Easier shell method: four wall boxes, each 4" thick × 10' tall × appropriate length. One box for the floor (fat slab, 16' × 18' × 2"). One box for the ceiling. Leave an open wall for the hallway opening, and cut a window out with `SUBTRACT` (box-shaped void).
- [ ] **1.5** Coffered ceiling: a 4×4 grid of coffers. Each coffer is a box subtracted from the ceiling slab.

### 5B. Furniture (mix of build + block)

- [ ] **2.1** Sectional: two `BOX`es forming the L. Each ~34" × 84" × 18" seat base. Seat cushions as separate fillet-edged boxes on top.
- [ ] **2.2** Coffee table: `BOX` 48" × 24" × 16". `FILLETEDGE` the top edges by 0.5".
- [ ] **2.3** Lounge chair: the complex one. Use `LOFT` across 3 section curves to make a curved shell back, or keep it simple with boxes + a cylinder back. Good place to **try and discard** an approach to learn LOFT.
- [ ] **2.4** Floor lamp: `REVOLVE` a profile (thin rod + flared base shade) around the vertical axis to make a lathe-turned lamp body. Great REVOLVE exercise.
- [ ] **2.5** Console table: box + four cylinder legs.
- [ ] **2.6** Mirror: flat box 2" thick with a SUBTRACT inset for the frame reveal.
- [ ] **2.7** Wall art: flat box 1.5" thick. Material will come later.
- [ ] **2.8** Drapery: two sweeps. Draw a wavy polyline from floor to ceiling (the drape profile in plan). `SWEEP` that polyline along a short vertical path — or easier, draw a thin vertical rectangle profile and sweep along a wavy horizontal path. Experiment.

### 5C. Materials

- [ ] **3.1** `MATBROWSER`. Import from the library:
  - **Wood - White Oak** for floor.
  - **Paint - Interior - White** for walls + ceiling.
  - **Fabric - Linen - Oatmeal** for sofa + lounge chairs.
  - **Wood - Walnut** for coffee table + console.
  - **Metal - Brass Satin** for lamp base + hardware.
  - **Glass - Mirror** for the mirror (applies reflectivity).
  - **Fabric - Sheer White** for drapery.
  - A custom material for wall art — you can assign a JPG image from your computer. See `MATERIALEDITOR` → create new from texture.
- [ ] **3.2** Assign each material to the appropriate layer via the Materials panel (by-layer is cleaner than by-object for this scale).

### 5D. Lighting

- [ ] **4.1** Turn off default lighting: set `DEFAULTLIGHTING = 0`.
- [ ] **4.2** Sunlight is already positioned by step 1.2. Make sure `SUNSTATUS = 1`.
- [ ] **4.3** Place 16 recessed `POINT` lights or `SPOT` lights in each coffer — or use `LIGHTLISTER` after placing one and arraying. Lumens ~600 each, warm color temp (~2700K).
- [ ] **4.4** Turn on the floor lamp: a `POINT` light inside the lamp shade, ~1200 lumens.

### 5E. Cameras

- [ ] **5.1** `CAMERA` 1: standing in the hallway opening, looking in — shows whole room.
- [ ] **5.2** `CAMERA` 2: low angle from behind a lounge chair — closer, more editorial.
- [ ] **5.3** Save both as named views: `VIEW` → Save → "HERO" and "EDITORIAL".

### 5F. Render

- [ ] **6.1** `RENDERPRESETS`: start with `Medium` — fast enough to iterate.
- [ ] **6.2** `RENDER`. Save the image to `projects/05-living-room/out/render-medium.png`. Evaluate: exposure right? Shadows right? Any material wrong?
- [ ] **6.3** Iterate: tune `RENDEREXPOSURE`, swap a material, try a different time of day.
- [ ] **6.4** Final pass: `RENDERPRESETS` = `High` or `Presentation`. Output `render-final.png`.

### 5G. Presentation sheet

- [ ] **7.1** ARCH-D layout with title block.
- [ ] **7.2** Insert the rendered PNG as an image (`IMAGEATTACH`), sized to fill ~70% of the sheet.
- [ ] **7.3** Three small viewports along the edge:
  - Floor plan view (top-down, `SHADE 2D`)
  - Camera HERO view (live 3D viewport, `Shaded with edges`)
  - Material palette callout — small rectangles swatched with each material label.
- [ ] **7.4** Notes: project name, sheet number, date, lighting time.
- [ ] **7.5** Plot to `projects/05-living-room/out/living-room-presentation.pdf`.

## Deliverables

- `projects/05-living-room/out/living-room.dwg`
- `projects/05-living-room/out/render-final.png`
- `projects/05-living-room/out/living-room-presentation.pdf`

## Concepts she'll leave understanding

- **3D is a pipeline, not a command.** Model → material → light → camera → render.
- **Sunlight is often your best light.** Geographic location + date + time gives a believable baseline for free.
- **Materials are scale-aware.** A wood grain set at the wrong scale looks fake; tune it in the material editor.
- **Rendering is iterative.** First pass is always ugly. Tune and re-render.
- **Presentation boards are how designers sell a design.** Plan + rendering + material palette is a standard layout in residential design presentations.

## Post-project: portfolio

This render belongs in Callie's design portfolio. When the project wraps, add the PNG to `-callie-job/portfolio-site/` (check with rjain before committing). A rendered AutoCAD interior is a differentiator vs. Pinterest mood boards.

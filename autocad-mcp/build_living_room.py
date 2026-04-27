"""
Build Project 5 — Living Room 3D Model.

Coastal-California living room, 16' W × 18' D × 10' ceiling, with:
- Coffered ceiling (4×4 grid)
- Window 6'×5' on east wall
- Wide hallway opening on north wall
- L-shape sectional, 2 lounge chairs, coffee table, console, mirror, wall art,
  drapery on window, area rug, floor lamp
- 16 recessed cans in the coffers

Substitutions vs. the brief:
- LOFT / REVOLVE / SWEEP shapes are approximated with boxes + cylinders
  (those commands need GUI interaction)
- Real materials (MATBROWSER) substituted with ACI color proxies
- Sun + RENDER substituted with SWISO + Conceptual visual style snapshot
- ARCH-D layout sheet substituted with the deliverable Word doc + PNGs

Idempotent: drops everything in the active drawing's model space before
re-running. Saves to projects/05-living-room/out/living-room.dwg.
"""
from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from acad import Acad


DRAWING_PATH = (
    r"c:\VSCode\callie-job\-callie-job\projects\05-living-room\out\living-room.dwg"
)

# ---------- room geometry (inches) ----------
W = 192.0   # 16'-0" interior width  (X)
D = 216.0   # 18'-0" interior depth  (Y)
H = 120.0   # 10'-0" ceiling height  (Z)
WALL = 4.0
SLAB = 2.0
CEILING_TH = 4.0

# Window on east wall (x = W..W+WALL)
WIN_Y1, WIN_Y2 = 72.0, 144.0    # 6'-0" wide
WIN_Z1, WIN_Z2 = 30.0, 90.0     # 5'-0" tall, sill at 30"

# Hallway opening on north wall (y = D..D+WALL)
HALL_X1, HALL_X2 = 48.0, 144.0   # 8'-0" wide, off-center toward east
HALL_Z1, HALL_Z2 = 0.0, 96.0     # 8'-0" tall

# Coffer grid: 4x4 in ceiling
COFFER_COLS, COFFER_ROWS = 4, 4
COFFER_W = 36.0      # each coffer 36" wide in X
COFFER_D = 42.0      # each coffer 42" deep in Y
COFFER_DEPTH = 6.0   # recess up into ceiling

# ACI colors (palette continuity with Project 1)
ACI_WOOD_WARM = 40       # walnut floor
ACI_WOOD_MID = 42        # walnut for coffee/console
ACI_CREAM = 33           # cream walls
ACI_WHITE = 254          # ceiling/trim/sheer
ACI_GLASS_BLUE = 140     # mirror + window glass
ACI_DARK_GRAY = 8        # lamp metal
ACI_LINEN = 43           # oatmeal linen sofa
ACI_RUG_BLUE = 160       # area rug (coastal blue)
ACI_BRASS = 42           # brass console/lamp accents
ACI_ART = 5              # wall art accent (blue)


def clear_modelspace(a: Acad) -> int:
    """Delete every entity in model space. Idempotent re-run."""
    n = 0
    # iterate via index because Delete() invalidates iterator
    while a.doc.ModelSpace.Count > 0:
        try:
            ent = a.doc.ModelSpace.Item(0)
            ent.Delete()
            n += 1
        except Exception:
            break
    return n


def main():
    a = Acad()
    print("[1] cancel + connect")
    a.cancel(); time.sleep(0.5)
    a.connect()
    a.wait_idle(5)
    print(f"    current doc = {a.doc.Name}")

    # If we're not on the living room drawing, save current and open/create.
    if "living-room" not in a.doc.Name.lower():
        print("[1b] save current dwg")
        try:
            a.save()
        except Exception as e:
            print(f"    save current: {e}")

        out_dir = os.path.dirname(DRAWING_PATH)
        os.makedirs(out_dir, exist_ok=True)
        if os.path.exists(DRAWING_PATH):
            print(f"[1c] open existing {DRAWING_PATH}")
            a.open_drawing(DRAWING_PATH)
        else:
            print("[1c] new drawing + saveas to living-room.dwg")
            a.new_drawing()
            a.wait_idle(5)
            a.save(DRAWING_PATH)
        a.wait_idle(5)
    print(f"    active doc = {a.doc.Name}")

    print("[2] units = architectural inches; suppress dialogs")
    a.doc.SetVariable("LUNITS", 4)        # architectural
    a.doc.SetVariable("INSUNITS", 1)      # inches
    a.doc.SetVariable("DEFAULTLIGHTING", 0)
    a.doc.SetVariable("FILEDIA", 0)       # suppress file dialogs (use cmd-line)
    a.doc.SetVariable("CMDDIA", 0)        # suppress command dialogs
    a.doc.SetVariable("ATTDIA", 0)        # suppress attribute dialogs
    a.doc.SetVariable("EXPERT", 5)        # suppress most "Are you sure?" prompts

    print("[3] purge model space (idempotent)")
    n = clear_modelspace(a)
    print(f"    removed {n}")

    print("[4] layers")
    a.create_layer("A-WALL", ACI_WHITE)
    a.create_layer("A-FLOR", ACI_WOOD_WARM)
    a.create_layer("A-CLNG", ACI_WHITE)
    a.create_layer("A-TRIM", ACI_WHITE)
    a.create_layer("A-GLAZ", ACI_GLASS_BLUE)
    a.create_layer("A-DOOR", ACI_WHITE)
    a.create_layer("E-LITE", ACI_DARK_GRAY)
    a.create_layer("I-FURN", ACI_LINEN)
    a.create_layer("I-FURN-WD", ACI_WOOD_MID)
    a.create_layer("I-FURN-MTL", ACI_BRASS)
    a.create_layer("I-FURN-ART", ACI_ART)
    a.create_layer("I-FURN-RUG", ACI_RUG_BLUE)
    a.create_layer("I-FURN-DRP", ACI_WHITE)

    # ------------------------------------------------------------------
    # 5A. SHELL — floor, walls (with openings), ceiling (with coffers)
    # ------------------------------------------------------------------
    print("[5] shell")

    # Floor
    a.set_active_layer("A-FLOR")
    a.add_box([0, 0, -SLAB], [W, D, 0])

    # Build walls then subtract openings
    a.set_active_layer("A-WALL")
    south = a.add_box([-WALL, -WALL, 0], [W + WALL, 0,        H])
    north = a.add_box([-WALL,  D,    0], [W + WALL, D + WALL, H])
    west  = a.add_box([-WALL,  0,    0], [0,        D,        H])
    east  = a.add_box([ W,     0,    0], [W + WALL, D,        H])

    # Cut window opening from east wall
    print("    cut window opening (east wall)")
    a.set_active_layer("A-GLAZ")
    win_void = a.add_box([W - 1, WIN_Y1, WIN_Z1], [W + WALL + 1, WIN_Y2, WIN_Z2])
    a.boolean("subtract", [east["handle"]], [win_void["handle"]])

    # Cut hallway opening from north wall
    print("    cut hallway opening (north wall)")
    hall_void = a.add_box([HALL_X1, D - 1, HALL_Z1], [HALL_X2, D + WALL + 1, HALL_Z2])
    a.boolean("subtract", [north["handle"]], [hall_void["handle"]])

    # Ceiling slab with coffers
    print("    ceiling slab + 4x4 coffer grid")
    a.set_active_layer("A-CLNG")
    ceiling = a.add_box([0, 0, H], [W, D, H + CEILING_TH])

    # 4x4 grid centers
    coffer_voids = []
    sx = (W - COFFER_COLS * COFFER_W) / (COFFER_COLS + 1)  # margin between coffers
    sy = (D - COFFER_ROWS * COFFER_D) / (COFFER_ROWS + 1)
    for r in range(COFFER_ROWS):
        for c in range(COFFER_COLS):
            x1 = sx + c * (COFFER_W + sx)
            y1 = sy + r * (COFFER_D + sy)
            x2 = x1 + COFFER_W
            y2 = y1 + COFFER_D
            v = a.add_box([x1, y1, H + CEILING_TH - COFFER_DEPTH],
                          [x2, y2, H + CEILING_TH + 0.1])
            coffer_voids.append(v["handle"])
    # subtract all 16 from ceiling slab
    a.boolean("subtract", [ceiling["handle"]], coffer_voids)

    # Recessed cans — small disk in the center of each coffer
    print("    16 recessed cans")
    a.set_active_layer("E-LITE")
    can_handles = []
    for r in range(COFFER_ROWS):
        for c in range(COFFER_COLS):
            cx = sx + c * (COFFER_W + sx) + COFFER_W / 2
            cy = sy + r * (COFFER_D + sy) + COFFER_D / 2
            can = a.add_cylinder([cx, cy, H + CEILING_TH - COFFER_DEPTH], 3.0, 0.5)
            can_handles.append(can["handle"])

    # Window glass pane (thin)
    print("    glass pane")
    a.set_active_layer("A-GLAZ")
    a.add_box([W + WALL/2 - 0.05, WIN_Y1, WIN_Z1],
              [W + WALL/2 + 0.05, WIN_Y2, WIN_Z2])

    # ------------------------------------------------------------------
    # 5B. FURNITURE
    # ------------------------------------------------------------------
    print("[6] furniture")

    # ----- L-Sectional sofa: south leg + east leg -----
    print("    sectional sofa (L)")
    a.set_active_layer("I-FURN")
    # South leg seat & back
    a.add_box([20,   0,  0], [140,  36, 16])    # seat
    a.add_box([20,   0, 16], [140,   6, 30])    # back
    a.add_box([20,   0, 16], [ 26,  36, 24])    # left arm
    a.add_box([134,  0, 16], [140,  36, 24])    # right-arm-stub (continues L)
    # Cushions on south leg (3)
    for i, x in enumerate([26, 64, 102]):
        a.add_box([x, 6, 16], [x + 36, 30, 22])
    # East leg seat & back  (continuing the L shape forward)
    a.add_box([104, 36, 0], [140,  120, 16])    # seat
    a.add_box([134, 36, 16], [140, 120, 30])    # back
    # arm at far end
    a.add_box([104, 114, 16], [140, 120, 24])
    # Cushions on east leg (2)
    for i, y in enumerate([42, 78]):
        a.add_box([110, y, 16], [134, y + 30, 22])

    # ----- 2 Lounge chairs facing the sofa -----
    print("    2 lounge chairs")
    chairs_xy = [(10, 130), (148, 130)]
    for cx, cy in chairs_xy:
        # seat
        a.add_box([cx, cy, 0], [cx + 34, cy + 36, 16])
        # back
        a.add_box([cx, cy + 30, 16], [cx + 34, cy + 36, 32])
        # arms
        a.add_box([cx,        cy, 16], [cx + 4,  cy + 30, 22])
        a.add_box([cx + 30,   cy, 16], [cx + 34, cy + 30, 22])
        # cushion
        a.add_box([cx + 4, cy + 4, 16], [cx + 30, cy + 28, 20])

    # ----- Coffee table -----
    print("    coffee table")
    a.set_active_layer("I-FURN-WD")
    a.add_box([56, 84, 0], [104, 108, 14])      # base under top
    a.add_box([54, 82, 14], [106, 110, 16])     # top, slight overhang

    # ----- Area rug -----
    print("    area rug 8'x10'")
    a.set_active_layer("I-FURN-RUG")
    a.add_box([24, 24, 0], [120, 144, 0.25])

    # ----- Console table on west wall -----
    print("    console table + legs")
    a.set_active_layer("I-FURN-WD")
    a.add_box([0,  78, 28], [18, 138, 30])      # top
    # 4 cylindrical legs
    for lx in [1.5, 16.5]:
        for ly in [80, 136]:
            a.add_cylinder([lx, ly, 0], 1.0, 28.0)

    # ----- Mirror above console (on west wall) -----
    print("    mirror above console")
    a.set_active_layer("A-GLAZ")
    a.add_box([0, 84, 36], [2, 132, 96])

    # ----- Wall art above sofa (on south wall) -----
    print("    wall art above sofa")
    a.set_active_layer("I-FURN-ART")
    a.add_box([54, 0, 42], [102, 2, 90])        # 48" wide x 48" tall portrait

    # ----- Drapery panels at window -----
    print("    drapery panels")
    a.set_active_layer("I-FURN-DRP")
    # two panels, one each side of window
    drape_z1, drape_z2 = 24, 108
    # Left panel
    a.add_box([W - 4, 60,  drape_z1], [W - 1, 84,  drape_z2])
    # Right panel
    a.add_box([W - 4, 132, drape_z1], [W - 1, 156, drape_z2])

    # ----- Floor lamp next to chair 2 (right of east lounge chair) -----
    print("    floor lamp")
    a.set_active_layer("I-FURN-MTL")
    lamp_x, lamp_y = 184, 128
    a.add_cylinder([lamp_x, lamp_y, 0],   6.0, 2.0)    # base disk
    a.add_cylinder([lamp_x, lamp_y, 2],   1.0, 56.0)   # pole
    a.set_active_layer("I-FURN")                       # shade as fabric proxy
    a.add_cylinder([lamp_x, lamp_y, 56],  9.0, 12.0)   # shade

    # ------------------------------------------------------------------
    # 5C. View + freeze ceiling for snap legibility
    # ------------------------------------------------------------------
    print("[7] freeze ceiling for 3D legibility, set SW iso conceptual")
    try:
        a.freeze_layer("A-CLNG", freeze=True)
    except Exception as e:
        print(f"    freeze ceiling: {e}")

    try:
        a.set_view("SWISO"); a.wait_idle(5)
        a.set_visual_style("Conceptual"); a.wait_idle(5)
    except Exception as e:
        print(f"    view: {e}")
    a.zoom_extents()

    print("[8] save")
    a.save()
    print(f"    saved: {a.doc.FullName}  entities={a.doc.ModelSpace.Count}")


if __name__ == "__main__":
    main()

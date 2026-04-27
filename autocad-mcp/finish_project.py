"""
Finish Project 1 — Home Office: turn the v2 3D model into a deliverable
package an interior-design client would expect.

Adds in model space:
- A-ANNO-DIMS, A-ANNO-TEXT layers
- 5 linear dimensions (overall E-W, N-S, door, door offset, window)
- 7 numbered tag bubbles (one per FF&E item — keys to SPEC.md schedule)
- Room tag MTEXT (HOME OFFICE / size / SF / clg height)
- Designer stamp MTEXT (project info, scale, date, drawn-by)
- North arrow (filled triangle + N)

Dim variables are pre-set via SetVariable so dim text/arrows are readable
when zoomed-extents at 1/2"=1'-0" plot scale.

Idempotent: deletes any prior anno geometry by layer prefix before re-adding.
"""
from __future__ import annotations

import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from acad import Acad, _point3


# ---------- room/furniture geometry ----------
ROOM_W = 138.0   # 11'-6"
ROOM_L = 120.0   # 10'-0"
DOOR_X1, DOOR_X2 = 55.0, 87.0
WIN_Y1,  WIN_Y2  = 36.0, 84.0

# (tag #, label, x, y) — labels go in SPEC.md, only tag # appears on the plan
FURN = [
    (1, "Desk",        69, 105),
    (2, "Task Chair",  69, 75),
    (3, "Bookcase",    12, 75),
    (4, "Armchair",    117, 99),
    (5, "Side Table",  88, 99),
    (6, "Floor Lamp",  108, 76),
    (7, "Area Rug",    98, 90),
]

ACI_DIM_RED = 1
ACI_TEXT_MAGENTA = 6


def cleanup_prior_anno(a: Acad) -> int:
    to_delete = []
    for ent in a.ms:
        try:
            layer = ent.Layer
        except Exception:
            continue
        if layer.startswith("A-ANNO"):
            to_delete.append(ent)
    n = 0
    for ent in to_delete:
        try:
            ent.Delete(); n += 1
        except Exception:
            pass
    return n


def add_dim_rotated(a: Acad, p1, p2, dim_loc, rot_rad: float):
    return a.ms.AddDimRotated(_point3(p1), _point3(p2), _point3(dim_loc), float(rot_rad))


def add_mtext(a: Acad, insertion, width: float, text: str):
    return a.ms.AddMText(_point3(insertion), float(width), text)


def add_tag_bubble(a: Acad, num: int, x: float, y: float):
    """A 5"-radius circle with the FF&E tag number inside."""
    a.add_circle([x, y, 0.5], 5.0)
    # Center text near bubble center; tweak X/Y for visual centering at h=5
    label = str(num)
    offset_x = 1.6 if num >= 10 else 1.2
    a.add_text([x - offset_x, y - 2.5, 0.5], label, 5.0)


def main():
    a = Acad()
    print("[1] cancel + connect")
    a.cancel(); time.sleep(0.5)
    a.connect()
    a.wait_idle(5)
    print(f"    doc={a.doc.Name}  entities={a.doc.ModelSpace.Count}")

    # Make sure we're in plan view while constructing dims
    print("[2] TOP + 2DWireframe")
    a.set_view("TOP"); a.wait_idle(3)
    a.set_visual_style("2DWireframe"); a.wait_idle(3)
    a.freeze_layer("A-CLNG", freeze=True)

    print("[3] anno layers")
    a.create_layer("A-ANNO-DIMS", ACI_DIM_RED)
    a.create_layer("A-ANNO-TEXT", ACI_TEXT_MAGENTA)

    print("[4] purge prior annotations")
    n = cleanup_prior_anno(a)
    print(f"    removed {n}")

    print("[5] dim style sysvars")
    # SetVariable applies live to the current dim style; new dims pick these up.
    # Plot at 1/2"=1'-0" (1:24). Set DIMSCALE=24 so the plotted text/arrows
    # come out at DIMTXT/DIMASZ inches on paper.
    sv = a.doc.SetVariable
    sv("DIMSCALE", 24.0)
    sv("DIMTXT",  0.125)   # 1/8" plotted text
    sv("DIMASZ",  0.125)   # 1/8" arrowheads
    sv("DIMEXE",  0.125)   # ext line beyond dim
    sv("DIMEXO",  0.0625)  # ext line offset from origin
    sv("DIMTAD",  1.0)     # text above dim line
    sv("DIMTIH",  0.0)     # dim text aligned with dim line (off = 0)
    sv("DIMTOH",  0.0)     # outside text aligned with dim line
    sv("DIMLUNIT", 4.0)    # architectural
    sv("DIMTSZ",  0.0)     # use arrowheads, not ticks
    sv("DIMDLI",  0.5)     # baseline spacing

    print("[6] dimensions on A-ANNO-DIMS")
    a.set_active_layer("A-ANNO-DIMS")
    # Overall E-W (south side), N-S (west side)
    add_dim_rotated(a, [0, 0, 0],     [ROOM_W, 0, 0],     [ROOM_W/2, -24, 0], 0.0)
    add_dim_rotated(a, [0, 0, 0],     [0, ROOM_L, 0],     [-24, ROOM_L/2, 0], math.pi/2)
    # Door opening width
    add_dim_rotated(a, [DOOR_X1, 0, 0], [DOOR_X2, 0, 0], [(DOOR_X1+DOOR_X2)/2, -10, 0], 0.0)
    # Door offset from west wall
    add_dim_rotated(a, [0, 0, 0],     [DOOR_X1, 0, 0],   [DOOR_X1/2, -10, 0], 0.0)
    # Window opening on east wall
    add_dim_rotated(a, [ROOM_W, WIN_Y1, 0], [ROOM_W, WIN_Y2, 0],
                    [ROOM_W + 10, (WIN_Y1+WIN_Y2)/2, 0], math.pi/2)
    print("    5 dims")

    print("[7] FF&E tag bubbles + room tag + designer stamp on A-ANNO-TEXT")
    a.set_active_layer("A-ANNO-TEXT")
    for num, _label, x, y in FURN:
        add_tag_bubble(a, num, x, y)

    # Room tag — three single-line texts, centered above the room
    rt_x = ROOM_W / 2 - 24
    rt_y = ROOM_L + 12
    a.add_text([rt_x - 4, rt_y + 22, 0.5], "HOME OFFICE",                     10.0)
    a.add_text([rt_x - 12, rt_y + 8, 0.5], "11'-6\" x 10'-0\"  -  115 SF",     6.0)
    a.add_text([rt_x + 6, rt_y - 4, 0.5], "CLG: 9'-0\" AFF",                   6.0)

    # Designer stamp — below the room, left aligned
    sp_x, sp_y = -8, -28
    a.add_text([sp_x, sp_y,       0.5], "CALLIE WELLS  -  INTERIOR DESIGN",   6.0)
    a.add_text([sp_x, sp_y - 12,  0.5], "Project:  Home Office Conversion",   4.0)
    a.add_text([sp_x, sp_y - 22,  0.5], "Client:   Rancho Santa Margarita, CA", 4.0)
    a.add_text([sp_x, sp_y - 32,  0.5], "Sheet A-101  -  Floor Plan & FF&E Tags", 4.0)
    a.add_text([sp_x, sp_y - 42,  0.5], "Scale 1/2\" = 1'-0\"   Date 2026-04-25", 4.0)

    # North arrow at NE, outside the room
    north_x, north_y = ROOM_W + 22, ROOM_L - 14
    a.add_polyline(
        [[north_x, north_y - 8], [north_x + 4, north_y + 8],
         [north_x - 4, north_y + 8], [north_x, north_y - 8]],
        closed=True,
    )
    a.add_text([north_x - 3.5, north_y + 11, 0.5], "N", 9.0)
    print("    7 bubbles + room tag + stamp + north arrow")

    print("[8] save")
    a.save()
    print(f"    saved: {a.doc.FullName}  entities={a.doc.ModelSpace.Count}")


if __name__ == "__main__":
    main()

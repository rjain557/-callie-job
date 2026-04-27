"""Living Room — annotate the plan with dims, FF&E tag bubbles, room tag,
designer stamp, north arrow."""
from __future__ import annotations
import math, os, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from acad import Acad, _point3


W, D, H = 192.0, 216.0, 120.0
WIN_Y1, WIN_Y2 = 72.0, 144.0
HALL_X1, HALL_X2 = 48.0, 144.0

# (tag, label, x, y) — labels appear in SPEC.md schedule, not on the plan
FURN = [
    (1, "Sectional Sofa",  80, 18),
    (2, "Lounge L",        27, 148),
    (3, "Lounge R",       165, 148),
    (4, "Coffee Table",    80, 96),
    (5, "Console",          9, 108),
    (6, "Mirror",           1, 108),
    (7, "Wall Art",        78, 1),
    (8, "Drapery L",      178, 72),
    (9, "Drapery R",      178, 144),
    (10,"Area Rug",        72, 84),
    (11,"Floor Lamp",     184, 128),
]

ACI_DIM_RED = 1
ACI_TEXT_MAGENTA = 6


def cleanup_prior_anno(a: Acad) -> int:
    targets = []
    for ent in a.ms:
        try:
            if ent.Layer.startswith("A-ANNO"):
                targets.append(ent)
        except Exception:
            pass
    n = 0
    for ent in targets:
        try: ent.Delete(); n += 1
        except Exception: pass
    return n


def add_dim_rotated(a: Acad, p1, p2, dim_loc, rot_rad: float):
    return a.ms.AddDimRotated(_point3(p1), _point3(p2), _point3(dim_loc), float(rot_rad))


def add_tag_bubble(a: Acad, num: int, x: float, y: float):
    a.add_circle([x, y, 0.5], 5.0)
    label = str(num)
    offx = 1.6 if num >= 10 else 1.2
    a.add_text([x - offx, y - 2.5, 0.5], label, 5.0)


def main():
    a = Acad(); a.cancel(); time.sleep(0.3); a.connect(); a.wait_idle(5)
    print(f"doc={a.doc.Name} entities={a.doc.ModelSpace.Count}", flush=True)
    sv = a.doc.SetVariable
    sv("FILEDIA", 0); sv("CMDDIA", 0); sv("EXPERT", 5)

    a.set_view("TOP"); a.wait_idle(3)
    a.set_visual_style("2DWireframe"); a.wait_idle(3)
    try: a.freeze_layer("A-CLNG", freeze=True)
    except Exception: pass

    a.create_layer("A-ANNO-DIMS", ACI_DIM_RED)
    a.create_layer("A-ANNO-TEXT", ACI_TEXT_MAGENTA)
    n = cleanup_prior_anno(a)
    print(f"removed {n} prior anno entities", flush=True)

    # Plot scale 1/4" = 1'-0" → DIMSCALE = 48 (room is bigger than home office)
    sv("DIMSCALE", 48.0)
    sv("DIMTXT", 0.125)
    sv("DIMASZ", 0.125)
    sv("DIMEXE", 0.125)
    sv("DIMEXO", 0.0625)
    sv("DIMTAD", 1.0)
    sv("DIMTIH", 0.0)
    sv("DIMTOH", 0.0)
    sv("DIMLUNIT", 4.0)
    sv("DIMTSZ", 0.0)

    print("[dims]", flush=True)
    a.set_active_layer("A-ANNO-DIMS")
    add_dim_rotated(a, [0, 0, 0],     [W, 0, 0],     [W/2, -36, 0], 0.0)
    add_dim_rotated(a, [0, 0, 0],     [0, D, 0],     [-36, D/2, 0], math.pi/2)
    add_dim_rotated(a, [HALL_X1, D, 0], [HALL_X2, D, 0],
                    [(HALL_X1+HALL_X2)/2, D + 18, 0], 0.0)
    add_dim_rotated(a, [W, WIN_Y1, 0], [W, WIN_Y2, 0],
                    [W + 18, (WIN_Y1+WIN_Y2)/2, 0], math.pi/2)

    print("[tags]", flush=True)
    a.set_active_layer("A-ANNO-TEXT")
    for num, _label, x, y in FURN:
        add_tag_bubble(a, num, x, y)

    # Room tag — three single-line texts, north of the room
    rt_x, rt_y = W/2 - 30, D + 30
    a.add_text([rt_x,      rt_y + 24, 0.5], "LIVING ROOM",                  14.0)
    a.add_text([rt_x - 8,  rt_y + 8,  0.5], "16'-0\" x 18'-0\"  -  288 SF", 8.0)
    a.add_text([rt_x + 8,  rt_y - 6,  0.5], "CLG: 10'-0\" AFF",             8.0)

    # Designer stamp — south, below the dim line
    sp_x, sp_y = -8, -52
    a.add_text([sp_x, sp_y,        0.5], "CALLIE WELLS  -  INTERIOR DESIGN",   8.0)
    a.add_text([sp_x, sp_y - 14,   0.5], "Project:  Coastal Living Room",       6.0)
    a.add_text([sp_x, sp_y - 26,   0.5], "Client:   Rancho Santa Margarita, CA", 6.0)
    a.add_text([sp_x, sp_y - 38,   0.5], "Sheet A-501  -  Floor Plan & FF&E Tags", 6.0)
    a.add_text([sp_x, sp_y - 50,   0.5], "Scale 1/4\" = 1'-0\"   Date 2026-04-27", 6.0)

    # North arrow, NE of room
    nx, ny = W + 30, D - 18
    a.add_polyline(
        [[nx, ny - 10], [nx + 5, ny + 10], [nx - 5, ny + 10], [nx, ny - 10]],
        closed=True,
    )
    a.add_text([nx - 4, ny + 14, 0.5], "N", 12.0)

    a.save()
    print(f"DONE entities={a.doc.ModelSpace.Count}", flush=True)


if __name__ == "__main__":
    main()

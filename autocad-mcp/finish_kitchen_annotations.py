"""Kitchen — annotate the plan with dims, FF&E tag bubbles, room tag,
designer stamp, north arrow."""
from __future__ import annotations
import math, os, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from acad import Acad, _point3


W, D, H = 168.0, 120.0, 120.0

# (tag, label, x, y) — labels appear in SPEC.md schedule
FURN = [
    (1,  "B36",     18,  12),
    (2,  "Range",   51,  14),
    (3,  "DW",      78,  12),
    (4,  "SB36",   108,  12),
    (5,  "B30",    141,  12),
    (6,  "Pantry", 162,  12),
    (7,  "Hood",    51,  9),     # bubble below range
    (8,  "Island",  84,  72),    # center of island
    (9,  "Sink",   113,  13),    # over sink area
    (10, "Counter", 30,  21),    # near front edge of counter
    (11, "Faucet", 113, 23),
]

ACI_DIM_RED = 1
ACI_TEXT_MAGENTA = 6


def cleanup_prior_anno(a: Acad) -> int:
    targets = [e for e in a.ms if e.Layer.startswith("A-ANNO")]
    n = 0
    for ent in targets:
        try: ent.Delete(); n += 1
        except Exception: pass
    return n


def add_dim_rotated(a: Acad, p1, p2, dim_loc, rot_rad: float):
    return a.ms.AddDimRotated(_point3(p1), _point3(p2), _point3(dim_loc), float(rot_rad))


def add_tag_bubble(a: Acad, num: int, x: float, y: float):
    a.add_circle([x, y, 0.5], 4.0)
    label = str(num)
    offx = 1.4 if num >= 10 else 1.0
    a.add_text([x - offx, y - 2.0, 0.5], label, 4.0)


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
    print(f"removed {n} prior anno", flush=True)

    sv("DIMSCALE", 24.0)
    sv("DIMTXT", 0.125); sv("DIMASZ", 0.125)
    sv("DIMEXE", 0.125); sv("DIMEXO", 0.0625)
    sv("DIMTAD", 1.0); sv("DIMTIH", 0.0); sv("DIMTOH", 0.0)
    sv("DIMLUNIT", 4.0); sv("DIMTSZ", 0.0)

    print("[dims]", flush=True)
    a.set_active_layer("A-ANNO-DIMS")
    # Overall E-W
    add_dim_rotated(a, [0, 0, 0], [W, 0, 0], [W/2, -22, 0], 0.0)
    # Overall N-S
    add_dim_rotated(a, [0, 0, 0], [0, D, 0], [-22, D/2, 0], math.pi/2)
    # Cabinet run: chain dims along south wall
    cab_x = [0, 36, 66, 90, 126, 156, 168]
    for i in range(len(cab_x) - 1):
        x1, x2 = cab_x[i], cab_x[i + 1]
        add_dim_rotated(a, [x1, 0, 0], [x2, 0, 0],
                         [(x1 + x2) / 2, -10, 0], 0.0)
    # Island W
    add_dim_rotated(a, [36, 51, 0], [132, 51, 0], [84, 47, 0], 0.0)
    # Island D (with overhang)
    add_dim_rotated(a, [36, 51, 0], [36, 105, 0], [30, 78, 0], math.pi/2)

    print("[tags]", flush=True)
    a.set_active_layer("A-ANNO-TEXT")
    for num, _label, x, y in FURN:
        add_tag_bubble(a, num, x, y)

    # Room tag — north of room
    rt_x, rt_y = W/2 - 24, D + 12
    a.add_text([rt_x,      rt_y + 22, 0.5], "KITCHEN",                   12.0)
    a.add_text([rt_x - 10, rt_y + 8,  0.5], "14'-0\" x 10'-0\"  -  140 SF", 6.0)
    a.add_text([rt_x + 6,  rt_y - 4,  0.5], "CLG: 10'-0\" AFF",           6.0)

    # Designer stamp — south, below dim line
    sp_x, sp_y = -8, -42
    a.add_text([sp_x, sp_y,        0.5], "CALLIE WELLS  -  INTERIOR DESIGN", 6.0)
    a.add_text([sp_x, sp_y - 12,   0.5], "Project:  Kitchen Casework",        4.0)
    a.add_text([sp_x, sp_y - 22,   0.5], "Client:   Rancho Santa Margarita, CA", 4.0)
    a.add_text([sp_x, sp_y - 32,   0.5], "Sheet A-201  -  Plan, Elevations & 3D", 4.0)
    a.add_text([sp_x, sp_y - 42,   0.5], "Scale 1/2\" = 1'-0\"   Date 2026-04-27", 4.0)

    # North arrow, NE of room
    nx, ny = W + 22, D - 14
    a.add_polyline(
        [[nx, ny - 8], [nx + 4, ny + 8], [nx - 4, ny + 8], [nx, ny - 8]],
        closed=True,
    )
    a.add_text([nx - 2.5, ny + 11, 0.5], "N", 9.0)

    a.save()
    print(f"DONE entities={a.doc.ModelSpace.Count}", flush=True)


if __name__ == "__main__":
    main()

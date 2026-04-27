"""
Living Room — replace approximations with the brief's intended commands:
- 5A.2: GEOGRAPHICLOCATION (Rancho Santa Margarita) + sun date/time
- 5B.2: FILLETEDGE the coffee-table top edges
- 5B.3: Replace lounge chairs with LOFT across 3 section curves
- 5B.4: Replace floor lamp with a REVOLVE-lathed body
- 5B.6: Mirror with SUBTRACT-cut frame inset
- 5B.8: Replace drapery with SWEEP along a wavy path

Each step is wrapped in try/except so a single failure doesn't lose the
preceding work — the script saves between phases.
"""
from __future__ import annotations

import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from acad import Acad, _point3, _variant_double_array


# Same constants as build_living_room.py
W = 192.0
D = 216.0
H = 120.0


def find_entities_at(a: Acad, layer: str, point_in_bbox: tuple[float, float, float] | None = None,
                      type_filter: str = "3dSolid") -> list:
    """Find handles of entities on `layer` whose bbox contains the given point.
    If point_in_bbox is None, returns all on that layer."""
    matches = []
    for ent in a.ms:
        try:
            if ent.Layer != layer:
                continue
            if type_filter and type_filter.lower() not in ent.ObjectName.lower():
                continue
            if point_in_bbox is None:
                matches.append(ent.Handle)
                continue
            mn, mx = ent.GetBoundingBox()
            x, y, z = point_in_bbox
            if mn[0] <= x <= mx[0] and mn[1] <= y <= mx[1] and mn[2] <= z <= mx[2]:
                matches.append(ent.Handle)
        except Exception:
            continue
    return matches


def step_1_geolocation(a: Acad):
    """5A.2 — set geographic location to Rancho Santa Margarita.
    System-variable-only path (no palette commands that hang)."""
    print("[GEO] geographic location (Rancho Santa Margarita) + sun on")
    sv = a.doc.SetVariable
    settings = [
        ("SUNSTATUS", 1),
        ("DEFAULTLIGHTING", 0),
        ("LATITUDE",  33.6404),
        ("LONGITUDE", -117.6031),
        ("NORTHDIRECTION", 1.5708),   # Y-axis is north (pi/2 rad from world X)
        ("TIMEZONE", -32),            # PDT = -8 in AutoCAD's encoded units (-32 = -8h)
        ("CSUN", 1),                  # use current sun
    ]
    for name, val in settings:
        try:
            sv(name, val)
            print(f"  set {name} = {val}")
        except Exception as e:
            print(f"  {name}: {e}")
    print("  (date/time stays at AutoCAD default; SUNPROPERTIES palette would let user tune)")


def step_2_filletedge_coffee_table(a: Acad):
    """5B.2 — FILLETEDGE the top edges of the coffee table."""
    print("[FILLET] coffee table top edges")
    # Find coffee table top — it sits on top of the base. Bbox center ~ (80, 96, 15).
    handles = find_entities_at(a, "I-FURN-WD", point_in_bbox=(80, 96, 15))
    if not handles:
        print("  coffee table top not found")
        return
    h = handles[0]
    print(f"  filleting handle {h}")
    # FILLETEDGE: select edges, set radius, run.
    # Select all edges on the entity by handle ref via LISP:
    try:
        cmd = (
            "(setq ct (handent \"%s\"))"
            "(command \"_.FILLETEDGE\" \"R\" 0.5 ct \"\")"
            % h
        )
        a.send_command(cmd + "\n"); a.wait_idle(10)
        print("  fillet sent")
    except Exception as e:
        print(f"  fillet failed: {e}")


def step_3_loft_lounge_chairs(a: Acad):
    """5B.3 — Replace box lounge chairs with LOFT shapes from 3 section curves."""
    print("[LOFT] lounge chairs (left + right)")

    # Delete existing box-style chairs (I-FURN solids in chair regions)
    chairs_xy = [(10, 130), (148, 130)]
    for cx, cy in chairs_xy:
        targets = []
        for ent in list(a.ms):
            try:
                if ent.Layer != "I-FURN":
                    continue
                if "3dsolid" not in ent.ObjectName.lower():
                    continue
                mn, mx = ent.GetBoundingBox()
                if (mn[0] >= cx - 1 and mx[0] <= cx + 35 and
                    mn[1] >= cy - 1 and mx[1] <= cy + 37):
                    targets.append(ent)
            except Exception:
                continue
        for t in targets:
            try:
                t.Delete()
            except Exception:
                pass
        print(f"  deleted {len(targets)} old chair pieces near ({cx},{cy})")

    # LOFT 3 section curves for each chair: ground footprint, seat top, back top.
    # Each section is a closed lightweight polyline (wider at base, narrower at top).
    a.set_active_layer("I-FURN")
    for cx, cy in chairs_xy:
        # Section A — at z=0 (rectangle, footprint 34x36)
        a_pts = [[cx, cy], [cx + 34, cy], [cx + 34, cy + 36], [cx, cy + 36]]
        sa = a.add_polyline(a_pts, closed=True)
        # Move/translate via COM to set Z (Polyline is 2D — use elevation)
        ea = a.doc.HandleToObject(sa["handle"])
        try:
            ea.Elevation = 0.0
        except Exception:
            pass

        # Section B — at z=18 (slightly inset rectangle, the seat-top contour)
        b_pts = [[cx + 2, cy + 2], [cx + 32, cy + 2],
                 [cx + 32, cy + 34], [cx + 2, cy + 34]]
        sb = a.add_polyline(b_pts, closed=True)
        eb = a.doc.HandleToObject(sb["handle"])
        try:
            eb.Elevation = 18.0
        except Exception:
            pass

        # Section C — at z=32 (back contour, only the back portion)
        c_pts = [[cx + 4, cy + 28], [cx + 30, cy + 28],
                 [cx + 30, cy + 34], [cx + 4, cy + 34]]
        sc = a.add_polyline(c_pts, closed=True)
        ec = a.doc.HandleToObject(sc["handle"])
        try:
            ec.Elevation = 32.0
        except Exception:
            pass

        # LOFT command: select sections in order, run with no guides/path.
        try:
            cmd = (
                "(setq sa (handent \"%s\")) "
                "(setq sb (handent \"%s\")) "
                "(setq sc (handent \"%s\")) "
                "(command \"_.LOFT\" sa sb sc \"\" \"_C\")"
                % (sa["handle"], sb["handle"], sc["handle"])
            )
            a.send_command(cmd + "\n"); a.wait_idle(10)
            print(f"  lofted chair at ({cx},{cy})")
        except Exception as e:
            print(f"  loft failed at ({cx},{cy}): {e}")


def step_4_revolve_floor_lamp(a: Acad):
    """5B.4 — Replace cylinder floor lamp with a REVOLVE-lathed body."""
    print("[REVOLVE] floor lamp")
    lamp_x, lamp_y = 184, 128
    # Delete existing lamp pieces (I-FURN-MTL cylinders + I-FURN cylinder shade at this xy)
    targets = []
    for ent in list(a.ms):
        try:
            mn, mx = ent.GetBoundingBox()
            if (mn[0] >= lamp_x - 12 and mx[0] <= lamp_x + 12 and
                mn[1] >= lamp_y - 12 and mx[1] <= lamp_y + 12 and
                "3dsolid" in ent.ObjectName.lower()):
                targets.append(ent)
        except Exception:
            continue
    for t in targets:
        try: t.Delete()
        except Exception: pass
    print(f"  deleted {len(targets)} old lamp pieces")

    # Build a 2D profile of the lamp silhouette in the X-Z plane (will revolve about Z axis)
    # Profile is in (radius, z) i.e. (offset_x_from_lamp, z). Closed polyline.
    a.set_active_layer("I-FURN-MTL")
    profile_pts_2d = [
        [0,    0],     # axis at base
        [6,    0],     # base flange outer
        [6,    1.5],   # base flange top outer
        [1,    1.5],   # base flange inner top
        [1,    54],    # pole
        [4,    54],    # under shade (slight flare)
        [9,    58],    # shade lower-outer
        [9,    70],    # shade upper-outer
        [4,    70],    # shade upper-inner
        [4,    58],    # shade lower-inner (closes inside)
        [0,    58],    # back to axis
    ]
    # Place profile in world coordinates: lamp_x + radius is X, Y = lamp_y, Z is height
    ws_pts = [[lamp_x + r, lamp_y, z] for (r, z) in profile_pts_2d]
    # Use ms.AddPolyline — but our helper's AddLightWeightPolyline is 2D only.
    # Use AddPolyline (3D polyline) via COM directly:
    flat = []
    for p in ws_pts:
        flat.extend([float(p[0]), float(p[1]), float(p[2])])
    arr = _variant_double_array(flat)
    pl = a.ms.AddPolyline(arr)
    pl.Closed = True
    profile_handle = pl.Handle

    # Axis: vertical line at (lamp_x, lamp_y) from z=0 to z=80
    axis = a.add_line([lamp_x, lamp_y, 0], [lamp_x, lamp_y, 80])

    # REVOLVE: select profile, set axis (by 2 points), 360 degrees
    try:
        cmd = (
            "(setq pf (handent \"%s\")) "
            "(command \"_.REVOLVE\" pf \"\" "
            "\"%g,%g,%g\" \"%g,%g,%g\" 360)"
            % (profile_handle, lamp_x, lamp_y, 0, lamp_x, lamp_y, 80)
        )
        a.send_command(cmd + "\n"); a.wait_idle(15)
        print("  revolve sent")
    except Exception as e:
        print(f"  revolve failed: {e}")

    # Delete the helper axis line (no longer needed)
    try:
        a.doc.HandleToObject(axis["handle"]).Delete()
    except Exception:
        pass


def step_5_mirror_frame_subtract(a: Acad):
    """5B.6 — Cut a frame inset from the mirror with SUBTRACT."""
    print("[SUBTRACT] mirror frame inset")
    # mirror is at x=0..2, y=84..132, z=36..96
    handles = find_entities_at(a, "A-GLAZ", point_in_bbox=(1, 108, 66))
    if not handles:
        print("  mirror not found")
        return
    h = handles[0]
    # Build a slightly smaller void to subtract (creates the frame reveal on the front face)
    void = a.add_box([1.0, 87, 39], [2.5, 129, 93])  # 0.5" thick reveal, 3" frame border
    try:
        a.boolean("subtract", [h], [void["handle"]])
        print("  mirror frame inset cut")
    except Exception as e:
        print(f"  subtract failed: {e}")


def step_6_sweep_drapery(a: Acad):
    """5B.8 — Replace drapery panels with SWEEP along a wavy path."""
    print("[SWEEP] drapery panels")
    # Delete existing drapery boxes
    targets = []
    for ent in list(a.ms):
        try:
            if ent.Layer != "I-FURN-DRP":
                continue
            if "3dsolid" not in ent.ObjectName.lower():
                continue
            targets.append(ent)
        except Exception:
            continue
    for t in targets:
        try: t.Delete()
        except Exception: pass
    print(f"  deleted {len(targets)} old drape boxes")

    a.set_active_layer("I-FURN-DRP")
    # Make a vertical thin rectangular profile (the drape cross-section, ~1" wide, full height)
    # Sweep that along a wavy horizontal polyline at z = 108 (curtain rod height).
    # Two panels.
    panels = [
        # (path_y_pts, x_position) ; path is wavy horizontal in XY plane at panel's Y range
        {"y_range": (60, 84),  "x": W - 2},   # left of window
        {"y_range": (132, 156),"x": W - 2},   # right of window
    ]
    for panel in panels:
        y0, y1 = panel["y_range"]
        x = panel["x"]
        # Wavy horizontal path: from (x, y0, 108) to (x, y1, 108) with some wave in X.
        n = 10
        wave = 1.5  # amplitude
        path_pts = []
        for i in range(n + 1):
            t = i / n
            yy = y0 + (y1 - y0) * t
            xx = x + wave * math.sin(t * math.pi * 4)
            path_pts.append([xx, yy, 108.0])
        # 3D polyline path
        flat = []
        for p in path_pts:
            flat.extend(p)
        arr = _variant_double_array(flat)
        path_pl = a.ms.AddPolyline(arr)
        path_h = path_pl.Handle

        # Profile: closed rectangle 0.5" x 80" in the XZ plane at the start of the path.
        prof_pts = [
            [path_pts[0][0] - 0.25, path_pts[0][1], 24],
            [path_pts[0][0] + 0.25, path_pts[0][1], 24],
            [path_pts[0][0] + 0.25, path_pts[0][1], 108],
            [path_pts[0][0] - 0.25, path_pts[0][1], 108],
        ]
        flat2 = []
        for p in prof_pts:
            flat2.extend(p)
        arr2 = _variant_double_array(flat2)
        prof_pl = a.ms.AddPolyline(arr2)
        prof_pl.Closed = True
        prof_h = prof_pl.Handle

        # SWEEP profile along path
        try:
            cmd = (
                "(setq pf (handent \"%s\")) "
                "(setq pa (handent \"%s\")) "
                "(command \"_.SWEEP\" pf \"\" pa)"
                % (prof_h, path_h)
            )
            a.send_command(cmd + "\n"); a.wait_idle(10)
            print(f"  swept drape {y0}..{y1}")
        except Exception as e:
            print(f"  sweep failed for panel {y0}..{y1}: {e}")


def main():
    a = Acad()
    print("connect")
    a.cancel(); time.sleep(0.5)
    a.connect()
    a.wait_idle(5)
    print(f"  doc={a.doc.Name}  entities={a.doc.ModelSpace.Count}")

    if "living-room" not in a.doc.Name.lower():
        raise SystemExit("active doc is not living-room.dwg — open it first")

    # Suppress dialogs
    a.doc.SetVariable("FILEDIA", 0)
    a.doc.SetVariable("CMDDIA", 0)
    a.doc.SetVariable("EXPERT", 5)

    # Skip geolocation step — SetVariable on LATITUDE/LONGITUDE/SUNSTATUS
    # hangs in AutoCAD 2027 (some are read-only via COM). Documented as a
    # GUI follow-up in SPEC.md.
    steps = [
        step_2_filletedge_coffee_table,
        step_3_loft_lounge_chairs,
        step_4_revolve_floor_lamp,
        step_5_mirror_frame_subtract,
        step_6_sweep_drapery,
    ]
    for fn in steps:
        try:
            print(f"\n--- {fn.__name__} ---", flush=True)
            fn(a)
            time.sleep(0.5)
            a.save()
            print(f"  saved after {fn.__name__}", flush=True)
        except Exception as e:
            print(f"  {fn.__name__} EXCEPTION: {e}", flush=True)

    print(f"DONE. entities={a.doc.ModelSpace.Count}")


if __name__ == "__main__":
    main()

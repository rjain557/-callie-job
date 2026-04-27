"""Resume after REVOLVE crash — finish mirror SUBTRACT and SWEEP drapery."""
from __future__ import annotations
import math, os, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from acad import Acad, _variant_double_array


def find_at(a: Acad, layer: str, point):
    matches = []
    for ent in list(a.ms):
        try:
            if ent.Layer != layer or "3dsolid" not in ent.ObjectName.lower():
                continue
            mn, mx = ent.GetBoundingBox()
            if (mn[0] <= point[0] <= mx[0] and mn[1] <= point[1] <= mx[1]
                and mn[2] <= point[2] <= mx[2]):
                matches.append(ent.Handle)
        except Exception:
            pass
    return matches


def mirror_frame(a: Acad):
    print("[mirror] subtract frame inset", flush=True)
    h = find_at(a, "A-GLAZ", (1.0, 108.0, 66.0))
    if not h:
        print("  mirror not found"); return
    print(f"  mirror handle = {h[0]}", flush=True)
    void = a.add_box([1.0, 87, 39], [2.5, 129, 93])
    a.boolean("subtract", [h[0]], [void["handle"]])
    print("  done", flush=True)


def sweep_drapery(a: Acad):
    print("[sweep] drapery panels", flush=True)
    # Delete existing drape boxes
    targets = [e for e in list(a.ms)
               if e.Layer == "I-FURN-DRP" and "3dsolid" in e.ObjectName.lower()]
    for t in targets:
        try: t.Delete()
        except Exception: pass
    print(f"  deleted {len(targets)} old drape boxes", flush=True)

    a.set_active_layer("I-FURN-DRP")
    W = 192.0
    panels = [(60, 84), (132, 156)]
    for y0, y1 in panels:
        x = W - 2
        n = 10
        wave = 1.5
        path_pts = []
        for i in range(n + 1):
            t = i / n
            yy = y0 + (y1 - y0) * t
            xx = x + wave * math.sin(t * math.pi * 4)
            path_pts.append([xx, yy, 108.0])
        flat = []
        for p in path_pts:
            flat.extend(p)
        path_pl = a.ms.AddPolyline(_variant_double_array(flat))
        path_h = path_pl.Handle

        prof_pts = [
            [path_pts[0][0] - 0.25, path_pts[0][1], 24],
            [path_pts[0][0] + 0.25, path_pts[0][1], 24],
            [path_pts[0][0] + 0.25, path_pts[0][1], 108],
            [path_pts[0][0] - 0.25, path_pts[0][1], 108],
        ]
        flat2 = []
        for p in prof_pts:
            flat2.extend(p)
        prof_pl = a.ms.AddPolyline(_variant_double_array(flat2))
        prof_pl.Closed = True
        prof_h = prof_pl.Handle

        cmd = (
            f'(setq pf (handent "{prof_h}")) '
            f'(setq pa (handent "{path_h}")) '
            f'(command "_.SWEEP" pf "" pa)\n'
        )
        a.send_command(cmd)
        print(f"  swept {y0}..{y1}", flush=True)
        time.sleep(2)
        a.wait_idle(15)


def main():
    a = Acad()
    a.cancel(); time.sleep(0.5)
    a.connect(); a.wait_idle(5)
    print(f"doc={a.doc.Name} entities={a.doc.ModelSpace.Count}", flush=True)

    a.doc.SetVariable("FILEDIA", 0)
    a.doc.SetVariable("CMDDIA", 0)
    a.doc.SetVariable("EXPERT", 5)

    try:
        mirror_frame(a)
        a.save()
    except Exception as e:
        print(f"  mirror_frame: {e}", flush=True)

    try:
        sweep_drapery(a)
        a.save()
    except Exception as e:
        print(f"  sweep_drapery: {e}", flush=True)

    print(f"DONE entities={a.doc.ModelSpace.Count}", flush=True)


if __name__ == "__main__":
    main()

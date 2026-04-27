"""Minimal test: FILLETEDGE the coffee table top."""
from __future__ import annotations
import os, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from acad import Acad


def main():
    a = Acad()
    print("connect", flush=True)
    a.cancel(); time.sleep(0.5)
    a.connect(); a.wait_idle(5)
    print(f"  doc={a.doc.Name}", flush=True)

    a.doc.SetVariable("FILEDIA", 0)
    a.doc.SetVariable("CMDDIA", 0)
    a.doc.SetVariable("EXPERT", 5)

    # find coffee table top — bbox center ~ (80, 96, 15)
    target = None
    for ent in list(a.ms):
        try:
            if ent.Layer != "I-FURN-WD":
                continue
            if "3dsolid" not in ent.ObjectName.lower():
                continue
            mn, mx = ent.GetBoundingBox()
            cx = (mn[0] + mx[0]) / 2
            cy = (mn[1] + mx[1]) / 2
            cz = (mn[2] + mx[2]) / 2
            # Top piece sits z=14..16
            if 70 < cx < 110 and 80 < cy < 110 and 14 < cz < 16:
                target = ent
                break
        except Exception:
            continue

    if not target:
        print("  no coffee top found"); return
    h = target.Handle
    print(f"  target={h}", flush=True)

    # Try FILLETEDGE via SendCommand with select-by-handent
    cmd = (
        f'(setq ct (handent "{h}")) '
        f'(command "_.FILLETEDGE" "_R" 0.5 ct "")\n'
    )
    print(f"  sending: {cmd.strip()}", flush=True)
    a.send_command(cmd)
    print("  waiting...", flush=True)
    idle = a.wait_idle(20)
    print(f"  idle={idle}", flush=True)
    a.save()
    print(f"  saved, entities={a.doc.ModelSpace.Count}", flush=True)


if __name__ == "__main__":
    main()

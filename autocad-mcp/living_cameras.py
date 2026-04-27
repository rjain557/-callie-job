"""Living Room — 5E. Save HERO and EDITORIAL named camera views.

Uses VIEW _3DV (3D view) which is the modern CAMERA-equivalent:
takes camera position + target and saves as a named view.
"""
from __future__ import annotations
import os, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from acad import Acad


def main():
    a = Acad(); a.cancel(); time.sleep(0.3); a.connect(); a.wait_idle(5)
    print(f"doc={a.doc.Name} entities={a.doc.ModelSpace.Count}", flush=True)
    sv = a.doc.SetVariable
    sv("FILEDIA", 0); sv("CMDDIA", 0); sv("EXPERT", 5)

    cams = [
        # name, cam pos, target
        ("HERO",      (96, 240, 66),  (96, 108, 42)),
        ("EDITORIAL", (168, 170, 30), (96, 80, 30)),
    ]
    for name, (px, py, pz), (tx, ty, tz) in cams:
        # CAMERA then position, target, then eXit
        cmd = (f'_.CAMERA\n{px},{py},{pz}\n{tx},{ty},{tz}\nX\n')
        try:
            a.send_command(cmd)
            time.sleep(0.5)
            a.wait_idle(8)
            # Save as named view
            a.send_command(f'_.-VIEW\n_S\n{name}\n')
            time.sleep(0.3)
            a.wait_idle(8)
            print(f"  {name}: cam={px,py,pz} target={tx,ty,tz}", flush=True)
        except Exception as e:
            print(f"  {name}: {e}", flush=True)
    a.save()
    print(f"DONE", flush=True)


if __name__ == "__main__":
    main()

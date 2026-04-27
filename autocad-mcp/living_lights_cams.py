"""Living Room — 5D lights + 5E cameras only. Materials already done."""
from __future__ import annotations
import os, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from acad import Acad


W, D, H = 192.0, 216.0, 120.0
COFFER_COLS, COFFER_ROWS = 4, 4
COFFER_W, COFFER_D = 36.0, 42.0


def main():
    a = Acad()
    a.cancel(); time.sleep(0.5)
    a.connect(); a.wait_idle(5)
    print(f"doc={a.doc.Name} entities={a.doc.ModelSpace.Count}", flush=True)
    sv = a.doc.SetVariable
    sv("FILEDIA", 0); sv("CMDDIA", 0); sv("EXPERT", 5)
    try:
        sv("DEFAULTLIGHTING", 0)
        print("DEFAULTLIGHTING=0", flush=True)
    except Exception as e:
        print(f"DEFAULTLIGHTING: {e}", flush=True)

    # -------- 16 recessed cans --------
    # AutoCAD prompts on POINTLIGHT for "[Lighting unit not currently set...]"
    # First time. Acknowledge by setting LIGHTINGUNITS=2 (photometric, intl).
    try:
        sv("LIGHTINGUNITS", 2)
        print("LIGHTINGUNITS=2 (photometric)", flush=True)
    except Exception as e:
        print(f"LIGHTINGUNITS: {e}", flush=True)

    print("[16 cans]", flush=True)
    sx = (W - COFFER_COLS * COFFER_W) / (COFFER_COLS + 1)
    sy = (D - COFFER_ROWS * COFFER_D) / (COFFER_ROWS + 1)
    placed = 0
    for r in range(COFFER_ROWS):
        for c in range(COFFER_COLS):
            cx = sx + c * (COFFER_W + sx) + COFFER_W / 2
            cy = sy + r * (COFFER_D + sy) + COFFER_D / 2
            cz = H - 0.5
            # Minimal POINTLIGHT: just position + exit (X) — accept defaults.
            cmd = f'_.POINTLIGHT\n{cx},{cy},{cz}\nX\n'
            try:
                a.send_command(cmd)
                time.sleep(0.3)
                a.wait_idle(5)
                placed += 1
            except Exception as e:
                print(f"  {r},{c}: {e}", flush=True)
                break
    print(f"  placed {placed}/16", flush=True)
    a.save()

    # -------- floor lamp light --------
    print("[lamp light]", flush=True)
    try:
        a.send_command(f'_.POINTLIGHT\n184,128,64\nX\n')
        time.sleep(0.3)
        a.wait_idle(5)
        print("  placed", flush=True)
    except Exception as e:
        print(f"  failed: {e}", flush=True)
    a.save()

    # -------- cameras --------
    print("[cameras]", flush=True)
    cams = [
        ("HERO",      "CAMERA pos=hallway looking south",  96,228,66, 96,108,42),
        ("EDITORIAL", "low angle behind right chair",      168,170,30, 96,80,30),
    ]
    for name, desc, px,py,pz, tx,ty,tz in cams:
        try:
            a.send_command(f'_.CAMERA {px},{py},{pz} {tx},{ty},{tz}\n')
            a.wait_idle(3)
            a.send_command(f'_.-VIEW _S {name}\n')
            a.wait_idle(3)
            print(f"  {name}: {desc}", flush=True)
        except Exception as e:
            print(f"  {name}: {e}", flush=True)
    a.save()
    print(f"\nDONE entities={a.doc.ModelSpace.Count}", flush=True)


if __name__ == "__main__":
    main()

"""Capture multiple realistic-style snapshots of the detailed kitchen.
Uses Realistic + ShadedWithEdges visual styles, multiple iso angles."""
from __future__ import annotations
import os, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from acad import Acad
from snap_helpers import find_acad_main_hwnd, restore_window, capture_acad


def main():
    a = Acad(); a.cancel(); time.sleep(0.5); a.connect(); a.wait_idle(5)
    sv = a.doc.SetVariable
    sv("FILEDIA", 0); sv("CMDDIA", 0); sv("EXPERT", 5)
    try: sv("DEFAULTLIGHTING", 0)
    except Exception: pass

    # Try to turn on shadows for richer visual style
    for var, val in [("VSEDGES", 1), ("VSFACEHIGHLIGHT", 30),
                     ("VSSHADOWS", 2), ("VSLIGHTINGQUALITY", 2),
                     ("VSMATERIALMODE", 2)]:
        try:
            sv(var, val)
            print(f"  {var}={val}", flush=True)
        except Exception as e:
            print(f"  {var}: {e}", flush=True)

    out_dir = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "projects", "04-kitchen", "out"
    ))
    os.makedirs(out_dir, exist_ok=True)

    hwnd = find_acad_main_hwnd()
    restore_window(hwnd)
    a.send_command("_.CLEANSCREENON\n"); a.wait_idle(3)

    # Freeze ceiling + annotations for clean iso
    a.set_active_layer("0")
    try:
        a.freeze_layer("A-CLNG", freeze=True)
        a.freeze_layer("A-ANNO-DIMS", freeze=True)
        a.freeze_layer("A-ANNO-TEXT", freeze=True)
    except Exception:
        pass

    snaps = [
        ("render-realistic-ne.png",     "NEISO", "Realistic"),
        ("render-realistic-nw.png",     "NWISO", "Realistic"),
        ("render-shaded-ne.png",        "NEISO", "ShadedWithEdges"),
        ("render-presentation-iso.png", "NEISO", "ShadedWithEdges"),
    ]
    for fname, view, style in snaps:
        try:
            print(f"[{fname}] view={view} style={style}", flush=True)
            a.set_view(view); a.wait_idle(3)
            a.set_visual_style(style); a.wait_idle(3)
            a.zoom_extents()
            time.sleep(1.5)
            capture_acad(os.path.join(out_dir, fname))
            print(f"  saved {fname}", flush=True)
        except Exception as e:
            print(f"  EXC: {e}", flush=True)

    # Restore
    a.send_command("_.CLEANSCREENOFF\n"); a.wait_idle(3)
    a.freeze_layer("A-ANNO-DIMS", freeze=False)
    a.freeze_layer("A-ANNO-TEXT", freeze=False)
    a.save()
    print("DONE", flush=True)


if __name__ == "__main__":
    main()

"""Living Room — capture deliverable snapshots:
- floor-plan.png  : TOP view, 2DWireframe, anno layers visible
- presentation-iso.png  : SWISO Conceptual, anno frozen, ceiling frozen
- hero.png        : HERO named view, Conceptual
- editorial.png   : EDITORIAL named view, Conceptual
"""
from __future__ import annotations
import os, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from acad import Acad
from snap_helpers import capture_acad, find_acad_main_hwnd, restore_window


def main():
    a = Acad(); a.cancel(); time.sleep(0.3); a.connect(); a.wait_idle(5)
    sv = a.doc.SetVariable
    sv("FILEDIA", 0); sv("CMDDIA", 0); sv("EXPERT", 5)

    out_dir = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "projects", "05-living-room", "out"
    ))
    os.makedirs(out_dir, exist_ok=True)

    hwnd = find_acad_main_hwnd()
    restore_window(hwnd)

    a.send_command("_.CLEANSCREENON\n"); a.wait_idle(3)

    # ----- floor plan -----
    print("[plan]", flush=True)
    a.set_active_layer("0")
    a.freeze_layer("A-ANNO-DIMS", freeze=False)
    a.freeze_layer("A-ANNO-TEXT", freeze=False)
    try: a.freeze_layer("A-CLNG", freeze=True)
    except Exception: pass
    a.set_view("TOP"); a.wait_idle(3)
    a.set_visual_style("2DWireframe"); a.wait_idle(3)
    a.zoom_extents()
    time.sleep(1.5)
    capture_acad(os.path.join(out_dir, "floor-plan.png"))
    print("  saved floor-plan.png", flush=True)

    # ----- presentation iso -----
    print("[iso]", flush=True)
    a.freeze_layer("A-ANNO-DIMS", freeze=True)
    a.freeze_layer("A-ANNO-TEXT", freeze=True)
    a.set_view("SWISO"); a.wait_idle(3)
    a.set_visual_style("Conceptual"); a.wait_idle(3)
    a.zoom_extents()
    time.sleep(1.2)
    capture_acad(os.path.join(out_dir, "presentation-iso.png"))
    print("  saved presentation-iso.png", flush=True)

    # ----- HERO -----
    print("[hero]", flush=True)
    try:
        a.send_command("_.-VIEW _R HERO\n"); a.wait_idle(5)
        a.set_visual_style("Conceptual"); a.wait_idle(3)
        time.sleep(1.0)
        capture_acad(os.path.join(out_dir, "hero.png"))
        print("  saved hero.png", flush=True)
    except Exception as e:
        print(f"  HERO restore failed: {e}", flush=True)

    # ----- EDITORIAL -----
    print("[editorial]", flush=True)
    try:
        a.send_command("_.-VIEW _R EDITORIAL\n"); a.wait_idle(5)
        a.set_visual_style("Conceptual"); a.wait_idle(3)
        time.sleep(1.0)
        capture_acad(os.path.join(out_dir, "editorial.png"))
        print("  saved editorial.png", flush=True)
    except Exception as e:
        print(f"  EDITORIAL restore failed: {e}", flush=True)

    # restore default state
    print("[restore]", flush=True)
    a.freeze_layer("A-ANNO-DIMS", freeze=False)
    a.freeze_layer("A-ANNO-TEXT", freeze=False)
    a.send_command("_.CLEANSCREENOFF\n"); a.wait_idle(3)
    a.set_view("TOP"); a.wait_idle(3)
    a.set_visual_style("2DWireframe"); a.wait_idle(3)
    a.zoom_extents()
    a.save()
    print("DONE", flush=True)


if __name__ == "__main__":
    main()

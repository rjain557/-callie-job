"""Re-take both deliverable snapshots using the AutoCAD-window-only helper."""
from __future__ import annotations
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from acad import Acad
from snap_helpers import capture_acad, find_acad_main_hwnd, restore_window


def main():
    a = Acad()
    a.cancel(); time.sleep(0.5)
    a.connect()
    a.wait_idle(5)

    out_dir = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "projects", "01-home-office", "out"
    ))
    os.makedirs(out_dir, exist_ok=True)

    # Resize AutoCAD upfront so subsequent zoom_extents fits the right window
    hwnd = find_acad_main_hwnd()
    restore_window(hwnd)

    # PLAN snapshot — anno layers visible
    a.set_active_layer("0")
    a.freeze_layer("A-ANNO-DIMS", freeze=False)
    a.freeze_layer("A-ANNO-TEXT", freeze=False)
    # CLEANSCREENON hides ribbon/palettes so the viewport fills the window
    a.send_command("_.CLEANSCREENON\n"); a.wait_idle(3)
    print("TOP + 2DWireframe...")
    a.set_view("TOP"); a.wait_idle(3)
    a.set_visual_style("2DWireframe"); a.wait_idle(3)
    a.zoom_extents()
    time.sleep(1.5)
    out_plan = os.path.join(out_dir, "floor-plan.png")
    capture_acad(out_plan)
    print(f"  saved: {out_plan}")

    # ISO snapshot — anno layers frozen for clean 3D
    a.freeze_layer("A-ANNO-DIMS", freeze=True)
    a.freeze_layer("A-ANNO-TEXT", freeze=True)
    print("SWISO + Conceptual...")
    a.set_view("SWISO"); a.wait_idle(3)
    a.set_visual_style("Conceptual"); a.wait_idle(3)
    a.zoom_extents()
    time.sleep(1.2)
    out_iso = os.path.join(out_dir, "presentation-iso.png")
    capture_acad(out_iso)
    print(f"  saved: {out_iso}")

    # restore default open state (annotated TOP view, ribbon back on)
    a.freeze_layer("A-ANNO-DIMS", freeze=False)
    a.freeze_layer("A-ANNO-TEXT", freeze=False)
    a.send_command("_.CLEANSCREENOFF\n"); a.wait_idle(3)
    a.set_view("TOP"); a.wait_idle(3)
    a.set_visual_style("2DWireframe"); a.wait_idle(3)
    a.zoom_extents()
    a.save()
    print(f"DONE entities={a.doc.ModelSpace.Count}")


if __name__ == "__main__":
    main()

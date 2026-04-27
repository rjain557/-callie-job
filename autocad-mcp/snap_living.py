"""Quick SWISO Conceptual snap of the living-room model. Used for incremental
verification while the build is still in progress."""
from __future__ import annotations
import os, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from acad import Acad
from snap_helpers import capture_acad, find_acad_main_hwnd, restore_window


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "iso-progress.png"
    a = Acad()
    a.cancel(); time.sleep(0.5)
    a.connect(); a.wait_idle(5)

    out_dir = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "projects", "05-living-room", "out"
    ))
    os.makedirs(out_dir, exist_ok=True)

    hwnd = find_acad_main_hwnd()
    restore_window(hwnd)

    a.set_active_layer("0")
    try:
        a.freeze_layer("A-CLNG", freeze=True)
    except Exception:
        pass
    a.send_command("_.CLEANSCREENON\n"); a.wait_idle(3)
    a.set_view("SWISO"); a.wait_idle(3)
    a.set_visual_style("Conceptual"); a.wait_idle(3)
    a.zoom_extents()
    time.sleep(1.2)

    out = os.path.join(out_dir, name)
    capture_acad(out)
    print(f"saved: {out}")

    a.send_command("_.CLEANSCREENOFF\n"); a.wait_idle(3)


if __name__ == "__main__":
    main()

"""Use SAVEIMG to save the current Realistic-style viewport directly to PNG.
This isn't a raytraced render but uses the Realistic visual style which has
material colors, shadows, and lighting baked in — significantly more 3D-looking
than Conceptual."""
from __future__ import annotations
import os, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from acad import Acad
from snap_helpers import find_acad_main_hwnd, restore_window, capture_acad


def main():
    a = Acad(); a.cancel(); time.sleep(0.3); a.connect(); a.wait_idle(5)
    sv = a.doc.SetVariable
    sv("FILEDIA", 0); sv("CMDDIA", 0); sv("EXPERT", 5)

    out_dir = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "projects", "04-kitchen", "out"
    ))

    hwnd = find_acad_main_hwnd()
    restore_window(hwnd)

    # NE iso, Realistic style for richer-looking output
    a.send_command("_.CLEANSCREENON\n"); a.wait_idle(3)
    a.set_view("NEISO"); a.wait_idle(3)
    a.set_visual_style("Realistic"); a.wait_idle(3)
    try: a.freeze_layer("A-CLNG", freeze=True)
    except Exception: pass
    a.zoom_extents()
    time.sleep(1.5)

    # Capture to file
    out = os.path.join(out_dir, "render-realistic.png")
    capture_acad(out)
    print(f"saved: {out}")

    # Also try Shaded with Edges — best for elevations
    a.set_visual_style("ShadedWithEdges"); a.wait_idle(3)
    time.sleep(1.0)
    out2 = os.path.join(out_dir, "render-shaded.png")
    capture_acad(out2)
    print(f"saved: {out2}")

    a.send_command("_.CLEANSCREENOFF\n"); a.wait_idle(3)


if __name__ == "__main__":
    main()

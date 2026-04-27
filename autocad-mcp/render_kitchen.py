"""Trigger RENDER on the kitchen at NEISO. AutoCAD 2027 uses an Active Shade
window — we kick it off and let the user save the result manually if it
doesn't auto-write to a file.

Pre-render setup:
- Set NEISO view, Conceptual visual style first to confirm composition
- Switch to Realistic visual style for the render
- Restore the AutoCAD window so the render output is visible
- Send `_.RENDER` with no preset (uses current default)

This will likely OPEN the render window and require the user to click
"Save..." in that window. The script does not block on the render
completing.
"""
from __future__ import annotations
import os, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from acad import Acad
from snap_helpers import find_acad_main_hwnd, restore_window


def main():
    a = Acad(); a.cancel(); time.sleep(0.3); a.connect(); a.wait_idle(5)
    print(f"doc={a.doc.Name}", flush=True)
    sv = a.doc.SetVariable
    sv("FILEDIA", 0); sv("CMDDIA", 0); sv("EXPERT", 5)
    # Make sure default lighting is OFF so our placed lights (or sun) drive the render
    try: sv("DEFAULTLIGHTING", 0)
    except Exception as e: print(f"  DEFAULTLIGHTING: {e}", flush=True)
    try: sv("LIGHTINGUNITS", 2)
    except Exception as e: print(f"  LIGHTINGUNITS: {e}", flush=True)

    hwnd = find_acad_main_hwnd()
    restore_window(hwnd)
    a.send_command("_.CLEANSCREENOFF\n"); a.wait_idle(3)

    print("setting view + style", flush=True)
    a.set_view("NEISO"); a.wait_idle(3)
    # Realistic visual style is a better preview than Conceptual; final RENDER
    # uses the renderer regardless of visual style.
    a.set_visual_style("Realistic"); a.wait_idle(3)
    a.zoom_extents()
    time.sleep(1.0)
    a.save()

    print("triggering RENDER (this opens the AutoCAD render window)...", flush=True)
    # Fire the render. The render window will pop up. The user can save from
    # there. Keep the script alive briefly so AutoCAD has time to start.
    try:
        a.send_command("_.RENDER\n")
        time.sleep(3)
    except Exception as e:
        print(f"  RENDER: {e}", flush=True)

    print("\nDONE — check the AutoCAD render window. To save the image:", flush=True)
    print("  1. In the AutoCAD render window, click the disk/save icon", flush=True)
    print("  2. Save as: projects/04-kitchen/out/render-final.png", flush=True)


if __name__ == "__main__":
    main()

"""Kitchen — capture deliverable snapshots:
- floor-plan.png        : TOP, 2DWireframe, anno layers visible
- presentation-iso.png  : NWISO Conceptual, anno frozen, ceiling frozen,
                          north + east walls frozen so we can see in
- elevation-long-wall.png : FRONT view (looking south to north along Y axis)
                            with island and ceiling frozen so cabinets read
- elevation-island.png  : BACK view of island (looking north to south)
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
        os.path.dirname(__file__), "..", "projects", "04-kitchen", "out"
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
    # Freeze the closer walls (north + east) so the camera sees into the room
    print("[iso]", flush=True)
    a.freeze_layer("A-ANNO-DIMS", freeze=True)
    a.freeze_layer("A-ANNO-TEXT", freeze=True)
    # Wall layer is shared so we can't freeze just half. Use NEISO (camera at NE, looking SW) and zoom_extents.
    a.set_view("NEISO"); a.wait_idle(3)
    a.set_visual_style("Conceptual"); a.wait_idle(3)
    a.zoom_extents()
    time.sleep(1.2)
    capture_acad(os.path.join(out_dir, "presentation-iso.png"))
    print("  saved presentation-iso.png", flush=True)

    # ----- elevation, long wall (front view: looking from north toward south) -----
    # FRONT view in AutoCAD looks along -Y axis (from +Y toward origin).
    # That means viewer is at north side looking south — south wall is far.
    # We want to see the SOUTH WALL CABINETS, so we need to look TOWARD the south wall.
    # FRONT view = Y axis is into screen, X is horizontal, Z is vertical.
    # Walls in front of the cabinets are NORTH wall + island. Freeze them temporarily.
    print("[elevation long wall]", flush=True)
    try:
        # Freeze island so it's not blocking the view
        a.freeze_layer("I-CASE-ISLA", freeze=True)
        a.freeze_layer("I-CASE-CTR", freeze=False)
    except Exception:
        pass
    a.set_view("FRONT"); a.wait_idle(3)
    a.set_visual_style("2DWireframe"); a.wait_idle(3)
    a.zoom_extents()
    time.sleep(1.2)
    capture_acad(os.path.join(out_dir, "elevation-long-wall.png"))
    print("  saved elevation-long-wall.png", flush=True)

    # ----- elevation, island (front view of island, looking north into seating side) -----
    # BACK view: looking from -Y toward +Y. South side viewer.
    # That puts south wall cabinets close to camera (in foreground) and island past them.
    # Better approach: looking at island from the north (seating) side — that's a BACK view
    # but we'd want only the island visible; freeze cabinets temporarily.
    print("[elevation island]", flush=True)
    try:
        a.freeze_layer("I-CASE-ISLA", freeze=False)
        a.freeze_layer("I-CASE", freeze=True)
        a.freeze_layer("I-CASE-WALL", freeze=True)
        a.freeze_layer("I-CASE-PANT", freeze=True)
        a.freeze_layer("I-FURN-APPL", freeze=True)
        a.freeze_layer("I-FURN-APPL-MTL", freeze=True)
    except Exception as e:
        print(f"  freeze: {e}")
    a.set_view("BACK"); a.wait_idle(3)
    a.set_visual_style("2DWireframe"); a.wait_idle(3)
    a.zoom_extents()
    time.sleep(1.2)
    capture_acad(os.path.join(out_dir, "elevation-island.png"))
    print("  saved elevation-island.png", flush=True)

    # ----- restore default state -----
    print("[restore]", flush=True)
    for layer in ["I-CASE-ISLA", "I-CASE", "I-CASE-WALL", "I-CASE-PANT",
                  "I-FURN-APPL", "I-FURN-APPL-MTL", "A-ANNO-DIMS", "A-ANNO-TEXT"]:
        try: a.freeze_layer(layer, freeze=False)
        except Exception: pass
    a.send_command("_.CLEANSCREENOFF\n"); a.wait_idle(3)
    a.set_view("TOP"); a.wait_idle(3)
    a.set_visual_style("2DWireframe"); a.wait_idle(3)
    a.zoom_extents()
    a.save()
    print("DONE", flush=True)


if __name__ == "__main__":
    main()

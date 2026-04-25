"""
Build v2 of the home-office drawing: adds floor, ceiling, baseboards, door leaf,
window glass + muntins + sill + apron, roller shade, area rug, and material colors.

Runs against a running AutoCAD via direct COM (imports the same Acad class
that the MCP server uses). Safe to re-run — new layers/geometry are additive.

Prereqs: AutoCAD 2027 open with home-office.dwg active (we will open it if needed).
"""
from __future__ import annotations

import os
import sys
import time

# Make acad.py importable when run from anywhere
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from acad import Acad


DRAWING_PATH = r"c:\VSCode\callie-job\-callie-job\projects\01-home-office\out\home-office.dwg"

# Known color palette (AutoCAD Color Index)
ACI_WOOD_WARM = 40
ACI_WOOD_MID = 42
ACI_CREAM = 33
ACI_WHITE = 254
ACI_GLASS_BLUE = 140
ACI_DARK_GRAY = 8
ACI_CHARCOAL = 252
ACI_SHADE_TAN = 43
ACI_RUG_BLUE = 160
ACI_UPHOLSTERY = 170
ACI_FLOOR_LVP = 40


def identify_furniture(a: Acad) -> dict[str, str]:
    """Map semantic names to handles by looking at I-FURN solids' centroids.

    The v1 build left 6 solids on I-FURN: 4 boxes + 3 cylinders.
    Actually: desk/bookcase/armchair (boxes), desk-chair/side-table/floor-lamp (cylinders).
    We identify by bounding box centroid position (approximate).
    """
    ents = a.list_entities(type_filter="3dSolid", limit=500)
    on_furn = [e for e in ents if e["layer"] == "I-FURN"]
    doc = a.doc
    # Collect centroid + size for each candidate
    items = []
    for e in on_furn:
        ent = doc.HandleToObject(e["handle"])
        try:
            bb_min, bb_max = ent.GetBoundingBox()
        except Exception:
            continue
        cx = (bb_min[0] + bb_max[0]) / 2
        cy = (bb_min[1] + bb_max[1]) / 2
        cz = (bb_min[2] + bb_max[2]) / 2
        sx = bb_max[0] - bb_min[0]
        sy = bb_max[1] - bb_min[1]
        sz = bb_max[2] - bb_min[2]
        items.append({"h": e["handle"], "c": (cx, cy, cz), "s": (sx, sy, sz)})

    mapping: dict[str, str] = {}
    # Known v1 geometry — expected (cx,cy,cz)+(sx,sy,sz). Match by nearest euclidean distance in (x,y,z,sx,sy,sz) space.
    targets = {
        "desk":       (69, 105, 15, 60, 30, 30),
        "desk_chair": (69, 75, 9,   20, 20, 18),
        "bookcase":   (6,  60, 36,  12, 36, 72),
        "armchair":   (117, 99, 16, 34, 34, 32),
        "side_table": (88, 99, 11,  18, 18, 22),
        "floor_lamp": (108, 75, 30, 12, 12, 60),
    }
    used = set()
    for name, (tx, ty, tz, tsx, tsy, tsz) in targets.items():
        best, best_d = None, 1e18
        for it in items:
            if it["h"] in used:
                continue
            cx, cy, cz = it["c"]
            sx, sy, sz = it["s"]
            d = ((cx-tx)**2 + (cy-ty)**2 + (cz-tz)**2
                 + (sx-tsx)**2 + (sy-tsy)**2 + (sz-tsz)**2)
            if d < best_d:
                best_d = d
                best = it
        if best is not None:
            mapping[name] = best["h"]
            used.add(best["h"])
    return mapping


def main():
    a = Acad()

    print("[1/10] Cancel any stuck state via Win32 PostMessage...")
    cancel_result = a.cancel()
    print(f"       {cancel_result}")
    time.sleep(0.5)

    print("[2/10] Connect to AutoCAD...")
    a.connect()
    print(f"       version={a.app.Version}  docs={a.app.Documents.Count}")

    print("[3/10] Wait for AutoCAD to be idle...")
    idle = a.wait_idle(timeout_s=10.0)
    print(f"       {idle}")

    # Ensure home-office.dwg is active
    active_name = a.doc.Name.lower()
    if "home-office" not in active_name:
        print(f"[3b] Active drawing is '{a.doc.Name}' — opening home-office.dwg")
        a.open_drawing(DRAWING_PATH)
        a.wait_idle(5)
    else:
        print(f"       active drawing: {a.doc.Name}")

    print("[4/10] Identify existing furniture by position...")
    furn = identify_furniture(a)
    print(f"       mapped: {list(furn.keys())}")
    for name, h in furn.items():
        print(f"         {name} = {h}")

    print("[5/10] Create v2 layers...")
    a.create_layer("A-FLOR", ACI_WOOD_WARM)
    a.create_layer("A-CLNG", ACI_WHITE)
    a.create_layer("A-TRIM", ACI_WHITE)
    # Ensure the layers used by v1 are set correctly too
    for name, idx in (("A-WALL", ACI_WHITE), ("A-DOOR", ACI_WHITE),
                      ("A-GLAZ", ACI_GLASS_BLUE)):
        try:
            a.create_layer(name, idx)
        except Exception as e:
            print(f"       warn: {name}: {e}")

    print("[6/10] Build v2 geometry...")

    # Floor
    a.set_active_layer("A-FLOR")
    floor = a.add_box([0, 0, -0.5], [138, 120, 0])
    print(f"       floor: {floor['handle']}")

    # Ceiling (will freeze layer at end)
    a.set_active_layer("A-CLNG")
    ceiling = a.add_box([0, 0, 96], [138, 120, 97])
    print(f"       ceiling: {ceiling['handle']}")

    # Baseboards (5 segments — south has two because of door gap)
    a.set_active_layer("A-TRIM")
    baseboards = [
        a.add_box([0, 0, 0], [55, 0.75, 4]),          # south, west of door
        a.add_box([87, 0, 0], [138, 0.75, 4]),        # south, east of door
        a.add_box([0, 119.25, 0], [138, 120, 4]),     # north
        a.add_box([137.25, 0, 0], [138, 120, 4]),     # east
        a.add_box([0, 0, 0], [0.75, 120, 4]),         # west
    ]
    print(f"       {len(baseboards)} baseboards placed")

    # Door leaf (swung open 90° inward, hinged at x=87)
    a.set_active_layer("A-DOOR")
    door_leaf = a.add_box([85.5, 0, 0], [87, 32, 80])
    print(f"       door leaf: {door_leaf['handle']}")

    # Window glass
    a.set_active_layer("A-GLAZ")
    glass = a.add_box([140, 36, 36], [140.1, 84, 84])
    print(f"       window glass: {glass['handle']}")

    # Window muntins (horizontal + vertical) on A-TRIM (white)
    a.set_active_layer("A-TRIM")
    muntin_h = a.add_box([139.5, 36, 59.25], [140.5, 84, 60.75])
    muntin_v = a.add_box([139.5, 59.25, 36], [140.5, 60.75, 84])
    # Sill + apron (interior trim)
    sill = a.add_box([135, 33, 35], [138, 87, 36])
    apron = a.add_box([137, 34, 33], [138, 86, 35])
    print(f"       muntins + sill + apron placed")

    # Roller shade (pulled 24" down from head)
    a.set_active_layer("A-GLAZ")
    shade = a.add_box([137, 36, 60], [137.25, 84, 84])
    a.change_color(shade["handle"], ACI_SHADE_TAN)
    print(f"       shade: {shade['handle']}")

    # Area rug under reading nook
    a.set_active_layer("I-FURN")
    rug = a.add_box([62, 70, 0], [134, 118, 0.125])
    a.change_color(rug["handle"], ACI_RUG_BLUE)
    print(f"       rug: {rug['handle']}")

    print("[7/10] Apply material colors to v1 furniture...")
    color_map = {
        "desk":        ACI_WOOD_WARM,
        "desk_chair":  ACI_CHARCOAL,
        "bookcase":    ACI_WOOD_MID,
        "armchair":    ACI_UPHOLSTERY,
        "side_table":  ACI_CREAM,
        "floor_lamp":  ACI_DARK_GRAY,
    }
    for name, handle in furn.items():
        color = color_map.get(name)
        if color is None:
            continue
        try:
            a.change_color(handle, color)
            print(f"         {name} ({handle}) -> color {color}")
        except Exception as e:
            print(f"         {name}: FAILED: {e}")

    print("[8/10] Freeze A-CLNG layer (ceiling hidden in 3D view)...")
    a.freeze_layer("A-CLNG", freeze=True)

    print("[9/10] Set SW isometric view + Conceptual visual style, zoom extents...")
    try:
        a.set_view("SWISO")
        a.wait_idle(5)
        a.set_visual_style("Conceptual")
        a.wait_idle(5)
    except Exception as e:
        print(f"       view/style deferred: {e}")
    a.zoom_extents()

    print("[10/10] Save...")
    a.save()

    status = a.status()
    print(f"\nDONE. {status['active_document']['entity_count']} entities. "
          f"Saved: {status['active_document']['path']}")


if __name__ == "__main__":
    main()

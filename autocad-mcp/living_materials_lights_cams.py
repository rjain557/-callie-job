"""
Living Room — 5C materials, 5D lighting, 5E cameras.

5C Materials:
  Define 8 named materials via doc.Materials, set basic appearance properties,
  and assign each to its layer (by-layer is cleaner than by-object).
  AutoCAD library import (MATBROWSER) is GUI-only — these are custom analogues
  that match the brief's intent (white oak floor, walnut, oatmeal linen, etc.).

5D Lighting:
  - Turn off default lighting, sun on (via SetVariable in a try/except, since
    some sun sysvars are read-only on this build of 2027).
  - 16 recessed point lights, one in each ceiling coffer, ~600 lm 2700K.
  - 1 point light inside the floor lamp shade, ~1200 lm 2700K.

5E Cameras:
  HERO  — standing in the hallway opening, looking south into the room.
  EDIT  — low angle from behind a lounge chair (close, more editorial).
  Saved as named views.
"""
from __future__ import annotations
import os, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from acad import Acad, _point3, _variant_double_array


# room geometry (must match build_living_room.py)
W = 192.0
D = 216.0
H = 120.0
COFFER_COLS, COFFER_ROWS = 4, 4
COFFER_W = 36.0
COFFER_D = 42.0
COFFER_DEPTH = 6.0


# ---------- materials ----------
# Each entry: (name, layer, diffuse RGB, shininess 0-100, reflectivity 0-100, opacity 0-100, description)
MATERIALS = [
    ("Wood-WhiteOak-Floor",   "A-FLOR",     (216, 184, 138), 30, 5,   100, "Wood - White Oak (floor)"),
    ("Paint-Interior-White",  "A-WALL",     (245, 240, 230), 5,  0,   100, "Paint - Interior - White (walls)"),
    ("Paint-Ceiling-White",   "A-CLNG",     (250, 248, 244), 5,  0,   100, "Paint - Ceiling - White"),
    ("Paint-Trim-White",      "A-TRIM",     (250, 248, 244), 10, 0,   100, "Paint - Trim - White (coffers)"),
    ("Fabric-Linen-Oatmeal",  "I-FURN",     (220, 208, 188), 5,  0,   100, "Fabric - Linen - Oatmeal (sofa, chairs)"),
    ("Wood-Walnut",           "I-FURN-WD",  (104, 70,  46),  40, 8,   100, "Wood - Walnut (coffee table, console)"),
    ("Metal-Brass-Satin",     "I-FURN-MTL", (181, 144, 86),  60, 30,  100, "Metal - Brass Satin (lamp, hardware)"),
    ("Glass-Mirror",          "A-GLAZ",     (200, 220, 230), 90, 95,  100, "Glass - Mirror (mirror + window)"),
    ("Fabric-Sheer-White",    "I-FURN-DRP", (250, 248, 240), 5,  0,   55,  "Fabric - Sheer White (drapery)"),
    ("Custom-WallArt-Coastal","I-FURN-ART", (66, 110, 145),  20, 5,   100, "Custom - Coastal blue wall art"),
    ("Fabric-Rug-Indigo",     "I-FURN-RUG", (50, 78, 122),   8,  2,   100, "Fabric - Indigo wool rug"),
    ("Metal-Recessed-Can",    "E-LITE",     (220, 220, 220), 50, 30,  100, "Metal - Brushed nickel recessed can"),
]


def define_materials(a: Acad):
    print("[5C] materials", flush=True)
    materials = a.doc.Materials
    created = 0
    for name, layer, rgb, shin, refl, opac, desc in MATERIALS:
        # Add or fetch
        try:
            mat = materials.Item(name)
        except Exception:
            try:
                mat = materials.Add(name)
                created += 1
            except Exception as e:
                print(f"  add {name}: {e}", flush=True)
                continue

        # Diffuse color via AcCmColor
        try:
            tc = a.app.GetInterfaceObject(
                f"AutoCAD.AcCmColor.{int(a.app.Version.split('.')[0])}")
            tc.ColorMethod = 0xC2  # acColorMethodByRGB
            tc.SetRGB(rgb[0], rgb[1], rgb[2])
            mat.Diffuse = tc
        except Exception as e:
            print(f"  {name} diffuse: {e}", flush=True)

        # Shininess + reflectivity (these props vary by version; try/except each)
        for prop, val in (("Shininess", shin), ("Reflection", refl), ("Opacity", opac)):
            try:
                setattr(mat, prop, val)
            except Exception:
                pass

        # Description
        try:
            mat.Description = desc
        except Exception:
            pass

    print(f"  created {created} new, total materials = {materials.Count}", flush=True)

    # Assign by layer
    print("  assigning to layers", flush=True)
    for name, layer, *_ in MATERIALS:
        try:
            lyr = a.doc.Layers.Item(layer)
            lyr.Material = name
            print(f"    {layer:14s} <- {name}", flush=True)
        except Exception as e:
            print(f"    {layer}: {e}", flush=True)


def lighting(a: Acad):
    print("[5D] lighting", flush=True)
    sv = a.doc.SetVariable

    # 5D.1-2 Turn off default lighting
    try:
        sv("DEFAULTLIGHTING", 0)
        print("  DEFAULTLIGHTING = 0", flush=True)
    except Exception as e:
        print(f"  DEFAULTLIGHTING: {e}", flush=True)

    # SUNSTATUS may be read-only; attempt but don't block
    try:
        sv("SUNSTATUS", 1)
        print("  SUNSTATUS = 1", flush=True)
    except Exception as e:
        print(f"  SUNSTATUS read-only on this version ({e})", flush=True)

    # 5D.3 Recessed cans — 16 point lights, one per coffer
    print("  16 recessed point lights", flush=True)
    sx = (W - COFFER_COLS * COFFER_W) / (COFFER_COLS + 1)
    sy = (D - COFFER_ROWS * COFFER_D) / (COFFER_ROWS + 1)
    placed = 0
    for r in range(COFFER_ROWS):
        for c in range(COFFER_COLS):
            cx = sx + c * (COFFER_W + sx) + COFFER_W / 2
            cy = sy + r * (COFFER_D + sy) + COFFER_D / 2
            cz = H + 0.5  # just below ceiling
            name = f"CAN_{r+1}_{c+1}"
            cmd = (
                f'_.LIGHT _P {cx},{cy},{cz} _N {name} _C 2700 '
                f'_I 4000 _S _OFF \n'
            )
            try:
                a.send_command(cmd)
                a.wait_idle(3)
                placed += 1
            except Exception as e:
                print(f"    {name} failed: {e}", flush=True)
                break
    print(f"    placed {placed}/16 recessed lights", flush=True)

    # 5D.4 Floor lamp light (point inside shade)
    print("  floor lamp point light", flush=True)
    try:
        a.send_command(f'_.LIGHT _P 184,128,64 _N FLOOR_LAMP _C 2700 _I 8000 _S _OFF \n')
        a.wait_idle(3)
    except Exception as e:
        print(f"    failed: {e}", flush=True)


def cameras(a: Acad):
    print("[5E] cameras", flush=True)
    # Add named views via Views collection. View takes a current viewport's
    # state, so the easiest way is: position the camera via VPOINT/CAMERA
    # commands, then save the named view.
    views = [
        ("HERO",      "_.CAMERA 96,228,66 96,108,42\n",
         "Standing in hallway opening, looking south into the room"),
        ("EDITORIAL", "_.CAMERA 168,170,30 96,80,30\n",
         "Low angle from behind right lounge chair, toward sectional"),
    ]
    for name, cmd, desc in views:
        try:
            a.send_command(cmd)
            a.wait_idle(3)
            a.send_command(f'_.-VIEW _S {name}\n')
            a.wait_idle(3)
            print(f"  {name}: saved ({desc})", flush=True)
        except Exception as e:
            print(f"  {name}: {e}", flush=True)


def main():
    a = Acad()
    a.cancel(); time.sleep(0.5)
    a.connect(); a.wait_idle(5)
    print(f"doc={a.doc.Name} entities={a.doc.ModelSpace.Count}", flush=True)
    a.doc.SetVariable("FILEDIA", 0)
    a.doc.SetVariable("CMDDIA", 0)
    a.doc.SetVariable("EXPERT", 5)

    for name, fn in [("materials", define_materials), ("lighting", lighting),
                     ("cameras", cameras)]:
        try:
            fn(a)
            a.save()
            print(f"  saved after {name}", flush=True)
        except Exception as e:
            print(f"  {name} EXCEPTION: {e}", flush=True)

    print(f"\nDONE entities={a.doc.ModelSpace.Count}", flush=True)


if __name__ == "__main__":
    main()

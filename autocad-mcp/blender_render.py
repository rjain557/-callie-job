"""Blender render pipeline. Run with:

  blender --background --python autocad-mcp/blender_render.py -- <args>

Args (after the literal `--`):
  --fbx PATH        kitchen.fbx (or any AutoCAD FBX export)
  --out PATH        output PNG path
  --view {hero,ne,nw,se,sw}    camera angle
  --resolution WxH  e.g. 1920x1200 (default 1600x1100)
  --samples N       Cycles samples (default 128)
  --engine {CYCLES,EEVEE}      default CYCLES

Maps AutoCAD layer names to PBR materials based on the layer-name
prefix. Edits the lookup table in MATERIAL_PRESETS to change finishes
without re-running the AutoCAD side.

Why this script:
- Layered AutoCAD models lose their layer info as Blender material slots
  via FBX, but objects keep their layer name as a custom property or as
  a name suffix. We re-attach materials by layer-name match.
- AutoCAD's per-object materials don't survive the FBX round trip well.
- Blender's principled BSDF + a few procedural textures gives us
  PBR-looking renders without needing a texture library on disk.
"""
from __future__ import annotations
import argparse
import math
import os
import sys


# ---- material presets (PBR-ish via principled BSDF parameters) ----
# (base_color RGBA 0-1, roughness, metallic, ior, transmission, has_wood_grain)
MATERIAL_PRESETS = {
    # AutoCAD layer prefix -> material spec
    "A-FLOR":         {"name": "WhiteOak Floor", "color": (0.55, 0.41, 0.27, 1), "roughness": 0.55, "metallic": 0.0, "wood": True},
    "A-WALL":         {"name": "Paint White",    "color": (0.92, 0.91, 0.88, 1), "roughness": 0.85, "metallic": 0.0},
    "A-CLNG":         {"name": "Ceiling White",  "color": (0.95, 0.94, 0.92, 1), "roughness": 0.90, "metallic": 0.0},
    "A-TRIM":         {"name": "Trim White",     "color": (0.95, 0.94, 0.92, 1), "roughness": 0.40, "metallic": 0.0},
    "I-CASE":         {"name": "Cabinet Paint",  "color": (0.93, 0.92, 0.89, 1), "roughness": 0.30, "metallic": 0.0},
    "I-CASE-ISLA":    {"name": "Island Paint",   "color": (0.93, 0.92, 0.89, 1), "roughness": 0.30, "metallic": 0.0},
    "I-CASE-WALL":    {"name": "Wall Cab Paint", "color": (0.93, 0.92, 0.89, 1), "roughness": 0.30, "metallic": 0.0},
    "I-CASE-PANT":    {"name": "Pantry Paint",   "color": (0.93, 0.92, 0.89, 1), "roughness": 0.30, "metallic": 0.0},
    "I-CASE-WD":      {"name": "Walnut Cabinet", "color": (0.31, 0.20, 0.12, 1), "roughness": 0.35, "metallic": 0.0, "wood": True},
    "I-CASE-CTR":     {"name": "Quartz Counter", "color": (0.92, 0.91, 0.89, 1), "roughness": 0.10, "metallic": 0.0, "marble": True},
    "I-FURN-APPL":    {"name": "Range Black",    "color": (0.07, 0.07, 0.08, 1), "roughness": 0.30, "metallic": 0.5},
    "I-FURN-APPL-MTL":{"name": "Stainless",      "color": (0.78, 0.78, 0.80, 1), "roughness": 0.20, "metallic": 1.0},
    "I-FURN-SINK":    {"name": "Stainless Sink", "color": (0.80, 0.80, 0.82, 1), "roughness": 0.18, "metallic": 1.0},
    "I-HARDWARE":     {"name": "Brushed Nickel", "color": (0.82, 0.82, 0.84, 1), "roughness": 0.25, "metallic": 1.0},
    "I-TILE":         {"name": "Subway Tile",    "color": (0.97, 0.97, 0.96, 1), "roughness": 0.10, "metallic": 0.0},
    "I-CROWN":        {"name": "Crown White",    "color": (0.95, 0.94, 0.92, 1), "roughness": 0.40, "metallic": 0.0},
    "I-PENDANT":      {"name": "Pendant Bronze", "color": (0.18, 0.13, 0.10, 1), "roughness": 0.40, "metallic": 0.7},
    "I-STOOL":        {"name": "Stool Walnut",   "color": (0.31, 0.20, 0.12, 1), "roughness": 0.45, "metallic": 0.0, "wood": True},
    "A-GLAZ":         {"name": "Glass",          "color": (0.85, 0.92, 0.95, 1), "roughness": 0.05, "metallic": 0.0, "glass": True},
    "I-FURN-RUG":     {"name": "Wool Rug",       "color": (0.20, 0.31, 0.48, 1), "roughness": 0.95, "metallic": 0.0},
    "I-FURN-DRP":     {"name": "Sheer Drape",    "color": (0.95, 0.94, 0.92, 1), "roughness": 0.50, "metallic": 0.0, "glass": True, "transmission": 0.6},
    "I-FURN-WD":      {"name": "Walnut",         "color": (0.31, 0.20, 0.12, 1), "roughness": 0.35, "metallic": 0.0, "wood": True},
    "I-FURN-MTL":     {"name": "Brass Satin",    "color": (0.71, 0.57, 0.34, 1), "roughness": 0.30, "metallic": 1.0},
    "I-FURN-ART":     {"name": "Art Coastal",    "color": (0.26, 0.43, 0.57, 1), "roughness": 0.50, "metallic": 0.0},
    "E-LITE":         {"name": "Recessed Trim",  "color": (0.86, 0.86, 0.88, 1), "roughness": 0.30, "metallic": 1.0},
}

# Camera presets — (location, target) in METERS (FBX from AutoCAD scales inches->cm by default)
# AutoCAD inches -> Blender meters: 1 in = 0.0254 m. So a 168" room = 4.27 m
CAMERA_PRESETS = {
    "ne":   {"loc": (10, -3, 5),  "target": (2, 3, 1.5)},
    "nw":   {"loc": (-3, -3, 5),  "target": (2, 3, 1.5)},
    "se":   {"loc": (10, 8, 5),   "target": (2, 3, 1.5)},
    "sw":   {"loc": (-3, 8, 5),   "target": (2, 3, 1.5)},
    "hero": {"loc": (-2, 5, 1.7), "target": (3, 1, 1.0)},
}


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--fbx", default=None)
    p.add_argument("--dxf", default=None)
    p.add_argument("--out", required=True)
    p.add_argument("--view", default="ne", choices=list(CAMERA_PRESETS))
    p.add_argument("--resolution", default="1600x1100")
    p.add_argument("--samples", type=int, default=128)
    p.add_argument("--engine", default="CYCLES", choices=["CYCLES", "EEVEE"])
    return p.parse_args(argv)


def main():
    import bpy  # only available inside Blender

    args = parse_args()
    print(f"=== Blender render ===", flush=True)
    print(f"fbx={args.fbx} dxf={args.dxf} out={args.out}", flush=True)
    print(f"view={args.view} resolution={args.resolution} samples={args.samples}", flush=True)

    # --- clean scene ---
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in bpy.data.materials:
        bpy.data.materials.remove(block)

    # --- import geometry ---
    if args.fbx:
        bpy.ops.import_scene.fbx(filepath=args.fbx)
    elif args.dxf:
        # DXF import is provided by an addon; enable then call.
        try:
            bpy.ops.preferences.addon_enable(module="io_import_dxf")
        except Exception:
            pass
        try:
            bpy.ops.import_scene.dxf(filepath=args.dxf)
        except AttributeError:
            # Newer Blender ships DXF importer differently; try the registry path
            bpy.ops.wm.dxf_import(filepath=args.dxf)
    else:
        sys.exit("must pass --fbx or --dxf")
    print(f"imported {len(bpy.data.objects)} objects", flush=True)
    # Convert AutoCAD inches -> Blender meters: 1 in = 0.0254 m
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.transform.resize(value=(0.0254, 0.0254, 0.0254))
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    # --- assign materials by layer-name match ---
    mats = {}
    for layer_prefix, spec in MATERIAL_PRESETS.items():
        m = bpy.data.materials.new(name=spec["name"])
        m.use_nodes = True
        bsdf = m.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = spec["color"]
            bsdf.inputs["Roughness"].default_value = spec["roughness"]
            bsdf.inputs["Metallic"].default_value = spec["metallic"]
            if spec.get("glass"):
                # Newer Blender: 'Transmission Weight'; fall back gracefully
                for key in ("Transmission Weight", "Transmission"):
                    if key in bsdf.inputs:
                        bsdf.inputs[key].default_value = spec.get("transmission", 1.0)
                        break
                bsdf.inputs["Roughness"].default_value = spec["roughness"]
        mats[layer_prefix] = m

    # Match each Blender object to an AutoCAD layer.
    # DXF import places layer info into a custom 'Layer' property OR into
    # a collection name. Try several strategies.
    fallback = mats.get("A-WALL")
    matched = 0
    total_meshes = 0
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        total_meshes += 1
        name = obj.name
        layer = None
        # Strategy 1: custom property on object
        for k in ("Layer", "layer", "AcadLayer"):
            if k in obj:
                layer = str(obj[k])
                break
        # Strategy 2: parent collection name
        if not layer and obj.users_collection:
            for c in obj.users_collection:
                if c.name.startswith("A-") or c.name.startswith("I-") or c.name.startswith("E-"):
                    layer = c.name
                    break
        # Strategy 3: substring match on the object name
        if not layer:
            for prefix in sorted(mats.keys(), key=len, reverse=True):
                if prefix in name:
                    layer = prefix
                    break

        # Pick material by exact prefix match (longest first)
        chosen = None
        if layer:
            for prefix in sorted(mats.keys(), key=len, reverse=True):
                if layer.startswith(prefix):
                    chosen = mats[prefix]
                    break
        m = chosen if chosen else fallback
        obj.data.materials.clear()
        obj.data.materials.append(m)
        if chosen:
            matched += 1
    print(f"matched material on {matched} / {total_meshes} mesh objects",
          flush=True)

    # --- camera ---
    cam_data = bpy.data.cameras.new("RenderCam")
    cam_obj = bpy.data.objects.new("RenderCam", cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj
    preset = CAMERA_PRESETS[args.view]
    cam_obj.location = preset["loc"]
    # Aim camera at target
    target = preset["target"]
    direction = (target[0] - cam_obj.location[0],
                 target[1] - cam_obj.location[1],
                 target[2] - cam_obj.location[2])
    # Compute Euler angles for camera-look-at
    import mathutils
    direction_v = mathutils.Vector(direction)
    rot_quat = direction_v.to_track_quat('-Z', 'Y')
    cam_obj.rotation_euler = rot_quat.to_euler()
    cam_data.lens = 35  # 35mm equivalent

    # --- lighting ---
    # Sun
    sun_data = bpy.data.lights.new("Sun", type="SUN")
    sun_data.energy = 3.0
    sun_data.angle = math.radians(2)  # soft sun
    sun_obj = bpy.data.objects.new("Sun", sun_data)
    bpy.context.scene.collection.objects.link(sun_obj)
    sun_obj.location = (5, -3, 8)
    sun_obj.rotation_euler = (math.radians(50), math.radians(15), math.radians(-30))

    # Ambient (world environment)
    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.95, 0.97, 1.0, 1)
        bg.inputs[1].default_value = 0.6  # dim ambient

    # --- render settings ---
    scene = bpy.context.scene
    scene.render.engine = args.engine
    if args.engine == "CYCLES":
        scene.cycles.samples = args.samples
        scene.cycles.use_denoising = True
    else:
        scene.eevee.taa_render_samples = max(args.samples, 64)
    w, h = (int(x) for x in args.resolution.split("x"))
    scene.render.resolution_x = w
    scene.render.resolution_y = h
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = os.path.abspath(args.out)

    # --- render ---
    print("rendering...", flush=True)
    bpy.ops.render.render(write_still=True)
    print(f"saved {scene.render.filepath}", flush=True)


if __name__ == "__main__":
    main()

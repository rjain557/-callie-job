"""Blender render that imports per-layer STL files and assigns PBR materials.

Run via:
  blender --background --python blender_render_stl.py -- \
      --stldir <dir>  --out <png>  --view ne  --resolution 1600x1100  --samples 128

Each STL is imported as one mesh; the filename (minus .stl) is used as the
layer name to look up the material preset.
"""
from __future__ import annotations
import argparse
import glob
import math
import os
import sys


# Same material presets as the FBX path
MATERIAL_PRESETS = {
    # Floor — warm white-oak wood, slight roughness
    "A-FLOR":         {"name": "WhiteOak Floor", "color": (0.62, 0.45, 0.28, 1), "roughness": 0.50, "metallic": 0.0},
    # Walls — soft warm white
    "A-WALL":         {"name": "Paint White",    "color": (0.94, 0.93, 0.90, 1), "roughness": 0.85, "metallic": 0.0},
    "A-CLNG":         {"name": "Ceiling White",  "color": (0.97, 0.96, 0.94, 1), "roughness": 0.90, "metallic": 0.0},
    "A-TRIM":         {"name": "Trim White",     "color": (0.96, 0.95, 0.93, 1), "roughness": 0.40, "metallic": 0.0},
    # Cabinets — warm cream, slight tone differentiation from walls
    "I-CASE":         {"name": "Cabinet Cream",  "color": (0.86, 0.83, 0.76, 1), "roughness": 0.32, "metallic": 0.0},
    "I-CASE-ISLA":    {"name": "Island Cream",   "color": (0.86, 0.83, 0.76, 1), "roughness": 0.32, "metallic": 0.0},
    "I-CASE-WALL":    {"name": "Wall Cab Cream", "color": (0.86, 0.83, 0.76, 1), "roughness": 0.32, "metallic": 0.0},
    # Pantry — walnut for visual anchor on the east end
    "I-CASE-PANT":    {"name": "Pantry Walnut",  "color": (0.31, 0.20, 0.12, 1), "roughness": 0.40, "metallic": 0.0},
    # Counter — quartz with subtle gray
    "I-CASE-CTR":     {"name": "Quartz Counter", "color": (0.88, 0.87, 0.85, 1), "roughness": 0.18, "metallic": 0.0},
    # Range black — matte black appliance
    "I-FURN-APPL":    {"name": "Range Black",    "color": (0.05, 0.05, 0.06, 1), "roughness": 0.35, "metallic": 0.6},
    # Stainless / brushed
    "I-FURN-APPL-MTL":{"name": "Stainless",      "color": (0.80, 0.80, 0.82, 1), "roughness": 0.22, "metallic": 1.0},
    "I-FURN-SINK":    {"name": "Stainless Sink", "color": (0.82, 0.82, 0.84, 1), "roughness": 0.18, "metallic": 1.0},
    "I-HARDWARE":     {"name": "Brushed Nickel", "color": (0.78, 0.78, 0.80, 1), "roughness": 0.30, "metallic": 1.0},
    # Detail (door reveals)
    "I-DETAIL":       {"name": "Cabinet Detail", "color": (0.78, 0.75, 0.68, 1), "roughness": 0.32, "metallic": 0.0},
    # Tile backsplash — bright white matte
    "I-TILE":         {"name": "Subway Tile",    "color": (0.95, 0.95, 0.93, 1), "roughness": 0.15, "metallic": 0.0},
    # Crown molding — match trim
    "I-CROWN":        {"name": "Crown White",    "color": (0.96, 0.95, 0.93, 1), "roughness": 0.40, "metallic": 0.0},
    # Pendants — antique bronze
    "I-PENDANT":      {"name": "Pendant Bronze", "color": (0.20, 0.14, 0.08, 1), "roughness": 0.45, "metallic": 0.85},
    # Bar stools — walnut
    "I-STOOL":        {"name": "Stool Walnut",   "color": (0.34, 0.22, 0.13, 1), "roughness": 0.40, "metallic": 0.0},
    "A-GLAZ":         {"name": "Glass",          "color": (0.85, 0.92, 0.95, 1), "roughness": 0.05, "metallic": 0.0, "transmission": 0.95},
    "I-FURN-RUG":     {"name": "Wool Rug",       "color": (0.20, 0.31, 0.48, 1), "roughness": 0.95, "metallic": 0.0},
    "I-FURN-DRP":     {"name": "Sheer Drape",    "color": (0.95, 0.94, 0.92, 1), "roughness": 0.50, "metallic": 0.0, "transmission": 0.6},
    "I-FURN-WD":      {"name": "Walnut",         "color": (0.31, 0.20, 0.12, 1), "roughness": 0.35, "metallic": 0.0},
    "I-FURN-MTL":     {"name": "Brass Satin",    "color": (0.71, 0.57, 0.34, 1), "roughness": 0.30, "metallic": 1.0},
    "I-FURN-ART":     {"name": "Art Coastal",    "color": (0.26, 0.43, 0.57, 1), "roughness": 0.50, "metallic": 0.0},
    "E-LITE":         {"name": "Recessed Trim",  "color": (0.86, 0.86, 0.88, 1), "roughness": 0.30, "metallic": 1.0},
}


# Camera presets in Blender meters. Room is at X 0..4.27, Y 0..3.05,
# Z 0..3.05. Cabinets along south wall (Y=0); island center (2.13, 1.83, 0.43).
# We position cameras with NO wall in the camera->target line.
CAMERA_PRESETS = {
    # "ne" — camera in NE corner of room, looking SW toward cabinet run
    "ne":   {"loc": (3.8, 2.6, 1.7),  "target": (1.5, 0.3, 0.9)},
    # "nw" — camera in NW corner, looking SE
    "nw":   {"loc": (0.4, 2.6, 1.7),  "target": (3.0, 0.3, 0.9)},
    # "hallway" — looking through the hallway opening from outside (-X)
    "hallway": {"loc": (-0.6, 1.5, 1.5), "target": (3.0, 1.5, 0.9)},
    # "above" — top-down isometric, camera way above looking down at angle
    "above": {"loc": (5.0, -1.5, 4.5), "target": (2.0, 1.5, 0.5)},
    # "wide" — wide-angle interior view from above the island
    "wide":  {"loc": (3.5, 2.7, 1.8),  "target": (0.5, 0.3, 0.9)},
    # "longwall" — across the island toward the long wall, low and wide
    "longwall": {"loc": (2.13, 2.6, 1.4), "target": (2.13, 0.0, 0.9)},
    # "hero" — slight 3/4 view, from N side looking S over island toward cabinets
    "hero": {"loc": (2.7, 2.4, 1.5), "target": (1.5, 0.4, 0.85)},
}


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--stldir", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--view", default="ne", choices=list(CAMERA_PRESETS))
    p.add_argument("--resolution", default="1600x1100")
    p.add_argument("--samples", type=int, default=128)
    p.add_argument("--engine", default="CYCLES")
    return p.parse_args(argv)


def main():
    import bpy
    import mathutils

    args = parse_args()
    print(f"=== Blender render (STL multi-import) ===", flush=True)
    print(f"stldir={args.stldir}\nout={args.out}", flush=True)

    # Clean scene
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in bpy.data.materials:
        bpy.data.materials.remove(block)

    # Build material registry
    mats = {}
    for prefix, spec in MATERIAL_PRESETS.items():
        m = bpy.data.materials.new(name=spec["name"])
        m.use_nodes = True
        bsdf = m.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = spec["color"]
            bsdf.inputs["Roughness"].default_value = spec["roughness"]
            bsdf.inputs["Metallic"].default_value = spec["metallic"]
            t = spec.get("transmission")
            if t is not None:
                for key in ("Transmission Weight", "Transmission"):
                    if key in bsdf.inputs:
                        bsdf.inputs[key].default_value = t
                        break
        mats[prefix] = m

    fallback = mats["A-WALL"]

    # --- procedural texture upgrades ---
    def add_wood_grain(material, base_color):
        """Add a Wave + Noise texture combo to fake wood grain."""
        nodes = material.node_tree.nodes
        links = material.node_tree.links
        bsdf = nodes.get("Principled BSDF")
        if not bsdf:
            return
        wave = nodes.new("ShaderNodeTexWave")
        wave.wave_type = "BANDS"
        wave.inputs["Scale"].default_value = 8
        wave.inputs["Distortion"].default_value = 4
        wave.inputs["Detail"].default_value = 2
        noise = nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 25
        cr = nodes.new("ShaderNodeValToRGB")
        cr.color_ramp.elements[0].color = (base_color[0]*0.6, base_color[1]*0.55, base_color[2]*0.5, 1)
        cr.color_ramp.elements[1].color = base_color
        mix = nodes.new("ShaderNodeMixRGB")
        mix.blend_type = "MULTIPLY"
        mix.inputs["Fac"].default_value = 0.4
        links.new(wave.outputs["Color"], cr.inputs[0])
        links.new(cr.outputs[0], mix.inputs[1])
        links.new(noise.outputs["Color"], mix.inputs[2])
        links.new(mix.outputs[0], bsdf.inputs["Base Color"])

    def add_marble_veining(material, base_color):
        nodes = material.node_tree.nodes
        links = material.node_tree.links
        bsdf = nodes.get("Principled BSDF")
        if not bsdf:
            return
        noise = nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 5
        noise.inputs["Detail"].default_value = 12
        noise.inputs["Distortion"].default_value = 3
        cr = nodes.new("ShaderNodeValToRGB")
        cr.color_ramp.elements[0].color = base_color
        cr.color_ramp.elements[1].color = (0.55, 0.55, 0.58, 1)  # gray vein
        cr.color_ramp.elements[1].position = 0.62
        links.new(noise.outputs["Fac"], cr.inputs[0])
        links.new(cr.outputs[0], bsdf.inputs["Base Color"])

    def add_brushed_metal(material):
        nodes = material.node_tree.nodes
        links = material.node_tree.links
        bsdf = nodes.get("Principled BSDF")
        if not bsdf:
            return
        noise = nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 200  # tight grain
        noise.inputs["Detail"].default_value = 2
        cr = nodes.new("ShaderNodeValToRGB")
        cr.color_ramp.elements[0].color = (0.18, 0.18, 0.20, 1)  # roughness range
        cr.color_ramp.elements[1].color = (0.30, 0.30, 0.32, 1)
        links.new(noise.outputs["Fac"], cr.inputs[0])
        links.new(cr.outputs[0], bsdf.inputs["Roughness"])

    # Apply procedural textures
    add_wood_grain(mats["A-FLOR"], MATERIAL_PRESETS["A-FLOR"]["color"])
    add_wood_grain(mats["I-CASE-PANT"], MATERIAL_PRESETS["I-CASE-PANT"]["color"])
    add_wood_grain(mats["I-STOOL"], MATERIAL_PRESETS["I-STOOL"]["color"])
    add_marble_veining(mats["I-CASE-CTR"], MATERIAL_PRESETS["I-CASE-CTR"]["color"])
    add_brushed_metal(mats["I-FURN-APPL-MTL"])
    add_brushed_metal(mats["I-FURN-SINK"])
    add_brushed_metal(mats["I-HARDWARE"])

    # Import every STL in the dir
    stls = sorted(glob.glob(os.path.join(args.stldir, "*.stl")))
    print(f"importing {len(stls)} STL files", flush=True)
    for stl in stls:
        layer = os.path.splitext(os.path.basename(stl))[0]
        # Skip near-empty stl
        if os.path.getsize(stl) < 200:
            print(f"  skip {layer} ({os.path.getsize(stl)} bytes — empty)", flush=True)
            continue
        before = set(bpy.data.objects.keys())
        # Blender 4.5 import_mesh.stl deprecated; use wm.stl_import
        try:
            bpy.ops.wm.stl_import(filepath=stl)
        except AttributeError:
            bpy.ops.import_mesh.stl(filepath=stl)
        # Newly added objects
        after = set(bpy.data.objects.keys())
        new_objs = [bpy.data.objects[name] for name in after - before]
        # Pick material
        m = mats.get(layer, fallback)
        for obj in new_objs:
            obj.name = f"{layer}_{obj.name}"
            obj.data.materials.clear()
            obj.data.materials.append(m)
        print(f"  {layer}: {len(new_objs)} mesh(es)", flush=True)

    # Convert from AutoCAD inches to Blender meters
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.transform.resize(value=(0.0254, 0.0254, 0.0254))
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    # Compute scene bounding box for debug visibility
    minp = [1e9, 1e9, 1e9]
    maxp = [-1e9, -1e9, -1e9]
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        for v in obj.bound_box:
            wp = obj.matrix_world @ mathutils.Vector(v)
            minp = [min(minp[i], wp[i]) for i in range(3)]
            maxp = [max(maxp[i], wp[i]) for i in range(3)]
    print(f"scene bbox: {minp} -> {maxp}", flush=True)

    # Make all materials double-sided (helps with single-sided STL faces)
    for m in bpy.data.materials:
        try:
            m.use_backface_culling = False
        except Exception:
            pass

    # Camera
    cam_data = bpy.data.cameras.new("RenderCam")
    cam_obj = bpy.data.objects.new("RenderCam", cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj
    preset = CAMERA_PRESETS[args.view]
    cam_obj.location = preset["loc"]
    direction = mathutils.Vector((
        preset["target"][0] - cam_obj.location[0],
        preset["target"][1] - cam_obj.location[1],
        preset["target"][2] - cam_obj.location[2],
    ))
    cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    cam_data.lens = 28  # wide-ish for interior

    # Lighting — softer sun + 3-pendant area lights over island + ambient fill
    sun = bpy.data.lights.new("Sun", type="SUN")
    sun.energy = 1.5  # gentler than before
    sun.angle = math.radians(3)
    sun_obj = bpy.data.objects.new("Sun", sun)
    bpy.context.scene.collection.objects.link(sun_obj)
    sun_obj.location = (-3, -3, 6)
    sun_obj.rotation_euler = (math.radians(50), math.radians(15), math.radians(-30))

    # Ambient world (warm interior color)
    world = bpy.context.scene.world or bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.92, 0.93, 0.95, 1)
        bg.inputs[1].default_value = 1.0

    # Three pendant lights over the island
    for i, px in enumerate([1.52, 2.13, 2.74]):
        pend = bpy.data.lights.new(f"Pendant{i}", type="POINT")
        pend.energy = 35
        pend.color = (1.0, 0.92, 0.78)  # warm 2700K
        pend_obj = bpy.data.objects.new(f"Pendant{i}", pend)
        bpy.context.scene.collection.objects.link(pend_obj)
        pend_obj.location = (px, 1.83, 2.0)

    # 16 recessed cans across the ceiling — small point lights
    for r in range(4):
        for c in range(4):
            cx = 0.4 + c * 1.0
            cy = 0.45 + r * 0.7
            can = bpy.data.lights.new(f"Can{r}{c}", type="POINT")
            can.energy = 8
            can.color = (1.0, 0.92, 0.78)
            can_obj = bpy.data.objects.new(f"Can{r}{c}", can)
            bpy.context.scene.collection.objects.link(can_obj)
            can_obj.location = (cx, cy, 2.95)

    # Render settings
    scene = bpy.context.scene
    scene.render.engine = args.engine
    if args.engine == "CYCLES":
        scene.cycles.samples = args.samples
        scene.cycles.use_denoising = True
        # GPU if available
        prefs = bpy.context.preferences.addons["cycles"].preferences
        try:
            prefs.compute_device_type = "CUDA"
            prefs.refresh_devices()
            for d in prefs.devices:
                d.use = True
            scene.cycles.device = "GPU"
        except Exception:
            pass
    else:
        scene.eevee.taa_render_samples = max(args.samples, 64)
    w, h = (int(x) for x in args.resolution.split("x"))
    scene.render.resolution_x = w
    scene.render.resolution_y = h
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = os.path.abspath(args.out)

    print("rendering...", flush=True)
    bpy.ops.render.render(write_still=True)
    print(f"saved {scene.render.filepath}", flush=True)


if __name__ == "__main__":
    main()

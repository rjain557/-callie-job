"""End-to-end: AutoCAD DWG -> FBX export -> Blender render -> PNG.

Usage:
  python dwg_to_blender.py
    --project 04-kitchen          (or 05-living-room, 01-home-office)
    --view ne                     (camera angle)
    --resolution 1600x1100
    --samples 128
    --out kitchen-render.png

Pipeline:
  1. Send FBXEXPORT to the running AutoCAD via SendCommand
  2. Wait for the .fbx file
  3. Spawn `blender --background --python blender_render.py -- ...`
  4. Wait for the .png file
"""
from __future__ import annotations
import argparse
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def find_blender():
    candidates = [
        os.path.expandvars(r"%LOCALAPPDATA%\BlenderPortable\blender-*\blender.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\BlenderFoundation.Blender_*\blender.exe"),
        r"C:\Program Files\Blender Foundation\Blender 4.5\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 4.4\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 4.3\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender\blender.exe",
    ]
    import glob
    for path_pattern in candidates:
        for hit in sorted(glob.glob(path_pattern), reverse=True):
            if os.path.exists(hit):
                return hit
    p = shutil.which("blender")
    return p


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--project", required=True)
    p.add_argument("--view", default="ne")
    p.add_argument("--resolution", default="1600x1100")
    p.add_argument("--samples", type=int, default=128)
    p.add_argument("--engine", default="CYCLES")
    p.add_argument("--out", default="render-blender.png")
    args = p.parse_args()

    repo = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    out_dir = os.path.join(repo, "projects", args.project, "out")
    os.makedirs(out_dir, exist_ok=True)
    fbx_path = os.path.join(out_dir, args.project.split("-", 1)[1] + ".fbx")
    out_png = os.path.join(out_dir, args.out)

    # 1) Export FBX from AutoCAD
    print(f"[1/2] FBX export -> {fbx_path}", flush=True)
    from export_fbx import export_fbx
    if not export_fbx(fbx_path):
        sys.exit("FBX export failed")

    # 2) Render in Blender
    print(f"[2/2] Blender render -> {out_png}", flush=True)
    blender = find_blender()
    if not blender:
        sys.exit("Blender not found. Install via winget install BlenderFoundation.Blender")
    print(f"  blender = {blender}", flush=True)

    cmd = [
        blender, "--background",
        "--python", os.path.join(os.path.dirname(__file__), "blender_render.py"),
        "--",
        "--fbx", fbx_path,
        "--out", out_png,
        "--view", args.view,
        "--resolution", args.resolution,
        "--samples", str(args.samples),
        "--engine", args.engine,
    ]
    print("  cmd:", " ".join(f'"{c}"' if " " in c else c for c in cmd), flush=True)
    subprocess.run(cmd, check=True)
    print(f"DONE: {out_png}", flush=True)


if __name__ == "__main__":
    main()

"""Export the active AutoCAD drawing to FBX.

FBXEXPORT command in AutoCAD 2027 prompts:
- Specify name of FBX file: <path>
- Geometry option [All/Selected/Layer/Sheet] <All>: A
- Export materials [Yes/No] <Yes>: Y
- Export textures [Yes/No] <Yes>: Y
- Export lights [Yes/No] <Yes>: Y
- Export cameras [Yes/No] <Yes>: Y
- Done

We pre-set FILEDIA=0 so the export goes through the command line and does
not pop the Save As dialog.
"""
from __future__ import annotations
import os, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from acad import Acad


def export_fbx(out_path: str):
    a = Acad(); a.cancel(); time.sleep(0.3); a.connect(); a.wait_idle(5)
    print(f"doc={a.doc.Name}", flush=True)
    sv = a.doc.SetVariable
    sv("FILEDIA", 0); sv("CMDDIA", 0); sv("EXPERT", 5)

    # FBXEXPORT also has a non-dialog form. Use _-FBXEXPORT (dash) just in case.
    # Default options accept All, Yes, Yes, Yes, Yes — we just send blanks
    # to take defaults.
    out_path = os.path.abspath(out_path)
    if os.path.exists(out_path):
        os.remove(out_path)

    cmd = f'_.-FBXEXPORT\n{out_path}\n_A\n_Y\n_Y\n_Y\n_Y\n'
    print(f"sending FBXEXPORT to {out_path}", flush=True)
    try:
        a.send_command(cmd)
    except Exception as e:
        print(f"  EXC: {e}", flush=True)

    # Wait for the file to appear
    for i in range(60):
        time.sleep(1)
        if os.path.exists(out_path):
            size = os.path.getsize(out_path)
            print(f"  exported: {out_path} ({size:,} bytes)", flush=True)
            return out_path
    print("  TIMEOUT — FBX not produced. Check AutoCAD command line for errors.",
          flush=True)
    return None


def main():
    out_dir = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "projects", "04-kitchen", "out"
    ))
    os.makedirs(out_dir, exist_ok=True)
    export_fbx(os.path.join(out_dir, "kitchen.fbx"))


if __name__ == "__main__":
    main()

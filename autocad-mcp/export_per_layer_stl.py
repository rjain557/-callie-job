"""Export each AutoCAD layer's 3D solids to its own STL file.

Strategy: freeze all other layers, run STLOUT with selection=ALL (only the
visible layer's geometry is selectable when others are frozen), repeat
per layer.

Blender will import each .stl and name the resulting mesh by filename so
we can reassign PBR materials.
"""
from __future__ import annotations
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from acad import Acad


# Layers we want to render. Skip A-CLNG (frozen for visibility),
# A-ANNO-* (annotations, not 3D).
RENDER_LAYERS = [
    "A-FLOR", "A-WALL", "A-TRIM", "A-GLAZ",
    "I-CASE", "I-CASE-ISLA", "I-CASE-WALL", "I-CASE-PANT",
    "I-CASE-CTR", "I-FURN-APPL", "I-FURN-APPL-MTL", "I-FURN-SINK",
    "I-DETAIL", "I-HARDWARE", "I-TILE", "I-CROWN",
    "I-PENDANT", "I-STOOL",
]

# Layers that exist in the dwg should be set frozen state per export iteration.
# The "all layers" set we'll discover at runtime.


def export_one_layer(a: Acad, target: str, out_path: str, all_layers: list[str]):
    """Freeze every layer except `target`, then STLOUT all selected solids."""
    sv = a.doc.SetVariable
    sv("FILEDIA", 0); sv("CMDDIA", 0); sv("EXPERT", 5)

    # Set target as active so we can freeze others
    try:
        a.set_active_layer(target)
    except Exception as e:
        print(f"  set_active({target}): {e}", flush=True)

    # Freeze all non-target layers
    for L in all_layers:
        if L == target:
            try: a.freeze_layer(L, freeze=False)
            except Exception: pass
        else:
            try: a.freeze_layer(L, freeze=True)
            except Exception: pass

    if os.path.exists(out_path):
        os.remove(out_path)

    # STLOUT: select objects, all, then options. With FILEDIA=0 takes path on cmd line.
    cmd = f'_.STLOUT\nALL\n\n_Y\n{out_path}\n'
    try:
        a.send_command(cmd)
    except Exception as e:
        print(f"  STLOUT EXC: {e}", flush=True)

    # Wait for file
    for _ in range(20):
        time.sleep(0.5)
        if os.path.exists(out_path):
            return os.path.getsize(out_path)
    return 0


def main():
    a = Acad(); a.cancel(); time.sleep(0.3); a.connect(); a.wait_idle(5)
    print(f"doc={a.doc.Name}", flush=True)

    out_dir = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "projects", "04-kitchen", "out", "stl-by-layer"
    ))
    os.makedirs(out_dir, exist_ok=True)

    # Discover all layers
    all_layers = [L["name"] for L in a.list_layers()]
    print(f"all layers in dwg: {all_layers}", flush=True)

    # Save current frozen state so we can restore
    initial_frozen = {L["name"]: L["frozen"] for L in a.list_layers()}

    # Export each render layer
    results = {}
    for L in RENDER_LAYERS:
        if L not in all_layers:
            continue
        out = os.path.join(out_dir, f"{L}.stl")
        size = export_one_layer(a, L, out, all_layers)
        results[L] = size
        print(f"  {L}: {size:,} bytes", flush=True)

    # Restore frozen state
    print("restoring layer states", flush=True)
    for L in all_layers:
        try:
            a.freeze_layer(L, freeze=initial_frozen.get(L, False))
        except Exception:
            pass
    a.set_active_layer("0")
    a.save()
    print(f"\nDONE. {sum(1 for s in results.values() if s > 0)} layers exported", flush=True)


if __name__ == "__main__":
    main()

"""Delete duplicate 3D solids (same bounding box) left by partial v2 runs."""
from __future__ import annotations
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from acad import Acad


def main():
    a = Acad()
    a.connect()
    doc = a.doc
    # Collect all 3D solids with bbox
    seen = {}
    dupes = []
    by_layer: dict[str, int] = {}
    total = 0
    for ent in doc.ModelSpace:
        if ent.ObjectName != "AcDb3dSolid":
            continue
        total += 1
        by_layer[ent.Layer] = by_layer.get(ent.Layer, 0) + 1
        try:
            bb_min, bb_max = ent.GetBoundingBox()
        except Exception:
            continue
        key = (round(bb_min[0], 2), round(bb_min[1], 2), round(bb_min[2], 2),
               round(bb_max[0], 2), round(bb_max[1], 2), round(bb_max[2], 2),
               ent.Layer)
        if key in seen:
            dupes.append((ent.Handle, key))
        else:
            seen[key] = ent.Handle

    print(f"Total 3D solids: {total}")
    print(f"Unique by bbox+layer: {len(seen)}")
    print(f"Duplicates to delete: {len(dupes)}")
    print(f"Layer counts BEFORE: {by_layer}")

    deleted = 0
    for handle, key in dupes:
        try:
            ent = doc.HandleToObject(handle)
            ent.Delete()
            deleted += 1
        except Exception as e:
            print(f"  could not delete {handle}: {e}")

    print(f"Deleted {deleted} duplicates")

    # Final count
    by_layer2: dict[str, int] = {}
    final = 0
    for ent in doc.ModelSpace:
        if ent.ObjectName != "AcDb3dSolid":
            continue
        final += 1
        by_layer2[ent.Layer] = by_layer2.get(ent.Layer, 0) + 1
    print(f"Layer counts AFTER: {by_layer2}")
    print(f"Final 3D solids: {final}")

    doc.Save()
    print("Saved.")


if __name__ == "__main__":
    main()

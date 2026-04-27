"""Probe what light-creation APIs exist on this AutoCAD 2027 build."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from acad import Acad

a = Acad(); a.cancel(); a.connect(); a.wait_idle(5)
ms = a.ms
methods = [m for m in dir(ms) if "ight" in m.lower() or "Light" in m]
print("ms light methods:", methods)
# Also check Documents.Add* and other interfaces
print("\nIAcadModelSpace:", type(ms).__name__)
# Try AddPointLight
if hasattr(ms, "AddPointLight"):
    print("HAS AddPointLight")
else:
    print("NO AddPointLight")
print(f"\nactive doc: {a.doc.Name}, entities: {ms.Count}")

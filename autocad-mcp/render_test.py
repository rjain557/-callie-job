"""Probe the AutoCAD 2027 RENDER COM/SendCommand surface.

Strategy 1 — set RENDEROUTPUTFILENAME and run `_.-RENDER` (dash form).
Strategy 2 — set RENDEROUTPUTSIZE then RENDER without dash and see what
            shows up in the render window destination.
We try strategy 1 first, save after, and report what file (if any) was
written.
"""
from __future__ import annotations
import os, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from acad import Acad


def main():
    a = Acad(); a.cancel(); time.sleep(0.3); a.connect(); a.wait_idle(5)
    print(f"doc={a.doc.Name}", flush=True)
    sv = a.doc.SetVariable

    # Suppress dialogs
    sv("FILEDIA", 0); sv("CMDDIA", 0); sv("EXPERT", 5)

    # Probe relevant sysvars one at a time, catching read-only or unknown.
    probes = [
        "RENDEROUTPUTFILENAME",
        "RENDEROUTPUTSIZE",
        "RENDEREXPOSURE",
        "RENDERPRESET",
        "RENDERLIGHTING",
        "RPREF",
    ]
    for name in probes:
        try:
            v = a.doc.GetVariable(name)
            print(f"  {name} = {v!r}", flush=True)
        except Exception as e:
            print(f"  {name}: read failed: {e}", flush=True)


if __name__ == "__main__":
    main()

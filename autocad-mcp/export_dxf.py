"""Export the active drawing to DXF (ASCII). Reliable via SendCommand,
preserves geometry + layer info — perfect for Blender re-import.

Command: `_.DXFOUT` with FILEDIA=0 takes the path from the command line.
"""
from __future__ import annotations
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from acad import Acad


def export_dxf(out_path: str):
    a = Acad(); a.cancel(); time.sleep(0.3); a.connect(); a.wait_idle(5)
    print(f"doc={a.doc.Name}", flush=True)
    sv = a.doc.SetVariable
    sv("FILEDIA", 0); sv("CMDDIA", 0); sv("EXPERT", 5)

    out_path = os.path.abspath(out_path)
    if os.path.exists(out_path):
        os.remove(out_path)

    # Use the COM SaveAs API directly — DXF format code is depending on
    # AutoCAD version. AC1027 (2013+) DXF == acR2013_dxf == 64
    # acR2018_dxf == 70, acR2024_dxf == newer
    try:
        # Use the SaveAs method — second arg is the file format constant
        # acDXF = various ints depending on version. Use string method instead.
        a.doc.SaveAs(out_path, 64)  # acR2013_dxf
        print(f"  saved via COM SaveAs -> {out_path}", flush=True)
        if os.path.exists(out_path):
            return out_path
    except Exception as e:
        print(f"  COM SaveAs failed: {e}", flush=True)

    # Fallback: SendCommand DXFOUT (with FILEDIA=0 the dialog is suppressed)
    print("  fallback: SendCommand _.DXFOUT", flush=True)
    cmd = f'_.DXFOUT\n{out_path}\n\n'  # path + accept default options + enter
    try:
        a.send_command(cmd)
    except Exception as e:
        print(f"  EXC: {e}", flush=True)
    for i in range(60):
        time.sleep(1)
        if os.path.exists(out_path):
            return out_path
    return None


def main():
    out_dir = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "projects", "04-kitchen", "out"
    ))
    p = export_dxf(os.path.join(out_dir, "kitchen.dxf"))
    print(f"DXF: {p}  size={os.path.getsize(p):,}" if p else "FAILED", flush=True)


if __name__ == "__main__":
    main()

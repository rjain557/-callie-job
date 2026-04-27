"""Try several RENDER syntaxes that might output to a PNG file directly.
Each is sent and we wait briefly to see if AutoCAD writes the file."""
from __future__ import annotations
import os, sys, time, glob

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from acad import Acad


def main():
    a = Acad(); a.cancel(); time.sleep(0.3); a.connect(); a.wait_idle(5)
    sv = a.doc.SetVariable
    sv("FILEDIA", 0); sv("CMDDIA", 0); sv("EXPERT", 5)

    out_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "projects", "04-kitchen", "out", "render-final.png"
    ))
    if os.path.exists(out_path):
        os.remove(out_path)

    # Variant A: -RENDER with file destination (AutoCAD 2026+ syntax)
    print("[A] sending _.-RENDER with file output...", flush=True)
    cmd = f'_.-RENDER\n_M\n_F\n{out_path}\n'
    try:
        a.send_command(cmd)
        # Render takes time — wait
        for i in range(30):
            time.sleep(2)
            if os.path.exists(out_path):
                print(f"  file appeared at {out_path}", flush=True)
                return
        print("  timeout waiting for file", flush=True)
    except Exception as e:
        print(f"  EXC: {e}", flush=True)

    # Variant B: SAVEIMG (older) — writes the current viewport to a raster file
    print("[B] trying _.SAVEIMG...", flush=True)
    out_b = out_path.replace("render-final", "render-saveimg")
    if os.path.exists(out_b): os.remove(out_b)
    try:
        a.send_command(f'_.SAVEIMG\n{out_b}\n')
        for i in range(15):
            time.sleep(1)
            if os.path.exists(out_b):
                print(f"  file appeared at {out_b}", flush=True)
                break
        else:
            print("  timeout", flush=True)
    except Exception as e:
        print(f"  EXC: {e}", flush=True)


if __name__ == "__main__":
    main()

"""Continuation of finish_project.py — capture the SWISO presentation render.

Splits out the iso snapshot because AutoCAD won't let you freeze the active
layer; finish_project.py left A-ANNO-TEXT active. We switch active to "0",
freeze the anno layers, render, then thaw + save.
"""
from __future__ import annotations
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ctypes
import psutil
import win32gui
import win32con
import win32process
import win32ui
from PIL import Image

from acad import Acad


def capture_full_screen(out_path: str):
    user32 = ctypes.windll.user32
    w = user32.GetSystemMetrics(0)
    h = user32.GetSystemMetrics(1)
    hdesk = win32gui.GetDesktopWindow()
    hwnd_dc = win32gui.GetWindowDC(hdesk)
    mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
    save_dc = mfc_dc.CreateCompatibleDC()
    bmp = win32ui.CreateBitmap()
    bmp.CreateCompatibleBitmap(mfc_dc, w, h)
    save_dc.SelectObject(bmp)
    save_dc.BitBlt((0, 0), (w, h), mfc_dc, (0, 0), win32con.SRCCOPY)
    bi = bmp.GetInfo()
    bs = bmp.GetBitmapBits(True)
    img = Image.frombuffer("RGB", (bi["bmWidth"], bi["bmHeight"]), bs, "raw", "BGRX", 0, 1)
    img.save(out_path)
    win32gui.DeleteObject(bmp.GetHandle())
    save_dc.DeleteDC()
    mfc_dc.DeleteDC()
    win32gui.ReleaseDC(hdesk, hwnd_dc)


def restore_acad_window():
    pids = [p.info["pid"] for p in psutil.process_iter(["pid", "name"])
            if (p.info["name"] or "").lower() == "acad.exe"]
    main_hwnd = None
    def cb(hwnd, _):
        nonlocal main_hwnd
        if not win32gui.IsWindowVisible(hwnd):
            return
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        if pid in pids and "AutoCAD" in win32gui.GetWindowText(hwnd):
            main_hwnd = hwnd
    win32gui.EnumWindows(cb, None)
    if main_hwnd:
        if win32gui.IsIconic(main_hwnd):
            win32gui.ShowWindow(main_hwnd, win32con.SW_RESTORE)
        time.sleep(0.6)


def main():
    a = Acad()
    a.cancel(); time.sleep(0.5)
    a.connect()
    a.wait_idle(5)

    print(f"doc={a.doc.Name}  entities={a.doc.ModelSpace.Count}")

    # Move active layer off any anno layer
    print("set active layer = 0")
    a.set_active_layer("0")

    # Freeze anno layers for clean 3D
    print("freeze anno layers")
    a.freeze_layer("A-ANNO-DIMS", freeze=True)
    a.freeze_layer("A-ANNO-TEXT", freeze=True)

    print("SWISO + Conceptual + zoom extents")
    a.set_view("SWISO"); a.wait_idle(3)
    a.set_visual_style("Conceptual"); a.wait_idle(3)
    a.zoom_extents()
    time.sleep(1.0)

    out_dir = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "projects", "01-home-office", "out"
    ))
    restore_acad_window()
    out = os.path.join(out_dir, "presentation-iso.png")
    print(f"snap -> {out}")
    capture_full_screen(out)

    # Thaw so the dwg, when reopened, shows annotations
    print("thaw anno layers")
    a.freeze_layer("A-ANNO-DIMS", freeze=False)
    a.freeze_layer("A-ANNO-TEXT", freeze=False)

    # Re-set view to TOP for next time the dwg opens — plan view is the deliverable
    a.set_view("TOP"); a.wait_idle(3)
    a.set_visual_style("2DWireframe"); a.wait_idle(3)
    a.zoom_extents()

    a.save()
    print(f"DONE. saved: {a.doc.FullName}")


if __name__ == "__main__":
    main()

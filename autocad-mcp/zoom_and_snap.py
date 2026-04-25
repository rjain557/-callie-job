"""Zoom extents, set SW isometric + Conceptual, then snap."""
from __future__ import annotations
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from acad import Acad

import ctypes
import psutil
import win32gui
import win32con
import win32process
import win32ui
from PIL import Image


def capture_full_screen(out_path):
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


def main():
    a = Acad()
    a.cancel()
    time.sleep(0.5)
    a.connect()
    # retry resolving .doc in case AutoCAD is momentarily busy
    for i in range(10):
        try:
            name = a.doc.Name
            print(f"active: {name}")
            break
        except Exception as e:
            print(f"  waiting on doc ({i}): {e}")
            time.sleep(1.0)
    else:
        raise SystemExit("AutoCAD never became responsive")
    try:
        a.set_view("SWISO")
        a.wait_idle(5)
    except Exception as e:
        print(f"view: {e}")
    try:
        a.set_visual_style("Conceptual")
        a.wait_idle(5)
    except Exception as e:
        print(f"style: {e}")
    a.zoom_extents()
    time.sleep(1.0)

    # Restore window maximized
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
        win32gui.ShowWindow(main_hwnd, win32con.SW_SHOWMAXIMIZED)
        time.sleep(1.2)

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                       "projects", "01-home-office", "out", "home-office-v2.png")
    capture_full_screen(os.path.abspath(out))
    print(f"saved: {out}")

    # Final count + save
    entcount = a.doc.ModelSpace.Count
    print(f"entities: {entcount}")
    a.save()


if __name__ == "__main__":
    main()

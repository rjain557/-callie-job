"""Capture a screenshot of AutoCAD after restoring/sizing the window."""
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


def find_acad_main():
    pids = [p.info["pid"] for p in psutil.process_iter(["pid", "name"])
            if (p.info["name"] or "").lower() == "acad.exe"]
    found = []

    def cb(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return
        _, wpid = win32process.GetWindowThreadProcessId(hwnd)
        if pids and wpid in pids and "AutoCAD" in win32gui.GetWindowText(hwnd):
            found.append(hwnd)

    win32gui.EnumWindows(cb, None)
    return found[0] if found else None


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
    bmpinfo = bmp.GetInfo()
    bmpstr = bmp.GetBitmapBits(True)
    img = Image.frombuffer("RGB", (bmpinfo["bmWidth"], bmpinfo["bmHeight"]),
                           bmpstr, "raw", "BGRX", 0, 1)
    img.save(out_path)
    win32gui.DeleteObject(bmp.GetHandle())
    save_dc.DeleteDC()
    mfc_dc.DeleteDC()
    win32gui.ReleaseDC(hdesk, hwnd_dc)


def main():
    hwnd = find_acad_main()
    if hwnd:
        # Restore if iconic; then Maximize
        try:
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.ShowWindow(hwnd, win32con.SW_SHOWMAXIMIZED)
            win32gui.SetWindowPos(hwnd, win32con.HWND_TOP, 0, 0, 0, 0,
                                  win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW)
        except Exception as e:
            print(f"Restore/show: {e}")
        time.sleep(1.5)

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                       "projects", "01-home-office", "out", "home-office-v2.png")
    out = os.path.abspath(out)
    capture_full_screen(out)
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()

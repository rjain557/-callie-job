"""Shared snapshot utilities — capture AutoCAD's main window only."""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import time

import psutil
import win32gui
import win32con
import win32process
import win32ui
from PIL import Image

# PrintWindow flag: include the window's child rendering surfaces
# (DirectX/OpenGL viewports). Requires Windows 8.1+.
PW_RENDERFULLCONTENT = 0x00000002

_user32 = ctypes.WinDLL("user32", use_last_error=True)
_user32.PrintWindow.argtypes = [wintypes.HWND, wintypes.HDC, wintypes.UINT]
_user32.PrintWindow.restype = wintypes.BOOL


def find_acad_main_hwnd():
    pids = [p.info["pid"] for p in psutil.process_iter(["pid", "name"])
            if (p.info["name"] or "").lower() == "acad.exe"]
    found = []

    def cb(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        if pid in pids and "AutoCAD" in win32gui.GetWindowText(hwnd):
            found.append(hwnd)

    win32gui.EnumWindows(cb, None)
    return found[0] if found else None


def restore_window(hwnd, width: int = 1600, height: int = 1100):
    """Resize AutoCAD to a deterministic rect for capture.

    Forcing an explicit size avoids the ultrawide-maximize problem (window
    becomes 1490x420 on a 32:9 monitor and the drawing is tiny).
    """
    if not hwnd:
        return
    if win32gui.IsIconic(hwnd):
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        time.sleep(0.4)
    # Make sure it isn't maximized — otherwise SetWindowPos size is ignored.
    try:
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    except Exception:
        pass
    try:
        win32gui.SetWindowPos(hwnd, win32con.HWND_TOP, 0, 0, width, height,
                              win32con.SWP_SHOWWINDOW)
    except Exception:
        pass
    time.sleep(0.7)


def capture_window(hwnd, out_path: str):
    """Capture an AutoCAD window using PrintWindow w/ PW_RENDERFULLCONTENT.

    Uses the window's own backbuffer instead of reading screen pixels, so
    the capture is correct even when VS Code (or anything else) is on top.
    """
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    w, h = right - left, bottom - top

    win_dc = win32gui.GetWindowDC(hwnd)
    src_dc = win32ui.CreateDCFromHandle(win_dc)
    mem_dc = src_dc.CreateCompatibleDC()
    bmp = win32ui.CreateBitmap()
    bmp.CreateCompatibleBitmap(src_dc, w, h)
    mem_dc.SelectObject(bmp)

    ok = _user32.PrintWindow(hwnd, mem_dc.GetSafeHdc(), PW_RENDERFULLCONTENT)
    if not ok:
        # fallback: BitBlt from window DC (may be black on GPU surfaces)
        mem_dc.BitBlt((0, 0), (w, h), src_dc, (0, 0), win32con.SRCCOPY)

    bi = bmp.GetInfo()
    bs = bmp.GetBitmapBits(True)
    img = Image.frombuffer("RGB", (bi["bmWidth"], bi["bmHeight"]), bs, "raw", "BGRX", 0, 1)
    img.save(out_path)
    win32gui.DeleteObject(bmp.GetHandle())
    mem_dc.DeleteDC()
    src_dc.DeleteDC()
    win32gui.ReleaseDC(hwnd, win_dc)


def crop_centered_aspect(path: str, target_aspect: float = 1.6):
    """Re-open the saved PNG and crop to the given aspect ratio (W/H), centered.

    Use to strip the dead horizontal padding when AutoCAD is maximized onto
    an ultrawide monitor: the drawing sits in the middle of the viewport.
    """
    img = Image.open(path)
    w, h = img.size
    cur_aspect = w / h if h else 1.0
    if cur_aspect <= target_aspect + 0.05:
        return  # already close enough
    new_w = int(h * target_aspect)
    left = max(0, (w - new_w) // 2)
    img.crop((left, 0, left + new_w, h)).save(path)


def capture_acad(out_path: str, target_aspect: float = 1.6):
    hwnd = find_acad_main_hwnd()
    if not hwnd:
        raise RuntimeError("AutoCAD window not found")
    restore_window(hwnd)
    capture_window(hwnd, out_path)
    crop_centered_aspect(out_path, target_aspect=target_aspect)
    return hwnd

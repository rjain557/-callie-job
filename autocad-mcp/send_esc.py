"""Force-focus AutoCAD and send ESC with the Alt-tap foreground-unlock trick."""
import time
import psutil
import win32api
import win32con
import win32gui
import win32process


def find_acad_main():
    pids = [p.info["pid"] for p in psutil.process_iter(["pid", "name"])
            if (p.info["name"] or "").lower() == "acad.exe"]
    found = []

    def cb(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return
        _, wpid = win32process.GetWindowThreadProcessId(hwnd)
        if wpid in pids and "AutoCAD 2027" in win32gui.GetWindowText(hwnd):
            found.append(hwnd)

    win32gui.EnumWindows(cb, None)
    return found[0] if found else None


def force_foreground(hwnd):
    # Tap Alt to unlock foreground stealing restriction
    win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)
    win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)
    time.sleep(0.05)
    # Restore if minimized
    if win32gui.IsIconic(hwnd):
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    win32gui.BringWindowToTop(hwnd)
    try:
        win32gui.SetForegroundWindow(hwnd)
        return True
    except Exception as e:
        print(f"SetForegroundWindow err: {e}")
        return False


def main():
    main_hwnd = find_acad_main()
    print(f"main: {main_hwnd}")
    ok = force_foreground(main_hwnd)
    print(f"foregrounded: {ok}")
    time.sleep(0.5)
    fg = win32gui.GetForegroundWindow()
    print(f"foreground hwnd now: {fg} ('{win32gui.GetWindowText(fg)}')")
    # Send Esc via real hardware-level event
    for _ in range(5):
        win32api.keybd_event(win32con.VK_ESCAPE, 0x01, 0, 0)
        time.sleep(0.04)
        win32api.keybd_event(win32con.VK_ESCAPE, 0x01, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(0.2)
    print("Sent 5x ESC")


if __name__ == "__main__":
    main()

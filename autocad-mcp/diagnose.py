"""Dump every window belonging to acad.exe so we can see what's blocking."""
import psutil
import win32gui
import win32process


def main():
    pids = [p.info["pid"] for p in psutil.process_iter(["pid", "name"])
            if (p.info["name"] or "").lower() == "acad.exe"]
    print(f"acad.exe PIDs: {pids}")

    top_level = []

    def cb(hwnd, _):
        _, wpid = win32process.GetWindowThreadProcessId(hwnd)
        if wpid in pids:
            visible = win32gui.IsWindowVisible(hwnd)
            enabled = win32gui.IsWindowEnabled(hwnd)
            cls = win32gui.GetClassName(hwnd)
            title = win32gui.GetWindowText(hwnd)
            top_level.append({
                "hwnd": hwnd, "cls": cls, "title": title,
                "visible": visible, "enabled": enabled,
            })

    win32gui.EnumWindows(cb, None)
    for w in top_level:
        print(w)


if __name__ == "__main__":
    main()

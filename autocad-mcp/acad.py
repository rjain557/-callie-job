"""
AutoCAD COM wrapper.

Talks to a running AutoCAD instance via Windows COM automation.
Launches AutoCAD if it isn't already running.

Design notes
------------
* `Acad.connect()` returns a fresh or cached Application object. When a call
  fails with RPC_SERVER_UNAVAILABLE (AutoCAD was closed and restarted) or
  RPC_E_CALL_REJECTED (modal busy state), we retry-with-reconnect inside a
  decorator so callers don't have to think about it.
* `IAcadLayer.Color` was removed in the AutoCAD 2027 COM typelib. We now
  drive color through `TrueColor` (AcCmColor object) with an ACI fallback.
* `cancel()` sends WM_KEYDOWN/WM_KEYUP for VK_ESCAPE to the command-line
  Edit control via Win32 PostMessage — the only reliable way to break out
  of a stuck modal prompt without focus stealing.
* `wait_idle()` polls CMDACTIVE until 0 (no command active) so callers can
  serialize after a raw SendCommand without flying blind.
"""

from __future__ import annotations

import time
from functools import wraps
from typing import Any, Callable

import pythoncom
import win32com.client

# Optional deps for cancel() — degrade gracefully if missing.
try:
    import win32gui
    import win32process
    import win32api
    import win32con
    import psutil
    _WIN32_OK = True
except ImportError:
    _WIN32_OK = False


_APP_PROGID = "AutoCAD.Application"

# COM error codes we treat as "reconnect and retry"
_RPC_SERVER_UNAVAILABLE = -2147023174  # 0x800706BA
# And "wait and retry" (AutoCAD is modal-busy, not dead)
_RPC_E_CALL_REJECTED = -2147418111  # 0x80010001
_RPC_E_SERVERCALL_RETRYLATER = -2147418111  # same code family


class AcadError(RuntimeError):
    pass


def _variant_double_array(values: list[float]):
    return win32com.client.VARIANT(
        pythoncom.VT_ARRAY | pythoncom.VT_R8, list(values)
    )


def _point3(xyz):
    if len(xyz) == 2:
        xyz = (xyz[0], xyz[1], 0.0)
    return _variant_double_array([float(xyz[0]), float(xyz[1]), float(xyz[2])])


def _points_flat(points):
    flat: list[float] = []
    for p in points:
        flat.extend([float(p[0]), float(p[1])])
    return _variant_double_array(flat)


def _is_rpc_unavailable(exc) -> bool:
    return isinstance(exc, pythoncom.com_error) and getattr(exc, "hresult", None) == _RPC_SERVER_UNAVAILABLE \
        or (isinstance(exc, pythoncom.com_error) and exc.args and exc.args[0] == _RPC_SERVER_UNAVAILABLE)


def _is_rpc_rejected(exc) -> bool:
    return isinstance(exc, pythoncom.com_error) and exc.args and exc.args[0] == _RPC_E_CALL_REJECTED


def _resilient(method: Callable):
    """Auto-reconnect on RPC_SERVER_UNAVAILABLE, retry-with-backoff on RPC_E_CALL_REJECTED."""

    @wraps(method)
    def wrapper(self, *args, **kwargs):
        attempts = 0
        max_rejects = 5
        while True:
            try:
                return method(self, *args, **kwargs)
            except pythoncom.com_error as e:
                code = e.args[0] if e.args else None
                if code == _RPC_SERVER_UNAVAILABLE:
                    # Stale COM ref — AutoCAD restarted. Reconnect once.
                    self._app = None
                    if attempts == 0:
                        attempts += 1
                        self.connect()
                        continue
                    raise
                if code == _RPC_E_CALL_REJECTED:
                    if attempts < max_rejects:
                        attempts += 1
                        time.sleep(0.5 * attempts)
                        continue
                    raise
                raise

    return wrapper


class Acad:
    """Thin wrapper around the AutoCAD Application COM object."""

    def __init__(self) -> None:
        self._app = None

    # ---------- connection ----------

    def connect(self, launch_if_needed: bool = True, timeout_s: float = 60.0):
        pythoncom.CoInitialize()
        try:
            self._app = win32com.client.GetActiveObject(_APP_PROGID)
            return self._app
        except Exception:
            if not launch_if_needed:
                raise AcadError("AutoCAD is not running and launch_if_needed=False")

        self._app = win32com.client.Dispatch(_APP_PROGID)
        self._app.Visible = True

        deadline = time.time() + timeout_s
        while time.time() < deadline:
            try:
                _ = self._app.Documents.Count
                break
            except Exception:
                time.sleep(0.5)
        else:
            raise AcadError("Timed out waiting for AutoCAD to become ready")

        try:
            if self._app.Documents.Count == 0:
                self._app.Documents.Add()
        except Exception:
            pass
        return self._app

    @property
    def app(self):
        if self._app is None:
            self.connect()
        return self._app

    @property
    def doc(self):
        return self.app.ActiveDocument

    @property
    def ms(self):
        return self.doc.ModelSpace

    # ---------- synchronization ----------

    @_resilient
    def wait_idle(self, timeout_s: float = 30.0) -> dict[str, Any]:
        """Poll CMDACTIVE until 0 (no command running) or timeout."""
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            try:
                active = int(self.doc.GetVariable("CMDACTIVE"))
            except Exception:
                time.sleep(0.2)
                continue
            if active == 0:
                return {"idle": True, "elapsed_s": round(timeout_s - (deadline - time.time()), 2)}
            time.sleep(0.2)
        return {"idle": False, "timeout_s": timeout_s}

    def cancel(self) -> dict[str, Any]:
        """Win32-level escape: PostMessage VK_ESCAPE to AutoCAD's command-line Edit control.
        Works even when COM is rejecting calls, because it bypasses COM entirely."""
        if not _WIN32_OK:
            return {"ok": False, "error": "Win32 deps missing"}

        WM_KEYDOWN, WM_KEYUP, VK_ESCAPE = 0x0100, 0x0101, 0x1B

        pids = [p.info["pid"] for p in psutil.process_iter(["pid", "name"])
                if (p.info["name"] or "").lower() == "acad.exe"]
        if not pids:
            return {"ok": False, "error": "acad.exe not running"}

        # Find main hwnd + the command-line Edit child
        main_hwnd = None

        def top_cb(hwnd, _):
            nonlocal main_hwnd
            if not win32gui.IsWindowVisible(hwnd):
                return
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            if pid in pids and "AutoCAD" in win32gui.GetWindowText(hwnd):
                main_hwnd = hwnd

        win32gui.EnumWindows(top_cb, None)
        if not main_hwnd:
            return {"ok": False, "error": "AutoCAD main window not found"}

        edit_hwnd = None

        def child_cb(hwnd, _):
            nonlocal edit_hwnd
            if win32gui.GetClassName(hwnd) == "Edit":
                edit_hwnd = hwnd

        win32gui.EnumChildWindows(main_hwnd, child_cb, None)

        targets = [main_hwnd]
        if edit_hwnd:
            targets.append(edit_hwnd)

        for hwnd in targets:
            for _ in range(3):
                win32api.PostMessage(hwnd, WM_KEYDOWN, VK_ESCAPE, 0)
                win32api.PostMessage(hwnd, WM_KEYUP, VK_ESCAPE, 0)

        return {"ok": True, "main_hwnd": main_hwnd, "edit_hwnd": edit_hwnd, "sent": 3}

    # ---------- document ops ----------

    @_resilient
    def status(self) -> dict[str, Any]:
        a = self.app
        try:
            active = a.ActiveDocument
            active_info = {
                "name": active.Name,
                "path": active.FullName,
                "saved": bool(active.Saved),
                "active_layer": active.ActiveLayer.Name,
                "entity_count": active.ModelSpace.Count,
            }
        except Exception as e:
            active_info = {"error": str(e)}
        return {
            "version": a.Version,
            "visible": bool(a.Visible),
            "document_count": a.Documents.Count,
            "active_document": active_info,
        }

    @_resilient
    def new_drawing(self, template: str | None = None):
        if template:
            doc = self.app.Documents.Add(template)
        else:
            doc = self.app.Documents.Add()
        return {"name": doc.Name, "path": doc.FullName}

    @_resilient
    def open_drawing(self, path: str):
        doc = self.app.Documents.Open(path)
        return {"name": doc.Name, "path": doc.FullName}

    @_resilient
    def save(self, path: str | None = None) -> dict[str, Any]:
        d = self.doc
        if path:
            d.SaveAs(path)
        else:
            d.Save()
        return {"name": d.Name, "path": d.FullName, "saved": bool(d.Saved)}

    @_resilient
    def zoom_extents(self) -> None:
        self.app.ZoomExtents()

    # ---------- raw command ----------

    @_resilient
    def send_command(self, cmd: str) -> None:
        """Queue a raw AutoCAD command string. Must end with newline (we enforce it)."""
        if not cmd.endswith("\n"):
            cmd = cmd + "\n"
        self.doc.SendCommand(cmd)

    # ---------- 2D geometry ----------

    @_resilient
    def add_line(self, start, end) -> dict[str, Any]:
        ent = self.ms.AddLine(_point3(start), _point3(end))
        return {"handle": ent.Handle, "type": ent.ObjectName, "layer": ent.Layer}

    @_resilient
    def add_polyline(self, points, closed: bool = False) -> dict[str, Any]:
        if len(points) < 2:
            raise AcadError("polyline needs at least 2 points")
        ent = self.ms.AddLightWeightPolyline(_points_flat(points))
        if closed:
            ent.Closed = True
        return {"handle": ent.Handle, "type": ent.ObjectName, "closed": bool(ent.Closed), "layer": ent.Layer}

    @_resilient
    def add_rectangle(self, lower_left, upper_right) -> dict[str, Any]:
        x1, y1 = float(lower_left[0]), float(lower_left[1])
        x2, y2 = float(upper_right[0]), float(upper_right[1])
        pts = [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
        return self.add_polyline(pts, closed=True)

    @_resilient
    def add_circle(self, center, radius: float) -> dict[str, Any]:
        ent = self.ms.AddCircle(_point3(center), float(radius))
        return {"handle": ent.Handle, "type": ent.ObjectName, "layer": ent.Layer}

    @_resilient
    def add_text(self, insertion, text: str, height: float = 2.5) -> dict[str, Any]:
        ent = self.ms.AddText(text, _point3(insertion), float(height))
        return {"handle": ent.Handle, "type": ent.ObjectName, "layer": ent.Layer}

    # ---------- 3D solids ----------

    @_resilient
    def add_box(self, corner1, corner2) -> dict[str, Any]:
        """Create a 3D box between two opposite corners. Uses ModelSpace.AddBox
        which takes center + length/width/height."""
        x1, y1, z1 = (float(corner1[0]), float(corner1[1]),
                      float(corner1[2]) if len(corner1) > 2 else 0.0)
        x2, y2, z2 = (float(corner2[0]), float(corner2[1]),
                      float(corner2[2]) if len(corner2) > 2 else 0.0)
        cx, cy, cz = (x1 + x2) / 2, (y1 + y2) / 2, (z1 + z2) / 2
        length = abs(x2 - x1)
        width = abs(y2 - y1)
        height = abs(z2 - z1)
        ent = self.ms.AddBox(_point3([cx, cy, cz]), length, width, height)
        return {"handle": ent.Handle, "type": ent.ObjectName, "layer": ent.Layer,
                "center": [cx, cy, cz], "size": [length, width, height]}

    @_resilient
    def add_cylinder(self, center, radius: float, height: float) -> dict[str, Any]:
        """Vertical cylinder: axis along Z, base centered at `center`."""
        cx, cy, cz = (float(center[0]), float(center[1]),
                      float(center[2]) if len(center) > 2 else 0.0)
        # AddCylinder takes the base center (not mid); cz is the bottom.
        # But AutoCAD's AddCylinder actually uses the *axis midpoint*. Offset by h/2.
        mid = [cx, cy, cz + float(height) / 2.0]
        ent = self.ms.AddCylinder(_point3(mid), float(radius), float(height))
        return {"handle": ent.Handle, "type": ent.ObjectName, "layer": ent.Layer,
                "base_center": [cx, cy, cz], "radius": float(radius), "height": float(height)}

    @_resilient
    def boolean(self, op: str, source_handles: list[str], other_handles: list[str]) -> dict[str, Any]:
        """Boolean: op in ('union','subtract','intersect').
        Subtract/Intersect: `source` is the result receiver, `other` is consumed."""
        op = op.lower()
        op_code = {"union": 0, "subtract": 0, "intersect": 2}
        # Actual COM constants:
        #   acUnion = 0
        #   acSubtraction = 1 (some sources say; AutoCAD Boolean method uses these ints)
        #   acIntersection = 2
        code_map = {"union": 0, "subtract": 1, "intersect": 2}
        if op not in code_map:
            raise AcadError(f"unknown boolean op: {op}")
        if not source_handles:
            raise AcadError("source_handles is empty")

        src = self.doc.HandleToObject(source_handles[0])
        # If multiple sources, union them first
        for h in source_handles[1:]:
            s = self.doc.HandleToObject(h)
            src.Boolean(0, s)  # union

        if op == "union":
            for h in other_handles:
                o = self.doc.HandleToObject(h)
                src.Boolean(0, o)
        else:
            others = [self.doc.HandleToObject(h) for h in other_handles]
            # Boolean each other into src
            for o in others:
                src.Boolean(code_map[op], o)

        return {"handle": src.Handle, "op": op, "remaining": src.ObjectName}

    # ---------- entity modification ----------

    @_resilient
    def change_color(self, handle: str, color_index: int) -> dict[str, Any]:
        """Set TrueColor of a single entity by handle."""
        ent = self.doc.HandleToObject(handle)
        tc = self.app.GetInterfaceObject(f"AutoCAD.AcCmColor.{int(self.app.Version.split('.')[0])}")
        tc.ColorMethod = 0xC3  # acColorMethodByACI
        tc.ColorIndex = int(color_index)
        ent.TrueColor = tc
        return {"handle": handle, "color_index": int(color_index)}

    # ---------- views & visual style ----------

    @_resilient
    def set_view(self, preset: str) -> dict[str, Any]:
        """Set current viewport to a named 3D preset. Preset = SWISO/SEISO/NEISO/NWISO/TOP/FRONT/BACK/LEFT/RIGHT."""
        preset = preset.upper()
        ok = {"SWISO", "SEISO", "NEISO", "NWISO", "TOP", "FRONT", "BACK", "LEFT", "RIGHT"}
        if preset not in ok:
            raise AcadError(f"unknown preset: {preset}")
        self.send_command(f"_.-VIEW\n_{preset}\n")
        return {"view": preset}

    @_resilient
    def set_visual_style(self, style: str) -> dict[str, Any]:
        """Conceptual/Realistic/Shaded/ShadedWithEdges/Wireframe/2DWireframe/XRay."""
        self.send_command(f"_.VSCURRENT\n_{style}\n")
        return {"visual_style": style}

    # ---------- inspection ----------

    @_resilient
    def list_entities(self, type_filter: str | None = None, limit: int = 200) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for i, ent in enumerate(self.ms):
            if i >= limit:
                break
            obj_name = ent.ObjectName
            if type_filter and type_filter.lower() not in obj_name.lower():
                continue
            row: dict[str, Any] = {
                "handle": ent.Handle,
                "type": obj_name,
                "layer": ent.Layer,
            }
            try:
                if obj_name == "AcDbLine":
                    row["start"] = list(ent.StartPoint)
                    row["end"] = list(ent.EndPoint)
                    row["length"] = ent.Length
                elif obj_name == "AcDbCircle":
                    row["center"] = list(ent.Center)
                    row["radius"] = ent.Radius
                elif obj_name in ("AcDbPolyline", "AcDb2dPolyline"):
                    row["closed"] = bool(ent.Closed)
                    try:
                        row["length"] = ent.Length
                    except Exception:
                        pass
                elif obj_name in ("AcDbText", "AcDbMText"):
                    row["text"] = ent.TextString
            except Exception:
                pass
            out.append(row)
        return out

    # ---------- layers ----------

    @_resilient
    def list_layers(self) -> list[dict[str, Any]]:
        out = []
        for layer in self.doc.Layers:
            row = {
                "name": layer.Name,
                "frozen": bool(layer.Freeze),
                "locked": bool(layer.Lock),
                "on": bool(layer.LayerOn),
            }
            # 2027 removed .Color; read via TrueColor.ColorIndex
            try:
                row["color_index"] = int(layer.TrueColor.ColorIndex)
            except Exception:
                pass
            out.append(row)
        return out

    @_resilient
    def create_layer(self, name: str, color_index: int | None = None) -> dict[str, Any]:
        layers = self.doc.Layers
        created = False
        try:
            layer = layers.Item(name)
        except Exception:
            layer = layers.Add(name)
            created = True

        if color_index is not None:
            # Use TrueColor (works on 2027). `Color` property removed from IAcadLayer.
            tc = self.app.GetInterfaceObject(f"AutoCAD.AcCmColor.{int(self.app.Version.split('.')[0])}")
            tc.ColorMethod = 0xC3  # acColorMethodByACI
            tc.ColorIndex = int(color_index)
            layer.TrueColor = tc

        result = {"name": layer.Name, "created": created}
        try:
            result["color_index"] = int(layer.TrueColor.ColorIndex)
        except Exception:
            pass
        return result

    @_resilient
    def set_active_layer(self, name: str) -> dict[str, Any]:
        layer = self.doc.Layers.Item(name)
        self.doc.ActiveLayer = layer
        return {"active_layer": layer.Name}

    @_resilient
    def freeze_layer(self, name: str, freeze: bool = True) -> dict[str, Any]:
        layer = self.doc.Layers.Item(name)
        layer.Freeze = bool(freeze)
        return {"name": layer.Name, "frozen": bool(layer.Freeze)}

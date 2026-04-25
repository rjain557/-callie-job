"""
AutoCAD MCP server.

Exposes a small, useful set of tools that drive a running AutoCAD instance
via Windows COM. Designed to be the first version we grow from — prefer
adding new tools over bloating existing ones.

Launch:
    python server.py

Claude Code registers this via .mcp.json at the repo root.
"""

from __future__ import annotations

import sys
from typing import Any, Optional

from mcp.server.fastmcp import FastMCP

from acad import Acad, AcadError


mcp = FastMCP("autocad")
_acad = Acad()


def _ok(data: Any) -> dict[str, Any]:
    return {"ok": True, "data": data}


def _err(exc: Exception) -> dict[str, Any]:
    return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


# ---------- connection / status ----------

@mcp.tool()
def acad_status() -> dict[str, Any]:
    """Report whether AutoCAD is reachable and what's currently open.

    Returns version, visibility, document count, and details about the
    active drawing (name, path, active layer, entity count).
    """
    try:
        return _ok(_acad.status())
    except Exception as e:
        return _err(e)


@mcp.tool()
def acad_reconnect() -> dict[str, Any]:
    """Force the server to drop its cached COM pointer and reconnect to AutoCAD.

    Use when AutoCAD was closed & reopened (so the old reference is stale) or
    when repeated RPC_SERVER_UNAVAILABLE errors suggest a dead connection.
    """
    try:
        _acad._app = None
        _acad.connect(launch_if_needed=True)
        return _ok(_acad.status())
    except Exception as e:
        return _err(e)


@mcp.tool()
def acad_cancel() -> dict[str, Any]:
    """Send ESC to AutoCAD's command line via Win32 PostMessage (bypasses COM).

    Clears a stuck pick prompt (`Specify opposite corner...`) or any modal
    command-line state that's causing COM to reject calls with RPC_E_CALL_REJECTED.
    Safe to call at any time — no-op if AutoCAD is already idle.
    """
    try:
        return _ok(_acad.cancel())
    except Exception as e:
        return _err(e)


@mcp.tool()
def acad_wait_idle(timeout_s: float = 30.0) -> dict[str, Any]:
    """Block until AutoCAD's CMDACTIVE is 0 (no command running) or timeout.

    Use after a raw `acad_run_command` that queues an async operation to confirm
    it finished before issuing follow-up work.
    """
    try:
        return _ok(_acad.wait_idle(timeout_s=timeout_s))
    except Exception as e:
        return _err(e)


# ---------- document ops ----------

@mcp.tool()
def acad_new_drawing(template: Optional[str] = None) -> dict[str, Any]:
    """Start a new drawing. Optional `template` is an absolute path to a .dwt file."""
    try:
        return _ok(_acad.new_drawing(template))
    except Exception as e:
        return _err(e)


@mcp.tool()
def acad_open_drawing(path: str) -> dict[str, Any]:
    """Open an existing .dwg/.dxf at `path`."""
    try:
        return _ok(_acad.open_drawing(path))
    except Exception as e:
        return _err(e)


@mcp.tool()
def acad_save(path: Optional[str] = None) -> dict[str, Any]:
    """Save the active drawing. Pass `path` to save-as to a new location."""
    try:
        return _ok(_acad.save(path))
    except Exception as e:
        return _err(e)


@mcp.tool()
def acad_zoom_extents() -> dict[str, Any]:
    """Zoom the active viewport to the extents of all drawn geometry."""
    try:
        _acad.zoom_extents()
        return _ok({"zoomed": "extents"})
    except Exception as e:
        return _err(e)


# ---------- raw command (escape hatch + learning tool) ----------

@mcp.tool()
def acad_run_command(command: str) -> dict[str, Any]:
    """Send a raw AutoCAD command string (e.g. 'LINE\\n0,0\\n10,10\\n\\n').

    This is the escape hatch for anything the typed tools don't cover yet.
    Use \\n where you'd press Enter. End with an extra \\n to terminate.
    """
    try:
        _acad.send_command(command)
        return _ok({"sent": command})
    except Exception as e:
        return _err(e)


# ---------- 2D geometry ----------

@mcp.tool()
def acad_draw_line(start: list[float], end: list[float]) -> dict[str, Any]:
    """Draw a line. `start` and `end` are [x, y] or [x, y, z]."""
    try:
        return _ok(_acad.add_line(start, end))
    except Exception as e:
        return _err(e)


@mcp.tool()
def acad_draw_polyline(points: list[list[float]], closed: bool = False) -> dict[str, Any]:
    """Draw a lightweight polyline from a list of [x, y] points. Set `closed=True` to close it."""
    try:
        return _ok(_acad.add_polyline(points, closed=closed))
    except Exception as e:
        return _err(e)


@mcp.tool()
def acad_draw_rectangle(lower_left: list[float], upper_right: list[float]) -> dict[str, Any]:
    """Draw a closed rectangle polyline between two corner points."""
    try:
        return _ok(_acad.add_rectangle(lower_left, upper_right))
    except Exception as e:
        return _err(e)


@mcp.tool()
def acad_draw_circle(center: list[float], radius: float) -> dict[str, Any]:
    """Draw a circle given a center point and radius."""
    try:
        return _ok(_acad.add_circle(center, radius))
    except Exception as e:
        return _err(e)


@mcp.tool()
def acad_draw_text(insertion: list[float], text: str, height: float = 2.5) -> dict[str, Any]:
    """Place single-line text at `insertion` with the given character `height`."""
    try:
        return _ok(_acad.add_text(insertion, text, height))
    except Exception as e:
        return _err(e)


# ---------- 3D solids ----------

@mcp.tool()
def acad_add_box(corner1: list[float], corner2: list[float]) -> dict[str, Any]:
    """Create a 3D solid box between two opposite corners [x,y,z]. Returns handle."""
    try:
        return _ok(_acad.add_box(corner1, corner2))
    except Exception as e:
        return _err(e)


@mcp.tool()
def acad_add_cylinder(center: list[float], radius: float, height: float) -> dict[str, Any]:
    """Create a vertical cylinder. `center` is the base center [x,y,z], axis is +Z."""
    try:
        return _ok(_acad.add_cylinder(center, radius, height))
    except Exception as e:
        return _err(e)


@mcp.tool()
def acad_boolean(op: str, source_handles: list[str], other_handles: list[str]) -> dict[str, Any]:
    """Boolean op on 3D solids. `op` in ('union','subtract','intersect'). For subtract,
    `source_handles[0]` keeps its identity and has `other_handles` subtracted from it.
    Other solids are consumed."""
    try:
        return _ok(_acad.boolean(op, source_handles, other_handles))
    except Exception as e:
        return _err(e)


@mcp.tool()
def acad_change_color(handle: str, color_index: int) -> dict[str, Any]:
    """Override the color of a single entity by handle. Uses AcCmColor (2027-safe)."""
    try:
        return _ok(_acad.change_color(handle, color_index))
    except Exception as e:
        return _err(e)


# ---------- views & visual style ----------

@mcp.tool()
def acad_set_view(preset: str) -> dict[str, Any]:
    """Set viewport to a named 3D preset: SWISO/SEISO/NEISO/NWISO/TOP/FRONT/BACK/LEFT/RIGHT."""
    try:
        return _ok(_acad.set_view(preset))
    except Exception as e:
        return _err(e)


@mcp.tool()
def acad_set_visual_style(style: str) -> dict[str, Any]:
    """Set current visual style: Conceptual/Realistic/Shaded/ShadedWithEdges/Wireframe/2DWireframe/XRay."""
    try:
        return _ok(_acad.set_visual_style(style))
    except Exception as e:
        return _err(e)


# ---------- inspection ----------

@mcp.tool()
def acad_list_entities(type_filter: Optional[str] = None, limit: int = 200) -> dict[str, Any]:
    """List entities in model space. Optional `type_filter` matches ObjectName substring
    (e.g. 'Line', 'Circle', 'Polyline', '3dSolid'). Default limit of 200 keeps output bounded."""
    try:
        return _ok(_acad.list_entities(type_filter=type_filter, limit=limit))
    except Exception as e:
        return _err(e)


# ---------- layers ----------

@mcp.tool()
def acad_list_layers() -> dict[str, Any]:
    """List all layers in the active drawing with color, on/off/frozen/lock state."""
    try:
        return _ok(_acad.list_layers())
    except Exception as e:
        return _err(e)


@mcp.tool()
def acad_create_layer(name: str, color_index: Optional[int] = None) -> dict[str, Any]:
    """Create (or update the color of) a layer. `color_index` is an AutoCAD Color Index (1-255)."""
    try:
        return _ok(_acad.create_layer(name, color_index))
    except Exception as e:
        return _err(e)


@mcp.tool()
def acad_set_active_layer(name: str) -> dict[str, Any]:
    """Set the active layer. New geometry will be placed on this layer."""
    try:
        return _ok(_acad.set_active_layer(name))
    except Exception as e:
        return _err(e)


@mcp.tool()
def acad_freeze_layer(name: str, freeze: bool = True) -> dict[str, Any]:
    """Freeze (or thaw) a layer so it isn't rendered. Useful for hiding the ceiling in 3D views."""
    try:
        return _ok(_acad.freeze_layer(name, freeze=freeze))
    except Exception as e:
        return _err(e)


# ---------- teach mode ----------

@mcp.tool()
def acad_teach(topic: str) -> dict[str, Any]:
    """Return a short explanation of a core AutoCAD concept or command.

    Curated mini-glossary for learning mode. For anything not listed, the model
    should explain it directly and we'll add the answer here if it recurs.
    """
    topic_k = topic.strip().lower()
    entries = {
        "layer": (
            "Layers are AutoCAD's equivalent of transparent sheets stacked on top of each other. "
            "Interior design convention: separate layers for Walls, Doors, Windows, Furniture, "
            "Electrical, Dimensions, Text. Control color/linetype/visibility per layer. Command: LAYER."
        ),
        "polyline": (
            "A single entity made of connected line/arc segments. Preferred over multiple LINE entities "
            "for walls and outlines because you can offset, fillet, and get area as one unit. Command: PLINE."
        ),
        "block": (
            "A reusable group of entities (like a sofa, chair, or door symbol) inserted as one object. "
            "Good for furniture libraries. Command: BLOCK to define, INSERT to place."
        ),
        "units": (
            "UNITS command sets drawing units (inches, mm). For US interior design typically architectural "
            "inches. Set this FIRST before drawing — changing later doesn't rescale existing geometry."
        ),
        "model space": (
            "Where you draw real-world geometry at 1:1 scale. Paper space (layouts) is where you arrange "
            "views for plotting at a specific sheet scale."
        ),
        "ucs": (
            "User Coordinate System. Rotates/moves the drawing axes without moving geometry. Useful for "
            "working on angled walls. Command: UCS."
        ),
        "box": (
            "A 3D solid rectangular prism. AddBox takes a center point + length/width/height. "
            "Two-corner form via the BOX command: BOX <corner1> <corner2>. Sibling primitives: "
            "CYLINDER, SPHERE, CONE, TORUS, WEDGE, PYRAMID."
        ),
        "boolean": (
            "Combine 3D solids: UNION merges, SUBTRACT removes one from another, INTERSECT keeps "
            "only the overlap. Essential for carving door/window openings out of walls."
        ),
        "visual style": (
            "How 3D geometry is rendered in the viewport: 2dWireframe (flat lines), Wireframe (3D lines), "
            "Conceptual (shaded + colored faces), Realistic (materials + lighting), Shaded (smooth shading), "
            "X-Ray (translucent). Command: VSCURRENT."
        ),
    }
    if topic_k in entries:
        return _ok({"topic": topic, "summary": entries[topic_k]})
    return _ok({"topic": topic, "summary": None, "note": "No curated entry — ask the model for an explanation."})


if __name__ == "__main__":
    # Best-effort early connect so startup errors surface before Claude sends a tool call
    try:
        _acad.connect(launch_if_needed=False)
    except Exception as e:
        print(f"[autocad-mcp] AutoCAD not running yet (will launch on first tool call): {e}", file=sys.stderr)
    mcp.run()

# Session — 2026-04-23 / -04-24 (Part 2: First 3D build + MCP hardening)

## What we did

1. Connected the `autocad` MCP server to a live AutoCAD 2027 (trial) session.
2. Built [Project 1 — Home Office](../../projects/01-home-office.md) directly in **3D** (skipping the 2D fundamentals in the brief — user's call), then **upgraded it** to include floor, ceiling, baseboards, door leaf, window glass + muntins + sill + apron, roller shade, area rug, and per-object material colors.
3. **Rewrote `acad.py` and `server.py`** to eliminate every failure mode we hit (auto-reconnect, Win32 cancel, wait-idle, typed 3D tools, AutoCAD 2027 TrueColor compatibility).

Final: [projects/01-home-office/out/home-office.dwg](../../projects/01-home-office/out/home-office.dwg) has **25 3D solids** across 7 layers.

## v2 deliverable

| Layer | Count | Contents |
|---|---|---|
| A-WALL | 4 | S / N / E / W walls with door + window openings cut |
| A-FLOR | 1 | LVP floor plane |
| A-CLNG | 1 | Ceiling slab (layer frozen for 3D view) |
| A-TRIM | 9 | 5 baseboards, 2 window muntins, sill, apron |
| A-DOOR | 1 | Door leaf shown swung open 90° inward |
| A-GLAZ | 2 | Window glass + roller shade (pulled down 24") |
| I-FURN | 7 | Desk, chair, bookcase, armchair, side table, floor lamp, area rug |

Each furniture piece has a per-object color: walnut-brown for wood, charcoal for the task chair, upholstery blue-gray for the armchair, cream for accent pieces, dark gray for the floor lamp. Layers handle everything else via ByLayer.

## What hurt (and what we did about it)

### Problems

1. **Stale COM pointer** after AutoCAD restart — MCP server cached `self._app` forever; `RPC_SERVER_UNAVAILABLE` until restart.
2. **Modal deadlock** on any command-line pick prompt — COM rejects every call with `RPC_E_CALL_REJECTED`; SendCommand can't break out from Claude's side.
3. **Can't send Esc** — COM is blocked; Win32 keystrokes need focus (blocked by foreground-stealing protection); PowerShell `SendKeys` needs per-call approval.
4. **Fly-blind SendCommand** — async, no error signal. One bad LISP leaves AutoCAD wedged; we can't tell.
5. **AutoCAD 2027 typelib drift** — `IAcadLayer.Color` is gone; `IAcadAcCmColor.SetColorMethod` is now a property `ColorMethod`. Silent `AttributeError` even when the underlying operation succeeded.
6. **Raw LISP + `(handent ...)` chains** — brittle; when the first `handent` fails, nothing is created, but SendCommand doesn't report it.

### Fixes now in `acad.py` / `server.py`

| Feature | Where | What it does |
|---|---|---|
| `@_resilient` decorator | [acad.py](../../autocad-mcp/acad.py) | Auto-reconnect on `RPC_SERVER_UNAVAILABLE`; retry-with-backoff on `RPC_E_CALL_REJECTED` |
| `Acad.cancel()` | [acad.py](../../autocad-mcp/acad.py) | Win32 `PostMessage(WM_KEYDOWN, VK_ESCAPE)` to the command-line Edit child. Bypasses COM — works even when COM is rejecting |
| `Acad.wait_idle()` | [acad.py](../../autocad-mcp/acad.py) | Polls `CMDACTIVE` until 0 so you can confirm async SendCommand finished |
| `add_box`, `add_cylinder` | [acad.py](../../autocad-mcp/acad.py) | Use `ModelSpace.AddBox` / `AddCylinder` directly — synchronous, returns handle, no LISP fragility |
| `boolean(op, sources, others)` | [acad.py](../../autocad-mcp/acad.py) | Uses solid's `.Boolean()` method with op codes 0/1/2 — handle-addressed, no select-by-click |
| `change_color(handle, aci)` | [acad.py](../../autocad-mcp/acad.py) | Via `AcCmColor.ColorMethod` (2027-safe). No more raw `-CHPROP` round trips |
| `set_view`, `set_visual_style` | [acad.py](../../autocad-mcp/acad.py) | Typed wrappers around `-VIEW` / `VSCURRENT` SendCommand |
| `freeze_layer` | [acad.py](../../autocad-mcp/acad.py) | Needed for hiding the ceiling in 3D views |
| `create_layer` color fix | [acad.py](../../autocad-mcp/acad.py) | Uses `layer.TrueColor` (new AcCmColor object) instead of removed `.Color` integer |
| New MCP tools | [server.py](../../autocad-mcp/server.py) | `acad_reconnect`, `acad_cancel`, `acad_wait_idle`, `acad_add_box`, `acad_add_cylinder`, `acad_boolean`, `acad_change_color`, `acad_set_view`, `acad_set_visual_style`, `acad_freeze_layer` |

## Scripts used to build v2

The v2 build was driven by a fresh Python process (not via MCP tools) because the running MCP server had a stale COM ref. Scripts live in [autocad-mcp/](../../autocad-mcp/):

- **`build_v2.py`** — reads v1 from the active drawing, maps v1 furniture handles by bounding-box centroid + size (robust against handle renumbering), creates v2 layers + geometry, applies material colors, freezes ceiling, saves.
- **`cleanup_dupes.py`** — deletes 3D solids with identical bounding boxes on the same layer. Needed because partial runs during debugging left duplicates. Went from 40 → 25 solids.
- **`send_esc.py` / `diagnose.py`** — Win32 experiments kept for reference.
- **`snapshot.py` / `zoom_and_snap.py`** — capture the viewport to PNG for verification.
- **`test_com.py`** — single-shot COM health check; useful as a sanity probe when the MCP server is suspect.

## Known follow-ups

1. **`@_resilient` doesn't cover property access** (`.doc`, `.app`, `.ms`) — if `Application` is momentarily busy, property access raises and callers have to retry themselves. Fix: push the try/reconnect into the `doc`/`ms` properties or convert them to methods.
2. **Window restore in `snapshot.py`** kicked AutoCAD into a new modal state once — `ShowWindow(SW_SHOWMAXIMIZED)` when the window was already maximized. Harmless but noisy.
3. **Materials, not just colors** — we used ACI overrides as a stand-in for materials. Real materials (via `MATERIALASSIGN` and the Autodesk Material Library) render properly under Realistic + lights. Project 5 in the curriculum covers this.
4. **Door leaf shown open** is a diagrammatic shortcut. For real documentation, draw the leaf closed + a 2D swing arc on the plan view, and have the 3D solid be the closed panel.
5. **No annotations** — next upgrade should add dimensions, room tag (with area + ceiling height), and furniture labels.
6. **Side table's position** (we placed it at the armchair side but the brief spec for the reading nook wanted it next to the armchair) — worth measuring clearances in a real review.

## Screenshot of v2

[projects/01-home-office/out/home-office-v2.png](../../projects/01-home-office/out/home-office-v2.png) — SW isometric, ceiling frozen, conceptual visual style.

## How to resume

```
# From the repo root:
cd -callie-job
# Open AutoCAD 2027, any drawing
# Then:
.venv/Scripts/python.exe autocad-mcp/build_v2.py   # re-runs idempotently
```

If the MCP server's COM ref goes stale (you restarted AutoCAD since Claude Code launched), call the new `acad_reconnect` tool in chat instead of restarting Claude Code.

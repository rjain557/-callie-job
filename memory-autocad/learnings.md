# Learnings

Durable, non-obvious facts worth remembering. Add to this when something surprised you or a future session would waste time rediscovering it.

## AutoCAD / COM

- `AutoCAD.Application.26` is the ProgID for AutoCAD 2026, `.27` for AutoCAD 2027. Generic `AutoCAD.Application` resolves to the newest installed version — the MCP server at [autocad-mcp/acad.py](../autocad-mcp/acad.py) uses the generic ProgID so it works across AutoCAD versions without changes. User's current workstation has AutoCAD 2027 (trial), not 2026.
- Point arguments to `ModelSpace.AddLine`, `AddCircle`, etc. must be `VARIANT(VT_ARRAY | VT_R8, [...])`. Plain Python lists get rejected. See the helpers in [acad.py](../autocad-mcp/acad.py).
- `AddLightWeightPolyline` takes **flat** [x1, y1, x2, y2, ...] — not nested pairs.
- A modal dialog in AutoCAD (e.g. unsaved-changes prompt) blocks all COM calls silently. If a tool hangs, check AutoCAD first.
- An active command at the AutoCAD command line (e.g. `MOVE Select objects:`) blocks COM with `com_error (-2147418111, 'Call was rejected by callee.')` = `RPC_E_CALL_REJECTED`. Fix: click into AutoCAD and press `Esc` twice to clear the command. If this happens repeatedly, add a typed tool that does `doc.SendCommand("\x1b\x1b")` before the operation.
- When `RPC_E_CALL_REJECTED` persists despite multiple `Esc` presses (user + Win32 `keybd_event` + `PostMessage` + Alt-tap foreground-unlock), `Application.Version` will still respond but `Documents.Count` / `ActiveDocument` will be rejected. At that point the command-line `Esc` trick is not enough. Fastest recovery: close the drawing tab (the `x` next to the filename, not the app X) and reopen via `acad_open_drawing`. `IsHungAppWindow` returns 0, so Task Manager won't flag it — the AutoCAD message pump is fine, it's the COM call filter that's saying "busy."
- `SetForegroundWindow` from a Python subprocess is blocked by Windows' foreground-stealing protection unless you tap `VK_MENU` (Alt) first. Even then, keystrokes may route to the wrong focused control. For keystroke-based unblock attempts, target the command-line Edit child window (class `Edit`) via `PostMessage(hwnd, WM_KEYDOWN, VK_ESCAPE, 0)` — not the top-level `AfxMDIFrame140u` main window.
- `Document.SendCommand` is async — it queues the command string. End with `\n` to execute.
- `IAcadLayer.Color` (ACI integer) was removed in AutoCAD 2027's COM typelib — setting it raises `AttributeError`. The replacement is `TrueColor` (an `AcCmColor` object, obtained via `app.GetInterfaceObject("AutoCAD.AcCmColor.26")`). `acad.py` is now updated to use `TrueColor` for both layers and entities.
- `IAcadAcCmColor.SetColorMethod(...)` in older typelibs became a property `ColorMethod` in AutoCAD 2027. Assign with `tc.ColorMethod = 0xC3` (acColorMethodByACI), not a method call. Easy to miss — `win32com.gen_py` raises `AttributeError` with a "Did you mean: 'ColorMethod'?" hint.
- For multi-step solid modeling (BOX → SUBTRACT chains), wrap the whole sequence in a single LISP `(progn ...)` sent via `acad_run_command`. Capture each solid with `(setq x (entlast))` right after `(command "_.BOX" ...)` so SUBTRACT can reference it by ename. Avoids the interactive-selection problem `SendCommand` would otherwise hit.
- 3D primitive commands via LISP: `(command "_.BOX" "x1,y1,z1" "x2,y2,z2")` (two-corner form), `(command "_.CYLINDER" "cx,cy,cz" radius height)`. Both create solids on the current layer.

## Interior design conventions

- National CAD Standard layer discipline prefixes:
  - `A-` Architectural, `I-` Interiors, `E-` Electrical, `M-` Mechanical, `P-` Plumbing, `S-` Structural
  - Common: `A-WALL`, `A-DOOR`, `A-GLAZ`, `I-FURN`, `E-LITE`, `A-ANNO-DIMS`, `A-ANNO-TEXT`
- Residential standard ceiling height: 8'-0" (96"). Commercial often 9'-0" or 10'-0".
- Standard door widths (interior residential): 2'-0", 2'-6", 2'-8", 3'-0". Exterior: 3'-0" minimum.
- Hallway minimum width (residential, not ADA): 36". ADA: 44".

## Repo gotchas (this repo specifically)

- Repo folder is literally named `-callie-job` (with a leading dash). Shell commands choke on it: always use `./` prefix or `--` separator for `mv`, `cp`, `rm`, etc.
- `.mcp.json` is shared with the job-search pipeline (hosts a `googleworkspace` MCP server). Never overwrite — always read-and-merge.
- PowerShell (Windows PowerShell 5.1 default) does not like non-ASCII characters (em-dashes, smart quotes) in `.ps1` files. Keep setup scripts ASCII.
- VSCode workspace root for this user is `c:/VSCode/callie-job/` (outer wrapper), but the git repo is inside at `c:/VSCode/callie-job/-callie-job/`. User opens Claude Code at the outer wrapper, so a local (non-git-tracked) `.mcp.json` lives at the outer path too, mirroring the inner committed one with absolute paths. Do NOT use relative paths starting with `-callie-job\...` in MCP configs — Python may treat the leading dash as a flag and the server won't start.

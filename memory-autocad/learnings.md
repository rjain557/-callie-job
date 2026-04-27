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
- Cannot freeze the *active* layer — `layer.Freeze = True` raises `Invalid layer`. Always switch active to `0` (or any other layer) before freezing the layer you were just drawing on. Bit me writing iso-snapshot helpers that wanted to hide A-ANNO-* before rendering.
- `AddMText(insertion, width, text)` with embedded font codes (`{\fArial|b1;...}`) often renders nothing if the named font isn't registered as a text style in the drawing — and AutoCAD does not warn. For deliverable text (room tags, stamps, schedule cells), use `AddText` (single-line) with explicit height; reserve `AddMText` only when paragraph wrapping is needed and the active text style is known to be valid.
- `SetVariable("DIMSCALE", 24.0)` (and friends `DIMTXT`, `DIMASZ`, `DIMEXE`, `DIMEXO`, `DIMTAD`, `DIMLUNIT`, `DIMTSZ`, `DIMDLI`) applied to the live dim style propagate to dims created *after* the call. Set them BEFORE creating dims with `AddDimRotated`. Existing dims do not retroactively rescale.

## Snapshot / window capture (Windows)

- Reading pixels from the desktop DC using the AutoCAD window's rect captures whatever is on top — VS Code or any other foreground window will show through. Use `user32.PrintWindow(hwnd, hdc, PW_RENDERFULLCONTENT=2)` instead: it reads from the window's own backbuffer, including the GPU-composited AutoCAD viewport. Available Windows 8.1+.
- `SW_SHOWMAXIMIZED` is unreliable on multi-monitor setups — Windows will pick the "wrong" monitor (often an ultrawide), giving you a 1490×420 window when you wanted ~1600×1100. Force a deterministic size with `SW_RESTORE` followed by `SetWindowPos(... 1600, 1100)`.
- When taking multiple snapshots in sequence, resize the window BEFORE the first `zoom_extents`. Otherwise the first capture is fitted to the old viewport size and looks tiny. Subsequent captures are correct because by then the resize already took effect.
- `CLEANSCREENON` (F11 toggle) hides the ribbon, status bar widgets, and palettes — gives the viewport more pixels for snapshots. Pair with a matching `CLEANSCREENOFF` at the end so the user gets their UI back.

## Driving 3D modeling commands via SendCommand (Project 5)

- **POINTLIGHT** prompts for "Lighting unit" warning the first time it's used. Preset `LIGHTINGUNITS = 2` (photometric international) before the first call. Then the minimal command form is `_.POINTLIGHT\n<x,y,z>\nX\n` — coordinates + eXit. Without the explicit `X`, AutoCAD enters the option-loop and SendCommand never returns to idle.
- **CAMERA** prompts for camera position, target, then enters an option loop. Form: `_.CAMERA\n<px,py,pz>\n<tx,ty,tz>\nX\n`. Save as named view via `_.-VIEW\n_S\n<name>\n` — that part works.
- **`_.-VIEW _R <name>`** does NOT reliably restore a camera view's position when that view was saved via `CAMERA`+`-VIEW _S`. It snaps to a default isometric instead. Workaround: render at the time the camera is set, or use `IAcadView.SetCamera` direct COM.
- **LOFT** with handle-addressed sections works: `(setq sa (handent "...")) (command "_.LOFT" sa sb sc "" "_C")`. The `_C` after the empty enter selects "Cross-sections only" mode (no guides/path).
- **REVOLVE** with handle-addressed profile + axis points: `(command "_.REVOLVE" pf "" "x1,y1,z1" "x2,y2,z2" 360)`. Works but leaves AutoCAD in a busy state for several seconds on complex profiles — wrap subsequent ops in try/except and don't access ActiveDocument immediately.
- **SWEEP** with handle-addressed profile and path: `(command "_.SWEEP" pf "" pa)`. Profile must be a closed planar curve at the start of the path; path is a 3D polyline.
- **FILLETEDGE** with handle reference: `(command "_.FILLETEDGE" "_R" 0.5 ct "")`. The `"_R" 0.5` sets radius before selecting; trailing `""` exits.
- **`Documents.Add()` opens a "Select Template" dialog** by default. Either pass an explicit template path string, or — if you've already created a blank Drawing1.dwg — sidestep by `SaveAs` to your destination path via `acad_save(<path>)`. Setting `FILEDIA=0` doesn't always suppress this particular dialog because it pre-dates the system variable.
- **`Documents.Add` from inside a script while a modal dialog is up causes RPC_E_CALL_REJECTED for ALL subsequent COM calls** until the dialog is dismissed manually.

## AutoCAD sysvars that are read-only or hang via COM SetVariable on AutoCAD 2027

- `SUNSTATUS = 1` — hangs the calling thread permanently. Set via `SUNPROPERTIES` palette.
- `LATITUDE`, `LONGITUDE`, `TIMEZONE` — write-attempt may hang. Set via `GEOGRAPHICLOCATION` command (which also opens a dialog).
- `LIGHTINGUNITS = 2` — works fine via SetVariable. Required prerequisite for POINTLIGHT/SPOTLIGHT to skip the lighting-unit warning.
- `DEFAULTLIGHTING = 0` — works fine via SetVariable.
- `FILEDIA`, `CMDDIA`, `EXPERT` — work fine. Useful for `EXPERT >= 4` to suppress most "Are you sure?" prompts during heavy edits.

## Materials API on AutoCAD 2027

- `doc.Materials.Add(name)` creates a basic material; `doc.Materials.Item(name)` retrieves.
- `IAcadMaterial.Diffuse` does NOT exist on the 2027 typelib. Material color is set via the (largely undocumented) material map child objects, or via the GUI's Material Editor. For COM scripting, `Materials.Add` + assign-to-layer is enough to register a named material that can later be edited by hand.
- `layer.Material = "matname"` works once the material exists in `doc.Materials`. Assigning by-layer is cleaner than per-object.
- Library imports via `MATBROWSER` are GUI-only — there's no COM equivalent for "import this material from the AutoCAD Material Library."

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

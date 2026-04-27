# Session — 2026-04-25 (Project 1 deliverable package)

## What we did

Took the v2 3D model from the 04-23/24 session and built it out into a full
package "a remote interior designer would deliver to a client":

1. **Annotated the plan** in model space — A-ANNO-DIMS and A-ANNO-TEXT layers,
   5 linear dimensions (overall E-W, N-S, door, door offset, window),
   7 numbered FF&E tag bubbles keyed to the schedule, room tag, designer
   stamp, north arrow.
2. **Set the dim style for plot scale 1/2"=1'-0"** via system variables
   (`DIMSCALE=24`, `DIMTXT=0.125`, `DIMASZ=0.125`, etc.) so dim text and
   arrowheads come out at 1/8" plotted.
3. **Captured two presentation PNGs** at 1600×1100 directly from AutoCAD's
   own backbuffer (PrintWindow + `PW_RENDERFULLCONTENT`) — `floor-plan.png`
   in TOP/2DWireframe and `presentation-iso.png` in SWISO/Conceptual.
4. **Wrote companion docs** — `SPEC.md` (project narrative, FF&E schedule,
   finish schedule, lighting/power notes, scope exclusions) and
   `PRESENTATION.md` (client-facing cover sheet referencing the PNGs).

Final deliverable lives at
[projects/01-home-office/out/](../../projects/01-home-office/out/):
`home-office.dwg` (54 entities), `floor-plan.png`, `presentation-iso.png`,
`SPEC.md`, `PRESENTATION.md`.

## What hurt (and what we did about it)

### 1. AutoCAD modal-deadlock at session start

Same as last time — `RPC_E_CALL_REJECTED` until the user clicked into the
AutoCAD window and pressed ESC three times. `acad_cancel` (Win32
PostMessage) was sent successfully but did not clear the state. Possibly
because AutoCAD was in a state that doesn't accept ESC over PostMessage
(modal dialog vs. command-line picker).

**Carry-forward:** investigate whether `acad_cancel` should also try
`SendMessage` (synchronous) or attach-thread-input + SetForegroundWindow as
a last resort. For now, manual ESC after modal hangs is the workaround.

### 2. Snapshot captured the wrong window contents

`zoom_and_snap.py` read pixels from the desktop DC at the AutoCAD window's
rect — but VS Code was on top, so the captured pixels were VS Code, not
AutoCAD.

**Fix:** new `snap_helpers.py` uses `user32.PrintWindow` with
`PW_RENDERFULLCONTENT` (Windows 8.1+). That reads from the window's own
backbuffer, so even a covered or off-screen AutoCAD window captures
correctly — including the GPU-composited viewport.

### 3. `SW_SHOWMAXIMIZED` produced an ultrawide-but-short capture

User's setup is multi-monitor with at least one 32:9 ultrawide display.
Maximizing AutoCAD landed it on the wide monitor (~1490×420) which is
useless for a portrait-shaped floor plan. Drawing came out tiny and
horizontally surrounded by dead pixels.

**Fix:** `restore_window` now uses `SW_RESTORE` followed by an explicit
`SetWindowPos` to a deterministic 1600×1100 — predictable across monitor
configs. The cropping helper (`crop_centered_aspect`) also strips remaining
horizontal slack.

### 4. First snapshot in a sequence was zoomed wrong

If `restore_window` ran *inside* `capture_acad`, the first call's
`zoom_extents` had already happened against the old window dimensions —
the drawing was sized for the previous viewport. The iso (second call)
was fine because by then the resize had already taken effect.

**Fix:** `finish_resnap.py` now calls `restore_window` upfront before any
view operations; `zoom_extents` runs against the correct viewport from the
first capture onward.

### 5. MText with `\f...|b1;` formatting codes sometimes rendered invisible

Initial room tag and designer stamp were `AddMText` with embedded font and
color codes. They didn't display. Suspect the font name (`Arial`) wasn't
registered as a SHX/TTF in this drawing's text style, so AutoCAD silently
skipped formatting — and the default style had Height=0 with no fallback.

**Fix:** switched to plain `AddText` (single-line) with explicit heights.
Three `AddText` calls for the room tag, five for the stamp. Less elegant
but bulletproof.

### 6. `freeze_layer` on the *active* layer is rejected

`finish_project.py` was setting `A-ANNO-TEXT` active in step 7, then trying
to freeze it in step 9. AutoCAD raises `Invalid layer` because you cannot
freeze the active layer.

**Fix:** the iso-snapshot helper switches the active layer to `0` before
freezing the anno layers.

## Tools added this session

| File | Purpose |
| --- | --- |
| [autocad-mcp/finish_project.py](../../autocad-mcp/finish_project.py) | Idempotent build of the annotation set on top of the v2 model |
| [autocad-mcp/finish_iso_snap.py](../../autocad-mcp/finish_iso_snap.py) | One-shot SWISO Conceptual snapshot (used during recovery from #6) |
| [autocad-mcp/finish_resnap.py](../../autocad-mcp/finish_resnap.py) | Re-take both deliverable snapshots after edits |
| [autocad-mcp/snap_helpers.py](../../autocad-mcp/snap_helpers.py) | Shared `PrintWindow` capture + window-resize + crop helpers |

## Known follow-ups

1. **`acad_cancel` resilience.** It worked for "stuck pick prompt" but not
   "modal-busy at session start" today. Consider adding a SendMessage path
   and a focus-then-keybd-event fallback.
2. **Promote dim/text creation to typed MCP tools.** `AddDimRotated` and
   `AddText`/`AddMText` are still called by direct COM in the script. Per
   the convention in [CONTEXT.md](../CONTEXT.md), if used twice we promote.
   They're now used >>2x — promote next session: `acad_add_linear_dim`,
   `acad_add_mtext`.
3. **Promote dim style sysvar batch** to a tool: `acad_set_plot_scale(scale)`
   that sets DIMSCALE, DIMTXT, DIMASZ etc. for a target plot scale.
4. **Layouts and title blocks in paper space.** This deliverable is model
   space + companion markdown. A truly print-ready set would have
   `Layout1` (cover), `Layout2` (plan with title block), `Layout3` (iso).
   Project 3 in the curriculum covers this — defer.
5. **Materials, not flat ACI.** Project 5 territory.
6. **Reflected ceiling plan** with light fixtures. Recommended in `SPEC.md`
   §5 but not modeled. Add when Project 4 (kitchen elevations) introduces
   ceiling-cut workflows.

## How to resume / re-run

```
cd -callie-job
# Open AutoCAD 2027 (any drawing)
.venv/Scripts/python.exe autocad-mcp/finish_project.py   # builds annotations
.venv/Scripts/python.exe autocad-mcp/finish_resnap.py    # re-snaps PNGs
```

Both scripts are idempotent — `finish_project` deletes prior `A-ANNO-*`
geometry before drawing fresh.

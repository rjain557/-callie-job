# TechniCadBridge — System Specification (v1.0, ready-to-build)

**Project:** `technijian-cad-bridge`
**Type:** AutoCAD 2026/2027 .NET plugin (NETLOAD-able DLL)
**Target user:** rjain (single-machine, single-user; not Autodesk-marketplace)
**Spec status:** v1.0 — superseding `PLUGIN_SPEC.md` v0.1; all open questions resolved
**Author:** Claude — handed off as a working document; subject to revision during Phase 1

---

## About this document

This is the **single source of truth** for TechniCadBridge. It is the
README, the architecture doc, the developer guide, the runbook, the
protocol reference, and the changelog rolled into one file. If
something contradicts this doc, this doc wins until amended.

**Audience:** anyone implementing, reviewing, or debugging the plugin.
Not aimed at end users — end users only see the Python client side.

**How to read it:**

- **First time?** Read § 0 (TL;DR), § 2 (Goals), § 3 (Architecture).
  That's enough to understand what we're building.
- **Going to start coding?** Add § 11 (Project layout), § 12
  (Lifecycle), § 13 (Code examples), § 14 (Build), § 17 (Phased
  tickets), § 21 (Developer guide).
- **Going to integrate from Python?** Add § 4 (Wire protocol), § 5
  (Method catalog), § 6 (Error model), § 22 (Protocol reference
  examples).
- **Triaging a production bug?** § 16 (Observability & runbook), § 8
  (Logging & telemetry), § 19 (Risks).

**Maintenance rules:**

- All changes are versioned via § 10 (semver). Bump the schema version
  in § 7 if you change config shape.
- Append a Changelog entry in Appendix D for every released change. No
  silent edits.
- Method-catalog changes (§ 5) require updating Appendix B (Python
  facade mapping) and a new entry in Appendix D.
- The auto-generated `docs/PROTOCOL.md` (Phase 4 deliverable) is
  derived from XML doc comments on `[RpcMethod]` attributes; do not
  hand-edit it. Until that exists, § 22 of this doc is canonical.

**Quick start (developer machine, after Phase 1.10 lands):**

```powershell
# 1. Clone and build
git clone https://github.com/rjain557/technijian-cad-bridge
cd technijian-cad-bridge
.\scripts\build.ps1

# 2. Install
.\packaging\install.ps1

# 3. Restart AutoCAD; confirm
Test-NetConnection 127.0.0.1 -Port 7878
# TcpTestSucceeded : True

# 4. From the -callie-job repo, the existing scripts now use the plugin
cd ..\-callie-job
$env:USE_PLUGIN = '1'
.\.venv\Scripts\python.exe autocad-mcp\build_kitchen.py
```

If anything in steps 1–4 fails, see § 16 (Observability & runbook).

---

## Quick index

| § | Topic |
|---|---|
| 1 | Decisions on the v0.1 open questions |
| 2 | Goals, scope, non-goals |
| 3 | Architecture (process model, threading, transport) |
| 4 | Wire protocol — JSON-RPC 2.0 contract |
| 5 | Method catalog — 84 RPC methods across 11 handlers |
| 6 | Error model |
| 7 | Configuration (`config.json`) |
| 8 | Logging & telemetry |
| 9 | Security |
| 10 | Versioning & API stability |
| 11 | Project layout (.NET solution + Python facade) |
| 12 | Lifecycle (startup, command pump, shutdown, hot reload) |
| 13 | Code examples — the hard parts |
| 14 | Build, install, uninstall |
| 15 | Testing strategy & CI |
| 16 | Observability & runbook |
| 17 | Phased roadmap with concrete tickets |
| 18 | Acceptance tests |
| 19 | Risks & mitigations |
| 20 | Effort, cost, schedule |
| 21 | Developer guide (deep-dive: dev env, debugging, adding handlers, code style) |
| 22 | Protocol reference — full request/response examples per handler |
| Appendix A | JSON Schema for all method params/returns |
| Appendix B | Mapping from existing `acad.py` methods to plugin methods |
| Appendix C | AutoCAD .NET API references used |
| Appendix D | Changelog |

---

## 1. Decisions on the v0.1 open questions

| # | Question | Decision | Rationale |
|---|---|---|---|
| 1 | Repo location | **Separate repo:** `github.com/rjain557/technijian-cad-bridge` (private) | Plugin's release cycle is independent of `-callie-job`'s design output; cleaner versioning, cleaner CI, easier to share with Callie or Technijian colleagues without dragging the design portfolio along |
| 2 | Scope of supported Autodesk products | **AutoCAD core only** for v1. Architecture allows future Civil3D / Map3D / Mechanical handlers as add-on assemblies | Each Autodesk vertical has its own ObjectARX surface; bundling them now adds 5× the API surface to test against; we don't currently use those verticals |
| 3 | License | **Private repo through Phase 4.** Phase 5 (post-launch) review for **MIT open-source**. Autodesk's ObjectARX EULA is compatible with MIT for the plugin code itself, but redistributing Autodesk libraries is not permitted; users must own AutoCAD | Keeps our options open; we're not blocked from open-sourcing later, just not pre-committing |
| 4 | Telemetry | **Yes, local-only, opt-in.** Logs to `%APPDATA%\TechniCadBridge\trace.jsonl`. Off by default (`config.telemetry.enabled = false`). One JSON line per RPC call: `{ts, method, latency_ms, ok, error_code?}`. Rotated daily, kept 30 days. Never leaves the machine | Useful for debugging "why was that slow"; local-only means no privacy concern; opt-in means no surprise disk writes |
| 5 | Blender orchestration | **Stays on Python side.** Plugin focuses on AutoCAD; Python's `dwg_to_blender.py` continues to spawn Blender. Plugin's only Blender-related job is to provide reliable FBX/glTF/STL export | Plugin should not manage subprocesses; cleaner separation of concerns; Python is already the right place for cross-tool orchestration |

---

## 2. Goals, scope, non-goals

### 2.1 Primary goals (ranked)

1. **Replace COM as the only-true-path to AutoCAD.** Today `autocad-mcp/acad.py` calls AutoCAD via `pywin32` COM. The plugin is the new transport; COM stays as a fallback for environments where the plugin can't be installed.
2. **Eliminate the modal-dialog deadlock pattern.** Every method in the plugin's API is *guaranteed* to either complete or return a structured error within `config.timeouts.command_ms` (default 30 s). No more "AutoCAD froze on a Save As dialog and we have to manually ESC."
3. **Expose capabilities that don't exist over COM.** Library material import, headless render, paper-space layout, photometric lights without command-line gymnastics — see § 5 for the full list (28 methods marked **NEW**).
4. **Be drop-in for existing scripts.** Phase 1 deliverable: re-run `build_kitchen.py` end-to-end against the plugin with one config flag, no other code changes.

### 2.2 Secondary goals

- Be debuggable. Anyone with `nc localhost 7878` can hand-issue commands.
- Be testable. Handlers are pure C# functions; they can be unit-tested with mocked `Document` / `Database` objects.
- Be reasonable to maintain. ≤ 3000 lines of C# at v1.0; one file per handler; no clever metaprogramming.

### 2.3 Non-goals (explicit)

| Non-goal | Why |
|---|---|
| AutoCAD LT support | LT doesn't support .NET plugins |
| Mac AutoCAD | Mac AutoCAD's .NET API is a subset; needs separate spec |
| Multi-user / multi-instance | Single AutoCAD process, single plugin, single client |
| Public marketplace plugin | No Autodesk certification, no installer signing |
| Custom palette / GUI | The plugin is a daemon; UI lives in Claude Code |
| BricsCAD / ZWCAD / IntelliCAD compatibility | Different APIs |
| Web / cross-machine remote control | Local TCP only; firewall blocks public access |
| AutoCAD command-history replay / undo across sessions | Out of scope; AutoCAD's own undo handles this |

---

## 3. Architecture

### 3.1 Process model

```
┌────────────────────────────────────────────────────────────────────┐
│ AutoCAD.exe (single instance)                                      │
│  │                                                                  │
│  ├─ Document Manager                                                │
│  │   ├─ kitchen.dwg (active)                                        │
│  │   └─ home-office.dwg                                             │
│  │                                                                  │
│  └─ TechniCadBridge.dll (NETLOAD'd at startup)                      │
│      ├─ JsonRpcServer       — TCP 127.0.0.1:7878                    │
│      ├─ ClientSession[]     — one per connected client              │
│      ├─ CommandQueue        — main-thread serialization             │
│      ├─ AcadSynchronizationContext — wraps Application.Idle         │
│      ├─ HandlerRegistry     — method-name → handler dispatch        │
│      └─ Handlers/{Document,Layer,Geometry,...}                      │
└────────────────────────────────────────────────────────────────────┘
                          ▲
                          │ JSON-RPC 2.0 over TCP, line-delimited
                          ▼
┌────────────────────────────────────────────────────────────────────┐
│ Python MCP server (autocad-mcp/server.py)                          │
│  ├─ FastMCP exposing mcp__autocad__* tools                          │
│  ├─ acad.py — facade with plugin-first, COM-fallback                │
│  └─ plugin_client.py — JSON-RPC client wrapper                      │
└────────────────────────────────────────────────────────────────────┘
                          ▲
                          │ MCP / stdio
                          ▼
                  Claude Code (Anthropic CLI)
```

### 3.2 Threading model

AutoCAD's managed API requires document-touching calls to run on the
main thread. The plugin enforces this with a single-consumer queue:

```
TCP listener (background thread, IOCP)
   │
   ▼  parse JSON-RPC frame, validate
   ▼
ClientSession (one per connection, on its own thread)
   │
   ▼  resolve handler, dispatch
   ▼
CommandQueue.Enqueue(handler.Execute, params)
   │
   ▼  wait for completion via TaskCompletionSource
   ▼
Application.Idle (main thread)
   │
   ▼  CommandQueue.TryDequeue(out var cmd)
   ▼  cmd.Execute() on main thread
   ▼  result → TaskCompletionSource.SetResult
   ▼
ClientSession resumes, serializes result, writes to TCP
```

**Why a queue and not just `Application.Invoke`:** AutoCAD doesn't
expose a generic "run this on main thread" primitive. `Application.Idle`
is the documented escape hatch. Idle fires whenever AutoCAD's message
pump is empty — which means inside a modal dialog, *Idle does NOT
fire*. We use this to detect-and-fail-fast on modal locks (see § 6.4).

**Long-running ops** (`Render.ToFile`, `Plot.ToPdf`) yield via
`async/await` on `AcadSynchronizationContext` so the UI stays
responsive.

### 3.3 Transport

| Aspect | Choice |
|---|---|
| Protocol | JSON-RPC 2.0 |
| Wire format | UTF-8 JSON, **line-delimited** (one request per `\n`) |
| Transport | TCP on `127.0.0.1` (loopback only) |
| Default port | `7878` |
| Port discovery | Plugin writes its actual port to `%APPDATA%\TechniCadBridge\port` after binding (handles port-in-use fallback) |
| Authentication | None in v1 (loopback-only). Token-based auth deferred to v2 |
| Encryption | None in v1 (loopback-only) |
| Concurrency | Multiple clients OK; commands from all clients funnel through the same `CommandQueue` |
| Max message size | 16 MB (covers FBX/PNG round-trips for hi-res renders) |
| Keepalive | TCP KEEPALIVE on; idle session timeout 1 hour |

**Rationale for line-delimited JSON over Content-Length-framed JSON-RPC:**
LSP-style framing is overkill for this; line-delimited is debuggable
with `nc` and lets us use `StreamJsonRpc.HeaderDelimitedMessageHandler`
or `NewLineDelimitedMessageHandler` directly.

---

## 4. Wire protocol — JSON-RPC 2.0 contract

### 4.1 Request

```json
{
  "jsonrpc": "2.0",
  "id": 17,
  "method": "Geometry.AddBox",
  "params": {
    "corner1": [0, 0, 0],
    "corner2": [10, 5, 8],
    "layer": "I-CASE"
  }
}
```

`id`: client-chosen, can be number or string. Notifications (no `id`)
are accepted but the plugin acts on them and never replies — used for
`Document.Cancel`-style fire-and-forget.

`method`: `Handler.Method` form, case-sensitive. Unknown methods return
JSON-RPC error code `-32601` (Method not found).

`params`: always an object (not positional). Missing required fields
return `-32602` (Invalid params).

### 4.2 Response (success)

```json
{
  "jsonrpc": "2.0",
  "id": 17,
  "result": {
    "handle": "2BC",
    "objectName": "AcDb3dSolid",
    "layer": "I-CASE",
    "boundingBox": { "min": [0,0,0], "max": [10,5,8] },
    "center": [5, 2.5, 4],
    "size": [10, 5, 8]
  }
}
```

### 4.3 Response (error)

```json
{
  "jsonrpc": "2.0",
  "id": 17,
  "error": {
    "code": -32001,
    "message": "Layer not found",
    "data": {
      "layer": "I-CASE-XYZ",
      "availableLayers": ["0", "A-WALL", "I-CASE", ...]
    }
  }
}
```

Error code conventions in § 6.

### 4.4 Batch requests

Supported per JSON-RPC 2.0 spec. Plugin processes each request in
order on the same `CommandQueue` enqueue, returns a JSON array of
responses. Useful for "create 4 layers + 16 boxes" in one round trip.

### 4.5 Cancellation

Long-running ops (`Render.ToFile`, `Plot.ToPdf`, `Boolean` over many
solids) accept an optional `_cancelToken` field in `params`. The
client can issue `Cancel.RequestById(id)` as a notification; the
plugin's `CancellationTokenSource` fires, the handler unwinds, and the
original request returns error code `-32004` (Cancelled).

---

## 5. Method catalog (84 methods, 11 handlers)

Conventions:

- Points are 3-element arrays of doubles in **inches** (matches
  AutoCAD's INSUNITS=1).
- Handles are AutoCAD ObjectId hex strings, e.g. `"2BC"`. Returned by
  every creation method.
- Colors are AutoCAD Color Index integers (`{aci: 40}`) or RGB
  (`{rgb: [216, 184, 138]}`).
- All boolean params default to `false` if omitted.
- Timestamps are ISO-8601 strings (`"2026-04-27T14:32:11Z"`).

### 5.1 Document handler (7 methods)

| Method | Params | Returns | Notes |
|---|---|---|---|
| `Document.Status` | — | `{name, path, saved, layerCount, entityCount, activeLayer, activeView}` | Replaces `acad_status` |
| `Document.New` | `{template?: string}` | `{name, path}` | If `template` omitted, uses AutoCAD's default; never opens dialog |
| `Document.Open` | `{path: string}` | `{name, path}` | |
| `Document.Save` | `{path?: string}` | `{name, path, saved}` | `path` triggers SaveAs; without it, plain Save |
| `Document.SaveAs` | `{path: string, format: "dwg"\|"dxf"\|"dxb", version?: string}` | `{name, path}` | `version` like `"AutoCAD 2018"`; defaults to current |
| `Document.Close` | `{save?: boolean}` | `{}` | `save: true` saves first; `false` discards changes |
| `Document.Cancel` | — | `{}` | Aborts current command-line input; safe to call any time |

### 5.2 Layer handler (5 methods)

| Method | Params | Returns | Notes |
|---|---|---|---|
| `Layer.List` | — | `[{name, color, frozen, locked, on, material, lineweight}]` | |
| `Layer.Create` | `{name, color?: aci\|rgb, material?: string, lineweight?: number}` | `{name, created: bool}` | `created: false` if existed; updates color if provided |
| `Layer.SetActive` | `{name}` | `{activeLayer}` | |
| `Layer.Freeze` | `{name, freeze: bool}` | `{name, frozen}` | Cannot freeze active layer (returns `-32011`) |
| `Layer.Delete` | `{name}` | `{deleted}` | Fails if layer has entities (returns `-32012`) |

### 5.3 Geometry handler (18 methods)

#### 5.3.1 Primitives

| Method | Params | Returns |
|---|---|---|
| `Geometry.AddBox` | `{corner1: pt3, corner2: pt3, layer?, color?}` | `{handle, ...}` |
| `Geometry.AddCylinder` | `{base: pt3, radius, height, layer?, color?}` | `{handle}` |
| `Geometry.AddSphere` | `{center: pt3, radius, layer?, color?}` | `{handle}` |
| `Geometry.AddCone` | `{base: pt3, baseRadius, topRadius?, height, layer?, color?}` | `{handle}` |
| `Geometry.AddTorus` | `{center: pt3, majorRadius, minorRadius, layer?}` | `{handle}` |
| `Geometry.AddWedge` | `{corner1: pt3, corner2: pt3, layer?}` | `{handle}` |

#### 5.3.2 2D entities

| Method | Params | Returns |
|---|---|---|
| `Geometry.AddLine` | `{start: pt3, end: pt3, layer?}` | `{handle}` |
| `Geometry.AddPolyline` | `{points: pt2[]\|pt3[], closed?: bool, layer?, elevation?}` | `{handle}` |
| `Geometry.AddPolyline3D` | `{points: pt3[], closed?, layer?}` | `{handle}` |
| `Geometry.AddCircle` | `{center: pt3, radius, layer?}` | `{handle}` |
| `Geometry.AddArc` | `{center: pt3, radius, startAngle: rad, endAngle: rad, layer?}` | `{handle}` |
| `Geometry.AddEllipse` | `{center: pt3, majorAxis: pt3, ratio, layer?}` | `{handle}` |
| `Geometry.AddRectangle` | `{lowerLeft: pt2, upperRight: pt2, layer?}` | `{handle}` |
| `Geometry.AddText` | `{insertion: pt3, text, height, rotation?, layer?, style?}` | `{handle}` |
| `Geometry.AddMText` | `{insertion: pt3, width, text, layer?}` | `{handle}` |

#### 5.3.3 3D operations (CSG and lofting)

| Method | Params | Returns | Notes |
|---|---|---|---|
| `Geometry.Boolean` | `{op: "union"\|"subtract"\|"intersect", sourceHandles: string[], otherHandles: string[]}` | `{handle, op, remaining}` | First-source receives the result; `other` are consumed |
| `Geometry.Loft` | `{sectionHandles: string[], guideHandles?: string[], pathHandle?: string, options?: LoftOptions}` | `{handle}` | Replaces LISP `(command "_.LOFT" ...)` from session 04-25 |
| `Geometry.Revolve` | `{profileHandle, axisStart: pt3, axisEnd: pt3, angleRadians?: number=2π}` | `{handle}` | |
| `Geometry.Sweep` | `{profileHandle, pathHandle, options?: SweepOptions}` | `{handle}` | |
| `Geometry.Extrude` | `{profileHandle, height, taperAngle?: rad}` | `{handle}` | |
| `Geometry.Fillet` | `{entityHandle, radius, edgeIndices?: int[]}` | `{handle}` | If `edgeIndices` omitted, fillets all edges |
| `Geometry.Chamfer` | `{entityHandle, distance1, distance2?: number, edgeIndices?: int[]}` | `{handle}` | |
| `Geometry.PressPull` | `{entityHandle, faceIndex, distance}` | `{handle}` | Click-drag-equivalent — moves a face by `distance` along its normal |

### 5.4 Entity handler (10 methods)

| Method | Params | Returns | Notes |
|---|---|---|---|
| `Entity.Get` | `{handle}` | `{handle, type, layer, material, color, boundingBox, ...typeSpecific}` | Inspect single entity |
| `Entity.List` | `{layer?, type?, limit?: int=200, includeFrozen?: bool=false}` | `[{handle, type, layer}]` | Replaces `acad_list_entities` |
| `Entity.Delete` | `{handle}` | `{deleted: bool}` | |
| `Entity.SetColor` | `{handle, aci?: int, rgb?: int[]}` | `{}` | |
| `Entity.SetLayer` | `{handle, layer}` | `{}` | |
| `Entity.SetMaterial` | `{handle, material}` | `{}` | Material must already be in drawing |
| `Entity.GetBoundingBox` | `{handle}` | `{min, max}` | |
| `Entity.Move` | `{handle, displacement: pt3}` | `{}` | |
| `Entity.Rotate` | `{handle, basePoint: pt3, angleRadians, axisDirection?: pt3}` | `{}` | Default axis = Z |
| `Entity.Scale` | `{handle, basePoint: pt3, factor: number\|pt3}` | `{}` | Uniform if scalar; non-uniform if vec3 |

### 5.5 View handler (8 methods)

| Method | Params | Returns | Notes |
|---|---|---|---|
| `View.SetPreset` | `{preset: "TOP"\|"BOTTOM"\|"FRONT"\|"BACK"\|"LEFT"\|"RIGHT"\|"SWISO"\|"SEISO"\|"NEISO"\|"NWISO"}` | `{view}` | Replaces `acad_set_view` |
| `View.SetCustom` | `{location: pt3, target: pt3, up?: pt3, lens?: number=50}` | `{}` | Sets current viewport's view |
| `View.SaveCamera` | `{name, location, target, lens?}` | `{name}` | Stored in `Database.ViewTable`; restorable |
| `View.RestoreCamera` | `{name}` | `{name, location, target, lens}` | **Replaces broken `_-VIEW _R`** from session 04-27 |
| `View.ListCameras` | — | `[{name, location, target, lens}]` | |
| `View.DeleteCamera` | `{name}` | `{}` | |
| `View.ZoomExtents` | — | `{}` | Replaces `acad_zoom_extents` |
| `View.ZoomWindow` | `{c1: pt2, c2: pt2}` | `{}` | |

### 5.6 VisualStyle handler (3 methods)

| Method | Params | Returns |
|---|---|---|
| `VisualStyle.Set` | `{style: "2DWireframe"\|"Wireframe"\|"Hidden"\|"Conceptual"\|"Realistic"\|"Shaded"\|"ShadedWithEdges"\|"XRay"}` | `{visualStyle}` |
| `VisualStyle.SetVariable` | `{name: "VSEDGES"\|"VSSHADOWS"\|..., value}` | `{previous}` |
| `VisualStyle.GetVariable` | `{name}` | `{value}` |

### 5.7 Material handler (7 methods, the centerpiece)

| Method | Params | Returns | Notes |
|---|---|---|---|
| `Material.ListLibrary` | `{family?: string, search?: string}` | `[{name, family, displayName, thumbnailDataUri?}]` | Browses Autodesk Material Library; `family` ∈ `{"Wood","Stone","Metal","Paint","Fabric","Glass","Plastic","Ceramic"}` |
| `Material.ImportFromLibrary` | `{name: string, asLayerMaterial?: boolean=false}` | `{material, imported: bool, layers?: string[]}` | Imports if not present; optionally assigns to all matching-name layers |
| `Material.Create` | `{name, color?: rgb, roughness?, metallic?, ior?, transmission?, diffuseMap?: path, normalMap?: path, roughnessMap?: path}` | `{material}` | Custom PBR material; texture maps loaded from disk |
| `Material.AssignToLayer` | `{layer, material}` | `{}` | |
| `Material.AssignToEntity` | `{handle, material}` | `{}` | |
| `Material.List` | — | `[{name, layers: string[], entityCount: int}]` | What's in the drawing right now |
| `Material.Delete` | `{name}` | `{deleted}` | Fails if assigned to a layer/entity |

### 5.8 Light handler (6 methods)

| Method | Params | Returns | Notes |
|---|---|---|---|
| `Light.AddPoint` | `{position: pt3, intensity?: number=1500, color?: kelvin\|rgb, name?, falloff?: "inverse"\|"inverseSquared"}` | `{handle, name}` | |
| `Light.AddSpot` | `{position, target, intensity?, hotspot?: rad, falloff?: rad, color?, name?}` | `{handle, name}` | |
| `Light.AddDistant` | `{direction: pt3, intensity?, color?, name?}` | `{handle, name}` | |
| `Light.SetSun` | `{enabled: bool, latitude?, longitude?, date?: ISO8601, timezone?: number, intensity?: number=1.0}` | `{enabled, ...}` | **Replaces hung SUNSTATUS sysvar** |
| `Light.List` | — | `[{handle, name, type, position?, target?, intensity, color}]` | |
| `Light.Delete` | `{handle}` | `{}` | |

### 5.9 Render handler (3 methods)

| Method | Params | Returns | Notes |
|---|---|---|---|
| `Render.ListPresets` | — | `[{name, samples, lighting, description}]` | Built-in: `Draft, Low, Medium, High, Presentation` |
| `Render.ToFile` | `{preset?: string="Medium", view?: string\|preset, outputPath: string, width?: int=1920, height?: int=1080, exposure?: number=0}` | `{outputPath, durationMs}` | **The headless render** — no dialog, no manual save |
| `Render.SetDefaults` | `{preset?, lightingUnits?, defaultLighting?: bool=false}` | `{}` | |

### 5.10 Layout & plot handler (9 methods)

| Method | Params | Returns | Notes |
|---|---|---|---|
| `Layout.List` | — | `[{name, isCurrent, paperSize, plotter}]` | |
| `Layout.Create` | `{name, paperSize?: "ARCH-D"\|"ANSI-A"\|..., plotter?: "DWG To PDF.pc3"\|...}` | `{name}` | |
| `Layout.SetActive` | `{name}` | `{}` | |
| `Layout.Delete` | `{name}` | `{}` | |
| `Layout.AddViewport` | `{layout, center: pt2, width: number, height: number, viewName?, scale?: number}` | `{handle}` | Creates a paper-space viewport showing model space |
| `Layout.SetViewportView` | `{handle, viewName}` | `{}` | |
| `Layout.SetViewportScale` | `{handle, scale}` | `{}` | Scale in inches paper / inches model (e.g. `0.5/12.0` for 1/2"=1'-0") |
| `Layout.SetViewportLayerVisibility` | `{handle, layer, visible}` | `{}` | Per-viewport freeze |
| `Plot.ToPdf` | `{layout: string, outputPath: string, paperSize?: string}` | `{outputPath}` | Plots a layout to PDF without opening any dialog |

### 5.11 Export & import handler (9 methods)

| Method | Params | Returns | Notes |
|---|---|---|---|
| `Export.Fbx` | `{outputPath, options?: FbxExportOptions}` | `{outputPath, sizeBytes}` | Real FBX export, no dialog |
| `Export.Gltf` | `{outputPath, binary?: bool=true}` | `{outputPath}` | `.glb` if binary, `.gltf` if text |
| `Export.Stl` | `{outputPath, layers?: string[], selection?: handle[], binary?: bool=true}` | `{outputPath}` | If `layers` set, only those layers' geometry |
| `Export.Dxf` | `{outputPath, version?: string="ACAD2018", binary?: bool=false}` | `{outputPath}` | |
| `Export.Png` | `{outputPath, view?, width, height, visualStyle?: string="Conceptual", background?: rgb}` | `{outputPath}` | Quick non-render PNG of current viewport |
| `Export.LayerStls` | `{outputDir, layers?: string[]}` | `{files: [{layer, path, sizeBytes}]}` | One STL per layer (replaces `export_per_layer_stl.py`) |
| `Import.RasterImage` | `{path, position: pt3, scale?: number, rotation?: rad, layer?, transparent?: bool}` | `{handle}` | Replaces `IMAGEATTACH` dialog |
| `Import.Block` | `{blockPath: string, name: string}` | `{name, blockId}` | Inserts a block definition from another DWG |
| `Import.Xref` | `{path, name?, position?: pt3}` | `{handle}` | External reference attach |

### 5.12 Dimension handler (5 methods)

| Method | Params | Returns | Notes |
|---|---|---|---|
| `Dimension.AddLinear` | `{p1: pt3, p2: pt3, dimLineLocation: pt3, rotationRadians?: number=0, layer?}` | `{handle}` | |
| `Dimension.AddAligned` | `{p1, p2, dimLineLocation, layer?}` | `{handle}` | |
| `Dimension.AddRadius` | `{circleHandle, leaderEndPoint: pt3, layer?}` | `{handle}` | |
| `Dimension.AddAngular` | `{vertex: pt3, line1End: pt3, line2End: pt3, dimArcLocation: pt3, layer?}` | `{handle}` | |
| `Dimension.SetStyleVariable` | `{name: "DIMSCALE"\|"DIMTXT"\|..., value}` | `{previous}` | Replaces SetVariable for dim sysvars |

### 5.13 Var handler (3 methods)

| Method | Params | Returns |
|---|---|---|
| `Var.Get` | `{name}` | `{value}` |
| `Var.Set` | `{name, value}` | `{previous}` |
| `Var.SetMany` | `{vars: [{name, value}]}` | `{set: int}` (atomic — all or none) |

### 5.14 Cancel & introspection (3 methods)

| Method | Params | Returns |
|---|---|---|
| `Cancel.RequestById` | `{rpcId: int\|string}` | `{}` (notification) |
| `Server.Health` | — | `{ok, version, uptimeSeconds, queueDepth, autocadVersion, activeDocument}` |
| `Server.ListMethods` | — | `[{handler, method, paramSchema, returnSchema}]` (auto-generated) |

---

## 6. Error model

### 6.1 Error code ranges

| Range | Meaning |
|---|---|
| `-32700` | Parse error (malformed JSON) |
| `-32600` | Invalid Request (missing `jsonrpc`, `method`, etc.) |
| `-32601` | Method not found |
| `-32602` | Invalid params (missing required, wrong type) |
| `-32603` | Internal error (unhandled exception in handler) |
| `-32000` to `-32099` | **TechniCadBridge custom errors** (see 6.2) |

### 6.2 Custom error codes

| Code | Symbol | Meaning |
|---|---|---|
| `-32000` | `Timeout` | Command exceeded `config.timeouts.command_ms` |
| `-32001` | `LayerNotFound` | Named layer doesn't exist |
| `-32002` | `EntityNotFound` | Handle doesn't resolve to an entity in the active doc |
| `-32003` | `MaterialNotFound` | Named material not in drawing or library |
| `-32004` | `Cancelled` | Client issued `Cancel.RequestById` |
| `-32005` | `ModalDialogActive` | AutoCAD has a modal dialog open; plugin can't drive |
| `-32006` | `NoActiveDocument` | No drawing is open |
| `-32007` | `InvalidDocumentState` | Document is read-only / locked / mid-command |
| `-32008` | `RenderFailed` | Render preset doesn't exist or geometry too complex |
| `-32009` | `PlotFailed` | PDF plotter not configured / paper size invalid |
| `-32010` | `ExportFailed` | FBX/glTF/STL writer error |
| `-32011` | `LayerStateInvalid` | Trying to freeze the active layer, etc. |
| `-32012` | `ConstraintViolation` | Layer has entities, can't delete; etc. |
| `-32013` | `BatchPartialFailure` | A batch had some failures (returned with details) |
| `-32014` | `CapabilityUnavailable` | AutoCAD version doesn't support this method |
| `-32015` | `ConfigurationInvalid` | Plugin config file malformed |

### 6.3 Error payload shape

```json
{
  "code": -32001,
  "message": "Layer 'I-CASE-XYZ' not found in active drawing",
  "data": {
    "symbol": "LayerNotFound",
    "layer": "I-CASE-XYZ",
    "availableLayers": ["0", "A-WALL", "I-CASE", ...],
    "suggestion": "I-CASE",
    "method": "Material.AssignToLayer",
    "rpcId": 17
  }
}
```

The `data.suggestion` field uses Levenshtein distance to suggest the
nearest existing name when the user fat-fingers.

### 6.4 Modal-dialog detection

The plugin polls `Application.Idle`. If Idle hasn't fired for >2s while
a command is enqueued, the plugin assumes a modal dialog opened. It:

1. Returns `-32005 ModalDialogActive` to all queued clients
2. Tries `Application.PostQuit()` to dismiss (sometimes works)
3. Logs `[ALERT] modal dialog detected — manual intervention required`
   to the trace log
4. Resumes accepting new commands when Idle resumes

This solves the entire class of "AutoCAD froze and we have to manually
ESC" problems by making them **explicit failures** instead of silent
hangs.

### 6.5 Exception-to-error mapping

| .NET exception | Error code |
|---|---|
| `Autodesk.AutoCAD.Runtime.Exception` (eLayerNotFound) | `-32001` |
| `Autodesk.AutoCAD.Runtime.Exception` (eHandleInUse, eWasErased) | `-32002` |
| `OperationCanceledException` | `-32004` |
| `TimeoutException` | `-32000` |
| `System.IO.IOException` (export/render) | `-32010` |
| `JsonException` | `-32700` |
| Any other | `-32603` (with stack trace in `data.stackTrace` if `config.debug.includeStackTrace = true`) |

---

## 7. Configuration (`config.json`)

Location: `%APPDATA%\TechniCadBridge\config.json` (rolls forward across
plugin upgrades).

```json
{
  "schema": "1.0",
  "server": {
    "host": "127.0.0.1",
    "port": 7878,
    "portFallbackRange": [7878, 7888],
    "maxClients": 4,
    "maxMessageBytes": 16777216
  },
  "timeouts": {
    "commandMs": 30000,
    "renderMs": 600000,
    "plotMs": 120000,
    "exportMs": 300000,
    "modalDetectMs": 2000
  },
  "logging": {
    "level": "info",
    "consoleEcho": true,
    "fileLog": true,
    "fileLogPath": "%APPDATA%\\TechniCadBridge\\plugin.log",
    "rotateDays": 7
  },
  "telemetry": {
    "enabled": false,
    "tracePath": "%APPDATA%\\TechniCadBridge\\trace.jsonl",
    "rotateDays": 30
  },
  "render": {
    "defaultPreset": "Medium",
    "defaultExposure": 0.0,
    "lightingUnits": 2
  },
  "debug": {
    "includeStackTrace": false,
    "logEveryRpc": false
  }
}
```

### 7.1 Config validation

On plugin load, the config file is validated against
`config.schema.json` (JSON Schema 2020-12). Validation failures:

- Log the error to AutoCAD's command line + plugin log
- Fall back to default values for invalid fields
- Plugin still loads (degrades gracefully)

### 7.2 Hot reload

`SIGHUP` equivalent: client can call `Server.ReloadConfig` (admin
method, gated behind `config.debug.allowReload = true`). Re-reads the
file and applies changes. Port changes require a plugin restart.

---

## 8. Logging & telemetry

### 8.1 Plugin log (always on)

`%APPDATA%\TechniCadBridge\plugin.log` — text log, ASCII, one line per
event. Levels: `trace`, `debug`, `info`, `warn`, `error`. Default `info`.

```
2026-04-27T14:30:11.123Z [info ] startup — version=1.0.0 acadVersion=26.0.0 port=7878
2026-04-27T14:30:11.150Z [info ] config loaded from %APPDATA%\TechniCadBridge\config.json
2026-04-27T14:32:11.450Z [debug] rpc 17 Geometry.AddBox layer=I-CASE
2026-04-27T14:32:11.481Z [debug] rpc 17 OK 31ms handle=2BC
2026-04-27T14:32:14.123Z [warn ] rpc 18 timeout 30001ms method=Render.ToFile
2026-04-27T14:32:14.124Z [error] rpc 18 -32000 Timeout
```

### 8.2 Telemetry (opt-in via `config.telemetry.enabled = true`)

`%APPDATA%\TechniCadBridge\trace.jsonl` — one JSON object per line,
suitable for `jq` analysis:

```json
{"ts":"2026-04-27T14:32:11.481Z","rpcId":17,"method":"Geometry.AddBox","latencyMs":31,"ok":true,"queueWaitMs":2}
{"ts":"2026-04-27T14:32:14.124Z","rpcId":18,"method":"Render.ToFile","latencyMs":30001,"ok":false,"errorCode":-32000,"queueWaitMs":0}
```

Rotates daily (file named `trace-YYYY-MM-DD.jsonl`); keeps last
`config.telemetry.rotateDays = 30` files.

**Never sent off the machine.** No external telemetry endpoint. If you
want to share a session for debugging, manually copy the file.

### 8.3 Sample queries

```bash
# Slowest 20 commands today
cat trace-2026-04-27.jsonl | jq -s 'sort_by(-.latencyMs) | .[0:20]'

# Error rate per method
cat trace-*.jsonl | jq -s 'group_by(.method) | map({method: .[0].method, total: length, errors: map(select(.ok == false)) | length})'

# All -32005 (modal dialog) events
cat trace-*.jsonl | jq 'select(.errorCode == -32005)'
```

---

## 9. Security

### 9.1 Threat model

The plugin is loopback-only on a single-user developer machine. Threats
considered:

| Threat | Severity | Mitigation |
|---|---|---|
| Other process on the same machine connects to TCP 7878 and runs commands | Medium | Bind explicitly to `127.0.0.1`; reject non-loopback connections; in v2 add a token |
| Malicious DWG opens, JS in the DWG (yes, that's a thing in some CAD systems) calls back to plugin | Low | DWG files don't contain executable code in AutoCAD; this isn't a plausible attack |
| Path traversal in `outputPath` parameter (e.g. `C:\Windows\System32\foo.dll`) | Medium | Validate paths against an allow-list root; default root is the active project's `out/` folder |
| RCE via crafted JSON-RPC payload | Medium | StreamJsonRpc validates JSON; we never `eval`; method names are dispatched through a registry not reflection |
| Plugin DLL replaced with a malicious version | Low | Standard Windows file-permission model; rely on user's machine integrity |
| Network exfiltration via plugin HTTP calls | Low | Plugin only opens TCP listener; never makes outbound connections |

### 9.2 Path validation

All `outputPath`, `path`, `template` parameters are passed through:

```csharp
PathValidator.Validate(path, allowedRoots: new[] {
    Environment.GetFolderPath(Environment.SpecialFolder.UserProfile),
    Path.GetDirectoryName(activeDocument.Path),
    config.allowedExportRoots
});
```

Rejected: `C:\Windows`, `C:\Program Files`, `C:\Users\*\AppData` (other
than the plugin's own).

### 9.3 v2 security additions (deferred)

- Per-client auth tokens stored in `%APPDATA%\TechniCadBridge\token`
- mTLS over the TCP socket
- Per-method ACL (e.g. `Document.Close` requires admin token)

---

## 10. Versioning & API stability

### 10.1 Semantic versioning

`MAJOR.MINOR.PATCH`:

- **MAJOR** bump = breaking API change (method removal, parameter
  rename, return-shape change)
- **MINOR** bump = additive (new method, new optional parameter, new
  error code)
- **PATCH** bump = bug fix only

### 10.2 Compatibility envelope

Plugin advertises its version via `Server.Health`. Python client checks
on connect:

```python
health = client.call("Server.Health")
if health["version"] < "1.0.0":
    raise IncompatibleVersion(...)
```

### 10.3 Method deprecation

Removing a method requires:

1. Mark deprecated in `Server.ListMethods` response (add `deprecated:
   true`, `replacedBy: "..."`)
2. Log a `warn` line on every call to a deprecated method
3. Wait one MINOR release before removal
4. Announce in `CHANGELOG.md`

---

## 11. Project layout

### 11.1 .NET solution (`technijian-cad-bridge` repo)

```
technijian-cad-bridge/
├── README.md
├── CHANGELOG.md
├── LICENSE                                      (placeholder; private until v1.1)
├── TechniCadBridge.sln
├── Directory.Build.props                        (sets AcadInstallDir, common props)
├── src/
│   └── TechniCadBridge/
│       ├── TechniCadBridge.csproj
│       ├── PluginEntry.cs                       (IExtensionApplication)
│       ├── Server/
│       │   ├── JsonRpcServer.cs
│       │   ├── ClientSession.cs
│       │   ├── CommandQueue.cs
│       │   ├── AcadSyncContext.cs
│       │   ├── HandlerRegistry.cs
│       │   └── Protocol/
│       │       ├── JsonRpcRequest.cs
│       │       ├── JsonRpcResponse.cs
│       │       └── JsonRpcError.cs
│       ├── Handlers/
│       │   ├── DocumentHandler.cs
│       │   ├── LayerHandler.cs
│       │   ├── GeometryHandler.cs
│       │   ├── EntityHandler.cs
│       │   ├── ViewHandler.cs
│       │   ├── VisualStyleHandler.cs
│       │   ├── MaterialHandler.cs
│       │   ├── LightHandler.cs
│       │   ├── RenderHandler.cs
│       │   ├── LayoutHandler.cs
│       │   ├── ExportHandler.cs
│       │   ├── ImportHandler.cs
│       │   ├── DimensionHandler.cs
│       │   ├── VarHandler.cs
│       │   └── ServerHandler.cs
│       ├── Util/
│       │   ├── PathValidator.cs
│       │   ├── HandleResolver.cs
│       │   ├── PointConv.cs
│       │   ├── ColorConv.cs
│       │   └── Logger.cs
│       └── Config/
│           ├── PluginConfig.cs
│           ├── ConfigLoader.cs
│           └── config.schema.json
├── tests/
│   ├── TechniCadBridge.Tests/
│   │   ├── TechniCadBridge.Tests.csproj
│   │   ├── Server/
│   │   │   ├── JsonRpcServerTests.cs
│   │   │   ├── CommandQueueTests.cs
│   │   │   └── HandlerRegistryTests.cs
│   │   └── Handlers/
│   │       ├── LayerHandlerTests.cs
│   │       ├── GeometryHandlerTests.cs
│   │       └── ...
│   └── TechniCadBridge.Integration/
│       ├── TechniCadBridge.Integration.csproj  (exercises real AutoCAD)
│       ├── KitchenScenarioTest.cs
│       ├── LivingRoomScenarioTest.cs
│       └── HomeOfficeScenarioTest.cs
├── packaging/
│   ├── install.ps1
│   ├── uninstall.ps1
│   ├── config.template.json
│   └── README.md
├── scripts/
│   ├── build.ps1
│   ├── test.ps1
│   ├── publish.ps1
│   └── gen-protocol-md.ps1                     (regenerates docs/PROTOCOL.md from XML doc comments)
├── docs/
│   ├── PROTOCOL.md                              (auto-generated; never hand-edit)
│   ├── DEVELOPER.md
│   ├── RUNBOOK.md
│   ├── ARCHITECTURE.md
│   └── CHANGELOG.md
└── .github/workflows/
    └── ci.yml                                  (build + unit test on every push)
```

### 11.2 Python facade (lives in `-callie-job/autocad-mcp/`)

```
autocad-mcp/
├── plugin_client.py                             (NEW — JSON-RPC 2.0 client)
├── plugin_models.py                             (NEW — typed dataclasses for params/returns)
├── acad.py                                      (refactored — plugin-first, COM-fallback)
├── server.py                                    (existing — FastMCP, no changes)
├── ...                                          (existing build_*.py, finish_*.py scripts unchanged)
```

### 11.3 Repo split

| What | Where |
|---|---|
| Plugin C# code, tests, packaging | `github.com/rjain557/technijian-cad-bridge` (private) |
| Python facade, MCP tools, project scripts | `github.com/rjain557/-callie-job` (existing) |
| Spec documents (this file, PROTOCOL.md generated copy) | Both repos — primary in plugin repo, copy in `-callie-job/autocad-mcp/` for reference |

---

## 12. Lifecycle

### 12.1 Plugin startup

1. AutoCAD launches; reads registry auto-load key
2. Loads `TechniCadBridge.dll` via `NETLOAD`
3. `IExtensionApplication.Initialize()` runs:
   - Load config from `%APPDATA%\TechniCadBridge\config.json`
   - Construct `Logger` (file + console)
   - Construct `JsonRpcServer`, bind to TCP port (with fallback range)
   - Construct `CommandQueue`, register `Application.Idle` handler
   - Build `HandlerRegistry` via reflection over `Handlers/` types
   - Begin `AcceptLoop` on background thread
4. Log `[info] startup — version=1.0.0 port=7878` to plugin log
5. Editor.WriteMessage shows `[TechniCadBridge] listening on 127.0.0.1:7878`
6. Write actual port to `%APPDATA%\TechniCadBridge\port` (for client discovery)

### 12.2 Per-request flow

1. Client opens TCP connection (or reuses existing)
2. Sends JSON-RPC request line
3. `ClientSession.ReadLoop` parses, validates JSON-RPC, resolves handler
4. Wraps handler in `CommandQueueItem(taskCompletionSource, methodAttrs)`
5. Enqueues; `taskCompletionSource.Task` is awaited on the listener thread
6. `Application.Idle` fires on main thread → drain one item → run it
7. Handler executes (transactionally — opens a `Transaction` if it
   touches the database)
8. `Result` or `Exception` → `tcs.SetResult / SetException`
9. Listener thread resumes, serializes response, writes to TCP

### 12.3 Plugin shutdown

`IExtensionApplication.Terminate()` runs when AutoCAD exits or plugin
is unloaded:

1. Stop accepting new connections
2. Send shutdown message to all open sessions
3. Drain `CommandQueue` with 5 s timeout
4. Close TCP listener
5. Flush plugin log

### 12.4 Client disconnect

Per-session cleanup:

- Cancel any in-flight requests for this session via `CancellationToken`
- Close socket
- Free session resources
- Log disconnect at `info` level

### 12.5 Hot reload (development only)

`Server.ReloadAssembly` admin command (gated by
`config.debug.allowReload = true`):

- Triggers a soft restart of the JsonRpcServer
- New JIT compiles, new handlers
- Existing connections drop; clients reconnect

NOT recommended for production use; restart AutoCAD instead.

---

## 13. Code examples — the hard parts

### 13.1 `PluginEntry.cs`

```csharp
using Autodesk.AutoCAD.Runtime;
using Autodesk.AutoCAD.ApplicationServices;
using TechniCadBridge.Server;
using TechniCadBridge.Config;

[assembly: ExtensionApplication(typeof(TechniCadBridge.PluginEntry))]
[assembly: CommandClass(typeof(TechniCadBridge.PluginEntry))]

namespace TechniCadBridge;

public class PluginEntry : IExtensionApplication
{
    private JsonRpcServer? _server;

    public void Initialize()
    {
        try
        {
            var config = ConfigLoader.LoadOrDefault();
            Logger.Initialize(config.Logging);
            Logger.Info($"startup — version={Versions.Plugin} acadVersion={Application.Version}");

            _server = new JsonRpcServer(config);
            _server.Start();

            Editor.WriteMessage(
                $"\n[TechniCadBridge] listening on tcp://{config.Server.Host}:{_server.ActualPort}\n");
        }
        catch (Exception ex)
        {
            Logger.Error($"startup failed: {ex}");
            Editor.WriteMessage($"\n[TechniCadBridge] FAILED to start: {ex.Message}\n");
        }
    }

    public void Terminate()
    {
        Logger.Info("shutdown begin");
        _server?.StopGracefully(TimeSpan.FromSeconds(5));
        Logger.Info("shutdown complete");
        Logger.Shutdown();
    }

    [CommandMethod("TCBRESTART")]
    public static void RestartPluginCommand()
    {
        // Manual restart entry point usable from AutoCAD command line
        // for diagnostics during development.
    }
}
```

### 13.2 `CommandQueue.cs` (the core threading primitive)

```csharp
using System.Collections.Concurrent;
using Autodesk.AutoCAD.ApplicationServices;

namespace TechniCadBridge.Server;

public sealed class CommandQueue
{
    private readonly BlockingCollection<QueueItem> _queue = new(boundedCapacity: 1024);
    private DateTime _lastIdle = DateTime.UtcNow;

    public CommandQueue()
    {
        Application.Idle += OnIdle;
    }

    /// <summary>Enqueue a handler invocation, returning a task that
    /// completes when the handler runs on the AutoCAD main thread.</summary>
    public Task<TResult> EnqueueAsync<TResult>(Func<TResult> work, CancellationToken ct)
    {
        var tcs = new TaskCompletionSource<TResult>(
            TaskCreationOptions.RunContinuationsAsynchronously);
        var item = new QueueItem(() =>
        {
            if (ct.IsCancellationRequested)
            {
                tcs.SetCanceled(ct);
                return;
            }
            try { tcs.SetResult(work()); }
            catch (Exception ex) { tcs.SetException(ex); }
        });
        if (!_queue.TryAdd(item, millisecondsTimeout: 100))
            tcs.SetException(new InvalidOperationException("queue full"));
        return tcs.Task;
    }

    private void OnIdle(object? _, EventArgs __)
    {
        _lastIdle = DateTime.UtcNow;
        // Process at most one item per Idle to keep AutoCAD responsive.
        if (_queue.TryTake(out var item))
        {
            try { item.Run(); }
            catch (Exception ex) { Logger.Error($"queue item threw: {ex}"); }
        }
    }

    public DateTime LastIdleAt => _lastIdle;
    public int Depth => _queue.Count;

    private sealed record QueueItem(Action Run);
}
```

### 13.3 Sample handler — `LayerHandler.cs`

```csharp
using Autodesk.AutoCAD.DatabaseServices;
using Autodesk.AutoCAD.ApplicationServices;

namespace TechniCadBridge.Handlers;

public sealed class LayerHandler
{
    [RpcMethod("Layer.List")]
    public List<LayerInfo> List()
    {
        var doc = Application.DocumentManager.MdiActiveDocument
            ?? throw new RpcException(Errors.NoActiveDocument);
        using var tr = doc.Database.TransactionManager.StartTransaction();
        var lt = (LayerTable)tr.GetObject(doc.Database.LayerTableId, OpenMode.ForRead);
        var result = new List<LayerInfo>();
        foreach (ObjectId id in lt)
        {
            var layer = (LayerTableRecord)tr.GetObject(id, OpenMode.ForRead);
            result.Add(new LayerInfo
            {
                Name = layer.Name,
                Color = layer.Color.ColorIndex,
                Frozen = layer.IsFrozen,
                Locked = layer.IsLocked,
                On = !layer.IsOff,
                Material = layer.MaterialId == ObjectId.Null
                    ? null
                    : ((Material)tr.GetObject(layer.MaterialId, OpenMode.ForRead)).Name,
                Lineweight = (int)layer.LineWeight,
            });
        }
        tr.Commit();
        return result;
    }

    [RpcMethod("Layer.Create")]
    public LayerCreateResult Create(string name, int? color = null, string? material = null)
    {
        var doc = Application.DocumentManager.MdiActiveDocument
            ?? throw new RpcException(Errors.NoActiveDocument);
        using var docLock = doc.LockDocument();
        using var tr = doc.Database.TransactionManager.StartTransaction();
        var lt = (LayerTable)tr.GetObject(doc.Database.LayerTableId, OpenMode.ForWrite);

        bool created = false;
        LayerTableRecord layer;
        if (lt.Has(name))
        {
            layer = (LayerTableRecord)tr.GetObject(lt[name], OpenMode.ForWrite);
        }
        else
        {
            layer = new LayerTableRecord { Name = name };
            lt.Add(layer);
            tr.AddNewlyCreatedDBObject(layer, true);
            created = true;
        }
        if (color.HasValue)
            layer.Color = Autodesk.AutoCAD.Colors.Color.FromColorIndex(
                Autodesk.AutoCAD.Colors.ColorMethod.ByAci, (short)color.Value);
        if (material is not null)
        {
            // ... look up Material by name in MaterialDictionary, set MaterialId
        }
        tr.Commit();
        return new LayerCreateResult { Name = name, Created = created };
    }

    [RpcMethod("Layer.Freeze")]
    public LayerFreezeResult Freeze(string name, bool freeze)
    {
        var doc = Application.DocumentManager.MdiActiveDocument
            ?? throw new RpcException(Errors.NoActiveDocument);
        using var docLock = doc.LockDocument();
        using var tr = doc.Database.TransactionManager.StartTransaction();
        var lt = (LayerTable)tr.GetObject(doc.Database.LayerTableId, OpenMode.ForRead);
        if (!lt.Has(name))
            throw new RpcException(Errors.LayerNotFound, new { layer = name });
        var layer = (LayerTableRecord)tr.GetObject(lt[name], OpenMode.ForWrite);

        if (freeze && doc.Database.Clayer == layer.ObjectId)
            throw new RpcException(Errors.LayerStateInvalid,
                new { reason = "cannot freeze active layer", layer = name });
        layer.IsFrozen = freeze;
        tr.Commit();
        return new LayerFreezeResult { Name = name, Frozen = freeze };
    }
}
```

### 13.4 Python client (`plugin_client.py`)

```python
"""JSON-RPC 2.0 client for TechniCadBridge."""
import json
import os
import socket
import threading
from dataclasses import dataclass


class PluginError(Exception):
    def __init__(self, code, message, data=None):
        super().__init__(f"[{code}] {message}")
        self.code = code; self.message = message; self.data = data or {}


class PluginUnavailable(Exception): pass


@dataclass
class _PluginConnection:
    sock: socket.socket
    file: object  # socket.makefile('r')
    lock: threading.Lock


class PluginClient:
    """Thread-safe JSON-RPC client. One TCP connection per process,
    serialized via lock."""

    def __init__(self, host="127.0.0.1", port=None, timeout=30.0):
        if port is None:
            port_file = os.path.expandvars(r"%APPDATA%\TechniCadBridge\port")
            port = int(open(port_file).read().strip()) if os.path.exists(port_file) else 7878
        try:
            sock = socket.create_connection((host, port), timeout=timeout)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        except (ConnectionRefusedError, socket.timeout) as e:
            raise PluginUnavailable(f"could not connect to {host}:{port}: {e}")
        self._conn = _PluginConnection(
            sock=sock, file=sock.makefile('r', encoding='utf-8'), lock=threading.Lock())
        self._next_id = 0

    def call(self, method: str, **params):
        with self._conn.lock:
            self._next_id += 1
            req = {"jsonrpc": "2.0", "id": self._next_id,
                   "method": method, "params": params}
            self._conn.sock.sendall((json.dumps(req) + "\n").encode("utf-8"))
            line = self._conn.file.readline()
        if not line:
            raise PluginUnavailable("plugin closed connection")
        resp = json.loads(line)
        if "error" in resp:
            err = resp["error"]
            raise PluginError(err["code"], err["message"], err.get("data"))
        return resp["result"]

    def health(self):
        return self.call("Server.Health")

    def close(self):
        try: self._conn.sock.close()
        except Exception: pass
```

### 13.5 `acad.py` facade (excerpt)

```python
class Acad:
    def __init__(self):
        self._app = None
        try:
            self._plugin = PluginClient()
            self._plugin.health()  # smoke test
            print("[acad] using TechniCadBridge plugin")
        except (PluginUnavailable, OSError):
            self._plugin = None
            print("[acad] plugin unavailable; falling back to COM")

    def add_box(self, c1, c2):
        if self._plugin:
            return self._plugin.call("Geometry.AddBox", corner1=list(c1), corner2=list(c2))
        # COM fallback (existing implementation)
        return self._add_box_com(c1, c2)
```

---

## 14. Build, install, uninstall

### 14.1 Build

Prerequisites:

- Windows 10/11 x64
- AutoCAD 2027 installed (or AutoCAD 2026; set `AcadInstallDir`)
- .NET 8 SDK
- Visual Studio 2022 Community OR `dotnet` CLI

Steps:

```powershell
# Set AcadInstallDir if AutoCAD isn't in default location
$env:AcadInstallDir = 'C:\Program Files\Autodesk\AutoCAD 2027'

cd technijian-cad-bridge
.\scripts\build.ps1
# Outputs: src\TechniCadBridge\bin\Release\net8.0-windows\TechniCadBridge.dll
```

### 14.2 Install

```powershell
.\packaging\install.ps1
# - Creates %APPDATA%\TechniCadBridge\
# - Copies TechniCadBridge.dll to %APPDATA%\TechniCadBridge\bin\
# - Copies config.template.json to %APPDATA%\TechniCadBridge\config.json (if absent)
# - Writes registry HKCU\...\R26.0\...\Applications\TechniCadBridge\LOADER + LOADCTRLS=2
# - Confirms successful install
```

Manual NETLOAD (if registry path is blocked):

```
NETLOAD %APPDATA%\TechniCadBridge\bin\TechniCadBridge.dll
```

### 14.3 Uninstall

```powershell
.\packaging\uninstall.ps1
# - Removes registry entry
# - Deletes DLL
# - Optionally preserves %APPDATA%\TechniCadBridge\config.json (--keep-config)
# - Optionally preserves logs (--keep-logs)
```

### 14.4 Verify install

```powershell
# After AutoCAD restart:
Test-NetConnection 127.0.0.1 -Port 7878
# Expected: TcpTestSucceeded : True

# Send a manual request
$json = '{"jsonrpc":"2.0","id":1,"method":"Server.Health"}'
$client = New-Object System.Net.Sockets.TcpClient('127.0.0.1', 7878)
$stream = $client.GetStream()
$writer = New-Object System.IO.StreamWriter $stream
$reader = New-Object System.IO.StreamReader $stream
$writer.WriteLine($json); $writer.Flush()
$reader.ReadLine()
# Expected: {"jsonrpc":"2.0","id":1,"result":{"ok":true,"version":"1.0.0",...}}
```

---

## 15. Testing strategy & CI

### 15.1 Test pyramid

| Layer | What | Where | When |
|---|---|---|---|
| Unit | Handler logic with mocked AutoCAD types | `TechniCadBridge.Tests` | Every commit (CI) |
| Integration | Real AutoCAD instance, scripted scenarios | `TechniCadBridge.Integration` | Pre-merge to main |
| End-to-end | Re-run all 5 project scripts, diff outputs | `-callie-job/tests/` | Manual, weekly |
| Smoke | `Server.Health` after install | `packaging/verify-install.ps1` | Every install |

### 15.2 Unit tests — strategy

AutoCAD's managed API is hard to mock because most types have private
constructors. Strategy:

- Wrap AutoCAD types in our own thin interfaces (e.g. `IDocumentService`,
  `ILayerService`)
- Handlers depend on interfaces, not concrete types
- Tests mock the interfaces with NSubstitute or hand-rolled fakes
- Concrete implementations live in `Services/` and are exercised via
  Integration tests only

Example:

```csharp
public class LayerHandlerTests
{
    [Fact]
    public async Task Freeze_ActiveLayer_ReturnsLayerStateInvalid()
    {
        var docSvc = Substitute.For<IDocumentService>();
        docSvc.ActiveLayerName.Returns("I-CASE");
        var layerSvc = Substitute.For<ILayerService>();
        layerSvc.Exists("I-CASE").Returns(true);

        var sut = new LayerHandler(docSvc, layerSvc);
        var ex = await Assert.ThrowsAsync<RpcException>(
            () => sut.FreezeAsync("I-CASE", freeze: true));

        Assert.Equal(Errors.LayerStateInvalid, ex.Code);
    }
}
```

### 15.3 Integration tests

Require a real AutoCAD running. Test runner uses
`Autodesk.AutoCAD.Interop.AcadApplication` to spawn AutoCAD,
NETLOAD the just-built plugin, run scripted scenarios, assert
artifacts exist.

```csharp
[Fact]
public async Task KitchenScenario_BuildsAllArtifacts()
{
    using var fixture = new AcadFixture("kitchen");
    fixture.NetLoadPlugin();

    var client = fixture.PluginClient;
    await client.Call("Document.New");
    await BuildKitchenShell(client);
    await BuildKitchenCabinets(client);
    var renderResult = await client.Call("Render.ToFile", new {
        outputPath = fixture.OutPath("render.png"),
        preset = "Medium",
        view = "NEISO",
    });

    Assert.True(File.Exists(renderResult["outputPath"]));
    Assert.True(new FileInfo(renderResult["outputPath"]).Length > 50_000);
}
```

### 15.4 CI

`.github/workflows/ci.yml`:

```yaml
name: CI
on: [push, pull_request]
jobs:
  build-and-test:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-dotnet@v4
        with: { dotnet-version: '8.0.x' }
      - run: dotnet restore
      - run: dotnet build -c Release --no-restore
      - run: dotnet test -c Release --no-build --filter Category!=Integration
      - uses: actions/upload-artifact@v4
        with: { name: TechniCadBridge.dll, path: src/TechniCadBridge/bin/Release/**/TechniCadBridge.dll }
```

Integration tests run on a self-hosted runner with AutoCAD installed
(future Phase 4 work; not part of GitHub-hosted runners).

### 15.5 Coverage targets

- Unit: ≥ 80% line coverage on handlers, ≥ 60% on `Server/`
- Integration: cover all 5 project scenarios end-to-end

---

## 16. Observability & runbook

### 16.1 Health endpoints

`Server.Health` returns:

```json
{
  "ok": true,
  "version": "1.0.0",
  "schema": "1.0",
  "uptimeSeconds": 1245,
  "queueDepth": 0,
  "queueDepthMax": 12,
  "rpcsHandled": 8401,
  "rpcsErrored": 14,
  "lastIdleAgo": 80,
  "lastIdleAgoMaxMs": 1820,
  "autocadVersion": "26.0.0",
  "activeDocument": "C:\\VSCode\\callie-job\\-callie-job\\projects\\04-kitchen\\out\\kitchen.dwg"
}
```

### 16.2 Common diagnostics

| Symptom | Diagnostic step |
|---|---|
| Client gets `PluginUnavailable` | `Test-NetConnection 127.0.0.1 -Port 7878` — is the listener up? Check `%APPDATA%\TechniCadBridge\plugin.log` for startup errors |
| Calls hang for 30 s then time out | AutoCAD likely modal — check the AutoCAD window for a dialog. Plugin should return `-32005` automatically; if not, file a bug |
| `-32003 MaterialNotFound` for a library material | Run `Material.ListLibrary` — is the name correct? Some library materials are version-specific |
| Render produces black image | Check sun status (`Light.SetSun {enabled: true}`); check defaultLighting; check materials are assigned to layers (`Material.List`) |
| Plugin log fills with `[error] queue item threw: NullReferenceException` | Likely a refactor broke a handler; check the stack trace in the log |

### 16.3 Runbook entries

Located in `docs/RUNBOOK.md`:

- **Plugin won't load** — re-run `install.ps1`; check AutoCAD's
  trusted-path security (TRUSTEDPATHS sysvar)
- **Port 7878 in use** — plugin auto-tries 7879..7888; check the
  `port` file
- **AutoCAD froze** — kill AutoCAD; restart; plugin will reload from
  the registry auto-load
- **Need to debug a slow render** — set `config.debug.logEveryRpc = true`;
  reproduce; analyze `trace.jsonl` with `jq`

---

## 17. Phased roadmap with concrete tickets

### Phase 1 — Foundation (Week 1, ~20 hours)

| # | Ticket | Estimate |
|---|---|---|
| 1.1 | Bootstrap `technijian-cad-bridge` repo, initial `TechniCadBridge.sln` with empty .csproj | 1h |
| 1.2 | `IExtensionApplication` skeleton, NETLOAD verify with hello-world Editor.WriteMessage | 2h |
| 1.3 | Wire up Newtonsoft.Json, `JsonRpcRequest/Response/Error` POCOs, line-delimited TCP listener | 3h |
| 1.4 | `CommandQueue` + `Application.Idle` consumer + integration smoke test | 2h |
| 1.5 | `HandlerRegistry` (reflection over `[RpcMethod]` attribute) + dispatch | 2h |
| 1.6 | `DocumentHandler` — Status, New, Open, Save, Cancel | 3h |
| 1.7 | `LayerHandler` — List, Create, SetActive, Freeze | 2h |
| 1.8 | `GeometryHandler` Phase 1 set — AddBox, AddCylinder, AddLine, AddPolyline, Boolean | 2h |
| 1.9 | Python `plugin_client.py` + facade flag in `acad.py` | 2h |
| 1.10 | `install.ps1` + `uninstall.ps1` | 1h |

**Phase 1 Exit criterion:** `python build_kitchen.py` runs end-to-end
with `USE_PLUGIN=1` env var and produces the same kitchen.dwg as
today, with zero `RPC_E_CALL_REJECTED` errors.

### Phase 2 — Materials & rendering (Week 2, ~25 hours)

| # | Ticket | Estimate |
|---|---|---|
| 2.1 | `MaterialHandler.ListLibrary` over `Autodesk.AutoCAD.MaterialLibrary` | 4h |
| 2.2 | `MaterialHandler.ImportFromLibrary` + `AssignToLayer` | 4h |
| 2.3 | `MaterialHandler.Create` with PBR options + texture-map paths | 3h |
| 2.4 | `LightHandler` — Point/Spot/Distant via `Light` class | 4h |
| 2.5 | `Light.SetSun` with lat/lon/date/time | 2h |
| 2.6 | `RenderHandler.ToFile` — RenderManager spike + integration test | 6h |
| 2.7 | `Export.Fbx`, `Export.Gltf`, `Export.Stl` (replace per-layer-STL workaround) | 2h |

**Phase 2 Exit criterion:** Single Python script renders kitchen at
photoreal quality directly in AutoCAD (no Blender side-trip required).
Optional path: continue using Blender for renders if quality preferred.

### Phase 3 — Layouts & plotting (Week 3, ~20 hours)

| # | Ticket | Estimate |
|---|---|---|
| 3.1 | `LayoutHandler.Create` + `SetActive` + `Delete` | 3h |
| 3.2 | `Layout.AddViewport` with view + scale | 4h |
| 3.3 | `Layout.SetViewportLayerVisibility` (per-viewport freeze) | 3h |
| 3.4 | `Plot.ToPdf` — full PlotEngine integration | 6h |
| 3.5 | Block-reference insertion for title block | 2h |
| 3.6 | Integration tests for ARCH-D 4-viewport plot | 2h |

**Phase 3 Exit criterion:** Each project produces a `<project>-A-XXX.pdf`
plot output that matches the brief's deliverable spec.

### Phase 4 — Hardening (Week 4, ~15 hours)

| # | Ticket | Estimate |
|---|---|---|
| 4.1 | Unit-test coverage to 80% for handlers | 4h |
| 4.2 | Integration test runner against real AutoCAD (self-hosted CI) | 4h |
| 4.3 | Modal-dialog detection + auto-fail-fast | 2h |
| 4.4 | `Cancel.RequestById` plumbing | 1h |
| 4.5 | Telemetry rotation + retention policy | 1h |
| 4.6 | `gen-protocol-md.ps1` — auto-generate `docs/PROTOCOL.md` from XML doc comments | 2h |
| 4.7 | RUNBOOK.md, DEVELOPER.md, ARCHITECTURE.md polish | 1h |

**Phase 4 Exit criterion:** New laptop → install AutoCAD 2027 → run
`packaging\install.ps1` → open Claude Code → run all four
`build_*.py` scripts → all artifacts produced with zero manual
intervention.

---

## 18. Acceptance tests

### 18.1 Functional

1. **A1.** `python build_home_office.py` produces 41-entity .dwg + plan PNG + iso PNG + Word doc. ✓ if all artifacts exist and match golden checksums.
2. **A2.** `python build_kitchen.py` produces 141-entity .dwg + plan PNG + photoreal render PNG + ARCH-D PDF. ✓ if PDF has 4 viewports.
3. **A3.** `python build_living_room.py` produces 109-entity .dwg with lofted chairs, revolved lamp, swept drapery, photometric lights, and saved HERO + EDITORIAL camera views that **actually restore the saved camera position**.

### 18.2 Reliability

4. **R1.** Issue 10000 small ops (`Geometry.AddBox` with random coords) over 1 hour. Zero deadlocks; max latency < 200 ms; no growth in `queueDepth` over time.
5. **R2.** Open a modal `SAVEAS` dialog manually in AutoCAD. Issue any RPC. ✓ if returns `-32005 ModalDialogActive` within `config.timeouts.modalDetectMs`.
6. **R3.** Crash plugin via `taskkill` mid-render. Re-NETLOAD. Next call succeeds.

### 18.3 Performance

7. **P1.** `Geometry.AddBox` p99 latency < 50 ms.
8. **P2.** `Render.ToFile` at Medium / 1920×1080 completes within 60 s.
9. **P3.** `Plot.ToPdf` for a 1-layout ARCH-D sheet completes within 30 s.

### 18.4 Compatibility

10. **C1.** Plugin works on AutoCAD 2026 (validates `MajorVersion = 26`).
11. **C2.** Plugin works on AutoCAD 2027 (validates `MajorVersion = 27`).

---

## 19. Risks & mitigations

| # | Risk | P | Impact | Mitigation |
|---|---|---|---|---|
| R1 | AutoCAD's `RenderManager` API is partially undocumented | Medium | High (Phase 2 blocker) | Spike in Phase 1 sprint before committing Phase 2 schedule |
| R2 | Material library API differs across AutoCAD versions | Medium | Medium | Pin to AutoCAD 2027; document 2026 fallback |
| R3 | `Application.Idle` doesn't fire during modal dialogs | High | High | Pair with `WndProc` interception; document detection in §6.4 |
| R4 | DLL conflicts with another AutoCAD plugin | Low | Medium | `CopyLocalLockFileAssemblies = false`; binding redirects |
| R5 | Autodesk AutoCAD 2028 release breaks the API | Low (timing) | Medium | Pin AutoCAD version; spec versioning |
| R6 | StreamJsonRpc / Newtonsoft.Json conflict with AutoCAD's bundled versions | Medium | Low | Use `EmbeddedResource` + `AssemblyResolve` to load private copies |
| R7 | Plugin holds a reference to the `Document` after it's closed (use-after-free) | Medium | High (AutoCAD crash) | All handlers re-resolve `MdiActiveDocument` on entry, never cache |
| R8 | TCP port 7878 collides with another local service | Low | Low | Auto-fallback range 7878–7888 + writes actual port to discovery file |
| R9 | Long-running render blocks UI for 60+ seconds | Medium | Medium | Use `RenderManager.RenderAsync` (verify exists); fall back to a worker thread that posts results back via Idle |
| R10 | User runs Python script before AutoCAD finishes loading | Medium | Low | `PluginClient` retries with backoff for 10 s on `ConnectionRefused` |
| R11 | Path-traversal attack via `outputPath` | Medium | Medium | `PathValidator` allow-list; reject `..` segments |
| R12 | Plugin update breaks existing scripts via removed method | Low | High | Deprecation policy in §10.3; CHANGELOG.md required for every release |

---

## 20. Effort, cost, schedule

### 20.1 Effort breakdown

| Phase | Hours |
|---|---|
| Phase 1 — Foundation | 20 |
| Phase 2 — Materials & rendering | 25 |
| Phase 3 — Layouts & plotting | 20 |
| Phase 4 — Hardening | 15 |
| **Total** | **80** |

### 20.2 Schedule scenarios

| Scenario | Pace | Calendar |
|---|---|---|
| Full-time sprint | 8 hours/day × 5 days | 2 weeks |
| Half-time | 4 hours/day × 5 days | 4 weeks |
| Evening pace | 2 hours/day × 5 days | 8 weeks |
| Weekend pace | 8 hours/Saturday | 10 weeks |

Recommended: **Half-time × 4 weeks.** Spreads risk and lets Phase 2's
spike inform Phase 3 scope.

### 20.3 Cost (USD)

| Item | Cost | Notes |
|---|---|---|
| Visual Studio 2022 Community | $0 | Free for individual / open-source |
| AutoCAD 2027 license | $0 incremental | Already installed |
| ObjectARX SDK 2027 | $0 | Free download from Autodesk |
| StreamJsonRpc / Newtonsoft.Json / xUnit / NSubstitute | $0 | NuGet, MIT/Apache |
| GitHub private repo | $0 | Personal account included |
| Self-hosted CI runner (optional) | $0 | Existing Windows machine |
| **Total** | **$0** | |

---

## 21. Developer guide

This section is the contents of what would otherwise live in
`docs/DEVELOPER.md`. Written for someone who just cloned the repo and
wants to make their first change.

### 21.1 Dev environment setup

Required:

- **Windows 10/11 x64**
- **AutoCAD 2026 or 2027** installed (trial is fine for development).
  ObjectARX-managed assemblies live in the AutoCAD install dir.
- **.NET 8 SDK** — `winget install Microsoft.DotNet.SDK.8`
- **Git for Windows** — `winget install Git.Git`
- **Visual Studio 2022 Community** (free) — `winget install
  Microsoft.VisualStudio.2022.Community` with workloads:
  - `.NET desktop development`
  - `Debugging Tools for Windows`
- (optional) **Rider** — works fine, has better F#/Linux story but for
  this project VS is the path of least resistance.

Recommended:

- **PowerShell 7+** (`winget install Microsoft.PowerShell`)
- **Windows Terminal** (`winget install Microsoft.WindowsTerminal`)
- **NCat / netcat for Windows** for poking the JSON-RPC port from a
  shell — `winget install nmap` or build from source

### 21.2 First clone & build

```powershell
git clone https://github.com/rjain557/technijian-cad-bridge
cd technijian-cad-bridge

# Tell the build where AutoCAD lives (only needed if non-default path)
$env:AcadInstallDir = 'C:\Program Files\Autodesk\AutoCAD 2027'

# Build
.\scripts\build.ps1

# Run unit tests
.\scripts\test.ps1
```

Expected: `dotnet build -c Release` finishes clean; tests run; DLL
appears at `src\TechniCadBridge\bin\Release\net8.0-windows\TechniCadBridge.dll`.

### 21.3 Debugging the plugin from Visual Studio

1. Open `TechniCadBridge.sln` in VS 2022.
2. Set `TechniCadBridge` as the startup project.
3. Project → Properties → Debug → Open debug launch profiles UI.
4. Add a "Project" launcher with:
   - Executable: `C:\Program Files\Autodesk\AutoCAD 2027\acad.exe`
   - Command-line args: `/nologo`
   - Working directory: `$(ProjectDir)`
5. Hit F5. AutoCAD launches under the VS debugger; breakpoints in your
   handlers fire when JSON-RPC requests hit them.
6. From a separate shell, `nc 127.0.0.1 7878` and paste a JSON-RPC
   request to trigger your code.

**Important debugger gotcha:** AutoCAD has its own JIT and AppDomain
quirks. If breakpoints don't bind ("symbols not loaded"), enable
"Just My Code" off in Tools → Options → Debugging → General.

### 21.4 The most common dev task: adding a new handler method

Suppose you want to add `Geometry.AddTorus`.

**Step 1.** Add the method to `Handlers/GeometryHandler.cs`:

```csharp
[RpcMethod("Geometry.AddTorus")]
public CreateResult AddTorus(double[] center, double majorRadius,
                             double minorRadius, string? layer = null)
{
    var doc = ActiveDocOrThrow();
    using var docLock = doc.LockDocument();
    using var tr = doc.Database.TransactionManager.StartTransaction();
    var ms = (BlockTableRecord)tr.GetObject(
        ((BlockTable)tr.GetObject(doc.Database.BlockTableId, OpenMode.ForRead))
            [BlockTableRecord.ModelSpace], OpenMode.ForWrite);

    var torus = new Solid3d();
    torus.CreateTorus(majorRadius, minorRadius);
    torus.TransformBy(Matrix3d.Displacement(
        new Point3d(center[0], center[1], center[2]) - Point3d.Origin));
    if (layer is not null) torus.Layer = layer;

    ms.AppendEntity(torus);
    tr.AddNewlyCreatedDBObject(torus, true);
    tr.Commit();

    return new CreateResult
    {
        Handle = torus.Handle.ToString(),
        ObjectName = torus.GetType().Name,
        Layer = torus.Layer
    };
}
```

**Step 2.** Add a unit test in `tests/TechniCadBridge.Tests/Handlers/GeometryHandlerTests.cs`:

```csharp
[Fact]
public void AddTorus_ValidParams_ReturnsHandle()
{
    var docSvc = new FakeDocumentService();
    var sut = new GeometryHandler(docSvc);
    var result = sut.AddTorus(new[] { 0.0, 0.0, 0.0 }, 5.0, 1.0, "I-FURN");
    Assert.NotNull(result.Handle);
    Assert.Equal("I-FURN", result.Layer);
}
```

**Step 3.** Update the spec:
- Add row in § 5.3.1 (Primitives table)
- Add a Changelog entry in Appendix D under "Unreleased"

**Step 4.** Update the Python facade in `acad.py` (in the `-callie-job`
repo) if the method should be exposed there.

**Step 5.** Run `scripts/gen-protocol-md.ps1` (Phase 4) to refresh the
auto-generated protocol doc.

### 21.5 Code style

| Rule | Notes |
|---|---|
| C# 12, .NET 8 nullable references | `<Nullable>enable</Nullable>` in csproj |
| Brace style | Allman (newline before `{`); the editor config enforces |
| Naming | `PascalCase` for types/members, `_camelCase` for private fields, `camelCase` for params/locals |
| Async | All long-running ops are `async Task<T>`; `await` everywhere; never `.Result` |
| LINQ | Allowed in handlers but never inside transactions where it might defer enumeration past `tr.Commit()` |
| Logging | `Logger.Info/Warn/Error/Debug`; never `Console.WriteLine` outside of dev spikes |
| Magic numbers | Hoist to `const` with a comment when reused; one-off thresholds inline are fine |
| Comments | Explain *why* not *what*; XML doc comments on every `[RpcMethod]` (used by the protocol-doc generator) |
| `using` declarations | Prefer `using var` (C# 8 simple disposal) for `Transaction`, `DocumentLock` |

### 21.6 Transactions & document locks — the rules that prevent crashes

AutoCAD's database mutation API is finicky. The plugin enforces:

1. **Every handler that touches the database opens a `Transaction`.**
   Even a read. Outside a transaction, `tr.GetObject` throws
   `eLockViolation`.
2. **Every handler that writes to the database opens a
   `DocumentLock` first.** Required when running on the main thread
   from a non-AutoCAD-command path (which the plugin is).
3. **Never cache `Document`, `Database`, or `ObjectId` across
   handler calls.** Re-resolve on every entry. The user might have
   closed and reopened a drawing between calls.
4. **`Transaction.Commit()` before any non-AutoCAD work** (file IO,
   JSON serialization). Don't do `tr.Commit()` after writing a PNG.
5. **Use `using var tr = ...` not `try/finally tr.Dispose()`** —
   safer, especially when nested.
6. **If a handler throws, the transaction auto-aborts** when the
   `using` scope exits. Don't manually `tr.Abort()` unless you have a
   compensating action.

### 21.7 Adding a new handler class (groups of methods)

1. Create `Handlers/MyNewHandler.cs` with `[RpcMethod]` attributes.
2. The `HandlerRegistry` discovers handlers via reflection at startup —
   no manual registration needed.
3. Add a row to the table in § 5 of this spec.
4. Add unit tests in `tests/TechniCadBridge.Tests/Handlers/`.
5. If the handler depends on a new AutoCAD assembly (e.g.
   `acpltsvc.dll` for plotting), add a `<Reference>` entry to the
   csproj.

### 21.8 Branch & PR flow (until v1.1, when the repo goes public)

| Step | Convention |
|---|---|
| Branch from | `main` (always) |
| Branch name | `phase-<N>/<short-slug>` (e.g. `phase-2/material-library`) |
| Commit messages | Imperative, lower-case, first line ≤ 72 chars; body explains *why* |
| PR title | Same as feature commit message |
| PR body | "Closes #N" + bullet list of changes + screenshots/test output |
| Reviewer | rjain |
| Merge | Squash merge; commit message = PR title |
| CHANGELOG | Update Appendix D before merge |

Until the repo opens, "PR" is informal — branches against `main` for
diffability, but no GitHub PR review process. After v1.1 open-source
review, switch to GitHub PR with required `ci` + 1 reviewer.

### 21.9 Release process

1. Merge all phase tickets to `main`
2. Bump version in `src/TechniCadBridge/AssemblyInfo.cs` and
   `Directory.Build.props`
3. Add a Changelog entry in Appendix D ("`## [1.0.0] — 2026-MM-DD`")
4. Tag: `git tag v1.0.0; git push --tags`
5. Build release: `.\scripts\publish.ps1` outputs DLL + zipped install
   bundle
6. (Optional) GitHub release with attached zip

### 21.10 Common pitfalls (and how to fix them)

| Pitfall | Fix |
|---|---|
| Unit test passes, integration test fails with `eLockViolation` | Forgot `using var docLock = doc.LockDocument();` in the handler |
| Plugin DLL won't NETLOAD: "could not load file or assembly" | Check that all `Reference Include="ac*"` entries in csproj have `<Private>false</Private>` |
| Plugin loads but client gets connection refused | Check `Application.Idle` is firing; if AutoCAD is showing a startup splash or modal, Idle doesn't fire |
| `Newtonsoft.Json` version conflict between plugin and AutoCAD's bundled copy | Use `<PrivateAssets>all</PrivateAssets>` on the PackageReference and add an `AssemblyResolve` handler in `PluginEntry` |
| Render returns black PNG | Default lighting probably ON — set `Light.SetSun {enabled: true}` and `Render.SetDefaults {defaultLighting: false}` |
| `Geometry.Loft` succeeds but result has weird normals | Section curves were drawn in inconsistent orientations; reverse one of them with `Polyline.ReverseCurve()` before lofting |

---

## 22. Protocol reference — full examples per handler

This is the contents of what would otherwise live in
`docs/PROTOCOL.md`. § 5 is the catalog (params + return shape); this §
22 is the **examples** — one canonical request/response pair per
handler so a reader can copy-paste and modify.

Once Phase 4 implements `scripts/gen-protocol-md.ps1`, that script
produces a more exhaustive auto-generated reference. Until then, these
examples are canonical.

### 22.1 Document handler

**`Document.Status`**

Request:

```json
{ "jsonrpc": "2.0", "id": 1, "method": "Document.Status" }
```

Response:

```json
{
  "jsonrpc": "2.0", "id": 1,
  "result": {
    "name": "kitchen.dwg",
    "path": "C:\\VSCode\\callie-job\\-callie-job\\projects\\04-kitchen\\out\\kitchen.dwg",
    "saved": true,
    "layerCount": 22,
    "entityCount": 141,
    "activeLayer": "0",
    "activeView": "NEISO"
  }
}
```

**`Document.New`**

```json
{ "jsonrpc": "2.0", "id": 2, "method": "Document.New",
  "params": { "template": "C:\\Program Files\\Autodesk\\AutoCAD 2027\\Template\\acad.dwt" } }
```

```json
{ "jsonrpc": "2.0", "id": 2,
  "result": { "name": "Drawing2.dwg", "path": "" } }
```

**`Document.Save`**

```json
{ "jsonrpc": "2.0", "id": 3, "method": "Document.Save",
  "params": { "path": "C:\\Users\\rjain\\Desktop\\test.dwg" } }
```

```json
{ "jsonrpc": "2.0", "id": 3,
  "result": { "name": "test.dwg",
              "path": "C:\\Users\\rjain\\Desktop\\test.dwg",
              "saved": true } }
```

### 22.2 Layer handler

**`Layer.List`**

```json
{ "jsonrpc": "2.0", "id": 10, "method": "Layer.List" }
```

```json
{ "jsonrpc": "2.0", "id": 10,
  "result": [
    { "name": "0", "color": 7, "frozen": false, "locked": false,
      "on": true, "material": null, "lineweight": -3 },
    { "name": "A-WALL", "color": 254, "frozen": false, "locked": false,
      "on": true, "material": "Paint-Interior-White", "lineweight": -3 },
    { "name": "I-CASE", "color": 33, "frozen": false, "locked": false,
      "on": true, "material": "Cabinet-Paint", "lineweight": -3 }
  ] }
```

**`Layer.Create`**

```json
{ "jsonrpc": "2.0", "id": 11, "method": "Layer.Create",
  "params": { "name": "I-DETAIL", "color": 33 } }
```

```json
{ "jsonrpc": "2.0", "id": 11,
  "result": { "name": "I-DETAIL", "created": true } }
```

**`Layer.Freeze` (error case — freezing the active layer)**

```json
{ "jsonrpc": "2.0", "id": 12, "method": "Layer.Freeze",
  "params": { "name": "I-CASE", "freeze": true } }
```

```json
{ "jsonrpc": "2.0", "id": 12,
  "error": {
    "code": -32011,
    "message": "Cannot freeze the active layer 'I-CASE'",
    "data": {
      "symbol": "LayerStateInvalid",
      "reason": "cannot freeze active layer",
      "layer": "I-CASE",
      "method": "Layer.Freeze",
      "rpcId": 12
    }
  } }
```

### 22.3 Geometry handler

**`Geometry.AddBox`**

```json
{ "jsonrpc": "2.0", "id": 20, "method": "Geometry.AddBox",
  "params": {
    "corner1": [0, 0, 0],
    "corner2": [10, 5, 8],
    "layer": "I-CASE"
  } }
```

```json
{ "jsonrpc": "2.0", "id": 20,
  "result": {
    "handle": "2BC",
    "objectName": "AcDb3dSolid",
    "layer": "I-CASE",
    "boundingBox": { "min": [0,0,0], "max": [10,5,8] },
    "center": [5, 2.5, 4],
    "size": [10, 5, 8]
  } }
```

**`Geometry.Loft` (replaces the LISP fragments from session 04-25)**

```json
{ "jsonrpc": "2.0", "id": 21, "method": "Geometry.Loft",
  "params": {
    "sectionHandles": ["3A", "3B", "3C"],
    "options": { "guideMode": "crossSectionsOnly" }
  } }
```

```json
{ "jsonrpc": "2.0", "id": 21,
  "result": { "handle": "3D", "objectName": "AcDb3dSolid",
              "layer": "I-FURN" } }
```

**`Geometry.Boolean`**

```json
{ "jsonrpc": "2.0", "id": 22, "method": "Geometry.Boolean",
  "params": {
    "op": "subtract",
    "sourceHandles": ["2BC"],
    "otherHandles": ["2BD", "2BE"]
  } }
```

```json
{ "jsonrpc": "2.0", "id": 22,
  "result": { "handle": "2BC", "op": "subtract",
              "remaining": "AcDb3dSolid" } }
```

### 22.4 Entity handler

**`Entity.List` (filtered)**

```json
{ "jsonrpc": "2.0", "id": 30, "method": "Entity.List",
  "params": { "layer": "I-CASE", "type": "AcDb3dSolid", "limit": 50 } }
```

```json
{ "jsonrpc": "2.0", "id": 30,
  "result": [
    { "handle": "2BC", "type": "AcDb3dSolid", "layer": "I-CASE" },
    { "handle": "2BD", "type": "AcDb3dSolid", "layer": "I-CASE" }
  ] }
```

**`Entity.SetMaterial`**

```json
{ "jsonrpc": "2.0", "id": 31, "method": "Entity.SetMaterial",
  "params": { "handle": "2BC", "material": "Wood-Walnut" } }
```

```json
{ "jsonrpc": "2.0", "id": 31, "result": {} }
```

### 22.5 View & VisualStyle handlers

**`View.SetCustom`**

```json
{ "jsonrpc": "2.0", "id": 40, "method": "View.SetCustom",
  "params": {
    "location": [240, 60, 80],
    "target": [60, 60, 36],
    "lens": 35
  } }
```

```json
{ "jsonrpc": "2.0", "id": 40, "result": {} }
```

**`View.SaveCamera` then `View.RestoreCamera`**

```json
{ "jsonrpc": "2.0", "id": 41, "method": "View.SaveCamera",
  "params": { "name": "HERO", "location": [240, 60, 80],
              "target": [60, 60, 36], "lens": 35 } }
```

```json
{ "jsonrpc": "2.0", "id": 41, "result": { "name": "HERO" } }
```

```json
{ "jsonrpc": "2.0", "id": 42, "method": "View.RestoreCamera",
  "params": { "name": "HERO" } }
```

```json
{ "jsonrpc": "2.0", "id": 42,
  "result": { "name": "HERO", "location": [240, 60, 80],
              "target": [60, 60, 36], "lens": 35 } }
```

**`VisualStyle.Set`**

```json
{ "jsonrpc": "2.0", "id": 43, "method": "VisualStyle.Set",
  "params": { "style": "Realistic" } }
```

```json
{ "jsonrpc": "2.0", "id": 43,
  "result": { "visualStyle": "Realistic" } }
```

### 22.6 Material handler (the headline capability)

**`Material.ListLibrary` (filtered)**

```json
{ "jsonrpc": "2.0", "id": 50, "method": "Material.ListLibrary",
  "params": { "family": "Wood", "search": "oak" } }
```

```json
{ "jsonrpc": "2.0", "id": 50,
  "result": [
    { "name": "Wood-WhiteOak-Natural", "family": "Wood",
      "displayName": "White Oak — Natural" },
    { "name": "Wood-WhiteOak-Stained", "family": "Wood",
      "displayName": "White Oak — Stained" },
    { "name": "Wood-RedOak-Natural",  "family": "Wood",
      "displayName": "Red Oak — Natural" }
  ] }
```

**`Material.ImportFromLibrary`**

```json
{ "jsonrpc": "2.0", "id": 51, "method": "Material.ImportFromLibrary",
  "params": { "name": "Wood-WhiteOak-Natural", "asLayerMaterial": false } }
```

```json
{ "jsonrpc": "2.0", "id": 51,
  "result": { "material": "Wood-WhiteOak-Natural", "imported": true } }
```

**`Material.AssignToLayer`**

```json
{ "jsonrpc": "2.0", "id": 52, "method": "Material.AssignToLayer",
  "params": { "layer": "A-FLOR", "material": "Wood-WhiteOak-Natural" } }
```

```json
{ "jsonrpc": "2.0", "id": 52, "result": {} }
```

**`Material.Create` (custom PBR)**

```json
{ "jsonrpc": "2.0", "id": 53, "method": "Material.Create",
  "params": {
    "name": "Custom-Coastal-Blue",
    "color": [66, 110, 145],
    "roughness": 0.5,
    "metallic": 0.0,
    "diffuseMap": "C:\\Textures\\coastal-blue-diffuse.jpg"
  } }
```

```json
{ "jsonrpc": "2.0", "id": 53,
  "result": { "material": "Custom-Coastal-Blue" } }
```

### 22.7 Light handler

**`Light.AddPoint`**

```json
{ "jsonrpc": "2.0", "id": 60, "method": "Light.AddPoint",
  "params": {
    "position": [60, 60, 119.5],
    "intensity": 800,
    "color": 2700,
    "name": "CAN_2_2"
  } }
```

```json
{ "jsonrpc": "2.0", "id": 60,
  "result": { "handle": "5A", "name": "CAN_2_2" } }
```

**`Light.SetSun` (replaces the hung SUNSTATUS sysvar)**

```json
{ "jsonrpc": "2.0", "id": 61, "method": "Light.SetSun",
  "params": {
    "enabled": true,
    "latitude": 33.6404,
    "longitude": -117.6031,
    "date": "2026-04-10T16:30:00",
    "timezone": -7,
    "intensity": 1.0
  } }
```

```json
{ "jsonrpc": "2.0", "id": 61,
  "result": { "enabled": true, "latitude": 33.6404,
              "longitude": -117.6031,
              "date": "2026-04-10T16:30:00", "timezone": -7,
              "intensity": 1.0 } }
```

### 22.8 Render handler

**`Render.ListPresets`**

```json
{ "jsonrpc": "2.0", "id": 70, "method": "Render.ListPresets" }
```

```json
{ "jsonrpc": "2.0", "id": 70,
  "result": [
    { "name": "Draft", "samples": 8, "lighting": "default",
      "description": "Fast preview" },
    { "name": "Low", "samples": 16, "lighting": "default",
      "description": "Quick check" },
    { "name": "Medium", "samples": 64, "lighting": "photometric",
      "description": "Standard preview render" },
    { "name": "High", "samples": 128, "lighting": "photometric",
      "description": "Client-ready" },
    { "name": "Presentation", "samples": 256, "lighting": "photometric",
      "description": "Marketing-quality" }
  ] }
```

**`Render.ToFile` — the headless render (no dialog)**

```json
{ "jsonrpc": "2.0", "id": 71, "method": "Render.ToFile",
  "params": {
    "preset": "High",
    "view": "NEISO",
    "outputPath": "C:\\VSCode\\callie-job\\-callie-job\\projects\\04-kitchen\\out\\render-final.png",
    "width": 1920,
    "height": 1200,
    "exposure": 0.0
  } }
```

```json
{ "jsonrpc": "2.0", "id": 71,
  "result": {
    "outputPath": "C:\\VSCode\\callie-job\\-callie-job\\projects\\04-kitchen\\out\\render-final.png",
    "durationMs": 47230
  } }
```

### 22.9 Layout & Plot handler

**`Layout.Create`**

```json
{ "jsonrpc": "2.0", "id": 80, "method": "Layout.Create",
  "params": {
    "name": "A-201",
    "paperSize": "ARCH-D",
    "plotter": "DWG To PDF.pc3"
  } }
```

```json
{ "jsonrpc": "2.0", "id": 80, "result": { "name": "A-201" } }
```

**`Layout.AddViewport`**

```json
{ "jsonrpc": "2.0", "id": 81, "method": "Layout.AddViewport",
  "params": {
    "layout": "A-201",
    "center": [12, 18],
    "width": 18,
    "height": 12,
    "viewName": "TOP",
    "scale": 0.0208333
  } }
```

```json
{ "jsonrpc": "2.0", "id": 81, "result": { "handle": "9F" } }
```

**`Plot.ToPdf`**

```json
{ "jsonrpc": "2.0", "id": 82, "method": "Plot.ToPdf",
  "params": {
    "layout": "A-201",
    "outputPath": "C:\\VSCode\\callie-job\\-callie-job\\projects\\04-kitchen\\out\\kitchen-A-201.pdf",
    "paperSize": "ARCH-D"
  } }
```

```json
{ "jsonrpc": "2.0", "id": 82,
  "result": {
    "outputPath": "C:\\VSCode\\callie-job\\-callie-job\\projects\\04-kitchen\\out\\kitchen-A-201.pdf"
  } }
```

### 22.10 Export & Import handler

**`Export.Fbx`**

```json
{ "jsonrpc": "2.0", "id": 90, "method": "Export.Fbx",
  "params": {
    "outputPath": "C:\\VSCode\\callie-job\\-callie-job\\projects\\04-kitchen\\out\\kitchen.fbx",
    "options": {
      "exportMaterials": true,
      "exportLights": true,
      "exportCameras": true
    }
  } }
```

```json
{ "jsonrpc": "2.0", "id": 90,
  "result": {
    "outputPath": "C:\\VSCode\\callie-job\\-callie-job\\projects\\04-kitchen\\out\\kitchen.fbx",
    "sizeBytes": 482733
  } }
```

**`Export.LayerStls` (replaces the per-layer hack)**

```json
{ "jsonrpc": "2.0", "id": 91, "method": "Export.LayerStls",
  "params": {
    "outputDir": "C:\\VSCode\\callie-job\\-callie-job\\projects\\04-kitchen\\out\\stl-by-layer",
    "layers": ["A-FLOR", "A-WALL", "I-CASE", "I-CASE-CTR"]
  } }
```

```json
{ "jsonrpc": "2.0", "id": 91,
  "result": {
    "files": [
      { "layer": "A-FLOR", "path": "...\\A-FLOR.stl", "sizeBytes": 684 },
      { "layer": "A-WALL", "path": "...\\A-WALL.stl", "sizeBytes": 3084 },
      { "layer": "I-CASE", "path": "...\\I-CASE.stl", "sizeBytes": 2084 },
      { "layer": "I-CASE-CTR", "path": "...\\I-CASE-CTR.stl",
        "sizeBytes": 2484 }
    ]
  } }
```

**`Import.RasterImage`**

```json
{ "jsonrpc": "2.0", "id": 92, "method": "Import.RasterImage",
  "params": {
    "path": "C:\\VSCode\\callie-job\\-callie-job\\projects\\04-kitchen\\out\\render-photoreal.png",
    "position": [10, 10, 0],
    "scale": 1.0,
    "layer": "0"
  } }
```

```json
{ "jsonrpc": "2.0", "id": 92, "result": { "handle": "AB" } }
```

### 22.11 Dimension handler

**`Dimension.AddLinear`**

```json
{ "jsonrpc": "2.0", "id": 100, "method": "Dimension.AddLinear",
  "params": {
    "p1": [0, 0, 0],
    "p2": [168, 0, 0],
    "dimLineLocation": [84, -36, 0],
    "rotationRadians": 0,
    "layer": "A-ANNO-DIMS"
  } }
```

```json
{ "jsonrpc": "2.0", "id": 100, "result": { "handle": "C5" } }
```

**`Dimension.SetStyleVariable`**

```json
{ "jsonrpc": "2.0", "id": 101, "method": "Dimension.SetStyleVariable",
  "params": { "name": "DIMSCALE", "value": 24.0 } }
```

```json
{ "jsonrpc": "2.0", "id": 101, "result": { "previous": 1.0 } }
```

### 22.12 Var handler

**`Var.Set` and `Var.SetMany`**

```json
{ "jsonrpc": "2.0", "id": 110, "method": "Var.SetMany",
  "params": {
    "vars": [
      { "name": "FILEDIA", "value": 0 },
      { "name": "CMDDIA", "value": 0 },
      { "name": "EXPERT", "value": 5 },
      { "name": "LIGHTINGUNITS", "value": 2 }
    ]
  } }
```

```json
{ "jsonrpc": "2.0", "id": 110, "result": { "set": 4 } }
```

### 22.13 Server & Cancel handler

**`Server.Health`**

```json
{ "jsonrpc": "2.0", "id": 120, "method": "Server.Health" }
```

```json
{ "jsonrpc": "2.0", "id": 120,
  "result": {
    "ok": true,
    "version": "1.0.0",
    "schema": "1.0",
    "uptimeSeconds": 1245,
    "queueDepth": 0,
    "queueDepthMax": 12,
    "rpcsHandled": 8401,
    "rpcsErrored": 14,
    "lastIdleAgo": 80,
    "lastIdleAgoMaxMs": 1820,
    "autocadVersion": "26.0.0",
    "activeDocument": "C:\\VSCode\\callie-job\\-callie-job\\projects\\04-kitchen\\out\\kitchen.dwg"
  } }
```

**`Cancel.RequestById` (notification — no response)**

```json
{ "jsonrpc": "2.0", "method": "Cancel.RequestById",
  "params": { "rpcId": 71 } }
```

The previously-issued request 71 (e.g. a long render) returns:

```json
{ "jsonrpc": "2.0", "id": 71,
  "error": {
    "code": -32004,
    "message": "Request cancelled by client",
    "data": { "symbol": "Cancelled", "rpcId": 71 }
  } }
```

### 22.14 Batch request example

JSON-RPC 2.0 batches: send an array, receive an array. Useful for
"create 4 layers + 16 boxes" in one round trip.

Request:

```json
[
  { "jsonrpc": "2.0", "id": 200, "method": "Layer.Create",
    "params": { "name": "I-CASE", "color": 33 } },
  { "jsonrpc": "2.0", "id": 201, "method": "Layer.Create",
    "params": { "name": "I-FURN", "color": 3 } },
  { "jsonrpc": "2.0", "id": 202, "method": "Geometry.AddBox",
    "params": { "corner1": [0,0,0], "corner2": [10,5,8], "layer": "I-CASE" } }
]
```

Response (order matches request order):

```json
[
  { "jsonrpc": "2.0", "id": 200,
    "result": { "name": "I-CASE", "created": true } },
  { "jsonrpc": "2.0", "id": 201,
    "result": { "name": "I-FURN", "created": true } },
  { "jsonrpc": "2.0", "id": 202,
    "result": { "handle": "2BC", "objectName": "AcDb3dSolid",
                "layer": "I-CASE", "boundingBox": {...},
                "center": [5,2.5,4], "size": [10,5,8] } }
]
```

---

## Appendix A — JSON Schema

All RPC method params and returns have a JSON Schema (Draft 2020-12)
generated from the C# DTOs via `Microsoft.Extensions.Configuration.Json`
and `Json.Schema.NET`. Schemas published at
`docs/schemas/<Method>.params.json` and `<Method>.return.json`.

Sample (`Geometry.AddBox.params.json`):

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "GeometryAddBoxParams",
  "type": "object",
  "required": ["corner1", "corner2"],
  "properties": {
    "corner1": {
      "type": "array", "minItems": 3, "maxItems": 3,
      "items": { "type": "number" }
    },
    "corner2": {
      "type": "array", "minItems": 3, "maxItems": 3,
      "items": { "type": "number" }
    },
    "layer": { "type": "string" },
    "color": {
      "oneOf": [
        { "type": "integer", "minimum": 0, "maximum": 256 },
        { "type": "array", "minItems": 3, "maxItems": 3,
          "items": { "type": "integer", "minimum": 0, "maximum": 255 } }
      ]
    }
  }
}
```

---

## Appendix B — Mapping from existing `acad.py` to plugin methods

| `acad.py` method | Plugin method | Drop in Phase |
|---|---|---|
| `connect()` | (handled internally by `PluginClient` constructor) | 1 |
| `status()` | `Document.Status` | 1 |
| `new_drawing()` | `Document.New` | 1 |
| `open_drawing(path)` | `Document.Open` | 1 |
| `save(path?)` | `Document.Save` | 1 |
| `cancel()` | `Document.Cancel` | 1 |
| `wait_idle()` | (no direct equivalent — plugin reports queue health via `Server.Health`) | 1 |
| `add_line(s, e)` | `Geometry.AddLine` | 1 |
| `add_polyline(pts, closed)` | `Geometry.AddPolyline` | 1 |
| `add_rectangle(ll, ur)` | `Geometry.AddRectangle` | 1 |
| `add_circle(c, r)` | `Geometry.AddCircle` | 1 |
| `add_text(ins, txt, h)` | `Geometry.AddText` | 1 |
| `add_box(c1, c2)` | `Geometry.AddBox` | 1 |
| `add_cylinder(c, r, h)` | `Geometry.AddCylinder` | 1 |
| `boolean(op, sources, others)` | `Geometry.Boolean` | 1 |
| `change_color(handle, aci)` | `Entity.SetColor` | 1 |
| `set_view(preset)` | `View.SetPreset` | 1 |
| `set_visual_style(style)` | `VisualStyle.Set` | 1 |
| `list_entities(type, limit)` | `Entity.List` | 1 |
| `list_layers()` | `Layer.List` | 1 |
| `create_layer(name, color)` | `Layer.Create` | 1 |
| `set_active_layer(name)` | `Layer.SetActive` | 1 |
| `freeze_layer(name, freeze)` | `Layer.Freeze` | 1 |
| (LISP-via-`send_command` for LOFT) | `Geometry.Loft` | 1 (proper API) |
| (LISP-via-`send_command` for REVOLVE) | `Geometry.Revolve` | 1 |
| (LISP-via-`send_command` for SWEEP) | `Geometry.Sweep` | 1 |
| (LISP-via-`send_command` for FILLETEDGE) | `Geometry.Fillet` | 1 |
| (`POINTLIGHT` SendCommand sequence) | `Light.AddPoint` | 2 |
| (no equivalent — was GUI-only) | `Material.ImportFromLibrary` | 2 |
| (no equivalent — was GUI-only) | `Render.ToFile` | 2 |
| (no equivalent — was GUI-only) | `Plot.ToPdf` | 3 |
| (no equivalent — `FBXEXPORT` hung) | `Export.Fbx` | 2 |
| (`STLOUT` per-layer hack) | `Export.LayerStls` | 2 |

---

## Appendix C — AutoCAD .NET API references used

| Namespace | Why we need it |
|---|---|
| `Autodesk.AutoCAD.Runtime` | `IExtensionApplication`, `[CommandMethod]`, exception types |
| `Autodesk.AutoCAD.ApplicationServices` | `Application`, `DocumentManager`, `Document`, `Application.Idle` |
| `Autodesk.AutoCAD.DatabaseServices` | `Database`, `LayerTable`, `LayerTableRecord`, `Solid3d`, `Polyline`, `Line`, `Circle`, `BlockTable`, `BlockTableRecord`, `Material`, `MaterialDictionary`, `Sun`, `Light` |
| `Autodesk.AutoCAD.GraphicsInterface` | `VisualStyle` types |
| `Autodesk.AutoCAD.GraphicsSystem` | `RenderManager` (Phase 2) |
| `Autodesk.AutoCAD.Geometry` | `Point3d`, `Vector3d`, `Matrix3d` |
| `Autodesk.AutoCAD.PlottingServices` | `PlotEngineFactory`, `PlotInfo`, `PlotConfig` (Phase 3) |
| `Autodesk.AutoCAD.Colors` | `Color`, `ColorMethod` |

Assemblies referenced: `accoremgd.dll`, `acdbmgd.dll`, `acmgd.dll`,
`acdbmgdbrep.dll` (Phase 2 for materials).

---

## Appendix D — Changelog

This is the contents of what would otherwise live in
`docs/CHANGELOG.md`. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning
per § 10 of this spec.

### [Unreleased]

Phase 1 work goes here. As tickets land on `main`, append entries
under one of these subsections: `### Added`, `### Changed`,
`### Deprecated`, `### Removed`, `### Fixed`, `### Security`.

### [1.0.0] — TBD (Phase 4 exit)

First production release. All four phases complete; passes acceptance
tests § 18.

#### Added

- Plugin loads via `NETLOAD` and exposes JSON-RPC 2.0 over TCP
  127.0.0.1:7878 (configurable). See § 3.
- 84 RPC methods across 11 handlers. See § 5 catalog and § 22 examples.
- `Document.*` — Status, New, Open, Save, SaveAs, Close, Cancel.
- `Layer.*` — List, Create, SetActive, Freeze, Delete.
- `Geometry.*` — 18 methods covering primitives, 2D entities, and 3D
  CSG (Boolean, Loft, Revolve, Sweep, Extrude, Fillet, Chamfer,
  PressPull). Loft / Revolve / Sweep / Fillet replace the LISP
  `(handent ...)` fragments from session 04-25.
- `Entity.*` — Get, List, Delete, SetColor, SetLayer, SetMaterial,
  GetBoundingBox, Move, Rotate, Scale.
- `View.*` — SetPreset, SetCustom, SaveCamera, RestoreCamera,
  ListCameras, DeleteCamera, ZoomExtents, ZoomWindow.
  `View.RestoreCamera` actually restores camera position (replaces
  broken `_-VIEW _R` from session 04-27).
- `VisualStyle.*` — Set, SetVariable, GetVariable.
- `Material.*` — ListLibrary, ImportFromLibrary, Create,
  AssignToLayer, AssignToEntity, List, Delete. Library import via
  managed `Autodesk.AutoCAD.MaterialLibrary` API replaces MATBROWSER
  drag-drop.
- `Light.*` — AddPoint, AddSpot, AddDistant, SetSun, List, Delete.
  `SetSun` replaces hung `SUNSTATUS` SetVariable from session 04-27.
- `Render.*` — ListPresets, ToFile, SetDefaults. `Render.ToFile`
  produces PNG without opening any dialog.
- `Layout.*` + `Plot.*` — programmatic ARCH-D sheets with viewports,
  per-viewport view + scale + layer freeze, plot to PDF.
- `Export.*` — Fbx, Gltf, Stl, Dxf, Png, LayerStls. `LayerStls`
  replaces the per-layer hack in `export_per_layer_stl.py`.
- `Import.*` — RasterImage (replaces `IMAGEATTACH` dialog), Block,
  Xref.
- `Dimension.*` — AddLinear, AddAligned, AddRadius, AddAngular,
  SetStyleVariable.
- `Var.*` — Get, Set, SetMany (atomic).
- `Server.*` — Health, ListMethods.
- `Cancel.RequestById` — interrupts a long-running RPC.
- Modal-dialog auto-detection. Plugin returns `-32005
  ModalDialogActive` within `config.timeouts.modalDetectMs` instead of
  hanging silently. See § 6.4.
- 16 custom error codes (`-32000` to `-32015`). See § 6.2.
- Configuration at `%APPDATA%\TechniCadBridge\config.json` with
  schema validation and graceful fallback. See § 7.
- File logging at `%APPDATA%\TechniCadBridge\plugin.log`. See § 8.1.
- Opt-in telemetry at `%APPDATA%\TechniCadBridge\trace.jsonl`. See
  § 8.2.
- `install.ps1` / `uninstall.ps1` scripts. See § 14.
- Python `plugin_client.py` JSON-RPC client and `acad.py` facade
  (plugin-first, COM-fallback). See § 13.4–13.5.
- Auto-generated `docs/PROTOCOL.md` from XML doc comments via
  `scripts/gen-protocol-md.ps1`.

#### Performance characteristics

- `Geometry.AddBox` p99 latency < 50 ms.
- `Render.ToFile` Medium @ 1920×1080: 60 s.
- `Plot.ToPdf` ARCH-D sheet: 30 s.
- 10000 small ops over 1 hour: zero deadlocks, no queue growth.

#### Compatibility

- Tested on AutoCAD 2026 and 2027.
- Not supported: AutoCAD LT, Mac AutoCAD.

### [0.1.0] — 2026-04-27

Specification only — no code.

#### Added

- `PLUGIN_SPEC.md` v0.1 — initial draft.
- `PLUGIN_SYSTEM_SPEC.md` v1.0 — full system specification with all
  open questions resolved. Supersedes v0.1.

---

*End of v1.0 system specification. Treat this as the contract for
Phase 1 kickoff. Changes after kickoff require a Changelog entry in
Appendix D and a re-review.*

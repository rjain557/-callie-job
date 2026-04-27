# TechniCadBridge — System Specification (v1.0, ready-to-build)

**Project:** `technijian-cad-bridge`
**Type:** AutoCAD 2026/2027 .NET plugin (NETLOAD-able DLL)
**Target user:** rjain (single-machine, single-user; not Autodesk-marketplace)
**Spec status:** v1.0 — superseding `PLUGIN_SPEC.md` v0.1; all open questions resolved
**Author:** Claude — handed off as a working document; subject to revision during Phase 1

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
| Appendix A | JSON Schema for all method params/returns |
| Appendix B | Mapping from existing `acad.py` methods to plugin methods |
| Appendix C | AutoCAD .NET API references used |

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

*End of v1.0 system specification. Treat this as the contract for
Phase 1 kickoff. Changes after kickoff require a CHANGELOG entry and
a re-review.*

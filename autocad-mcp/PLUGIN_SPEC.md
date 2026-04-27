# AutoCAD Plugin — Software Specification

**Project name:** `TechniCadBridge` (working title — replace before publishing)
**Repo location:** `-callie-job/autocad-plugin/`
**Stakeholder:** rjain — drives Callie's AutoCAD learning + design deliverables
**Author of this spec:** Claude (handed off as a working document; expect changes during Phase 1)
**Spec status:** v0.1 — for review before scaffolding

---

## 0. TL;DR

Build a managed (.NET 8) AutoCAD plugin that loads inside the AutoCAD
2026/2027 process via `NETLOAD`, exposes the full Managed API (palette
operations, render manager, material library, layouts, plotting) over a
local JSON-RPC channel, and replaces every place where the existing
Python MCP server today resorts to `SendCommand`, `FILEDIA=0` dialog
suppression, or hand-tuned LISP fragments.

The plugin is the second leg of a tripod:

```
Claude Code  ──MCP──▶  Python MCP server  ──JSON-RPC──▶  TechniCadBridge.dll  ──Managed API──▶  AutoCAD
   (you)                  (autocad-mcp/server.py)             (loaded via NETLOAD)
```

Today the second leg goes `Python ──COM──▶ AutoCAD`. COM is the source
of every hard-to-debug failure surface in this repo (modal dialogs,
RPC_E_CALL_REJECTED, palette commands hanging, half the system
variables being read-only). The plugin closes that gap.

---

## 1. Why we need this

### 1.1 Catalog of pain points the plugin fixes

The five issues each consumed >30 minutes of a paid session:

| # | What broke | Today's hack | Plugin solution |
|---|------------|--------------|-----------------|
| 1 | `Documents.Add()` opens "Select Template" dialog and freezes COM | Save current Drawing1.dwg as the destination via SaveAs | Plugin's `Document.New(template?)` calls `Application.DocumentManager.Add(templatePath)` — never opens a dialog |
| 2 | `RENDER` opens an interactive window; result is unsaved | Substitute Conceptual visual style snapshot | Plugin calls `Autodesk.AutoCAD.GraphicsSystem.RenderManager.Render(preset, outputPath, w, h)` — file lands directly |
| 3 | `MATBROWSER` is palette-only, library import is GUI-drag-drop | Define generic materials via COM, no textures | Plugin uses `MaterialMap` + `Material.SetTexture` + AutoCAD's library-API to attach real PBR materials by name |
| 4 | `SUNSTATUS = 1` SetVariable hangs | Skip sun, document as GUI follow-up | Plugin sets the underlying Sun object via the managed API (`Database.Sun.IsActive = true`) |
| 5 | `POINTLIGHT` requires `LIGHTINGUNITS = 2` preset + explicit "X" eXit, otherwise hangs | Pre-set sysvar, append "X\n" | Plugin calls `Light.AddPointLight(position, intensity, color)` directly — no command-line round trip |

### 1.2 Catalog of capabilities we need but don't have today

| Capability | Why we need it | API the plugin will use |
|---|---|---|
| Library material import (Wood, Stone, Metal, Paint families) | Photoreal renders with grain/veining | `Autodesk.AutoCAD.MaterialLibrary` |
| Headless render to file at preset + size | Replace the Blender side-trip for users who want AutoCAD-native output | `RenderManager.Render(...)` |
| Paper-space layout setup (title block, viewports, plot to PDF) | Project 4 / 5 deliverable: ARCH-D presentation board | `Database.LayoutDictionary` + `Plot.PlotEngineFactory` |
| FBX / glTF / 3DS export with explicit options | Bridge to Blender / Twinmotion | `FbxExporter.Export(options)` (3D Studio MAX SDK shipped with AutoCAD) |
| `IMAGEATTACH` of a PNG with explicit position + scale | Embed a render onto a layout sheet | `RasterImageDef.ResolvePath` + `RasterImage` |
| FILLETEDGE / LOFT / REVOLVE / SWEEP with handle-addressed inputs | Replaces the LISP `(handent ...)` fragments that work but are fragile | `Solid3d.LoftFromCrossSections(...)`, `Solid3d.RevolveAroundAxis(...)`, etc. |
| Cancel a stuck modal cleanly | Today only `Win32 PostMessage VK_ESCAPE` works, and only sometimes | `Application.PostQuit()` is too aggressive, but `Editor.GetHistory().AbortAll()` works |
| Per-viewport visual style (each viewport in a layout can have its own style) | Required for the 4-viewport ARCH-D presentation sheet | `Viewport.VisualStyleId` |

---

## 2. Goals & non-goals

### 2.1 Goals (in priority order)

1. **Drop-in replacement for COM-based ops.** Every method on the
   existing `Acad` Python class (`autocad-mcp/acad.py`) gets a
   plugin-backed counterpart with the same signature.
2. **Headless render-to-file.** `Render(preset, view, output_path,
   width, height)` writes a PNG and returns. No dialog, no manual save.
3. **Real materials.** `AssignLibraryMaterial(layer, materialName)`
   imports the named library material if not already in the drawing,
   then assigns it.
4. **Paper-space layouts.** Programmatic layout creation with title
   block, viewports, viewport scales, plot to PDF.
5. **Robust cancel.** A `Cancel()` plugin command that aborts whatever
   the user-input pipeline is doing without resetting state we care
   about.

### 2.2 Non-goals

- Not building a public marketplace plugin. Single-user, single-machine
  use only. No Autodesk certification needed.
- Not supporting AutoCAD versions older than 2026.
- Not building a custom GUI / palette. The plugin is a daemon.
- Not duplicating Blender's render pipeline. AutoCAD render output is
  optional; the Blender bridge stays as the higher-quality path.
- Not building a feature for every AutoCAD command. Scope is locked to
  the surface of operations we currently script.

---

## 3. Architecture

### 3.1 Process model

```
┌─────────────────────────────────────────────────────────────────┐
│ AutoCAD.exe                                                     │
│  ├─ Document(s) (.dwg files open)                                │
│  └─ TechniCadBridge.dll (loaded via NETLOAD on AutoCAD startup)  │
│       ├─ JsonRpcServer  (TCP localhost:7878 — configurable)      │
│       ├─ CommandQueue   (single-threaded, serialized)             │
│       └─ Handlers       (one C# class per command group)          │
└─────────────────────────────────────────────────────────────────┘
              ▲
              │ JSON-RPC 2.0 over TCP (or named pipe in v2)
              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Python MCP server  (autocad-mcp/server.py)                       │
│  ├─ Existing FastMCP exposure (mcp__autocad__*)                  │
│  └─ acad.py refactored to call plugin first, COM as fallback     │
└─────────────────────────────────────────────────────────────────┘
              ▲
              │ MCP / stdio
              ▼
       Claude Code  (Anthropic CLI)
```

### 3.2 Why JSON-RPC over TCP

Alternatives considered:

| Channel | Pros | Cons |
|---|---|---|
| **JSON-RPC over TCP** ✓ | Multi-language friendly; survives multiple Python clients; easy to debug with `nc localhost 7878` | Slight setup (firewall prompt the first time) |
| Named pipes | No port; secure-by-default | Windows-only API; harder to debug |
| Local HTTP / REST | Easy with curl | Verbose for high-frequency calls |
| File-based queue | Trivial | Latency, polling overhead |
| Direct .NET interop from Python (pythonnet) | Zero serialization | Coupling; pythonnet has known race issues with AutoCAD's main thread |

JSON-RPC over TCP wins for ergonomics + debuggability. Default port
`7878` (configurable via `%APPDATA%\TechniCadBridge\config.json`).

### 3.3 Threading model

AutoCAD's managed API requires that calls touching the document
database happen on the main thread. The plugin enforces this with a
single-consumer command queue:

```
TCP listener thread
   ▼  (parses JSON-RPC, validates, resolves handler)
   ▼  (enqueues onto CommandQueue)
   ▼
Main-thread pump (registered via Application.Idle event or AcMgr.Idle)
   ▼  (dequeues; runs handler under lock; serializes result)
   ▼
TCP response
```

Long-running operations (RENDER) yield back to the pump every N
milliseconds via `Async/await` on a custom `AcadSynchronizationContext`.
This keeps AutoCAD's UI responsive while a render runs in the
background.

---

## 4. JSON-RPC protocol

### 4.1 Wire format

Standard JSON-RPC 2.0. Request:

```json
{ "jsonrpc": "2.0", "id": 1, "method": "Geometry.AddBox",
  "params": { "corner1": [0,0,0], "corner2": [10,5,8], "layer": "I-CASE" } }
```

Response:

```json
{ "jsonrpc": "2.0", "id": 1,
  "result": { "handle": "2BC", "objectName": "AcDb3dSolid",
              "boundingBox": { "min": [0,0,0], "max": [10,5,8] } } }
```

Error:

```json
{ "jsonrpc": "2.0", "id": 1,
  "error": { "code": -32001, "message": "Layer not found",
             "data": { "layer": "X" } } }
```

### 4.2 Method catalog (v1)

Grouped by handler class. Methods marked **NEW** don't have a working
COM equivalent today.

#### Document

| Method | Returns | Replaces |
|---|---|---|
| `Document.Status` | `{name, path, saved, layerCount, entityCount, activeLayer}` | `acad_status` |
| `Document.New(template?)` | `{name, path}` | `acad_new_drawing` (no template dialog) |
| `Document.Open(path)` | `{name, path}` | `acad_open_drawing` |
| `Document.Save(path?)` | `{name, path, saved}` | `acad_save` |
| `Document.SaveAs(path, format)` | `{name, path}` | **NEW** — explicit format (DWG/DXF/DXB) |
| `Document.Close(save?)` | `{}` | **NEW** |
| `Document.Cancel` | `{}` | `acad_cancel` (cleaner) |

#### Layer

| Method | Returns | Replaces |
|---|---|---|
| `Layer.List` | `[{name, color, frozen, locked, on, material}]` | `acad_list_layers` |
| `Layer.Create({name, color, material?})` | `{name, created}` | `acad_create_layer` |
| `Layer.SetActive(name)` | `{activeLayer}` | `acad_set_active_layer` |
| `Layer.Freeze({name, freeze})` | `{name, frozen}` | `acad_freeze_layer` |
| `Layer.Delete(name)` | `{deleted}` | **NEW** |

#### Geometry (2D + 3D)

| Method | Returns | Replaces |
|---|---|---|
| `Geometry.AddBox({c1, c2, layer?})` | `{handle, ...}` | `acad_add_box` |
| `Geometry.AddCylinder({base, radius, height, layer?})` | `{handle}` | `acad_add_cylinder` |
| `Geometry.AddSphere({center, radius})` | `{handle}` | **NEW** |
| `Geometry.AddCone({base, radius, height})` | `{handle}` | **NEW** |
| `Geometry.AddLine({start, end})` | `{handle}` | `acad_draw_line` |
| `Geometry.AddPolyline({points, closed})` | `{handle}` | `acad_draw_polyline` |
| `Geometry.AddCircle({center, radius})` | `{handle}` | `acad_draw_circle` |
| `Geometry.AddArc({center, radius, startAngle, endAngle})` | `{handle}` | **NEW** |
| `Geometry.AddText({insertion, text, height})` | `{handle}` | `acad_draw_text` |
| `Geometry.AddMText({insertion, width, text})` | `{handle}` | **NEW (works) ** |
| `Geometry.AddRectangle({lowerLeft, upperRight})` | `{handle}` | `acad_draw_rectangle` |
| `Geometry.Boolean({op, sourceHandles, otherHandles})` | `{handle}` | `acad_boolean` |
| `Geometry.Loft({sectionHandles, options?})` | `{handle}` | **NEW (replaces LISP)** |
| `Geometry.Revolve({profileHandle, axisStart, axisEnd, angleRadians})` | `{handle}` | **NEW (replaces LISP)** |
| `Geometry.Sweep({profileHandle, pathHandle})` | `{handle}` | **NEW (replaces LISP)** |
| `Geometry.Extrude({profileHandle, height})` | `{handle}` | **NEW** |
| `Geometry.Fillet({entityHandles, edges?, radius})` | `{handle}` | **NEW (replaces LISP)** |
| `Geometry.Chamfer({entityHandles, distance})` | `{handle}` | **NEW** |
| `Geometry.PressPull({faceSelectionRayPoint, distance})` | `{handle}` | **NEW** |

#### Entity manipulation

| Method | Returns | Replaces |
|---|---|---|
| `Entity.GetBoundingBox(handle)` | `{min, max}` | (was inline COM) |
| `Entity.SetColor({handle, colorIndex?, rgb?})` | `{handle}` | `acad_change_color` |
| `Entity.SetLayer({handle, layer})` | `{}` | **NEW** |
| `Entity.SetMaterial({handle, material})` | `{}` | **NEW** |
| `Entity.Delete(handle)` | `{deleted}` | **NEW** |
| `Entity.List({layer?, type?, limit?})` | `[{handle, type, layer, ...}]` | `acad_list_entities` |
| `Entity.Move({handle, displacement})` | `{}` | **NEW** |
| `Entity.Rotate({handle, basePoint, angleRadians, axis?})` | `{}` | **NEW** |

#### View, camera, visual style

| Method | Returns | Replaces |
|---|---|---|
| `View.SetPreset(preset)` | `{view}` | `acad_set_view` |
| `View.SetCustom({location, target, up?, lens?})` | `{}` | **NEW (replaces broken `_-VIEW _R`)** |
| `View.SaveCamera({name, location, target, lens?})` | `{name}` | **NEW (working save)** |
| `View.RestoreCamera(name)` | `{}` | **NEW (working restore)** |
| `View.ZoomExtents` | `{}` | `acad_zoom_extents` |
| `View.ZoomWindow({c1, c2})` | `{}` | **NEW** |
| `VisualStyle.Set(style)` | `{visualStyle}` | `acad_set_visual_style` |
| `VisualStyle.SetVariable({name, value})` | `{}` | **NEW** |

#### Materials (the centerpiece capability)

| Method | Returns | Notes |
|---|---|---|
| `Material.ListLibrary({family?})` | `[{name, family, thumbnailUri?}]` | Browses the AutoCAD Material Library |
| `Material.ImportFromLibrary(name)` | `{material, imported}` | Adds to drawing if not present |
| `Material.Create({name, color, roughness?, metallic?, ior?, transmission?, textureMap?})` | `{material}` | Custom PBR-ish material |
| `Material.AssignToLayer({layer, material})` | `{}` | Replaces COM `layer.Material = name` |
| `Material.AssignToEntity({handle, material})` | `{}` | |
| `Material.List` | `[{name, layers, entityCount}]` | |

#### Lights

| Method | Returns |
|---|---|
| `Light.AddPoint({position, intensity, color, name?})` | `{handle}` |
| `Light.AddSpot({position, target, intensity, hotspot, falloff, color, name?})` | `{handle}` |
| `Light.AddDistant({direction, intensity, color, name?})` | `{handle}` |
| `Light.SetSun({status, latitude, longitude, date, time, timezone})` | `{}` |
| `Light.List` | `[{handle, name, type, position, intensity}]` |
| `Light.Delete(handle)` | `{}` |

#### Render

| Method | Returns |
|---|---|
| `Render.ListPresets` | `[{name, samples, lighting}]` |
| `Render.ToFile({preset, view?, outputPath, width, height})` | `{outputPath, durationMs}` |

#### Layouts & plotting

| Method | Returns |
|---|---|
| `Layout.List` | `[{name, isCurrent}]` |
| `Layout.Create({name, paperSize?, plotter?})` | `{name}` |
| `Layout.SetActive(name)` | `{}` |
| `Layout.AddViewport({layout, center, width, height, view?, scale?})` | `{handle}` |
| `Layout.SetViewportView({handle, viewName})` | `{}` |
| `Layout.SetViewportScale({handle, scale})` | `{}` |
| `Layout.SetViewportLayerVisibility({handle, layer, visible})` | `{}` (per-viewport freeze) |
| `Plot.ToPdf({layout, outputPath, paperSize?})` | `{outputPath}` |

#### Export / Import

| Method | Returns |
|---|---|
| `Export.Fbx({outputPath, options?})` | `{outputPath}` |
| `Export.Gltf({outputPath, binary?, options?})` | `{outputPath}` |
| `Export.Stl({outputPath, layer?, selection?})` | `{outputPath}` |
| `Export.Dxf({outputPath, version?})` | `{outputPath}` |
| `Export.Png({outputPath, view?, width, height, visualStyle?})` | `{outputPath}` |
| `Import.RasterImage({path, position, scale, rotation?, layer?})` | `{handle}` |

#### Annotations & dimensions

| Method | Returns |
|---|---|
| `Dimension.AddLinear({p1, p2, dimLineLocation, rotation, layer?})` | `{handle}` |
| `Dimension.AddAligned({p1, p2, dimLineLocation, layer?})` | `{handle}` |
| `Dimension.AddRadius({circleHandle, leaderEndPoint})` | `{handle}` |
| `Dimension.AddAngular({...})` | `{handle}` |
| `Dimension.SetStyleVariable({name, value})` | `{}` |

#### System variables (sandboxed)

| Method | Returns |
|---|---|
| `Var.Get(name)` | `{value}` |
| `Var.Set({name, value})` | `{previous}` |
| `Var.SetMany([{name, value}])` | `{}` (atomic, all-or-nothing) |

---

## 5. Project structure

```
autocad-plugin/
├── README.md                          (build & install instructions)
├── TechniCadBridge.sln                (Visual Studio solution)
├── src/
│   ├── TechniCadBridge.csproj
│   ├── AssemblyInfo.cs                (NETLOAD entry point)
│   ├── PluginEntry.cs                 (IExtensionApplication impl)
│   ├── Server/
│   │   ├── JsonRpcServer.cs
│   │   ├── CommandQueue.cs
│   │   ├── AcadSyncContext.cs
│   │   └── Protocol.cs                (JSON-RPC 2.0 types)
│   ├── Handlers/
│   │   ├── DocumentHandler.cs
│   │   ├── LayerHandler.cs
│   │   ├── GeometryHandler.cs
│   │   ├── EntityHandler.cs
│   │   ├── ViewHandler.cs
│   │   ├── MaterialHandler.cs
│   │   ├── LightHandler.cs
│   │   ├── RenderHandler.cs
│   │   ├── LayoutHandler.cs
│   │   ├── ExportHandler.cs
│   │   └── DimensionHandler.cs
│   └── Util/
│       ├── PointConv.cs              (Vector3 ↔ double[3])
│       └── HandleResolver.cs         (handle string → DBObject)
├── tests/
│   ├── TechniCadBridge.Tests.csproj
│   └── HandlerTests.cs               (in-process, no AutoCAD required for unit-level)
├── packaging/
│   ├── install.ps1                   (NETLOAD on AutoCAD startup)
│   ├── uninstall.ps1
│   └── config.template.json
└── docs/
    ├── PROTOCOL.md                   (JSON-RPC method reference, regenerated from XML doc comments)
    └── DEVELOPER.md
```

### 5.1 Dependencies

- .NET 8 (matches AutoCAD 2026/2027's CLR target)
- `accoremgd.dll`, `acdbmgd.dll`, `acmgd.dll` (AutoCAD ObjectARX .NET assemblies — referenced as private, never copied)
- `StreamJsonRpc` 2.x (Microsoft) — proven JSON-RPC 2.0 implementation; thread-safe
- `Newtonsoft.Json` 13.x (already shipped with AutoCAD; reuse to avoid version conflicts)
- xUnit + Moq for unit tests
- `coverlet` for coverage

### 5.2 Project files (key snippets)

`TechniCadBridge.csproj`:

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net8.0-windows</TargetFramework>
    <Platforms>x64</Platforms>
    <UseWindowsForms>false</UseWindowsForms>
    <Nullable>enable</Nullable>
    <LangVersion>12.0</LangVersion>
    <ImplicitUsings>enable</ImplicitUsings>
    <CopyLocalLockFileAssemblies>false</CopyLocalLockFileAssemblies>
  </PropertyGroup>
  <ItemGroup>
    <Reference Include="accoremgd"><HintPath>$(AcadInstallDir)\accoremgd.dll</HintPath><Private>false</Private></Reference>
    <Reference Include="acdbmgd"><HintPath>$(AcadInstallDir)\acdbmgd.dll</HintPath><Private>false</Private></Reference>
    <Reference Include="acmgd"><HintPath>$(AcadInstallDir)\acmgd.dll</HintPath><Private>false</Private></Reference>
    <PackageReference Include="StreamJsonRpc" Version="2.18.48" />
  </ItemGroup>
</Project>
```

---

## 6. Lifecycle

### 6.1 Plugin startup (when AutoCAD launches)

1. AutoCAD calls `IExtensionApplication.Initialize()` on `PluginEntry`.
2. `PluginEntry` constructs the `JsonRpcServer`, loads
   `%APPDATA%\TechniCadBridge\config.json`, binds to TCP port (default
   7878) on `127.0.0.1`.
3. Server starts a background `AcceptLoop`. New clients get their own
   `JsonRpc` session that wraps the `CommandQueue`.
4. `Editor.WriteMessage` logs `[TechniCadBridge] listening on tcp://127.0.0.1:7878`
   so the user sees it in AutoCAD's command window.

### 6.2 Plugin command pump

A `CommandQueue` of `Func<Task<JToken>>` gets drained on the AutoCAD main
thread via `Application.Idle` event subscriptions. One command per idle
tick to keep the UI responsive.

### 6.3 Plugin shutdown

`IExtensionApplication.Terminate()` cancels the listener, closes open
client sessions cleanly, and drains the queue with a 5s timeout.

### 6.4 NETLOAD on startup

Manual: `NETLOAD <path-to>\TechniCadBridge.dll` in AutoCAD command line.
Automatic: install script writes a registry key
`HKCU\Software\Autodesk\AutoCAD\R26.0\ACAD-9001:409\Applications\TechniCadBridge`
with `LOADER` pointing at the DLL and `LOADCTRLS=2` (auto-load on
startup).

---

## 7. Python client side (refactor of `autocad-mcp/`)

### 7.1 New file: `autocad-mcp/plugin_client.py`

```python
class PluginClient:
    def __init__(self, host="127.0.0.1", port=7878):
        self._sock = socket.create_connection((host, port))
        self._rpc_id = 0
        self._lock = threading.Lock()

    def call(self, method: str, **params) -> Any:
        with self._lock:
            self._rpc_id += 1
            req = {"jsonrpc": "2.0", "id": self._rpc_id,
                   "method": method, "params": params}
            self._sock.sendall((json.dumps(req) + "\n").encode())
            line = self._readline()
            resp = json.loads(line)
        if "error" in resp:
            raise PluginError(resp["error"])
        return resp["result"]
```

### 7.2 `acad.py` becomes a thin facade

Each method in `Acad`:
1. Tries `self._plugin.call(...)` first
2. Falls back to existing COM path on `PluginUnavailable` (e.g. plugin
   not loaded yet)

This keeps backward compatibility — old workflows still work; new
workflows get the plugin's reliability.

### 7.3 `server.py` (FastMCP) needs no changes

The MCP tools `mcp__autocad__*` continue to work because they call into
`Acad`, which now transparently uses the plugin.

---

## 8. Phases / roadmap

### Phase 1 — Foundation (1 week, ~20 hours)

| Task | Outcome |
|---|---|
| 1.1 Solution scaffold + NETLOAD-able `IExtensionApplication` skeleton | DLL loads cleanly, prints "listening on" message in AutoCAD |
| 1.2 `JsonRpcServer` + `CommandQueue` + `AcadSyncContext` | `nc localhost 7878` and a hand-typed JSON request hits the main thread |
| 1.3 `DocumentHandler` (Status, New, Open, Save, Cancel) | Plugin can replace COM for these ops |
| 1.4 `LayerHandler` + `GeometryHandler` (the trivial ops: Box, Cylinder, Polyline, Boolean) | Plugin can build the home-office shell from scratch |
| 1.5 Python client (`plugin_client.py`) + facade in `acad.py` | Existing `build_kitchen.py` runs against the plugin with one config flag |

**Exit criterion:** Re-run `build_kitchen.py` and `build_living_room.py`
end-to-end against the plugin with zero `RPC_E_CALL_REJECTED` errors.

### Phase 2 — Materials & rendering (1 week, ~25 hours)

| Task | Outcome |
|---|---|
| 2.1 `MaterialHandler` — list library, import by name, assign to layer | We can call MATBROWSER's library from a Python script |
| 2.2 `LightHandler` — point/spot/distant + sun config | Sun + photometric lighting set entirely from script |
| 2.3 `RenderHandler.ToFile` | A single Python call produces `render-final.png` raytraced output |
| 2.4 `Export.Fbx` | Reliable FBX export — replaces the per-layer-STL workaround |
| 2.5 Per-layer material × view × resolution test matrix | Confidence that all 5 projects render correctly |

**Exit criterion:** A single Python script renders all four projects
(home office, kitchen, living room, future condo) at presentation
quality without any GUI clicks.

### Phase 3 — Layouts & plotting (1 week, ~20 hours)

| Task | Outcome |
|---|---|
| 3.1 `LayoutHandler` — create, set active, manage viewports | Programmatic ARCH-D layout |
| 3.2 `Layout.AddViewport` with per-viewport view, scale, layer freeze | Four-up presentation board (plan / iso / 2 elevations) |
| 3.3 `Plot.ToPdf` with proper plot configurations | PDF deliverable matches what AutoCAD's PLOT dialog produces |
| 3.4 Title-block block-reference insertion (block library) | Designer stamp + sheet number wired up |

**Exit criterion:** Each of the four projects has a `<project>-A-XXX.pdf`
plot output matching the brief's deliverable spec.

### Phase 4 — Hardening (1 week, ~15 hours)

| Task | Outcome |
|---|---|
| 4.1 Unit tests for every handler (in-proc, no AutoCAD) | Coverage >70% on handler logic |
| 4.2 Integration test runner (drives a real AutoCAD instance, runs all 5 projects, diffs output PNGs) | CI signal that a plugin update doesn't regress |
| 4.3 Crash recovery — if plugin throws, server stays up; client gets a clear error code | No more "AutoCAD froze" sessions |
| 4.4 Auto-load registry key + uninstall script | `install.ps1` and `uninstall.ps1` work first time on a clean machine |
| 4.5 PROTOCOL.md generated from XML doc comments | API reference always matches the code |

**Exit criterion:** New laptop → install AutoCAD 2026 → run
`packaging\install.ps1` → open Claude Code → run `build_kitchen.py` → 60
seconds later we have `kitchen.dwg` + render-final.png with zero manual
intervention.

---

## 9. Risks & mitigations

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| AutoCAD's render API is partially undocumented | Medium | High — Phase 2 can't ship without it | Prototype `RenderHandler.ToFile` in Phase 1 sprint as a spike before committing to Phase 2 schedule |
| Material library import varies by AutoCAD version (2026 vs 2027 SDK API drift) | Medium | Medium | Pin to AutoCAD 2027; document the 2026 fallback path in `DEVELOPER.md` |
| `Application.Idle` doesn't fire when AutoCAD is in a modal dialog | High | High — defeats the purpose | Combine with `WndProc` interception to bail out of modal states automatically |
| Plugin DLL conflicts with another installed plugin (assembly version mismatch) | Low | Medium | `CopyLocalLockFileAssemblies = false` + thorough binding redirect in `app.config` |
| User doesn't have admin rights | Medium | Low | NETLOAD doesn't require admin; only the registry auto-load key does — script falls back to manual NETLOAD instructions |
| Autodesk pushes a 2028 release that breaks the API | Low (unknown timing) | Medium | Pin AutoCAD version in `README`; spec versioning policy in `DEVELOPER.md` |

---

## 10. Acceptance tests

Plugin is "done" when these run green from a cold AutoCAD start:

1. **Kitchen full pipeline** — `python build_kitchen.py` produces a 141-entity .dwg, dimensioned plan PNG, photoreal Cycles render PNG, and ARCH-D PDF. No manual ESC required during the run.
2. **Living room re-render** — `python build_living_room.py` produces the same set of artifacts including the lofted lounge chairs, revolved lamp, swept drapery, and 16 photometric lights, and the saved HERO + EDITORIAL camera views actually produce the camera-set views (not the SWISO fallback).
3. **Home office spec docx** — `node build_word_doc.js` produces a Word doc with embedded photoreal AutoCAD-rendered (not just Conceptual) iso. Document validates with `pandoc` round-trip.
4. **Crash recovery** — `kill TechniCadBridge.dll` mid-render; AutoCAD stays alive, plugin restarts on next NETLOAD, next Python call succeeds.
5. **Cancel reliability** — script issues 1000 small ops with random `Cancel` calls interspersed; all return cleanly within 200 ms.

---

## 11. Open questions

These need rjain's input before we scaffold:

1. **Hosting.** Keep this plugin in `-callie-job` or move to a separate
   repo (`technijian-cad-bridge`)? My vote: separate repo so the
   AutoCAD plugin's release cycle isn't tied to Callie's design output.
2. **Scope creep.** Should the plugin also expose APIs for the other
   AutoCAD extensions Technijian uses (Map3D, Civil3D, Mechanical)? My
   vote: not in v1. Stay surgical; expand in v2 if the demand exists.
3. **License.** Public open-source or private repo? If public, MIT
   license — but understand any AutoCAD .NET project links against
   Autodesk's redistributable libraries which have their own EULA.
4. **Telemetry.** Worth logging command latencies for the plugin to a
   local file (`%APPDATA%\TechniCadBridge\trace.jsonl`)? Useful for
   debugging but a small disk-write hit per call.
5. **Plugin ↔ Blender bridge.** Should the plugin orchestrate the
   AutoCAD → Blender FBX → Cycles render pipeline directly (i.e. the
   plugin spawns Blender and waits)? Today this lives in
   `autocad-mcp/dwg_to_blender.py` on the Python side. My vote: keep
   on Python side — the plugin shouldn't manage subprocesses.

---

## 12. Out of scope (explicitly)

- Web-based remote control. The plugin is local TCP only; no
  authentication, no TLS. Lock down via firewall rules if remote needed.
- Multi-user collaboration. Single AutoCAD instance, single plugin,
  single client at a time (until v2).
- AutoCAD LT support. LT doesn't support .NET plugins.
- Mac AutoCAD. Mac AutoCAD's .NET API is a subset; we'd need a
  separate spec.

---

## 13. Effort & cost

- **Phase 1:** ~20 hours (scaffold + foundation handlers + Python facade)
- **Phase 2:** ~25 hours (materials + render + FBX export)
- **Phase 3:** ~20 hours (layouts + plotting)
- **Phase 4:** ~15 hours (hardening + CI + install)

**Total: ~80 hours.** At 2 hours/day evening pace, ~10 weeks elapsed.
Big-bang sprint: 2 weeks of focused day-job time.

Cost in license / tooling:
- Visual Studio 2022 Community (free)
- AutoCAD 2027 (existing trial — converts to subscription if used past
  trial)
- ObjectARX SDK 2027 (free download from Autodesk Developer Network,
  account signup required)
- StreamJsonRpc + Newtonsoft.Json (NuGet, free)
- xUnit + coverlet (NuGet, free)

**No new line-item spend.**

---

*End of v0.1 spec. Mark up directly in this file or open a Linear
ticket; treat unresolved comments as gating for Phase 1 kickoff.*

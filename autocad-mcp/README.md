# autocad-mcp

MCP server that drives a running AutoCAD instance over Windows COM.

## Tools

| Tool | What it does |
|---|---|
| `acad_status` | Is AutoCAD reachable? What's open? |
| `acad_new_drawing` | Start a new drawing (optional template path) |
| `acad_open_drawing` | Open a .dwg/.dxf |
| `acad_save` | Save, optionally Save-As |
| `acad_zoom_extents` | Zoom to the extents of all geometry |
| `acad_run_command` | Raw AutoCAD command string — escape hatch |
| `acad_draw_line` | Line from [x,y] to [x,y] |
| `acad_draw_polyline` | Lightweight polyline, optionally closed |
| `acad_draw_rectangle` | Closed rectangle polyline |
| `acad_draw_circle` | Circle by center + radius |
| `acad_draw_text` | Single-line text |
| `acad_list_entities` | Inspect model space contents |
| `acad_list_layers` | List layers + state |
| `acad_create_layer` | Add/update layer + color |
| `acad_set_active_layer` | Set current drawing layer |
| `acad_teach` | Mini-glossary for learning AutoCAD concepts |

## Design notes

- **Units on responses.** Every tool returns `{"ok": true, "data": ...}` or `{"ok": false, "error": "..."}` so Claude can branch cleanly.
- **Lazy connect.** The server tries to attach to a running AutoCAD on startup; if one isn't running, the first tool call launches it.
- **Prefer typed tools, fall back to `acad_run_command`.** The raw-command tool is deliberately included — AutoCAD has 1000+ commands and we won't wrap them all. When we hit a command twice via `acad_run_command`, we upgrade it to a typed tool.

## Growing the server

Add a method to [acad.py](acad.py) first (so the COM knowledge lives in one place), then expose it as an `@mcp.tool()` in [server.py](server.py). Keep tool docstrings tight — Claude reads them as the function signature.

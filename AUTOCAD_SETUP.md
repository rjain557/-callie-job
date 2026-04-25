# AutoCAD Setup — callie-job repo

Portable across any **Windows workstation with AutoCAD (full) + Python 3.10+**.
Not portable to macOS/Linux (AutoCAD COM is Windows-only).

This sets up the AutoCAD learning/drawing track that lives alongside the job-search pipeline in this repo. Both are independent — running setup here does not affect the pipeline.

## First-time setup on a new machine

```powershell
git clone https://github.com/rjain557/-callie-job
cd -callie-job
powershell -ExecutionPolicy Bypass -File scripts\setup-autocad.ps1
```

This creates `.venv/`, installs `pywin32` + `mcp`, and generates the AutoCAD COM typelib cache.

## Wire it into Claude Code

Nothing to do — [.mcp.json](.mcp.json) at the repo root tells Claude Code to run the server out of `.venv`. Restart Claude Code after the first setup so it picks up the new MCP server. First time you run a tool, Claude Code will prompt you to approve the `autocad` MCP server — approve it.

## Daily use

1. Open AutoCAD (any blank drawing — or the server will open one for you on first tool call).
2. Open this repo in Claude Code.
3. Ask: *"What's in the active drawing?"* — Claude should call `acad_status`.

## Project layout (AutoCAD track only)

| Path | Purpose |
|---|---|
| [autocad-mcp/](autocad-mcp/) | MCP server that drives AutoCAD |
| [autocad-mcp/acad.py](autocad-mcp/acad.py) | Thin COM wrapper around the AutoCAD Application object |
| [autocad-mcp/server.py](autocad-mcp/server.py) | FastMCP server exposing tools |
| [memory-autocad/](memory-autocad/) | Persistent memory for AutoCAD-related Claude sessions (see [memory-autocad/README.md](memory-autocad/README.md)) |
| [projects/](projects/) | Interior design project specs (briefs, drawing checklists, reference sketches) |
| [scripts/setup-autocad.ps1](scripts/setup-autocad.ps1) | One-shot environment setup |
| [.mcp.json](.mcp.json) | Claude Code MCP server registration (project-scoped, portable) |

(The repo also contains the job-search pipeline — see [CLAUDE.md](CLAUDE.md) — which is unrelated.)

## Troubleshooting

- **"AutoCAD.Application not registered"** — AutoCAD isn't installed, or is LT. Full AutoCAD required.
- **`pywin32` import errors in the venv** — re-run `scripts\setup-autocad.ps1`; the post-install step registers DLLs.
- **Claude Code doesn't see the `autocad` MCP server** — restart Claude Code after editing [.mcp.json](.mcp.json); confirm the approval prompt when it first tries to connect.
- **Tool hangs forever** — check AutoCAD; a modal dialog (e.g. "Save changes?") blocks COM. Close the dialog.
- **`python -m venv .venv` fails** — make sure Python 3.10+ is installed. Run `py --version` to confirm.

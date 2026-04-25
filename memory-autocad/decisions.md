# Decisions log

Short, dated entries. One decision per block.

---

## 2026-04-23 — Python + COM for the AutoCAD connector

**Decision:** Build an MCP server in Python using pywin32 COM automation, running out of a local `.venv` at the repo root.

**Why:** Fastest iteration loop, no AutoCAD plugin install/rebuild cycle, no Visual Studio dependency. AutoCAD's COM API is mature and stable.

**Alternatives considered:**
- .NET plugin loaded into AutoCAD via `NETLOAD` — deeper API access, but heavy tooling and slow iteration.
- AutoLISP scripts generated on the fly — awkward to get data back into Claude.
- Raw `.scr` script files — one-way, no feedback, no entity queries.

**Revisit if:** we need access to APIs that COM doesn't expose (some 2024+ features, custom Express Tools, some layout-grid APIs).

---

## 2026-04-23 — In-repo memory instead of user-scoped auto-memory

**Decision:** Keep project memory in `memory/` inside the repo (not in the user-scoped auto-memory at `C:\Users\rjain\.claude\projects\...`).

**Why:** User wants the project portable across workstations. Auto-memory is per-machine and won't travel. A pointer is still added to auto-memory so cross-conversation Claude knows to read the in-repo memory.

**Alternatives:** rely only on auto-memory (not portable); duplicate to both (sync burden).

# Solution Decision: MANUAL-obsidian-mcp

**Date:** 2026-03-24
**Decided by:** Human reviewer
**Chosen approach:** Approach 2 — Direct Filesystem Access

---

## Decision

The MCP server will read and write the Obsidian vault directly via the
filesystem using Python's `pathlib`. It will not depend on the Local REST API
plugin or require Obsidian to be running.

## Rationale

The user's workflow is one-directional: Claude (via MCP) builds and manages
the knowledge base, and Obsidian is used separately as a read-only viewer.
Because Obsidian is not running during MCP operations, there is no cache
inconsistency risk and no need for the Local REST API plugin. This makes
Approach 2 the simplest and most reliable fit.

## Alternatives Considered

| Approach | Why Not Chosen |
|----------|----------------|
| Approach 1 — Thin Proxy (REST API) | Requires Obsidian to be running; user does not want this constraint |
| Approach 3 — Hybrid | Adds significant complexity to handle a fallback the user does not need |

## Open Questions at Decision Time

- Exact location of `obsidian.json` on the user's Linux system (likely
  `~/.config/obsidian/obsidian.json` — to be confirmed during implementation)
- Whether `gitpython` or subprocess is preferred for git operations
  (Approach 2 doc listed `gitpython`; may be revised to subprocess in Plan.MD
  for simplicity)

## Risks Accepted

- Direct filesystem writes may cause a brief delay before Obsidian reflects
  changes on next open — accepted, as this is the intended workflow
- `gitpython` dependency has known edge cases — acceptable for personal use;
  can be swapped for subprocess if issues arise

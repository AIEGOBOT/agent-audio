# Repository Agent Instructions

Agent Audio is intended to remain agent-, model-, hardware- and use-case-independent.

## Architecture rules

- Keep MCP tools generic. Do not add game-engine-specific parameters to the core protocol.
- Keep Stable Audio implementation details behind backend/runtime modules.
- New hardware support should be added as a backend adapter, not scattered conditionals.
- Never bundle third-party model weights into this repository.
- Never bypass gated-model license or authentication flows.
- Prefer verified fallbacks over optimistic hardware claims.
- Windows, macOS and Linux behavior must be considered for installer changes.
- Skill instructions should use the open Agent Skills `SKILL.md` format whenever possible.

## Definition of done for installer changes

- `python -m compileall src install` passes.
- unit tests pass without requiring model weights.
- `--doctor` works without network access.
- an existing Cursor `mcp.json` is merged, never replaced.
- unsupported accelerators degrade to a documented backend.

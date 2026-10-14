# MCP SDK compatibility

Agent Audio currently supports `mcp>=1.30,<2`. Keep the same constraint in
`pyproject.toml` and `uv.lock`. This applies to fresh pip installs as well as
frozen uv installs. Dependabot major updates for MCP are ignored until a
deliberate migration is validated; minor and patch updates remain enabled.

PR #12 widens the range to `<3` and locks MCP 2.3.0. Its stdio test fails because
`mcp.server.fastmcp.FastMCP` was removed and `ClientSession` no longer accepts
the v1 `datetime.timedelta` timeout value. Do not merge that dependency-only PR.

Retaining v1 avoids changing the working tool protocol and inference pipeline.
Migrating to v2 is a separate option, but requires adapting MCPServer startup,
client timeout handling, tool schemas, structured/text results, and error
behavior. An import alias alone is insufficient evidence of compatibility.
Revisit this choice if v1 maintenance/security support or a needed feature
requires v2. This constraint is not a claim that v2 is supported.

Before widening the range, run the complete CI matrix on Ubuntu Python
3.11/3.12/3.13, Windows Python 3.12, and macOS Python 3.12. If both majors are
advertised, test both explicitly, including fresh installation and real stdio
initialize/list/call/error round trips. Keep dependency audit and CodeQL passing.

The regression suite checks dependency boundaries, real stdio status and input
rejection, and successful tool dispatch with a synthetic WAV backend. Existing
runtime tests exercise subprocess output handling and output preservation.
These model-free checks do not prove Stable Audio model inference, listening
quality, implicit Skill activation, or final game/video integration. Those
require the separate end-to-end acceptance workflow and installed model weights.

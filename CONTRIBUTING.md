# Contributing

Agent Audio is an early preview focused on local sound effects in game and
video work. Read [project direction](docs/project-direction.md) before proposing
new backends, model selection or engine-specific integration. Small, reproducible
fixes and first-use reports are especially useful.

## Report an issue or an experience

Search [existing issues](https://github.com/AIEGOBOT/agent-audio/issues), then
choose the bug-report or experience-report template. English and Korean reports
are welcome; repository documentation remains in English.

Include your OS, available RAM, CPU/GPU, client/version, Agent Audio commit and
selected backend. Describe the requested task and the first failing step.
Distinguish installation, MCP connection, WAV generation, automatic Skill use,
project integration and listening quality. Successful reports are useful too;
do not mark untested layers as passed.

Share only relevant, reviewed excerpts. Replace personal paths with placeholders
and omit credentials, full client configuration, private prompts, model weights
and unreviewed logs. Follow [SECURITY.md](SECURITY.md) for security concerns.

## Develop and verify

Use a Git checkout and a dedicated environment. This preview's installer needs
the repository's `install/`, `skills/` and source files; the documented user
installation path is the Git checkout, not a standalone package-index install.

```text
uv sync --frozen
uv run --frozen ruff check src install tests
uv run --frozen ruff format --check src install tests
uv run --frozen python -m compileall -q src install
uv run --frozen pytest -q
uv run --frozen python install/bootstrap.py --doctor
```

The model-free checks do not need model weights. Doctor inspects prerequisites;
it does not perform inference or verify every dependency. A machine without a
runtime can still run these checks. Never accept model terms for another user.

For real generation and Skill changes, follow
[end-to-end validation](docs/end-to-end-validation.md). Keep raw records and
generated media outside the checkout. Record skipped tests and environmental
limits. An explicit standalone MCP probe does not prove discovery in a fresh
application chat or automatic Skill use.

## Submit a focused pull request

- Explain the user-visible problem, resulting behavior and checks actually run.
- Preserve existing settings, Skills, models, runtimes and outputs; report
  conflicts instead of deleting or resetting them.
- Keep MCP interfaces generic and backend-specific behavior in backend/runtime
  modules. Do not add paid-cloud fallback or unsupported acceleration claims.
- Include regression coverage for meaningful behavior changes. Documentation-only
  edits need accurate commands and working links, not tests that restate prose.
- Keep model weights, generated media, credentials and private logs out of Git.

Dependency updates need the same review as other code changes. In particular,
a passing check on the current branch does not verify a proposed MCP SDK major
upgrade. See [AGENTS.md](AGENTS.md) for the working contract and
[ARCHITECTURE.md](ARCHITECTURE.md) for module boundaries.

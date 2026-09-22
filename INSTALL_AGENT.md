# Agent Installation Protocol

This file is written for AI coding agents.

Your objective is to install Agent Audio with as little manual work as possible while preserving user control over licenses, credentials and privileged system changes.

## Non-negotiable rules

1. Do not accept Stability AI, Gemma, Hugging Face or any other third-party terms on the user's behalf.
2. Do not expose or print authentication tokens into chat when avoidable.
3. Do not replace an existing MCP configuration wholesale. Merge safely and create a backup before editing JSON config files.
4. Do not require ComfyUI.
5. Prefer a user-local installation; avoid administrator/root privileges unless they are genuinely required.
6. If accelerated inference setup fails, fall back to a supported portable backend instead of leaving the installation broken.
7. Report the backend actually installed. Never claim CUDA, XPU or Metal acceleration unless it was verified.

## 1. Inspect the repository

Read:

- `README.md`
- `skills/audio-production/SKILL.md`
- `models/registry.json`

## 2. Detect the environment

Determine:

- operating system
- CPU architecture
- GPU vendor(s)
- whether NVIDIA tooling is available
- whether Apple Silicon is present
- whether Intel graphics are present
- installed agent clients (`codex`, `claude`, Cursor)
- Python and `uv` availability

Do not guess hardware support from the GPU name alone.

## 3. Prepare Python tooling

Preferred runtime is Python 3.11+ and `uv`.

If `uv` is missing, install it with the platform's normal user-level method. If that requires a privileged package-manager action, ask the user before escalating privileges.

From the repository root run:

```text
uv sync
```

## 4. Run diagnostics

Run:

```text
uv run python install/bootstrap.py --doctor
```

Review the selected backend and any warnings.

## 5. Install Stable Audio runtime

Run:

```text
uv run python install/bootstrap.py --runtime-only
```

The bootstrapper installs Stability AI's official `stable-audio-3` runtime under the user's Agent Audio data directory.

If model access requires authentication or license acceptance, stop at that point and ask the user to complete/approve it. Resume only after the user has acted.

### Backend policy

- Apple Silicon: prefer the official MLX optimized runtime.
- Other systems: use the official TFLite/LiteRT CPU runtime as the portable baseline.
- NVIDIA acceleration is an extension point; use it only if this repository's validated accelerated adapter says it is supported on the current OS.
- Intel XPU acceleration is experimental until explicitly enabled by a validated adapter. Intel machines must remain functional through the CPU backend.

## 6. Register MCP and Skill

Run:

```text
uv run python install/bootstrap.py --register-only
```

The bootstrapper should register what it can automatically.

Expected user-level skill destinations:

- Codex: `~/.agents/skills/audio-production/`
- Claude Code: `~/.claude/skills/audio-production/`
- Cursor: `~/.cursor/skills/audio-production/`

The same source Skill must be used for all clients. Do not maintain divergent copies in the repository.

Expected MCP behavior:

- Codex: register a user-level stdio MCP named `agent-audio` using the native Codex MCP command when available.
- Claude Code: register a user-level stdio MCP named `agent-audio` using the native Claude Code MCP command when available.
- Cursor: safely merge an `agent-audio` entry into `~/.cursor/mcp.json`.

If an agent is already configured, do not duplicate the entry.

## 7. Restart/reload clients when necessary

A client may need a fresh session to discover a newly added MCP server or skill. Restart only the relevant client if needed.

## 8. Verify

First call `audio_status` through MCP.

Then generate a small verification asset such as:

```text
A clean cinematic metallic impact, isolated one-shot, no music, no voice.
```

Save it to a temporary/test output directory. Verify that a non-empty WAV is produced.

Do not add test audio to the user's active project unless requested.

## 9. Report completion

Report only concrete facts:

- installed backend
- model/runtime readiness
- agents registered
- skill registration status
- MCP verification result
- any fallback in use

If something remains unsupported, say exactly what and keep the working fallback enabled.

# Agent Audio

Universal local audio generation for AI coding agents.

Agent Audio exposes Stable Audio 3 through an MCP server and ships a portable Agent Skill that can be discovered by Codex, Claude Code, Cursor, and other Agent Skills/MCP-compatible clients.

## Goal

The intended installation flow is deliberately agent-first:

```text
User gives an AI coding agent this GitHub repository URL
        ↓
Agent reads INSTALL_AGENT.md
        ↓
Agent detects OS / hardware / installed clients
        ↓
Agent installs the local runtime
        ↓
Agent registers the MCP server + audio-production skill
        ↓
User asks for a larger task
        ↓
Agent invokes audio-production automatically when audio is materially useful
```

No ComfyUI installation is required.

## Current status

This repository is an early v0.1 scaffold.

Working design targets:

- Windows, macOS and Linux.
- NVIDIA, Intel and Apple hardware without making the MCP protocol hardware-specific.
- Codex, Claude Code and Cursor first; additional MCP/Agent Skills clients can be added as adapters.
- Stable Audio 3 Medium as the default high-quality model.
- Portable CPU fallback through Stability AI's official TFLite/LiteRT implementation.
- Apple Silicon acceleration through Stability AI's official MLX implementation.

Acceleration roadmap:

- NVIDIA CUDA / TensorRT: backend interface reserved; automatic cross-platform setup still needs validation, especially on Windows.
- Intel XPU: backend interface reserved; until validated, Intel systems use the portable CPU runtime rather than pretending XPU acceleration is supported.

## Install with an AI agent

Give your coding agent this repository URL and say:

> Install this project. Follow `INSTALL_AGENT.md` exactly. Register both the MCP server and the `audio-production` skill for this agent. Do not accept model licenses on my behalf.

The agent should handle the rest.

## Manual developer setup

```bash
git clone <this-repository-url>
cd agent-audio
uv sync
uv run python install/bootstrap.py --doctor
```

To register detected agents without installing the Stable Audio runtime:

```bash
uv run python install/bootstrap.py --register-only
```

To install the runtime and register detected agents:

```bash
uv run python install/bootstrap.py
```

## MCP tools

The initial MCP server exposes:

- `audio_status` — inspect platform, hardware and runtime readiness.
- `generate_audio` — generate a WAV using the selected Stable Audio backend.

The MCP surface intentionally does not contain Unity/game-specific concepts. Games, videos, applications, websites, film, advertising and general media workflows all use the same audio layer.

## Model licenses

Model weights are **not** included in this repository.

Stable Audio 3 Medium is distributed separately by Stability AI and is subject to the Stability AI Community License. It also includes T5Gemma components subject to Gemma terms. The installer must never silently accept those terms for the user.

See `THIRD_PARTY_NOTICES.md`.

## Project layout

```text
agent-audio/
├─ INSTALL_AGENT.md
├─ AGENTS.md
├─ skills/audio-production/
├─ src/agent_audio/
├─ install/bootstrap.py
├─ models/registry.json
└─ tests/
```

## License

Agent Audio source code is MIT licensed. Third-party models and runtimes keep their own licenses.

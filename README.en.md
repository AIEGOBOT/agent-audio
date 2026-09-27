# Agent Audio

Universal local audio generation for AI coding agents.

[한국어 (default)](README.md) | English

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

This repository is an early v0.1 release. Independent installation and real
3-second, 44.1 kHz stereo WAV generation through MCP were verified on Windows
using the TFLite/LiteRT CPU backend. Model-free CI passed on Windows, macOS and
Linux, with 45 tests in each of five Python/OS combinations, plus dependency
auditing and CodeQL. Real MLX generation still needs Apple hardware validation;
model-free CI does not establish model inference support on every platform.

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

The agent should follow the installation guide and report any configuration
conflicts or required model access. Existing settings are preserved.

## Manual developer setup

Requires Git, Python 3.11+ and uv. The separate audio runtime uses Python 3.12.

```bash
git clone https://github.com/AIEGOBOT/agent-audio.git
cd agent-audio
uv sync --frozen
uv run --frozen python install/bootstrap.py --doctor
```

To register detected agents without installing the Stable Audio runtime:

```bash
uv run --frozen python install/bootstrap.py --register-only
```

To install the runtime and register detected agents:

```bash
uv run --frozen python install/bootstrap.py
```

The default data directory is `~/.agent-audio`: the runtime lives in
`runtime/stable-audio-3/`, its models in `optimized/<backend>/models/`, the private
model cache in `cache/huggingface/`, and generated audio in `output/`. Set
`AGENT_AUDIO_HOME` before installation to choose a separate data directory; new
MCP registrations retain it. The MCP application uses the repository's `.venv`;
the runtime uses its own `optimized/<backend>/.venv`.

Conflicting Skills, runtime checkouts and MCP entries are preserved and reported.
Legacy MCP entries without Python's `-I` need a reviewed migration. Runtime and
model revisions are pinned; TFLite model downloads also use SHA-256 verification.
See [security boundaries](SECURITY.md) for limitations and configuration handling.

## MCP tools

The initial MCP server exposes:

- `audio_status` — inspect platform, hardware and runtime readiness.
- `generate_audio` — generate a WAV using the selected Stable Audio backend.

The MCP surface intentionally does not contain Unity/game-specific concepts. Games, videos, applications, websites, film, advertising and general media workflows all use the same audio layer.

`audio_status` includes the runtime Python and model paths. For `generate_audio`,
omit `output_path` to get a unique WAV in the default output folder, or specify a
new `.wav` path. Existing outputs are never overwritten. The output filesystem
must support hardlinks. Duration must be greater than zero and at most 380
seconds; long CPU requests may exceed the 540-second inference timeout.

## Development checks

These checks do not require model weights. Doctor also works offline.

```bash
uv run --frozen ruff check src install tests
uv run --frozen ruff format --check src install tests
uv run --frozen python -m compileall -q src install
uv run --frozen pytest -q
uv run --frozen python install/bootstrap.py --doctor
```

## Model licenses

Model weights are **not** included in this repository.

Stable Audio 3 Medium is distributed separately by Stability AI and is subject to the Stability AI Community License. It also includes T5Gemma components subject to Gemma terms. The installer must never silently accept those terms for the user.

See [third-party notices](THIRD_PARTY_NOTICES.md).

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

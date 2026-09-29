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

Agent Audio installs a dedicated runtime and models without requiring ComfyUI,
Stability Matrix, or an existing Stable Audio environment.

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

> Install this project. Read INSTALL_AGENT.md first and follow its instructions. Inspect my OS, hardware, Python, uv and installed agent clients. Install the dedicated runtime and models, register both the MCP server and audio-production Skill, and verify a short WAV through MCP. Preserve existing settings and do not accept model licenses on my behalf.

The agent should follow the installation guide and report any configuration
conflicts or required model access. Existing settings are preserved.

## Disk space and memory

These figures apply to the default **Windows x64 / TFLite CPU / Stable Audio 3
Medium** configuration. Planning recommendations are not verified minimum specs.

| Item | Planning guidance / measurement |
|---|---|
| Free disk space before installation | **25 GB or more recommended**, allowing for temporary downloads, package caches, model copies and additional outputs |
| Model downloads | Four default weights total **7.36 GB (6.86 GiB)**; runtime and Python packages are additional |
| Installed file sizes | Dedicated data directory, generated native cache and MCP venv: **8.15 GB (7.59 GiB)** with hardlinks counted once |
| System RAM | **32 GB class recommended**, matching the tested Windows host; 8/16 GB minimum configurations have not been validated |
| Generation memory | Inference process peak Working Set: **11.56 GiB** for one 3-second generation; OS/editor/other applications are additional |
| GPU / VRAM | No dedicated GPU or VRAM required for the current CPU backend |

The model directory and cache share hardlinks where possible. Summing both
directory sizes counts weights twice: 15.51 GB in this installation. Copying
instead of hardlinking increases storage use. The installed-size figure excludes
the separate uv cache, base Python, external output folders and filesystem
overhead. Disk GB is decimal; GiB is binary.

Memory was measured on 2026-09-28 with an existing native cache and one 3-second
request. It is not a first-run or long-generation maximum. Apple Silicon MLX
storage and unified memory requirements need separate validation; do not apply
the CPU numbers to MLX. See [measurement details](docs/resource-requirements.md).

## Manual developer setup

Requires Git, Python 3.11+ and uv. The separate audio runtime uses Python 3.12.

```bash
git clone https://github.com/AIEGOBOT/agent-audio.git
cd agent-audio
uv sync --frozen
uv run --frozen python install/bootstrap.py --doctor
```

After reviewing diagnostics, install the runtime and models, then register
detected clients:

```bash
uv run --frozen python install/bootstrap.py --runtime-only
uv run --frozen python install/bootstrap.py --register-only
```

Use `--register-only` by itself when the runtime is already prepared.

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

Skill destinations for detected clients:

| Client | Skill directory |
|---|---|
| Codex | `~/.agents/skills/audio-production/` |
| Claude Code | `~/.claude/skills/audio-production/` |
| Cursor | `~/.cursor/skills/audio-production/` |

Open a fresh client session if it does not discover the new MCP server or Skill.
Any required authentication or license acceptance must be completed by the user.

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

Example arguments for a 3-second effect:

```json
{
  "prompt": "Heavy cinematic metallic robot impact, dense mechanical body, sharp transient, subtle electrical crackle, isolated sound effect, no voice, no music",
  "seconds": 3
}
```

These two MCP tools do not expose every capability of the upstream model.

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

## Documentation and project layout

- [Agent installation guide](INSTALL_AGENT.md): inspect, install, register and verify.
- [Repository instructions](AGENTS.md): architecture rules and required checks.
- [Security boundaries](SECURITY.md): configuration preservation and execution limits.
- [Resource measurements](docs/resource-requirements.md): disk and memory guidance.
- [Third-party notices](THIRD_PARTY_NOTICES.md): separate model and runtime terms.

```text
agent-audio/
├─ INSTALL_AGENT.md
├─ AGENTS.md
├─ SECURITY.md
├─ docs/resource-requirements.md
├─ skills/audio-production/
├─ src/agent_audio/
├─ install/bootstrap.py
├─ models/registry.json
├─ tests/
└─ .github/workflows/
```

## License

Agent Audio source code is [MIT licensed](LICENSE). Third-party models and runtimes keep their own licenses.

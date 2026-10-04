# Agent Audio

**Give your coding agent local audio generation for games and videos.**

Agent Audio provides an MCP server and an Agent Skill, without requiring ComfyUI
or a paid audio-generation API. It installs its own runtime and uses Stable
Audio 3 Medium to generate audio on your computer.

Ask your agent to build or edit something, with useful sound effects handled
as part of the task. The goal is to review the finished result, not manage a
separate audio-production workflow.

**Early preview (v0.1).** Short audio generation has been demonstrated in the
[environments below](#current-status). Automatic use during game/video work and
listening quality still need end-to-end validation.

[Install](#install-with-an-ai-agent) · [Usage](#using-agent-audio) ·
[Support and limits](#current-status) · [Update](#updating-an-existing-installation) ·
[Get help](#troubleshooting-and-help)

## Before you install

Use a local coding agent with command execution and configuration access.
Codex, Claude Code and Cursor are the initial registration targets. Your agent
can check Git, Python 3.11+ and `uv`; the audio runtime uses Python 3.12.

<a id="disk-space-and-memory"></a>

| Environment | Plan for |
|---|---|
| Windows CPU setup | **25 GB or more free disk space and a 32 GB-class RAM system recommended.** Model downloads are about **7.36 GB**; packages and caches are additional. No dedicated GPU is required. |
| Apple Silicon setup | A short generation is reported on a **24 GiB** Mac, with **6.88 GB** of MLX model files. Total installation size and peak memory have not been measured. |

These are planning guidance and observations, **not verified minimum specs**.
Smaller machines and longer generations need separate validation. See
[resource measurements](docs/resource-requirements.md) for the full conditions.

Local generation has **no audio-service subscription or per-generation API fee**.
Agent subscriptions, hardware and electricity are separate. You must accept any
required model terms and complete authentication yourself; see
[licenses](#license). Initial installation downloads the runtime and models.

## Install with an AI agent

Paste this into your coding agent:

```text
Install Agent Audio from https://github.com/AIEGOBOT/agent-audio.
Read INSTALL_AGENT.md first and follow its instructions.
Check my OS, hardware, RAM, disk space, Python, uv and installed agent clients.
Install the dedicated runtime and models, then register the MCP server and
audio-production Skill. Preserve existing settings and report conflicts.
Do not accept model licenses or bypass permissions on my behalf.
Verify a short WAV through MCP and report what worked, what was not tested,
and any remaining steps I need to complete.
```

The agent should report the installed backend, client registration results and
test WAV path. If the client does not discover the new tools or Skill, start a
fresh session. Installation permissions, credentials and license acceptance
remain under your control.

Already installed? See [updating](#updating-an-existing-installation).
Prefer commands? See [manual setup](#manual-developer-setup).

<a id="goal"></a>

## Using Agent Audio

After setup, work in your game or video project and make an ordinary production
request. For example:

**Game task**

> Finish the enemy hit reaction and victory feedback in this small game.
> Keep the existing visual style and make the feature ready to play.

**Video task**

> Edit these clips into a 20-second product teaser with clean transitions and
> a finished end card, using the tools already available in this project.

These are examples of intended use, not validated demos. The Skill guides the
agent to reuse suitable audio, generate missing sounds when useful, and connect
them to the requested work. A separate sound request, audio-plan approval or
candidate-selection step is not the default workflow. Explicit sound requests
also work through the same tools.

The agent needs access to the project and appropriate editing tools to apply
the files. It should respect existing assets, intentional silence and requests
for no audio. The MCP server generates WAVs; it is not a game engine or video
editor, and the Skill does not guarantee that every agent will invoke it.

## Current status

| Environment or client | Current implementation and evidence |
|---|---|
| Windows | TFLite/LiteRT CPU is the default. Independent installation and a 3-second, 44.1 kHz stereo WAV through MCP are documented. |
| Apple Silicon macOS | MLX is selected. A user-provided report dated 2026-10-03 records a 3-second WAV on an M5 Pro with 24 GiB memory via a standalone stdio MCP client. |
| Linux and other CPU environments | The installer selects the CPU path outside Apple Silicon. Linux has model-free CI coverage; this is not verified model inference support. |
| NVIDIA / Intel graphics | The current default remains CPU; CUDA/TensorRT and Intel XPU acceleration are not enabled as validated automatic paths. |
| Codex / Claude Code / Cursor | MCP and Skill registration are implemented. Registration alone does not establish fresh-session discovery, automatic use or completed project integration. |

See the [Windows measurements](docs/resource-requirements.md) and
[macOS report](docs/macos-mlx-validation.md) for conditions and evidence limits.
Model-free CI runs on Windows, macOS and Linux. A valid WAV or passing CI does
not establish listening quality or successful game/video integration; those
remain separate [end-to-end checks](docs/end-to-end-validation.md).

### Known limits

The current interface is **text-to-WAV generation**, not audio-to-audio editing,
inpainting or continuation. Nonempty negative prompts are rejected; describe
the desired sound in the main prompt. Existing output files are not overwritten,
and the output filesystem must support hardlinks.

CPU generation can be slow, and long requests can hit the 540-second inference
timeout. Start with short sounds. Other models, accelerators and client
combinations are directions to validate, not blanket support promises.

## Updating an existing installation

**Updating the Git checkout does not update an installed Skill copy.** Ask your
agent to preserve local changes, update the checkout and compare the complete
installed `audio-production` folder with the repository version.

Review and authorize any Skill replacement. Keep the old copy outside all Skill
discovery folders, preserve customizations, then register the new copy and start
a fresh session. Do not reinstall models just to refresh a Skill. Runtime and
MCP conflicts need separate review, not deletion of existing environments or
unrelated settings. Your agent can follow the
[detailed update procedure](docs/end-to-end-validation.md#existing-installations).

## Troubleshooting and help

| Symptom | First check |
|---|---|
| Tools or Skill are missing | Start a fresh client session and ask the agent to check that client's MCP and Skill registration outcomes. |
| Setup reports a conflict | Review the existing paths and settings. A conflict means they were preserved, not that they should be deleted. See [updating](#updating-an-existing-installation). |
| Models are missing or access is denied | Let the agent identify the missing files or access step. Complete required authentication and model-license acceptance yourself. |
| Generation fails or times out | Try a short request and inspect the reported backend and local error log. `audio_status` reports prerequisites, not a successful generation test. |
| A WAV exists but is not used in the project | Check the agent's access to the project and its editing tools. File generation and final integration are separate steps. |

Search [existing issues](https://github.com/AIEGOBOT/agent-audio/issues) or
[report a problem](https://github.com/AIEGOBOT/agent-audio/issues/new). Include OS,
RAM, CPU/GPU, client/version, Agent Audio commit, backend, reproduction steps
and the exact error. State whether setup, generation or integration failed.

Review logs before sharing. **Do not post credentials, full client configuration,
private prompts or personal paths.** Follow [SECURITY.md](SECURITY.md) for security
concerns rather than posting sensitive details publicly.

<a id="model-licenses"></a>

## License

Agent Audio source code is [MIT licensed](LICENSE). Model weights are not
included in this repository. Stable Audio 3 Medium is distributed separately
under Stability AI's Community License, with T5Gemma components subject to Gemma
terms. You must review applicable model terms; the source-code license does not
replace them. See [third-party notices](THIRD_PARTY_NOTICES.md).

## Technical and developer reference

### What this project provides

Agent Audio supplies dedicated setup, MCP/client registration, runtime and file
management, and the audio-production Skill. Stability AI supplies the models and
inference implementations; the MCP Python SDK supplies the protocol framework.
The calling agent and its project tools handle final integration.

This is an integration tool, not a newly trained model. See
[architecture](ARCHITECTURE.md) and [project direction](docs/project-direction.md).

### Manual developer setup

Requires Git, Python 3.11+ and `uv`. Review [INSTALL_AGENT.md](INSTALL_AGENT.md)
for permissions, resource checks and model access first.

```bash
git clone https://github.com/AIEGOBOT/agent-audio.git
cd agent-audio
uv sync --frozen
uv run --frozen python install/bootstrap.py --doctor
```

After reviewing diagnostics:

```bash
uv run --frozen python install/bootstrap.py --runtime-only
uv run --frozen python install/bootstrap.py --register-only
```

Use `--register-only` alone when the runtime is prepared, or run bootstrap
without flags for both steps. Data defaults to `~/.agent-audio`; set
`AGENT_AUDIO_HOME` before installation to choose another location. Outputs
are in its `output/` folder. See [INSTALL_AGENT.md](INSTALL_AGENT.md) for paths,
client registration and per-client conflict handling, and [SECURITY.md](SECURITY.md)
for runtime/model pinning and file-preservation details.

### MCP tools

| Tool | Purpose |
|---|---|
| `audio_status` | Inspect platform, hardware, backend, runtime/model paths and readiness. |
| `generate_audio` | Generate a WAV using the selected Stable Audio backend and return its path. |

Omit `output_path` for a unique default output, or choose a new `.wav` path.
Duration must be greater than zero and at most 380 seconds, subject to the
540-second inference timeout. `runtime_ready` checks files and model headers,
not successful inference. The separate `readiness` object reports checkout
verification and unperformed checksum, dependency-health and generation checks.
`capabilities.negative_prompt` is false under the current CFG 1.0 policy;
nonempty negative prompts are rejected.

```json
{
  "prompt": "Heavy metallic impact, sharp transient, isolated sound effect, no voice, no music",
  "seconds": 3
}
```

### Development checks

These checks do not require model weights; doctor also works offline.

```bash
uv run --frozen ruff check src install tests
uv run --frozen ruff format --check src install tests
uv run --frozen python -m compileall -q src install
uv run --frozen pytest -q
uv run --frozen python install/bootstrap.py --doctor
```

### Documentation and project layout

| Reader | Start here |
|---|---|
| Installing agent | [INSTALL_AGENT.md](INSTALL_AGENT.md) |
| User checking resource needs | [Resource measurements](docs/resource-requirements.md) |
| Contributor | [Repository instructions](AGENTS.md) and [architecture](ARCHITECTURE.md) |
| Maintainer validating real work | [Project direction](docs/project-direction.md) and [end-to-end validation](docs/end-to-end-validation.md) |
| Comparing models | [Small-SFX versus Medium benchmark](benchmarks/sfx_model_compare/README.md) |

Source is in `src/agent_audio/`, setup starts at `install/bootstrap.py`, the
portable Skill is in `skills/audio-production/`, and regression tests are in
`tests/`. Keep generated media and model weights outside Git.

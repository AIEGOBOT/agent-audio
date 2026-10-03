# macOS MLX installation and generation record

This is an English summary of the user-provided `agent-audio-install-report.md`,
dated 2026-10-03 (Korea time). It records reported observations, not a new test
performed by the reviewer. The source report was checked against Agent Audio
commit `651c0057757ccd3dbd52e076892b7ea1ed0fcac8`, available on `main` at review
time. Runtime/model pins, model filenames and installation paths agree with
that implementation. Personal paths are normalized below.

The original MCP script, log and WAV remain on the reporting Mac and were not
provided with the report. Hardware, package versions and generation results
were not independently remeasured. No model weights or private configuration
are included in this record.

## Reported environment and installation

| Item | Reported value |
|---|---|
| Host | Mac mini, Apple M5 Pro, 24 GiB unified memory |
| OS / architecture | macOS 27.0.1 / arm64 |
| Agent Audio | 0.1.0, commit `651c0057757ccd3dbd52e076892b7ea1ed0fcac8` |
| MCP application / runtime Python | 3.14.8 / 3.12.15 |
| uv / MLX | 0.12.22 / 0.32.3 |
| Device check | Metal available; MLX default device `Device(gpu, 0)` |
| Model | Stable Audio 3 Medium |
| Runtime commit | `779434a908193105335fd8d833418603625b2859` |
| Model revision | `da6edc54ddba10bfd79a077102ded687f80e882b` |
| Data root | `~/.agent-audio` |
| Runtime | `~/.agent-audio/runtime/stable-audio-3` |
| Runtime Python | `<runtime>/optimized/mlx/.venv/bin/python` |
| Models | `<runtime>/optimized/mlx/models/mlx` |
| Model cache | `~/.agent-audio/cache/huggingface/hub` |

A dedicated environment was installed without reusing an existing audio runtime.
Codex MCP registration and `~/.agents/skills/audio-production/SKILL.md`
installation succeeded, with existing configuration preserved and no reported
conflicts. The registered command used the repository's `.venv/bin/python -I -m
agent_audio.mcp_server`, `AGENT_AUDIO_HOME` and a 600-second tool timeout.
Claude Code and Cursor were not detected and were not registered.

## Reported checks

| Check | Result |
|---|---|
| Model-free unit tests | 98 passed in 8.27 seconds |
| Runtime dependency check | 23 packages checked; no compatibility errors |
| Doctor | `runtime_ready: true`, no warnings |
| Runtime provenance | `upstream_checkout: verified` |
| MCP initialization / tool listing | Successful; `audio_status`, `generate_audio` |
| MCP generation | Successful; `isError: false` |

The unit-test result is separate from the real generation test. The report does
not include results for all repository static checks or an explicit offline
doctor run. Doctor readiness alone does not check inference or model checksums.

## Reported generation

A standalone client connected to the installed stdio MCP server and requested:

```json
{
  "prompt": "A clean cinematic metallic impact, isolated one-shot, no music, no voice.",
  "seconds": 3
}
```

| Metric | Reported result |
|---|---|
| Generation elapsed time | 8.02 seconds |
| Output | `~/.agent-audio/output/agent-audio-c181a5f35c7f41f9a384fbbfbaa09474.wav` |
| WAV size / duration | 529,244 bytes / 3.0 seconds |
| Audio format | 44,100 Hz, stereo, PCM 16-bit |
| Samples | All finite; 209,631 nonzero sample values |
| Peak absolute amplitude / RMS | Approximately 0.9175 / 0.0879 |

These values are consistent with a non-silent, 3-second stereo PCM WAV whose
samples do not reach full scale. They do not establish audible quality or
prompt adherence. Listening was not performed. Timing boundaries and cache
state were not recorded; the elapsed time is a single observation.

## Model storage and integrity

| File | Bytes |
|---|---:|
| `dit_medium_f16.npz` | 2,907,300,946 |
| `same_l_decoder_f32.npz` | 1,704,311,976 |
| `same_l_encoder_f32.npz` | 1,704,313,504 |
| `t5gemma_f16.npz` | 567,443,068 |
| **Total** | **6,883,369,494 (6.88 GB / 6.41 GiB)** |

This is model file size, not total installation consumption. Peak unified memory
and total installed storage were not measured. See [resource guidance](resource-requirements.md).

The installer resolves the pinned revision and checks installed files against
cache content. MLX has no independently pinned SHA-256 reference manifest.
The report states that downloads succeeded without authentication and that no
third-party terms were accepted on the user's behalf. This does not change the
project's license and authentication boundaries in [SECURITY.md](../SECURITY.md).

## Scope and follow-up evidence

The report establishes a user-reported short text-to-audio success through MCP.
It does not verify direct MCP invocation or Skill discovery in a fresh Codex
chat, long music generation, repeatability, or smaller-memory configurations.
Audio editing, inpainting and continuation are not exposed by the current MCP
interface, even though the upstream model has these capabilities.

The report identifies `~/.agent-audio/tests/mcp_smoke_test.py` and
`~/.agent-audio/mcp-smoke-test.log` as evidence on the reporting Mac. These are
external artifacts, not files shipped by this repository. A stronger follow-up
would retain a sanitized script/log and WAV checksum, test a fresh Codex chat,
and record listening results, timing scope and resource measurements. See the
[installation verification procedure](../INSTALL_AGENT.md#8-verify-real-generation).

# Community preview readiness

Current repository review: **2026-11-15**. Reviewed source:
[`55aee8f`](https://github.com/AIEGOBOT/agent-audio/commit/55aee8fe2aa40ef06714414b9c356150912c4fe1).
This record prepares an early tester preview; it is not a published release or
a claim that the complete game/video workflow has passed.

## Distribution scope

Invite early users to try local sound-effect generation and report installation
and game/video workflow results. Use the existing Git-checkout installation
prompt in [README](../README.md#install-with-an-ai-agent). Do not advertise a
package-index install or distribute model weights.

Describe Agent Audio as an integration of a dedicated local runtime, MCP tools
and a portable Skill. Stable Audio 3 Medium supplies generation; the calling
agent's project tools perform game/video integration. Automatic use is intended
behavior that still needs fresh-session evidence.

## Current repository evidence

| Layer | Result and scope |
|---|---|
| Source | Local working branch and GitHub `main` matched `55aee8f` before this documentation change. |
| Remote model-free CI | [Tests and dependency audit](https://github.com/AIEGOBOT/agent-audio/actions/runs/43610761484) passed on `55aee8f`: Windows/macOS/Linux with Python 3.12, plus Linux 3.11 and 3.13; application dependency audit passed. |
| Remote analysis | [CodeQL](https://github.com/AIEGOBOT/agent-audio/actions/runs/43610761342) passed on `55aee8f`. |
| Documentation | Contribution and removal instructions were checked against current source, repository guidance and workflow commands; issue and PR template structure was reviewed. |

This documentation review did not rerun generation, fresh-application discovery,
implicit Skill use, game/video integration, listening or first-time installation.
The earlier observations below remain tied to their original source revision.

## Historical validation record (2026-10-05)

The existing draft records the following observations for
[`d7708a5`](https://github.com/AIEGOBOT/agent-audio/commit/d7708a5105740f8cd87cca9cd355fc524c9bb5f3).
They are retained as historical evidence, not new tests of `55aee8f`.

| Layer | Result and scope |
|---|---|
| Remote source | GitHub `main` matched local `d7708a5` before documentation preparation. |
| Remote model-free CI | [Tests and dependency audit](https://github.com/AIEGOBOT/agent-audio/actions/runs/37189397615) passed on this commit: Windows/macOS/Linux with Python 3.12, plus Linux 3.11 and 3.13; application dependency audit passed. |
| Remote analysis | [CodeQL](https://github.com/AIEGOBOT/agent-audio/actions/runs/37189397607) passed on this commit. |
| Local static checks | Ruff check, Ruff format check (24 files), and compilation passed. |
| Local unit tests | **86 passed, 12 skipped** on Windows, Python 3.12.1. Skips are not passes. |
| Lock consistency | `uv lock --check --offline` passed. No dependencies were installed or updated during this review. |
| Local doctor | TFLite selected, runtime files ready, upstream checkout verified. This was not an OS-level network-isolation test or a model-checksum verification. |
| Real generation | A standalone stdio MCP client listed both tools, called `audio_status`, then generated a 3-second WAV with `generate_audio`. Details below. |
| Fresh application discovery / implicit Skill use | **NOT TESTED** in this review. The local Skill installation was absent and was not reinstalled for this probe. |
| Game/video integration / listening | **NOT TESTED** in this review. |
| Independent first-time installation | **NOT TESTED** in this review; the generation probe reused an existing dedicated installation. |

Local model-free commands actually run from the repository root:

```powershell
.\.venv\Scripts\python.exe -m ruff check src install tests
.\.venv\Scripts\python.exe -m ruff format --check src install tests
.\.venv\Scripts\python.exe -m compileall -q src install
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe install/bootstrap.py --doctor
uv lock --check --offline
```

These used the existing environment: MCP 1.30.0, psutil 7.2.2, pytest 8.4.2 and
Ruff 0.16.9. This is not a fresh dependency-installation test. Use the standard
commands in [AGENTS.md](../AGENTS.md) for installer changes.

### Generation observation

- Host: Windows x64, 31.59 GiB usable system RAM, 15.52 GiB available before the
  probe; TFLite CPU, Stable Audio 3 Medium.
- Runtime: `779434a908193105335fd8d833418603625b2859`.
- Model revision: `da6edc54ddba10bfd79a077102ded687f80e882b`.
- Prompt: "A dry close metallic impact with a sharp transient and short decay,
  isolated one-shot sound effect, no voice, no music."
- MCP generation call: **57.036 seconds**, including the inference process
  startup/model loading. MCP server startup and the earlier status call are
  excluded. Existing model files and native caches were present; this is one
  observation, not a cold-cache or general speed benchmark.
- Output: **3.0 seconds, 44,100 Hz, stereo PCM16, 529,244 bytes**.
- Normalized sample peak: **0.976959**; RMS: **0.067620**. Not digitally silent;
  no full-scale integer samples. PCM16 cannot represent NaN or infinity. These
  measurements do not establish prompt adherence, absence of audible distortion
  or sound quality. Peak memory was not measured in this run.
- WAV SHA-256: `7b620e9c45e1b71b503f0157de5bc5a99e293e4f8dac3ad8e59c6861b0ef798d`.

The original record states that the reproducible probe, raw local result and WAV
were retained outside Git. Their locations and contents were not rechecked for
this documentation review. No generated media, credentials or personal paths
are included in this record. The recorded probe did not modify client
registration, Skills or model/runtime pins.

## Public repository preparation

Observed GitHub state on **2026-11-15**, before opening this documentation PR:

- Public repository, MIT source license, Issues enabled.
- No release or tag existed. Package metadata was `0.1.0`; no release was created
  during this review. Proposed first tag: `v0.1.0-alpha.1`, marked prerelease.
- No open PRs or issues. The dependency update PRs were reviewed and merged;
  [#19](https://github.com/AIEGOBOT/agent-audio/pull/19) was closed as superseded.
  The resulting `main` CI is linked above. Review future dependency updates
  separately from preview launch.
- Private vulnerability reporting was **disabled**. Before promotion, enable it
  in GitHub or establish and document a private reporting channel. Do not direct
  users to publish sensitive vulnerability details in normal issues.
- The About description still emphasized general audio/music and no topics were
  configured. Suggested description: "Local sound effects for coding agents
  building games and videos. MCP server + Agent Skill using Stable Audio 3."
- Suggested topics: `audio-generation`, `sound-effects`, `mcp`, `agent-skills`,
  `stable-audio`. These are proposed metadata, not changes already applied.

This preparation adds contribution guidance, bug/experience issue templates, a
pull-request template and README removal/feedback guidance. They become visible
on GitHub after the reviewed changes reach the default branch. GitHub settings
and community posts have not been changed or published.

## Before inviting early testers

- [ ] Review and merge the preparation diff; confirm CI on the resulting commit.
- [ ] Establish a working private security-reporting route and check the public
  Security page. Apply the reviewed About description/topics if desired.
- [ ] Choose the actual release commit/tag and publish a GitHub **prerelease**
  with source installation instructions, resource guidance and known limits.
  Recheck evidence if code/runtime/Skill content has changed since this record.
- [ ] Prepare and review any English/Korean invitation text, retain the
  early-preview wording and link to the same README and issue chooser in both.
- [ ] Invite installation/workflow feedback without calling untested clients,
  smaller-memory hosts or Linux inference validated.

For a small tester invitation, open product checks can be disclosed as the
reason for seeking feedback. For a broader launch promising automatic finished
audio, complete the following first using
[end-to-end validation](end-to-end-validation.md):

- [ ] One observed independent first installation with intervention notes.
- [ ] One fresh-session game task and one video task with matching installed
  Skills, observed tool use, integration and final playback.
- [ ] Intentional-silence, suitable-existing-audio and unrelated-work controls.
- [ ] A listening comparison and a short, shareable finished example with clear
  provenance. Do not label an explicitly prompted example an implicit-use test.

## Wording boundaries for announcements

Say "early preview" and "looking for installation and workflow feedback."
State that generation runs locally after setup, models have separate terms,
and hardware/agent costs still apply. Link to current RAM/disk guidance.

Do not claim every agent/OS/GPU is supported, automatic integration is proven,
8/16 GB machines are validated, CPU generation is instant, quality beats a
cloud service, or MIT grants rights to the model weights. Do not present CI or
WAV metadata as evidence of listening quality.

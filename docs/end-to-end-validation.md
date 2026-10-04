# End-to-end validation

Use this guide after [installation](../INSTALL_AGENT.md). It defines tests to
run, not completed results. Model-free CI, real WAV generation, implicit Skill
activation, project integration and listening quality are different evidence
levels. See [project direction](project-direction.md) for the intended experience.

## Preparation and preservation

Record the Agent Audio commit, client/model/version, OS, hardware, selected
backend, runtime/model revisions and the installed Skill path. Keep logs and
outputs in a new local validation folder outside this repository. Use copies
of projects, not an active production project. Record the original Git status
and do not discard unrelated changes, replace configuration wholesale or commit
models, generated media, credentials or private paths to this repository.

Run the model-free checks from [AGENTS.md](../AGENTS.md) separately. A missing
runtime on a model-free machine is not an inference failure or an inference
pass. Record exactly which commands ran and which could not run.

### Existing installations

`git pull` updates source files, not the Skill copies installed in agent-client
folders. The installer intentionally reports a conflict if an installed Skill
differs. A new `AGENT_AUDIO_HOME` isolates runtime data; it does not by itself
isolate Skills, client configuration or credentials.

Before testing a new revision:

1. Inspect local changes before updating the checkout. Fetch and use the intended
   reviewed commit without overwriting local work. Check which checkout and
   Python executable the active `agent-audio` MCP registration actually uses.
2. Compare the complete installed `audio-production` folder with this revision's
   `skills/audio-production` folder, including reference files. Record content
   hashes; checking only the folder name is insufficient. Check for duplicate
   or project-local Skill copies that could change discovery.
3. If different, review the diff and obtain authorization for this specific
   Skill update. Preserve local customizations. Back up the full installed
   folder to a unique private location **outside every Skill discovery root**;
   leaving an old `SKILL.md` under a discoverable backup folder can expose both.
   Never delete or overwrite an unknown/conflicting Skill to make a test pass.
4. Only after an authorized migration has moved the old copy out of the target
   path, run `uv run --frozen python install/bootstrap.py --register-only`.
   Do not reinstall models just to update a Skill. Read all per-client outcomes;
   an MCP conflict needs separate review, not a wholesale configuration reset.
5. Confirm the installed files match the intended source revision and start a
   fresh client session. Skill refresh and MCP connectivity are separate checks.

An upgrade on a previously configured machine is not a clean-install test. To
claim first-time usability, observe a separate fresh user/environment or an
independent user's first install, including prerequisites and human intervention.
Existing ComfyUI/Stable Audio runtimes must not be used as an undocumented shortcut.

## A. Runtime and client smoke tests

Use `audio_status` and a roughly 3-second `generate_audio` call through MCP.
Record the backend actually used, call duration, output path/hash, duration,
sample rate, channel count and file size. Distinguish startup/model loading from
warm-cache measurements; mark timing scope unknown when it was not measured.
Where possible inspect non-finite samples, silence, peaks and RMS. A valid file
or a nonzero peak is not a listening test.

Record whether the call came from a standalone stdio test client or the actual
registered application's fresh chat. The former verifies the generation path,
not the latter's tool discovery. An explicit tool request is a connectivity
check, not proof of automatic use during a larger production task.

## B. Implicit use in real work

Use separate, fresh task sessions after setup, outside this repository. Keep
this evaluation guide, installation instructions and explicit sound-generation
requests out of the task worker's conversation/project. Otherwise the test is
primed to use audio. The installed Skill's normal discovery metadata is allowed.
Use ordinary client settings; record approvals without disabling security to
make the result look autonomous. If fresh sessions cannot be arranged, label
the run assisted/prompted, not a passing implicit-use test.

A coordinator may read this guide and prepare fixtures, then evaluate the saved
worker transcript and deliverable afterward. Do not tell the task worker to
follow this guide or use Agent Audio during an implicit-use test. Do not coach
it to add sound after an omission and count the retry as an unassisted pass.

Prepare one small game fixture and one small video fixture with the necessary
engine/editor and editable material already available. The fixtures should
have intended audible events but no suitable existing sound assets. Use the
existing project tools rather than imposing a new engine, cloud API or editor.
Missing host-editing capability is an integration blocker to record.

Example task requests (adapt only the project details):

**Game:** "Complete a small playable scene in this test project with an enemy
hit response, a pickup reward, a win state and restart. Keep the existing engine,
controls and style, and deliver a runnable result."

**Video:** "Finish a 10-second teaser from the supplied material with a title
reveal, a visible action beat and a closing logo. Keep the existing visual style
and export a reviewable final video."

For each result, inspect the transcript and actual deliverable for:

- Whether audio was considered and the Skill loaded without a separate request.
  If Skill loading is not visible, mark it unobserved rather than inferring it
  from a successful tool call. Record MCP calls and outcomes separately.
- Whether assets were generated and correctly referenced, timed and mixed in
  the finished result. Play the game events/restart or the exported video when
  the test environment can do so. Static references alone do not prove playback.
- Whether the agent avoided intermediate creative approvals and manual asset
  selection/transfer. Count these separately from required permission prompts.
- Whether changes stayed within the requested work and preserved unrelated
  assets, settings, existing mix and applicable volume/mute behavior.

For an isolated audio-file request, a WAV may be the full deliverable; for these
larger tasks, merely returning WAV paths is not an integration pass.

## C. Do-not-generate controls

In separate tasks, verify that the agent does not generate unnecessary audio
when asked to update documentation/refactor unrelated code, keep a video silent,
or work in a project with suitable existing audio. Record accidental generation
as a failure even if the new sound is technically valid. Do not delete good
assets to force a generation demonstration.

## D. Finished-result quality and cost

Human review happens **after** the worker delivers the result; it is not a
required mid-task candidate-selection step. Compare with the prior workflow
using the same fixture and task. Keep the baseline environment free of this
Skill/tool without deleting a user's installed configuration; use a separately
prepared profile/environment where supported. Otherwise record a before/after
comparison and its limitations, not a controlled A/B result.

When feasible, hide which version used Agent Audio and compare at comparable
listening levels. Record reviewer identity as a non-sensitive label, preference
and concrete reasons: event fit, timing, unwanted speech/music, repetition,
clipping and balance. A first pair is a product check, not a general model ranking.
An agent that cannot listen must record listening quality as not tested.

Record total task time, audio-call time, retries, manual interventions, available
RAM/disk and observed resource use where measurable. Do not infer a minimum
system requirement from success on one machine. Ask the reviewer after delivery
whether the improvement justifies the observed wait and resource burden; no
acceptable universal latency threshold has been agreed yet.

## Result record

Use one local record per run. `NOT_TESTED` and `BLOCKED` are not passes. Report a
layer as `FAIL` when it ran but missed its criterion, rather than hiding failure
inside a successful overall installation report.

```text
Run ID / date:
Agent Audio commit / branch:
Client / agent model / version:
OS / hardware / backend:
Runtime and model revisions:
Installed Skill path / content hashes:
Fixture revision / task request / fresh session evidence:
Setup type: existing-install upgrade | independent clean install
Model-free checks: PASS | FAIL | BLOCKED | NOT_TESTED
MCP connection in actual client: PASS | FAIL | BLOCKED | NOT_TESTED
WAV generation: PASS | FAIL | BLOCKED | NOT_TESTED
Implicit Skill use: OBSERVED | NOT_OBSERVED | FAIL | BLOCKED | NOT_TESTED
Game integration: PASS | FAIL | BLOCKED | NOT_TESTED
Video integration: PASS | FAIL | BLOCKED | NOT_TESTED
Do-not-generate controls: PASS | FAIL | BLOCKED | NOT_TESTED
Listening comparison: preferred | tied | worse | NOT_TESTED
Candidate approvals / manual file transfers:
Permission / license / credential interventions (separate):
Total task time / audio time / timing scope / retries:
Measured resources / unmeasured quantities:
Output paths and hashes / transcript / reproduction evidence:
Failures and unverified claims:
```

## Turning results into changes

Reproduce one failure before changing code. Distinguish Skill discovery, model
quality, resource limits and project integration rather than attributing every
failure to MCP or adding a backend. Keep the initial observation unchanged; use
a new run ID after a fix. Re-run affected checks and the model-free suite when
code changes. Do not mark a natural-use test as passed by explicitly forcing the
Skill in the rerun; use a new unprimed task.

Only publish reviewed, sanitized summaries with actual observations, environment
and limits. Keep raw transcripts, configuration backups and generated media
local unless sharing was explicitly authorized. Do not update README validation
claims from this plan alone.

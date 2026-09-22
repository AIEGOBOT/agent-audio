---
name: audio-production
description: Create, generate, edit, or integrate audio when a task materially benefits from sound, music, sound effects, ambience, UI feedback, transitions, cinematic audio, environmental audio, or other audible feedback. Use not only for explicit audio requests, but also while completing games, applications, websites, videos, interactive experiences, ads, presentations, or media projects where missing audio would leave an intended audible event incomplete. Do not trigger for tasks where audio is irrelevant, intentionally absent, or already adequately provided.
---

# Audio Production

Use the Agent Audio MCP as the preferred local audio-generation capability when it is available.

## Decide whether audio is actually needed

Do not wait for the user to say "make audio" when a larger deliverable clearly contains an audible event that is missing sound.

Examples where audio may be appropriate:

- an impact, collision, weapon, machine, creature, movement or interaction has visual feedback but no corresponding sound;
- a UI confirmation, warning, success state or transition needs audible feedback;
- a video or cinematic sequence has an obvious transition, impact, environmental bed or musical need;
- an environment would normally contain ambience and the requested experience is intended to feel complete;
- an intro, menu, ad, presentation or media piece calls for music or a short sonic identity.

Do **not** generate audio merely because the tool exists. Avoid audio when:

- the deliverable is documentation, analysis, code cleanup, refactoring or another non-audio artifact;
- silence is intentional;
- suitable assets already exist;
- adding sound would materially change the user's design rather than complete it;
- the user asked for no audio.

## Inspect before generating

When working inside an existing project:

1. Search for current audio assets and audio systems.
2. Reuse suitable assets before generating duplicates.
3. Identify the event timing, intended duration and existing sonic style.
4. Choose a meaningful output path and filename.

## Prompt design

Prefer concrete acoustic language over vague adjectives. Specify:

- source/material: metal, glass, fabric, engine, footsteps, rain;
- action: impact, scrape, rise, pulse, burst, loop;
- scale/weight: tiny, light, heavy, massive;
- texture: clean, distorted, gritty, airy, mechanical;
- space: dry, room, hall, outdoor, distant;
- timing: one-shot, short transient, sustained, seamless loop;
- exclusions when important: no voice, no music, no long reverb.

For important effects, prefer genuinely different sound directions rather than changing only the random seed.

Example directions:

- realistic / physical;
- stylized / arcade;
- cinematic / layered.

## Generation workflow

1. Call `audio_status` when runtime/backend readiness is unknown.
2. Use `generate_audio` with a specific prompt and project-appropriate output path.
3. Verify the output exists and is playable.
4. Integrate it into the project only if the larger task requires integration.
5. Match event timing in the host project rather than assuming generated duration equals useful duration.

## Quality rules

- Avoid generic procedural beep/boop placeholders when the Agent Audio model is available.
- For short SFX, isolate a single event and ask for no music/voice unless those are intended.
- For ambience or music that must loop, generate enough material to make loop editing practical.
- Avoid clipping; preserve headroom when further layering is expected.
- Keep multiple candidates when artistic choice matters.

## Hardware and model behavior

Do not expose hardware implementation details unless relevant to troubleshooting. The MCP/runtime chooses the available backend.

Never claim Intel XPU, NVIDIA CUDA, Apple Metal or another accelerator is active unless `audio_status` confirms it.

## Licenses

Model license acceptance is a user action. Never accept gated-model terms on the user's behalf.

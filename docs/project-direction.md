# Project direction

This is a product baseline, not a claim that all intended behavior has been
validated. It records the direction agreed during the 2026-10-04 planning review.

## Purpose and first users

Enable coding agents to generate and integrate useful local audio while making
games and videos, without an additional audio-generation service fee or a
separate manual sound-production workflow.

The project must be useful in the maintainer's own work and usable by people
who cannot rely on the maintainer's one-to-one installation help. The first
users are creators working with coding agents who do not want to manage an
audio-generation application, write each sound prompt, download candidates and
apply every file themselves. Both games and videos remain in scope.

## Intended experience

The user gives an agent the repository URL for installation. Once setup is
authorized and verified, the user asks for a game, video, feature or scene. The
agent checks whether sound is useful, reuses suitable existing assets, generates
what is missing and integrates it. The user reviews the finished result, not a
mandatory audio plan or candidate-selection page.

Agent autonomy is limited by the requested task, explicit creative constraints
and host permissions. License acceptance, credentials, spending and material
system changes are not implicitly authorized by this workflow.

"No additional audio-generation fee" does not mean free hardware, electricity
or agent subscriptions, or an exemption from model-license conditions. The
quality target is a practical improvement over simple placeholder effects;
superiority to existing cloud services is not the goal or an established fact.

## What the project contributes

Agent Audio integrates existing technology: dedicated local setup, MCP/client
registration, runtime and output management, preservation of existing settings,
and a portable Skill for using audio in a larger task. Stability AI supplies
the current models and inference implementations; the MCP Python SDK supplies
the communication framework. Project integration is performed by the calling
agent and its tools, not by a built-in game engine or video editor.

MCP and Skill are means to the experience, not requirements to maximize feature
count. A simpler existing-tool or CLI-based approach remains a valid comparison.
Do not claim uniqueness or superiority solely from using local models, MCP or
Skills. Installation convenience and reliable task completion are value
hypotheses to test.

## First-public-release scope

Focus on missing sound effects in game and video work using the current
text-to-WAV path. Keep interfaces generic and the implementation open to other
agents, models and hardware, without promising untested combinations.

Do not make paid-cloud fallback, every accelerator, every agent, model switching,
voice cloning, a full music-production suite or engine-specific MCP parameters
requirements of the first release. Do not remove currently useful generic
behavior merely to enforce the initial focus. Expand only in response to a
validated user need and a supportable implementation.

## Success criteria

- The maintainer uses it repeatedly and does less manual audio work.
- A new user completes installation and first use without maintainer rescue.
- In both a game task and a video task, useful audio reaches the finished result
  without a separate sound request, candidate choice or manual file transfer.
- Finished results are judged more suitable than the prior placeholder workflow,
  rather than merely producing valid WAVs or more numerous sounds.

## Open hypotheses

Actual listening quality, implicit Skill activation, final integration,
acceptable generation time, acceptable installation/resource burden and the
maintainable support matrix still require evidence. No minimum machine spec or
universal quality claim follows from one installation or a short generation.

Use [end-to-end validation](end-to-end-validation.md) to start with one game
scene, one video scene and a separately observed first-time install. Record
failures before proposing refactors or expanding features. Use the evidence to
retain, simplify or integrate the project rather than treating this direction
as an immutable answer.

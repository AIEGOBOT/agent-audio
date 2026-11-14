---
name: Bug report
about: Report a reproducible installation, generation or integration problem
title: ""
labels: ""
assignees: ""
---

<!-- English and Korean are welcome. Remove credentials, personal paths,
private prompts and full client configuration before submitting.
For security concerns, read SECURITY.md instead of posting exploit details. -->

## What failed?

Describe the requested task, expected result and actual result.

Failing stage: prerequisites / download or model access / client registration /
MCP connection / WAV generation / automatic Skill use / project integration /
listening quality / other

## Environment

- Agent Audio commit (`git rev-parse HEAD`):
- OS and version:
- CPU / GPU:
- Total RAM / available RAM before generation:
- Free disk space before installation (if relevant):
- Client and version (Codex / Claude Code / Cursor / other):
- Selected backend from doctor or `audio_status`:
- Setup: first installation / existing installation / update

## Reproduction

1.
2.
3.

Exact error and a short, sanitized log excerpt:

```text
Paste only the relevant excerpt here.
```

## What worked?

Mark each relevant layer PASS, FAIL or NOT TESTED. For Skill use, state whether
loading was observed; do not infer it just from a generated file.

- MCP connection (actual application chat or standalone test client?):
- WAV generation:
- Automatic Skill use (was audio explicitly requested?):
- Game/video integration and playback:
- Listening (what did you actually hear?):

## Additional context

For a timeout: requested duration and observed elapsed time.
For a conflict: which component conflicted, without sharing full configuration.
For a WAV: duration, channels and sample rate if available.
Attach audio only if it is safe and permitted to share; it is not required.

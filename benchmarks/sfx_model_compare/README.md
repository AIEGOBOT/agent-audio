# SFX model comparison

This benchmark compares Stable Audio 3 Small-SFX with SAME-S against Medium with SAME-L on the same pinned TFLite CPU runtime. It does not isolate the DiT from the decoder. It never changes the production MCP tool schema or default Medium model.

The editable `manifest.json` has 20 categories with five English prompts each: impacts, explosions, weapons, footsteps, vehicles, machinery, UI, whooshes, science fiction, horror, creatures, nature, weather, water, fire, ambience, household, industrial, destruction, and magic. Each prompt runs at 3 and 10 seconds on both models: 100 × 2 × 2 = 400 cases. The smoke run selects the first prompt in the first two categories (eight cases).

Each prompt and duration receives a 31-bit seed from SHA-256 of `agent-audio-sfx-v1:<id>:<duration>`. Paired models receive exactly the same seed and prompt. The fixed options are eight pingpong steps, CFG 1, fp32 DiT, w8a8 decoder, eight CPU threads, initial noise level 1.0, and model release after use. Decoder family and DiT checkpoint differ by design. The pinned upstream and model revisions are recorded in each row. TFLite and runtime versions should also be captured from the installed environment before interpreting cross-machine results. Runtime packages use upstream version ranges, so a pinned checkout alone does not pin all dependencies.

## Commands

From the repository root:

```text
uv sync --frozen
uv run --frozen python -m agent_audio.benchmark validate
uv run --frozen python -m agent_audio.benchmark prepare
uv run --frozen python -m agent_audio.benchmark run --smoke --output benchmark-results/smoke-001
uv run --frozen python -m agent_audio.benchmark report --output benchmark-results/smoke-001
uv run --frozen python -m agent_audio.benchmark run --output benchmark-results/full-001
uv run --frozen python -m agent_audio.benchmark report --output benchmark-results/full-001
```

`prepare` downloads Medium through the normal installer, then the two Small-SFX TFLite weights into Agent Audio's private cache. The common T5 encoder is reused. Weight revisions and SHA-256 values are pinned. Gated access and license acceptance remain user actions. Do not run the full set until the smoke run succeeds and memory and time are acceptable. Every result directory must be new; outputs are never overwritten. The command is serial and uses the same generation lock as production.

The results directory contains `run.json`, one `results.jsonl` row per attempted case, `summary.json`, `summary.csv`, `audio/`, and optional `report.html`. The report opens locally without a server. It filters category and duration, navigates pairs, optionally plays A then B then advances through matching pairs, stores ratings in browser localStorage, reveals identities on demand, and exports ratings as JSON. A/B identity is assigned independently by a hash of the run ID, prompt, seed and pair; it stays stable when additional pairs complete. Exact A/B balance is not guaranteed. Ratings are isolated by run identity and pair content, and exports record whether identities have been revealed. Legacy browser ratings are not migrated because their A/B mapping cannot be verified. Browser-local ratings should be exported before clearing browser storage or moving the report.

`run.json` holds the manifest hash, command scope, backend, model/runtime revisions, and installed dependency versions. Every JSONL row holds the case ID, category, prompt, model, requested duration, seed, generation order, backend and revisions, fixed options, output path, success/error status, wall time, memory measurement and WAV sanity fields. WAV fields are present on successful cases only. `summary.json` and `summary.csv` aggregate successes, time and peak memory by model, duration, and category; ratios are the row model's median divided by the other model's median. The summary also reports median per-pair Small-SFX/Medium time and memory ratios on matching successful pairs, with excluded-pair counts; this avoids comparing different surviving subsets. No code declares a quality winner. The report only includes pairs with two successful outputs.

Timing includes model load, sampling, decoding, and WAV validation for each case; `prepare` downloads occur separately. Cases run in manifest and duration order, while the first model alternates by pair. Cache warming and system load can bias timings; inspect order and use repeated runs before making a final default-model decision. A 10-second Medium run on this laptop has not been validated yet. Listening ratings determine quality; automatic peak, RMS, clipping and near-silence metrics only flag technical anomalies.

Memory uses psutil sampling every 100 ms. The process peak is the largest child process's OS peak working set on Windows when available and sampled RSS elsewhere. The sampled tree RSS is a sum and can double-count shared pages. These figures may miss a short peak between samples. Results from Windows, Linux and macOS should be compared within a platform, not merged as equivalent measurements. The TFLite path can be selected explicitly on Apple Silicon for this comparison, but real model generation through this benchmark has only been verified on Windows so far.

The report displays attempted, successful, planned and complete-pair counts and smoke scope. It does not establish population quality: there is one seed per prompt, no controlled repeated runs, and no formal multi-rater protocol. The benchmark guide and manifest are source-tree assets; installed-wheel users must supply `--manifest` explicitly.

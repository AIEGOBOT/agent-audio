# Architecture

Agent Audio provides two generic stdio MCP tools: status and text-to-WAV
generation. The CLI and `install/bootstrap.py` also expose installation and
registration. They share runtime orchestration; client-specific configuration
merging lives in `installer.py`.

## Runtime boundary

`backends.py` holds the small Stable Audio backend adapters: model files,
artifact format, tokenizer requirement, script name, generation arguments and
input policy. `detect.py` chooses MLX on Apple Silicon and the portable TFLite
backend elsewhere. New acceleration support needs a validated adapter, not
hardware-specific MCP parameters. `profiles.py` holds model selections for
production Medium and the separate Small-SFX comparison.

`runtime.py` owns dedicated paths, isolated environment variables, checkout
provenance, installation, readiness and generation. `download_models.py` runs
standalone in the dedicated runtime Python, so its pinned download manifests do
not depend on importing the MCP application. Native dependency requirements
still come from upstream version ranges.

Generation validates input, checks prerequisite artifacts and checkout
provenance, serializes inference, runs a dedicated process through `process.py`,
validates the staged WAV, then publishes it with an exclusive hardlink.
`storage.py` coordinates writers and preserves existing files. Windows inference
uses a Job Object; Unix inference uses a dedicated process group.

The current pinned backends use CFG 1.0. Nonempty negative prompts are rejected
because upstream ignores them under that policy. A future guidance policy needs
quality and resource validation. Status reports file readiness and provenance,
but never claims generation, model checksum or native dependency validation.

## Installation and evaluation

Skill and MCP outcomes are independent per client. Conflicts are preserved;
partial failure is represented in JSON and by a nonzero installer exit code.
Native client registration uses temporary empty configurations before merging
the Agent Audio entry into the user's configuration.

`benchmark.py` is a repository-oriented, serial TFLite comparison tool, separate
from production MCP. It records run identity, revisions and measurements.
`benchmark_report.py` uses stable pair identities and records model disclosure
in listening ratings. Common-success-pair statistics complement per-model
summaries. One seed per prompt and a partial run cannot establish a general
quality winner. Existing results and browser ratings are user artifacts.

See [security boundaries](SECURITY.md) and [installer instructions](INSTALL_AGENT.md)
for preservation policy and required verification.

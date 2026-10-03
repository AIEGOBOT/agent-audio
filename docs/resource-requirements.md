# Disk space and memory measurements

This document records observations and planning recommendations for installation. **It is not a benchmark of minimum system requirements.** Disk units use 1 GB = 1,000,000,000 bytes and 1 GiB = 1,073,741,824 bytes.

## Planning recommendations

- For the default Windows TFLite CPU configuration, allow **at least 25 GB of free disk space** on the installation volume and plan for a **32 GB class RAM system**.
- The disk recommendation leaves room for installed files, packages, temporary downloads, model copies and future outputs. It does not cover every audio project's storage needs.
- The RAM recommendation is based on the tested host and an observed inference process peak Working Set of about 11.56 GiB, allowing room for the OS, editor and other applications. Minimum RAM on 8/16 GB systems or for long generations has not been validated.
- The current CPU path requires no dedicated GPU or VRAM. Do not confuse an integrated GPU's reported shared memory capacity with system RAM requirements.
- Apple Silicon MLX has different model sizes and unified memory usage. Do not use these Windows observations as MLX minimum specs.

## Measurement conditions

| Item | Condition |
|---|---|
| Date | 2026-09-28 |
| Agent Audio | `76d08838ef2dd03ddf9ceafe049a92c6a3592251` |
| OS and CPU | Windows 11 x64, Intel Core Ultra 7 258V |
| System RAM | 32 GiB installed; about 31.59 GiB usable by the OS |
| Backend and model | TFLite / LiteRT 2.2.0 CPU, Stable Audio 3 Medium |
| Runtime commit | `779434a908193105335fd8d833418603625b2859` |
| Model revision | `da6edc54ddba10bfd79a077102ded687f80e882b` |
| Generation | MCP `generate_audio`, 3 seconds, `medium` DiT / `same-l` decoder, default options |
| Cache state | Model files and native generation cache already present |
| Result | 529,244-byte WAV, 44.1 kHz, stereo, 3.0 seconds; MCP call took about 57.2 seconds |

The test used the dedicated Agent Audio runtime prepared during this installation test. It did not invoke an existing ComfyUI, Stability Matrix or separate audio environment. Runtime varies with host load; the duration above is a single observation.

## Downloads and storage

The installer currently downloads these four TFLite files. Different models or precision variants have different download sizes.

| File | Bytes |
|---|---:|
| `sa3-m/dit_fp32.tflite` | 5,816,313,104 |
| `same-l/dec_w8a8.tflite` | 515,381,432 |
| `same-l/enc_w8a8.tflite` | 466,762,056 |
| `t5gemma/encoder_fp16.tflite` | 563,818,608 |
| **Model total** | **7,362,275,200 — about 7.36 GB / 6.86 GiB** |

This is the sum of model file sizes. Network overhead, retries, Python packages and runtime downloads are additional.

| Installed files measured | Bytes |
|---|---:|
| Dedicated data directory, counting hardlinks once | 8,063,142,903 |
| MCP application `.venv`, including development dependencies | 82,049,559 |
| **Total** | **8,145,192,462 — about 8.15 GB / 7.59 GiB** |
| Simple directory sum counting hardlinks repeatedly | 15,507,467,662 — about 15.51 GB |

The dedicated data directory includes the official runtime checkout, runtime `.venv`, models, Hugging Face cache and native cache after generation. One observed decoder XNNPACK cache file was about 0.43 GB. Other generation settings may create additional cache files.

The total is the **sum of file lengths**, counting entries with the same `(device ID, file ID)` once. It is not the actual allocation including disk clusters, compression and filesystem metadata. The separate `uv` package cache, base Python, Agent Audio source checkout and external output folders are excluded. Storage use increases when models are copied instead of hardlinked. This is also not a before/after disk usage measurement that assigns costs for files shared with external programs.

## Memory measurement and limitations

A real stdio MCP client started a new Agent Audio server. Windows process snapshots tracked only that server and its descendants. `GetProcessMemoryInfo` was read about every 0.1 seconds. Unrelated existing MCP servers and the measurement client itself were excluded.

| Metric | Observation |
|---|---:|
| Inference process `PeakWorkingSetSize` | 12,413,423,616 bytes — **about 11.56 GiB** |
| Largest sampled sum of MCP and descendant Working Sets | 12,493,750,272 bytes — about 11.64 GiB |
| Inference process peak private commit (`PeakPagefileUsage`) | 6,844,239,872 bytes — about 6.37 GiB |

Working Set includes shareable resident pages such as mapped model files. Summing Working Sets across processes can count shared pages more than once. Private commit is private committed virtual memory; it is not actual pagefile occupancy or total physical RAM. Do not add these two metrics to calculate RAM requirements.

The OS-maintained process peak counters were sampled before exit; a final change between samples and process exit could be missed. This observation does not establish an absolute peak for first installation, a cold cache or long generations. Memory mapping, OS caches and other applications also affect usage.

## Upstream documentation and other environments

### User-reported Apple Silicon MLX observation

The [2026-10-03 macOS installation report](macos-mlx-validation.md) records
successful Stable Audio 3 Medium generation on an Apple M5 Pro with 24 GiB
unified memory. Four MLX model files total **6,883,369,494 bytes (6.88 GB /
6.41 GiB)**. The reported 3-second generation took 8.02 seconds; timing scope
and cache state were not recorded, so this is not a controlled comparison with
the Windows observation above.

The host had about 178 GiB free before installation. That is available capacity,
not installation consumption or a disk recommendation. Runtime packages, caches
and total installed storage were not measured. Neither peak unified memory nor
minimum RAM was measured; successful short generation on 24 GiB does not
establish requirements for smaller machines or longer outputs.

### Upstream references

The [official TFLite guide at the pinned commit](https://github.com/Stability-AI/stable-audio-3/blob/779434a908193105335fd8d833418603625b2859/optimized/tflite/README.md) explains CPU execution and file sizes by precision. The installation sizes here were measured for Agent Audio's four selected files and actual installation, rather than every upstream variant combined.

The [official MLX memory measurements](https://github.com/Stability-AI/stable-audio-3/blob/779434a908193105335fd8d833418603625b2859/optimized/mlx/README.md#speed--memory) use different hardware, a different backend and model-release options. Agent Audio's reported MLX generation above does not yet include equivalent storage or peak-memory measurements.

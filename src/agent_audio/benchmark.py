"""Reproducible, model-free-testable SFX comparison runner."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import math
import os
import platform
import statistics
import struct
import subprocess
import sys
import tempfile
import threading
import time
import uuid
import wave
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path

import psutil

from .download_models import MODEL_REVISION
from .process import run_inference
from .profiles import PROFILES, tflite_command
from .runtime import (
    GENERATION_TIMEOUT,
    UPSTREAM_REVISION,
    _backend_folder,
    _runtime_command,
    _venv_ready,
    install_runtime,
    runtime_environment,
    runtime_paths,
    runtime_python,
    verify_upstream_checkout,
)
from .storage import file_lock, reject_link

MODELS = ("small-sfx", "medium")
DURATIONS = (3, 10)
PARAMETERS = {
    "steps": 8,
    "cfg": 1.0,
    "threads": 8,
    "dit_precision": "fp32",
    "decoder_precision": "w8a8",
    "sampler": "pingpong",
    "init_noise_level": 1.0,
    "free_models": True,
}


def seed_for(item_id: str, duration: int) -> int:
    raw = hashlib.sha256(f"agent-audio-sfx-v1:{item_id}:{duration}".encode()).digest()
    return int.from_bytes(raw[:4], "big") & 0x7FFFFFFF


def load_manifest(path: Path) -> dict:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
        raise ValueError("Unsupported manifest schema")
    if manifest.get("durations") != [3, 10]:
        raise ValueError("Manifest durations must be [3, 10]")
    items = manifest.get("items")
    if not isinstance(items, list) or len(items) != 100:
        raise ValueError("Manifest must contain exactly 100 prompts")
    counts = Counter()
    ids = set()
    for item in items:
        if not isinstance(item, dict) or not all(
            isinstance(item.get(key), str) and item[key].strip()
            for key in ("id", "category", "prompt")
        ):
            raise ValueError("Every prompt needs nonempty id, category and prompt")
        if (
            item["id"] in ids
            or item["id"] != f"{item['category']}_{counts[item['category']] + 1:02d}"
        ):
            raise ValueError(f"Duplicate or out-of-order prompt ID: {item['id']}")
        ids.add(item["id"])
        counts[item["category"]] += 1
    if len(counts) != 20 or set(counts.values()) != {5}:
        raise ValueError("Manifest requires 20 categories with 5 prompts each")
    return manifest


def expand_cases(manifest: dict, *, smoke: bool = False) -> list[dict]:
    items = manifest["items"]
    if smoke:
        categories = list(dict.fromkeys(item["category"] for item in items))[:2]
        items = [
            next(item for item in items if item["category"] == category)
            for category in categories
        ]
    cases = []
    for item_index, item in enumerate(items):
        for duration in DURATIONS:
            # Alternate which model starts each pair to reduce order bias.
            order = MODELS if (item_index + duration // 10) % 2 == 0 else MODELS[::-1]
            for model in order:
                cases.append(
                    {
                        **item,
                        "duration_requested": duration,
                        "model": model,
                        "seed": seed_for(item["id"], duration),
                        "case_id": f"{item['id']}_{duration}s_{model}",
                    }
                )
    return cases


def benchmark_ready() -> bool:
    folder = _backend_folder("tflite")
    if not _venv_ready("tflite") or not (folder / "scripts/sa3_tflite.py").is_file():
        return False
    names = set(PROFILES["small-sfx"].tflite_files + PROFILES["medium"].tflite_files)
    return all((folder / "models/tflite" / name).is_file() for name in names)


def prepare_models() -> None:
    # The production installer handles Medium and the isolated Python environment.
    if install_runtime("tflite") != "tflite":
        raise RuntimeError("This benchmark currently supports the TFLite CPU backend")
    folder = _backend_folder("tflite")
    with file_lock(runtime_paths().upstream):
        subprocess.run(
            [
                str(runtime_python("tflite")),
                "-I",
                str(Path(__file__).with_name("download_models.py")),
                "--backend",
                "tflite",
                "--root",
                str(folder),
                "--cache",
                runtime_environment()["HF_HUB_CACHE"],
                "--benchmark-small",
            ],
            env=runtime_environment(),
            stdin=subprocess.DEVNULL,
            stdout=sys.stderr,
            check=True,
            timeout=3600,
        )
    if not benchmark_ready():
        raise RuntimeError("Benchmark models are incomplete")


@dataclass
class MemorySample:
    process_peak_working_set: int | None = None
    tree_peak_sampled_rss: int | None = None
    process_peak_private_commit: int | None = None
    method: str = "psutil 100 ms samples; largest process OS peak on Windows, sampled RSS elsewhere; tree sum may double-count shared pages"


def _sample_memory(pid: int, stop: threading.Event, sample: MemorySample) -> None:
    try:
        root = psutil.Process(pid)
    except psutil.Error:
        return
    while not stop.is_set():
        try:
            processes = [root, *root.children(recursive=True)]
            rss = []
            for process in processes:
                try:
                    info = process.memory_info()
                    rss.append(info.rss)
                    # Windows venv python.exe may spawn the real base interpreter.
                    # The largest descendant is the inference process, not the wrapper.
                    sample.process_peak_working_set = max(
                        sample.process_peak_working_set or 0,
                        getattr(info, "peak_wset", info.rss),
                    )
                    if hasattr(info, "peak_pagefile"):
                        sample.process_peak_private_commit = max(
                            sample.process_peak_private_commit or 0,
                            info.peak_pagefile,
                        )
                except psutil.Error:
                    continue
            if rss:
                sample.tree_peak_sampled_rss = max(
                    sample.tree_peak_sampled_rss or 0, sum(rss)
                )
        except psutil.Error:
            pass
        stop.wait(0.1)


def wav_metrics(path: Path, requested: int) -> dict:
    with wave.open(str(path), "rb") as audio:
        channels, width, rate, frames = (
            audio.getnchannels(),
            audio.getsampwidth(),
            audio.getframerate(),
            audio.getnframes(),
        )
        if channels < 1 or width != 2 or rate <= 0 or frames <= 0:
            raise ValueError("Expected a nonempty 16-bit PCM WAV")
        if abs(frames / rate - requested) > 1 / rate:
            raise ValueError("Unexpected WAV duration")
        count = clipped = quiet = 0
        sum_sq = 0
        peak = 0
        while block := audio.readframes(65536):
            if len(block) % 2:
                raise ValueError("Truncated PCM sample")
            for (value,) in struct.iter_unpack("<h", block):
                magnitude = abs(value)
                peak = max(peak, magnitude)
                clipped += magnitude >= 32767
                quiet += magnitude < 328
                sum_sq += value * value
                count += 1
        if count != frames * channels:
            raise ValueError("Truncated WAV frames")
    return {
        "duration_actual": frames / rate,
        "sample_rate": rate,
        "channels": channels,
        "bit_depth": width * 8,
        "wav_bytes": path.stat().st_size,
        "peak_amplitude": peak / 32768,
        "rms": math.sqrt(sum_sq / count) / 32768,
        "clipping_ratio": clipped / count,
        "near_silence_ratio": quiet / count,
        "invalid_samples": 0,
    }


def run_case(case: dict, output: Path) -> dict:
    profile = PROFILES[case["model"]]
    destination = output / "audio" / f"{case['case_id']}.wav"
    reject_link(destination)
    if os.path.lexists(destination):
        raise FileExistsError(f"Output exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    record = {
        **case,
        "backend": "tflite-cpu",
        "runtime_revision": UPSTREAM_REVISION,
        "model_revision": MODEL_REVISION,
        "parameters": PARAMETERS.copy(),
        "dit": profile.dit,
        "decoder": profile.decoder,
        "os": platform.platform(),
        "available_memory_before_bytes": psutil.virtual_memory().available,
        "output_path": str(destination),
        "success": False,
        "error_type": None,
        "error_message": None,
    }
    sample = MemorySample()
    stop = threading.Event()
    thread = None

    def started(pid: int) -> None:
        nonlocal thread
        thread = threading.Thread(
            target=_sample_memory, args=(pid, stop, sample), daemon=True
        )
        thread.start()

    with tempfile.TemporaryDirectory(
        prefix=".agent-audio-benchmark-", dir=destination.parent
    ) as stage:
        temporary = Path(stage) / "audio.wav"
        command, cwd = _runtime_command("tflite")
        command += tflite_command(
            profile,
            prompt=case["prompt"],
            seconds=case["duration_requested"],
            seed=case["seed"],
            output=str(temporary),
            **{key: PARAMETERS[key] for key in ("steps", "cfg", "threads")},
        )
        env = runtime_environment()
        env["HF_HUB_OFFLINE"] = "1"
        start = time.perf_counter()
        try:
            run_inference(
                command,
                cwd,
                env,
                GENERATION_TIMEOUT,
                on_start=started,
                log_dir=runtime_paths().root / "logs",
            )
            metrics = wav_metrics(temporary, case["duration_requested"])
            os.link(temporary, destination)
            record.update(metrics)
            record["success"] = True
        except Exception as exc:
            record["error_type"] = type(exc).__name__
            record["error_message"] = str(exc)[:1000]
        finally:
            record["generation_wall_seconds"] = time.perf_counter() - start
            stop.set()
            if thread:
                thread.join(timeout=2)
            record.update(asdict(sample))
    return record


def _percentile(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * percentile
    lower = int(position)
    fraction = position - lower
    return (
        ordered[lower] * (1 - fraction)
        + ordered[min(lower + 1, len(ordered) - 1)] * fraction
    )


def paired_summary(records: list[dict]) -> dict:
    """Compare matching successful cases, never unmatched surviving subsets."""
    pairs = defaultdict(dict)
    for row in records:
        key = (row["id"], row["duration_requested"], row["seed"], row["prompt"])
        pairs[key][row["model"]] = row
    timing_ratios = []
    memory_ratios = []
    complete = 0
    for models in pairs.values():
        if set(models) != set(MODELS) or not all(
            row["success"] for row in models.values()
        ):
            continue
        complete += 1
        small, medium = models["small-sfx"], models["medium"]
        if medium["generation_wall_seconds"] > 0:
            timing_ratios.append(
                small["generation_wall_seconds"] / medium["generation_wall_seconds"]
            )
        if small.get("process_peak_working_set") is not None and medium.get(
            "process_peak_working_set"
        ):
            memory_ratios.append(
                small["process_peak_working_set"] / medium["process_peak_working_set"]
            )
    return {
        "attempted_pairs": len(pairs),
        "complete_success_pairs": complete,
        "excluded_pairs": len(pairs) - complete,
        "timing_pairs": len(timing_ratios),
        "memory_pairs": len(memory_ratios),
        "median_time_ratio": statistics.median(timing_ratios)
        if timing_ratios
        else None,
        "median_memory_ratio": statistics.median(memory_ratios)
        if memory_ratios
        else None,
        "ratio_definition": "median of per-pair small-sfx / medium ratios; both outputs successful",
    }


def summarize(records: list[dict]) -> dict:
    groups = defaultdict(list)
    for row in records:
        groups[(row["model"], "all", "all")].append(row)
        groups[(row["model"], str(row["duration_requested"]), "all")].append(row)
        groups[(row["model"], "all", row["category"])].append(row)
        groups[(row["model"], str(row["duration_requested"]), row["category"])].append(
            row
        )
    output = []
    for (model, duration, category), rows in sorted(groups.items()):
        ok = [row for row in rows if row["success"]]
        times = [row["generation_wall_seconds"] for row in ok]
        memory = [
            row["process_peak_working_set"]
            for row in ok
            if row.get("process_peak_working_set") is not None
        ]
        output.append(
            {
                "model": model,
                "duration": duration,
                "category": category,
                "cases": len(rows),
                "successes": len(ok),
                "success_rate": len(ok) / len(rows),
                "median_seconds": statistics.median(times) if times else None,
                "mean_seconds": statistics.mean(times) if times else None,
                "p95_seconds": _percentile(times, 0.95),
                "median_peak_bytes": statistics.median(memory) if memory else None,
                "p95_peak_bytes": _percentile(memory, 0.95),
            }
        )
    lookup = {(row["model"], row["duration"], row["category"]): row for row in output}
    for row in output:
        other = lookup.get(
            (
                "small-sfx" if row["model"] == "medium" else "medium",
                row["duration"],
                row["category"],
            )
        )
        for key, label in (
            ("median_seconds", "speed_ratio_to_other"),
            ("median_peak_bytes", "memory_ratio_to_other"),
        ):
            row[label] = (
                row[key] / other[key]
                if other and row[key] is not None and other[key]
                else None
            )
    return {
        "groups": output,
        "ratio_definition": "row median / other model median; successful cases only",
        "paired_success": paired_summary(records),
    }


def write_summary(records: list[dict], output: Path, *, replace: bool = False) -> None:
    summary = summarize(records)
    (output / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    mode = "w" if replace else "x"
    with (output / "summary.csv").open(mode, newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(summary["groups"][0]))
        writer.writeheader()
        writer.writerows(summary["groups"])


def runtime_dependencies() -> dict[str, str]:
    code = (
        "import importlib.metadata as m,json; "
        "print(json.dumps({p:m.version(p) for p in "
        "('ai-edge-litert','numpy','huggingface-hub','sentencepiece')}))"
    )
    output = subprocess.check_output(
        [str(runtime_python("tflite")), "-I", "-c", code],
        env=runtime_environment(),
        text=True,
        timeout=30,
    )
    return json.loads(output)


def run(manifest_path: Path, output: Path, *, smoke: bool = False) -> list[dict]:
    manifest = load_manifest(manifest_path)
    if os.path.lexists(output):
        raise FileExistsError(f"Result directory exists: {output}")
    if not benchmark_ready():
        raise RuntimeError("Benchmark runtime/models are not ready; run prepare first")
    verify_upstream_checkout(runtime_paths().upstream)
    dependency_versions = runtime_dependencies()
    output.mkdir(parents=True)
    cases = expand_cases(manifest, smoke=smoke)
    (output / "run.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "run_id": str(uuid.uuid4()),
                "manifest_sha256": hashlib.sha256(
                    manifest_path.read_bytes()
                ).hexdigest(),
                "cases": len(cases),
                "smoke": smoke,
                "parameters": PARAMETERS,
                "runtime_revision": UPSTREAM_REVISION,
                "model_revision": MODEL_REVISION,
                "backend": "tflite-cpu",
                "application_dependencies": {
                    "psutil": importlib.metadata.version("psutil"),
                },
                "runtime_dependencies": dependency_versions,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    records = []
    model_runs = Counter()
    with file_lock(runtime_paths().root / "generation"):
        with (output / "results.jsonl").open("x", encoding="utf-8") as stream:
            for index, case in enumerate(cases, 1):
                print(f"[{index}/{len(cases)}] {case['case_id']}", flush=True)
                case = {
                    **case,
                    "sequence_index": index,
                    "model_run_index": model_runs[case["model"]] + 1,
                    "first_run_for_model": model_runs[case["model"]] == 0,
                }
                record = run_case(case, output)
                model_runs[case["model"]] += 1
                records.append(record)
                stream.write(json.dumps(record, ensure_ascii=False) + "\n")
                stream.flush()
    write_summary(records, output)
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="Stable Audio SFX benchmark")
    parser.add_argument("command", choices=("validate", "prepare", "run", "report"))
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path(__file__).resolve().parents[2]
        / "benchmarks/sfx_model_compare/manifest.json",
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    if args.command == "validate":
        cases = expand_cases(load_manifest(args.manifest))
        print(json.dumps({"prompts": 100, "cases": len(cases)}))
    elif args.command == "prepare":
        prepare_models()
        print("Benchmark runtime and models ready")
    elif args.command == "run":
        if args.output is None:
            parser.error("--output is required for run")
        records = run(args.manifest, args.output, smoke=args.smoke)
        print(
            json.dumps(
                {"cases": len(records), "successes": sum(r["success"] for r in records)}
            )
        )
    else:
        if args.output is None:
            parser.error("--output is required for report")
        from .benchmark_report import write_report

        write_report(args.output)


if __name__ == "__main__":
    main()

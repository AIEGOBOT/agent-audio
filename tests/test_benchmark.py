import json
import wave
from pathlib import Path
from types import SimpleNamespace

import pytest

from agent_audio import benchmark
from agent_audio.benchmark_report import _pairs, write_report
from agent_audio.profiles import PROFILES, tflite_command

MANIFEST = (
    Path(__file__).resolve().parents[1] / "benchmarks/sfx_model_compare/manifest.json"
)


def test_manifest_and_case_expansion():
    manifest = benchmark.load_manifest(MANIFEST)
    assert len(manifest["items"]) == 100
    assert len({item["category"] for item in manifest["items"]}) == 20
    cases = benchmark.expand_cases(manifest)
    assert len(cases) == 400
    assert {case["duration_requested"] for case in cases} == {3, 10}
    assert len(benchmark.expand_cases(manifest, smoke=True)) == 8
    for index in range(0, len(cases), 2):
        assert cases[index]["seed"] == cases[index + 1]["seed"]
        assert cases[index]["prompt"] == cases[index + 1]["prompt"]
    assert (
        sum(cases[index]["model"] == "small-sfx" for index in range(0, 400, 2)) == 100
    )


def test_model_commands_share_every_option_except_profile():
    commands = [
        tflite_command(
            profile, prompt="metal impact", seconds=3, seed=42, output="out.wav"
        )
        for profile in PROFILES.values()
    ]
    for command in commands:
        assert command[command.index("--seed") + 1] == "42"
        assert command[command.index("--steps") + 1] == "8"
        assert command[command.index("--dit-precision") + 1] == "fp32"
        assert command[command.index("--decoder-precision") + 1] == "w8a8"
    assert commands[0][commands[0].index("--dit") + 1] == "sm-sfx"
    assert commands[1][commands[1].index("--dit") + 1] == "medium"


def test_manifest_rejects_wrong_counts(tmp_path):
    value = benchmark.load_manifest(MANIFEST)
    value["items"].pop()
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(ValueError, match="100 prompts"):
        benchmark.load_manifest(path)


def test_wav_sanity_and_truncation(tmp_path):
    path = tmp_path / "audio.wav"
    with wave.open(str(path), "wb") as audio:
        audio.setparams((2, 2, 8000, 0, "NONE", ""))
        audio.writeframes(b"\0\0" * 2 * 8000 * 3)
    metrics = benchmark.wav_metrics(path, 3)
    assert metrics["duration_actual"] == 3
    assert metrics["near_silence_ratio"] == 1
    path.write_bytes(path.read_bytes()[:-100])
    with pytest.raises((ValueError, EOFError)):
        benchmark.wav_metrics(path, 3)


def test_aggregation_serialization_and_report(tmp_path):
    cases = benchmark.expand_cases(benchmark.load_manifest(MANIFEST), smoke=True)[:2]
    rows = []
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir()
    for case, elapsed in zip(cases, (2.0, 4.0)):
        (audio_dir / f"{case['case_id']}.wav").write_bytes(b"fixture")
        rows.append(
            {
                **case,
                "success": True,
                "generation_wall_seconds": elapsed,
                "process_peak_working_set": 100
                if case["model"] == "small-sfx"
                else 200,
            }
        )
    benchmark.write_summary(rows, tmp_path)
    summary = json.loads((tmp_path / "summary.json").read_text())
    assert len(summary["groups"]) == 8
    assert (
        next(
            row
            for row in summary["groups"]
            if row["model"] == "medium"
            and row["duration"] == "all"
            and row["category"] == "all"
        )["speed_ratio_to_other"]
        == 2
    )
    with (tmp_path / "results.jsonl").open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row) + "\n")
    assert len(_pairs(rows)) == 1
    report = write_report(tmp_path)
    assert "Sample A" in report.read_text(encoding="utf-8")
    assert "Export ratings JSON" in report.read_text(encoding="utf-8")
    with pytest.raises(FileExistsError):
        write_report(tmp_path)


def test_existing_result_dir_is_preserved(tmp_path):
    destination = tmp_path / "existing"
    destination.mkdir()
    marker = destination / "keep.txt"
    marker.write_text("keep")
    with pytest.raises(FileExistsError):
        benchmark.run(MANIFEST, destination)
    assert marker.read_text() == "keep"


def test_memory_sampler_selects_inference_child(monkeypatch):
    class Process:
        def __init__(self, pid, rss, peak):
            self.pid = pid
            self.info = SimpleNamespace(
                rss=rss, peak_wset=peak, peak_pagefile=peak // 2
            )

        def memory_info(self):
            return self.info

        def children(self, recursive=False):
            return [Process(2, 1000, 2000)]

    class Once:
        calls = 0

        def is_set(self):
            self.calls += 1
            return self.calls > 1

        def wait(self, delay):
            pass

    monkeypatch.setattr(benchmark.psutil, "Process", lambda pid: Process(pid, 10, 20))
    sample = benchmark.MemorySample()
    benchmark._sample_memory(1, Once(), sample)
    assert sample.process_peak_working_set == 2000
    assert sample.tree_peak_sampled_rss == 1010


def test_pair_identity_survives_completion_changes_and_isolates_runs():
    cases = benchmark.expand_cases(benchmark.load_manifest(MANIFEST), smoke=True)
    rows = [{**case, "success": True} for case in cases]
    initial = _pairs(rows[:2], run_id="run-one")[0]
    regenerated = next(
        pair for pair in _pairs(rows, run_id="run-one") if pair["key"] == initial["key"]
    )
    assert regenerated == initial
    other_run = _pairs(rows[:2], run_id="run-two")[0]
    assert other_run["rating_key"] != initial["rating_key"]
    changed_prompt = [{**row, "prompt": "a different prompt"} for row in rows[:2]]
    assert (
        _pairs(changed_prompt, run_id="run-one")[0]["rating_key"]
        != initial["rating_key"]
    )


def test_paired_summary_excludes_unmatched_survivors():
    cases = benchmark.expand_cases(benchmark.load_manifest(MANIFEST), smoke=True)[:4]
    rows = [
        {
            **case,
            "success": True,
            "generation_wall_seconds": 2 if case["model"] == "small-sfx" else 4,
            "process_peak_working_set": 10 if case["model"] == "small-sfx" else 20,
        }
        for case in cases
    ]
    rows[2]["success"] = False
    result = benchmark.summarize(rows)["paired_success"]
    assert result["complete_success_pairs"] == 1
    assert result["excluded_pairs"] == 1
    assert result["median_time_ratio"] == 0.5
    assert result["median_memory_ratio"] == 0.5


def test_report_records_run_scope_and_reveal_state(tmp_path):
    rows = [
        {**case, "success": True}
        for case in benchmark.expand_cases(
            benchmark.load_manifest(MANIFEST), smoke=True
        )[:2]
    ]
    (tmp_path / "results.jsonl").write_text(
        "\n".join(json.dumps(row) for row in rows), encoding="utf-8"
    )
    (tmp_path / "run.json").write_text(
        json.dumps({"run_id": "test-run", "cases": 8, "smoke": True}), encoding="utf-8"
    )
    document = write_report(tmp_path).read_text(encoding="utf-8")
    assert (
        "2 attempted cases; 2 successful outputs; 1 complete listening pairs."
        in document
    )
    assert "Planned cases: 8. Smoke run." in document
    assert 'const runId="test-run"' in document
    assert "identities_revealed" in document
    assert "ratings[p.rating_key]" in document
    assert "run_id:runId" in document


def test_legacy_report_identity_ignores_mutable_completion_metadata(tmp_path):
    (tmp_path / "results.jsonl").write_text("", encoding="utf-8")
    metadata = {
        "manifest_sha256": "manifest",
        "runtime_revision": "runtime",
        "model_revision": "model",
        "backend": "tflite",
        "parameters": {"steps": 8},
        "status": "running",
    }
    path = tmp_path / "run.json"
    path.write_text(json.dumps(metadata), encoding="utf-8")
    before = (
        write_report(tmp_path)
        .read_text(encoding="utf-8")
        .split("const runId=", 1)[1]
        .split(", storageKey=", 1)[0]
    )
    metadata.update(
        status="stopped_early_and_pruned",
        completed_before_pruning=204,
        retained_cases=102,
        retained_durations=[3],
    )
    path.write_text(json.dumps(metadata), encoding="utf-8")
    document = write_report(tmp_path, replace=True).read_text(encoding="utf-8")
    after = document.split("const runId=", 1)[1].split(", storageKey=", 1)[0]
    assert before == after
    assert "0 retained result rows" in document
    assert "Completed before pruning: 204." in document
    assert "Metadata retained cases: 102." in document
    assert "Retained durations (seconds): [3]." in document
    assert "Run status: stopped_early_and_pruned." in document
    assert "total historical attempts" in document


def test_report_escapes_run_id_script_terminator(tmp_path):
    (tmp_path / "results.jsonl").write_text("", encoding="utf-8")
    (tmp_path / "run.json").write_text(
        json.dumps({"run_id": "</script><script>bad</script>"}), encoding="utf-8"
    )
    document = write_report(tmp_path).read_text(encoding="utf-8")
    assert 'const runId="\\u003c/script>' in document
    assert "<script>bad" not in document

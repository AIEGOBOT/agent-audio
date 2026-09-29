import subprocess
import sys
import wave
import zipfile
from pathlib import Path

import pytest

from agent_audio import runtime


def test_wrapper_alone_is_not_a_ready_runtime(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_AUDIO_HOME", str(tmp_path))
    folder = runtime.runtime_paths().upstream / "optimized" / "tflite"
    folder.mkdir(parents=True)
    for name in ("sa3", "sa3.bat", "sa3.ps1"):
        (folder / name).write_text("wrapper only")
    assert not runtime.backend_ready("tflite")


def test_mlx_runtime_does_not_require_tflite_tokenizer(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_AUDIO_HOME", str(tmp_path))
    monkeypatch.setattr(runtime, "_venv_ready", lambda backend: backend == "mlx")
    folder = runtime.runtime_paths().upstream / "optimized" / "mlx"
    (folder / "scripts").mkdir(parents=True)
    (folder / "scripts" / "sa3_mlx.py").write_text("# runtime entry point")
    for path in runtime._model_paths("mlx"):
        path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("test.npy", b"model fixture")
    assert not (folder / "models" / "tokenizer.model").exists()
    assert runtime.backend_ready("mlx")


def test_generation_logs_do_not_corrupt_mcp_stdout(tmp_path, monkeypatch, capfd):
    monkeypatch.setenv("AGENT_AUDIO_HOME", str(tmp_path))
    monkeypatch.setattr(runtime, "detect_environment", lambda: None)
    monkeypatch.setattr(runtime, "recommended_backend", lambda _: "tflite")
    monkeypatch.setattr(runtime, "backend_ready", lambda _: True)
    monkeypatch.setattr(runtime, "verify_upstream_checkout", lambda _: None)
    # A real subprocess writes a diagnostic. This is a protocol regression test,
    # not a substitute for the separate real-model acceptance test.
    script = "import wave,sys; print('runtime diagnostic'); f=wave.open(sys.argv[sys.argv.index('--out')+1],'wb'); f.setparams((1,2,8000,0,'NONE','')); f.writeframes(b'\\0\\0'*24000); f.close()"
    monkeypatch.setattr(
        runtime,
        "_runtime_command",
        lambda _: ([sys.executable, "-c", script], tmp_path),
    )
    runtime.generate_audio("unit test", 3, str(tmp_path / "test.wav"))
    captured = capfd.readouterr()
    assert "runtime diagnostic" not in captured.out
    assert "runtime diagnostic" in captured.err


def test_model_cache_cannot_reuse_an_unrelated_hf_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_AUDIO_HOME", str(tmp_path))
    for name in ("HF_HOME", "HF_HUB_CACHE", "HUGGINGFACE_HUB_CACHE", "HF_XET_CACHE"):
        monkeypatch.setenv(name, str(tmp_path.parent / "unrelated-models"))
    env = runtime.runtime_environment()
    for name in ("HF_HOME", "HF_HUB_CACHE", "HUGGINGFACE_HUB_CACHE", "HF_XET_CACHE"):
        assert Path(env[name]).is_relative_to(tmp_path)


def test_runtime_command_uses_dedicated_python_without_shell(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_AUDIO_HOME", str(tmp_path))
    command, cwd = runtime._runtime_command("tflite")
    assert Path(command[0]).is_relative_to(tmp_path)
    assert ".venv" in Path(command[0]).parts
    assert command[1] == "-I"
    assert command[2].endswith("sa3_tflite.py")


@pytest.mark.parametrize(
    "seconds", [float("nan"), float("inf"), -float("inf"), 0, -1, 381]
)
def test_invalid_durations_rejected_before_starting_anything(seconds, monkeypatch):
    monkeypatch.setattr(
        runtime,
        "detect_environment",
        lambda: pytest.fail("Must validate before hardware probing"),
    )
    with pytest.raises(ValueError):
        runtime.generate_audio("test", seconds)


def test_existing_output_is_never_replaced(tmp_path, monkeypatch):
    monkeypatch.setattr(runtime, "detect_environment", lambda: None)
    monkeypatch.setattr(runtime, "recommended_backend", lambda _: "tflite")
    monkeypatch.setattr(runtime, "backend_ready", lambda _: True)
    monkeypatch.setattr(runtime, "verify_upstream_checkout", lambda _: None)
    output = tmp_path / "keep.wav"
    output.write_bytes(b"original")
    with pytest.raises(FileExistsError):
        runtime.generate_audio("test", 3, str(output))
    assert output.read_bytes() == b"original"


def test_runtime_env_removes_python_injection(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_AUDIO_HOME", str(tmp_path))
    for name in (
        "PYTHONPATH",
        "PYTHONHOME",
        "PYTHONUSERBASE",
        "VIRTUAL_ENV",
        "CONDA_PREFIX",
    ):
        monkeypatch.setenv(name, "unrelated")
        assert name not in runtime.runtime_environment()


def test_unmanaged_runtime_with_readme_is_not_executed(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_AUDIO_HOME", str(tmp_path))
    root = runtime.runtime_paths().upstream
    root.mkdir(parents=True)
    (root / "README.md").write_text("not the official runtime")
    with pytest.raises(RuntimeError, match="Unmanaged"):
        runtime.ensure_upstream_checkout()
    assert (root / "README.md").read_text() == "not the official runtime"


@pytest.mark.parametrize(
    "origin,revision",
    [
        ("https://example.com/fake.git", runtime.UPSTREAM_REVISION),
        (runtime.UPSTREAM_REPO, "wrong"),
    ],
)
def test_untrusted_runtime_provenance_rejected(tmp_path, monkeypatch, origin, revision):
    (tmp_path / ".git").mkdir()
    monkeypatch.setattr(
        runtime, "_git", lambda repo, *args: origin if args[0] == "remote" else revision
    )
    with pytest.raises(RuntimeError):
        runtime.verify_upstream_checkout(tmp_path)


def test_truncated_wav_rejected(tmp_path):
    path = tmp_path / "bad.wav"
    with wave.open(str(path), "wb") as audio:
        audio.setparams((1, 2, 8000, 0, "NONE", ""))
        audio.writeframes(b"\0\0" * 24000)
    path.write_bytes(path.read_bytes()[:-100])
    with pytest.raises(RuntimeError, match="truncated"):
        runtime._validate_wav(path, 3)


def test_inference_timeout_stops_process(tmp_path):
    from agent_audio.process import run_inference

    with pytest.raises(subprocess.TimeoutExpired):
        run_inference(
            [sys.executable, "-c", "import time; time.sleep(30)"],
            tmp_path,
            runtime.runtime_environment(),
            0.2,
        )


def test_prompt_metacharacters_are_literal_and_raced_output_is_preserved(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("AGENT_AUDIO_HOME", str(tmp_path / "data"))
    monkeypatch.setattr(runtime, "detect_environment", lambda: None)
    monkeypatch.setattr(runtime, "recommended_backend", lambda _: "tflite")
    monkeypatch.setattr(runtime, "backend_ready", lambda _: True)
    monkeypatch.setattr(runtime, "verify_upstream_checkout", lambda _: None)
    destination = tmp_path / "out.wav"
    prompt = '-n " & echo INJECTED | %PATH% ; $(touch marker)'

    def render(command, cwd, env, timeout):
        assert f"--prompt={prompt}" in command
        assert env["HF_HUB_OFFLINE"] == "1"
        path = command[command.index("--out") + 1]
        with wave.open(path, "wb") as audio:
            audio.setparams((1, 2, 8000, 0, "NONE", ""))
            audio.writeframes(b"\0\0" * 24000)
        destination.write_bytes(b"another writer")

    monkeypatch.setattr(runtime, "run_inference", render)
    with pytest.raises(FileExistsError):
        runtime.generate_audio(prompt, 3, str(destination))
    assert destination.read_bytes() == b"another writer"
    assert not list(tmp_path.glob(".agent-audio-render-*"))


def test_timeout_kills_descendants(tmp_path):
    import time

    from agent_audio.process import run_inference

    finished = tmp_path / "descendant-finished"
    spawned = tmp_path / "spawned"
    child = f"import time,pathlib; time.sleep(2); pathlib.Path({str(finished)!r}).write_text('orphan')"
    parent = f"import subprocess,sys,time,pathlib; subprocess.Popen([sys.executable,'-c',{child!r}]); pathlib.Path({str(spawned)!r}).write_text('started'); time.sleep(30)"
    with pytest.raises(subprocess.TimeoutExpired):
        run_inference(
            [sys.executable, "-c", parent], tmp_path, runtime.runtime_environment(), 0.8
        )
    assert spawned.exists()
    time.sleep(2.2)
    assert not finished.exists()

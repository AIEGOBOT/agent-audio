import subprocess

import pytest

from agent_audio import detect
from agent_audio.detect import EnvironmentInfo, recommended_backend


def make_info(*, apple_silicon: bool = False) -> EnvironmentInfo:
    return EnvironmentInfo(
        os="Darwin" if apple_silicon else "Windows",
        architecture="64bit",
        machine="arm64" if apple_silicon else "AMD64",
        apple_silicon=apple_silicon,
        nvidia_detected=False,
        intel_graphics_detected=False,
        codex_installed=False,
        claude_installed=False,
        cursor_installed=False,
    )


def test_apple_silicon_prefers_mlx() -> None:
    assert recommended_backend(make_info(apple_silicon=True)) == "mlx"


def test_other_platforms_use_portable_tflite() -> None:
    assert recommended_backend(make_info()) == "tflite"


@pytest.mark.parametrize(
    "display,expected",
    [("NVIDIA Corporation Device", False), ("Intel Corporation UHD 630", True)],
)
def test_linux_graphics_probe_uses_no_shell_and_no_stdin(
    monkeypatch, display, expected
) -> None:
    calls = []

    def run(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=(
                "00:1f.3 Audio device: Intel Corporation Device\n"
                f"01:00.0 VGA compatible controller: {display}\n"
            ),
            stderr="",
        )

    monkeypatch.setattr(detect.platform, "system", lambda: "Linux")
    monkeypatch.setattr(detect.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(detect.subprocess, "run", run)
    # Only display controller lines count, like the former grep filter.
    assert detect._detect_intel_graphics() is expected
    ((command, kwargs),) = calls
    assert command == ["/usr/bin/lspci"]
    assert kwargs["stdin"] is subprocess.DEVNULL

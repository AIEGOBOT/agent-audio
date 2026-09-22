from __future__ import annotations

import os
import platform
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .detect import detect_environment, recommended_backend

UPSTREAM_REPO = "https://github.com/Stability-AI/stable-audio-3.git"


@dataclass(frozen=True)
class RuntimePaths:
    root: Path
    upstream: Path
    output: Path


def data_root() -> Path:
    custom = os.environ.get("AGENT_AUDIO_HOME")
    return Path(custom).expanduser().resolve() if custom else Path.home() / ".agent-audio"


def runtime_paths() -> RuntimePaths:
    root = data_root()
    return RuntimePaths(root=root, upstream=root / "runtime" / "stable-audio-3", output=root / "output")


def ensure_upstream_checkout() -> Path:
    paths = runtime_paths()
    paths.upstream.parent.mkdir(parents=True, exist_ok=True)
    if (paths.upstream / ".git").exists() or (paths.upstream / "README.md").exists():
        return paths.upstream

    git = shutil.which("git")
    if not git:
        raise RuntimeError(
            "Git is required for the v0.1 runtime bootstrap. Ask the agent to install Git, then retry."
        )
    subprocess.run([git, "clone", "--depth", "1", UPSTREAM_REPO, str(paths.upstream)], check=True)
    return paths.upstream


def install_runtime() -> str:
    info = detect_environment()
    backend = recommended_backend(info)
    repo = ensure_upstream_checkout()

    if backend == "mlx":
        installer = repo / "optimized" / "mlx" / "install.sh"
        subprocess.run(["bash", str(installer), "-y", "--download", "medium"], cwd=installer.parent, check=True)
        return backend

    tflite_dir = repo / "optimized" / "tflite"
    if platform.system() == "Windows":
        subprocess.run(["cmd", "/c", "install.bat", "--download", "medium"], cwd=tflite_dir, check=True)
    else:
        subprocess.run(["bash", "install.sh", "-y", "--download", "medium"], cwd=tflite_dir, check=True)
    return backend


def backend_ready(backend: str | None = None) -> bool:
    info = detect_environment()
    backend = backend or recommended_backend(info)
    repo = runtime_paths().upstream

    if backend == "mlx":
        return (repo / "optimized" / "mlx" / "sa3").exists()

    tflite = repo / "optimized" / "tflite"
    if platform.system() == "Windows":
        return (tflite / "sa3.bat").exists() or (tflite / "sa3.ps1").exists()
    return (tflite / "sa3").exists()


def _runtime_command(backend: str) -> tuple[list[str], Path]:
    repo = runtime_paths().upstream
    if backend == "mlx":
        folder = repo / "optimized" / "mlx"
        return [str(folder / "sa3")], folder

    folder = repo / "optimized" / "tflite"
    if platform.system() == "Windows":
        bat = folder / "sa3.bat"
        return ["cmd", "/c", str(bat)], folder
    return [str(folder / "sa3")], folder


def generate_audio(
    prompt: str,
    seconds: float = 10.0,
    output_path: str | None = None,
    negative_prompt: str | None = None,
) -> Path:
    if not prompt.strip():
        raise ValueError("prompt must not be empty")
    if seconds <= 0 or seconds > 380:
        raise ValueError("seconds must be > 0 and <= 380")

    info = detect_environment()
    backend = recommended_backend(info)
    if not backend_ready(backend):
        raise RuntimeError(
            f"Stable Audio runtime is not ready for backend '{backend}'. "
            "Run the Agent Audio bootstrap installer first."
        )

    paths = runtime_paths()
    paths.output.mkdir(parents=True, exist_ok=True)
    destination = Path(output_path).expanduser().resolve() if output_path else paths.output / "agent-audio.wav"
    destination.parent.mkdir(parents=True, exist_ok=True)

    command, cwd = _runtime_command(backend)
    command += [
        "--prompt",
        prompt,
        "--dit",
        "medium",
        "--decoder",
        "same-l",
        "--seconds",
        str(seconds),
        "--out",
        str(destination),
    ]
    if negative_prompt:
        command += ["--negative-prompt", negative_prompt]

    subprocess.run(command, cwd=cwd, check=True)
    if not destination.exists() or destination.stat().st_size == 0:
        raise RuntimeError(f"Audio generation completed without a valid output file: {destination}")
    return destination

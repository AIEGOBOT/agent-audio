from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

from .detect import detect_environment, recommended_backend
from .runtime import backend_ready, install_runtime, runtime_paths

SKILL_NAME = "audio-production"
MCP_NAME = "agent-audio"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _venv_python() -> Path:
    root = repo_root()
    if sys.platform == "win32":
        candidate = root / ".venv" / "Scripts" / "python.exe"
    else:
        candidate = root / ".venv" / "bin" / "python"
    return candidate if candidate.exists() else Path(sys.executable).resolve()


def _copy_skill(destination_root: Path) -> Path:
    source = repo_root() / "skills" / SKILL_NAME
    destination = destination_root / SKILL_NAME
    destination_root.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination)
    return destination


def install_skills() -> dict[str, str]:
    info = detect_environment()
    results: dict[str, str] = {}
    if info.codex_installed:
        results["codex"] = str(_copy_skill(Path.home() / ".agents" / "skills"))
    if info.claude_installed:
        results["claude"] = str(_copy_skill(Path.home() / ".claude" / "skills"))
    if info.cursor_installed:
        results["cursor"] = str(_copy_skill(Path.home() / ".cursor" / "skills"))
    return results


def _run_if_missing(command: list[str], name: str) -> str:
    list_cmd = command[:2] + ["list"] if command[0].endswith("codex") else [command[0], "mcp", "list"]
    try:
        listed = subprocess.run(list_cmd, capture_output=True, text=True, timeout=15, check=False)
        if name.lower() in (listed.stdout + listed.stderr).lower():
            return "already-registered"
    except (OSError, subprocess.SubprocessError):
        pass

    completed = subprocess.run(command, capture_output=True, text=True, timeout=60, check=False)
    if completed.returncode != 0:
        message = (completed.stderr or completed.stdout).strip()
        raise RuntimeError(message or f"registration command failed: {' '.join(command)}")
    return "registered"


def _register_codex(python: Path) -> str:
    codex = shutil.which("codex")
    if not codex:
        return "not-installed"
    command = [codex, "mcp", "add", MCP_NAME, "--", str(python), "-m", "agent_audio.mcp_server"]
    return _run_if_missing(command, MCP_NAME)


def _register_claude(python: Path) -> str:
    claude = shutil.which("claude")
    if not claude:
        return "not-installed"
    command = [claude, "mcp", "add", "-s", "user", MCP_NAME, "--", str(python), "-m", "agent_audio.mcp_server"]
    return _run_if_missing(command, MCP_NAME)


def _register_cursor(python: Path) -> str:
    info = detect_environment()
    if not info.cursor_installed:
        return "not-installed"

    config_path = Path.home() / ".cursor" / "mcp.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    data: dict[str, object]
    if config_path.exists():
        backup = config_path.with_suffix(".json.agent-audio.bak")
        shutil.copy2(config_path, backup)
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Cursor MCP config is invalid JSON: {config_path}: {exc}") from exc
    else:
        data = {}

    servers = data.setdefault("mcpServers", {})
    if not isinstance(servers, dict):
        raise RuntimeError("Cursor mcp.json has a non-object 'mcpServers' field; refusing to overwrite it.")

    existing = servers.get(MCP_NAME)
    desired = {
        "type": "stdio",
        "command": str(python),
        "args": ["-m", "agent_audio.mcp_server"],
    }
    if existing == desired:
        return "already-registered"
    servers[MCP_NAME] = desired
    config_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return "registered"


def register_agents() -> dict[str, object]:
    python = _venv_python()
    return {
        "python": str(python),
        "skills": install_skills(),
        "mcp": {
            "codex": _register_codex(python),
            "claude": _register_claude(python),
            "cursor": _register_cursor(python),
        },
    }


def doctor() -> dict[str, object]:
    info = detect_environment()
    backend = recommended_backend(info)
    return {
        "environment": info.to_dict(),
        "recommended_backend": backend,
        "runtime_ready": backend_ready(backend),
        "runtime_path": str(runtime_paths().upstream),
        "warnings": [
            "NVIDIA detected: v0.1 keeps a portable fallback unless a validated accelerator adapter is available."
            if info.nvidia_detected
            else "",
            "Intel graphics detected: v0.1 uses the CPU fallback; XPU acceleration is reserved for a validated adapter."
            if info.intel_graphics_detected
            else "",
        ],
    }


def perform_install(runtime: bool = True, register: bool = True) -> dict[str, object]:
    result: dict[str, object] = {"doctor_before": doctor()}
    if runtime:
        result["runtime_backend"] = install_runtime()
    if register:
        result["registration"] = register_agents()
    result["doctor_after"] = doctor()
    return result

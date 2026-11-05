from __future__ import annotations

import asyncio
import signal
import threading
from functools import partial
from pathlib import Path

from anyio import CancelScope
from mcp.server.fastmcp import FastMCP

from .detect import detect_environment, recommended_backend
from .runtime import backend_ready, runtime_details, runtime_paths
from .runtime import generate_audio as _generate_audio

mcp = FastMCP("agent-audio")
# Stop events of generations in progress, for cancellation and SIGTERM.
_active_generations: set[threading.Event] = set()


@mcp.tool()
def audio_status() -> dict[str, object]:
    """Inspect Agent Audio platform, hardware, selected backend and runtime readiness."""
    info = detect_environment()
    backend = recommended_backend(info)
    return {
        "environment": info.to_dict(),
        "selected_backend": backend,
        "runtime_ready": backend_ready(backend),
        "runtime_root": str(runtime_paths().upstream),
        **runtime_details(backend),
        "notes": {
            "nvidia": "Detected NVIDIA hardware is reported, but v0.1 uses the portable backend unless a validated accelerated adapter is installed.",
            "intel": "Intel graphics are supported through the portable CPU path in v0.1; XPU acceleration is not claimed until validated.",
        },
    }


@mcp.tool()
async def generate_audio(
    prompt: str,
    seconds: float = 10.0,
    output_path: str | None = None,
    negative_prompt: str | None = None,
) -> str:
    """Generate local audio from text using Stable Audio 3 Medium and return the WAV path.

    Use for music, sound effects, ambience, UI sounds, transitions and general media audio.
    The caller should choose a meaningful output path when integrating into a project.
    The current backends reject nonempty negative_prompt; use prompt to describe
    the desired sound. audio_status reports capabilities and readiness check scope.
    Only one generation runs at a time for each Agent Audio data folder. A call
    made while another generation runs fails at once with a lock error. Wait for
    each call to return before the next call; do not call this tool in parallel.
    """
    # A worker thread keeps the event loop free for cancellation, ping and
    # audio_status while inference runs.
    cancel = threading.Event()
    _active_generations.add(cancel)
    worker = asyncio.create_task(
        asyncio.to_thread(
            partial(
                _generate_audio,
                prompt=prompt,
                seconds=seconds,
                output_path=output_path,
                negative_prompt=negative_prompt,
                cancel=cancel,
            )
        )
    )
    try:
        # Keep a joinable worker when the request task is cancelled.
        path: Path = await asyncio.shield(worker)
    except asyncio.CancelledError:
        cancel.set()
        # MCP uses AnyIO level cancellation; every unshielded await in its
        # cancelled scope would raise again. Direct Task.cancel() can also
        # recur during cleanup, so shield the worker and keep joining it.
        with CancelScope(shield=True):
            while not worker.done():
                try:
                    await asyncio.shield(worker)
                except asyncio.CancelledError:
                    continue
                except Exception:
                    break
            if not worker.cancelled():
                worker.exception()  # Retrieve errors without masking cancellation.
        raise
    finally:
        # Keep the event registered until worker cleanup releases its resources.
        cancel.set()
        _active_generations.discard(cancel)
    return str(path)


def _exit_on_sigterm(signum: int, frame: object) -> None:
    # Default SIGTERM handling skips finally blocks. A host that stops this
    # server during generation would then leave the generation lock and an
    # orphaned runtime process group. The stop events end inference in the
    # worker threads, and SystemExit runs the cleanup in this thread.
    for cancel in list(_active_generations):
        cancel.set()
    raise SystemExit(128 + signum)


def main() -> None:
    signal.signal(signal.SIGTERM, _exit_on_sigterm)
    mcp.run()


if __name__ == "__main__":
    main()

import asyncio
import datetime
import os
import signal
import sys
import threading
import time
import wave

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from agent_audio import mcp_server


def test_real_stdio_status_and_input_rejection(tmp_path):
    async def probe():
        params = StdioServerParameters(
            command=sys.executable,
            args=["-I", "-m", "agent_audio.mcp_server"],
            env={**os.environ, "AGENT_AUDIO_HOME": str(tmp_path)},
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(
                read, write, read_timeout_seconds=datetime.timedelta(seconds=30)
            ) as session:
                await session.initialize()
                tools = await session.list_tools()
                assert {t.name for t in tools.tools} == {
                    "audio_status",
                    "generate_audio",
                }
                status = await session.call_tool("audio_status", {})
                assert not status.isError
                assert status.structuredContent["runtime_ready"] is False
                assert (
                    status.structuredContent["capabilities"]["negative_prompt"] is False
                )
                assert (
                    status.structuredContent["readiness"]["generation"] == "not_checked"
                )
                result = await session.call_tool(
                    "generate_audio", {"prompt": "test", "seconds": 0}
                )
                assert result.isError
                rejected = await session.call_tool(
                    "generate_audio",
                    {"prompt": "impact", "seconds": 3, "negative_prompt": "music"},
                )
                assert rejected.isError
                assert any(
                    "negative_prompt is unsupported" in getattr(block, "text", "")
                    for block in rejected.content
                )

    asyncio.run(probe())


def test_successful_generation_tool_dispatch(tmp_path, monkeypatch):
    """Exercise registered MCP dispatch; synthetic audio is not model inference."""
    output = tmp_path / "impact.wav"
    calls = []

    def synthetic_backend(**kwargs):
        calls.append(kwargs)
        with wave.open(str(output), "wb") as wav:
            wav.setparams((1, 2, 8000, 0, "NONE", ""))
            wav.writeframes(b"\x00\x00" * 8000)
        return output

    monkeypatch.setattr(mcp_server, "_generate_audio", synthetic_backend)
    result = asyncio.run(
        mcp_server.mcp.call_tool(
            "generate_audio",
            {"prompt": "metal impact", "seconds": 1, "output_path": str(output)},
        )
    )
    content, structured = result
    assert any(getattr(block, "text", None) == str(output) for block in content)
    assert structured == {"result": str(output)}
    cancel = calls[0].pop("cancel")
    assert cancel.is_set()
    assert calls == [
        {
            "prompt": "metal impact",
            "seconds": 1.0,
            "output_path": str(output),
            "negative_prompt": None,
        }
    ]
    with wave.open(str(output), "rb") as wav:
        assert wav.getnframes() == 8000


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX signal semantics")
def test_sigterm_during_generation_releases_lock_and_stops_runtime(tmp_path):
    home = tmp_path / "home"
    marker = tmp_path / "started"
    output = tmp_path / "out" / "impact.wav"
    child = (
        "import os,pathlib,time; "
        f"pathlib.Path({str(marker)!r}).write_text(f'{{os.getpid()}} {{os.getppid()}}'); "
        "time.sleep(60)"
    )
    server = "\n".join(
        [
            "import sys",
            "from agent_audio import mcp_server, runtime",
            "runtime.detect_environment = lambda: None",
            "runtime.recommended_backend = lambda _: 'tflite'",
            "runtime.backend_ready = lambda _: True",
            "runtime.verify_upstream_checkout = lambda _: None",
            "runtime._runtime_command = lambda _: "
            f"([sys.executable, '-c', {child!r}], runtime.data_root())",
            "mcp_server.main()",
        ]
    )
    lock = home / "generation.agent-audio.lock"
    runtime_pid = None

    def alive(pid):
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        return True

    async def probe():
        nonlocal runtime_pid
        params = StdioServerParameters(
            command=sys.executable,
            args=["-I", "-c", server],
            env={**os.environ, "AGENT_AUDIO_HOME": str(home)},
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(
                read, write, read_timeout_seconds=datetime.timedelta(seconds=10)
            ) as session:
                await session.initialize()
                call = asyncio.create_task(
                    session.call_tool(
                        "generate_audio",
                        {"prompt": "impact", "seconds": 1, "output_path": str(output)},
                    )
                )
                for _ in range(200):
                    if marker.exists() and marker.read_text():
                        break
                    await asyncio.sleep(0.05)
                runtime_pid, server_pid = map(int, marker.read_text().split())
                assert lock.exists()
                # The event loop still answers while inference runs.
                status = await session.call_tool("audio_status", {})
                assert not status.isError
                os.kill(server_pid, signal.SIGTERM)
                for _ in range(100):
                    if not lock.exists() and not alive(runtime_pid):
                        break
                    await asyncio.sleep(0.05)
                call.cancel()

    try:
        try:
            asyncio.run(probe())
        except BaseException:
            pass
        assert runtime_pid is not None
        assert not lock.exists()
        assert not alive(runtime_pid)
        assert not list(output.parent.glob(".agent-audio-render-*"))
    finally:
        if runtime_pid is not None and alive(runtime_pid):
            os.killpg(runtime_pid, signal.SIGKILL)


def test_generation_runs_off_event_loop_and_stops_on_cancel(monkeypatch):
    seen = {}

    def blocking(**kwargs):
        seen.update(kwargs)
        (kwargs.get("cancel") or threading.Event()).wait(3)
        raise RuntimeError("stopped")

    monkeypatch.setattr(mcp_server, "_generate_audio", blocking)

    async def probe():
        call = asyncio.create_task(
            mcp_server.mcp.call_tool("generate_audio", {"prompt": "x", "seconds": 1})
        )
        gap, last = 0.0, time.monotonic()
        for _ in range(10):
            await asyncio.sleep(0.05)
            now = time.monotonic()
            gap, last = max(gap, now - last), now
        call.cancel()
        with pytest.raises(asyncio.CancelledError):
            await call
        return gap

    assert asyncio.run(probe()) < 0.5
    assert seen["cancel"].is_set()

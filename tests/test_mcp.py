import asyncio
import datetime
import os
import signal
import sys
import threading
import time
import wave

import anyio
import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.shared.exceptions import McpError
from mcp.shared.memory import create_client_server_memory_streams
from mcp.types import (
    CancelledNotification,
    CancelledNotificationParams,
    ClientNotification,
)

from agent_audio import mcp_server, process, runtime


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


def test_parallel_generation_fails_at_once_with_lock_error(monkeypatch, tmp_path):
    # The README and the tool description say that a parallel call does not wait.
    from agent_audio.storage import file_lock

    started, release = threading.Event(), threading.Event()

    def locked(**kwargs):
        with file_lock(tmp_path / "generation", activity="generation"):
            started.set()
            release.wait(3)
        return tmp_path / "first.wav"

    monkeypatch.setattr(mcp_server, "_generate_audio", locked)

    async def probe():
        first = asyncio.create_task(
            mcp_server.mcp.call_tool("generate_audio", {"prompt": "x", "seconds": 1})
        )
        while not started.is_set():
            await asyncio.sleep(0.01)
        begin = time.monotonic()
        with pytest.raises(Exception, match="Another generation may be using"):
            await mcp_server.mcp.call_tool(
                "generate_audio", {"prompt": "y", "seconds": 1}
            )
        waited = time.monotonic() - begin
        release.set()
        await first
        return waited

    assert asyncio.run(probe()) < 1.0


@pytest.mark.parametrize("cancellation", ["asyncio", "anyio"])
def test_cancellation_waits_for_worker_even_when_repeated(
    monkeypatch, tmp_path, cancellation
):
    from agent_audio.storage import file_lock

    started, stopping, release, cleaned = (threading.Event() for _ in range(4))
    seen = {}

    def worker(**kwargs):
        seen.update(kwargs)
        try:
            with file_lock(tmp_path / "generation", activity="generation"):
                started.set()
                assert kwargs["cancel"].wait(5)
                stopping.set()
                assert release.wait(5)
                raise RuntimeError("cancelled worker")
        finally:
            cleaned.set()

    monkeypatch.setattr(mcp_server, "_generate_audio", worker)

    async def wait_for(event):
        with anyio.fail_after(5):
            while not event.is_set():
                await anyio.sleep(0.01)

    async def probe():
        scope = anyio.CancelScope()

        async def invoke():
            with scope:
                await mcp_server.generate_audio("impact")

        call = asyncio.create_task(invoke())
        try:
            await wait_for(started)
            if cancellation == "anyio":
                scope.cancel()
            else:
                call.cancel()
            await wait_for(stopping)
            # Repeated Task.cancel() must not interrupt shielded AnyIO cleanup either.
            for _ in range(3):
                call.cancel()
                await anyio.sleep(0.01)
            assert not call.done()
            assert seen["cancel"] in mcp_server._active_generations
            assert (tmp_path / "generation.agent-audio.lock").exists()
            release.set()
            try:
                await asyncio.wait_for(call, 5)
            except asyncio.CancelledError:
                pass
            assert cleaned.is_set()
            assert seen["cancel"] not in mcp_server._active_generations
            with file_lock(tmp_path / "generation"):
                pass
        finally:
            release.set()
            call.cancel()
            await asyncio.gather(call, return_exceptions=True)
            await wait_for(cleaned)

    anyio.run(probe)


@pytest.mark.parametrize("cancellation", ["notification", "disconnect"])
def test_mcp_transport_cancellation_joins_runtime_cleanup(
    tmp_path, monkeypatch, cancellation
):
    """Real MCP/AnyIO request scopes and a model-free inference subprocess."""
    import psutil

    monkeypatch.setenv("AGENT_AUDIO_HOME", str(tmp_path / "data"))
    monkeypatch.setattr(runtime, "detect_environment", lambda: None)
    monkeypatch.setattr(runtime, "recommended_backend", lambda _: "tflite")
    monkeypatch.setattr(runtime, "backend_ready", lambda _: True)
    monkeypatch.setattr(runtime, "verify_upstream_checkout", lambda _: None)
    marker, output = tmp_path / "started", tmp_path / "impact.wav"
    child = (
        "import os,pathlib,time; "
        f"pathlib.Path({str(marker)!r}).write_text(str(os.getpid())); "
        "time.sleep(30)"
    )
    monkeypatch.setattr(
        runtime, "_runtime_command", lambda _: ([sys.executable, "-c", child], tmp_path)
    )
    stopping, release, cleaned = (threading.Event() for _ in range(3))
    remove_log = process._remove_log

    def slow_cleanup(path):
        stopping.set()
        try:
            assert release.wait(5)
            remove_log(path)
        finally:
            cleaned.set()

    monkeypatch.setattr(process, "_remove_log", slow_cleanup)

    async def until(predicate):
        with anyio.fail_after(5):
            while not predicate():
                await anyio.sleep(0.01)

    async def probe():
        server = mcp_server.mcp._mcp_server
        server_done = anyio.Event()
        async with create_client_server_memory_streams() as (client_io, server_io):

            async def serve():
                try:
                    await server.run(*server_io, server.create_initialization_options())
                finally:
                    server_done.set()

            async with anyio.create_task_group() as group:
                group.start_soon(serve)
                async with ClientSession(*client_io) as session:
                    await session.initialize()
                    request_id = session._request_id
                    call = asyncio.create_task(
                        session.call_tool(
                            "generate_audio",
                            {
                                "prompt": "impact",
                                "seconds": 1,
                                "output_path": str(output),
                            },
                        )
                    )
                    try:
                        await until(
                            lambda: marker.exists() and bool(marker.read_text())
                        )
                        pid = int(marker.read_text())
                        if cancellation == "notification":
                            notification = ClientNotification(
                                CancelledNotification(
                                    method="notifications/cancelled",
                                    params=CancelledNotificationParams(
                                        requestId=request_id
                                    ),
                                )
                            )
                            await session.send_notification(notification)
                            # The SDK acknowledges cancellation before joining the
                            # handler. That response is not a cleanup guarantee.
                            with pytest.raises(McpError, match="cancelled"):
                                await asyncio.wait_for(call, 5)
                            await session.send_notification(notification)
                        else:
                            await client_io[1].aclose()
                        await until(stopping.is_set)
                        if cancellation == "notification":
                            await session.send_ping()
                        assert not psutil.pid_exists(pid)
                        assert mcp_server._active_generations
                        assert not server_done.is_set()
                        assert (
                            runtime.data_root() / "generation.agent-audio.lock"
                        ).exists()
                        assert list(tmp_path.glob(".agent-audio-render-*"))
                        release.set()
                        await until(lambda: not mcp_server._active_generations)
                        assert cleaned.is_set()
                        assert not output.exists()
                        assert not (
                            runtime.data_root() / "generation.agent-audio.lock"
                        ).exists()
                        assert not list(tmp_path.glob(".agent-audio-render-*"))
                        assert not list((runtime.data_root() / "logs").glob("*.log"))
                        await client_io[1].aclose()
                        await until(server_done.is_set)
                    finally:
                        release.set()
                        call.cancel()
                        await asyncio.gather(call, return_exceptions=True)
                        group.cancel_scope.cancel()

    anyio.run(probe)

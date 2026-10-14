import asyncio
import datetime
import os
import sys
import wave

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

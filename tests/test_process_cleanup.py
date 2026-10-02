import signal
import subprocess
import sys

import pytest

from agent_audio import process as inference


@pytest.mark.parametrize("outcome", [0, 7, "timeout", "cancel"])
def test_unix_group_cleaned_even_after_parent_exits(tmp_path, monkeypatch, outcome):
    groups = []

    class Parent:
        pid = 12345

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def wait(self, timeout=None):
            if timeout is not None:
                if outcome == "timeout":
                    raise subprocess.TimeoutExpired("fixture", timeout)
                if outcome == "cancel":
                    raise KeyboardInterrupt
            return outcome if isinstance(outcome, int) else 0

        def poll(self):
            # Parent has exited but its process group can still contain children.
            return 0

    monkeypatch.setattr(inference.sys, "platform", "linux")
    monkeypatch.setattr(signal, "SIGKILL", 9, raising=False)
    monkeypatch.setattr(inference.subprocess, "Popen", lambda *args, **kwargs: Parent())
    monkeypatch.setattr(
        inference.os,
        "killpg",
        lambda pid, sig: groups.append((pid, sig)),
        raising=False,
    )
    expected = {
        7: RuntimeError,
        "timeout": subprocess.TimeoutExpired,
        "cancel": KeyboardInterrupt,
    }
    if outcome in expected:
        with pytest.raises(expected[outcome]):
            inference.run_inference(["fixture"], tmp_path, {}, 1)
    else:
        inference.run_inference(["fixture"], tmp_path, {}, 1)
    assert groups == [(12345, signal.SIGKILL)]


def test_unix_already_exited_group_is_not_an_error(tmp_path, monkeypatch):

    def gone(pid, sig):
        raise ProcessLookupError

    monkeypatch.setattr(inference.sys, "platform", "linux")
    monkeypatch.setattr(signal, "SIGKILL", 9, raising=False)
    monkeypatch.setattr(inference.os, "killpg", gone, raising=False)
    inference.run_inference([sys.executable, "-c", "pass"], tmp_path, {}, 5)


@pytest.mark.skipif(sys.platform == "win32", reason="Native Unix process groups")
@pytest.mark.parametrize("exit_code", [0, 7])
def test_native_parent_exit_stops_descendants(tmp_path, exit_code):
    import os
    import time

    finished = tmp_path / "descendant-finished"
    child = (
        "import time,pathlib; time.sleep(1); "
        f"pathlib.Path({str(finished)!r}).write_text('orphan')"
    )
    parent = (
        "import subprocess,sys; "
        f"subprocess.Popen([sys.executable,'-c',{child!r}]); sys.exit({exit_code})"
    )
    if exit_code:
        with pytest.raises(RuntimeError, match="exit code 7"):
            inference.run_inference(
                [sys.executable, "-c", parent], tmp_path, os.environ.copy(), 5
            )
    else:
        inference.run_inference(
            [sys.executable, "-c", parent], tmp_path, os.environ.copy(), 5
        )
    time.sleep(1.2)
    assert not finished.exists()

"""Run inference with bounded lifetime, including its child processes."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
from pathlib import Path


def run_inference(
    command: list[str], cwd: Path, env: dict[str, str], timeout: float
) -> None:
    job = None
    if sys.platform == "win32":
        import win32api
        import win32con
        import win32job

        job = win32job.CreateJobObject(None, "")
        limits = win32job.QueryInformationJobObject(
            job, win32job.JobObjectExtendedLimitInformation
        )
        limits["BasicLimitInformation"]["LimitFlags"] |= (
            win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        )
        win32job.SetInformationJobObject(
            job, win32job.JobObjectExtendedLimitInformation, limits
        )
    try:
        with subprocess.Popen(
            command,
            cwd=cwd,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=sys.stderr,
            start_new_session=sys.platform != "win32",
        ) as process:
            try:
                if job is not None:
                    handle = win32api.OpenProcess(
                        win32con.PROCESS_SET_QUOTA | win32con.PROCESS_TERMINATE,
                        False,
                        process.pid,
                    )
                    try:
                        win32job.AssignProcessToJobObject(job, handle)
                    finally:
                        handle.Close()
                code = process.wait(timeout=timeout)
                if code:
                    # Runtime logs are on stderr; avoid reflecting full prompts into MCP errors.
                    raise RuntimeError(
                        f"Stable Audio inference failed with exit code {code}; see server stderr."
                    )
            except BaseException:
                if job is not None:
                    win32job.TerminateJobObject(job, 1)
                elif process.poll() is None:
                    os.killpg(process.pid, signal.SIGKILL)
                if process.poll() is None:
                    process.kill()
                process.wait()
                raise
    finally:
        if job is not None:
            job.Close()

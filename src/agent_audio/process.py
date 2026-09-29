"""Run inference with bounded lifetime, including its child processes."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import tempfile
from pathlib import Path


def run_inference(
    command: list[str],
    cwd: Path,
    env: dict[str, str],
    timeout: float,
    log_dir: Path | None = None,
) -> None:
    # The MCP host owns stderr and may close its reader while this server stays
    # alive. A child inheriting that pipe can fail while flushing Python's
    # streams, even after inference produced a valid WAV.
    log_dir = log_dir or cwd
    log_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    log_fd, log_name = tempfile.mkstemp(
        prefix="generation-", suffix=".log", dir=log_dir
    )
    log_path = Path(log_name)
    keep_log = False
    job = None
    try:
        with os.fdopen(log_fd, "wb") as log:
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
            with subprocess.Popen(
                command,
                cwd=cwd,
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=subprocess.STDOUT,
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
                        # Do not put model logs in an MCP response: they may
                        # contain the prompt. Keep the file for local diagnosis.
                        keep_log = True
                        raise RuntimeError(
                            f"Stable Audio inference failed with exit code {code}; "
                            f"see local log {log_path}."
                        )
                except BaseException as exc:
                    if isinstance(exc, subprocess.TimeoutExpired):
                        keep_log = True
                        exc.log_path = log_path
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
        if not keep_log:
            try:
                log_path.unlink(missing_ok=True)
            except PermissionError:
                # Windows can keep the file open briefly while descendants of
                # a completed runtime process exit after their job is closed.
                pass

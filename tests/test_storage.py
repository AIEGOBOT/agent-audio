import os
import stat
import sys

import pytest

from agent_audio.storage import atomic_write, file_lock, read_optional


def test_concurrent_edit_not_overwritten(tmp_path):
    config = tmp_path / "config.json"
    config.write_bytes(b"other editor changed it")
    with pytest.raises(RuntimeError, match="changed"):
        atomic_write(config, b"old", b"new")
    assert config.read_bytes() == b"other editor changed it"


def test_lock_rejects_second_writer(tmp_path):
    config = tmp_path / "config.json"
    with file_lock(config):
        with pytest.raises(RuntimeError, match="lock exists"):
            with file_lock(config):
                pytest.fail("must not enter")
    assert not list(tmp_path.glob("*.lock"))


def test_linked_config_not_modified(tmp_path):
    real = tmp_path / "real.json"
    real.write_bytes(b"keep")
    link = tmp_path / "link.json"
    try:
        link.symlink_to(real)
    except OSError:
        pytest.skip("symlink creation privilege unavailable")
    with pytest.raises(RuntimeError, match="link"):
        read_optional(link)
    assert real.read_bytes() == b"keep"


def test_repeated_edits_keep_distinct_backups(tmp_path):
    config = tmp_path / "config.json"
    config.write_bytes(b"first")
    with file_lock(config):
        atomic_write(config, b"first", b"second")
        atomic_write(config, b"second", b"third")
    assert {p.read_bytes() for p in tmp_path.glob("*.bak")} == {b"first", b"second"}


def test_busy_lock_names_activity_and_owner_pid(tmp_path):
    work = tmp_path / "generation"
    with file_lock(work, activity="generation"):
        with pytest.raises(RuntimeError) as busy:
            with file_lock(work, activity="generation"):
                pytest.fail("must not enter")
    message = str(busy.value)
    assert "Another generation" in message
    assert "install" not in message
    assert f"PID {os.getpid()}" in message


def test_edit_during_write_is_not_overwritten(tmp_path, monkeypatch):
    from agent_audio import storage

    config = tmp_path / "config.json"
    config.write_bytes(b"old")
    real_fsync, calls = os.fsync, []

    def fsync(fd):
        real_fsync(fd)
        calls.append(fd)
        if len(calls) == 2:  # After the backup and the staged update.
            config.write_bytes(b"external")

    monkeypatch.setattr(storage.os, "fsync", fsync)
    with pytest.raises(RuntimeError, match="changed"):
        atomic_write(config, b"old", b"new")
    assert config.read_bytes() == b"external"
    assert not list(tmp_path.glob(".agent-audio-*"))


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX file modes")
def test_replacement_keeps_file_mode(tmp_path):
    config = tmp_path / "config.json"
    config.write_bytes(b"old")
    config.chmod(0o644)
    atomic_write(config, b"old", b"new")
    assert config.read_bytes() == b"new"
    assert stat.S_IMODE(config.stat().st_mode) == 0o644

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

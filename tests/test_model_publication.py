import errno
import hashlib
import sys
from types import SimpleNamespace

import pytest

from agent_audio import download_models as models


def fixture_download(tmp_path, monkeypatch):
    cached = tmp_path / "cached"
    cached.write_bytes(b"verified weights")
    monkeypatch.setitem(
        sys.modules,
        "huggingface_hub",
        SimpleNamespace(hf_hub_download=lambda *args, **kwargs: str(cached)),
    )
    monkeypatch.setattr(
        models,
        "TFLITE_SHA256",
        {"model.tflite": hashlib.sha256(cached.read_bytes()).hexdigest()},
    )
    target = tmp_path / "runtime/models/tflite/model.tflite"
    original_link = models.os.link

    def cross_device(source, destination):
        if source == cached:
            raise OSError(errno.EXDEV, "cross-device link")
        original_link(source, destination)

    monkeypatch.setattr(models.os, "link", cross_device)
    return cached, target


def test_cross_device_copy_publishes_verified_complete_model(tmp_path, monkeypatch):
    cached, target = fixture_download(tmp_path, monkeypatch)
    models.download("tflite", tmp_path / "runtime", tmp_path)
    assert target.read_bytes() == cached.read_bytes()
    assert not list(target.parent.glob(".agent-audio-model-*"))


def test_failed_copy_leaves_no_conflict_and_can_retry(tmp_path, monkeypatch):
    cached, target = fixture_download(tmp_path, monkeypatch)
    original_copy = models.shutil.copyfileobj

    def interrupted(source, destination):
        destination.write(b"partial")
        raise OSError(errno.ENOSPC, "disk full")

    monkeypatch.setattr(models.shutil, "copyfileobj", interrupted)
    with pytest.raises(OSError, match="disk full"):
        models.download("tflite", tmp_path / "runtime", tmp_path)
    assert not target.exists()
    assert not list(target.parent.glob(".agent-audio-model-*"))
    monkeypatch.setattr(models.shutil, "copyfileobj", original_copy)
    models.download("tflite", tmp_path / "runtime", tmp_path)
    assert target.read_bytes() == cached.read_bytes()


def test_raced_copy_publication_preserves_other_writer(tmp_path, monkeypatch):
    _, target = fixture_download(tmp_path, monkeypatch)
    original_copy = models.shutil.copyfileobj

    def raced(source, destination):
        original_copy(source, destination)
        target.write_bytes(b"other writer")

    monkeypatch.setattr(models.shutil, "copyfileobj", raced)
    with pytest.raises(RuntimeError, match="appeared during installation"):
        models.download("tflite", tmp_path / "runtime", tmp_path)
    assert target.read_bytes() == b"other writer"
    assert not list(target.parent.glob(".agent-audio-model-*"))


def test_corrupt_copy_is_never_published(tmp_path, monkeypatch):
    _, target = fixture_download(tmp_path, monkeypatch)
    monkeypatch.setattr(
        models.shutil, "copyfileobj", lambda source, dest: dest.write(b"bad")
    )
    with pytest.raises(RuntimeError, match="Copied model checksum"):
        models.download("tflite", tmp_path / "runtime", tmp_path)
    assert not target.exists()
    assert not list(target.parent.glob(".agent-audio-model-*"))

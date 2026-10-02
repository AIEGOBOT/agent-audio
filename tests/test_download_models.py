import hashlib
import os
import sys
from types import SimpleNamespace

import pytest

from agent_audio import download_models as models


def setup_download(tmp_path, monkeypatch, checksum=None):
    cached = tmp_path / "cache" / "download"
    cached.parent.mkdir()
    cached.write_bytes(b"test weights")
    calls = []

    def fetch(*args, **kwargs):
        calls.append(kwargs)
        return str(cached)

    monkeypatch.setitem(
        sys.modules, "huggingface_hub", SimpleNamespace(hf_hub_download=fetch)
    )
    monkeypatch.setattr(
        models,
        "TFLITE_SHA256",
        {"dit.tflite": checksum or hashlib.sha256(cached.read_bytes()).hexdigest()},
    )
    return cached, calls


def test_download_pins_revision_and_retains_matching_model(tmp_path, monkeypatch):
    cached, calls = setup_download(tmp_path, monkeypatch)
    root = tmp_path / "runtime"
    models.download("tflite", root, cached.parent)
    target = root / "models/tflite/dit.tflite"
    original = target.stat().st_mtime_ns
    models.download("tflite", root, cached.parent)
    assert target.read_bytes() == cached.read_bytes()
    assert target.stat().st_mtime_ns == original
    assert all(c["revision"] == models.MODEL_REVISION for c in calls)


def test_corrupt_model_not_installed(tmp_path, monkeypatch):
    cached, _ = setup_download(tmp_path, monkeypatch, checksum="0" * 64)
    with pytest.raises(RuntimeError, match="checksum"):
        models.download("tflite", tmp_path / "runtime", cached.parent)
    assert not (tmp_path / "runtime/models/tflite/dit.tflite").exists()


def test_conflicting_existing_model_preserved(tmp_path, monkeypatch):
    cached, _ = setup_download(tmp_path, monkeypatch)
    target = tmp_path / "runtime/models/tflite/dit.tflite"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"keep existing")
    with pytest.raises(RuntimeError, match="conflicts"):
        models.download("tflite", tmp_path / "runtime", cached.parent)
    assert target.read_bytes() == b"keep existing"


def setup_relative_cache_link(tmp_path, monkeypatch):
    blob, calls = setup_download(tmp_path, monkeypatch)
    snapshot = blob.parent / "snapshots" / models.MODEL_REVISION / "dit.tflite"
    snapshot.parent.mkdir(parents=True)
    try:
        snapshot.symlink_to(os.path.relpath(blob, snapshot.parent))
    except (OSError, NotImplementedError):
        pytest.skip("Creating symlinks is not supported on this host")

    def fetch(*args, **kwargs):
        calls.append(kwargs)
        return str(snapshot)

    monkeypatch.setitem(
        sys.modules, "huggingface_hub", SimpleNamespace(hf_hub_download=fetch)
    )
    return blob, snapshot, calls


def test_relative_hf_cache_link_publishes_blob_and_reinstalls(tmp_path, monkeypatch):
    blob, snapshot, calls = setup_relative_cache_link(tmp_path, monkeypatch)
    root = tmp_path / "runtime"
    target = root / "models/tflite/dit.tflite"

    # HF snapshots use relative symlinks. Hardlinking the symlink itself on
    # Linux relocates its relative target and leaves a broken installed model.
    models.download("tflite", root, blob.parent)
    assert target.is_file()
    assert not target.is_symlink()
    assert target.samefile(blob)
    assert target.read_bytes() == blob.read_bytes()
    original = (target.stat().st_ino, target.stat().st_mtime_ns)
    models.download("tflite", root, blob.parent)
    assert (target.stat().st_ino, target.stat().st_mtime_ns) == original
    assert snapshot.is_symlink()
    assert snapshot.resolve() == blob
    assert all(c["revision"] == models.MODEL_REVISION for c in calls)


def test_relative_hf_cache_link_still_requires_matching_checksum(tmp_path, monkeypatch):
    blob, _, _ = setup_relative_cache_link(tmp_path, monkeypatch)
    blob.write_bytes(b"corrupt weights")
    root = tmp_path / "runtime"
    with pytest.raises(RuntimeError, match="checksum"):
        models.download("tflite", root, blob.parent)
    assert not os.path.lexists(root / "models/tflite/dit.tflite")


def test_relative_hf_cache_link_preserves_conflicting_model(tmp_path, monkeypatch):
    blob, _, _ = setup_relative_cache_link(tmp_path, monkeypatch)
    root = tmp_path / "runtime"
    target = root / "models/tflite/dit.tflite"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"keep existing")
    with pytest.raises(RuntimeError, match="conflicts"):
        models.download("tflite", root, blob.parent)
    assert target.read_bytes() == b"keep existing"


def test_missing_hf_cache_blob_is_not_published(tmp_path, monkeypatch):
    blob, snapshot, _ = setup_relative_cache_link(tmp_path, monkeypatch)
    blob.unlink()
    root = tmp_path / "runtime"
    with pytest.raises(FileNotFoundError):
        models.download("tflite", root, blob.parent)
    assert snapshot.is_symlink()
    assert not os.path.lexists(root / "models/tflite/dit.tflite")


def test_existing_broken_model_link_is_preserved(tmp_path, monkeypatch):
    blob, snapshot, _ = setup_relative_cache_link(tmp_path, monkeypatch)
    root = tmp_path / "runtime"
    target = root / "models/tflite/dit.tflite"
    target.parent.mkdir(parents=True)
    target.symlink_to(snapshot.readlink())
    original = target.readlink()
    assert not target.exists()
    with pytest.raises(RuntimeError, match="outside Agent Audio's cache"):
        models.download("tflite", root, blob.parent)
    assert target.is_symlink()
    assert target.readlink() == original

import hashlib
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

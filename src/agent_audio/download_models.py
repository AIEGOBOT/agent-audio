"""Pinned, data-only model downloads. Also runs in the dedicated runtime venv."""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
from pathlib import Path

MODEL_REPO = "stabilityai/stable-audio-3-optimized"
MODEL_REVISION = "da6edc54ddba10bfd79a077102ded687f80e882b"
# Values independently checked against a fresh download during the Windows test.
TFLITE_SHA256 = {
    "sa3-m/dit_fp32.tflite": "b811dc7d0135ca48afbc7a7bb7d19bdaaad13cbcb592418b8aa169e0c149daba",
    "same-l/dec_w8a8.tflite": "53dbca41ec9620257834bda4f3008a2cd5072afba564b84906f8ffdfca2647e7",
    "same-l/enc_w8a8.tflite": "9c76149a2fe6bd461fadf2a45b675fcd4bc64a26bd2f1d24810098a169cc41ec",
    "t5gemma/encoder_fp16.tflite": "8530d0b3e6b9b9dcf1239145c2a853fb749708eaddbb472ff8f0802b50059372",
}
MLX_FILES = (
    "dit_medium_f16.npz",
    "same_l_decoder_f32.npz",
    "same_l_encoder_f32.npz",
    "t5gemma_f16.npz",
)


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def download(backend: str, root: Path, cache: Path) -> None:
    from huggingface_hub import hf_hub_download

    manifest = TFLITE_SHA256 if backend == "tflite" else dict.fromkeys(MLX_FILES)
    prefix = "tflite" if backend == "tflite" else "MLX"
    for name, expected in manifest.items():
        target = root / "models" / backend / name
        # Always resolve via the pinned revision, even when a local model exists.
        cached = Path(
            hf_hub_download(
                MODEL_REPO, f"{prefix}/{name}", revision=MODEL_REVISION, cache_dir=cache
            )
        )
        actual = digest(cached)
        if expected and actual != expected:
            raise RuntimeError(f"Model checksum mismatch: {name}; refusing to install.")
        if os.path.lexists(target):
            # An external link is not independent, even if its contents happen to match.
            if target.is_symlink() and not target.resolve().is_relative_to(
                cache.resolve()
            ):
                raise RuntimeError(f"Model links outside Agent Audio's cache: {target}")
            if not target.is_file() or digest(target) != actual:
                raise RuntimeError(
                    f"Existing model conflicts with pinned weights: {target}; preserved."
                )
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.link(cached, target)
        except FileExistsError:
            raise RuntimeError(
                f"Model appeared during installation: {target}"
            ) from None
        except OSError:
            # Cross-device caches can copy without overwriting an existing target.
            with cached.open("rb") as source, target.open("xb") as destination:
                shutil.copyfileobj(source, destination)
        print(f"Verified {target} ({target.stat().st_size} bytes)", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", choices=("tflite", "mlx"), required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--cache", type=Path, required=True)
    args = parser.parse_args()
    download(args.backend, args.root, args.cache)


if __name__ == "__main__":
    main()

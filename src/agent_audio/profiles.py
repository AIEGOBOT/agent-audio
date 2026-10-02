"""Stable Audio model profiles kept behind the generic MCP surface."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelProfile:
    name: str
    dit: str
    decoder: str
    tflite_files: tuple[str, ...]


PROFILES = {
    "small-sfx": ModelProfile(
        "small-sfx",
        "sm-sfx",
        "same-s",
        (
            "sa3-sm-sfx/dit_fp32.tflite",
            "same-s/dec_w8a8.tflite",
            "t5gemma/encoder_fp16.tflite",
        ),
    ),
    "medium": ModelProfile(
        "medium",
        "medium",
        "same-l",
        (
            "sa3-m/dit_fp32.tflite",
            "same-l/dec_w8a8.tflite",
            "t5gemma/encoder_fp16.tflite",
        ),
    ),
}


def tflite_command(
    profile: ModelProfile,
    *,
    prompt: str,
    seconds: float,
    seed: int,
    output: str,
    steps: int = 8,
    cfg: float = 1.0,
    threads: int = 8,
) -> list[str]:
    return [
        f"--prompt={prompt}",
        "--dit",
        profile.dit,
        "--decoder",
        profile.decoder,
        "--dit-precision",
        "fp32",
        "--decoder-precision",
        "w8a8",
        "--seconds",
        str(seconds),
        "--seed",
        str(seed),
        "--steps",
        str(steps),
        "--cfg",
        str(cfg),
        "--threads",
        str(threads),
        "--init-noise-level",
        "1.0",
        "--free-models",
        "--out",
        output,
    ]

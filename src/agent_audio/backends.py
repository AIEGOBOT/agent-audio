"""Small Stable Audio adapters; no hardware-specific options cross the MCP boundary."""

from __future__ import annotations

import zipfile
from dataclasses import dataclass
from pathlib import Path

from . import download_models
from .profiles import PROFILES


@dataclass(frozen=True)
class StableAudioBackend:
    name: str
    requires_tokenizer: bool

    @property
    def script_name(self) -> str:
        return f"sa3_{self.name}.py"

    @property
    def model_files(self) -> tuple[str, ...]:
        if self.name == "tflite":
            return tuple(download_models.TFLITE_SHA256)
        return download_models.MLX_FILES

    def model_header_valid(self, path: Path) -> bool:
        if self.name == "tflite":
            with path.open("rb") as model:
                return model.read(8)[4:8] == b"TFL3"
        return zipfile.is_zipfile(path)

    def validate_negative_prompt(self, negative_prompt: str | None) -> None:
        # Both pinned scripts ignore this input with their default CFG of 1.0.
        # Changing guidance requires separate quality/resource validation.
        if negative_prompt:
            raise ValueError(
                f"negative_prompt is unsupported by the current {self.name} backend "
                "generation policy; omit it and describe the desired sound in prompt."
            )

    def generation_arguments(
        self, prompt: str, seconds: float, output: Path
    ) -> list[str]:
        profile = PROFILES["medium"]
        return [
            f"--prompt={prompt}",
            "--dit",
            profile.dit,
            "--decoder",
            profile.decoder,
            "--cfg",
            "1.0",
            "--seconds",
            str(seconds),
            "--out",
            str(output),
        ]


BACKENDS = {
    "tflite": StableAudioBackend("tflite", requires_tokenizer=True),
    "mlx": StableAudioBackend("mlx", requires_tokenizer=False),
}


def get_backend(name: str) -> StableAudioBackend:
    try:
        return BACKENDS[name]
    except KeyError:
        raise ValueError(f"Unsupported backend: {name}") from None

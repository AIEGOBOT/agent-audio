from agent_audio.detect import EnvironmentInfo, recommended_backend


def make_info(*, apple_silicon: bool = False) -> EnvironmentInfo:
    return EnvironmentInfo(
        os="Darwin" if apple_silicon else "Windows",
        architecture="64bit",
        machine="arm64" if apple_silicon else "AMD64",
        apple_silicon=apple_silicon,
        nvidia_detected=False,
        intel_graphics_detected=False,
        codex_installed=False,
        claude_installed=False,
        cursor_installed=False,
    )


def test_apple_silicon_prefers_mlx() -> None:
    assert recommended_backend(make_info(apple_silicon=True)) == "mlx"


def test_other_platforms_use_portable_tflite() -> None:
    assert recommended_backend(make_info()) == "tflite"

"""Prevent dependency-only upgrades from enabling an unsupported SDK major."""

import tomllib
from importlib.metadata import version
from pathlib import Path

from packaging.requirements import Requirement
from packaging.version import Version


def test_supported_mcp_range_and_locked_version():
    root = Path(__file__).resolve().parents[1]
    project = tomllib.loads((root / "pyproject.toml").read_text())
    requirement = next(
        Requirement(item)
        for item in project["project"]["dependencies"]
        if Requirement(item).name == "mcp"
    )
    assert Version("1.30.0") in requirement.specifier
    for unsupported in ("1.29.0", "2.0.0", "2.3.0", "3.0.0"):
        assert Version(unsupported) not in requirement.specifier
    lock = tomllib.loads((root / "uv.lock").read_text())
    locked = next(p for p in lock["package"] if p["name"] == "mcp")
    assert Version(locked["version"]).major == 1
    assert Version(locked["version"]) in requirement.specifier
    assert Version(version("mcp")) in requirement.specifier

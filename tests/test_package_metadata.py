from __future__ import annotations

import importlib
import sys
from pathlib import Path

import tomllib


ROOT = Path(__file__).resolve().parents[1]


def load_project() -> dict:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        return tomllib.load(handle)


def test_package_exposes_initial_version() -> None:
    sys.path.insert(0, str(ROOT / "src"))
    try:
        package = importlib.import_module("nature_academic_search")
    finally:
        sys.path.pop(0)

    assert package.__version__ == "0.1.0"


def test_project_declares_supported_python_and_mcp_versions() -> None:
    project = load_project()["project"]

    assert project["requires-python"] == ">=3.10"
    assert "mcp>=1.27,<2" in project["dependencies"]


def test_project_exposes_cli_and_mcp_entry_points() -> None:
    scripts = load_project()["project"]["scripts"]

    assert scripts == {
        "nature-academic-search": "nature_academic_search.cli:main",
        "nature-academic-search-mcp": "nature_academic_search.server:main",
    }

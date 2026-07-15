from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_module(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    return subprocess.run(
        [sys.executable, "-m", "nature_academic_search", *args],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_module_help_lists_supported_commands() -> None:
    completed = run_module("--help")

    assert completed.returncode == 0, completed.stderr
    for command in ("serve", "preflight", "citation", "install"):
        assert command in completed.stdout


def test_version_comes_from_package_metadata() -> None:
    completed = run_module("--version")

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "nature-academic-search 0.1.1"


def test_preflight_help_does_not_access_network() -> None:
    completed = run_module("preflight", "--help")

    assert completed.returncode == 0, completed.stderr
    assert "Check PubMed, CrossRef, and arXiv connectivity" in completed.stdout


def test_citation_help_preserves_legacy_formats() -> None:
    completed = run_module("citation", "--help")

    assert completed.returncode == 0, completed.stderr
    for citation_format in ("nbib", "ris", "bib", "enw"):
        assert citation_format in completed.stdout

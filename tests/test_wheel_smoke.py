from __future__ import annotations

import runpy
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_wheel.py"


def test_wheel_smoke_drops_source_and_personal_runtime_overrides(monkeypatch) -> None:
    overrides = {
        "PYTHONPATH": str(ROOT / "src"),
        "PYTHONHOME": "/some/other/python",
        "VIRTUAL_ENV": "/some/editable/environment",
        "NATURE_ACADEMIC_SEARCH_CONFIG": "/some/personal/config.toml",
        "ACADEMIC_SEARCH_LLM_API_KEY": "example-only",
        "CROSSREF_MAILTO": "private@example.com",
        "PUBMED_EMAIL": "private@example.com",
        "NCBI_API_KEY": "example-only",
        "OPENALEX_API_KEY": "example-only",
        "SEMANTIC_SCHOLAR_API_KEY": "example-only",
    }
    for name, value in overrides.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setenv("PATH", "/some/bin")

    environment = runpy.run_path(str(SCRIPT))["smoke_environment"]()

    remaining_overrides = set(overrides).intersection(environment)
    assert not remaining_overrides, sorted(remaining_overrides)
    assert environment["PATH"] == "/some/bin"


def test_wheel_smoke_rejects_missing_artifact_before_installing(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(tmp_path / "missing.whl")],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )

    assert result.returncode == 2
    assert "provide exactly one existing .whl file" in result.stderr


@pytest.mark.parametrize("filename", ["ci.yml", "publish.yml"])
def test_built_wheel_must_pass_smoke_before_artifact_upload(filename: str) -> None:
    workflow = yaml.safe_load((ROOT / ".github" / "workflows" / filename).read_text())
    steps = workflow["jobs"]["build"]["steps"]
    smoke = [
        index for index, step in enumerate(steps)
        if "python scripts/check_wheel.py" in step.get("run", "")
    ]
    upload = next(
        index for index, step in enumerate(steps)
        if "upload-artifact" in step.get("uses", "")
    )

    assert len(smoke) == 1, "The built wheel needs a clean installation smoke gate"
    assert smoke[0] < upload


def test_publish_runs_package_and_legacy_tests_before_building() -> None:
    workflow = yaml.safe_load((ROOT / ".github/workflows/publish.yml").read_text())
    commands = [step.get("run", "") for step in workflow["jobs"]["build"]["steps"]]
    build = commands.index("python -m build")

    assert "python -m pytest" in commands[:build]
    assert "python -m pytest mcp-server/tests" in commands[:build]

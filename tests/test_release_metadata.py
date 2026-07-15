from __future__ import annotations

from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10
    import tomli as tomllib

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_project_declares_mit_license_file() -> None:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        project = tomllib.load(handle)["project"]

    assert project["license"] == {"file": "LICENSE"}
    assert read("LICENSE").startswith("MIT License\n")


def test_readme_documents_all_supported_install_paths() -> None:
    readme = read("README.md")

    assert "uv tool install nature-academic-search" in readme
    assert "bash install.sh researcher@example.com" in readme
    assert "codex plugin marketplace add wp-a/nature-academic-search" in readme
    assert "claude plugin marketplace add wp-a/nature-academic-search" in readme


def test_readme_presents_the_chinese_research_workflow() -> None:
    readme = read("README.md")

    for required in (
        "可复现的文献检索、核验与引用导出",
        "直接这样问",
        "检索 → 去重 → 核验 → 导出",
        "Google Scholar",
        "Codex",
        "Claude Code",
        "如果这个项目",
    ):
        assert required in readme


def test_ci_covers_supported_python_and_legacy_contract() -> None:
    workflow = read(".github/workflows/ci.yml")

    assert "3.10" in workflow and "3.13" in workflow
    assert "python -m pytest" in workflow
    assert "mcp-server/tests" in workflow
    assert "python -m build" in workflow
    assert "twine check dist/*" in workflow


def test_publish_workflow_uses_oidc_without_api_token() -> None:
    workflow = read(".github/workflows/publish.yml")

    assert "id-token: write" in workflow
    assert "environment:" in workflow
    assert "pypa/gh-action-pypi-publish@release/v1" in workflow
    assert "PYPI_API_TOKEN" not in workflow
    assert "password:" not in workflow


def test_publish_workflow_uploads_release_assets_without_a_checkout() -> None:
    workflow = read(".github/workflows/publish.yml")

    assert '--repo "${{ github.repository }}"' in workflow


def test_dependabot_tracks_python_and_actions_monthly() -> None:
    config = read(".github/dependabot.yml")

    assert 'package-ecosystem: "pip"' in config
    assert 'package-ecosystem: "github-actions"' in config
    assert config.count('interval: "monthly"') == 2


def test_maintenance_runbook_records_release_gates() -> None:
    runbook = read("docs/maintenance.md")

    for required in (
        "Trusted Publisher",
        "python -m pytest",
        "twine check",
        "claude plugin validate --strict",
        "v0.1.0",
    ):
        assert required in runbook

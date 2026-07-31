from __future__ import annotations

import json
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10
    import tomli as tomllib

ROOT = Path(__file__).resolve().parents[1]
RELEASE_VERSION = "0.2.0"
DISPLAY_BRAND = "Academic Paper Search"
TECHNICAL_ID = "nature-academic-search"


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def read_json(path: str) -> dict:
    return json.loads(read(path))


def test_release_version_is_synchronized_across_package_and_plugins() -> None:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        package_version = tomllib.load(handle)["project"]["version"]

    codex_manifest = read_json("plugins/nature-academic-search/.codex-plugin/plugin.json")
    claude_manifest = read_json("plugins/nature-academic-search/.claude-plugin/plugin.json")
    claude_marketplace = read_json(".claude-plugin/marketplace.json")
    mcp = read_json("plugins/nature-academic-search/.mcp.json")
    mcp_args = mcp["mcpServers"]["nature-academic-search"]["args"]

    assert package_version == RELEASE_VERSION
    assert codex_manifest["version"] == RELEASE_VERSION
    assert claude_manifest["version"] == RELEASE_VERSION
    assert claude_marketplace["metadata"]["version"] == RELEASE_VERSION
    assert f"nature-academic-search=={RELEASE_VERSION}" in mcp_args


def test_project_declares_mit_license_file() -> None:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        project = tomllib.load(handle)["project"]

    assert project["license"] == {"file": "LICENSE"}
    assert read("LICENSE").startswith("MIT License\n")


def test_display_brand_changes_without_renaming_package_or_commands() -> None:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        project = tomllib.load(handle)["project"]
    readme = read("README.md")

    assert f"# {DISPLAY_BRAND}" in readme
    assert "Nature Academic Search" not in readme
    assert "安装标识仍为 `nature-academic-search`" in readme
    assert project["name"] == TECHNICAL_ID
    assert project["description"].startswith(DISPLAY_BRAND)
    assert set(project["scripts"]) == {
        TECHNICAL_ID,
        "nature-academic-search-mcp",
    }


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


def test_readme_explains_expanded_source_routing_without_overclaiming() -> None:
    readme = read("README.md")

    for source in (
        "CrossRef",
        "PubMed",
        "arXiv",
        "OpenAlex",
        "Europe PMC",
        "Semantic Scholar",
        "ClinicalTrials.gov",
    ):
        assert source in readme
    for contract in (
        'entity_type="trial"',
        "sources_queried",
        "sources_succeeded",
        "sources_skipped",
        "citation_counts",
        "试验注册",
    ):
        assert contract in readme


def test_community_growth_docs_track_discovery_instead_of_release_count() -> None:
    growth = read("docs/community-growth.md")
    submissions = read("docs/community-submissions.md")

    for required in (
        "Qualified third-party listings",
        "Qualified external GitHub mentions",
        "External unique referrers",
        "8-12",
        "Release count is not a growth KPI",
        "2026-08-30",
    ):
        assert required in growth

    for required in (
        "Academic and AI-for-science",
        "Agent Skills",
        "MCP catalogs and registries",
        "human action required",
        "submission_url",
    ):
        assert required in submissions


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
        "VERSION",
        "low-maintenance runtime distribution",
        "If the TestPyPI Trusted Publisher is configured",
    ):
        assert required in runbook

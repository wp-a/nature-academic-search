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
    readme = read("README.md")
    growth = read("docs/community-growth.md")
    submissions = read("docs/community-submissions.md")

    for required in (
        "Qualified third-party listings",
        "Qualified external GitHub mentions",
        "External unique referrers",
        "4-6 high-authority targets",
        "at least 100 GitHub stars",
        "previous 180 days",
        "Release count is not a growth KPI",
        "2026-08-30",
        "Prepared nominations",
        "does not count as submitted",
        "wpironman.top",
    ):
        assert required in growth

    qualified_submission_line = next(
        line for line in growth.splitlines() if "| Qualified submissions |" in line
    )
    assert "human-review packet" not in qualified_submission_line

    for required in (
        "Academic and AI-for-science",
        "Agent Skills",
        "MCP catalogs and registries",
        "Current Checkpoint",
        "human action required",
        "submission_url",
        "prepared",
        "withdrawn",
        "https://github.com/cocoafun/awesome-academic-skills/pull/2",
        "https://github.com/ai4s-research/awesome-ai-for-science/pull/86",
        "https://github.com/modelscope/Awesome-Vibe-Research/pull/17",
        "https://github.com/MinhaoXiong/awesome-automated-research/pull/7",
        "https://github.com/VoltAgent/awesome-agent-skills/pull/860",
        "https://github.com/punkpeye/awesome-mcp-servers/pull/11253",
        "https://github.com/TensorBlock/awesome-mcp-servers/issues/1491",
        "https://github.com/TensorBlock/awesome-mcp-servers/pull/1492",
        "https://tensorblock.co/mcp/servers/github-wp-a-nature-academic-search-24b4493d",
        "https://github.com/in-fun/mcpbar/pull/5",
    ):
        assert required in submissions

    assert "| Qualified submissions | 4 |" in growth
    assert "| Qualified third-party listings | 1 |" in growth
    assert "| Qualified external GitHub mentions | 1 |" in growth
    assert "| GitHub stars | 90 |" in growth
    assert "Skip repositories below 100 stars" in growth
    assert "| Withdrawn submissions | 2 |" in submissions
    assert "| Declined submissions | 1 |" in submissions
    assert "| Qualified third-party listings | 1 |" in submissions
    assert "`VoltAgent/awesome-agent-skills` | PR | declined" in submissions
    assert "`appcypher/awesome-mcp-servers` | PR branch | skipped" in submissions
    assert "`TensorBlock/awesome-mcp-servers` | Issue form | accepted" in submissions
    assert "TensorBlock MCP Server Directory" in readme


def test_real_result_examples_are_dated_grounded_and_rendered() -> None:
    cases = {
        "topic-scoping": (
            "large language models medical education",
            "10.1371/journal.pdig.0000198",
            "PubMed returned HTTP 429",
        ),
        "citation-verification": (
            "10.1038/nature14539",
            "Deep learning",
            "mismatch",
        ),
        "pubmed-mesh": (
            "D001185",
            "D000098842",
            "D004501",
        ),
    }

    for slug, required_values in cases.items():
        document = read(f"docs/examples/{slug}.md")
        assert "2026-07-31" in document
        assert "TODO" not in document
        assert "<待" not in document
        for required in required_values:
            assert required in document

        image = ROOT / "docs" / "assets" / f"academic-search-{slug}.png"
        assert image.stat().st_size > 50_000


def test_readme_leads_to_three_copyable_real_result_cases() -> None:
    readme = read("README.md")

    for required in (
        "academic-search-topic-scoping.png",
        "三个可复制的中文场景",
        "开题检索",
        "AI 幻觉引用核验",
        "PubMed / MeSH 检索",
        "docs/examples/topic-scoping.md",
        "docs/examples/citation-verification.md",
        "docs/examples/pubmed-mesh.md",
        "本次真实结果",
        "2026-07-31",
        "git clone https://github.com/wp-a/nature-academic-search.git",
        "bash install.sh --client both --email researcher@example.com",
        "PyPI `0.2.0` 与插件固定版本尚未包含该修复",
    ):
        assert required in readme


def test_mesh_example_discloses_current_main_install_boundary() -> None:
    example = read("docs/examples/pubmed-mesh.md")
    installation = read("docs/installation.md")

    for document in (example, installation):
        assert "当前 `main`" in document or "current `main`" in document
        assert "git clone https://github.com/wp-a/nature-academic-search.git" in document
        assert "bash install.sh --client both --email researcher@example.com" in document
        assert "PyPI `0.2.0`" in document
        assert "尚未包含" in document or "not present" in document


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

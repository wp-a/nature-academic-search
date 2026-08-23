from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10
    import tomli as tomllib

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "nature-academic-search"
PLUGIN_SKILL = PLUGIN / "skills" / "nature-academic-search"
DISPLAY_BRAND = "Academic Paper Search"
TECHNICAL_ID = "nature-academic-search"
PACKAGED_REFERENCES = (
    "citation-files.md",
    "search-workflows.md",
    "source-tiers.md",
)


def project_version() -> str:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        return tomllib.load(handle)["project"]["version"]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_codex_plugin_manifest_matches_package() -> None:
    manifest = load_json(PLUGIN / ".codex-plugin" / "plugin.json")

    assert manifest["name"] == "nature-academic-search"
    assert manifest["version"] == project_version()
    assert manifest["skills"] == "./skills/"
    assert manifest["mcpServers"] == "./.mcp.json"
    assert manifest["license"] == "MIT"


def test_claude_plugin_manifest_matches_package() -> None:
    manifest = load_json(PLUGIN / ".claude-plugin" / "plugin.json")

    assert manifest["$schema"] == "https://anthropic.com/claude-code/plugin.schema.json"
    assert manifest["name"] == "nature-academic-search"
    assert manifest["version"] == project_version()
    assert manifest["skills"] == ["./skills/nature-academic-search"]


def test_plugin_mcp_launches_the_release_pinned_pypi_package() -> None:
    mcp_config = load_json(PLUGIN / ".mcp.json")["mcpServers"]["nature-academic-search"]

    assert mcp_config == {
        "command": "uvx",
        "args": [
            "--from",
            f"nature-academic-search=={project_version()}",
            "nature-academic-search-mcp",
        ],
    }


def test_root_and_plugin_skills_are_synchronized_and_concise() -> None:
    root_skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    plugin_skill = (PLUGIN_SKILL / "SKILL.md").read_text(encoding="utf-8")

    assert plugin_skill == root_skill
    frontmatter = re.match(r"^---\n(.*?)\n---\n", root_skill, re.DOTALL)
    assert frontmatter
    assert "name: nature-academic-search" in frontmatter.group(1)
    assert re.search(r"description:\s*>?-?\s*\n?\s*Use when", frontmatter.group(1))
    body = root_skill[frontmatter.end() :]
    assert len(body.split()) <= 600

    for reference in PACKAGED_REFERENCES:
        assert (PLUGIN_SKILL / "references" / reference).read_bytes() == (
            ROOT / "references" / reference
        ).read_bytes()


def test_skill_sync_script_reports_clean_mirror() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/sync_skill.py", "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr


def test_skill_reference_links_exist_inside_plugin() -> None:
    skill = (PLUGIN_SKILL / "SKILL.md").read_text(encoding="utf-8")
    references = re.findall(r"\]\((references/[^)]+)\)", skill)

    assert references
    assert all((PLUGIN_SKILL / reference).is_file() for reference in references)


def test_skill_routes_chinese_research_requests_and_reports_verification() -> None:
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")

    for required in (
        "找文献",
        "文献检索",
        "任务路由",
        "verified",
        "mismatch",
        "not_found",
        "manual_needed",
        "结果契约",
        "search_run",
        "record_id",
        "result_fingerprint",
        "expected",
        "references/search-workflows.md",
        "references/source-tiers.md",
        "references/citation-files.md",
    ):
        assert required in skill


def test_skill_documents_seven_source_roles_and_entity_boundary() -> None:
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")

    for source in (
        "crossref",
        "pubmed",
        "arxiv",
        "openalex",
        "europe_pmc",
        "semantic_scholar",
        "clinicaltrials_gov",
    ):
        assert source in skill.casefold()
    for contract in (
        'entity_type="trial"',
        "sources_queried",
        "sources_succeeded",
        "sources_skipped",
        "errors",
        "citation_counts",
        "实际工具输出",
        "search_run",
        "record_id",
        "result_fingerprint",
    ):
        assert contract in skill


def test_runtime_guides_do_not_claim_unconnected_database_tools() -> None:
    paths = [ROOT / "SKILL.md", ROOT / "README.md"]
    paths.extend(sorted((ROOT / "references").glob("**/*.md")))
    content = "\n".join(path.read_text(encoding="utf-8") for path in paths)

    for unsupported_tool in (
        "search_google_scholar",
        "search_webofscience",
        "search_scopus",
        "search_biorxiv",
        "search_medrxiv",
        "pubmed_search_articles",
        "search_crossref",
        "search_arxiv",
    ):
        assert unsupported_tool not in content
    for unconnected_source in (
        "Google Scholar",
        "Web of Science",
        "Scopus",
        "Embase",
        "CNKI",
        "万方",
    ):
        assert re.search(
            rf"(?:未连接|没有连接|不包含)[^。\n]*{re.escape(unconnected_source)}",
            content,
        )


def test_codex_skill_interface_targets_chinese_researchers() -> None:
    interface = load_yaml(PLUGIN_SKILL / "agents" / "openai.yaml")["interface"]

    assert interface["display_name"] == DISPLAY_BRAND
    assert "文献" in interface["short_description"]
    assert "$nature-academic-search" in interface["default_prompt"]
    assert "检索" in interface["default_prompt"]
    assert "OpenAlex" in interface["short_description"]


def test_display_brand_changes_without_renaming_skill_or_plugins() -> None:
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    codex_manifest = load_json(PLUGIN / ".codex-plugin" / "plugin.json")
    claude_manifest = load_json(PLUGIN / ".claude-plugin" / "plugin.json")
    claude_marketplace = load_json(ROOT / ".claude-plugin" / "marketplace.json")

    assert f"# {DISPLAY_BRAND}" in skill
    assert "# Nature Academic Search" not in skill
    assert codex_manifest["name"] == TECHNICAL_ID
    assert codex_manifest["interface"]["displayName"] == DISPLAY_BRAND
    assert DISPLAY_BRAND in codex_manifest["description"]
    assert claude_manifest["name"] == TECHNICAL_ID
    assert DISPLAY_BRAND in claude_manifest["description"]
    assert claude_marketplace["plugins"][0]["name"] == TECHNICAL_ID
    assert DISPLAY_BRAND in claude_marketplace["plugins"][0]["description"]


def test_plugin_manifests_describe_expanded_source_roles() -> None:
    codex_manifest = load_json(PLUGIN / ".codex-plugin" / "plugin.json")
    claude_manifest = load_json(PLUGIN / ".claude-plugin" / "plugin.json")
    claude_marketplace = load_json(ROOT / ".claude-plugin" / "marketplace.json")

    for content in (
        codex_manifest["description"],
        codex_manifest["interface"]["longDescription"],
        claude_manifest["description"],
        claude_marketplace["plugins"][0]["description"],
    ):
        assert "OpenAlex" in content
        assert "Europe PMC" in content
        assert "ClinicalTrials.gov" in content


def test_marketplaces_point_to_the_packaged_plugin() -> None:
    codex_marketplace = load_json(ROOT / ".agents" / "plugins" / "marketplace.json")
    claude_marketplace = load_json(ROOT / ".claude-plugin" / "marketplace.json")

    assert codex_marketplace["plugins"][0]["source"]["path"] == (
        "./plugins/nature-academic-search"
    )
    assert claude_marketplace["plugins"][0]["source"] == (
        "./plugins/nature-academic-search"
    )

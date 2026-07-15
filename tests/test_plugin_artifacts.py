from __future__ import annotations

import json
import re
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
        "references/search-workflows.md",
        "references/citation-files.md",
    ):
        assert required in skill


def test_codex_skill_interface_targets_chinese_researchers() -> None:
    interface = load_yaml(PLUGIN_SKILL / "agents" / "openai.yaml")["interface"]

    assert interface["display_name"] == DISPLAY_BRAND
    assert "文献" in interface["short_description"]
    assert "$nature-academic-search" in interface["default_prompt"]
    assert "检索" in interface["default_prompt"]


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


def test_marketplaces_point_to_the_packaged_plugin() -> None:
    codex_marketplace = load_json(ROOT / ".agents" / "plugins" / "marketplace.json")
    claude_marketplace = load_json(ROOT / ".claude-plugin" / "marketplace.json")

    assert codex_marketplace["plugins"][0]["source"]["path"] == (
        "./plugins/nature-academic-search"
    )
    assert claude_marketplace["plugins"][0]["source"] == (
        "./plugins/nature-academic-search"
    )

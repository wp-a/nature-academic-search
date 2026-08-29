from __future__ import annotations

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "plugins" / "dsh-academic-paper-search"
PYPI_VERSION = "0.3.0"
DSH_MCP_CLIENT_VERSION = "0.1.1-rc.2"


class DshPatchLoader(yaml.SafeLoader):
    """Treat Cordis's JavaScript tag as a scalar for offline contract checks."""


DshPatchLoader.add_constructor(
    "tag:yaml.org,2002:js",
    lambda loader, node: loader.construct_scalar(node),
)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_patch() -> tuple[dict, str]:
    text = (BUNDLE / "cordis.patch.yml").read_text(encoding="utf-8")
    return yaml.load(text, Loader=DshPatchLoader), text


def test_dsh_bundle_manifest_is_installable_and_pinned() -> None:
    manifest = read_json(BUNDLE / "package.json")

    assert manifest["name"] == "dsh-academic-paper-search"
    assert manifest["version"] == "0.1.0"
    assert manifest["type"] == "module"
    assert manifest["main"] == "./index.js"
    assert manifest["dsh"]["bundle"]["patch"] == "./cordis.patch.yml"
    assert manifest["dependencies"]["@deepseek-ai/dsh-mcp-client"] == DSH_MCP_CLIENT_VERSION
    assert "dsh-plugin" in manifest["keywords"]
    assert "deepseek-harness" in manifest["keywords"]


def test_dsh_bundle_patch_mounts_the_pinned_academic_mcp_server() -> None:
    patch, text = read_patch()
    row = patch[0]["insert"][0]

    assert row["id"] == "academic-search-mcp"
    assert row["name"] == "@deepseek-ai/dsh-mcp-client"
    assert row["config"]["transport"] == "stdio"
    assert row["config"]["serverName"] == "academic_search"
    assert row["config"]["command"] == "uvx"
    assert row["config"]["args"] == [
        "--from",
        f"nature-academic-search=={PYPI_VERSION}",
        "nature-academic-search-mcp",
    ]
    assert row["config"]["failOnStartupError"] is False
    assert row["config"]["reconnect"]["enabled"] is True
    assert row["config"]["reconnect"]["maxAttempts"] == 10

    for env_name in (
        "PUBMED_EMAIL",
        "NCBI_API_KEY",
        "CROSSREF_MAILTO",
        "OPENALEX_API_KEY",
        "SEMANTIC_SCHOLAR_API_KEY",
    ):
        assert env_name in row["config"]["env"]
        assert f"process.env.{env_name}" in row["config"]["env"][env_name]
        assert "?? ''" in row["config"]["env"][env_name]

    assert "dsh plugin --profile <name> add dsh-academic-paper-search" in text
    assert "mcp__academic_search__" in text


def test_dsh_bundle_documentation_is_bilingual_and_states_boundaries() -> None:
    english = (BUNDLE / "README.md").read_text(encoding="utf-8")
    chinese = (BUNDLE / "README.zh.md").read_text(encoding="utf-8")

    for content in (english, chinese):
        assert "dsh plugin --profile" in content
        assert "nature-academic-search==0.3.0" in content
        assert "@deepseek-ai/dsh-mcp-client" in content
        assert "not a scholarly source" in content or "不是学术来源" in content
        assert "developer preview" in content or "developer preview" in content

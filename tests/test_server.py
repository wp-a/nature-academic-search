from __future__ import annotations

import asyncio
import importlib
import json
import sys
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def load_server():
    sys.path.insert(0, str(ROOT / "src"))
    try:
        return importlib.import_module("nature_academic_search.server")
    finally:
        sys.path.pop(0)


def test_mcp_exposes_exactly_four_backward_compatible_tools() -> None:
    server = load_server()

    tools = asyncio.run(server.mcp.list_tools())

    assert {tool.name for tool in tools} == {
        "search_papers",
        "get_paper_by_id",
        "get_citation",
        "lookup_mesh",
    }


def test_empty_identifier_is_rejected_before_source_call() -> None:
    server = load_server()

    with patch.object(server._crossref, "get_by_doi") as get_by_doi:
        result = json.loads(server.get_paper_by_id(""))

    assert result == {"error": "Empty identifier"}
    get_by_doi.assert_not_called()


def test_invalid_search_source_is_rejected_before_search() -> None:
    server = load_server()

    with patch.object(server, "search_all") as search_all:
        result = json.loads(server.search_papers("prime editing", sources=["unknown"]))

    assert result["error"].startswith("Invalid sources")
    search_all.assert_not_called()


def test_identifier_detection_accepts_urls_and_versions() -> None:
    server = load_server()

    assert server.detect_id_type("https://doi.org/10.1000/example") == "doi"
    assert server.detect_id_type("PMID:12345678") == "pmid"
    assert server.detect_id_type("https://arxiv.org/abs/2401.12345v2") == "arxiv"


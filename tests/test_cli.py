from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

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
    for command in ("serve", "preflight", "citation", "install", "workflow"):
        assert command in completed.stdout


def test_version_comes_from_package_metadata() -> None:
    completed = run_module("--version")

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "nature-academic-search 0.2.0"


def test_preflight_help_does_not_access_network() -> None:
    completed = run_module("preflight", "--help")

    assert completed.returncode == 0, completed.stderr
    assert "Check academic source connectivity" in completed.stdout


def test_legacy_preflight_script_delegates_to_packaged_command() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/preflight.py", "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "Check academic source connectivity" in completed.stdout


def test_citation_help_preserves_legacy_formats() -> None:
    completed = run_module("citation", "--help")

    assert completed.returncode == 0, completed.stderr
    for citation_format in ("nbib", "ris", "bib", "enw"):
        assert citation_format in completed.stdout


def preflight_config(
    *,
    openalex_api_key: str = "",
    semantic_scholar_api_key: str = "",
) -> SimpleNamespace:
    return SimpleNamespace(
        pubmed_email="researcher@example.org",
        pubmed_api_key="ncbi-secret",
        crossref_mailto="researcher@example.org",
        crossref_timeout=15,
        arxiv_timeout=30,
        openalex_api_key=openalex_api_key,
        openalex_timeout=20,
        semantic_scholar_api_key=semantic_scholar_api_key,
        semantic_scholar_timeout=20,
        europe_pmc_timeout=20,
        clinicaltrials_gov_timeout=20,
    )


def test_preflight_reports_all_sources_and_isolates_failures() -> None:
    from nature_academic_search import preflight

    def probe(endpoint: dict, _: SimpleNamespace) -> dict:
        if endpoint["source"] == "europe_pmc":
            return {"ok": False, "time": 0.2, "error": "HTTP 503", "metadata": {}}
        metadata = (
            {"data_version": "2026-07-20"}
            if endpoint["source"] == "clinicaltrials_gov"
            else {}
        )
        return {"ok": True, "time": 0.1, "error": None, "metadata": metadata}

    with (
        patch.object(preflight, "get_config", return_value=preflight_config()),
        patch.object(preflight, "_probe_endpoint", side_effect=probe) as probe_endpoint,
    ):
        results = preflight.check_endpoints()

    assert list(results) == [
        "crossref",
        "pubmed",
        "arxiv",
        "openalex",
        "europe_pmc",
        "semantic_scholar",
        "clinicaltrials_gov",
    ]
    assert results["europe_pmc"]["ok"] is False
    assert results["crossref"]["ok"] is True
    assert results["clinicaltrials_gov"]["metadata"]["data_version"] == (
        "2026-07-20"
    )
    assert results["semantic_scholar"]["ok"] is True
    assert results["semantic_scholar"]["skipped"] is True
    assert results["semantic_scholar"]["credential"] == {
        "name": "SEMANTIC_SCHOLAR_API_KEY",
        "status": "missing",
    }
    assert results["openalex"]["access_mode"] == "anonymous"
    assert probe_endpoint.call_count == 6
    assert "ncbi-secret" not in repr(results)
    assert "researcher@example.org" not in repr(results)


def test_preflight_runs_semantic_scholar_when_key_is_configured() -> None:
    from nature_academic_search import preflight

    config = preflight_config(
        openalex_api_key="openalex-secret",
        semantic_scholar_api_key="s2-secret",
    )
    successful = {"ok": True, "time": 0.1, "error": None, "metadata": {}}

    with (
        patch.object(preflight, "get_config", return_value=config),
        patch.object(
            preflight,
            "_probe_endpoint",
            return_value=successful,
        ) as probe_endpoint,
    ):
        results = preflight.check_endpoints()

    assert probe_endpoint.call_count == 7
    assert results["semantic_scholar"]["skipped"] is False
    assert results["semantic_scholar"]["credential"]["status"] == "configured"
    assert results["openalex"]["access_mode"] == "keyed"
    assert "openalex-secret" not in repr(results)
    assert "s2-secret" not in repr(results)


def test_clinicaltrials_version_extraction_is_optional() -> None:
    from nature_academic_search.preflight import _extract_clinicaltrials_version

    body = b'{"dataTimestamp":"2026-07-20T00:00:00Z"}'

    assert _extract_clinicaltrials_version(body, {}) == "2026-07-20T00:00:00Z"
    assert _extract_clinicaltrials_version(b"{}", {}) is None


def test_citation_preflight_uses_the_unified_skip_aware_reporter() -> None:
    from nature_academic_search import citation, preflight

    results = {
        "semantic_scholar": {
            "ok": True,
            "skipped": True,
            "time": 0.0,
            "error": None,
        }
    }
    with (
        patch.object(preflight, "check_endpoints", return_value=results),
        patch.object(preflight, "print_report", return_value=True) as print_report,
    ):
        status = citation.main(["--preflight"])

    assert status == 0
    print_report.assert_called_once_with(results)

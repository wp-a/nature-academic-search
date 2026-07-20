"""Low-cost connectivity checks for supported academic data sources."""

from __future__ import annotations

import argparse
import json
import socket
import sys
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from .config import Config, get_config

ENDPOINTS = [
    {
        "source": "crossref",
        "name": "CrossRef REST",
        "url": "https://api.crossref.org/works/10.1038/nature14539",
        "timeout_attr": "crossref_timeout",
        "affected": "DOI metadata lookup and formatted citations",
        "expect_status": 200,
    },
    {
        "source": "pubmed",
        "name": "PubMed E-utilities",
        "url": (
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
            "?db=pubmed&retmax=1&term=10.1038/nature14539%5Bdoi%5D"
        ),
        "timeout": 10,
        "affected": "PubMed search, PMID lookup, and MeSH lookup",
        "credential": ("NCBI_API_KEY", "pubmed_api_key"),
    },
    {
        "source": "arxiv",
        "name": "arXiv API",
        "url": "https://export.arxiv.org/api/query?id_list=1706.03762&max_results=1",
        "timeout_attr": "arxiv_timeout",
        "affected": "arXiv search and identifier lookup",
    },
    {
        "source": "openalex",
        "name": "OpenAlex API",
        "url": "https://api.openalex.org/works/W2741809807?select=id",
        "timeout_attr": "openalex_timeout",
        "affected": "OpenAlex publication search and enrichment metadata",
        "credential": ("OPENALEX_API_KEY", "openalex_api_key"),
    },
    {
        "source": "europe_pmc",
        "name": "Europe PMC API",
        "url": (
            "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
            "?query=EXT_ID:31452104&format=json&pageSize=1"
        ),
        "timeout_attr": "europe_pmc_timeout",
        "affected": "Europe PMC publication and PMCID lookup",
    },
    {
        "source": "semantic_scholar",
        "name": "Semantic Scholar API",
        "url": (
            "https://api.semanticscholar.org/graph/v1/paper/"
            "DOI:10.1038/nature14539?fields=paperId"
        ),
        "timeout_attr": "semantic_scholar_timeout",
        "affected": "Semantic Scholar explicit search and enrichment",
        "credential": (
            "SEMANTIC_SCHOLAR_API_KEY",
            "semantic_scholar_api_key",
        ),
        "requires_credential": True,
    },
    {
        "source": "clinicaltrials_gov",
        "name": "ClinicalTrials.gov API",
        "url": (
            "https://clinicaltrials.gov/api/v2/studies/"
            "NCT04280705?format=json"
        ),
        "timeout_attr": "clinicaltrials_gov_timeout",
        "affected": "ClinicalTrials.gov registration search and lookup",
    },
]


def check_single(
    name: str,
    url: str,
    timeout: int,
    expect_status: int | None = None,
) -> tuple[bool, float, str | None]:
    """Check one public endpoint using the legacy three-value return contract."""
    endpoint = {
        "source": name,
        "name": name,
        "url": url,
        "timeout": timeout,
        "expect_status": expect_status,
    }
    result = _probe_endpoint(endpoint, get_config())
    return result["ok"], result["time"], result["error"]


def check_endpoints() -> dict[str, dict[str, Any]]:
    """Check all seven sources without exposing configured credential values."""
    config = get_config()
    results: dict[str, dict[str, Any]] = {}
    for endpoint in ENDPOINTS:
        source = endpoint["source"]
        credential = _credential_status(endpoint, config)
        if endpoint.get("requires_credential") and credential["status"] == "missing":
            result: dict[str, Any] = {
                "ok": True,
                "time": 0.0,
                "error": None,
                "metadata": {},
                "skipped": True,
                "skip_reason": f"{credential['name']} is not configured",
            }
        else:
            result = dict(_probe_endpoint(endpoint, config))
            result["skipped"] = False

        result["name"] = endpoint["name"]
        result["affected"] = endpoint["affected"]
        if credential:
            result["credential"] = credential
        if source == "openalex":
            result["access_mode"] = (
                "keyed" if credential["status"] == "configured" else "anonymous"
            )
        results[source] = result
    return results


def _probe_endpoint(endpoint: dict[str, Any], config: Config) -> dict[str, Any]:
    """Perform one bounded request and return secret-safe status metadata."""
    url = str(endpoint["url"])
    source = str(endpoint["source"])
    headers = {"User-Agent": "nature-academic-search-preflight/0.1"}
    if source == "openalex" and config.openalex_api_key:
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}api_key={quote(config.openalex_api_key, safe='')}"
    if source == "semantic_scholar" and config.semantic_scholar_api_key:
        headers["x-api-key"] = config.semantic_scholar_api_key

    timeout = int(
        getattr(config, endpoint["timeout_attr"])
        if endpoint.get("timeout_attr")
        else endpoint.get("timeout", 10)
    )
    start = time.perf_counter()
    try:
        with urlopen(Request(url, headers=headers), timeout=timeout) as response:
            status = response.status
            body = response.read()
            response_headers = dict(response.headers.items())
        elapsed = time.perf_counter() - start
        expected = endpoint.get("expect_status")
        if expected is not None and status != expected:
            return _result(
                False,
                elapsed,
                f"unexpected HTTP {status} (expected {expected})",
            )
        metadata: dict[str, Any] = {}
        if source == "clinicaltrials_gov":
            version = _extract_clinicaltrials_version(body, response_headers)
            if version:
                metadata["data_version"] = version
        return _result(True, elapsed, None, metadata)
    except Exception as exc:
        return _result(False, time.perf_counter() - start, _safe_error(exc, timeout))


def _credential_status(endpoint: dict[str, Any], config: Config) -> dict[str, str]:
    credential = endpoint.get("credential")
    if not credential:
        return {}
    environment_name, config_attribute = credential
    return {
        "name": environment_name,
        "status": "configured" if getattr(config, config_attribute) else "missing",
    }


def _extract_clinicaltrials_version(
    body: bytes,
    headers: dict[str, Any],
) -> str | None:
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        payload = {}
    if isinstance(payload, dict):
        timestamp = payload.get("dataTimestamp")
        if timestamp:
            return str(timestamp)
        derived = payload.get("derivedSection")
        if isinstance(derived, dict):
            misc = derived.get("miscInfoModule")
            if isinstance(misc, dict) and misc.get("versionHolder"):
                return str(misc["versionHolder"])
    for name, value in headers.items():
        if name.casefold() in {"last-modified", "x-data-version"} and value:
            return str(value)
    return None


def _safe_error(exc: Exception, timeout: int) -> str:
    if isinstance(exc, (TimeoutError, socket.timeout)):
        return f"timeout after {timeout}s"
    if isinstance(exc, HTTPError):
        return f"HTTP {exc.code}"
    if isinstance(exc, URLError):
        reason = exc.reason
        if isinstance(reason, (TimeoutError, socket.timeout)):
            return f"timeout after {timeout}s"
        return type(reason).__name__ if reason is not None else "URL error"
    return type(exc).__name__


def _result(
    ok: bool,
    elapsed: float,
    error: str | None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "ok": ok,
        "time": elapsed,
        "error": error,
        "metadata": metadata or {},
    }


def print_report(results: dict[str, dict[str, Any]]) -> bool:
    """Print source-level reachability, credential state, and partial failures."""
    print("PRE-FLIGHT REPORT")
    for info in results.values():
        if info.get("skipped"):
            status = "SKIP"
            detail = f" ({info['skip_reason']})"
        elif info["ok"]:
            status = "OK"
            detail = f" ({info['time']:.1f}s)"
        else:
            status = "FAIL"
            detail = f" ({info['error']})"
        credential = info.get("credential")
        credential_detail = (
            f" [{credential['name']}: {credential['status']}]" if credential else ""
        )
        version = info.get("metadata", {}).get("data_version")
        version_detail = f" [data version: {version}]" if version else ""
        print(
            f"  {info['name']:24s}: {status}{detail}"
            f"{credential_detail}{version_detail}"
        )

    checked = [info for info in results.values() if not info.get("skipped")]
    reachable = sum(1 for info in checked if info["ok"])
    skipped = len(results) - len(checked)
    print(f"  {reachable}/{len(checked)} checked endpoints reachable; {skipped} skipped.")

    failed = [info for info in checked if not info["ok"]]
    if failed:
        print("  Affected:")
        for info in failed:
            print(f"    - {info['name']}: {info['affected']}")
    return not failed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check academic source connectivity")
    parser.parse_args(argv)
    return 0 if print_report(check_endpoints()) else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Install one wheel in a clean temporary environment and check its public interfaces."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def smoke_environment() -> dict[str, str]:
    """Prevent source imports and personal model/source configuration from leaking in."""
    prefixes = (
        "PYTHON",
        "ACADEMIC_SEARCH_",
        "NATURE_ACADEMIC_SEARCH_",
        "CROSSREF_",
        "PUBMED_",
        "NCBI_",
        "OPENALEX_",
        "SEMANTIC_SCHOLAR_",
        "EUROPE_PMC_",
        "CLINICALTRIALS_",
    )
    return {
        name: value
        for name, value in os.environ.items()
        if not name.startswith(prefixes) and name not in {"VIRTUAL_ENV", "CONDA_PREFIX"}
    }


def run(command: list[str], *, expected: int = 0, timeout: int = 30) -> str:
    result = subprocess.run(
        command,
        env=smoke_environment(),
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if result.returncode != expected:
        raise RuntimeError(
            f"{Path(command[0]).name} {' '.join(command[1:])}: "
            f"expected exit {expected}, got {result.returncode}\n"
            f"{result.stdout}\n{result.stderr}"
        )
    return result.stdout


async def check_mcp(command: Path) -> None:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    parameters = StdioServerParameters(command=str(command), env=smoke_environment())
    async with stdio_client(parameters) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            result = await session.list_tools()
            tools = {tool.name: tool for tool in result.tools}
            assert set(tools) == {
                "search_papers", "get_paper_by_id", "get_citation", "lookup_mesh",
            }, f"Unexpected MCP tools: {set(tools)}"
            assert {"entity_type", "filters", "ranking"} <= set(
                tools["search_papers"].inputSchema["properties"]
            )
            assert {"expected", "include_relations"} <= set(
                tools["get_paper_by_id"].inputSchema["properties"]
            )


def check_workflow() -> None:
    """Exercise installed workflow parsing, search, default lookup and RIS export offline."""
    from unittest.mock import patch

    from nature_academic_search.cli import main
    from nature_academic_search.sources.crossref import CrossRefSource

    record = {
        "DOI": "10.1000/wheel-smoke",
        "title": ["Installed wheel smoke record"],
        "author": [{"given": "Test", "family": "Author"}],
        "container-title": ["Smoke Journal"],
        "published": {"date-parts": [[2024]]},
        "type": "journal-article",
    }

    def source_response(path: str, **kwargs: object) -> dict:
        if path == "/works":
            return {"items": [record], "total-results": 1}
        assert path == "/works/10.1000/wheel-smoke", path
        return record

    workflow_file = Path("smoke.yml")
    workflow_file.write_text(
        "workflow: installed-wheel\n"
        "question: Installed wheel smoke record\n"
        "steps: [plan, search, verify, export]\n"
        "search:\n  sources: [crossref]\n  rows: 1\n",
        encoding="utf-8",
    )
    output = Path("artifacts")
    with (
        patch.object(CrossRefSource, "_request", side_effect=source_response) as request,
        patch(
            "requests.sessions.Session.request", side_effect=AssertionError("Unexpected network"),
        ),
    ):
        result = main([
            "workflow", "run", "--file", str(workflow_file),
            "--output", str(output), "--approve",
        ])
    assert result == 0, "Installed workflow failed"
    assert request.call_count == 2, "Workflow must both search and resolve the result"
    verification = json.loads((output / "verification.json").read_text(encoding="utf-8"))
    assert len(verification) == 1 and verification[0]["status"] == "verified", verification
    manifest = json.loads((output / "run.json").read_text(encoding="utf-8"))
    assert not manifest.get("errors"), manifest
    assert manifest["exported_count"] == 1, manifest
    ris = (output / "references.ris").read_text(encoding="utf-8")
    assert "10.1000/wheel-smoke" in ris and "Installed wheel smoke record" in ris, ris


def check_installed() -> None:
    from importlib import metadata, resources

    import nature_academic_search

    package_path = Path(nature_academic_search.__file__).resolve()
    assert package_path.is_relative_to(Path(sys.prefix).resolve()), package_path
    version = metadata.version("nature-academic-search")
    assert nature_academic_search.__version__ == version
    executables = Path(sys.executable).parent
    suffix = ".exe" if os.name == "nt" else ""
    cli = str(executables / f"nature-academic-search{suffix}")
    assert run([cli, "--version"]).strip() == f"nature-academic-search {version}"
    for subcommand in ("search", "verify", "preflight", "citation", "install", "workflow"):
        run([cli, subcommand, "--help"])
    error = json.loads(run([cli, "search", "smoke", "--sources", "invalid"], expected=1))
    assert error["error"].startswith("Invalid sources"), error
    error = json.loads(run([cli, "verify", ""], expected=1))
    assert error == {"error": "Empty identifier"}, error
    installation = run([
        cli, "install", "--client", "both", "--email", "smoke@example.com", "--dry-run",
    ])
    assert "codex mcp add" in installation and "claude mcp add" in installation
    skill = resources.files("nature_academic_search").joinpath("_skill")
    for relative in (
        "SKILL.md", "references/search-workflows.md", "references/source-tiers.md",
        "references/citation-files.md", "agents/openai.yaml",
    ):
        assert skill.joinpath(relative).read_text(encoding="utf-8").strip(), relative
    skill_text = skill.joinpath("SKILL.md").read_text(encoding="utf-8")
    assert "search_papers" in skill_text and "get_paper_by_id" in skill_text
    asyncio.run(asyncio.wait_for(
        check_mcp(executables / f"nature-academic-search-mcp{suffix}"), timeout=20,
    ))
    check_workflow()
    print(f"Installed wheel smoke passed: nature-academic-search {version}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wheel", nargs="?", type=Path, help="Path to a built .whl")
    parser.add_argument("--installed", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.installed:
        check_installed()
        return 0
    if args.wheel is None or not args.wheel.is_file() or args.wheel.suffix != ".whl":
        parser.error("provide exactly one existing .whl file")
    wheel = args.wheel.resolve()
    script = Path(__file__).resolve()
    with tempfile.TemporaryDirectory(prefix="academic-wheel-smoke-") as temporary:
        destination = Path(temporary)
        environment = destination / "venv"
        run([sys.executable, "-I", "-m", "venv", str(environment)], timeout=60)
        executable_directory = environment / ("Scripts" if os.name == "nt" else "bin")
        python = executable_directory / ("python.exe" if os.name == "nt" else "python")
        run([
            str(python), "-I", "-m", "pip", "install", "--quiet", "--no-input",
            "--disable-pip-version-check", str(wheel),
        ], timeout=180)
        run([str(python), "-I", "-m", "pip", "check"])
        # Console scripts run outside the checkout, without editable installs or PYTHONPATH.
        previous_directory = Path.cwd()
        try:
            os.chdir(destination)
            print(run([str(python), "-I", str(script), "--installed"], timeout=90), end="")
        finally:
            os.chdir(previous_directory)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Install the managed skill and register the MCP server with supported clients."""

from __future__ import annotations

import argparse
import os
import shlex
import shutil
import subprocess
from collections.abc import Callable, Sequence
from importlib import resources
from pathlib import Path
from typing import Any


SERVER_NAME = "nature-academic-search"
SERVER_COMMAND = "nature-academic-search-mcp"
Runner = Callable[..., Any]


def register_client(
    client: str,
    email: str,
    *,
    runner: Runner = subprocess.run,
    dry_run: bool = False,
    printer: Callable[[str], None] = print,
) -> None:
    get_command, remove_command, add_command = _registration_commands(client, email)

    if dry_run:
        printer(f"check: {shlex.join(get_command)}")
        printer(f"replace if present: {shlex.join(remove_command)}")
        printer(shlex.join(add_command))
        return

    existing = runner(get_command, capture_output=True, text=True, check=False)
    if existing.returncode == 0:
        runner(remove_command, capture_output=True, text=True, check=True)
    runner(add_command, capture_output=True, text=True, check=True)


def install_skill(client: str, source: Path, *, home: Path | None = None) -> Path:
    base_home = home or Path.home()
    client_root = ".codex" if client == "codex" else ".claude"
    target = base_home / client_root / "skills" / SERVER_NAME
    target.mkdir(parents=True, exist_ok=True)

    shutil.copy2(source / "SKILL.md", target / "SKILL.md")
    for directory in ("references", "agents"):
        source_directory = source / directory
        if source_directory.is_dir():
            shutil.copytree(source_directory, target / directory, dirs_exist_ok=True)
    return target


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Install the nature-academic-search skill and MCP server",
    )
    parser.add_argument("--client", choices=("codex", "claude", "both"), default="both")
    parser.add_argument("--email", default=os.environ.get("PUBMED_EMAIL"))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skill-source", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    if not args.email:
        parser.error("--email or PUBMED_EMAIL is required for PubMed access")

    clients = ("codex", "claude") if args.client == "both" else (args.client,)
    source = args.skill_source or _packaged_skill_source()

    for client in clients:
        if args.dry_run:
            print(f"copy skill to ~/.{client}/skills/{SERVER_NAME}")
        else:
            if shutil.which(client) is None:
                parser.error(f"{client} CLI is not installed or not on PATH")
            target = install_skill(client, source)
            print(f"installed skill: {target}")
        register_client(client, args.email, dry_run=args.dry_run)
    return 0


def _registration_commands(client: str, email: str) -> tuple[list[str], list[str], list[str]]:
    if client == "codex":
        return (
            ["codex", "mcp", "get", SERVER_NAME, "--json"],
            ["codex", "mcp", "remove", SERVER_NAME],
            [
                "codex",
                "mcp",
                "add",
                SERVER_NAME,
                "--env",
                f"PUBMED_EMAIL={email}",
                "--",
                SERVER_COMMAND,
            ],
        )
    if client == "claude":
        return (
            ["claude", "mcp", "get", SERVER_NAME],
            ["claude", "mcp", "remove", "--scope", "user", SERVER_NAME],
            [
                "claude",
                "mcp",
                "add",
                "--scope",
                "user",
                "--env",
                f"PUBMED_EMAIL={email}",
                SERVER_NAME,
                "--",
                SERVER_COMMAND,
            ],
        )
    raise ValueError(f"Unsupported client: {client}")


def _packaged_skill_source() -> Path:
    return Path(str(resources.files("nature_academic_search").joinpath("_skill")))

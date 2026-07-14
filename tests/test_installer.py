from __future__ import annotations

import importlib
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]


def load_installer():
    sys.path.insert(0, str(ROOT / "src"))
    try:
        return importlib.import_module("nature_academic_search.installer")
    finally:
        sys.path.pop(0)


class RecordingRunner:
    def __init__(self, get_returncode: int = 1):
        self.get_returncode = get_returncode
        self.calls: list[list[str]] = []

    def __call__(self, command, **kwargs):
        normalized = list(command)
        self.calls.append(normalized)
        returncode = self.get_returncode if "get" in normalized else 0
        return SimpleNamespace(returncode=returncode, stdout="", stderr="")


def test_codex_registration_replaces_existing_entry() -> None:
    installer = load_installer()
    runner = RecordingRunner(get_returncode=0)

    installer.register_client("codex", "researcher@example.com", runner=runner)

    assert runner.calls == [
        ["codex", "mcp", "get", "nature-academic-search", "--json"],
        ["codex", "mcp", "remove", "nature-academic-search"],
        [
            "codex",
            "mcp",
            "add",
            "nature-academic-search",
            "--env",
            "PUBMED_EMAIL=researcher@example.com",
            "--",
            "nature-academic-search-mcp",
        ],
    ]


def test_claude_registration_uses_user_scope() -> None:
    installer = load_installer()
    runner = RecordingRunner(get_returncode=1)

    installer.register_client("claude", "researcher@example.com", runner=runner)

    assert runner.calls == [
        ["claude", "mcp", "get", "nature-academic-search"],
        [
            "claude",
            "mcp",
            "add",
            "--scope",
            "user",
            "--env",
            "PUBMED_EMAIL=researcher@example.com",
            "nature-academic-search",
            "--",
            "nature-academic-search-mcp",
        ],
    ]


def test_skill_install_copies_only_managed_artifacts(tmp_path: Path) -> None:
    installer = load_installer()
    source = tmp_path / "source"
    (source / "references").mkdir(parents=True)
    (source / "agents").mkdir()
    (source / "SKILL.md").write_text("skill", encoding="utf-8")
    (source / "references" / "workflow.md").write_text("workflow", encoding="utf-8")
    (source / "agents" / "openai.yaml").write_text("interface: {}\n", encoding="utf-8")
    home = tmp_path / "home"

    target = installer.install_skill("codex", source, home=home)

    assert target == home / ".codex" / "skills" / "nature-academic-search"
    assert (target / "SKILL.md").read_text(encoding="utf-8") == "skill"
    assert (target / "references" / "workflow.md").is_file()
    assert (target / "agents" / "openai.yaml").is_file()


def run_install_script(tmp_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["HOME"] = str(tmp_path / "home")
    return subprocess.run(
        ["bash", "install.sh", *args],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_shell_installer_dry_run_is_dual_client_and_non_mutating(tmp_path: Path) -> None:
    completed = run_install_script(
        tmp_path,
        "--client",
        "both",
        "--email",
        "researcher@example.com",
        "--dry-run",
    )

    assert completed.returncode == 0, completed.stderr
    assert "uv tool install" in completed.stdout or "pipx install" in completed.stdout
    assert "codex mcp add" in completed.stdout
    assert "claude mcp add" in completed.stdout
    assert "pip install" not in completed.stdout
    assert not (tmp_path / "home").exists()


def test_shell_installer_preserves_legacy_positional_email(tmp_path: Path) -> None:
    completed = run_install_script(
        tmp_path,
        "legacy@example.com",
        "--client",
        "codex",
        "--dry-run",
    )

    assert completed.returncode == 0, completed.stderr
    assert "PUBMED_EMAIL=legacy@example.com" in completed.stdout
    assert "claude mcp add" not in completed.stdout

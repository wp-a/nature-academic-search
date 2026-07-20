#!/usr/bin/env python3
"""Synchronize the canonical skill files into the distributable plugin."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_SKILL = (
    ROOT / "plugins" / "nature-academic-search" / "skills" / "nature-academic-search"
)
FILES = (
    Path("SKILL.md"),
    Path("references/citation-files.md"),
    Path("references/search-workflows.md"),
    Path("references/source-tiers.md"),
)


def target_for(source: Path) -> Path:
    if source.name == "SKILL.md":
        return PLUGIN_SKILL / "SKILL.md"
    return PLUGIN_SKILL / "references" / source.name


def check() -> list[str]:
    mismatches = []
    for relative in FILES:
        source = ROOT / relative
        target = target_for(relative)
        if not target.is_file() or source.read_bytes() != target.read_bytes():
            mismatches.append(str(relative))
    return mismatches


def sync() -> None:
    for relative in FILES:
        source = ROOT / relative
        target = target_for(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail when mirrors differ")
    args = parser.parse_args(argv)

    if args.check:
        mismatches = check()
        if mismatches:
            print("Skill mirror is out of date: " + ", ".join(mismatches), file=sys.stderr)
            return 1
        print("Skill mirror is synchronized")
        return 0

    sync()
    print("Synchronized canonical skill into plugin")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

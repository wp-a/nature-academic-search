from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_sources_import_without_repository_working_directory(tmp_path: Path) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")

    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from nature_academic_search.sources import "
                "ArxivSource, CrossRefSource, PubMedSource; "
                "assert all((ArxivSource, CrossRefSource, PubMedSource))"
            ),
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr


def test_logging_setup_is_idempotent() -> None:
    sys.path.insert(0, str(ROOT / "src"))
    try:
        from nature_academic_search.logging import JSONFormatter, setup_logging

        logger = setup_logging()
        first_handlers = tuple(logger.handlers)
        same_logger = setup_logging()
    finally:
        sys.path.pop(0)

    assert same_logger is logger
    assert tuple(same_logger.handlers) == first_handlers
    assert sum(isinstance(handler.formatter, JSONFormatter) for handler in first_handlers) == 1

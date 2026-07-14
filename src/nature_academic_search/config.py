"""Runtime configuration loaded from environment variables or an optional TOML file."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import toml


class Config:
    def __init__(self, config_path: str | Path | None = None):
        selected_path = config_path or os.environ.get("NATURE_ACADEMIC_SEARCH_CONFIG")
        self._config: dict[str, Any] = {}
        if selected_path:
            path = Path(selected_path).expanduser()
            if path.is_file():
                self._config = toml.load(path)

    @property
    def pubmed_email(self) -> str:
        return os.environ.get("PUBMED_EMAIL") or self._value("pubmed", "email", "")

    @property
    def pubmed_api_key(self) -> str:
        return os.environ.get("NCBI_API_KEY") or self._value("pubmed", "api_key", "")

    @property
    def crossref_mailto(self) -> str:
        return os.environ.get("CROSSREF_MAILTO") or self._value("crossref", "mailto", "")

    @property
    def crossref_timeout(self) -> int:
        return int(os.environ.get("CROSSREF_TIMEOUT") or self._value("crossref", "timeout", 15))

    @property
    def arxiv_timeout(self) -> int:
        return int(os.environ.get("ARXIV_TIMEOUT") or self._value("arxiv", "timeout", 30))

    @property
    def default_rows(self) -> int:
        return int(os.environ.get("ACADEMIC_SEARCH_DEFAULT_ROWS") or 5)

    @property
    def max_rows(self) -> int:
        return int(os.environ.get("ACADEMIC_SEARCH_MAX_ROWS") or 50)

    def _value(self, section: str, key: str, default: Any) -> Any:
        return self._config.get(section, {}).get(key, default)


_config: Config | None = None


def get_config() -> Config:
    global _config
    if _config is None:
        _config = Config()
    return _config

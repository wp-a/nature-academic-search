"""Stable error types for academic search operations."""

from __future__ import annotations


class AcademicSearchError(Exception):
    """Base exception for academic search operations."""


class DataSourceError(AcademicSearchError):
    """Error returned by a specific literature source."""

    def __init__(self, source: str, message: str, original_error: Exception | None = None):
        self.source = source
        self.original_error = original_error
        super().__init__(f"[{source}] {message}")


class TimeoutError(AcademicSearchError):
    """A source request exceeded its retry or timeout budget."""


class ConfigError(AcademicSearchError):
    """Invalid academic search configuration."""

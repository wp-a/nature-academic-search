"""Data source modules for academic search."""

from .crossref import CrossRefSource
from .pubmed import PubMedSource
from .arxiv import ArxivSource

__all__ = ["CrossRefSource", "PubMedSource", "ArxivSource"]

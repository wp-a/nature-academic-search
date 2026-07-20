"""Data source adapters for academic search."""

from .arxiv import ArxivSource
from .crossref import CrossRefSource
from .openalex import OpenAlexSource
from .pubmed import PubMedSource

__all__ = ["ArxivSource", "CrossRefSource", "OpenAlexSource", "PubMedSource"]

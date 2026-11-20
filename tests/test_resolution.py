from __future__ import annotations

import sys
from types import SimpleNamespace
from unittest.mock import Mock, patch

from nature_academic_search import resolution
from nature_academic_search.workflow import WorkflowRunner


def test_default_workflow_lookup_does_not_load_mcp_server() -> None:
    record = {"title": "An example publication", "doi": "10.1000/example"}
    resolve = Mock(return_value=record)
    adapters = {"crossref": SimpleNamespace(get_by_doi=resolve)}
    with (
        patch.dict(sys.modules, {"nature_academic_search.server": None}),
        patch.object(resolution, "runtime_adapters", return_value=adapters),
    ):
        assert WorkflowRunner().lookup_fn("https://doi.org/10.1000/example", "doi") == record

    resolve.assert_called_once_with("10.1000/example")

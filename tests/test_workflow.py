from __future__ import annotations

import json
from pathlib import Path

import pytest

from nature_academic_search.workflow import WorkflowRunner, WorkflowSpec


def spec(**overrides: object) -> WorkflowSpec:
    data: dict[str, object] = {
        "workflow": "literature-review",
        "question": "AI safety in medicine",
        "steps": ["plan", "search", "verify", "screen", "export"],
        "search": {"entity_type": "publication", "sources": ["crossref"], "rows": 2},
        "outputs": [
            "run.json",
            "results.json",
            "verification.json",
            "screening.csv",
            "references.ris",
            "report.md",
        ],
    }
    data.update(overrides)
    return WorkflowSpec.from_mapping(data)


def test_workflow_spec_rejects_unknown_steps_and_normalizes_defaults() -> None:
    with pytest.raises(ValueError, match="Unsupported workflow step"):
        WorkflowSpec.from_mapping({"workflow": "x", "question": "q", "steps": ["unknown"]})

    parsed = WorkflowSpec.from_mapping({"workflow": "x", "question": "q"})

    assert parsed.steps == ("plan", "search", "verify", "screen", "export")
    assert parsed.search["entity_type"] == "publication"
    assert "run.json" in parsed.outputs


def test_workflow_requires_approval_before_search(tmp_path: Path) -> None:
    called = False

    def search(_: WorkflowSpec) -> dict:
        nonlocal called
        called = True
        raise AssertionError("search must not run before approval")

    result = WorkflowRunner(search_fn=search).run(spec(), tmp_path)

    assert result["status"] == "approval_required"
    assert called is False
    assert (tmp_path / "plan.json").is_file()
    assert not (tmp_path / "results.json").exists()


def test_workflow_runs_auditable_search_verify_screen_and_export(tmp_path: Path) -> None:
    result_record = {
        "entity_type": "publication",
        "record_id": "publication:doi:10.1000/example",
        "doi": "10.1000/example",
        "title": "AI safety in medicine",
        "authors": ["Jane Doe"],
        "year": 2024,
        "journal": "Example Journal",
        "abstract": "Short abstract",
    }

    def search(_: WorkflowSpec) -> dict:
        return {
            "search_run": {"schema_version": "1", "run_id": "search-1"},
            "results": [result_record],
            "errors": None,
        }

    def lookup(identifier: str, _: str) -> dict:
        assert identifier == "10.1000/example"
        return dict(result_record)

    class Provider:
        def generate_json(self, task: str, payload: dict, *, allow_full_text: bool = False) -> dict:
            assert task == "screen"
            assert allow_full_text is False
            assert "abstract" in payload["records"][0]
            return {
                "decisions": [
                    {
                        "record_id": result_record["record_id"],
                        "decision": "include",
                        "reason": "on topic",
                    }
                ]
            }

    result = WorkflowRunner(search_fn=search, lookup_fn=lookup, provider=Provider()).run(
        spec(), tmp_path, approve=True
    )

    assert result["status"] == "completed"
    assert set(result["artifacts"]) >= {
        "run.json",
        "results.json",
        "verification.json",
        "screening.csv",
        "references.ris",
        "report.md",
    }
    assert json.loads((tmp_path / "verification.json").read_text())[0]["status"] == "verified"
    assert "10.1000/example" in (tmp_path / "references.ris").read_text()
    assert "include" in (tmp_path / "screening.csv").read_text()
    assert json.loads((tmp_path / "run.json").read_text())["search_run"]["run_id"] == "search-1"


def test_provider_failure_skips_screening_but_keeps_export(tmp_path: Path) -> None:
    record = {
        "entity_type": "publication",
        "record_id": "publication:doi:10.1000/example",
        "doi": "10.1000/example",
        "title": "Example",
        "year": 2024,
    }

    class Unavailable:
        def generate_json(self, *args: object, **kwargs: object) -> dict:
            raise RuntimeError("gateway unavailable")

    def search(_: WorkflowSpec) -> dict:
        return {"search_run": {}, "results": [record], "errors": None}

    def lookup(_: str, __: str) -> dict:
        return dict(record)

    result = WorkflowRunner(
        search_fn=search, lookup_fn=lookup, provider=Unavailable()
    ).run(spec(), tmp_path, approve=True)

    assert result["status"] == "completed_with_skips"
    assert result["model_steps"]["screen"]["status"] == "skipped"
    assert "pending_manual" in (tmp_path / "screening.csv").read_text()
    assert "10.1000/example" in (tmp_path / "references.ris").read_text()

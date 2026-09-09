from __future__ import annotations

import json
from pathlib import Path

import pytest

from nature_academic_search.errors import DataSourceError
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


def test_provider_failure_keeps_pending_records_out_of_export(tmp_path: Path) -> None:
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
    assert (tmp_path / "references.ris").read_text() == ""
    assert json.loads((tmp_path / "verification.json").read_text())[0]["status"] == "verified"


def test_workflow_expands_citation_graph_only_when_step_is_explicit(tmp_path: Path) -> None:
    record = {
        "entity_type": "publication",
        "record_id": "publication:doi:10.1000/example",
        "doi": "10.1000/example",
        "title": "Example",
        "year": 2024,
    }

    def search(_: WorkflowSpec) -> dict:
        return {"results": [record], "errors": None}

    calls: list[dict] = []

    def graph_fn(seed: dict, **kwargs: object) -> dict:
        calls.append({"seed": seed, **kwargs})
        return {"schema_version": "1", "seed_record_id": seed["record_id"], "edges": []}

    workflow = spec(
        steps=["plan", "search", "expand_citations"],
        citation_graph={"relation": "references", "depth": 2, "sources": ["crossref"]},
    )
    result = WorkflowRunner(search_fn=search, graph_fn=graph_fn).run(
        workflow, tmp_path, approve=True
    )

    assert result["status"] == "completed"
    graph_payload = json.loads((tmp_path / "graph.json").read_text())
    assert graph_payload["graph_count"] == 1
    assert calls[0]["depth"] == 2
    assert calls[0]["relation_sources"] == ("crossref",)


@pytest.mark.parametrize(
    ("field", "identifier", "adapter", "method"),
    [
        ("doi", "10.1038/nature14539", "_crossref", "get_by_doi"),
        ("pmid", "28344011", "_pubmed", "get_by_pmid"),
        ("pmcid", "PMC12345", "_europe_pmc", "get_by_pmcid"),
        ("arxiv_id", "1706.03762", "_arxiv", "get_by_id"),
        ("openalex_id", "W12345", "_openalex", "get_by_id"),
        ("semantic_scholar_id", "paper-id", "_semantic_scholar", "get_by_id"),
        ("nct_id", "NCT01234567", "_clinicaltrials", "get_by_id"),
    ],
)
def test_default_workflow_resolves_identifiers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    field: str, identifier: str, adapter: str, method: str,
) -> None:
    from nature_academic_search import server

    record = {
        field: identifier,
        "title": "Example record",
        "entity_type": "trial" if field == "nct_id" else "publication",
    }
    queried = []

    def resolve(value: str) -> dict:
        queried.append(value)
        return dict(record)

    monkeypatch.setattr(getattr(server, adapter), method, resolve)
    WorkflowRunner(search_fn=lambda _: {"results": [record]}).run(
        spec(steps=["plan", "search", "verify"]), tmp_path, approve=True
    )

    checked = json.loads((tmp_path / "verification.json").read_text())[0]
    assert queried == [identifier]
    assert checked["status"] == "verified"
    assert checked["fields"]["title"]["status"] == "match"


@pytest.mark.parametrize(
    ("source_error", "expected_status"),
    [("Identifier not found", "not_found"), ("HTTP 404 from API", "not_found"),
     ("Request timed out", "manual_needed")],
)
def test_default_workflow_distinguishes_missing_records_from_source_failures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    source_error: str, expected_status: str,
) -> None:
    from nature_academic_search import server

    record = {"doi": "10.1000/example", "title": "Example"}

    def fail(_: str) -> dict:
        raise DataSourceError("crossref", source_error)

    monkeypatch.setattr(server._crossref, "get_by_doi", fail)
    result = WorkflowRunner(search_fn=lambda _: {"results": [record]}).run(
        spec(steps=["plan", "search", "verify", "export"]), tmp_path, approve=True
    )

    checked = json.loads((tmp_path / "verification.json").read_text())[0]
    assert checked["status"] == expected_status
    assert (tmp_path / "references.ris").read_text() == ""
    if expected_status == "manual_needed":
        assert checked["method"] == "workflow_lookup_error"
        assert result["errors"][0]["step"] == "verify"


def test_default_workflow_keeps_missing_identifiers_for_manual_review(tmp_path: Path) -> None:
    WorkflowRunner(search_fn=lambda _: {"results": [{"title": "No identifier"}]}).run(
        spec(steps=["plan", "search", "verify"]), tmp_path, approve=True
    )
    checked = json.loads((tmp_path / "verification.json").read_text())[0]
    assert checked["status"] == "manual_needed"
    assert checked["method"] == "workflow_missing_identifier"


@pytest.mark.parametrize("decision", ["include", "exclude", "pending_manual", "invalid", None])
def test_screened_export_requires_explicit_inclusion(tmp_path: Path, decision: str | None) -> None:
    record = {"doi": "10.1000/example", "title": "Example"}

    class Provider:
        def generate_json(self, task: str, payload: dict, **kwargs: object) -> dict:
            return {"decisions": [] if decision is None else [{
                "record_id": payload["records"][0]["record_id"], "decision": decision,
            }]}

    result = WorkflowRunner(
        search_fn=lambda _: {"results": [record]}, lookup_fn=lambda *_: dict(record),
        provider=Provider(),
    ).run(spec(), tmp_path, approve=True)

    exported = (tmp_path / "references.ris").read_text()
    assert (record["doi"] in exported) is (decision == "include")
    manifest = json.loads((tmp_path / "run.json").read_text())
    assert result["exported_count"] == manifest["exported_count"] == int(decision == "include")
    assert f"导出记录：{int(decision == 'include')}" in (tmp_path / "report.md").read_text()


@pytest.mark.parametrize("screen_enabled", [True, False])
def test_no_model_export_respects_whether_screening_is_requested(
    tmp_path: Path, screen_enabled: bool,
) -> None:
    record = {"doi": "10.1000/example", "title": "Example"}
    steps = ["plan", "search", "verify", "export"]
    if screen_enabled:
        steps.insert(-1, "screen")
    WorkflowRunner(
        search_fn=lambda _: {"results": [record]}, lookup_fn=lambda *_: dict(record),
    ).run(spec(steps=steps), tmp_path, approve=True)
    assert (record["doi"] in (tmp_path / "references.ris").read_text()) is not screen_enabled


def test_screening_cannot_override_verification_or_export_trials_as_papers(tmp_path: Path) -> None:
    records = [
        {"doi": "10.1000/good", "title": "Good"},
        {"doi": "10.1000/wrong", "title": "Incorrect title"},
        {"entity_type": "trial", "nct_id": "NCT01234567", "title": "Trial registration"},
    ]

    def lookup(identifier: str, _: str) -> dict:
        record = next(r for r in records if identifier in (r.get("doi"), r.get("nct_id")))
        return {**record, "title": "Correct title"} if identifier.endswith("wrong") else record

    class Provider:
        def generate_json(self, task: str, payload: dict, **kwargs: object) -> dict:
            return {"decisions": [
                {"record_id": record["record_id"], "decision": "include"}
                for record in payload["records"]
            ]}

    result = WorkflowRunner(
        search_fn=lambda _: {"results": records}, lookup_fn=lookup, provider=Provider(),
    ).run(spec(), tmp_path, approve=True)

    exported = (tmp_path / "references.ris").read_text()
    assert "10.1000/good" in exported
    assert "10.1000/wrong" not in exported
    assert "Trial registration" not in exported
    assert result["exported_count"] == 1


def test_default_verification_handles_crossref_author_truncation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from nature_academic_search import server

    raw = {
        "DOI": "10.1000/many-authors", "title": ["Many authors"],
        "author": [{"given": "Author", "family": str(index)} for index in range(8)],
        "published-print": {"date-parts": [[2024]]}, "container-title": ["Journal"],
    }
    candidate = server._crossref._normalize_search_item(raw)
    actual = server._crossref._normalize_detail_item(raw)
    assert candidate["authors"][-1] == "et al."
    monkeypatch.setattr(server._crossref, "get_by_doi", lambda _: actual)
    WorkflowRunner(search_fn=lambda _: {"results": [candidate]}).run(
        spec(steps=["plan", "search", "verify", "export"]), tmp_path, approve=True
    )
    checked = json.loads((tmp_path / "verification.json").read_text())[0]
    assert checked["status"] == "verified"
    assert checked["fields"]["authors"]["status"] == "match"
    assert "10.1000/many-authors" in (tmp_path / "references.ris").read_text()
    assert "AU  - et al." not in (tmp_path / "references.ris").read_text()


def test_workflow_discloses_secondary_ids_outside_lookup_scope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from nature_academic_search import server

    candidate = {
        "doi": "10.1000/merged", "pmid": "28344011", "openalex_id": "W12345",
        "title": "Merged record", "year": 2024,
    }
    actual = {key: value for key, value in candidate.items() if key not in {"pmid", "openalex_id"}}
    monkeypatch.setattr(server._crossref, "get_by_doi", lambda _: actual)
    WorkflowRunner(search_fn=lambda _: {"results": [candidate]}).run(
        spec(steps=["plan", "search", "verify", "export"]), tmp_path, approve=True
    )
    checked = json.loads((tmp_path / "verification.json").read_text())[0]
    assert checked["status"] == "verified"
    assert checked["unchecked_identifiers"] == ["pmid", "openalex_id"]
    assert checked["fields"]["doi"]["status"] == "match"
    exported = (tmp_path / "references.ris").read_text()
    assert "10.1000/merged" in exported
    assert "PMID:" not in exported
    assert json.loads((tmp_path / "results.json").read_text())["results"][0]["pmid"] == "28344011"


@pytest.mark.parametrize(
    ("actual", "status"),
    [
        ({"title": "Example", "pmid": "28344011"}, "manual_needed"),
        ({"title": "Example", "doi": "10.1000/example", "pmid": "12345678"}, "mismatch"),
    ],
)
def test_verification_scope_preserves_missing_primary_and_conflicting_secondary_ids(
    tmp_path: Path, actual: dict, status: str,
) -> None:
    record = {"title": "Example", "doi": "10.1000/example", "pmid": "28344011"}
    WorkflowRunner(
        search_fn=lambda _: {"results": [record]}, lookup_fn=lambda *_: actual,
    ).run(spec(steps=["plan", "search", "verify", "export"]), tmp_path, approve=True)
    checked = json.loads((tmp_path / "verification.json").read_text())[0]
    assert checked["status"] == status
    assert checked["unchecked_identifiers"] == []
    assert (tmp_path / "references.ris").read_text() == ""

"""Local declarative research workflow runner with auditable artifacts."""

from __future__ import annotations

import asyncio
import csv
import inspect
import json
import re
import uuid
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .graph import DEFAULT_RELATION_SOURCES, build_citation_graph
from .provenance import stable_record_id
from .search import search_all
from .verification import verify_record

DEFAULT_WORKFLOW_STEPS = ("plan", "search", "verify", "screen", "export")
WORKFLOW_STEPS = (*DEFAULT_WORKFLOW_STEPS, "expand_citations")
DEFAULT_OUTPUTS = (
    "run.json",
    "results.json",
    "verification.json",
    "screening.csv",
    "references.ris",
    "report.md",
)


@dataclass(frozen=True)
class WorkflowSpec:
    workflow: str
    question: str
    steps: tuple[str, ...]
    search: dict[str, Any]
    outputs: tuple[str, ...]
    verification: dict[str, Any]
    screening: dict[str, Any]
    citation_graph: dict[str, Any]
    privacy: dict[str, Any]

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> WorkflowSpec:
        if not isinstance(raw, Mapping):
            raise ValueError("workflow must be an object")
        workflow = str(raw.get("workflow") or "").strip()
        question = str(raw.get("question") or "").strip()
        if not workflow:
            raise ValueError("workflow name is required")
        if not question:
            raise ValueError("question is required")
        raw_steps = raw.get("steps") or DEFAULT_WORKFLOW_STEPS
        if isinstance(raw_steps, str):
            raw_steps = [raw_steps]
        steps = tuple(str(step).strip() for step in raw_steps)
        unsupported = [step for step in steps if step not in WORKFLOW_STEPS]
        if unsupported:
            raise ValueError(f"Unsupported workflow step(s): {unsupported}")
        outputs = raw.get("outputs") or DEFAULT_OUTPUTS
        if isinstance(outputs, str):
            outputs = [outputs]
        normalized_outputs = tuple(str(output).strip() for output in outputs)
        for output in normalized_outputs:
            if not output or Path(output).name != output:
                raise ValueError("workflow outputs must be file names without path separators")
        search = dict(raw.get("search") or {})
        search.setdefault("entity_type", "publication")
        search.setdefault("rows", 20)
        if search["entity_type"] not in {"publication", "trial"}:
            raise ValueError("search.entity_type must be 'publication' or 'trial'")
        raw_graph = raw.get("citation_graph") or {}
        if not isinstance(raw_graph, Mapping):
            raise ValueError("citation_graph must be an object")
        citation_graph = dict(raw_graph)
        graph_relation = str(citation_graph.get("relation") or "both")
        if graph_relation not in {"references", "cited_by", "both"}:
            raise ValueError("citation_graph.relation must be 'references', 'cited_by', or 'both'")
        graph_depth = citation_graph.get("depth", 1)
        if (
            not isinstance(graph_depth, int)
            or isinstance(graph_depth, bool)
            or graph_depth not in {1, 2}
        ):
            raise ValueError("citation_graph.depth must be 1 or 2")
        graph_rows = citation_graph.get("rows", 20)
        if (
            not isinstance(graph_rows, int)
            or isinstance(graph_rows, bool)
            or not 1 <= graph_rows <= 100
        ):
            raise ValueError("citation_graph.rows must be between 1 and 100")
        graph_sources = citation_graph.get("sources")
        if isinstance(graph_sources, str):
            raise ValueError("citation_graph.sources must be an array")
        if graph_sources is not None and (
            not isinstance(graph_sources, (list, tuple))
            or not all(isinstance(source, str) for source in graph_sources)
        ):
            raise ValueError("citation_graph.sources must be an array of source names")
        return cls(
            workflow=workflow,
            question=question,
            steps=steps,
            search=search,
            outputs=normalized_outputs,
            verification=dict(raw.get("verification") or {}),
            screening=dict(raw.get("screening") or {}),
            citation_graph=citation_graph,
            privacy=dict(raw.get("privacy") or {}),
        )

    @classmethod
    def from_yaml(cls, path: str | Path) -> WorkflowSpec:
        try:
            import yaml
        except ImportError as exc:
            raise RuntimeError(
                "YAML workflows require PyYAML; install the package test/runtime extra"
            ) from exc
        source = Path(path)
        with source.open(encoding="utf-8") as handle:
            loaded = yaml.safe_load(handle)
        if not isinstance(loaded, Mapping):
            raise ValueError("workflow YAML must contain an object")
        return cls.from_mapping(loaded)


class WorkflowRunner:
    """Run deterministic source steps and optional model-assisted steps locally."""

    def __init__(
        self,
        *,
        provider: Any | None = None,
        search_fn: Callable[[WorkflowSpec], Any] | None = None,
        lookup_fn: Callable[[str, str], Any] | None = None,
        graph_fn: Callable[..., Any] | None = None,
    ) -> None:
        self.provider = provider
        self.search_fn = search_fn
        self.lookup_fn = lookup_fn
        self.graph_fn = graph_fn

    def run(
        self,
        workflow: WorkflowSpec,
        output_dir: str | Path,
        *,
        approve: bool | Callable[[dict[str, Any]], bool] = False,
    ) -> dict[str, Any]:
        destination = Path(output_dir).expanduser().resolve()
        destination.mkdir(parents=True, exist_ok=True)
        run_id = str(uuid.uuid4())
        started_at = _utc_now()
        plan = self._plan(workflow)
        self._write_json(destination, "plan.json", plan)

        if "search" in workflow.steps and not _approved(approve, plan):
            return {
                "status": "approval_required",
                "run_id": run_id,
                "artifacts": ["plan.json"],
                "plan": plan,
            }

        model_steps: dict[str, dict[str, Any]] = {}
        errors: list[dict[str, str]] = []
        search_result: dict[str, Any] = {"results": [], "errors": None}
        if "search" in workflow.steps:
            try:
                search_result = _as_dict(self._run_search(workflow))
            except Exception as exc:
                errors.append({"step": "search", "error": _safe_error(exc)})
                search_result = {"results": [], "errors": [{"error": _safe_error(exc)}]}
            self._write_json(destination, "results.json", search_result)

        records = [
            dict(record)
            for record in search_result.get("results", [])
            if isinstance(record, Mapping)
        ]
        for record in records:
            record.setdefault("record_id", stable_record_id(record))

        verification: list[dict[str, Any]] = []
        if "verify" in workflow.steps:
            verification = self._verify_records(records, errors)
            self._write_json(destination, "verification.json", verification)

        if "expand_citations" in workflow.steps:
            graphs = self._expand_citation_graphs(records, workflow, errors)
            self._write_json(destination, "graph.json", graphs)

        screening = self._screen_records(workflow, records, model_steps, errors)
        if "screen" in workflow.steps:
            self._write_csv(destination, "screening.csv", screening)

        included = _included_records(
            records,
            verification,
            workflow.verification.get("include_statuses", ["verified"]),
        )
        if "export" in workflow.steps:
            self._write_text(destination, "references.ris", _records_to_ris(included))
            self._write_text(
                destination,
                "report.md",
                _report(workflow, records, verification, screening, model_steps),
            )

        artifacts = ["plan.json", "run.json"]
        if (destination / "graph.json").exists():
            artifacts.append("graph.json")
        artifacts.extend(output for output in workflow.outputs if (destination / output).exists())
        completed_at = _utc_now()
        status = "completed_with_skips" if any(
            step.get("status") == "skipped" for step in model_steps.values()
        ) else "completed"
        manifest = {
            "schema_version": "1",
            "workflow_run_id": run_id,
            "workflow": workflow.workflow,
            "question": workflow.question,
            "started_at": started_at,
            "completed_at": completed_at,
            "status": status,
            "steps": list(workflow.steps),
            "search_run": _safe_payload(search_result.get("search_run") or {}),
            "artifacts": list(dict.fromkeys(artifacts)),
            "model_steps": model_steps,
            "errors": errors or None,
        }
        self._write_json(destination, "run.json", manifest)
        return {
            "status": status,
            "run_id": run_id,
            "artifacts": manifest["artifacts"],
            "model_steps": model_steps,
            "errors": errors or None,
        }

    def _plan(self, workflow: WorkflowSpec) -> dict[str, Any]:
        return {
            "schema_version": "1",
            "workflow": workflow.workflow,
            "question": workflow.question,
            "steps": list(workflow.steps),
            "search": _safe_payload(workflow.search),
            "approval_required": "search" in workflow.steps,
            "privacy": {"allow_full_text": bool(workflow.privacy.get("allow_full_text", False))},
        }

    def _run_search(self, workflow: WorkflowSpec) -> Any:
        if self.search_fn is not None:
            return _resolve(self.search_fn(workflow))
        search = workflow.search
        return asyncio.run(
            search_all(
                workflow.question,
                search.get("sources"),
                int(search.get("rows", 20)),
                filter_type=search.get("type"),
                entity_type=str(search.get("entity_type", "publication")),
                enrichers=search.get("enrich") or [],
                filters=search.get("filters"),
                ranking=search.get("ranking"),
            )
        )

    def _verify_records(
        self, records: Sequence[Mapping[str, Any]], errors: list[dict[str, str]]
    ) -> list[dict[str, Any]]:
        output: list[dict[str, Any]] = []
        for record in records:
            identifier, id_type = _record_identifier(record)
            if not identifier or self.lookup_fn is None:
                output.append(
                    {
                        "record_id": record.get("record_id"),
                        "status": "manual_needed",
                        "method": "workflow_lookup_not_configured",
                    }
                )
                continue
            try:
                actual = _resolve(self.lookup_fn(identifier, id_type))
                checked = verify_record(_verification_expected(record), actual)
                checked["record_id"] = record.get("record_id")
                output.append(checked)
            except Exception as exc:
                errors.append({"step": "verify", "error": _safe_error(exc)})
                output.append(
                    {
                        "record_id": record.get("record_id"),
                        "status": "manual_needed",
                        "method": "workflow_lookup_error",
                    }
                )
        return output

    def _expand_citation_graphs(
        self,
        records: Sequence[Mapping[str, Any]],
        workflow: WorkflowSpec,
        errors: list[dict[str, str]],
    ) -> dict[str, Any]:
        config = workflow.citation_graph
        relation = str(config.get("relation") or "both")
        depth = int(config.get("depth", 1))
        rows = int(config.get("rows", 20))
        max_nodes = int(config.get("max_nodes", 100))
        max_edges = int(config.get("max_edges", 200))
        source_names = tuple(config.get("sources") or DEFAULT_RELATION_SOURCES)
        graph_builder = self.graph_fn or build_citation_graph
        adapters = None
        if self.graph_fn is None:
            from .sources.registry import build_adapters

            adapters = build_adapters(source_names)
        graphs: list[dict[str, Any]] = []
        for record in records:
            try:
                kwargs = {
                    "relation": relation,
                    "depth": depth,
                    "rows": rows,
                    "relation_sources": source_names,
                    "max_nodes": max_nodes,
                    "max_edges": max_edges,
                }
                if adapters is not None:
                    kwargs["adapters"] = adapters
                graphs.append(graph_builder(record, **kwargs))
            except Exception as exc:
                errors.append({"step": "expand_citations", "error": _safe_error(exc)})
        return {
            "schema_version": "1",
            "graphs": graphs,
            "graph_count": len(graphs),
            "errors": [item for item in errors if item.get("step") == "expand_citations"] or None,
        }

    def _screen_records(
        self,
        workflow: WorkflowSpec,
        records: Sequence[Mapping[str, Any]],
        model_steps: dict[str, dict[str, Any]],
        errors: list[dict[str, str]],
    ) -> list[dict[str, Any]]:
        pending = [
            {
                "record_id": record.get("record_id"),
                "decision": "pending_manual",
                "reason": "screening requires human review",
            }
            for record in records
        ]
        if "screen" not in workflow.steps:
            return pending
        if self.provider is None:
            model_steps["screen"] = {"status": "skipped", "reason": "provider_not_configured"}
            return pending
        payload = {
            "question": workflow.question,
            "records": [
                _model_record(
                    record,
                    allow_full_text=bool(workflow.privacy.get("allow_full_text", False)),
                )
                for record in records
            ],
            "rules": _safe_payload(workflow.screening),
        }
        try:
            response = self.provider.generate_json(
                "screen",
                payload,
                allow_full_text=bool(workflow.privacy.get("allow_full_text", False)),
            )
            decisions = response.get("decisions") if isinstance(response, Mapping) else None
            if not isinstance(decisions, list):
                raise ValueError("screen response must contain a decisions list")
            normalized = {
                str(item.get("record_id")): {
                    "record_id": item.get("record_id"),
                    "decision": str(item.get("decision") or "pending_manual"),
                    "reason": str(item.get("reason") or ""),
                }
                for item in decisions
                if isinstance(item, Mapping) and item.get("record_id")
            }
            allowed = {"include", "exclude", "pending_manual"}
            return [
                normalized.get(str(item["record_id"]), item)
                if str(
                    normalized.get(str(item["record_id"]), {}).get(
                        "decision", "pending_manual"
                    )
                )
                in allowed
                else item
                for item in pending
            ]
        except Exception as exc:
            model_steps["screen"] = {"status": "skipped", "reason": _safe_error(exc)}
            errors.append({"step": "screen", "error": _safe_error(exc)})
            return pending
        finally:
            model_steps.setdefault("screen", {"status": "completed"})

    @staticmethod
    def _write_json(destination: Path, name: str, value: Any) -> None:
        (destination / name).write_text(
            json.dumps(_safe_payload(value), ensure_ascii=False, indent=2, default=str) + "\n",
            encoding="utf-8",
        )

    @staticmethod
    def _write_text(destination: Path, name: str, value: str) -> None:
        (destination / name).write_text(value, encoding="utf-8")

    @staticmethod
    def _write_csv(destination: Path, name: str, rows: Sequence[Mapping[str, Any]]) -> None:
        with (destination / name).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["record_id", "decision", "reason"])
            writer.writeheader()
            writer.writerows(rows)


def _resolve(value: Any) -> Any:
    if inspect.isawaitable(value):
        return asyncio.run(value)
    return value


def _as_dict(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError("search function must return an object")
    return dict(value)


def _approved(approval: bool | Callable[[dict[str, Any]], bool], plan: dict[str, Any]) -> bool:
    return bool(approval(plan) if callable(approval) else approval)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _record_identifier(record: Mapping[str, Any]) -> tuple[str, str]:
    for field, id_type in (
        ("doi", "doi"),
        ("pmid", "pmid"),
        ("pmcid", "pmcid"),
        ("arxiv_id", "arxiv"),
        ("openalex_id", "openalex"),
        ("semantic_scholar_id", "semantic_scholar"),
        ("nct_id", "nct"),
    ):
        if record.get(field):
            return str(record[field]), id_type
    return "", "auto"


def _verification_expected(record: Mapping[str, Any]) -> dict[str, Any]:
    fields = (
        (
            "title",
            "authors",
            "year",
            "journal",
            "doi",
            "pmid",
            "pmcid",
            "arxiv_id",
            "openalex_id",
            "semantic_scholar_id",
        )
        if str(record.get("entity_type") or "publication") != "trial"
        else ("nct_id", "title", "status", "sponsor", "start_date", "completion_date")
    )
    expected = {
        field: record[field]
        for field in fields
        if record.get(field) not in (None, "", [])
    }
    if record.get("entity_type") == "trial" and record.get("overall_status"):
        expected["status"] = record["overall_status"]
    return expected


def _model_record(
    record: Mapping[str, Any], *, allow_full_text: bool
) -> dict[str, Any]:
    fields = (
        "record_id",
        "title",
        "abstract",
        "authors",
        "year",
        "journal",
        "doi",
        "pmid",
        "pmcid",
        "arxiv_id",
    )
    output = {field: record[field] for field in fields if record.get(field) not in (None, "", [])}
    if allow_full_text:
        for field in ("fulltext_url", "full_text", "pdf_url"):
            if record.get(field):
                output[field] = record[field]
    return output


def _safe_payload(value: Any, key: str = "") -> Any:
    lowered = key.casefold()
    if any(
        token in lowered
        for token in ("api_key", "token", "secret", "password", "authorization")
    ):
        return "[REDACTED]"
    if isinstance(value, Mapping):
        return {
            str(child_key): _safe_payload(child_value, str(child_key))
            for child_key, child_value in value.items()
            if _safe_payload(child_value, str(child_key)) is not None
        }
    if isinstance(value, list):
        return [_safe_payload(item) for item in value]
    if isinstance(value, tuple):
        return [_safe_payload(item) for item in value]
    return value


def _safe_error(error: BaseException) -> str:
    text = str(error)
    return re.sub(
        r"(?i)(?:api[_-]?key|token|secret|password)\s*[=:]\s*\S+",
        "credential=[REDACTED]",
        text,
    )


def _included_records(
    records: Sequence[Mapping[str, Any]],
    verification: Sequence[Mapping[str, Any]],
    statuses: Any,
) -> list[dict[str, Any]]:
    allowed = (
        {str(status) for status in statuses}
        if isinstance(statuses, Sequence) and not isinstance(statuses, str)
        else {"verified"}
    )
    verified_by_id = {str(item.get("record_id")): item.get("status") for item in verification}
    return [
        dict(record)
        for record in records
        if verified_by_id.get(str(record.get("record_id"))) in allowed
    ]


def _records_to_ris(records: Sequence[Mapping[str, Any]]) -> str:
    chunks: list[str] = []
    for record in records:
        lines = ["TY  - JOUR"]
        for author in record.get("authors") or []:
            lines.append(f"AU  - {author}")
        if record.get("title"):
            lines.append(f"TI  - {record['title']}")
        if record.get("journal"):
            lines.append(f"JO  - {record['journal']}")
        if record.get("year"):
            lines.append(f"PY  - {record['year']}")
        if record.get("doi"):
            lines.append(f"DO  - {record['doi']}")
        if record.get("pmid"):
            lines.append(f"AN  - PMID:{record['pmid']}")
        lines.extend(["ER  - ", ""])
        chunks.append("\n".join(lines))
    return "\n".join(chunks)


def _report(
    workflow: WorkflowSpec,
    records: Sequence[Mapping[str, Any]],
    verification: Sequence[Mapping[str, Any]],
    screening: Sequence[Mapping[str, Any]],
    model_steps: Mapping[str, Any],
) -> str:
    counts: dict[str, int] = {}
    for item in verification:
        status = str(item.get("status") or "unknown")
        counts[status] = counts.get(status, 0) + 1
    return "\n".join(
        [
            f"# {workflow.workflow}",
            "",
            f"- 研究问题：{workflow.question}",
            f"- 检索记录：{len(records)}",
            f"- 核验状态：{json.dumps(counts, ensure_ascii=False)}",
            f"- 筛选记录：{len(screening)}",
            f"- 模型步骤：{json.dumps(dict(model_steps), ensure_ascii=False)}",
            "",
            "本报告只汇总可追溯 artifact；模型筛选不等于证据质量判断。",
            "",
        ]
    )

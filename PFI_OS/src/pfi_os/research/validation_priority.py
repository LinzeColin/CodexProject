from __future__ import annotations

import csv
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from pfi_os.config import PROJECT_ROOT
from pfi_os.research.validation_queue import VALIDATION_QUEUE_PATH
from pfi_os.storage import atomic_write_json, atomic_write_text, read_json_state


VALIDATION_PRIORITY_COLUMNS = [
    "priority_rank",
    "priority_score",
    "action_bucket",
    "evidence_gap",
    "status",
    "symbol",
    "market",
    "research_topic",
    "signal_to_validate",
    "needed_input",
    "verification_method",
    "risk_if_skipped",
    "blockers",
    "task_id",
    "source_report",
]

FOUNDATIONAL_GAPS = {"DataQuality", "CrossSourceValidation", "ReportEvidence"}
DATA_DEPENDENT_GAPS = {"DataQuality", "CrossSourceValidation", "ParameterStability", "TrainTestValidation", "WalkForwardValidation"}


GAP_SCORE = {
    "DataQuality": 30,
    "CrossSourceValidation": 29,
    "ReportEvidence": 24,
    "RiskGate": 22,
    "WalkForwardValidation": 21,
    "TrainTestValidation": 20,
    "ParameterStability": 18,
    "DecisionQuality": 17,
    "WordReport": 10,
    "EvidenceReview": 8,
}


def build_validation_priority_plan(
    *,
    as_of: str | None = None,
    project_root: Path | str = PROJECT_ROOT,
    queue_path: Path | str = VALIDATION_QUEUE_PATH,
    max_tasks: int = 120,
    include_completed: bool = False,
) -> dict[str, Any]:
    root = Path(project_root).expanduser()
    target_queue = Path(queue_path).expanduser()
    task_date = as_of or datetime.now().date().isoformat()
    raw_records = read_json_state(target_queue, [], expected_type=list)
    clean_records = [item for item in raw_records if isinstance(item, dict)]
    candidate_records = [
        item for item in clean_records if include_completed or str(item.get("status", "")).strip() != "已完成"
    ]
    scored = [_priority_row(item, task_date) for item in candidate_records]
    scored.sort(key=lambda item: (-int(item["priority_score"]), _gap_sort_key(str(item["evidence_gap"])), str(item["created_at"])))
    for index, row in enumerate(scored, start=1):
        row["priority_rank"] = index
    selected = scored[: max(1, int(max_tasks))]
    return {
        "schema": "PFIOSValidationTaskPriorityPlanV1",
        "system": "PFI_OS",
        "subsystem": "Validation Task Priority Planner",
        "as_of": task_date,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "project_root": str(root),
        "queue_path": str(target_queue),
        "queue_record_count": len(clean_records),
        "candidate_record_count": len(candidate_records),
        "prioritized_task_count": len(selected),
        "include_completed": bool(include_completed),
        "max_tasks": int(max_tasks),
        "status_counts": _counts(scored, "status"),
        "gap_counts": _counts(scored, "evidence_gap"),
        "bucket_counts": _counts(scored, "action_bucket"),
        "top_tasks": selected,
        "assumptions": [
            "This planner only ranks validation tasks; it does not run validation, refresh market data, mutate holdings, change task status, or place orders.",
            "Priority scores are an execution-planning heuristic, not proof that any strategy is valid.",
            "Tasks with missing symbols or markets are routed to input preparation before data-dependent validation.",
        ],
        "outputs": {},
    }


def write_validation_priority_plan(
    *,
    as_of: str | None = None,
    project_root: Path | str = PROJECT_ROOT,
    queue_path: Path | str = VALIDATION_QUEUE_PATH,
    output_dir: Path | str | None = None,
    max_tasks: int = 120,
    include_completed: bool = False,
) -> dict[str, Any]:
    payload = build_validation_priority_plan(
        as_of=as_of,
        project_root=project_root,
        queue_path=queue_path,
        max_tasks=max_tasks,
        include_completed=include_completed,
    )
    target = Path(output_dir).expanduser() if output_dir else Path(project_root).expanduser() / "data" / "validationQueue"
    _write_priority_outputs(payload, target)
    return payload


def validation_priority_frame(payload: dict[str, Any]) -> pd.DataFrame:
    rows = payload.get("top_tasks", [])
    if not rows:
        return pd.DataFrame(columns=VALIDATION_PRIORITY_COLUMNS)
    frame = pd.DataFrame(rows)
    return frame[[column for column in VALIDATION_PRIORITY_COLUMNS if column in frame.columns]]


def validation_priority_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# Validation Task Priority Plan {payload.get('as_of', '')}",
        "",
        "## Summary",
        f"- Queue Records: `{payload.get('queue_record_count', 0)}`",
        f"- Candidate Records: `{payload.get('candidate_record_count', 0)}`",
        f"- Prioritized Tasks: `{payload.get('prioritized_task_count', 0)}`",
        f"- Queue: `{payload.get('queue_path', '')}`",
        "",
        "## Action Buckets",
        _markdown_table(payload.get("bucket_counts", []), ["action_bucket", "count"]),
        "",
        "## Evidence Gaps",
        _markdown_table(payload.get("gap_counts", []), ["evidence_gap", "count"]),
        "",
        "## Top Tasks",
        _markdown_table(
            payload.get("top_tasks", [])[:80],
            [
                "priority_rank",
                "priority_score",
                "action_bucket",
                "evidence_gap",
                "symbol",
                "market",
                "research_topic",
                "blockers",
            ],
        ),
        "",
        "## Assumptions",
        *[f"- {item}" for item in payload.get("assumptions", [])],
    ]
    return "\n".join(lines) + "\n"


def _priority_row(record: dict[str, Any], as_of: str) -> dict[str, Any]:
    gap = _infer_gap(record)
    status = str(record.get("status") or "待验证").strip()
    symbol = str(record.get("symbol", "")).strip()
    market = str(record.get("market", "")).strip()
    source_report = str(record.get("source_report", "")).strip()
    blockers = _blockers(gap, symbol, market, source_report)
    bucket = _action_bucket(gap, status, blockers)
    score = _priority_score(record, gap, status, symbol, market, source_report, blockers, as_of)
    return {
        "priority_rank": 0,
        "priority_score": score,
        "action_bucket": bucket,
        "evidence_gap": gap,
        "status": status,
        "symbol": symbol,
        "market": market,
        "research_topic": str(record.get("research_topic", "")).strip(),
        "signal_to_validate": str(record.get("signal_to_validate", "")).strip(),
        "needed_input": _needed_input(gap),
        "verification_method": _verification_method(gap),
        "risk_if_skipped": _risk_if_skipped(gap),
        "blockers": "; ".join(blockers),
        "task_id": str(record.get("task_id", "")).strip() or _stable_task_id(record),
        "source_report": source_report,
        "created_at": str(record.get("created_at", "")).strip(),
        "dedupe_key": str(record.get("dedupe_key", "")).strip(),
    }


def _priority_score(
    record: dict[str, Any],
    gap: str,
    status: str,
    symbol: str,
    market: str,
    source_report: str,
    blockers: list[str],
    as_of: str,
) -> int:
    score = 20
    score += {"待验证": 18, "验证中": 10, "暂停": -10, "已完成": -50}.get(status, 0)
    score += GAP_SCORE.get(gap, GAP_SCORE["EvidenceReview"])
    if gap in FOUNDATIONAL_GAPS:
        score += 8
    if str(record.get("task_id", "")).startswith("reportGapTask_"):
        score += 8
    if source_report:
        score += 6
    if symbol and market:
        score += 8
    if blockers:
        score -= 12
    if gap in DATA_DEPENDENT_GAPS and (not symbol or not market):
        score -= 8
    score += _recency_score(str(record.get("created_at", "")), as_of)
    return max(0, min(100, score))


def _infer_gap(record: dict[str, Any]) -> str:
    explicit = str(record.get("evidence_gap", "")).strip()
    if explicit:
        return explicit
    text = " ".join(
        str(record.get(key, ""))
        for key in ("research_topic", "signal_to_validate", "notes", "source_paragraph")
    ).lower()
    if "数据质量" in text or "data quality" in text:
        return "DataQuality"
    if "多源" in text or "cross" in text:
        return "CrossSourceValidation"
    if "walk" in text or "滚动" in text:
        return "WalkForwardValidation"
    if "样本内" in text or "样本外" in text or "train" in text:
        return "TrainTestValidation"
    if "参数稳定" in text or "parameter" in text:
        return "ParameterStability"
    if "风险闸门" in text or "risk gate" in text:
        return "RiskGate"
    if "decision quality" in text or "决策质量" in text:
        return "DecisionQuality"
    if "pfi_osreportevidencev1" in text or "报告证据" in text:
        return "ReportEvidence"
    if "word" in text or "报告文件" in text:
        return "WordReport"
    return "EvidenceReview"


def _blockers(gap: str, symbol: str, market: str, source_report: str) -> list[str]:
    blockers = []
    if gap in DATA_DEPENDENT_GAPS:
        if not symbol:
            blockers.append("missing_symbol")
        if not market:
            blockers.append("missing_market")
    if gap in {"ReportEvidence", "WordReport", "RiskGate", "DecisionQuality"} and not source_report:
        blockers.append("missing_source_report")
    return blockers


def _action_bucket(gap: str, status: str, blockers: list[str]) -> str:
    if status == "已完成":
        return "Completed"
    if status == "暂停":
        return "Paused"
    if blockers:
        return "PrepareInputs"
    if gap in FOUNDATIONAL_GAPS:
        return "RunFirst"
    if gap in {"RiskGate", "DecisionQuality", "EvidenceReview", "WordReport"}:
        return "ManualReview"
    return "BatchValidate"


def _needed_input(gap: str) -> str:
    return {
        "DataQuality": "symbol, market, provider, start/end date, interval, adjustment mode",
        "CrossSourceValidation": "symbol, market, date range, at least two real data sources",
        "ReportEvidence": "source report path, RunMetadata path, report evidence schema",
        "RiskGate": "RunMetadata, metrics, costs, drawdown, stop/degrade conditions",
        "WalkForwardValidation": "historical bars, strategy version, parameters, window definition",
        "TrainTestValidation": "historical bars, train/test split, costs, benchmark",
        "ParameterStability": "strategy parameters, scan ranges, benchmark, costs",
        "DecisionQuality": "thesis, evidence, risks, opposing view, exit/degrade conditions",
        "WordReport": "report artifact path and linked RunMetadata",
    }.get(gap, "source material and clear validation question")


def _verification_method(gap: str) -> str:
    return {
        "DataQuality": "Run data quality audit and save provider/date/field/missing-value evidence.",
        "CrossSourceValidation": "Compare close prices across providers and save tolerance result.",
        "ReportEvidence": "Regenerate report with PFIOSReportEvidenceV1 and linked RunMetadata.",
        "RiskGate": "Recompute risk gate and downgrade if evidence remains incomplete.",
        "WalkForwardValidation": "Run rolling windows and compare window stability.",
        "TrainTestValidation": "Run in-sample/out-of-sample split and compare degradation.",
        "ParameterStability": "Run parameter grid and check whether conclusions rely on one setting.",
        "DecisionQuality": "Complete Decision Quality checklist and record missing evidence.",
        "WordReport": "Export traceable Word report and confirm artifact exists.",
    }.get(gap, "Manual evidence review with source, assumption, and verification note.")


def _risk_if_skipped(gap: str) -> str:
    return {
        "DataQuality": "Bad or incomplete market data may invalidate every downstream metric.",
        "CrossSourceValidation": "Single-source errors may be mistaken for real strategy evidence.",
        "ReportEvidence": "The report cannot be traced back to data, entity, workflow, and risk gates.",
        "RiskGate": "A strategy can look profitable while hiding unacceptable drawdown or cost risk.",
        "WalkForwardValidation": "The result may be time-window overfit.",
        "TrainTestValidation": "The result may only work in the fitting sample.",
        "ParameterStability": "The result may depend on one fragile parameter.",
        "DecisionQuality": "The research conclusion may omit thesis, risks, or disconfirming evidence.",
        "WordReport": "Formal review and future audit cannot locate the evidence artifact.",
    }.get(gap, "The task remains an unresolved evidence gap.")


def _recency_score(created_at: str, as_of: str) -> int:
    if not created_at:
        return 0
    try:
        created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        target = datetime.fromisoformat(as_of).replace(tzinfo=created.tzinfo or timezone.utc)
    except ValueError:
        return 0
    age_days = max(0, (target.date() - created.date()).days)
    if age_days <= 1:
        return 5
    if age_days <= 7:
        return 3
    if age_days <= 30:
        return 1
    return 0


def _gap_sort_key(gap: str) -> int:
    order = {
        "DataQuality": 0,
        "CrossSourceValidation": 1,
        "ReportEvidence": 2,
        "RiskGate": 3,
        "WalkForwardValidation": 4,
        "TrainTestValidation": 5,
        "ParameterStability": 6,
        "DecisionQuality": 7,
        "WordReport": 8,
        "EvidenceReview": 9,
    }
    return order.get(gap, 99)


def _counts(rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key, "") or "Unknown")
        counts[value] = counts.get(value, 0) + 1
    return [{key: name, "count": count} for name, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))]


def _write_priority_outputs(payload: dict[str, Any], target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    stamp = _date_stamp(str(payload.get("as_of", "")))
    stem = f"ValidationTaskPriorityPlan_{stamp}"
    paths = {
        "json": target / f"{stem}.json",
        "csv": target / f"{stem}.csv",
        "markdown": target / f"{stem}.md",
        "pdf": target / f"{stem}.pdf",
        "latest_json": target / "ValidationTaskPriorityPlan_latest.json",
        "latest_csv": target / "ValidationTaskPriorityPlan_latest.csv",
        "latest_markdown": target / "ValidationTaskPriorityPlan_latest.md",
        "latest_pdf": target / "ValidationTaskPriorityPlan_latest.pdf",
    }
    payload["outputs"] = {key: str(value) for key, value in paths.items()}
    csv_text = _csv_text(payload.get("top_tasks", []))
    markdown = validation_priority_markdown(payload)
    atomic_write_text(paths["csv"], csv_text)
    atomic_write_text(paths["latest_csv"], csv_text)
    atomic_write_text(paths["markdown"], markdown)
    atomic_write_text(paths["latest_markdown"], markdown)
    _write_priority_pdf(paths["pdf"], payload)
    _write_priority_pdf(paths["latest_pdf"], payload)
    atomic_write_json(paths["json"], payload)
    atomic_write_json(paths["latest_json"], payload)


def _csv_text(rows: list[dict[str, Any]]) -> str:
    from io import StringIO

    handle = StringIO()
    writer = csv.DictWriter(handle, fieldnames=VALIDATION_PRIORITY_COLUMNS, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return handle.getvalue()


def _markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return "| " + " | ".join(columns) + " |\n| " + " | ".join("---" for _ in columns) + " |"
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(_cell(row.get(column, "")) for column in columns) + " |")
    return "\n".join(lines)


def _write_priority_pdf(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"Validation Task Priority Plan {payload.get('as_of', '')}",
        f"Queue Records: {payload.get('queue_record_count', 0)}",
        f"Candidate Records: {payload.get('candidate_record_count', 0)}",
        f"Prioritized Tasks: {payload.get('prioritized_task_count', 0)}",
        "",
        "Action Buckets:",
    ]
    for row in payload.get("bucket_counts", [])[:10]:
        lines.append(f"- {row.get('action_bucket')}: {row.get('count')}")
    lines.extend(["", "Top Tasks:"])
    for task in payload.get("top_tasks", [])[:25]:
        lines.append(
            f"{task.get('priority_rank')}. {task.get('priority_score')} "
            f"{task.get('action_bucket')} {task.get('evidence_gap')} "
            f"{_pdf_ascii(str(task.get('symbol') or 'NO_SYMBOL'))}"
        )
    lines.append("")
    lines.append("Research-only. No live trading. No real orders.")
    content = ["BT", "/F1 10 Tf", "56 760 Td", "12 TL"]
    for line in lines[:58]:
        content.append(f"({_pdf_escape(_pdf_ascii(line))}) Tj")
        content.append("T*")
    content.append("ET")
    stream = "\n".join(content).encode("latin-1")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    _write_pdf_objects(path, objects)


def _write_pdf_objects(path: Path, objects: list[bytes]) -> None:
    content = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(content))
        content.extend(f"{index} 0 obj\n".encode("ascii"))
        content.extend(obj)
        content.extend(b"\nendobj\n")
    xref_offset = len(content)
    content.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    content.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        content.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    content.extend(
        (
            "trailer\n"
            f"<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            "startxref\n"
            f"{xref_offset}\n"
            "%%EOF\n"
        ).encode("ascii")
    )
    path.write_bytes(content)


def _date_stamp(as_of: str) -> str:
    try:
        return datetime.fromisoformat(as_of).strftime("%d%m%Y")
    except ValueError:
        return datetime.now().strftime("%d%m%Y")


def _stable_task_id(record: dict[str, Any]) -> str:
    raw = "|".join(str(record.get(key, "")) for key in ("source_report", "research_topic", "signal_to_validate", "source_paragraph"))
    return f"priorityTask_{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:20]}"


def _cell(value: Any) -> str:
    return str(value).replace("\n", " ").replace("|", "/")


def _pdf_ascii(text: str) -> str:
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

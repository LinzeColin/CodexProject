from __future__ import annotations

import csv
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any

from pfi_os.config import PROJECT_ROOT
from pfi_os.data import BarDataRequest, save_cross_source_validation_result, validate_close_across_sources
from pfi_os.data.provider_status import provider_statuses
from pfi_os.research.validation_priority import build_validation_priority_plan
from pfi_os.research.validation_queue import VALIDATION_QUEUE_PATH
from pfi_os.storage import atomic_write_json, atomic_write_text


VALIDATION_EXECUTION_COLUMNS = [
    "execution_id",
    "task_id",
    "execution_status",
    "evidence_status",
    "evidence_gap",
    "symbol",
    "market",
    "providers_requested",
    "providers_used",
    "overlap_rows",
    "max_close_diff_pct",
    "mean_close_diff_pct",
    "result_status",
    "blockers",
    "cross_validation_report_path",
    "source_report",
]


def build_validation_task_execution(
    *,
    as_of: str | None = None,
    project_root: Path | str = PROJECT_ROOT,
    queue_path: Path | str = VALIDATION_QUEUE_PATH,
    task_id: str | None = None,
    symbol: str | None = None,
    market: str | None = None,
    providers: list[str] | None = None,
    start: str = "2024-01-01",
    end: str = "2024-01-31",
    interval: str = "1d",
    tolerance_pct: float = 0.01,
    cross_validation_output_dir: Path | str | None = None,
) -> dict[str, Any]:
    root = Path(project_root).expanduser()
    run_date = as_of or datetime.now().date().isoformat()
    task = _select_task(
        as_of=run_date,
        project_root=root,
        queue_path=queue_path,
        task_id=task_id,
        symbol=symbol,
        market=market,
    )
    request_symbol = str(symbol or task.get("symbol") or "").strip()
    request_market = str(market or task.get("market") or "").strip()
    execution_id = _execution_id(task, request_symbol, request_market, start, end, interval)
    if str(task.get("evidence_gap", "")) != "CrossSourceValidation":
        return _base_payload(
            execution_id=execution_id,
            as_of=run_date,
            root=root,
            task=task,
            symbol=request_symbol,
            market=request_market,
            providers_requested=providers or [],
            providers_used=[],
            start=start,
            end=end,
            interval=interval,
            tolerance_pct=tolerance_pct,
            execution_status="Blocked",
            evidence_status="NeedsMoreEvidence",
            blockers=["unsupported_evidence_gap"],
            result_status="NotRun",
            error="This execution runner currently supports CrossSourceValidation tasks only.",
        )
    provider_candidates = providers or _default_providers_for_market(request_market)
    blockers = []
    if not request_symbol:
        blockers.append("missing_symbol")
    if not request_market:
        blockers.append("missing_market")
    if len(provider_candidates) < 2:
        blockers.append("at_least_two_real_providers_required")
    if blockers:
        return _base_payload(
            execution_id=execution_id,
            as_of=run_date,
            root=root,
            task=task,
            symbol=request_symbol,
            market=request_market,
            providers_requested=provider_candidates,
            providers_used=[],
            start=start,
            end=end,
            interval=interval,
            tolerance_pct=tolerance_pct,
            execution_status="Blocked",
            evidence_status="NeedsMoreEvidence",
            blockers=blockers,
            result_status="NotRun",
            error="Validation input is incomplete or fewer than two real providers are available.",
        )
    request = BarDataRequest(symbol=request_symbol, market=request_market, interval=interval, start=start, end=end)
    try:
        result = validate_close_across_sources(provider_candidates, request, tolerance_pct=tolerance_pct)
        output_root = Path(cross_validation_output_dir).expanduser() if cross_validation_output_dir else root / "data" / "validationQueue"
        cross_path = save_cross_source_validation_result(result, output_dir=output_root)
        if result.status == "Pass":
            execution_status = "Pass"
            evidence_status = "EvidenceAvailable"
            blockers = []
        elif result.status in {"Review", "NoOverlap", "InsufficientData"}:
            execution_status = "Review"
            evidence_status = "NeedsMoreEvidence"
            blockers = [f"cross_validation_status_{result.status}"]
        else:
            execution_status = "Review"
            evidence_status = "NeedsMoreEvidence"
            blockers = ["unexpected_cross_validation_status"]
        payload = _base_payload(
            execution_id=execution_id,
            as_of=run_date,
            root=root,
            task=task,
            symbol=request_symbol,
            market=request_market,
            providers_requested=provider_candidates,
            providers_used=list(result.providers),
            start=start,
            end=end,
            interval=interval,
            tolerance_pct=tolerance_pct,
            execution_status=execution_status,
            evidence_status=evidence_status,
            blockers=blockers,
            result_status=result.status,
            cross_validation_report_path=str(cross_path),
        )
        payload["result"] = {
            "overlap_rows": result.overlap_rows,
            "max_close_diff_pct": result.max_close_diff_pct,
            "mean_close_diff_pct": result.mean_close_diff_pct,
            "details_preview": result.details.head(10).to_dict(orient="records") if not result.details.empty else [],
        }
        return payload
    except Exception as exc:
        return _base_payload(
            execution_id=execution_id,
            as_of=run_date,
            root=root,
            task=task,
            symbol=request_symbol,
            market=request_market,
            providers_requested=provider_candidates,
            providers_used=[],
            start=start,
            end=end,
            interval=interval,
            tolerance_pct=tolerance_pct,
            execution_status="Error",
            evidence_status="NeedsMoreEvidence",
            blockers=["execution_error"],
            result_status="Error",
            error=f"{type(exc).__name__}: {exc}",
        )


def write_validation_task_execution(
    *,
    as_of: str | None = None,
    project_root: Path | str = PROJECT_ROOT,
    queue_path: Path | str = VALIDATION_QUEUE_PATH,
    output_dir: Path | str | None = None,
    task_id: str | None = None,
    symbol: str | None = None,
    market: str | None = None,
    providers: list[str] | None = None,
    start: str = "2024-01-01",
    end: str = "2024-01-31",
    interval: str = "1d",
    tolerance_pct: float = 0.01,
) -> dict[str, Any]:
    root = Path(project_root).expanduser()
    target = Path(output_dir).expanduser() if output_dir else root / "data" / "validationQueue"
    payload = build_validation_task_execution(
        as_of=as_of,
        project_root=root,
        queue_path=queue_path,
        task_id=task_id,
        symbol=symbol,
        market=market,
        providers=providers,
        start=start,
        end=end,
        interval=interval,
        tolerance_pct=tolerance_pct,
        cross_validation_output_dir=target,
    )
    _write_execution_outputs(payload, target)
    return payload


def validation_task_execution_markdown(payload: dict[str, Any]) -> str:
    result = payload.get("result", {})
    lines = [
        f"# Validation Task Execution {payload.get('as_of', '')}",
        "",
        "## Summary",
        f"- Execution ID: `{payload.get('execution_id', '')}`",
        f"- Task ID: `{payload.get('task_id', '')}`",
        f"- Execution Status: `{payload.get('execution_status', '')}`",
        f"- Evidence Status: `{payload.get('evidence_status', '')}`",
        f"- Evidence Gap: `{payload.get('evidence_gap', '')}`",
        f"- Symbol: `{payload.get('symbol', '')}`",
        f"- Market: `{payload.get('market', '')}`",
        f"- Providers Requested: `{', '.join(payload.get('providers_requested', []))}`",
        f"- Providers Used: `{', '.join(payload.get('providers_used', []))}`",
        f"- Result Status: `{payload.get('result_status', '')}`",
        f"- Overlap Rows: `{result.get('overlap_rows', 0)}`",
        f"- Max Close Diff: `{_pct(result.get('max_close_diff_pct', 0.0))}`",
        f"- Mean Close Diff: `{_pct(result.get('mean_close_diff_pct', 0.0))}`",
        f"- Cross Validation Report: `{payload.get('cross_validation_report_path', '')}`",
        f"- Blockers: `{'; '.join(payload.get('blockers', []))}`",
        "",
        "## Conclusion",
        f"- FACT: `{payload.get('fact', '')}`",
        f"- INFERENCE: `{payload.get('inference', '')}`",
        f"- Next Action: `{payload.get('next_action', '')}`",
        "",
        "## Assumptions",
        *[f"- {item}" for item in payload.get("assumptions", [])],
    ]
    if payload.get("error"):
        lines.extend(["", "## Error", f"`{payload['error']}`"])
    return "\n".join(lines) + "\n"


def _select_task(
    *,
    as_of: str,
    project_root: Path,
    queue_path: Path | str,
    task_id: str | None,
    symbol: str | None,
    market: str | None,
) -> dict[str, Any]:
    plan = build_validation_priority_plan(as_of=as_of, project_root=project_root, queue_path=queue_path, max_tasks=500)
    tasks = plan.get("top_tasks", [])
    if task_id:
        for task in tasks:
            if str(task.get("task_id")) == task_id:
                return task
        return {"task_id": task_id, "evidence_gap": "CrossSourceValidation", "symbol": symbol or "", "market": market or ""}
    for task in tasks:
        if (
            str(task.get("evidence_gap")) == "CrossSourceValidation"
            and str(task.get("action_bucket")) == "RunFirst"
            and str(task.get("symbol", "")).strip()
            and str(task.get("market", "")).strip()
        ):
            return task
    return {"task_id": "", "evidence_gap": "CrossSourceValidation", "symbol": symbol or "", "market": market or ""}


def _default_providers_for_market(market: str) -> list[str]:
    statuses = {item.provider: item.status for item in provider_statuses()}
    text = str(market).upper()
    providers: list[str] = []
    if text in {"US", "HK", "CN"} and statuses.get("Moomoo") == "Ready":
        providers.append("Moomoo")
    if text in {"US", "HK"} and statuses.get("Yahoo Finance") == "Ready":
        providers.append("Yahoo Finance")
    if text == "US" and statuses.get("Alpha Vantage") == "Ready":
        providers.append("Alpha Vantage")
    if text == "US" and statuses.get("Polygon") == "Ready":
        providers.append("Polygon")
    if text == "CN" and statuses.get("AKShare") == "Ready":
        providers.append("AKShare")
    if text == "CN" and statuses.get("TuShare") == "Ready":
        providers.append("TuShare")
    return providers


def _base_payload(
    *,
    execution_id: str,
    as_of: str,
    root: Path,
    task: dict[str, Any],
    symbol: str,
    market: str,
    providers_requested: list[str],
    providers_used: list[str],
    start: str,
    end: str,
    interval: str,
    tolerance_pct: float,
    execution_status: str,
    evidence_status: str,
    blockers: list[str],
    result_status: str,
    cross_validation_report_path: str = "",
    error: str = "",
) -> dict[str, Any]:
    fact, inference, next_action = _conclusion(execution_status, evidence_status, blockers, result_status)
    return {
        "schema": "PFIOSValidationTaskExecutionV1",
        "system": "PFI_OS",
        "subsystem": "Validation Task Execution",
        "as_of": as_of,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "project_root": str(root),
        "execution_id": execution_id,
        "task_id": str(task.get("task_id", "")),
        "source_report": str(task.get("source_report", "")),
        "research_topic": str(task.get("research_topic", "")),
        "evidence_gap": str(task.get("evidence_gap", "CrossSourceValidation")),
        "symbol": symbol,
        "market": market,
        "request": {"symbol": symbol, "market": market, "interval": interval, "start": start, "end": end},
        "tolerance_pct": tolerance_pct,
        "providers_requested": providers_requested,
        "providers_used": providers_used,
        "execution_status": execution_status,
        "evidence_status": evidence_status,
        "result_status": result_status,
        "blockers": blockers,
        "cross_validation_report_path": cross_validation_report_path,
        "result": {"overlap_rows": 0, "max_close_diff_pct": 0.0, "mean_close_diff_pct": 0.0, "details_preview": []},
        "error": error,
        "fact": fact,
        "inference": inference,
        "next_action": next_action,
        "assumptions": [
            "This execution record is research-only; it does not connect to live trading and does not place orders.",
            "A blocked or error status is valid evidence of an execution attempt, not evidence that the strategy or data passed.",
            "The original validation queue is not mutated by this runner.",
        ],
        "outputs": {},
    }


def _conclusion(execution_status: str, evidence_status: str, blockers: list[str], result_status: str) -> tuple[str, str, str]:
    if execution_status == "Pass":
        return (
            "Cross-source validation produced overlapping provider data within tolerance.",
            "This specific evidence gap can be treated as available for the tested symbol/date window.",
            "Link this execution and cross-validation report back to the source report evidence layer.",
        )
    if execution_status == "Review":
        return (
            f"Cross-source validation ran and returned {result_status}.",
            "The evidence gap is not fully closed; the report should remain NeedsMoreEvidence until reviewed.",
            "Review provider details, tolerance, overlap rows, and whether a broader sample is needed.",
        )
    if execution_status == "Blocked":
        return (
            "Cross-source validation was not run because required inputs or provider coverage were missing.",
            "The evidence gap remains open; no data-quality conclusion should be upgraded.",
            "Configure at least two real providers or fill missing symbol/market fields, then rerun.",
        )
    return (
        "Cross-source validation attempt failed during execution.",
        "The evidence gap remains open; failure details must be reviewed before retrying.",
        "Fix the provider/runtime error and rerun the same task.",
    )


def _write_execution_outputs(payload: dict[str, Any], target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    stamp = _date_stamp(str(payload.get("as_of", "")))
    execution_slug = str(payload.get("execution_id", "")).replace("validationExecution_", "")[:16] or "execution"
    stem = f"ValidationTaskExecution_{stamp}_{execution_slug}"
    paths = {
        "json": target / f"{stem}.json",
        "csv": target / f"{stem}.csv",
        "markdown": target / f"{stem}.md",
        "pdf": target / f"{stem}.pdf",
        "latest_json": target / "ValidationTaskExecution_latest.json",
        "latest_csv": target / "ValidationTaskExecution_latest.csv",
        "latest_markdown": target / "ValidationTaskExecution_latest.md",
        "latest_pdf": target / "ValidationTaskExecution_latest.pdf",
    }
    payload["outputs"] = {key: str(value) for key, value in paths.items()}
    csv_text = _csv_text(payload)
    markdown = validation_task_execution_markdown(payload)
    atomic_write_text(paths["csv"], csv_text)
    atomic_write_text(paths["latest_csv"], csv_text)
    atomic_write_text(paths["markdown"], markdown)
    atomic_write_text(paths["latest_markdown"], markdown)
    _write_execution_pdf(paths["pdf"], payload)
    _write_execution_pdf(paths["latest_pdf"], payload)
    atomic_write_json(paths["json"], payload, default=str)
    atomic_write_json(paths["latest_json"], payload, default=str)


def _csv_text(payload: dict[str, Any]) -> str:
    from io import StringIO

    result = payload.get("result", {})
    row = {
        "execution_id": payload.get("execution_id", ""),
        "task_id": payload.get("task_id", ""),
        "execution_status": payload.get("execution_status", ""),
        "evidence_status": payload.get("evidence_status", ""),
        "evidence_gap": payload.get("evidence_gap", ""),
        "symbol": payload.get("symbol", ""),
        "market": payload.get("market", ""),
        "providers_requested": ";".join(payload.get("providers_requested", [])),
        "providers_used": ";".join(payload.get("providers_used", [])),
        "overlap_rows": result.get("overlap_rows", 0),
        "max_close_diff_pct": result.get("max_close_diff_pct", 0.0),
        "mean_close_diff_pct": result.get("mean_close_diff_pct", 0.0),
        "result_status": payload.get("result_status", ""),
        "blockers": ";".join(payload.get("blockers", [])),
        "cross_validation_report_path": payload.get("cross_validation_report_path", ""),
        "source_report": payload.get("source_report", ""),
    }
    handle = StringIO()
    writer = csv.DictWriter(handle, fieldnames=VALIDATION_EXECUTION_COLUMNS, extrasaction="ignore")
    writer.writeheader()
    writer.writerow(row)
    return handle.getvalue()


def _write_execution_pdf(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    result = payload.get("result", {})
    lines = [
        f"Validation Task Execution {payload.get('as_of', '')}",
        f"Execution Status: {payload.get('execution_status', '')}",
        f"Evidence Status: {payload.get('evidence_status', '')}",
        f"Task: {payload.get('task_id', '')}",
        f"Symbol: {payload.get('symbol', '')} / {payload.get('market', '')}",
        f"Providers Requested: {', '.join(payload.get('providers_requested', []))}",
        f"Providers Used: {', '.join(payload.get('providers_used', []))}",
        f"Result Status: {payload.get('result_status', '')}",
        f"Overlap Rows: {result.get('overlap_rows', 0)}",
        f"Max Close Diff: {_pct(result.get('max_close_diff_pct', 0.0))}",
        f"Mean Close Diff: {_pct(result.get('mean_close_diff_pct', 0.0))}",
        f"Blockers: {'; '.join(payload.get('blockers', []))}",
        "",
        f"FACT: {payload.get('fact', '')}",
        f"INFERENCE: {payload.get('inference', '')}",
        f"Next Action: {payload.get('next_action', '')}",
        "",
        "Research-only. No live trading. No real orders.",
    ]
    if payload.get("error"):
        lines.append(f"Error: {payload.get('error', '')}")
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


def _execution_id(task: dict[str, Any], symbol: str, market: str, start: str, end: str, interval: str) -> str:
    raw = "|".join([str(task.get("task_id", "")), symbol, market, start, end, interval])
    return f"validationExecution_{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:24]}"


def _date_stamp(as_of: str) -> str:
    try:
        return datetime.fromisoformat(as_of).strftime("%d%m%Y")
    except ValueError:
        return datetime.now().strftime("%d%m%Y")


def _pct(value: object) -> str:
    try:
        return f"{float(value):.2%}"
    except (TypeError, ValueError):
        return "0.00%"


def _pdf_ascii(text: str) -> str:
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

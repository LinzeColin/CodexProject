from __future__ import annotations

import csv
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any

from pfi_os.config import PROJECT_ROOT, REPORT_ROOT_DIR
from pfi_os.research.validation_queue import VALIDATION_QUEUE_PATH, create_validation_task
from pfi_os.storage import atomic_write_json, atomic_write_text, locked_json_update, read_json_state


REPORT_GAP_TASK_COLUMNS = [
    "task_id",
    "evidence_gap",
    "source_report",
    "metadata_path",
    "run",
    "strategy_id",
    "symbol",
    "market",
    "research_topic",
    "signal_to_validate",
    "sample_period",
    "cost_assumption",
    "benchmark",
    "status",
    "dedupe_key",
]


def build_report_gap_validation_tasks(
    *,
    as_of: str | None = None,
    project_root: Path | str = PROJECT_ROOT,
    report_root: Path | str = REPORT_ROOT_DIR,
    report_decision_payload: dict[str, Any] | None = None,
    max_records: int = 500,
) -> dict[str, Any]:
    root = Path(project_root).expanduser()
    reports = Path(report_root).expanduser()
    task_date = as_of or datetime.now().date().isoformat()
    if report_decision_payload is None:
        from pfi_os.reports import build_report_decision_support_index

        decision_payload = build_report_decision_support_index(
            as_of=task_date,
            project_root=root,
            report_root=reports,
            max_records=max_records,
        )
    else:
        decision_payload = report_decision_payload
    tasks = []
    for record in decision_payload.get("records", []):
        if str(record.get("report_readiness", "")) not in {"NeedsMoreEvidence", "DoNotUse"}:
            continue
        for gap in _classified_gaps(str(record.get("critical_missing_evidence", ""))):
            tasks.append(_task_payload(record, gap))
    unique = _dedupe_tasks(tasks)
    return {
        "schema": "PFIOSReportEvidenceGapTasksV1",
        "system": "PFI_OS",
        "subsystem": "Report Evidence Gap Task Generator",
        "as_of": task_date,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "project_root": str(root),
        "report_root": str(reports),
        "source_schema": decision_payload.get("schema", ""),
        "source_record_count": int(decision_payload.get("record_count", 0) or 0),
        "task_count": len(unique),
        "gap_counts": _gap_counts(unique),
        "tasks": unique,
        "assumptions": [
            "This generator only creates validation tasks; it does not run validation, refresh market data, modify reports, or place orders.",
            "Generated tasks are evidence repair requests for research review, not trading instructions.",
            "Existing queue tasks are preserved. Append mode uses stable dedupe keys to avoid repeated task creation.",
        ],
    }


def append_report_gap_validation_tasks(
    *,
    as_of: str | None = None,
    project_root: Path | str = PROJECT_ROOT,
    report_root: Path | str = REPORT_ROOT_DIR,
    queue_path: Path | str | None = VALIDATION_QUEUE_PATH,
    output_dir: Path | str | None = None,
    dry_run: bool = False,
    max_records: int = 500,
    report_decision_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = build_report_gap_validation_tasks(
        as_of=as_of,
        project_root=project_root,
        report_root=report_root,
        max_records=max_records,
        report_decision_payload=report_decision_payload,
    )
    target_queue = Path(queue_path).expanduser() if queue_path is not None else VALIDATION_QUEUE_PATH
    existing = read_json_state(target_queue, [], expected_type=list)
    existing_clean = [item for item in existing if isinstance(item, dict)]
    existing_keys = {_queue_key(item) for item in existing_clean}
    pending = []
    skipped_existing = 0
    for task in payload["tasks"]:
        key = _queue_key(task)
        if key in existing_keys:
            skipped_existing += 1
            continue
        queue_record = create_validation_task(task).to_dict()
        for extra_key in ("evidence_gap", "metadata_path", "run", "strategy_id", "dedupe_key"):
            queue_record[extra_key] = task.get(extra_key, "")
        pending.append(queue_record)
        existing_keys.add(key)
    appended_count = 0
    if pending and not dry_run:

        def append_tasks(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
            nonlocal appended_count
            clean_records = [item for item in records if isinstance(item, dict)]
            keys = {_queue_key(item) for item in clean_records}
            additions = []
            for item in pending:
                key = _queue_key(item)
                if key in keys:
                    continue
                additions.append(item)
                keys.add(key)
            appended_count = len(additions)
            return clean_records + additions

        locked_json_update(target_queue, [], append_tasks, expected_type=list)
    payload["queue_path"] = str(target_queue)
    payload["dry_run"] = bool(dry_run)
    payload["pending_task_count"] = len(pending)
    payload["appended_task_count"] = 0 if dry_run else appended_count
    payload["skipped_existing_count"] = skipped_existing
    if output_dir is not None or not dry_run:
        target = Path(output_dir).expanduser() if output_dir else Path(project_root).expanduser() / "data" / "reportDecision"
        _write_gap_task_outputs(payload, target)
    return payload


def report_gap_task_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# Report Evidence Gap Tasks {payload.get('as_of', '')}",
        "",
        "## Summary",
        f"- Source Records: `{payload.get('source_record_count', 0)}`",
        f"- Candidate Tasks: `{payload.get('task_count', 0)}`",
        f"- Pending New Tasks: `{payload.get('pending_task_count', 0)}`",
        f"- Appended Tasks: `{payload.get('appended_task_count', 0)}`",
        f"- Skipped Existing: `{payload.get('skipped_existing_count', 0)}`",
        f"- Queue: `{payload.get('queue_path', '')}`",
        "",
        "## Gap Counts",
        _markdown_table(payload.get("gap_counts", []), ["evidence_gap", "count"]),
        "",
        "## Tasks",
        _markdown_table(
            payload.get("tasks", [])[:120],
            ["evidence_gap", "research_topic", "symbol", "market", "signal_to_validate", "status"],
        ),
        "",
        "## Assumptions",
        *[f"- {item}" for item in payload.get("assumptions", [])],
    ]
    return "\n".join(lines) + "\n"


def _task_payload(record: dict[str, Any], gap: str) -> dict[str, Any]:
    linked = str(record.get("linked_report_path", ""))
    metadata = str(record.get("metadata_path", ""))
    source_report = linked or metadata
    run = str(record.get("run", ""))
    strategy = str(record.get("strategy_id", ""))
    symbol = str(record.get("symbol", ""))
    market = str(record.get("market", ""))
    signal = _signal_for_gap(gap)
    topic = f"补齐报告证据：{run} / {gap}"
    task = {
        "task_id": _stable_task_id(source_report, metadata, run, gap),
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source_report": source_report,
        "source_paragraph": str(record.get("critical_missing_evidence", ""))[:1000],
        "research_topic": topic,
        "symbol": symbol,
        "market": market,
        "signal_to_validate": signal,
        "sample_period": "使用原报告样本区间；缺失时覆盖完整市场周期并记录起止日期。",
        "cost_assumption": "沿用原 RunMetadata 成本假设；缺失时补充佣金、滑点、冲击成本、汇率或申赎费用。",
        "benchmark": _benchmark_for_market(market),
        "status": "待验证",
        "validation_report_path": "",
        "notes": (
            "由 Report Decision Support Index 自动生成；"
            f"metadata_path={metadata}; strategy_id={strategy}; evidence_gap={gap}; "
            "只用于补证据和复核，不构成交易建议。"
        ),
        "evidence_gap": gap,
        "metadata_path": metadata,
        "run": run,
        "strategy_id": strategy,
        "dedupe_key": _dedupe_key(source_report, metadata, run, gap, symbol, market),
    }
    return task


def _classified_gaps(text: str) -> list[str]:
    parts = [item.strip() for item in text.split(";") if item.strip()]
    categories: list[str] = []
    for item in parts:
        lowered = item.lower()
        if "pfi_osreportevidencev1" in lowered:
            categories.append("ReportEvidence")
        elif "数据质量" in item:
            categories.append("DataQuality")
        elif "多源" in item or "cross" in lowered:
            categories.append("CrossSourceValidation")
        elif "风险闸门" in item:
            categories.append("RiskGate")
        elif "决策质量" in item or "decision" in lowered or "证据质量" in item:
            categories.append("DecisionQuality")
        elif "参数稳定" in item:
            categories.append("ParameterStability")
        elif "样本内" in item or "样本外" in item or "train" in lowered:
            categories.append("TrainTestValidation")
        elif "walk" in lowered or "滚动" in item:
            categories.append("WalkForwardValidation")
        elif "word" in lowered or "报告文件" in item:
            categories.append("WordReport")
        else:
            categories.append("EvidenceReview")
    return _dedupe(categories)


def _signal_for_gap(gap: str) -> str:
    return {
        "ReportEvidence": "重新导出包含 PFIOSReportEvidenceV1 的 Word 报告和 RunMetadata。",
        "DataQuality": "补跑并保存数据质量检查，确认数据源、时间区间、缺失值和异常值。",
        "CrossSourceValidation": "补跑多源交叉校验，比较至少两个可用真实数据源的关键价格。",
        "RiskGate": "重建研究风险闸门，覆盖收益、回撤、成本、稳定性、样本外和停用条件。",
        "DecisionQuality": "补齐 Decision Quality，包括 Thesis、证据、风险、反方观点和退出条件。",
        "ParameterStability": "补跑参数稳定性扫描，检查结论是否依赖单一参数。",
        "TrainTestValidation": "补跑样本内/样本外验证，确认训练和测试表现是否一致。",
        "WalkForwardValidation": "补跑 walk-forward 验证，检查规律是否跨时间窗口稳定。",
        "WordReport": "重新生成可追溯 Word 报告，并确认对应 RunMetadata。",
    }.get(gap, "人工复核缺失证据并补充可追溯验证材料。")


def _benchmark_for_market(market: str) -> str:
    text = str(market).upper()
    if text == "CN":
        return "沪深300"
    if text == "HK":
        return "恒生指数"
    if text == "US":
        return "S&P 500"
    return "按报告研究对象选择可复核基准"


def _dedupe_tasks(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str, str, str]] = set()
    result: list[dict[str, Any]] = []
    for task in tasks:
        key = _queue_key(task)
        if key in seen:
            continue
        seen.add(key)
        result.append(task)
    return result


def _queue_key(payload: dict[str, Any]) -> tuple[str, str, str, str]:
    explicit = str(payload.get("dedupe_key", ""))
    return (
        explicit or str(payload.get("source_report", "")),
        str(payload.get("symbol", "")),
        str(payload.get("signal_to_validate", "")),
        str(payload.get("source_paragraph", ""))[:160],
    )


def _dedupe_key(source_report: str, metadata: str, run: str, gap: str, symbol: str, market: str) -> str:
    return _stable_hash("reportGapKey", source_report, metadata, run, gap, symbol, market)


def _stable_task_id(*parts: str) -> str:
    return f"reportGapTask_{_stable_hash(*parts)[:20]}"


def _stable_hash(*parts: str) -> str:
    return hashlib.sha256("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()


def _gap_counts(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for task in tasks:
        gap = str(task.get("evidence_gap", "") or "EvidenceReview")
        counts[gap] = counts.get(gap, 0) + 1
    return [{"evidence_gap": key, "count": value} for key, value in sorted(counts.items(), key=lambda item: (-item[1], item[0]))]


def _write_gap_task_outputs(payload: dict[str, Any], target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    stamp = _date_stamp(str(payload.get("as_of", "")))
    stem = f"ReportEvidenceGapTasks_{stamp}"
    json_path = target / f"{stem}.json"
    csv_path = target / f"{stem}.csv"
    markdown_path = target / f"{stem}.md"
    pdf_path = target / f"{stem}.pdf"
    latest_json = target / "ReportEvidenceGapTasks_latest.json"
    latest_csv = target / "ReportEvidenceGapTasks_latest.csv"
    latest_markdown = target / "ReportEvidenceGapTasks_latest.md"
    latest_pdf = target / "ReportEvidenceGapTasks_latest.pdf"
    payload["outputs"] = {
        "json": str(json_path),
        "csv": str(csv_path),
        "markdown": str(markdown_path),
        "pdf": str(pdf_path),
        "latest_json": str(latest_json),
        "latest_csv": str(latest_csv),
        "latest_markdown": str(latest_markdown),
        "latest_pdf": str(latest_pdf),
    }
    csv_text = _csv_text(payload.get("tasks", []))
    markdown = report_gap_task_markdown(payload)
    atomic_write_text(csv_path, csv_text)
    atomic_write_text(latest_csv, csv_text)
    atomic_write_text(markdown_path, markdown)
    atomic_write_text(latest_markdown, markdown)
    _write_gap_task_pdf(pdf_path, payload)
    _write_gap_task_pdf(latest_pdf, payload)
    atomic_write_json(json_path, payload)
    atomic_write_json(latest_json, payload)


def _csv_text(tasks: list[dict[str, Any]]) -> str:
    from io import StringIO

    handle = StringIO()
    writer = csv.DictWriter(handle, fieldnames=REPORT_GAP_TASK_COLUMNS, extrasaction="ignore")
    writer.writeheader()
    for task in tasks:
        writer.writerow(task)
    return handle.getvalue()


def _markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return "| " + " | ".join(columns) + " |\n| " + " | ".join("---" for _ in columns) + " |"
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(_cell(row.get(column, "")) for column in columns) + " |")
    return "\n".join(lines)


def _write_gap_task_pdf(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"Report Evidence Gap Tasks {payload.get('as_of', '')}",
        f"Source Records: {payload.get('source_record_count', 0)}",
        f"Candidate Tasks: {payload.get('task_count', 0)}",
        f"Pending New Tasks: {payload.get('pending_task_count', 0)}",
        f"Appended Tasks: {payload.get('appended_task_count', 0)}",
        f"Skipped Existing: {payload.get('skipped_existing_count', 0)}",
        "",
        "Gap Counts:",
    ]
    for row in payload.get("gap_counts", [])[:12]:
        lines.append(f"- {row.get('evidence_gap')}: {row.get('count')}")
    lines.extend(["", "Top Tasks:"])
    for task in payload.get("tasks", [])[:24]:
        lines.append(f"- {task.get('evidence_gap')}: {task.get('research_topic')}")
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


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def _cell(value: Any) -> str:
    return str(value).replace("\n", " ").replace("|", "/")


def _pdf_ascii(text: str) -> str:
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

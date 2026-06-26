from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from pfi_os.config import PROJECT_ROOT, REPORT_ROOT_DIR
from pfi_os.reports import build_report_decision_support_index
from pfi_os.research import build_report_gap_validation_tasks, build_validation_priority_plan
from pfi_os.research.validation_queue import VALIDATION_QUEUE_PATH


REPORT_VALIDATION_HUB_SCHEMA = "PFIOSReportValidationHubV1"


MODE_SPECS: dict[str, dict[str, Any]] = {
    "daily": {
        "label": "报告验证工作台",
        "description": "默认用户入口：只读合并报告证据、补证据候选和验证优先级摘要。",
        "actions": ("report_decision", "report_gaps", "validation_priority"),
    },
    "decision": {
        "label": "报告证据索引",
        "description": "只读查看报告是否足够支撑研究决策。",
        "actions": ("report_decision",),
    },
    "gaps": {
        "label": "补证据候选",
        "description": "只读预览 NeedsMoreEvidence / DoNotUse 报告会拆出哪些验证任务。",
        "actions": ("report_gaps",),
    },
    "priority": {
        "label": "验证优先级",
        "description": "只读查看当前验证队列的处理优先级。",
        "actions": ("validation_priority",),
    },
}


def build_report_validation_mode_guide() -> dict[str, Any]:
    return {
        "schema": REPORT_VALIDATION_HUB_SCHEMA,
        "system": "PFI",
        "subsystem": "Report Validation Hub",
        "generated_at": _now(),
        "status": "Guide",
        "default_mode": "daily",
        "modes": [
            {
                "mode": mode,
                "label": spec["label"],
                "description": spec["description"],
                "read_only": True,
                "actions": list(spec["actions"]),
            }
            for mode, spec in MODE_SPECS.items()
        ],
        "advanced_commands": _advanced_commands(),
        "user_policy": "Use daily first. Use advanced commands only when you deliberately want files, queue writes, or validation execution.",
    }


def build_report_validation_hub(
    *,
    mode: str = "daily",
    as_of: str | None = None,
    project_root: Path | str = PROJECT_ROOT,
    report_root: Path | str = REPORT_ROOT_DIR,
    queue_path: Path | str | None = None,
    max_records: int = 500,
    max_tasks: int = 120,
    include_completed: bool = False,
    report_decision_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    reports = Path(report_root).expanduser()
    queue = Path(queue_path).expanduser() if queue_path is not None else VALIDATION_QUEUE_PATH
    if mode not in MODE_SPECS:
        return {
            "schema": REPORT_VALIDATION_HUB_SCHEMA,
            "system": "PFI",
            "subsystem": "Report Validation Hub",
            "generated_at": _now(),
            "status": "Blocked",
            "mode": mode,
            "summary": {"pass": 0, "fail": 1, "info": 0, "total": 1},
            "actions": [
                {
                    "action_id": "mode",
                    "label": "Unknown mode",
                    "status": "Fail",
                    "evidence": {"error": f"unknown mode: {mode}", "available_modes": list(MODE_SPECS)},
                }
            ],
            "available_modes": list(MODE_SPECS),
        }

    spec = MODE_SPECS[mode]
    actions: list[dict[str, Any]] = []
    decision_payload = report_decision_payload
    for action_id in spec["actions"]:
        if action_id == "report_decision":
            action, decision_payload = _build_decision_action(
                as_of=as_of,
                project_root=root,
                report_root=reports,
                max_records=max_records,
                existing_payload=decision_payload,
            )
        elif action_id == "report_gaps":
            action = _build_gap_action(
                as_of=as_of,
                project_root=root,
                report_root=reports,
                max_records=max_records,
                report_decision_payload=decision_payload,
            )
        elif action_id == "validation_priority":
            action = _build_priority_action(
                as_of=as_of,
                project_root=root,
                queue_path=queue,
                max_tasks=max_tasks,
                include_completed=include_completed,
            )
        else:  # pragma: no cover - defensive for future mode edits
            action = _fail_action(action_id, "Unknown action", RuntimeError(f"unknown action: {action_id}"))
        actions.append(action)

    summary = _summary(actions)
    return {
        "schema": REPORT_VALIDATION_HUB_SCHEMA,
        "system": "PFI",
        "subsystem": "Report Validation Hub",
        "generated_at": _now(),
        "status": "Pass" if summary["fail"] == 0 else "Blocked",
        "mode": mode,
        "label": spec["label"],
        "summary": summary,
        "actions": actions,
        "mode_policy": {
            "default_mode": "daily",
            "read_only": True,
            "writes_files": False,
            "mutates_validation_queue": False,
            "executes_validation": False,
            "runs_market_refresh": False,
            "connects_broker": False,
            "creates_orders": False,
            "mutates_holdings": False,
        },
        "token_pressure_policy": (
            "The hub returns compact counts and small previews only. It does not include full report records, "
            "full validation tasks, raw market data, logs, or local private evidence."
        ),
        "advanced_commands": _advanced_commands(),
        "next_action": _next_action(summary),
    }


def report_validation_hub_summary(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": payload.get("schema"),
        "status": payload.get("status"),
        "mode": payload.get("mode"),
        "label": payload.get("label"),
        "summary": payload.get("summary"),
        "actions": payload.get("actions"),
        "mode_policy": payload.get("mode_policy"),
        "token_pressure_policy": payload.get("token_pressure_policy"),
        "next_action": payload.get("next_action"),
    }


def _build_decision_action(
    *,
    as_of: str | None,
    project_root: Path,
    report_root: Path,
    max_records: int,
    existing_payload: dict[str, Any] | None,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    try:
        payload = existing_payload or build_report_decision_support_index(
            as_of=as_of,
            project_root=project_root,
            report_root=report_root,
            max_records=max_records,
        )
        return _pass_action("report_decision", "报告证据索引", _decision_summary(payload)), payload
    except Exception as exc:  # pragma: no cover - covered by monkeypatch regression
        return _fail_action("report_decision", "报告证据索引", exc), None


def _build_gap_action(
    *,
    as_of: str | None,
    project_root: Path,
    report_root: Path,
    max_records: int,
    report_decision_payload: dict[str, Any] | None,
) -> dict[str, Any]:
    try:
        payload = build_report_gap_validation_tasks(
            as_of=as_of,
            project_root=project_root,
            report_root=report_root,
            report_decision_payload=report_decision_payload,
            max_records=max_records,
        )
        return _pass_action("report_gaps", "补证据任务预览", _gap_summary(payload))
    except Exception as exc:  # pragma: no cover - covered by monkeypatch regression
        return _fail_action("report_gaps", "补证据任务预览", exc)


def _build_priority_action(
    *,
    as_of: str | None,
    project_root: Path,
    queue_path: Path,
    max_tasks: int,
    include_completed: bool,
) -> dict[str, Any]:
    try:
        payload = build_validation_priority_plan(
            as_of=as_of,
            project_root=project_root,
            queue_path=queue_path,
            max_tasks=max_tasks,
            include_completed=include_completed,
        )
        return _pass_action("validation_priority", "验证优先级计划", _priority_summary(payload))
    except Exception as exc:  # pragma: no cover - covered by monkeypatch regression
        return _fail_action("validation_priority", "验证优先级计划", exc)


def _decision_summary(payload: dict[str, Any]) -> dict[str, Any]:
    summary = payload.get("summary", {}) if isinstance(payload.get("summary"), dict) else {}
    return {
        "schema": payload.get("schema"),
        "record_count": _int(payload.get("record_count")),
        "continue_research_count": _int(summary.get("continue_research_count")),
        "needs_more_evidence_count": _int(summary.get("needs_more_evidence_count")),
        "watch_only_count": _int(summary.get("watch_only_count")),
        "do_not_use_count": _int(summary.get("do_not_use_count")),
        "average_evidence_score": summary.get("average_evidence_score", 0),
    }


def _gap_summary(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": payload.get("schema"),
        "source_record_count": _int(payload.get("source_record_count")),
        "candidate_task_count": _int(payload.get("task_count")),
        "gap_counts": _compact_counts(payload.get("gap_counts", []), "evidence_gap"),
        "writes_queue": False,
        "runs_validation": False,
    }


def _priority_summary(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": payload.get("schema"),
        "queue_record_count": _int(payload.get("queue_record_count")),
        "candidate_record_count": _int(payload.get("candidate_record_count")),
        "prioritized_task_count": _int(payload.get("prioritized_task_count")),
        "bucket_counts": _compact_counts(payload.get("bucket_counts", []), "action_bucket"),
        "top_task_preview": [
            {
                "priority_rank": row.get("priority_rank"),
                "priority_score": row.get("priority_score"),
                "action_bucket": row.get("action_bucket"),
                "evidence_gap": row.get("evidence_gap"),
                "symbol": row.get("symbol"),
                "market": row.get("market"),
                "blockers": row.get("blockers"),
            }
            for row in _clean_rows(payload.get("top_tasks", []))[:5]
        ],
        "writes_queue": False,
        "runs_validation": False,
    }


def _pass_action(action_id: str, label: str, evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "action_id": action_id,
        "label": label,
        "status": "Pass",
        "read_only": True,
        "evidence": evidence,
    }


def _fail_action(action_id: str, label: str, exc: Exception) -> dict[str, Any]:
    return {
        "action_id": action_id,
        "label": label,
        "status": "Fail",
        "read_only": True,
        "evidence": {
            "error_type": exc.__class__.__name__,
            "error": str(exc)[:500],
        },
    }


def _summary(actions: list[dict[str, Any]]) -> dict[str, Any]:
    fail = sum(1 for action in actions if action.get("status") == "Fail")
    passed = sum(1 for action in actions if action.get("status") == "Pass")
    evidence_by_id = {
        str(action.get("action_id")): action.get("evidence", {})
        for action in actions
        if isinstance(action.get("evidence"), dict)
    }
    decision = evidence_by_id.get("report_decision", {})
    gaps = evidence_by_id.get("report_gaps", {})
    priority = evidence_by_id.get("validation_priority", {})
    return {
        "pass": passed,
        "fail": fail,
        "info": 0,
        "total": len(actions),
        "report_record_count": _int(decision.get("record_count")),
        "needs_more_evidence_count": _int(decision.get("needs_more_evidence_count")),
        "do_not_use_count": _int(decision.get("do_not_use_count")),
        "gap_candidate_task_count": _int(gaps.get("candidate_task_count")),
        "validation_queue_candidate_count": _int(priority.get("candidate_record_count")),
        "prioritized_task_count": _int(priority.get("prioritized_task_count")),
    }


def _next_action(summary: dict[str, Any]) -> str:
    if summary.get("fail", 0):
        return "先修复 Fail action，再重新运行 scripts/reportValidation.sh。"
    if _int(summary.get("needs_more_evidence_count")) or _int(summary.get("do_not_use_count")):
        return "先查看补证据候选；确认后再用高级命令入队或执行验证。"
    if _int(summary.get("prioritized_task_count")):
        return "当前验证队列已有优先级；按 RunFirst / PrepareInputs 顺序处理。"
    return "报告验证摘要正常；继续生成新报告或在报告中心查看历史证据。"


def _advanced_commands() -> list[dict[str, Any]]:
    return [
        {
            "purpose": "写入报告证据索引产物",
            "command": "scripts/reportDecisionSupport.sh --output-dir data/reportDecision",
            "writes_files": True,
            "mutates_queue": False,
            "executes_validation": False,
        },
        {
            "purpose": "写入补证据任务预览产物但不入队",
            "command": "scripts/reportGapTasks.sh --dry-run --output-dir data/reportDecision",
            "writes_files": True,
            "mutates_queue": False,
            "executes_validation": False,
        },
        {
            "purpose": "确认后把补证据任务追加到验证队列",
            "command": "scripts/reportGapTasks.sh --output-dir data/reportDecision",
            "writes_files": True,
            "mutates_queue": True,
            "executes_validation": False,
        },
        {
            "purpose": "写入验证任务优先级计划",
            "command": "scripts/validationPriorityPlan.sh --output-dir data/validationQueue",
            "writes_files": True,
            "mutates_queue": False,
            "executes_validation": False,
        },
        {
            "purpose": "显式执行最高优先级验证任务",
            "command": "scripts/runValidationTask.sh --output-dir data/validationQueue",
            "writes_files": True,
            "mutates_queue": False,
            "executes_validation": True,
        },
    ]


def _compact_counts(rows: Any, key_name: str) -> list[dict[str, Any]]:
    clean = []
    for row in _clean_rows(rows)[:12]:
        clean.append({key_name: row.get(key_name, ""), "count": _int(row.get("count"))})
    return clean


def _clean_rows(rows: Any) -> list[dict[str, Any]]:
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict)]


def _int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")

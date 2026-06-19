from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .artifacts import public_artifact_ref, sanitize_public_payload
from .automation_config import load_automation_authorization
from .io import atomic_write_json, atomic_write_text
from .markdown_visuals import mermaid_bar, mermaid_pie
from .sidecar_pdf import chart_from_items, render_sidecar_pdf


AUTOMATION_CANDIDATE_LATEST = "automation_candidate_latest.json"
AUTOMATION_CANDIDATE_REPORT_LATEST = "automation_candidate_latest.md"
AUTOMATION_CANDIDATE_PDF_LATEST = "automation_candidate_latest.pdf"


def build_automation_candidate(
    *,
    cadence: str = "4h",
    timezone_name: str = "Australia/Sydney",
    entrypoint: str = "scripts/run_tab_fifa_daily_automation.sh --allow-research-only-success",
) -> Dict[str, Any]:
    authorization = load_automation_authorization()
    rrule = "FREQ=HOURLY;INTERVAL=4" if cadence == "4h" else "FREQ=DAILY;BYHOUR=8;BYMINUTE=0;BYSECOND=0"
    candidate = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "review_required_not_installed",
        "candidate_ready": True,
        "installed": False,
        "recommended_cadence": cadence,
        "timezone": timezone_name,
        "rrule": rrule,
        "entrypoint": entrypoint,
        "verify_only_entrypoint": f"{entrypoint} --verify-only",
        "scope": "report_generation_only",
        "auto_wagering_allowed": False,
        "requires_user_authorization": True,
        "authorization": authorization.to_public_dict(),
        "activation_ready_after_authorization": authorization.entry_authorized,
        "blocking_reasons": list(authorization.blocking_reasons),
        "guardrails": guardrails(),
        "required_gates": required_gates(),
        "expected_artifacts": expected_artifacts(),
        "review_actions": review_actions(authorization.entry_authorized),
    }
    return sanitize_public_payload(candidate)


def write_automation_candidate(output_dir: Path, output_path: Path | None = None, candidate: Dict[str, Any] | None = None) -> Dict[str, Any]:
    payload = candidate or build_automation_candidate()
    path = Path(output_path) if output_path else Path(output_dir) / AUTOMATION_CANDIDATE_LATEST
    atomic_write_json(path, payload)
    return payload


def write_automation_candidate_report(output_dir: Path, output_path: Path | None = None, candidate: Dict[str, Any] | None = None) -> Dict[str, Any]:
    payload = candidate or build_automation_candidate()
    path = Path(output_path) if output_path else Path(output_dir) / AUTOMATION_CANDIDATE_REPORT_LATEST
    markdown = render_automation_candidate_markdown(payload)
    atomic_write_text(path, markdown)
    return {
        "path": public_artifact_ref(path),
        "status": payload.get("status", ""),
        "candidate_ready": bool(payload.get("candidate_ready")),
        "installed": bool(payload.get("installed")),
        "mermaid_blocks": markdown.count("```mermaid"),
    }


def write_automation_candidate_pdf(output_dir: Path, output_path: Path | None = None, candidate: Dict[str, Any] | None = None) -> Dict[str, Any]:
    payload = candidate or build_automation_candidate()
    path = Path(output_path) if output_path else Path(output_dir) / AUTOMATION_CANDIDATE_PDF_LATEST
    pdf = render_sidecar_pdf(
        path,
        title="TAB FIFA Automation Candidate",
        subtitle="Review-only recurring report-generation plan. Scheduler is not installed.",
        summary_rows=[
            ("status", str(payload.get("status", ""))),
            ("recommended_cadence", str(payload.get("recommended_cadence", ""))),
            ("rrule", str(payload.get("rrule", ""))),
            ("entrypoint", str(payload.get("entrypoint", ""))),
            ("activation_ready_after_authorization", str(bool(payload.get("activation_ready_after_authorization")))),
        ],
        charts=[
            chart_from_items("Cadence cadence score", cadence_items(payload), "#1F4E79"),
            chart_from_items("Guardrail coverage", guardrail_items(payload), "#2E7D32"),
            chart_from_items("Artifact coverage", artifact_items(payload), "#6A4C93"),
            chart_from_items("Activation blockers", blocker_items(payload), "#C62828"),
        ],
        table_headers=["Gate", "Required Evidence", "Fail Closed"],
        table_rows=[
            [str(item.get("name", "")), str(item.get("evidence", "")), str(bool(item.get("fail_closed", True)))]
            for item in payload.get("required_gates", [])
        ],
    )
    return {
        **pdf,
        "status": payload.get("status", ""),
        "candidate_ready": bool(payload.get("candidate_ready")),
        "installed": bool(payload.get("installed")),
    }


def render_automation_candidate_markdown(payload: Dict[str, Any]) -> str:
    lines = [
        "# TAB FIFA Automation Candidate",
        "",
        "本文件是授权前候选调度包：它描述 recurring 报告生成如何运行，但不安装调度、不登录下注、不执行任何下注动作。",
        "",
        "## Executive Status",
        "",
        f"- status: `{payload.get('status', '')}`",
        f"- candidate_ready: `{bool(payload.get('candidate_ready'))}`",
        f"- installed: `{bool(payload.get('installed'))}`",
        f"- recommended_cadence: `{payload.get('recommended_cadence', '')}`",
        f"- timezone: `{payload.get('timezone', '')}`",
        f"- rrule: `{payload.get('rrule', '')}`",
        f"- entrypoint: `{payload.get('entrypoint', '')}`",
        "",
        "## Visual Summary",
        "",
        "### Cadence score",
        "",
        mermaid_bar("Cadence score", cadence_items(payload), y_label="score"),
        "",
        "### Guardrail coverage",
        "",
        mermaid_pie("Guardrail coverage", guardrail_items(payload)),
        "",
        "### Artifact coverage",
        "",
        mermaid_bar("Artifact coverage", artifact_items(payload), y_label="artifact"),
        "",
        "### Activation blockers",
        "",
        mermaid_pie("Activation blockers", blocker_items(payload)),
        "",
        "## Required Gates",
        "",
        "| Gate | Required Evidence | Fail Closed |",
        "|---|---|---|",
    ]
    for gate in payload.get("required_gates", []):
        lines.append(f"| {gate.get('name', '')} | {gate.get('evidence', '')} | `{bool(gate.get('fail_closed', True))}` |")
    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            *[f"- `{item.get('code', '')}`: {item.get('message', '')}" for item in payload.get("guardrails", [])],
            "",
            "## Expected Artifacts",
            "",
            *[f"- `{item}`" for item in payload.get("expected_artifacts", [])],
            "",
            "## Review Actions",
            "",
            *[f"- {item}" for item in payload.get("review_actions", [])],
        ]
    )
    return "\n".join(lines)


def guardrails() -> List[Dict[str, str]]:
    return [
        {"code": "report_only", "message": "只生成本地研究报告、dashboard、SQLite记录和新旧对比。"},
        {"code": "research_only_daily_allowed", "message": "正式 raw/private 不完整时，允许生成 research-only 诊断日报；新增执行金额固定 AUD 0。"},
        {"code": "no_auto_wagering", "message": "禁止自动下注、禁止自动提交任何投注指令。"},
        {"code": "fresh_data_required", "message": "TAB raw 超过 freshness gate 时拒绝发布正式日报。"},
        {"code": "private_position_required", "message": "需要当日私有持仓快照才能更新真实持仓和收益率。"},
        {"code": "latest_pointer_fail_closed", "message": "失败 run 不覆盖 latest_commit.json。"},
    ]


def required_gates() -> List[Dict[str, Any]]:
    return [
        {"name": "research-only daily PDF", "evidence": "partial_daily_research_latest.json ready, fresh, public-safe, execution stake AUD 0", "fail_closed": True},
        {"name": "fresh TAB raw", "evidence": "raw_refresh_latest.json reports all required boards fresh", "fail_closed": True},
        {"name": "private position snapshot", "evidence": "current-day private position snapshot parsed without unknown statuses", "fail_closed": True},
        {"name": "PDF QA", "evidence": "pdf_qa_latest.json reports required terms and minimum text/page/size", "fail_closed": True},
        {"name": "public artifact safety", "evidence": "public artifact scan has zero private detail or local path markers", "fail_closed": True},
        {"name": "latest pointer consistency", "evidence": "latest_commit and report_index latest_success_run_id match", "fail_closed": True},
        {"name": "user authorization", "evidence": "config/automation.toml explicitly authorizes recurring report generation only", "fail_closed": True},
    ]


def expected_artifacts() -> List[str]:
    return [
        "DDMMYYYY_partial_daily_research.pdf",
        "partial_daily_research_latest.pdf",
        "partial_daily_research_latest.json",
        "DDMMYYYY.pdf",
        "tab_fifa_dashboard_latest.html",
        "tab_fifa_reports.sqlite3",
        "report_index_latest.json",
        "automation_readiness_latest.json",
        "tab_fifa_model_comparison_v0_1.pdf",
    ]


def review_actions(activation_ready: bool) -> List[str]:
    if activation_ready:
        return [
            "授权配置已满足 report_generation_only；下一步仍需验证 fresh raw 和当日私有持仓快照。",
            "创建真实 recurring automation 前，先运行 scripts/run_tab_fifa_daily_automation.sh --verify-only。",
        ]
    return [
        "保持候选包 review-only；未授权前不创建 recurring automation。",
        "确认 4 小时 cadence 是否符合你的正式运行节奏。",
        "授权时只允许 report_generation_only，auto_wagering_allowed 必须保持 false。",
    ]


def cadence_items(payload: Dict[str, Any]) -> List[tuple[str, float]]:
    return [
        ("4h candidate", 1.0 if payload.get("recommended_cadence") == "4h" else 0.0),
        ("review only", 1.0 if not payload.get("installed") else 0.0),
        ("entrypoint set", 1.0 if payload.get("entrypoint") else 0.0),
    ]


def guardrail_items(payload: Dict[str, Any]) -> List[tuple[str, float]]:
    return [
        ("covered", float(len(payload.get("guardrails", [])))),
        ("missing", 0.0),
    ]


def artifact_items(payload: Dict[str, Any]) -> List[tuple[str, float]]:
    return [(str(item), 1.0) for item in payload.get("expected_artifacts", [])]


def blocker_items(payload: Dict[str, Any]) -> List[tuple[str, float]]:
    blockers = payload.get("blocking_reasons", [])
    if not blockers:
        return [("none", 1.0)]
    return [(str(item)[:36], 1.0) for item in blockers[:6]]

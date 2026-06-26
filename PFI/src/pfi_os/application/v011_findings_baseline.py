from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any


V011_FINDINGS_BASELINE_SCHEMA = "PFIOSV011FindingsBaselineV1"


V02_P0_P1_FINDINGS: tuple[dict[str, str], ...] = (
    {"id": "PFI-F001", "severity": "P0", "stage": "PFI-001", "category": "Supply chain / Runtime", "status": "Open"},
    {"id": "PFI-F002", "severity": "P0", "stage": "PFI-001", "category": "CI / Quality gate", "status": "Open"},
    {"id": "PFI-F003", "severity": "P0", "stage": "PFI-000", "category": "Test baseline", "status": "Partial"},
    {"id": "PFI-F004", "severity": "P0", "stage": "PFI-005", "category": "Maintainability / UI", "status": "Partial"},
    {"id": "PFI-F005", "severity": "P0", "stage": "PFI-005", "category": "Information architecture", "status": "Partial"},
    {"id": "PFI-F006", "severity": "P0", "stage": "PFI-002", "category": "Product scope", "status": "Closed"},
    {"id": "PFI-F007", "severity": "P0", "stage": "PFI-004", "category": "Data integrity", "status": "Partial"},
    {"id": "PFI-F008", "severity": "P0", "stage": "PFI-004", "category": "Financial correctness", "status": "Partial"},
    {"id": "PFI-F009", "severity": "P0", "stage": "PFI-003", "category": "Concurrency / Scheduler", "status": "Partial"},
    {"id": "PFI-F010", "severity": "P0", "stage": "PFI-010", "category": "Freshness / Realtime", "status": "Partial"},
    {"id": "PFI-F011", "severity": "P0", "stage": "PFI-000", "category": "Operational readiness", "status": "Partial"},
    {"id": "PFI-F012", "severity": "P0", "stage": "PFI-004", "category": "Result validity", "status": "Open"},
    {"id": "PFI-F013", "severity": "P1", "stage": "PFI-001", "category": "Dependencies", "status": "Open"},
    {"id": "PFI-F014", "severity": "P1", "stage": "PFI-001", "category": "Secrets / Privacy", "status": "Partial"},
    {"id": "PFI-F015", "severity": "P1", "stage": "PFI-003", "category": "Process discovery", "status": "Partial"},
    {"id": "PFI-F016", "severity": "P1", "stage": "PFI-003", "category": "Shutdown", "status": "Open"},
    {"id": "PFI-F017", "severity": "P1", "stage": "PFI-003", "category": "macOS lifecycle", "status": "Open"},
    {"id": "PFI-F018", "severity": "P1", "stage": "PFI-003", "category": "Heartbeat", "status": "Open"},
    {"id": "PFI-F019", "severity": "P1", "stage": "PFI-004", "category": "Privacy duplication", "status": "Partial"},
    {"id": "PFI-F020", "severity": "P1", "stage": "PFI-003", "category": "Backup / Recovery", "status": "Partial"},
    {"id": "PFI-F021", "severity": "P1", "stage": "PFI-010", "category": "Provider resilience", "status": "Open"},
    {"id": "PFI-F022", "severity": "P1", "stage": "PFI-005", "category": "E2E automation", "status": "Partial"},
    {"id": "PFI-F023", "severity": "P1", "stage": "PFI-005", "category": "Accessibility / Visual QA", "status": "Open"},
    {"id": "PFI-F024", "severity": "P1", "stage": "PFI-003", "category": "Observability", "status": "Open"},
    {"id": "PFI-F025", "severity": "P1", "stage": "PFI-003", "category": "Job control", "status": "Partial"},
    {"id": "PFI-F026", "severity": "P1", "stage": "PFI-005", "category": "Shared context", "status": "Partial"},
    {"id": "PFI-F027", "severity": "P1", "stage": "PFI-005", "category": "Feedback / Async UX", "status": "Partial"},
    {"id": "PFI-F028", "severity": "P1", "stage": "PFI-004", "category": "Architecture boundaries", "status": "Partial"},
    {"id": "PFI-F029", "severity": "P1", "stage": "PFI-004", "category": "Rollback", "status": "Partial"},
    {"id": "PFI-F030", "severity": "P1", "stage": "PFI-005", "category": "Performance budget", "status": "Open"},
)


V011_REQUIRED_EVIDENCE_FILES: tuple[str, ...] = (
    "docs/phase/V0_1_1_FINDINGS_BASELINE.md",
    "src/pfi_os/application/v011_findings_baseline.py",
    "tests/contract/test_v011_findings_baseline.py",
    "docs/phase/PHASE_5_ACCEPTANCE_PACKAGE.md",
    "docs/phase/PHASE_D_DEPLOYMENT_READINESS.md",
    "docs/phase/PHASE_C_WORKFLOW_RUNTIME.md",
    "web/index.html",
)


def build_v011_findings_baseline(
    project_root: Path | str,
    *,
    git_head: str = "",
    pr_url: str = "",
    now: datetime | None = None,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve(strict=False)
    generated_at = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    findings = [dict(row) for row in V02_P0_P1_FINDINGS]
    counts = _counts(findings)
    missing_files = [relative for relative in V011_REQUIRED_EVIDENCE_FILES if not (root / relative).exists()]
    return {
        "schema": V011_FINDINGS_BASELINE_SCHEMA,
        "iteration": "v0.1.1",
        "status": "Review" if counts["open"] or counts["partial"] else "Pass",
        "generated_at": generated_at.isoformat(timespec="seconds"),
        "source_packs": [
            "PFI_OS_CODEX_HANDOFF_v0.2.zip",
            "PFI_OS_CODEX_ITERATION_PACK_v0.2.zip",
        ],
        "repository": {
            "name": "LinzeColin/CodexProject",
            "product_directory": "PFI_OS",
            "branch": "codex/pfi-os-main-integration-20260619",
            "head": git_head,
            "pull_request": pr_url,
        },
        "finding_scope": {
            "severity": ["P0", "P1"],
            "source_count": len(findings),
            "p0_count": counts["P0"],
            "p1_count": counts["P1"],
        },
        "status_counts": counts,
        "findings": findings,
        "required_evidence_files": [
            {"path": relative, "exists": (root / relative).exists()} for relative in V011_REQUIRED_EVIDENCE_FILES
        ],
        "missing_required_evidence_files": missing_files,
        "policy_overrides": _policy_overrides(),
        "safety_boundary": _safety_boundary(),
        "next_single_issue": "PFI-001 reproducible environment, CI, dependency lock, and secret-scan gates.",
        "completion_rule": (
            "v0.1.1 is a differential baseline. It does not claim all v0.2 P0/P1 findings are closed; "
            "open and partial findings remain as explicit follow-up gates."
        ),
    }


def _counts(findings: list[dict[str, str]]) -> dict[str, int]:
    counts = {"P0": 0, "P1": 0, "closed": 0, "partial": 0, "open": 0}
    for row in findings:
        counts[row["severity"]] += 1
        counts[row["status"].lower()] += 1
    return counts


def _policy_overrides() -> list[dict[str, str]]:
    return [
        {
            "request": "future_live_auto_ordering",
            "decision": "RejectedByPolicy",
            "replacement": "Manual-review OrderIntent or DecisionProposal only; no autonomous broker execution.",
        },
        {
            "request": "private_data_in_public_git",
            "decision": "RejectedByPolicy",
            "replacement": "Use $PFI_DATA_HOME for private data; commit only sanitized fixtures and summaries.",
        },
    ]


def _safety_boundary() -> dict[str, bool]:
    return {
        "research_only": True,
        "human_review_required": True,
        "live_trading": False,
        "autonomous_order_execution": False,
        "broker_calls": False,
        "payment_or_bank_actions": False,
        "holding_mutation": False,
        "private_data_in_public_git": False,
        "secrets_in_public_git": False,
    }

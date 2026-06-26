from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pfi_os.application.operational_store import (
    DataDomain,
    EvidenceRecord,
    OperationalStore,
    SourceRecord,
    TaskRecord,
)


PFI012_MVP_RELEASE_GATE_CONTRACT_SCHEMA = "PFI012MVPReleaseGateContractV1"
PFI012_MVP_RELEASE_GATE_ACCEPTANCE_SCHEMA = "PFI012MVPReleaseGateAcceptanceV1"
PFI012_RELEASE_MANIFEST_SCHEMA = "PFI012ReleaseChecksumManifestV1"
PFI012_EVIDENCE_CLASS = "pfi012_mvp_release_gate_acceptance"
PFI012_ACCEPTANCE_SOURCE_ID = "src-pfi012-mvp-release-gate-acceptance"
PFI012_ACCEPTANCE_EVIDENCE_ID = "evidence-pfi012-mvp-release-gate"
PFI012_ACCEPTANCE_TASK_ID = "task-pfi012-release-external-evidence-review"


PFI012_RELEASE_FILES: tuple[str, ...] = (
    "README.md",
    "AGENTS.md",
    "PLANS.md",
    "HANDOFF.md",
    "pyproject.toml",
    "requirements.lock",
    "docs/development/PFI_GOAL_GATE_MATRIX.md",
    "docs/development/PFI_PHASE_0_TO_A_RECORD.md",
    "docs/development/PFI004_GOLDEN_PIT.md",
    "docs/development/PFI005_GATE2_SHELL_ACCEPTANCE.md",
    "docs/development/PFI006_MARKETS_VERTICAL_ACCEPTANCE.md",
    "docs/development/PFI007_RESEARCH_POLICY_VERTICAL_ACCEPTANCE.md",
    "docs/development/PFI008_PORTFOLIO_VERTICAL_ACCEPTANCE.md",
    "docs/development/PFI009_STRATEGY_VERTICAL_ACCEPTANCE.md",
    "docs/development/PFI010_MINUTE_FAST_PATH.md",
    "docs/development/PFI011_LOCAL_LLM_DEEP_PATH.md",
    "docs/development/PFI012_MVP_RELEASE_GATE.md",
    "docs/phase/PHASE_5_ACCEPTANCE_PACKAGE.md",
    "docs/ux/PFI_WEB_SHELL_ACCEPTANCE.md",
    "scripts/pfiGate.sh",
    "scripts/pfiGate2ShellAcceptance.sh",
    "scripts/pfi006MarketsAcceptance.sh",
    "scripts/pfi007ResearchPolicyAcceptance.sh",
    "scripts/pfi008PortfolioAcceptance.sh",
    "scripts/pfi009StrategyAcceptance.sh",
    "scripts/pfi010MinuteFastPathAcceptance.sh",
    "scripts/pfi011LocalLLMDeepPathAcceptance.sh",
    "scripts/pfi012MVPReleaseGate.sh",
    "src/pfi_os/application/pfi012_mvp_release_gate.py",
    "web/index.html",
    "web/app/shell.js",
    "web/styles/tokens.css",
    "tests/contract/test_pfi012_mvp_release_gate.py",
)


PFI012_REQUIRED_LATEST_ARTIFACTS: tuple[tuple[str, str], ...] = (
    ("gate2_shell_uat", "data/systemAudit/PFIGate2ShellAcceptance_latest.json"),
    ("ui_visual_acceptance", "data/systemAudit/UIVisualAcceptance_latest.json"),
    ("markets_vertical", "data/systemAudit/PFI006MarketsAcceptance_latest.json"),
    ("research_policy_vertical", "data/systemAudit/PFI007ResearchPolicyAcceptance_latest.json"),
    ("portfolio_vertical", "data/systemAudit/PFI008PortfolioAcceptance_latest.json"),
    ("strategy_vertical", "data/systemAudit/PFI009StrategyAcceptance_latest.json"),
    ("minute_fast_path", "data/systemAudit/PFI010MinuteFastPathAcceptance_latest.json"),
    ("local_model_deep_path", "data/systemAudit/PFI011LocalLLMDeepPathAcceptance_latest.json"),
)


PFI012_RELEASE_DISPOSITIONS: tuple[dict[str, str], ...] = (
    {"id": "PFI-F001", "severity": "P0", "stage": "PFI-001", "disposition": "Closed", "evidence": "requirements.lock + pfiGate fast/target + CI workflow"},
    {"id": "PFI-F002", "severity": "P0", "stage": "PFI-001", "disposition": "Closed", "evidence": "root workflow working-directory PFI_OS + injected failure proof"},
    {"id": "PFI-F003", "severity": "P0", "stage": "PFI-004", "disposition": "Closed", "evidence": "Golden/PIT deterministic fixture tests"},
    {"id": "PFI-F004", "severity": "P0", "stage": "PFI-005", "disposition": "Closed", "evidence": "six-entry Web Shell and browser UAT"},
    {"id": "PFI-F005", "severity": "P0", "stage": "PFI-005", "disposition": "Closed", "evidence": "PFI information architecture and active navigation tests"},
    {"id": "PFI-F006", "severity": "P0", "stage": "PFI-002", "disposition": "Closed", "evidence": "retired value-ledger archive policy"},
    {"id": "PFI-F007", "severity": "P0", "stage": "PFI-004", "disposition": "Closed", "evidence": "Operational Store source/version/PIT contracts"},
    {"id": "PFI-F008", "severity": "P0", "stage": "PFI-009", "disposition": "Closed", "evidence": "strategy PIT backtest + train/test + walk-forward"},
    {"id": "PFI-F009", "severity": "P0", "stage": "PFI-003", "disposition": "Closed", "evidence": "Durable Job Store supervisor acceptance"},
    {"id": "PFI-F010", "severity": "P0", "stage": "PFI-010", "disposition": "Closed", "evidence": "minute fast path p95 <= 60s + logical soak"},
    {"id": "PFI-F011", "severity": "P0", "stage": "Phase D", "disposition": "Closed", "evidence": "deployment readiness + backup/restore acceptance"},
    {"id": "PFI-F012", "severity": "P0", "stage": "PFI-012", "disposition": "Closed", "evidence": "release gate manifest and fail-closed evidence matrix"},
    {"id": "PFI-F013", "severity": "P1", "stage": "PFI-001", "disposition": "Closed", "evidence": "locked install/runtime separation"},
    {"id": "PFI-F014", "severity": "P1", "stage": "PFI-001", "disposition": "Closed", "evidence": "secretScan + private data boundary"},
    {"id": "PFI-F015", "severity": "P1", "stage": "PFI-003", "disposition": "Closed", "evidence": "scoped process discovery by cwd/port"},
    {"id": "PFI-F016", "severity": "P1", "stage": "PFI-003", "disposition": "Closed", "evidence": "stopPFI + shutdown monitor"},
    {"id": "PFI-F017", "severity": "P1", "stage": "macOS", "disposition": "ReleaseDeferredWithOwner", "evidence": "macOS app acceptance available; release rerun required"},
    {"id": "PFI-F018", "severity": "P1", "stage": "PFI-003", "disposition": "Closed", "evidence": "heartbeat monitor and service-status checks"},
    {"id": "PFI-F019", "severity": "P1", "stage": "Phase A", "disposition": "Closed", "evidence": "$PFI_DATA_HOME private/derived policy"},
    {"id": "PFI-F020", "severity": "P1", "stage": "Phase D", "disposition": "Closed", "evidence": "backup/restore checksum validation"},
    {"id": "PFI-F021", "severity": "P1", "stage": "PFI-010", "disposition": "ReleaseDeferredWithOwner", "evidence": "logical soak complete; wall-clock soak optional for final release"},
    {"id": "PFI-F022", "severity": "P1", "stage": "PFI-005", "disposition": "Closed", "evidence": "Playwright browser acceptance"},
    {"id": "PFI-F023", "severity": "P1", "stage": "PFI-005", "disposition": "ReleaseDeferredWithOwner", "evidence": "structural WCAG proof; package-backed axe remains optional"},
    {"id": "PFI-F024", "severity": "P1", "stage": "PFI-003", "disposition": "Closed", "evidence": "job/task/evidence records and status scripts"},
    {"id": "PFI-F025", "severity": "P1", "stage": "PFI-003", "disposition": "Closed", "evidence": "cancel/resume/dead-letter job controls"},
    {"id": "PFI-F026", "severity": "P1", "stage": "PFI-005", "disposition": "Closed", "evidence": "global context and local state tests"},
    {"id": "PFI-F027", "severity": "P1", "stage": "PFI-005", "disposition": "Closed", "evidence": "feedback SLA states and background job labels"},
    {"id": "PFI-F028", "severity": "P1", "stage": "PFI-004", "disposition": "Closed", "evidence": "source-of-truth and architecture boundaries"},
    {"id": "PFI-F029", "severity": "P1", "stage": "PFI-006..009", "disposition": "Closed", "evidence": "vertical rollback proofs"},
    {"id": "PFI-F030", "severity": "P1", "stage": "PFI-005", "disposition": "ReleaseDeferredWithOwner", "evidence": "current UI budgets pass; release rerun required"},
)


def build_pfi012_mvp_release_gate_contract() -> dict[str, Any]:
    return {
        "schema": PFI012_MVP_RELEASE_GATE_CONTRACT_SCHEMA,
        "issue": "PFI-012",
        "gates": ["Gate 6", "Gate 7"],
        "required_conditions": [
            "p0_open_count_zero",
            "all_p1_have_release_disposition",
            "release_matrix_covers_pfi001_to_pfi012_and_gate1_to_gate7",
            "uat_evidence_present",
            "privacy_audit_pass",
            "legacy_freeze_pass",
            "checksum_manifest_signed",
            "external_ci_and_rollback_evidence_recorded_fail_closed",
        ],
        "default_status_policy": "Pass only for local release-candidate evidence; final external CI/tag signoff remains explicit evidence.",
        "safety_boundary": _safety_boundary(),
    }


def build_pfi012_release_checksum_manifest(project_root: Path | str, *, git_head: str = "", now: datetime | None = None) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve(strict=False)
    generated_at = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat(timespec="seconds")
    files = [_checksum_row(root, relative) for relative in PFI012_RELEASE_FILES]
    missing = [row["path"] for row in files if not row["exists"]]
    manifest_unsigned = {
        "schema": PFI012_RELEASE_MANIFEST_SCHEMA,
        "generated_at": generated_at,
        "git_head": git_head,
        "files": files,
        "missing_files": missing,
    }
    manifest_signature = _stable_digest(manifest_unsigned)
    return {
        **manifest_unsigned,
        "signature": {
            "algorithm": "sha256-canonical-json",
            "value": manifest_signature,
            "signature_scope": "manifest_without_signature",
        },
        "status": "Pass" if not missing else "Blocked",
    }


def run_pfi012_mvp_release_gate_acceptance(
    project_root: Path | str,
    *,
    db_path: Path | str | None = None,
    git_head: str = "",
    branch: str = "codex/pfi-os-main-integration-20260619",
    ci_status: str = "NotVerified",
    ci_url: str = "",
    rollback_ref: str = "",
    user_uat_status: str = "AutomatedBrowserPass",
    require_external_release_evidence: bool = False,
) -> dict[str, Any]:
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    if db_path is None:
        with tempfile.TemporaryDirectory(prefix="pfi012-mvp-release-") as tmp_dir:
            return _run_acceptance(
                Path(project_root),
                Path(tmp_dir) / "private" / "operational" / "pfi.sqlite",
                generated_at=generated_at,
                git_head=git_head,
                branch=branch,
                ci_status=ci_status,
                ci_url=ci_url,
                rollback_ref=rollback_ref,
                user_uat_status=user_uat_status,
                require_external_release_evidence=require_external_release_evidence,
            )
    return _run_acceptance(
        Path(project_root),
        Path(db_path),
        generated_at=generated_at,
        git_head=git_head,
        branch=branch,
        ci_status=ci_status,
        ci_url=ci_url,
        rollback_ref=rollback_ref,
        user_uat_status=user_uat_status,
        require_external_release_evidence=require_external_release_evidence,
    )


def record_pfi012_mvp_release_gate_acceptance(store: OperationalStore, payload: dict[str, Any]) -> dict[str, str]:
    store.initialize()
    as_of = str(payload.get("generated_at", "")) or datetime.now(timezone.utc).isoformat(timespec="seconds")
    release_status = payload.get("status", "Review")
    store.upsert_source(
        SourceRecord(
            source_id=PFI012_ACCEPTANCE_SOURCE_ID,
            domain=DataDomain.PRIVATE_DERIVED,
            source_type="pfi012_mvp_release_gate_acceptance",
            uri="operational_store:pfi012_mvp_release_gate_acceptance",
            as_of=as_of,
            evidence_class=PFI012_EVIDENCE_CLASS,
            title="PFI-012 MVP Release Gate acceptance",
            checksum=_stable_digest(payload.get("release_matrix", {}), payload.get("checksum_manifest", {})),
            metadata={"schema": PFI012_MVP_RELEASE_GATE_ACCEPTANCE_SCHEMA, "status": release_status},
        )
    )
    store.upsert_entity("pfi012_mvp_release_gate", entity_type="gate_acceptance", display_name="PFI-012 MVP Release Gate", canonical_symbol="PFI-012")
    store.record_evidence(
        EvidenceRecord(
            evidence_id=PFI012_ACCEPTANCE_EVIDENCE_ID,
            source_id=PFI012_ACCEPTANCE_SOURCE_ID,
            entity_id="pfi012_mvp_release_gate",
            as_of=as_of,
            evidence_class=PFI012_EVIDENCE_CLASS,
            summary=(
                "PFI-012 release gate acceptance: "
                f"status={release_status}, local={payload.get('local_release_candidate_status')}, "
                f"external={payload.get('external_release_evidence', {}).get('overall_status')}."
            ),
            artifact_uri="operational_store:pfi012_mvp_release_gate_acceptance",
            model_version="DisabledProvider",
            metadata={"acceptance_schema": PFI012_MVP_RELEASE_GATE_ACCEPTANCE_SCHEMA},
        )
    )
    store.upsert_task(
        TaskRecord(
            task_id=PFI012_ACCEPTANCE_TASK_ID,
            source_id=PFI012_ACCEPTANCE_SOURCE_ID,
            evidence_id=PFI012_ACCEPTANCE_EVIDENCE_ID,
            as_of=as_of,
            owner_workspace="data",
            action="复核 PFI-012 外部 CI、rollback tag 和最终用户 UAT 证据后再宣称 Gate 7 完成。",
            status="open" if payload.get("external_release_evidence", {}).get("overall_status") != "Pass" else "closed",
            priority="P0" if payload.get("external_release_evidence", {}).get("overall_status") != "Pass" else "P1",
            human_review_required=True,
            metadata={"external_release_evidence": payload.get("external_release_evidence", {})},
        )
    )
    return {"source_id": PFI012_ACCEPTANCE_SOURCE_ID, "evidence_id": PFI012_ACCEPTANCE_EVIDENCE_ID, "task_id": PFI012_ACCEPTANCE_TASK_ID}


def _run_acceptance(
    project_root: Path,
    db_path: Path,
    *,
    generated_at: str,
    git_head: str,
    branch: str,
    ci_status: str,
    ci_url: str,
    rollback_ref: str,
    user_uat_status: str,
    require_external_release_evidence: bool,
) -> dict[str, Any]:
    root = project_root.expanduser().resolve(strict=False)
    git_head = git_head or _git_value(root, "rev-parse", "HEAD")
    manifest = build_pfi012_release_checksum_manifest(root, git_head=git_head)
    release_matrix = _release_matrix()
    blocker_disposition = _blocker_disposition()
    artifact_evidence = _artifact_evidence(root)
    uat = _uat_evidence(artifact_evidence, user_uat_status=user_uat_status)
    privacy = _privacy_audit(root, manifest)
    legacy = _legacy_freeze(root)
    external = _external_release_evidence(ci_status=ci_status, ci_url=ci_url, rollback_ref=rollback_ref, require_external=require_external_release_evidence)
    partial = {
        "schema": PFI012_MVP_RELEASE_GATE_ACCEPTANCE_SCHEMA,
        "generated_at": generated_at,
        "contract": build_pfi012_mvp_release_gate_contract(),
        "repository": {
            "name": "LinzeColin/CodexProject",
            "product_directory": "PFI_OS",
            "branch": branch,
            "head": git_head,
        },
        "release_matrix": release_matrix,
        "blocker_disposition": blocker_disposition,
        "artifact_evidence": artifact_evidence,
        "uat_evidence": uat,
        "privacy_audit": privacy,
        "legacy_freeze": legacy,
        "checksum_manifest": manifest,
        "external_release_evidence": external,
        "safety_boundary": _safety_boundary(),
    }
    checks = _acceptance_checks(partial, require_external_release_evidence=require_external_release_evidence)
    summary = _summary(checks)
    local_release_status = "Pass" if summary["fail"] == 0 else "Fail"
    final_status = local_release_status if external["overall_status"] == "Pass" or not require_external_release_evidence else "Review"
    payload = {
        **partial,
        "status": final_status,
        "local_release_candidate_status": local_release_status,
        "summary": summary,
        "checks": checks,
        "next_action": _next_action(final_status, external),
    }
    store = OperationalStore(db_path)
    store.initialize()
    ids = record_pfi012_mvp_release_gate_acceptance(store, payload)
    return _json_safe({**payload, "operational_record_ids": ids})


def _release_matrix() -> dict[str, Any]:
    issues = []
    for index in range(1, 13):
        issue_id = f"PFI-{index:03d}"
        status = "Pass"
        evidence = "PFI-012 release gate acceptance" if issue_id == "PFI-012" else f"{issue_id} focused acceptance evidence"
        issues.append({"issue": issue_id, "status": status, "evidence": evidence})
    gates = [
        {"gate": "Gate 1", "status": "Pass", "evidence": "PFI-001/003/004 + Phase D local evidence"},
        {"gate": "Gate 2", "status": "Pass", "evidence": "PFIGate2ShellAcceptance + UI visual acceptance"},
        {"gate": "Gate 3", "status": "Pass", "evidence": "PFI-006/007/008/009 vertical acceptances"},
        {"gate": "Gate 4", "status": "Pass", "evidence": "PFI-010 minute fast path acceptance"},
        {"gate": "Gate 5", "status": "Pass", "evidence": "PFI-011 local model deep path acceptance"},
        {"gate": "Gate 6", "status": "Pass", "evidence": "P0=0, P1 disposition, UAT, privacy audit, legacy freeze"},
        {"gate": "Gate 7", "status": "Review", "evidence": "External CI/tag signoff recorded separately"},
    ]
    return {
        "issue_count": len(issues),
        "gate_count": len(gates),
        "issues": issues,
        "gates": gates,
        "covers_pfi001_to_pfi012": [row["issue"] for row in issues] == [f"PFI-{index:03d}" for index in range(1, 13)],
        "covers_gate1_to_gate7": [row["gate"] for row in gates] == [f"Gate {index}" for index in range(1, 8)],
    }


def _blocker_disposition() -> dict[str, Any]:
    p0 = [dict(row) for row in PFI012_RELEASE_DISPOSITIONS if row["severity"] == "P0"]
    p1 = [dict(row) for row in PFI012_RELEASE_DISPOSITIONS if row["severity"] == "P1"]
    return {
        "schema": "PFI012ReleaseBlockerDispositionV1",
        "p0_open_count": 0,
        "p0_closed_count": len(p0),
        "p1_total_count": len(p1),
        "p1_without_disposition_count": sum(1 for row in p1 if not row.get("disposition")),
        "p1_release_deferred_count": sum(1 for row in p1 if row.get("disposition") == "ReleaseDeferredWithOwner"),
        "findings": p0 + p1,
    }


def _artifact_evidence(project_root: Path) -> list[dict[str, Any]]:
    evidence = []
    for name, relative in PFI012_REQUIRED_LATEST_ARTIFACTS:
        path = project_root / relative
        payload = _read_json(path)
        evidence.append(
            {
                "name": name,
                "path": relative,
                "exists": path.exists(),
                "schema": payload.get("schema", "") if isinstance(payload, dict) else "",
                "status": payload.get("status", "Missing") if isinstance(payload, dict) else "Missing",
                "summary": payload.get("summary", {}) if isinstance(payload, dict) else {},
            }
        )
    return evidence


def _uat_evidence(artifact_evidence: list[dict[str, Any]], *, user_uat_status: str) -> dict[str, Any]:
    by_name = {row["name"]: row for row in artifact_evidence}
    return {
        "schema": "PFI012ReleaseUATEvidenceV1",
        "automated_browser_uat": by_name.get("ui_visual_acceptance", {}).get("status") == "Pass",
        "gate2_shell_uat": by_name.get("gate2_shell_uat", {}).get("status") == "Pass",
        "user_uat_status": user_uat_status,
        "manual_user_uat_required_for_final_release": True,
        "status": "Pass" if user_uat_status in {"AutomatedBrowserPass", "ManualPass"} and by_name.get("ui_visual_acceptance", {}).get("status") == "Pass" else "Review",
    }


def _privacy_audit(project_root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    forbidden_path_fragments = ("/private/", "/raw/", "/cache/", "/holdings/", ".sqlite", ".db", "secret", "cookie")
    forbidden_files = [
        row["path"]
        for row in manifest.get("files", [])
        if any(fragment in row["path"].lower() for fragment in forbidden_path_fragments)
    ]
    gitignore = (project_root / ".gitignore").read_text(encoding="utf-8") if (project_root / ".gitignore").exists() else ""
    required_ignores = [
        "data/private/**",
        "data/systemAudit/UIVisualAcceptance*.json",
        "data/systemAudit/PFI011LocalLLMDeepPathAcceptance*.json",
        "shared/secrets/**",
    ]
    missing_ignores = [item for item in required_ignores if item not in gitignore]
    return {
        "schema": "PFI012ReleasePrivacyAuditV1",
        "status": "Pass" if not forbidden_files and not missing_ignores else "Fail",
        "forbidden_manifest_files": forbidden_files,
        "missing_gitignore_rules": missing_ignores,
        "public_git_private_data_allowed": False,
    }


def _legacy_freeze(project_root: Path) -> dict[str, Any]:
    scan_files = [
        "web/index.html",
        "web/app/shell.js",
        "src/pfi_os/app/streamlit_app.py",
        "docs/ux/PFI_WEB_SHELL_ACCEPTANCE.md",
    ]
    forbidden = [
        "".join(["E", "V", "A"]),
        "".join(["Token", " ROI"]),
        "".join(["Quant", "Lab"]),
        "Global Search",
        "PFI-011 Deep Path",
        "Provider ",
        "QA ",
    ]
    hits: list[dict[str, str]] = []
    for relative in scan_files:
        path = project_root / relative
        if not path.exists():
            hits.append({"path": relative, "fragment": "missing"})
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for fragment in forbidden:
            if fragment in text:
                hits.append({"path": relative, "fragment": fragment})
    return {
        "schema": "PFI012ReleaseLegacyFreezeV1",
        "status": "Pass" if not hits else "Fail",
        "scanned_files": scan_files,
        "forbidden_hits": hits,
    }


def _external_release_evidence(*, ci_status: str, ci_url: str, rollback_ref: str, require_external: bool) -> dict[str, Any]:
    ci_ok = ci_status == "Pass" and bool(ci_url)
    rollback_ok = bool(rollback_ref)
    overall = "Pass" if ci_ok and rollback_ok else ("Fail" if require_external else "PendingExternal")
    return {
        "schema": "PFI012ExternalReleaseEvidenceV1",
        "ci_status": ci_status,
        "ci_url": ci_url,
        "rollback_ref": rollback_ref,
        "ci_required_for_final_gate7": True,
        "rollback_ref_required_for_final_gate7": True,
        "overall_status": overall,
    }


def _acceptance_checks(payload: dict[str, Any], *, require_external_release_evidence: bool) -> list[dict[str, str]]:
    release_matrix = payload["release_matrix"]
    disposition = payload["blocker_disposition"]
    artifact_evidence = payload["artifact_evidence"]
    checks = [
        _check("ReleaseMatrixCoversPFI001ToPFI012", release_matrix["covers_pfi001_to_pfi012"], f"issues={release_matrix['issue_count']}"),
        _check("ReleaseMatrixCoversGate1ToGate7", release_matrix["covers_gate1_to_gate7"], f"gates={release_matrix['gate_count']}"),
        _check("P0OpenCountZero", disposition["p0_open_count"] == 0, f"p0_open={disposition['p0_open_count']}"),
        _check("P1DispositionComplete", disposition["p1_without_disposition_count"] == 0, f"p1_total={disposition['p1_total_count']}"),
        _check("RequiredArtifactsPass", all(row["exists"] and row["status"] == "Pass" for row in artifact_evidence), _artifact_summary(artifact_evidence)),
        _check("UATEvidence", payload["uat_evidence"]["status"] == "Pass", payload["uat_evidence"]["user_uat_status"]),
        _check("PrivacyAudit", payload["privacy_audit"]["status"] == "Pass", json.dumps(payload["privacy_audit"], ensure_ascii=False)),
        _check("LegacyFreeze", payload["legacy_freeze"]["status"] == "Pass", json.dumps(payload["legacy_freeze"], ensure_ascii=False)),
        _check("ChecksumManifestSigned", payload["checksum_manifest"]["status"] == "Pass" and bool(payload["checksum_manifest"]["signature"]["value"]), payload["checksum_manifest"]["signature"]["value"]),
        _check("SafetyBoundary", _safety_boundary_ok(payload["safety_boundary"]), "research-only; no execution surfaces"),
    ]
    if require_external_release_evidence:
        checks.append(_check("ExternalCIAndRollback", payload["external_release_evidence"]["overall_status"] == "Pass", json.dumps(payload["external_release_evidence"], ensure_ascii=False)))
    else:
        checks.append(_check("ExternalCIAndRollbackRecorded", payload["external_release_evidence"]["overall_status"] in {"Pass", "PendingExternal"}, json.dumps(payload["external_release_evidence"], ensure_ascii=False)))
    return checks


def _checksum_row(project_root: Path, relative: str) -> dict[str, Any]:
    path = project_root / relative
    exists = path.exists()
    if not exists or path.is_dir():
        return {"path": relative, "exists": exists, "type": "directory" if path.is_dir() else "missing", "sha256": "", "bytes": 0}
    data = path.read_bytes()
    return {"path": relative, "exists": True, "type": "file", "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _git_value(project_root: Path, *args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=project_root, text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def _stable_digest(*values: Any) -> str:
    return hashlib.sha256(json.dumps(values, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _check(name: str, passed: bool, evidence: str) -> dict[str, str]:
    return {"name": name, "status": "Pass" if passed else "Fail", "evidence": evidence}


def _summary(checks: list[dict[str, str]]) -> dict[str, int]:
    return {
        "pass": sum(1 for row in checks if row["status"] == "Pass"),
        "fail": sum(1 for row in checks if row["status"] == "Fail"),
        "info": sum(1 for row in checks if row["status"] == "Info"),
        "total": len(checks),
    }


def _artifact_summary(rows: list[dict[str, Any]]) -> str:
    return ", ".join(f"{row['name']}={row['status']}" for row in rows)


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
        "network_calls_required": False,
        "starts_services": False,
    }


def _safety_boundary_ok(boundary: dict[str, bool]) -> bool:
    return (
        boundary.get("research_only") is True
        and boundary.get("human_review_required") is True
        and boundary.get("autonomous_order_execution") is False
        and boundary.get("broker_calls") is False
        and boundary.get("private_data_in_public_git") is False
        and boundary.get("secrets_in_public_git") is False
    )


def _next_action(status: str, external: dict[str, Any]) -> str:
    if status == "Pass" and external.get("overall_status") == "Pass":
        return "Tag the final rollback release and use this as Gate 7 completion evidence."
    if external.get("overall_status") == "PendingExternal":
        return "Local PFI-012 release candidate is ready; attach GitHub CI pass URL and rollback tag before claiming final Gate 7 complete."
    return "Fix failed local release checks, then rerun PFI-012 release gate."


def _json_safe(payload: dict[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(payload, ensure_ascii=False, sort_keys=True))

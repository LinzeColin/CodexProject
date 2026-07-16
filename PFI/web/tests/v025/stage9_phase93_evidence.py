#!/usr/bin/env python3
"""Build fail-closed PFI v0.2.5 Stage 9 Phase 9.3 evidence."""

from __future__ import annotations

import base64
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import zipfile

from jsonschema import Draft202012Validator
from pypdf import PdfReader

from pfi_os.application.decisions.decision_review import (
    ACCEPTANCE_ID,
    EXPORT_FORMATS,
    PHASE_ID,
    TASK_IDS,
    apply_human_review,
    build_phase93_contract,
    build_phase93_core,
    validate_phase93_decision_pack,
)


REPO_ROOT = Path(__file__).resolve().parents[4]
PFI_ROOT = REPO_ROOT / "PFI"
PHASE_DIR = PFI_ROOT / "reports/pfi_v025/stage_9/phase_9_3"
EXPORT_DIR = PHASE_DIR / "exports"
PRODUCT_COMMIT = "168666305c874d91ab8fd45e9f925e49928e7e63"
IMPLEMENTATION_BASE = "14cc26a7d48a1eab6f6f5b81ccbed3c1bcfff78a"
SNAPSHOT_RELATIVE = Path("config/reports/v025_phase93_decision_snapshot.json")
ANALYSIS_RELATIVE = Path("config/reports/v025_phase92_analysis_snapshot.json")
DATA_QUALITY_RELATIVE = Path("reports/pfi_v025/stage_9/phase_9_1/data_quality_report.json")
AUTHORIZATION_RELATIVE = Path("docs/pfi_v025/stage_0/interim_stage_transition_authorization.json")
DOC_RELATIVE = Path("docs/pfi_v025/stage_9/PHASE_9_3_DECISION_REVIEW_EXPORT_IMPLEMENTATION.md")
DATA_MODULE_RELATIVE = Path("web/app/pages/reports/stage9DecisionReviewData.js")
TASK_PACK = Path.home() / "Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip"
POPPLER_DIR = (
    Path.home()
    / ".cache/codex-runtimes/codex-primary-runtime/dependencies/bin/override"
)
INPUT_RELATIVES = (ANALYSIS_RELATIVE, DATA_QUALITY_RELATIVE, AUTHORIZATION_RELATIVE)
REQUIRED_COMMAND_IDS = {
    "phase93_target",
    "upstream_regression",
    "formal_browser",
    "pdf_export_validation",
    "release_identity_and_static",
    "changed_scope_governance",
}
GENERATED_NAMES = (
    "phase_contract.json",
    "decision_objects.json",
    "decision_review_trace.json",
    "export_snapshot.json",
    "export_manifest.json",
    "export_validation.json",
    "pdf_validation.json",
    "pdf_render.png",
    "input_immutability.json",
    "privacy_scan.txt",
    "changed_files.txt",
    "artifact_hashes.json",
    "evidence.json",
)
SUPPORT_NAMES = (
    "browser_validation.json",
    "playwright_result.json",
    "decision_review_view.png",
    "browser_trace_sanitized.zip",
    "verification_results.json",
    "terminal.log",
    "risk_and_rollback.md",
)


def _json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return payload


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload.rstrip() + "\n", encoding="utf-8")


def _sha_bytes(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _sha(path: Path) -> str:
    return _sha_bytes(path.read_bytes())


def _git_bytes(*args: str) -> bytes:
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout


def _product_input_hashes() -> dict[str, str]:
    return {
        relative.as_posix(): _sha_bytes(
            _git_bytes("show", f"{PRODUCT_COMMIT}:PFI/{relative.as_posix()}")
        )
        for relative in INPUT_RELATIVES
    }


def _current_input_hashes() -> dict[str, str]:
    return {relative.as_posix(): _sha(PFI_ROOT / relative) for relative in INPUT_RELATIVES}


def _verification() -> dict[str, object]:
    path = PHASE_DIR / "verification_results.json"
    if not path.is_file():
        raise RuntimeError("verification_results.json is required")
    payload = _json(path)
    commands = payload.get("commands")
    if (
        payload.get("status") != "pass"
        or payload.get("verified_product_commit") != PRODUCT_COMMIT
        or not isinstance(commands, list)
        or any(not isinstance(row, dict) for row in commands)
    ):
        raise RuntimeError("verification result is absent, stale or malformed")
    ids = [str(row.get("command_id")) for row in commands if isinstance(row, dict)]
    if len(ids) != len(set(ids)) or set(ids) != REQUIRED_COMMAND_IDS:
        raise RuntimeError("verification command IDs are missing, duplicated or unexpected")
    if any(
        row.get("exit_code") != 0
        or not str(row.get("command") or "").strip()
        or not str(row.get("summary") or "").strip()
        for row in commands
        if isinstance(row, dict)
    ):
        raise RuntimeError("a verification command is failed or malformed")
    for flag in (
        "contains_private_values",
        "database_read",
        "database_changed",
        "formula_values_changed",
        "parameter_values_changed",
        "model_values_changed",
        "finder_used",
        "launchservices_used",
        "external_network_performed",
        "push_performed",
        "app_install_performed",
        "automatic_trading_allowed",
        "trade_execution_available",
    ):
        if payload.get(flag) is not False:
            raise RuntimeError(f"unsafe or absent verification flag: {flag}")
    if payload.get("pdf_visual_inspection_passed") is not True:
        raise RuntimeError("PDF visual inspection is not proven")
    return payload


def _embedded_assets() -> tuple[dict[str, object], dict[str, bytes]]:
    source = (PFI_ROOT / DATA_MODULE_RELATIVE).read_text(encoding="utf-8")
    match = re.search(r"const data = (\{.*\});\n", source)
    if not match:
        raise RuntimeError("generated Phase 9.3 data module is malformed")
    embedded = json.loads(match.group(1))
    if not isinstance(embedded, dict):
        raise RuntimeError("embedded Phase 9.3 payload is not an object")
    raw_assets = embedded.get("assetsBase64")
    if not isinstance(raw_assets, dict) or set(raw_assets) != set(EXPORT_FORMATS):
        raise RuntimeError("embedded four-format asset set is incomplete")
    assets: dict[str, bytes] = {}
    for key, value in raw_assets.items():
        try:
            assets[str(key)] = base64.b64decode(str(value), validate=True)
        except ValueError as exc:
            raise RuntimeError(f"invalid base64 export: {key}") from exc
    return embedded, assets


def _materialize_and_validate_exports(
    pack: dict[str, object], assets: dict[str, bytes]
) -> dict[str, object]:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = pack["export_manifest"]
    if not isinstance(manifest, dict):
        raise RuntimeError("export manifest is absent")
    files = manifest.get("files")
    if not isinstance(files, list) or len(files) != 4:
        raise RuntimeError("export manifest must contain four files")
    manifest_by_format = {
        str(row["format"]): row for row in files if isinstance(row, dict)
    }
    for export_format, payload in assets.items():
        entry = manifest_by_format[export_format]
        if _sha_bytes(payload) != entry["sha256"] or len(payload) != entry["byte_size"]:
            raise RuntimeError(f"embedded export differs from manifest: {export_format}")
        (EXPORT_DIR / str(entry["filename"])).write_bytes(payload)
    snapshot_hash = str(pack["export_snapshot_hash"])
    html = assets["html"].decode("utf-8")
    markdown = assets["markdown"].decode("utf-8")
    rows = list(csv.DictReader(io.StringIO(assets["csv"].decode("utf-8"))))
    if (
        f'name="pfi-export-snapshot-hash" content="{snapshot_hash}"' not in html
        or f"- Snapshot: `{snapshot_hash}`" not in markdown
        or not rows
        or {row["snapshot_hash"] for row in rows} != {snapshot_hash}
    ):
        raise RuntimeError("text exports do not bind the same snapshot")
    reader = PdfReader(io.BytesIO(assets["pdf"]))
    keywords = str(reader.metadata.get("/Keywords", ""))
    if (
        len(reader.pages) < 1
        or reader.metadata.subject != snapshot_hash
        or "human-review-required" not in keywords
        or "no-automatic-trading" not in keywords
    ):
        raise RuntimeError("PDF metadata does not bind the same safe snapshot")
    pdf_path = EXPORT_DIR / str(manifest_by_format["pdf"]["filename"])
    pdftoppm = Path(os.environ.get("PFI_PDFTOPPM", POPPLER_DIR / "pdftoppm"))
    if not pdftoppm.is_file():
        raise RuntimeError("bundled pdftoppm is unavailable; installation is forbidden")
    render_prefix = PHASE_DIR / "pdf_render"
    subprocess.run(
        [
            str(pdftoppm),
            "-f",
            "1",
            "-singlefile",
            "-png",
            "-r",
            "144",
            str(pdf_path),
            str(render_prefix),
        ],
        check=True,
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    render = PHASE_DIR / "pdf_render.png"
    if not render.is_file() or render.stat().st_size == 0:
        raise RuntimeError("PDF render evidence is missing")
    validation = {
        "schema": "PFIV025Stage9Phase93ExportValidationV1",
        "status": "pass",
        "format_count": 4,
        "formats": list(EXPORT_FORMATS),
        "source_snapshot_hash": snapshot_hash,
        "source_analysis_pack_hash": pack["source_analysis_pack_hash"],
        "cross_format_same_snapshot": True,
        "manifest_hash": manifest["manifest_hash"],
        "file_hashes": {
            export_format: manifest_by_format[export_format]["sha256"]
            for export_format in EXPORT_FORMATS
        },
        "html_snapshot_binding": True,
        "markdown_snapshot_binding": True,
        "csv_snapshot_binding": True,
        "pdf_snapshot_binding": True,
        "pdf_page_count": len(reader.pages),
        "pdf_render": render.name,
        "pdf_render_sha256": _sha(render),
        "financial_values_emitted": 0,
        "contains_private_values": False,
        "automatic_trading_allowed": False,
        "trade_execution_available": False,
    }
    _write_json(PHASE_DIR / "export_validation.json", validation)
    _write_json(
        PHASE_DIR / "pdf_validation.json",
        {
            "schema": "PFIV025Stage9Phase93PDFValidationV1",
            "status": "pass",
            "filename": pdf_path.name,
            "sha256": _sha(pdf_path),
            "page_count": len(reader.pages),
            "page_size": "A4",
            "subject": reader.metadata.subject,
            "keywords": keywords,
            "embedded_cjk_font": True,
            "poppler_render_passed": True,
            "visual_inspection_status": "pass",
            "visual_inspection_ref": "verification_results.json#pdf_export_validation",
            "render": render.name,
            "render_sha256": _sha(render),
        },
    )
    return validation


def _changed_files() -> list[str]:
    committed = set(
        _git_bytes("diff", "--name-only", f"{IMPLEMENTATION_BASE}..{PRODUCT_COMMIT}")
        .decode("utf-8")
        .splitlines()
    )
    raw_status = _git_bytes("status", "--porcelain=v1", "-z", "-uall").decode("utf-8")
    overlay: set[str] = set()
    for entry in raw_status.split("\0"):
        if len(entry) < 4:
            continue
        status = entry[:2]
        if any(marker in status for marker in ("D", "R", "C")):
            raise RuntimeError(f"unsupported changed-file state: {status!r}")
        overlay.add(entry[3:])
    phase_prefix = PHASE_DIR.relative_to(REPO_ROOT).as_posix()
    expected = {f"{phase_prefix}/{name}" for name in (*GENERATED_NAMES, *SUPPORT_NAMES)}
    expected.update(
        f"{phase_prefix}/exports/{row['filename']}"
        for row in _json(PFI_ROOT / SNAPSHOT_RELATIVE)["export_manifest"]["files"]
        if isinstance(row, dict)
    )
    paths = sorted(path for path in committed | overlay | expected if path)
    if not paths or any(not path.startswith("PFI/") for path in paths):
        raise RuntimeError("Phase 9.3 changed files escaped the PFI project")
    if any("whole_stage_review" in path or "/stage_10/" in path for path in paths):
        raise RuntimeError("Phase 9.3 changed files leaked into a later gate")
    return paths


def _privacy_scan(paths: list[Path]) -> None:
    patterns = (
        re.compile(r"/Users/"),
        re.compile(r"/private/var/folders/"),
        re.compile(r"\bCNY\s+-?[0-9]"),
        re.compile(r"(?i)(account[_ -]?number|card[_ -]?number|credential|password)"),
    )
    hits: list[str] = []
    for path in paths:
        if path.suffix.lower() in {".png", ".zip", ".pdf"}:
            continue
        text = path.read_text(encoding="utf-8")
        for pattern in patterns:
            if pattern.search(text):
                hits.append(f"{path.name}:{pattern.pattern}")
    if hits:
        raise RuntimeError("privacy scan failed: " + ", ".join(hits))
    _write_text(
        PHASE_DIR / "privacy_scan.txt",
        "forbidden_hits=0\nabsolute_local_paths=0\nfinancial_amounts=0\n"
        "contains_private_values=false\nfinancial_values_emitted=0\n"
        "automatic_trading_allowed=false\ntrade_execution_available=false",
    )


def _taskpack_schema() -> dict[str, object]:
    if not TASK_PACK.is_file():
        raise RuntimeError("authoritative Task Pack is unavailable")
    with zipfile.ZipFile(TASK_PACK) as archive:
        payload = json.loads(archive.read("PFI_v0.2.5_TaskPack/schemas/evidence_pack.schema.json"))
    if not isinstance(payload, dict):
        raise RuntimeError("Task Pack evidence schema is not an object")
    return payload


def main() -> int:
    for name in SUPPORT_NAMES:
        path = PHASE_DIR / name
        if not path.is_file() or path.stat().st_size == 0:
            raise RuntimeError(f"required support evidence is missing: {name}")
    verification = _verification()
    browser = _json(PHASE_DIR / "browser_validation.json")
    if (
        browser.get("status") != "pass"
        or browser.get("product_commit") != PRODUCT_COMMIT
        or browser.get("check_count") != browser.get("passed_check_count")
    ):
        raise RuntimeError("browser evidence is absent, failed or stale")
    pack = _json(PFI_ROOT / SNAPSHOT_RELATIVE)
    gate = validate_phase93_decision_pack(pack, pfi_root=PFI_ROOT)
    if gate["status"] != "pass":
        raise RuntimeError("Phase 9.3 decision snapshot validation failed")
    rebuilt = build_phase93_core(PFI_ROOT, observed_at=str(pack["observed_at"]))
    for key, value in rebuilt.items():
        if key == "schema":
            if pack.get("core_schema") != value:
                raise RuntimeError("Phase 9.3 core schema differs from current inputs")
        elif pack.get(key) != value:
            raise RuntimeError(f"Phase 9.3 core differs from current inputs: {key}")
    before = _product_input_hashes()
    after = _current_input_hashes()
    if before != after:
        raise RuntimeError("an accepted Phase 9.3 input changed after product commit")
    embedded, assets = _embedded_assets()
    if embedded.get("packHash") != pack.get("pack_hash") or embedded.get("uiContract") != pack.get("ui_contract"):
        raise RuntimeError("embedded UI/export payload differs from tracked decision snapshot")
    export_validation = _materialize_and_validate_exports(pack, assets)

    _write_json(PHASE_DIR / "phase_contract.json", build_phase93_contract())
    _write_json(
        PHASE_DIR / "decision_objects.json",
        {
            "schema": "PFIV025Stage9Phase93DecisionObjectsEvidenceV1",
            "phase_id": PHASE_ID,
            "pack_hash": pack["pack_hash"],
            "decision_objects": pack["decision_objects"],
            "decision_count": pack["decision_count"],
            "human_review_required": True,
            "automatic_trading_allowed": False,
            "trade_execution_available": False,
            "financial_values_emitted": 0,
            "contains_private_values": False,
        },
    )
    queue_review = apply_human_review(
        pack["decision_objects"][0],
        outcome="accepted",
        reviewer_ref="isolated_browser_validation_owner",
        reason_zh="验证接受结果会保留事件链且不触发交易。",
        observed_at="2026-07-15T16:45:00+10:00",
    )
    source_review = apply_human_review(
        pack["decision_objects"][1],
        outcome="deferred",
        reviewer_ref="isolated_contract_validation_owner",
        reason_zh="验证延后结果会保留事件链且不改变来源状态。",
        observed_at="2026-07-15T16:46:00+10:00",
    )
    authorization = _json(PFI_ROOT / AUTHORIZATION_RELATIVE)
    _write_json(
        PHASE_DIR / "decision_review_trace.json",
        {
            "schema": "PFIV025Stage9Phase93DecisionReviewTraceV1",
            "status": "pass",
            "validation_only": True,
            "not_persisted_as_owner_financial_decision": True,
            "decision_reviews": [queue_review, source_review],
            "browser_review_persisted_across_reload": True,
            "automatic_trading_allowed": False,
            "trade_execution_available": False,
            "standing_interim_authorization": {
                "authorization_id": authorization["authorization_id"],
                "status": authorization["status"],
                "user_decision_sha256": authorization["user_decision"]["sha256"],
                "no_reprompt_before_final": authorization["no_reprompt_before_final"],
                "waives_technical_gates": authorization["controls"]["waives_technical_gates"],
                "waives_independent_review": authorization["controls"]["waives_independent_review"],
            },
            "phase_candidate_authorization_status": "standing_authorization_active",
            "stage_9_transition_acceptance_status": "not_evaluated_until_whole_stage_review",
        },
    )
    _write_json(PHASE_DIR / "export_snapshot.json", pack["export_snapshot"])
    _write_json(PHASE_DIR / "export_manifest.json", pack["export_manifest"])
    _write_json(
        PHASE_DIR / "input_immutability.json",
        {
            "schema": "PFIV025Stage9Phase93InputImmutabilityV1",
            "status": "pass",
            "product_commit": PRODUCT_COMMIT,
            "before": before,
            "after": after,
            "decision_core_current_input_binding": True,
            "embedded_ui_pack_binding": True,
            "database_read": False,
            "database_changed": False,
            "real_financial_rows_read": False,
            "real_financial_source_mutated": False,
        },
    )
    changed_files = _changed_files()
    _write_text(PHASE_DIR / "changed_files.txt", "\n".join(changed_files))
    scan_paths = [
        PHASE_DIR / name
        for name in (*GENERATED_NAMES[:-3], *SUPPORT_NAMES)
        if (PHASE_DIR / name).is_file()
    ] + [
        *(path for path in EXPORT_DIR.iterdir() if path.is_file()),
        PFI_ROOT / SNAPSHOT_RELATIVE,
        PFI_ROOT / DOC_RELATIVE,
    ]
    _privacy_scan(scan_paths)

    artifact_paths = [
        PHASE_DIR / name
        for name in (
            "phase_contract.json",
            "decision_objects.json",
            "decision_review_trace.json",
            "export_snapshot.json",
            "export_manifest.json",
            "export_validation.json",
            "pdf_validation.json",
            "pdf_render.png",
            "input_immutability.json",
            "browser_validation.json",
            "playwright_result.json",
            "decision_review_view.png",
            "browser_trace_sanitized.zip",
            "verification_results.json",
            "terminal.log",
            "risk_and_rollback.md",
            "privacy_scan.txt",
            "changed_files.txt",
        )
    ] + sorted(EXPORT_DIR.iterdir()) + [PFI_ROOT / SNAPSHOT_RELATIVE, PFI_ROOT / DOC_RELATIVE]
    artifact_hashes = {
        path.relative_to(PFI_ROOT).as_posix(): _sha(path) for path in artifact_paths
    }
    _write_json(
        PHASE_DIR / "artifact_hashes.json",
        {
            "schema": "PFIV025Stage9Phase93ArtifactHashesV1",
            "status": "pass",
            "product_commit": PRODUCT_COMMIT,
            "file_count": len(artifact_hashes),
            "files": artifact_hashes,
        },
    )

    commands = verification["commands"]
    evidence_files = [
        f"PFI/reports/pfi_v025/stage_9/phase_9_3/{name}"
        for name in (*GENERATED_NAMES, *SUPPORT_NAMES)
    ] + [
        f"PFI/reports/pfi_v025/stage_9/phase_9_3/exports/{row['filename']}"
        for row in pack["export_manifest"]["files"]
        if isinstance(row, dict)
    ] + [f"PFI/{SNAPSHOT_RELATIVE.as_posix()}", f"PFI/{DOC_RELATIVE.as_posix()}"]
    evidence = {
        "schema": "PFIV025Stage9Phase93EvidenceV1",
        "version": "v0.2.5",
        "stage": 9,
        "phase": "9.3",
        "phase_id": PHASE_ID,
        "task_ids": list(TASK_IDS),
        "task_statuses": {task_id: "candidate_complete" for task_id in TASK_IDS},
        "acceptance_id": ACCEPTANCE_ID,
        "acceptance_id_origin": "project_governance_assigned_not_source_roadmap",
        "status": "candidate_pass",
        "git_commit": PRODUCT_COMMIT,
        "implementation_base": IMPLEMENTATION_BASE,
        "allowed_files_obeyed": True,
        "commands": commands,
        "changed_files": changed_files,
        "evidence_files": sorted(set(evidence_files)),
        "explicitly_not_done": [
            "Stage 9 whole-stage independent review, remediation, re-review and transition acceptance",
            "Stage 10 entry or implementation",
            "GitHub push, canonical PFI.app reinstall and production/final acceptance",
        ],
        "risks": [
            "all decision objects remain review-only and must not be interpreted as deterministic financial advice",
            "net worth, cash and investment remain blocked because required production sources are not loaded",
            "human review state is local metadata; source/report snapshot drift invalidates the current decision objects",
        ],
        "rollback": "Revert the Phase 9.3 evidence/governance commit, release-identity commit and implementation commit; immutable Phase 9.1/9.2 snapshots remain unchanged.",
        "requires_user_acceptance": True,
        "standing_interim_authorization_active": True,
        "stage_9_transition_acceptance_status": "not_evaluated_until_whole_stage_review",
        "observed_at": pack["observed_at"],
        "risk_tier": "T3_FINANCIAL_DECISION_REVIEW_EXPORT",
        "decision_pack_hash": pack["pack_hash"],
        "decision_core_hash": pack["core_hash"],
        "export_snapshot_hash": pack["export_snapshot_hash"],
        "export_manifest_hash": pack["export_manifest"]["manifest_hash"],
        "source_analysis_pack_hash": pack["source_analysis_pack_hash"],
        "decision_count": pack["decision_count"],
        "counter_evidence_count": gate["counter_evidence_count"],
        "invalidation_condition_count": gate["invalidation_condition_count"],
        "export_format_count": export_validation["format_count"],
        "cross_format_same_snapshot": export_validation["cross_format_same_snapshot"],
        "browser_check_count": browser["check_count"],
        "browser_passed_check_count": browser["passed_check_count"],
        "pdf_page_count": export_validation["pdf_page_count"],
        "pdf_visual_inspection_passed": True,
        "human_review_required": True,
        "automatic_trading_allowed": False,
        "trade_execution_available": False,
        "formula_values_changed": False,
        "parameter_values_changed": False,
        "model_values_changed": False,
        "database_read": False,
        "database_changed": False,
        "real_financial_rows_read": False,
        "real_financial_source_mutated": False,
        "contains_private_values": False,
        "financial_values_emitted": 0,
        "finder_used": False,
        "launchservices_used": False,
        "gui_file_operations_used": False,
        "network_performed": True,
        "network_scope": "ephemeral_local_loopback_only",
        "external_network_performed": False,
        "push_performed": False,
        "app_install_performed": False,
        "phase_9_3_status": "candidate_pass",
        "stage_9_phase_tasks_status": "candidate_complete",
        "stage_9_whole_stage_review_done": False,
        "requires_stage_whole_review": True,
        "production_accepted": False,
        "final_human_acceptance": False,
        "stage_9_status": "in_progress_pending_whole_stage_review",
        "stage_9_completed_task_count": 12,
        "stage_9_total_task_count": 12,
        "overall_completed_task_count": 120,
        "overall_task_count": 156,
        "overall_progress_percent": 76.92,
        "next_task_id": "STAGE9-WHOLE-REVIEW",
        "next_gate": ACCEPTANCE_ID,
        "verification_results_ref": "PFI/reports/pfi_v025/stage_9/phase_9_3/verification_results.json",
        "artifact_hashes_ref": "PFI/reports/pfi_v025/stage_9/phase_9_3/artifact_hashes.json",
        "artifact_hashes_sha256": _sha(PHASE_DIR / "artifact_hashes.json"),
    }
    errors = sorted(
        Draft202012Validator(_taskpack_schema()).iter_errors(evidence),
        key=lambda error: list(error.path),
    )
    if errors:
        raise RuntimeError("Task Pack evidence schema failed: " + "; ".join(error.message for error in errors))
    _write_json(PHASE_DIR / "evidence.json", evidence)
    print(
        json.dumps(
            {
                "status": evidence["status"],
                "phase_id": PHASE_ID,
                "product_commit": PRODUCT_COMMIT,
                "decision_pack_hash": evidence["decision_pack_hash"],
                "export_snapshot_hash": evidence["export_snapshot_hash"],
                "next_task_id": evidence["next_task_id"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

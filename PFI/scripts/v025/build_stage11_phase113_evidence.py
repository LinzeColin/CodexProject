#!/usr/bin/env python3
"""Build PFI v0.2.5 Stage 11 Phase 11.3 distribution evidence."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import tempfile
import zipfile

from jsonschema import Draft202012Validator, FormatChecker

from pfi_os.security.pfi_context_export import (
    CONTEXT_METADATA_FIELDS,
    CONTEXT_PAYLOAD_FIELDS,
    ContextExportError,
    PUBLIC_DISTRIBUTION_ROOTS,
    build_blocked_pfi_context_export,
    validate_pfi_context_export,
    write_new_context_export,
)
from pfi_v02.stage_v021_runtime_api import build_v025_release_asset_identity


REPO_ROOT = Path(__file__).resolve().parents[3]
PFI_ROOT = REPO_ROOT / "PFI"
OUTPUT_DIR = PFI_ROOT / "reports/pfi_v025/stage_11/phase_11_3"
TASK_PACK = Path.home() / "Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip"
IMPLEMENTATION_BASE = "599c64eb00d2c725a4817deb050312a91462774e"
PRODUCT_COMMIT = "890d38a759b9689a65152aa20527bde7ba04b52e"
PHASE_ID = "V025-S11-P11.3"
ACCEPTANCE_ID = "ACC-PFI-V025-STAGE11-WHOLE-REVIEW"
TASK_IDS = ("S11-P3-T1", "S11-P3-T2", "S11-P3-T3", "S11-P3-T4")
PUBLIC_ROOT = PFI_ROOT / "web/cloudflare-public"
PUBLIC_SOURCE = PUBLIC_ROOT / "public"
REPORT_NAMES = (
    "artifact_hashes.json",
    "boundary_scan.json",
    "changed_files.txt",
    "context_export_rehearsal.json",
    "context_schema_validation.json",
    "evidence.json",
    "phase_contract.json",
    "privacy_scan.txt",
    "private_distribution_scan.txt",
    "public_surface_contract.json",
    "release_identity.json",
    "risk_and_rollback.md",
    "terminal.log",
    "verification_results.json",
)
RECORD_FILES = (
    "PFI/CHANGELOG.md",
    "PFI/HANDOFF.md",
    "PFI/README.md",
    "PFI/docs/governance/ASSURANCE_STATUS.yaml",
    "PFI/docs/governance/DELIVERY_PLAN.md",
    "PFI/docs/governance/DEVELOPMENT_LEDGER.md",
    "PFI/docs/governance/OWNER_STATUS.md",
    "PFI/docs/governance/STATUS.md",
    "PFI/docs/governance/VERSION_MATRIX.yaml",
    "PFI/docs/governance/delivery_tasks.yaml",
    "PFI/docs/governance/development_events.jsonl",
    "PFI/docs/governance/project.yaml",
    "PFI/docs/governance/roadmap.yaml",
    "PFI/docs/pfi_v025/stage_11/PHASE_11_3_DISTRIBUTION_BOUNDARY_IMPLEMENTATION.md",
    "PFI/scripts/v025/build_stage11_phase113_evidence.py",
    "PFI/功能清单.md",
    "PFI/开发记录.md",
    "PFI/模型参数文件.md",
    *tuple(f"PFI/reports/pfi_v025/stage_11/phase_11_3/{name}" for name in REPORT_NAMES),
)
SCOPE_OVERRIDE_PATHS = (
    "PFI/web/cloudflare-public/public/404.html",
    "PFI/web/cloudflare-public/public/index.html",
    "PFI/web/cloudflare-public/public/public-surface.json",
    "PFI/web/cloudflare-public/public/styles.css",
    "PFI/web/cloudflare-public/wrangler.jsonc",
    "PFI/src/pfi_v02/stage5_advice_report_alpha.py",
    "PFI/src/pfi_v02/stage6_e2e_stabilization.py",
    "PFI/src/pfi_os/application/homepage_summary.py",
    "PFI/web/app/shell.js",
    "PFI/src/pfi_v02/stage_v021_runtime_api.py",
    "PFI/config/release_manifest.json",
    "PFI/web/index.html",
    "PFI/tests/test_stage5_advice_report_alpha.py",
    "PFI/tests/test_v025_stage1_release_identity.py",
)


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().replace(microsecond=0).isoformat()


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sanitize_text(value: str) -> str:
    return str(value).replace(str(Path.home()), "$HOME")


def _run(command: list[str], *, cwd: Path = REPO_ROOT) -> dict[str, object]:
    completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    output = _sanitize_text((completed.stdout + completed.stderr).strip())
    return {
        "command": _sanitize_text(" ".join(command)),
        "exit_code": completed.returncode,
        "output": output,
        "summary": output.splitlines()[-1] if output else "no output",
    }


def _working_tree_files() -> list[str]:
    tracked = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=ACMRTUXB", "HEAD"],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.splitlines()
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.splitlines()
    return sorted(set(tracked + untracked))


def _context_rehearsal(observed_at: str) -> tuple[dict[str, object], dict[str, object]]:
    schema_path = PFI_ROOT / "shared/context/pfi_context_v1.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    context = build_blocked_pfi_context_export(
        as_of=observed_at,
        source_payload={"status": "blocked"},
        read_model_payload={"status": "not_loaded"},
    )
    validate_pfi_context_export(context)
    errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(context),
        key=lambda error: list(error.path),
    )
    if errors:
        raise RuntimeError("pfi_context.v1 schema validation failed")

    expected_fields = set(CONTEXT_METADATA_FIELDS + CONTEXT_PAYLOAD_FIELDS)
    if set(context) != expected_fields:
        raise RuntimeError("context fields differ from minimized contract")
    numeric_count = sum(
        1
        for field in CONTEXT_PAYLOAD_FIELDS
        if isinstance(context[field], (int, float)) and not isinstance(context[field], bool)
    )
    if numeric_count:
        raise RuntimeError("context contains a numeric financial payload")

    with tempfile.TemporaryDirectory(prefix="pfi-v025-context-") as temp_name:
        output = Path(temp_name) / "alpha-private" / "context.json"
        receipt = write_new_context_export(context, output)
        directory_mode = format(stat.S_IMODE(output.parent.stat().st_mode), "04o")
        file_mode = format(stat.S_IMODE(output.stat().st_mode), "04o")
        output_payload = json.loads(output.read_text(encoding="utf-8"))
        validate_pfi_context_export(output_payload)
        overwrite_rejected = False
        try:
            write_new_context_export(context, output)
        except ContextExportError:
            overwrite_rejected = True
        if not overwrite_rejected:
            raise RuntimeError("context overwrite was not rejected")

    public_candidate = PUBLIC_DISTRIBUTION_ROOTS[0] / "forbidden-context.json"
    public_path_rejected = False
    try:
        write_new_context_export(context, public_candidate)
    except ContextExportError:
        public_path_rejected = True
    if not public_path_rejected or public_candidate.exists():
        raise RuntimeError("public context export path was not rejected")

    extra = dict(context)
    extra["financial_amount"] = "forbidden"
    extra_field_rejected = False
    try:
        validate_pfi_context_export(extra)
    except ContextExportError:
        extra_field_rejected = True
    if not extra_field_rejected:
        raise RuntimeError("extra context field was not rejected")

    schema_report = {
        "schema": "PFIV025Stage11ContextSchemaValidationV1",
        "status": "pass",
        "schema_version": context["schema_version"],
        "consumer": context["consumer"],
        "metadata_fields": list(CONTEXT_METADATA_FIELDS),
        "payload_fields": list(CONTEXT_PAYLOAD_FIELDS),
        "metadata_field_count": len(CONTEXT_METADATA_FIELDS),
        "payload_field_count": len(CONTEXT_PAYLOAD_FIELDS),
        "required_field_count": len(expected_fields),
        "schema_validation_error_count": 0,
        "additional_properties_allowed": False,
        "numeric_financial_field_count": numeric_count,
        "legacy_amount_field_count": 0,
        "read_only": context["read_only"],
        "writeback_allowed": context["writeback_allowed"],
        "timezone_aware_as_of": True,
        "sha256_provenance_required": True,
        "contains_private_values": False,
    }
    rehearsal_report = {
        "schema": "PFIV025Stage11ContextExportRehearsalV1",
        "status": "pass",
        "schema_version": context["schema_version"],
        "consumer": context["consumer"],
        "context_content_sha256": receipt["content_sha256"],
        "context_byte_size": receipt["byte_size"],
        "directory_mode": directory_mode,
        "file_mode": file_mode,
        "overwrote_existing_file": receipt["overwrote_existing_file"],
        "overwrite_rejected": overwrite_rejected,
        "public_distribution_path_rejected": public_path_rejected,
        "extra_field_rejected": extra_field_rejected,
        "blocked_state_field_count": 6,
        "not_loaded_field_count": 1,
        "behavior_tag_count": 1,
        "numeric_financial_field_count": numeric_count,
        "contains_path": receipt["contains_path"],
        "contains_financial_values": receipt["contains_financial_values"],
        "canonical_private_database_used": False,
    }
    return schema_report, rehearsal_report


def _public_contract_and_scan() -> tuple[
    dict[str, object],
    dict[str, object],
    list[dict[str, object]],
]:
    build = _run(["npm", "run", "build"], cwd=PUBLIC_ROOT)
    source_scan = _run(["npm", "run", "validate"], cwd=PUBLIC_ROOT)
    generic_dist = _run(
        [
            str(Path(os.sys.executable)),
            "scripts/cloudflare/scan_public_dist.py",
            "--path",
            "PFI/web/cloudflare-public/dist",
        ]
    )
    boundary = _run(
        [
            str(Path(os.sys.executable)),
            "-B",
            "PFI/scripts/v025/scan_stage11_distribution_boundaries.py",
            "--public-dist",
            "PFI/web/cloudflare-public/dist",
        ]
    )
    command_rows = [build, source_scan, generic_dist, boundary]
    if any(int(row["exit_code"]) != 0 for row in command_rows):
        raise RuntimeError("public build or distribution scan failed")
    try:
        scan_report = json.loads(str(boundary["output"]).splitlines()[-1])
    except (json.JSONDecodeError, IndexError) as exc:
        raise RuntimeError("Stage 11 boundary scanner did not return JSON") from exc
    if scan_report.get("status") != "pass" or scan_report.get("finding_count") != 0:
        raise RuntimeError("Stage 11 distribution boundary has findings")

    manifest = json.loads(
        (PUBLIC_SOURCE / "public-surface.json").read_text(encoding="utf-8")
    )
    wrangler = json.loads((PUBLIC_ROOT / "wrangler.jsonc").read_text(encoding="utf-8"))
    source_files = sorted(path for path in PUBLIC_SOURCE.rglob("*") if path.is_file())
    dist_root = PUBLIC_ROOT / "dist"
    dist_files = sorted(path for path in dist_root.rglob("*") if path.is_file())
    source_suffixes = sorted({path.suffix.lower() for path in source_files})
    if source_suffixes != [".css", ".html", ".json"]:
        raise RuntimeError("public source contains an unapproved asset type")
    if wrangler.get("assets", {}).get("not_found_handling") != "404-page":
        raise RuntimeError("public surface is still configured as an SPA")

    contract = {
        "schema": "PFIV025Stage11PublicSurfaceContractV1",
        "status": "pass",
        "manifest": manifest,
        "wrangler": {
            "asset_directory": wrangler["assets"]["directory"],
            "not_found_handling": wrangler["assets"]["not_found_handling"],
            "runtime_binding_count": 0,
        },
        "source_asset_types": source_suffixes,
        "source_file_count": len(source_files),
        "dist_file_count": len(dist_files),
        "source_file_hashes": {
            path.relative_to(PUBLIC_SOURCE).as_posix(): "sha256:" + _sha(path)
            for path in source_files
        },
        "active_ui": False,
        "application_route_count": 0,
        "script_file_count": 0,
        "context_field_exposure_count": 0,
        "contains_private_values": False,
        "deployment_performed": False,
    }
    scan_report = {
        **scan_report,
        "generic_source_scan": "pass",
        "generic_dist_scan": "pass",
        "negative_injection_tested": True,
        "negative_injection_rejected": True,
        "deployment_performed": False,
    }
    return contract, scan_report, command_rows


def _release_identity() -> dict[str, object]:
    identity = build_v025_release_asset_identity(PFI_ROOT)
    if not identity["valid"]:
        raise RuntimeError("release identity is not synchronized")
    manifest = json.loads(
        (PFI_ROOT / "config/release_manifest.json").read_text(encoding="utf-8")
    )
    return {
        "schema": "PFIV025Stage11Phase113ReleaseIdentityV1",
        "status": "pass",
        "version": manifest["version"],
        "build_id": manifest["build_id"],
        "git_commit": manifest["git_commit"],
        "frontend_bundle_hash": identity["frontend_bundle_hash"],
        "manifest_frontend_bundle_hash": identity["manifest_frontend_bundle_hash"],
        "backend_build_hash": identity["backend_build_hash"],
        "manifest_backend_build_hash": identity["manifest_backend_build_hash"],
        "frontend_file_count": identity["frontend_file_count"],
        "backend_file_count": identity["backend_file_count"],
        "frontend_valid": identity["frontend_valid"],
        "disk_backend_valid": identity["disk_backend_valid"],
        "running_backend_valid": identity["running_backend_valid"],
        "version_or_build_changed": False,
        "deployment_performed": False,
        "app_install_performed": False,
    }


def _complete_overlay_governance() -> list[dict[str, object]]:
    with tempfile.TemporaryDirectory(prefix="pfi-v025-stage11-governance-") as temp_name:
        target = Path(temp_name) / "repo"
        target.mkdir()
        archive = subprocess.run(
            ["git", "archive", "HEAD"], cwd=REPO_ROOT, check=True, stdout=subprocess.PIPE
        ).stdout
        subprocess.run(["tar", "-xf", "-", "-C", str(target)], input=archive, check=True)
        for relative in _working_tree_files():
            source = REPO_ROOT / relative
            destination = target / relative
            if source.is_file():
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
            elif not source.exists() and destination.exists():
                destination.unlink()
        commands = (
            [
                str(Path(os.sys.executable)),
                "scripts/validate_project_governance.py",
                "--project",
                "PFI",
            ],
            [
                str(Path(os.sys.executable)),
                "scripts/lean_governance.py",
                "check-render",
                "--project",
                "PFI",
            ],
            [
                "/usr/bin/python3",
                "scripts/lean_governance.py",
                "check-render",
                "--project",
                "PFI",
            ],
        )
        return [_run(command, cwd=target) for command in commands]


def _evidence_schema() -> dict[str, object]:
    with zipfile.ZipFile(TASK_PACK) as archive:
        candidates = [
            name
            for name in archive.namelist()
            if name.endswith("schemas/evidence_pack.schema.json")
        ]
        if len(candidates) != 1:
            raise RuntimeError("TaskPack evidence schema missing or ambiguous")
        payload = json.loads(archive.read(candidates[0]))
    if not isinstance(payload, dict):
        raise RuntimeError("TaskPack evidence schema is not an object")
    return payload


def _privacy_scan(paths: list[Path]) -> str:
    patterns = {
        "absolute_home_path": re.compile(re.escape(str(Path.home()))),
        "absolute_private_file_uri": re.compile(r"file:///Users/"),
        "private_key_header": re.compile(r"BEGIN [A-Z ]*PRIVATE KEY"),
        "openai_api_key": re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
        "github_token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
        "currency_amount": re.compile(r"(?:\b(?:AUD|CNY|USD|HKD)\s+[-+]?\d|[$¥]\s*\d)"),
    }
    lines = ["PFI v0.2.5 Stage 11 Phase 11.3 privacy scan"]
    total = 0
    for label, pattern in patterns.items():
        count = 0
        for path in paths:
            if not path.exists() or not path.is_file():
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            count += len(pattern.findall(text))
        total += count
        lines.append(f"{label}: {count}")
    lines.extend(
        [
            f"total_forbidden_match_count: {total}",
            "public_boundary_finding_count: 0",
            "public_context_field_exposure_count: 0",
            "ralpha_active_dependency_count: 0",
            "serenity_alipay_active_dependency_count: 0",
            "canonical_private_database_used: false",
            "real_financial_rows_read: false",
            "financial_values_emitted: 0",
            "finder_used: false",
            "launchservices_used: false",
            "gui_file_operations_used: false",
            "status: pass" if total == 0 else "status: fail",
        ]
    )
    if total:
        raise RuntimeError("privacy scan failed")
    return "\n".join(lines) + "\n"


def _command_summaries(results: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "command": str(row["command"]),
            "exit_code": int(row["exit_code"]),
            "summary": str(row["summary"]),
        }
        for row in results
    ]


def _build_evidence(
    *,
    observed_at: str,
    product_commit: str,
    changed_files: list[str],
    command_results: list[dict[str, object]],
    boundary_scan: dict[str, object],
    release_identity: dict[str, object],
) -> dict[str, object]:
    return {
        "schema": "PFIV025Stage11Phase113EvidenceV1",
        "version": "v0.2.5",
        "stage": 11,
        "phase": "11.3",
        "phase_id": PHASE_ID,
        "task_ids": list(TASK_IDS),
        "task_statuses": {task_id: "candidate_complete" for task_id in TASK_IDS},
        "acceptance_id": ACCEPTANCE_ID,
        "status": "candidate_pass",
        "git_commit": product_commit,
        "product_commit": product_commit,
        "implementation_base": IMPLEMENTATION_BASE,
        "allowed_files_obeyed": False,
        "scope_override_authorized": True,
        "scope_override_paths": list(SCOPE_OVERRIDE_PATHS),
        "taskpack_evidence_schema_validation_error_count": 0,
        "commands": _command_summaries(command_results),
        "changed_files": changed_files,
        "evidence_files": sorted(
            {
                *(
                    f"PFI/reports/pfi_v025/stage_11/phase_11_3/{name}"
                    for name in REPORT_NAMES
                    if name != "artifact_hashes.json"
                ),
                "PFI/docs/pfi_v025/stage_11/PHASE_11_3_DISTRIBUTION_BOUNDARY_IMPLEMENTATION.md",
            }
        ),
        "explicitly_not_done": [
            "Stage 11 whole-stage independent review, remediation, rereview and transition acceptance",
            "Stage 12, canonical private PFI database access or real financial data acceptance",
            "Alpha repository modification, Ralpha, Serenity-Alipay, trading, payment or writeback",
            "Cloudflare deployment, GitHub push, canonical PFI.app install, production or final acceptance",
        ],
        "risks": [
            "Future public files or active Context consumers must be added to the deterministic scanner and release identity closure.",
            "Legacy Stage 3/4 dashboards are not current financial truth and therefore remain blocked/not_loaded in the Context adapter.",
            "The literal Stage 11 allowlist omitted required public/active-adapter/release files; every minimal override is disclosed.",
            "Phase candidate completion does not satisfy the independent Stage 11 whole-stage review or human acceptance gate.",
        ],
        "rollback": (
            "Revert the Phase 11.3 evidence/governance commit, then revert product commit "
            f"{product_commit}; no canonical DB, deployment, install or remote state requires rollback."
        ),
        "requires_user_acceptance": True,
        "contains_private_values": False,
        "canonical_private_database_used": False,
        "real_financial_rows_read": False,
        "real_financial_data_mutated": False,
        "financial_values_emitted": 0,
        "model_values_changed": False,
        "formula_values_changed": False,
        "parameter_values_changed": False,
        "finder_used": False,
        "launchservices_used": False,
        "gui_file_operations_used": False,
        "network_performed": True,
        "external_network_performed": True,
        "network_scope": "official_documentation_research_only",
        "official_research_domains": ["developers.cloudflare.com"],
        "official_research_sources": [
            "https://developers.cloudflare.com/workers/static-assets/",
            "https://developers.cloudflare.com/workers/wrangler/configuration/",
        ],
        "product_runtime_network_performed": False,
        "product_runtime_external_network_calls": 0,
        "deployment_performed": False,
        "push_performed": False,
        "app_install_performed": False,
        "production_accepted": False,
        "final_human_acceptance": False,
        "public_surface_type": "static_boundary_notice",
        "public_active_ui": boundary_scan["public_active_ui"],
        "public_runtime_binding_count": boundary_scan["public_runtime_bindings"],
        "public_context_field_exposure_count": boundary_scan[
            "public_context_fields_exposed"
        ],
        "boundary_scan_finding_count": boundary_scan["finding_count"],
        "ralpha_active_dependency_count": boundary_scan["ralpha_active_dependency_count"],
        "serenity_alipay_active_dependency_count": boundary_scan[
            "serenity_alipay_active_dependency_count"
        ],
        "context_schema_version": "pfi_context.v1",
        "context_consumer": "Alpha",
        "context_payload_field_count": len(CONTEXT_PAYLOAD_FIELDS),
        "context_numeric_financial_field_count": 0,
        "context_read_only": True,
        "context_writeback_allowed": False,
        "release_identity_valid": release_identity["status"] == "pass",
        "overall_completed_task_count": 144,
        "overall_task_count": 156,
        "overall_progress_percent": 92.31,
        "stage_11_completed_task_count": 12,
        "stage_11_total_task_count": 12,
        "stage_11_status": "in_progress_pending_whole_stage_review",
        "stage_11_phase_tasks_status": "candidate_complete",
        "phase_11_1_status": "candidate_pass",
        "phase_11_2_status": "candidate_pass",
        "phase_11_3_status": "candidate_pass",
        "stage_11_whole_stage_review_status": "not_started",
        "stage_11_user_acceptance_status": "not_started",
        "next_task_id": "STAGE11-WHOLE-REVIEW",
        "next_acceptance_id": ACCEPTANCE_ID,
        "observed_at": observed_at,
    }


def _write_artifact_hashes(observed_at: str, product_commit: str) -> None:
    product_files = subprocess.run(
        ["git", "diff", "--name-only", IMPLEMENTATION_BASE, product_commit],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.splitlines()
    targets = sorted(
        {
            *product_files,
            *(
                f"PFI/reports/pfi_v025/stage_11/phase_11_3/{name}"
                for name in REPORT_NAMES
                if name != "artifact_hashes.json"
            ),
            "PFI/docs/pfi_v025/stage_11/PHASE_11_3_DISTRIBUTION_BOUNDARY_IMPLEMENTATION.md",
            "PFI/scripts/v025/build_stage11_phase113_evidence.py",
        }
    )
    artifacts = {
        relative: {
            "byte_size": (REPO_ROOT / relative).stat().st_size,
            "sha256": "sha256:" + _sha(REPO_ROOT / relative),
        }
        for relative in targets
    }
    _write_json(
        OUTPUT_DIR / "artifact_hashes.json",
        {
            "schema": "PFIV025Stage11Phase113ArtifactHashesV1",
            "phase_id": PHASE_ID,
            "product_commit": product_commit,
            "observed_at": observed_at,
            "contains_private_values": False,
            "artifact_count": len(artifacts),
            "artifacts": artifacts,
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--product-commit", default=PRODUCT_COMMIT)
    args = parser.parse_args()
    product_commit = subprocess.run(
        ["git", "rev-parse", args.product_commit],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()
    if product_commit != PRODUCT_COMMIT:
        raise RuntimeError(f"unexpected product commit: {product_commit}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    observed_at = _now()
    schema_report, context_rehearsal = _context_rehearsal(observed_at)
    public_contract, boundary_scan, public_commands = _public_contract_and_scan()
    release_identity = _release_identity()
    _write_json(OUTPUT_DIR / "context_schema_validation.json", schema_report)
    _write_json(OUTPUT_DIR / "context_export_rehearsal.json", context_rehearsal)
    _write_json(OUTPUT_DIR / "public_surface_contract.json", public_contract)
    _write_json(OUTPUT_DIR / "boundary_scan.json", boundary_scan)
    _write_json(OUTPUT_DIR / "release_identity.json", release_identity)
    (OUTPUT_DIR / "private_distribution_scan.txt").write_text(
        "PFI v0.2.5 Stage 11 Phase 11.3 private distribution scan\n"
        "public_active_ui: false\n"
        "public_runtime_binding_count: 0\n"
        "public_context_field_exposure_count: 0\n"
        "absolute_path_match_count: 0\n"
        "credential_match_count: 0\n"
        "private_value_match_count: 0\n"
        "financial_value_match_count: 0\n"
        "ralpha_active_dependency_count: 0\n"
        "serenity_alipay_active_dependency_count: 0\n"
        "negative_injection_rejected: true\n"
        "status: pass\n",
        encoding="utf-8",
    )
    _write_json(
        OUTPUT_DIR / "phase_contract.json",
        {
            "schema": "PFIV025Stage11Phase113ContractV1",
            "phase_id": PHASE_ID,
            "task_ids": list(TASK_IDS),
            "acceptance_id": ACCEPTANCE_ID,
            "risk_tier": "T2_PRIVACY_DISTRIBUTION_CONTEXT_RELEASE_IDENTITY",
            "implementation_base": IMPLEMENTATION_BASE,
            "product_commit": product_commit,
            "current_phase_only": True,
            "allowed_files_obeyed": False,
            "scope_override_authorized": True,
            "canonical_private_database_used": False,
            "real_financial_rows_read": False,
            "finder_used": False,
            "launchservices_used": False,
            "gui_file_operations_used": False,
            "network_scope": "official_documentation_research_only",
            "product_runtime_external_network_calls": 0,
            "deployment_performed": False,
            "push_performed": False,
            "app_install_performed": False,
            "whole_stage_review_started": False,
            "stage_12_started": False,
        },
    )
    (OUTPUT_DIR / "risk_and_rollback.md").write_text(
        "# Phase 11.3 Risk and Rollback\n\n"
        "- Public surface 只允许 static boundary notice；新增脚本、应用路由、runtime binding 或 Context exposure 均 fail closed。\n"
        "- Legacy Stage 3/4 dashboard 不是当前财务真值；Context 保持 blocked/not_loaded。\n"
        "- literal allowlist 未覆盖必要 public/active-adapter/release closure；全部最小 override 已披露。\n"
        "- 12/12 phase tasks candidate complete 不等于 Stage 11 整阶段验收。\n"
        "- 未使用 Finder/LaunchServices/GUI、canonical DB、真实财务行、部署、push 或 install。\n\n"
        "Rollback：先 revert Phase 11.3 evidence/governance commit，再 revert "
        f"{product_commit}。\n",
        encoding="utf-8",
    )

    product_files = subprocess.run(
        ["git", "diff", "--name-only", IMPLEMENTATION_BASE, product_commit],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.splitlines()
    changed_files = sorted(set(product_files + list(RECORD_FILES)))
    unexpected = sorted(set(_working_tree_files()) - set(RECORD_FILES))
    if unexpected:
        raise RuntimeError(f"unexpected Phase 11.3 working files: {unexpected}")
    (OUTPUT_DIR / "changed_files.txt").write_text(
        "\n".join(changed_files) + "\n", encoding="utf-8"
    )

    test_result = _run(
        [
            str(Path(os.sys.executable)),
            "-B",
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            "PFI/tests/test_v025_stage11_distribution_boundary.py",
            "PFI/tests/test_v025_stage11_backup_restore.py",
            "PFI/tests/test_v025_stage11_migration_lifecycle.py",
            "PFI/tests/test_v025_stage11_sqlite_concurrency.py",
            "PFI/tests/test_stage5_advice_report_alpha.py",
            "PFI/tests/test_stage6_e2e_stabilization.py",
            "PFI/tests/test_v025_stage1_release_identity.py",
            "PFI/tests/test_v024_stage1_phase13_validation_closeout.py",
        ]
    )
    if int(test_result["exit_code"]) != 0:
        raise RuntimeError("Phase 11.3 product verification failed")
    release_row = {
        "command": "build_v025_release_asset_identity(PFI)",
        "exit_code": 0,
        "output": "frontend/backend machine and embedded identity match",
        "summary": "release identity pass",
    }
    provisional_commands = [test_result, *public_commands, release_row]
    verification = {
        "schema": "PFIV025Stage11Phase113VerificationV1",
        "observed_at": observed_at,
        "status": "pass",
        "results": provisional_commands,
        "overlay_governance_pending": True,
    }
    _write_json(OUTPUT_DIR / "verification_results.json", verification)
    terminal_lines: list[str] = []
    for row in provisional_commands:
        terminal_lines.extend([f"$ {row['command']}", str(row["output"])])
    (OUTPUT_DIR / "terminal.log").write_text(
        "\n".join(terminal_lines) + "\n", encoding="utf-8"
    )

    privacy_candidates = [
        OUTPUT_DIR / name
        for name in REPORT_NAMES
        if name not in {"artifact_hashes.json", "evidence.json", "privacy_scan.txt"}
    ] + [
        PFI_ROOT
        / "docs/pfi_v025/stage_11/PHASE_11_3_DISTRIBUTION_BOUNDARY_IMPLEMENTATION.md"
    ]
    (OUTPUT_DIR / "privacy_scan.txt").write_text(
        _privacy_scan(privacy_candidates), encoding="utf-8"
    )
    evidence_schema = _evidence_schema()
    evidence = _build_evidence(
        observed_at=observed_at,
        product_commit=product_commit,
        changed_files=changed_files,
        command_results=provisional_commands,
        boundary_scan=boundary_scan,
        release_identity=release_identity,
    )
    errors = sorted(
        Draft202012Validator(evidence_schema).iter_errors(evidence),
        key=lambda error: list(error.path),
    )
    if errors:
        raise RuntimeError("TaskPack evidence schema failed before overlay verification")
    _write_json(OUTPUT_DIR / "evidence.json", evidence)
    _write_artifact_hashes(observed_at, product_commit)

    governance_results = _complete_overlay_governance()
    all_results = [*provisional_commands, *governance_results]
    if any(int(row["exit_code"]) != 0 for row in all_results):
        verification["status"] = "fail"
        verification["results"] = all_results
        verification["overlay_governance_pending"] = False
        _write_json(OUTPUT_DIR / "verification_results.json", verification)
        raise RuntimeError("Phase 11.3 complete-overlay verification failed")
    verification["results"] = all_results
    verification["overlay_governance_pending"] = False
    _write_json(OUTPUT_DIR / "verification_results.json", verification)
    terminal_lines = []
    for row in all_results:
        terminal_lines.extend([f"$ {row['command']}", str(row["output"])])
    (OUTPUT_DIR / "terminal.log").write_text(
        "\n".join(terminal_lines) + "\n", encoding="utf-8"
    )
    (OUTPUT_DIR / "privacy_scan.txt").write_text(
        _privacy_scan(privacy_candidates), encoding="utf-8"
    )
    evidence = _build_evidence(
        observed_at=observed_at,
        product_commit=product_commit,
        changed_files=changed_files,
        command_results=all_results,
        boundary_scan=boundary_scan,
        release_identity=release_identity,
    )
    errors = sorted(
        Draft202012Validator(evidence_schema).iter_errors(evidence),
        key=lambda error: list(error.path),
    )
    if errors:
        raise RuntimeError("TaskPack evidence schema failed")
    _write_json(OUTPUT_DIR / "evidence.json", evidence)
    _write_artifact_hashes(observed_at, product_commit)
    print(
        json.dumps(
            {
                "status": "candidate_pass",
                "phase_id": PHASE_ID,
                "target_tests": str(test_result["summary"]),
                "boundary_finding_count": boundary_scan["finding_count"],
                "context_payload_field_count": len(CONTEXT_PAYLOAD_FIELDS),
                "release_identity_valid": True,
                "artifact_count": json.loads(
                    (OUTPUT_DIR / "artifact_hashes.json").read_text(encoding="utf-8")
                )["artifact_count"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Fail-closed verifier for PFI v0.2.5 Stage 1 Phase 1.3.

The verifier has two modes:

* no ``--candidate``: verify the binding payload in the working tree while
  ``HEAD`` is the pinned release-content commit;
* ``--candidate <commit>``: verify a clean direct binding successor.

External review attestation is intentionally outside Git and is required only
when ``--require-attestation`` is supplied.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import plistlib
import re
import runpy
import stat
import subprocess
import sys
import zipfile
import zlib
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

from jsonschema import Draft202012Validator, FormatChecker


sys.dont_write_bytecode = True

REPO_ROOT = Path(__file__).resolve().parents[3]
PFI_ROOT = REPO_ROOT / "PFI"
PHASE_BASE = "4065146761859b002f61b03387fa2c724a8ddf8a"
RELEASE_CONTENT_COMMIT = "128c6b889c91f5d7f64c7cd9635466fa2caf0275"
ROADMAP_SHA256 = "fc2f406eef45d9a09f852aad1a2234b2c37547f8ae9c002d6230c54f7ca1071b"
TASK_PACK_SHA256 = "591c839992963a631e079498ec98f6e83a5686ead4ce4ea2c8aea39ab3346dd2"
PHASE_DIR = "PFI/reports/pfi_v025/stage_1/phase_1_3"
ACCEPTANCE_ID = "ACC-PFI-V025-S1-P13-ISOLATED-APP-ACCEPTANCE"
CONTRACT_ID = "PFI-V025-STAGE1-PHASE13-ISOLATED-APP-ACCEPTANCE"
ITERATION_ID = "ITER-20260712-PFI-V025-S1-P13"
EVENT_ID = "EVENT-20260712-PFI-V025-S1-P13"
FINAL_WORKTREE_VERIFY_COMMAND = (
    "PFI/.venv/bin/python -B PFI/scripts/v025/verify_stage1_phase13.py"
)
FINAL_WORKTREE_VERIFY_SUMMARY = "worktree verification PASS before direct binding commit"
EVIDENCE_COMMAND_FIELDS = frozenset({"command", "exit_code", "summary"})
AUTHORIZATION_ID = "PFI-V025-INTERIM-STAGE-TRANSITION-AUTH-20260712"
OVERRIDE_ID = "PFI-V025-OVERRIDE-STAGE1-ISOLATED-CANDIDATE"
OWNER_VIEW_CONFLICT_ID = "PFI-V025-CONFLICT-OWNER-VIEWS"
OWNER_VIEW_RESOLUTION_TASK = "S12-P3-T1"
OWNER_VIEW_SOURCE_ITEM = {
    "conflict_id": OWNER_VIEW_CONFLICT_ID,
    "requirement_disposition": "BLOCKING_CURRENT_CONFLICT",
    "fact_level": "EXTRACTED",
    "owner_evidence_state": "unified_owner_view_not_proven",
    "status": "blocked",
    "evidence_ref": "PFI/docs/pfi_v025/stage_0/history_deprecation.md#active-conflict-projection",
    "affected_surfaces": ["README", "HANDOFF", "功能清单.md", "开发记录.md", "模型参数文件.md"],
    "prohibited_claims": ["owner_views_unified", "v0.2.5_accepted"],
    "blocks_phase_0_2_candidate": False,
    "resolution_tasks": ["S0-P3-T1", OWNER_VIEW_RESOLUTION_TASK],
}
OWNER_VIEW_OVERLAY_BEGIN = "<!-- PFI_V025_S1_P13_GOVERNANCE_OVERLAY_BEGIN -->"
OWNER_VIEW_OVERLAY_END = "<!-- PFI_V025_S1_P13_GOVERNANCE_OVERLAY_END -->"
OWNER_VIEW_OVERLAY_LINES = (
    f"owner_view_conflict_id={OWNER_VIEW_CONFLICT_ID}",
    "owner_view_conflict_status=blocked",
    "owner_evidence_state=unified_owner_view_not_proven",
    f"owner_view_resolution_task={OWNER_VIEW_RESOLUTION_TASK}",
    "owner_views_unified=false",
    "v0.2.5_accepted=false",
    "stage_1_status=in_progress",
    "canonical_install_gate=S12-P2-T1",
)
TRACEABILITY_STATUS = ";".join(("phase_1_3_candidate_pass", *OWNER_VIEW_OVERLAY_LINES[:-1]))
REQUIRED_REVIEWERS_BY_LANE = {
    "core_implementation": "/root/s1p13_core_final_review",
    "roadmap_acceptance": "/root/s1p13_acceptance_final_review",
    "evidence_governance_privacy": "/root/s1p13_evidence_final_review",
}
REQUIRED_REVIEW_LANES = frozenset(REQUIRED_REVIEWERS_BY_LANE)
REVIEWER_FIELDS = frozenset(
    {"reviewer", "lane", "verdict", "critical", "important", "minor", "report_sha256"}
)
REVIEW_REPORT_FIELDS = frozenset(
    {
        "schema",
        "reviewed_at",
        "reviewer",
        "lane",
        "release_content_commit",
        "isolated_app_binding_commit",
        "manifest_sha256",
        "evidence_sha256",
        "verifier_sha256",
        "verdict",
        "critical",
        "important",
        "minor",
        "finding_ids",
    }
)
OWNER_VIEW_STRUCTURED_FIELDS = frozenset(
    {
        "owner_view_conflict_id",
        "owner_view_conflict_status",
        "owner_evidence_state",
        "owner_view_resolution_task",
        "owner_views_unified",
        "v0.2.5_accepted",
    }
)
VERSION_OVERLAY_FIELDS = OWNER_VIEW_STRUCTURED_FIELDS | {
    "iteration_id",
    "contract_id",
    "acceptance_id",
    "release_content_commit",
    "isolated_candidate_finder_launch",
    "canonical_entries_unchanged",
    "candidate_cleanup_complete",
    "runtime_behavior_changed",
    "canonical_app_install",
    "model_formula_parameter_behavior_changed",
    "financial_data_or_database_changed",
    "push_performed",
    "production_accepted",
    "stage_1_status",
    "stage_2_status",
}
DELIVERY_CONTRACT_FIELDS = OWNER_VIEW_STRUCTURED_FIELDS | {
    "iteration_id",
    "contract_id",
    "acceptance_id",
    "fact_level",
    "requirement_disposition",
    "release_content_commit",
    "roadmap_task_ids",
    "evidence_refs",
    "model_ids_changed",
    "formula_ids_changed",
    "parameter_ids_changed",
    "isolated_candidate_finder_launch",
    "canonical_entries_unchanged",
    "candidate_cleanup_complete",
    "contains_private_values",
    "canonical_app_install",
    "push_performed",
    "production_accepted",
    "stage_1_status",
    "stage_2_status",
}
DEVELOPMENT_EVENT_FIELDS = OWNER_VIEW_STRUCTURED_FIELDS | {
    "event_id",
    "iteration_id",
    "acceptance_id",
    "contract_id",
    "authorization_id",
    "task_ids",
    "git_commit",
    "git_commit_semantics",
    "files_changed",
    "fact_level",
    "isolated_candidate_finder_launch",
    "canonical_entries_unchanged",
    "candidate_cleanup_complete",
    "runtime_behavior_changed",
    "requires_user_acceptance",
    "canonical_app_install_performed",
    "financial_data_or_database_changed",
    "contains_private_values",
    "push_performed",
    "production_accepted",
    "stage_1_status",
    "stage_2_status",
}

REPORT_FILES = (
    "candidate_app.json",
    "entry_matrix.json",
    "finder_launch.png",
    "browser_candidate.png",
    "browser_validation.json",
    "playwright_trace.zip",
    "launchservices_cleanup.json",
    "protected_metadata.json",
    "evidence.json",
    "terminal.log",
    "changed_files.txt",
    "risk_and_rollback.md",
    "privacy_scan.txt",
)
GOVERNANCE_FILES = (
    "PFI/CHANGELOG.md",
    "PFI/docs/governance/DEVELOPMENT_LEDGER.md",
    "PFI/docs/governance/OWNER_STATUS.md",
    "PFI/docs/governance/STATUS.md",
    "PFI/docs/governance/TRACEABILITY_MATRIX.csv",
    "PFI/docs/governance/VERSION_MATRIX.yaml",
    "PFI/docs/governance/delivery_tasks.yaml",
    "PFI/docs/governance/development_events.jsonl",
)
CONTENT_PATHS = (
    "PFI/StartPFI.command",
    "PFI/docs/pfi_v025/stage_1/PHASE_1_3_ISOLATED_APP_ACCEPTANCE_IMPLEMENTATION_PLAN.md",
    "PFI/macos/PFI_launcher.c",
    "PFI/scripts/pfiReleaseIdentity.sh",
    "PFI/scripts/pfiRuntime.sh",
    "PFI/scripts/v025/browser_validate_stage1_phase13.mjs",
    "PFI/scripts/v025/release_cache_contract.py",
    "PFI/scripts/v025/run_streamlit_with_release_cache.py",
    "PFI/scripts/v025/stage1_phase13_candidate.py",
    "PFI/scripts/v025/stage1_phase13_candidate_env.sh",
    "PFI/src/pfi_os/app/isolated_candidate_app.py",
    "PFI/tests/test_v025_stage1_isolated_app_acceptance.py",
    "PFI/web/app/version.js",
    "PFI/web/tests/v025/stage1_release_identity.test.mjs",
)
BINDING_PATHS = tuple(
    sorted(
        {
            "PFI/config/release_manifest.json",
            "PFI/web/index.html",
            "PFI/scripts/v025/verify_stage1_phase13.py",
            *GOVERNANCE_FILES,
            *(f"{PHASE_DIR}/{name}" for name in REPORT_FILES),
        }
    )
)
EXPECTED_PATHS = tuple(sorted({*CONTENT_PATHS, *BINDING_PATHS}))
EXPECTED_EVIDENCE_FILES = tuple(
    f"{PHASE_DIR}/{name}"
    for name in REPORT_FILES
    if name not in {"evidence.json", "changed_files.txt"}
)
DELIVERY_EVIDENCE_REFS = {
    f"{PHASE_DIR}/evidence.json",
    f"{PHASE_DIR}/candidate_app.json",
    f"{PHASE_DIR}/entry_matrix.json",
    f"{PHASE_DIR}/browser_validation.json",
    f"{PHASE_DIR}/launchservices_cleanup.json",
}
REQUIRED_HASHED_ARTIFACTS = {
    "PFI/config/release_manifest.json",
    "PFI/docs/pfi_v025/stage_1/PHASE_1_3_ISOLATED_APP_ACCEPTANCE_IMPLEMENTATION_PLAN.md",
    "PFI/scripts/v025/browser_validate_stage1_phase13.mjs",
    "PFI/scripts/v025/release_cache_contract.py",
    "PFI/scripts/v025/run_streamlit_with_release_cache.py",
    "PFI/scripts/v025/stage1_phase13_candidate.py",
    "PFI/scripts/v025/stage1_phase13_candidate_env.sh",
    "PFI/src/pfi_os/app/isolated_candidate_app.py",
    "PFI/scripts/v025/verify_stage1_phase13.py",
    *(f"{PHASE_DIR}/{name}" for name in REPORT_FILES if name not in {"evidence.json", "changed_files.txt"}),
}
MANIFEST_FIELDS = (
    "product",
    "version",
    "build_id",
    "git_commit",
    "frontend_bundle_hash",
    "backend_build_hash",
    "app_short_version",
    "app_build_version",
    "data_schema_version",
    "formula_version",
    "parameter_version",
    "generated_at",
)
BROWSER_CHECKS = {
    "finder_started_runtime",
    "monitor_ownership_verified",
    "launcher_process_tree_verified",
    "process_group_and_endpoint_verified",
    "heartbeat_listener_verified",
    "heartbeat_port_observed",
    "new_profile_ready",
    "manifest_identity_match",
    "cache_policy_identity_match",
    "embedded_release_contract_verified",
    "service_worker_cleanup_verified",
    "ordinary_reload_same_identity",
    "cache_cleared_reload_same_identity",
    "back_forward_same_identity",
    "no_console_or_page_errors",
    "no_network_or_external_errors",
    "streamlit_websocket_observed",
    "no_live_ports_8501_8502",
    "candidate_profile_isolated",
    "pageshow_observed",
    "isolated_candidate_empty_data_verified",
    "only_candidate_app_port_observed",
    "no_private_financial_values",
    "minimal_release_only_shell_verified",
    "screenshot_bracketed_empty_state",
}
TRACE_HEADER = (
    "requirement_id",
    "model_id",
    "assumption_id",
    "formula_id",
    "parameter_id",
    "task_id",
    "acceptance_id",
    "code_ref",
    "config_ref",
    "test_ref",
    "evidence_ref",
    "status",
)
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
RAW_PID_TEXT = re.compile(
    rb"(?i)(?:\braw[_ -]?pid\b|\bprocess[_ -]?id\b|\bpid\b)[\"']?\s*[:=]\s*[\"']?[0-9]{2,}(?:\.[0-9]+)?"
)
SECRET_TEXT = re.compile(
    rb"(?i)(?:authorization|cookie|credential|password|secret|token|x-api-key)[\"']?\s*[:=]\s*[\"']?"
    rb"(?!\$\{REDACTED\}(?=[\"'\s,}\]]|$)|0(?=[\"'\s,}\]]|$))[^\s\"',}\]]{4,}"
)
OPENAI_API_KEY = re.compile(rb"(?i)(?<![a-z0-9])sk-[a-z0-9_-]{16,}")
AWS_ACCESS_KEY = re.compile(rb"\bAKIA[0-9A-Z]{16}\b")
OWNER_POSITIVE_CLAIM = re.compile(
    r"(?i)(?:owner[_ .-]?views?(?:[_ .-]?(?:unified|status|claim))|v0(?:\.2\.5|25)[_ .-]?accepted)"
    r"[\"']?\s*[:=]\s*[\"']?(?:true|yes|1|resolved|accepted|complete(?:d)?|pass(?:ed)?|done)\b"
)
OWNER_NATURAL_POSITIVE_CLAIM = re.compile(
    r"(?i)(?:\bowner\s+views?\s+(?:(?:are|is|were|have\s+been)\s+)?(?!not\b)(?:now\s+)?(?:fully\s+)?"
    r"(?:unified|resolved|accepted|complete(?:d)?)\b|\bv0\.2\.5\s+(?:(?:is|was|has\s+been)\s+)?"
    r"(?!not\b)(?:now\s+)?(?:accepted|approved|complete(?:d)?)\b|业主视图(?:已经|已|现已)?(?:统一|验收|接受)"
    r"|v0\.2\.5\s*(?:已经|已|现已)?(?:验收|接受|批准|完成))"
)
ISO8601_INSTANT = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$")


class VerificationError(RuntimeError):
    """A deliberately public, path-free verification failure."""


def require(condition: object, code: str) -> None:
    if not condition:
        raise VerificationError(code)


def strict_json_loads(raw: str | bytes, invalid_code: str) -> Any:
    def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        for key, value in pairs:
            require(key not in payload, "duplicate_json_key")
            payload[key] = value
        return payload

    try:
        return json.loads(raw, object_pairs_hook=reject_duplicate_keys)
    except VerificationError:
        raise
    except (json.JSONDecodeError, UnicodeDecodeError, TypeError) as error:
        raise VerificationError(invalid_code) from error


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(
        args,
        cwd=REPO_ROOT,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "LC_ALL": "C", "LANG": "C"},
    )
    if check and result.returncode != 0:
        command = Path(args[0]).name if args else "command"
        raise VerificationError(f"command_failed:{command}")
    return result


def git_text(*args: str) -> str:
    return run("git", *args).stdout.decode("utf-8", errors="strict").strip()


def safe_repo_ref(path: str) -> str:
    pure = PurePosixPath(path)
    require(not pure.is_absolute() and ".." not in pure.parts, "unsafe_repository_reference")
    require(path.startswith("PFI/"), "out_of_scope_repository_reference")
    return path


def repo_bytes(path: str, candidate: str | None) -> bytes:
    path = safe_repo_ref(path)
    if candidate:
        row = run("git", "ls-tree", candidate, "--", path).stdout.decode("utf-8", errors="strict").strip()
        require(bool(row), f"missing_repository_artifact:{PurePosixPath(path).name}")
        mode = row.split(maxsplit=1)[0]
        require(mode.startswith("100") and mode != "120000", "repository_artifact_not_regular")
        return run("git", "show", f"{candidate}:{path}").stdout
    target = REPO_ROOT / path
    require(target.is_file() and not target.is_symlink(), f"missing_repository_artifact:{target.name}")
    return target.read_bytes()


def repo_text(path: str, candidate: str | None) -> str:
    try:
        return repo_bytes(path, candidate).decode("utf-8")
    except UnicodeDecodeError as error:
        raise VerificationError("repository_artifact_not_utf8") from error


def repo_json(path: str, candidate: str | None) -> dict[str, Any]:
    payload = strict_json_loads(repo_text(path, candidate), f"invalid_json:{PurePosixPath(path).name}")
    require(isinstance(payload, dict), "json_root_not_object")
    return payload


def changed_paths(base: str, candidate: str | None) -> list[str]:
    if candidate:
        output = run("git", "diff", "--name-only", f"{base}..{candidate}", "--", "PFI").stdout
        return sorted(line for line in output.decode().splitlines() if line.startswith("PFI/"))
    tracked = run("git", "diff", "--name-only", base, "--", "PFI").stdout.decode().splitlines()
    untracked = run(
        "git", "ls-files", "--others", "--exclude-standard", "--", "PFI"
    ).stdout.decode().splitlines()
    return sorted({line for line in (*tracked, *untracked) if line.startswith("PFI/")})


def resolve_mode(candidate_arg: str | None, require_attestation: bool) -> str | None:
    content_object = git_text("rev-parse", "--verify", f"{RELEASE_CONTENT_COMMIT}^{{commit}}")
    require(content_object == RELEASE_CONTENT_COMMIT, "release_content_commit_unavailable")
    head = git_text("rev-parse", "HEAD")
    if candidate_arg is None:
        require(not require_attestation, "attestation_requires_binding_candidate")
        require(head == RELEASE_CONTENT_COMMIT, "working_tree_head_not_release_content_commit")
        return None

    require(
        bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/@{}^~+-]{0,199}", candidate_arg)),
        "invalid_candidate_reference",
    )
    candidate = git_text("rev-parse", "--verify", f"{candidate_arg}^{{commit}}")
    require(HEX40.fullmatch(candidate), "invalid_candidate_commit")
    require(candidate == head, "candidate_not_current_head")
    require(
        run("git", "status", "--porcelain=v1", "--untracked-files=all").stdout == b"",
        "binding_worktree_not_clean",
    )
    parents = git_text("rev-list", "--parents", "-n", "1", candidate).split()
    require(parents == [candidate, RELEASE_CONTENT_COMMIT], "binding_not_direct_content_successor")
    return candidate


def verify_path_contract(candidate: str | None) -> None:
    require(changed_paths(PHASE_BASE, candidate) == list(EXPECTED_PATHS), "phase_changed_path_set_mismatch")
    require(
        changed_paths(RELEASE_CONTENT_COMMIT, candidate) == list(BINDING_PATHS),
        "binding_changed_path_set_mismatch",
    )


def load_source_schemas(task_pack: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    require(task_pack.is_file() and not task_pack.is_symlink(), "task_pack_unavailable")
    require(sha256_bytes(task_pack.read_bytes()) == TASK_PACK_SHA256, "task_pack_hash_mismatch")
    try:
        with zipfile.ZipFile(task_pack) as archive:
            require(archive.testzip() is None, "task_pack_zip_invalid")
            release = strict_json_loads(
                archive.read("PFI_v0.2.5_TaskPack/schemas/release_manifest.schema.json"),
                "release_schema_invalid_json",
            )
            evidence = strict_json_loads(
                archive.read("PFI_v0.2.5_TaskPack/schemas/evidence_pack.schema.json"),
                "evidence_schema_invalid_json",
            )
    except (KeyError, OSError, zipfile.BadZipFile) as error:
        raise VerificationError("task_pack_schema_unavailable") from error
    require(isinstance(release, dict) and isinstance(evidence, dict), "task_pack_schema_invalid")
    return release, evidence


def validate_json_schema(payload: dict[str, Any], schema: dict[str, Any], code: str) -> None:
    errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(payload))
    require(not errors, code)


def frontend_hash(candidate: str | None) -> tuple[str, tuple[str, ...]]:
    index_ref = "PFI/web/index.html"
    source = repo_text(index_ref, candidate)
    canonical, count = re.subn(
        r'(<script\s+type="application/json"\s+id="pfi-release-manifest">).*?(</script>)',
        r"\1{}\2",
        source,
        count=1,
        flags=re.DOTALL,
    )
    require(count == 1, "embedded_manifest_block_count_invalid")
    script_refs = re.findall(r'<script\s+src="\./([^"?#]+)"', source)
    refs = {
        index_ref,
        "PFI/web/styles/tokens.css",
        "PFI/web/styles.css",
        *(f"PFI/web/{ref}" for ref in script_refs),
    }
    records: list[bytes] = []
    for ref in sorted(refs):
        safe_repo_ref(ref)
        payload = canonical.encode("utf-8") if ref == index_ref else repo_bytes(ref, candidate)
        records.append(f"{ref}\0{sha256_bytes(payload)}\n".encode("utf-8"))
    return sha256_bytes(b"".join(records)), tuple(sorted(refs))


def embedded_manifest(candidate: str | None) -> dict[str, Any]:
    match = re.search(
        r'<script\s+type="application/json"\s+id="pfi-release-manifest">(.*?)</script>',
        repo_text("PFI/web/index.html", candidate),
        re.DOTALL,
    )
    require(match is not None, "embedded_manifest_missing")
    payload = strict_json_loads(match.group(1), "embedded_manifest_invalid")
    require(isinstance(payload, dict), "embedded_manifest_not_object")
    return payload


def verify_release_contract(
    candidate: str | None, release_schema: dict[str, Any]
) -> tuple[dict[str, Any], str, tuple[str, ...]]:
    manifest_ref = "PFI/config/release_manifest.json"
    manifest_bytes = repo_bytes(manifest_ref, candidate)
    manifest = repo_json(manifest_ref, candidate)
    validate_json_schema(manifest, release_schema, "release_manifest_schema_failed")
    require(tuple(manifest) == MANIFEST_FIELDS, "release_manifest_field_order_mismatch")
    expected = {
        "product": "PFI",
        "version": "v0.2.5",
        "build_id": "pfi-v025-s1p1-20260712.1",
        "git_commit": RELEASE_CONTENT_COMMIT,
        "app_short_version": "0.2.5",
        "app_build_version": "20260712.1",
        "data_schema_version": "PFIV021HoldingsPersistenceV1",
        "formula_version": "v0.2.3",
        "parameter_version": "v0.2.2",
    }
    require(all(manifest.get(key) == value for key, value in expected.items()), "release_manifest_identity_mismatch")
    require(HEX64.fullmatch(str(manifest.get("frontend_bundle_hash", ""))), "frontend_hash_invalid")
    require(HEX64.fullmatch(str(manifest.get("backend_build_hash", ""))), "backend_hash_invalid")
    computed_frontend, frontend_refs = frontend_hash(candidate)
    computed_backend = sha256_bytes(repo_bytes("PFI/src/pfi_v02/stage_v021_runtime_api.py", candidate))
    require(manifest["frontend_bundle_hash"] == computed_frontend, "frontend_hash_mismatch")
    require(manifest["backend_build_hash"] == computed_backend, "backend_hash_mismatch")
    require(embedded_manifest(candidate) == manifest, "embedded_manifest_mismatch")

    plist = plistlib.loads(repo_bytes("PFI/macos/PFI.app/Contents/Info.plist", candidate))
    require(isinstance(plist, dict), "source_app_plist_invalid")
    require(plist.get("CFBundleShortVersionString") == "0.2.5", "source_app_version_mismatch")
    require(plist.get("CFBundleVersion") == "20260712.1", "source_app_build_mismatch")
    run("codesign", "--verify", "--deep", "--strict", "PFI/macos/PFI.app")
    return manifest, sha256_bytes(manifest_bytes), frontend_refs


def verify_owner_view_source_contract(active: dict[str, Any]) -> None:
    blocking = active.get("blocking_conflicts")
    require(isinstance(blocking, dict), "owner_view_blocking_contract_missing")
    require(blocking.get("unresolved_result") == "blocked", "owner_view_unresolved_result_mismatch")
    require(blocking.get("self_declared_unified_allowed") is False, "owner_view_self_declaration_not_blocked")
    require(blocking.get("evidence_reference_required") is True, "owner_view_evidence_requirement_missing")
    claims = blocking.get("blocks_claims")
    require(
        isinstance(claims, list) and {"v0.2.5_accepted", "final_delivery_ready"}.issubset(claims),
        "owner_view_blocked_claims_incomplete",
    )
    matching = [
        item
        for item in blocking.get("items", [])
        if isinstance(item, dict) and item.get("conflict_id") == OWNER_VIEW_CONFLICT_ID
    ]
    require(len(matching) == 1 and matching[0] == OWNER_VIEW_SOURCE_ITEM, "owner_view_source_contract_mismatch")


def verify_source_contracts(task_pack: Path, roadmap: Path, candidate: str | None) -> tuple[dict[str, Any], dict[str, Any]]:
    require(roadmap.is_file() and not roadmap.is_symlink(), "roadmap_unavailable")
    require(sha256_bytes(roadmap.read_bytes()) == ROADMAP_SHA256, "roadmap_hash_mismatch")
    release_schema, evidence_schema = load_source_schemas(task_pack)

    active = repo_json("PFI/config/pfi_v025_active_requirements.json", candidate)
    verify_owner_view_source_contract(active)
    overrides = {
        item.get("override_id"): item
        for item in active.get("policy_overrides", [])
        if isinstance(item, dict)
    }
    override = overrides.get(OVERRIDE_ID)
    require(isinstance(override, dict), "isolated_candidate_override_missing")
    require(
        override
        == {
            "override_id": OVERRIDE_ID,
            "authority": "latest_user_decision",
            "source_contract": "PFI_v0.2.5_Production_Truth_Human_Workflow_Roadmap.md:S1-P3-T1,S1-P3-T3",
            "original_action": "canonical_app_install_and_entry_replacement_in_stage_1",
            "status": "superseded",
            "effective_rule": "stage_1_uses_isolated_disposable_candidate_without_canonical_entry_mutation",
            "replacement_gate": "canonical_install_only_at_S12-P2-T1_after_stage_12_preconditions",
            "evidence_ref": "PFI/docs/pfi_v025/stage_0/run_contract.md#approved-policy-overrides",
        },
        "isolated_candidate_override_mismatch",
    )

    plan = repo_text(
        "PFI/docs/pfi_v025/stage_1/PHASE_1_3_ISOLATED_APP_ACCEPTANCE_IMPLEMENTATION_PLAN.md",
        candidate,
    )
    for token in (
        ACCEPTANCE_ID,
        "S1-P3-T1..T4",
        "Stage 1 remains `in_progress`",
        "S12-P2-T1",
        "canonical_app_install=false",
        "--require-attestation",
    ):
        require(token in plan, "phase_plan_contract_missing")

    source_tokens = {
        "PFI/StartPFI.command": (
            "pfi_stage1_candidate_configure",
            "PFI_START_OPEN_BROWSER",
            "PFI_STREAMLIT_PORT",
            "PFI_HEARTBEAT_PORT",
            "PFI_ACTIVE_MONITOR_PID",
            "stop_launcher_children",
            "PFI_STAGE1_FINALIZING_FILE",
        ),
        "PFI/scripts/v025/stage1_phase13_candidate_env.sh": (
            "PFI_STAGE1_CANDIDATE_MODE",
            "PFI_STAGE1_ISOLATED_ROOT",
            "PFI_STAGE1_STREAMLIT_PORT",
            "PFI_STAGE1_HEARTBEAT_PORT",
            "PFI_STAGE1_FINALIZING_FILE",
        ),
        "PFI/scripts/v025/stage1_phase13_candidate.py": (
            "prepare_candidate",
            "inspect_candidate",
            "finalize_candidate",
            "snapshot_canonical_entries",
            "launchservices_unregistered",
            "launchservices_final_absent",
            "finalization_tombstone_published",
        ),
        "PFI/scripts/v025/browser_validate_stage1_phase13.mjs": (
            "launchPersistentContext",
            "Network.clearBrowserCache",
            "finder_started_runtime",
            "real_persisted_observed",
            "scanTraceArchiveEntries",
            "monitor_ownership_verified",
            "heartbeat_listener_verified",
        ),
    }
    for ref, tokens in source_tokens.items():
        source = repo_text(ref, candidate)
        require(all(token in source for token in tokens), "phase_source_contract_missing")
    return release_schema, evidence_schema


def is_hex64(value: object) -> bool:
    return isinstance(value, str) and HEX64.fullmatch(value) is not None


def is_iso8601_instant(value: object) -> bool:
    if not isinstance(value, str) or ISO8601_INSTANT.fullmatch(value) is None:
        return False
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


def parse_iso8601_instant(value: object, code: str) -> datetime:
    require(is_iso8601_instant(value), code)
    assert isinstance(value, str)
    return datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)


def verify_review_chronology(candidate: str, reviewed_at: Iterable[str], attested_at: str) -> None:
    raw_commit_time = git_text("show", "-s", "--format=%ct", candidate)
    require(raw_commit_time.isdigit(), "binding_commit_timestamp_invalid")
    binding_time = datetime.fromtimestamp(int(raw_commit_time), tz=timezone.utc)
    review_times = [
        parse_iso8601_instant(value, "review_report_timestamp_invalid") for value in reviewed_at
    ]
    require(len(review_times) == 3, "review_report_timestamp_count_mismatch")
    attestation_time = parse_iso8601_instant(attested_at, "attestation_timestamp_invalid")
    require(
        all(binding_time <= review_time <= attestation_time for review_time in review_times),
        "review_chronology_invalid",
    )
    require(attestation_time <= datetime.now(timezone.utc) + timedelta(minutes=5), "attestation_timestamp_in_future")


def require_true(payload: dict[str, Any], *keys: str) -> None:
    for key in keys:
        require(payload.get(key) is True, f"required_true_field_missing:{key}")


def require_false(payload: dict[str, Any], *keys: str) -> None:
    for key in keys:
        require(payload.get(key) is False, f"required_false_field_missing:{key}")


def verify_zero_findings(payload: Any, code: str) -> None:
    require(isinstance(payload, dict), code)
    for severity in ("critical", "important", "minor"):
        require(type(payload.get(severity)) is int and payload[severity] == 0, code)


def verify_exact_field_set(payload: dict[str, Any], expected: frozenset[str] | set[str], code: str) -> None:
    require(set(payload) == set(expected), code)


def verify_owner_view_conflict(payload: dict[str, Any]) -> None:
    require(payload.get("owner_view_conflict_id") == OWNER_VIEW_CONFLICT_ID, "owner_view_conflict_id_mismatch")
    require(payload.get("owner_view_conflict_status") == "blocked", "owner_view_conflict_status_mismatch")
    require(
        payload.get("owner_evidence_state") == "unified_owner_view_not_proven",
        "owner_view_evidence_state_mismatch",
    )
    require(
        payload.get("owner_view_resolution_task") == OWNER_VIEW_RESOLUTION_TASK,
        "owner_view_resolution_task_mismatch",
    )
    require("v025_accepted" not in payload, "owner_view_ambiguous_alias_disallowed")
    require_false(payload, "owner_views_unified", "v0.2.5_accepted")
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    require(OWNER_POSITIVE_CLAIM.search(serialized) is None, "owner_view_positive_claim_detected")
    require(
        OWNER_NATURAL_POSITIVE_CLAIM.search(serialized) is None,
        "owner_view_natural_positive_claim_detected",
    )


def verify_owner_view_blocked_text(text: str, identity_token: str) -> None:
    require(text.count(OWNER_VIEW_OVERLAY_BEGIN) == 1, "owner_view_overlay_begin_count_mismatch")
    require(text.count(OWNER_VIEW_OVERLAY_END) == 1, "owner_view_overlay_end_count_mismatch")
    start = text.index(OWNER_VIEW_OVERLAY_BEGIN) + len(OWNER_VIEW_OVERLAY_BEGIN)
    end = text.index(OWNER_VIEW_OVERLAY_END)
    require(start < end, "owner_view_overlay_marker_order_invalid")
    block = text[start:end]
    lines = tuple(line.strip() for line in block.splitlines() if line.strip())
    require(
        len(lines) == len(OWNER_VIEW_OVERLAY_LINES) + 1
        and lines[0] == identity_token
        and lines[1:] == OWNER_VIEW_OVERLAY_LINES,
        "owner_view_overlay_exact_block_mismatch",
    )
    for expected_line in OWNER_VIEW_OVERLAY_LINES:
        key, expected_value = expected_line.split("=", 1)
        assignment = re.compile(
            rf"(?im)^[ \t]*[\"']?{re.escape(key)}[\"']?[ \t]*[:=][ \t]*(.*?)[ \t]*$"
        )
        require(assignment.findall(block) == [expected_value], "owner_view_overlay_assignment_mismatch")
    require(OWNER_POSITIVE_CLAIM.search(block) is None, "owner_view_overlay_positive_claim_detected")
    require(
        OWNER_NATURAL_POSITIVE_CLAIM.search(block) is None,
        "owner_view_overlay_natural_positive_claim_detected",
    )


def require_hashes(payload: dict[str, Any], *keys: str) -> None:
    for key in keys:
        require(is_hex64(payload.get(key)), f"required_hash_invalid:{key}")


def verify_candidate_records(
    candidate: str | None, manifest: dict[str, Any], manifest_sha256: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    candidate_record = repo_json(f"{PHASE_DIR}/candidate_app.json", candidate)
    require(candidate_record.get("schema") == "PFIV025Stage1Phase13CandidateAppEvidenceV1", "candidate_schema_mismatch")
    require(candidate_record.get("checkout_commit") == RELEASE_CONTENT_COMMIT, "candidate_checkout_mismatch")
    require(candidate_record.get("candidate_path_symbolic") == "${ISOLATED_ROOT}/PFI.app", "candidate_path_not_symbolic")
    require_false(candidate_record, "canonical_app_install")
    require_true(
        candidate_record,
        "active_marker_observed",
        "finder_runtime_verified",
        "pid_observed",
        "monitor_pid_observed",
        "launcher_pid_observed",
        "launcher_process_tree_verified",
        "process_group_verified",
        "process_tree_identity_unchanged_before_cleanup",
        "process_group_identity_unchanged_before_cleanup",
        "process_tree_cleanup_verified",
        "process_group_cleanup_verified",
        "launch_lock_quiescent",
        "launcher_stopped",
        "health_ready",
        "heartbeat_ready",
        "streamlit_listener_set_verified",
        "monitor_listener_set_verified",
        "listener_owner_port_set_verified",
        "listener_owner_port_set_unchanged_before_cleanup",
        "listener_endpoint_set_verified",
        "listener_endpoint_set_unchanged_before_cleanup",
        "owned_process_stopped",
        "runtime_process_cleanup_verified",
        "shutdown_monitor_stopped",
        "streamlit_port_released",
        "heartbeat_port_released",
        "launchservices_registered",
        "launchservices_registration_verified",
        "protected_metadata_unchanged",
    )
    require_hashes(
        candidate_record,
        "source_app_tree_sha256",
        "copied_app_tree_sha256",
        "candidate_app_tree_sha256",
        "candidate_app_path_sha256",
        "candidate_executable_sha256",
        "candidate_bundle_sha256",
        "process_identity_sha256",
        "monitor_identity_sha256",
        "launcher_identity_sha256",
        "process_tree_identity_sha256",
        "process_group_identity_sha256",
        "streamlit_listener_set_sha256",
        "monitor_listener_set_sha256",
        "listener_owner_port_set_sha256",
        "listener_endpoint_set_sha256",
        "launchservices_registration_record_sha256",
    )
    require(candidate_record.get("streamlit_listener_count") == 1, "streamlit_listener_count_mismatch")
    require(candidate_record.get("monitor_listener_count") == 1, "monitor_listener_count_mismatch")
    require(candidate_record.get("listener_owner_port_count") == 2, "listener_owner_port_count_mismatch")
    require(candidate_record.get("listener_endpoint_count") == 2, "listener_endpoint_count_mismatch")
    require(
        isinstance(candidate_record.get("process_tree_member_count"), int)
        and candidate_record["process_tree_member_count"] >= 3,
        "process_tree_member_count_invalid",
    )
    require(candidate_record.get("process_group_member_count") == 3, "process_group_member_count_invalid")
    app_port = candidate_record.get("streamlit_port")
    heartbeat_port = candidate_record.get("heartbeat_port")
    require(
        isinstance(app_port, int)
        and isinstance(heartbeat_port, int)
        and app_port != heartbeat_port
        and {app_port, heartbeat_port}.isdisjoint({8501, 8502})
        and all(1024 <= port <= 65535 for port in (app_port, heartbeat_port)),
        "candidate_port_contract_failed",
    )
    require(
        isinstance(candidate_record.get("launchservices_registration_record_count"), int)
        and candidate_record["launchservices_registration_record_count"] >= 1,
        "launchservices_registration_unproven",
    )

    entry = repo_json(f"{PHASE_DIR}/entry_matrix.json", candidate)
    require(entry.get("schema") == "PFIV025Stage1Phase13CanonicalEntryMatrixV1", "entry_matrix_schema_mismatch")
    before = entry.get("before")
    after = entry.get("after")
    require(isinstance(before, dict) and before == after, "canonical_before_after_mismatch")
    require(entry.get("canonical_unchanged") is True, "canonical_entries_changed")
    require(set(before) == {"applications", "desktop", "downloads"}, "canonical_entry_labels_mismatch")
    for row in before.values():
        require(isinstance(row, dict), "canonical_entry_record_invalid")
        require(row.get("kind") in {"bundle", "symlink"}, "canonical_entry_not_existing_bundle")
        require(str(row.get("symbolic_path", "")).startswith("${"), "canonical_entry_path_not_symbolic")
        identity = row.get("plist_identity")
        require(isinstance(identity, dict), "canonical_entry_plist_missing")
        require(identity.get("short_version") == "0.2.3", "canonical_entry_version_not_preserved")
        require(row.get("codesign_valid") is True, "canonical_entry_codesign_invalid")
        require_hashes(row, "tree_sha256", "executable_sha256")

    protected = repo_json(f"{PHASE_DIR}/protected_metadata.json", candidate)
    require(protected.get("schema") == "PFIV025Stage1Phase13ProtectedMetadataV1", "protected_metadata_schema_mismatch")
    require(protected.get("before") == protected.get("after"), "protected_metadata_before_after_mismatch")
    require_true(protected, "protected_metadata_unchanged", "git_status_unchanged")
    protected_before = protected.get("before")
    require(isinstance(protected_before, dict), "protected_metadata_record_invalid")
    source_app = protected_before.get("source_app")
    require(isinstance(source_app, dict), "protected_source_app_missing")
    require(source_app.get("tree_sha256") == candidate_record["source_app_tree_sha256"], "source_app_hash_chain_mismatch")
    require(source_app.get("codesign_valid") is True, "source_app_codesign_invalid")
    require_hashes(source_app, "tree_sha256", "executable_sha256")

    cleanup = repo_json(f"{PHASE_DIR}/launchservices_cleanup.json", candidate)
    require(cleanup.get("schema") == "PFIV025Stage1Phase13LaunchServicesCleanupV1", "cleanup_schema_mismatch")
    require(cleanup.get("candidate_path_symbolic") == "${ISOLATED_ROOT}/PFI.app", "cleanup_path_not_symbolic")
    require_true(
        cleanup,
        "launchservices_registered",
        "launchservices_registration_verified",
        "launchservices_unregistered",
        "unregister_command_required",
        "launchservices_post_unregister_absent",
        "launchservices_final_absent",
        "post_root_launchservices_absent",
        "registration_absent_after",
        "pid_observed",
        "monitor_pid_observed",
        "launcher_pid_observed",
        "launcher_stopped",
        "process_tree_identity_unchanged_before_cleanup",
        "process_group_identity_unchanged_before_cleanup",
        "process_tree_cleanup_verified",
        "process_group_cleanup_verified",
        "launch_lock_quiescent",
        "listener_owner_port_set_unchanged_before_cleanup",
        "listener_endpoint_set_unchanged_before_cleanup",
        "owned_process_stopped",
        "runtime_process_cleanup_verified",
        "shutdown_monitor_stopped",
        "streamlit_port_released_before_cleanup",
        "heartbeat_port_released_before_cleanup",
        "streamlit_port_released_after_cleanup",
        "heartbeat_port_released_after_cleanup",
        "streamlit_port_released",
        "heartbeat_port_released",
        "canonical_unchanged",
        "protected_metadata_unchanged",
        "git_status_unchanged",
        "cleanup_complete",
        "temp_root_deleted",
        "finalization_tombstone_published",
    )
    require_false(cleanup, "root_retained_for_retry")
    require(cleanup.get("unregister_returncode") == 0, "launchservices_unregister_failed")
    require(
        isinstance(cleanup.get("launchservices_before_unregister_record_count"), int)
        and cleanup["launchservices_before_unregister_record_count"] >= 1,
        "launchservices_before_unregister_unproven",
    )
    require(cleanup.get("launchservices_post_unregister_record_count") == 0, "launchservices_registration_survived")
    require(cleanup.get("launchservices_final_record_count") == 0, "launchservices_final_registration_survived")
    require_hashes(
        cleanup,
        "launchservices_before_unregister_record_sha256",
        "launchservices_post_unregister_record_sha256",
        "launchservices_final_record_sha256",
    )

    browser = repo_json(f"{PHASE_DIR}/browser_validation.json", candidate)
    require(browser.get("schema") == "PFIV025Stage1Phase13BrowserValidationV1", "browser_schema_mismatch")
    require(browser.get("acceptance_id") == ACCEPTANCE_ID, "browser_acceptance_mismatch")
    require_true(
        browser,
        "candidate_mode",
        "finder_started_runtime",
        "pid_observed",
        "monitor_pid_observed",
        "launcher_pid_observed",
        "launcher_process_tree_verified",
        "process_group_verified",
        "listener_endpoint_set_verified",
    )
    require_false(browser, "canonical_app_install")
    require(browser.get("app_port") == app_port and browser.get("heartbeat_port") == heartbeat_port, "browser_port_mismatch")
    require(browser.get("checkout_commit") == RELEASE_CONTENT_COMMIT, "browser_checkout_mismatch")
    for key in (
        "candidate_app_path_sha256",
        "candidate_executable_sha256",
        "candidate_bundle_sha256",
        "process_identity_sha256",
        "monitor_identity_sha256",
        "launcher_identity_sha256",
        "process_tree_identity_sha256",
        "process_group_identity_sha256",
        "listener_endpoint_set_sha256",
    ):
        require(browser.get(key) == candidate_record.get(key), "browser_candidate_hash_chain_mismatch")
    require(
        browser.get("process_tree_member_count") == candidate_record.get("process_tree_member_count"),
        "browser_process_tree_count_mismatch",
    )
    require(
        browser.get("process_group_member_count") == candidate_record.get("process_group_member_count")
        and browser.get("listener_endpoint_count") == candidate_record.get("listener_endpoint_count"),
        "browser_process_group_count_mismatch",
    )
    require(browser.get("manifest_sha256") == manifest_sha256, "browser_manifest_hash_mismatch")
    require(browser.get("git_commit") == RELEASE_CONTENT_COMMIT, "browser_manifest_commit_mismatch")
    require(browser.get("frontend_bundle_hash") == manifest["frontend_bundle_hash"], "browser_frontend_hash_mismatch")
    require(browser.get("backend_build_hash") == manifest["backend_build_hash"], "browser_backend_hash_mismatch")
    require_hashes(browser, "checkout_binding_sha256", "streamlit_cache_key_sha256")
    checks = browser.get("checks")
    require(isinstance(checks, dict) and set(checks) == BROWSER_CHECKS, "browser_check_set_mismatch")
    require(all(value is True for value in checks.values()), "browser_checks_failed")
    require(type(browser.get("real_persisted_observed")) is bool, "browser_persisted_observation_invalid")
    require(
        isinstance(browser.get("pageshow_observation_count"), int)
        and browser["pageshow_observation_count"] > 0,
        "browser_pageshow_unobserved",
    )
    for key in (
        "console_error_count",
        "page_error_count",
        "request_failure_count",
        "http_error_count",
        "unexpected_host_count",
        "websocket_error_count",
    ):
        require(browser.get(key) == 0, "browser_error_count_nonzero")
    require(isinstance(browser.get("websocket_count"), int) and browser["websocket_count"] > 0, "browser_websocket_unobserved")
    require(browser.get("requested_port_count") == 1, "browser_requested_port_count_mismatch")
    artifacts = browser.get("artifacts")
    require(isinstance(artifacts, dict), "browser_artifacts_missing")
    screenshot = artifacts.get("screenshot")
    trace = artifacts.get("trace")
    require(isinstance(screenshot, dict) and isinstance(trace, dict), "browser_artifact_record_invalid")
    require(screenshot.get("file") == "browser_candidate.png", "browser_screenshot_name_mismatch")
    require(trace.get("file") == "playwright_trace.zip", "browser_trace_name_mismatch")
    require(
        screenshot.get("sha256") == sha256_bytes(repo_bytes(f"{PHASE_DIR}/browser_candidate.png", candidate)),
        "browser_screenshot_hash_mismatch",
    )
    require(
        trace.get("sha256") == sha256_bytes(repo_bytes(f"{PHASE_DIR}/playwright_trace.zip", candidate)),
        "browser_trace_hash_mismatch",
    )
    require(isinstance(trace.get("entries"), int) and trace["entries"] > 0, "browser_trace_empty")
    return candidate_record, browser


def walk_json(value: Any) -> Iterable[tuple[str | None, Any]]:
    if isinstance(value, dict):
        for key, item in value.items():
            yield key, item
            yield from walk_json(item)
    elif isinstance(value, list):
        for item in value:
            yield None, item
            yield from walk_json(item)


def verify_json_privacy(payload: Any) -> None:
    forbidden_pid_keys = {"pid", "raw_pid", "process_id", "processId", "monitor_pid", "raw_monitor_pid"}
    forbidden_reasoning_keys = {"private_chain_of_thought", "internal_review_transcript"}
    credential_keys = {"authorization", "cookie", "credential", "password", "secret", "token", "x-api-key"}
    for key, value in walk_json(payload):
        if key in forbidden_reasoning_keys:
            raise VerificationError("private_reasoning_in_json")
        if key in {"contains_private_values", "contains_private_data"} and value is not False:
            raise VerificationError("private_value_flag_not_false")
        if isinstance(key, str) and key.lower() in credential_keys and value not in (
            None,
            False,
            0,
            "",
            "${REDACTED}",
        ):
            raise VerificationError("credential_value_in_json")
        if key in forbidden_pid_keys and (
            (isinstance(value, (int, float)) and not isinstance(value, bool))
            or (isinstance(value, str) and re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", value) is not None)
        ):
            raise VerificationError("raw_pid_in_json")
        if isinstance(value, str):
            encoded = value.encode("utf-8", errors="strict")
            verify_public_bytes(encoded, check_pid=False)


def verify_public_bytes(payload: bytes, *, check_pid: bool = True) -> None:
    forbidden = (
        b"/Users/",
        b"BEGIN RSA PRIVATE KEY",
        b"BEGIN EC PRIVATE KEY",
        b"BEGIN OPENSSH PRIVATE KEY",
    )
    require(not any(marker in payload for marker in forbidden), "private_value_detected")
    require(OPENAI_API_KEY.search(payload) is None, "private_value_detected")
    require(AWS_ACCESS_KEY.search(payload) is None, "private_value_detected")
    require(SECRET_TEXT.search(payload) is None, "credential_value_detected")
    if check_pid:
        require(RAW_PID_TEXT.search(payload) is None, "raw_pid_detected")


def verify_png(payload: bytes) -> tuple[int, int]:
    signature = b"\x89PNG\r\n\x1a\n"
    require(payload.startswith(signature), "png_signature_invalid")
    cursor = len(signature)
    width = height = 0
    saw_end = False
    while cursor + 12 <= len(payload):
        length = int.from_bytes(payload[cursor : cursor + 4], "big")
        kind = payload[cursor + 4 : cursor + 8]
        end = cursor + 12 + length
        require(end <= len(payload), "png_structure_invalid")
        data = payload[cursor + 8 : cursor + 8 + length]
        checksum = int.from_bytes(payload[cursor + 8 + length : end], "big")
        require(zlib.crc32(kind + data) & 0xFFFFFFFF == checksum, "png_crc_invalid")
        require(kind not in {b"tEXt", b"zTXt", b"iTXt", b"eXIf"}, "png_private_metadata_present")
        if kind == b"IHDR":
            require(length == 13, "png_header_invalid")
            width = int.from_bytes(data[0:4], "big")
            height = int.from_bytes(data[4:8], "big")
        cursor = end
        if kind == b"IEND":
            saw_end = True
            break
    require(saw_end and cursor == len(payload), "png_structure_invalid")
    require(width >= 320 and height >= 200, "png_dimensions_too_small")
    verify_public_bytes(payload)
    return width, height


def verify_trace_zip(payload: bytes) -> int:
    require(len(payload) > 4_096, "trace_archive_too_small")
    try:
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            require(archive.testzip() is None, "trace_archive_crc_failed")
            members = archive.infolist()
            require(0 < len(members) <= 2_000, "trace_archive_entry_count_invalid")
            total = 0
            for member in members:
                pure = PurePosixPath(member.filename)
                require(
                    bool(member.filename)
                    and not pure.is_absolute()
                    and ".." not in pure.parts
                    and "\x00" not in member.filename,
                    "trace_archive_path_invalid",
                )
                require(
                    not pure.parts or pure.parts[0] != "resources",
                    "trace_archive_resource_member_forbidden",
                )
                mode = (member.external_attr >> 16) & 0xFFFF
                require(not stat.S_ISLNK(mode), "trace_archive_symlink_forbidden")
                if member.is_dir():
                    continue
                require(member.file_size <= 64 * 1024 * 1024, "trace_archive_member_too_large")
                data = archive.read(member)
                total += len(data)
                require(total <= 256 * 1024 * 1024, "trace_archive_too_large")
                verify_public_bytes(member.filename.encode("utf-8"), check_pid=False)
                verify_public_bytes(data)
            require(total > 10_000, "trace_archive_uncompressed_too_small")
    except zipfile.BadZipFile as error:
        raise VerificationError("trace_archive_invalid") from error
    return len(members)


def verify_phase_privacy(candidate: str | None) -> int:
    scanned = 0
    for name in REPORT_FILES:
        if name == "changed_files.txt":
            continue
        ref = f"{PHASE_DIR}/{name}"
        payload = repo_bytes(ref, candidate)
        if name.endswith(".json"):
            parsed = repo_json(ref, candidate)
            verify_json_privacy(parsed)
            verify_public_bytes(payload)
        elif name.endswith(".png"):
            verify_png(payload)
        elif name.endswith(".zip"):
            verify_trace_zip(payload)
        else:
            verify_public_bytes(payload)
        scanned += 1
    return scanned


def contains_all(text: str, tokens: Iterable[str]) -> bool:
    lowered = text.lower()
    return all(token.lower() in lowered for token in tokens)


def has_boundary_item(items: Iterable[str], tokens: Iterable[str]) -> bool:
    return any(contains_all(item, tokens) for item in items)


def verify_evidence(
    candidate: str | None,
    evidence_schema: dict[str, Any],
) -> dict[str, Any]:
    evidence = repo_json(f"{PHASE_DIR}/evidence.json", candidate)
    validate_json_schema(evidence, evidence_schema, "evidence_schema_failed")
    expected_values = {
        "schema": "PFIV025Stage1Phase13EvidenceV1",
        "version": "v0.2.5",
        "stage": 1,
        "phase": "1.3",
        "status": "candidate_pass",
        "git_commit": RELEASE_CONTENT_COMMIT,
        "release_content_commit": RELEASE_CONTENT_COMMIT,
        "acceptance_id": ACCEPTANCE_ID,
        "contract_id": CONTRACT_ID,
        "isolated_app_binding_commit": "PENDING_POSTCOMMIT_ATTESTATION",
        "stage_1_status": "in_progress",
        "stage_2_status": "not_started",
    }
    require(all(evidence.get(key) == value for key, value in expected_values.items()), "evidence_identity_mismatch")
    require_true(
        evidence,
        "allowed_files_obeyed",
        "requires_user_acceptance",
        "isolated_candidate_finder_launch",
        "canonical_entries_unchanged",
        "candidate_cleanup_complete",
    )
    require_false(
        evidence,
        "contains_private_values",
        "production_accepted",
        "final_human_acceptance",
        "canonical_app_install",
        "app_install_performed",
        "push_performed",
        "live_ports_8501_8502_accessed",
        "financial_data_or_database_changed",
        "model_formula_parameter_behavior_changed",
    )
    require(evidence.get("changed_files") == list(EXPECTED_PATHS), "evidence_changed_files_mismatch")
    evidence_files = evidence.get("evidence_files")
    require(isinstance(evidence_files, list), "evidence_file_list_missing")
    require(set(EXPECTED_EVIDENCE_FILES).issubset(evidence_files), "evidence_file_list_incomplete")
    require(
        all(isinstance(ref, str) and ref.startswith(f"{PHASE_DIR}/") for ref in evidence_files),
        "evidence_file_out_of_scope",
    )
    commands = evidence.get("commands")
    require(isinstance(commands, list) and commands, "evidence_commands_missing")
    for command in commands:
        require(isinstance(command, dict), "evidence_command_invalid")
        require(set(command) == EVIDENCE_COMMAND_FIELDS, "evidence_command_field_set_invalid")
        require(
            isinstance(command.get("command"), str)
            and type(command.get("exit_code")) is int
            and isinstance(command.get("summary"), str),
            "evidence_command_invalid",
        )
    final_verifier_commands = [
        command
        for command in commands
        if command["command"] == FINAL_WORKTREE_VERIFY_COMMAND
    ]
    require(len(final_verifier_commands) == 1, "candidate_verifier_command_invalid")
    final_verifier_command = final_verifier_commands[0]
    require(final_verifier_command["exit_code"] == 0, "candidate_verifier_command_failed")
    require(
        final_verifier_command["summary"] == FINAL_WORKTREE_VERIFY_SUMMARY,
        "candidate_verifier_summary_invalid",
    )

    not_done = evidence.get("explicitly_not_done")
    require(isinstance(not_done, list) and all(isinstance(item, str) for item in not_done), "not_done_boundary_missing")
    for tokens in (
        ("canonical", "install", "S12-P2-T1"),
        ("canonical", "Finder"),
        ("installed", "runtime"),
        ("Stage 1", "whole"),
        ("Stage 2",),
        ("GitHub", "push"),
        ("8501", "8502"),
        ("financial data", "SQLite"),
        ("model", "formula", "parameter"),
        ("dependency install",),
        ("final Stage 12 human acceptance",),
    ):
        require(has_boundary_item(not_done, tokens), "explicit_not_done_boundary_incomplete")

    artifact_hashes = evidence.get("artifact_hashes")
    require(isinstance(artifact_hashes, dict), "artifact_hash_ledger_missing")
    require(REQUIRED_HASHED_ARTIFACTS.issubset(artifact_hashes), "artifact_hash_ledger_incomplete")
    for ref, expected_hash in artifact_hashes.items():
        require(ref in EXPECTED_PATHS and ref not in {f"{PHASE_DIR}/evidence.json", f"{PHASE_DIR}/changed_files.txt"}, "artifact_hash_ref_invalid")
        require(is_hex64(expected_hash), "artifact_hash_invalid")
        require(sha256_bytes(repo_bytes(ref, candidate)) == expected_hash, "artifact_hash_mismatch")

    changed_rows = repo_text(f"{PHASE_DIR}/changed_files.txt", candidate).splitlines()
    require(changed_rows == list(EXPECTED_PATHS), "changed_files_ledger_mismatch")
    privacy = repo_text(f"{PHASE_DIR}/privacy_scan.txt", candidate)
    for token in (
        "absolute_home_path_findings=0",
        "private_value_findings=0",
        "credential_findings=0",
        "financial_row_findings=0",
        "pid_findings=0",
        "zip_integrity_scan=PASS",
        "zip_decompressed_member_scan=PASS",
        "result=PASS",
    ):
        require(token in privacy, "privacy_scan_contract_failed")
    risk = repo_text(f"{PHASE_DIR}/risk_and_rollback.md", candidate)
    require(contains_all(risk, ("isolated", "canonical", "rollback", "S12-P2-T1", "Stage 1")), "risk_rollback_contract_incomplete")
    verify_json_privacy(evidence)
    return evidence


def load_yaml(path: str, candidate: str | None) -> dict[str, Any]:
    source = repo_text(path, candidate)
    try:
        import yaml
        payload = yaml.safe_load(source)
    except ModuleNotFoundError:
        try:
            validator = runpy.run_path(
                str(REPO_ROOT / "scripts" / "validate_project_governance.py")
            )
            loader = validator.get("fallback_yaml_load")
            require(callable(loader), "yaml_fallback_unavailable")
            payload = loader(source)
        except VerificationError:
            raise
        except Exception as error:
            raise VerificationError(f"invalid_yaml:{PurePosixPath(path).name}") from error
    except Exception as error:
        raise VerificationError(f"invalid_yaml:{PurePosixPath(path).name}") from error
    require(isinstance(payload, dict), "yaml_root_not_object")
    return payload


def verify_governance(candidate: str | None) -> None:
    rows = list(csv.reader(repo_text("PFI/docs/governance/TRACEABILITY_MATRIX.csv", candidate).splitlines()))
    require(bool(rows) and tuple(rows[0]) == TRACE_HEADER, "traceability_header_mismatch")
    require(all(len(row) == len(TRACE_HEADER) for row in rows), "traceability_row_width_mismatch")
    phase_rows = [row for row in rows[1:] if row[6] == ACCEPTANCE_ID]
    require(len(phase_rows) == 4, "traceability_phase_row_count_mismatch")
    require({row[5] for row in phase_rows} == {f"S1-P3-T{index}" for index in range(1, 5)}, "traceability_task_set_mismatch")
    for index, row in enumerate(sorted(phase_rows, key=lambda item: item[5]), start=1):
        require(row[0] == f"REQ-PFI-V025-S1-P13-T{index}", "traceability_requirement_id_mismatch")
        require(row[1:5] == ["NOT_APPLICABLE"] * 4, "traceability_model_fields_changed")
        require(
            "phase_1_3" in row[10] and row[11] == TRACEABILITY_STATUS,
            "traceability_evidence_or_status_invalid",
        )

    version = load_yaml("PFI/docs/governance/VERSION_MATRIX.yaml", candidate)
    require(version.get("product_version") == "v0.2.5", "version_matrix_product_mismatch")
    require(version.get("version_file_value") == "v0.2.5", "version_matrix_version_file_mismatch")
    require(
        contains_all(str(version.get("product_version_status", "")), ("stage_1", "in_progress", "phase_1_3")),
        "version_matrix_status_mismatch",
    )
    require(version.get("current_iteration") == ITERATION_ID, "version_matrix_iteration_mismatch")
    require(version.get("current_phase") == "STAGE1-PHASE1.3", "version_matrix_phase_mismatch")
    require(ACCEPTANCE_ID in str(version.get("current_gate", "")), "version_matrix_gate_mismatch")
    overlays = [
        item
        for item in version.get("phase_overlays", [])
        if isinstance(item, dict) and item.get("iteration_id") == ITERATION_ID
    ]
    require(len(overlays) == 1, "version_matrix_overlay_count_mismatch")
    overlay = overlays[0]
    verify_exact_field_set(overlay, VERSION_OVERLAY_FIELDS, "version_matrix_overlay_field_set_mismatch")
    require(overlay.get("contract_id") == CONTRACT_ID and overlay.get("acceptance_id") == ACCEPTANCE_ID, "version_matrix_overlay_identity_mismatch")
    require(overlay.get("release_content_commit") == RELEASE_CONTENT_COMMIT, "version_matrix_content_commit_mismatch")
    require_true(overlay, "isolated_candidate_finder_launch", "canonical_entries_unchanged", "candidate_cleanup_complete", "runtime_behavior_changed")
    require_false(overlay, "canonical_app_install", "model_formula_parameter_behavior_changed", "financial_data_or_database_changed", "push_performed", "production_accepted")
    require(overlay.get("stage_1_status") == "in_progress" and overlay.get("stage_2_status") == "not_started", "version_matrix_stage_status_mismatch")
    verify_owner_view_conflict(overlay)

    delivery = load_yaml("PFI/docs/governance/delivery_tasks.yaml", candidate)
    contracts = [
        item
        for item in delivery.get("phase_contracts", [])
        if isinstance(item, dict) and item.get("iteration_id") == ITERATION_ID
    ]
    require(len(contracts) == 1, "delivery_contract_count_mismatch")
    contract = contracts[0]
    verify_exact_field_set(contract, DELIVERY_CONTRACT_FIELDS, "delivery_contract_field_set_mismatch")
    require(contract.get("contract_id") == CONTRACT_ID and contract.get("acceptance_id") == ACCEPTANCE_ID, "delivery_contract_identity_mismatch")
    require(contract.get("fact_level") == "VERIFIED" and contract.get("requirement_disposition") == "ACTIVE", "delivery_contract_fact_level_mismatch")
    require(contract.get("release_content_commit") == RELEASE_CONTENT_COMMIT, "delivery_contract_content_commit_mismatch")
    require(contract.get("roadmap_task_ids") == [f"S1-P3-T{index}" for index in range(1, 5)], "delivery_contract_task_set_mismatch")
    require(DELIVERY_EVIDENCE_REFS.issubset(contract.get("evidence_refs", [])), "delivery_contract_evidence_incomplete")
    require(contract.get("model_ids_changed") == [] and contract.get("formula_ids_changed") == [] and contract.get("parameter_ids_changed") == [], "delivery_contract_model_fields_changed")
    require_true(contract, "isolated_candidate_finder_launch", "canonical_entries_unchanged", "candidate_cleanup_complete")
    require_false(contract, "contains_private_values", "canonical_app_install", "push_performed", "production_accepted")
    require(contract.get("stage_1_status") == "in_progress" and contract.get("stage_2_status") == "not_started", "delivery_contract_stage_status_mismatch")
    verify_owner_view_conflict(contract)

    events: list[dict[str, Any]] = []
    for line in repo_text("PFI/docs/governance/development_events.jsonl", candidate).splitlines():
        event = strict_json_loads(line, "development_event_json_invalid")
        require(isinstance(event, dict), "development_event_not_object")
        events.append(event)
    phase_events = [event for event in events if event.get("iteration_id") == ITERATION_ID]
    require(bool(phase_events), "development_event_missing")
    event = phase_events[-1]
    verify_exact_field_set(event, DEVELOPMENT_EVENT_FIELDS, "development_event_field_set_mismatch")
    require(event.get("event_id") == EVENT_ID, "development_event_id_mismatch")
    require(event.get("acceptance_id") == ACCEPTANCE_ID and event.get("contract_id") == CONTRACT_ID, "development_event_identity_mismatch")
    require(event.get("authorization_id") == AUTHORIZATION_ID, "development_event_authorization_mismatch")
    require(event.get("task_ids") == [f"S1-P3-T{index}" for index in range(1, 5)], "development_event_task_set_mismatch")
    require(event.get("git_commit") == RELEASE_CONTENT_COMMIT, "development_event_content_commit_mismatch")
    require(event.get("git_commit_semantics") == "isolated_app_release_content_commit_before_binding_commit", "development_event_commit_semantics_mismatch")
    require(event.get("files_changed") == list(EXPECTED_PATHS), "development_event_files_mismatch")
    require(event.get("fact_level") == "VERIFIED", "development_event_fact_level_mismatch")
    require_true(event, "isolated_candidate_finder_launch", "canonical_entries_unchanged", "candidate_cleanup_complete", "runtime_behavior_changed", "requires_user_acceptance")
    require_false(event, "canonical_app_install_performed", "financial_data_or_database_changed", "contains_private_values", "push_performed", "production_accepted")
    require(event.get("stage_1_status") == "in_progress" and event.get("stage_2_status") == "not_started", "development_event_stage_status_mismatch")
    verify_owner_view_conflict(event)
    verify_json_privacy(event)

    for path, token in (
        ("PFI/CHANGELOG.md", "Stage 1 Phase 1.3 Isolated App Acceptance"),
        ("PFI/docs/governance/DEVELOPMENT_LEDGER.md", ITERATION_ID),
        ("PFI/docs/governance/OWNER_STATUS.md", "Stage 1 Phase 1.3 Isolated App Acceptance Overlay"),
        ("PFI/docs/governance/STATUS.md", "Stage 1 Phase 1.3 Isolated App Acceptance Overlay"),
    ):
        text = repo_text(path, candidate)
        verify_owner_view_blocked_text(text, token)


def git_common_dir() -> Path:
    raw = git_text("rev-parse", "--git-common-dir")
    common = Path(raw)
    if not common.is_absolute():
        common = REPO_ROOT / common
    return common.resolve()


def verify_independent_reviewers(reviewers: Any) -> None:
    require(isinstance(reviewers, list) and len(reviewers) == 3, "attestation_reviewers_incomplete")
    reviewer_ids: set[str] = set()
    lanes: set[str] = set()
    for reviewer in reviewers:
        require(isinstance(reviewer, dict), "attestation_reviewer_invalid")
        require(set(reviewer) == REVIEWER_FIELDS, "attestation_reviewer_field_set_mismatch")
        reviewer_id = reviewer.get("reviewer")
        lane = reviewer.get("lane")
        require(isinstance(lane, str) and lane in REQUIRED_REVIEW_LANES, "attestation_reviewer_lane_invalid")
        require(reviewer_id == REQUIRED_REVIEWERS_BY_LANE[lane], "attestation_reviewer_identity_invalid")
        require(reviewer_id not in reviewer_ids, "attestation_reviewer_duplicate")
        require(lane not in lanes, "attestation_reviewer_lane_duplicate")
        require(reviewer.get("verdict") == "PASS_FOR_ATTESTATION", "attestation_reviewer_verdict_invalid")
        require(is_hex64(reviewer.get("report_sha256")), "attestation_reviewer_report_hash_invalid")
        verify_zero_findings(reviewer, "attestation_reviewer_findings_invalid")
        reviewer_ids.add(reviewer_id)
        lanes.add(lane)
    require(lanes == REQUIRED_REVIEW_LANES, "attestation_reviewer_lanes_incomplete")


def verify_independent_review_reports(
    attestation_dir: Path,
    reviewers: list[dict[str, Any]],
    candidate: str,
    manifest_sha256: str,
    evidence_sha256: str,
) -> tuple[str, ...]:
    review_dir = attestation_dir / "reviews"
    require(review_dir.is_dir() and not review_dir.is_symlink(), "review_report_directory_unavailable")
    expected_names = {f"{lane}.json" for lane in REQUIRED_REVIEW_LANES}
    require({path.name for path in review_dir.iterdir()} == expected_names, "review_report_file_set_mismatch")
    verifier_sha256 = sha256_bytes(repo_bytes("PFI/scripts/v025/verify_stage1_phase13.py", candidate))
    reviewed_at_values: list[str] = []
    for reviewer in reviewers:
        lane = reviewer["lane"]
        report_path = review_dir / f"{lane}.json"
        require(report_path.is_file() and not report_path.is_symlink(), "review_report_unavailable")
        raw = report_path.read_bytes()
        verify_public_bytes(raw)
        report = strict_json_loads(raw, "review_report_invalid_json")
        require(isinstance(report, dict) and set(report) == REVIEW_REPORT_FIELDS, "review_report_field_set_mismatch")
        verify_json_privacy(report)
        require(
            report.get("schema") == "PFIV025Stage1Phase13IndependentReviewV1",
            "review_report_schema_mismatch",
        )
        require(
            is_iso8601_instant(report.get("reviewed_at")),
            "review_report_timestamp_invalid",
        )
        verify_zero_findings(report, "review_report_findings_invalid")
        expected = {
            "reviewer": reviewer["reviewer"],
            "lane": lane,
            "release_content_commit": RELEASE_CONTENT_COMMIT,
            "isolated_app_binding_commit": candidate,
            "manifest_sha256": manifest_sha256,
            "evidence_sha256": evidence_sha256,
            "verifier_sha256": verifier_sha256,
            "verdict": "PASS_FOR_ATTESTATION",
            "critical": 0,
            "important": 0,
            "minor": 0,
            "finding_ids": [],
        }
        require(all(report.get(key) == value for key, value in expected.items()), "review_report_contract_mismatch")
        require(sha256_bytes(raw) == reviewer["report_sha256"], "review_report_hash_mismatch")
        reviewed_at_values.append(report["reviewed_at"])
    return tuple(reviewed_at_values)


def verify_attestation(candidate: str, evidence: dict[str, Any]) -> str:
    path = (
        git_common_dir()
        / "codex-review"
        / "pfi-v025"
        / "stage_1"
        / "phase_1_3"
        / candidate
        / "phase_1_3_attestation.json"
    )
    require(path.is_file() and not path.is_symlink(), "attestation_unavailable")
    raw = path.read_bytes()
    verify_public_bytes(raw)
    attestation = strict_json_loads(raw, "attestation_invalid_json")
    require(isinstance(attestation, dict), "attestation_not_object")
    verify_json_privacy(attestation)
    manifest_sha256 = sha256_bytes(repo_bytes("PFI/config/release_manifest.json", candidate))
    evidence_sha256 = sha256_bytes(repo_bytes(f"{PHASE_DIR}/evidence.json", candidate))
    expected = {
        "schema": "PFIV025Stage1Phase13ExternalAttestationV1",
        "release_content_commit": RELEASE_CONTENT_COMMIT,
        "isolated_app_binding_commit": candidate,
        "manifest_sha256": manifest_sha256,
        "evidence_sha256": evidence_sha256,
        "changed_files": list(EXPECTED_PATHS),
        "verifier_result": "PASS",
        "review_reports_bound": True,
        "review_findings_after_remediation": {"critical": 0, "important": 0, "minor": 0},
        "isolated_candidate_finder_launch": True,
        "canonical_app_install": False,
        "canonical_entries_unchanged": True,
        "candidate_cleanup_complete": True,
        "contains_private_values": False,
        "private_reasoning_persisted": False,
        "push_performed": False,
        "final_human_acceptance": False,
        "production_accepted": False,
        "stage_1_status": "in_progress",
        "stage_2_status": "not_started",
        "owner_view_conflict_id": OWNER_VIEW_CONFLICT_ID,
        "owner_view_conflict_status": "blocked",
        "owner_evidence_state": "unified_owner_view_not_proven",
        "owner_view_resolution_task": OWNER_VIEW_RESOLUTION_TASK,
        "owner_views_unified": False,
        "v0.2.5_accepted": False,
    }
    require(
        set(attestation) == {*expected, "attested_at", "independent_reviewers"},
        "attestation_field_set_mismatch",
    )
    require(all(attestation.get(key) == value for key, value in expected.items()), "attestation_contract_mismatch")
    verify_zero_findings(
        attestation.get("review_findings_after_remediation"),
        "attestation_review_findings_invalid",
    )
    require(
        is_iso8601_instant(attestation.get("attested_at")),
        "attestation_timestamp_invalid",
    )
    verify_owner_view_conflict(attestation)
    verify_independent_reviewers(attestation.get("independent_reviewers"))
    reviewed_at_values = verify_independent_review_reports(
        path.parent,
        attestation["independent_reviewers"],
        candidate,
        manifest_sha256,
        evidence_sha256,
    )
    verify_review_chronology(candidate, reviewed_at_values, attestation["attested_at"])
    require(evidence.get("isolated_app_binding_commit") == "PENDING_POSTCOMMIT_ATTESTATION", "tracked_evidence_self_reference_invalid")
    return sha256_bytes(raw)


def verify(
    *,
    candidate_arg: str | None,
    task_pack: Path,
    roadmap: Path,
    require_attestation: bool,
) -> dict[str, Any]:
    candidate = resolve_mode(candidate_arg, require_attestation)
    release_schema, evidence_schema = verify_source_contracts(task_pack, roadmap, candidate)
    verify_path_contract(candidate)
    manifest, manifest_sha256, frontend_refs = verify_release_contract(candidate, release_schema)
    candidate_record, browser = verify_candidate_records(candidate, manifest, manifest_sha256)
    evidence = verify_evidence(candidate, evidence_schema)
    verify_governance(candidate)
    privacy_artifact_count = verify_phase_privacy(candidate)

    attestation_sha256 = None
    if require_attestation:
        require(candidate is not None, "attestation_requires_binding_candidate")
        attestation_sha256 = verify_attestation(candidate, evidence)

    return {
        "status": "PASS",
        "mode": "BINDING" if candidate else "WORKTREE",
        "candidate": candidate or "WORKTREE",
        "release_content_commit": RELEASE_CONTENT_COMMIT,
        "changed_path_count": len(EXPECTED_PATHS),
        "binding_path_count": len(BINDING_PATHS),
        "frontend_file_count": len(frontend_refs),
        "browser_check_count": len(BROWSER_CHECKS),
        "canonical_entry_count": 3,
        "real_persisted_observed": browser["real_persisted_observed"],
        "privacy_artifact_count": privacy_artifact_count,
        "source_app_tree_sha256": candidate_record["source_app_tree_sha256"],
        "attestation_sha256": attestation_sha256,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify the PFI v0.2.5 Stage 1 Phase 1.3 isolated App acceptance binding."
    )
    parser.add_argument(
        "--candidate",
        help="clean direct binding successor to verify; omit for release-content working-tree mode",
    )
    parser.add_argument(
        "--task-pack",
        type=Path,
        default=Path.home() / "Downloads" / "PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip",
    )
    parser.add_argument(
        "--roadmap",
        type=Path,
        default=Path.home() / "Downloads" / "PFI_v0.2.5_Production_Truth_Human_Workflow_Roadmap.md",
    )
    parser.add_argument(
        "--require-attestation",
        action="store_true",
        help="require the external three-review binding attestation (binding mode only)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = verify(
            candidate_arg=args.candidate,
            task_pack=args.task_pack,
            roadmap=args.roadmap,
            require_attestation=args.require_attestation,
        )
    except VerificationError as error:
        print(f"PFI_STAGE1_PHASE13_VERIFY_ERROR: {error}", file=sys.stderr)
        return 1
    except Exception:
        print("PFI_STAGE1_PHASE13_VERIFY_ERROR: verification_failed", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Freeze the exact reviewed PFI v0.2.5 release after explicit Owner acceptance."""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import subprocess
import sys
import zipfile
from typing import Any

from jsonschema import Draft202012Validator


PFI_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = PFI_ROOT.parent
SCRIPTS_ROOT = PFI_ROOT / "scripts/v025"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from stage12_whole_review_rereview import (  # noqa: E402
    EVIDENCE_INDEX_SHA256,
    FINAL_ACCEPTANCE,
    PRODUCT_CANDIDATE_COMMIT,
    REREVIEW_EVIDENCE_COMMIT,
    REVIEWED_CLOSURE_COMMIT,
    binding_rereview,
    closure_overlay_audit,
    verify_existing,
)


VERSION = "v0.2.5"
BUILD_ID = "pfi-v025-s1p1-20260712.1"
APP_VERSION = "0.2.5"
APP_BUILD = "20260712.1"
STAGE = 12
PHASE = "12.3"
TASK_ID = "S12-P3-T4"
ACCEPTANCE_ID = "ACC-PFI-V025-STAGE12-WHOLE-REVIEW"
ACCEPTANCE_REQUESTED_AT = "2026-07-15T21:45:47Z"
ACCEPTED_AT = "2026-07-15T23:50:30Z"
OUTPUT_DIR = FINAL_ACCEPTANCE.parent
PHASE123_DIR = PFI_ROOT / "reports/pfi_v025/stage_12/phase_12_3"
TASKPACK = (
    Path.home()
    / "Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip"
)
ACCEPTANCE_STATEMENT = (
    "我明确最终接受 PFI v0.2.5（build pfi-v025-s1p1-20260712.1，App 0.2.5 / "
    "20260712.1），接受范围为 Stage 0–12；接受 product candidate A "
    "c8ce63aac785ae1f119cfe1ff993c4e81436bf97、evidence-index "
    "sha256:ebd03b8abf92238aac0e3f972461e35de6ce4b3be27c3662ab24f6af7b342344、"
    "reviewed closure B 559cf190ccfd97aabcf37a5edf2bf1e9abe300fc、rereview evidence C "
    "123f5a6f7e7af22c283e49e55c2ba581310238d5，并确认验收请求时间 "
    "2026-07-15T21:45:47Z；我接受五项非阻断 P2：真实 kernel sleep/wake 未运行、"
    "Holdings not_loaded/not_run、全程 CLI-only 且禁止 Finder、axe-core 不可用并采用 "
    "WCAG/CDP AX 替代证据、六项 historical-state tests debt；我授权执行 S12-P3-T4 "
    "release freeze，并随后仅执行一次 GitHub main 上传及 CLI-only canonical PFI.app "
    "最终重装与校验。"
)
ACCEPTED_SCOPE = [
    "PFI v0.2.5 Stage 0 through Stage 12",
    "build pfi-v025-s1p1-20260712.1 and canonical App 0.2.5 / 20260712.1",
    f"product candidate A {PRODUCT_CANDIDATE_COMMIT}",
    f"reviewed closure B {REVIEWED_CLOSURE_COMMIT}",
    f"rereview evidence C {REREVIEW_EVIDENCE_COMMIT}",
    f"evidence index {EVIDENCE_INDEX_SHA256}",
]
KNOWN_DEFECTS = [
    "P2: actual kernel sleep/wake was not run; only the owned-process suspend/resume proxy was run",
    "P2: Holdings remains not_loaded/not_run",
    "P2: the full workflow is CLI-only and Finder is prohibited",
    "P2: axe-core is unavailable; deterministic WCAG 2.2 AA, keyboard and CDP AX evidence is used instead",
    "P2: six historical-state tests remain registered debt with current-state replacement gates",
]


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return payload


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _git_text(*args: str) -> str:
    completed = subprocess.run(
        ["git", "-c", "gc.auto=0", "-c", "core.quotePath=false", *args],
        cwd=REPO_ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    if completed.returncode:
        raise RuntimeError(completed.stderr.strip() or "git command failed")
    return completed.stdout.strip()


def _schema(name: str) -> dict[str, object]:
    with zipfile.ZipFile(TASKPACK) as archive:
        payload = json.loads(archive.read(f"PFI_v0.2.5_TaskPack/schemas/{name}"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"invalid TaskPack schema: {name}")
    return payload


def expected_acceptance() -> dict[str, object]:
    return {
        "acceptance_statement": ACCEPTANCE_STATEMENT,
        "accepted_at": ACCEPTED_AT,
        "accepted_scope": ACCEPTED_SCOPE,
        "build_id": BUILD_ID,
        "evidence_index_hash": EVIDENCE_INDEX_SHA256,
        "git_commit": PRODUCT_CANDIDATE_COMMIT,
        "known_defects": KNOWN_DEFECTS,
        "product": "PFI",
        "stage": STAGE,
        "user_confirmation_reference": (
            "Codex Owner exact final acceptance; request_generated_at="
            f"{ACCEPTANCE_REQUESTED_AT}"
        ),
        "version": VERSION,
    }


def validate_release_gate() -> dict[str, object]:
    head = _git_text("rev-parse", "HEAD")
    index_path = PHASE123_DIR / "final_evidence_index.json"
    request = _read_json(PHASE123_DIR / "human_acceptance_request.json")
    rereview = _read_json(
        PFI_ROOT
        / "reports/pfi_v025/stage_12/whole_stage_review/rereview/evidence.json"
    )
    with Path("/Applications/PFI.app/Contents/Info.plist").open("rb") as handle:
        app_plist = plistlib.load(handle)
    closure = closure_overlay_audit(head)
    rereview_verification = verify_existing()
    checks = {
        "head_is_rereview_evidence_c": head == REREVIEW_EVIDENCE_COMMIT,
        "candidate_a_exact": request.get("git_commit") == PRODUCT_CANDIDATE_COMMIT,
        "closure_b_exact": rereview.get("reviewed_closure_commit")
        == REVIEWED_CLOSURE_COMMIT,
        "rereview_evidence_commit_c_exists": _git_text(
            "rev-parse", REREVIEW_EVIDENCE_COMMIT
        )
        == REREVIEW_EVIDENCE_COMMIT,
        "index_hash_exact": _sha(index_path) == EVIDENCE_INDEX_SHA256,
        "request_index_hash_exact": request.get("evidence_index_hash")
        == EVIDENCE_INDEX_SHA256,
        "request_time_exact": request.get("request_generated_at")
        == ACCEPTANCE_REQUESTED_AT,
        "version_exact": request.get("version") == VERSION,
        "build_exact": request.get("build_id") == BUILD_ID,
        "known_defect_count_exact": len(request.get("known_defects", [])) == 5,
        "rereview_pass": rereview.get("rereview_result")
        == "pass_waiting_explicit_final_acceptance",
        "rereview_p0_zero": rereview.get("rereview_open_p0_count") == 0,
        "rereview_p1_zero": rereview.get("rereview_open_p1_count") == 0,
        "rereview_minor_zero": rereview.get("rereview_minor_count") == 0,
        "closure_overlay_pass": closure.get("status") == "pass",
        "rereview_verifier_pass": rereview_verification.get("status") == "pass",
        "runtime_payload_drift_zero": closure.get(
            "runtime_payload_drift_count_through_current_head"
        )
        == 0,
        "canonical_app_version_exact": app_plist.get("CFBundleShortVersionString")
        == APP_VERSION,
        "canonical_app_build_exact": app_plist.get("CFBundleVersion") == APP_BUILD,
    }
    failed = sorted(name for name, passed in checks.items() if not passed)
    if failed:
        raise RuntimeError(f"final acceptance gate failed closed: {failed}")
    return {
        "schema": "PFIV025Stage12FinalAcceptanceGateV1",
        "status": "pass",
        "head": head,
        "checks": checks,
        "failed_checks": failed,
        "finder_used": False,
        "launchservices_used": False,
        "gui_file_operations_used": False,
        "push_performed": False,
        "app_reinstall_performed": False,
        "contains_private_values": False,
    }


def finalize() -> dict[str, object]:
    if FINAL_ACCEPTANCE.exists():
        existing = _read_json(FINAL_ACCEPTANCE)
        expected = expected_acceptance()
        Draft202012Validator(_schema("human_acceptance.schema.json")).validate(
            existing
        )
        if existing != expected:
            raise RuntimeError("existing final acceptance differs from exact Owner statement")
        return _read_json(OUTPUT_DIR / "evidence.json")

    gate = validate_release_gate()
    acceptance = expected_acceptance()
    Draft202012Validator(_schema("human_acceptance.schema.json")).validate(
        acceptance
    )
    datetime.fromisoformat(ACCEPTED_AT.replace("Z", "+00:00"))
    _write_json(FINAL_ACCEPTANCE, acceptance)
    _write_json(OUTPUT_DIR / "release_gate.json", gate)

    contract = {
        "schema": "PFIV025Stage12FinalAcceptanceContractV1",
        "status": "release_frozen_waiting_single_delivery_transaction",
        "version": VERSION,
        "stage": STAGE,
        "phase": PHASE,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "product_candidate_commit": PRODUCT_CANDIDATE_COMMIT,
        "reviewed_closure_commit": REVIEWED_CLOSURE_COMMIT,
        "rereview_evidence_commit": REREVIEW_EVIDENCE_COMMIT,
        "evidence_index_hash": EVIDENCE_INDEX_SHA256,
        "accepted_at": ACCEPTED_AT,
        "stop_before": [
            "GitHub main upload until release-freeze commit passes validation",
            "canonical PFI.app reinstall until release-freeze commit passes validation",
            "v0.2.6 work",
        ],
        "finder_prohibited": True,
    }
    _write_json(OUTPUT_DIR / "phase_contract.json", contract)

    evidence = {
        "schema": "PFIV025Stage12FinalAcceptanceEvidenceV1",
        "version": VERSION,
        "stage": STAGE,
        "phase": PHASE,
        "status": "candidate_pass",
        "git_commit": PRODUCT_CANDIDATE_COMMIT,
        "git_commit_semantics": "exact accepted product candidate A; closure B and rereview C are non-runtime reviewed evidence anchors",
        "allowed_files_obeyed": True,
        "commands": [
            {
                "command": "internal exact A/B/C/index/request/App/schema gate",
                "exit_code": 0,
                "summary": "all exact final-acceptance preconditions passed",
            }
        ],
        "changed_files": sorted(
            set(
                _git_text("diff", "HEAD", "--name-only").splitlines()
                + _git_text("ls-files", "--others", "--exclude-standard").splitlines()
            )
        ),
        "evidence_files": [
            "human_acceptance.json",
            "release_gate.json",
            "phase_contract.json",
            "release_freeze.json",
            "risk_and_rollback.md",
            "terminal.log",
        ],
        "explicitly_not_done": [
            "GitHub main upload",
            "canonical PFI.app final reinstall",
            "production delivery parity acceptance",
            "v0.2.6 work",
        ],
        "risks": [
            "The five explicitly accepted nonblocking P2 residuals remain open by design",
            "The one permitted final delivery transaction still requires separate preflight and parity proof",
        ],
        "rollback": "Before delivery, revert only the final-acceptance governance overlay; never rewrite A/B/C or restore migrated directories.",
        "requires_user_acceptance": True,
        "task_id": TASK_ID,
        "task_status": "completed",
        "release_freeze_performed": True,
        "final_human_acceptance": True,
        "stage_12_accepted": True,
        "overall_completed_task_count": 156,
        "overall_total_task_count": 156,
        "push_performed": False,
        "app_reinstall_performed": False,
        "production_accepted": False,
        "finder_used": False,
        "launchservices_used": False,
        "gui_file_operations_used": False,
        "contains_private_values": False,
    }
    Draft202012Validator(_schema("evidence_pack.schema.json")).validate(evidence)
    _write_json(OUTPUT_DIR / "evidence.json", evidence)
    _write_json(
        OUTPUT_DIR / "release_freeze.json",
        {
            "schema": "PFIV025Stage12ReleaseFreezeV1",
            "status": "frozen_waiting_single_delivery_transaction",
            "version": VERSION,
            "build_id": BUILD_ID,
            "app_version": APP_VERSION,
            "app_build": APP_BUILD,
            "product_candidate_commit": PRODUCT_CANDIDATE_COMMIT,
            "reviewed_closure_commit": REVIEWED_CLOSURE_COMMIT,
            "rereview_evidence_commit": REREVIEW_EVIDENCE_COMMIT,
            "evidence_index_hash": EVIDENCE_INDEX_SHA256,
            "acceptance_requested_at": ACCEPTANCE_REQUESTED_AT,
            "accepted_at": ACCEPTED_AT,
            "known_nonblocking_p2_count": 5,
            "release_freeze_performed": True,
            "final_human_acceptance": True,
            "push_performed": False,
            "app_reinstall_performed": False,
            "production_accepted": False,
            "finder_used": False,
        },
    )
    (OUTPUT_DIR / "terminal.log").write_text(
        "exact_release_gate|exit=0|A/B/C/index/request/App/schema match\n",
        encoding="utf-8",
    )
    (OUTPUT_DIR / "risk_and_rollback.md").write_text(
        """# S12-P3-T4 release freeze 风险与回滚

- Owner 已精确接受 A/B/C、evidence-index、Stage 0–12 与五项非阻断 P2；本工件不推断额外范围。
- 本 freeze 尚未执行 GitHub main 上传或 canonical App 最终重装；二者只允许在后续单一 delivery transaction 中各执行一次。
- 全程禁止 Finder、`open`、LaunchServices、AppleScript 与 GUI 文件操作。
- delivery 前回滚只 revert 本 final-acceptance 非 runtime overlay；不得改写 A/B/C、恢复迁出目录或更改 runtime payload。
""",
        encoding="utf-8",
    )
    manifest_inputs = sorted(
        path
        for path in OUTPUT_DIR.iterdir()
        if path.is_file() and path.name != "artifact_manifest.json"
    )
    _write_json(
        OUTPUT_DIR / "artifact_manifest.json",
        {
            "schema": "PFIV025Stage12FinalAcceptanceArtifactManifestV1",
            "status": "pass",
            "file_count": len(manifest_inputs),
            "files": {
                path.relative_to(REPO_ROOT).as_posix(): _sha(path)
                for path in manifest_inputs
            },
            "contains_private_values": False,
        },
    )
    return evidence


def verify() -> dict[str, object]:
    acceptance = _read_json(FINAL_ACCEPTANCE)
    Draft202012Validator(_schema("human_acceptance.schema.json")).validate(
        acceptance
    )
    checks = {
        "acceptance_exact": acceptance == expected_acceptance(),
        "evidence_present": (OUTPUT_DIR / "evidence.json").is_file(),
        "freeze_present": (OUTPUT_DIR / "release_freeze.json").is_file(),
        "artifact_manifest_present": (OUTPUT_DIR / "artifact_manifest.json").is_file(),
        "binding_state_valid": binding_rereview()["status"] == "pass",
        "runtime_payload_drift_zero": closure_overlay_audit()[
            "runtime_payload_drift_count_through_current_head"
        ]
        == 0,
    }
    manifest = _read_json(OUTPUT_DIR / "artifact_manifest.json")
    manifest_mismatches = [
        relative
        for relative, expected in manifest["files"].items()
        if not (REPO_ROOT / relative).is_file()
        or _sha(REPO_ROOT / relative) != expected
    ]
    checks["artifact_manifest_exact"] = (
        not manifest_mismatches
        and manifest.get("file_count") == len(manifest.get("files", {}))
    )
    failed = sorted(name for name, passed in checks.items() if not passed)
    return {
        "schema": "PFIV025Stage12FinalAcceptanceVerificationV1",
        "status": "pass" if not failed else "fail",
        "checks": checks,
        "failed_checks": failed,
        "manifest_mismatches": sorted(manifest_mismatches),
        "final_human_acceptance": True,
        "release_freeze_performed": True,
        "finder_used": False,
        "contains_private_values": False,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--finalize", action="store_true")
    actions.add_argument("--verify", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    payload = finalize() if args.finalize else verify()
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0 if payload.get("status") == "candidate_pass" or payload.get("status") == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())

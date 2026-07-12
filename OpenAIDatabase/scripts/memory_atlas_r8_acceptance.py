#!/usr/bin/env python3
"""Compute Memory Atlas v1.2 R8 acceptance from the corrected requirement history."""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


BASE_MATRIX = Path("机器治理/证据与日志/remediation/v1_2_r0/requirements_gap_matrix.csv")
DELTA_PATHS = tuple(
    Path(f"机器治理/证据与日志/remediation/v1_2_r{phase}/requirements_gap_delta.csv")
    for phase in range(1, 8)
)
EXPECTED_REQUIREMENT_COUNT = 58
EXPECTED_R8_REQUIREMENTS = frozenset(
    {"S03-AC05", "S04-AC04", "S10-AC04", "S14-AC02", "S14-AC05"}
)
R8_DELTA_PATH = Path("机器治理/证据与日志/remediation/v1_2_r8/requirements_gap_delta.csv")
R8_ACCEPTANCE_PATH = Path("机器治理/证据与日志/remediation/v1_2_r8/final_acceptance.json")
R8_STATUS_PATH = Path("机器治理/证据与日志/remediation/v1_2_r8/status.json")
R8_STAGE_LEDGER_PATH = Path(
    "机器治理/证据与日志/stage_pass_gates/stage_pass_gate_status.v1_2_r8.json"
)
FINAL_RECORD_PATHS = (
    R8_DELTA_PATH,
    R8_ACCEPTANCE_PATH,
    R8_STATUS_PATH,
    R8_STAGE_LEDGER_PATH,
)

REQUIRED_R8_GATE_IDS = (
    "unit_tests",
    "frontend_build",
    "chinese_ux_audit",
    "rendered_chinese_ux",
    "visual_roi_audit",
    "visual_workflows",
    "command_workflows",
    "proposal_e2e",
    "owner_daily_e2e",
    "stage7_visual",
    "stage7_performance",
    "stage7_privacy_accessibility",
    "raw_append_only_audit",
    "credential_audit",
    "github_backup_modes",
    "tracked_only_recovery",
    "report_contract_audit",
)

FOUR_LINE_GATES = (
    {
        "line_id": "L1_BEHAVIOR_INTELLIGENCE",
        "name_zh": "行为智能与洞察",
        "gate_ids": ("unit_tests", "visual_workflows", "report_contract_audit"),
    },
    {
        "line_id": "L2_INFO_ROI_CHINESE_VISUALS",
        "name_zh": "信息 ROI、中文与多维可视化",
        "gate_ids": (
            "frontend_build",
            "chinese_ux_audit",
            "rendered_chinese_ux",
            "visual_roi_audit",
            "visual_workflows",
            "stage7_visual",
            "stage7_performance",
        ),
    },
    {
        "line_id": "L3_GITHUB_BACKUP_RECOVERY",
        "name_zh": "ChatGPT、Codex 与后续 Agent 的 GitHub 备份恢复",
        "gate_ids": (
            "github_backup_modes",
            "tracked_only_recovery",
            "raw_append_only_audit",
            "stage7_privacy_accessibility",
            "credential_audit",
        ),
    },
    {
        "line_id": "L4_UIUX_GOVERNED_ACTIONS",
        "name_zh": "UIUX、授权变更与低负担运维",
        "gate_ids": (
            "frontend_build",
            "rendered_chinese_ux",
            "command_workflows",
            "proposal_e2e",
            "owner_daily_e2e",
            "stage7_privacy_accessibility",
        ),
    },
)


class AcceptanceHistoryError(RuntimeError):
    """The corrected requirement ledger is missing, duplicated or contradictory."""


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise AcceptanceHistoryError(f"missing requirement evidence: {path.as_posix()}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def reconcile_requirement_history(repo_root: Path) -> dict[str, dict[str, Any]]:
    repo_root = Path(repo_root).resolve()
    baseline = _read_csv(repo_root / BASE_MATRIX)
    if len(baseline) != EXPECTED_REQUIREMENT_COUNT:
        raise AcceptanceHistoryError(
            f"R0 requirement count must be {EXPECTED_REQUIREMENT_COUNT}, got {len(baseline)}"
        )

    state: dict[str, dict[str, Any]] = {}
    for row in baseline:
        requirement_id = str(row.get("requirement_id") or "")
        if not requirement_id or requirement_id in state:
            raise AcceptanceHistoryError("R0 contains a missing or duplicate requirement_id")
        state[requirement_id] = {
            "requirement_id": requirement_id,
            "stage_id": str(row.get("stage_id") or ""),
            "requirement": str(row.get("requirement") or ""),
            "status": str(row.get("current_status") or ""),
            "evidence": str(row.get("implementation_evidence") or ""),
            "evidence_phase": "R0",
        }

    for index, relative_path in enumerate(DELTA_PATHS, 1):
        rows = _read_csv(repo_root / relative_path)
        seen: set[str] = set()
        for row in rows:
            requirement_id = str(row.get("requirement_id") or "")
            if requirement_id not in state or requirement_id in seen:
                raise AcceptanceHistoryError(
                    f"R{index} delta contains an unknown or duplicate requirement_id: {requirement_id}"
                )
            seen.add(requirement_id)
            before = str(row.get("before_status") or "")
            after = str(row.get("after_status") or "")
            if state[requirement_id]["status"] != before:
                raise AcceptanceHistoryError(
                    f"R{index} status chain mismatch for {requirement_id}: "
                    f"expected {state[requirement_id]['status']}, delta says {before}"
                )
            evidence = next(
                (str(value) for key, value in row.items() if key.endswith("_evidence") and value),
                "",
            )
            state[requirement_id].update(
                {
                    "status": after,
                    "evidence": evidence or state[requirement_id]["evidence"],
                    "evidence_phase": f"R{index}",
                }
            )

    unresolved = {requirement_id for requirement_id, row in state.items() if row["status"] != "VERIFIED"}
    if unresolved != EXPECTED_R8_REQUIREMENTS:
        raise AcceptanceHistoryError(
            f"R1-R7 must leave exactly the five R8 requirements; got {sorted(unresolved)}"
        )
    return state


def _passed_gate_ids(gates: list[dict[str, Any]]) -> tuple[set[str], list[str], list[str]]:
    gate_ids = [str(gate.get("gate_id") or "") for gate in gates]
    duplicates = sorted({gate_id for gate_id in gate_ids if gate_id and gate_ids.count(gate_id) > 1})
    passed = {
        str(gate.get("gate_id"))
        for gate in gates
        if gate.get("status") == "PASS"
        and isinstance(gate.get("command"), list)
        and len(gate["command"]) >= 2
    }
    missing = sorted(set(REQUIRED_R8_GATE_IDS).difference(gate_ids))
    failed = sorted(set(REQUIRED_R8_GATE_IDS).difference(passed).difference(missing))
    return passed, missing, sorted(set(failed).union(duplicates))


def _promote(
    state: dict[str, dict[str, Any]],
    requirement_id: str,
    passed: set[str],
    required_gate_ids: tuple[str, ...],
    evidence: str,
) -> None:
    if set(required_gate_ids).issubset(passed):
        state[requirement_id].update(
            status="VERIFIED",
            evidence=evidence,
            evidence_phase="R8",
            gate_ids=list(required_gate_ids),
        )


def _stage_status(rows: list[dict[str, Any]]) -> str:
    statuses = {str(row["status"]) for row in rows}
    if statuses == {"VERIFIED"}:
        return "VERIFIED"
    for status in ("FAILED", "PARTIAL", "NOT_VERIFIED"):
        if status in statuses:
            return status
    return "FAILED"


def build_acceptance_summary(
    repo_root: Path,
    gates: list[dict[str, Any]],
    verified_commit: str,
) -> dict[str, Any]:
    state = reconcile_requirement_history(repo_root)
    passed, missing, failed = _passed_gate_ids(gates)

    _promote(
        state,
        "S03-AC05",
        passed,
        ("rendered_chinese_ux", "stage7_privacy_accessibility", "raw_append_only_audit"),
        "Three rendered viewports contain no raw manifest/hash/path/import timestamp details, while the 512-file sanitized public-raw manifest and append-only ledger pass independently.",
    )
    _promote(
        state,
        "S04-AC04",
        passed,
        ("github_backup_modes", "tracked_only_recovery"),
        "The final tracked recovery set passes exact-commit recovery, and isolated dry-run/apply backup-mode tests prove local commit behavior with zero remote push.",
    )
    _promote(
        state,
        "S10-AC04",
        passed,
        ("rendered_chinese_ux",),
        "A real three-viewport browser gate checks zh-CN language, Chinese decision labels, untranslated-label denylist, layout containment, reachability and console/network health.",
    )

    four_line_coverage = []
    for line in FOUR_LINE_GATES:
        missing_for_line = sorted(set(line["gate_ids"]).difference(passed))
        four_line_coverage.append(
            {
                "line_id": line["line_id"],
                "name_zh": line["name_zh"],
                "status": "PASS" if not missing_for_line else "FAIL",
                "gate_ids": list(line["gate_ids"]),
                "failed_or_missing_gate_ids": missing_for_line,
            }
        )

    if all(line["status"] == "PASS" for line in four_line_coverage):
        state["S14-AC02"].update(
            status="VERIFIED",
            evidence="The aggregate final audit executes and passes explicit gates for all four v1.2 upgrade lines.",
            evidence_phase="R8",
            gate_ids=list(REQUIRED_R8_GATE_IDS),
        )
    if all(row["status"] == "VERIFIED" for key, row in state.items() if key != "S14-AC05"):
        state["S14-AC05"].update(
            status="VERIFIED",
            evidence="The corrected R0-R8 ledger replays without gaps and exposes current requirement counts plus S01-S14 status instead of historical marker-only PASS claims.",
            evidence_phase="R8",
            gate_ids=list(REQUIRED_R8_GATE_IDS),
        )

    status_counts = Counter(str(row["status"]) for row in state.values())
    remaining = sorted(key for key, row in state.items() if row["status"] != "VERIFIED")
    stage_pass_gates = []
    for stage_number in range(1, 15):
        stage_id = f"S{stage_number:02d}"
        stage_rows = [row for row in state.values() if row["stage_id"] == stage_id]
        stage_pass_gates.append(
            {
                "stage_id": stage_id,
                "status": _stage_status(stage_rows),
                "requirement_count": len(stage_rows),
                "verified_requirement_count": sum(row["status"] == "VERIFIED" for row in stage_rows),
                "requirement_ids": sorted(str(row["requirement_id"]) for row in stage_rows),
            }
        )

    passed_all = (
        not missing
        and not failed
        and not remaining
        and status_counts.get("VERIFIED", 0) == EXPECTED_REQUIREMENT_COUNT
        and all(line["status"] == "PASS" for line in four_line_coverage)
        and all(stage["status"] == "VERIFIED" for stage in stage_pass_gates)
    )
    return {
        "schema_version": "memory_atlas.r8_acceptance.v1",
        "status": "PASS" if passed_all else "FAIL",
        "phase": "R8_OVERALL_ACCEPTANCE_AND_SINGLE_FINAL_DELIVERY",
        "verified_commit": verified_commit,
        "required_gate_ids": list(REQUIRED_R8_GATE_IDS),
        "passed_gate_ids": sorted(passed),
        "missing_gate_ids": missing,
        "failed_gate_ids": failed,
        "four_line_coverage": four_line_coverage,
        "requirements": {
            "total": len(state),
            "verified": status_counts.get("VERIFIED", 0),
            "partial": status_counts.get("PARTIAL", 0),
            "failed": status_counts.get("FAILED", 0),
            "not_verified": status_counts.get("NOT_VERIFIED", 0),
            "remaining_non_verified": remaining,
            "rows": [state[key] for key in sorted(state)],
        },
        "stage_pass_gates": stage_pass_gates,
    }


def build_final_records(
    repo_root: Path,
    summary: dict[str, Any],
    generated_at: str,
    runtime_commit: str,
    delivery_context: dict[str, Any],
) -> dict[str, Any]:
    if summary.get("status") != "PASS":
        raise AcceptanceHistoryError("cannot build final records from a failed R8 acceptance")
    if summary.get("verified_commit") != runtime_commit:
        raise AcceptanceHistoryError("R8 acceptance commit does not match the delivered runtime commit")
    requirements = summary.get("requirements")
    if not isinstance(requirements, dict) or requirements.get("verified") != EXPECTED_REQUIREMENT_COUNT:
        raise AcceptanceHistoryError("R8 acceptance does not prove 58 verified requirements")

    before = reconcile_requirement_history(repo_root)
    final_rows = {
        str(row.get("requirement_id")): row
        for row in requirements.get("rows", [])
        if isinstance(row, dict)
    }
    delta_rows: list[dict[str, str]] = []
    for requirement_id in sorted(EXPECTED_R8_REQUIREMENTS):
        final_row = final_rows.get(requirement_id)
        if not final_row or final_row.get("status") != "VERIFIED" or final_row.get("evidence_phase") != "R8":
            raise AcceptanceHistoryError(f"R8 promotion evidence is missing for {requirement_id}")
        delta_rows.append(
            {
                "requirement_id": requirement_id,
                "before_status": str(before[requirement_id]["status"]),
                "after_status": "VERIFIED",
                "r8_evidence": str(final_row.get("evidence") or ""),
                "remaining_gap": "None",
                "next_remediation_phase": "FINAL_DELIVERY_COMPLETE",
            }
        )

    acceptance = dict(summary)
    acceptance.update(
        {
            "generated_at": generated_at,
            "runtime_commit": runtime_commit,
            "delivery_context": dict(delivery_context),
            "evidence_model": "runtime commit plus immediate final-record child commit",
        }
    )
    stage_ledger = {
        "schema_version": "memory_atlas.stage_pass_gate_status.v1_2_r8",
        "status": "PASS",
        "phase": "R8_OVERALL_ACCEPTANCE_AND_SINGLE_FINAL_DELIVERY",
        "generated_at": generated_at,
        "runtime_commit": runtime_commit,
        "supersedes": [
            "机器治理/证据与日志/stage_pass_gates/stage_pass_gate_status.v1_2_s14_p3.json",
            "all marker-only v1.2 aggregate PASS claims created before remediation R0",
        ],
        "requirements": {
            key: value
            for key, value in requirements.items()
            if key != "rows"
        },
        "four_line_coverage": summary["four_line_coverage"],
        "stage_pass_gates": summary["stage_pass_gates"],
        "query_contract": {
            "current_truth": R8_STAGE_LEDGER_PATH.as_posix(),
            "requirement_delta": R8_DELTA_PATH.as_posix(),
            "full_acceptance": R8_ACCEPTANCE_PATH.as_posix(),
        },
    }
    status = {
        "schema_version": "memory_atlas.remediation_r8_status.v1",
        "phase": "R8_OVERALL_ACCEPTANCE_AND_SINGLE_FINAL_DELIVERY",
        "captured_at": generated_at,
        "status": "R8_ACCEPTANCE_AND_LIVE_DELIVERY_VERIFIED_PENDING_SINGLE_FINAL_PUSH",
        "runtime_commit": runtime_commit,
        "requirements": stage_ledger["requirements"],
        "four_line_coverage": summary["four_line_coverage"],
        "delivery_context": dict(delivery_context),
        "single_push_rule": {
            "push_count_before_this_record": 0,
            "final_push_must_publish_the_immediate_record_child": True,
            "post_push_remote_clone_verification_is_external_and_rerunnable": True,
        },
        "evidence": {
            "requirements_gap_delta": R8_DELTA_PATH.as_posix(),
            "final_acceptance": R8_ACCEPTANCE_PATH.as_posix(),
            "stage_pass_gate_status": R8_STAGE_LEDGER_PATH.as_posix(),
        },
    }
    return {
        "delta_rows": delta_rows,
        "acceptance": acceptance,
        "stage_ledger": stage_ledger,
        "status": status,
    }


def _write_text_atomic(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(payload, encoding="utf-8")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def write_final_records(repo_root: Path, records: dict[str, Any]) -> list[Path]:
    repo_root = Path(repo_root).resolve()
    fieldnames = [
        "requirement_id",
        "before_status",
        "after_status",
        "r8_evidence",
        "remaining_gap",
        "next_remediation_phase",
    ]
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(records["delta_rows"])
    payloads = {
        R8_DELTA_PATH: buffer.getvalue(),
        R8_ACCEPTANCE_PATH: json.dumps(records["acceptance"], ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        R8_STATUS_PATH: json.dumps(records["status"], ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        R8_STAGE_LEDGER_PATH: json.dumps(records["stage_ledger"], ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    }
    for relative_path, payload in payloads.items():
        _write_text_atomic(repo_root / relative_path, payload)
    return list(FINAL_RECORD_PATHS)


def _load_json_object(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise AcceptanceHistoryError(f"missing final R8 record: {path.name}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise AcceptanceHistoryError(f"invalid final R8 JSON record: {path.name}") from exc
    if not isinstance(payload, dict):
        raise AcceptanceHistoryError(f"final R8 record must be an object: {path.name}")
    return payload


def audit_final_records(
    repo_root: Path,
    expected_runtime_commit: str | None = None,
) -> dict[str, Any]:
    repo_root = Path(repo_root).resolve()
    acceptance = _load_json_object(repo_root / R8_ACCEPTANCE_PATH)
    stage_ledger = _load_json_object(repo_root / R8_STAGE_LEDGER_PATH)
    status = _load_json_object(repo_root / R8_STATUS_PATH)
    delta_rows = _read_csv(repo_root / R8_DELTA_PATH)

    runtime_commit = str(acceptance.get("runtime_commit") or "")
    if not re.fullmatch(r"[0-9a-f]{40}", runtime_commit):
        raise AcceptanceHistoryError("final R8 acceptance has an invalid runtime commit")
    if expected_runtime_commit and runtime_commit != expected_runtime_commit:
        raise AcceptanceHistoryError("final R8 runtime commit does not match the expected commit")
    if acceptance.get("status") != "PASS" or acceptance.get("verified_commit") != runtime_commit:
        raise AcceptanceHistoryError("final R8 acceptance is not a PASS for the delivered runtime")
    if set(acceptance.get("required_gate_ids") or []) != set(REQUIRED_R8_GATE_IDS):
        raise AcceptanceHistoryError("final R8 acceptance does not register the exact gate set")
    if not set(REQUIRED_R8_GATE_IDS).issubset(set(acceptance.get("passed_gate_ids") or [])):
        raise AcceptanceHistoryError("one or more final R8 runtime gates are not recorded as PASS")

    requirements = acceptance.get("requirements")
    rows = requirements.get("rows") if isinstance(requirements, dict) else None
    if (
        not isinstance(rows, list)
        or len(rows) != EXPECTED_REQUIREMENT_COUNT
        or requirements.get("total") != EXPECTED_REQUIREMENT_COUNT
        or requirements.get("verified") != EXPECTED_REQUIREMENT_COUNT
        or requirements.get("remaining_non_verified") != []
        or any(not isinstance(row, dict) or row.get("status") != "VERIFIED" for row in rows)
    ):
        raise AcceptanceHistoryError("final R8 acceptance does not contain 58 verified requirement rows")

    before = reconcile_requirement_history(repo_root)
    if len(delta_rows) != len(EXPECTED_R8_REQUIREMENTS):
        raise AcceptanceHistoryError("final R8 delta must contain exactly five promotions")
    seen: set[str] = set()
    for row in delta_rows:
        requirement_id = str(row.get("requirement_id") or "")
        if requirement_id not in EXPECTED_R8_REQUIREMENTS or requirement_id in seen:
            raise AcceptanceHistoryError("final R8 delta contains an unknown or duplicate requirement")
        seen.add(requirement_id)
        if (
            row.get("before_status") != before[requirement_id]["status"]
            or row.get("after_status") != "VERIFIED"
            or not str(row.get("r8_evidence") or "").strip()
            or row.get("remaining_gap") != "None"
        ):
            raise AcceptanceHistoryError(f"final R8 delta is invalid for {requirement_id}")
        before[requirement_id]["status"] = "VERIFIED"
    if seen != EXPECTED_R8_REQUIREMENTS or any(row["status"] != "VERIFIED" for row in before.values()):
        raise AcceptanceHistoryError("final R8 delta does not reconcile the requirement history to 58/58")

    stages = stage_ledger.get("stage_pass_gates")
    stage_ids = [stage.get("stage_id") for stage in stages] if isinstance(stages, list) else []
    if (
        stage_ledger.get("status") != "PASS"
        or stage_ledger.get("runtime_commit") != runtime_commit
        or stage_ids != [f"S{number:02d}" for number in range(1, 15)]
        or any(stage.get("status") != "VERIFIED" for stage in stages)
        or sum(int(stage.get("requirement_count", 0)) for stage in stages) != EXPECTED_REQUIREMENT_COUNT
        or sum(int(stage.get("verified_requirement_count", 0)) for stage in stages) != EXPECTED_REQUIREMENT_COUNT
    ):
        raise AcceptanceHistoryError("final R8 S01-S14 stage ledger is incomplete or inconsistent")
    four_lines = stage_ledger.get("four_line_coverage")
    if not isinstance(four_lines, list) or len(four_lines) != 4 or any(line.get("status") != "PASS" for line in four_lines):
        raise AcceptanceHistoryError("final R8 stage ledger does not prove all four upgrade lines")
    if status.get("runtime_commit") != runtime_commit or status.get("requirements", {}).get("verified") != 58:
        raise AcceptanceHistoryError("final R8 status does not match the accepted runtime and requirements")

    serialized = json.dumps(
        {"acceptance": acceptance, "stage_ledger": stage_ledger, "status": status},
        ensure_ascii=False,
    )
    if "/Users/" in serialized or re.search(r"[A-Za-z]:[\\/]", serialized):
        raise AcceptanceHistoryError("final R8 records contain a machine-local absolute path")
    return {
        "status": "PASS",
        "schema_version": "memory_atlas.r8_final_records_audit.v1",
        "runtime_commit": runtime_commit,
        "requirement_count": EXPECTED_REQUIREMENT_COUNT,
        "verified_requirement_count": EXPECTED_REQUIREMENT_COUNT,
        "stage_count": 14,
        "four_line_count": 4,
        "record_paths": [path.as_posix() for path in FINAL_RECORD_PATHS],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    generate = subparsers.add_parser("generate", help="write final R8 requirement and stage records")
    generate.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    generate.add_argument("--audit-json", type=Path, required=True)
    generate.add_argument("--runtime-commit", required=True)
    generate.add_argument("--generated-at", required=True)
    generate.add_argument("--local-apps-verified", action="store_true")
    generate.add_argument("--cloudflare-live-verified", action="store_true")
    audit = subparsers.add_parser("audit", help="recompute and validate committed R8 records")
    audit.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    audit.add_argument("--expected-runtime-commit")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "generate":
            audit_payload = _load_json_object(args.audit_json)
            if audit_payload.get("status") != "PASS" or not isinstance(audit_payload.get("r8_acceptance"), dict):
                raise AcceptanceHistoryError("atlasctl final audit JSON is not a complete R8 PASS")
            records = build_final_records(
                args.repo_root,
                audit_payload["r8_acceptance"],
                generated_at=args.generated_at,
                runtime_commit=args.runtime_commit,
                delivery_context={
                    "local_apps_verified": args.local_apps_verified,
                    "cloudflare_live_verified": args.cloudflare_live_verified,
                    "single_push_pending": True,
                },
            )
            outputs = write_final_records(args.repo_root, records)
            result = {
                "status": "PASS",
                "command": "generate",
                "runtime_commit": args.runtime_commit,
                "outputs": [path.as_posix() for path in outputs],
            }
        else:
            result = audit_final_records(args.repo_root, args.expected_runtime_commit)
    except (AcceptanceHistoryError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAIL", "reason": str(exc)}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())

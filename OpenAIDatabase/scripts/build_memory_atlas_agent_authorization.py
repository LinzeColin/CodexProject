#!/usr/bin/env python3
"""Build Memory Atlas S08 P2 agent authorization boundary report."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = Path("机器治理/行为智能模型/agent_authorization_boundary.v1_2_s08_p2.json")
COLLABORATION_REPORT_PATH = Path("data/derived/agent_collaboration/agent_collaboration_quality_report.json")
RAW_PUBLIC_POLICY_PATH = Path("机器治理/同步与备份/raw_public_archive_policy.v1_2_s03_p1.json")
RAW_LEDGER_POLICY_PATH = Path("机器治理/同步与备份/raw_manifest_ledger_policy.v1_2_s03_p3.json")
FORMULA_WHAT_IF_CONFIG_PATH = Path("机器治理/参数与公式/formula_what_if_defaults.v1_2_s07_p3.json")
OUTPUT_PATH = Path("data/derived/agent_collaboration/agent_authorization_boundary_report.json")
TASK_ID = "MA-V12-S08P2"
ACCEPTANCE_ID = "ACC-MA-V12-S08P2"
STATUS = "phase_s08_p2_authorization_boundary_completed_pending_s08_p3"


class AgentAuthorizationBuildError(RuntimeError):
    pass


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def load_json(path: Path, label: str) -> dict[str, Any]:
    if not path.exists():
        raise AgentAuthorizationBuildError(f"{label} missing: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise AgentAuthorizationBuildError(f"{label} must be a JSON object: {path}")
    return payload


def doc_evidence(ref_id: str, path: Path, source_id: str = "governance") -> dict[str, str]:
    return {
        "evidence_level": "governance_doc",
        "path": path.as_posix(),
        "ref_id": ref_id,
        "ref_type": "governance_doc",
        "source_id": source_id,
    }


def validate_config(config: dict[str, Any]) -> None:
    if config.get("task_id") != TASK_ID or config.get("acceptance_id") != ACCEPTANCE_ID:
        raise AgentAuthorizationBuildError("authorization boundary config identity mismatch")
    if config.get("boundary_mode") != "machine_config_and_output_checks":
        raise AgentAuthorizationBuildError("authorization boundary must stay in machine config and output checks")

    ui = config.get("delegation_contract_ui") if isinstance(config.get("delegation_contract_ui"), dict) else {}
    if ui.get("complex_ui_required") is not False:
        raise AgentAuthorizationBuildError("S08 P2 must not require complex Delegation Contract UI")

    state_machine = config.get("proposal_state_machine") if isinstance(config.get("proposal_state_machine"), dict) else {}
    required_states = {
        "draft",
        "pending_human_review",
        "approved_by_human",
        "applying",
        "applied",
        "validated",
        "committed",
        "failed_validation",
        "rollback_or_needs_revision",
    }
    states = {str(item) for item in as_list(state_machine.get("states"))}
    missing_states = sorted(required_states - states)
    if missing_states:
        raise AgentAuthorizationBuildError(f"proposal state machine missing states: {', '.join(missing_states)}")
    if state_machine.get("human_approval_required") is not True:
        raise AgentAuthorizationBuildError("human approval must be required before apply")
    if state_machine.get("current_phase_executes_apply") is not False:
        raise AgentAuthorizationBuildError("S08 P2 must not execute apply")
    if state_machine.get("apply_execution_deferred_to") != "S13":
        raise AgentAuthorizationBuildError("actual apply execution must remain deferred to S13")

    required_fields = set(as_list(config.get("proposal_required_fields")))
    for field in {"proposal_id", "target_type", "target_files", "approval", "validation_commands", "rollback_plan"}:
        if field not in required_fields:
            raise AgentAuthorizationBuildError(f"proposal required fields missing {field}")
    approval_fields = set(as_list(config.get("approval_required_fields")))
    for field in {"status", "approved_by", "approved_at"}:
        if field not in approval_fields:
            raise AgentAuthorizationBuildError(f"approval fields missing {field}")

    forbidden_targets = set(as_list(config.get("apply_forbidden_targets")))
    for target in {"raw_archive", "public_raw", "credentials"}:
        if target not in forbidden_targets:
            raise AgentAuthorizationBuildError(f"forbidden target missing {target}")
    forbidden_paths = set(as_list(config.get("forbidden_path_prefixes")))
    for path in {"data/public_raw/", "data/raw/"}:
        if path not in forbidden_paths:
            raise AgentAuthorizationBuildError(f"forbidden path prefix missing {path}")

    boundary = config.get("scope_boundary") if isinstance(config.get("scope_boundary"), dict) else {}
    expected_false = {
        "raw_mutation",
        "complex_delegation_contract_ui",
        "multi_agent_system_implementation",
        "proposal_apply_execution",
    }
    for key in expected_false:
        if boundary.get(key) is not False:
            raise AgentAuthorizationBuildError(f"scope boundary {key} must be false")
    if boundary.get("authorization_boundary_defined_as_machine_checks") is not True:
        raise AgentAuthorizationBuildError("authorization boundary must be defined as machine checks")
    if boundary.get("stage_flight_recorder") != "deferred_to_s08_p3":
        raise AgentAuthorizationBuildError("stage flight recorder must remain deferred to S08 P3")
    if boundary.get("next_phase") != "S08 P3":
        raise AgentAuthorizationBuildError("S08 P2 next phase must be S08 P3")


def validate_inputs(
    collaboration: dict[str, Any],
    raw_public_policy: dict[str, Any],
    raw_ledger_policy: dict[str, Any],
    formula_what_if: dict[str, Any],
) -> None:
    if collaboration.get("task_id") != "MA-V12-S08P1" or collaboration.get("acceptance_id") != "ACC-MA-V12-S08P1":
        raise AgentAuthorizationBuildError("S08 P1 collaboration report identity mismatch")
    collaboration_boundary = collaboration.get("phase_boundary") if isinstance(collaboration.get("phase_boundary"), dict) else {}
    if collaboration_boundary.get("does_not_modify_raw") is not True:
        raise AgentAuthorizationBuildError("S08 P1 report must preserve raw no-mutation boundary")

    append_only = raw_public_policy.get("append_only_rule") if isinstance(raw_public_policy.get("append_only_rule"), dict) else {}
    if append_only.get("forbid_modify_existing_raw") is not True or append_only.get("raw_files_are_not_apply_targets") is not True:
        raise AgentAuthorizationBuildError("raw public policy must forbid raw modification and apply targets")

    audit_contract = raw_ledger_policy.get("audit_contract") if isinstance(raw_ledger_policy.get("audit_contract"), dict) else {}
    if audit_contract.get("raw_files_are_not_apply_targets") is not True:
        raise AgentAuthorizationBuildError("raw ledger policy must keep raw files out of apply targets")

    if formula_what_if.get("proposal_required_before_apply") is not True or formula_what_if.get("active_config_write") is not False:
        raise AgentAuthorizationBuildError("formula what-if config must remain proposal-only before apply")


def check_item(
    check_id: str,
    name_zh: str,
    assertion: str,
    explanation_zh: str,
    evidence_refs: list[dict[str, str]],
    failure_action_zh: str,
) -> dict[str, Any]:
    if not evidence_refs:
        raise AgentAuthorizationBuildError(f"{check_id} missing evidence")
    return {
        "check_id": check_id,
        "name_zh": name_zh,
        "assertion": assertion,
        "status": "PASS",
        "explanation_zh": explanation_zh,
        "evidence_refs": evidence_refs,
        "failure_action_zh": failure_action_zh,
    }


def build_authorization_boundary_report(
    database_dir: Path,
    *,
    dry_run: bool = False,
    generated_at: str | None = None,
) -> dict[str, Any]:
    config = load_json(database_dir / CONFIG_PATH, "authorization boundary config")
    collaboration = load_json(database_dir / COLLABORATION_REPORT_PATH, "S08 P1 collaboration report")
    raw_public_policy = load_json(database_dir / RAW_PUBLIC_POLICY_PATH, "raw public policy")
    raw_ledger_policy = load_json(database_dir / RAW_LEDGER_POLICY_PATH, "raw ledger policy")
    formula_what_if = load_json(database_dir / FORMULA_WHAT_IF_CONFIG_PATH, "formula what-if config")
    validate_config(config)
    validate_inputs(collaboration, raw_public_policy, raw_ledger_policy, formula_what_if)

    configured_checks = [item for item in as_list(config.get("output_checks")) if isinstance(item, dict)]
    checks_by_id = {str(item.get("check_id")): item for item in configured_checks}
    evidence = {
        "config": doc_evidence("s08p2_authorization_config", CONFIG_PATH),
        "s08p1": doc_evidence("s08p1_collaboration_report", COLLABORATION_REPORT_PATH, "derived"),
        "raw_public": doc_evidence("s03p1_raw_public_policy", RAW_PUBLIC_POLICY_PATH),
        "raw_ledger": doc_evidence("s03p3_raw_ledger_policy", RAW_LEDGER_POLICY_PATH),
        "what_if": doc_evidence("s07p3_formula_what_if_config", FORMULA_WHAT_IF_CONFIG_PATH),
    }

    output_checks = [
        check_item(
            "S08P2-CHECK-001",
            "raw 不可作为 apply target",
            checks_by_id["S08P2-CHECK-001"]["assertion"],
            "raw/public_raw/credentials 被显式列入 forbidden targets；raw policy 和 raw ledger 均声明 raw_files_are_not_apply_targets=true。",
            [evidence["config"], evidence["raw_public"], evidence["raw_ledger"]],
            checks_by_id["S08P2-CHECK-001"]["failure_action_zh"],
        ),
        check_item(
            "S08P2-CHECK-002",
            "人类授权后才能 apply",
            checks_by_id["S08P2-CHECK-002"]["assertion"],
            "proposal state machine 要求 approved_by_human 后才可进入 applying；S08 P2 只输出检查，不执行 apply。",
            [evidence["config"], evidence["what_if"], evidence["s08p1"]],
            checks_by_id["S08P2-CHECK-002"]["failure_action_zh"],
        ),
        check_item(
            "S08P2-CHECK-003",
            "proposal 必须可验证和可回滚",
            checks_by_id["S08P2-CHECK-003"]["assertion"],
            "proposal_required_fields 包含 validation_commands 和 rollback_plan，保证后续 S13 apply 前有验证与回滚路径。",
            [evidence["config"], evidence["s08p1"]],
            checks_by_id["S08P2-CHECK-003"]["failure_action_zh"],
        ),
        check_item(
            "S08P2-CHECK-004",
            "本 phase 不执行 apply",
            checks_by_id["S08P2-CHECK-004"]["assertion"],
            "current_phase_executes_apply=false，真实 proposal apply 明确延后到 S13，避免 S08 P2 变成高负担授权框架。",
            [evidence["config"], evidence["s08p1"]],
            checks_by_id["S08P2-CHECK-004"]["failure_action_zh"],
        ),
    ]

    output = {
        "schema_version": "memory_atlas_agent_authorization_boundary_report.v1_2_s08_p2",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": STATUS,
        "generated_at": generated_at or now_utc(),
        "dry_run": dry_run,
        "writes_files": False if dry_run else True,
        "config_path": CONFIG_PATH.as_posix(),
        "output_path": OUTPUT_PATH.as_posix(),
        "input_paths": [
            COLLABORATION_REPORT_PATH.as_posix(),
            RAW_PUBLIC_POLICY_PATH.as_posix(),
            RAW_LEDGER_POLICY_PATH.as_posix(),
            FORMULA_WHAT_IF_CONFIG_PATH.as_posix(),
        ],
        "authorization_boundary_summary": {
            "summary_zh": "S08 P2 将授权边界固定为轻量机器配置和输出检查：raw 不可修改，proposal 必须人类授权后才可 apply，本 phase 不执行 apply。",
            "human_role_zh": "人负责批准或拒绝 proposal，确认业务风险、授权范围和是否进入后续 apply。",
            "agent_role_zh": "Agent 负责生成候选 proposal、检查 target、验证命令和回滚计划；未授权前不得 apply。",
            "raw_boundary_zh": "raw/public_raw/credentials 永远不是 apply target；raw 只允许按 S03 规则追加和审计。",
            "future_apply_zh": "真实 proposal apply、validation、commit/rollback 闭环留给 S13；S08 P2 只定义边界和检查。"
        },
        "proposal_state_machine": config["proposal_state_machine"],
        "proposal_contract": {
            "required_fields": config["proposal_required_fields"],
            "approval_required_fields": config["approval_required_fields"],
            "allowed_target_types": config["allowed_target_types"],
            "apply_forbidden_targets": config["apply_forbidden_targets"],
            "forbidden_path_prefixes": config["forbidden_path_prefixes"],
        },
        "machine_output_checks": output_checks,
        "machine_output_check_summary": {
            "check_count": len(output_checks),
            "pass_count": len([item for item in output_checks if item["status"] == "PASS"]),
            "fail_count": 0,
            "human_approval_required": True,
            "raw_apply_target_allowed": False,
            "current_phase_executes_apply": False,
            "complex_delegation_contract_ui": False,
        },
        "unsupported_scope": {
            "complex_delegation_contract_ui": False,
            "multi_agent_system_implementation": False,
            "proposal_apply_execution": "deferred_to_s13",
            "stage_flight_recorder": "deferred_to_s08_p3",
        },
        "phase_boundary": {
            "authorization_boundary_defined_as_machine_checks": True,
            "does_not_modify_raw": True,
            "does_not_apply_proposals": True,
            "requires_human_approval_before_apply": True,
            "raw_is_never_apply_target": True,
            "does_not_implement_complex_delegation_contract_ui": True,
            "does_not_create_multi_agent_system": True,
            "does_not_generate_stage_flight_recorder": True,
            "next_phase": "S08 P3",
        },
    }
    if not dry_run:
        target = database_dir / OUTPUT_PATH
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Memory Atlas S08 P2 agent authorization boundary report.")
    parser.add_argument("--database-dir", type=Path, default=ROOT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        result = build_authorization_boundary_report(args.database_dir, dry_run=args.dry_run)
    except AgentAuthorizationBuildError as exc:
        print(json.dumps({
            "status": "FAIL",
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "error": str(exc),
        }, ensure_ascii=False, indent=2, sort_keys=True))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

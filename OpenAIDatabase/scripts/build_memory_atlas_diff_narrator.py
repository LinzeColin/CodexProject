#!/usr/bin/env python3
"""Build the Memory Atlas v1.2 S13 P2 Chinese diff narrator report."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK_ID = "MA-V12-S13P2"
ACCEPTANCE_ID = "ACC-MA-V12-S13P2"
STATUS = "phase_s13_p2_diff_narrator_completed_pending_s13_p3"
CONTRACT_VERSION = "diff_narrator.v1_2_s13_p2"
SCHEMA_VERSION = "openai_database.diff_narrator.v1_2_s13_p2"
MACHINE_DIFF_SCHEMA_VERSION = "openai_database.diff_narrator_machine_diff.v1_2_s13_p2"

CONFIG_PATH = Path("机器治理/运行门禁/diff_narrator.v1_2_s13_p2.json")
STATE_MACHINE_REPORT_PATH = Path("data/derived/proposals/proposal_state_machine_report.json")
SELF_ITERATION_PATH = Path("data/derived/behavior_intelligence/self_iteration_suggestions.json")
OUTPUT_PATH = Path("data/derived/proposals/diff_narrator_report.json")
MACHINE_DIFF_PATH = Path("机器治理/证据与日志/proposal_diffs/diff_narrator_machine_diff.v1_2_s13_p2.json")

REQUIRED_HUMAN_SECTIONS = [
    "what_changed_zh",
    "why_changed_zh",
    "affected_surfaces_zh",
    "how_to_verify_zh",
    "how_to_rollback_zh",
]


class DiffNarratorBuildError(RuntimeError):
    pass


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise DiffNarratorBuildError(f"missing required input: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def isoformat_z(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def source_as_of(*payloads: dict[str, Any]) -> datetime:
    candidates = [parse_time(str(payload.get("generated_at"))) for payload in payloads if payload.get("generated_at")]
    valid = [candidate for candidate in candidates if candidate is not None]
    if not valid:
        return datetime(2026, 7, 8, tzinfo=timezone.utc)
    return max(valid)


def validate_config(config: dict[str, Any]) -> None:
    narrator = config.get("diff_narrator") if isinstance(config.get("diff_narrator"), dict) else {}
    sections = set(narrator.get("required_human_sections") or [])
    missing = [section for section in REQUIRED_HUMAN_SECTIONS if section not in sections]
    if config.get("schema_version") != CONTRACT_VERSION or config.get("task_id") != TASK_ID or config.get("acceptance_id") != ACCEPTANCE_ID:
        raise DiffNarratorBuildError("S13 P2 config identity mismatch")
    if config.get("status") != STATUS:
        raise DiffNarratorBuildError("S13 P2 config status mismatch")
    if narrator.get("language") != "zh":
        raise DiffNarratorBuildError("S13 P2 diff narrator must be Chinese")
    if missing:
        raise DiffNarratorBuildError(f"S13 P2 config missing narrator sections: {', '.join(missing)}")
    if narrator.get("human_homepage_policy", {}).get("no_full_machine_diff") is not True:
        raise DiffNarratorBuildError("S13 P2 must keep full machine diff out of the human homepage")
    if narrator.get("machine_diff_evidence_path") != str(MACHINE_DIFF_PATH):
        raise DiffNarratorBuildError("S13 P2 machine diff evidence path mismatch")
    boundary = config.get("scope_boundary") if isinstance(config.get("scope_boundary"), dict) else {}
    if boundary.get("raw_mutation") is not False or boundary.get("proposal_apply_execution") is not False:
        raise DiffNarratorBuildError("S13 P2 must not mutate raw or execute proposal apply")
    if boundary.get("rollback_execution") is not False:
        raise DiffNarratorBuildError("S13 P2 must not execute rollback")


def self_iteration_by_proposal_id(self_iteration: dict[str, Any]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for suggestion in self_iteration.get("self_iteration_suggestions") or []:
        if not isinstance(suggestion, dict):
            continue
        proposal = suggestion.get("proposal") if isinstance(suggestion.get("proposal"), dict) else {}
        proposal_id = proposal.get("proposal_id")
        if proposal_id:
            indexed[str(proposal_id)] = suggestion
    return indexed


def join_target_files(target_files: list[str]) -> str:
    if not target_files:
        return "未声明目标文件"
    return "、".join(target_files[:4]) + (" 等" if len(target_files) > 4 else "")


def summarize_verification(commands: list[str]) -> str:
    if not commands:
        return "先运行对应 phase validator，再检查 raw 和 apply 边界。"
    return "运行 " + "；".join(commands[:3]) + "。"


def build_narration(proposal: dict[str, Any], suggestion: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    proposal_id = str(proposal.get("proposal_id") or suggestion.get("suggestion_id"))
    proposal_payload = suggestion.get("proposal") if isinstance(suggestion.get("proposal"), dict) else {}
    target_files = [str(item) for item in proposal.get("target_files") or proposal_payload.get("target_files") or []]
    before_after_diff = proposal_payload.get("before_after_diff") if isinstance(proposal_payload.get("before_after_diff"), dict) else {}
    before_zh = str(before_after_diff.get("before_zh") or "当前 phase 不修改目标文件。")
    after_zh = str(before_after_diff.get("after_zh") or "人类批准后再生成最小 diff。")
    validation_commands = [str(item) for item in proposal.get("validation_commands") or proposal_payload.get("validation_commands") or []]
    rollback_plan_zh = str(proposal.get("rollback_plan_zh") or proposal_payload.get("rollback_plan_zh") or "使用 proposal rollback 或 git revert；raw 文件不回滚。")
    target_type = str(proposal.get("target_type") or suggestion.get("target_type") or proposal_payload.get("target_type") or "unknown")
    risk_level = str(proposal_payload.get("risk_level") or "medium")
    human_reason_zh = str(proposal_payload.get("human_reason_zh") or suggestion.get("suggestion_zh") or "来自自我迭代候选，需要人类确认后才可采纳。")
    expected_change_zh = str(suggestion.get("expected_change_zh") or after_zh)

    narration = {
        "proposal_id": proposal_id,
        "target_type": target_type,
        "target_files": target_files,
        "current_state": proposal.get("current_state"),
        "risk_level": risk_level,
        "what_changed_zh": f"改了什么：如果后续采纳，将把 {join_target_files(target_files)} 从「{before_zh}」推进到「{after_zh}」。S13 P2 只解释 diff，不写文件。",
        "why_changed_zh": f"为什么改：{human_reason_zh} 预期收益是：{expected_change_zh}",
        "affected_surfaces_zh": f"影响什么：影响 {target_type} 范围内的 {join_target_files(target_files)}；不影响 data/public_raw、data/raw、credentials、cookies 或 tokens。",
        "how_to_verify_zh": f"如何验证：{summarize_verification(validation_commands)}",
        "how_to_rollback_zh": f"如何回滚：{rollback_plan_zh}",
        "machine_diff_ref": str(MACHINE_DIFF_PATH),
        "machine_diff_inline_in_human_summary": False,
        "apply_execution_allowed": False,
        "raw_apply_target_allowed": False,
    }
    machine_diff = {
        "proposal_id": proposal_id,
        "target_type": target_type,
        "target_files": target_files,
        "risk_level": risk_level,
        "before_after_diff": before_after_diff,
        "human_reason_zh": human_reason_zh,
        "expected_change_zh": expected_change_zh,
        "validation_commands": validation_commands,
        "rollback_plan_zh": rollback_plan_zh,
        "evidence_refs": proposal_payload.get("evidence_refs") or suggestion.get("evidence_refs") or [],
        "apply_execution_allowed": False,
        "raw_apply_target_allowed": False,
    }
    return narration, machine_diff


def build_payloads(database_dir: Path, dry_run: bool) -> tuple[dict[str, Any], dict[str, Any]]:
    config = read_json(database_dir / CONFIG_PATH)
    state_report = read_json(database_dir / STATE_MACHINE_REPORT_PATH)
    self_iteration = read_json(database_dir / SELF_ITERATION_PATH)
    validate_config(config)

    as_of = source_as_of(state_report, self_iteration)
    suggestions = self_iteration_by_proposal_id(self_iteration)
    narrations: list[dict[str, Any]] = []
    machine_diffs: list[dict[str, Any]] = []
    missing_sources: list[str] = []

    for proposal in state_report.get("proposals") or []:
        if not isinstance(proposal, dict):
            continue
        proposal_id = str(proposal.get("proposal_id"))
        suggestion = suggestions.get(proposal_id)
        if not suggestion:
            missing_sources.append(proposal_id)
            continue
        narration, machine_diff = build_narration(proposal, suggestion)
        narrations.append(narration)
        machine_diffs.append(machine_diff)

    all_have_sections = all(all(narration.get(section) for section in REQUIRED_HUMAN_SECTIONS) for narration in narrations)
    machine_diff_kept_out = all(narration.get("machine_diff_inline_in_human_summary") is False for narration in narrations)
    apply_execution = any(narration.get("apply_execution_allowed") is not False for narration in narrations)
    raw_mutation = any(narration.get("raw_apply_target_allowed") is not False for narration in narrations)

    output = {
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": STATUS,
        "contract_version": CONTRACT_VERSION,
        "dry_run": dry_run,
        "writes_files": not dry_run,
        "applies_proposals": False,
        "raw_mutation": False,
        "as_of": isoformat_z(as_of),
        "config_path": str(CONFIG_PATH),
        "source_reports": [str(STATE_MACHINE_REPORT_PATH), str(SELF_ITERATION_PATH)],
        "output_path": str(OUTPUT_PATH),
        "machine_diff_evidence_path": str(MACHINE_DIFF_PATH),
        "human_homepage_policy": {
            "no_full_machine_diff": True,
            "summary_only": True,
        },
        "required_human_sections": REQUIRED_HUMAN_SECTIONS,
        "narrations": narrations,
        "summary": {
            "narration_count": len(narrations),
            "machine_diff_count": len(machine_diffs),
            "missing_source_count": len(missing_sources),
            "missing_sources": missing_sources,
            "all_narrations_have_required_sections": all_have_sections,
            "machine_diff_kept_out_of_human_homepage": machine_diff_kept_out,
            "proposal_apply_execution": apply_execution,
            "raw_mutation": raw_mutation,
        },
        "output_contract": {
            "report": str(OUTPUT_PATH),
            "machine_diff_evidence": str(MACHINE_DIFF_PATH),
            "machine_config": str(CONFIG_PATH),
            "next_phase": "S13 P3",
        },
        "phase_boundary": {
            "does_not_apply_proposals": True,
            "does_not_modify_raw": True,
            "does_not_upload_github_main": True,
            "does_not_push_remote": True,
            "does_not_execute_rollback": True,
            "next_phase": "S13 P3",
        },
    }

    machine = {
        "schema_version": MACHINE_DIFF_SCHEMA_VERSION,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": STATUS,
        "contract_version": CONTRACT_VERSION,
        "as_of": isoformat_z(as_of),
        "source_reports": [str(STATE_MACHINE_REPORT_PATH), str(SELF_ITERATION_PATH)],
        "machine_diffs": machine_diffs,
        "summary": {
            "machine_diff_count": len(machine_diffs),
            "full_machine_diff_kept_out_of_human_homepage": True,
            "proposal_apply_execution": False,
            "raw_mutation": False,
        },
    }
    return output, machine


def write_json_if_changed(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if not path.exists() or path.read_text(encoding="utf-8") != serialized:
        path.write_text(serialized, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build Memory Atlas S13 P2 diff narrator report.")
    parser.add_argument("--database-dir", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    database_dir = args.database_dir.resolve()
    output, machine = build_payloads(database_dir, dry_run=args.dry_run)
    if not args.dry_run:
        write_json_if_changed(database_dir / OUTPUT_PATH, output)
        write_json_if_changed(database_dir / MACHINE_DIFF_PATH, machine)
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

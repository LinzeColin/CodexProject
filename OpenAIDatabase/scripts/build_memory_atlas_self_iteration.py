#!/usr/bin/env python3
"""Build Memory Atlas S09 P2 self-iteration suggestions with proposal expiry."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = Path("机器治理/行为智能模型/self_iteration.v1_2_s09_p2.json")
LATENT_PATH = Path("data/derived/behavior_intelligence/latent_signals.json")
OUTPUT_PATH = Path("data/derived/behavior_intelligence/self_iteration_suggestions.json")
TASK_ID = "MA-V12-S09P2"
ACCEPTANCE_ID = "ACC-MA-V12-S09P2"
STATUS = "phase_s09_p2_self_iteration_completed_pending_s09_p3"
REQUIRED_FIELDS = {
    "suggestion_id",
    "target_type",
    "target_files",
    "rationale_zh",
    "expected_change_zh",
    "evidence_refs",
    "proposal",
    "action_half_life_days",
}


class SelfIterationBuildError(RuntimeError):
    pass


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def to_iso(value: datetime) -> str:
    return value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stable_hash(value: str, length: int = 12) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:length]


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def load_json(path: Path, label: str) -> dict[str, Any]:
    if not path.exists():
        raise SelfIterationBuildError(f"{label} missing: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SelfIterationBuildError(f"{label} must be a JSON object: {path}")
    return payload


def unique_evidence_refs(items: list[dict[str, Any]], limit: int = 8) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in items:
        for key in ("supporting_evidence_refs", "contradicting_evidence_refs", "evidence_refs"):
            for ref in as_list(item.get(key)):
                if not isinstance(ref, dict):
                    continue
                ref_id = str(ref.get("ref_id") or json.dumps(ref, ensure_ascii=False, sort_keys=True))
                if ref_id in seen:
                    continue
                seen.add(ref_id)
                refs.append(ref)
                if len(refs) >= limit:
                    return refs
    return refs


def signal_by_claim_type(latent_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    signals = [item for item in as_list(latent_payload.get("latent_signals")) if isinstance(item, dict)]
    for signal in sorted(signals, key=lambda item: (-float(item.get("confidence") or 0), str(item.get("signal_id")))):
        claim_type = str(signal.get("claim_type") or "")
        result.setdefault(claim_type, signal)
    return result


def fallback_signal(latent_payload: dict[str, Any]) -> dict[str, Any]:
    signals = [item for item in as_list(latent_payload.get("latent_signals")) if isinstance(item, dict)]
    if not signals:
        raise SelfIterationBuildError("latent signals input has no signals")
    return sorted(signals, key=lambda item: (-float(item.get("confidence") or 0), str(item.get("signal_id"))))[0]


def suggestion_copy(target_type: str, signal: dict[str, Any]) -> tuple[str, str]:
    claim = str(signal.get("claim_zh") or "当前 latent signal")
    next_validation = str(signal.get("next_validation_zh") or "用下一次 run 验证是否有实际价值。")
    copy_by_target = {
        "memory": (
            f"把可恢复资产相关经验登记为候选记忆更新，先记录证据和恢复命令，不直接改全局记忆。",
            f"下一次交接时可更快恢复 {claim}，但只有通过复跑证据后才写入长期记忆。",
        ),
        "config": (
            "把重复流程收束为最小 dry-run/validator 候选，先保留 proposal，不直接改运行配置。",
            f"若 {next_validation} 成立，可减少重复操作；若不成立，proposal 到期后归档。",
        ),
        "AGENTS": (
            "把 run contract 边界经验转成 AGENTS/开发记录候选改动，先验证是否能减少越界。",
            "下一次同类 run 可更早锁定非目标列表，但不会在本 phase 改写 AGENTS。",
        ),
        "style": (
            "把质量上限经验转成文档风格候选，减少人类入口中过度分析术语和重复解释。",
            "人类页面应更短、更可读；若影响验收可追溯性，则不采纳。",
        ),
        "personalization": (
            "把讨论收口经验转成 personalization prompt 候选，帮助后续 agent 先问交付件和停止条件。",
            "后续对话可更快形成可验收产物；若没有复用价值，proposal 到期归档。",
        ),
    }
    return copy_by_target.get(target_type, ("生成自我迭代候选。", "等待后续验证。"))


def proposal_for(
    *,
    target: dict[str, Any],
    signal: dict[str, Any],
    suggestion_id: str,
    created_at: datetime,
    config: dict[str, Any],
    evidence_refs: list[dict[str, Any]],
) -> dict[str, Any]:
    expiry = config.get("proposal_expiry") if isinstance(config.get("proposal_expiry"), dict) else {}
    warn_days = int(expiry.get("warn_after_days") or 7)
    stale_days = int(expiry.get("stale_after_days") or 30)
    archive_days = int(expiry.get("archive_after_days") or 90)
    expires_after_days = int(expiry.get("expires_after_days") or stale_days)
    expires_at = created_at + timedelta(days=expires_after_days)
    proposal_state = config.get("proposal_state") if isinstance(config.get("proposal_state"), dict) else {}
    target_type = str(target["target_type"])
    target_files = [str(item) for item in as_list(target.get("target_files"))]
    return {
        "proposal_id": f"proposal_{stable_hash(suggestion_id)}",
        "state": str(proposal_state.get("initial_state") or "pending_human_review"),
        "created_at": to_iso(created_at),
        "expires_at": to_iso(expires_at),
        "warn_after_days": warn_days,
        "stale_after_days": stale_days,
        "archive_after_days": archive_days,
        "action_half_life_days": int(target.get("action_half_life_days") or 14),
        "target_type": target_type,
        "target_files": target_files,
        "human_reason_zh": f"来自 latent signal {signal.get('signal_id')} 的自我迭代候选；需要人类确认后才可转为 apply。",
        "before_after_diff": {
            "mode": "proposal_only_no_file_write",
            "before_zh": "当前 phase 不修改目标文件。",
            "after_zh": "若后续人类批准，再在对应 phase 生成最小 diff。",
        },
        "risk_level": "low" if target_type in {"style", "personalization"} else "medium",
        "rollback_plan_zh": "当前 phase 未写目标文件；若后续 proposal 被采纳，使用对应 commit 的 git revert 或 proposal rollback。",
        "validation_commands": [
            "python OpenAIDatabase/scripts/atlasctl.py audit --check self-iteration-safety",
            "pnpm --dir OpenAIDatabase/apps/memory-atlas run validate:v1.2-s09-p2",
        ],
        "evidence_refs": evidence_refs[:5],
        "requires_human_approval_before_apply": True,
        "apply_execution_allowed": False,
        "raw_apply_target_allowed": False,
        "not_permanent_pending": True,
    }


def make_suggestion(target: dict[str, Any], signal: dict[str, Any], created_at: datetime, config: dict[str, Any]) -> dict[str, Any]:
    target_type = str(target["target_type"])
    suggestion_zh, expected_change_zh = suggestion_copy(target_type, signal)
    suggestion_id = f"self_iter_{target_type.lower()}_{stable_hash(str(signal.get('signal_id')) + target_type)}"
    evidence_refs = unique_evidence_refs([signal], limit=8)
    if not evidence_refs:
        raise SelfIterationBuildError(f"suggestion {suggestion_id} missing evidence refs")
    proposal = proposal_for(
        target=target,
        signal=signal,
        suggestion_id=suggestion_id,
        created_at=created_at,
        config=config,
        evidence_refs=evidence_refs,
    )
    return {
        "suggestion_id": suggestion_id,
        "target_type": target_type,
        "target_files": [str(item) for item in as_list(target.get("target_files"))],
        "source_signal_ids": [str(signal.get("signal_id"))],
        "source_claim_type": signal.get("claim_type"),
        "suggestion_zh": suggestion_zh,
        "rationale_zh": str(signal.get("claim_zh") or suggestion_zh),
        "expected_change_zh": expected_change_zh,
        "action_half_life_days": int(target.get("action_half_life_days") or 14),
        "action_half_life": {
            "starts_at": to_iso(created_at),
            "half_life_days": int(target.get("action_half_life_days") or 14),
            "interpretation_zh": "超过半衰期仍未被验证或采纳时，先降低优先级，不转成压力清单。",
        },
        "evidence_refs": evidence_refs,
        "proposal": proposal,
        "not_pressure_list": True,
        "not_applied": True,
    }


def validate_config(config: dict[str, Any]) -> None:
    if config.get("task_id") != TASK_ID or config.get("acceptance_id") != ACCEPTANCE_ID:
        raise SelfIterationBuildError("self-iteration config identity mismatch")
    configured_fields = set(as_list(config.get("required_suggestion_fields")))
    missing = sorted(REQUIRED_FIELDS - configured_fields)
    if missing:
        raise SelfIterationBuildError(f"self-iteration config missing fields: {', '.join(missing)}")
    targets = [item for item in as_list(config.get("suggestion_targets")) if isinstance(item, dict)]
    target_types = {str(item.get("target_type")) for item in targets}
    required_targets = {"memory", "config", "AGENTS", "style", "personalization"}
    if not required_targets <= target_types:
        raise SelfIterationBuildError("self-iteration config missing required target types")
    expiry = config.get("proposal_expiry") if isinstance(config.get("proposal_expiry"), dict) else {}
    if int(expiry.get("expires_after_days") or 0) <= 0:
        raise SelfIterationBuildError("proposal expiry must be positive")
    boundary = config.get("scope_boundary") if isinstance(config.get("scope_boundary"), dict) else {}
    if boundary.get("raw_mutation") is not False:
        raise SelfIterationBuildError("S09 P2 must not mutate raw")
    if boundary.get("proposal_apply_execution") is not False:
        raise SelfIterationBuildError("S09 P2 must not apply proposals")
    if boundary.get("decision_debt_ledger") != "deferred_to_s09_p3":
        raise SelfIterationBuildError("S09 P2 must defer decision debt ledger to S09 P3")


def validate_inputs(latent_payload: dict[str, Any]) -> None:
    if latent_payload.get("task_id") != "MA-V12-S09P1" or latent_payload.get("acceptance_id") != "ACC-MA-V12-S09P1":
        raise SelfIterationBuildError("latent signal input identity mismatch")
    if not as_list(latent_payload.get("latent_signals")):
        raise SelfIterationBuildError("latent signal input has no signals")


def validate_suggestion(item: dict[str, Any], config: dict[str, Any]) -> list[str]:
    bad_items: list[str] = []
    suggestion_id = item.get("suggestion_id")
    for field in REQUIRED_FIELDS:
        if item.get(field) in (None, "", []):
            bad_items.append(f"{suggestion_id}:missing_{field}")
    if int(item.get("action_half_life_days") or 0) <= 0:
        bad_items.append(f"{suggestion_id}:invalid_action_half_life")
    if item.get("not_pressure_list") is not True:
        bad_items.append(f"{suggestion_id}:pressure_list_boundary_missing")
    if item.get("not_applied") is not True:
        bad_items.append(f"{suggestion_id}:applied_in_current_phase")
    target_files = [str(file) for file in as_list(item.get("target_files"))]
    blocked_targets = [str(target) for target in as_list(config.get("blocked_targets"))]
    if any(blocked in file for blocked in blocked_targets for file in target_files):
        bad_items.append(f"{suggestion_id}:blocked_target")
    proposal = item.get("proposal") if isinstance(item.get("proposal"), dict) else {}
    for field in ["proposal_id", "state", "created_at", "expires_at", "rollback_plan_zh", "validation_commands"]:
        if proposal.get(field) in (None, "", []):
            bad_items.append(f"{suggestion_id}:proposal_missing_{field}")
    if proposal.get("state") != "pending_human_review":
        bad_items.append(f"{suggestion_id}:proposal_state_not_pending_human_review")
    if proposal.get("apply_execution_allowed") is not False:
        bad_items.append(f"{suggestion_id}:proposal_apply_allowed")
    if proposal.get("raw_apply_target_allowed") is not False:
        bad_items.append(f"{suggestion_id}:proposal_raw_apply_allowed")
    if proposal.get("not_permanent_pending") is not True:
        bad_items.append(f"{suggestion_id}:proposal_permanent_pending")
    try:
        created = parse_utc(str(proposal.get("created_at")))
        expires = parse_utc(str(proposal.get("expires_at")))
        if expires <= created:
            bad_items.append(f"{suggestion_id}:proposal_expiry_not_after_created")
    except (TypeError, ValueError):
        bad_items.append(f"{suggestion_id}:proposal_expiry_invalid")
    return bad_items


def validate_payload(payload: dict[str, Any], config: dict[str, Any]) -> None:
    if payload.get("task_id") != TASK_ID or payload.get("acceptance_id") != ACCEPTANCE_ID:
        raise SelfIterationBuildError("self-iteration payload identity mismatch")
    if payload.get("status") != STATUS:
        raise SelfIterationBuildError("self-iteration payload status mismatch")
    suggestions = [item for item in as_list(payload.get("self_iteration_suggestions")) if isinstance(item, dict)]
    if len(suggestions) < 5:
        raise SelfIterationBuildError("self-iteration payload must contain at least five suggestions")
    bad_items: list[str] = []
    for suggestion in suggestions:
        bad_items.extend(validate_suggestion(suggestion, config))
    boundary = payload.get("phase_boundary") if isinstance(payload.get("phase_boundary"), dict) else {}
    if boundary.get("does_not_apply_proposals") is not True:
        bad_items.append("phase_boundary:proposal_apply_missing")
    if boundary.get("does_not_create_decision_debt_ledger") is not True:
        bad_items.append("phase_boundary:decision_debt_not_deferred")
    if boundary.get("does_not_modify_raw") is not True:
        bad_items.append("phase_boundary:raw_mutation_missing")
    if boundary.get("next_phase") != "S09 P3":
        bad_items.append("phase_boundary:next_phase_not_s09p3")
    if bad_items:
        raise SelfIterationBuildError("; ".join(bad_items))


def build_self_iteration_suggestions(
    database_dir: Path,
    *,
    dry_run: bool = False,
    generated_at: str | None = None,
    output_path: Path = OUTPUT_PATH,
    config_path: Path = CONFIG_PATH,
    latent_path: Path = LATENT_PATH,
) -> dict[str, Any]:
    database_dir = database_dir.resolve()
    config = load_json(database_dir / config_path, "self-iteration config")
    latent_payload = load_json(database_dir / latent_path, "latent signals")
    validate_config(config)
    validate_inputs(latent_payload)
    created_at = parse_utc(generated_at or now_utc())
    signals_by_type = signal_by_claim_type(latent_payload)
    default_signal = fallback_signal(latent_payload)
    suggestions: list[dict[str, Any]] = []
    for target in as_list(config.get("suggestion_targets")):
        if not isinstance(target, dict):
            continue
        signal = signals_by_type.get(str(target.get("signal_claim_type"))) or default_signal
        suggestions.append(make_suggestion(target, signal, created_at, config))
    target_types = sorted({item["target_type"] for item in suggestions})
    payload: dict[str, Any] = {
        "schema_version": "memory_atlas_self_iteration.v1_2_s09_p2",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": STATUS,
        "generated_at": to_iso(created_at),
        "dry_run": dry_run,
        "writes_files": not dry_run,
        "config_path": config_path.as_posix(),
        "output_path": output_path.as_posix(),
        "input_paths": [latent_path.as_posix()],
        "input_task_ids": {"latent_signals": latent_payload.get("task_id")},
        "suggestion_count": len(suggestions),
        "target_types": target_types,
        "self_iteration_suggestions": suggestions,
        "proposal_expiry_summary": {
            "all_proposals_have_expiry": all(bool(item.get("proposal", {}).get("expires_at")) for item in suggestions),
            "all_suggestions_have_action_half_life": all(int(item.get("action_half_life_days") or 0) > 0 for item in suggestions),
            "warn_after_days": int(config["proposal_expiry"]["warn_after_days"]),
            "stale_after_days": int(config["proposal_expiry"]["stale_after_days"]),
            "archive_after_days": int(config["proposal_expiry"]["archive_after_days"]),
            "permanent_pending_allowed": False,
        },
        "phase_boundary": {
            "does_not_apply_proposals": True,
            "requires_human_approval_before_apply": True,
            "does_not_modify_raw": True,
            "does_not_upload_github_main": True,
            "does_not_create_decision_debt_ledger": True,
            "decision_debt_ledger_deferred_to": "S09 P3",
            "does_not_output_psychological_diagnosis": True,
            "does_not_output_personality_label": True,
            "next_phase": "S09 P3",
        },
    }
    validate_payload(payload, config)
    if not dry_run:
        output = database_dir / output_path
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Memory Atlas S09 P2 self-iteration suggestion builder.")
    parser.add_argument("--database-dir", type=Path, default=ROOT)
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    parser.add_argument("--latent", type=Path, default=LATENT_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        payload = build_self_iteration_suggestions(
            args.database_dir,
            dry_run=args.dry_run,
            output_path=args.output,
            config_path=args.config,
            latent_path=args.latent,
        )
    except SelfIterationBuildError as exc:
        print(json.dumps({
            "status": "FAIL",
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "reason": str(exc),
            "writes_files": False,
        }, ensure_ascii=False, indent=2, sort_keys=True))
        return 2
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

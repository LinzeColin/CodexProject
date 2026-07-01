#!/usr/bin/env python3
"""Generate Review 8 governance views from canonical machine sources."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import validate_project_governance as structural


sys.dont_write_bytecode = True

ROOT = structural.ROOT
GENERATOR_VERSION = "4.0.0"
COMPLETED_TASK_STATES = {"completed", "rejected", "deprecated"}
EXECUTABLE_TASK_STATES = {"ready", "in_progress", "blocked", "planned"}
ASSURANCE_STATUSES = {"VERIFIED", "PARTIAL", "UNVERIFIED", "FAILED", "NOT_APPLICABLE"}
PROJECT_REPOSITORIES = {
    "Alpha": "https://github.com/LinzeColin/Alpha",
    "EEI": "https://github.com/LinzeColin/CodexProject/tree/main/EEI",
    "EVA_OS": "https://github.com/LinzeColin/EVA_OS",
    "FIFA": "https://github.com/LinzeColin/FIFA",
    "OpMe_System": "https://github.com/LinzeColin/OpMe_System",
    "OpenAIDatabase": "https://github.com/LinzeColin/CodexProject/tree/main/OpenAIDatabase",
    "PFI_BIG_DATA_SIMULATOR": "https://github.com/LinzeColin/CodexProject/tree/main/PFI/%E5%A4%A7%E6%95%B0%E6%8D%AE%E6%A8%A1%E6%8B%9F%E5%99%A8",
    "Serenity-Alipay": "https://github.com/LinzeColin/Serenity-Alipay",
    "whkmSalary": "https://github.com/LinzeColin/whkmSalary",
    "arxiv-daily-push": "https://github.com/LinzeColin/CodexProject/tree/main/arxiv-daily-push",
}


ASSURANCE_POLICY = {
    "Alpha": {
        "empirical": "unknown",
        "operational": "blocked",
        "readiness": "blocked",
        "decision": "是否提供生产数据、paper broker 与 live execution policy 证据，或继续保持 blocked。",
        "blockers": ["production validation evidence", "broker policy decision", "calibration evidence"],
    },
    "EEI": {
        "empirical": "partial",
        "operational": "partial",
        "readiness": "blocked",
        "decision": "是否继续 24 小时 operator soak；当前 4 小时证据只支持 partial。",
        "blockers": ["24h operator soak evidence", "historical event binding backlog"],
    },
    "EVA_OS": {
        "empirical": "unknown",
        "operational": "blocked",
        "readiness": "blocked",
        "decision": "是否投入 137 个 remaining parameter reviews 和来源/校准证据。",
        "blockers": ["parameter review backlog", "source and calibration evidence"],
    },
    "FIFA": {
        "empirical": "unknown",
        "operational": "blocked",
        "readiness": "conditional",
        "decision": "是否关闭 17 个 parser/validation 参数人工复核。",
        "blockers": ["17 active parameters need semantic review", "TAB production evidence not claimed"],
    },
    "OpMe_System": {
        "empirical": "unknown",
        "operational": "blocked",
        "readiness": "conditional",
        "decision": "是否补齐 calibration、prompt/provider policy 与 owner sign-off 证据。",
        "blockers": ["calibration evidence", "prompt/provider policy", "owner sign-off"],
    },
    "OpenAIDatabase": {
        "empirical": "unknown",
        "operational": "blocked",
        "readiness": "blocked",
        "decision": "是否继续补齐 memory routing 分支和 FORM-010 语义复核。",
        "blockers": ["remaining semantic review", "calibration/source evidence"],
    },
    "PFI_BIG_DATA_SIMULATOR": {
        "empirical": "unknown",
        "operational": "blocked",
        "readiness": "conditional",
        "decision": "是否关闭 PARAM-110/PARAM-111 或保留 human review required。",
        "blockers": ["two implementation parameters need review", "calibration evidence"],
    },
    "Serenity-Alipay": {
        "empirical": "unknown",
        "operational": "partial",
        "readiness": "conditional",
        "decision": "是否启动 empirical calibration evidence task；实现一致性已经 machine verified。",
        "blockers": ["empirical calibration unknown", "owner evidence decision"],
    },
    "whkmSalary": {
        "empirical": "unknown",
        "operational": "blocked",
        "readiness": "blocked",
        "decision": "是否提供一手政策、法域、生效日期、计税基础和舍入证据。",
        "blockers": ["policy source evidence", "jurisdiction/effective date evidence"],
    },
    "arxiv-daily-push": {
        "empirical": "partial",
        "operational": "partial",
        "readiness": "blocked",
        "decision": "是否启动生产 trial；当前只有本地两日模拟，生产启动和 30 天验收仍 blocked。",
        "blockers": ["production trial not started", "30-day acceptance absent", "historical event binding backlog"],
    },
}


REVIEW8_DECISION_POLICY_PATH = ROOT / "governance" / "decision_policies" / "review8_owner_decision_policy.json"


def load_review8_decision_policy() -> dict[str, Any]:
    return json.loads(REVIEW8_DECISION_POLICY_PATH.read_text(encoding="utf-8"))


REVIEW8_DECISION_POLICY = load_review8_decision_policy()


def decision_policy_for(project_id: str, next_task: dict[str, Any]) -> dict[str, Any]:
    policy = dict(REVIEW8_DECISION_POLICY.get("project_policies", {}).get(project_id, {}))
    task_id = str(next_task.get("task_id") or "")
    task_override = (
        REVIEW8_DECISION_POLICY.get("task_overrides", {})
        .get(project_id, {})
        .get(task_id, {})
    )
    if isinstance(task_override, dict):
        policy.update(task_override)
    return policy


def adp_s2pmt07_blocked_next_task(
    stale_candidates: list[dict[str, str]] | None = None,
    matrix: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Keep ADP's owner-visible next action pinned to the V7.2 final gate."""

    matrix = matrix or {}
    current_iteration = str(matrix.get("current_iteration") or "")
    current_gate = str(matrix.get("current_gate") or "")
    current_alias = str(matrix.get("current_v7_legacy_alias") or "")
    final_bundle_chain_ready = (
        "POST-FINAL-BUNDLE-CURRENT-STATE-SYNC" in current_iteration
        or "POST_FINAL_BUNDLE_CURRENT_STATE_SYNC" in current_gate
        or "FINAL_ACCEPTANCE_BUNDLE_READY_NO_PRODUCTION_ACCEPTANCE" in current_gate
        or "final bundle artifact chain complete" in current_alias.lower()
    )
    production_boundary_preflight_ready = (
        "INTEGRATED-PRODUCTION-ACCEPTANCE-PREFLIGHT" in current_iteration
        or "INTEGRATED_PRODUCTION_ACCEPTANCE_PREFLIGHT" in current_gate
        or "INTEGRATED-PRODUCTION-ACCEPTANCE-WRITE-GATE" in current_iteration
        or "INTEGRATED_PRODUCTION_ACCEPTANCE_WRITE_GATE" in current_gate
        or "production-boundary preflight passed" in current_alias.lower()
        or "write-gate precheck" in current_alias.lower()
    )
    owner_decision_recorded_write_gate_allowed = (
        "WRITE_GATE_ALLOWED" in current_gate
        or "owner_production_boundary_decision_recorded=true" in current_alias
        or "acceptance_write_gate_allowed=true" in current_alias
    )
    integrated_production_accepted_no_daily_operation = (
        bool(matrix.get("stage2_integrated_production_accepted", False))
        or "INTEGRATED_PRODUCTION_ACCEPTED" in current_gate
        or "integrated_production_accepted=true" in current_alias
    ) and not bool(matrix.get("s2pmt07_daily_operation_enabled", False))
    daily_operation_preflight_current = (
        "DAILY-OPERATION-AUTHORIZATION-PREFLIGHT" in current_iteration
        or "DAILY_OPERATION_AUTHORIZATION_PREFLIGHT" in current_gate
        or "daily operation authorization preflight" in current_alias.lower()
    )
    daily_operation_owner_decision_keep_disabled = (
        "DAILY-OPERATION-OWNER-DECISION-KEEP-DISABLED" in current_iteration
        or "DAILY_OPERATION_OWNER_DECISION_RECORDED_KEEP_DISABLED" in current_gate
        or "keep_daily_operation_disabled_no_persistent_authorization" in current_alias
    )
    daily_operation_persistent_authorization_missing = (
        "DAILY-OPERATION-PERSISTENT-AUTHORIZATION-GATE" in current_iteration
        or "DAILY_OPERATION_PERSISTENT_AUTHORIZATION_MISSING" in current_gate
        or "persistent_daily_operation_authorization_missing" in current_alias
    )
    daily_operation_persistent_authorization_request_ready = (
        "DAILY-OPERATION-PERSISTENT-AUTHORIZATION-REQUEST" in current_iteration
        or "DAILY_OPERATION_PERSISTENT_AUTHORIZATION_REQUEST_READY" in current_gate
        or "daily_operation_persistent_enablement_authorization.request.json" in current_alias
    )
    daily_operation_blockers = str(matrix.get("s2pmt07_daily_operation_authorization_preflight_blockers") or "")
    daily_operation_preflight_passed = bool(
        matrix.get("s2pmt07_daily_operation_authorization_preflight_passed", False)
    )
    daily_operation_gh_equivalent_repaired = (
        "github_open_pr_count_zero_api_v1" in current_alias
        or (
            "missing_gh_cli" not in daily_operation_blockers
            and "missing_smtp_secret_env_names" in daily_operation_blockers
        )
    )
    controlled_real_run_rechecked = (
        "controlled foreground real-run acceptance recheck passed" in current_alias.lower()
        or "duplicate_smtp_send_avoided=true" in current_alias
    )
    completion_report_is_next = (
        "S2PLT04-COMPLETION-REPORT" in current_iteration
        or "S2PLT04_COMPLETION_REPORT" in current_gate
        or "S2PLT04 report" in current_alias
    )
    explicit_s2plt02_terminal_current = (
        "S2PLT02-TERMINAL" in current_iteration
        or "S2PLT02_TERMINAL" in current_gate
        or "S2PLT02-REAL-DELIVERY-MANIFEST" in current_iteration
        or "S2PLT02_REAL_DELIVERY_MANIFEST" in current_gate
    )
    terminal_delivery_proof_is_next = (
        "S2PLT02-TERMINAL-DELIVERY-PROOF" in current_iteration
        or "S2PLT02-TERMINAL-CAPTURE-WINDOW-RUNTIME-STATE-SYNC" in current_iteration
        or "S2PLT02_TERMINAL_DELIVERY_PROOF" in current_gate
        or "S2PLT02_TERMINAL_CAPTURE_WINDOW_RUNTIME_STATE_SYNC" in current_gate
        or "S2PLT02 terminal delivery proof" in current_alias
        or "terminal proof" in current_alias
        or "LATEST-NONTERMINAL-EVIDENCE-SYNC" in current_iteration
        or "LATEST_NONTERMINAL_EVIDENCE_SYNC" in current_gate
    )
    s2plt02_terminal_delivery_accepted = (
        "S2PLT02_TERMINAL_DELIVERY_PROOF_READY" in current_gate
        or "S2PLT02 terminal delivery proof artifact passed" in current_alias
        or "S2PLT02 terminal delivery proof accepted" in current_alias
    )
    s2plt03_terminal_resilience_accepted = (
        "S2PLT03_TERMINAL_RESILIENCE_PROOF_READY" in current_gate
        or "S2PLT03 terminal resilience proof artifact passed" in current_alias
        or "S2PLT03 terminal resilience proof accepted" in current_alias
    )
    terminal_resilience_proof_is_next = (
        s2plt02_terminal_delivery_accepted
        or "S2PLT03-TERMINAL-RESILIENCE-PROOF" in current_iteration
        or "S2PLT03_TERMINAL_RESILIENCE_PROOF" in current_gate
        or "S2PLT03 terminal resilience proof" in current_alias
    )
    real_proof_capture_is_next = (
        "S2PLT02-REAL-PROOF-CAPTURE" in current_iteration
        or "S2PLT02_REAL_PROOF_CAPTURE" in current_gate
        or "real-proof capture" in current_alias
        or "real proof capture" in current_alias
    )
    if daily_operation_persistent_authorization_request_ready:
        return {
            "task_id": "S2PMT07-DAILY-OPERATION-PERSISTENT-ENABLEMENT-AUTHORIZATION",
            "status": "blocked",
            "reason": (
                "Persistent DAILY_OPERATION authorization request packet is ready, but it is request-only. "
                "FINAL_ACCEPTANCE_BUNDLE/daily_operation_persistent_enablement_authorization.json still "
                "does not exist, so runtime remains disabled."
            ),
            "acceptance_ids": ["ACC-S2PMT07-FINAL-REVIEW", "ACC-S2PL-DAILY-OPERATION-AUTHORIZATION"],
            "owner": "content_owner + engineering_owner",
            "human_owner_role": "content_owner + engineering_owner",
            "unblock_condition": (
                "Owner must either keep DAILY_OPERATION disabled or create a separate explicit persistent "
                "DAILY_OPERATION authorization artifact, then run the persistent authorization gate and a "
                "separate enablement preflight while SMTP, scheduler, Release, restore, and DAILY_OPERATION "
                "remain disabled until those gates pass."
            ),
            "stale_candidates": stale_candidates or [],
        }
    if daily_operation_persistent_authorization_missing:
        return {
            "task_id": "S2PMT07-DAILY-OPERATION-PERSISTENT-ENABLEMENT-AUTHORIZATION",
            "status": "blocked",
            "reason": (
                "Persistent DAILY_OPERATION authorization gate has run and is blocked because "
                "FINAL_ACCEPTANCE_BUNDLE/daily_operation_persistent_enablement_authorization.json "
                "does not exist. Runtime remains disabled."
            ),
            "acceptance_ids": ["ACC-S2PMT07-FINAL-REVIEW", "ACC-S2PL-DAILY-OPERATION-AUTHORIZATION"],
            "owner": "content_owner + engineering_owner",
            "human_owner_role": "content_owner + engineering_owner",
            "unblock_condition": (
                "Provide a new explicit owner persistent DAILY_OPERATION authorization artifact, "
                "then run a separate enablement preflight while keeping SMTP, scheduler, Release, "
                "restore, and DAILY_OPERATION disabled until that gate passes."
            ),
            "stale_candidates": stale_candidates or [],
        }
    if daily_operation_owner_decision_keep_disabled:
        return {
            "task_id": "S2PMT07-DAILY-OPERATION-PERSISTENT-ENABLEMENT-AUTHORIZATION",
            "status": "blocked",
            "reason": (
                "DAILY_OPERATION owner decision is recorded as keep-disabled. Persistent "
                "DAILY_OPERATION is not authorized; runtime remains disabled until a separate "
                "explicit owner authorization and enablement artifact exists."
            ),
            "acceptance_ids": ["ACC-S2PMT07-FINAL-REVIEW", "ACC-S2PL-DAILY-OPERATION-AUTHORIZATION"],
            "owner": "content_owner + engineering_owner",
            "human_owner_role": "content_owner + engineering_owner",
            "unblock_condition": (
                "Provide explicit owner authorization for persistent DAILY_OPERATION in a new "
                "artifact, then run a separate enablement gate. Do not enable SMTP, scheduler, "
                "Release, restore, or persistent operation from the keep-disabled decision."
            ),
            "stale_candidates": stale_candidates or [],
        }
    if daily_operation_preflight_current:
        if daily_operation_preflight_passed:
            return {
                "task_id": "S2PMT07-DAILY-OPERATION-OWNER-AUTHORIZATION-DECISION",
                "status": "blocked",
                "reason": (
                    "DAILY_OPERATION authorization preflight technical checks now pass after "
                    "reviewed GitHub open PR evidence, local-runner SMTP secret key-presence "
                    "evidence, and ADP-scoped git artifact hygiene. Runtime remains disabled; "
                    "the only remaining blocker is explicit owner authorization for persistent "
                    "DAILY_OPERATION, plus a separate enablement artifact if approved."
                ),
                "acceptance_ids": ["ACC-S2PMT07-FINAL-REVIEW", "ACC-S2PL-DAILY-OPERATION-AUTHORIZATION"],
                "owner": "content_owner + engineering_owner",
                "human_owner_role": "content_owner + engineering_owner",
                "unblock_condition": (
                    "Record explicit owner DAILY_OPERATION authorization or keep DAILY_OPERATION "
                    "disabled. Do not enable SMTP, scheduler, Release, restore, or persistent "
                    "operation from the preflight artifact alone."
                ),
                "stale_candidates": stale_candidates or [],
            }
        blocker_summary = (
            "The reviewed GitHub open PR count equivalent has cleared the gh CLI blocker; "
            "the remaining production preflight blockers are missing SMTP secret env names "
            "and OpenAIDatabase session-history archive git artifact hygiene violations."
            if daily_operation_gh_equivalent_repaired
            else (
                "The remaining production preflight blockers are missing gh CLI availability, "
                "missing SMTP secret env names, and OpenAIDatabase session-history archive "
                "git artifact hygiene violations."
            )
        )
        unblock_condition = (
            "Provide required SMTP secret environment names without logging secret values, "
            "and resolve OpenAIDatabase session-history archive git artifact hygiene "
            "violations. Maintain github_open_pr_count_zero_api_v1 evidence, "
            "open_pr_count=0, ADP_ALLOW_SMTP_SEND=false, LaunchAgents disabled, and "
            "FINAL_ACCEPTANCE_BUNDLE/integrated_production_acceptance.json evidence. Then "
            "rerun daily-operation authorization preflight; runtime remains disabled."
            if daily_operation_gh_equivalent_repaired
            else (
                "Make the production preflight pass: provide required runtime command "
                "availability or reviewed equivalent, required SMTP secret environment names "
                "without logging secret values, and resolve OpenAIDatabase session-history "
                "archive git artifact hygiene violations. Maintain open_pr_count=0, "
                "ADP_ALLOW_SMTP_SEND=false, LaunchAgents disabled, and "
                "FINAL_ACCEPTANCE_BUNDLE/integrated_production_acceptance.json evidence. "
                "Then rerun daily-operation authorization preflight; runtime remains disabled."
            )
        )
        next_task_id = (
            "S2PMT07-DAILY-OPERATION-PREFLIGHT-SECRET-AND-ARTIFACT-REPAIR"
            if daily_operation_gh_equivalent_repaired
            else "S2PMT07-DAILY-OPERATION-AUTHORIZATION-PREFLIGHT"
        )
        return {
            "task_id": next_task_id,
            "status": "blocked",
            "reason": (
                "DAILY_OPERATION authorization preflight has been run after "
                "INTEGRATED_PRODUCTION_ACCEPTED, but it remains blocked by the "
                f"nested production preflight. {blocker_summary} "
                "Repair the production preflight blockers before requesting persistent DAILY_OPERATION authorization. "
                "Current boundary evidence remains open_pr_count=0, "
                "ADP_ALLOW_SMTP_SEND=false, LaunchAgents disabled, and "
                "FINAL_ACCEPTANCE_BUNDLE/integrated_production_acceptance.json present."
            ),
            "acceptance_ids": ["ACC-S2PMT07-FINAL-REVIEW", "ACC-S2PL-DAILY-OPERATION-AUTHORIZATION"],
            "owner": "content_owner + engineering_owner + independent_final_reviewer",
            "human_owner_role": "content_owner + engineering_owner + independent_final_reviewer",
            "unblock_condition": unblock_condition,
            "stale_candidates": stale_candidates or [],
        }
    if integrated_production_accepted_no_daily_operation:
        return {
            "task_id": "S2PMT07-DAILY-OPERATION-AUTHORIZATION-PREFLIGHT",
            "status": "blocked",
            "reason": (
                "INTEGRATED_PRODUCTION_ACCEPTED evidence is written for Stage 2, "
                "but DAILY_OPERATION remains disabled. The next action is a separate "
                "owner authorization and safety preflight for daily operation; SMTP, "
                "scheduler, Release, and restore remain disabled until that preflight passes."
            ),
            "acceptance_ids": ["ACC-S2PMT07-FINAL-REVIEW", "ACC-S2PL-INTEGRATED-PRODUCTION"],
            "owner": "content_owner + engineering_owner + independent_final_reviewer",
            "human_owner_role": "content_owner + engineering_owner + independent_final_reviewer",
            "unblock_condition": (
                "Record explicit DAILY_OPERATION authorization, prove disabled runtime flags, "
                "run the daily-operation preflight, and only then consider persistent operation enablement."
            ),
            "stale_candidates": stale_candidates or [],
        }
    if owner_decision_recorded_write_gate_allowed:
        return {
            "task_id": "S2PMT07-INTEGRATED-PRODUCTION-ACCEPTANCE-EVIDENCE-WRITE",
            "status": "blocked",
            "reason": (
                "Owner production-boundary decision evidence is recorded and the final "
                "acceptance write gate is allowed only for evidence writing. Runtime "
                "enablement remains forbidden: SMTP, scheduler, Release, restore, and "
                "DAILY_OPERATION stay disabled until separately validated."
            ),
            "acceptance_ids": ["ACC-S2PMT07-FINAL-REVIEW", "ACC-S2PL-INTEGRATED-PRODUCTION"],
            "owner": "content_owner + engineering_owner + independent_final_reviewer",
            "human_owner_role": "content_owner + engineering_owner + independent_final_reviewer",
            "unblock_condition": (
                "Write and validate INTEGRATED_PRODUCTION_ACCEPTED evidence through the "
                "final gate without enabling runtime production or changing public schema, "
                "DB, source adapters, ranking, queues, or V7 contracts."
            ),
            "stale_candidates": stale_candidates or [],
        }
    if production_boundary_preflight_ready:
        controlled_run_clause = (
            " Owner-authorized controlled foreground real-run acceptance recheck passed "
            "without duplicate SMTP and with persistent ADP_ALLOW_SMTP_SEND=false; this is "
            "evidence, not DAILY_OPERATION."
            if controlled_real_run_rechecked
            else ""
        )
        return {
            "task_id": "S2PMT07-INTEGRATED-PRODUCTION-ACCEPTANCE-OWNER-DECISION",
            "status": "blocked",
            "reason": (
                "The S2PMT07 production-boundary preflight checks passed with final bundle ready, "
                "owner decision packet ready, acceptance write-gate precheck blocked correctly, "
                "open_pr_count=0, ADP_ALLOW_SMTP_SEND=false, LaunchAgents disabled, and no background "
                "ADP process."
                + controlled_run_clause
                + " The remaining action is owner production-boundary decision evidence "
                "before any INTEGRATED_PRODUCTION_ACCEPTED write or DAILY_OPERATION enablement."
            ),
            "acceptance_ids": ["ACC-S2PMT07-FINAL-REVIEW", "ACC-S2PL-INTEGRATED-PRODUCTION"],
            "owner": "content_owner + engineering_owner + independent_final_reviewer",
            "human_owner_role": "content_owner + engineering_owner + independent_final_reviewer",
            "unblock_condition": (
                "Record owner production-boundary decision evidence, then run the final acceptance "
                "write gate without enabling SMTP/scheduler/Release/restore automatically."
            ),
            "stale_candidates": stale_candidates or [],
        }
    if final_bundle_chain_ready:
        return {
            "task_id": "S2PMT07-INTEGRATED-PRODUCTION-ACCEPTANCE-PREFLIGHT",
            "status": "blocked",
            "reason": (
                "The S2PMT07 final acceptance bundle artifact chain is complete and "
                "validates with missing_items=[] while production acceptance remains false. "
                "The next action is a production-boundary preflight and owner decision, "
                "not rebuilding S2PLT04 or enabling SMTP/scheduler/Release automatically."
            ),
            "acceptance_ids": ["ACC-S2PMT07-FINAL-REVIEW", "ACC-S2PL-INTEGRATED-PRODUCTION"],
            "owner": "content_owner + engineering_owner + independent_final_reviewer",
            "human_owner_role": "content_owner + engineering_owner + independent_final_reviewer",
            "unblock_condition": (
                "Review the final bundle, no-production attestation, LaunchAgent disabled "
                "state, persistent ADP_ALLOW_SMTP_SEND=false state, and owner production "
                "boundary decision before writing INTEGRATED_PRODUCTION_ACCEPTED evidence."
            ),
            "stale_candidates": stale_candidates or [],
        }
    if completion_report_is_next or s2plt03_terminal_resilience_accepted:
        return {
            "task_id": "S2PMT07-S2PLT04-COMPLETION-REPORT",
            "status": "blocked",
            "reason": (
                "S2PLT01 terminal acceptance, S2PLT02 terminal delivery proof, "
                "S2PLT03 terminal resilience proof, independent reviewer assignment, "
                "and P0/P1 zero-proof artifacts are validated as no-production final-bundle "
                "inputs; S2PLT04 completion report is the next required blocked artifact "
                "before final command, handoff, signoff, manifest, or production acceptance can proceed."
            ),
            "acceptance_ids": ["ACC-S2PLT04-COMPLETION", "ACC-S2PMT07-FINAL-REVIEW"],
            "owner": "content_owner + engineering_owner + independent_final_reviewer",
            "human_owner_role": "content_owner + engineering_owner + independent_final_reviewer",
            "unblock_condition": (
                "Build, independently review, write, and validate "
                "FINAL_ACCEPTANCE_BUNDLE/s2plt04_completion_report.json without enabling "
                "SMTP, scheduler, Release, restore, public schema changes, or production acceptance."
            ),
            "stale_candidates": stale_candidates or [],
        }
    if terminal_resilience_proof_is_next:
        return {
            "task_id": "S2PLT03-TERMINAL-RESILIENCE-PROOF",
            "status": "blocked",
            "reason": (
                "S2PLT02 terminal delivery proof artifact is validated and ready "
                "as a no-production final-bundle input; the next blocked terminal "
                "dependency is the reviewed S2PLT03 terminal resilience proof artifact."
            ),
            "acceptance_ids": ["ACC-S2PLT03-RESILIENCE", "ACC-S2PMT07-FINAL-REVIEW"],
            "owner": "content_owner + engineering_owner + independent_final_reviewer",
            "human_owner_role": "content_owner + engineering_owner + independent_final_reviewer",
            "unblock_condition": (
                "Build, independently review, write, and validate "
                "FINAL_ACCEPTANCE_BUNDLE/s2plt03_terminal_resilience_proof.json "
                "without enabling SMTP, scheduler, Release, restore, or production acceptance."
            ),
            "stale_candidates": stale_candidates or [],
        }
    if explicit_s2plt02_terminal_current or terminal_delivery_proof_is_next:
        return {
            "task_id": "S2PLT02-TERMINAL-DELIVERY-PROOF",
            "status": "blocked",
            "reason": (
                "The live S2PLT02 real-proof capture authorization artifact is "
                "validated, but S2PLT02 still lacks a second consecutive real "
                "M1-M4 SMTP service day, eight real emails, real launchd scheduler "
                "proof, and terminal delivery proof artifact."
            ),
            "acceptance_ids": ["ACC-S2PLT02-2D", "ACC-S2PMT07-FINAL-REVIEW"],
            "owner": "content_owner + engineering_owner + independent_final_reviewer",
            "human_owner_role": "content_owner + engineering_owner + independent_final_reviewer",
            "unblock_condition": (
                "Use the validated no-production authorization only to collect "
                "the missing S2PLT02 terminal evidence, then validate "
                "FINAL_ACCEPTANCE_BUNDLE/s2plt02_terminal_delivery_proof.json "
                "without claiming Stage2 production acceptance."
            ),
            "stale_candidates": stale_candidates or [],
        }
    if real_proof_capture_is_next:
        return {
            "task_id": "S2PLT02-REAL-PROOF-CAPTURE-AUTHORIZATION",
            "status": "blocked",
            "reason": (
                "S2PLT01 terminal acceptance and P0/P1 zero-proof are validated inputs, "
                "but S2PLT02 still lacks explicit owner authorization for real SMTP/"
                "scheduler capture, second consecutive real M1-M4 SMTP day, real "
                "launchd scheduler proof, and terminal delivery proof artifact."
            ),
            "acceptance_ids": ["ACC-S2PLT02-2D", "ACC-S2PMT07-FINAL-REVIEW"],
            "owner": "content_owner + engineering_owner + independent_final_reviewer",
            "human_owner_role": "content_owner + engineering_owner + independent_final_reviewer",
            "unblock_condition": (
                "First obtain explicit owner authorization for real SMTP/scheduler proof "
                "capture; then capture a second consecutive real M1-M4 SMTP service day, "
                "real launchd scheduler proof, and validate "
                "FINAL_ACCEPTANCE_BUNDLE/s2plt02_terminal_delivery_proof.json without "
                "claiming Stage2 production acceptance."
            ),
            "stale_candidates": stale_candidates or [],
        }

    return {
        "task_id": "S2PMT07-INDEPENDENT-FINAL-REVIEWER-ASSIGNMENT",
        "status": "blocked",
        "reason": (
            "Current S2PMT07 blockers are mapped to required future evidence; "
            "independent reviewer assignment remains required before the future "
            "closure decision packet can be turned into a real P0/P1 zero-proof "
            "closure artifact."
        ),
        "acceptance_ids": ["ACC-S2PMT07-FINAL-REVIEW"],
        "owner": "content_owner + engineering_owner + independent_final_reviewer",
        "human_owner_role": "content_owner + engineering_owner + independent_final_reviewer",
        "unblock_condition": (
            "Provide independent final reviewer assignment artifact, independent "
            "closure decision, P0/P1 zero proof, S2PLT04 completion report, final "
            "bundle manifest, independent signoff, final command execution, "
            "no-production attestation, and next-agent handoff before any final "
            "gate closure claim."
        ),
        "stale_candidates": stale_candidates or [],
    }


def adp_s2pmt07_gate_is_current(project_id: str, matrix: dict[str, Any]) -> bool:
    """Return true when ADP's V7.2 current task is any S2PMT07 final-gate state."""

    if project_id != "arxiv-daily-push":
        return False
    current_gate = str(matrix.get("current_gate") or "")
    current_v7_task_id = str(matrix.get("current_v7_task_id") or "")
    return current_v7_task_id == "S2PMT07" or current_gate.startswith("S2PMT07")


def adp_s2pmt07_current_recommendation(matrix: dict[str, Any]) -> str:
    """Build the current ADP S2PMT07 owner recommendation from the active matrix."""

    normalized_manifest_clause = ""
    capture_window_cli_clause = ""
    evidence_inventory_clause = ""
    readiness_live_auth_clause = ""
    latest_nonterminal_clause = ""
    capture_window_runtime_clause = ""
    current_iteration = str(matrix.get("current_iteration") or "")
    current_gate = str(matrix.get("current_gate") or "")
    current_alias = str(matrix.get("current_v7_legacy_alias") or "")
    final_bundle_chain_ready = (
        "POST-FINAL-BUNDLE-CURRENT-STATE-SYNC" in current_iteration
        or "POST_FINAL_BUNDLE_CURRENT_STATE_SYNC" in current_gate
        or "FINAL_ACCEPTANCE_BUNDLE_READY_NO_PRODUCTION_ACCEPTANCE" in current_gate
        or "final bundle artifact chain complete" in current_alias.lower()
    )
    production_boundary_preflight_ready = (
        "INTEGRATED-PRODUCTION-ACCEPTANCE-PREFLIGHT" in current_iteration
        or "INTEGRATED_PRODUCTION_ACCEPTANCE_PREFLIGHT" in current_gate
        or "INTEGRATED-PRODUCTION-ACCEPTANCE-WRITE-GATE" in current_iteration
        or "INTEGRATED_PRODUCTION_ACCEPTANCE_WRITE_GATE" in current_gate
        or "production-boundary preflight passed" in current_alias.lower()
        or "write-gate precheck" in current_alias.lower()
    )
    controlled_real_run_rechecked = (
        "controlled foreground real-run acceptance recheck passed" in current_alias.lower()
        or "duplicate_smtp_send_avoided=true" in current_alias
    )
    owner_decision_recorded_write_gate_allowed = (
        "WRITE_GATE_ALLOWED" in current_gate
        or "owner_production_boundary_decision_recorded=true" in current_alias
        or "acceptance_write_gate_allowed=true" in current_alias
    )
    integrated_production_accepted_no_daily_operation = (
        bool(matrix.get("stage2_integrated_production_accepted", False))
        or "INTEGRATED_PRODUCTION_ACCEPTED" in current_gate
        or "integrated_production_accepted=true" in current_alias
    ) and not bool(matrix.get("s2pmt07_daily_operation_enabled", False))
    daily_operation_preflight_current = (
        "DAILY-OPERATION-AUTHORIZATION-PREFLIGHT" in current_iteration
        or "DAILY_OPERATION_AUTHORIZATION_PREFLIGHT" in current_gate
        or "daily operation authorization preflight" in current_alias.lower()
    )
    daily_operation_owner_decision_keep_disabled = (
        "DAILY-OPERATION-OWNER-DECISION-KEEP-DISABLED" in current_iteration
        or "DAILY_OPERATION_OWNER_DECISION_RECORDED_KEEP_DISABLED" in current_gate
        or "keep_daily_operation_disabled_no_persistent_authorization" in current_alias
    )
    daily_operation_persistent_authorization_missing = (
        "DAILY-OPERATION-PERSISTENT-AUTHORIZATION-GATE" in current_iteration
        or "DAILY_OPERATION_PERSISTENT_AUTHORIZATION_MISSING" in current_gate
        or "persistent_daily_operation_authorization_missing" in current_alias
    )
    daily_operation_persistent_authorization_request_ready = (
        "DAILY-OPERATION-PERSISTENT-AUTHORIZATION-REQUEST" in current_iteration
        or "DAILY_OPERATION_PERSISTENT_AUTHORIZATION_REQUEST_READY" in current_gate
        or "daily_operation_persistent_enablement_authorization.request.json" in current_alias
    )
    daily_operation_blockers = str(matrix.get("s2pmt07_daily_operation_authorization_preflight_blockers") or "")
    daily_operation_preflight_passed = bool(
        matrix.get("s2pmt07_daily_operation_authorization_preflight_passed", False)
    )
    daily_operation_gh_equivalent_repaired = (
        "github_open_pr_count_zero_api_v1" in current_alias
        or (
            "missing_gh_cli" not in daily_operation_blockers
            and "missing_smtp_secret_env_names" in daily_operation_blockers
        )
    )
    s2plt02_terminal_delivery_ready = (
        "S2PLT02_TERMINAL_DELIVERY_PROOF_READY" in current_gate
        or "S2PLT02 terminal delivery proof artifact passed" in current_alias
        or "S2PLT02 terminal delivery proof accepted" in current_alias
    )
    s2plt03_terminal_resilience_ready = (
        "S2PLT03_TERMINAL_RESILIENCE_PROOF_READY" in current_gate
        or "S2PLT03 terminal resilience proof artifact passed" in current_alias
        or "S2PLT03 terminal resilience proof accepted" in current_alias
    )
    if (
        "S2PLT02-REAL-DELIVERY-MANIFEST-NORMALIZATION" in current_iteration
        or "s2plt02_real_delivery_manifest_normalization_iteration" in matrix
        or "normalized manifest" in current_alias.lower()
        or "normalized 2026" in current_alias.lower()
        or "normalized_manifest_ready=true" in current_alias
    ):
        normalized_manifest_clause = (
            " S2PLT02-REAL-DELIVERY-MANIFEST-NORMALIZATION normalized manifest gate,"
        )
    if (
        "S2PLT02-TERMINAL-CAPTURE-WINDOW-AUDIT-CLI" in current_iteration
        or "s2plt02_terminal_capture_window_audit_cli_iteration" in matrix
        or "capture-window audit reproducible" in current_alias.lower()
        or "audit-s2plt02-terminal-capture-window" in current_alias
    ):
        capture_window_cli_clause = (
            " S2PLT02-TERMINAL-CAPTURE-WINDOW-AUDIT-CLI reproducible dry-run blocker CLI,"
        )
    if (
        "S2PLT02-TERMINAL-PROOF-EVIDENCE-INVENTORY" in current_iteration
        or "s2plt02_terminal_proof_evidence_inventory_iteration" in matrix
        or "S2PLT02_TERMINAL_PROOF_EVIDENCE_INVENTORY" in str(matrix.get("current_gate") or "")
        or "audit-s2plt02-terminal-proof-evidence-inventory" in current_alias
        or "terminal proof classifier" in current_alias.lower()
    ):
        evidence_inventory_clause = (
            " S2PLT02-TERMINAL-PROOF-EVIDENCE-INVENTORY usable/blocked/missing classification,"
        )
    if (
        "S2PLT02-REAL-PROOF-CAPTURE-READINESS-LIVE-AUTH-SYNC" in current_iteration
        or "S2PLT02_REAL_PROOF_CAPTURE_READINESS_LIVE_AUTH_SYNC" in str(matrix.get("current_gate") or "")
        or "authorization_artifact_status=pass" in current_alias
        or "real_proof_capture_authorized=true" in current_alias
    ):
        readiness_live_auth_clause = (
            " S2PLT02-REAL-PROOF-CAPTURE-READINESS-LIVE-AUTH-SYNC authorization-pass readiness,"
        )
    if (
        "S2PMT07-S2PLT04-S2PLT02-LATEST-NONTERMINAL-EVIDENCE-SYNC" in current_iteration
        or "S2PLT04_S2PLT02_LATEST_NONTERMINAL_EVIDENCE_SYNC" in str(matrix.get("current_gate") or "")
        or "latest nonterminal" in current_alias.lower()
        or "13 S2PLT02 nonterminal refs" in current_alias
        or "14 S2PLT02 nonterminal refs" in current_alias
    ):
        latest_nonterminal_clause = (
            " S2PMT07-S2PLT04-S2PLT02-LATEST-NONTERMINAL-EVIDENCE-SYNC evidence freshness gate,"
        )
    if (
        "S2PLT02-TERMINAL-CAPTURE-WINDOW-RUNTIME-STATE-SYNC" in current_iteration
        or "S2PLT02_TERMINAL_CAPTURE_WINDOW_RUNTIME_STATE_SYNC" in str(matrix.get("current_gate") or "")
        or "launchagents_loaded_but_disabled" in current_alias
        or "runtime state sync" in current_alias.lower()
    ):
        capture_window_runtime_clause = (
            " S2PLT02-TERMINAL-CAPTURE-WINDOW-RUNTIME-STATE-SYNC loaded-but-disabled scheduler boundary,"
        )
    if daily_operation_persistent_authorization_request_ready:
        return (
            "A: Persistent DAILY_OPERATION authorization request packet is ready, but it is "
            "request-only and does not authorize runtime. Keep DAILY_OPERATION disabled unless "
            "the owner creates a separate explicit authorization artifact, then rerun the "
            "persistent authorization gate and a separate enablement preflight."
        )
    if daily_operation_persistent_authorization_missing:
        return (
            "A: Persistent DAILY_OPERATION authorization gate is blocked because the explicit "
            "owner authorization artifact is missing. Keep DAILY_OPERATION disabled; do not "
            "enable SMTP, scheduler, Release, restore, or persistent operation until that "
            "artifact exists and a separate enablement preflight passes."
        )
    if daily_operation_owner_decision_keep_disabled:
        return (
            "A: DAILY_OPERATION owner decision is recorded as keep-disabled. Persistent "
            "DAILY_OPERATION is not authorized; keep runtime disabled unless the owner later "
            "provides a separate explicit persistent DAILY_OPERATION authorization and a new "
            "enablement artifact passes."
        )
    if daily_operation_preflight_current:
        if daily_operation_preflight_passed:
            return (
                "A: DAILY_OPERATION authorization preflight technical checks now pass. "
                "The gh CLI blocker is covered by github_open_pr_count_zero_api_v1, SMTP "
                "secret key presence is proven by adp_local_runner_env_file_secret_presence_v1 "
                "without logging values, and ADP-scoped git artifact hygiene passes. Keep "
                "runtime disabled unless the owner explicitly authorizes persistent "
                "DAILY_OPERATION in a separate artifact."
            )
        if daily_operation_gh_equivalent_repaired:
            return (
                "A: DAILY_OPERATION authorization preflight has run after "
                "INTEGRATED_PRODUCTION_ACCEPTED, and github_open_pr_count_zero_api_v1 "
                "has cleared the gh CLI blocker. production_preflight_passed is still "
                "false; repair missing SMTP secret env names and OpenAIDatabase "
                "session-history archive git artifact hygiene violations before "
                "requesting persistent DAILY_OPERATION authorization. runtime enablement remains disabled."
            )
        return (
            "A: DAILY_OPERATION authorization preflight has run after "
            "INTEGRATED_PRODUCTION_ACCEPTED, but production_preflight_passed is "
            "false. Repair missing gh CLI availability, missing SMTP secret env names, "
            "and OpenAIDatabase session-history archive git artifact hygiene violations "
            "before requesting persistent DAILY_OPERATION "
            "authorization. runtime enablement remains disabled."
        )
    if integrated_production_accepted_no_daily_operation:
        return (
            "A: INTEGRATED_PRODUCTION_ACCEPTED evidence is written for Stage 2 and "
            "runtime enablement remains disabled; next request explicit DAILY_OPERATION "
            "authorization and run the daily-operation safety preflight before enabling "
            "SMTP, scheduler, Release, restore, or persistent operation."
        )
    if owner_decision_recorded_write_gate_allowed:
        return (
            "A: owner production-boundary decision evidence is recorded and the final "
            "acceptance write gate is allowed as no-runtime evidence; next write "
            "INTEGRATED_PRODUCTION_ACCEPTED evidence only through the final gate, while "
            "keeping SMTP, scheduler, Release, restore, and DAILY_OPERATION disabled."
        )
    if production_boundary_preflight_ready:
        controlled_run_sentence = (
            "Owner-authorized controlled foreground real-run acceptance recheck passed without duplicate SMTP; "
            "treat it only as evidence, not DAILY_OPERATION; "
            if controlled_real_run_rechecked
            else ""
        )
        return (
            "A: keep V7.2 as CURRENT product contract, keep V7.1 read-only, treat "
            "the integrated production acceptance preflight and write-gate precheck as passed no-production evidence; "
            + controlled_run_sentence
            + "review FINAL_ACCEPTANCE_BUNDLE/owner_production_boundary_decision.request.json, "
            "then record owner production-boundary decision evidence or pause; do not enable "
            "SMTP, scheduler, Release, restore, DAILY_OPERATION, or write "
            "INTEGRATED_PRODUCTION_ACCEPTED automatically."
        )
    if final_bundle_chain_ready:
        return (
            "A: keep V7.2 as CURRENT product contract, keep V7.1 read-only, treat "
            "the validated S2PMT07 final acceptance bundle as complete no-production "
            "evidence with FINAL_ACCEPTANCE_BUNDLE/manifest.json passing and "
            "missing_items=[]; do not rebuild S2PLT04/final-bundle artifacts, do not "
            "enable SMTP, scheduler, Release, restore, or DAILY_OPERATION, and next run "
            "only the integrated production acceptance boundary preflight plus owner "
            "decision evidence before any INTEGRATED_PRODUCTION_ACCEPTED claim."
        )
    if s2plt03_terminal_resilience_ready:
        return (
            "A: keep V7.2 as CURRENT product contract, keep V7.1 read-only, treat "
            "the validated independent reviewer assignment, P0/P1 zero-proof artifact, "
            "FINAL_ACCEPTANCE_BUNDLE/s2plt02_terminal_delivery_proof.json, and "
            "FINAL_ACCEPTANCE_BUNDLE/s2plt03_terminal_resilience_proof.json as existing "
            "no-production final-bundle inputs; do not re-run S2PLT02 SMTP/scheduler capture "
            "or S2PLT03 resilience proof; next build, independently review, write, and validate "
            "FINAL_ACCEPTANCE_BUNDLE/s2plt04_completion_report.json before final bundle manifest, "
            "independent final signoff, final command execution proof, no-production attestation "
            "closure, and next-agent handoff."
        )
    if s2plt02_terminal_delivery_ready:
        return (
            "A: keep V7.2 as CURRENT product contract, keep V7.1 read-only, treat "
            "the validated independent reviewer assignment, P0/P1 zero-proof artifact, "
            "and FINAL_ACCEPTANCE_BUNDLE/s2plt02_terminal_delivery_proof.json as "
            "existing no-production final-bundle inputs; do not re-run S2PLT02 SMTP "
            "or scheduler capture; next build, independently review, write, and validate "
            "FINAL_ACCEPTANCE_BUNDLE/s2plt03_terminal_resilience_proof.json before "
            "S2PLT04 completion proof, final bundle manifest, independent final signoff, "
            "final command execution proof, no-production attestation, and next-agent "
            "handoff."
        )
    return (
        "A: keep V7.2 as CURRENT product contract, keep V7.1 read-only, treat "
        "live authorization, independent reviewer assignment, P0/P1 zero-proof "
        "artifact FINAL_ACCEPTANCE_BUNDLE/p0_p1_zero_proof.json, the stdout-only "
        "terminal proof draft builder, S2PLT02-REAL-SCHEDULER-PROOF-INPUT-VALIDATOR, "
        "S2PLT02-TERMINAL-DELIVERY-INPUT-INVENTORY input inventory, "
        "S2PLT02-TERMINAL-DELIVERY-PROOF-CAPTURE-PLAN capture plan, "
        "S2PLT02-TERMINAL-CAPTURE-WINDOW-AUDIT dry-run blocker evidence, "
        "S2PLT02-REAL-DELIVERY-MANIFEST-INPUT-VALIDATOR manifest gate,"
        f"{normalized_manifest_clause}{capture_window_cli_clause}{capture_window_runtime_clause}{evidence_inventory_clause}{readiness_live_auth_clause}{latest_nonterminal_clause} and only current explicit no-production "
        "real-delivery manifest inputs as validated no-write inputs, record the "
        "current dry-run/scheduler-disabled capture window as blocked evidence, "
        "and next collect S2PLT02 terminal delivery proof only from complete real "
        "delivery/scheduler manifests in a controlled real capture window before "
        "S2PLT03 terminal proof, S2PLT04 completion proof, final bundle manifest, "
        "independent final signoff, final command execution proof, no-production "
        "attestation, and next-agent handoff."
    )


def git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def current_commit() -> str:
    value = git_output(["rev-parse", "HEAD"])
    return value if re.fullmatch(r"[0-9a-f]{40}", value) else "0" * 40


def current_tree_hash() -> str:
    value = git_output(["rev-parse", "HEAD^{tree}"])
    return value if re.fullmatch(r"[0-9a-f]{40}", value) else "0" * 40


def configured_source_base() -> str | None:
    value = os.environ.get("GOVERNANCE_SOURCE_BASE_COMMIT", "").strip()
    return value if re.fullmatch(r"[0-9a-f]{40}", value) else None


def configured_source_tree() -> str | None:
    value = os.environ.get("GOVERNANCE_SOURCE_TREE_HASH", "").strip()
    return value if re.fullmatch(r"[0-9a-f]{40}", value) else None


def assurance_status(value: str | None) -> str:
    normalized = str(value or "unknown").strip().lower()
    mapping = {
        "pass": "VERIFIED",
        "verified": "VERIFIED",
        "machine_verified": "VERIFIED",
        "partial": "PARTIAL",
        "blocked_precheck": "BLOCKED_PRECHECK",
        "blocked": "FAILED",
        "failed": "FAILED",
        "unknown": "UNVERIFIED",
        "unverified": "UNVERIFIED",
        "not_applicable": "NOT_APPLICABLE",
        "not applicable": "NOT_APPLICABLE",
        "n/a": "NOT_APPLICABLE",
    }
    return mapping.get(normalized, "UNVERIFIED")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def canonical_input_paths(project_path: Path) -> list[Path]:
    candidates = [
        project_path / "VERSION",
        project_path / "CHANGELOG.md",
        project_path / "docs/governance/MODEL_SPEC.md",
        project_path / "docs/governance/model_registry.yaml",
        project_path / "docs/governance/formula_registry.yaml",
        project_path / "docs/governance/parameter_registry.csv",
        project_path / "docs/governance/DEVELOPMENT_LEDGER.md",
        project_path / "docs/governance/development_events.jsonl",
        project_path / "docs/governance/DELIVERY_PLAN.md",
        project_path / "docs/governance/delivery_tasks.yaml",
        project_path / "docs/governance/VERSION_MATRIX.yaml",
        project_path / "docs/governance/TRACEABILITY_MATRIX.csv",
        ROOT / "governance/projects.yaml",
    ]
    return [path for path in candidates if path.is_file()]


def source_snapshot_hash(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda item: rel(item)):
        digest.update(rel(path).encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes().replace(b"\r\n", b"\n"))
        digest.update(b"\0")
    return "sha256:" + digest.hexdigest()


def active_registry_counts(project_path: Path) -> dict[str, int]:
    parameters = read_csv(project_path / "docs/governance/parameter_registry.csv")
    active_params = [row for row in parameters if str(row.get("status") or "").lower() == "active"]
    checked_params = [
        row
        for row in active_params
        if row.get("source_selector") and row.get("extracted_value") not in {None, ""} and row.get("evidence_hash")
    ]
    formula_data = structural.load_yaml(project_path / "docs/governance/formula_registry.yaml")
    formulas = structural.as_list(formula_data.get("formulas")) if isinstance(formula_data, dict) else []
    active_formulas = [
        row for row in formulas if isinstance(row, dict) and str(row.get("status") or "").lower() == "active"
    ]
    checked_formulas = [
        row
        for row in active_formulas
        if row.get("implementation_refs") and row.get("implementation_fingerprint") and row.get("evidence_hash")
    ]
    return {
        "total_parameters": len(parameters),
        "active_parameters": len(active_params),
        "checked_parameters": len(checked_params),
        "total_formulas": len(formulas),
        "active_formulas": len(active_formulas),
        "checked_formulas": len(checked_formulas),
    }


def collect_unresolved_fact_ids(project_id: str, parsed: dict[str, Any], counts: dict[str, int]) -> list[str]:
    ids: set[str] = set()

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                if key in {"unknown_task_ids", "semantic_review_task_ids", "unresolved_fact_ids"}:
                    for ref in structural.as_list(item):
                        text = str(ref).strip()
                        if text:
                            ids.add(text)
                else:
                    visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    for key in ("models", "formulas", "parameters", "tasks", "traceability", "version_matrix"):
        visit(parsed.get(key))
    if counts["checked_parameters"] < counts["active_parameters"]:
        ids.add(f"FACT-{project_id}-IMPLEMENTATION-PARAMETER-REVIEW")
    if counts["checked_formulas"] < counts["active_formulas"]:
        ids.add(f"FACT-{project_id}-IMPLEMENTATION-FORMULA-REVIEW")
    policy = ASSURANCE_POLICY.get(project_id, {})
    if policy.get("empirical") in {"unknown", "partial"}:
        ids.add(f"FACT-{project_id}-EMPIRICAL-EVIDENCE")
    if policy.get("operational") in {"blocked", "partial", "unknown"}:
        ids.add(f"FACT-{project_id}-OPERATIONAL-EVIDENCE")
    return sorted(ids)


def load_events(project_path: Path) -> list[dict[str, Any]]:
    path = project_path / "docs/governance/development_events.jsonl"
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            events.append(value)
    return events


def event_time(event: dict[str, Any]) -> str:
    return str(event.get("timestamp") or event.get("date") or "")


def max_event_time(events: list[dict[str, Any]]) -> str:
    values = [event_time(event) for event in events if event_time(event)]
    return max(values) if values else "UNKNOWN"


def pending_event_count(events: list[dict[str, Any]]) -> int:
    count = 0
    for event in events:
        commit = str(event.get("result_commit") or event.get("git_commit") or "").upper()
        if commit in {"", "PENDING", "PENDING_CI"}:
            count += 1
    return count


def event_binding_counts(events: list[dict[str, Any]]) -> dict[str, int]:
    counts = {
        "tree_bound_events": 0,
        "commit_bound_events": 0,
        "legacy_unbound_events": 0,
        "precommit_pending_events": 0,
    }
    for event in events:
        binding = str(event.get("binding_status") or "").strip().lower()
        commit = str(event.get("result_commit") or event.get("git_commit") or "").strip()
        has_commit = bool(re.fullmatch(r"[0-9a-f]{7,40}", commit))
        if binding == "precommit_tree_bound":
            counts["tree_bound_events"] += 1
        elif has_commit or event.get("ci_attestation_ref"):
            counts["commit_bound_events"] += 1
        elif binding in {"pre_commit_pending", "precommit_pending"}:
            counts["precommit_pending_events"] += 1
        else:
            counts["legacy_unbound_events"] += 1
    return counts


def final_commit_binding(events: list[dict[str, Any]]) -> str:
    if not events:
        return "PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION"
    latest = events[-1]
    commit = str(latest.get("result_commit") or latest.get("git_commit") or "").strip()
    if re.fullmatch(r"[0-9a-f]{7,40}", commit):
        ref = str(latest.get("ci_run_reference") or latest.get("ci_attestation_ref") or "").strip()
        if ref:
            return f"CI_ATTESTED:{commit} {ref}"
        return f"COMMIT_BOUND:{commit}"
    ref = str(latest.get("ci_attestation_ref") or "").strip()
    if ref:
        return f"CI_ATTESTED:{ref}"
    return "PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION"


def latest_commit_bound_source(events: list[dict[str, Any]]) -> tuple[str | None, str | None]:
    for event in reversed(events):
        commit = str(event.get("result_commit") or event.get("git_commit") or "").strip()
        tree = str(event.get("result_tree_hash") or event.get("git_tree_hash") or "").strip()
        if re.fullmatch(r"[0-9a-f]{40}", commit):
            return commit, tree if re.fullmatch(r"[0-9a-f]{40}", tree) else None
    return None, None


def completed_task_ids(tasks: list[dict[str, Any]]) -> set[str]:
    return {
        str(task.get("task_id"))
        for task in tasks
        if isinstance(task, dict) and str(task.get("status") or "") in COMPLETED_TASK_STATES
    }


def task_is_stale_or_satisfied(project_id: str, task: dict[str, Any], counts: dict[str, int], impl_status: str) -> str:
    objective = str(task.get("objective") or "").lower()
    task_id = str(task.get("task_id") or "")
    if project_id == "Serenity-Alipay" and task_id == "TASK-A-001":
        baseline_exists = (
            counts["active_parameters"] > 0
            and counts["active_formulas"] > 0
            and impl_status == "VERIFIED"
        )
        if baseline_exists and "first" in objective and "governance baseline" in objective:
            return "Serenity-Alipay baseline exists and implementation congruence is VERIFIED; the first-baseline task is stale."
    if "create the first" in objective and counts["active_parameters"] > 0 and counts["active_formulas"] > 0:
        return "Task objective says to create the first baseline, but active formula and parameter registries already exist."
    return ""


def select_next_task(
    project_id: str,
    tasks: list[dict[str, Any]],
    counts: dict[str, int],
    impl_status: str,
    current_phase: str = "",
    arxiv_stage1_accepted: bool = False,
) -> dict[str, Any]:
    completed = completed_task_ids(tasks)
    candidates: list[dict[str, Any]] = []
    stale: list[dict[str, str]] = []
    for task in tasks:
        if not isinstance(task, dict):
            continue
        task_id = str(task.get("task_id") or "")
        status = str(task.get("status") or "")
        if status not in EXECUTABLE_TASK_STATES:
            continue
        stale_reason = task_is_stale_or_satisfied(project_id, task, counts, impl_status)
        if stale_reason:
            stale.append({"task_id": task_id, "reason": stale_reason})
            continue
        dependencies = [str(dep) for dep in structural.as_list(task.get("dependencies")) if str(dep)]
        unmet = [dep for dep in dependencies if dep not in completed]
        if unmet or not task.get("acceptance_ids"):
            continue
        if status != "blocked" and not task.get("test_commands"):
            continue
        if (
            project_id == "arxiv-daily-push"
            and arxiv_stage1_accepted
            and status == "blocked"
            and task_id.startswith("ADP-PHASE11-")
        ):
            stale.append(
                {
                    "task_id": task_id,
                    "reason": "Legacy Phase 11 blocked trial task is superseded by V5/V6 Stage 1 accepted evidence; production variable enablement is tracked as a separate fail-closed operational action.",
                }
            )
            continue
        candidates.append(task)
    if not candidates:
        return {
            "task_id": "NONE",
            "status": "not_applicable",
            "reason": "No ready or in_progress task has completed dependencies, Acceptance IDs, and test commands.",
            "acceptance_ids": [],
            "owner": "project owner",
            "human_owner_role": "project_owner",
            "unblock_condition": "Define a ready/in_progress/blocked task with completed dependencies, Acceptance IDs, and evidence policy.",
            "stale_candidates": stale,
        }
    use_current_phase_priority = project_id == "arxiv-daily-push" and str(current_phase).startswith("S")
    if use_current_phase_priority:
        phase_candidates = [
            task
            for task in candidates
            if str(task.get("phase") or "") == current_phase and str(task.get("status") or "") != "blocked"
        ]
        if phase_candidates:
            phase_priority = {"in_progress": 0, "ready": 1, "planned": 2}
            phase_candidates.sort(key=lambda task: (phase_priority.get(str(task.get("status")), 9), str(task.get("task_id"))))
            candidates = phase_candidates

    priority = {"blocked": 0, "in_progress": 1, "ready": 2, "planned": 3}
    candidates.sort(key=lambda task: (priority.get(str(task.get("status")), 9), str(task.get("task_id"))))
    task = candidates[0]
    role = REVIEW8_DECISION_POLICY.get(project_id, {}).get("owner_role", "project_owner")
    status = str(task.get("status") or "")
    if status == "blocked":
        unblock = str(task.get("risk") or task.get("objective") or "Human owner must provide the missing evidence before this task can complete.")
    else:
        command = structural.as_list(task.get("test_commands"))[0] if task.get("test_commands") else "listed acceptance command"
        if str(command).strip().upper() == "PENDING":
            unblock = "Define concrete acceptance test commands before marking this task complete, then attach the listed evidence refs."
        else:
            unblock = f"Run `{command}` and attach the listed evidence refs."
    return {
        "task_id": str(task.get("task_id") or "NONE"),
        "status": status,
        "reason": str(task.get("objective") or ""),
        "acceptance_ids": structural.as_list(task.get("acceptance_ids")),
        "owner": role,
        "human_owner_role": role,
        "unblock_condition": unblock,
        "stale_candidates": stale,
    }


def yaml_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if value is None:
        return "null"
    return json.dumps(str(value), ensure_ascii=False)


def dump_yaml(value: Any, indent: int = 0) -> list[str]:
    pad = " " * indent
    if isinstance(value, dict):
        lines: list[str] = []
        for key, item in value.items():
            if item == []:
                lines.append(f"{pad}{key}: []")
                continue
            if isinstance(item, (dict, list)):
                lines.append(f"{pad}{key}:")
                lines.extend(dump_yaml(item, indent + 2))
            else:
                lines.append(f"{pad}{key}: {yaml_scalar(item)}")
        return lines
    if isinstance(value, list):
        if not value:
            return [f"{pad}[]"]
        lines = []
        for item in value:
            if isinstance(item, (dict, list)):
                lines.append(f"{pad}-")
                lines.extend(dump_yaml(item, indent + 2))
            else:
                lines.append(f"{pad}- {yaml_scalar(item)}")
        return lines
    return [f"{pad}{yaml_scalar(value)}"]


def existing_assurance_base(project_path: Path) -> str | None:
    path = project_path / "docs/governance/ASSURANCE_STATUS.yaml"
    if not path.exists():
        return None
    match = re.search(r"(?m)^source_base_commit:\s*\"?([0-9a-f]{40})\"?\s*$", path.read_text(encoding="utf-8"))
    commit = match.group(1) if match else ""
    return commit if re.fullmatch(r"[0-9a-f]{40}", commit) else None


def existing_assurance_tree(project_path: Path) -> str | None:
    path = project_path / "docs/governance/ASSURANCE_STATUS.yaml"
    if not path.exists():
        return None
    match = re.search(r"(?m)^source_tree_hash:\s*\"?([0-9a-f]{40})\"?\s*$", path.read_text(encoding="utf-8"))
    tree = match.group(1) if match else ""
    return tree if re.fullmatch(r"[0-9a-f]{40}", tree) else None


def existing_assurance_status(project_path: Path) -> dict[str, Any]:
    path = project_path / "docs/governance/ASSURANCE_STATUS.yaml"
    if not path.exists():
        return {}
    data = structural.load_yaml(path)
    return data if isinstance(data, dict) else {}


def existing_root_base() -> str | None:
    for path in (ROOT / "GOVERNANCE_DASHBOARD.md", ROOT / "OWNER_PORTFOLIO.md", ROOT / "README.md"):
        if not path.exists():
            continue
        match = re.search(r"source_base_commit:\s*`?([0-9a-f]{40})`?", path.read_text(encoding="utf-8"))
        commit = match.group(1) if match else ""
        if re.fullmatch(r"[0-9a-f]{40}", commit):
            return commit
    return None


def existing_root_tree() -> str | None:
    for path in (ROOT / "GOVERNANCE_DASHBOARD.md", ROOT / "OWNER_PORTFOLIO.md", ROOT / "README.md"):
        if not path.exists():
            continue
        match = re.search(r"source_tree_hash:\s*`?([0-9a-f]{40})`?", path.read_text(encoding="utf-8"))
        tree = match.group(1) if match else ""
        if re.fullmatch(r"[0-9a-f]{40}", tree):
            return tree
    return None


def latest_manifest(project_id: str, events: list[dict[str, Any]]) -> dict[str, Any]:
    manifest_dir = ROOT / "governance/run_manifests"
    event_refs: list[str] = []
    if events:
        event_refs.extend(str(ref) for ref in structural.as_list(events[-1].get("evidence_refs")))

    def load_manifest(ref: str) -> dict[str, Any]:
        path = ROOT / ref
        if path.suffix != ".json" or not path.is_file() or manifest_dir not in path.parents:
            return {}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
        if str(data.get("project_id") or "") != project_id:
            return {}
        data["_path"] = rel(path)
        return data

    for ref in reversed(event_refs):
        data = load_manifest(ref)
        if data:
            return data
    for ref in reversed([str(path.relative_to(ROOT)) for path in sorted(manifest_dir.glob("*.json"))]):
        data = load_manifest(ref)
        if data:
            return data
    return {}


def arxiv_stage1_acceptance_proven(project_id: str, events: list[dict[str, Any]], manifest: dict[str, Any]) -> bool:
    if project_id != "arxiv-daily-push":
        return False
    if (
        manifest.get("production_acceptance_claimed") is False
        and (
            str(manifest.get("task_id") or "").startswith("S1P5T03-R")
            or str(manifest.get("status") or "").lower() == "pending_cloud_ci"
        )
    ):
        return False
    manifest_claims_acceptance = (
        manifest.get("production_acceptance_claimed") is True
        and manifest.get("accepted_for_production") is True
        and str(manifest.get("arxiv_production_acceptance_label") or "") == "ARXIV_PRODUCTION_ACCEPTED"
        and str(manifest.get("status") or "").lower() in {"pass", "completed"}
    )
    if manifest_claims_acceptance:
        return True
    for event in reversed(events):
        if event.get("production_acceptance_claimed") is False and str(event.get("task_id") or "").startswith("S1P5T03-R"):
            return False
        if (
            event.get("production_acceptance_claimed") is True
            and str(event.get("arxiv_production_acceptance_label") or "") == "ARXIV_PRODUCTION_ACCEPTED"
            and str(event.get("result") or "").lower() in {"pass", "completed"}
        ):
            return True
    return False


def load_project(project: dict[str, Any]) -> dict[str, Any]:
    project_id = structural.project_scope(project)
    project_path = ROOT / str(project.get("path") or "")
    parsed_validation = structural.Validation()
    parsed = structural.parse_project_governance(project_path, parsed_validation, True, project_id)
    tasks = [task for task in structural.as_list(parsed.get("tasks")) if isinstance(task, dict)]
    events = load_events(project_path)
    matrix = parsed.get("version_matrix") if isinstance(parsed.get("version_matrix"), dict) else {}
    counts = active_registry_counts(project_path)
    manifest = latest_manifest(project_id, events)
    source_paths = canonical_input_paths(project_path)
    source_hash = source_snapshot_hash(source_paths)
    latest_commit, latest_tree = latest_commit_bound_source(events)
    base_commit = configured_source_base() or latest_commit or existing_assurance_base(project_path) or current_commit()
    tree_hash = configured_source_tree() or latest_tree or existing_assurance_tree(project_path) or current_tree_hash()
    policy = dict(ASSURANCE_POLICY.get(project_id, {}))
    arxiv_stage1_accepted = arxiv_stage1_acceptance_proven(project_id, events, manifest)
    if arxiv_stage1_accepted:
        policy.update(
            {
                "empirical": "verified",
                "operational": "verified",
                "readiness": "verified",
                "decision": "Stage 1 arXiv accepted; production schedule remains controlled by GitHub Variables/Secrets and fail-closed gates.",
                "blockers": [],
            }
        )
    if adp_s2pmt07_gate_is_current(project_id, matrix):
        policy["readiness"] = "blocked_precheck"
        policy["decision"] = "S2PMT07 final gate precheck is blocked; Stage 1 remains accepted, but integrated production acceptance is not available."
    unresolved = collect_unresolved_fact_ids(project_id, parsed, counts)
    if arxiv_stage1_accepted:
        accepted_s1_resolved = {
            "ADP-PHASE8-VIDEO-001",
            "FACT-arxiv-daily-push-EMPIRICAL-EVIDENCE",
            "FACT-arxiv-daily-push-OPERATIONAL-EVIDENCE",
        }
        unresolved = [item for item in unresolved if item not in accepted_s1_resolved]
    impl_status = (
        "NOT_APPLICABLE"
        if counts["active_parameters"] == 0 and counts["active_formulas"] == 0
        else "VERIFIED"
        if counts["checked_parameters"] == counts["active_parameters"]
        and counts["checked_formulas"] == counts["active_formulas"]
        else "PARTIAL"
    )
    parameter_source_status = "VERIFIED" if counts["checked_parameters"] == counts["active_parameters"] else "PARTIAL"
    event_counts = event_binding_counts(events)
    evidence_freshness_status = "PARTIAL" if event_counts["legacy_unbound_events"] else "VERIFIED"
    methodological_status = "UNVERIFIED" if policy.get("empirical") in {"unknown", "partial"} else "VERIFIED"
    existing_assurance = existing_assurance_status(project_path)
    existing_owner_decision = (
        existing_assurance.get("owner_decision")
        if isinstance(existing_assurance.get("owner_decision"), dict)
        else {}
    )
    next_task = select_next_task(
        project_id,
        tasks,
        counts,
        impl_status,
        str(matrix.get("current_phase") or ""),
        arxiv_stage1_accepted=arxiv_stage1_accepted,
    )
    adp_s2pmt07_current = adp_s2pmt07_gate_is_current(project_id, matrix)
    if adp_s2pmt07_current:
        next_task = adp_s2pmt07_blocked_next_task(
            structural.as_list(next_task.get("stale_candidates")) if isinstance(next_task, dict) else [],
            matrix=matrix,
        )
    decision_policy = decision_policy_for(project_id, next_task)
    if decision_policy.get("owner_role") and str(next_task.get("task_id") or "") != "NONE" and not adp_s2pmt07_current:
        next_task = {
            **next_task,
            "owner": str(decision_policy.get("owner_role")),
            "human_owner_role": str(decision_policy.get("owner_role")),
        }
    release_gate = str(matrix.get("current_gate") or "UNKNOWN")
    if (
        project_id == "arxiv-daily-push"
        and not arxiv_stage1_accepted
        and str(next_task.get("task_id") or "").startswith("S1P5T03-R")
    ):
        release_gate = "STRICT_ARXIV_PRODUCTION_ACCEPTANCE_REOPENED_PENDING_S1P5T03R_CLOUD_CI"
    owner_decision = {
        "required": True,
        "decision_id": str(decision_policy.get("decision_id") or f"DEC-{project_id}-REVIEW8-001"),
        "review_id": str(decision_policy.get("review_id") or "REVIEW8"),
        "project_id": project_id,
        "decision_question": str(decision_policy.get("question") or policy.get("decision") or "Decide the next evidence investment."),
        "question": str(decision_policy.get("question") or policy.get("decision") or "Decide the next evidence investment."),
        "human_owner_role": str(decision_policy.get("owner_role") or "project_owner"),
        "human_assignment_status": str(decision_policy.get("assignment") or "HUMAN_ASSIGNMENT_REQUIRED"),
        "current_recommendation": str(decision_policy.get("recommendation") or "A: fund project-specific evidence collection"),
        "option_a": str(decision_policy.get("option_a") or "Collect the project-specific evidence required by the current blocker."),
        "option_b": str(decision_policy.get("option_b") or "Keep the project blocked or conditional until evidence exists."),
        "option_c": str(decision_policy.get("option_c") or "Pause this project from delivery claims."),
        "options": [
            str(decision_policy.get("option_a") or "Collect the project-specific evidence required by the current blocker."),
            str(decision_policy.get("option_b") or "Keep the project blocked or conditional until evidence exists."),
            str(decision_policy.get("option_c") or "Pause this project from delivery claims."),
        ],
        "estimated_effort": str(decision_policy.get("effort") or "project_owner review required"),
        "estimated_cost_or_resource": str(decision_policy.get("resource") or "owner time and evidence collection"),
        "expected_benefit": str(decision_policy.get("benefit") or "close the current evidence blocker"),
        "principal_risks": str(decision_policy.get("risks") or "evidence remains missing or unsuitable"),
        "evidence_required": str(decision_policy.get("evidence") or "project-specific evidence manifest"),
        "decision_deadline_or_priority": str(decision_policy.get("priority") or "P1"),
        "consequence_of_no_decision": str(decision_policy.get("no_decision") or "readiness remains blocked"),
        "unblock_task_id": next_task["task_id"],
        "acceptance_ids": next_task["acceptance_ids"] or ["HUMAN-ACTION-REQUIRED"],
        "generated_from_refs": [f"{project.get('path')}/docs/governance/ASSURANCE_STATUS.yaml", f"{project.get('path')}/docs/governance/delivery_tasks.yaml"],
        "last_reviewed_at": max_event_time(events),
    }
    for key, value in existing_owner_decision.items():
        if value not in (None, ""):
            owner_decision[key] = value
    if adp_s2pmt07_current:
        owner_decision["current_recommendation"] = adp_s2pmt07_current_recommendation(matrix)
        current_gate_text = str(matrix.get("current_gate") or "")
        current_iteration_text = str(matrix.get("current_iteration") or "")
        production_boundary_preflight_ready = (
            "INTEGRATED-PRODUCTION-ACCEPTANCE-PREFLIGHT" in current_iteration_text
            or "INTEGRATED_PRODUCTION_ACCEPTANCE_PREFLIGHT" in current_gate_text
            or "INTEGRATED-PRODUCTION-ACCEPTANCE-WRITE-GATE" in current_iteration_text
            or "INTEGRATED_PRODUCTION_ACCEPTANCE_WRITE_GATE" in current_gate_text
        )
        owner_decision_recorded_write_gate_allowed = (
            "WRITE_GATE_ALLOWED" in current_gate_text
            or "owner_production_boundary_decision_recorded=true" in str(matrix.get("current_v7_legacy_alias") or "")
            or "acceptance_write_gate_allowed=true" in str(matrix.get("current_v7_legacy_alias") or "")
        )
        integrated_production_accepted_no_daily_operation = (
            bool(matrix.get("stage2_integrated_production_accepted", False))
            or "INTEGRATED_PRODUCTION_ACCEPTED" in current_gate_text
            or "integrated_production_accepted=true" in str(matrix.get("current_v7_legacy_alias") or "")
        ) and not bool(matrix.get("s2pmt07_daily_operation_enabled", False))
        daily_operation_preflight_current = (
            "DAILY-OPERATION-AUTHORIZATION-PREFLIGHT" in current_iteration_text
            or "DAILY_OPERATION_AUTHORIZATION_PREFLIGHT" in current_gate_text
            or "daily operation authorization preflight" in str(matrix.get("current_v7_legacy_alias") or "").lower()
        )
        daily_operation_alias = str(matrix.get("current_v7_legacy_alias") or "")
        daily_operation_owner_decision_keep_disabled = (
            "DAILY-OPERATION-OWNER-DECISION-KEEP-DISABLED" in current_iteration_text
            or "DAILY_OPERATION_OWNER_DECISION_RECORDED_KEEP_DISABLED" in current_gate_text
            or "keep_daily_operation_disabled_no_persistent_authorization" in daily_operation_alias
        )
        daily_operation_persistent_authorization_missing = (
            "DAILY-OPERATION-PERSISTENT-AUTHORIZATION-GATE" in current_iteration_text
            or "DAILY_OPERATION_PERSISTENT_AUTHORIZATION_MISSING" in current_gate_text
            or "persistent_daily_operation_authorization_missing" in daily_operation_alias
        )
        daily_operation_persistent_authorization_request_ready = (
            "DAILY-OPERATION-PERSISTENT-AUTHORIZATION-REQUEST" in current_iteration_text
            or "DAILY_OPERATION_PERSISTENT_AUTHORIZATION_REQUEST_READY" in current_gate_text
            or "daily_operation_persistent_enablement_authorization.request.json" in daily_operation_alias
        )
        daily_operation_blockers = str(matrix.get("s2pmt07_daily_operation_authorization_preflight_blockers") or "")
        daily_operation_preflight_passed = bool(
            matrix.get("s2pmt07_daily_operation_authorization_preflight_passed", False)
        )
        daily_operation_gh_equivalent_repaired = (
            "github_open_pr_count_zero_api_v1" in daily_operation_alias
            or (
                "missing_gh_cli" not in daily_operation_blockers
                and "missing_smtp_secret_env_names" in daily_operation_blockers
            )
        )
        if daily_operation_persistent_authorization_request_ready:
            owner_decision["review_id"] = "S2PMT07-DAILY-OPERATION-PERSISTENT-AUTHORIZATION-REQUEST"
            owner_decision["decision_question"] = (
                "持久 DAILY_OPERATION 授权请求包已准备好；是否创建新的显式 owner 持久 "
                "DAILY_OPERATION 授权 artifact，或继续保持禁用。"
            )
            owner_decision["question"] = owner_decision["decision_question"]
            owner_decision["option_a"] = (
                "继续保持 DAILY_OPERATION 禁用；不创建授权 artifact，不启用 SMTP、scheduler、Release 或 production restore。"
            )
            owner_decision["option_b"] = (
                "若 owner 明确授权持久 DAILY_OPERATION，则提交 "
                "FINAL_ACCEPTANCE_BUNDLE/daily_operation_persistent_enablement_authorization.json，"
                "再跑 persistent authorization gate 和单独 enablement preflight。"
            )
            owner_decision["option_c"] = "禁止把 request artifact、一次受控运行验收或 keep-disabled 决策当作持久运行授权。"
            owner_decision["options"] = [
                owner_decision["option_a"],
                owner_decision["option_b"],
                owner_decision["option_c"],
            ]
            owner_decision["evidence_required"] = (
                "FINAL_ACCEPTANCE_BUNDLE/daily_operation_persistent_enablement_authorization.request.json, "
                "governance/run_manifests/ADP-S2PMT07-DAILY-OPERATION-PERSISTENT-AUTHORIZATION-REQUEST-20260701.json, "
                "FINAL_ACCEPTANCE_BUNDLE/daily_operation_persistent_enablement_authorization.json if owner authorizes, "
                "persistent ADP_ALLOW_SMTP_SEND=false, LaunchAgents disabled, open_pr_count=0, and no background ADP process"
            )
            owner_decision["unblock_task_id"] = next_task["task_id"]
        elif daily_operation_persistent_authorization_missing:
            owner_decision["review_id"] = "S2PMT07-DAILY-OPERATION-PERSISTENT-ENABLEMENT-AUTHORIZATION"
            owner_decision["decision_question"] = (
                "持久 DAILY_OPERATION 授权门已运行但阻断；是否提供新的显式 owner 持久 "
                "DAILY_OPERATION 授权 artifact，或继续保持禁用。"
            )
            owner_decision["question"] = owner_decision["decision_question"]
            owner_decision["option_a"] = (
                "继续保持 DAILY_OPERATION 禁用；不启用 SMTP、scheduler、Release 或 production restore。"
            )
            owner_decision["option_b"] = (
                "若 owner 明确授权持久 DAILY_OPERATION，则提交 "
                "FINAL_ACCEPTANCE_BUNDLE/daily_operation_persistent_enablement_authorization.json，"
                "再跑单独 enablement preflight。"
            )
            owner_decision["option_c"] = "禁止把一次受控运行验收或 keep-disabled 决策当作持久运行授权。"
            owner_decision["options"] = [
                owner_decision["option_a"],
                owner_decision["option_b"],
                owner_decision["option_c"],
            ]
            owner_decision["evidence_required"] = (
                "FINAL_ACCEPTANCE_BUNDLE/daily_operation_persistent_enablement_authorization_gate.json, "
                "governance/run_manifests/ADP-S2PMT07-DAILY-OPERATION-PERSISTENT-AUTHORIZATION-GATE-20260701.json, "
                "persistent_daily_operation_authorization_missing, "
                "FINAL_ACCEPTANCE_BUNDLE/daily_operation_persistent_enablement_authorization.json if owner authorizes, "
                "persistent ADP_ALLOW_SMTP_SEND=false, LaunchAgents disabled, open_pr_count=0, and no background ADP process"
            )
            owner_decision["unblock_task_id"] = next_task["task_id"]
        elif daily_operation_owner_decision_keep_disabled:
            owner_decision["review_id"] = "S2PMT07-DAILY-OPERATION-PERSISTENT-ENABLEMENT-AUTHORIZATION"
            owner_decision["decision_question"] = (
                "DAILY_OPERATION owner decision 已记录为保持禁用；是否提供新的显式 owner 持久 "
                "DAILY_OPERATION 授权 artifact，或继续保持 DAILY_OPERATION 禁用。"
            )
            owner_decision["question"] = owner_decision["decision_question"]
            owner_decision["option_a"] = (
                "继续保持 DAILY_OPERATION 禁用；不启用 SMTP、scheduler、Release 或 production restore。"
            )
            owner_decision["option_b"] = (
                "若 owner 明确授权持久 DAILY_OPERATION，则先写新的授权 artifact，再跑单独 enablement gate。"
            )
            owner_decision["option_c"] = "禁止把 keep-disabled artifact 当作运行授权并启用生产。"
            owner_decision["options"] = [
                owner_decision["option_a"],
                owner_decision["option_b"],
                owner_decision["option_c"],
            ]
            owner_decision["evidence_required"] = (
                "FINAL_ACCEPTANCE_BUNDLE/daily_operation_owner_authorization_decision.json, "
                "governance/run_manifests/ADP-S2PMT07-DAILY-OPERATION-OWNER-DECISION-KEEP-DISABLED-20260701.json, "
                "persistent ADP_ALLOW_SMTP_SEND=false, LaunchAgents disabled, open_pr_count=0, and no background ADP process"
            )
            owner_decision["unblock_task_id"] = next_task["task_id"]
        elif daily_operation_preflight_current:
            owner_decision["review_id"] = next_task["task_id"]
            if daily_operation_preflight_passed:
                owner_decision["decision_question"] = (
                    "DAILY_OPERATION 授权预检技术项已通过；是否记录显式 owner DAILY_OPERATION 持久运行授权，"
                    "或继续保持 DAILY_OPERATION 关闭。无论选择如何，预检 artifact 本身不得启用 "
                    "SMTP/scheduler/Release/restore。"
                )
            elif daily_operation_gh_equivalent_repaired:
                owner_decision["decision_question"] = (
                    "DAILY_OPERATION 授权预检已重跑但仍阻断；github_open_pr_count_zero_api_v1 已解除 gh CLI 阻断，"
                    "是否先补齐 SMTP secret env 名称并处理 OpenAIDatabase 大文件治理问题，并继续禁止 "
                    "SMTP/scheduler/Release/restore/DAILY_OPERATION。"
                )
            else:
                owner_decision["decision_question"] = (
                    "DAILY_OPERATION 授权预检已运行但阻断；具体阻断来自 production preflight，是否先修复 "
                    "gh CLI、SMTP secret env 名称和 OpenAIDatabase 大文件治理问题，并继续禁止 "
                    "SMTP/scheduler/Release/restore/DAILY_OPERATION。"
                )
            owner_decision["question"] = owner_decision["decision_question"]
            owner_decision["option_a"] = (
                "记录显式 DAILY_OPERATION owner 授权后，再由单独 enablement 任务决定是否启用；当前预检不启用运行。"
                if daily_operation_preflight_passed
                else "先修复 DAILY_OPERATION 预检前置条件，再重跑预检；预检通过前不得请求或启用持久日常运行。"
            )
            owner_decision["evidence_required"] = (
                "governance/run_manifests/ADP-S2PMT07-DAILY-OPERATION-SECRET-ARTIFACT-REPAIR-20260701.json, "
                "FINAL_ACCEPTANCE_BUNDLE/integrated_production_acceptance.json, "
                "owner DAILY_OPERATION authorization artifact, open_pr_count=0, ADP_ALLOW_SMTP_SEND=false before enablement, "
                "LaunchAgents disabled before enablement, and no background ADP process"
                if daily_operation_preflight_passed
                else (
                    "governance/run_manifests/ADP-S2PMT07-DAILY-OPERATION-GH-EQUIVALENT-REPAIR-20260701.json, "
                    "github_open_pr_count_zero_api_v1 reviewed equivalent or gh CLI availability, "
                    "ADP_SMTP_HOST/ADP_SMTP_PORT/ADP_SMTP_USERNAME/ADP_SMTP_PASSWORD env names without secret values, "
                    "and resolved OpenAIDatabase session-history archive git artifact hygiene blockers"
                )
            )
            owner_decision["unblock_task_id"] = next_task["task_id"]
        elif integrated_production_accepted_no_daily_operation:
            owner_decision["review_id"] = "S2PMT07-DAILY-OPERATION-AUTHORIZATION-PREFLIGHT"
            owner_decision["decision_question"] = (
                "INTEGRATED_PRODUCTION_ACCEPTED 证据已写入；是否进入单独 DAILY_OPERATION 授权预检，并继续禁止 "
                "SMTP/scheduler/Release/restore，直到该预检通过。"
            )
            owner_decision["question"] = owner_decision["decision_question"]
            owner_decision["option_a"] = (
                "进入 DAILY_OPERATION 授权预检：先证明持久 SMTP 开关、LaunchAgents、后台进程和运行边界仍安全，"
                "再由 owner 单独决定是否启用日常运行。"
            )
            owner_decision["evidence_required"] = (
                "FINAL_ACCEPTANCE_BUNDLE/integrated_production_acceptance.json, daily-operation authorization artifact, "
                "daily-operation preflight pass, persistent ADP_ALLOW_SMTP_SEND=false before enablement, LaunchAgents disabled before enablement, "
                "open_pr_count=0, and no background ADP process before enablement"
            )
            owner_decision["unblock_task_id"] = next_task["task_id"]
        elif owner_decision_recorded_write_gate_allowed:
            owner_decision["review_id"] = "S2PMT07-INTEGRATED-PRODUCTION-ACCEPTANCE-WRITE-GATE"
            owner_decision["decision_question"] = (
                "Owner 生产边界决策证据已记录，acceptance write gate 已允许；是否只写入 "
                "INTEGRATED_PRODUCTION_ACCEPTED 证据，并继续禁止 SMTP/scheduler/Release/DAILY_OPERATION。"
            )
            owner_decision["question"] = owner_decision["decision_question"]
            owner_decision["option_a"] = (
                "继续最终验收写入：只写入 INTEGRATED_PRODUCTION_ACCEPTED 证据，不启用 SMTP、"
                "scheduler、Release、restore 或 DAILY_OPERATION。"
            )
            owner_decision["evidence_required"] = (
                "FINAL_ACCEPTANCE_BUNDLE/owner_production_boundary_decision.json, passing owner decision artifact gate, "
                "passing acceptance write gate, final bundle manifest pass, no-production side-effect attestation pass, "
                "persistent ADP_ALLOW_SMTP_SEND=false, LaunchAgents disabled, open_pr_count=0, and no background ADP process"
            )
            owner_decision["unblock_task_id"] = next_task["task_id"]
        elif production_boundary_preflight_ready:
            owner_decision["review_id"] = (
                "S2PMT07-INTEGRATED-PRODUCTION-ACCEPTANCE-WRITE-GATE"
                if "WRITE_GATE" in current_gate_text or "WRITE-GATE" in current_iteration_text
                else "S2PMT07-INTEGRATED-PRODUCTION-ACCEPTANCE-PREFLIGHT"
            )
            owner_decision["decision_question"] = (
                "S2PMT07 production-boundary preflight 与 acceptance write-gate precheck 已通过；是否记录 owner 生产验收边界决策证据，"
                "进入最终 acceptance write gate，同时继续禁止自动启用 SMTP/scheduler/Release/DAILY_OPERATION。"
            )
            owner_decision["question"] = owner_decision["decision_question"]
            owner_decision["option_a"] = (
                "记录 owner 生产验收边界决策证据：preflight 已验证 final bundle ready、"
                "open_pr_count=0、持久 ADP_ALLOW_SMTP_SEND=false、LaunchAgents disabled、无后台 ADP 进程；"
                "下一步仍不得自动启用 SMTP/scheduler/Release/DAILY_OPERATION。"
            )
            owner_decision["evidence_required"] = (
                "owner review of FINAL_ACCEPTANCE_BUNDLE/owner_production_boundary_decision.request.json, "
                "preflight checks passed, final bundle manifest pass, no-production side-effect "
                "attestation pass, persistent ADP_ALLOW_SMTP_SEND=false, LaunchAgents disabled, "
                "open_pr_count=0, no background ADP process, and explicit owner production-boundary decision artifact"
            )
            owner_decision["unblock_task_id"] = next_task["task_id"]
        elif (
            "POST_FINAL_BUNDLE_CURRENT_STATE_SYNC" in current_gate_text
            or "FINAL_ACCEPTANCE_BUNDLE_READY_NO_PRODUCTION_ACCEPTANCE" in current_gate_text
            or "POST-FINAL-BUNDLE-CURRENT-STATE-SYNC" in current_iteration_text
        ):
            owner_decision["option_a"] = (
                "继续 S2PMT07 final bundle 后的生产边界预检：最终包、S2PLT04、final command、handoff、"
                "independent signoff 和 no-production attestation 均已通过；默认下一步只做 owner 生产验收边界决策和证据复核，"
                "不自动启用 SMTP/scheduler/Release/DAILY_OPERATION。"
            )
        elif "S2PLT03_TERMINAL_RESILIENCE_PROOF_READY" in current_gate_text:
            owner_decision["option_a"] = (
                "继续 S2PMT07 / S2PLT04 前置证据链：S2PLT02 terminal delivery proof 与 "
                "S2PLT03 terminal resilience proof 均已作为 no-production 输入通过，默认下一步只构建、"
                "独立复审并验证 S2PLT04 completion report，保持 final bundle/production gate 阻断。"
            )
        else:
            owner_decision["option_a"] = (
                "继续 S2PMT07 / S2PLT04 前置证据链：S2PLT02 terminal delivery proof 已作为 no-production 输入通过，"
                "默认下一步只构建、独立复审并验证 S2PLT03 terminal resilience proof，保持 S2PLT04/final bundle/production gate 阻断。"
            )
        options = list(structural.as_list(owner_decision.get("options")))
        if options:
            options[0] = owner_decision["option_a"]
            owner_decision["options"] = options
    if "decision_question" not in owner_decision and "question" in owner_decision:
        owner_decision["decision_question"] = owner_decision["question"]
    if "question" not in owner_decision and "decision_question" in owner_decision:
        owner_decision["question"] = owner_decision["decision_question"]

    delivery_readiness = {
        "status": assurance_status(str(policy.get("readiness") or "blocked")),
        "release_gate": release_gate,
        "blocker_ids": unresolved[:8],
    }
    if project_id == "arxiv-daily-push" and str(matrix.get("current_v7_contract_version") or "").startswith("ADP-PRODUCT-CONTRACT-V7."):
        delivery_readiness.update(
            {
                "v7_contract": str(matrix.get("current_v7_contract_version") or "UNKNOWN"),
                "v7_contract_hash": str(matrix.get("v7_product_contract_sha256") or "UNKNOWN"),
                "v7_roadmap_hash": str(matrix.get("v7_roadmap_sha256") or "UNKNOWN"),
                "v7_parallel_audit": str(matrix.get("v7_parallel_audit_version") or "UNKNOWN"),
                "v7_parallel_audit_hash": str(matrix.get("v7_parallel_audit_sha256") or "UNKNOWN"),
                "open_p0_findings": matrix.get("v7_open_p0_findings", "UNKNOWN"),
                "open_p1_findings": matrix.get("v7_open_p1_findings", "UNKNOWN"),
                "production_forbidden_until": str(matrix.get("stage2_production_forbidden_until") or "UNKNOWN"),
                "stage2_stop_gate": str(matrix.get("stage2_stop_gate") or "UNKNOWN"),
                "stage2_integrated_production_accepted": bool(
                    matrix.get("stage2_integrated_production_accepted", False)
                ),
                "current_zero_proof_open_p0_findings": matrix.get(
                    "current_zero_proof_open_p0_findings", "UNKNOWN"
                ),
                "current_zero_proof_open_p1_findings": matrix.get(
                    "current_zero_proof_open_p1_findings", "UNKNOWN"
                ),
                "baseline_counts_mutated": bool(matrix.get("baseline_counts_mutated", False)),
                "parallel_shadow_source_task": str(matrix.get("current_v7_shadow_source_task_id") or "UNKNOWN"),
                "current_v7_task_id": str(matrix.get("current_v7_task_id") or "UNKNOWN"),
            }
        )
        current_p0 = matrix.get("current_zero_proof_open_p0_findings")
        current_p1 = matrix.get("current_zero_proof_open_p1_findings")
        current_zero_known = current_p0 is not None and current_p1 is not None
        current_zero_open = int(current_p0 or 0) or int(current_p1 or 0)
        inherited_open = int(matrix.get("v7_open_p0_findings") or 0) or int(
            matrix.get("v7_open_p1_findings") or 0
        )
        if (current_zero_known and current_zero_open) or (not current_zero_known and inherited_open):
            delivery_readiness["blocker_ids"] = list(delivery_readiness["blocker_ids"]) + [
                "INHERITED_V7_1_AUDIT_P0_P1_OPEN"
            ]

    assurance = {
        "project_id": project_id,
        "as_of_event_id": str(events[-1].get("event_id") or events[-1].get("iteration_id") or "NONE") if events else "NONE",
        "source_snapshot_hash": source_hash,
        "source_base_commit": base_commit,
        "source_tree_hash": tree_hash,
        "snapshot_event_time": max_event_time(events),
        "generator_version": GENERATOR_VERSION,
        "final_commit_binding": final_commit_binding(events),
        "dimensions": {
            "structural_completeness": {
                "status": "VERIFIED",
                "fact_level": "EXTRACTED",
                "evidence_refs": ["scripts/validate_project_governance.py"],
            },
            "implementation_congruence": {
                "status": impl_status,
                "machine_verified_means": "documented implementation values and fingerprints match extractable code/config sources only",
                "fact_level": "EXTRACTED",
                "checked_active_parameters": counts["checked_parameters"],
                "total_active_parameters": counts["active_parameters"],
                "checked_active_formulas": counts["checked_formulas"],
                "total_active_formulas": counts["active_formulas"],
                "unresolved_fact_ids": [
                    item for item in unresolved if "IMPLEMENTATION" in item or "PARAM" in item or "FORM" in item
                ],
                "evidence_refs": [
                    f"{project.get('path')}/docs/governance/parameter_registry.csv",
                    f"{project.get('path')}/docs/governance/formula_registry.yaml",
                ],
            },
            "parameter_source_quality": {
                "status": parameter_source_status,
                "fact_level": "EXTRACTED" if parameter_source_status == "VERIFIED" else "UNKNOWN",
                "checked_active_parameters": counts["checked_parameters"],
                "total_active_parameters": counts["active_parameters"],
                "evidence_refs": [f"{project.get('path')}/docs/governance/parameter_registry.csv"],
            },
            "methodological_rationale": {
                "status": methodological_status,
                "fact_level": "UNKNOWN" if methodological_status == "UNVERIFIED" else "EXTRACTED",
                "machine_verified_means": "methodological, calibration, and baseline rationale are tracked separately from implementation congruence",
                "unresolved_fact_ids": [item for item in unresolved if "EMPIRICAL" in item],
                "evidence_refs": [f"{project.get('path')}/docs/governance/MODEL_SPEC.md"],
            },
            "empirical_validation": {
                "status": assurance_status(str(policy.get("empirical") or "unknown")),
                "fact_level": "UNKNOWN" if assurance_status(str(policy.get("empirical") or "unknown")) == "UNVERIFIED" else "EXTRACTED",
                "unresolved_fact_ids": [item for item in unresolved if "EMPIRICAL" in item],
                "evidence_refs": [f"{project.get('path')}/docs/governance/delivery_tasks.yaml"],
            },
            "operational_validation": {
                "status": assurance_status(str(policy.get("operational") or "unknown")),
                "fact_level": "UNKNOWN"
                if assurance_status(str(policy.get("operational") or "unknown")) == "UNVERIFIED"
                else "EXTRACTED",
                "unresolved_fact_ids": [item for item in unresolved if "OPERATIONAL" in item],
                "evidence_refs": [f"{project.get('path')}/docs/governance/development_events.jsonl"],
            },
            "delivery_evidence": {
                "status": "VERIFIED"
                if assurance_status(str(policy.get("readiness") or "blocked")) == "BLOCKED_PRECHECK"
                else assurance_status(str(policy.get("readiness") or "blocked")),
                "fact_level": "EXTRACTED",
                "evidence_refs": [f"{project.get('path')}/docs/governance/delivery_tasks.yaml"],
            },
            "evidence_freshness": {
                "status": evidence_freshness_status,
                "fact_level": "EXTRACTED",
                "tree_bound_events": event_counts["tree_bound_events"],
                "commit_bound_events": event_counts["commit_bound_events"],
                "legacy_unbound_events": event_counts["legacy_unbound_events"],
                "precommit_pending_events": event_counts["precommit_pending_events"],
                "evidence_refs": [f"{project.get('path')}/docs/governance/development_events.jsonl"],
            },
        },
        "delivery_readiness": delivery_readiness,
        "next_executable_task": next_task,
        "owner_decision": owner_decision,
    }
    return {
        "project_id": project_id,
        "path": str(project.get("path") or ""),
        "ci_mode": str(project.get("ci_mode") or ""),
        "product_version": str(matrix.get("product_version") or "UNKNOWN"),
        "current_iteration": str(matrix.get("current_iteration") or "UNKNOWN"),
        "current_phase": str(matrix.get("current_phase") or "UNKNOWN"),
        "current_gate": str(matrix.get("current_gate") or "UNKNOWN"),
        "counts": counts,
        "models": len(structural.as_list(parsed.get("models"))),
        "tasks": tasks,
        "events": events,
        "latest_event": events[-1] if events else {},
        "latest_manifest": manifest,
        "pending_event_count": pending_event_count(events),
        "event_binding_counts": event_counts,
        "unresolved_fact_ids": unresolved,
        "policy_blockers": list(policy.get("blockers") or []),
        "assurance": assurance,
    }


def brief_list(values: list[str], limit: int = 3) -> str:
    if not values:
        return "none"
    text = ", ".join(values[:limit])
    if len(values) > limit:
        text += f", +{len(values) - limit}"
    return text


def render_readme(projects: list[dict[str, Any]], meta: dict[str, str]) -> str:
    rows = "\n".join(
        f"| `{item['project_id']}` | `{item['path']}` | {PROJECT_REPOSITORIES.get(item['project_id'], 'UNKNOWN')} |"
        for item in projects
    )
    return f"""# CodexProject

Active Codex-related project hub for LinzeColin.

## Governance Entry

- Execution contract: [AGENTS.md](AGENTS.md)
- Lean v2 standard: [docs/governance/STANDARD.md](docs/governance/STANDARD.md)
- Project human-entry files: `功能清单.md`, `开发记录.md`, `模型参数文件.md`

## Assurance Vocabulary

- `structural_completeness`: required governance files parse and cross-reference.
- `implementation_congruence`: documented implementation values and fingerprints match extractable code/config sources.
- `parameter_source_quality`: active parameter values have source selectors or explicit unresolved tasks.
- `empirical_validation`: model claims are supported by calibration, backtest, fixture, or experiment evidence.
- `operational_validation`: runtime, CI, soak, or production-trial evidence exists.
- `delivery_evidence`: delivery gates and completed tasks have acceptance evidence.
- `evidence_freshness`: events are tree-bound, commit-bound, or honestly listed as legacy unbound.

`machine_verified` is not a production claim. It only maps to implementation congruence when code/config extraction proves documented facts.

## Projects

| Project | Path | Repository |
|---|---|---|
{rows}

## Required Checks

Use read-only changed-scope checks for ordinary PR and local development:

```bash
python3 scripts/lean_governance.py ci --changed-only --base-ref origin/main
```

Write-mode generators are not part of the ordinary PR fast gate. Run them only
for scheduled/manual/release governance evidence, and write root generated views
to an artifact directory instead of the tracked repository root:

```bash
python3 scripts/generate_governance_dashboard.py --write --changed-only --base-ref origin/main --root-artifact-dir /tmp/governance-generated-views
```

This repository is the source-level project hub. Each project directory must keep Lean v2 canonical facts and human-entry files synchronized with implementation evidence. Root dashboards and portfolio summaries are generated on demand as CI artifacts instead of committed source files.
"""


def render_dashboard(projects: list[dict[str, Any]], meta: dict[str, str]) -> str:
    lines = [
        "# Governance Dashboard",
        "",
        f"- source_base_commit: `{meta['source_base_commit']}`",
        f"- source_tree_hash: `{meta['source_tree_hash']}`",
        f"- source_snapshot_hash: `{meta['source_snapshot_hash']}`",
        f"- snapshot_event_time: `{meta['snapshot_event_time']}`",
        f"- generator_version: `{GENERATOR_VERSION}`",
        "- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`",
        "",
        "| Project | Version | Phase | Impl | Param Source | Methodology | Empirical | Operational | Freshness | Readiness | Next |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for item in projects:
        assurance = item["assurance"]
        dims = assurance["dimensions"]
        next_task = assurance["next_executable_task"]["task_id"]
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{item['project_id']}`",
                    f"`{item['product_version']}`",
                    f"`{item['current_phase']}`",
                    f"`{dims['implementation_congruence']['status']}`",
                    f"`{dims['parameter_source_quality']['status']}`",
                    f"`{dims['methodological_rationale']['status']}`",
                    f"`{dims['empirical_validation']['status']}`",
                    f"`{dims['operational_validation']['status']}`",
                    f"`{dims['evidence_freshness']['status']}`",
                    f"`{assurance['delivery_readiness']['status']}`",
                    f"`{next_task}`",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Implementation congruence only means documented values and fingerprints match code/config sources.",
            "- Empirical validation and operational validation are separate dimensions and may remain UNVERIFIED, PARTIAL, or FAILED.",
            "- Branch protection details remain `UNVERIFIED` unless checked by authenticated GitHub API or UI evidence.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_owner_portfolio(projects: list[dict[str, Any]], meta: dict[str, str]) -> str:
    decision_projects = [item for item in projects if item["assurance"]["owner_decision"]["required"]]
    blockers: list[str] = []
    for item in projects:
        for blocker in item["policy_blockers"][:2]:
            blockers.append(f"{item['project_id']}: {blocker}")
    buckets = {status: [] for status in sorted(ASSURANCE_STATUSES)}
    for item in projects:
        status = item["assurance"]["delivery_readiness"]["status"]
        buckets.setdefault(status, []).append(item)
    bucket_total = sum(len(values) for values in buckets.values())
    next_task = next(
        (
            item["assurance"]["next_executable_task"]
            for item in projects
            if item["assurance"]["next_executable_task"]["task_id"] != "NONE"
        ),
        {"task_id": "NONE", "reason": "No executable governance task selected."},
    )
    lines = [
        "# OWNER_PORTFOLIO",
        "",
        "## 1. 当前结论",
        "",
        "Review8-A 后，本仓库的 Owner 视图必须把结构完整、实现一致、方法依据、实证、运行和交付分开；当前 Portfolio 不是生产可用声明。",
        "",
        "## 2. 本次运行改变了什么",
        "",
        "- 状态桶现在覆盖 `FAILED`、`PARTIAL`、`UNVERIFIED`、`VERIFIED`、`NOT_APPLICABLE`，总数必须等于登记项目数。",
        "- Owner 决策改为项目特定的人类责任角色、资源、收益、风险、证据和不决策后果。",
        "- 陈旧的“创建首个治理基线”任务不得在事实已满足时继续作为下一任务。",
        "",
        "## 3. 为什么重要",
        "",
        "没有这些约束，仓库可能在 CI 绿色时仍输出错误汇总、陈旧任务或无责任人的资金/上线决策。",
        "",
        "## 4. 需要人类决定什么",
        "",
        "优先决定 P0/P1 项目是否投入真实数据、专家/法务/隐私/风险 owner 时间和验收证据；Codex 只能执行治理和验证，不能替代人类批准。",
        "",
        "## 5. 默认建议",
        "",
        f"- 下一唯一任务：`{next_task['task_id']}` - {next_task['reason']}",
        "- 默认策略：先关闭 P0 证据和人类责任 blocker，再进入项目 C0-C7 实证闭环。",
        "",
        "## 6. 不决策后果",
        "",
        "没有 owner 决策和证据投入的项目保持 `FAILED`、`PARTIAL` 或 `UNVERIFIED`，不得提升为交付就绪。",
        "",
        "## 7. 下一行动、责任角色和验收证据",
        "",
        f"- human_owner_role: `{next_task.get('human_owner_role') or next_task.get('owner')}`",
        f"- acceptance_ids: `{brief_list([str(x) for x in next_task.get('acceptance_ids', [])])}`",
        f"- unblock_condition: {next_task.get('unblock_condition')}",
        "",
        "## 8. 九层 Assurance 状态",
        "",
        f"- project_total: `{len(projects)}`",
        f"- bucket_total: `{bucket_total}`",
        f"- failed: `{len(buckets.get('FAILED', []))}`",
        f"- partial: `{len(buckets.get('PARTIAL', []))}`",
        f"- unverified: `{len(buckets.get('UNVERIFIED', []))}`",
        f"- verified: `{len(buckets.get('VERIFIED', []))}`",
        f"- not_applicable: `{len(buckets.get('NOT_APPLICABLE', []))}`",
        "",
        "| Bucket | Count | Projects |",
        "|---|---:|---|",
    ]
    for status in ["FAILED", "PARTIAL", "UNVERIFIED", "VERIFIED", "NOT_APPLICABLE"]:
        values = buckets.get(status, [])
        lines.append(f"| `{status}` | `{len(values)}` | {brief_list([item['project_id'] for item in values], 20)} |")
    lines.extend(
        [
            "",
            "## 9. 技术元数据",
            "",
        ]
    )
    lines.extend(
        [
        f"- source_base_commit: `{meta['source_base_commit']}`",
        f"- source_tree_hash: `{meta['source_tree_hash']}`",
        f"- source_snapshot_hash: `{meta['source_snapshot_hash']}`",
        f"- snapshot_event_time: `{meta['snapshot_event_time']}`",
        f"- generator_version: `{GENERATOR_VERSION}`",
        "- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`",
        "- branch_protection: `UNVERIFIED` unless authenticated setup doctor evidence is attached",
        "",
        "## 10. Top 5 Blockers",
        "",
        ]
    )
    for blocker in blockers[:5]:
        lines.append(f"- {blocker}")
    lines.extend(
        [
            "",
            "## 11. Owner Decisions",
            "",
        ]
    )
    for item in decision_projects:
        decision = item["assurance"]["owner_decision"]
        lines.extend(
            [
                f"### `{decision['decision_id']}`",
                "",
                f"- human_owner_role: `{decision['human_owner_role']}`",
                f"- recommendation: {decision['current_recommendation']}",
                f"- estimated_effort: {decision['estimated_effort']}",
                f"- estimated_cost_or_resource: {decision['estimated_cost_or_resource']}",
                f"- expected_benefit: {decision['expected_benefit']}",
                f"- principal_risks: {decision['principal_risks']}",
                f"- evidence_required: {decision['evidence_required']}",
                f"- no_decision_consequence: {decision['consequence_of_no_decision']}",
                "",
            ]
        )
    lines.extend(["", "## 12. Executable Tasks", ""])
    for item in projects:
        task = item["assurance"]["next_executable_task"]
        lines.append(f"- `{item['project_id']}`: `{task['task_id']}` - {task['reason']}")
    lines.extend(["", "## 13. Next Unique Governance Task", ""])
    lines.append(f"- `{next_task['task_id']}` - {next_task['reason']}")
    lines.extend(["", "## 14. Assurance Dimensions", ""])
    lines.append("| Project | Structural | Impl | Param Source | Methodology | Empirical | Operational | Delivery | Freshness | Readiness | Owner action |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for item in projects:
        dims = item["assurance"]["dimensions"]
        lines.append(
            f"| `{item['project_id']}` | `{dims['structural_completeness']['status']}` | "
            f"`{dims['implementation_congruence']['status']}` | `{dims['parameter_source_quality']['status']}` | "
            f"`{dims['methodological_rationale']['status']}` | "
            f"`{dims['empirical_validation']['status']}` | `{dims['operational_validation']['status']}` | "
            f"`{dims['delivery_evidence']['status']}` | `{dims['evidence_freshness']['status']}` | "
            f"`{item['assurance']['delivery_readiness']['status']}` | {item['assurance']['owner_decision']['decision_question']} |"
        )
    return "\n".join(lines) + "\n"


def render_status(item: dict[str, Any]) -> str:
    assurance = item["assurance"]
    dims = assurance["dimensions"]
    counts = item["counts"]
    delivery = assurance["delivery_readiness"]
    v7_delivery_lines = ""
    if delivery.get("stage2_stop_gate"):
        stage2_accepted = str(bool(delivery.get("stage2_integrated_production_accepted"))).lower()
        v7_delivery_lines = (
            f"- V7 contract: `{delivery.get('v7_contract', 'UNKNOWN')}`\n"
            f"- V7 contract hash: `{delivery.get('v7_contract_hash', 'UNKNOWN')}`\n"
            f"- V7 roadmap hash: `{delivery.get('v7_roadmap_hash', 'UNKNOWN')}`\n"
            f"- V7.1 parallel audit: `{delivery.get('v7_parallel_audit', 'UNKNOWN')}`\n"
            f"- V7.1 audit hash: `{delivery.get('v7_parallel_audit_hash', 'UNKNOWN')}`\n"
            f"- Open audit blockers: `P0={delivery.get('open_p0_findings', 'UNKNOWN')} / P1={delivery.get('open_p1_findings', 'UNKNOWN')}`\n"
            f"- Current zero-proof open findings: `P0={delivery.get('current_zero_proof_open_p0_findings', 'UNKNOWN')} / P1={delivery.get('current_zero_proof_open_p1_findings', 'UNKNOWN')}`\n"
            f"- Baseline counts mutated: `{str(bool(delivery.get('baseline_counts_mutated'))).lower()}`\n"
            f"- Production-forbidden until: `{delivery.get('production_forbidden_until', 'UNKNOWN')}`\n"
            f"- Stage 2 stop gate: `{delivery.get('stage2_stop_gate', 'UNKNOWN')}`\n"
            f"- Stage 2 integrated accepted: `{stage2_accepted}`\n"
            f"- Next governance task: `{delivery.get('current_v7_task_id', 'UNKNOWN')}`\n"
            f"- Parallel shadow source task: `{delivery.get('parallel_shadow_source_task', 'UNKNOWN')}`\n"
        )
    return f"""# Project Governance Status

## Snapshot Metadata

- source_base_commit: `{assurance['source_base_commit']}`
- source_tree_hash: `{assurance['source_tree_hash']}`
- source_snapshot_hash: `{assurance['source_snapshot_hash']}`
- snapshot_event_time: `{assurance['snapshot_event_time']}`
- generator_version: `{GENERATOR_VERSION}`
- final_commit_binding: `{assurance['final_commit_binding']}`

## Current State

- Project: `{item['project_id']}`
- Path: `{item['path']}`
- Product version: `{item['product_version']}`
- Phase/Gate: `{item['current_phase']} / {item['current_gate']}`
- Models/Formulas/Parameters total: `{item['models']} / {counts['total_formulas']} / {counts['total_parameters']}`
- Active formulas/parameters: `{counts['active_formulas']} / {counts['active_parameters']}`
- Machine checked formulas/parameters: `{counts['checked_formulas']} / {counts['checked_parameters']}`

## Assurance

| Dimension | Status | Evidence |
|---|---|---|
| structural_completeness | `{dims['structural_completeness']['status']}` | `{brief_list(dims['structural_completeness']['evidence_refs'])}` |
| implementation_congruence | `{dims['implementation_congruence']['status']}` | `{brief_list(dims['implementation_congruence']['evidence_refs'])}` |
| parameter_source_quality | `{dims['parameter_source_quality']['status']}` | `{brief_list(dims['parameter_source_quality']['evidence_refs'])}` |
| methodological_rationale | `{dims['methodological_rationale']['status']}` | `{brief_list(dims['methodological_rationale']['evidence_refs'])}` |
| empirical_validation | `{dims['empirical_validation']['status']}` | `{brief_list(dims['empirical_validation']['evidence_refs'])}` |
| operational_validation | `{dims['operational_validation']['status']}` | `{brief_list(dims['operational_validation']['evidence_refs'])}` |
| delivery_evidence | `{dims['delivery_evidence']['status']}` | `{brief_list(dims['delivery_evidence']['evidence_refs'])}` |
| evidence_freshness | `{dims['evidence_freshness']['status']}` | `{brief_list(dims['evidence_freshness']['evidence_refs'])}` |

## Delivery

- Readiness: `{assurance['delivery_readiness']['status']}`
- Release gate: `{assurance['delivery_readiness']['release_gate']}`
{v7_delivery_lines}- Next executable task: `{assurance['next_executable_task']['task_id']}`
- Pending/stale events: `{item['pending_event_count']}`
- Tree-bound events: `{item['event_binding_counts']['tree_bound_events']}`
- Commit-bound events: `{item['event_binding_counts']['commit_bound_events']}`
- Legacy unbound events: `{item['event_binding_counts']['legacy_unbound_events']}`
- Unresolved fact IDs: `{len(item['unresolved_fact_ids'])}`
"""


def render_owner_status(item: dict[str, Any]) -> str:
    assurance = item["assurance"]
    dims = assurance["dimensions"]
    counts = item["counts"]
    next_task = assurance["next_executable_task"]
    decision = assurance["owner_decision"]
    blockers = item["policy_blockers"][:3] or [decision["evidence_required"]]
    while len(blockers) < 3:
        blockers.append(f"{decision['human_owner_role']} must provide project-specific evidence before readiness can improve.")
    option_a = decision["option_a"]
    option_b = decision["option_b"]
    option_c = decision["option_c"]
    changed_summary = "Owner 视图现在把实现一致性、参数来源、方法依据、实证验证、运行验证、交付证据和证据新鲜度分开，避免把 `MACHINE_VERIFIED` 误读为模型有效或可上线。"
    if assurance["delivery_readiness"]["status"] == "VERIFIED" and item["project_id"] == "arxiv-daily-push":
        current_conclusion = (
            f"{item['project_id']} 当前治理结论：Stage 1 B1/arXiv 已达到 `ARXIV_PRODUCTION_ACCEPTED`，"
            "`ADP-S1P5T05` 已完成本机 Codex/local runner 与 2026-06-30 迁移准备；"
            "GitHub 只保留代码、PR/CI、证据、状态和备份角色，不作为每日生产 runner。"
        )
        if next_task["task_id"] == "ADP-S1P5T04-PRODUCTION-SCHEDULE-OWNER-DECISION-041":
            changed_summary = (
                "test10 已从 `main` 在 GitHub-hosted Ubuntu runner 上完成：run `28059194999` / run_number `10` "
                "证明邮件主题使用 Sydney 服务日期 `20260624`，Gmail SMTP 已发送到 `linzezhang35@gmail.com`。"
                "本次没有启用 production schedule、没有上传 Release、没有引入视频要求。"
            )
        elif next_task["task_id"] == "S2P1T01":
            changed_summary = (
                "`ADP-S1P5T05` 已把生产策略切到本机 Mac + Codex/local runner："
                "新增 local daily CLI、local preflight、queue/ledger/report/email preview 本地持久化、"
                "launchd package 草案和 2026-06-30 迁移 runbook。"
                "没有启用 GitHub cloud schedule、没有真实 SMTP 生产发送、没有 Release 上传、没有视频要求。"
            )
    else:
        current_conclusion = (
            f"{item['project_id']} 当前治理结论：实现一致性为 `{dims['implementation_congruence']['status']}`，"
            f"方法/实证为 `{dims['methodological_rationale']['status']}` / `{dims['empirical_validation']['status']}`，"
            f"交付状态为 `{assurance['delivery_readiness']['status']}`；这不是生产上线声明。"
        )
    return f"""# OWNER_STATUS

## 1. 当前结论

{current_conclusion}

## 2. 本次运行改变了什么

{changed_summary}

## 3. 为什么重要

{decision['expected_benefit']}

## 4. 需要人类决定什么

- decision_id: `{decision['decision_id']}`
- decision_question: {decision['decision_question']}
- human_owner_role: `{decision['human_owner_role']}`
- human_assignment_status: `{decision['human_assignment_status']}`

## 5. 默认建议

- current_recommendation: {decision['current_recommendation']}
- estimated_effort: {decision['estimated_effort']}
- estimated_cost_or_resource: {decision['estimated_cost_or_resource']}

## 6. 不决策后果

{decision['consequence_of_no_decision']}

## 7. 下一行动、责任角色和验收证据

- next_task_id: `{next_task['task_id']}`
- responsible_role: `{next_task['human_owner_role']}`
- acceptance_ids: `{brief_list([str(x) for x in next_task.get('acceptance_ids', [])])}`
- unblock_condition: {next_task['unblock_condition']}

## 8. 九层 Assurance 状态

- structural_completeness: `{dims['structural_completeness']['status']}`
- implementation_congruence: `{dims['implementation_congruence']['status']}` ({counts['checked_parameters']}/{counts['active_parameters']} active parameters, {counts['checked_formulas']}/{counts['active_formulas']} active formulas)
- parameter_source_quality: `{dims['parameter_source_quality']['status']}`
- methodological_rationale: `{dims['methodological_rationale']['status']}`
- empirical_validation: `{dims['empirical_validation']['status']}`
- operational_validation: `{dims['operational_validation']['status']}`
- delivery_evidence: `{dims['delivery_evidence']['status']}`
- evidence_freshness: `{dims['evidence_freshness']['status']}`
- delivery_readiness: `{assurance['delivery_readiness']['status']}`

## 9. A/B/C Choice Matrix

| Decision Item | Current Recommendation | Choice A | Choice B | Choice C | No Decision Consequence |
|---|---|---|---|---|---|
| `{decision['decision_id']}` | {decision['current_recommendation']} | {option_a} | {option_b} | {option_c} | {decision['consequence_of_no_decision']} |

## 10. Current Blockers

1. {blockers[0]}
2. {blockers[1]}
3. {blockers[2]}

## 11. Evidence Required To Unblock

- evidence_required: {decision['evidence_required']}
- principal_risks: {decision['principal_risks']}
- generated_from_refs: `{brief_list([str(x) for x in decision.get('generated_from_refs', [])])}`

## 12. Model Formula Parameter Change

- model_count: `{item['models']}`
- total_formulas: `{counts['total_formulas']}`
- active_formulas: `{counts['active_formulas']}`
- total_parameters: `{counts['total_parameters']}`
- active_parameters: `{counts['active_parameters']}`
- active_values_changed_by_this_view: `0`

## 13. Tests And Acceptance

- required_commands: `validate_project_governance --all --semantic --drift-report`; `generate_governance_dashboard --write`
- release_gate: `{assurance['delivery_readiness']['release_gate']}`

## 14. Evidence Freshness

- final_commit_binding: `{assurance['final_commit_binding']}`
- tree_bound_events: `{item['event_binding_counts']['tree_bound_events']}`
- commit_bound_events: `{item['event_binding_counts']['commit_bound_events']}`
- legacy_unbound_events: `{item['event_binding_counts']['legacy_unbound_events']}`
- precommit_pending_events: `{item['event_binding_counts']['precommit_pending_events']}`
- pending_or_stale_events: `{item['pending_event_count']}`

## 15. UNKNOWN

- unresolved_fact_ids: `{len(item['unresolved_fact_ids'])}`

## 16. 技术元数据

- source_base_commit: `{assurance['source_base_commit']}`
- source_tree_hash: `{assurance['source_tree_hash']}`
- source_snapshot_hash: `{assurance['source_snapshot_hash']}`
- snapshot_event_time: `{assurance['snapshot_event_time']}`
- generator_version: `{GENERATOR_VERSION}`
- version: `{item['product_version']}`
- phase/gate: `{item['current_phase']} / {item['current_gate']}`

## 17. Next Unique Task

- task_id: `{next_task['task_id']}`
- reason: {next_task['reason']}
"""


def render_binding_backlog(projects: list[dict[str, Any]], meta: dict[str, str]) -> str:
    payload = {
        "generated_by": "scripts/generate_governance_dashboard.py",
        "generator_version": GENERATOR_VERSION,
        "task_id": "GOV-REVIEW7-BINDING-BACKLOG-001",
        "source_base_commit": meta["source_base_commit"],
        "source_tree_hash": meta["source_tree_hash"],
        "source_snapshot_hash": meta["source_snapshot_hash"],
        "status": "open",
        "policy": "Legacy events are not rewritten. Future meaningful runs must be PRECOMMIT_TREE_BOUND before commit and commit-bound by CI attestation after merge.",
        "projects": [
            {
                "project_id": item["project_id"],
                "tree_bound_events": item["event_binding_counts"]["tree_bound_events"],
                "commit_bound_events": item["event_binding_counts"]["commit_bound_events"],
                "legacy_unbound_events": item["event_binding_counts"]["legacy_unbound_events"],
                "precommit_pending_events": item["event_binding_counts"]["precommit_pending_events"],
                "next_task": "GOV-REVIEW7-BINDING-BACKLOG-001"
                if item["event_binding_counts"]["legacy_unbound_events"]
                else "NOT_APPLICABLE",
            }
            for item in projects
        ],
    }
    return "\n".join(dump_yaml(payload)) + "\n"


ROOT_OUTPUT_REL_PATHS = [
    "README.md",
    "GOVERNANCE_DASHBOARD.md",
    "OWNER_PORTFOLIO.md",
    "governance/binding_backlog.yaml",
]


def select_projects(
    projects: list[dict[str, Any]], *, project_filter: str | None = None, changed_only: bool = False, base_ref: str | None = None
) -> tuple[list[dict[str, Any]], bool]:
    if project_filter:
        selected = [
            project
            for project in projects
            if project_filter in {str(project.get("project_id")), str(project.get("path"))}
        ]
        if not selected:
            raise SystemExit(f"Unknown project: {project_filter}")
        return selected, False
    if changed_only:
        changed = structural.git_changed_files(base_ref)
        selected = [project for project in projects if structural.project_matches_changed(project, changed)]
        include_root = any(path in changed for path in ROOT_OUTPUT_REL_PATHS)
        return selected, include_root
    return projects, True


def generate(
    write: bool,
    *,
    project_filter: str | None = None,
    changed_only: bool = False,
    base_ref: str | None = None,
    root_artifact_dir: Path | None = None,
) -> dict[str, Any]:
    config = structural.load_yaml(structural.PROJECTS_FILE)
    projects = [project for project in structural.as_list(config.get("projects")) if isinstance(project, dict)]
    selected_projects, include_root = select_projects(projects, project_filter=project_filter, changed_only=changed_only, base_ref=base_ref)
    infos = [load_project(project) for project in selected_projects]
    all_infos = [load_project(project) for project in projects] if include_root else infos
    portfolio_hash = source_snapshot_hash(
        [ROOT / "governance/projects.yaml"] + [ROOT / i["path"] / "docs/governance/parameter_registry.csv" for i in all_infos]
    )
    event_times = [info["assurance"]["snapshot_event_time"] for info in all_infos if info["assurance"]["snapshot_event_time"] != "UNKNOWN"]
    meta = {
        "source_base_commit": configured_source_base() or existing_root_base() or current_commit(),
        "source_tree_hash": configured_source_tree() or existing_root_tree() or current_tree_hash(),
        "source_snapshot_hash": portfolio_hash,
        "snapshot_event_time": max(event_times) if event_times else "UNKNOWN",
    }
    outputs: list[str] = []
    if include_root:
        root_outputs = {
            ROOT / "README.md": render_readme(all_infos, meta),
            ROOT / "GOVERNANCE_DASHBOARD.md": render_dashboard(all_infos, meta),
            ROOT / "OWNER_PORTFOLIO.md": render_owner_portfolio(all_infos, meta),
            ROOT / "governance" / "binding_backlog.yaml": render_binding_backlog(all_infos, meta),
        }
        for path, text in root_outputs.items():
            if write:
                target = root_artifact_dir / rel(path) if root_artifact_dir else path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(text, encoding="utf-8")
            outputs.append(rel(path))
    for info in infos:
        base = ROOT / info["path"] / "docs/governance"
        assurance_path = base / "ASSURANCE_STATUS.yaml"
        assurance_text = "\n".join(dump_yaml(info["assurance"])) + "\n"
        status_path = base / "STATUS.md"
        owner_path = base / "OWNER_STATUS.md"
        if write:
            assurance_path.write_text(assurance_text, encoding="utf-8")
            status_path.write_text(render_status(info), encoding="utf-8")
            owner_path.write_text(render_owner_status(info), encoding="utf-8")
        outputs.extend([rel(assurance_path), rel(status_path), rel(owner_path)])
    return {
        "status": "PASS",
        "write": write,
        "source_base_commit": meta["source_base_commit"],
        "source_snapshot_hash": meta["source_snapshot_hash"],
        "snapshot_event_time": meta["snapshot_event_time"],
        "generator_version": GENERATOR_VERSION,
        "outputs": outputs,
        "root_output_mode": "artifact" if root_artifact_dir else "tracked",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Write generated governance views.")
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument("--all", action="store_true", help="Generate all root and project governance views.")
    scope.add_argument("--project", help="Generate governance views for one project id or path.")
    scope.add_argument("--changed-only", action="store_true", help="Generate governance views for changed projects only.")
    parser.add_argument("--base-ref", help="Optional base ref for --changed-only.")
    parser.add_argument(
        "--root-artifact-dir",
        type=Path,
        help="Write root generated views under this artifact directory instead of the tracked repository root.",
    )
    args = parser.parse_args()
    print(
        json.dumps(
            generate(
                args.write,
                project_filter=args.project,
                changed_only=args.changed_only,
                base_ref=args.base_ref,
                root_artifact_dir=args.root_artifact_dir,
            ),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

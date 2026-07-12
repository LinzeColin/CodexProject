#!/usr/bin/env python3
"""Build the KMFA v0.1.4 S10-P1 post-remediation report entry."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools import v014_s09_post_remediation_stage_review as s09_phase
from KMFA.tools.check_v014_s09_post_remediation_stage_review import (
    validate_v014_s09_post_remediation_stage_review,
)
from KMFA.tools.check_v014_s10_p1_report_templates import (
    validate_v014_s10_p1_report_templates,
)
from KMFA.tools.report_templates import (
    REQUIRED_BUSINESS_OVERVIEW_SECTION_TITLES,
    REQUIRED_PROJECT_COST_SECTION_TITLES,
)


PHASE_ID = "V014_S10_P1_POST_REMEDIATION_REPORT_ENTRY"
ROADMAP_PHASE_ID = "S10-P1"
TASK_ID = "KMFA-V014-S10-P1-POST-REMEDIATION-REPORT-ENTRY-20260711"
ACCEPTANCE_ID = "ACC-V014-S10-P1-POST-REMEDIATION-REPORT-ENTRY"
VERSION = "0.1.4-s10-p1-post-remediation-report-entry"
STATUS = "completed_validated_local_only_management_report_entries_locked_no_go_upload_deferred"
DECISION = "NO_GO"
FORMULA_ID = "FORM-KMFA-V014-S10-P1-POST-REMEDIATION-REPORT-ENTRY-001"
PARAMETER_IDS = ("PARAM-KMFA-1696", "PARAM-KMFA-1697", "PARAM-KMFA-1698")
MODEL_REGISTRY_KEY = "kmfa_v014_s10_p1_post_remediation_report_entry"

OUTPUT_DIR = Path("KMFA/stage_artifacts") / PHASE_ID
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "report_entry_summary.json"
MANIFEST_PATH = MACHINE_DIR / "report_entry_manifest.json"
ENTRIES_PATH = MACHINE_DIR / "report_entries_public_safe.json"
GO_NO_GO_PATH = MACHINE_DIR / "report_entry_go_no_go_report.json"
COMPLETION_PATH = HUMAN_DIR / "s10_p1_completion_record_zh.md"
MANAGEMENT_PREVIEW_PATH = HUMAN_DIR / "management_report_entry_preview_zh.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results_zh.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register_zh.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan_zh.md"

QUALITY_DIR = Path("KMFA/metadata/quality")
METADATA_SUMMARY_PATH = QUALITY_DIR / "v014_s10_p1_post_remediation_report_entry_summary.json"
METADATA_MANIFEST_PATH = QUALITY_DIR / "v014_s10_p1_post_remediation_report_entry_manifest.json"
METADATA_ENTRIES_PATH = QUALITY_DIR / "v014_s10_p1_post_remediation_report_entries_public_safe.json"
METADATA_GO_NO_GO_PATH = QUALITY_DIR / "v014_s10_p1_post_remediation_report_entry_go_no_go_report.json"

PRIVATE_DIR = Path("KMFA/.codex_private_runtime/v014_s10_p1_post_remediation_report_entry")
PRIVATE_RAW_BEFORE_PATH = PRIVATE_DIR / "raw_immutability_before.json"
PRIVATE_RAW_AFTER_PATH = PRIVATE_DIR / "raw_immutability_after.json"
PRIVATE_VALIDATION_REPORT_PATH = PRIVATE_DIR / "s10_p1_report_entry_validation_zh.md"

DEVELOPMENT_EVENTS_PATH = Path("KMFA/docs/governance/development_events.jsonl")
STAGE_STATUS_PATH = Path("KMFA/metadata/stage_status.jsonl")
TASK_STATUS_PATH = Path("KMFA/metadata/traceability/v1_4_stage_phase_task_status.jsonl")


def _git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    return result.stdout.strip()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def _upsert_jsonl(path: Path, key: str, record: dict[str, Any]) -> None:
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    encoded = json.dumps(record, ensure_ascii=False, separators=(",", ":"))
    output: list[str] = []
    replaced = False
    for line in lines:
        if not line.strip():
            continue
        current = json.loads(line)
        if current.get(key) == record.get(key):
            if not replaced:
                output.append(encoded)
                replaced = True
            continue
        output.append(line)
    if not replaced:
        output.append(encoded)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(output) + "\n", encoding="utf-8")


def _report_entries() -> list[dict[str, Any]]:
    trust_status = "当前可信等级 Q4 / D，状态 NO_GO（未放行），仅供内部复核。"
    common = {
        "visible_trust_status": trust_status,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "business_values_included": False,
        "internal_technical_title_visible": False,
        "missing_value_rendered_as_zero": False,
        "authority_value_overwrite_allowed": False,
    }
    return [
        {
            "entry_id": "project_cost_special_report",
            "visible_title": "项目成本专题报告",
            "visible_sections": list(REQUIRED_PROJECT_COST_SECTION_TITLES),
            "visible_management_summary": [
                "九类成本结构已覆盖，差旅和利息已有唯一权威分项来源。",
                "权威显示与系统复算保持分离，禁止互相覆盖。",
                "九项非零差异和一项未完成比较继续保留。",
            ],
            **common,
        },
        {
            "entry_id": "business_overview_report",
            "visible_title": "经营总览报告",
            "visible_sections": list(REQUIRED_BUSINESS_OVERVIEW_SECTION_TITLES),
            "visible_management_summary": [
                "收入、开票、回款、现金、项目和税务按管理章节组织。",
                "十二项口径差异均保留可读原因、依据、责任和状态。",
                "三项现金口径缺少唯一权威数值来源，保持未决且不补零。",
            ],
            **common,
        },
    ]


def _raw_snapshot(label: str) -> dict[str, Any]:
    return s09_phase.residual_phase.prior_phase._raw_snapshot(label)


def _normalize_raw(snapshot: dict[str, Any]) -> Any:
    return s09_phase.residual_phase._normalize_snapshot(snapshot)


def build_payloads(*, final_validation: bool = False) -> dict[str, Any]:
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    raw_before = _raw_snapshot("before_v014_s10_p1_post_remediation_report_entry")
    s09 = validate_v014_s09_post_remediation_stage_review(require_private_evidence=False)
    historical_s10 = validate_v014_s10_p1_report_templates()
    raw_after = _raw_snapshot("after_v014_s10_p1_post_remediation_report_entry")
    prior_raw = _read_json(s09_phase.PRIVATE_RAW_AFTER_PATH)

    raw_exact = _normalize_raw(raw_before) == _normalize_raw(raw_after)
    raw_cross_phase_exact = _normalize_raw(raw_before) == _normalize_raw(prior_raw)
    if not raw_exact or not raw_cross_phase_exact:
        raise ValueError("raw source changed during S10-P1 post-remediation report entry")

    entries = _report_entries()
    summary = {
        "schema_version": "kmfa.v014.s10_p1.post_remediation_report_entry_summary.v1",
        "project_id": "KMFA",
        "stage_id": "S10",
        "phase_id": PHASE_ID,
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "status": STATUS,
        "decision": DECISION,
        "report_template_count": len(entries),
        "management_section_count": sum(len(entry["visible_sections"]) for entry in entries),
        "project_cost_section_count": len(entries[0]["visible_sections"]),
        "business_overview_section_count": len(entries[1]["visible_sections"]),
        "cost_category_count": s09["cost_category_count"],
        "human_readable_reconciliation_count": s09["human_readable_reconciliation_count"],
        "queue_closed_or_excluded_count": s09["queue_closed_or_excluded_count"],
        "open_final_difference_accepted_count": s09["open_final_difference_accepted_count"],
        "nonzero_delta_reconciliation_count": s09["nonzero_delta_reconciliation_count"],
        "zero_delta_reconciliation_count": s09["zero_delta_reconciliation_count"],
        "incomplete_reconciliation_count": s09["incomplete_reconciliation_count"],
        "forced_zero_materialization_count": s09["forced_zero_materialization_count"],
        "missing_cash_value_materialized_as_zero_count": 0,
        "authority_system_overwrite_allowed_count": s09["authority_system_overwrite_allowed_count"],
        "current_data_quality_grade": s09["current_data_quality_grade"],
        "current_report_grade": s09["current_report_grade"],
        "release_permission": s09["release_permission"],
        "formal_report_count": 0,
        "export_artifact_count": 0,
        "raw_source_file_count": raw_before["file_count"],
        "raw_snapshot_exact_match": raw_exact,
        "raw_cross_phase_snapshot_exact_match": raw_cross_phase_exact,
    }
    trust_entry = {
        "current_data_quality_grade": summary["current_data_quality_grade"],
        "current_report_grade": summary["current_report_grade"],
        "decision": DECISION,
        "visible_release_label": "未放行",
        "visible_usage_label": "仅供内部复核，不作为正式经营决策依据",
        "inherited_from_stage9_post_remediation_review": True,
        "grade_calculation_performed_by_this_phase": False,
        "grade_override_allowed": False,
    }
    release_gate = {
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "delivery_allowed": False,
        "report_runtime_performed": False,
        "report_export_performed": False,
    }
    phase_boundaries = {
        "s10_p1_performed": True,
        "s10_p2_performed": False,
        "s10_p3_performed": False,
        "stage10_review_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
    raw_boundary = {
        "raw_read_authorized": True,
        "raw_snapshot_validation_performed": True,
        "raw_write_performed": False,
        "raw_delete_performed": False,
        "raw_move_performed": False,
        "raw_rename_performed": False,
        "raw_overwrite_performed": False,
        "raw_mutation_performed": False,
    }
    public_repo_safety = {
        "aggregate_only": True,
        "raw_file_committed": False,
        "raw_filename_committed": False,
        "raw_hash_committed": False,
        "field_or_header_plaintext_committed": False,
        "business_value_committed": False,
        "project_or_customer_plaintext_committed": False,
        "private_runtime_committed": False,
        "credential_or_secret_committed": False,
    }
    entries_document = {
        "schema_version": "kmfa.v014.s10_p1.post_remediation_report_entries_public_safe.v1",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "report_entries": entries,
    }
    manifest = {
        "schema_version": "kmfa.v014.s10_p1.post_remediation_report_entry_manifest.v1",
        "project_id": "KMFA",
        "version": VERSION,
        "stage_id": "S10",
        "phase_id": PHASE_ID,
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": generated_at,
        "reviewed_head": _git_output(["rev-parse", "HEAD"]),
        "branch": _git_output(["branch", "--show-current"]),
        "status": STATUS,
        "decision": DECISION,
        "summary": summary,
        "report_entries": entries,
        "trust_entry": trust_entry,
        "release_gate": release_gate,
        "phase_boundaries": phase_boundaries,
        "raw_boundary": raw_boundary,
        "public_repo_safety": public_repo_safety,
        "dependencies": {
            "stage9_post_remediation_review_validated": True,
            "historical_s10_p1_structure_validated": historical_s10.get("template_count") == 2,
            "historical_dynamic_state_reused": False,
            "current_stage9_state_authoritative": True,
        },
        "source_evidence_refs": {
            "current_stage9_review": s09_phase.MANIFEST_PATH.as_posix(),
            "historical_s10_p1_structure": "KMFA/stage_artifacts/V014_S10_P1_REPORT_TEMPLATES/machine/report_templates_manifest.json",
            "roadmap": "KMFA/taskpack/v1_4/roadmap/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_4.md",
        },
        "artifact_refs": {
            "summary": SUMMARY_PATH.as_posix(),
            "entries": ENTRIES_PATH.as_posix(),
            "go_no_go": GO_NO_GO_PATH.as_posix(),
            "management_preview": MANAGEMENT_PREVIEW_PATH.as_posix(),
            "completion": COMPLETION_PATH.as_posix(),
            "test_results": TEST_RESULTS_PATH.as_posix(),
            "validator": "KMFA/tools/check_v014_s10_p1_post_remediation_report_entry.py",
        },
        "validation_summary": {
            "red_test_observed": True,
            "focused_tests": "PASS" if final_validation else "PENDING",
            "strict_validator": "PASS" if final_validation else "PENDING",
            "stage9_dependency": "PASS",
            "historical_s10_p1_structure": "PASS",
            "raw_snapshot_exact": "PASS",
            "governance_and_safety_scans": "PASS" if final_validation else "PENDING",
            "final_validation_recorded": final_validation,
        },
        "next_required_phase": "S10-P2",
    }
    go_no_go = {
        "schema_version": "kmfa.v014.s10_p1.post_remediation_report_entry_go_no_go.v1",
        "project_id": "KMFA",
        "stage_id": "S10",
        "phase_id": PHASE_ID,
        "decision": DECISION,
        "current_data_quality_grade": summary["current_data_quality_grade"],
        "current_report_grade": summary["current_report_grade"],
        "blocking_reason_codes": [
            "three_cash_slots_lack_unique_authority_source",
            "nine_nonzero_differences_remain_preserved",
            "one_reconciliation_remains_incomplete",
            "full_business_value_consistency_not_verified",
        ],
        "formal_report_allowed": False,
        "github_upload_performed": False,
    }
    return {
        "summary": summary,
        "manifest": manifest,
        "entries": entries_document,
        "go_no_go": go_no_go,
        "private": {
            "raw_before": raw_before,
            "raw_after": raw_after,
        },
    }


def _render_management_preview(manifest: dict[str, Any]) -> str:
    lines = [
        "# KMFA 管理报告入口预览",
        "",
        "## 当前可信状态",
        "",
        "- 当前可信等级：Q4 / D",
        "- 当前状态：NO_GO（未放行）",
        "- 使用限制：仅供内部复核，不作为正式经营决策依据",
        "",
    ]
    for entry in manifest["report_entries"]:
        lines.extend([f"## {entry['visible_title']}", ""])
        for section in entry["visible_sections"]:
            lines.append(f"### {section}")
        lines.append("")
        lines.extend(f"- {item}" for item in entry["visible_management_summary"])
        lines.append("")
    lines.extend(
        [
            "## 当前限制",
            "",
            "- 三项现金口径缺少唯一权威数值来源，保持未决且不补零。",
            "- 九项非零差异继续保留，不覆盖、不静默通过。",
            "- 一项比较尚未完成，完整业务一致性未成立。",
        ]
    )
    return "\n".join(lines)


def _render_completion(manifest: dict[str, Any]) -> str:
    summary = manifest["summary"]
    return f"""# KMFA v0.1.4 S10-P1 修补后报告入口完成记录

- phase：`{PHASE_ID}`
- roadmap phase：`{ROADMAP_PHASE_ID}`
- status：`{STATUS}`
- decision：`{DECISION}`
- 模板 / 管理章节：`{summary['report_template_count']} / {summary['management_section_count']}`
- 当前差异：`{summary['queue_closed_or_excluded_count']} closed-or-excluded / {summary['open_final_difference_accepted_count']} final-accepted-open`
- 非零 / 零 / 未完成：`{summary['nonzero_delta_reconciliation_count']} / {summary['zero_delta_reconciliation_count']} / {summary['incomplete_reconciliation_count']}`
- 可信等级：`{summary['current_data_quality_grade']} / {summary['current_report_grade']} / {DECISION}`
- missing cash 写零 / authority overwrite：`{summary['missing_cash_value_materialized_as_zero_count']} / {summary['authority_system_overwrite_allowed_count']}`
- S10-P2 / S10-P3 / Stage 10 review：`false / false / false`
- GitHub upload / app reinstall / business execution：`false / false / false`

本 phase 只建立管理可读模板与继承可信状态入口，不计算新等级、不生成正式报告或导出物。
"""


def _render_test_results(manifest: dict[str, Any]) -> str:
    final = manifest["validation_summary"]["final_validation_recorded"]
    state = "PASS" if final else "PENDING"
    return f"""# KMFA v0.1.4 S10-P1 修补后报告入口测试结果

- RED：`PASS`，已观察到实现缺失断言失败。
- focused tests：`{state}`
- strict validator：`{state}`
- Stage 9 post-remediation dependency：`PASS`
- historical S10-P1 structural baseline：`PASS`
- raw before/after/cross-phase snapshot：`PASS`
- governance / no-float / no-omission / structured parse / secret scan：`{state}`
- final validation recorded：`{str(final).lower()}`
- GitHub upload：`false`
"""


def _render_private_report(summary: dict[str, Any]) -> str:
    return f"""# S10-P1 报告入口私有验证记录

- 原始文件数量：{summary['raw_source_file_count']}
- 本 phase 前后快照一致：{str(summary['raw_snapshot_exact_match']).lower()}
- 与 Stage 9 快照一致：{str(summary['raw_cross_phase_snapshot_exact_match']).lower()}
- 三项现金缺失保持未决且未补零。
- 九项非零差异保持原样，未覆盖权威值。
"""


def _phase_public_files() -> list[str]:
    return [
        path.as_posix()
        for path in (
            SUMMARY_PATH,
            MANIFEST_PATH,
            ENTRIES_PATH,
            GO_NO_GO_PATH,
            COMPLETION_PATH,
            MANAGEMENT_PREVIEW_PATH,
            TEST_RESULTS_PATH,
            RISK_REGISTER_PATH,
            ROLLBACK_PATH,
            METADATA_SUMMARY_PATH,
            METADATA_MANIFEST_PATH,
            METADATA_ENTRIES_PATH,
            METADATA_GO_NO_GO_PATH,
        )
    ] + [
        "KMFA/tools/v014_s10_p1_post_remediation_report_entry.py",
        "KMFA/tools/check_v014_s10_p1_post_remediation_report_entry.py",
        "KMFA/tests/test_v014_s10_p1_post_remediation_report_entry.py",
    ]


def _write_governance(generated_at: str) -> None:
    evidence_ref = MANIFEST_PATH.as_posix()
    _upsert_jsonl(
        DEVELOPMENT_EVENTS_PATH,
        "event_id",
        {
            "event_id": "DEV-KMFA-20260711-V014-S10-P1-POST-REMEDIATION-REPORT-ENTRY",
            "event_time": generated_at,
            "event_type": "development",
            "project_id": "KMFA",
            "stage_id": "S10",
            "phase_id": PHASE_ID,
            "roadmap_phase_id": ROADMAP_PHASE_ID,
            "task_id": TASK_ID,
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "decision": DECISION,
            "raw_business_data_committed": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "business_execution_performed": False,
            "evidence_ref": evidence_ref,
            "files_changed": _phase_public_files(),
            "result_commit": "PENDING",
        },
    )
    _upsert_jsonl(
        STAGE_STATUS_PATH,
        "phase_id",
        {
            "schema_version": "kmfa.stage_status.v1",
            "record_type": "phase_status",
            "project_id": "KMFA",
            "stage_id": "S10",
            "phase_id": PHASE_ID,
            "roadmap_phase_id": ROADMAP_PHASE_ID,
            "task_id": TASK_ID,
            "version": VERSION,
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "decision": DECISION,
            "raw_data_committed": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "business_execution_performed": False,
            "evidence_ref": evidence_ref,
            "updated_at": generated_at,
        },
    )
    _upsert_jsonl(
        TASK_STATUS_PATH,
        "phase_id",
        {
            "schema_version": "kmfa.v014_stage_phase_task_status.v1",
            "record_type": "v014_phase",
            "project_id": "KMFA",
            "stage_id": "S10",
            "governance_stage_id": "REPORT-TRUST-AND-GENERATION",
            "roadmap_stage_id": "S10",
            "roadmap_phase_id": ROADMAP_PHASE_ID,
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "version": VERSION,
            "name": "v0.1.4 S10-P1 post-remediation report entry",
            "phase_goal": "bind management-readable report templates to current Stage 9 trust and blocker state",
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "derived_percent": 100,
            "estimated_task_units": 1,
            "completed_task_units": 1,
            "task_count": 1,
            "raw_data_committed": False,
            "evidence_ref": evidence_ref,
            "updated_at": generated_at[:10],
        },
    )


def generate(*, final_validation: bool = False, write_governance: bool = True) -> dict[str, Any]:
    payloads = build_payloads(final_validation=final_validation)
    for path, payload in (
        (SUMMARY_PATH, payloads["summary"]),
        (MANIFEST_PATH, payloads["manifest"]),
        (ENTRIES_PATH, payloads["entries"]),
        (GO_NO_GO_PATH, payloads["go_no_go"]),
        (METADATA_SUMMARY_PATH, payloads["summary"]),
        (METADATA_MANIFEST_PATH, payloads["manifest"]),
        (METADATA_ENTRIES_PATH, payloads["entries"]),
        (METADATA_GO_NO_GO_PATH, payloads["go_no_go"]),
        (PRIVATE_RAW_BEFORE_PATH, payloads["private"]["raw_before"]),
        (PRIVATE_RAW_AFTER_PATH, payloads["private"]["raw_after"]),
    ):
        _write_json(path, payload)
    _write_text(COMPLETION_PATH, _render_completion(payloads["manifest"]))
    _write_text(MANAGEMENT_PREVIEW_PATH, _render_management_preview(payloads["manifest"]))
    _write_text(TEST_RESULTS_PATH, _render_test_results(payloads["manifest"]))
    _write_text(
        RISK_REGISTER_PATH,
        """# S10-P1 修补后报告入口风险登记

| 风险 | 控制 | 状态 |
|---|---|---|
| 缺失现金被显示为零 | 明确保持三项未决，missing-to-zero 固定为 0 | controlled |
| 历史 12 pending 状态污染当前入口 | 仅复用旧模板结构，动态状态绑定最新 Stage 9 证据 | controlled |
| inherited grade 被误解为 S10-P2 计算 | 标记仅继承展示，grade calculation=false | controlled |
| 模板被误当成正式报告 | formal report、decision basis、delivery 均为 false | controlled |
""",
    )
    _write_text(
        ROLLBACK_PATH,
        f"""# S10-P1 修补后报告入口回滚计划

1. 回退本 phase 的本地 commit 和 `{OUTPUT_DIR.as_posix()}` 公开证据。
2. 删除本 phase ignored private runtime 草稿，不触碰原始目录。
3. 恢复到 Stage 9 post-remediation review 的 `Q4 / D / NO_GO` 状态。
4. 不回退、不移动、不删除、不覆盖任何原始文件。
""",
    )
    _write_text(PRIVATE_VALIDATION_REPORT_PATH, _render_private_report(payloads["summary"]))
    if write_governance:
        _write_governance(payloads["manifest"]["generated_at"])
    return payloads["manifest"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--final-validation", action="store_true")
    args = parser.parse_args()
    manifest = generate(final_validation=args.final_validation)
    summary = manifest["summary"]
    print(
        "S10-P1 post-remediation report entry: "
        f"templates={summary['report_template_count']} sections={summary['management_section_count']} "
        f"closed_or_excluded={summary['queue_closed_or_excluded_count']} "
        f"open_final={summary['open_final_difference_accepted_count']} decision={manifest['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

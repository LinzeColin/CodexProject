from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PHASE_ID = "V014_RAW_PROCESSED_ALIGNMENT_BLOCKER_REPORT"
TASK_ID = "KMFA-V014-RAW-PROCESSED-ALIGNMENT-BLOCKER-REPORT-20260706"
VERSION = "0.1.4-raw-processed-alignment-blocker-report"
STATUS = "completed_validated_local_only_no_go_alignment_blocker_report"
DECISION = "NO_GO"
NEXT_REQUIRED_INPUT = "owner_or_authorized_delegate_supplies_target_slot_to_processed_value_source_map"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
QUALITY_DIR = PROJECT_ROOT / "metadata" / "quality"

SUMMARY_PATH = MACHINE_DIR / "raw_processed_alignment_blocker_summary.json"
MANIFEST_PATH = MACHINE_DIR / "raw_processed_alignment_blocker_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "raw_processed_alignment_blocker_go_no_go_report.json"
REPORT_PATH = HUMAN_DIR / "raw_processed_alignment_blocker_report.md"
DIAGNOSTIC_PACKET_PATH = HUMAN_DIR / "chatgpt_agent_diagnostic_packet.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = QUALITY_DIR / "v014_raw_processed_alignment_blocker_summary.json"
METADATA_MANIFEST_PATH = QUALITY_DIR / "v014_raw_processed_alignment_blocker_manifest.json"
METADATA_GO_NO_GO_PATH = QUALITY_DIR / "v014_raw_processed_alignment_blocker_go_no_go_report.json"

SOURCE_ARTIFACTS = {
    "value_scope": PROJECT_ROOT
    / "stage_artifacts/V014_VALUE_CONSISTENCY_SCOPE_GATE/machine/value_consistency_scope_go_no_go_report.json",
    "raw_matching": PROJECT_ROOT
    / "stage_artifacts/V014_RAW_VALUE_MATCHING_PRIVATE_DRY_RUN/machine/raw_value_matching_private_dry_run_go_no_go_report.json",
    "processed_staging": PROJECT_ROOT
    / "stage_artifacts/V014_PRIVATE_PROCESSED_VALUE_STAGING/machine/private_processed_value_staging_summary.json",
    "source_resolution": PROJECT_ROOT
    / "stage_artifacts/V014_PRIVATE_PROCESSED_VALUE_SOURCE_RESOLUTION/machine/private_processed_value_source_resolution_summary.json",
    "source_map_capture": PROJECT_ROOT
    / "stage_artifacts/V014_PRIVATE_PROCESSED_VALUE_SOURCE_MAP_CAPTURE/machine/private_processed_value_source_map_capture_summary.json",
    "authorized_fill": PROJECT_ROOT
    / "stage_artifacts/V014_PRIVATE_PROCESSED_VALUE_SOURCE_MAP_AUTHORIZED_FILL/machine/private_processed_value_source_map_authorized_fill_summary.json",
    "gap_resolution": PROJECT_ROOT
    / "stage_artifacts/V014_PRIVATE_PROCESSED_VALUE_SOURCE_MAP_AUTHORIZED_FILL_GAP_RESOLUTION/machine/private_processed_value_source_map_gap_resolution_summary.json",
    "owner_application": PROJECT_ROOT
    / "stage_artifacts/V014_PRIVATE_PROCESSED_VALUE_SOURCE_MAP_OWNER_AUTHORIZED_FILL_APPLICATION/machine/private_processed_value_source_map_owner_authorized_fill_application_summary.json",
    "comparability": PROJECT_ROOT
    / "stage_artifacts/V014_RAW_PROCESSED_COMPARABILITY_DIAGNOSTIC/machine/raw_processed_comparability_diagnostic_summary.json",
    "overall_review": PROJECT_ROOT
    / "stage_artifacts/V014_STAGE1_18_OVERALL_REVIEW/machine/stage1_18_overall_go_no_go_report.json",
}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _get(data: dict[str, Any], *keys: str, default: Any = 0) -> Any:
    for key in keys:
        if key in data:
            return data[key]
    return default


def _load_inputs() -> dict[str, dict[str, Any]]:
    missing = [str(path) for path in SOURCE_ARTIFACTS.values() if not path.exists()]
    if missing:
        raise FileNotFoundError("missing source artifacts: " + ", ".join(missing))
    return {name: _read_json(path) for name, path in SOURCE_ARTIFACTS.items()}


def _build_summary(inputs: dict[str, dict[str, Any]], generated_at: str) -> dict[str, Any]:
    staging = inputs["processed_staging"]
    source_resolution = inputs["source_resolution"]
    capture = inputs["source_map_capture"]
    authorized_fill = inputs["authorized_fill"]
    gap_resolution = inputs["gap_resolution"]
    owner_application = inputs["owner_application"]
    comparability = inputs["comparability"]
    overall_review = inputs["overall_review"]

    blocker_chain = [
        "processed_targets_are_path_only",
        "staged_processed_value_fingerprint_count_is_zero",
        "usable_processed_source_map_count_is_zero",
        "authorized_source_map_is_partial",
        "active_owner_record_is_keep_pending_only",
        "raw_processed_structural_key_intersection_is_zero",
        "comparable_value_pair_count_is_zero",
    ]
    blocked_operations = [
        "processed_value_materialization_replay",
        "raw_to_processed_value_comparison",
        "processed_data_reconciliation",
        "business_value_consistency_verification",
        "lineage_full_check",
        "formal_report_release",
        "github_upload",
        "app_reinstall",
        "business_execution",
    ]

    return {
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "status": STATUS,
        "generated_at": generated_at,
        "decision": DECISION,
        "source_artifact_count": len(SOURCE_ARTIFACTS),
        "raw_value_fingerprint_count": _get(
            comparability, "prior_raw_value_fingerprint_record_count"
        ),
        "raw_unique_numeric_fingerprint_count": _get(
            comparability, "prior_raw_unique_numeric_fingerprint_count"
        ),
        "raw_root_file_count": _get(comparability, "raw_root_file_count"),
        "raw_root_stat_unchanged_after_phase": bool(
            _get(comparability, "raw_root_stat_unchanged_after_phase", default=False)
        ),
        "raw_inbox_mutation_detected": bool(_get(comparability, "raw_inbox_mutation_detected", default=True)),
        "processed_target_slot_count": _get(staging, "processed_target_slot_count"),
        "approved_private_processed_target_slot_count": _get(
            staging, "approved_private_processed_target_slot_count"
        ),
        "staged_processed_value_fingerprint_count": _get(
            comparability,
            "staged_processed_value_fingerprint_count",
            "private_processed_value_fingerprint_count",
        ),
        "private_processed_value_fingerprint_count": _get(
            staging, "private_processed_value_fingerprint_count"
        ),
        "usable_processed_source_map_count": _get(
            source_resolution, "usable_private_processed_value_source_map_count"
        ),
        "resolved_processed_value_source_count": _get(
            source_resolution, "resolved_processed_value_source_count"
        ),
        "captured_processed_value_fingerprint_count": _get(
            capture, "captured_processed_value_fingerprint_count"
        ),
        "authorized_filled_item_count": _get(authorized_fill, "authorized_filled_item_count"),
        "authorized_unfilled_item_count": _get(authorized_fill, "authorized_unfilled_item_count"),
        "source_map_records_written_count": _get(
            authorized_fill, "source_map_records_written_count"
        ),
        "unresolved_gap_item_count": _get(gap_resolution, "unresolved_gap_item_count"),
        "active_fill_record_keep_pending_count": _get(
            owner_application, "active_fill_record_keep_pending_count"
        ),
        "source_map_records_applied_count": _get(owner_application, "source_map_records_applied_count"),
        "new_authorized_fingerprint_count": _get(
            owner_application, "new_authorized_fingerprint_count"
        ),
        "raw_processed_structural_key_intersection_count": _get(
            comparability, "raw_processed_structural_key_intersection_count"
        ),
        "comparable_value_pair_count": _get(comparability, "comparable_value_pair_count"),
        "business_value_consistency_verified": False,
        "raw_to_processed_value_comparison_performed": False,
        "processed_data_reconciliation_performed": False,
        "lineage_full_check_complete": False,
        "formal_report_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "overall_review_blocker_count": len(overall_review.get("blocker_ids", [])),
        "blocker_chain": blocker_chain,
        "blocked_operations": blocked_operations,
        "diagnostic_conclusion": "evidence_insufficient_no_comparable_raw_processed_pairs",
        "why_processed_data_cannot_be_declared_aligned": (
            "Existing public-safe evidence proves raw numeric fingerprints exist, but processed target slots do "
            "not have authorized processed value fingerprints or shared join keys sufficient to create comparable "
            "raw/processed value pairs."
        ),
        "interim_report_generated_for_external_agent_diagnosis": True,
        "final_discrepancy_report_required_now": False,
        "final_discrepancy_report_required_if_repeated_mismatch_after_authorized_map": True,
        "next_required_input": NEXT_REQUIRED_INPUT,
        "required_owner_input_public_safe_schema": [
            "target_slot_reference_from_existing_private_worklist",
            "authorized_processed_value_fingerprint",
            "authorized_source_basis_reference",
            "owner_or_authorized_delegate_role",
            "authorization_timestamp",
            "allowed_action_code",
        ],
    }


def _build_go_no_go(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "decision": DECISION,
        "status": STATUS,
        "blocker_ids": [
            "NO_COMPARABLE_RAW_PROCESSED_VALUE_PAIRS",
            "PROCESSED_VALUE_SOURCE_MAP_INCOMPLETE",
            "AUTHORIZED_PROCESSED_VALUE_FINGERPRINTS_MISSING",
            "RAW_TO_PROCESSED_COMPARISON_BLOCKED",
        ],
        "resolved_blocker_ids": [
            "RAW_SOURCE_CONTAINER_AUTHORITY_RECORDED",
            "RAW_ROOT_READONLY_MUTATION_GUARD_RECHECKED",
            "PUBLIC_SAFE_BLOCKER_REPORT_GENERATED",
        ],
        "comparable_value_pair_count": summary["comparable_value_pair_count"],
        "business_value_consistency_verified": False,
        "raw_to_processed_value_comparison_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "next_required_input": NEXT_REQUIRED_INPUT,
    }


def _build_manifest(summary: dict[str, Any], go_no_go: dict[str, Any]) -> dict[str, Any]:
    return {
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "status": STATUS,
        "go_no_go": go_no_go,
        "summary": summary,
        "source_artifacts": {name: str(path.relative_to(PROJECT_ROOT)) for name, path in SOURCE_ARTIFACTS.items()},
        "outputs": [
            str(SUMMARY_PATH.relative_to(PROJECT_ROOT)),
            str(MANIFEST_PATH.relative_to(PROJECT_ROOT)),
            str(GO_NO_GO_PATH.relative_to(PROJECT_ROOT)),
            str(REPORT_PATH.relative_to(PROJECT_ROOT)),
            str(DIAGNOSTIC_PACKET_PATH.relative_to(PROJECT_ROOT)),
            str(TEST_RESULTS_PATH.relative_to(PROJECT_ROOT)),
        ],
        "public_safety": {
            "raw_file_committed": False,
            "raw_filename_committed": False,
            "raw_digest_committed": False,
            "raw_business_value_committed": False,
            "field_or_sheet_plaintext_committed": False,
            "private_runtime_path_committed": False,
            "public_evidence_aggregate_only": True,
        },
    }


def _render_report(summary: dict[str, Any]) -> str:
    blocker_lines = "\n".join(f"- `{item}`" for item in summary["blocker_chain"])
    blocked_ops = "\n".join(f"- `{item}`" for item in summary["blocked_operations"])
    return f"""# KMFA v0.1.4 Raw/Processed Alignment Blocker Report

## 结论

当前不能声明处理数据已经和原始数据对上。本轮只生成 public-safe 诊断报告，不做 raw-to-processed 数值比较，不做正式报告，不上传 GitHub，不重装 app，不执行业务动作。

## 关键公开计数

- raw_value_fingerprint_count: `{summary['raw_value_fingerprint_count']}`
- raw_unique_numeric_fingerprint_count: `{summary['raw_unique_numeric_fingerprint_count']}`
- processed_target_slot_count: `{summary['processed_target_slot_count']}`
- staged_processed_value_fingerprint_count: `{summary['staged_processed_value_fingerprint_count']}`
- usable_processed_source_map_count: `{summary['usable_processed_source_map_count']}`
- authorized_filled_item_count: `{summary['authorized_filled_item_count']}`
- authorized_unfilled_item_count: `{summary['authorized_unfilled_item_count']}`
- unresolved_gap_item_count: `{summary['unresolved_gap_item_count']}`
- active_fill_record_keep_pending_count: `{summary['active_fill_record_keep_pending_count']}`
- raw_processed_structural_key_intersection_count: `{summary['raw_processed_structural_key_intersection_count']}`
- comparable_value_pair_count: `{summary['comparable_value_pair_count']}`

## 为什么还不能对上

{summary['why_processed_data_cannot_be_declared_aligned']}

当前 blocker chain：

{blocker_lines}

## 仍然阻断的动作

{blocked_ops}

## 下一步必须补充

`{summary['next_required_input']}`

需要 owner 或授权代理提供 target-slot 到 processed-value source-map 的授权证据；没有该证据时，任何 materialization replay、raw-to-processed comparison、业务值一致性声明、lineage full check、正式报告、GitHub upload 或 app reinstall 都不应执行。
"""


def _render_diagnostic_packet(summary: dict[str, Any]) -> str:
    schema = "\n".join(f"- `{item}`" for item in summary["required_owner_input_public_safe_schema"])
    return f"""# 可转发诊断包：KMFA raw/processed 暂无法对齐

## 可公开给外部 agent 的事实

- 版本：`{VERSION}`
- 当前决策：`{DECISION}`
- raw 数值 fingerprint 已存在：`{summary['raw_value_fingerprint_count']}` 条
- raw unique numeric fingerprint：`{summary['raw_unique_numeric_fingerprint_count']}`
- processed target slots：`{summary['processed_target_slot_count']}`
- staged processed value fingerprints：`{summary['staged_processed_value_fingerprint_count']}`
- usable processed source-map：`{summary['usable_processed_source_map_count']}`
- authorized filled / unfilled：`{summary['authorized_filled_item_count']}` / `{summary['authorized_unfilled_item_count']}`
- unresolved source-map gaps：`{summary['unresolved_gap_item_count']}`
- comparable value pairs：`{summary['comparable_value_pair_count']}`
- business_value_consistency_verified：`false`

## 需要外部 agent 诊断的问题

如何在不暴露原始业务数据、不提交 raw 文件、不公开字段/表名/行列/业务值的前提下，补齐 target-slot 到 processed-value source-map 的授权证据，使系统能生成可比较的 raw/processed value pairs？

## 允许的输入结构

{schema}

## 禁止事项

- 不要要求公开 raw 文件名、raw hash、表名、字段/表头、行列坐标或业务值。
- 不要把本诊断解释为已经完成 raw-to-processed comparison。
- 不要建议直接上传 GitHub、重装 app、发布正式报告或执行业务动作。
"""


def _render_go_no_go(go_no_go: dict[str, Any]) -> str:
    blockers = "\n".join(f"- `{item}`" for item in go_no_go["blocker_ids"])
    return f"""# Go/No-Go

- decision: `{go_no_go['decision']}`
- status: `{go_no_go['status']}`
- comparable_value_pair_count: `{go_no_go['comparable_value_pair_count']}`
- next_required_input: `{go_no_go['next_required_input']}`

## Blockers

{blockers}
"""


def _render_test_results() -> str:
    return "\n".join(
        [
            "# KMFA v0.1.4 Raw/Processed Alignment Blocker Report Test Results",
            "",
            "- status: `pending_final_validation`",
            f"- task_id: `{TASK_ID}`",
            "- validator: `pending_final_validation`",
            "- focused_unit_test: `pending_final_validation`",
            "- governance_validator: `pending_final_validation`",
            "- raw_private_scan: `pending_final_validation`",
            "- secret_scan: `pending_final_validation`",
            "",
        ]
    )


def _render_risk_register() -> str:
    return """# Risk Register

| risk_id | risk | mitigation | status |
| --- | --- | --- | --- |
| RPA-BLOCK-001 | 把证据不足误判为业务值不一致 | 明确 comparable value pairs 为 0，当前不能做业务值差异结论 | controlled |
| RPA-BLOCK-002 | public report 泄露 raw/private 明细 | 只输出聚合计数、状态和允许输入结构 | controlled |
| RPA-BLOCK-003 | 外部 agent 建议越权执行 | 报告内锁定禁止 upload、reinstall、formal report 和业务动作 | controlled |
"""


def _render_rollback() -> str:
    return """# Rollback Plan

- 删除本 phase 新增的 `V014_RAW_PROCESSED_ALIGNMENT_BLOCKER_REPORT` 证据目录。
- 删除 `KMFA/metadata/quality/v014_raw_processed_alignment_blocker_*.json` copies。
- 回滚本 phase 新增工具、validator、focused test 和治理索引记录。
- 不需要 raw 数据回滚，因为本 phase 不读取、不写入、不删除、不移动 raw 数据。
"""


def generate(generated_at: str = "2026-07-06T00:00:00+10:00") -> dict[str, Any]:
    inputs = _load_inputs()
    summary = _build_summary(inputs, generated_at)
    go_no_go = _build_go_no_go(summary)
    manifest = _build_manifest(summary, go_no_go)

    _write_json(SUMMARY_PATH, summary)
    _write_json(GO_NO_GO_PATH, go_no_go)
    _write_json(MANIFEST_PATH, manifest)
    _write_text(REPORT_PATH, _render_report(summary))
    _write_text(DIAGNOSTIC_PACKET_PATH, _render_diagnostic_packet(summary))
    _write_text(GO_NO_GO_RECORD_PATH, _render_go_no_go(go_no_go))
    _write_text(TEST_RESULTS_PATH, _render_test_results())
    _write_text(RISK_REGISTER_PATH, _render_risk_register())
    _write_text(ROLLBACK_PATH, _render_rollback())

    QUALITY_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SUMMARY_PATH, METADATA_SUMMARY_PATH)
    shutil.copy2(MANIFEST_PATH, METADATA_MANIFEST_PATH)
    shutil.copy2(GO_NO_GO_PATH, METADATA_GO_NO_GO_PATH)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-at", default="2026-07-06T00:00:00+10:00")
    args = parser.parse_args()
    manifest = generate(generated_at=args.generated_at)
    summary = manifest["summary"]
    print(
        "Generated KMFA v0.1.4 raw/processed alignment blocker report "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"comparable_pairs={summary['comparable_value_pair_count']}, "
        f"next_required_input={summary['next_required_input']})"
    )


if __name__ == "__main__":
    main()

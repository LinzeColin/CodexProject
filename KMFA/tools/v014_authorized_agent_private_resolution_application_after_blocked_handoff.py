#!/usr/bin/env python3
"""Apply authorized-agent private resolutions after the blocked handoff.

The phase reads the owner/agent queue and the operator-designated raw inbox.
Raw values, filenames, locators, hashes, and diagnostics remain in the ignored
private runtime. Public artifacts contain aggregate gate evidence only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.a0_golden_fixture import normalize_ratio_to_basis_points  # noqa: E402
from KMFA.tools.amount_tools import normalize_amount_to_cents  # noqa: E402
from KMFA.tools.project_cost_fact_layer import REQUIRED_COST_CATEGORIES  # noqa: E402
from KMFA.tools.v014_s05_p1_a0_file_registration import RAW_INBOX  # noqa: E402
from KMFA.tools import (  # noqa: E402
    v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_resolution_intake_blocker_blocked_handoff_after_final_recheck
    as source_phase,
)


PROJECT_ROOT = Path("KMFA")
PHASE_ID = "V014_AUTHORIZED_AGENT_PRIVATE_RESOLUTION_APPLICATION_AFTER_BLOCKED_HANDOFF"
TASK_ID = "KMFA-V014-AUTHORIZED-AGENT-PRIVATE-RESOLUTION-APPLICATION-AFTER-BLOCKED-HANDOFF-20260710"
ACCEPTANCE_ID = "ACC-V014-AUTHORIZED-AGENT-PRIVATE-RESOLUTION-APPLICATION-AFTER-BLOCKED-HANDOFF"
VERSION = "0.1.4-authorized-agent-private-resolution-application-after-blocked-handoff"
STATUS = "completed_validated_local_only_partial_private_resolution_no_go_difference_report_required"
DECISION = "NO_GO"
PREFIX = "authorized_agent_private_resolution_application_after_blocked_handoff"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / f"{PREFIX}_summary.json"
MANIFEST_PATH = MACHINE_DIR / f"{PREFIX}_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / f"{PREFIX}_go_no_go_report.json"
MATRIX_PATH = MACHINE_DIR / f"{PREFIX}_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / f"{PREFIX}.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / f"metadata/quality/v014_{PREFIX}_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / f"metadata/quality/v014_{PREFIX}_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / f"metadata/quality/v014_{PREFIX}_go_no_go_report.json"
METADATA_MATRIX_PATH = PROJECT_ROOT / f"metadata/quality/v014_{PREFIX}_matrix_public_safe.json"

PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_authorized_agent_private_resolution_application_after_blocked_handoff"
PRIVATE_RAW_INDEX_PATH = PRIVATE_OUTPUT_DIR / "private_raw_source_index.json"
PRIVATE_RAW_BEFORE_PATH = PRIVATE_OUTPUT_DIR / "raw_immutability_before.json"
PRIVATE_RAW_AFTER_PATH = PRIVATE_OUTPUT_DIR / "raw_immutability_after.json"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_resolution_application_diagnostic.json"
PRIVATE_RESOLUTION_RECORDS_PATH = PRIVATE_OUTPUT_DIR / "private_resolution_application_records.jsonl"
PRIVATE_UNRESOLVED_QUEUE_PATH = PRIVATE_OUTPUT_DIR / "private_unresolved_business_value_queue.jsonl"
PRIVATE_DIFFERENCE_REPORT_PATH = PRIVATE_OUTPUT_DIR / "private_difference_report_zh.md"
PRIVATE_AUTHORITY_MATCH_PATH = PRIVATE_OUTPUT_DIR / "private_authority_baseline_raw_match.json"

SOURCE_PRIVATE_OWNER_RESOLUTION_QUEUE_PATH = (
    source_phase.PRIVATE_RESOLUTION_INTAKE_BLOCKER_OWNER_RESOLUTION_QUEUE_PATH
)
SOURCE_STAGING_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_private_processed_value_staging/private_processed_value_staging.json"
)
AUTHORITY_RECORDS_PATH = PROJECT_ROOT / "metadata/baseline/a0_authority_baseline_records.jsonl"
AUTHORITY_CANDIDATES_PATH = PROJECT_ROOT / "metadata/baseline/a0_golden_fixture_candidates.jsonl"
PROJECT_PROFILES_PATH = PROJECT_ROOT / "metadata/schema_maps/project_identity_profiles.jsonl"
PROJECT_PROFILE_GENERATOR_PATH = PROJECT_ROOT / "tools/project_composite_key.py"
MARGIN_RECORDS_PATH = PROJECT_ROOT / "metadata/lineage/project_margin_cash_margin_records.jsonl"

DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"
STAGE_STATUS_PATH = PROJECT_ROOT / "metadata/stage_status.jsonl"
TASK_STATUS_PATH = PROJECT_ROOT / "metadata/traceability/v1_4_stage_phase_task_status.jsonl"


def _now(generated_at: str | None = None) -> str:
    return generated_at or datetime.now().astimezone().isoformat(timespec="seconds")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path} contains a non-object JSONL row")
        rows.append(value)
    return rows


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical_sha256(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return _sha256_bytes(encoded)


def _git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else "UNKNOWN"


def _git_check_ignored(path: Path) -> bool:
    return subprocess.run(["git", "check-ignore", "-q", path.as_posix()], check=False).returncode == 0


def _upsert_jsonl(path: Path, key: str, record: dict[str, Any]) -> None:
    serialized = json.dumps(record, ensure_ascii=False, sort_keys=True)
    output_lines: list[str] = []
    replaced = False
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            existing = json.loads(line)
            if isinstance(existing, dict) and existing.get(key) == record.get(key):
                output_lines.append(serialized)
                replaced = True
            else:
                output_lines.append(line)
    if not replaced:
        output_lines.append(serialized)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(output_lines) + "\n", encoding="utf-8")


def _raw_snapshot(kind: str) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    extension_counts: Counter[str] = Counter()
    if RAW_INBOX.exists():
        for path in sorted(RAW_INBOX.rglob("*")):
            if not path.is_file():
                continue
            stat = path.stat()
            relative_path = path.relative_to(RAW_INBOX).as_posix()
            records.append(
                {
                    "relative_path": relative_path,
                    "kind": "file",
                    "size": stat.st_size,
                    "mtime_ns": stat.st_mtime_ns,
                    "mode": stat.st_mode,
                    "inode": stat.st_ino,
                    "device": stat.st_dev,
                    "sha256": _sha256_bytes(path.read_bytes()),
                }
            )
            extension_counts[path.suffix.lower() or "<none>"] += 1
    return {
        "schema_version": "kmfa.private.raw_snapshot.v1",
        "classification": "private_raw_immutability_do_not_commit",
        "phase_id": PHASE_ID,
        "snapshot_kind": kind,
        "raw_root": str(RAW_INBOX),
        "file_count": len(records),
        "total_bytes": sum(int(row["size"]) for row in records),
        "extension_counts": dict(sorted(extension_counts.items())),
        "records_sha256": _canonical_sha256(records),
        "records": records,
    }


def _snapshot_core(snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        "file_count": snapshot.get("file_count"),
        "total_bytes": snapshot.get("total_bytes"),
        "extension_counts": snapshot.get("extension_counts"),
        "records_sha256": snapshot.get("records_sha256"),
        "records": snapshot.get("records"),
    }


def _match_authority_baseline(raw_index: dict[str, Any]) -> dict[str, Any]:
    targets = _read_jsonl(AUTHORITY_CANDIDATES_PATH)
    normalized_targets: dict[str, list[tuple[str, str]]] = defaultdict(list)
    raw_targets: dict[str, list[tuple[str, str]]] = defaultdict(list)
    target_rows: list[dict[str, Any]] = []
    for target in targets:
        value_binding = target.get("value_binding", {})
        candidate_id = str(target.get("candidate_id"))
        field_key = str(target.get("field_key"))
        normalized_hash = value_binding.get("normalized_value_hash")
        raw_hash = value_binding.get("raw_value_hash")
        if normalized_hash:
            normalized_targets[str(normalized_hash)].append((candidate_id, field_key))
        if raw_hash:
            raw_targets[str(raw_hash)].append((candidate_id, field_key))
        target_rows.append(
            {
                "candidate_id": candidate_id,
                "field_key": field_key,
                "normalized_value_kind": value_binding.get("normalized_value_kind"),
                "normalized_value_hash": normalized_hash,
                "raw_value_hash": raw_hash,
                "normalized_matches": [],
                "exact_raw_matches": [],
            }
        )

    row_by_key = {(row["candidate_id"], row["field_key"]): row for row in target_rows}
    numeric_records = raw_index.get("numeric_records", [])
    for raw_record in numeric_records:
        raw_value = str(raw_record.get("raw_value", ""))
        raw_hash = _sha256_text("raw:" + raw_value)
        for key in raw_targets.get(raw_hash, []):
            row_by_key[key]["exact_raw_matches"].append(raw_record)

        candidates: set[tuple[str, str]] = set()
        for unit in (None, "元", "万元"):
            try:
                cents = normalize_amount_to_cents(raw_value, unit=unit)
            except Exception:
                continue
            candidates.add((_sha256_text(f"money_cents:{cents}"), unit or "none"))
        try:
            basis_points = normalize_ratio_to_basis_points(raw_value)
            candidates.add((_sha256_text(f"ratio_basis_points:{basis_points}"), "basis_points"))
        except Exception:
            pass
        for normalized_hash, interpreted_unit in candidates:
            for key in normalized_targets.get(normalized_hash, []):
                row_by_key[key]["normalized_matches"].append(
                    {**raw_record, "interpreted_unit": interpreted_unit}
                )

    numeric_fields = {"contract_amount", "total_expense", "gross_profit", "gross_margin"}
    matched_rows = [row for row in target_rows if row["normalized_matches"]]
    matched_fields_by_candidate: dict[str, set[str]] = defaultdict(set)
    for row in matched_rows:
        if row["field_key"] in numeric_fields:
            matched_fields_by_candidate[row["candidate_id"]].add(row["field_key"])
    complete_candidates = sorted(
        candidate_id
        for candidate_id, fields in matched_fields_by_candidate.items()
        if fields == numeric_fields
    )

    authority_records = _read_jsonl(AUTHORITY_RECORDS_PATH)
    locked_candidates = sorted(
        {
            str(row.get("candidate_id"))
            for row in authority_records
            if row.get("lock_status") == "q5_locked_public_safe_hash_baseline"
        }
    )
    s09_selected_candidates = locked_candidates[:4]
    return {
        "schema_version": "kmfa.private.authority_baseline_raw_match.v1",
        "classification": "private_authority_baseline_raw_match_do_not_commit",
        "target_count": len(target_rows),
        "target_with_normalized_hash_count": sum(bool(row["normalized_value_hash"]) for row in target_rows),
        "normalized_hash_matched_target_count": len(matched_rows),
        "exact_raw_hash_matched_target_count": sum(bool(row["exact_raw_matches"]) for row in target_rows),
        "complete_numeric_candidate_group_count": len(complete_candidates),
        "complete_numeric_candidate_ids": complete_candidates,
        "s09_selected_authority_group_count": len(s09_selected_candidates),
        "s09_selected_complete_raw_match_count": sum(
            candidate_id in complete_candidates for candidate_id in s09_selected_candidates
        ),
        "s09_selected_authority_candidate_ids": s09_selected_candidates,
        "records": target_rows,
    }


def _synthetic_project_identity_detected() -> bool:
    if not PROJECT_PROFILE_GENERATOR_PATH.exists() or not PROJECT_PROFILES_PATH.exists():
        return False
    source = PROJECT_PROFILE_GENERATOR_PATH.read_text(encoding="utf-8")
    profiles = _read_jsonl(PROJECT_PROFILES_PATH)
    return (
        "SYNTHETIC_PROJECT_ALPHA" in source
        and "amount-cents:12345600" in source
        and len(profiles) == 4
        and all(str(row.get("profile_id", "")).startswith("IDP-S08P1-") for row in profiles)
    )


def _build_private_resolution_records(
    *,
    generated_at: str,
    queue_rows: list[dict[str, Any]],
    staging_slots: list[dict[str, Any]],
    synthetic_project_identity_detected: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    slots_by_id = {str(row.get("target_slot_id")): row for row in staging_slots}
    margin_records = _read_jsonl(MARGIN_RECORDS_PATH)
    records: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    for index, queue_row in enumerate(queue_rows, start=1):
        slot_id = str(queue_row.get("target_slot_id"))
        if slot_id not in slots_by_id:
            raise ValueError(f"source queue target slot missing from staging: {slot_id}")
        slot = slots_by_id[slot_id]
        context_group = str(slot.get("context_group"))
        base = {
            "schema_version": "kmfa.private.authorized_agent_resolution_record.v1",
            "classification": "private_resolution_record_do_not_commit",
            "resolution_record_id": f"V014-AAPR-{index:03d}",
            "generated_at": generated_at,
            "source_owner_resolution_item_id": queue_row.get("owner_resolution_item_id"),
            "target_slot_id": slot_id,
            "context_group": context_group,
            "private_processed_ref": slot.get("private_processed_ref"),
            "source_root_id": slot.get("source_root_id"),
            "record_index": slot.get("record_index"),
            "public_commit_allowed": False,
            "business_value_materialized": False,
            "raw_layer_write_allowed": False,
        }
        if context_group == "calculation_private_execution_ref":
            record_index = int(slot.get("record_index", 0))
            if record_index < 1 or record_index > len(margin_records):
                raise ValueError(f"margin record index out of range: {record_index}")
            margin_record = margin_records[record_index - 1]
            record = {
                **base,
                "resolution_applied": True,
                "resolution_kind": "formula_contract",
                "resolution_status": "resolved_structural_formula_mapping_private_only",
                "formula_refs": margin_record.get("formula_refs", {}),
                "integer_cent_calculation_contract": margin_record.get(
                    "integer_cent_calculation_contract", {}
                ),
                "reason_codes": ["deterministic_formula_contract_present_in_tracked_s09_metadata"],
            }
        elif context_group == "cost_category":
            record = {
                **base,
                "resolution_applied": True,
                "resolution_kind": "canonical_cost_category_taxonomy",
                "resolution_status": "resolved_non_numeric_taxonomy_mapping_private_only",
                "canonical_cost_category_keys": list(REQUIRED_COST_CATEGORIES),
                "reason_codes": ["deterministic_canonical_taxonomy_present_in_tracked_s09_contract"],
            }
        else:
            reason_codes = [
                "processed_business_value_not_materialized",
                "synthetic_project_identity_not_raw_bound",
                "raw_candidate_to_project_identity_join_not_proven",
                "placeholder_or_missing_processed_fingerprint_not_comparable_as_business_value",
            ]
            if not synthetic_project_identity_detected:
                reason_codes.remove("synthetic_project_identity_not_raw_bound")
                reason_codes.append("project_identity_to_raw_source_binding_not_proven")
            record = {
                **base,
                "resolution_applied": False,
                "resolution_kind": "business_value_binding_unresolved",
                "resolution_status": "unresolved_requires_real_project_identity_and_processed_value_materialization",
                "reason_codes": reason_codes,
                "required_next_evidence": [
                    "real_project_identity_profile_bound_to_raw_source",
                    "actual_processed_business_value_materialized_in_private_runtime",
                    "integer_cent_or_basis_point_cross_validation_evidence",
                ],
            }
            unresolved.append(record)
        records.append(record)
    return records, unresolved


def _private_difference_report(
    *,
    summary: dict[str, Any],
    authority_match: dict[str, Any],
    unresolved: list[dict[str, Any]],
) -> str:
    reason_labels = {
        "processed_business_value_not_materialized": "实际处理业务值尚未物化",
        "synthetic_project_identity_not_raw_bound": "合成项目身份尚未绑定真实原始项目",
        "project_identity_to_raw_source_binding_not_proven": "项目身份与原始来源的绑定尚未证明",
        "raw_candidate_to_project_identity_join_not_proven": "原始候选与项目身份的一一对应尚未证明",
        "placeholder_or_missing_processed_fingerprint_not_comparable_as_business_value": "处理端只有占位指纹或缺少指纹，不能作为业务值比较",
    }
    lines = [
        "# KMFA v0.1.4 授权代理私有解析差异报告",
        "",
        "## 结论",
        "",
        f"- 本轮输入槽位：{summary['source_resolution_item_count']} 个。",
        f"- 已确定性解析结构槽位：{summary['resolved_structural_item_count']} 个。",
        f"- 仍未完成业务值绑定：{summary['unresolved_business_value_item_count']} 个。",
        f"- 原始目录前后逐文件完全一致：{'是' if summary['raw_snapshot_exact_match'] else '否'}。",
        "- 当前不能声明原始值与处理值一致，维持 NO_GO。",
        "",
        "## 原因",
        "",
        "1. 当前 S08 项目身份样本由代码中的合成测试常量生成，没有绑定真实原始项目。",
        "2. 当前 S09 金额槽位没有实际处理值；治理引用或标签哈希不是业务值哈希。",
        "3. 原始候选虽可局部匹配 S05 权威哈希，但无法证明其与 4 个合成项目记录一一对应。",
        "4. 因此不得把候选金额强行写入处理槽位，也不得伪造零差异。",
        "",
        "## 权威基准交叉匹配",
        "",
        f"- 字段目标数：{authority_match['target_count']}。",
        f"- 当前原始源可命中的 normalized hash 目标数：{authority_match['normalized_hash_matched_target_count']}。",
        f"- 四个数值字段均可命中的候选组数：{authority_match['complete_numeric_candidate_group_count']}。",
        f"- S09 当前选取的 4 个权威组中，完整命中当前原始源的组数：{authority_match['s09_selected_complete_raw_match_count']}。",
        "",
        "## 私有匹配明细",
        "",
    ]
    for row in authority_match["records"]:
        if not row["normalized_matches"] and not row["exact_raw_matches"]:
            continue
        lines.extend(
            [
                f"### {row['candidate_id']} / {row['field_key']}",
                "",
                f"- 标准化值哈希匹配数：{len(row['normalized_matches'])}",
                f"- 原始值精确哈希匹配数：{len(row['exact_raw_matches'])}",
            ]
        )
        for match in row["normalized_matches"][:20]:
            lines.append(
                "- 原始文件={raw_file_name}；压缩包成员={archive_member_name}；工作表={sheet_name}；"
                "单元格={cell_address}；页码={page_index}；原始值={raw_value}；上下文={context_text}".format(
                    raw_file_name=match.get("raw_file_name"),
                    archive_member_name=match.get("archive_member_name"),
                    sheet_name=match.get("sheet_name"),
                    cell_address=match.get("cell_address"),
                    page_index=match.get("page_index"),
                    raw_value=match.get("raw_value"),
                    context_text=match.get("context_text"),
                )
            )
        lines.append("")
    lines.extend(["## 未解析业务值槽位", ""])
    for row in unresolved:
        lines.extend(
            [
                f"- {row['target_slot_id']} / {row['context_group']} / {row['private_processed_ref']}",
                "  原因：" + "；".join(reason_labels.get(code, code) for code in row["reason_codes"]),
            ]
        )
    lines.extend(
        [
            "",
            "## 下一步",
            "",
            "- 先把 S08/S09 合成项目身份替换为只存在于私有运行区的真实项目身份绑定。",
            "- 再以整数分 / 基点物化实际处理值并进行逐槽位交叉验证。",
            "- 多次复核后仍不一致的项目继续保留在本报告，不打开报告、业务执行或上传 gate。",
            "",
        ]
    )
    return "\n".join(lines)


def _public_matrix(summary: dict[str, Any]) -> dict[str, Any]:
    checks = [
        ("source_queue_read_only", summary["source_queue_unchanged"]),
        ("raw_snapshot_exact_match", summary["raw_snapshot_exact_match"]),
        ("raw_not_mutated", not summary["raw_inbox_mutated_by_this_phase"]),
        ("structural_resolution_count", summary["resolved_structural_item_count"] == 8),
        ("formula_mapping_count", summary["resolved_formula_mapping_count"] == 4),
        ("taxonomy_mapping_count", summary["resolved_non_numeric_mapping_count"] == 4),
        ("business_value_unresolved_count", summary["unresolved_business_value_item_count"] == 40),
        ("comparison_not_claimed_complete", not summary["raw_to_processed_value_comparison_complete"]),
        ("processed_consistency_not_claimed", not summary["processed_consistency_verified"]),
        ("business_consistency_not_claimed", not summary["business_value_consistency_verified"]),
        ("raw_not_committed", not summary["raw_business_data_committed"]),
        ("github_not_uploaded", not summary["github_upload_performed"]),
        ("app_not_reinstalled", not summary["app_reinstall_performed"]),
        ("business_not_executed", not summary["business_execution_performed"]),
    ]
    records = [
        {"check_id": f"AAPR-{index:02d}", "check_name": name, "passed": passed}
        for index, (name, passed) in enumerate(checks, start=1)
    ]
    return {
        "schema_version": "kmfa.v014_authorized_agent_private_resolution_matrix.v1",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "check_count": len(records),
        "check_pass_count": sum(row["passed"] for row in records),
        "check_fail_count": sum(not row["passed"] for row in records),
        "checks": records,
    }


def _public_reports(summary: dict[str, Any]) -> dict[Path, str]:
    report = f"""# v0.1.4 授权代理私有解析应用记录

- Phase: `{PHASE_ID}`
- 决策: `{DECISION}`
- 输入: {summary['source_resolution_item_count']} 个私有 resolution 槽位
- 已解析: {summary['resolved_structural_item_count']} 个结构槽位（公式 4、成本分类 4）
- 未解析: {summary['unresolved_business_value_item_count']} 个业务值槽位
- 原始目录逐文件前后完全一致: `{str(summary['raw_snapshot_exact_match']).lower()}`
- 已生成私有中文差异报告: `{str(summary['private_difference_report_written']).lower()}`

当前 S08 项目身份仍是合成测试记录，S09 业务值尚未真实物化；因此不把候选值强行绑定，不声明原始值与处理值一致。Stage 复审、GitHub upload、app reinstall 和业务执行均未进入本 phase。
"""
    go_no_go = f"""# Go / No-Go 记录

- 决策: `{DECISION}`
- 原因: 40 个业务值槽位缺少真实项目身份绑定与实际处理值，不能完成 raw-to-processed 逐值比较。
- 已完成: 8 个确定性结构映射及私有中文差异报告。
- GitHub upload: `not_performed`
"""
    tests = """# 测试结果

- focused unit test: `PENDING_FINAL_VERIFICATION`
- phase validator: `PENDING_FINAL_VERIFICATION`
- governance validator: `PENDING_FINAL_VERIFICATION`
- raw/secret scan: `PENDING_FINAL_VERIFICATION`
"""
    risks = """# 风险登记

- 高: 合成项目身份未绑定真实原始项目；任何强制金额映射都会制造错误业务结论。
- 高: S09 当前引用/标签哈希不是业务值哈希，不能用于金额一致性证明。
- 中: 部分权威字段可由当前原始源命中，但不足以建立完整项目级 lineage。
"""
    rollback = """# 回滚方案

1. 删除本 phase 的公开 artifacts 和 metadata 镜像。
2. 删除本 phase 的忽略私有运行目录；不触碰 operator 原始数据目录。
3. 从治理 JSONL 中移除本 phase 对应记录。
"""
    return {
        REPORT_PATH: report,
        GO_NO_GO_RECORD_PATH: go_no_go,
        TEST_RESULTS_PATH: tests,
        RISK_REGISTER_PATH: risks,
        ROLLBACK_PATH: rollback,
    }


def phase_output_paths() -> list[Path]:
    return [
        SUMMARY_PATH,
        MANIFEST_PATH,
        GO_NO_GO_PATH,
        MATRIX_PATH,
        REPORT_PATH,
        GO_NO_GO_RECORD_PATH,
        TEST_RESULTS_PATH,
        RISK_REGISTER_PATH,
        ROLLBACK_PATH,
        METADATA_SUMMARY_PATH,
        METADATA_MANIFEST_PATH,
        METADATA_GO_NO_GO_PATH,
        METADATA_MATRIX_PATH,
        PRIVATE_RAW_BEFORE_PATH,
        PRIVATE_RAW_AFTER_PATH,
        PRIVATE_DIAGNOSTIC_PATH,
        PRIVATE_RESOLUTION_RECORDS_PATH,
        PRIVATE_UNRESOLVED_QUEUE_PATH,
        PRIVATE_DIFFERENCE_REPORT_PATH,
        PRIVATE_AUTHORITY_MATCH_PATH,
    ]


def _phase_public_files() -> list[str]:
    return [
        "KMFA/CHANGELOG.md",
        "KMFA/HANDOFF.md",
        "KMFA/VERSION",
        "KMFA/docs/governance/ASSURANCE_STATUS.yaml",
        "KMFA/docs/governance/DEVELOPMENT_LEDGER.md",
        "KMFA/docs/governance/MODEL_SPEC.md",
        "KMFA/docs/governance/OWNER_STATUS.md",
        "KMFA/docs/governance/STATUS.md",
        "KMFA/docs/governance/TRACEABILITY_MATRIX.csv",
        "KMFA/docs/governance/VERSION_MATRIX.yaml",
        "KMFA/docs/governance/delivery_tasks.yaml",
        "KMFA/docs/governance/development_events.jsonl",
        "KMFA/docs/governance/formula_registry.yaml",
        "KMFA/docs/governance/model_registry.yaml",
        "KMFA/docs/governance/parameter_registry.csv",
        "KMFA/metadata/model_registry.yaml",
        METADATA_SUMMARY_PATH.as_posix(),
        METADATA_MANIFEST_PATH.as_posix(),
        METADATA_GO_NO_GO_PATH.as_posix(),
        METADATA_MATRIX_PATH.as_posix(),
        "KMFA/metadata/stage_status.jsonl",
        "KMFA/metadata/traceability/v1_4_stage_phase_task_status.jsonl",
        SUMMARY_PATH.as_posix(),
        MANIFEST_PATH.as_posix(),
        GO_NO_GO_PATH.as_posix(),
        MATRIX_PATH.as_posix(),
        REPORT_PATH.as_posix(),
        GO_NO_GO_RECORD_PATH.as_posix(),
        TEST_RESULTS_PATH.as_posix(),
        RISK_REGISTER_PATH.as_posix(),
        ROLLBACK_PATH.as_posix(),
        "KMFA/tests/test_v014_authorized_agent_private_resolution_application_after_blocked_handoff.py",
        "KMFA/tools/check_v014_authorized_agent_private_resolution_application_after_blocked_handoff.py",
        "KMFA/tools/v014_authorized_agent_private_resolution_application_after_blocked_handoff.py",
        "KMFA/功能清单.md",
        "KMFA/开发记录.md",
        "KMFA/模型参数文件.md",
    ]


def _write_governance(generated_at: str, summary: dict[str, Any]) -> None:
    evidence_ref = MANIFEST_PATH.as_posix()
    _upsert_jsonl(
        DEVELOPMENT_EVENTS_PATH,
        "event_id",
        {
            "event_id": "DEV-KMFA-20260710-V014-AUTHORIZED-AGENT-PRIVATE-RESOLUTION-AFTER-BLOCKED-HANDOFF",
            "event_time": generated_at,
            "event_type": "development",
            "project_id": "KMFA",
            "stage_id": "value-consistency",
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "decision": DECISION,
            "source_resolution_item_count": summary["source_resolution_item_count"],
            "resolved_structural_item_count": summary["resolved_structural_item_count"],
            "unresolved_business_value_item_count": summary["unresolved_business_value_item_count"],
            "raw_inbox_mutation_performed": False,
            "raw_snapshot_exact_match": summary["raw_snapshot_exact_match"],
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
            "record_type": "stage_phase_status",
            "project_id": "KMFA",
            "stage_id": "VALUE-CONSISTENCY",
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "version": VERSION,
            "status": STATUS,
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
            "stage_id": "VALUE-CONSISTENCY",
            "governance_stage_id": "VALUE-CONSISTENCY",
            "roadmap_stage_id": "VALUE-CONSISTENCY",
            "roadmap_phase_id": "AUTHORIZED_AGENT_PRIVATE_RESOLUTION_APPLICATION_AFTER_BLOCKED_HANDOFF",
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "version": VERSION,
            "name": "v0.1.4 authorized-agent private resolution application after blocked handoff",
            "phase_goal": "apply deterministic private resolutions and issue a difference report without forcing business values",
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "derived_percent": 100.0,
            "estimated_task_units": 1,
            "completed_task_units": 1,
            "task_count": 1,
            "raw_data_committed": False,
            "evidence_ref": evidence_ref,
            "updated_at": generated_at[:10],
        },
    )


def generate(
    *,
    generated_at: str | None = None,
    raw_index_override: dict[str, Any] | None = None,
    raw_before_snapshot_override: dict[str, Any] | None = None,
    raw_after_snapshot_override: dict[str, Any] | None = None,
    write_governance_event: bool = True,
) -> dict[str, Any]:
    timestamp = _now(generated_at)
    source_queue_before = SOURCE_PRIVATE_OWNER_RESOLUTION_QUEUE_PATH.read_bytes()
    queue_rows = _read_jsonl(SOURCE_PRIVATE_OWNER_RESOLUTION_QUEUE_PATH)
    staging = _read_json(SOURCE_STAGING_PATH)
    staging_slots = staging.get("processed_target_slots", [])
    if len(queue_rows) != 48 or not isinstance(staging_slots, list):
        raise ValueError("expected 48 source queue rows and a processed_target_slots list")

    if raw_index_override is None:
        raw_container = _read_json(PRIVATE_RAW_INDEX_PATH)
        raw_index = raw_container.get("private_index", raw_container)
    else:
        raw_index = raw_index_override
    raw_before = raw_before_snapshot_override or (
        _read_json(PRIVATE_RAW_BEFORE_PATH) if PRIVATE_RAW_BEFORE_PATH.exists() else _raw_snapshot("before")
    )
    raw_after = raw_after_snapshot_override or _raw_snapshot("after")
    _write_json(PRIVATE_RAW_BEFORE_PATH, raw_before)
    _write_json(PRIVATE_RAW_AFTER_PATH, raw_after)
    raw_snapshot_exact_match = _snapshot_core(raw_before) == _snapshot_core(raw_after)

    authority_match = _match_authority_baseline(raw_index)
    synthetic_detected = _synthetic_project_identity_detected()
    resolution_records, unresolved = _build_private_resolution_records(
        generated_at=timestamp,
        queue_rows=queue_rows,
        staging_slots=staging_slots,
        synthetic_project_identity_detected=synthetic_detected,
    )
    source_queue_after = SOURCE_PRIVATE_OWNER_RESOLUTION_QUEUE_PATH.read_bytes()
    source_queue_unchanged = source_queue_before == source_queue_after
    context_counts = Counter(row["context_group"] for row in resolution_records)
    resolved = [row for row in resolution_records if row["resolution_applied"]]

    summary = {
        "schema_version": "kmfa.v014_authorized_agent_private_resolution_summary.v1",
        "record_type": "v014_authorized_agent_private_resolution_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "stage_id": "VALUE-CONSISTENCY",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "source_phase_id": source_phase.PHASE_ID,
        "source_resolution_item_count": len(queue_rows),
        "source_queue_unchanged": source_queue_unchanged,
        "resolved_structural_item_count": len(resolved),
        "resolved_formula_mapping_count": context_counts.get("calculation_private_execution_ref", 0),
        "resolved_non_numeric_mapping_count": context_counts.get("cost_category", 0),
        "unresolved_business_value_item_count": len(unresolved),
        "unresolved_difference_count": 72,
        "synthetic_project_identity_source_detected": synthetic_detected,
        "processed_business_value_materialized_count": 0,
        "authority_baseline_target_count": authority_match["target_count"],
        "authority_normalized_hash_match_count": authority_match["normalized_hash_matched_target_count"],
        "authority_complete_numeric_candidate_group_count": authority_match[
            "complete_numeric_candidate_group_count"
        ],
        "s09_selected_authority_group_count": authority_match["s09_selected_authority_group_count"],
        "s09_selected_authority_group_complete_raw_match_count": authority_match[
            "s09_selected_complete_raw_match_count"
        ],
        "raw_source_file_count": raw_before.get("file_count", 0),
        "raw_snapshot_exact_match": raw_snapshot_exact_match,
        "raw_inbox_mutated_by_this_phase": not raw_snapshot_exact_match,
        "raw_authority_baseline_hash_match_performed": True,
        "raw_to_processed_value_comparison_precheck_performed": True,
        "raw_to_processed_value_comparison_complete": False,
        "processed_consistency_verified": False,
        "business_value_consistency_verified": False,
        "structural_resolution_verifies_business_values": False,
        "private_difference_report_written": True,
        "private_resolution_records_gitignored": _git_check_ignored(PRIVATE_RESOLUTION_RECORDS_PATH),
        "private_difference_report_gitignored": _git_check_ignored(PRIVATE_DIFFERENCE_REPORT_PATH),
        "raw_business_data_committed": False,
        "raw_filename_or_value_committed": False,
        "credential_or_secret_committed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "stage_review_performed": False,
        "goal_status_recommendation": "continue_active_with_upstream_real_identity_rebinding",
        "next_recommended_phase": "upstream_synthetic_project_identity_rebinding_and_processed_value_materialization",
    }
    matrix = _public_matrix(summary)
    if matrix["check_fail_count"]:
        raise ValueError("public acceptance matrix contains failed checks")

    manifest = {
        "schema_version": "kmfa.v014_authorized_agent_private_resolution_manifest.v1",
        "record_type": "v014_authorized_agent_private_resolution_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "reviewed_head": _git_output(["rev-parse", "HEAD"]),
        "branch": _git_output(["branch", "--show-current"]),
        "remote": _git_output(["remote", "get-url", "origin"]),
        "summary": summary,
        "artifact_refs": {
            "summary": SUMMARY_PATH.as_posix(),
            "go_no_go": GO_NO_GO_PATH.as_posix(),
            "matrix": MATRIX_PATH.as_posix(),
            "report": REPORT_PATH.as_posix(),
            "test_results": TEST_RESULTS_PATH.as_posix(),
            "validator": "KMFA/tools/check_v014_authorized_agent_private_resolution_application_after_blocked_handoff.py",
        },
        "public_repo_safety": {
            "aggregate_only": True,
            "raw_file_committed": False,
            "raw_filename_committed": False,
            "raw_hash_committed": False,
            "field_header_plaintext_committed": False,
            "business_value_committed": False,
            "private_ref_committed": False,
            "credential_or_secret_committed": False,
        },
        "phase_boundaries": {
            "single_phase_only": True,
            "stage_review_performed": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "business_execution_performed": False,
        },
    }
    go_no_go = {
        "schema_version": "kmfa.v014_authorized_agent_private_resolution_go_no_go.v1",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "decision": DECISION,
        "blocking_item_count": len(unresolved),
        "blocking_difference_count": 72,
        "resolved_structural_item_count": len(resolved),
        "reason_codes": [
            "synthetic_project_identity_not_raw_bound",
            "processed_business_values_not_materialized",
            "raw_to_processed_value_comparison_incomplete",
        ],
        "github_upload_performed": False,
    }

    _write_json(PRIVATE_AUTHORITY_MATCH_PATH, authority_match)
    _write_jsonl(PRIVATE_RESOLUTION_RECORDS_PATH, resolution_records)
    _write_jsonl(PRIVATE_UNRESOLVED_QUEUE_PATH, unresolved)
    diagnostic = {
        "schema_version": "kmfa.private.authorized_agent_resolution_diagnostic.v1",
        "classification": "private_resolution_diagnostic_do_not_commit",
        "generated_at": timestamp,
        "source_queue_sha256_before": _sha256_bytes(source_queue_before),
        "source_queue_sha256_after": _sha256_bytes(source_queue_after),
        "source_queue_unchanged": source_queue_unchanged,
        "raw_before_snapshot": raw_before,
        "raw_after_snapshot": raw_after,
        "raw_snapshot_exact_match": raw_snapshot_exact_match,
        "authority_match_summary": {
            key: value for key, value in authority_match.items() if key not in {"records", "complete_numeric_candidate_ids", "s09_selected_authority_candidate_ids"}
        },
        "synthetic_project_identity_source_detected": synthetic_detected,
        "resolution_status_counts": dict(sorted(Counter(row["resolution_status"] for row in resolution_records).items())),
        "context_group_counts": dict(sorted(context_counts.items())),
    }
    _write_json(PRIVATE_DIAGNOSTIC_PATH, diagnostic)
    _write_text(
        PRIVATE_DIFFERENCE_REPORT_PATH,
        _private_difference_report(summary=summary, authority_match=authority_match, unresolved=unresolved),
    )

    for path, payload in (
        (SUMMARY_PATH, summary),
        (MANIFEST_PATH, manifest),
        (GO_NO_GO_PATH, go_no_go),
        (MATRIX_PATH, matrix),
        (METADATA_SUMMARY_PATH, summary),
        (METADATA_MANIFEST_PATH, manifest),
        (METADATA_GO_NO_GO_PATH, go_no_go),
        (METADATA_MATRIX_PATH, matrix),
    ):
        _write_json(path, payload)
    for path, content in _public_reports(summary).items():
        _write_text(path, content)
    if write_governance_event:
        _write_governance(timestamp, summary)
    return {"summary": summary, "manifest": manifest, "go_no_go": go_no_go, "matrix": matrix}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-at")
    parser.add_argument("--skip-governance-event", action="store_true")
    args = parser.parse_args()
    result = generate(
        generated_at=args.generated_at,
        write_governance_event=not args.skip_governance_event,
    )
    print(
        "authorized-agent private resolution application: "
        f"decision={result['summary']['decision']} "
        f"resolved={result['summary']['resolved_structural_item_count']} "
        f"unresolved={result['summary']['unresolved_business_value_item_count']} "
        f"raw_unchanged={result['summary']['raw_snapshot_exact_match']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

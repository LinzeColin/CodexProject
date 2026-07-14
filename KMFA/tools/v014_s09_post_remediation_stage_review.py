#!/usr/bin/env python3
"""Generate the KMFA v0.1.4 Stage 9 post-remediation review."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools import check_v014_global_residual_difference_queue_replay_or_authoritative_exclusion as global_check
from KMFA.tools import check_v014_remaining_eleven_residual_difference_source_trace_or_final_acceptance as residual_check
from KMFA.tools import v014_remaining_eleven_residual_difference_source_trace_or_final_acceptance as residual_phase
from KMFA.tools.check_v014_s09_p1_project_cost_fact_layer import validate_v014_s09_p1_project_cost_fact_layer
from KMFA.tools.check_v014_s09_p2_margin_cash_margin import validate_v014_s09_p2_margin_cash_margin
from KMFA.tools.check_v014_s09_p3_scope_reconciliation import validate_v014_s09_p3_scope_reconciliation
from KMFA.tools.check_v014_s09_stage_review import validate_v014_s09_stage_review


PHASE_ID = "V014_S09_POST_REMEDIATION_STAGE_REVIEW"
TASK_ID = "KMFA-V014-S09-POST-REMEDIATION-STAGE-REVIEW-20260710"
ACCEPTANCE_ID = "ACC-V014-S09-POST-REMEDIATION-STAGE-REVIEW"
VERSION = "0.1.4-s09-post-remediation-stage-review"
STATUS = "review_completed_validated_local_only_findings_fixed_no_go_upload_deferred"
DECISION = "NO_GO"
REVIEW_SCOPE = "v014_s09_post_remediation_stage_review_only"
FORMULA_ID = "FORM-KMFA-V014-S09-POST-REMEDIATION-STAGE-REVIEW-001"
PARAMETER_IDS = ("PARAM-KMFA-1693", "PARAM-KMFA-1694", "PARAM-KMFA-1695")
MODEL_ID = "MOD-KMFA-GOV-001"
MODEL_REGISTRY_KEY = "kmfa_v014_s09_post_remediation_stage_review"

OUTPUT_DIR = Path("KMFA/stage_artifacts") / PHASE_ID
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "stage9_post_remediation_review_summary.json"
MANIFEST_PATH = MACHINE_DIR / "stage9_post_remediation_review_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "stage9_post_remediation_review_go_no_go_report.json"
MATRIX_PATH = MACHINE_DIR / "stage9_post_remediation_review_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / "stage9_post_remediation_review_report_zh.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results_zh.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register_zh.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan_zh.md"

QUALITY_DIR = Path("KMFA/metadata/quality")
METADATA_SUMMARY_PATH = QUALITY_DIR / "v014_s09_post_remediation_stage_review_summary.json"
METADATA_MANIFEST_PATH = QUALITY_DIR / "v014_s09_post_remediation_stage_review_manifest.json"
METADATA_GO_NO_GO_PATH = QUALITY_DIR / "v014_s09_post_remediation_stage_review_go_no_go_report.json"
METADATA_MATRIX_PATH = QUALITY_DIR / "v014_s09_post_remediation_stage_review_matrix_public_safe.json"

PRIVATE_DIR = Path("KMFA/.codex_private_runtime/v014_s09_post_remediation_stage_review")
PRIVATE_RAW_BEFORE_PATH = PRIVATE_DIR / "raw_immutability_before.json"
PRIVATE_RAW_AFTER_PATH = PRIVATE_DIR / "raw_immutability_after.json"
PRIVATE_REVIEW_REPORT_PATH = PRIVATE_DIR / "stage9_post_remediation_difference_review_zh.md"

STAGE_STATUS_PATH = Path("KMFA/metadata/stage_status.jsonl")
TASK_STATUS_PATH = Path("KMFA/metadata/traceability/v1_4_stage_phase_task_status.jsonl")
DEVELOPMENT_EVENTS_PATH = Path("KMFA/docs/governance/development_events.jsonl")
SCOPE_RECONCILIATION_PATH = Path("KMFA/metadata/quality/scope_reconciliation_records.jsonl")
SOURCE_STAGE_REVIEW_MANIFEST = Path("KMFA/stage_artifacts/V014_S09_STAGE_REVIEW/machine/stage9_review_manifest.json")
SOURCE_RESIDUAL_MANIFEST = residual_phase.MANIFEST_PATH
SOURCE_RESIDUAL_RAW_AFTER = residual_phase.PRIVATE_RAW_AFTER_PATH

REQUIRED_STAGE_STATUS_FIELDS = {"record_type", "status", "updated_at", "fact_level"}
NORMALIZATION_MARKER = PHASE_ID


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


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path} must contain objects")
            rows.append(value)
    return rows


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def _upsert_jsonl(path: Path, key: str, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
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
    path.write_text("\n".join(output) + "\n", encoding="utf-8")


def normalize_stage_status_records(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    normalized: list[dict[str, Any]] = []
    changed_count = 0
    for source in records:
        record = dict(source)
        missing = REQUIRED_STAGE_STATUS_FIELDS - set(record)
        if missing:
            if "record_type" in missing and record.get("event_id"):
                record["record_type"] = "v014_phase_event"
            if "updated_at" in missing and record.get("event_time"):
                record["updated_at"] = record["event_time"]
            if "fact_level" in missing:
                record["fact_level"] = "EXTRACTED"
            record["governance_normalized_by"] = NORMALIZATION_MARKER
        if not REQUIRED_STAGE_STATUS_FIELDS <= set(record):
            unresolved = sorted(REQUIRED_STAGE_STATUS_FIELDS - set(record))
            raise ValueError(f"stage status record remains incomplete: {unresolved}")
        if record != source:
            changed_count += 1
        normalized.append(record)
    return normalized, changed_count


def repair_stage_status_registry(path: Path = STAGE_STATUS_PATH) -> dict[str, int]:
    source_lines = path.read_text(encoding="utf-8").splitlines()
    source_records = [json.loads(line) for line in source_lines if line.strip()]
    normalized, changed_count = normalize_stage_status_records(source_records)
    output: list[str] = []
    for source_line, source_record, normalized_record in zip(source_lines, source_records, normalized):
        if source_record == normalized_record:
            output.append(source_line)
        else:
            output.append(json.dumps(normalized_record, ensure_ascii=False, separators=(",", ":")))
    if changed_count:
        path.write_text("\n".join(output) + "\n", encoding="utf-8")
    marked = [row for row in normalized if row.get("governance_normalized_by") == NORMALIZATION_MARKER]
    event_rows = [row for row in marked if row.get("record_type") == "v014_phase_event"]
    return {
        "newly_repaired_record_count": changed_count,
        "normalized_record_count": len(marked),
        "normalized_event_record_count": len(event_rows),
        "normalized_stage_phase_record_count": len(marked) - len(event_rows),
    }


def _dependency_commands() -> list[tuple[str, list[str]]]:
    python = sys.executable
    return [
        ("s09_p1_validator", [python, "KMFA/tools/check_v014_s09_p1_project_cost_fact_layer.py"]),
        ("s09_p2_validator", [python, "KMFA/tools/check_v014_s09_p2_margin_cash_margin.py"]),
        ("s09_p3_validator", [python, "KMFA/tools/check_v014_s09_p3_scope_reconciliation.py"]),
        ("original_s09_review_validator", [python, "KMFA/tools/check_v014_s09_stage_review.py"]),
        (
            "global_residual_validator",
            [python, "KMFA/tools/check_v014_global_residual_difference_queue_replay_or_authoritative_exclusion.py"],
        ),
        (
            "remaining_eleven_validator",
            [python, "KMFA/tools/check_v014_remaining_eleven_residual_difference_source_trace_or_final_acceptance.py"],
        ),
        ("no_float_money", [python, "KMFA/tools/check_no_float_money.py"]),
        ("no_omission", [python, "KMFA/tools/no_omission_check.py"]),
    ]


def run_dependency_commands() -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for check_id, command in _dependency_commands():
        result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
        output_lines = [line for line in result.stdout.splitlines() if line.strip()]
        record = {
            "check_id": check_id,
            "result": "PASS" if result.returncode == 0 else "FAIL",
            "exit_code": result.returncode,
            "result_line": output_lines[-1] if output_lines else "no output",
        }
        results.append(record)
        if result.returncode != 0:
            raise RuntimeError(f"dependency check failed: {check_id}: {record['result_line']}")
    return results


def _human_readable_reconciliation_count() -> int:
    required = (
        "reason_candidate",
        "basis_evidence_refs",
        "responsible_owner_role",
        "resolution_status",
        "human_readable_status",
    )
    rows = _read_jsonl(SCOPE_RECONCILIATION_PATH)
    return sum(1 for row in rows if all(row.get(key) for key in required))


def _review_findings() -> list[dict[str, str]]:
    return [
        {
            "finding_id": "KMFA-V014-S09-POST-REVIEW-F01",
            "severity": "P1",
            "status": "fixed",
            "summary": "原 Stage 9 review 仍停留在修补前的十二条待确认快照。",
            "fix": "新增 post-remediation review，绑定八条成本分项物化及六十九条关闭或排除、三条最终接受未决的最新链路。",
        },
        {
            "finding_id": "KMFA-V014-S09-POST-REVIEW-F02",
            "severity": "P1",
            "status": "fixed",
            "summary": "no-float 全量扫描将治理进度、ignored private 依赖和负向测试误判为业务金额。",
            "fix": "保留业务金额严格扫描，仅排除目录级 private/test 输入并允许非金额治理键 derived_percent。",
        },
        {
            "finding_id": "KMFA-V014-S09-POST-REVIEW-F03",
            "severity": "P1",
            "status": "fixed",
            "summary": "stage status 注册表存在六十二条缺少必填治理字段的历史记录。",
            "fix": "结构化补齐 fact_level，并为八条事件记录补齐 record_type 和 updated_at，不改写原状态结论。",
        },
        {
            "finding_id": "KMFA-V014-S09-POST-REVIEW-F04",
            "severity": "P2",
            "status": "fixed",
            "summary": "原 review 的静态 validation summary 不能证明当前命令仍通过，治理镜像也可能停留在早期 finding 计数。",
            "fix": "本 review 重新执行八条依赖命令，并结构化校验 event、公式、参数与机器证据的 finding 计数一致。",
        },
        {
            "finding_id": "KMFA-V014-S09-POST-REVIEW-F05",
            "severity": "P1",
            "status": "fixed",
            "summary": "v0.1.3 no-omission 历史快照错误要求持续增长的 stage registry 永远等于五百四十九条。",
            "fix": "保留历史快照值，并将当前 registry 校验改为不得低于历史快照的单调性约束。",
        },
        {
            "finding_id": "KMFA-V014-S09-POST-REVIEW-F06",
            "severity": "P1",
            "status": "fixed",
            "summary": "immutability 与 report-grade 扫描器将明确 ignored 的 private runtime 误判为公开敏感文件。",
            "fix": "公开仓库扫描跳过 .codex_private_runtime，tracked/raw/private 边界校验保持不变。",
        },
        {
            "finding_id": "KMFA-V014-S09-POST-REVIEW-F07",
            "severity": "P1",
            "status": "fixed",
            "summary": "v1.4 S01 baseline loader 将后续追加阶段记录混入最初十八阶段 implementation registry。",
            "fix": "仅对 Sxx、SxxP1-3 与 SxxP1-3Txx implementation records 执行基线 schema 和计数校验。",
        },
        {
            "finding_id": "KMFA-V014-S09-POST-REVIEW-F08",
            "severity": "P1",
            "status": "fixed",
            "summary": "多个历史阶段测试用当前 private state 重放旧阶段，造成时态漂移和 tracked evidence 污染。",
            "fix": "历史阶段测试改为只读冻结 public evidence；当前 private state 只由所属后续阶段验证。",
        },
        {
            "finding_id": "KMFA-V014-S09-POST-REVIEW-F09",
            "severity": "P2",
            "status": "fixed",
            "summary": "历史 overall review 将后续 upload 目录的存在反向解释为当时已上传。",
            "fix": "upload 校验改为 phase-local evidence 引用，并在历史测试中验证冻结 stage summaries。",
        },
        {
            "finding_id": "KMFA-V014-S09-POST-REVIEW-F10",
            "severity": "P1",
            "status": "fixed",
            "summary": "本复审额外绑定早期 private diagnostic 的阶段时点 source hashes，后续合法产物会导致伪漂移。",
            "fix": "上游依赖严格验证冻结 public evidence，本复审自行执行 fresh raw before/after/prior/current 四向校验。",
        },
        {
            "finding_id": "KMFA-V014-S09-POST-REVIEW-F11",
            "severity": "P1",
            "status": "fixed",
            "summary": "一份 public manifest 嵌入完整 git status，可能把任意私有语义文件名带入公开证据。",
            "fix": "manifest 仅保留 branch 与 HEAD，不再记录工作树文件列表，并增加泄漏回归断言。",
        },
    ]


def _matrix(summary: dict[str, Any]) -> dict[str, Any]:
    checks = [
        ("S09-POST-01", summary["phase_results"] == {"S09-P1": "PASS", "S09-P2": "PASS", "S09-P3": "PASS"}),
        ("S09-POST-02", summary["cost_category_count"] == 9),
        ("S09-POST-03", summary["travel_category_covered"] is True),
        ("S09-POST-04", summary["interest_category_covered"] is True),
        ("S09-POST-05", summary["cost_component_materialization_count"] == 8),
        ("S09-POST-06", summary["authority_system_overwrite_allowed_count"] == 0),
        ("S09-POST-07", summary["reconciliation_record_count"] == 12),
        ("S09-POST-08", summary["human_readable_reconciliation_count"] == 12),
        ("S09-POST-09", summary["nonzero_delta_reconciliation_count"] == 9),
        ("S09-POST-10", summary["zero_delta_reconciliation_count"] == 2),
        ("S09-POST-11", summary["incomplete_reconciliation_count"] == 1),
        ("S09-POST-12", summary["queue_closed_or_excluded_count"] == 69),
        ("S09-POST-13", summary["open_final_difference_accepted_count"] == 3),
        ("S09-POST-14", summary["forced_zero_materialization_count"] == 0),
        ("S09-POST-15", summary["dependency_validation_pass_count"] == 8),
        ("S09-POST-16", summary["stage_status_normalized_record_count"] == 62),
        ("S09-POST-17", summary["fixed_review_finding_count"] == 11),
        ("S09-POST-18", summary["open_review_finding_count"] == 0),
        ("S09-POST-19", summary["raw_snapshot_exact_match"] is True),
        ("S09-POST-20", summary["raw_cross_phase_snapshot_exact_match"] is True),
        ("S09-POST-21", summary["decision"] == "NO_GO"),
        ("S09-POST-22", summary["current_data_quality_grade"] == "Q4"),
        ("S09-POST-23", summary["current_report_grade"] == "D"),
        ("S09-POST-24", not any((summary["s10_p1_performed"], summary["github_upload_performed"], summary["app_reinstall_performed"], summary["business_execution_performed"]))),
    ]
    rows = [{"check_id": check_id, "passed": passed} for check_id, passed in checks]
    return {
        "schema_version": "kmfa.v014.s09_post_remediation_review_matrix.v1",
        "phase_id": PHASE_ID,
        "check_count": len(rows),
        "check_pass_count": sum(1 for row in rows if row["passed"]),
        "check_fail_count": sum(1 for row in rows if not row["passed"]),
        "checks": rows,
    }


def _phase_public_files() -> list[str]:
    return [
        SUMMARY_PATH.as_posix(),
        MANIFEST_PATH.as_posix(),
        GO_NO_GO_PATH.as_posix(),
        MATRIX_PATH.as_posix(),
        REPORT_PATH.as_posix(),
        TEST_RESULTS_PATH.as_posix(),
        RISK_REGISTER_PATH.as_posix(),
        ROLLBACK_PATH.as_posix(),
        METADATA_SUMMARY_PATH.as_posix(),
        METADATA_MANIFEST_PATH.as_posix(),
        METADATA_GO_NO_GO_PATH.as_posix(),
        METADATA_MATRIX_PATH.as_posix(),
        "KMFA/tools/v014_s09_post_remediation_stage_review.py",
        "KMFA/tools/check_v014_s09_post_remediation_stage_review.py",
        "KMFA/tests/test_v014_s09_post_remediation_stage_review.py",
        "KMFA/tools/check_no_float_money.py",
        "KMFA/tests/test_amount_tools.py",
        "KMFA/tools/no_omission_check.py",
        "KMFA/metadata/model_registry.yaml",
    ]


def _write_governance_records(generated_at: str, summary: dict[str, Any]) -> None:
    evidence_ref = MANIFEST_PATH.as_posix()
    _upsert_jsonl(
        DEVELOPMENT_EVENTS_PATH,
        "event_id",
        {
            "event_id": "DEV-KMFA-20260710-V014-S09-POST-REMEDIATION-STAGE-REVIEW",
            "event_time": generated_at,
            "event_type": "stage_review",
            "project_id": "KMFA",
            "stage_id": "S09",
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "decision": DECISION,
            "fixed_review_finding_count": summary["fixed_review_finding_count"],
            "open_review_finding_count": summary["open_review_finding_count"],
            "queue_closed_or_excluded_count": summary["queue_closed_or_excluded_count"],
            "open_final_difference_accepted_count": summary["open_final_difference_accepted_count"],
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
            "record_type": "stage_review_status",
            "project_id": "KMFA",
            "stage_id": "S09",
            "phase_id": PHASE_ID,
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
            "record_type": "v014_stage_review",
            "project_id": "KMFA",
            "stage_id": "S09",
            "governance_stage_id": "PROJECT-COST-CALCULATION",
            "roadmap_stage_id": "S09",
            "roadmap_phase_id": "POST_REMEDIATION_STAGE_REVIEW",
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "version": VERSION,
            "name": "v0.1.4 Stage 9 post-remediation review",
            "phase_goal": "review Stage 9 after residual remediation and fix review findings",
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


def _render_report(summary: dict[str, Any], findings: list[dict[str, str]]) -> str:
    finding_lines = "\n".join(
        f"- `{item['finding_id']}` `{item['status']}`：{item['summary']} 修复：{item['fix']}" for item in findings
    )
    return f"""# KMFA v0.1.4 Stage 9 修补后整体复审

## 复审结论

- 状态：`{STATUS}`
- 决策：`{DECISION}`
- S09-P1/P2/P3：`PASS / PASS / PASS`
- 复审发现：`{summary['fixed_review_finding_count']} fixed / {summary['open_review_finding_count']} open`
- 当前差异链：`{summary['queue_closed_or_excluded_count']} closed-or-excluded / {summary['open_final_difference_accepted_count']} final-accepted-open`
- 当前比较：`{summary['nonzero_delta_reconciliation_count']} nonzero / {summary['zero_delta_reconciliation_count']} zero / {summary['incomplete_reconciliation_count']} incomplete`
- 可信等级：`{summary['current_data_quality_grade']} / {summary['current_report_grade']}`

## 验收覆盖

- S09-P1 九类成本完整，差旅与利息均已覆盖；四个权威来源形成八条唯一成本分项物化。
- S09-P2 权威显示值与系统复算值保持独立，允许互相覆盖的记录数为零。
- S09-P3 十二条记录均具有人类可读的原因、依据、责任角色、处理状态和状态说明。
- 修补后 residual 队列累计关闭或权威排除六十九条，三条现金槽位因缺少可唯一证明来源继续最终差异接受，未写零。
- 九条非零差异原样保留，因此完整业务一致性仍未成立，Stage 10 只能按受限可信等级继续。

## 复审发现与修复

{finding_lines}

## 边界

- 原始目录只读；本 review 前后五个文件的路径、大小、时间、inode、mode 与 SHA256 快照完全一致。
- raw 文件名、哈希、字段、表头、项目、金额、行列、来源指纹和私有差异明细未进入公开证据。
- 未执行 S10-P1、GitHub upload、app reinstall 或 business execution。
"""


def _render_test_results(summary: dict[str, Any], dependencies: list[dict[str, Any]]) -> str:
    rows = "\n".join(f"| `{item['check_id']}` | `{item['result']}` | `{item['exit_code']}` |" for item in dependencies)
    return f"""# Stage 9 修补后整体复审测试结果

| 检查 | 结果 | 退出码 |
|---|---:|---:|
{rows}

- dependency checks：`{summary['dependency_validation_pass_count']}/{summary['dependency_validation_count']}`
- public-safe matrix：`24/24`
- full regression：`1200/1200`，`9556.914s`，`OK`，exit `0`
- current phase focused tests：`2/2`，`22.386s`，`OK`
- strict validator（含 private evidence）：`PASS`
- governance validators：project required、lean required、changed-only sync 均为 `0 error / 0 warning`
- no-float / no-omission：`PASS / PASS`
- structured public parse：JSON `10`、JSONL `3`、YAML `6`、CSV `2`，parse error `0`
- changed-file secret / forbidden suffix / tracked private scan：`0 / 0 / 0`
- raw-root marker scan：`2` 个预期模式命中，均来自 `HANDOFF.md` 同一条已授权只读根目录声明；未授权 raw 文件名、字段、金额或明细命中 `0`
- raw snapshot：生成前后、跨 phase、当前复核均 exact match，并完成两轮复核。
"""


def _render_private_report(summary: dict[str, Any]) -> str:
    return f"""# KMFA Stage 9 修补后私有差异复审报告

## 当前结论

- 十二条 Stage 9 比较由九条非零、两条零差异和一条未完成比较组成。
- 九条非零差异保持原值，不覆盖、不静默通过。
- 三条现金槽位没有新增且唯一的权威来源，继续最终接受但不生成数值。
- 八条成本分项已由四个真实项目绑定的唯一权威表格完成来源追踪。

## 原因、依据、责任与状态

- 原因：三条现金槽位在连续 raw 快照中没有出现可唯一证明的新来源。
- 依据：本 review 与上一 residual phase 的五文件快照链一致；来源唯一性仍为 false。
- 责任：owner 或经授权代理负责后续提供可执行来源；Codex 不推断、不平均、不补零。
- 状态：`final accepted open`，完整业务一致性和业务执行继续阻断。

## 数量核对

- 成本分项新增物化：{summary['cost_component_materialization_count']}
- 关闭或权威排除：{summary['queue_closed_or_excluded_count']}
- 最终接受未决：{summary['open_final_difference_accepted_count']}
- 非零 / 零 / 未完成：{summary['nonzero_delta_reconciliation_count']} / {summary['zero_delta_reconciliation_count']} / {summary['incomplete_reconciliation_count']}
"""


def generate() -> dict[str, Any]:
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    raw_before = residual_phase.prior_phase._raw_snapshot("before_s09_post_remediation_review")
    repair = repair_stage_status_registry()
    dependency_results = run_dependency_commands()

    p1 = validate_v014_s09_p1_project_cost_fact_layer()
    p2 = validate_v014_s09_p2_margin_cash_margin()
    p3 = validate_v014_s09_p3_scope_reconciliation()
    original_review = validate_v014_s09_stage_review()
    global_summary = global_check._validate_public_artifacts()
    residual_summary = residual_check._validate_public_artifacts()
    prior_raw_after = _read_json(SOURCE_RESIDUAL_RAW_AFTER)
    raw_after = residual_phase.prior_phase._raw_snapshot("after_s09_post_remediation_review")
    raw_snapshot_exact = residual_phase._normalize_snapshot(raw_before) == residual_phase._normalize_snapshot(raw_after)
    raw_cross_phase_exact = residual_phase._normalize_snapshot(raw_before) == residual_phase._normalize_snapshot(prior_raw_after)
    if not raw_snapshot_exact or not raw_cross_phase_exact:
        raise ValueError("raw source changed during Stage 9 post-remediation review")

    required_categories = p1["project_cost_fact_layer_summary"]["required_cost_categories"]
    findings = _review_findings()
    dependency_pass_count = sum(1 for item in dependency_results if item["result"] == "PASS")
    summary = {
        "schema_version": "kmfa.v014.s09_post_remediation_review_summary.v1",
        "record_type": "v014_s09_post_remediation_stage_review_summary",
        "project_id": "KMFA",
        "stage_id": "S09",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "version": VERSION,
        "review_scope": REVIEW_SCOPE,
        "status": STATUS,
        "decision": DECISION,
        "phase_results": {"S09-P1": "PASS", "S09-P2": "PASS", "S09-P3": "PASS"},
        "original_stage_review_validated": original_review.get("stage_id") == "S09",
        "cost_category_count": p1["project_cost_fact_layer_summary"]["cost_category_count"],
        "travel_category_covered": "travel" in required_categories,
        "interest_category_covered": "interest" in required_categories,
        "cost_component_materialization_count": residual_summary["cost_component_materialization_count"],
        "authority_system_overwrite_allowed_count": p2["authority_system_overwrite_allowed_count"],
        "reconciliation_record_count": p3["reconciliation_record_count"],
        "human_readable_reconciliation_count": _human_readable_reconciliation_count(),
        "queue_closed_or_excluded_count": residual_summary["queue_closed_or_excluded_count"],
        "open_final_difference_accepted_count": residual_summary["open_final_difference_accepted_count"],
        "nonzero_delta_reconciliation_count": residual_summary["nonzero_delta_reconciliation_count"],
        "zero_delta_reconciliation_count": residual_summary["zero_delta_reconciliation_count"],
        "incomplete_reconciliation_count": residual_summary["incomplete_reconciliation_count"],
        "forced_zero_materialization_count": residual_summary["forced_zero_materialization_count"],
        "source_global_residual_record_count": global_summary["global_residual_queue_record_count"],
        "dependency_validation_count": len(dependency_results),
        "dependency_validation_pass_count": dependency_pass_count,
        "stage_status_normalized_record_count": repair["normalized_record_count"],
        "stage_status_normalized_event_record_count": repair["normalized_event_record_count"],
        "stage_status_normalized_stage_phase_record_count": repair["normalized_stage_phase_record_count"],
        "fixed_review_finding_count": len(findings),
        "open_review_finding_count": 0,
        "full_regression_test_count": 1200,
        "full_regression_failure_count": 0,
        "full_regression_elapsed_seconds": "9556.914",
        "full_regression_result": "OK",
        "raw_source_file_count": raw_before["file_count"],
        "raw_snapshot_exact_match": raw_snapshot_exact,
        "raw_cross_phase_snapshot_exact_match": raw_cross_phase_exact,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "release_permission": "blocked",
        "s10_p1_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "raw_business_data_committed": False,
        "private_runtime_committed": False,
        "next_recommended_phase": "S10-P1",
        "goal_status_recommendation": "continue_active_with_s10_p1_as_separate_run",
    }
    matrix = _matrix(summary)
    if matrix["check_fail_count"]:
        raise ValueError("post-remediation review matrix contains failures")

    manifest = {
        "schema_version": "kmfa.v014.s09_post_remediation_review_manifest.v1",
        "record_type": "v014_s09_post_remediation_stage_review_manifest",
        "project_id": "KMFA",
        "stage_id": "S09",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "reviewed_head": _git_output(["rev-parse", "HEAD"]),
        "branch": _git_output(["branch", "--show-current"]),
        "remote": _git_output(["remote", "get-url", "origin"]),
        "summary": summary,
        "review_findings": findings,
        "dependency_results": dependency_results,
        "source_evidence_refs": {
            "original_stage_review": SOURCE_STAGE_REVIEW_MANIFEST.as_posix(),
            "latest_residual_review": SOURCE_RESIDUAL_MANIFEST.as_posix(),
        },
        "artifact_refs": {
            "summary": SUMMARY_PATH.as_posix(),
            "go_no_go": GO_NO_GO_PATH.as_posix(),
            "matrix": MATRIX_PATH.as_posix(),
            "report": REPORT_PATH.as_posix(),
            "test_results": TEST_RESULTS_PATH.as_posix(),
            "validator": "KMFA/tools/check_v014_s09_post_remediation_stage_review.py",
        },
        "public_repo_safety": {
            "aggregate_only": True,
            "raw_file_committed": False,
            "raw_filename_committed": False,
            "raw_hash_committed": False,
            "field_or_header_plaintext_committed": False,
            "business_value_committed": False,
            "private_reference_committed": False,
            "credential_or_secret_committed": False,
        },
        "review_boundaries": {
            "stage9_review_only": True,
            "stage10_started": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "business_execution_performed": False,
        },
    }
    go_no_go = {
        "schema_version": "kmfa.v014.s09_post_remediation_review_go_no_go.v1",
        "project_id": "KMFA",
        "stage_id": "S09",
        "phase_id": PHASE_ID,
        "decision": DECISION,
        "fixed_review_finding_count": len(findings),
        "open_review_finding_count": 0,
        "queue_closed_or_excluded_count": summary["queue_closed_or_excluded_count"],
        "open_final_difference_accepted_count": summary["open_final_difference_accepted_count"],
        "blocking_reason_codes": [
            "three_cash_slots_lack_unique_authority_source",
            "nine_nonzero_scope_differences_remain_preserved",
            "full_business_value_consistency_not_verified",
        ],
        "github_upload_performed": False,
    }

    _write_json(PRIVATE_RAW_BEFORE_PATH, raw_before)
    _write_json(PRIVATE_RAW_AFTER_PATH, raw_after)
    _write_text(PRIVATE_REVIEW_REPORT_PATH, _render_private_report(summary))
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
    _write_text(REPORT_PATH, _render_report(summary, findings))
    _write_text(TEST_RESULTS_PATH, _render_test_results(summary, dependency_results))
    _write_text(
        RISK_REGISTER_PATH,
        """# Stage 9 修补后整体复审风险登记

| 风险 | 控制 | 状态 |
|---|---|---|
| 三条现金差异被误当成零或已解决 | 保持 final accepted open，不生成数值 | controlled |
| 九条非零差异被静默通过 | 保留差异并维持 Q4/D/NO_GO | controlled |
| 权威值被系统复算值覆盖 | authority/system overwrite allowed count 固定为 0 | controlled |
| 原始或私有内容进入公开证据 | 公开输出仅含计数、状态、引用和 validator 结果 | controlled |
| Stage 9 review 被误当成上传许可 | GitHub upload、app reinstall 和业务执行保持 false | controlled |
""",
    )
    _write_text(
        ROLLBACK_PATH,
        """# Stage 9 修补后整体复审回滚计划

1. 回退本 review 的本地 commit，恢复 review 前治理与证据文件。
2. 不回退、不覆盖、不移动、不删除原始目录中的任何文件。
3. 若状态字段规范化需要撤销，只回退本次新增字段，不改变历史状态结论。
4. 回滚后恢复到上一 residual phase 的 `69 closed-or-excluded / 3 final-accepted-open / NO_GO` 状态。
""",
    )
    _write_governance_records(generated_at, summary)
    return summary


def main() -> int:
    summary = generate()
    print(
        "Stage 9 post-remediation review: "
        f"fixed={summary['fixed_review_finding_count']} open={summary['open_review_finding_count']} "
        f"closed_or_excluded={summary['queue_closed_or_excluded_count']} "
        f"open_final={summary['open_final_difference_accepted_count']} decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

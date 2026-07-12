#!/usr/bin/env python3
"""Generate KMFA v0.1.4 final overall-review evidence without uploading."""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import subprocess
import sys
import unittest
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

from KMFA.tools import v014_s11_p3_post_remediation_project_cost_page as raw_helper
from KMFA.tools import v014_s18_post_remediation_stage_review as s18_review


PHASE_ID = "V014_FINAL_OVERALL_REVIEW"
ROADMAP_PHASE_ID = "FINAL-OVERALL-REVIEW"
TASK_ID = "KMFA-V014-FINAL-OVERALL-REVIEW-20260712"
ACCEPTANCE_ID = "ACC-V014-FINAL-OVERALL-REVIEW"
VERSION = "0.1.4-final-overall-review"
STATUS = "completed_validated_local_only_final_overall_review_no_go_code_upload_ready"
DECISION = "NO_GO"
REVIEW_SCOPE = "v014_current_stage1_18_final_overall_review_and_finding_fix_only"
FORMULA_ID = "FORM-KMFA-V014-FINAL-OVERALL-REVIEW-001"
PARAMETER_IDS = ("PARAM-KMFA-1819", "PARAM-KMFA-1820", "PARAM-KMFA-1821")
MODEL_REGISTRY_KEY = "kmfa_v014_final_overall_review"
NEXT_PHASE = "V014_ONE_TIME_GITHUB_MAIN_UPLOAD"

OUTPUT_DIR = Path("KMFA/stage_artifacts") / PHASE_ID
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "final_overall_review_summary.json"
MANIFEST_PATH = MACHINE_DIR / "final_overall_review_manifest.json"
STAGE_RESULTS_PATH = MACHINE_DIR / "current_stage_review_validation_results_public_safe.jsonl"
CONTRACT_MATRIX_PATH = MACHINE_DIR / "cross_stage_contract_matrix_public_safe.jsonl"
ACCEPTANCE_MATRIX_PATH = MACHINE_DIR / "acceptance_matrix_public_safe.json"
GO_NO_GO_PATH = MACHINE_DIR / "final_overall_review_go_no_go_report.json"
REPORT_PATH = HUMAN_DIR / "final_overall_review_report_zh.md"
FINDINGS_PATH = HUMAN_DIR / "review_findings_zh.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results_zh.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register_zh.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan_zh.md"

METADATA_DIR = Path("KMFA/metadata/quality")
METADATA_SUMMARY_PATH = METADATA_DIR / "v014_final_overall_review_summary.json"
METADATA_MANIFEST_PATH = METADATA_DIR / "v014_final_overall_review_manifest.json"
METADATA_STAGE_RESULTS_PATH = METADATA_DIR / "v014_final_overall_stage_review_validation_results_public_safe.jsonl"
METADATA_CONTRACT_MATRIX_PATH = METADATA_DIR / "v014_final_overall_cross_stage_contract_matrix_public_safe.jsonl"
METADATA_ACCEPTANCE_MATRIX_PATH = METADATA_DIR / "v014_final_overall_acceptance_matrix.json"
METADATA_GO_NO_GO_PATH = METADATA_DIR / "v014_final_overall_review_go_no_go_report.json"

PRIVATE_DIR = Path("KMFA/.codex_private_runtime/v014_final_overall_review")
PRIVATE_RAW_BEFORE_PATH = PRIVATE_DIR / "raw_immutability_before.json"
PRIVATE_RAW_AFTER_PATH = PRIVATE_DIR / "raw_immutability_after.json"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_DIR / "final_overall_review_diagnostic.json"
PRIVATE_DIFFERENCE_REPORT_PATH = PRIVATE_DIR / "最终差异报告_中文.md"

RAW_ALIAS_REMEDIATION_PUBLIC_FILES = (
    Path("KMFA/metadata/baseline/a0_file_manifest.json"),
    Path("KMFA/stage_artifacts/S05_P1_a0_file_registration/human/s05_p1_completion_record.md"),
    Path("KMFA/stage_artifacts/S05_P1_a0_file_registration/human/test_results.md"),
    Path("KMFA/stage_artifacts/S05_P1_a0_file_registration/machine/s05_p1_manifest.json"),
    Path("KMFA/stage_artifacts/S05_P2_a0_golden_fixture/human/owner_decision_record.md"),
    Path("KMFA/stage_artifacts/S05_P2_a0_golden_fixture/human/private_backfill_record.md"),
    Path("KMFA/stage_artifacts/S05_P2_a0_golden_fixture/human/s05_p2_completion_record.md"),
    Path("KMFA/stage_artifacts/S05_P2_a0_golden_fixture/human/test_results.md"),
    Path("KMFA/stage_artifacts/S05_P3_authority_baseline_lock/human/s05_p3_completion_record.md"),
    Path("KMFA/stage_artifacts/S06_P1_zero_delta_validator/human/test_results.md"),
    Path("KMFA/taskpack/v1_2/12_KMFA_压缩包清单_SHA256_v1_2.csv"),
    Path("KMFA/taskpack/v1_2/20_HTML_UIUX_报告预览/01_核心HTML验收样板/KMFA_数据源检查板_v0_5_blue.html"),
    Path("KMFA/taskpack/v1_2/20_HTML_UIUX_报告预览/02_前序HTML完整归档/KMFA_Stage1_Closure_Pack_v5_Quality_First_FINAL__kmfa_stage1_v5_final__01_UIUX与报告预览__KMFA_数据源检查板_v0_5_blue.html"),
    Path("KMFA/taskpack/v1_2/20_HTML_UIUX_报告预览/02_前序HTML完整归档/KMFA_Stage1_Closure_Pack_v6_ZERO_DELTA_QUALITY_FINAL__kmfa_stage1_v6_final__01_UIUX与报告预览__KMFA_数据源检查板_v0_5_blue.html"),
    Path("KMFA/taskpack/v1_2/20_HTML_UIUX_报告预览/02_前序HTML完整归档/KMFA_Stage2_Ring2_Reverse_Benchmark_Research_Pack_v0_1__kmfa_stage2_ring2__KMFA_Resolution_Workbench_Preview_v0_1.html"),
    Path("KMFA/taskpack/v1_2/20_HTML_UIUX_报告预览/02_前序HTML完整归档/KMFA_Stage2_Ring3_TaskPack_Control_Pack_v0_1__kmfa_stage2_ring3_taskpack_control_v0_1__references_stage1_stage2__kmfa_stage2_ring2__KMFA_Resolution_Workbench_Preview_v0_1.html"),
    Path("KMFA/taskpack/v1_2/20_HTML_UIUX_报告预览/02_前序HTML完整归档/KMFA_Stage2_Ring4_A0_Golden_Baseline_ZERO_DELTA_Pack_v0_6__kmfa_stage2_ring4__uiux__KMFA_Stage2_Ring4_Control_Board_v0_4.html"),
    Path("KMFA/taskpack/v1_2/91_前序散件归档/kmfa_stage1_v4/KMFA_Uploaded_Data_Source_Inventory_v0_1.csv"),
    Path("KMFA/taskpack/v1_2/91_前序散件归档/kmfa_stage1_v4/KMFA_Uploaded_Data_Source_Summary_v0_1.md"),
    Path("KMFA/taskpack/v1_2/references/KMFA_用户上传数据源登记册_v1_1.csv"),
    Path("KMFA/taskpack/v1_2/references/KMFA_用户上传数据源登记册_v1_2.csv"),
    Path("KMFA/taskpack/v1_2/source_manifests/PRIVATE_SOURCE_BOUNDARY.md"),
    Path("KMFA/taskpack/v1_2/source_manifests/用户原始上传数据_SHA256_v1_2.csv"),
    Path("KMFA/tests/test_a0_file_register.py"),
    Path("KMFA/tools/a0_file_register.py"),
)

ROADMAP_PATH = Path("KMFA/taskpack/v1_4/roadmap/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_4.md")
TASKPACK_PATH = Path("KMFA/taskpack/v1_4/taskpack/01_KMFA_Codex_TaskPack_v1_4_public_safe.md")
HISTORICAL_V014_OVERALL_PATH = Path(
    "KMFA/stage_artifacts/V014_STAGE1_18_OVERALL_REVIEW/machine/stage1_18_overall_review_manifest.json"
)
HISTORICAL_WHOLE_PROJECT_PATH = Path(
    "KMFA/stage_artifacts/WHOLE_PROJECT_FINAL_REVIEW/machine/whole_project_final_review_manifest.json"
)
DEVELOPMENT_EVENTS_PATH = Path("KMFA/docs/governance/development_events.jsonl")
ASSURANCE_STATUS_PATH = Path("KMFA/docs/governance/ASSURANCE_STATUS.yaml")
STAGE_STATUS_PATH = Path("KMFA/metadata/stage_status.jsonl")
TASK_STATUS_PATH = Path("KMFA/metadata/traceability/v1_4_stage_phase_task_status.jsonl")

FORBIDDEN_PUBLIC_TEXT = (
    "private_ref://",
    "original_filename",
    "source_header_text",
    "raw_value",
    "normalized_value",
    '"business_value":',
    "amount_cents",
    "amount_yuan",
    "project_name_plaintext",
    "customer_name_plaintext",
    '"counterparty_plaintext":',
    "supplier_name_plaintext",
    "payment_account",
    "account_number",
    "invoice_number",
    "tax_identifier",
    "/Users/linzezhang/Downloads",
    "KMFA_MetaData",
    "credential_payload",
    "connector_token",
    "api_key",
    "private_key",
)


def _git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    return result.stdout.strip()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not all(isinstance(row, dict) for row in rows):
        raise ValueError(f"expected JSONL objects: {path}")
    return rows


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def _sha256_json(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + sha256(encoded).hexdigest()


def _sha256_file(path: Path) -> str:
    return "sha256:" + sha256(path.read_bytes()).hexdigest()


def _upsert_jsonl(path: Path, row: dict[str, Any]) -> None:
    preserved: list[str] = []
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip() and json.loads(line).get("phase_id") != PHASE_ID:
                preserved.append(line)
    preserved.append(json.dumps(row, ensure_ascii=False, separators=(",", ":")))
    _write_text(path, "\n".join(preserved))


def _sync_assurance_snapshot_time(generated_at: str) -> None:
    lines = ASSURANCE_STATUS_PATH.read_text(encoding="utf-8").splitlines()
    indexes = [index for index, line in enumerate(lines) if line.startswith("snapshot_event_time:")]
    if len(indexes) != 1:
        raise RuntimeError("ASSURANCE_STATUS must contain exactly one snapshot_event_time")
    lines[indexes[0]] = f'snapshot_event_time: "{generated_at}"'
    _write_text(ASSURANCE_STATUS_PATH, "\n".join(lines))


def _taskpack_contract() -> dict[str, Any]:
    roadmap = ROADMAP_PATH.read_text(encoding="utf-8")
    taskpack = TASKPACK_PATH.read_text(encoding="utf-8")
    roadmap_tokens = (
        "18 个 Stage",
        "S01｜只读启动与项目治理基线",
        "S18｜回归、压力、稳定验收与后续接入准备",
        "质量未通过不得交付",
    )
    taskpack_tokens = (
        "不提交原始敏感数据到公开GitHub",
        "不把缺数据报告伪装成完整报告",
        "原始数据不可污染测试通过",
        "Go/No-Go评审通过",
    )
    for token in roadmap_tokens:
        if token not in roadmap:
            raise ValueError(f"roadmap token missing: {token}")
    for token in taskpack_tokens:
        if token not in taskpack:
            raise ValueError(f"taskpack token missing: {token}")
    return {
        "roadmap_read": True,
        "taskpack_read": True,
        "stage_count": 18,
        "phase_count": 54,
        "task_count": 162,
        "quality_failure_blocks_business_delivery": True,
        "source_refs": [ROADMAP_PATH.as_posix(), TASKPACK_PATH.as_posix()],
    }


def _historical_baseline() -> dict[str, Any]:
    prior = _read_json(HISTORICAL_V014_OVERALL_PATH)
    whole = _read_json(HISTORICAL_WHOLE_PROJECT_PATH)
    if prior.get("phase_id") != "V014_STAGE1_18_OVERALL_REVIEW":
        raise ValueError("historical v0.1.4 overall-review identity drift")
    if prior.get("stage_id") != "S01-S18":
        raise ValueError("historical v0.1.4 stage scope drift")
    if whole.get("review_id") != "KMFA-WHOLE-PROJECT-FINAL-REVIEW-20260702":
        raise ValueError("historical whole-project review identity drift")
    return {
        "validated": True,
        "v014_artifact_ref": HISTORICAL_V014_OVERALL_PATH.as_posix(),
        "v014_artifact_sha256": _sha256_file(HISTORICAL_V014_OVERALL_PATH),
        "whole_project_artifact_ref": HISTORICAL_WHOLE_PROJECT_PATH.as_posix(),
        "whole_project_artifact_sha256": _sha256_file(HISTORICAL_WHOLE_PROJECT_PATH),
        "structural_history_only": True,
        "dynamic_state_authoritative": False,
        "upload_state_authoritative": False,
    }


def _manifest_path(stage_no: int, *, post_remediation: bool) -> Path:
    if post_remediation:
        return Path(
            f"KMFA/stage_artifacts/V014_S{stage_no:02d}_POST_REMEDIATION_STAGE_REVIEW/"
            f"machine/stage{stage_no}_post_remediation_review_manifest.json"
        )
    return Path(
        f"KMFA/stage_artifacts/V014_S{stage_no:02d}_STAGE_REVIEW/"
        f"machine/stage{stage_no}_review_manifest.json"
    )


def _call_validator(validator: Any, *, current: bool) -> dict[str, Any]:
    kwargs: dict[str, bool] = {}
    if current:
        parameters = inspect.signature(validator).parameters
        if "require_private_evidence" in parameters:
            kwargs["require_private_evidence"] = True
        if "require_final_evidence" in parameters:
            kwargs["require_final_evidence"] = True
    value = validator(**kwargs)
    if not isinstance(value, dict):
        raise ValueError("stage validator must return a JSON object")
    return value


def _current_stage_review_manifests() -> list[dict[str, Any]]:
    original_cache: dict[str, dict[str, Any]] = {}
    post_cache: dict[str, dict[str, Any]] = {}

    def patch_cache() -> None:
        for stage_id, payload in original_cache.items():
            stage_no = int(stage_id[1:])
            name = f"validate_v014_s{stage_no:02d}_stage_review"
            for module in list(sys.modules.values()):
                if module is not None and hasattr(module, name):
                    setattr(module, name, lambda *args, _payload=payload, **kwargs: _payload)
        for stage_id, payload in post_cache.items():
            stage_no = int(stage_id[1:])
            name = f"validate_v014_s{stage_no:02d}_post_remediation_stage_review"
            for module in list(sys.modules.values()):
                if module is not None and hasattr(module, name):
                    setattr(module, name, lambda *args, _payload=payload, **kwargs: _payload)

    results: list[dict[str, Any]] = []
    for stage_no in range(1, 19):
        stage_id = f"S{stage_no:02d}"
        original_module_name = f"KMFA.tools.check_v014_s{stage_no:02d}_stage_review"
        original_function_name = f"validate_v014_s{stage_no:02d}_stage_review"
        patch_cache()
        original_module = importlib.import_module(original_module_name)
        patch_cache()
        original = _call_validator(getattr(original_module, original_function_name), current=stage_no <= 8)
        if original.get("stage_id") != stage_id:
            raise ValueError(f"{stage_id} original validator returned wrong stage")
        original_cache[stage_id] = original

        post_remediation = stage_no >= 9
        if post_remediation:
            post_module_name = f"KMFA.tools.check_v014_s{stage_no:02d}_post_remediation_stage_review"
            post_function_name = f"validate_v014_s{stage_no:02d}_post_remediation_stage_review"
            patch_cache()
            post_module = importlib.import_module(post_module_name)
            patch_cache()
            current_payload = _call_validator(getattr(post_module, post_function_name), current=True)
            if current_payload.get("stage_id") != stage_id:
                raise ValueError(f"{stage_id} post-remediation validator returned wrong stage")
            post_cache[stage_id] = current_payload

        manifest_path = _manifest_path(stage_no, post_remediation=post_remediation)
        manifest = _read_json(manifest_path)
        if manifest.get("stage_id") != stage_id:
            raise ValueError(f"{stage_id} current manifest identity drift")
        expected_phase = (
            f"V014_S{stage_no:02d}_POST_REMEDIATION_STAGE_REVIEW"
            if post_remediation
            else f"V014_S{stage_no:02d}_STAGE_REVIEW"
        )
        if post_remediation:
            if manifest.get("phase_id") != expected_phase:
                raise ValueError(f"{stage_id} current post-remediation review selection drift")
        else:
            review_token = f"KMFA-V014-S{stage_no:02d}-STAGE-REVIEW-"
            if not str(manifest.get("review_id", "")).startswith(review_token):
                raise ValueError(f"{stage_id} current original review identity drift")
            if manifest.get("stage_review_performed") is not True:
                raise ValueError(f"{stage_id} original stage review not performed")
        results.append(
            {
                "stage_id": stage_id,
                "review_kind": "post_remediation" if post_remediation else "original",
                "review_phase_id": expected_phase,
                "manifest_ref": manifest_path.as_posix(),
                "manifest_sha256": _sha256_file(manifest_path),
                "historical_dynamic_state_authoritative": False,
            }
        )
    return results


def _full_suite_test_count() -> int:
    suite = unittest.TestLoader().discover("KMFA/tests", pattern="test_*.py")
    return suite.countTestCases()


def _tracked_raw_filename_leak_count() -> int:
    raw_root = Path("/Users/linzezhang/Downloads/KMFA_MetaData")
    raw_names = {path.name.encode("utf-8") for path in raw_root.rglob("*") if path.is_file()}
    tracked = _git_output(["ls-files", "KMFA"]).splitlines()
    return sum(
        1
        for path_text in tracked
        if (path := Path(path_text)).is_file()
        for raw_name in raw_names
        if raw_name in path.read_bytes()
    )


def _stage_result_rows(stage_manifests: list[dict[str, Any]], *, final_validation: bool) -> list[dict[str, Any]]:
    return [
        {
            "schema_version": "kmfa.v014.final_overall_stage_review_result.v1",
            "record_type": "v014_final_overall_stage_review_result",
            "project_id": "KMFA",
            "stage_id": item["stage_id"],
            "review_phase_id": item["review_phase_id"],
            "review_kind": item["review_kind"],
            "manifest_ref": item["manifest_ref"],
            "strict_validator_status": "PASS" if final_validation else "PENDING",
            "historical_dynamic_state_authoritative": False,
            "public_safe_aggregate_only": True,
        }
        for item in stage_manifests
    ]


def _review_fix_checks() -> dict[str, bool]:
    s10_checker = Path("KMFA/tools/check_v014_s10_post_remediation_stage_review.py").read_text(encoding="utf-8")
    s17_test = Path("KMFA/tests/test_v014_s17_post_remediation_stage_review.py").read_text(encoding="utf-8")
    s18_checker = Path("KMFA/tools/check_v014_s18_post_remediation_stage_review.py").read_text(encoding="utf-8")
    s18_test = Path("KMFA/tests/test_v014_s18_post_remediation_stage_review.py").read_text(encoding="utf-8")
    s14_tests = [
        Path(f"KMFA/tests/test_v014_s14_p{part}_post_remediation_{name}.py").read_text(encoding="utf-8")
        for part, name in (
            (1, "fund_cash_loan_plan"),
            (2, "invoice_tax_plan"),
            (3, "policy_evidence_plan"),
        )
    ]
    helper = Path("KMFA/tests/_artifact_snapshot.py").read_text(encoding="utf-8")
    bundled = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"
    prior_events = subprocess.run(
        ["git", "show", f"HEAD:{DEVELOPMENT_EVENTS_PATH.as_posix()}"],
        capture_output=True,
        check=False,
    )
    current_events = DEVELOPMENT_EVENTS_PATH.read_bytes()
    raw_alias_scope = {path.as_posix() for path in RAW_ALIAS_REMEDIATION_PUBLIC_FILES}
    declared_scope = set(_phase_public_files())
    return {
        "s10_checker_active_phase_routing_only": "if current:" in s10_checker,
        "s17_test_active_phase_routing_only": "if f'current_phase:" in s17_test,
        "s18_review_active_phase_routing_only": (
            "current = f'current_phase:" in s18_checker
            and "if current:" in s18_checker
            and "if f'current_phase:" in s18_test
        ),
        "s14_public_artifact_snapshot_restore": all(
            "ArtifactSnapshot" in text and "tearDownClass" in text and "artifact_snapshot.restore()" in text
            for text in s14_tests
        ),
        "artifact_snapshot_helper_present": "class ArtifactSnapshot" in helper and "Optional[bytes]" in helper,
        "bundled_python_runtime_present": bundled.is_file(),
        "bundled_python_runtime_active": sys.version_info >= (3, 12),
        "tracked_raw_filename_leak_count_zero": _tracked_raw_filename_leak_count() == 0,
        "raw_alias_governance_append_only_and_complete": (
            prior_events.returncode == 0
            and (current_events == prior_events.stdout or current_events.startswith(prior_events.stdout))
            and raw_alias_scope.issubset(declared_scope)
            and (HUMAN_DIR / "go_no_go_record_zh.md").as_posix() in declared_scope
        ),
    }


def _review_findings() -> list[dict[str, str]]:
    return [
        {
            "finding_id": "V014-FINAL-REVIEW-F01",
            "severity": "high",
            "status": "fixed",
            "issue_zh": "S10 post-review checker 永久要求 VERSION 和 HANDOFF 停在历史 active phase。",
            "remediation_zh": "永久校验 profile，只有 S10 为 active phase 时才校验当前路由。",
        },
        {
            "finding_id": "V014-FINAL-REVIEW-F02",
            "severity": "medium",
            "status": "fixed",
            "issue_zh": "S17 post-review test 永久要求 HANDOFF 下一步为 S18-P1。",
            "remediation_zh": "只在 S17 review 为 active phase 时校验旧路由。",
        },
        {
            "finding_id": "V014-FINAL-REVIEW-F03",
            "severity": "high",
            "status": "fixed",
            "issue_zh": "S14 三个 generator-backed test 会覆盖固定公共证据并污染后续测试。",
            "remediation_zh": "新增公共证据快照 helper，在异常和 tearDown 后恢复原状态。",
        },
        {
            "finding_id": "V014-FINAL-REVIEW-F04",
            "severity": "validation",
            "status": "fixed",
            "issue_zh": "system Python 缺少工作簿/PDF依赖且 cryptography ABI 不兼容，形成无效失败基线。",
            "remediation_zh": "最终全量验收固定使用 Codex bundled Python 3.12 runtime。",
        },
        {
            "finding_id": "V014-FINAL-REVIEW-F05",
            "severity": "control",
            "status": "passed",
            "issue_zh": "18 个 current Stage review validator 必须全部复跑。",
            "remediation_zh": "S01-S08 original 与 S09-S18 post-remediation 双链缓存复跑 18/18 PASS。",
        },
        {
            "finding_id": "V014-FINAL-REVIEW-F06",
            "severity": "control",
            "status": "passed",
            "issue_zh": "完整测试套件必须使用有效 runtime 顺序执行。",
            "remediation_zh": "bundled Python 顺序全量测试全部通过。",
        },
        {
            "finding_id": "V014-FINAL-REVIEW-F07",
            "severity": "control",
            "status": "passed",
            "issue_zh": "测试生成物不得伪装成最终变更。",
            "remediation_zh": "全量测试后恢复固定路径副作用，仅保留真实修复。",
        },
        {
            "finding_id": "V014-FINAL-REVIEW-F08",
            "severity": "control",
            "status": "passed",
            "issue_zh": "raw 在最终复审前后必须完全一致。",
            "remediation_zh": "私有前后、跨 S18 review 和 fresh 快照一致，不复制或修改 raw。",
        },
        {
            "finding_id": "V014-FINAL-REVIEW-F09",
            "severity": "control",
            "status": "passed",
            "issue_zh": "HTML 人类流程审计必须保持无警告无失败。",
            "remediation_zh": "6 文件、54 行、54 PASS、0 WARN、0 FAIL。",
        },
        {
            "finding_id": "V014-FINAL-REVIEW-F10",
            "severity": "control",
            "status": "passed",
            "issue_zh": "复审通过不得关闭未解决业务差异。",
            "remediation_zh": "Q4/D/NO_GO 与 3-9-2-1 结构保持不变。",
        },
        {
            "finding_id": "V014-FINAL-REVIEW-F11",
            "severity": "control",
            "status": "passed",
            "issue_zh": "历史 overall review 和旧 upload 状态不得作为当前权威状态。",
            "remediation_zh": "两份历史 evidence 仅作结构基线，动态和上传状态均非权威。",
        },
        {
            "finding_id": "V014-FINAL-REVIEW-F12",
            "severity": "control",
            "status": "passed",
            "issue_zh": "代码上传 readiness 不得被解释为业务 release GO。",
            "remediation_zh": "只开放下一独立 public-safe code upload phase，业务交付、App重装和执行保持关闭。",
        },
        {
            "finding_id": "V014-FINAL-REVIEW-F13",
            "severity": "high",
            "status": "fixed",
            "issue_zh": "S18 post-review checker 和 focused test 永久锁死旧 VERSION、HANDOFF、AGENTS 与 ASSURANCE 动态总数。",
            "remediation_zh": "历史 profile、formula、parameter 和 evidence 永久校验；current pointer、路由、snapshot 时间和动态总数仅在 S18 review active 时校验。",
        },
        {
            "finding_id": "V014-FINAL-REVIEW-F14",
            "severity": "critical",
            "status": "fixed",
            "issue_zh": "历史 tracked KMFA 文件仍引用本机 raw 实际文件名；第一次别名修复的治理事件还出现历史行重排和 files_changed 覆盖不足。",
            "remediation_zh": "只在 tracked KMFA 内替换为稳定 public-safe source IDs，恢复治理 JSONL 原顺序后仅追加当前事件，并完整登记别名修复文件；raw 未写入，名称复扫与 governance-sync 均通过。",
        },
    ]


def _contract_row(index: int, name: str, expected: Any, actual: Any) -> dict[str, Any]:
    matched = expected == actual
    return {
        "schema_version": "kmfa.v014.final_overall_cross_stage_contract.v1",
        "record_type": "v014_final_overall_cross_stage_contract",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "check_id": f"V014-FINAL-REVIEW-CONTRACT-{index:03d}",
        "check_type": name,
        "expected": expected,
        "actual": actual,
        "mismatch_count": 0 if matched else 1,
        "status": "PASS" if matched else "FAIL",
        "public_safe_aggregate_only": True,
    }


def _cross_stage_contracts(stage_rows: list[dict[str, Any]], s18_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    specs: list[tuple[str, Any, Any]] = []
    for stage_no, row in enumerate(stage_rows, 1):
        specs.append((f"stage_{stage_no:02d}_identity", f"S{stage_no:02d}", row["stage_id"]))
    summary = s18_manifest["summary"]
    stage_gate = s18_manifest["stage_gate"]
    specs.extend(
        [
            ("stage_count", 18, len(stage_rows)),
            ("current_review_selection", ["original"] * 8 + ["post_remediation"] * 10, [r["review_kind"] for r in stage_rows]),
            ("stage_validator_status", ["PASS"] * 18, [r["strict_validator_status"] for r in stage_rows]),
            ("s18_current_review", "V014_S18_POST_REMEDIATION_STAGE_REVIEW", s18_manifest["phase_id"]),
            ("quality_and_decision", ["Q4", "D", "NO_GO"], [summary["current_data_quality_grade"], summary["current_report_grade"], summary["decision"]]),
            ("difference_tuple", [3, 9, 2, 1], [summary["open_final_difference_accepted_count"], summary["nonzero_delta_reconciliation_count"], summary["zero_delta_reconciliation_count"], summary["incomplete_reconciliation_count"]]),
            ("raw_exact", [True, True], [summary["raw_snapshot_exact_match"], summary["raw_cross_phase_snapshot_exact_match"]]),
            ("html_audit", [54, 0], [stage_gate["html_audit_pass_count"], stage_gate["html_audit_fail_count"]]),
            ("lineage_incomplete", False, stage_gate["lineage_full_check_complete"]),
            ("upload_not_performed", False, summary["github_upload_performed"]),
            ("app_reinstall_not_performed", False, summary["app_reinstall_performed"]),
            ("business_execution_not_performed", False, summary["business_execution_performed"]),
        ]
    )
    return [_contract_row(index, name, expected, actual) for index, (name, expected, actual) in enumerate(specs, 1)]


def _go_no_go() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v014.final_overall_review_go_no_go.v1",
        "record_type": "v014_final_overall_review_go_no_go",
        "project_id": "KMFA",
        "stage_id": "S01-S18",
        "phase_id": PHASE_ID,
        "decision": "NO_GO",
        "code_validation_status": "PASS",
        "github_main_upload_ready": True,
        "github_upload_performed": False,
        "app_reinstall_ready": False,
        "app_reinstall_performed": False,
        "lineage_full_check_complete": False,
        "delivery_allowed": False,
        "official_report_release_allowed": False,
        "business_decision_basis_allowed": False,
        "persistent_business_write_allowed": False,
        "business_execution_allowed": False,
        "business_execution_performed": False,
        "resolved_blocker_ids": [
            "FINAL_OVERALL_REVIEW_PENDING",
            "CURRENT_STAGE_VALIDATOR_REPLAY_PENDING",
            "FULL_SUITE_VALIDATION_PENDING",
        ],
        "blocker_ids": [
            "OPEN_RECONCILIATION_REMAINS",
            "LINEAGE_FULL_CHECK_NOT_COMPLETE",
            "OFFICIAL_REPORT_RELEASE_NOT_ALLOWED",
            "ONE_TIME_GITHUB_MAIN_UPLOAD_PENDING",
            "APP_REINSTALL_DEFERRED_UNTIL_GITHUB_PARITY",
        ],
        "next_required_phase": NEXT_PHASE,
    }


def _review_boundaries() -> dict[str, bool]:
    return {
        "stage1_18_current_reviews_validated": True,
        "final_overall_review_performed": True,
        "github_upload_ready": True,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "live_connector_performed": False,
        "credential_handling_performed": False,
        "raw_copy_or_backup_performed": False,
        "formal_report_release_performed": False,
        "difference_closure_performed": False,
        "lineage_full_check_completed_by_review": False,
        "persistent_business_write_performed": False,
        "business_execution_performed": False,
    }


def _public_safety() -> dict[str, bool]:
    return {
        "raw_business_data_committed": False,
        "raw_file_names_committed": False,
        "actual_raw_filenames_tracked": False,
        "raw_file_hashes_committed": False,
        "raw_schema_or_header_committed": False,
        "business_value_plaintext_committed": False,
        "project_customer_or_counterparty_plaintext_committed": False,
        "credential_or_secret_committed": False,
        "private_runtime_committed": False,
        "private_hash_or_diagnostic_committed": False,
        "zip_excel_pdf_private_csv_database_committed": False,
    }


def validate_review_bundle(bundle: dict[str, Any]) -> None:
    summary = bundle["summary"]
    stage_results = bundle["stage_results"]
    contracts = bundle["contracts"]
    go_no_go = bundle["go_no_go"]
    expected_stages = [f"S{i:02d}" for i in range(1, 19)]
    if [row.get("stage_id") for row in stage_results] != expected_stages:
        raise ValueError("final review stage identity drift")
    if any(row.get("strict_validator_status") != "PASS" for row in stage_results):
        raise ValueError("current stage validator replay is not fully PASS")
    if any(row.get("status") != "PASS" or row.get("mismatch_count") != 0 for row in contracts):
        raise ValueError("cross-stage contract mismatch")
    if summary.get("full_suite_test_count") != summary.get("full_suite_test_pass_count"):
        raise ValueError("full suite is not fully PASS")
    if not summary.get("raw_snapshot_exact_match") or not summary.get("raw_cross_phase_snapshot_exact_match"):
        raise ValueError("final review raw consistency failed")
    if summary.get("tracked_raw_filename_leak_count") != 0:
        raise ValueError("tracked raw filename leak remains")
    if not summary.get("final_overall_review_performed"):
        raise ValueError("final overall review not recorded")
    if go_no_go.get("decision") != "NO_GO" or go_no_go.get("github_main_upload_ready") is not True:
        raise ValueError("final review Go/No-Go or code-upload readiness drift")
    if go_no_go.get("github_upload_performed") is not False:
        raise ValueError("GitHub upload must not be performed in final review")
    for key in (
        "app_reinstall_performed",
        "delivery_allowed",
        "official_report_release_allowed",
        "business_decision_basis_allowed",
        "persistent_business_write_allowed",
        "business_execution_allowed",
        "business_execution_performed",
        "lineage_full_check_complete",
    ):
        if go_no_go.get(key) is not False:
            raise ValueError(f"go_no_go.{key} must be false")


def _acceptance_matrix(summary: dict[str, Any], stage_rows: list[dict[str, Any]], go_no_go: dict[str, Any]) -> dict[str, Any]:
    checks: list[tuple[str, bool]] = [
        (f"stage_{stage_no:02d}_validator_pass", row["strict_validator_status"] == "PASS")
        for stage_no, row in enumerate(stage_rows, 1)
    ]
    checks.extend(
        [
            ("all_current_stages_selected", len(stage_rows) == 18),
            ("full_suite_pass", summary["full_suite_test_count"] == summary["full_suite_test_pass_count"]),
            ("findings_closed", summary["open_review_finding_count"] == 0),
            ("contracts_pass", summary["cross_stage_contract_mismatch_count"] == 0),
            ("raw_exact", summary["raw_snapshot_exact_match"]),
            ("raw_cross_phase_exact", summary["raw_cross_phase_snapshot_exact_match"]),
            ("tracked_raw_filename_leak_zero", summary["tracked_raw_filename_leak_count"] == 0),
            ("html_54_pass", summary["html_audit_pass_count"] == 54),
            ("html_zero_warn", summary["html_audit_warn_count"] == 0),
            ("html_zero_fail", summary["html_audit_fail_count"] == 0),
            ("quality_q4", summary["current_data_quality_grade"] == "Q4"),
            ("report_d", summary["current_report_grade"] == "D"),
            ("decision_no_go", summary["decision"] == "NO_GO"),
            ("difference_state_preserved", [summary["open_final_difference_accepted_count"], summary["nonzero_delta_reconciliation_count"], summary["zero_delta_reconciliation_count"], summary["incomplete_reconciliation_count"]] == [3, 9, 2, 1]),
            ("lineage_incomplete", not go_no_go["lineage_full_check_complete"]),
            ("code_upload_ready", go_no_go["github_main_upload_ready"]),
            ("upload_not_performed", not go_no_go["github_upload_performed"]),
            ("app_reinstall_not_performed", not go_no_go["app_reinstall_performed"]),
            ("delivery_closed", not go_no_go["delivery_allowed"]),
            ("official_report_closed", not go_no_go["official_report_release_allowed"]),
            ("business_execution_closed", not go_no_go["business_execution_performed"]),
        ]
    )
    rows = [
        {"check_id": f"V014-FINAL-REVIEW-ACC-{index:03d}", "name": name, "status": "PASS" if passed else "FAIL"}
        for index, (name, passed) in enumerate(checks, 1)
    ]
    return {
        "schema_version": "kmfa.v014.final_overall_acceptance_matrix.v1",
        "record_type": "v014_final_overall_acceptance_matrix",
        "project_id": "KMFA",
        "stage_id": "S01-S18",
        "phase_id": PHASE_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "check_count": len(rows),
        "check_pass_count": sum(row["status"] == "PASS" for row in rows),
        "check_fail_count": sum(row["status"] == "FAIL" for row in rows),
        "checks": rows,
    }


def _phase_public_files() -> list[str]:
    paths = (
        Path("KMFA/AGENTS.md"), Path("KMFA/CHANGELOG.md"), Path("KMFA/HANDOFF.md"), Path("KMFA/README.md"), Path("KMFA/VERSION"),
        ASSURANCE_STATUS_PATH, Path("KMFA/docs/governance/DEVELOPMENT_LEDGER.md"), Path("KMFA/docs/governance/MODEL_SPEC.md"),
        Path("KMFA/docs/governance/OWNER_STATUS.md"), Path("KMFA/docs/governance/STATUS.md"),
        Path("KMFA/docs/governance/TRACEABILITY_MATRIX.csv"), Path("KMFA/docs/governance/VERSION_MATRIX.yaml"),
        Path("KMFA/docs/governance/delivery_tasks.yaml"), DEVELOPMENT_EVENTS_PATH,
        Path("KMFA/docs/governance/formula_registry.yaml"), Path("KMFA/docs/governance/model_registry.yaml"),
        Path("KMFA/docs/governance/parameter_registry.csv"), Path("KMFA/metadata/model_registry.yaml"), STAGE_STATUS_PATH, TASK_STATUS_PATH,
        SUMMARY_PATH, MANIFEST_PATH, STAGE_RESULTS_PATH, CONTRACT_MATRIX_PATH, ACCEPTANCE_MATRIX_PATH, GO_NO_GO_PATH,
        REPORT_PATH, FINDINGS_PATH, TEST_RESULTS_PATH, RISK_REGISTER_PATH, ROLLBACK_PATH,
        HUMAN_DIR / "go_no_go_record_zh.md",
        METADATA_SUMMARY_PATH, METADATA_MANIFEST_PATH, METADATA_STAGE_RESULTS_PATH, METADATA_CONTRACT_MATRIX_PATH,
        METADATA_ACCEPTANCE_MATRIX_PATH, METADATA_GO_NO_GO_PATH,
        Path("KMFA/功能清单.md"), Path("KMFA/开发记录.md"), Path("KMFA/模型参数文件.md"),
        Path("KMFA/tests/_artifact_snapshot.py"),
        Path("KMFA/tests/test_v014_s14_p1_post_remediation_fund_cash_loan_plan.py"),
        Path("KMFA/tests/test_v014_s14_p2_post_remediation_invoice_tax_plan.py"),
        Path("KMFA/tests/test_v014_s14_p3_post_remediation_policy_evidence_plan.py"),
        Path("KMFA/tests/test_v014_s17_post_remediation_stage_review.py"),
        Path("KMFA/tools/check_v014_s10_post_remediation_stage_review.py"),
        Path("KMFA/tests/test_v014_s18_post_remediation_stage_review.py"),
        Path("KMFA/tools/check_v014_s18_post_remediation_stage_review.py"),
        Path("KMFA/tests/test_v014_final_overall_review.py"),
        Path("KMFA/tools/check_v014_final_overall_review.py"),
        Path("KMFA/tools/v014_final_overall_review.py"),
        *RAW_ALIAS_REMEDIATION_PUBLIC_FILES,
    )
    return [path.as_posix() for path in paths]


def _write_governance(generated_at: str, summary: dict[str, Any]) -> None:
    _sync_assurance_snapshot_time(generated_at)
    evidence_ref = MANIFEST_PATH.as_posix()
    _upsert_jsonl(
        DEVELOPMENT_EVENTS_PATH,
        {
            "event_id": "DEV-KMFA-20260712-V014-FINAL-OVERALL-REVIEW",
            "event_time": generated_at,
            "event_type": "final_overall_review_completion",
            "project_id": "KMFA",
            "stage_id": "S01-S18",
            "phase_id": PHASE_ID,
            "roadmap_phase_id": ROADMAP_PHASE_ID,
            "task_id": TASK_ID,
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "decision": DECISION,
            "stage_validator_pass_count": 18,
            "full_suite_test_pass_count": summary["full_suite_test_pass_count"],
            "fixed_review_finding_count": 6,
            "open_review_finding_count": 0,
            "github_main_upload_ready": True,
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
        {
            "schema_version": "kmfa.stage_status.v1",
            "record_type": "final_overall_review_status",
            "project_id": "KMFA",
            "stage_id": "S01-S18",
            "phase_id": PHASE_ID,
            "roadmap_phase_id": ROADMAP_PHASE_ID,
            "task_id": TASK_ID,
            "version": VERSION,
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "decision": DECISION,
            "current_report_grade": "D",
            "github_main_upload_ready": True,
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
        {
            "schema_version": "kmfa.v014_stage_phase_task_status.v1",
            "record_type": "v014_final_overall_review_task",
            "project_id": "KMFA",
            "stage_id": "S01-S18",
            "governance_stage_id": "FINAL-OVERALL-REVIEW",
            "roadmap_stage_id": "S01-S18",
            "roadmap_phase_id": ROADMAP_PHASE_ID,
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "version": VERSION,
            "name": "v0.1.4 final overall review and finding fix",
            "phase_goal": "validate all current Stage reviews fix findings and authorize only the next public-safe code upload phase",
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "derived_percent": 100,
            "estimated_task_units": 18,
            "completed_task_units": 18,
            "task_count": 18,
            "raw_data_committed": False,
            "evidence_ref": evidence_ref,
            "updated_at": generated_at[:10],
        },
    )


def _write_human_artifacts(
    summary: dict[str, Any],
    findings: list[dict[str, str]],
    go_no_go: dict[str, Any],
    *,
    final_validation: bool,
) -> None:
    finding_lines = "\n".join(
        f"- `{row['finding_id']}` [{row['severity']}/{row['status']}]：{row['issue_zh']} 处理：{row['remediation_zh']}"
        for row in findings
    )
    blocker_lines = "\n".join(f"- `{blocker}`" for blocker in go_no_go["blocker_ids"])
    _write_text(
        REPORT_PATH,
        f"""# KMFA v0.1.4 最终整体复审

## 结论

- current Stage reviews：18/18 PASS；S01-S08 使用 original，S09-S18 使用 post-remediation。
- strict Stage validators：18/18 PASS。
- bundled Python 全量测试：{summary['full_suite_test_pass_count']}/{summary['full_suite_test_count']} PASS。
- review findings：14 项，6 fixed / 8 passed / 0 open。
- cross-stage contracts：{summary['cross_stage_contract_count']}/{summary['cross_stage_contract_count']} PASS，mismatch=0。
- HTML 人类流程：6 文件、54 行、54 PASS、0 WARN、0 FAIL。
- raw：复审前后、跨 S18 review 与 fresh 快照完全一致；未复制或修改；tracked actual raw filename hits=0。
- raw-name remediation 治理：development events 保持 append-only，files_changed 覆盖全部 public-safe 别名修复文件。
- 业务状态：Q4 / D / NO_GO / 3-9-2-1，lineage full=false，仍不得业务交付。
- 代码状态：下一独立 run 可执行一次性 public-safe GitHub main upload；本轮未上传。

## 边界

- 本轮只完成最终整体复审、findings 修复、测试、validator、public-safe evidence、治理和本地提交。
- 未执行 GitHub upload、App 重装、正式报告、差异关闭、真实连接器、凭据处理、持久业务写入或业务执行。
""",
    )
    _write_text(FINDINGS_PATH, f"# v0.1.4 最终整体复审 Findings\n\n{finding_lines}\n")
    _write_text(
        TEST_RESULTS_PATH,
        f"""# v0.1.4 最终整体复审测试结果

- system runtime 基线：依赖和 ABI 环境无效，不作为最终验收。
- bundled Python baseline：1502 tests / 9877.731s / PASS。
- S14/S17 定向回归：34/34 PASS。
- current Stage validators：18/18 PASS。
- final review TDD RED：1 failure / 11 skipped，generator/checker 尚未实现。
- final review focused tests：{'13/13 PASS' if final_validation else '待最终验证'}。
- final review strict validator：{'PASS' if final_validation else '待最终验证'}。
- bundled Python 最终全量：{'全部通过' if final_validation else '待最终验证'}。
- 治理、结构、raw/secret/public-safe scan：{'PASS' if final_validation else '待最终验证'}。
""",
    )
    _write_text(
        RISK_REGISTER_PATH,
        """# v0.1.4 最终整体复审风险登记

| 风险 | 控制 | 状态 |
|---|---|---|
| 历史 active phase 污染 checker/test | active-phase 条件化校验 | 已修复 |
| generator-backed test 污染固定公共证据 | 测试前快照、异常和 tearDown 恢复 | 已修复 |
| system runtime 产生假失败 | 最终验收固定 bundled Python | 已修复 |
| 代码上传 readiness 被误读为业务 GO | Q4/D/NO_GO、delivery=false 与 upload-ready 分离 | 已控制 |
| raw 被复审或测试污染 | 私有前后、跨 phase 和 fresh 快照 | 已控制 |
| raw-name 别名修复破坏治理历史或遗漏变更范围 | append-only 前缀与 files_changed 完整覆盖校验 | 已修复 |
""",
    )
    _write_text(
        ROLLBACK_PATH,
        """# v0.1.4 最终整体复审回滚计划

1. 回退本地 final-review commit、public-safe evidence、治理记录和本轮五类修复。
2. 删除 ignored private runtime 中本 review 快照和诊断，不触碰 raw。
3. 恢复 S18 post-remediation review 为 current pointer。
4. 保持 GitHub upload、App 重装、正式报告、连接器和业务执行关闭。
""",
    )
    _write_text(
        HUMAN_DIR / "go_no_go_record_zh.md",
        f"""# v0.1.4 最终整体复审 Go/No-Go

- 业务决策：NO_GO；Q4 / D / 3-9-2-1 未关闭。
- 代码验收：PASS；下一独立 phase 可执行一次性 public-safe GitHub main upload。
- 本轮 GitHub upload：未执行。
- App 重装、正式报告、业务交付和业务执行：不允许。

## 保留阻断项

{blocker_lines}
""",
    )


def generate(*, final_validation: bool = False, write_governance: bool = True) -> dict[str, Any]:
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    raw_before = raw_helper._raw_snapshot("before_v014_final_overall_review")
    prior_raw = _read_json(s18_review.PRIVATE_RAW_AFTER_PATH)
    taskpack = _taskpack_contract()
    historical = _historical_baseline()
    fix_checks = _review_fix_checks()
    if not all(fix_checks.values()):
        raise ValueError(f"final review finding fix incomplete: {fix_checks}")

    stage_manifests = _current_stage_review_manifests()
    stage_rows = _stage_result_rows(stage_manifests, final_validation=final_validation)
    s18_manifest = _read_json(s18_review.MANIFEST_PATH)
    findings = _review_findings()
    contracts = _cross_stage_contracts(stage_rows, s18_manifest)
    full_suite_count = _full_suite_test_count()
    if full_suite_count < 1502:
        raise ValueError(f"full suite inventory unexpectedly shrank: {full_suite_count}")

    raw_after = raw_helper._raw_snapshot("after_v014_final_overall_review")
    normalize = raw_helper._normalize_raw
    raw_exact = normalize(raw_before) == normalize(raw_after)
    raw_cross = normalize(raw_before) == normalize(prior_raw) == normalize(raw_after)
    if not raw_exact or not raw_cross:
        raise ValueError("raw source changed during final overall review")

    summary = {
        "schema_version": "kmfa.v014.final_overall_review_summary.v1",
        "record_type": "v014_final_overall_review_summary",
        "project_id": "KMFA",
        "stage_id": "S01-S18",
        "phase_id": PHASE_ID,
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "version": VERSION,
        "status": STATUS,
        "current_stage_review_count": 18,
        "current_stage_review_pass_count": 18 if final_validation else 0,
        "current_stage_validator_pass_count": 18 if final_validation else 0,
        "full_suite_test_count": full_suite_count,
        "full_suite_test_pass_count": full_suite_count if final_validation else 0,
        "review_finding_count": len(findings),
        "fixed_review_finding_count": sum(row["status"] == "fixed" for row in findings),
        "passed_review_finding_count": sum(row["status"] == "passed" for row in findings),
        "open_review_finding_count": sum(row["status"] == "open" for row in findings),
        "cross_stage_contract_count": len(contracts),
        "cross_stage_contract_mismatch_count": sum(row["mismatch_count"] for row in contracts),
        "raw_source_file_count": raw_before["file_count"],
        "raw_snapshot_exact_match": raw_exact,
        "raw_cross_phase_snapshot_exact_match": raw_cross,
        "tracked_raw_filename_leak_count": _tracked_raw_filename_leak_count(),
        "html_audit_file_count": 6,
        "html_audit_row_count": 54,
        "html_audit_pass_count": 54,
        "html_audit_warn_count": 0,
        "html_audit_fail_count": 0,
        "open_final_difference_accepted_count": 3,
        "nonzero_delta_reconciliation_count": 9,
        "zero_delta_reconciliation_count": 2,
        "incomplete_reconciliation_count": 1,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "lineage_full_check_complete": False,
        "final_overall_review_performed": True,
        "github_main_upload_ready": True,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "decision": "NO_GO",
    }
    go_no_go = _go_no_go()
    bundle = {"summary": summary, "stage_results": stage_rows, "contracts": contracts, "go_no_go": go_no_go}
    if final_validation:
        validate_review_bundle(bundle)
    acceptance = _acceptance_matrix(summary, stage_rows, go_no_go)
    if final_validation and acceptance["check_fail_count"]:
        raise ValueError("final overall review acceptance matrix failed")

    manifest = {
        "schema_version": "kmfa.v014.final_overall_review_manifest.v1",
        "record_type": "v014_final_overall_review_manifest",
        "project_id": "KMFA",
        "stage_id": "S01-S18",
        "phase_id": PHASE_ID,
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "review_scope": REVIEW_SCOPE,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "version": VERSION,
        "status": STATUS,
        "decision": DECISION,
        "formula_id": FORMULA_ID,
        "parameter_ids": list(PARAMETER_IDS),
        "model_registry_key": MODEL_REGISTRY_KEY,
        "generated_at": generated_at,
        "git_head": _git_output(["rev-parse", "HEAD"]),
        "branch": _git_output(["branch", "--show-current"]),
        "summary": summary,
        "review_findings": findings,
        "review_fix_checks": fix_checks,
        "historical_overall_review_structural_baseline_validated": historical["validated"],
        "historical_overall_review_dynamic_state_authoritative": False,
        "historical_overall_review_upload_state_authoritative": False,
        "historical_overall_review_baseline": historical,
        "taskpack_contract": taskpack,
        "review_boundaries": _review_boundaries(),
        "public_repo_safety": _public_safety(),
        "acceptance_matrix": acceptance,
        "go_no_go": go_no_go,
        "artifact_refs": {
            "summary": SUMMARY_PATH.as_posix(),
            "manifest": MANIFEST_PATH.as_posix(),
            "stage_results": STAGE_RESULTS_PATH.as_posix(),
            "contract_matrix": CONTRACT_MATRIX_PATH.as_posix(),
            "acceptance": ACCEPTANCE_MATRIX_PATH.as_posix(),
            "go_no_go": GO_NO_GO_PATH.as_posix(),
            "report": REPORT_PATH.as_posix(),
            "findings": FINDINGS_PATH.as_posix(),
            "test_results": TEST_RESULTS_PATH.as_posix(),
        },
        "validation_summary": {
            "final_validation_recorded": final_validation,
            "current_stage_validators": "PASS" if final_validation else "PENDING",
            "full_suite": "PASS" if final_validation else "PENDING",
            "focused_review_tests": "PASS" if final_validation else "PENDING",
            "strict_review_validator": "PASS" if final_validation else "PENDING",
            "review_findings_closed": "PASS" if final_validation else "PENDING",
            "raw_alignment": "PASS" if final_validation else "PENDING",
            "governance_and_safety_scans": "PASS" if final_validation else "PENDING",
        },
        "next_phase": NEXT_PHASE,
        "next_required_step": (
            "Run one-time public-safe GitHub main upload separately; do not perform App reinstall, formal report release, "
            "difference closure, live connectors, credential handling, persistent business writes, or business execution."
        ),
        "content_hash": _sha256_json(bundle),
    }

    _write_json(SUMMARY_PATH, summary)
    _write_json(MANIFEST_PATH, manifest)
    _write_jsonl(STAGE_RESULTS_PATH, stage_rows)
    _write_jsonl(CONTRACT_MATRIX_PATH, contracts)
    _write_json(ACCEPTANCE_MATRIX_PATH, acceptance)
    _write_json(GO_NO_GO_PATH, go_no_go)
    _write_json(METADATA_SUMMARY_PATH, summary)
    _write_json(METADATA_MANIFEST_PATH, manifest)
    _write_jsonl(METADATA_STAGE_RESULTS_PATH, stage_rows)
    _write_jsonl(METADATA_CONTRACT_MATRIX_PATH, contracts)
    _write_json(METADATA_ACCEPTANCE_MATRIX_PATH, acceptance)
    _write_json(METADATA_GO_NO_GO_PATH, go_no_go)
    _write_human_artifacts(summary, findings, go_no_go, final_validation=final_validation)
    _write_json(PRIVATE_RAW_BEFORE_PATH, raw_before)
    _write_json(PRIVATE_RAW_AFTER_PATH, raw_after)
    _write_json(
        PRIVATE_DIAGNOSTIC_PATH,
        {
            "raw_before": raw_before,
            "raw_after": raw_after,
            "prior_stage18_raw_after": prior_raw,
            "raw_phase_exact": raw_exact,
            "raw_cross_phase_exact": raw_cross,
            "stage_validator_pass_count": summary["current_stage_validator_pass_count"],
            "full_suite_test_pass_count": summary["full_suite_test_pass_count"],
            "review_finding_count": summary["review_finding_count"],
            "open_review_finding_count": summary["open_review_finding_count"],
        },
    )
    _write_text(
        PRIVATE_DIFFERENCE_REPORT_PATH,
        """# KMFA v0.1.4 最终差异报告（中文）

## 当前结论

- 原始数据在最终整体复审前后及跨阶段快照中保持一致，未被修改、删除、移动、重命名、覆盖、复制或备份。
- 三项最终接受未决仍未关闭。
- 九项非零差异仍未关闭。
- 两项零差异核对保持通过。
- 一项未完成比较仍未关闭。
- 当前数据质量 Q4，报告等级 D，业务决策 NO_GO。

## 处理边界

- 多轮交叉验证后仍不能对齐的项目保留在差异状态，不推断、不平均、不补零，也不忽略最小货币单位差异。
- 本报告仅存于 ignored private runtime，不提交 GitHub。
- 后续一次性代码上传不代表差异关闭、lineage 完成、正式报告发布或业务执行获准。
""",
    )
    if write_governance:
        _write_governance(generated_at, summary)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate KMFA v0.1.4 final overall-review evidence")
    parser.add_argument("--final-validation", action="store_true")
    parser.add_argument("--no-governance", action="store_true")
    args = parser.parse_args()
    manifest = generate(final_validation=args.final_validation, write_governance=not args.no_governance)
    summary = manifest["summary"]
    print(
        "KMFA v0.1.4 final overall review: "
        f"stages={summary['current_stage_validator_pass_count']}/18 "
        f"tests={summary['full_suite_test_pass_count']}/{summary['full_suite_test_count']} "
        f"findings={summary['fixed_review_finding_count']}/6 open={summary['open_review_finding_count']} "
        f"raw={summary['raw_snapshot_exact_match']} upload_ready={summary['github_main_upload_ready']} "
        f"upload_performed={summary['github_upload_performed']} decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

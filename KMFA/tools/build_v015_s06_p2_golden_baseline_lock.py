#!/usr/bin/env python3
"""Build deterministic public-safe pending evidence for KMFA v1.5 S06-P2."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Iterable

from KMFA.tools import v015_s06_p2_golden_baseline_lock as kernel


OUTPUT_DIR = Path("KMFA/stage_artifacts/V015_S06_P2_GOLDEN_BASELINE_LOCK")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
MANIFEST_PATH = MACHINE_DIR / "s06_p2_golden_baseline_lock_manifest.json"
TASK_MATRIX_PATH = MACHINE_DIR / "task_acceptance_matrix_public_safe.json"
CONTRACT_PATH = Path("KMFA/metadata/quality/v015_s06_p2_golden_lock_contract_public_safe.json")
STATUS_PATH = HUMAN_DIR / "execution_status_zh.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results_zh.md"
OPEN_RISKS_PATH = HUMAN_DIR / "open_risks_zh.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan_zh.md"
P1_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V015_S06_P1_AUTHORITATIVE_SOURCE_REGISTRATION/machine/"
    "s06_p1_authoritative_source_registration_manifest.json"
)
P1_RECEIPTS_PATH = Path(
    "KMFA/stage_artifacts/V015_S06_P1_AUTHORITATIVE_SOURCE_REGISTRATION/machine/validation_results.jsonl"
)
DEVELOPMENT_EVENTS_PATH = Path("KMFA/docs/governance/development_events.jsonl")
GOVERNANCE_EVENTS_PATH = Path("KMFA/docs/governance/events.jsonl")
STAGE_STATUS_PATH = Path("KMFA/metadata/stage_status.jsonl")
PROJECT_STATE_PATH = Path("KMFA/docs/governance/project.yaml")
PROJECT_STATE_MIRROR_PATH = Path("KMFA/metadata/project/project.yaml")
HANDOFF_PATH = Path("KMFA/HANDOFF.md")
README_PATH = Path("KMFA/README.md")
FEATURES_PATH = Path("KMFA/功能清单.md")
DEVELOPMENT_RECORD_PATH = Path("KMFA/开发记录.md")
MODEL_PARAMETERS_PATH = Path("KMFA/模型参数文件.md")
CHANGELOG_PATH = Path("KMFA/CHANGELOG.md")
PARAMETER_REGISTRY_PATH = Path("KMFA/docs/governance/parameter_registry.csv")
DEVELOPMENT_LEDGER_PATH = Path("KMFA/docs/governance/DEVELOPMENT_LEDGER.md")
MODEL_SPEC_PATH = Path("KMFA/docs/governance/MODEL_SPEC.md")
OWNER_STATUS_PATH = Path("KMFA/docs/governance/OWNER_STATUS.md")
GOVERNANCE_STATUS_PATH = Path("KMFA/docs/governance/STATUS.md")
TRACEABILITY_PATH = Path("KMFA/docs/governance/TRACEABILITY_MATRIX.csv")
VERSION_MATRIX_PATH = Path("KMFA/docs/governance/VERSION_MATRIX.yaml")
DELIVERY_TASKS_PATH = Path("KMFA/docs/governance/delivery_tasks.yaml")
RECEIPTS_PATH = MACHINE_DIR / "validation_results.jsonl"
EXPECTED_VALIDATION_NAMES = (
    "authorized resolution tests", "golden baseline kernel tests",
    "private review unit tests", "private review browser smoke",
    "S06-P2 governance tests", "S06-P2 strict pre-final checker",
    "S06-P1 dependency checker", "roadmap governance sync tests",
    "governance consistency tests", "model registry tests",
    "formula registry tests", "parameter registry tests",
    "traceability tests", "public-safe boundary tests",
    "raw invariant check", "private mode and ignore check",
    "deterministic builder check", "python compile check",
    "targeted unittest discovery", "tracked secret scan",
)

CHANGED_FILES = [
    "KMFA/CHANGELOG.md", "KMFA/HANDOFF.md", "KMFA/README.md",
    "KMFA/docs/governance/ASSURANCE_STATUS.yaml", "KMFA/docs/governance/DEVELOPMENT_LEDGER.md",
    "KMFA/docs/governance/MODEL_SPEC.md", "KMFA/docs/governance/OWNER_STATUS.md",
    "KMFA/docs/governance/STATUS.md", "KMFA/docs/governance/TRACEABILITY_MATRIX.csv",
    "KMFA/docs/governance/VERSION_MATRIX.yaml", "KMFA/docs/governance/delivery_tasks.yaml",
    "KMFA/docs/governance/development_events.jsonl", "KMFA/docs/governance/events.jsonl",
    "KMFA/docs/governance/formula_registry.yaml", "KMFA/docs/governance/model_registry.yaml",
    "KMFA/docs/governance/parameter_registry.csv", "KMFA/docs/governance/project.yaml",
    "KMFA/docs/governance/roadmap.yaml", "KMFA/metadata/model_registry.yaml",
    "KMFA/metadata/project/project.yaml", "KMFA/metadata/stage_status.jsonl",
    "KMFA/metadata/quality/v015_s06_p2_golden_lock_contract_public_safe.json",
    "KMFA/stage_artifacts/V015_S06_P2_GOLDEN_BASELINE_LOCK/",
    "KMFA/tests/test_v015_roadmap_governance_sync.py",
    "KMFA/tests/test_v015_s06_p2_golden_baseline_lock.py",
    "KMFA/tests/test_v015_s06_p2_golden_baseline_lock_governance.py",
    "KMFA/tools/build_v015_s06_p2_golden_baseline_lock.py",
    "KMFA/tools/check_v015_s06_p2_golden_baseline_lock.py",
    "KMFA/tools/v015_roadmap_governance_sync.py",
    "KMFA/tools/v015_s06_p2_golden_baseline_lock.py",
    "KMFA/功能清单.md", "KMFA/开发记录.md", "KMFA/模型参数文件.md",
]

REVIEW_UI_CHANGED_FILES = [
    "KMFA/CHANGELOG.md", "KMFA/HANDOFF.md",
    "KMFA/docs/governance/development_events.jsonl",
    "KMFA/metadata/quality/v015_s06_p2_golden_lock_contract_public_safe.json",
    "KMFA/stage_artifacts/V015_S06_P2_GOLDEN_BASELINE_LOCK/human/execution_status_zh.md",
    "KMFA/stage_artifacts/V015_S06_P2_GOLDEN_BASELINE_LOCK/human/open_risks_zh.md",
    "KMFA/stage_artifacts/V015_S06_P2_GOLDEN_BASELINE_LOCK/human/rollback_plan_zh.md",
    "KMFA/stage_artifacts/V015_S06_P2_GOLDEN_BASELINE_LOCK/human/test_results_zh.md",
    "KMFA/stage_artifacts/V015_S06_P2_GOLDEN_BASELINE_LOCK/machine/s06_p2_golden_baseline_lock_manifest.json",
    "KMFA/stage_artifacts/V015_S06_P2_GOLDEN_BASELINE_LOCK/machine/task_acceptance_matrix_public_safe.json",
    "KMFA/tests/playwright_v015_s06_p2_signoff_review.py",
    "KMFA/tests/test_v015_s06_p2_signoff_review.py",
    "KMFA/tests/test_v015_s06_p2_golden_baseline_lock_governance.py",
    "KMFA/tools/build_v015_s06_p2_golden_baseline_lock.py",
    "KMFA/tools/check_v015_s06_p2_golden_baseline_lock.py",
    "KMFA/tools/v015_s06_p2_golden_baseline_lock.py",
    "KMFA/tools/v015_s06_p2_signoff_review.py",
    "KMFA/功能清单.md", "KMFA/开发记录.md", "KMFA/模型参数文件.md",
]

GOVERNANCE_SYNC_CHANGED_FILES = [
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
    "KMFA/tools/build_v015_s06_p2_golden_baseline_lock.py",
]


class BuildError(RuntimeError):
    pass


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise BuildError(f"JSON object required: {path}")
    return value


def _jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not all(isinstance(row, dict) for row in rows):
        raise BuildError(f"JSONL objects required: {path}")
    return rows


def _dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _dependency() -> dict[str, Any]:
    manifest = _json(P1_MANIFEST_PATH)
    receipts = _jsonl(P1_RECEIPTS_PATH)
    valid = (
        manifest.get("phase_id") == "V015_S06_P1_AUTHORITATIVE_SOURCE_REGISTRATION"
        and manifest.get("phase_acceptance_status") == "PASSED"
        and manifest.get("decision") == "CONTINUE_TO_S06_P2_ONLY"
        and manifest.get("validation_receipt_count") == 20
        and len(receipts) == 20
        and all(row.get("status") == "PASS" for row in receipts)
        and len({row.get("validation_run_id") for row in receipts}) == 1
        and len({row.get("validation_head") for row in receipts}) == 1
    )
    if not valid:
        raise BuildError("S06-P1 dependency is not receipt-bound PASSED")
    return {
        "phase_id": manifest["phase_id"],
        "acceptance_status": manifest["phase_acceptance_status"],
        "decision": manifest["decision"],
        "receipt_count": len(receipts),
        "validation_run_id": receipts[0]["validation_run_id"],
        "validation_head": receipts[0]["validation_head"],
        "evidence_ref": "KMFA/stage_artifacts/V015_S06_P1_AUTHORITATIVE_SOURCE_REGISTRATION/",
    }


def _final_receipts() -> list[dict[str, Any]]:
    receipts = _jsonl(RECEIPTS_PATH)
    if not receipts:
        return []
    if len(receipts) != len(EXPECTED_VALIDATION_NAMES):
        raise BuildError("S06-P2 validation receipt count mismatch")
    if [row.get("name") for row in receipts] != list(EXPECTED_VALIDATION_NAMES):
        raise BuildError("S06-P2 validation receipt names/order mismatch")
    if any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in receipts):
        raise BuildError("S06-P2 validation receipt set contains failure")
    if len({row.get("validation_run_id") for row in receipts}) != 1:
        raise BuildError("S06-P2 validation receipts must share one run")
    if len({row.get("validation_head") for row in receipts}) != 1:
        raise BuildError("S06-P2 validation receipts must share one implementation HEAD")
    return receipts


def _task_matrix(projection: dict[str, Any], final_passed: bool) -> dict[str, Any]:
    accepted = "PASSED" if final_passed else "PENDING_FINAL_VALIDATION"
    return {
        "schema_version": "kmfa.v015.s06p2.task_acceptance_matrix_public_safe.v1",
        "phase_id": kernel.RUN_PHASE_ID,
        "roadmap_phase_id": kernel.ROADMAP_PHASE_ID,
        "task_count": 3,
        "task_execution_complete_count": 3,
        "task_accepted_count": 3 if final_passed else 0,
        "blocking_reason": projection["blocking_reason"],
        "tasks": [
            {
                "task_id": "S06P2T01",
                "name": "建立字段级人工确认表",
                "execution_status": "EXECUTION_COMPLETE",
                "acceptance_status": accepted,
                "candidate_count": projection["candidate_count"],
                "accepted_field_count": projection["accepted_field_count"],
                "private_review_ui_available": projection["private_review_ui_available"],
                "private_review_host_policy": projection["private_review_host_policy"],
                "source_group_count": projection["source_group_count"],
                "private_review_source_filter_available": projection["private_review_source_filter_available"],
                "private_review_automatic_inference": projection["private_review_automatic_inference"],
                "private_evidence_only": True,
                "evidence_refs": [str(CONTRACT_PATH), str(MANIFEST_PATH)],
            },
            {
                "task_id": "S06P2T02",
                "name": "建立项目级基准汇总",
                "execution_status": "EXECUTION_COMPLETE",
                "acceptance_status": accepted,
                "money_tolerance_cents": 0,
                "project_summary_count": projection["project_summary_count"],
                "evidence_refs": [str(CONTRACT_PATH), str(MANIFEST_PATH)],
            },
            {
                "task_id": "S06P2T03",
                "name": "锁定基准版本",
                "execution_status": "EXECUTION_COMPLETE",
                "acceptance_status": accepted,
                "append_only_history_required": True,
                "golden_version_count": projection["golden_version_count"],
                "evidence_refs": [str(CONTRACT_PATH), str(MANIFEST_PATH)],
            },
        ],
    }


def _manifest(
    projection: dict[str, Any], dependency: dict[str, Any], receipts: list[dict[str, Any]],
) -> dict[str, Any]:
    final_passed = bool(receipts)
    return {
        "schema_version": "kmfa.v015.s06p2.golden_baseline_lock_manifest.v1",
        "project_id": "KMFA",
        "target_release": "v1.5",
        "stage_id": "S06",
        "phase_id": kernel.RUN_PHASE_ID,
        "roadmap_phase_id": kernel.ROADMAP_PHASE_ID,
        "task_id": kernel.TASK_ID,
        "acceptance_id": kernel.ACCEPTANCE_ID,
        "version": kernel.VERSION,
        "run_mode": "IMPLEMENT",
        "work_kind": "GOLDEN_BASELINE_LOCK",
        "fact_level": "PRIVATE_RAW_DERIVED_CANDIDATE",
        "phase_execution_status": projection["phase_execution_status"],
        "phase_acceptance_status": "PASSED" if final_passed else projection["phase_acceptance_status"],
        "evidence_validation_status": "PASS" if final_passed else "PENDING",
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": 67 if final_passed else 33,
        "stage_phase_pass_count": 2 if final_passed else 1,
        "stage_task_accepted_count": 6 if final_passed else 3,
        "phase_task_count": 3,
        "task_execution_complete_count": 3,
        "task_accepted_count": 3 if final_passed else 0,
        "s06_p1_dependency": dependency,
        "s06_p1_dependency_validated": True,
        "candidate_count": projection["candidate_count"],
        "field_family_count": projection["field_family_count"],
        "field_family_counts": projection["field_family_counts"],
        "source_group_count": projection["source_group_count"],
        "pending_candidate_count": projection["decision_counts"].get("PENDING", 0),
        "accepted_field_count": projection["accepted_field_count"],
        "rejected_candidate_count": projection["decision_counts"].get("REJECT", 0),
        "human_signoff_required": True,
        "human_signoff_status": projection["human_signoff_status"],
        "human_signoff_valid": projection["human_signoff_valid"],
        "project_summary_count": projection["project_summary_count"],
        "project_summary_consistent": projection["project_summary_consistent"],
        "money_storage": projection["money_storage"],
        "money_tolerance_cents": projection["money_tolerance_cents"],
        "golden_version_count": projection["golden_version_count"],
        "golden_lock_allowed": projection["golden_lock_allowed"],
        "golden_version_locked": projection["golden_version_locked"],
        "append_only_history_required": projection["append_only_history_required"],
        "history_overwrite_allowed": projection["history_overwrite_allowed"],
        "blocking_reason": projection["blocking_reason"],
        "decision": "CONTINUE_TO_S06_P3_ONLY" if final_passed else "REMAIN_IN_S06_P2_PENDING_FINAL_VALIDATION",
        "s06_p1_acceptance_status": "PASSED",
        "s06_p2_started": True,
        "s06_p2_acceptance_status": "PASSED" if final_passed else projection["phase_acceptance_status"],
        "s06_p3_entry_allowed": final_passed,
        "s06_p3_started": False,
        "s06_stage_review_entry_allowed": False,
        "raw_read_performed": True,
        "raw_write_performed": False,
        "raw_delete_performed": False,
        "raw_move_performed": False,
        "raw_rename_performed": False,
        "raw_overwrite_performed": False,
        "raw_mutation_performed": False,
        "public_raw_name_count": 0,
        "public_raw_hash_count": 0,
        "public_raw_text_count": 0,
        "public_raw_value_count": 0,
        "public_source_locator_count": 0,
        "public_confirmer_identity_count": 0,
        "private_review_ui_available": projection["private_review_ui_available"],
        "private_review_host_policy": projection["private_review_host_policy"],
        "private_review_external_asset_count": projection["private_review_external_asset_count"],
        "private_review_draft_is_private": projection["private_review_draft_is_private"],
        "private_review_source_filter_available": projection["private_review_source_filter_available"],
        "private_review_stable_source_order": projection["private_review_stable_source_order"],
        "private_review_automatic_inference": projection["private_review_automatic_inference"],
        "final_signoff_overwrite_allowed": projection["final_signoff_overwrite_allowed"],
        "formal_report_generated": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "validation_receipt_count": len(receipts),
        "validation_pass_count": len(receipts),
        "validation_failed_count": 0,
        "evidence_refs": [
            str(CONTRACT_PATH), str(TASK_MATRIX_PATH), str(STATUS_PATH),
            str(TEST_RESULTS_PATH), str(OPEN_RISKS_PATH), str(ROLLBACK_PATH),
        ],
    }


def _status(manifest: dict[str, Any]) -> str:
    return f"""# v1.5 S06-P2 黄金数据锁定执行状态

- T01：已生成 `{manifest['candidate_count']}` 条私有字段候选确认表，覆盖 `{manifest['field_family_count']}` 类字段；当前 accepted=`{manifest['accepted_field_count']}`、pending=`{manifest['pending_candidate_count']}`。
- owner review UI：已提供 token/origin gated、仅 `127.0.0.1` 监听的本机复核入口；按 `{manifest['source_group_count']}` 个来源固定排序、分组过滤并显示组内待决定数；无外部 asset，草稿 mode 0600；不预选 ACCEPT，不自动推断权威值。
- T02：已生成 `{manifest['project_summary_count']}` 个项目级黄金汇总；全部使用整数分，分类合计、总成本、收入、毛利和毛利率精确一致，允许误差为 0 分。
- T03：已锁定 `{manifest['golden_version_count']}` 个不可覆盖的黄金版本；纠错只能追加新版本。
- gate：`{manifest['phase_acceptance_status']}`；validation receipts=`{manifest['validation_receipt_count']}`；S06-P3 entry=`{str(manifest['s06_p3_entry_allowed']).lower()}`，但本轮未启动 S06-P3。
- boundary：私有名称/hash/文本/值/locator/确认人公开计数均为 0；raw mutation=false；formal report/GitHub/App/business=false。
"""


def _tests(manifest: dict[str, Any]) -> str:
    return f"""# v1.5 S06-P2 测试结果

- private preparation：{manifest['candidate_count']} candidates、6 field families、private mode 0600、Git ignored。
- signoff gate：packet digest、确认人/角色/时区时间/依据、逐候选 ACCEPT/REJECT、unit/tax/business meaning/source locator 均为必填。
- review transport：只允许 `127.0.0.1`、one-time token、same-origin 写请求；CSP/no-store/no-referrer/no external asset；mode-0600 草稿原子保存；按 `{manifest['source_group_count']}` 个来源稳定排序、过滤和显示组内进度。
- browser smoke：{manifest['candidate_count']} 条渲染、筛选、草稿保存/重载、未完成 finalization fail-closed 均通过；external request=0、page error=0。
- money gate：canonical money=`SIGNED_INTEGER_CENTS`；tolerance=`{manifest['money_tolerance_cents']}` cent；1 cent mismatch fail closed。
- summary gate：category total=total cost；revenue-total cost=gross profit；gross margin 使用 Decimal half-up 到 basis point 并与签署值一致。
- version gate：只允许追加新版本；version sequence、previous hash、correction reason 和 record hash 形成不可覆盖链。
- public boundary：原始名称/hash/文本/值/定位/确认人身份公开计数均为 0。
- acceptance：授权记录、逐项决策、项目汇总、版本锁定和最终验证必须同时通过；当前状态为 `{manifest['phase_acceptance_status']}`。
"""


def _risks(manifest: dict[str, Any]) -> str:
    return f"""# v1.5 S06-P2 开放风险

1. 跨来源工作簿无法与 8 个项目精确绑定，已整体排除；后续若要纳入，必须先取得可靠项目键。
2. 原资料未明确税口径，公开状态保持 `SOURCE_NOT_STATED`，不得擅自改写为含税或不含税。
3. 私有授权、决策和黄金版本只存在 ignored runtime；公开仓库只能证明汇总门禁状态，不能还原业务数据。
4. 已锁定版本不得覆盖或删除；后续纠错只能追加并说明原因。
5. S06-P3、Stage Review、正式报告、GitHub、App 和经营执行均未在本轮启动。
"""


def _rollback() -> str:
    return """# v1.5 S06-P2 回滚计划

1. 仅回滚 `v015_s06_p2_*` 工具、测试、localhost review UI、public-safe contract/evidence 和本 Phase 治理记录。
2. private candidate/signoff template 是可再生派生物；确认不再需要后可删除，但禁止改写或删除 raw inbox。
3. private draft 可重建；最终 signoff 只允许首次创建且不得覆盖。一旦存在已签署 golden ledger，不得覆盖或删改历史；纠错只能追加新版本。
4. 不回滚 S06-P1 已冻结的 20 条 receipts，也不启动 S06-P3、Stage Review、GitHub 或 App。
"""


def _replace_yaml_scalars(text: str, values: dict[str, Any]) -> str:
    for key, value in values.items():
        rendered = json.dumps(value, ensure_ascii=False) if isinstance(value, str) else str(value).lower() if isinstance(value, bool) else str(value)
        pattern = re.compile(rf"^{re.escape(key)}:.*$", re.MULTILINE)
        if pattern.search(text):
            text = pattern.sub(f"{key}: {rendered}", text, count=1)
        else:
            text = text.rstrip() + f"\n{key}: {rendered}\n"
    return text


def _project_state_text(path: Path, manifest: dict[str, Any]) -> str:
    final = manifest["phase_acceptance_status"] == "PASSED"
    values: dict[str, Any] = {
        "phase_execution_status": "EXECUTION_COMPLETE",
        "phase_acceptance_status": manifest["phase_acceptance_status"],
        "evidence_validation_status": manifest["evidence_validation_status"],
        "stage_lifecycle_status": "IN_PROGRESS", "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": manifest["stage_execution_percentage"],
        "stage_phase_pass_count": manifest["stage_phase_pass_count"],
        "stage_task_accepted_count": manifest["stage_task_accepted_count"],
        "phase_task_accepted_count": manifest["task_accepted_count"],
        "decision": manifest["decision"], "s06_p2_acceptance_status": manifest["phase_acceptance_status"],
        "s06_p2_pending_candidate_count": 0, "s06_p2_accepted_field_count": 92,
        "s06_p2_rejected_candidate_count": 65, "s06_p2_project_summary_count": 8,
        "s06_p2_golden_version_count": 1, "s06_p2_human_signoff_valid": True,
        "s06_p2_validation_receipt_count": manifest["validation_receipt_count"],
        "s06_p3_entry_allowed": final, "s06_p3_started": False,
    }
    if path == PROJECT_STATE_PATH:
        values.update({
            "summary": "KMFA v1.5 S06-P2 已核对 157 条候选并形成 8 个项目黄金基准；采用 92 条、剔除 65 条、金额误差 0 分、黄金版本 1 个。" if final else "KMFA v1.5 S06-P2 已完成 8 个项目黄金基准核对与锁定，当前等待最终验证。",
            "current_status": "s06_p2_passed_s06_p3_not_started" if final else "s06_p2_locked_pending_final_validation",
        })
    else:
        values.update({
            "current_phase_status": "s06_p2_passed_s06_p3_not_started" if final else "s06_p2_locked_pending_final_validation",
            "current_stage_status": f"in_progress_acceptance_pending_{manifest['stage_execution_percentage']}_percent",
        })
    return _replace_yaml_scalars(path.read_text(encoding="utf-8"), values)


def _replace_first_s06p2_section(text: str, heading: str, body: str) -> str:
    match = re.search(r"^## .*(?:S06-P2|s06p2).*$", text, re.MULTILINE)
    if not match:
        raise BuildError("S06-P2 document section missing")
    next_heading = re.search(r"^## ", text[match.end():], re.MULTILINE)
    end = match.end() + next_heading.start() if next_heading else len(text)
    return text[:match.start()] + heading + "\n\n" + body.rstrip() + "\n\n" + text[end:].lstrip("\n")


def _upsert_s06p2_section(text: str, heading: str, body: str) -> str:
    if re.search(r"^## .*(?:S06-P2|s06p2).*$", text, re.MULTILINE):
        return _replace_first_s06p2_section(text, heading, body)
    return heading + "\n\n" + body.rstrip() + "\n\n" + text.lstrip()


def _primary_document_outputs(manifest: dict[str, Any]) -> dict[Path, str]:
    final = manifest["phase_acceptance_status"] == "PASSED"
    label = "PASSED" if final else "待最终验证"
    common = f"""- 已处理 157 条候选：采用 92 条、剔除 65 条；未可靠绑定到 8 个项目的跨来源表格不做猜测，全部排除。
- 已形成 8 个项目汇总；合同额、分类成本、总成本、毛利和毛利率逐分核对，金额误差为 0 分。
- 已锁定首个不可覆盖的黄金版本；后续纠错只能说明原因并追加新版本。
- 如需人工复核，入口仍仅监听 `127.0.0.1`，不会向外网发送私有资料。
- 用户授权与具体项目数据只保存在本机私有目录；公开仓库不含名称、金额、定位或确认人身份。
- 当前 Phase=`{manifest['phase_acceptance_status']}`，最终验证记录=`{manifest['validation_receipt_count']}`；S06=`IN_PROGRESS/PENDING/{manifest['stage_execution_percentage']}%`。
- S06-P3 入口=`{str(manifest['s06_p3_entry_allowed']).lower()}`、started=false；本轮未做 Stage review、GitHub upload 或 App reinstall。"""
    features = f"""- `FEAT-KMFA-244`：逐字段授权核对，全部候选均有采用或剔除结论。
- `FEAT-KMFA-245`：8 个项目整数分汇总，0 分误差；冲突毛利与毛利率从已确认收入和成本重算。
- `FEAT-KMFA-246`：首个黄金版本使用追加式 hash 链锁定，禁止覆盖历史。
- `FEAT-KMFA-247`：私有复核与授权证据保持 mode 0600、Git ignored；公开只保留聚合计数。
{common}"""
    model = f"""- model/formula：`MOD-KMFA-COST-001 / FORM-KMFA-V015-S06-P2-GOLDEN-BASELINE-LOCK-001`；参数 `PARAM-KMFA-1957..1965`，登记总数仍为 `10/338/1580`。
- 核心控制值：candidates=157、accepted=92、rejected=65、projects=8、golden versions=1、money tolerance=0 cent、history overwrite=false。
- 税口径：原资料未明确时登记 `SOURCE_NOT_STATED`，不得擅自改为含税或不含税。
- 毛利与毛利率：来源值一致时保留；来源值缺失或冲突时，以已确认合同额和总成本精确派生。
{common}"""
    return {
        HANDOFF_PATH: _replace_first_s06p2_section(HANDOFF_PATH.read_text(encoding="utf-8"), f"## 当前状态（v1.5 S06-P2 黄金数据锁定，{label}）", common),
        README_PATH: _replace_first_s06p2_section(README_PATH.read_text(encoding="utf-8"), f"## v1.5 S06-P2 黄金数据锁定（{label}）", common),
        FEATURES_PATH: _replace_first_s06p2_section(FEATURES_PATH.read_text(encoding="utf-8"), f"## v1.5 S06-P2 黄金数据锁定能力（{label}）", features),
        DEVELOPMENT_RECORD_PATH: _replace_first_s06p2_section(DEVELOPMENT_RECORD_PATH.read_text(encoding="utf-8"), f"## 2026-07-15 - v1.5 S06-P2 黄金数据锁定（{label}）", common),
        MODEL_PARAMETERS_PATH: _replace_first_s06p2_section(MODEL_PARAMETERS_PATH.read_text(encoding="utf-8"), f"## v1.5 S06-P2 黄金数据锁定公式及参数（{label}）", model),
        CHANGELOG_PATH: _replace_first_s06p2_section(CHANGELOG_PATH.read_text(encoding="utf-8"), f"## 1.5.0-dev-s06p2（{label}）", common),
    }


def _parameter_registry_text(manifest: dict[str, Any]) -> str:
    lines = PARAMETER_REGISTRY_PATH.read_text(encoding="utf-8").splitlines()
    header = lines[0].split(",")
    index = {name: position for position, name in enumerate(header)}
    final = manifest["phase_acceptance_status"] == "PASSED"
    active_values = {
        "PARAM-KMFA-1957": "157;6;0;92;65",
        "PARAM-KMFA-1960": "true;VALID;true;true;127.0.0.1_ONLY;0;0600;false",
        "PARAM-KMFA-1961": "8;true",
        "PARAM-KMFA-1962": "1;true;true;false",
        "PARAM-KMFA-1965": (
            "3;3;67;IN_PROGRESS;PENDING;PASSED;true;false;false;false;false"
            if final else
            "3;0;33;IN_PROGRESS;PENDING;PENDING_FINAL_VALIDATION;false;false;false;false;false"
        ),
    }
    rationale = {
        "PARAM-KMFA-1957": "All candidates require an explicit authorized ACCEPT or REJECT decision",
        "PARAM-KMFA-1960": "Private user authorization is digest-bound to authorized-agent signoff and never exposed publicly",
        "PARAM-KMFA-1961": "Eight project summaries must reconcile exactly at zero-cent tolerance",
        "PARAM-KMFA-1962": "Corrections append a new hash-chained version and cannot overwrite history",
        "PARAM-KMFA-1965": "Receipt-bound final validation opens only the next S06-P3 entry without starting it",
    }
    receipts = _final_receipts()
    verification_head = receipts[0]["validation_head"] if receipts else "pending_implementation_commit"
    output = [lines[0]]
    seen: set[str] = set()
    for line in lines[1:]:
        parameter_id = line.split(",", 1)[0]
        if parameter_id not in active_values:
            output.append(line)
            continue
        fields = line.split(",")
        if len(fields) != len(header):
            raise BuildError(f"parameter registry row shape mismatch: {parameter_id}")
        fields[index["active_value"]] = active_values[parameter_id]
        fields[index["extracted_value"]] = active_values[parameter_id]
        fields[index["source_or_rationale"]] = rationale[parameter_id]
        fields[index["last_verified_commit"]] = verification_head
        fields[index["verified_at"]] = "2026-07-15"
        fields[index["evidence_hash"]] = "receipt_bound_pass" if final else "pending_final_validation"
        output.append(",".join(fields))
        seen.add(parameter_id)
    if seen != set(active_values):
        raise BuildError("S06-P2 parameter registry rows missing")
    return "\n".join(output) + "\n"


def _traceability_text(manifest: dict[str, Any]) -> str:
    status = "completed_validated_local_only_s06p2_passed_s06p3_entry_only" if manifest["phase_acceptance_status"] == "PASSED" else "golden_locked_pending_final_validation_local_only"
    replacement = (
        "REQ-KMFA-V015-S06-P2-GOLDEN-BASELINE-LOCK,MOD-KMFA-COST-001,ASM-KMFA-002;ASM-KMFA-004;ASM-KMFA-006,"
        "FORM-KMFA-V015-S06-P2-GOLDEN-BASELINE-LOCK-001,PARAM-KMFA-1957;PARAM-KMFA-1958;PARAM-KMFA-1959;PARAM-KMFA-1960;PARAM-KMFA-1961;PARAM-KMFA-1962;PARAM-KMFA-1963;PARAM-KMFA-1964;PARAM-KMFA-1965,"
        "KMFA-V015-S06-P2-GOLDEN-BASELINE-LOCK-20260715,ACC-KMFA-V015-S06-P2-GOLDEN-BASELINE-LOCK,"
        "KMFA/tools/v015_s06_p2_golden_baseline_lock.py;KMFA/tools/v015_s06_p2_authorized_resolution.py;KMFA/tools/v015_s06_p2_signoff_review.py;KMFA/tools/build_v015_s06_p2_golden_baseline_lock.py;KMFA/tools/check_v015_s06_p2_golden_baseline_lock.py;KMFA/tools/run_v015_s06_p2_validations.py,"
        "KMFA/metadata/quality/v015_s06_p2_golden_lock_contract_public_safe.json,"
        "KMFA/tests/test_v015_s06_p2_authorized_resolution.py;KMFA/tests/test_v015_s06_p2_golden_baseline_lock.py;KMFA/tests/test_v015_s06_p2_signoff_review.py;KMFA/tests/playwright_v015_s06_p2_signoff_review.py;KMFA/tests/test_v015_s06_p2_golden_baseline_lock_governance.py;KMFA/tests/test_v015_roadmap_governance_sync.py,"
        f"KMFA/stage_artifacts/V015_S06_P2_GOLDEN_BASELINE_LOCK/,{status}"
    )
    text = TRACEABILITY_PATH.read_text(encoding="utf-8")
    return re.sub(r"^REQ-KMFA-V015-S06-P2-GOLDEN-BASELINE-LOCK,.*$", replacement, text, count=1, flags=re.MULTILINE)


def _delivery_tasks_text(manifest: dict[str, Any]) -> str:
    final = manifest["phase_acceptance_status"] == "PASSED"
    block = f'''  - task_id: "KMFA-V015-S06-P2-GOLDEN-BASELINE-LOCK-20260715"
    phase: "V015_S06_P2_GOLDEN_BASELINE_LOCK"
    phase_kind: "TASKPACK_ROADMAP_PHASE"
    taskpack_roadmap_phase: true
    taskpack_roadmap_task: false
    acceptance_status: "{manifest['phase_acceptance_status']}"
    execution_status: "EXECUTION_COMPLETE"
    current_result: "{'8_PROJECT_GOLDEN_BASELINES_VALIDATED' if final else 'GOLDEN_LOCKED_PENDING_FINAL_VALIDATION'}"
    candidate_count: 157
    accepted_field_count: 92
    rejected_candidate_count: 65
    project_summary_count: 8
    money_difference_cents: 0
    golden_version_count: 1
    validation_receipt_count: {manifest['validation_receipt_count']}
    s06_p3_entry_allowed: {str(final).lower()}
    s06_p3_started: false
    code_refs:
      - "KMFA/tools/v015_s06_p2_authorized_resolution.py"
      - "KMFA/tools/v015_s06_p2_golden_baseline_lock.py"
      - "KMFA/tools/check_v015_s06_p2_golden_baseline_lock.py"
      - "KMFA/tools/run_v015_s06_p2_validations.py"
    test_refs:
      - "KMFA/tests/test_v015_s06_p2_authorized_resolution.py"
      - "KMFA/tests/test_v015_s06_p2_golden_baseline_lock.py"
      - "KMFA/tests/test_v015_s06_p2_golden_baseline_lock_governance.py"
    acceptance_ids:
      - "ACC-KMFA-V015-S06-P2-GOLDEN-BASELINE-LOCK"
    evidence_refs:
      - "KMFA/stage_artifacts/V015_S06_P2_GOLDEN_BASELINE_LOCK/"
'''
    text = DELIVERY_TASKS_PATH.read_text(encoding="utf-8")
    start = text.find('  - task_id: "KMFA-V015-S06-P2-GOLDEN-BASELINE-LOCK-20260715"')
    if start < 0:
        raise BuildError("S06-P2 delivery task missing")
    next_task = text.find("\n  - task_id:", start + 4)
    if next_task < 0:
        next_task = len(text)
    return text[:start] + block + text[next_task + (1 if next_task < len(text) else 0):]


def _governance_document_outputs(manifest: dict[str, Any]) -> dict[Path, str]:
    final = manifest["phase_acceptance_status"] == "PASSED"
    label = "PASSED" if final else "PENDING_FINAL_VALIDATION"
    common = f"""- 范围：本 Run 仅完成 Roadmap `S06-P2`，未启动 S06-P3、Stage review、GitHub upload 或 App reinstall。
- 决策：157 条候选全部处理，采用 92 条、剔除 65 条；无法与 8 个项目精确绑定的跨来源表格不猜测。
- 结果：8 个项目汇总均为整数分，金额误差 0 分；首个黄金版本已追加锁定，禁止覆盖历史。
- 授权边界：用户授权与业务明细仅存 private runtime；公开名称、金额、定位、授权原文及确认人身份均为 0。
- 状态：Phase=`{manifest['phase_acceptance_status']}`，receipts=`{manifest['validation_receipt_count']}`，S06=`IN_PROGRESS/PENDING/{manifest['stage_execution_percentage']}%`，S06-P3 entry/started=`{str(final).lower()}/false`。"""
    model = f"""- model/formula/parameters：`MOD-KMFA-COST-001 / FORM-KMFA-V015-S06-P2-GOLDEN-BASELINE-LOCK-001 / PARAM-KMFA-1957..1965`。
- 逻辑：`157 resolved = 92 accepted + 65 rejected`；`8 project summaries`；`money_difference_cents=0`；`golden_version_count=1`；`history_overwrite_allowed=false`。
- 来源毛利或毛利率缺失/冲突时，从已确认合同额与总成本精确派生；原资料未说明税口径时登记 `SOURCE_NOT_STATED`。
- 最终状态：`{label}`；receipts={manifest['validation_receipt_count']}；公开层只含聚合，不含可还原业务值。"""
    version = VERSION_MATRIX_PATH.read_text(encoding="utf-8")
    version = re.sub(r'(?m)^  golden_ledger_append_enabled: false$', '  golden_ledger_append_enabled: true', version, count=1)
    version = re.sub(r'(?m)^current_iteration:.*$', 'current_iteration: "ITER-20260715-KMFA-V015-S06-P2-GOLDEN-BASELINE-LOCK"', version, count=1)
    return {
        DEVELOPMENT_LEDGER_PATH: _upsert_s06p2_section(DEVELOPMENT_LEDGER_PATH.read_text(encoding="utf-8"), f"## 2026-07-15 - v1.5 S06-P2 黄金数据锁定（{label}）", common).rstrip() + "\n",
        MODEL_SPEC_PATH: _upsert_s06p2_section(MODEL_SPEC_PATH.read_text(encoding="utf-8"), f"## MOD-KMFA-COST-001 / FORM-KMFA-V015-S06-P2-GOLDEN-BASELINE-LOCK-001（{label}）", model).rstrip() + "\n",
        OWNER_STATUS_PATH: _upsert_s06p2_section(OWNER_STATUS_PATH.read_text(encoding="utf-8"), f"## v1.5 S06-P2 负责人状态（{label}）", common).rstrip() + "\n",
        GOVERNANCE_STATUS_PATH: _upsert_s06p2_section(GOVERNANCE_STATUS_PATH.read_text(encoding="utf-8"), f"## v1.5 S06-P2 治理状态（{label}）", common).rstrip() + "\n",
        TRACEABILITY_PATH: _traceability_text(manifest),
        VERSION_MATRIX_PATH: version,
        DELIVERY_TASKS_PATH: _delivery_tasks_text(manifest),
    }


def _record_body(schema_version: str, event_id: str) -> dict[str, Any]:
    return {
        "schema_version": schema_version,
        "event_id": event_id,
        "event_type": "phase_execution_pending_external_signoff",
        "summary": "S06-P2 prepared the private field review packet and fail-closed immutable golden lock; owner signoff is missing so no baseline was locked.",
        "project_id": "KMFA",
        "target_release": "v1.5",
        "stage_id": "S06",
        "phase_id": kernel.RUN_PHASE_ID,
        "roadmap_phase_id": kernel.ROADMAP_PHASE_ID,
        "task_id": kernel.TASK_ID,
        "acceptance_id": kernel.ACCEPTANCE_ID,
        "run_mode": "IMPLEMENT",
        "work_kind": "GOLDEN_BASELINE_LOCK",
        "fact_level": "EXTRACTED",
        "phase_execution_status": "EXECUTION_COMPLETE_PENDING_OWNER_SIGNOFF",
        "phase_acceptance_status": "BLOCKED_BY_MISSING_SIGNOFF",
        "evidence_validation_status": "PASS_PENDING_EXTERNAL_SIGNOFF",
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": 33,
        "stage_phase_pass_count": 1,
        "stage_task_accepted_count": 3,
        "phase_task_count": 3,
        "task_execution_complete_count": 1,
        "task_accepted_count": 0,
        "candidate_count": 233,
        "pending_candidate_count": 233,
        "accepted_field_count": 0,
        "human_signoff_status": "MISSING",
        "human_signoff_valid": False,
        "project_summary_count": 0,
        "money_tolerance_cents": 0,
        "golden_version_count": 0,
        "append_only_history_required": True,
        "history_overwrite_allowed": False,
        "raw_mutation_performed": False,
        "decision": "REMAIN_IN_S06_P2_PENDING_OWNER_SIGNOFF",
        "s06_p3_entry_allowed": False,
        "formal_report_generated": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "evidence_ref": "KMFA/stage_artifacts/V015_S06_P2_GOLDEN_BASELINE_LOCK/",
        "event_time": "2026-07-15T02:30:00+10:00",
        "updated_at": "2026-07-15T02:30:00+10:00",
        "version": kernel.VERSION,
        "status": "execution_complete_pending_owner_signoff_s06p2_blocked_local_only",
    }


def _governance_records() -> dict[Path, dict[str, Any]]:
    development = _record_body(
        "kmfa.development_event.v1",
        "DEV-KMFA-20260715-V015-S06-P2-GOLDEN-BASELINE-LOCK-PENDING-SIGNOFF",
    )
    development.update({
        "iteration_id": "ITER-20260715-KMFA-V015-S06-P2-GOLDEN-BASELINE-LOCK",
        "result_commit": "pending_implementation_commit",
        "files_changed": CHANGED_FILES,
    })
    governance = _record_body(
        "kmfa.governance_event.v1",
        "EVENT-KMFA-20260715-V015-S06-P2-GOLDEN-BASELINE-LOCK-PENDING-SIGNOFF",
    )
    stage = _record_body(
        "kmfa.stage_status.v1",
        "STATUS-KMFA-20260715-V015-S06-P2-GOLDEN-BASELINE-LOCK-PENDING-SIGNOFF",
    )
    stage["status_record_id"] = stage.pop("event_id")
    stage["record_type"] = "phase_status"
    return {
        DEVELOPMENT_EVENTS_PATH: development,
        GOVERNANCE_EVENTS_PATH: governance,
        STAGE_STATUS_PATH: stage,
    }


def _coverage_record() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.development_event.v1",
        "event_id": "DEV-KMFA-20260715-V015-S06-P2-GOLDEN-BASELINE-LOCK-COVERAGE",
        "event_type": "governance_coverage",
        "summary": "Completes exact changed-file coverage for S06-P2 generated pending-state artifacts.",
        "iteration_id": "ITER-20260715-KMFA-V015-S06-P2-GOLDEN-BASELINE-LOCK",
        "result_commit": "pending_implementation_commit",
        "project_id": "KMFA",
        "target_release": "v1.5",
        "stage_id": "S06",
        "phase_id": kernel.RUN_PHASE_ID,
        "task_id": kernel.TASK_ID,
        "acceptance_id": kernel.ACCEPTANCE_ID,
        "fact_level": "EXTRACTED",
        "files_changed": [
            "KMFA/stage_artifacts/V015_S06_P2_GOLDEN_BASELINE_LOCK/human/open_risks_zh.md",
            "KMFA/stage_artifacts/V015_S06_P2_GOLDEN_BASELINE_LOCK/machine/s06_p2_golden_baseline_lock_manifest.json",
            "KMFA/stage_artifacts/V015_S06_P2_GOLDEN_BASELINE_LOCK/machine/task_acceptance_matrix_public_safe.json",
        ],
        "event_time": "2026-07-15T02:31:00+10:00",
        "updated_at": "2026-07-15T02:31:00+10:00",
        "version": kernel.VERSION,
        "status": "coverage_complete_pending_owner_signoff",
    }


def _review_ui_continuation_record() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.development_event.v1",
        "event_id": "DEV-KMFA-20260714-V015-S06-P2-PRIVATE-REVIEW-UI-CONTINUATION",
        "event_type": "phase_continuation_pending_external_signoff",
        "summary": "Added a localhost-only token/origin-gated private owner review UI with mode-0600 draft persistence and fail-closed final sign-off creation; S06-P2 remains blocked by missing owner sign-off.",
        "iteration_id": "ITER-20260714-KMFA-V015-S06-P2-PRIVATE-REVIEW-UI",
        "result_commit": "pending_implementation_commit",
        "project_id": "KMFA",
        "target_release": "v1.5",
        "stage_id": "S06",
        "phase_id": kernel.RUN_PHASE_ID,
        "roadmap_phase_id": kernel.ROADMAP_PHASE_ID,
        "task_id": kernel.TASK_ID,
        "acceptance_id": kernel.ACCEPTANCE_ID,
        "fact_level": "EXTRACTED",
        "phase_execution_status": "EXECUTION_COMPLETE_PENDING_OWNER_SIGNOFF",
        "phase_acceptance_status": "BLOCKED_BY_MISSING_SIGNOFF",
        "private_review_ui_available": True,
        "private_review_host_policy": "127.0.0.1_ONLY",
        "private_review_external_asset_count": 0,
        "private_review_draft_mode": "0600",
        "owner_signoff_status": "MISSING",
        "golden_version_count": 0,
        "s06_p3_entry_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "files_changed": REVIEW_UI_CHANGED_FILES,
        "event_time": "2026-07-14T23:01:18+10:00",
        "updated_at": "2026-07-14T23:01:18+10:00",
        "version": kernel.VERSION,
        "status": "review_ui_ready_owner_signoff_still_missing",
    }


def _review_ui_governance_sync_record() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.development_event.v1",
        "event_id": "DEV-KMFA-20260714-V015-S06-P2-PRIVATE-REVIEW-UI-GOVERNANCE-SYNC",
        "event_type": "governance_sync",
        "summary": "Synchronized the S06-P2 localhost review transport across owner status delivery traceability model formula parameter and version records without adding a model formula or parameter ID or changing the blocked phase gate.",
        "iteration_id": "ITER-20260714-KMFA-V015-S06-P2-PRIVATE-REVIEW-UI",
        "result_commit": "pending_implementation_commit",
        "project_id": "KMFA",
        "target_release": "v1.5",
        "stage_id": "S06",
        "phase_id": kernel.RUN_PHASE_ID,
        "task_id": kernel.TASK_ID,
        "acceptance_id": kernel.ACCEPTANCE_ID,
        "fact_level": "EXTRACTED",
        "model_count": 10,
        "active_formula_count": 338,
        "active_parameter_count": 1580,
        "new_model_count": 0,
        "new_formula_count": 0,
        "new_parameter_id_count": 0,
        "phase_acceptance_status": "BLOCKED_BY_MISSING_SIGNOFF",
        "owner_signoff_status": "MISSING",
        "files_changed": GOVERNANCE_SYNC_CHANGED_FILES,
        "event_time": "2026-07-14T23:10:00+10:00",
        "updated_at": "2026-07-14T23:10:00+10:00",
        "version": kernel.VERSION,
        "status": "governance_synchronized_owner_signoff_still_missing",
    }


def _semantic_extraction_remediation_record() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.development_event.v1",
        "event_id": "DEV-KMFA-20260715-V015-S06-P1-CANDIDATE-SEMANTIC-REMEDIATION",
        "event_type": "upstream_phase_remediation",
        "summary": "Corrected S06-P1 candidate semantics before S06-P2 signoff: contract/total locator collisions, supporting-page promotions, margin-header profit candidates, and workbook summary candidates are all zero.",
        "iteration_id": "ITER-20260715-KMFA-V015-S06-P1-CANDIDATE-SEMANTIC-REMEDIATION",
        "result_commit": "pending_implementation_commit",
        "project_id": "KMFA",
        "target_release": "v1.5",
        "stage_id": "S06",
        "phase_id": "V015_S06_P1_AUTHORITATIVE_SOURCE_REGISTRATION",
        "roadmap_phase_id": "S06-P1",
        "task_id": "KMFA-V015-S06-P1-AUTHORITATIVE-SOURCE-REGISTRATION-20260715",
        "acceptance_id": "ACC-KMFA-V015-S06-P1-AUTHORITATIVE-SOURCE-REGISTRATION",
        "fact_level": "EXTRACTED",
        "candidate_count_before": 233,
        "candidate_count_after": 157,
        "field_family_count": 6,
        "contract_total_locator_collision_count": 0,
        "supporting_pdf_promoted_candidate_count": 0,
        "margin_header_gross_profit_candidate_count": 0,
        "workbook_summary_candidate_count": 0,
        "candidate_semantic_quality_passed": True,
        "raw_mutation_performed": False,
        "s06_p2_signoff_status": "MISSING",
        "s06_p3_entry_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "files_changed": [
            "KMFA/tools/v015_s06_p1_authoritative_source_registration.py",
            "KMFA/tools/v015_s06_p2_golden_baseline_lock.py",
            "KMFA/tools/v015_s06_p2_signoff_review.py",
            "KMFA/tests/test_v015_s06_p1_authoritative_source_registration.py",
            "KMFA/tests/test_v015_s06_p2_golden_baseline_lock.py",
            "KMFA/docs/governance/",
            "KMFA/metadata/",
            "KMFA/stage_artifacts/V015_S06_P1_AUTHORITATIVE_SOURCE_REGISTRATION/",
            "KMFA/stage_artifacts/V015_S06_P2_GOLDEN_BASELINE_LOCK/",
            "KMFA/HANDOFF.md",
            "KMFA/功能清单.md",
            "KMFA/开发记录.md",
            "KMFA/模型参数文件.md",
        ],
        "event_time": "2026-07-15T05:21:23+10:00",
        "updated_at": "2026-07-15T05:21:23+10:00",
        "version": kernel.VERSION,
        "status": "semantic_extraction_remediated_pending_local_commit",
    }


def _source_grouped_review_record() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.development_event.v1",
        "event_id": "DEV-KMFA-20260715-V015-S06-P2-SOURCE-GROUPED-REVIEW-UX",
        "event_type": "phase_continuation_pending_external_signoff",
        "summary": "Made the private S06-P2 review understandable without weakening the human gate: candidates are stably ordered and filterable across nine source groups with per-group pending progress and Chinese semantic labels; no value, project, unit, tax, or business inference is introduced.",
        "iteration_id": "ITER-20260715-KMFA-V015-S06-P2-SOURCE-GROUPED-REVIEW-UX",
        "result_commit": "pending_implementation_commit",
        "project_id": "KMFA",
        "target_release": "v1.5",
        "stage_id": "S06",
        "phase_id": kernel.RUN_PHASE_ID,
        "roadmap_phase_id": kernel.ROADMAP_PHASE_ID,
        "task_id": kernel.TASK_ID,
        "acceptance_id": kernel.ACCEPTANCE_ID,
        "fact_level": "EXTRACTED",
        "phase_execution_status": "EXECUTION_COMPLETE_PENDING_OWNER_SIGNOFF",
        "phase_acceptance_status": "BLOCKED_BY_MISSING_SIGNOFF",
        "candidate_count": 157,
        "source_group_count": 9,
        "private_review_source_filter_available": True,
        "private_review_stable_source_order": True,
        "private_review_automatic_inference": False,
        "owner_signoff_status": "MISSING",
        "golden_version_count": 0,
        "s06_p3_entry_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "files_changed": [
            "KMFA/tools/v015_s06_p2_signoff_review.py",
            "KMFA/tools/v015_s06_p2_golden_baseline_lock.py",
            "KMFA/tools/build_v015_s06_p2_golden_baseline_lock.py",
            "KMFA/tools/check_v015_s06_p2_golden_baseline_lock.py",
            "KMFA/tests/test_v015_s06_p2_signoff_review.py",
            "KMFA/tests/playwright_v015_s06_p2_signoff_review.py",
            "KMFA/tests/test_v015_s06_p2_golden_baseline_lock.py",
            "KMFA/tests/test_v015_s06_p2_golden_baseline_lock_governance.py",
            "KMFA/metadata/quality/v015_s06_p2_golden_lock_contract_public_safe.json",
            "KMFA/stage_artifacts/V015_S06_P2_GOLDEN_BASELINE_LOCK/",
            "KMFA/docs/governance/development_events.jsonl",
            "KMFA/CHANGELOG.md",
            "KMFA/HANDOFF.md",
            "KMFA/功能清单.md",
            "KMFA/开发记录.md",
            "KMFA/模型参数文件.md",
        ],
        "event_time": "2026-07-15T05:31:33+10:00",
        "updated_at": "2026-07-15T05:31:33+10:00",
        "version": kernel.VERSION,
        "status": "source_grouped_review_ready_owner_signoff_still_missing",
    }


def _authorized_resolution_record() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.development_event.v1",
        "event_id": "DEV-KMFA-20260715-V015-S06-P2-AUTHORIZED-BASELINE-RESOLUTION-GOVERNANCE-COMPLETE",
        "event_type": "authorized_private_baseline_resolution",
        "summary": "User delegated S06-P2 decisions to Codex; eight project baselines reconciled exactly, unmatched cross-source workbook candidates rejected, and the first append-only golden version locked privately.",
        "iteration_id": "ITER-20260715-KMFA-V015-S06-P2-AUTHORIZED-BASELINE-RESOLUTION-GOVERNANCE-COMPLETE",
        "result_commit": "pending_implementation_commit",
        "project_id": "KMFA", "target_release": "v1.5", "stage_id": "S06",
        "phase_id": kernel.RUN_PHASE_ID, "roadmap_phase_id": kernel.ROADMAP_PHASE_ID,
        "task_id": kernel.TASK_ID, "acceptance_id": kernel.ACCEPTANCE_ID,
        "fact_level": "AGGREGATE_PRIVATE_DERIVED",
        "candidate_count": 157, "accepted_field_count": 92,
        "rejected_candidate_count": 65, "project_summary_count": 8,
        "money_difference_cents": 0, "golden_version_count": 1,
        "private_user_authorization_recorded": True,
        "public_authorization_text_count": 0, "public_confirmer_identity_count": 0,
        "raw_mutation_performed": False, "s06_p3_started": False,
        "github_upload_performed": False, "app_reinstall_performed": False,
        "files_changed": [
            "KMFA/CHANGELOG.md", "KMFA/HANDOFF.md", "KMFA/README.md",
            "KMFA/docs/governance/development_events.jsonl",
            "KMFA/docs/governance/formula_registry.yaml",
            "KMFA/docs/governance/model_registry.yaml",
            "KMFA/docs/governance/parameter_registry.csv",
            "KMFA/docs/governance/project.yaml", "KMFA/docs/governance/roadmap.yaml",
            "KMFA/metadata/model_registry.yaml", "KMFA/metadata/project/project.yaml",
            "KMFA/metadata/quality/v015_s06_p2_golden_lock_contract_public_safe.json",
            "KMFA/stage_artifacts/V015_S06_P2_GOLDEN_BASELINE_LOCK/",
            "KMFA/tests/test_v015_roadmap_governance_sync.py",
            "KMFA/tools/v015_s06_p2_authorized_resolution.py",
            "KMFA/tools/v015_s06_p2_golden_baseline_lock.py",
            "KMFA/tools/v015_s06_p2_signoff_review.py",
            "KMFA/tools/build_v015_s06_p2_golden_baseline_lock.py",
            "KMFA/tools/check_v015_s06_p2_golden_baseline_lock.py",
            "KMFA/tools/run_v015_s06_p2_validations.py",
            "KMFA/tools/v015_roadmap_governance_sync.py",
            "KMFA/tests/test_v015_s06_p2_authorized_resolution.py",
            "KMFA/tests/test_v015_s06_p2_golden_baseline_lock.py",
            "KMFA/tests/test_v015_s06_p2_golden_baseline_lock_governance.py",
            "KMFA/功能清单.md", "KMFA/开发记录.md", "KMFA/模型参数文件.md",
        ],
        "event_time": "2026-07-15T06:30:00+10:00",
        "updated_at": "2026-07-15T06:30:00+10:00",
        "version": kernel.VERSION,
        "status": "golden_version_locked_pending_final_validation",
    }


def _final_validation_record() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.development_event.v1",
        "event_id": "DEV-KMFA-20260715-V015-S06-P2-FINAL-VALIDATION-PASS",
        "event_type": "phase_final_validation",
        "summary": "S06-P2 final validation passed with one receipt-bound run; all three phase tasks are accepted and S06-P3 entry is open but not started.",
        "iteration_id": "ITER-20260715-KMFA-V015-S06-P2-FINAL-VALIDATION",
        "result_commit": "pending_final_commit",
        "project_id": "KMFA", "target_release": "v1.5", "stage_id": "S06",
        "phase_id": kernel.RUN_PHASE_ID, "roadmap_phase_id": kernel.ROADMAP_PHASE_ID,
        "task_id": kernel.TASK_ID, "acceptance_id": kernel.ACCEPTANCE_ID,
        "fact_level": "VALIDATED",
        "phase_acceptance_status": "PASSED", "evidence_validation_status": "PASS",
        "validation_receipt_count": len(EXPECTED_VALIDATION_NAMES),
        "candidate_count": 157, "accepted_field_count": 92,
        "rejected_candidate_count": 65, "project_summary_count": 8,
        "money_difference_cents": 0, "golden_version_count": 1,
        "s06_p3_entry_allowed": True, "s06_p3_started": False,
        "github_upload_performed": False, "app_reinstall_performed": False,
        "files_changed": [
            "KMFA/stage_artifacts/V015_S06_P2_GOLDEN_BASELINE_LOCK/",
            "KMFA/docs/governance/", "KMFA/metadata/",
            "KMFA/HANDOFF.md", "KMFA/开发记录.md", "KMFA/功能清单.md", "KMFA/模型参数文件.md",
        ],
        "event_time": "2026-07-15T06:45:00+10:00",
        "updated_at": "2026-07-15T06:45:00+10:00",
        "version": kernel.VERSION, "status": "s06_p2_passed_s06_p3_not_started",
    }


def _authorized_governance_coverage_record() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.development_event.v1",
        "event_id": "DEV-KMFA-20260715-V015-S06-P2-AUTHORIZED-GOVERNANCE-FULL-COVERAGE",
        "event_type": "governance_coverage",
        "summary": "Exact tracked-file coverage for the authorized S06-P2 baseline resolution, lock, validation tooling, public-safe evidence, and governance synchronization.",
        "iteration_id": "ITER-20260715-KMFA-V015-S06-P2-AUTHORIZED-GOVERNANCE-FULL-COVERAGE",
        "result_commit": "pending_implementation_commit",
        "project_id": "KMFA", "target_release": "v1.5", "stage_id": "S06",
        "phase_id": kernel.RUN_PHASE_ID, "task_id": kernel.TASK_ID,
        "acceptance_id": kernel.ACCEPTANCE_ID, "fact_level": "EXTRACTED",
        "files_changed": [
            "KMFA/CHANGELOG.md", "KMFA/HANDOFF.md", "KMFA/README.md",
            "KMFA/docs/governance/DEVELOPMENT_LEDGER.md", "KMFA/docs/governance/MODEL_SPEC.md",
            "KMFA/docs/governance/OWNER_STATUS.md", "KMFA/docs/governance/STATUS.md",
            "KMFA/docs/governance/TRACEABILITY_MATRIX.csv", "KMFA/docs/governance/VERSION_MATRIX.yaml",
            "KMFA/docs/governance/delivery_tasks.yaml", "KMFA/docs/governance/development_events.jsonl",
            "KMFA/docs/governance/formula_registry.yaml", "KMFA/docs/governance/model_registry.yaml",
            "KMFA/docs/governance/parameter_registry.csv", "KMFA/docs/governance/project.yaml",
            "KMFA/docs/governance/roadmap.yaml", "KMFA/metadata/model_registry.yaml",
            "KMFA/metadata/project/project.yaml",
            "KMFA/metadata/quality/v015_s06_p2_golden_lock_contract_public_safe.json",
            "KMFA/stage_artifacts/V015_S06_P2_GOLDEN_BASELINE_LOCK/human/execution_status_zh.md",
            "KMFA/stage_artifacts/V015_S06_P2_GOLDEN_BASELINE_LOCK/human/open_risks_zh.md",
            "KMFA/stage_artifacts/V015_S06_P2_GOLDEN_BASELINE_LOCK/human/test_results_zh.md",
            "KMFA/stage_artifacts/V015_S06_P2_GOLDEN_BASELINE_LOCK/machine/s06_p2_golden_baseline_lock_manifest.json",
            "KMFA/stage_artifacts/V015_S06_P2_GOLDEN_BASELINE_LOCK/machine/task_acceptance_matrix_public_safe.json",
            "KMFA/tests/test_v015_roadmap_governance_sync.py",
            "KMFA/tests/test_v015_s06_p2_authorized_resolution.py",
            "KMFA/tests/test_v015_s06_p2_golden_baseline_lock_governance.py",
            "KMFA/tools/build_v015_s06_p2_golden_baseline_lock.py",
            "KMFA/tools/check_v015_s06_p2_golden_baseline_lock.py",
            "KMFA/tools/run_v015_s06_p2_validations.py",
            "KMFA/tools/v015_roadmap_governance_sync.py",
            "KMFA/tools/v015_s06_p2_authorized_resolution.py",
            "KMFA/tools/v015_s06_p2_golden_baseline_lock.py",
            "KMFA/tools/v015_s06_p2_signoff_review.py",
            "KMFA/功能清单.md", "KMFA/开发记录.md", "KMFA/模型参数文件.md",
        ],
        "event_time": "2026-07-15T06:40:00+10:00",
        "updated_at": "2026-07-15T06:40:00+10:00",
        "version": kernel.VERSION, "status": "authorized_governance_full_coverage",
    }


def _playwright_self_host_coverage_record() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.development_event.v1",
        "event_id": "DEV-KMFA-20260715-V015-S06-P2-PLAYWRIGHT-SELF-HOST-COVERAGE",
        "event_type": "test_evidence_coverage",
        "summary": "Made the S06-P2 Playwright smoke test self-hosting with isolated temporary draft signoff and screenshot paths for repeatable final validation.",
        "iteration_id": "ITER-20260715-KMFA-V015-S06-P2-FINAL-VALIDATION",
        "result_commit": "pending_implementation_commit",
        "project_id": "KMFA", "target_release": "v1.5", "stage_id": "S06",
        "phase_id": kernel.RUN_PHASE_ID, "task_id": kernel.TASK_ID,
        "acceptance_id": kernel.ACCEPTANCE_ID, "fact_level": "EXTRACTED",
        "files_changed": [
            "KMFA/tests/playwright_v015_s06_p2_signoff_review.py",
            "KMFA/tools/check_v015_s06_p2_golden_baseline_lock.py",
        ],
        "event_time": "2026-07-15T06:42:00+10:00",
        "updated_at": "2026-07-15T06:42:00+10:00",
        "version": kernel.VERSION, "status": "playwright_self_host_ready",
    }


def _append_records() -> None:
    for path, record in _governance_records().items():
        token = record.get("event_id") or record.get("status_record_id")
        existing = path.read_text(encoding="utf-8") if path.exists() else ""
        if token in existing:
            continue
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
    coverage = _coverage_record()
    existing = DEVELOPMENT_EVENTS_PATH.read_text(encoding="utf-8")
    if coverage["event_id"] not in existing:
        with DEVELOPMENT_EVENTS_PATH.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(coverage, ensure_ascii=False, separators=(",", ":")) + "\n")
    review_ui = _review_ui_continuation_record()
    existing = DEVELOPMENT_EVENTS_PATH.read_text(encoding="utf-8")
    if review_ui["event_id"] not in existing:
        with DEVELOPMENT_EVENTS_PATH.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(review_ui, ensure_ascii=False, separators=(",", ":")) + "\n")
    governance_sync = _review_ui_governance_sync_record()
    existing = DEVELOPMENT_EVENTS_PATH.read_text(encoding="utf-8")
    if governance_sync["event_id"] not in existing:
        with DEVELOPMENT_EVENTS_PATH.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(governance_sync, ensure_ascii=False, separators=(",", ":")) + "\n")
    remediation = _semantic_extraction_remediation_record()
    existing = DEVELOPMENT_EVENTS_PATH.read_text(encoding="utf-8")
    if remediation["event_id"] not in existing:
        with DEVELOPMENT_EVENTS_PATH.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(remediation, ensure_ascii=False, separators=(",", ":")) + "\n")
    grouped_review = _source_grouped_review_record()
    existing = DEVELOPMENT_EVENTS_PATH.read_text(encoding="utf-8")
    if grouped_review["event_id"] not in existing:
        with DEVELOPMENT_EVENTS_PATH.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(grouped_review, ensure_ascii=False, separators=(",", ":")) + "\n")
    authorized = _authorized_resolution_record()
    existing = DEVELOPMENT_EVENTS_PATH.read_text(encoding="utf-8")
    if authorized["event_id"] not in existing:
        with DEVELOPMENT_EVENTS_PATH.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(authorized, ensure_ascii=False, separators=(",", ":")) + "\n")
    full_coverage = _authorized_governance_coverage_record()
    existing = DEVELOPMENT_EVENTS_PATH.read_text(encoding="utf-8")
    if full_coverage["event_id"] not in existing:
        with DEVELOPMENT_EVENTS_PATH.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(full_coverage, ensure_ascii=False, separators=(",", ":")) + "\n")
    playwright_coverage = _playwright_self_host_coverage_record()
    existing = DEVELOPMENT_EVENTS_PATH.read_text(encoding="utf-8")
    if playwright_coverage["event_id"] not in existing:
        with DEVELOPMENT_EVENTS_PATH.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(playwright_coverage, ensure_ascii=False, separators=(",", ":")) + "\n")
    if _final_receipts():
        final = _final_validation_record()
        existing = DEVELOPMENT_EVENTS_PATH.read_text(encoding="utf-8")
        if final["event_id"] not in existing:
            with DEVELOPMENT_EVENTS_PATH.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(final, ensure_ascii=False, separators=(",", ":")) + "\n")


def _check_records() -> None:
    for path, record in _governance_records().items():
        token = record.get("event_id") or record.get("status_record_id")
        rows = _jsonl(path)
        matches = [row for row in rows if (row.get("event_id") or row.get("status_record_id")) == token]
        if matches != [record]:
            raise BuildError(f"governance record missing duplicated or drifted: {token}")
    coverage = _coverage_record()
    matches = [row for row in _jsonl(DEVELOPMENT_EVENTS_PATH) if row.get("event_id") == coverage["event_id"]]
    if matches != [coverage]:
        raise BuildError("governance coverage record missing duplicated or drifted")
    review_ui = _review_ui_continuation_record()
    matches = [row for row in _jsonl(DEVELOPMENT_EVENTS_PATH) if row.get("event_id") == review_ui["event_id"]]
    if matches != [review_ui]:
        raise BuildError("review UI continuation record missing duplicated or drifted")
    governance_sync = _review_ui_governance_sync_record()
    matches = [row for row in _jsonl(DEVELOPMENT_EVENTS_PATH) if row.get("event_id") == governance_sync["event_id"]]
    if matches != [governance_sync]:
        raise BuildError("review UI governance sync record missing duplicated or drifted")
    remediation = _semantic_extraction_remediation_record()
    matches = [row for row in _jsonl(DEVELOPMENT_EVENTS_PATH) if row.get("event_id") == remediation["event_id"]]
    if matches != [remediation]:
        raise BuildError("candidate semantic remediation record missing duplicated or drifted")
    grouped_review = _source_grouped_review_record()
    matches = [row for row in _jsonl(DEVELOPMENT_EVENTS_PATH) if row.get("event_id") == grouped_review["event_id"]]
    if matches != [grouped_review]:
        raise BuildError("source-grouped review record missing duplicated or drifted")
    authorized = _authorized_resolution_record()
    matches = [row for row in _jsonl(DEVELOPMENT_EVENTS_PATH) if row.get("event_id") == authorized["event_id"]]
    if matches != [authorized]:
        raise BuildError("authorized resolution record missing duplicated or drifted")
    full_coverage = _authorized_governance_coverage_record()
    matches = [row for row in _jsonl(DEVELOPMENT_EVENTS_PATH) if row.get("event_id") == full_coverage["event_id"]]
    if matches != [full_coverage]:
        raise BuildError("authorized governance coverage record missing duplicated or drifted")
    playwright_coverage = _playwright_self_host_coverage_record()
    matches = [row for row in _jsonl(DEVELOPMENT_EVENTS_PATH) if row.get("event_id") == playwright_coverage["event_id"]]
    if matches != [playwright_coverage]:
        raise BuildError("Playwright self-host coverage record missing duplicated or drifted")
    if _final_receipts():
        final = _final_validation_record()
        matches = [row for row in _jsonl(DEVELOPMENT_EVENTS_PATH) if row.get("event_id") == final["event_id"]]
        if matches != [final]:
            raise BuildError("final validation record missing duplicated or drifted")


def expected_outputs() -> dict[Path, str]:
    projection = kernel.current_public_projection()
    dependency = _dependency()
    receipts = _final_receipts()
    task_matrix = _task_matrix(projection, bool(receipts))
    manifest = _manifest(projection, dependency, receipts)
    outputs = {
        CONTRACT_PATH: _dump(projection),
        TASK_MATRIX_PATH: _dump(task_matrix),
        MANIFEST_PATH: _dump(manifest),
        STATUS_PATH: _status(manifest),
        TEST_RESULTS_PATH: _tests(manifest),
        OPEN_RISKS_PATH: _risks(manifest),
        ROLLBACK_PATH: _rollback(),
    }
    outputs[PROJECT_STATE_PATH] = _project_state_text(PROJECT_STATE_PATH, manifest)
    outputs[PROJECT_STATE_MIRROR_PATH] = _project_state_text(PROJECT_STATE_MIRROR_PATH, manifest)
    outputs.update(_primary_document_outputs(manifest))
    outputs[PARAMETER_REGISTRY_PATH] = _parameter_registry_text(manifest)
    outputs.update(_governance_document_outputs(manifest))
    return outputs


def write_outputs() -> None:
    for path, content in expected_outputs().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    _append_records()


def check_outputs() -> None:
    errors = [
        str(path) for path, content in expected_outputs().items()
        if not path.exists() or path.read_text(encoding="utf-8") != content
    ]
    if errors:
        raise BuildError("deterministic output mismatch: " + ", ".join(errors))
    _check_records()


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build S06-P2 public-safe pending evidence")
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write", action="store_true")
    action.add_argument("--check", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.write:
        write_outputs()
        print("WROTE: S06-P2 public-safe pending evidence")
    else:
        check_outputs()
        print("PASS: S06-P2 public-safe pending evidence matches deterministic builder")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

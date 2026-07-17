#!/usr/bin/env python3
"""生成 KMFA v1.5 S13-P3 的确定性公开安全证据。"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from KMFA.tools import v015_s13_p3_action_priority as kernel


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "KMFA"
PHASE_BASE_COMMIT = "ac1c5bc9edbca8114b5a79fa0e718f7f7a0b9c8d"
TASKPACK_SHA256 = "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"

EXPECTED_VALIDATION_NAMES = (
    "python_compile",
    "focused_kernel_tests",
    "focused_artifact_tests",
    "focused_governance_tests",
    "s13_p1_p2_regression",
    "s13_p2_dependency",
    "action_priority_self_check",
    "deterministic_evidence",
    "pre_final_phase_checker",
    "roadmap_governance_tests",
    "roadmap_sync_pending",
    "metadata_protocol",
    "project_governance",
    "lean_governance",
    "governance_sync",
    "no_float_money",
    "no_omission",
    "taskpack_source",
    "public_boundary",
    "git_diff_check",
)
EXPECTED_VALIDATION_COUNT = len(EXPECTED_VALIDATION_NAMES)

OUTPUT_ROOT = PROJECT_ROOT / "stage_artifacts" / kernel.RUN_PHASE_ID
MACHINE_ROOT = OUTPUT_ROOT / "machine"
HUMAN_ROOT = OUTPUT_ROOT / "human"

MANIFEST_PATH = MACHINE_ROOT / "s13_p3_action_priority_manifest.json"
SOURCE_CONTRACT_PATH = MACHINE_ROOT / "source_contract_public_safe.json"
TASK_MATRIX_PATH = MACHINE_ROOT / "task_acceptance_matrix_public_safe.json"
VERIFICATION_PATH = MACHINE_ROOT / "action_priority_verification_public_safe.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "validation_results.jsonl"

RANKING_CONTRACT_PATH = PROJECT_ROOT / "metadata/quality/v015_s13_p3_action_ranking_contract_public_safe.json"
FOCUS_CONTRACT_PATH = PROJECT_ROOT / "metadata/quality/v015_s13_p3_focus_item_contract_public_safe.json"
REVIEW_CONTRACT_PATH = PROJECT_ROOT / "metadata/quality/v015_s13_p3_recommendation_review_contract_public_safe.json"

IMPLEMENTATION_REPORT_PATH = HUMAN_ROOT / "implementation_report_zh.md"
ACTION_GUIDE_PATH = HUMAN_ROOT / "action_priority_guide_zh.md"
TEST_RESULTS_PATH = HUMAN_ROOT / "test_results_zh.md"
RISKS_ROLLBACK_PATH = HUMAN_ROOT / "risks_and_rollback_zh.md"

DEPENDENCY_MANIFEST_PATH = PROJECT_ROOT / "stage_artifacts/V015_S13_P2_BUSINESS_HEALTH_MODEL/machine/s13_p2_business_health_model_manifest.json"
DEPENDENCY_RECEIPTS_PATH = PROJECT_ROOT / "stage_artifacts/V015_S13_P2_BUSINESS_HEALTH_MODEL/machine/validation_results.jsonl"


class BuildError(RuntimeError):
    pass


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def dependency() -> dict[str, Any]:
    manifest = json.loads(DEPENDENCY_MANIFEST_PATH.read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in DEPENDENCY_RECEIPTS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    expected = {
        "run_phase_id": "V015_S13_P2_BUSINESS_HEALTH_MODEL",
        "phase_acceptance_status": "PASSED",
        "evidence_validation_status": "PASS",
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": 67,
        "decision": "CONTINUE_TO_S13_P3_ONLY",
        "s13_p2_started": True,
        "s13_p2_acceptance_status": "PASSED",
        "s13_p3_entry_allowed": True,
        "s13_p3_started": False,
        "validation_receipt_count": 20,
    }
    mismatches = [key for key, value in expected.items() if manifest.get(key) != value]
    if mismatches:
        raise BuildError("S13-P2 dependency mismatch: " + ", ".join(mismatches))
    if len(rows) != 20 or any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in rows):
        raise BuildError("S13-P2 receipts are not exactly 20 PASS records")
    if {row.get("validation_head") for row in rows} != {manifest.get("validation_head")}:
        raise BuildError("S13-P2 validation head mismatch")
    if {row.get("validation_run_id") for row in rows} != {manifest.get("validation_run_id")}:
        raise BuildError("S13-P2 validation run mismatch")
    head = str(manifest.get("validation_head") or "")
    if not re.fullmatch(r"[0-9a-f]{40}", head):
        raise BuildError("S13-P2 validation head invalid")
    if subprocess.run(["git", "merge-base", "--is-ancestor", head, "HEAD"], cwd=REPO_ROOT, check=False).returncode:
        raise BuildError("S13-P2 validation head is not reachable")
    return {
        "acceptance_status": "PASSED",
        "validation_head": head,
        "validation_run_id": manifest["validation_run_id"],
        "validation_receipt_count": 20,
        "s13_p3_entry_allowed": True,
        "s13_p3_started": False,
    }


def receipts() -> list[dict[str, Any]]:
    if not VALIDATION_RESULTS_PATH.is_file():
        return []
    rows = [json.loads(line) for line in VALIDATION_RESULTS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    if rows and [row.get("name") for row in rows] != list(EXPECTED_VALIDATION_NAMES):
        raise BuildError("S13-P3 validation receipt order mismatch")
    return rows


def final_binding(rows: list[dict[str, Any]]) -> tuple[bool, str | None, str | None]:
    if not rows:
        return False, None, None
    run_ids = {row.get("validation_run_id") for row in rows}
    heads = {row.get("validation_head") for row in rows}
    final = (
        len(rows) == EXPECTED_VALIDATION_COUNT
        and all(row.get("status") == "PASS" and row.get("exit_code") == 0 for row in rows)
        and len(run_ids) == 1
        and len(heads) == 1
        and None not in run_ids
        and None not in heads
    )
    return final, next(iter(run_ids)) if final else None, next(iter(heads)) if final else None


def _source_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s13p3.source_contract.v1",
        "source_package_sha256": TASKPACK_SHA256,
        "tracked_source": "KMFA/taskpack/v1_5/roadmap_v2_0.json",
        "stage_id": "S13",
        "stage_name_zh": "经营指标、健康模型与行动优先级",
        "roadmap_phase_id": "S13-P3",
        "phase_name_zh": "行动优先级",
        "task_count": 3,
        "task_ids": ["S13P3T01", "S13P3T02", "S13P3T03"],
        "scope": ["六因素可解释行动排序", "三至五项本期重点事项", "建议采纳结果与校准复盘"],
        "stop_conditions": ["不得自动执行行动", "不得用大量卡片淹没用户", "无结果数据时标记未知"],
        "excluded": ["S13 整体复审", "真实业务动作", "事实改写", "参数自动校准", "正式报告", "GitHub 上传", "App 重装"],
    }


def _task_matrix(final: bool) -> dict[str, Any]:
    status = "PASSED" if final else "PENDING_FINAL_VALIDATION"
    result = "TASK_ACCEPTED" if final else "AWAITING_FINAL_VALIDATION"
    tasks = [
        {
            "task_id": "S13P3T01",
            "name_zh": "实现行动排序模型",
            "acceptance_zh": "影响、可信度、紧急度、投入、现金成本和执行风险六因素权重合计 10000，排序理由逐项可见，任何行动都不能自动执行。",
            "status": status,
            "current_result": result,
            "evidence_refs": [str(RANKING_CONTRACT_PATH.relative_to(REPO_ROOT)), str(VERIFICATION_PATH.relative_to(REPO_ROOT))],
        },
        {
            "task_id": "S13P3T02",
            "name_zh": "生成本期重点事项",
            "acceptance_zh": "项目、回款、资金、税务和数据候选经过门禁与可信度过滤后，首页最多只显示 3 至 5 项，不伪造不足项。",
            "status": status,
            "current_result": result,
            "evidence_refs": [str(FOCUS_CONTRACT_PATH.relative_to(REPO_ROOT)), str(VERIFICATION_PATH.relative_to(REPO_ROOT))],
        },
        {
            "task_id": "S13P3T03",
            "name_zh": "建立建议复盘",
            "acceptance_zh": "建议、采纳、结果与校准分开记录；无结果时明确为未知，未验证建议写入事实和自动改参数次数均为 0。",
            "status": status,
            "current_result": result,
            "evidence_refs": [str(REVIEW_CONTRACT_PATH.relative_to(REPO_ROOT)), str(VERIFICATION_PATH.relative_to(REPO_ROOT))],
        },
    ]
    return {
        "schema_version": "kmfa.v015.s13p3.task_acceptance_matrix.v1",
        "phase_id": kernel.RUN_PHASE_ID,
        "task_count": 3,
        "task_accepted_count": 3 if final else 0,
        "phase_acceptance_status": status,
        "tasks": tasks,
    }


def _manifest(final: bool, rows: list[dict[str, Any]], run_id: str | None, head: str | None, verification: dict[str, Any]) -> dict[str, Any]:
    acceptance = "PASSED" if final else "PENDING_FINAL_VALIDATION"
    return {
        "schema_version": "kmfa.v015.s13p3.action_priority_manifest.v1",
        "project_id": "KMFA",
        "target_release": "v1.5",
        "version": kernel.VERSION,
        "run_phase_id": kernel.RUN_PHASE_ID,
        "roadmap_phase_id": kernel.ROADMAP_PHASE_ID,
        "task_id": kernel.TASK_ID,
        "acceptance_id": kernel.ACCEPTANCE_ID,
        "phase_base_commit": PHASE_BASE_COMMIT,
        "phase_execution_status": "EXECUTION_COMPLETE",
        "phase_acceptance_status": acceptance,
        "evidence_validation_status": "PASS" if final else "PENDING",
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": 100,
        "stage_phase_pass_count": 3 if final else 2,
        "stage_task_accepted_count": 9 if final else 6,
        "phase_task_count": 3,
        "phase_task_accepted_count": 3 if final else 0,
        "overall_accepted_phase_count": 37 if final else 36,
        "overall_taskpack_phase_count": 72,
        "decision": "GO_TO_S13_STAGE_REVIEW_ONLY" if final else "REMAIN_IN_S13_P3_FINAL_VALIDATION",
        "ranking_factor_count": len(kernel.RANKING_FACTORS),
        "ranking_weight_total_bps": verification["ranking_contract_summary"]["weight_total_bps"],
        "action_domain_count": len(kernel.ACTION_DOMAINS),
        "candidate_state_count": len(kernel.CANDIDATE_STATES),
        "focus_item_count": verification["sample_focus_selection"]["focus_item_count"],
        "focus_min_items": kernel.FOCUS_MIN_ITEMS,
        "focus_max_items": kernel.FOCUS_MAX_ITEMS,
        "focus_domain_cap": kernel.FOCUS_DOMAIN_CAP,
        "review_decision_count": len(kernel.REVIEW_DECISIONS),
        "outcome_state_count": len(kernel.OUTCOME_STATES),
        "public_check_accounting": verification["accounting"],
        "action_priority_model_implemented": True,
        "synthetic_action_priority_computed": True,
        "real_business_action_priority_computed": False,
        "automatic_execution_count": verification["automatic_execution_count"],
        "recommendation_fact_write_count": verification["recommendation_fact_write_count"],
        "automatic_parameter_change_count": verification["automatic_parameter_change_count"],
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "live_source_read_count": 0,
        "real_business_action_count": 0,
        "s13_p1_started": True,
        "s13_p1_acceptance_status": "PASSED",
        "s13_p2_started": True,
        "s13_p2_acceptance_status": "PASSED",
        "s13_p3_started": True,
        "s13_p3_acceptance_status": acceptance,
        "s13_stage_review_entry_allowed": final,
        "s13_stage_review_started": False,
        "formal_report_generated": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "validation_receipt_count": len(rows),
        "validation_run_id": run_id,
        "validation_head": head,
    }


def _human_files(final: bool, verification: dict[str, Any]) -> dict[Path, str]:
    status = "已通过最终验收" if final else "实现完成，等待最终验收"
    test_status = "全部通过" if final else "能力自检已通过，最终验收记录待生成"
    accounting = verification["accounting"]
    return {
        IMPLEMENTATION_REPORT_PATH: "\n".join([
            "# S13-P3 行动优先级",
            "",
            f"状态：{status}。",
            "",
            "这一步只帮助人决定先处理什么，不会替人执行任何行动。",
            "",
            "- 排序同时考虑影响、可信度、紧急度、投入、现金成本和执行风险，每项贡献都能看见。",
            "- 硬门槛失败、资料过期或可信度不足的事项不会混入本期重点。",
            "- 公开模拟首页只保留 5 项；规则允许 3 至 5 项，候选不足时宁可少显示，也不伪造事项。",
            "- 建议、是否采纳、实际结果和校准建议分开记录；没有结果时明确显示未知。",
            "- 本轮没有读取原始财务资料，没有执行真实业务动作，也没有自动修改模型参数。",
        ]) + "\n",
        ACTION_GUIDE_PATH: "\n".join([
            "# 行动优先级怎么理解",
            "",
            "分数越高，只表示在当前公开规则和资料下更值得优先人工核对，不表示系统已经批准或执行。",
            "",
            "首页只突出 3 至 5 件事。每件事都说明为什么排在这里、依据来自哪里、由谁核对以及下一步是什么。",
            "",
            "建议复盘不会把建议写成事实。没有结果证据时，结果只能是“未知”；校准只生成提案，不会自动改权重。",
        ]) + "\n",
        TEST_RESULTS_PATH: "\n".join([
            "# S13-P3 测试结果",
            "",
            f"状态：{test_status}。",
            "",
            f"- 公开模拟自检：{accounting['passed']}/{accounting['total']} 通过。",
            "- 六项排序权重合计 10000，所有分数均限制在 0 至 10000。",
            "- 已验证硬门槛、过期资料和低可信事项不会进入本期重点。",
            "- 已验证首页最多 5 项，候选不足时不会伪造补足。",
            "- 已验证未知结果保持未知，建议写事实、自动执行、自动改参数均为 0。",
            "- 原始资料访问次数：0；真实来源读取次数：0；真实业务动作次数：0。",
        ]) + "\n",
        RISKS_ROLLBACK_PATH: "\n".join([
            "# 风险与回滚",
            "",
            "- 当前排序只证明公开模拟规则可解释，不代表真实企业必须执行这些行动。",
            "- 权重和阈值未来只能在受控证据下形成新版本，不能直接覆盖历史或自动应用。",
            "- 首页数量限制不能替代硬门槛；资料不足时允许少于 3 项，禁止为了凑数制造建议。",
            "- 回滚只移除本阶段代码、测试、公开规则和证据，不触碰原始资料、S13-P1/P2、远端仓库或已安装 App。",
        ]) + "\n",
    }


def expected_outputs() -> dict[Path, str]:
    dependency()
    rows = receipts()
    final, run_id, head = final_binding(rows)
    verification = kernel.public_verification()
    if verification["accounting"] != {"total": 88, "passed": 88, "failed": 0} or verification["failed_checks"]:
        raise BuildError("S13-P3 public verification failed")
    outputs = {
        RANKING_CONTRACT_PATH: _json({
            "schema_version": "kmfa.v015.s13p3.action_ranking_contract.v1",
            "factors": kernel.ranking_contract(),
            "summary": kernel.validate_ranking_contract(kernel.ranking_contract()),
            "advisory_only": True,
            "automatic_execution_allowed": False,
            "sample_ranked_actions": verification["sample_ranked_actions"],
        }),
        FOCUS_CONTRACT_PATH: _json({
            "schema_version": "kmfa.v015.s13p3.focus_item_contract.v1",
            "domains": list(kernel.ACTION_DOMAINS),
            "focus_min_items": kernel.FOCUS_MIN_ITEMS,
            "focus_max_items": kernel.FOCUS_MAX_ITEMS,
            "domain_cap": kernel.FOCUS_DOMAIN_CAP,
            "candidate_flooding_allowed": False,
            "sample_focus_selection": verification["sample_focus_selection"],
        }),
        REVIEW_CONTRACT_PATH: _json({
            "schema_version": "kmfa.v015.s13p3.recommendation_review_contract.v1",
            "review_decisions": list(kernel.REVIEW_DECISIONS),
            "outcome_states": list(kernel.OUTCOME_STATES),
            "unknown_without_result_required": True,
            "recommendation_written_as_fact": False,
            "automatic_parameter_change_allowed": False,
            "sample_unknown_review": verification["sample_unknown_review"],
            "sample_calibration_proposal": verification["sample_calibration_proposal"],
        }),
        SOURCE_CONTRACT_PATH: _json(_source_contract()),
        TASK_MATRIX_PATH: _json(_task_matrix(final)),
        VERIFICATION_PATH: _json(verification),
        MANIFEST_PATH: _json(_manifest(final, rows, run_id, head, verification)),
    }
    outputs.update(_human_files(final, verification))
    return outputs


def write_outputs() -> None:
    for path, content in expected_outputs().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    VALIDATION_RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not VALIDATION_RESULTS_PATH.exists():
        VALIDATION_RESULTS_PATH.touch()


def check_outputs() -> None:
    mismatches = []
    for path, content in expected_outputs().items():
        if not path.is_file() or path.read_text(encoding="utf-8") != content:
            mismatches.append(str(path.relative_to(REPO_ROOT)))
    if mismatches:
        raise BuildError("S13-P3 deterministic output mismatch: " + ", ".join(mismatches))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        check_outputs() if args.check else write_outputs()
    except (OSError, ValueError, KeyError, json.JSONDecodeError, BuildError) as error:
        print(f"FAIL: {error}")
        return 1
    print("PASS: S13-P3 deterministic public-safe evidence" if args.check else "WROTE: S13-P3 deterministic public-safe evidence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

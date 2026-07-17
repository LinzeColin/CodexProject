#!/usr/bin/env python3
"""生成 KMFA v1.5 S15 整体复审的确定性公开证据。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
from pathlib import Path
from typing import Any

from KMFA.tools import v015_s15_stage_review_contract as contract


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = PROJECT_ROOT / "stage_artifacts/V015_S15_STAGE_REVIEW"
MACHINE_ROOT = OUTPUT_ROOT / "machine"
HUMAN_ROOT = OUTPUT_ROOT / "human"
EXPORT_ROOT = OUTPUT_ROOT / "exports"
HTML_PATH = EXPORT_ROOT / "html/kmfa_s15_integrated_review.html"
DESKTOP_SCREENSHOT_PATH = EXPORT_ROOT / "screenshots/kmfa_s15_review_desktop.png"
RESTRICTED_USER_SCREENSHOT_PATH = EXPORT_ROOT / "screenshots/kmfa_s15_review_restricted_user.png"
TABLET_SCREENSHOT_PATH = EXPORT_ROOT / "screenshots/kmfa_s15_review_tablet.png"
MOBILE_SCREENSHOT_PATH = EXPORT_ROOT / "screenshots/kmfa_s15_review_mobile.png"
SCREENSHOT_PATHS = (
    DESKTOP_SCREENSHOT_PATH,
    RESTRICTED_USER_SCREENSHOT_PATH,
    TABLET_SCREENSHOT_PATH,
    MOBILE_SCREENSHOT_PATH,
)
MANIFEST_PATH = MACHINE_ROOT / "s15_stage_review_manifest.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "validation_results.jsonl"

RUN_PHASE_ID = contract.RUN_PHASE_ID
TASK_ID = contract.TASK_ID
ACCEPTANCE_ID = contract.ACCEPTANCE_ID
VERSION = contract.VERSION
REVIEW_BASE_COMMIT = contract.REVIEW_BASE_COMMIT
TASKPACK_SHA256 = "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"

PREDECESSORS = (
    (
        "S15-P1",
        PROJECT_ROOT / "stage_artifacts/V015_S15_P1_APP_SHELL/machine/s15_p1_app_shell_manifest.json",
        PROJECT_ROOT / "stage_artifacts/V015_S15_P1_APP_SHELL/machine/validation_results.jsonl",
        20,
        8,
    ),
    (
        "S15-P2",
        PROJECT_ROOT / "stage_artifacts/V015_S15_P2_IDENTITY_ROLES/machine/s15_p2_identity_roles_manifest.json",
        PROJECT_ROOT / "stage_artifacts/V015_S15_P2_IDENTITY_ROLES/machine/validation_results.jsonl",
        20,
        12,
    ),
    (
        "S15-P3",
        PROJECT_ROOT / "stage_artifacts/V015_S15_P3_APP_EXPERIENCE/machine/s15_p3_app_experience_manifest.json",
        PROJECT_ROOT / "stage_artifacts/V015_S15_P3_APP_EXPERIENCE/machine/validation_results.jsonl",
        20,
        16,
    ),
)

EXPECTED_VALIDATION_NAMES = (
    "python_compile",
    "focused_contract_tests",
    "focused_review_tests",
    "focused_browser_tests",
    "focused_governance_tests",
    "s15_p1_dependency",
    "s15_p2_dependency",
    "s15_p3_dependency",
    "s15_p1_kernel_regression",
    "s15_p2_kernel_regression",
    "s15_p3_kernel_regression",
    "s15_p1_runtime_regression",
    "s15_p2_runtime_regression",
    "s15_p3_runtime_regression",
    "integrated_review_consistency",
    "builder_exact_rebuild",
    "stage_checker_pre_final",
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


class BuildError(RuntimeError):
    """S15 整体复审证据无法确定性生成。"""


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _csv_bytes(rows: list[dict[str, str]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not all(isinstance(row, dict) for row in rows):
        raise BuildError(f"JSONL rows must be objects: {path}")
    return rows


def source_contract() -> dict[str, Any]:
    source_manifest = json.loads(
        (PROJECT_ROOT / "taskpack/v1_5/source_manifest.json").read_text(encoding="utf-8")
    )
    roadmap = json.loads(
        (PROJECT_ROOT / "taskpack/v1_5/roadmap_v2_0.json").read_text(encoding="utf-8")
    )
    stage = next((row for row in roadmap.get("stages", []) if row.get("id") == "S15"), None)
    package = Path.home() / "Downloads/KMFA_ChatGPT_Stage3_Codex_TaskPack_Roadmap_v2_0_UIUX_FULL_REBUILD.zip"
    integrity = (
        package.is_file()
        and _sha256(package) == "sha256:" + TASKPACK_SHA256
        and source_manifest.get("source_package_sha256") == TASKPACK_SHA256
        and (source_manifest.get("stage_count"), source_manifest.get("phase_count"), source_manifest.get("task_count")) == (24, 72, 216)
        and (stage or {}).get("name") == "应用外壳、角色权限与多主体上下文"
        and [row.get("id") for row in (stage or {}).get("phases", [])] == ["P1", "P2", "P3"]
    )
    return {
        "schema_version": "kmfa.v015.s15.stage-review-source-contract.v1",
        "source_package_sha256": TASKPACK_SHA256,
        "tracked_source": "KMFA/taskpack/v1_5/roadmap_v2_0.json",
        "stage_id": "S15",
        "stage_name_zh": "应用外壳、角色权限与多主体上下文",
        "phase_count": 3,
        "task_count": 9,
        "review_overlay_counted_as_taskpack_phase": False,
        "source_integrity_status": "PASS" if integrity else "FAIL",
        "scope_zh": "只复审并修复 S15-P1/P2/P3 的路由、身份、公司、权限、搜索、通知、偏好、键盘和手机连接。",
        "excluded_zh": ["真实资料", "真实账号", "真实业务动作", "S16", "GitHub 上传", "App 重装"],
    }


def phase_evidence() -> dict[str, Any]:
    phases = []
    for phase_id, manifest_path, receipts_path, receipt_count, public_count in PREDECESSORS:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        rows = _jsonl(receipts_path)
        if (
            manifest.get("phase_acceptance_status") != "PASSED"
            or manifest.get("evidence_validation_status") != "PASS"
            or manifest.get("phase_task_accepted_count") != 3
            or manifest.get("validation_receipt_count") != receipt_count
            or len(rows) != receipt_count
            or any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in rows)
            or {row.get("validation_head") for row in rows} != {manifest.get("validation_head")}
            or {row.get("validation_run_id") for row in rows} != {manifest.get("validation_run_id")}
            or manifest.get("public_check_total") != public_count
            or manifest.get("public_check_failed_count") != 0
        ):
            raise BuildError(f"{phase_id} predecessor acceptance drift")
        phases.append(
            {
                "roadmap_phase_id": phase_id,
                "run_phase_id": manifest["run_phase_id"],
                "task_count": 3,
                "task_accepted_count": 3,
                "acceptance_status": "PASSED",
                "public_check_count": public_count,
                "validation_receipt_count": receipt_count,
                "validation_head": manifest["validation_head"],
                "validation_run_id": manifest["validation_run_id"],
                "manifest_sha256": _sha256(manifest_path),
                "receipts_sha256": _sha256(receipts_path),
            }
        )
    return {
        "schema_version": "kmfa.v015.s15.stage-review-phase-evidence.v1",
        "phases": phases,
        "accounting": {
            "phase_count": 3,
            "phase_passed_count": 3,
            "task_count": 9,
            "task_accepted_count": 9,
            "predecessor_public_check_count": 36,
            "predecessor_receipt_count": 60,
        },
    }


def cross_phase_contracts() -> dict[str, Any]:
    review = contract.build_integrated_review()
    rows = review["integration_bindings"]
    failed = sum(row["status"] != "PASS" for row in rows)
    return {
        "schema_version": "kmfa.v015.s15.cross-phase-contracts.v1",
        "accounting": {
            "total": len(rows),
            "passed": len(rows) - failed,
            "failed": failed,
            "blocking_failed": failed,
        },
        "contracts": rows,
        "integrated_review_fingerprint": review["review_fingerprint"],
    }


def findings() -> list[dict[str, str]]:
    values = (
        ("S15REV-F001", "HIGH", "快速切换角色或公司时，较早返回的身份、搜索或通知结果可能覆盖新身份页面。", "三个部分各自处理异步请求，缺少共同的身份版本门禁。", "为身份和体验请求增加序号及身份键；过期响应直接丢弃。"),
        ("S15REV-F002", "HIGH", "从多公司用户切到受限用户时，页面可能停留在该用户无权查看的公司。", "用户切换与全局公司上下文此前独立更新。", "切换用户时先校验公司授权；无权公司自动回到该用户首个授权公司。"),
        ("S15REV-F003", "MEDIUM", "三个体验标签只能点击或逐个 Tab，方向键、Home 和 End 不完整。", "标签外观完成，但没有实现标准键盘标签模型。", "补齐左右方向键、Home、End、焦点和选中状态同步。"),
        ("S15REV-F004", "MEDIUM", "手机和触控设备上的部分按钮与说明文字偏小。", "桌面密度样式直接缩放到触控环境。", "粗指针点击区统一不少于 44 像素，手机辅助文字提升到 14 像素。"),
    )
    return [
        {
            "finding_id": finding_id,
            "severity": severity,
            "finding_zh": finding,
            "root_cause_zh": cause,
            "fix_zh": fix,
            "evidence_ref": "KMFA/stage_artifacts/V015_S15_STAGE_REVIEW/machine/integrated_review_public_safe.json",
            "validation_ref": "KMFA/tests/test_v015_s15_stage_review_browser.py",
            "status": "FIXED_VALIDATED",
            "blocks_stage_acceptance": "false",
        }
        for finding_id, severity, finding, cause, fix in values
    ]


def risks() -> list[dict[str, str]]:
    values = (
        ("001", "当前身份和用户仍为公开演示，不是生产登录系统。", "LATER_AUTHORIZED_IDENTITY_INTEGRATION"),
        ("002", "搜索目录和通知仍为公开合成内容。", "LATER_PRODUCTION_SEARCH_AND_NOTIFICATION"),
        ("003", "偏好当前只在 localhost 进程内保存。", "LATER_PERSISTENT_USER_PROFILE"),
        ("004", "本轮浏览器覆盖 Chrome 桌面、平板和手机模拟，未替代真实设备验证。", "FINAL_CROSS_DEVICE_ACCEPTANCE"),
        ("005", "GitHub 与 App 一致性只在 v1.5 最终总验收处理。", "FINAL_OVERALL_GITHUB_AND_APP_PARITY_GATE"),
    )
    return [
        {
            "risk_id": f"RISK-KMFA-V015-S15-{number}",
            "risk": risk,
            "route": route,
            "status": "ROUTED_RESIDUAL",
            "plan_complete": "true",
            "blocks_s15_stage_acceptance": "false",
        }
        for number, risk, route in values
    ]


def browser_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s15.stage-review-browser-contract.v1",
        "browser": "Chromium headless",
        "page_kind": "LOCALHOST_PUBLIC_SAFE_INTEGRATED_SPA",
        "required_viewports": [
            {"id": "desktop", "width": 1440, "height": 1000},
            {"id": "tablet_touch", "width": 820, "height": 1180},
            {"id": "mobile_touch", "width": 390, "height": 844},
        ],
        "required_flows": [
            "三部分同页连接",
            "过期身份与敏感搜索响应丢弃",
            "受限用户公司自动收敛",
            "键盘标签模型",
            "搜索与通知跳转保留上下文",
            "用户偏好切换隔离",
            "平板无横向溢出",
            "手机触控尺寸和完整流程",
        ],
        "external_network_request_count_expected": 0,
        "page_error_count_expected": 0,
        "screenshot_paths": [str(path.relative_to(REPO_ROOT)) for path in SCREENSHOT_PATHS],
    }


def receipts() -> list[dict[str, Any]]:
    rows = _jsonl(VALIDATION_RESULTS_PATH)
    if rows and [row.get("name") for row in rows] != list(EXPECTED_VALIDATION_NAMES):
        raise BuildError("S15 review validation receipt order drift")
    return rows


def final_binding(rows: list[dict[str, Any]]) -> tuple[bool, str | None, str | None]:
    if not rows:
        return False, None, None
    run_ids = {row.get("validation_run_id") for row in rows}
    heads = {row.get("validation_head") for row in rows}
    final = (
        len(rows) == len(EXPECTED_VALIDATION_NAMES)
        and all(row.get("status") == "PASS" and row.get("exit_code") == 0 for row in rows)
        and len(run_ids) == len(heads) == 1
        and None not in run_ids
        and None not in heads
    )
    return final, next(iter(run_ids)) if final else None, next(iter(heads)) if final else None


def manifest(rows: list[dict[str, Any]]) -> dict[str, Any]:
    final, run_id, head = final_binding(rows)
    verification = contract.public_verification()
    summary = contract.validate_integrated_review(verification["integrated_review"])
    return {
        "schema_version": "kmfa.v015.s15_stage_review.manifest.v1",
        "project_id": "KMFA",
        "target_release": "v1.5",
        "stage_id": "S15",
        "run_phase_id": RUN_PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "version": VERSION,
        "review_base_commit": REVIEW_BASE_COMMIT,
        "counted_as_taskpack_phase": False,
        "counted_as_taskpack_task": False,
        "review_execution_status": "COMPLETED" if final else "EXECUTION_COMPLETE",
        "phase_execution_status": "EXECUTION_COMPLETE",
        "phase_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "evidence_validation_status": "PASS" if final else "PENDING",
        "stage_lifecycle_status": "COMPLETED" if final else "IN_PROGRESS",
        "stage_acceptance_status": "PASSED" if final else "PENDING",
        "stage_execution_percentage": 100,
        "decision": "GO_TO_S16_P1_ONLY" if final else "REMAIN_IN_S15_STAGE_REVIEW",
        "phase_accounting": phase_evidence()["accounting"],
        "cross_phase_accounting": cross_phase_contracts()["accounting"],
        "live_check_accounting": verification["accounting"],
        "review_findings": {"total": 4, "fixed_validated": 4, "open": 0, "blocking_open": 0},
        "open_risks": {"total": 5, "routed": 5, "plan_gap_count": 0, "blocking": 0},
        **summary,
        "browser_viewport_count": 3,
        "browser_flow_count": 8,
        "visual_evidence_count": len(SCREENSHOT_PATHS),
        "overall_accepted_phase_count": 43,
        "overall_taskpack_phase_count": 72,
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "live_source_read_count": 0,
        "external_network_request_count": 0,
        "real_identity_count": 0,
        "real_business_action_count": 0,
        "formal_report_generated": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "s15_p1_acceptance_status": "PASSED",
        "s15_p2_acceptance_status": "PASSED",
        "s15_p3_acceptance_status": "PASSED",
        "s15_stage_review_started": True,
        "s15_stage_review_performed": final,
        "s15_stage_review_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "s16_entry_allowed": final,
        "s16_p1_entry_allowed": final,
        "s16_p1_started": False,
        "s16_p2_plus_entry_allowed": False,
        "product_implementation_allowed": final,
        "validation_run_id": run_id,
        "validation_head": head,
        "validation_receipt_count": len(rows) if final else 0,
        "validation_pass_count": len(rows) if final else 0,
        "validation_failed_count": 0,
    }


def _human_outputs(final: bool) -> dict[Path, bytes]:
    status = "已通过最终验收" if final else "已完成复审与修复，等待最终验收"
    validation = f"{len(EXPECTED_VALIDATION_NAMES)}/{len(EXPECTED_VALIDATION_NAMES)} 项正式验收通过。" if final else f"{len(EXPECTED_VALIDATION_NAMES)} 项正式验收尚待执行。"
    return {
        HUMAN_ROOT / "stage15_review_report_zh.md": (
            "# KMFA v1.5 第 15 阶段整体复审\n\n"
            f"状态：{status}。\n\n"
            "- S15 三个部分、9 项任务、36 项原检查和 60 条前序验收记录均已复核。\n"
            "- 已修复 4 个衔接问题：过期响应、受限用户公司上下文、标签键盘操作、手机触控尺寸。\n"
            "- 41 项跨部分连接和 72 项实时检查全部通过；开放复审问题为 0。\n"
            "- 技术界面复审覆盖可访问性、性能、主题、响应式和反模式，综合分 92/100。\n"
            f"- {validation}\n"
            "- 本轮未读取真实资料、使用真实账号、执行真实业务、启动 S16、上传 GitHub 或重装 App。\n"
        ).encode("utf-8"),
        HUMAN_ROOT / "test_results_zh.md": (
            "# 测试结果\n\n"
            f"状态：{status}。\n\n"
            f"60 条前序验收、41 项跨部分连接、72 项实时检查、8 项浏览器流程、4 个已修复问题和 4 张浏览器画面保持一致；{validation}\n"
        ).encode("utf-8"),
        HUMAN_ROOT / "rollback_plan_zh.md": (
            "# 回滚方案\n\n只回滚本次 S15 整体复审新增的请求门禁、公司收敛、键盘/触控修复、测试、证据和状态登记；不改写 S15-P1/P2/P3 的原验收记录，不触碰真实资料、GitHub、App 或 S16。\n"
        ).encode("utf-8"),
        HUMAN_ROOT / "open_risks_zh.md": (
            "# 开放风险\n\n5 项剩余风险已有后续路径：生产身份、生产搜索与通知、持久偏好、真实设备验收，以及最终 GitHub/App 一致性。S15 通过不代表这些动作已经执行。\n"
        ).encode("utf-8"),
    }


def expected_outputs() -> dict[Path, bytes]:
    source = source_contract()
    if source["source_integrity_status"] != "PASS":
        raise BuildError("S15 TaskPack source integrity failed")
    predecessor = phase_evidence()
    cross = cross_phase_contracts()
    verification = contract.public_verification()
    if cross["accounting"]["failed"] or verification["accounting"]["failed"]:
        raise BuildError("S15 review verification failed")
    rows = receipts()
    final, _, _ = final_binding(rows)
    outputs = {
        MACHINE_ROOT / "source_contract_public_safe.json": _json_bytes(source),
        MACHINE_ROOT / "phase_evidence_public_safe.json": _json_bytes(predecessor),
        MACHINE_ROOT / "integrated_review_public_safe.json": _json_bytes(verification["integrated_review"]),
        MACHINE_ROOT / "cross_phase_contracts_public_safe.json": _json_bytes(cross),
        MACHINE_ROOT / "cross_phase_verification_public_safe.json": _json_bytes(verification),
        MACHINE_ROOT / "design_audit_public_safe.json": _json_bytes(contract.design_audit()),
        MACHINE_ROOT / "browser_acceptance_contract_public_safe.json": _json_bytes(browser_contract()),
        MACHINE_ROOT / "stage15_review_findings_public_safe.csv": _csv_bytes(findings()),
        MACHINE_ROOT / "open_risk_register_public_safe.csv": _csv_bytes(risks()),
        MANIFEST_PATH: _json_bytes(manifest(rows)),
        HTML_PATH: contract.render_html().encode("utf-8"),
    }
    outputs.update(_human_outputs(final))
    return outputs


def write_outputs() -> None:
    for path, content in expected_outputs().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    if not VALIDATION_RESULTS_PATH.exists():
        VALIDATION_RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        VALIDATION_RESULTS_PATH.write_text("", encoding="utf-8")


def check_outputs() -> list[str]:
    mismatches = [
        str(path.relative_to(REPO_ROOT))
        for path, content in expected_outputs().items()
        if not path.is_file() or path.read_bytes() != content
    ]
    if not VALIDATION_RESULTS_PATH.is_file():
        mismatches.append(str(VALIDATION_RESULTS_PATH.relative_to(REPO_ROOT)))
    missing = [str(path.relative_to(REPO_ROOT)) for path in SCREENSHOT_PATHS if not path.is_file()]
    return mismatches + missing


def main() -> int:
    parser = argparse.ArgumentParser(description="生成或检查 KMFA v1.5 S15 整体复审证据")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        if args.check:
            mismatches = check_outputs()
            if mismatches:
                raise BuildError("证据需要重新生成：" + ", ".join(mismatches))
        else:
            write_outputs()
    except (OSError, ValueError, KeyError, json.JSONDecodeError, BuildError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print("PASS: S15 stage review evidence " + ("is exact" if args.check else "written"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

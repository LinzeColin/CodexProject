#!/usr/bin/env python3
"""严格检查 KMFA v1.5 S19-P2 政策资格。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import struct
import subprocess
import sys
from pathlib import Path
from typing import Any

from KMFA.tools import build_v015_s19_p2_policy_eligibility as builder


REPO_ROOT = builder.REPO_ROOT

EXPECTED_VALIDATIONS = (
    ("phase_contract", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -c \"import ast,pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8')) for p in ('KMFA/tools/v015_s19_p2_policy_eligibility.py','KMFA/tools/run_v015_s19_p2_policy_eligibility.py','KMFA/tools/build_v015_s19_p2_policy_eligibility.py','KMFA/tools/check_v015_s19_p2_policy_eligibility.py','KMFA/tools/run_v015_s19_p2_browser_tests.py','KMFA/tools/run_v015_s19_p2_validations.py','KMFA/tools/v015_roadmap_governance_sync.py')]\""),
    ("focused_unit_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s19_p2_policy_eligibility"),
    ("focused_runtime_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s19_p2_policy_eligibility_runtime"),
    ("focused_browser_tests", "KMFA_PRESERVE_TRACKED_SCREENSHOTS=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/run_v015_s19_p2_browser_tests.py"),
    ("focused_artifact_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s19_p2_policy_eligibility_artifacts"),
    ("focused_governance_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s19_p2_policy_eligibility_governance"),
    ("s19_p1_dependency", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s19_p2_policy_eligibility.py --dependency-check"),
    ("deterministic_evidence", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/build_v015_s19_p2_policy_eligibility.py --check"),
    ("pre_final_phase_checker", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s19_p2_policy_eligibility.py --pre-final --skip-validation-receipts"),
    ("roadmap_governance_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_roadmap_governance_sync"),
    ("roadmap_sync_pending", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/v015_roadmap_governance_sync.py --check --validation-state S19_P2_PENDING_FINAL_VALIDATION"),
    ("metadata_protocol", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/metadata_protocol_check.py"),
    ("project_governance", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/validate_project_governance.py --project KMFA --mode required"),
    ("lean_governance", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/lean_governance.py validate --project KMFA --mode required"),
    ("governance_sync", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s19_p2_policy_eligibility.py --clean-governance-sync-check"),
    ("no_float_money", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_no_float_money.py"),
    ("no_omission", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/no_omission_check.py"),
    ("taskpack_source", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s19_p2_policy_eligibility.py --taskpack-source-check"),
    ("public_boundary", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s19_p2_policy_eligibility.py --public-boundary-check"),
    ("git_diff_check", f"git diff --check {builder.PHASE_BASE_COMMIT}..HEAD"),
)

if tuple(name for name, _ in EXPECTED_VALIDATIONS) != builder.EXPECTED_VALIDATION_NAMES:
    raise RuntimeError("builder/checker validation name drift")

ALLOWED_PHASE_PREFIXES = (
    "KMFA/AGENTS.md", "KMFA/CHANGELOG.md", "KMFA/HANDOFF.md", "KMFA/README.md",
    "KMFA/config/v015_s19_p2_policy_registry.json", "KMFA/docs/governance/",
    "KMFA/metadata/model_registry.yaml", "KMFA/metadata/project/project.yaml", "KMFA/metadata/stage_status.jsonl",
    "KMFA/stage_artifacts/V015_S19_P2_POLICY_ELIGIBILITY/", "KMFA/taskpack/v1_5/",
    "KMFA/tests/test_v015_roadmap_governance_sync.py", "KMFA/tests/test_v015_s19_p2_policy_eligibility.py",
    "KMFA/tests/test_v015_s19_p2_policy_eligibility_runtime.py", "KMFA/tests/test_v015_s19_p2_policy_eligibility_browser.py",
    "KMFA/tests/test_v015_s19_p2_policy_eligibility_artifacts.py", "KMFA/tests/test_v015_s19_p2_policy_eligibility_governance.py",
    "KMFA/tools/build_v015_s19_p2_policy_eligibility.py", "KMFA/tools/check_v015_s19_p2_policy_eligibility.py",
    "KMFA/tools/run_v015_s19_p2_browser_tests.py", "KMFA/tools/run_v015_s19_p2_policy_eligibility.py",
    "KMFA/tools/run_v015_s19_p2_validations.py", "KMFA/tools/v015_roadmap_governance_sync.py",
    "KMFA/tools/v015_s19_p2_policy_eligibility.py", "KMFA/功能清单.md", "KMFA/开发记录.md", "KMFA/模型参数文件.md",
)
PRESERVED_UNTRACKED_PREFIXES = (".github/workflows/kmfa-dual-plane.yml", "KMFA/machine/", "KMFA/文档/")


class CheckError(RuntimeError):
    """S19-P2 验收检查失败。"""


def _git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    if result.returncode:
        raise CheckError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _allowed(path: str) -> bool:
    return any(path == prefix or (prefix.endswith("/") and path.startswith(prefix)) for prefix in ALLOWED_PHASE_PREFIXES)


def _preserved(path: str) -> bool:
    return any(path == prefix or (prefix.endswith("/") and path.startswith(prefix)) for prefix in PRESERVED_UNTRACKED_PREFIXES)


def _check_scope() -> None:
    if subprocess.run(["git", "merge-base", "--is-ancestor", builder.PHASE_BASE_COMMIT, "HEAD"], cwd=REPO_ROOT, check=False).returncode:
        raise CheckError("S19-P2 base commit is not an ancestor of HEAD")
    changed: set[str] = set()
    for args in (
        ("-c", "core.quotepath=false", "diff", "--name-only", f"{builder.PHASE_BASE_COMMIT}..HEAD"),
        ("-c", "core.quotepath=false", "diff", "--name-only"),
        ("-c", "core.quotepath=false", "diff", "--cached", "--name-only"),
        ("-c", "core.quotepath=false", "ls-files", "--others", "--exclude-standard"),
    ):
        changed.update(line for line in _git(*args).splitlines() if line and not _preserved(line))
    unexpected = sorted(path for path in changed if not _allowed(path))
    if unexpected:
        raise CheckError("unexpected S19-P2 path(s): " + ", ".join(unexpected))


def _check_dependency() -> None:
    value = builder.dependency()
    expected = {"acceptance_status": "PASSED", "validation_receipt_count": 20, "overall_accepted_phase_count": 53, "s19_p2_entry_allowed": True, "s19_p2_started": False}
    mismatch = [key for key, expected_value in expected.items() if value.get(key) != expected_value]
    if mismatch:
        raise CheckError("S19-P1 依赖不完整：" + ", ".join(mismatch))


def _check_taskpack_source() -> None:
    package = Path.home() / "Downloads/KMFA_ChatGPT_Stage3_Codex_TaskPack_Roadmap_v2_0_UIUX_FULL_REBUILD.zip"
    if not package.is_file() or hashlib.sha256(package.read_bytes()).hexdigest() != builder.TASKPACK_SHA256:
        raise CheckError("TaskPack package missing or SHA-256 drifted")
    source_manifest = _json(builder.PROJECT_ROOT / "taskpack/v1_5/source_manifest.json")
    for key, value in {"source_package_sha256": builder.TASKPACK_SHA256, "stage_count": 24, "phase_count": 72, "task_count": 216}.items():
        if source_manifest.get(key) != value:
            raise CheckError(f"tracked TaskPack source manifest drifted: {key}")
    roadmap = _json(builder.PROJECT_ROOT / "taskpack/v1_5/roadmap_v2_0.json")
    stage = next((item for item in roadmap.get("stages", []) if item.get("id") == "S19"), None)
    phase = next((item for item in (stage or {}).get("phases", []) if item.get("id") == "P2"), None)
    expected = [
        ("T01", "建立政策规则登记", "记录科小、高新、专精特新/小巨人、研发加计扣除等规则版本和来源日期。", "政策注册表。", "规则需定期更新并标记有效性。", "规则时效检查。", "过期政策不得给确定结论。"),
        ("T02", "建立证据准备度", "知识产权、研发项目、人员、费用、高新收入和专项材料。", "准备度模型。", "只做缺口和风险提示。", "证据完整性测试。", "不得帮助伪造或包装材料。"),
        ("T03", "实现政策任务清单", "把缺失材料转为负责人、期限和证据位置。", "任务清单。", "与原始凭证和材料关联。", "任务流测试。", "无来源材料不得勾选完成。"),
    ]
    actual = [tuple(task.get(key) for key in ("id", "name", "action", "output", "acceptance", "evidence", "stop")) for task in (phase or {}).get("tasks", [])]
    if not stage or stage.get("name") != "税务、发票、政策资格与证据准备" or not phase or phase.get("name") != "政策资格" or actual != expected:
        raise CheckError("S19-P2 source contract drifted")


def _png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()[:24]
    if len(data) != 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        raise CheckError(f"PNG required: {path}")
    return struct.unpack(">II", data[16:24])


def _check_artifacts() -> None:
    builder.check_outputs()
    source = _json(builder.SOURCE_CONTRACT_PATH)
    registry = _json(builder.POLICY_REGISTRY_PATH)
    readiness = _json(builder.READINESS_PATH)
    tasks = _json(builder.TASK_CONTRACT_PATH)
    browser = _json(builder.BROWSER_CONTRACT_PATH)
    checks = _json(builder.PUBLIC_CHECKS_PATH)
    if source.get("roadmap_phase_id") != "S19-P2" or source.get("task_ids") != ["S19P2T01", "S19P2T02", "S19P2T03"] or source.get("eligibility_conclusion_allowed") is not False:
        raise CheckError("公开来源合同不完整")
    if (registry.get("policy_count"), registry.get("current_policy_count"), registry.get("blocked_policy_count"), registry.get("official_source_count"), registry.get("versioned_rule_count"), registry.get("review_metadata_count"), registry.get("expired_policy_deterministic_conclusion_count")) != (6, 5, 1, 6, 6, 6, 0):
        raise CheckError("政策注册表合同不完整")
    if (readiness.get("category_count"), readiness.get("evidence_item_count"), readiness.get("available_evidence_count"), readiness.get("missing_evidence_count"), readiness.get("review_evidence_count"), readiness.get("formal_eligibility_conclusion_count"), readiness.get("fabricated_evidence_count"), readiness.get("material_packaging_assistance_count")) != (6, 12, 7, 3, 2, 0, 0, 0):
        raise CheckError("证据准备度合同不完整")
    if (tasks.get("task_count"), tasks.get("owner_due_target_count"), tasks.get("missing_source_task_count"), tasks.get("source_review_task_count"), tasks.get("ready_task_count"), tasks.get("source_gate_enabled_count"), tasks.get("fabrication_or_packaging_allowed_count")) != (6, 6, 3, 2, 1, 6, 0):
        raise CheckError("政策任务合同不完整")
    if checks.get("check_count") != 80 or checks.get("pass_count") != 80 or checks.get("fail_count") != 0 or len(checks.get("checks", [])) != 80 or not all(row.get("status") == "PASS" for row in checks.get("checks", [])):
        raise CheckError("80 项公开检查未全部通过")
    if browser.get("browser_flow_count") != 8 or browser.get("visual_evidence_count") != 6 or browser.get("minimum_touch_target_px") != 44 or browser.get("horizontal_page_overflow_allowed") is not False or browser.get("external_network_request_count") != 0:
        raise CheckError("浏览器验收合同不完整")
    sizes = [_png_size(path) for path in builder.SCREENSHOT_PATHS]
    if any(width < 1000 or height < 700 for width, height in sizes[:5]):
        raise CheckError("电脑视觉证据尺寸漂移")
    if sizes[5][0] != 390 or sizes[5][1] < 844:
        raise CheckError("手机视觉证据尺寸漂移")


def _check_public_boundary() -> None:
    forbidden = (r"/Users/linzezhang/Downloads/KMFA_MetaData", r"BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY", r"(?i)(?:api[_-]?key|secret|token|password)\s*[:=]\s*['\"][^'\"]+")
    files = [path for path in builder.OUTPUT_ROOT.rglob("*") if path.is_file() and path.suffix.lower() in {".json", ".jsonl", ".html", ".csv", ".md"}]
    files.extend((builder.PROJECT_ROOT / "config/v015_s19_p2_policy_registry.json", builder.PROJECT_ROOT / "tools/v015_s19_p2_policy_eligibility.py", builder.PROJECT_ROOT / "tools/run_v015_s19_p2_policy_eligibility.py"))
    for path in files:
        text = path.read_text(encoding="utf-8")
        for pattern in forbidden:
            if re.search(pattern, text):
                raise CheckError(f"public boundary match in {path.relative_to(REPO_ROOT)}")
    value = _json(builder.MANIFEST_PATH)
    for key in ("raw_root_access_count", "live_source_read_count", "external_network_request_count", "real_identity_count", "credential_count", "real_business_action_count", "source_data_write_count", "fact_layer_write_count", "formal_eligibility_conclusion_count", "expired_policy_deterministic_conclusion_count", "fabricated_evidence_count", "material_packaging_assistance_count", "source_gate_bypass_count", "cross_company_leak_count"):
        if value.get(key) != 0:
            raise CheckError(f"public boundary count must remain zero: {key}")


def _check_governance_sync() -> None:
    accepted = _json(builder.MANIFEST_PATH).get("phase_acceptance_status") == "PASSED"
    state = "S19_P2_PASSED" if accepted else "S19_P2_PENDING_FINAL_VALIDATION"
    environment = dict(os.environ)
    environment.update({"PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": "."})
    result = subprocess.run([sys.executable, "-B", "KMFA/tools/v015_roadmap_governance_sync.py", "--check", "--validation-state", state], cwd=REPO_ROOT, env=environment, capture_output=True, text=True, check=False)
    if result.returncode:
        raise CheckError("governance roadmap sync drifted: " + (result.stdout + result.stderr)[-3000:])
    common = (
        "governance_model_count: 18", "active_formula_count: 390", "active_parameter_count: 2320", 'current_parameter_range: "PARAM-KMFA-2686..2705"', "stage_execution_percentage: 67",
        "s19_p2_started: true", "s19_p2_policy_count: 6", "s19_p2_current_policy_count: 5", "s19_p2_blocked_policy_count: 1", "s19_p2_evidence_item_count: 12",
        "s19_p2_available_evidence_count: 7", "s19_p2_missing_evidence_count: 3", "s19_p2_review_evidence_count: 2", "s19_p2_policy_task_count: 6",
        "s19_p2_formal_eligibility_conclusion_count: 0", "s19_p2_fabricated_evidence_count: 0", "s19_p2_material_packaging_assistance_count: 0", "s19_p2_source_gate_bypass_count: 0",
        "s19_p2_cross_company_leak_count: 0", "s19_p2_browser_flow_count: 8", "s19_p2_visual_evidence_count: 6", "s19_p2_public_check_count: 80", "s19_p2_raw_root_access_count: 0",
        "s19_p3_started: false", "github_upload_performed: false", "app_reinstall_performed: false",
    )
    phase_tokens = {"docs/governance/project.yaml": 'current_phase_id: "V015_S19_P2_POLICY_ELIGIBILITY"', "metadata/project/project.yaml": 'current_phase: "V015_S19_P2_POLICY_ELIGIBILITY"', "docs/governance/roadmap.yaml": 'current_phase_id: "V015_S19_P2_POLICY_ELIGIBILITY"'}
    for relative, phase_token in phase_tokens.items():
        text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
        missing = [token for token in (*common, phase_token) if token not in text]
        if missing:
            raise CheckError(f"governance state drifted in {relative}: " + ", ".join(missing))
    with (builder.PROJECT_ROOT / "docs/governance/parameter_registry.csv").open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    selected = [row for row in rows if row.get("parameter_id", "").startswith("PARAM-KMFA-") and 2686 <= int(row["parameter_id"].rsplit("-", 1)[-1]) <= 2705]
    if len(selected) != 20 or not all(row["model_id"] == "MOD-KMFA-POLICY-ELIGIBILITY-001" and row["formula_id"] == "FORM-KMFA-V015-S19-P2-POLICY-ELIGIBILITY-001" and row["status"] == "active" for row in selected):
        raise CheckError("S19-P2 parameter registry drifted")


def check(pre_final: bool = False, skip_validation_receipts: bool = False) -> None:
    _check_scope(); _check_dependency(); _check_taskpack_source(); _check_artifacts(); _check_public_boundary(); _check_governance_sync()
    value, matrix, rows = _json(builder.MANIFEST_PATH), _json(builder.TASK_MATRIX_PATH), builder.receipts()
    if pre_final:
        if value.get("phase_acceptance_status") != "PENDING_FINAL_VALIDATION" or value.get("phase_task_accepted_count") != 0 or matrix.get("phase_task_accepted_count") != 0:
            raise CheckError("pre-final manifest must remain pending")
        if value.get("s19_p1_acceptance_status") != "PASSED" or value.get("s19_p2_started") is not True or value.get("s19_p2_completed") is not False or value.get("s19_p3_entry_allowed") is not False or value.get("s19_p3_started") is not False or value.get("overall_accepted_phase_count") != 53:
            raise CheckError("pre-final must remain inside S19-P2")
        if rows and not skip_validation_receipts:
            raise CheckError("pre-final subject cannot contain validation receipts")
    else:
        final, run_id, head = builder.final_binding(rows)
        if not final or value.get("phase_acceptance_status") != "PASSED" or value.get("evidence_validation_status") != "PASS":
            raise CheckError("final S19-P2 acceptance receipts are incomplete")
        if value.get("phase_task_accepted_count") != 3 or matrix.get("phase_task_accepted_count") != 3:
            raise CheckError("all three S19-P2 tasks must be accepted")
        if value.get("validation_run_id") != run_id or value.get("validation_head") != head or value.get("overall_accepted_phase_count") != 54:
            raise CheckError("final receipt binding or accepted phase count drifted")
        if value.get("s19_p2_completed") is not True or value.get("s19_p3_entry_allowed") is not True or value.get("s19_p3_started") is not False or value.get("next_gate_id") != "S19-P3":
            raise CheckError("final state must open but not start S19-P3")
    for key in ("github_upload_performed", "app_reinstall_performed", "formal_business_report"):
        if value.get(key) is not False:
            raise CheckError(f"release boundary drifted: {key}")


def main() -> int:
    parser = argparse.ArgumentParser(description="检查 KMFA v1.5 S19-P2 政策资格")
    parser.add_argument("--pre-final", action="store_true")
    parser.add_argument("--skip-validation-receipts", action="store_true")
    parser.add_argument("--dependency-check", action="store_true")
    parser.add_argument("--taskpack-source-check", action="store_true")
    parser.add_argument("--public-boundary-check", action="store_true")
    parser.add_argument("--clean-governance-sync-check", action="store_true")
    args = parser.parse_args()
    try:
        if args.dependency_check: _check_dependency()
        elif args.taskpack_source_check: _check_taskpack_source()
        elif args.public_boundary_check: _check_public_boundary()
        elif args.clean_governance_sync_check: _check_governance_sync()
        else: check(pre_final=args.pre_final, skip_validation_receipts=args.skip_validation_receipts)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError, builder.BuildError, CheckError) as error:
        print(f"FAIL: {error}")
        return 1
    print("PASS: S19-P2 policy eligibility " + ("pre-final" if args.pre_final else "check"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

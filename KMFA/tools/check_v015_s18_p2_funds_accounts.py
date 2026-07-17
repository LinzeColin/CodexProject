#!/usr/bin/env python3
"""严格检查 KMFA v1.5 S18-P2 资金与账户。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import struct
import subprocess
from pathlib import Path
from typing import Any

from KMFA.tools import build_v015_s18_p2_funds_accounts as builder


REPO_ROOT = builder.REPO_ROOT

EXPECTED_VALIDATIONS = (
    (
        "phase_contract",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -c \"import ast,pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8')) for p in ('KMFA/tools/v015_s18_p2_funds_accounts.py','KMFA/tools/run_v015_s18_p2_funds_accounts.py','KMFA/tools/build_v015_s18_p2_funds_accounts.py','KMFA/tools/check_v015_s18_p2_funds_accounts.py','KMFA/tools/run_v015_s18_p2_browser_tests.py','KMFA/tools/run_v015_s18_p2_validations.py','KMFA/tools/v015_roadmap_governance_sync.py')]\"",
    ),
    (
        "focused_unit_tests",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s18_p2_funds_accounts",
    ),
    (
        "focused_runtime_tests",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s18_p2_funds_accounts_runtime",
    ),
    (
        "focused_browser_tests",
        "KMFA_PRESERVE_TRACKED_SCREENSHOTS=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/run_v015_s18_p2_browser_tests.py",
    ),
    (
        "focused_artifact_tests",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s18_p2_funds_accounts_artifacts",
    ),
    (
        "focused_governance_tests",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s18_p2_funds_accounts_governance",
    ),
    (
        "s18_p1_dependency",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s18_p2_funds_accounts.py --dependency-check",
    ),
    (
        "deterministic_evidence",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/build_v015_s18_p2_funds_accounts.py --check",
    ),
    (
        "pre_final_phase_checker",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s18_p2_funds_accounts.py --pre-final --skip-validation-receipts",
    ),
    (
        "roadmap_governance_tests",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_roadmap_governance_sync",
    ),
    (
        "roadmap_sync_pending",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/v015_roadmap_governance_sync.py --check --validation-state S18_P2_PENDING_FINAL_VALIDATION",
    ),
    (
        "metadata_protocol",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/metadata_protocol_check.py",
    ),
    (
        "project_governance",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/validate_project_governance.py --project KMFA --mode required",
    ),
    (
        "lean_governance",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/lean_governance.py validate --project KMFA --mode required",
    ),
    (
        "governance_sync",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s18_p2_funds_accounts.py --clean-governance-sync-check",
    ),
    (
        "no_float_money",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_no_float_money.py",
    ),
    (
        "no_omission",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/no_omission_check.py",
    ),
    (
        "taskpack_source",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s18_p2_funds_accounts.py --taskpack-source-check",
    ),
    (
        "public_boundary",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s18_p2_funds_accounts.py --public-boundary-check",
    ),
    ("git_diff_check", f"git diff --check {builder.PHASE_BASE_COMMIT}..HEAD"),
)

if tuple(name for name, _ in EXPECTED_VALIDATIONS) != builder.EXPECTED_VALIDATION_NAMES:
    raise RuntimeError("builder/checker validation name drift")

ALLOWED_PHASE_PREFIXES = (
    "KMFA/CHANGELOG.md",
    "KMFA/HANDOFF.md",
    "KMFA/README.md",
    "KMFA/docs/governance/",
    "KMFA/metadata/model_registry.yaml",
    "KMFA/metadata/project/project.yaml",
    "KMFA/metadata/stage_status.jsonl",
    "KMFA/stage_artifacts/V015_S18_P2_FUNDS_ACCOUNTS/",
    "KMFA/taskpack/v1_5/",
    "KMFA/tests/test_v015_roadmap_governance_sync.py",
    "KMFA/tests/test_v015_s18_p2_funds_accounts.py",
    "KMFA/tests/test_v015_s18_p2_funds_accounts_runtime.py",
    "KMFA/tests/test_v015_s18_p2_funds_accounts_browser.py",
    "KMFA/tests/test_v015_s18_p2_funds_accounts_artifacts.py",
    "KMFA/tests/test_v015_s18_p2_funds_accounts_governance.py",
    "KMFA/tools/build_v015_s18_p2_funds_accounts.py",
    "KMFA/tools/check_v015_s18_p2_funds_accounts.py",
    "KMFA/tools/run_v015_s18_p2_browser_tests.py",
    "KMFA/tools/run_v015_s18_p2_funds_accounts.py",
    "KMFA/tools/run_v015_s18_p2_validations.py",
    "KMFA/tools/v015_roadmap_governance_sync.py",
    "KMFA/tools/v015_s18_p2_funds_accounts.py",
    "KMFA/功能清单.md",
    "KMFA/开发记录.md",
    "KMFA/模型参数文件.md",
)

PRESERVED_UNTRACKED_PREFIXES = (
    ".github/workflows/kmfa-dual-plane.yml",
    "KMFA/machine/",
    "KMFA/文档/",
)


class CheckError(RuntimeError):
    """S18-P2 验收检查失败。"""


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
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", builder.PHASE_BASE_COMMIT, "HEAD"],
        cwd=REPO_ROOT,
        check=False,
    ).returncode:
        raise CheckError("S18-P2 base commit is not an ancestor of HEAD")
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
        raise CheckError("unexpected S18-P2 path(s): " + ", ".join(unexpected))


def _check_dependency() -> None:
    value = builder.dependency()
    expected = {
        "acceptance_status": "PASSED",
        "validation_receipt_count": 20,
        "overall_accepted_phase_count": 50,
        "s18_p2_entry_allowed": True,
        "s18_p2_started": False,
    }
    mismatch = [key for key, expected_value in expected.items() if value.get(key) != expected_value]
    if mismatch:
        raise CheckError("S18-P1 依赖不完整：" + ", ".join(mismatch))


def _check_taskpack_source() -> None:
    package = Path.home() / "Downloads/KMFA_ChatGPT_Stage3_Codex_TaskPack_Roadmap_v2_0_UIUX_FULL_REBUILD.zip"
    if not package.is_file() or hashlib.sha256(package.read_bytes()).hexdigest() != builder.TASKPACK_SHA256:
        raise CheckError("TaskPack package missing or SHA-256 drifted")
    source_manifest = _json(builder.PROJECT_ROOT / "taskpack/v1_5/source_manifest.json")
    for key, value in {
        "source_package_sha256": builder.TASKPACK_SHA256,
        "stage_count": 24,
        "phase_count": 72,
        "task_count": 216,
    }.items():
        if source_manifest.get(key) != value:
            raise CheckError(f"tracked TaskPack source manifest drifted: {key}")
    roadmap = _json(builder.PROJECT_ROOT / "taskpack/v1_5/roadmap_v2_0.json")
    stage = next((item for item in roadmap.get("stages", []) if item.get("id") == "S18"), None)
    phase = next((item for item in (stage or {}).get("phases", []) if item.get("id") == "P2"), None)
    expected = [
        ("T01", "建立银行账户事实", "多主体、多银行、多账户余额和流水。", "资金模型。", "余额日期、来源和账户脱敏明确。", "余额勾稽测试。", "账户不明不得汇总。"),
        ("T02", "实现现金预测", "基于回款计划、付款计划、贷款到期和确定性等级预测。", "预测。", "事实与假设分开。", "情景测试。", "预测不得伪装成确定值。"),
        ("T03", "实现贷款和资金计划", "展示到期、利息、保证金和资金缺口。", "资金页面。", "不包含支付执行。", "任务测试。", "付款按钮不得出现。"),
    ]
    actual = [
        tuple(task.get(key) for key in ("id", "name", "action", "output", "acceptance", "evidence", "stop"))
        for task in (phase or {}).get("tasks", [])
    ]
    if (
        not stage
        or stage.get("name") != "回款、应收、资金与贷款分析"
        or stage.get("goal") != "建立现金安全、催收优先级、多主体账户和资金计划能力，不执行付款。"
        or not phase
        or phase.get("name") != "资金与账户"
        or actual != expected
    ):
        raise CheckError("S18-P2 source contract drifted")


def _png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()[:24]
    if len(data) != 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        raise CheckError(f"PNG required: {path}")
    return struct.unpack(">II", data[16:24])


def _check_artifacts() -> None:
    builder.check_outputs()
    source = _json(builder.SOURCE_CONTRACT_PATH)
    accounts = _json(builder.ACCOUNT_CONTRACT_PATH)
    forecast = _json(builder.FORECAST_CONTRACT_PATH)
    funding = _json(builder.FUNDING_CONTRACT_PATH)
    browser = _json(builder.BROWSER_CONTRACT_PATH)
    checks = _json(builder.PUBLIC_CHECKS_PATH)
    if (
        source.get("data_classification") != "PUBLIC_SYNTHETIC"
        or source.get("roadmap_phase_id") != "S18-P2"
        or source.get("task_ids") != ["S18P2T01", "S18P2T02", "S18P2T03"]
    ):
        raise CheckError("公开来源合同不完整")
    if (
        accounts.get("company_count") != 3
        or accounts.get("bank_count") != 3
        or accounts.get("known_account_count") != 4
        or accounts.get("unknown_account_count") != 1
        or accounts.get("excluded_unknown_account_count") != 1
        or accounts.get("all_account_identifiers_masked") is not True
        or accounts.get("all_sources_explicit") is not True
        or accounts.get("account_reconciliation_difference_cents") != 0
        or accounts.get("bank_reconciliation_difference_cents") != 0
        or accounts.get("unknown_amount_in_total_cents") != 0
        or accounts.get("cross_company_leak_count") != 0
        or accounts.get("money_tolerance_cents") != 0
    ):
        raise CheckError("银行账户合同不完整")
    if (
        forecast.get("scenario_count") != 3
        or forecast.get("forecast_period_count") != 4
        or forecast.get("all_scenarios_separate_fact_plan_assumption") is not True
        or forecast.get("forecast_presented_as_certainty_count") != 0
        or forecast.get("assumption_fact_write_count") != 0
        or forecast.get("scenario_difference_cents") != 0
        or forecast.get("distinct_final_scenario_balance_count") != 3
        or "不是确定值" not in forecast.get("result_label_zh", "")
    ):
        raise CheckError("现金预测合同不完整")
    if (
        funding.get("loan_count") != 3
        or funding.get("loan_due_within_90_days_count") != 2
        or funding.get("funding_period_count") != 4
        or funding.get("all_maturities_explicit") is not True
        or funding.get("payment_execution_count") != 0
        or funding.get("bank_operation_count") != 0
        or funding.get("payment_button_count") != 0
    ):
        raise CheckError("贷款与资金合同不完整")
    if (
        checks.get("check_count") != 61
        or checks.get("pass_count") != 61
        or checks.get("fail_count") != 0
        or len(checks.get("checks", [])) != 61
        or not all(row.get("status") == "PASS" for row in checks.get("checks", []))
    ):
        raise CheckError("61 项公开检查未全部通过")
    if (
        browser.get("browser_flow_count") != 8
        or browser.get("visual_evidence_count") != 6
        or browser.get("horizontal_page_overflow_allowed") is not False
        or browser.get("external_network_request_count") != 0
    ):
        raise CheckError("浏览器验收合同不完整")
    sizes = [_png_size(path) for path in builder.SCREENSHOT_PATHS]
    if any(width < 1000 or height < 700 for width, height in sizes[:5]):
        raise CheckError("电脑视觉证据尺寸漂移")
    if sizes[5][0] != 390 or sizes[5][1] < 844:
        raise CheckError("手机视觉证据尺寸漂移")


def _check_public_boundary() -> None:
    forbidden = (
        r"/Users/linzezhang/Downloads/KMFA_MetaData",
        r"BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY",
        r"(?i)(?:api[_-]?key|secret|token|password)\s*[:=]\s*['\"][^'\"]+",
    )
    files = [
        path
        for path in builder.OUTPUT_ROOT.rglob("*")
        if path.is_file() and path.suffix.lower() in {".json", ".jsonl", ".html", ".md"}
    ]
    files.extend(
        [
            builder.PROJECT_ROOT / "tools/v015_s18_p2_funds_accounts.py",
            builder.PROJECT_ROOT / "tools/run_v015_s18_p2_funds_accounts.py",
        ]
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for pattern in forbidden:
            if re.search(pattern, text):
                raise CheckError(f"public boundary match in {path.relative_to(REPO_ROOT)}")
    value = _json(builder.MANIFEST_PATH)
    for key in (
        "raw_root_access_count",
        "live_source_read_count",
        "external_network_request_count",
        "real_identity_count",
        "credential_count",
        "real_business_action_count",
        "source_data_write_count",
        "fact_layer_write_count",
        "payment_execution_count",
        "bank_operation_count",
        "payment_button_count",
    ):
        if value.get(key) != 0:
            raise CheckError(f"public boundary count must remain zero: {key}")


def _check_governance_sync() -> None:
    accepted = _json(builder.MANIFEST_PATH).get("phase_acceptance_status") == "PASSED"
    state = "S18_P2_PASSED" if accepted else "S18_P2_PENDING_FINAL_VALIDATION"
    environment = dict(os.environ)
    environment.update({"PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": "."})
    result = subprocess.run(
        ["python3", "-B", "KMFA/tools/v015_roadmap_governance_sync.py", "--check", "--validation-state", state],
        cwd=REPO_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise CheckError("governance roadmap sync drifted: " + (result.stdout + result.stderr)[-3000:])
    common = (
        "governance_model_count: 15",
        "active_formula_count: 386",
        "active_parameter_count: 2240",
        'current_parameter_range: "PARAM-KMFA-2606..2625"',
        "stage_execution_percentage: 67",
        "s18_p2_started: true",
        "s18_p2_company_count: 3",
        "s18_p2_bank_count: 3",
        "s18_p2_known_account_count: 4",
        "s18_p2_unknown_account_count: 1",
        "s18_p2_excluded_unknown_account_count: 1",
        "s18_p2_account_reconciliation_difference_cents: 0",
        "s18_p2_bank_reconciliation_difference_cents: 0",
        "s18_p2_unknown_amount_in_total_cents: 0",
        "s18_p2_cross_company_leak_count: 0",
        "s18_p2_forecast_scenario_count: 3",
        "s18_p2_forecast_period_count: 4",
        "s18_p2_forecast_presented_as_certainty_count: 0",
        "s18_p2_assumption_fact_write_count: 0",
        "s18_p2_scenario_difference_cents: 0",
        "s18_p2_loan_count: 3",
        "s18_p2_loan_due_within_90_days_count: 2",
        "s18_p2_payment_execution_count: 0",
        "s18_p2_payment_button_count: 0",
        "s18_p2_raw_root_access_count: 0",
        "s18_p3_started: false",
    )
    current_phase_tokens = {
        "docs/governance/project.yaml": 'current_phase_id: "V015_S18_P2_FUNDS_ACCOUNTS"',
        "metadata/project/project.yaml": 'current_phase: "V015_S18_P2_FUNDS_ACCOUNTS"',
        "docs/governance/roadmap.yaml": 'current_phase_id: "V015_S18_P2_FUNDS_ACCOUNTS"',
    }
    for relative, phase_token in current_phase_tokens.items():
        text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
        missing = [token for token in (*common, phase_token) if token not in text]
        if missing:
            raise CheckError(f"governance state drifted in {relative}: " + ", ".join(missing))
    with (builder.PROJECT_ROOT / "docs/governance/parameter_registry.csv").open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))
    if any(len(row) != len(rows[0]) for row in rows[:21]):
        raise CheckError("S18-P2 parameter registry column count drifted")


def check(pre_final: bool = False, skip_validation_receipts: bool = False) -> None:
    _check_scope()
    _check_dependency()
    _check_taskpack_source()
    _check_artifacts()
    _check_public_boundary()
    _check_governance_sync()
    value = _json(builder.MANIFEST_PATH)
    matrix = _json(builder.TASK_MATRIX_PATH)
    rows = builder.receipts()
    if pre_final:
        if value.get("phase_acceptance_status") != "PENDING_FINAL_VALIDATION":
            raise CheckError("pre-final manifest must remain pending")
        if value.get("phase_task_accepted_count") != 0 or matrix.get("phase_task_accepted_count") != 0:
            raise CheckError("pre-final tasks cannot be accepted")
        if (
            value.get("s18_p1_acceptance_status") != "PASSED"
            or value.get("s18_p2_started") is not True
            or value.get("s18_p2_completed") is not False
            or value.get("s18_p3_entry_allowed") is not False
            or value.get("s18_p3_started") is not False
            or value.get("overall_accepted_phase_count") != 50
        ):
            raise CheckError("pre-final must remain inside S18-P2")
        if rows and not skip_validation_receipts:
            raise CheckError("pre-final subject cannot contain validation receipts")
    else:
        final, run_id, head = builder.final_binding(rows)
        if not final or value.get("phase_acceptance_status") != "PASSED" or value.get("evidence_validation_status") != "PASS":
            raise CheckError("final S18-P2 acceptance receipts are incomplete")
        if value.get("phase_task_accepted_count") != 3 or matrix.get("phase_task_accepted_count") != 3:
            raise CheckError("all three S18-P2 tasks must be accepted")
        if value.get("validation_run_id") != run_id or value.get("validation_head") != head:
            raise CheckError("final receipt binding drifted")
        if value.get("overall_accepted_phase_count") != 51:
            raise CheckError("accepted TaskPack phase count must advance to 51")
        if (
            value.get("s18_p2_completed") is not True
            or value.get("s18_p3_entry_allowed") is not True
            or value.get("s18_p3_started") is not False
            or value.get("next_gate_id") != "S18-P3"
        ):
            raise CheckError("final state must open but not start S18-P3")
    for key in ("github_upload_performed", "app_reinstall_performed", "formal_business_report"):
        if value.get(key) is not False:
            raise CheckError(f"release boundary drifted: {key}")


def main() -> int:
    parser = argparse.ArgumentParser(description="检查 KMFA v1.5 S18-P2 资金与账户")
    parser.add_argument("--pre-final", action="store_true")
    parser.add_argument("--skip-validation-receipts", action="store_true")
    parser.add_argument("--dependency-check", action="store_true")
    parser.add_argument("--taskpack-source-check", action="store_true")
    parser.add_argument("--public-boundary-check", action="store_true")
    parser.add_argument("--clean-governance-sync-check", action="store_true")
    args = parser.parse_args()
    try:
        if args.dependency_check:
            _check_dependency()
        elif args.taskpack_source_check:
            _check_taskpack_source()
        elif args.public_boundary_check:
            _check_public_boundary()
        elif args.clean_governance_sync_check:
            _check_governance_sync()
        else:
            check(pre_final=args.pre_final, skip_validation_receipts=args.skip_validation_receipts)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError, builder.BuildError, CheckError) as error:
        print(f"FAIL: {error}")
        return 1
    print("PASS: S18-P2 funds and accounts " + ("pre-final" if args.pre_final else "check"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

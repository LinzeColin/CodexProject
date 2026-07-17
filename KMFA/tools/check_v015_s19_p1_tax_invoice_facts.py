#!/usr/bin/env python3
"""严格检查 KMFA v1.5 S19-P1 税务与发票事实。"""

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

from KMFA.tools import build_v015_s19_p1_tax_invoice_facts as builder


REPO_ROOT = builder.REPO_ROOT

EXPECTED_VALIDATIONS = (
    (
        "phase_contract",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -c \"import ast,pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8')) for p in ('KMFA/tools/v015_s19_p1_tax_invoice_facts.py','KMFA/tools/run_v015_s19_p1_tax_invoice_facts.py','KMFA/tools/build_v015_s19_p1_tax_invoice_facts.py','KMFA/tools/check_v015_s19_p1_tax_invoice_facts.py','KMFA/tools/run_v015_s19_p1_browser_tests.py','KMFA/tools/run_v015_s19_p1_validations.py','KMFA/tools/v015_roadmap_governance_sync.py')]\"",
    ),
    ("focused_unit_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s19_p1_tax_invoice_facts"),
    ("focused_runtime_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s19_p1_tax_invoice_facts_runtime"),
    ("focused_browser_tests", "KMFA_PRESERVE_TRACKED_SCREENSHOTS=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/run_v015_s19_p1_browser_tests.py"),
    ("focused_artifact_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s19_p1_tax_invoice_facts_artifacts"),
    ("focused_governance_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s19_p1_tax_invoice_facts_governance"),
    ("s18_review_dependency", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s19_p1_tax_invoice_facts.py --dependency-check"),
    ("deterministic_evidence", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/build_v015_s19_p1_tax_invoice_facts.py --check"),
    ("pre_final_phase_checker", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s19_p1_tax_invoice_facts.py --pre-final --skip-validation-receipts"),
    ("roadmap_governance_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_roadmap_governance_sync"),
    ("roadmap_sync_pending", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/v015_roadmap_governance_sync.py --check --validation-state S19_P1_PENDING_FINAL_VALIDATION"),
    ("metadata_protocol", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/metadata_protocol_check.py"),
    ("project_governance", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/validate_project_governance.py --project KMFA --mode required"),
    ("lean_governance", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/lean_governance.py validate --project KMFA --mode required"),
    ("governance_sync", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s19_p1_tax_invoice_facts.py --clean-governance-sync-check"),
    ("no_float_money", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_no_float_money.py"),
    ("no_omission", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/no_omission_check.py"),
    ("taskpack_source", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s19_p1_tax_invoice_facts.py --taskpack-source-check"),
    ("public_boundary", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s19_p1_tax_invoice_facts.py --public-boundary-check"),
    ("git_diff_check", f"git diff --check {builder.PHASE_BASE_COMMIT}..HEAD"),
)

if tuple(name for name, _ in EXPECTED_VALIDATIONS) != builder.EXPECTED_VALIDATION_NAMES:
    raise RuntimeError("builder/checker validation name drift")

ALLOWED_PHASE_PREFIXES = (
    "KMFA/AGENTS.md",
    "KMFA/CHANGELOG.md",
    "KMFA/HANDOFF.md",
    "KMFA/README.md",
    "KMFA/config/v015_s19_p1_tax_invoice_policy.json",
    "KMFA/docs/governance/",
    "KMFA/metadata/model_registry.yaml",
    "KMFA/metadata/project/project.yaml",
    "KMFA/metadata/stage_status.jsonl",
    "KMFA/stage_artifacts/V015_S19_P1_TAX_INVOICE_FACTS/",
    "KMFA/taskpack/v1_5/",
    "KMFA/tests/test_v015_roadmap_governance_sync.py",
    "KMFA/tests/test_v015_s19_p1_tax_invoice_facts.py",
    "KMFA/tests/test_v015_s19_p1_tax_invoice_facts_runtime.py",
    "KMFA/tests/test_v015_s19_p1_tax_invoice_facts_browser.py",
    "KMFA/tests/test_v015_s19_p1_tax_invoice_facts_artifacts.py",
    "KMFA/tests/test_v015_s19_p1_tax_invoice_facts_governance.py",
    "KMFA/tools/build_v015_s19_p1_tax_invoice_facts.py",
    "KMFA/tools/check_v015_s19_p1_tax_invoice_facts.py",
    "KMFA/tools/run_v015_s19_p1_browser_tests.py",
    "KMFA/tools/run_v015_s19_p1_tax_invoice_facts.py",
    "KMFA/tools/run_v015_s19_p1_validations.py",
    "KMFA/tools/v015_roadmap_governance_sync.py",
    "KMFA/tools/v015_s19_p1_tax_invoice_facts.py",
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
    """S19-P1 验收检查失败。"""


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
        raise CheckError("S19-P1 base commit is not an ancestor of HEAD")
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
        raise CheckError("unexpected S19-P1 path(s): " + ", ".join(unexpected))


def _check_dependency() -> None:
    value = builder.dependency()
    expected = {
        "acceptance_status": "PASSED",
        "validation_receipt_count": 32,
        "overall_accepted_phase_count": 52,
        "s19_p1_entry_allowed": True,
        "s19_p1_started": False,
    }
    mismatch = [key for key, expected_value in expected.items() if value.get(key) != expected_value]
    if mismatch:
        raise CheckError("S18 整体复审依赖不完整：" + ", ".join(mismatch))


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
    phase = next((item for item in (stage or {}).get("phases", []) if item.get("id") == "P1"), None)
    expected = [
        ("T01", "建立销项、进项和税率事实", "关联合同、项目、凭证和回款。", "税票模型。", "税率、含税状态和发票状态明确。", "税率测试。", "未知税率不自动推断。"),
        ("T02", "实现进销项与合同匹配", "识别税率、主体、项目和期间异常。", "匹配规则。", "异常有证据。", "交叉测试。", "不自动做税务调整。"),
        ("T03", "实现项目税负视图", "按项目和业务类型分析。", "税务页面。", "明确只是管理分析。", "报告测试。", "不得输出正式申报结论。"),
    ]
    actual = [tuple(task.get(key) for key in ("id", "name", "action", "output", "acceptance", "evidence", "stop")) for task in (phase or {}).get("tasks", [])]
    if (
        not stage
        or stage.get("name") != "税务、发票、政策资格与证据准备"
        or stage.get("goal") != "支持税务风险和科小、高新、专精特新/小巨人等政策证据准备，不替代申报和专业签字。"
        or not phase
        or phase.get("name") != "税务与发票事实"
        or actual != expected
    ):
        raise CheckError("S19-P1 source contract drifted")


def _png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()[:24]
    if len(data) != 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        raise CheckError(f"PNG required: {path}")
    return struct.unpack(">II", data[16:24])


def _check_artifacts() -> None:
    builder.check_outputs()
    source = _json(builder.SOURCE_CONTRACT_PATH)
    model = _json(builder.TAX_MODEL_PATH)
    matching = _json(builder.MATCHING_PATH)
    burden = _json(builder.BURDEN_PATH)
    browser = _json(builder.BROWSER_CONTRACT_PATH)
    checks = _json(builder.PUBLIC_CHECKS_PATH)
    if source.get("data_classification") != "PUBLIC_SYNTHETIC" or source.get("roadmap_phase_id") != "S19-P1" or source.get("task_ids") != ["S19P1T01", "S19P1T02", "S19P1T03"]:
        raise CheckError("公开来源合同不完整")
    if (
        model.get("fact_count") != 8
        or model.get("direction_count") != 2
        or model.get("linked_dimension_count") != 4
        or model.get("explicit_tax_rate_count") != 3
        or model.get("unknown_rate_count") != 1
        or model.get("unknown_rate_blocked") is not True
        or model.get("rate_inference_count") != 0
        or model.get("integer_cent_required") is not True
    ):
        raise CheckError("税票事实模型不完整")
    if (
        matching.get("matched_count") != 4
        or matching.get("review_count") != 4
        or matching.get("anomaly_count") != 5
        or matching.get("anomaly_type_count") != 5
        or matching.get("all_anomalies_have_invoice_and_contract_evidence") is not True
        or matching.get("automatic_tax_adjustment_count") != 0
    ):
        raise CheckError("四维匹配合同不完整")
    if (
        burden.get("project_count") != 3
        or burden.get("business_type_count") != 3
        or burden.get("equation_difference_cents") != 0
        or burden.get("scope_limitation_displayed_count") != 3
        or burden.get("formal_filing_conclusion_count") != 0
    ):
        raise CheckError("项目税负管理合同不完整")
    if checks.get("check_count") != 64 or checks.get("pass_count") != 64 or checks.get("fail_count") != 0 or len(checks.get("checks", [])) != 64 or not all(row.get("status") == "PASS" for row in checks.get("checks", [])):
        raise CheckError("64 项公开检查未全部通过")
    if browser.get("browser_flow_count") != 7 or browser.get("visual_evidence_count") != 5 or browser.get("minimum_touch_target_px") != 44 or browser.get("horizontal_page_overflow_allowed") is not False or browser.get("external_network_request_count") != 0:
        raise CheckError("浏览器验收合同不完整")
    sizes = [_png_size(path) for path in builder.SCREENSHOT_PATHS]
    if any(width < 1000 or height < 700 for width, height in sizes[:4]):
        raise CheckError("电脑视觉证据尺寸漂移")
    if sizes[4][0] != 390 or sizes[4][1] < 844:
        raise CheckError("手机视觉证据尺寸漂移")


def _check_public_boundary() -> None:
    forbidden = (
        r"/Users/linzezhang/Downloads/KMFA_MetaData",
        r"BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY",
        r"(?i)(?:api[_-]?key|secret|token|password)\s*[:=]\s*['\"][^'\"]+",
    )
    files = [path for path in builder.OUTPUT_ROOT.rglob("*") if path.is_file() and path.suffix.lower() in {".json", ".jsonl", ".html", ".csv", ".md"}]
    files.extend((
        builder.PROJECT_ROOT / "config/v015_s19_p1_tax_invoice_policy.json",
        builder.PROJECT_ROOT / "tools/v015_s19_p1_tax_invoice_facts.py",
        builder.PROJECT_ROOT / "tools/run_v015_s19_p1_tax_invoice_facts.py",
    ))
    for path in files:
        text = path.read_text(encoding="utf-8")
        for pattern in forbidden:
            if re.search(pattern, text):
                raise CheckError(f"public boundary match in {path.relative_to(REPO_ROOT)}")
    value = _json(builder.MANIFEST_PATH)
    for key in (
        "raw_root_access_count", "live_source_read_count", "external_network_request_count",
        "real_identity_count", "credential_count", "real_business_action_count",
        "source_data_write_count", "fact_layer_write_count", "rate_inference_count",
        "automatic_tax_adjustment_count", "formal_filing_conclusion_count",
        "invoice_issue_count", "tax_filing_count", "cross_company_leak_count",
    ):
        if value.get(key) != 0:
            raise CheckError(f"public boundary count must remain zero: {key}")


def _check_governance_sync() -> None:
    accepted = _json(builder.MANIFEST_PATH).get("phase_acceptance_status") == "PASSED"
    state = "S19_P1_PASSED" if accepted else "S19_P1_PENDING_FINAL_VALIDATION"
    environment = dict(os.environ)
    environment.update({"PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": "."})
    result = subprocess.run(
        [sys.executable, "-B", "KMFA/tools/v015_roadmap_governance_sync.py", "--check", "--validation-state", state],
        cwd=REPO_ROOT, env=environment, capture_output=True, text=True, check=False,
    )
    if result.returncode:
        raise CheckError("governance roadmap sync drifted: " + (result.stdout + result.stderr)[-3000:])
    common = (
        "governance_model_count: 17", "active_formula_count: 389", "active_parameter_count: 2300",
        'current_parameter_range: "PARAM-KMFA-2666..2685"', "stage_execution_percentage: 33",
        's19_p1_started: true', "s19_p1_tax_invoice_fact_count: 8", "s19_p1_matched_count: 4",
        "s19_p1_review_count: 4", "s19_p1_anomaly_count: 5", "s19_p1_unknown_rate_count: 1",
        "s19_p1_rate_inference_count: 0", "s19_p1_automatic_tax_adjustment_count: 0",
        "s19_p1_project_burden_count: 3", "s19_p1_burden_equation_difference_cents: 0",
        "s19_p1_formal_filing_conclusion_count: 0", "s19_p1_cross_company_leak_count: 0",
        "s19_p1_browser_flow_count: 7", "s19_p1_visual_evidence_count: 5",
        "s19_p1_public_check_count: 64", "s19_p1_raw_root_access_count: 0",
        "s19_p2_started: false", "github_upload_performed: false", "app_reinstall_performed: false",
    )
    phase_tokens = {
        "docs/governance/project.yaml": 'current_phase_id: "V015_S19_P1_TAX_INVOICE_FACTS"',
        "metadata/project/project.yaml": 'current_phase: "V015_S19_P1_TAX_INVOICE_FACTS"',
        "docs/governance/roadmap.yaml": 'current_phase_id: "V015_S19_P1_TAX_INVOICE_FACTS"',
    }
    for relative, phase_token in phase_tokens.items():
        text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
        missing = [token for token in (*common, phase_token) if token not in text]
        if missing:
            raise CheckError(f"governance state drifted in {relative}: " + ", ".join(missing))
    parameter_path = builder.PROJECT_ROOT / "docs/governance/parameter_registry.csv"
    with parameter_path.open(encoding="utf-8-sig", newline="") as handle:
        raw_rows = list(csv.reader(handle))
    with parameter_path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    selected = [row for row in rows if row.get("parameter_id", "").startswith("PARAM-KMFA-") and 2666 <= int(row["parameter_id"].rsplit("-", 1)[-1]) <= 2685]
    if not raw_rows or any(len(row) != len(raw_rows[0]) for row in raw_rows) or len(selected) != 20:
        raise CheckError("S19-P1 parameter registry drifted")


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
        if value.get("phase_acceptance_status") != "PENDING_FINAL_VALIDATION" or value.get("phase_task_accepted_count") != 0 or matrix.get("phase_task_accepted_count") != 0:
            raise CheckError("pre-final manifest must remain pending")
        if (
            value.get("s18_stage_review_acceptance_status") != "PASSED"
            or value.get("s19_p1_started") is not True
            or value.get("s19_p1_completed") is not False
            or value.get("s19_p2_entry_allowed") is not False
            or value.get("s19_p2_started") is not False
            or value.get("overall_accepted_phase_count") != 52
        ):
            raise CheckError("pre-final must remain inside S19-P1")
        if rows and not skip_validation_receipts:
            raise CheckError("pre-final subject cannot contain validation receipts")
    else:
        final, run_id, head = builder.final_binding(rows)
        if not final or value.get("phase_acceptance_status") != "PASSED" or value.get("evidence_validation_status") != "PASS":
            raise CheckError("final S19-P1 acceptance receipts are incomplete")
        if value.get("phase_task_accepted_count") != 3 or matrix.get("phase_task_accepted_count") != 3:
            raise CheckError("all three S19-P1 tasks must be accepted")
        if value.get("validation_run_id") != run_id or value.get("validation_head") != head:
            raise CheckError("final receipt binding drifted")
        if value.get("overall_accepted_phase_count") != 53:
            raise CheckError("accepted TaskPack phase count must advance to 53")
        if (
            value.get("s19_p1_completed") is not True
            or value.get("s19_p2_entry_allowed") is not True
            or value.get("s19_p2_started") is not False
            or value.get("next_gate_id") != "S19-P2"
        ):
            raise CheckError("final state must open but not start S19-P2")
    for key in ("github_upload_performed", "app_reinstall_performed", "formal_business_report"):
        if value.get(key) is not False:
            raise CheckError(f"release boundary drifted: {key}")


def main() -> int:
    parser = argparse.ArgumentParser(description="检查 KMFA v1.5 S19-P1 税务与发票事实")
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
    print("PASS: S19-P1 tax invoice facts " + ("pre-final" if args.pre_final else "check"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

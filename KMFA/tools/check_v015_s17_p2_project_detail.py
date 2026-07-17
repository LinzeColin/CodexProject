#!/usr/bin/env python3
"""严格检查 KMFA v1.5 S17-P2 项目详情。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import struct
import subprocess
from pathlib import Path
from typing import Any

from KMFA.tools import build_v015_s17_p2_project_detail as builder


REPO_ROOT = builder.REPO_ROOT

EXPECTED_VALIDATIONS = (
    (
        "phase_contract",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -c \"import ast,pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8')) for p in ('KMFA/tools/v015_s17_p2_project_detail.py','KMFA/tools/run_v015_s17_p2_project_detail.py','KMFA/tools/build_v015_s17_p2_project_detail.py','KMFA/tools/check_v015_s17_p2_project_detail.py','KMFA/tools/run_v015_s17_p2_browser_tests.py','KMFA/tools/run_v015_s17_p2_validations.py','KMFA/tools/v015_roadmap_governance_sync.py')]\"",
    ),
    (
        "focused_unit_tests",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s17_p2_project_detail",
    ),
    (
        "focused_runtime_tests",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s17_p2_project_detail_runtime",
    ),
    (
        "focused_browser_tests",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/run_v015_s17_p2_browser_tests.py",
    ),
    (
        "focused_artifact_tests",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s17_p2_project_detail_artifacts",
    ),
    (
        "focused_governance_tests",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s17_p2_project_detail_governance",
    ),
    (
        "s17_p1_dependency",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s17_p2_project_detail.py --dependency-check",
    ),
    (
        "deterministic_evidence",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/build_v015_s17_p2_project_detail.py --check",
    ),
    (
        "pre_final_phase_checker",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s17_p2_project_detail.py --pre-final --skip-validation-receipts",
    ),
    (
        "roadmap_governance_tests",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_roadmap_governance_sync",
    ),
    (
        "roadmap_sync_pending",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/v015_roadmap_governance_sync.py --check --validation-state S17_P2_PENDING_FINAL_VALIDATION",
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
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s17_p2_project_detail.py --clean-governance-sync-check",
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
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s17_p2_project_detail.py --taskpack-source-check",
    ),
    (
        "public_boundary",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s17_p2_project_detail.py --public-boundary-check",
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
    "KMFA/stage_artifacts/V015_S17_P2_PROJECT_DETAIL/",
    "KMFA/tests/test_v015_roadmap_governance_sync.py",
    "KMFA/tests/test_v015_s17_p2_project_detail.py",
    "KMFA/tests/test_v015_s17_p2_project_detail_runtime.py",
    "KMFA/tests/test_v015_s17_p2_project_detail_browser.py",
    "KMFA/tests/test_v015_s17_p2_project_detail_artifacts.py",
    "KMFA/tests/test_v015_s17_p2_project_detail_governance.py",
    "KMFA/tools/build_v015_s17_p2_project_detail.py",
    "KMFA/tools/check_v015_s17_p2_project_detail.py",
    "KMFA/tools/run_v015_s17_p1_project_list.py",
    "KMFA/tools/run_v015_s17_p2_browser_tests.py",
    "KMFA/tools/run_v015_s17_p2_project_detail.py",
    "KMFA/tools/run_v015_s17_p2_validations.py",
    "KMFA/tools/v015_roadmap_governance_sync.py",
    "KMFA/tools/v015_s17_p1_project_list.py",
    "KMFA/tools/v015_s17_p2_project_detail.py",
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
    """S17-P2 验收检查失败。"""


def _git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    if result.returncode:
        raise CheckError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CheckError(f"JSON object required: {path}")
    return value


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
        raise CheckError("S17-P2 base commit is not an ancestor of HEAD")
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
        raise CheckError("unexpected S17-P2 path(s): " + ", ".join(unexpected))


def _check_dependency() -> None:
    value = builder.dependency()
    expected = {
        "acceptance_status": "PASSED",
        "validation_receipt_count": 20,
        "overall_accepted_phase_count": 47,
        "s17_p2_entry_allowed": True,
        "s17_p2_started": False,
    }
    mismatch = [key for key, expected_value in expected.items() if value.get(key) != expected_value]
    if mismatch:
        raise CheckError("S17-P1 依赖不完整：" + ", ".join(mismatch))


def _check_taskpack_source() -> None:
    package = Path.home() / "Downloads/KMFA_ChatGPT_Stage3_Codex_TaskPack_Roadmap_v2_0_UIUX_FULL_REBUILD.zip"
    if not package.is_file() or hashlib.sha256(package.read_bytes()).hexdigest() != builder.TASKPACK_SHA256:
        raise CheckError("TaskPack package missing or SHA-256 drifted")
    source_manifest = _json(builder.PROJECT_ROOT / "taskpack/v1_5/source_manifest.json")
    if any(
        source_manifest.get(key) != value
        for key, value in {
            "source_package_sha256": builder.TASKPACK_SHA256,
            "stage_count": 24,
            "phase_count": 72,
            "task_count": 216,
        }.items()
    ):
        raise CheckError("tracked TaskPack source manifest drifted")
    roadmap = _json(builder.PROJECT_ROOT / "taskpack/v1_5/roadmap_v2_0.json")
    stage = next((item for item in roadmap.get("stages", []) if item.get("id") == "S17"), None)
    phase = next((item for item in (stage or {}).get("phases", []) if item.get("id") == "P2"), None)
    expected = [
        ("T01", "实现概况页", "一页可回答项目是否赚钱及为什么。", "不得先显示技术状态码。"),
        ("T02", "实现成本页", "合计与引擎一致。", "图表与表格金额不一致失败。"),
        ("T03", "实现收入回款、差异和资料页", "返回保留上下文。", "标签内容重复堆叠失败。"),
    ]
    actual = [
        (task.get("id"), task.get("name"), task.get("acceptance"), task.get("stop"))
        for task in (phase or {}).get("tasks", [])
    ]
    if (
        not stage
        or stage.get("name") != "项目列表、项目详情与成本分析流程"
        or not phase
        or phase.get("name") != "项目详情"
        or actual != expected
    ):
        raise CheckError("S17-P2 source contract drifted")


def _png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()[:24]
    if len(data) != 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        raise CheckError(f"PNG required: {path}")
    return struct.unpack(">II", data[16:24])


def _check_artifacts() -> None:
    builder.check_outputs()
    overview = _json(builder.OVERVIEW_CONTRACT_PATH)
    cost = _json(builder.COST_CONTRACT_PATH)
    navigation = _json(builder.TAB_NAVIGATION_CONTRACT_PATH)
    browser = _json(builder.BROWSER_CONTRACT_PATH)
    if (
        overview.get("business_summary_first") is not True
        or overview.get("technical_status_code_first_count") != 0
        or overview.get("money_equation_difference_cents") != 0
        or overview.get("engine_zero_difference_pass") is not True
        or set(overview.get("engine_golden_difference_cents", {}).values()) != {0}
    ):
        raise CheckError("项目概况合同不完整")
    if (
        cost.get("category_count") != 10
        or cost.get("trend_period_count") != 4
        or cost.get("engine_difference_cents") != 0
        or cost.get("chart_table_difference_cents") != 0
        or cost.get("money_tolerance_cents") != 0
        or cost.get("zero_difference_pass") is not True
        or cost.get("unallocated_source_required") is not True
    ):
        raise CheckError("成本零差异合同不完整")
    if (
        navigation.get("tab_count") != 5
        or navigation.get("section_overlap_count") != 0
        or navigation.get("preserves_list_context") is not True
        or "page=2" not in navigation.get("return_url", "")
        or navigation.get("fact_layer_write_count") != 0
    ):
        raise CheckError("标签或返回上下文合同不完整")
    if len(browser.get("required_flows", [])) != 9 or browser.get("horizontal_page_overflow_allowed") is not False:
        raise CheckError("浏览器验收流程不完整")
    sizes = [_png_size(path) for path in builder.SCREENSHOT_PATHS]
    if any(width != 1440 or height < 1000 for width, height in sizes[:4]):
        raise CheckError("电脑视觉证据尺寸漂移")
    if sizes[4][0] != 390 or sizes[4][1] < 844:
        raise CheckError("手机视觉证据尺寸漂移")
    html = builder.HTML_PATH.read_text(encoding="utf-8")
    required = ("项目详情栏目", "当前判断", "收入与回款", "返回项目列表", "KMFA_PROJECT_DETAIL_TEST", "aria-live")
    missing = [token for token in required if token not in html]
    if missing:
        raise CheckError("runtime HTML contract missing: " + ", ".join(missing))


def _check_public_boundary() -> None:
    forbidden = (
        r"/Users/linzezhang/Downloads/KMFA_MetaData",
        r"BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY",
        r"(?i)(?:api[_-]?key|secret|token|password)\s*[:=]\s*['\"][^'\"]+",
    )
    files = [path for path in builder.OUTPUT_ROOT.rglob("*") if path.is_file() and path.suffix.lower() != ".png"]
    files.extend(
        [
            builder.PROJECT_ROOT / "tools/v015_s17_p2_project_detail.py",
            builder.PROJECT_ROOT / "tools/run_v015_s17_p2_project_detail.py",
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
        "fact_layer_write_count",
    ):
        if value.get(key) != 0:
            raise CheckError(f"public boundary count must remain zero: {key}")


def _check_governance_sync() -> None:
    accepted = _json(builder.MANIFEST_PATH).get("phase_acceptance_status") == "PASSED"
    state = "S17_P2_PASSED" if accepted else "S17_P2_PENDING_FINAL_VALIDATION"
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
        raise CheckError("governance sync drifted: " + (result.stdout + result.stderr)[-3000:])
    tokens = (
        "governance_model_count: 13",
        "active_formula_count: 382",
        "active_parameter_count: 2160",
        'current_parameter_range: "PARAM-KMFA-2526..2545"',
        "stage_execution_percentage: 67",
        "s17_p2_started: true",
        "s17_p2_engine_difference_cents: 0",
        "s17_p2_chart_table_difference_cents: 0",
        "s17_p3_started: false",
    )
    current_phase_tokens = {
        "docs/governance/project.yaml": 'current_phase_id: "V015_S17_P2_PROJECT_DETAIL"',
        "metadata/project/project.yaml": 'current_phase: "V015_S17_P2_PROJECT_DETAIL"',
        "docs/governance/roadmap.yaml": 'current_phase_id: "V015_S17_P2_PROJECT_DETAIL"',
    }
    for relative in ("docs/governance/project.yaml", "metadata/project/project.yaml", "docs/governance/roadmap.yaml"):
        text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
        missing = [token for token in (*tokens, current_phase_tokens[relative]) if token not in text]
        if missing:
            raise CheckError(f"governance state drifted in {relative}: " + ", ".join(missing))


def check(pre_final: bool = False, skip_validation_receipts: bool = False) -> None:
    _check_scope()
    _check_dependency()
    _check_taskpack_source()
    _check_artifacts()
    _check_public_boundary()
    value = _json(builder.MANIFEST_PATH)
    matrix = _json(builder.TASK_MATRIX_PATH)
    rows = builder.receipts()
    if pre_final:
        if value.get("phase_acceptance_status") != "PENDING_FINAL_VALIDATION":
            raise CheckError("pre-final manifest must remain pending")
        if value.get("phase_task_accepted_count") != 0 or matrix.get("phase_task_accepted_count") != 0:
            raise CheckError("pre-final tasks cannot be accepted")
        if (
            value.get("s17_p1_acceptance_status") != "PASSED"
            or value.get("s17_p2_started") is not True
            or value.get("s17_p3_entry_allowed") is not False
            or value.get("s17_p3_started") is not False
        ):
            raise CheckError("pre-final must remain inside S17-P2")
        if rows and not skip_validation_receipts:
            raise CheckError("pre-final subject cannot contain validation receipts")
    else:
        final, run_id, head = builder.final_binding(rows)
        if not final or value.get("phase_acceptance_status") != "PASSED" or value.get("evidence_validation_status") != "PASS":
            raise CheckError("final S17-P2 acceptance receipts are incomplete")
        if value.get("phase_task_accepted_count") != 3 or matrix.get("phase_task_accepted_count") != 3:
            raise CheckError("all three S17-P2 tasks must be accepted")
        if value.get("validation_run_id") != run_id or value.get("validation_head") != head:
            raise CheckError("final receipt binding drifted")
        if value.get("overall_accepted_phase_count") != 48:
            raise CheckError("accepted TaskPack phase count must advance to 48")
        if (
            value.get("s17_p3_entry_allowed") is not True
            or value.get("s17_p3_started") is not False
            or value.get("s17_stage_review_started") is not False
        ):
            raise CheckError("final state must open but not start S17-P3")
    for key in ("github_upload_performed", "app_reinstall_performed", "formal_report_generated"):
        if value.get(key) is not False:
            raise CheckError(f"release boundary drifted: {key}")


def main() -> int:
    parser = argparse.ArgumentParser(description="检查 KMFA v1.5 S17-P2 项目详情")
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
    except (OSError, ValueError, KeyError, json.JSONDecodeError, builder.BuildError, CheckError) as error:
        print(f"FAIL: {error}")
        return 1
    print("PASS: S17-P2 project detail " + ("pre-final" if args.pre_final else "check"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

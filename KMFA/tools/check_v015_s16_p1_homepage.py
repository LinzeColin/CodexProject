#!/usr/bin/env python3
"""严格检查 KMFA v1.5 S16-P1 经营首页首屏。"""

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

from KMFA.tools import build_v015_s16_p1_homepage as builder


REPO_ROOT = builder.REPO_ROOT

EXPECTED_VALIDATIONS = (
    (
        "python_compile",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -c \"import ast,pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8')) for p in ('KMFA/tools/v015_s16_p1_homepage.py','KMFA/tools/run_v015_s16_p1_homepage.py','KMFA/tools/build_v015_s16_p1_homepage.py','KMFA/tools/check_v015_s16_p1_homepage.py','KMFA/tools/run_v015_s16_p1_browser_tests.py','KMFA/tools/run_v015_s16_p1_validations.py','KMFA/tools/v015_roadmap_governance_sync.py')]\"",
    ),
    ("focused_kernel_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s16_p1_homepage"),
    ("focused_runtime_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s16_p1_homepage_runtime"),
    ("focused_browser_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/run_v015_s16_p1_browser_tests.py"),
    ("focused_artifact_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s16_p1_homepage_artifacts"),
    ("focused_governance_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s16_p1_homepage_governance"),
    ("s15_stage_review_dependency", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s16_p1_homepage.py --dependency-check"),
    ("deterministic_evidence", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/build_v015_s16_p1_homepage.py --check"),
    ("pre_final_phase_checker", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s16_p1_homepage.py --pre-final --skip-validation-receipts"),
    ("roadmap_governance_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_roadmap_governance_sync"),
    ("roadmap_sync_pending", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/v015_roadmap_governance_sync.py --check --validation-state S16_P1_PENDING_FINAL_VALIDATION"),
    ("metadata_protocol", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/metadata_protocol_check.py"),
    ("project_governance", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/validate_project_governance.py --project KMFA --mode required"),
    ("lean_governance", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/lean_governance.py validate --project KMFA --mode required"),
    ("governance_sync", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s16_p1_homepage.py --clean-governance-sync-check"),
    ("no_float_money", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_no_float_money.py"),
    ("no_omission", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/no_omission_check.py"),
    ("taskpack_source", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s16_p1_homepage.py --taskpack-source-check"),
    ("public_boundary", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s16_p1_homepage.py --public-boundary-check"),
    ("git_diff_check", f"git diff --check {builder.PHASE_BASE_COMMIT}..HEAD"),
)

if tuple(name for name, _ in EXPECTED_VALIDATIONS) != builder.EXPECTED_VALIDATION_NAMES:
    raise RuntimeError("builder/checker validation name drift")

ALLOWED_PHASE_PREFIXES = (
    "KMFA/AGENTS.md",
    "KMFA/CHANGELOG.md",
    "KMFA/HANDOFF.md",
    "KMFA/README.md",
    "KMFA/docs/governance/",
    "KMFA/metadata/model_registry.yaml",
    "KMFA/metadata/project/project.yaml",
    "KMFA/metadata/stage_status.jsonl",
    "KMFA/stage_artifacts/V015_S16_P1_HOMEPAGE_FIRST_SCREEN/",
    "KMFA/tests/test_v015_roadmap_governance_sync.py",
    "KMFA/tests/test_v015_s16_p1_homepage.py",
    "KMFA/tests/test_v015_s16_p1_homepage_runtime.py",
    "KMFA/tests/test_v015_s16_p1_homepage_browser.py",
    "KMFA/tests/test_v015_s16_p1_homepage_artifacts.py",
    "KMFA/tests/test_v015_s16_p1_homepage_governance.py",
    "KMFA/tools/build_v015_s16_p1_homepage.py",
    "KMFA/tools/check_v015_s16_p1_homepage.py",
    "KMFA/tools/run_v015_s16_p1_homepage.py",
    "KMFA/tools/run_v015_s16_p1_browser_tests.py",
    "KMFA/tools/run_v015_s16_p1_validations.py",
    "KMFA/tools/v015_roadmap_governance_sync.py",
    "KMFA/tools/v015_s16_p1_homepage.py",
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
    """S16-P1 验收检查失败。"""


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
        raise CheckError("S16-P1 base commit is not an ancestor of HEAD")
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
        raise CheckError("unexpected S16-P1 path(s): " + ", ".join(unexpected))


def _check_dependency() -> None:
    value = builder.dependency()
    if value.get("acceptance_status") != "PASSED" or value.get("validation_receipt_count") != 28:
        raise CheckError("S15 整体复审依赖未通过")
    if value.get("s16_p1_entry_allowed") is not True or value.get("s16_p1_started") is not False:
        raise CheckError("S15 整体复审没有只开放 S16-P1")


def _check_taskpack_source() -> None:
    package = Path.home() / "Downloads/KMFA_ChatGPT_Stage3_Codex_TaskPack_Roadmap_v2_0_UIUX_FULL_REBUILD.zip"
    if not package.is_file() or hashlib.sha256(package.read_bytes()).hexdigest() != builder.TASKPACK_SHA256:
        raise CheckError("TaskPack package missing or SHA-256 drifted")
    source_manifest = _json(builder.PROJECT_ROOT / "taskpack/v1_5/source_manifest.json")
    expected_manifest = {
        "source_package_sha256": builder.TASKPACK_SHA256,
        "stage_count": 24,
        "phase_count": 72,
        "task_count": 216,
    }
    if any(source_manifest.get(key) != value for key, value in expected_manifest.items()):
        raise CheckError("tracked TaskPack source manifest drifted")
    roadmap = _json(builder.PROJECT_ROOT / "taskpack/v1_5/roadmap_v2_0.json")
    stage = next((item for item in roadmap.get("stages", []) if item.get("id") == "S16"), None)
    phase = next((item for item in (stage or {}).get("phases", []) if item.get("id") == "P1"), None)
    expected = [
        ("T01", "实现核心经营摘要", "数字来源、截止日和完整性可见。", "缺数据时不得伪造完整结论。"),
        ("T02", "实现本期重点事项", "每项只有一个清晰主动作。", "不得堆砌 20 个告警。"),
        ("T03", "实现趋势和项目组合", "图表可读且有表格替代。", "装饰性雷达图无解释时不得使用。"),
    ]
    actual = [
        (task.get("id"), task.get("name"), task.get("acceptance"), task.get("stop"))
        for task in (phase or {}).get("tasks", [])
    ]
    if (
        not stage
        or stage.get("name") != "经营首页与管理层总览"
        or not phase
        or phase.get("name") != "首屏结构"
        or actual != expected
    ):
        raise CheckError("S16-P1 source contract drifted")


def _png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()[:24]
    if len(data) != 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        raise CheckError(f"PNG required: {path}")
    return struct.unpack(">II", data[16:24])


def _check_artifacts() -> None:
    builder.check_outputs()
    summary = _json(builder.SUMMARY_CONTRACT_PATH)
    focus = _json(builder.FOCUS_CONTRACT_PATH)
    visual = _json(builder.VISUAL_CONTRACT_PATH)
    browser = _json(builder.BROWSER_CONTRACT_PATH)
    if summary.get("metric_count") != 5 or summary.get("source_bound_metric_count") != 5:
        raise CheckError("经营摘要来源合同不完整")
    if summary.get("cutoff_bound_metric_count") != 5 or summary.get("completeness_bound_metric_count") != 5:
        raise CheckError("经营摘要截止日或完整性合同不完整")
    partial = summary.get("partial_example", {})
    if partial.get("overall_completeness") != "INCOMPLETE" or partial.get("complete_management_conclusion_available") is not False:
        raise CheckError("缺失资料状态没有阻断完整结论")
    if summary.get("missing_as_zero_count") != 0:
        raise CheckError("缺失资料被伪装为 0")
    if focus.get("focus_item_count") != 5 or focus.get("primary_action_count") != 5:
        raise CheckError("重点事项数量或主动作数量不正确")
    if focus.get("one_primary_action_each") is not True or focus.get("automatic_execution_count") != 0:
        raise CheckError("重点事项主动作合同不正确")
    if visual.get("trend_series_count") != 3 or visual.get("trend_table_alternative_count") != 3:
        raise CheckError("趋势与表格替代合同不完整")
    if visual.get("project_portfolio_count") != 4 or visual.get("decorative_radar_chart_count") != 0:
        raise CheckError("项目组合或雷达图约束不正确")
    if len(browser.get("required_flows", [])) != 6:
        raise CheckError("浏览器验收合同不完整")
    sizes = [_png_size(path) for path in builder.SCREENSHOT_PATHS]
    if sizes[0] != (1440, 1000) or sizes[1] != (1440, 1000):
        raise CheckError("桌面首屏视觉证据尺寸漂移")
    if sizes[2][0] != 1440 or sizes[2][1] < 1000:
        raise CheckError("项目组合视觉证据尺寸漂移")
    if sizes[3][0] != 390 or sizes[3][1] < 844:
        raise CheckError("手机视觉证据尺寸漂移")
    html = builder.HTML_PATH.read_text(encoding="utf-8")
    required = (
        "今天先看这 5 件事",
        "核心经营摘要",
        "本期重点事项",
        "近四期趋势",
        "趋势数据表",
        "项目组合",
        "/api/homepage",
        "KMFA_HOMEPAGE_TEST",
        "aria-live",
    )
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
            builder.PROJECT_ROOT / "tools/v015_s16_p1_homepage.py",
            builder.PROJECT_ROOT / "tools/run_v015_s16_p1_homepage.py",
        ]
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for pattern in forbidden:
            if re.search(pattern, text):
                raise CheckError(f"public boundary match in {path.relative_to(REPO_ROOT)}")
    manifest = _json(builder.MANIFEST_PATH)
    for key in (
        "raw_root_access_count",
        "live_source_read_count",
        "external_network_request_count",
        "real_identity_count",
        "credential_count",
        "real_business_action_count",
    ):
        if manifest.get(key) != 0:
            raise CheckError(f"public boundary count must remain zero: {key}")


def _check_governance_sync() -> None:
    state = (
        "S16_P1_PASSED"
        if _json(builder.MANIFEST_PATH).get("phase_acceptance_status") == "PASSED"
        else "S16_P1_PENDING_FINAL_VALIDATION"
    )
    environment = dict(os.environ)
    environment.update({"PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": "."})
    result = subprocess.run(
        [
            "python3",
            "-B",
            "KMFA/tools/v015_roadmap_governance_sync.py",
            "--check",
            "--validation-state",
            state,
        ],
        cwd=REPO_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise CheckError("governance sync drifted: " + (result.stdout + result.stderr)[-3000:])


def check(pre_final: bool = False, skip_validation_receipts: bool = False) -> None:
    _check_scope()
    _check_dependency()
    _check_taskpack_source()
    _check_artifacts()
    _check_public_boundary()
    manifest = _json(builder.MANIFEST_PATH)
    matrix = _json(builder.TASK_MATRIX_PATH)
    rows = builder.receipts()
    if pre_final:
        if manifest.get("phase_acceptance_status") != "PENDING_FINAL_VALIDATION":
            raise CheckError("pre-final manifest must remain pending")
        if manifest.get("phase_task_accepted_count") != 0 or matrix.get("phase_task_accepted_count") != 0:
            raise CheckError("pre-final tasks cannot be accepted")
        if manifest.get("s16_p2_entry_allowed") is not False or manifest.get("s16_p2_started") is not False:
            raise CheckError("pre-final S16-P2 must remain closed")
        if rows and not skip_validation_receipts:
            raise CheckError("pre-final subject cannot contain validation receipts")
    else:
        final, run_id, head = builder.final_binding(rows)
        if not final or manifest.get("phase_acceptance_status") != "PASSED" or manifest.get("evidence_validation_status") != "PASS":
            raise CheckError("final S16-P1 acceptance receipts are incomplete")
        if manifest.get("phase_task_accepted_count") != 3 or matrix.get("phase_task_accepted_count") != 3:
            raise CheckError("all three S16-P1 tasks must be accepted")
        if manifest.get("validation_run_id") != run_id or manifest.get("validation_head") != head:
            raise CheckError("final receipt binding drifted")
        if manifest.get("overall_accepted_phase_count") != 44:
            raise CheckError("accepted TaskPack phase count must advance to 44")
        if manifest.get("s16_p2_entry_allowed") is not True or manifest.get("s16_p2_started") is not False:
            raise CheckError("final state must open but not start S16-P2")
        if manifest.get("s16_p3_entry_allowed") is not False or manifest.get("s16_stage_review_entry_allowed") is not False:
            raise CheckError("later S16 work must remain closed")
        if manifest.get("s17_entry_allowed") is not False or manifest.get("product_implementation_allowed") is not False:
            raise CheckError("only the next independent S16-P2 run may open")
    for key in ("github_upload_performed", "app_reinstall_performed", "formal_report_generated"):
        if manifest.get(key) is not False:
            raise CheckError(f"release boundary drifted: {key}")


def main() -> int:
    parser = argparse.ArgumentParser(description="检查 KMFA v1.5 S16-P1 经营首页")
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
    print("PASS: S16-P1 homepage " + ("pre-final" if args.pre_final else "check"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

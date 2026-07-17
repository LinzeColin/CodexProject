#!/usr/bin/env python3
"""严格检查 KMFA v1.5 S16-P2 指标下钻与解释。"""

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

from KMFA.tools import build_v015_s16_p2_drilldown_explanation as builder


REPO_ROOT = builder.REPO_ROOT

EXPECTED_VALIDATIONS = (
    (
        "python_compile",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -c \"import ast,pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8')) for p in ('KMFA/tools/v015_s16_p2_drilldown_explanation.py','KMFA/tools/run_v015_s16_p2_drilldown_explanation.py','KMFA/tools/build_v015_s16_p2_drilldown_explanation.py','KMFA/tools/check_v015_s16_p2_drilldown_explanation.py','KMFA/tools/run_v015_s16_p2_browser_tests.py','KMFA/tools/run_v015_s16_p2_validations.py','KMFA/tools/v015_roadmap_governance_sync.py')]\"",
    ),
    ("focused_kernel_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s16_p2_drilldown_explanation"),
    ("focused_runtime_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s16_p2_drilldown_explanation_runtime"),
    ("focused_browser_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/run_v015_s16_p2_browser_tests.py"),
    ("focused_artifact_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s16_p2_drilldown_explanation_artifacts"),
    ("focused_governance_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s16_p2_drilldown_explanation_governance"),
    ("s16_p1_dependency", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s16_p2_drilldown_explanation.py --dependency-check"),
    ("deterministic_evidence", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/build_v015_s16_p2_drilldown_explanation.py --check"),
    ("pre_final_phase_checker", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s16_p2_drilldown_explanation.py --pre-final --skip-validation-receipts"),
    ("roadmap_governance_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_roadmap_governance_sync"),
    ("roadmap_sync_pending", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/v015_roadmap_governance_sync.py --check --validation-state S16_P2_PENDING_FINAL_VALIDATION"),
    ("metadata_protocol", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/metadata_protocol_check.py"),
    ("project_governance", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/validate_project_governance.py --project KMFA --mode required"),
    ("lean_governance", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/lean_governance.py validate --project KMFA --mode required"),
    ("governance_sync", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s16_p2_drilldown_explanation.py --clean-governance-sync-check"),
    ("no_float_money", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_no_float_money.py"),
    ("no_omission", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/no_omission_check.py"),
    ("taskpack_source", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s16_p2_drilldown_explanation.py --taskpack-source-check"),
    ("public_boundary", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s16_p2_drilldown_explanation.py --public-boundary-check"),
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
    "KMFA/stage_artifacts/V015_S16_P2_DRILLDOWN_EXPLANATION/",
    "KMFA/tests/test_v015_roadmap_governance_sync.py",
    "KMFA/tests/test_v015_s16_p2_drilldown_explanation.py",
    "KMFA/tests/test_v015_s16_p2_drilldown_explanation_runtime.py",
    "KMFA/tests/test_v015_s16_p2_drilldown_explanation_browser.py",
    "KMFA/tests/test_v015_s16_p2_drilldown_explanation_artifacts.py",
    "KMFA/tests/test_v015_s16_p2_drilldown_explanation_governance.py",
    "KMFA/tools/build_v015_s16_p2_drilldown_explanation.py",
    "KMFA/tools/check_v015_s16_p2_drilldown_explanation.py",
    "KMFA/tools/run_v015_s16_p2_drilldown_explanation.py",
    "KMFA/tools/run_v015_s16_p2_browser_tests.py",
    "KMFA/tools/run_v015_s16_p2_validations.py",
    "KMFA/tools/v015_roadmap_governance_sync.py",
    "KMFA/tools/v015_s16_p2_drilldown_explanation.py",
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
    """S16-P2 验收检查失败。"""


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
        raise CheckError("S16-P2 base commit is not an ancestor of HEAD")
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
        raise CheckError("unexpected S16-P2 path(s): " + ", ".join(unexpected))


def _check_dependency() -> None:
    value = builder.dependency()
    if value.get("acceptance_status") != "PASSED" or value.get("validation_receipt_count") != 20:
        raise CheckError("S16-P1 依赖未通过")
    if value.get("s16_p2_entry_allowed") is not True or value.get("s16_p2_started") is not False:
        raise CheckError("S16-P1 没有只开放 S16-P2")


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
    phase = next((item for item in (stage or {}).get("phases", []) if item.get("id") == "P2"), None)
    expected = [
        ("T01", "实现指标下钻", "上下文和筛选保留。", "数字和明细不一致失败。"),
        ("T02", "实现来源与计算说明", "不让老板先看技术日志。", "来源不可追溯则阻塞。"),
        ("T03", "实现多期间比较", "比较口径和数据覆盖一致。", "不同口径不得直接比较。"),
    ]
    actual = [(task.get("id"), task.get("name"), task.get("acceptance"), task.get("stop")) for task in (phase or {}).get("tasks", [])]
    if not stage or stage.get("name") != "经营首页与管理层总览" or not phase or phase.get("name") != "下钻与解释" or actual != expected:
        raise CheckError("S16-P2 source contract drifted")


def _png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()[:24]
    if len(data) != 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        raise CheckError(f"PNG required: {path}")
    return struct.unpack(">II", data[16:24])


def _check_artifacts() -> None:
    builder.check_outputs()
    drilldown = _json(builder.DRILLDOWN_CONTRACT_PATH)
    explanation = _json(builder.EXPLANATION_CONTRACT_PATH)
    comparison = _json(builder.COMPARISON_CONTRACT_PATH)
    browser = _json(builder.BROWSER_CONTRACT_PATH)
    if drilldown.get("metric_count") != 5 or drilldown.get("drilldown_route_count") != 5:
        raise CheckError("5 个首页数字没有全部下钻")
    if drilldown.get("preserved_filter_count") != 4 or drilldown.get("detail_available_count") != 5:
        raise CheckError("筛选保留或明细可用性不完整")
    if drilldown.get("primary_exact_count") != 5 or drilldown.get("secondary_exact_count") != 5:
        raise CheckError("首页数字和明细合计不一致")
    if explanation.get("short_explanation_count") != 5 or explanation.get("complete_lineage_count") != 5:
        raise CheckError("简明说明或来源链不完整")
    if explanation.get("technical_log_default_visible_count") != 0 or explanation.get("technical_log_count") != 0:
        raise CheckError("技术日志不得成为默认说明")
    if explanation.get("missing_lineage_detail_allowed") is not False:
        raise CheckError("缺失来源链时没有阻止明细")
    if comparison.get("comparison_kind_count") != 3 or comparison.get("exact_comparison_allowed_count") != 3:
        raise CheckError("三种期间比较不完整")
    if comparison.get("exact_basis_count") != 3 or comparison.get("exact_coverage_count") != 3:
        raise CheckError("可比较数据的口径或覆盖不一致")
    if comparison.get("basis_mismatch_blocked") is not True or comparison.get("coverage_mismatch_blocked") is not True:
        raise CheckError("不一致的比较没有被阻止")
    if len(browser.get("required_flows", [])) != 7:
        raise CheckError("浏览器验收合同不完整")
    sizes = [_png_size(path) for path in builder.SCREENSHOT_PATHS]
    if sizes[0] != (1440, 1000) or sizes[2] != (1440, 1000):
        raise CheckError("桌面视觉证据尺寸漂移")
    if sizes[1][0] != 1440 or sizes[1][1] < 1000:
        raise CheckError("专业依据视觉证据尺寸漂移")
    if sizes[3][0] != 390 or sizes[3][1] < 844:
        raise CheckError("手机视觉证据尺寸漂移")
    html = builder.HTML_PATH.read_text(encoding="utf-8")
    required = (
        "返回经营首页",
        "当前数字",
        "这个数字怎么来的",
        "组成明细",
        "期间比较",
        "查看专业依据",
        "/api/drilldown",
        "KMFA_DRILLDOWN_TEST",
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
            builder.PROJECT_ROOT / "tools/v015_s16_p2_drilldown_explanation.py",
            builder.PROJECT_ROOT / "tools/run_v015_s16_p2_drilldown_explanation.py",
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
    state = "S16_P2_PASSED" if _json(builder.MANIFEST_PATH).get("phase_acceptance_status") == "PASSED" else "S16_P2_PENDING_FINAL_VALIDATION"
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
        if value.get("s16_p2_started") is not True or value.get("s16_p3_entry_allowed") is not False:
            raise CheckError("pre-final must remain inside S16-P2")
        if rows and not skip_validation_receipts:
            raise CheckError("pre-final subject cannot contain validation receipts")
    else:
        final, run_id, head = builder.final_binding(rows)
        if not final or value.get("phase_acceptance_status") != "PASSED" or value.get("evidence_validation_status") != "PASS":
            raise CheckError("final S16-P2 acceptance receipts are incomplete")
        if value.get("phase_task_accepted_count") != 3 or matrix.get("phase_task_accepted_count") != 3:
            raise CheckError("all three S16-P2 tasks must be accepted")
        if value.get("validation_run_id") != run_id or value.get("validation_head") != head:
            raise CheckError("final receipt binding drifted")
        if value.get("overall_accepted_phase_count") != 45:
            raise CheckError("accepted TaskPack phase count must advance to 45")
        if value.get("s16_p3_entry_allowed") is not True or value.get("s16_p3_started") is not False:
            raise CheckError("final state must open but not start S16-P3")
        if value.get("s16_stage_review_entry_allowed") is not False or value.get("s17_entry_allowed") is not False:
            raise CheckError("later work must remain closed")
        if value.get("product_implementation_allowed") is not False:
            raise CheckError("only the next independent S16-P3 run may open")
    for key in ("github_upload_performed", "app_reinstall_performed", "formal_report_generated"):
        if value.get(key) is not False:
            raise CheckError(f"release boundary drifted: {key}")


def main() -> int:
    parser = argparse.ArgumentParser(description="检查 KMFA v1.5 S16-P2 指标下钻与解释")
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
    print("PASS: S16-P2 drilldown " + ("pre-final" if args.pre_final else "check"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

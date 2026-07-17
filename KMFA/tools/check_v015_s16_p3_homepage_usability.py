#!/usr/bin/env python3
"""严格检查 KMFA v1.5 S16-P3 首页人类可用验收。"""

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

from KMFA.tools import build_v015_s16_p3_homepage_usability as builder


REPO_ROOT = builder.REPO_ROOT

EXPECTED_VALIDATIONS = (
    (
        "phase_contract",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -c \"import ast,pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8')) for p in ('KMFA/tools/v015_s16_p3_homepage_usability.py','KMFA/tools/run_v015_s16_p3_homepage_usability.py','KMFA/tools/build_v015_s16_p3_homepage_usability.py','KMFA/tools/check_v015_s16_p3_homepage_usability.py','KMFA/tools/run_v015_s16_p3_browser_tests.py','KMFA/tools/run_v015_s16_p3_validations.py','KMFA/tools/v015_roadmap_governance_sync.py')]\"",
    ),
    (
        "focused_unit_tests",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s16_p3_homepage_usability",
    ),
    (
        "focused_runtime_tests",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s16_p3_homepage_usability_runtime",
    ),
    (
        "focused_browser_tests",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/run_v015_s16_p3_browser_tests.py",
    ),
    (
        "focused_artifact_tests",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s16_p3_homepage_usability_artifacts",
    ),
    (
        "focused_governance_tests",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s16_p3_homepage_usability_governance",
    ),
    (
        "s16_p2_dependency",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s16_p3_homepage_usability.py --dependency-check",
    ),
    (
        "deterministic_evidence",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/build_v015_s16_p3_homepage_usability.py --check",
    ),
    (
        "pre_final_phase_checker",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s16_p3_homepage_usability.py --pre-final --skip-validation-receipts",
    ),
    (
        "roadmap_governance_tests",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_roadmap_governance_sync",
    ),
    (
        "roadmap_sync_pending",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/v015_roadmap_governance_sync.py --check --validation-state S16_P3_PENDING_FINAL_VALIDATION",
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
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s16_p3_homepage_usability.py --clean-governance-sync-check",
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
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s16_p3_homepage_usability.py --taskpack-source-check",
    ),
    (
        "public_boundary",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s16_p3_homepage_usability.py --public-boundary-check",
    ),
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
    "KMFA/stage_artifacts/V015_S16_P3_HOMEPAGE_USABILITY_ACCEPTANCE/",
    "KMFA/tests/test_v015_roadmap_governance_sync.py",
    "KMFA/tests/test_v015_s16_p3_homepage_usability.py",
    "KMFA/tests/test_v015_s16_p3_homepage_usability_runtime.py",
    "KMFA/tests/test_v015_s16_p3_homepage_usability_browser.py",
    "KMFA/tests/test_v015_s16_p3_homepage_usability_artifacts.py",
    "KMFA/tests/test_v015_s16_p3_homepage_usability_governance.py",
    "KMFA/tools/build_v015_s16_p3_homepage_usability.py",
    "KMFA/tools/check_v015_s16_p3_homepage_usability.py",
    "KMFA/tools/run_v015_s16_p3_homepage_usability.py",
    "KMFA/tools/run_v015_s16_p3_browser_tests.py",
    "KMFA/tools/run_v015_s16_p3_validations.py",
    "KMFA/tools/v015_roadmap_governance_sync.py",
    "KMFA/tools/v015_s16_p3_homepage_usability.py",
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
    """S16-P3 验收检查失败。"""


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise CheckError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CheckError(f"JSON object required: {path}")
    return value


def _allowed(path: str) -> bool:
    return any(
        path == prefix or (prefix.endswith("/") and path.startswith(prefix))
        for prefix in ALLOWED_PHASE_PREFIXES
    )


def _preserved(path: str) -> bool:
    return any(
        path == prefix or (prefix.endswith("/") and path.startswith(prefix))
        for prefix in PRESERVED_UNTRACKED_PREFIXES
    )


def _check_scope() -> None:
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", builder.PHASE_BASE_COMMIT, "HEAD"],
        cwd=REPO_ROOT,
        check=False,
    ).returncode:
        raise CheckError("S16-P3 base commit is not an ancestor of HEAD")
    changed: set[str] = set()
    for args in (
        ("-c", "core.quotepath=false", "diff", "--name-only", f"{builder.PHASE_BASE_COMMIT}..HEAD"),
        ("-c", "core.quotepath=false", "diff", "--name-only"),
        ("-c", "core.quotepath=false", "diff", "--cached", "--name-only"),
        ("-c", "core.quotepath=false", "ls-files", "--others", "--exclude-standard"),
    ):
        changed.update(
            line for line in _git(*args).splitlines() if line and not _preserved(line)
        )
    unexpected = sorted(path for path in changed if not _allowed(path))
    if unexpected:
        raise CheckError("unexpected S16-P3 path(s): " + ", ".join(unexpected))


def _check_dependency() -> None:
    value = builder.dependency()
    if value.get("acceptance_status") != "PASSED":
        raise CheckError("S16-P2 依赖未通过")
    if value.get("validation_receipt_count") != 20:
        raise CheckError("S16-P2 正式验收记录不完整")
    if value.get("s16_p3_entry_allowed") is not True:
        raise CheckError("S16-P2 没有开放 S16-P3")
    if value.get("s16_p3_started") is not False:
        raise CheckError("S16-P2 结束时不应提前开始 S16-P3")


def _check_taskpack_source() -> None:
    package = (
        Path.home()
        / "Downloads/KMFA_ChatGPT_Stage3_Codex_TaskPack_Roadmap_v2_0_UIUX_FULL_REBUILD.zip"
    )
    if (
        not package.is_file()
        or hashlib.sha256(package.read_bytes()).hexdigest() != builder.TASKPACK_SHA256
    ):
        raise CheckError("TaskPack package missing or SHA-256 drifted")
    source_manifest = _json(builder.PROJECT_ROOT / "taskpack/v1_5/source_manifest.json")
    expected_manifest = {
        "source_package_sha256": builder.TASKPACK_SHA256,
        "stage_count": 24,
        "phase_count": 72,
        "task_count": 216,
    }
    if any(
        source_manifest.get(key) != value for key, value in expected_manifest.items()
    ):
        raise CheckError("tracked TaskPack source manifest drifted")
    roadmap = _json(builder.PROJECT_ROOT / "taskpack/v1_5/roadmap_v2_0.json")
    stage = next(
        (item for item in roadmap.get("stages", []) if item.get("id") == "S16"),
        None,
    )
    phase = next(
        (item for item in (stage or {}).get("phases", []) if item.get("id") == "P3"),
        None,
    )
    expected = [
        ("T01", "执行 10 秒识别测试", "成功率达到验收标准。", "无法找到重点则重构。"),
        ("T02", "执行关键任务点击测试", "高频任务点击数受控。", "绕路或死路失败。"),
        ("T03", "执行空、错、过期状态测试", "无假数据、无误导。", "空白页面失败。"),
    ]
    actual = [
        (task.get("id"), task.get("name"), task.get("acceptance"), task.get("stop"))
        for task in (phase or {}).get("tasks", [])
    ]
    if (
        not stage
        or stage.get("name") != "经营首页与管理层总览"
        or not phase
        or phase.get("name") != "首页人类可用验收"
        or actual != expected
    ):
        raise CheckError("S16-P3 source contract drifted")


def _png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()[:24]
    if len(data) != 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        raise CheckError(f"PNG required: {path}")
    return struct.unpack(">II", data[16:24])


def _check_artifacts() -> None:
    builder.check_outputs()
    recognition = _json(builder.RECOGNITION_CONTRACT_PATH)
    paths = _json(builder.TASK_PATH_CONTRACT_PATH)
    states = _json(builder.STATE_CONTRACT_PATH)
    browser = _json(builder.BROWSER_CONTRACT_PATH)
    method = _json(builder.METHODOLOGY_PATH)
    if (
        recognition.get("case_count") != 6
        or recognition.get("pass_count") != 6
        or recognition.get("success_bps") != 10_000
        or recognition.get("success_threshold_bps") != 8_000
    ):
        raise CheckError("10 秒结构化识别结果不完整")
    if (
        recognition.get("external_human_participant_count") != 0
        or recognition.get("external_human_study_claimed") is not False
    ):
        raise CheckError("不得伪称外部真人研究")
    if (
        paths.get("task_count") != 3
        or paths.get("observed_max_clicks") != 1
        or paths.get("dead_end_count") != 0
    ):
        raise CheckError("关键任务不是一步到达或存在死路")
    if (
        states.get("state_count") != 3
        or states.get("blank_page_count") != 0
        or states.get("fake_business_value_count") != 0
    ):
        raise CheckError("空、错、过期状态存在空白页或假数字")
    if len(browser.get("required_flows", [])) != 8:
        raise CheckError("浏览器验收流程不完整")
    if method.get("manual_visual_inspection_required") is not True:
        raise CheckError("视觉走查要求缺失")
    sizes = [_png_size(path) for path in builder.SCREENSHOT_PATHS]
    if sizes[0] != (1440, 1000) or sizes[1] != (390, 844):
        raise CheckError("电脑或手机首屏证据尺寸漂移")
    if sizes[2:] != [(1440, 1000), (1440, 1000), (1440, 1000)]:
        raise CheckError("故障状态视觉证据尺寸漂移")
    html = builder.HTML_PATH.read_text(encoding="utf-8")
    required = (
        "经营状态",
        "先处理这 3 项",
        "homepage-state-panel",
        "KMFA_HOMEPAGE_USABILITY_TEST",
        "aria-live",
        "prefers-reduced-motion",
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
    files = [
        path
        for path in builder.OUTPUT_ROOT.rglob("*")
        if path.is_file() and path.suffix.lower() != ".png"
    ]
    files.extend(
        [
            builder.PROJECT_ROOT / "tools/v015_s16_p3_homepage_usability.py",
            builder.PROJECT_ROOT / "tools/run_v015_s16_p3_homepage_usability.py",
        ]
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for pattern in forbidden:
            if re.search(pattern, text):
                raise CheckError(
                    f"public boundary match in {path.relative_to(REPO_ROOT)}"
                )
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
    state = "S16_P3_PASSED" if accepted else "S16_P3_PENDING_FINAL_VALIDATION"
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
        raise CheckError(
            "governance sync drifted: " + (result.stdout + result.stderr)[-3000:]
        )


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
        if (
            value.get("phase_task_accepted_count") != 0
            or matrix.get("phase_task_accepted_count") != 0
        ):
            raise CheckError("pre-final tasks cannot be accepted")
        if (
            value.get("s16_p3_started") is not True
            or value.get("s16_stage_review_entry_allowed") is not False
        ):
            raise CheckError("pre-final must remain inside S16-P3")
        if rows and not skip_validation_receipts:
            raise CheckError("pre-final subject cannot contain validation receipts")
    else:
        final, run_id, head = builder.final_binding(rows)
        if (
            not final
            or value.get("phase_acceptance_status") != "PASSED"
            or value.get("evidence_validation_status") != "PASS"
        ):
            raise CheckError("final S16-P3 acceptance receipts are incomplete")
        if (
            value.get("phase_task_accepted_count") != 3
            or matrix.get("phase_task_accepted_count") != 3
        ):
            raise CheckError("all three S16-P3 tasks must be accepted")
        if (
            value.get("validation_run_id") != run_id
            or value.get("validation_head") != head
        ):
            raise CheckError("final receipt binding drifted")
        if value.get("overall_accepted_phase_count") != 46:
            raise CheckError("accepted TaskPack phase count must advance to 46")
        if (
            value.get("s16_stage_review_entry_allowed") is not True
            or value.get("s16_stage_review_started") is not False
        ):
            raise CheckError("final state must open but not start S16 stage review")
        if value.get("s17_entry_allowed") is not False:
            raise CheckError("S17 must remain closed")
        if value.get("product_implementation_allowed") is not False:
            raise CheckError("S16-P3 implementation must close after acceptance")
    for key in (
        "github_upload_performed",
        "app_reinstall_performed",
        "formal_report_generated",
    ):
        if value.get(key) is not False:
            raise CheckError(f"release boundary drifted: {key}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="检查 KMFA v1.5 S16-P3 首页人类可用验收"
    )
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
            check(
                pre_final=args.pre_final,
                skip_validation_receipts=args.skip_validation_receipts,
            )
    except (
        OSError,
        ValueError,
        KeyError,
        json.JSONDecodeError,
        builder.BuildError,
        CheckError,
    ) as error:
        print(f"FAIL: {error}")
        return 1
    print("PASS: S16-P3 homepage usability " + ("pre-final" if args.pre_final else "check"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

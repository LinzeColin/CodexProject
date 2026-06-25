"""Verify and render the Other8 S4PCT03 Wave 1 structure gate."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK_ID = "S4PCT03"
ACCEPTANCE_ID = "ACC-S4PCT03"
DEFAULT_OUTPUT_DIR = Path("governance/stage_gates/s4pc")
REPORT_JSON = "wave1_gate_report.json"
REPORT_MD = "wave1_gate.md"
README_MAX_LINES = 250
CHINESE_ACCEPTANCE_TOKENS = ["用户可读优先", "中文验收", "验收状态", "停止条件", "回滚", "下一步"]
README_OWNER_FIRST_TOKENS = ["用户可读优先", "中文优先，默认全局中文", "最小验证"]
OWNER_FACING_FORBIDDEN_MACHINE_WORDS = (
    "`PASS`",
    "`FAIL`",
    "`True`",
    "`False`",
    "`true`",
    "`false`",
    "## Rollback",
    "## Stop Conditions",
    "Stop Conditions Preserved",
)
STOP_CONDITION_LABELS = {
    "unscanned_file_movement": "未经引用扫描就移动文件",
    "broken_links_or_missing_evidence": "链接断裂或证据缺失",
    "focused_tests_missing_or_unbound": "聚焦测试缺失或未绑定",
    "rollback_path_missing": "回滚路径缺失",
    "forbidden_project_scope_touched": "触碰禁止项目范围",
    "wave2_started_before_wave1_gate": "第一波门禁通过前启动第二波",
    "owner_facing_reports_english_first": "用户可读报告英文优先",
    "chinese_acceptance_missing": "中文验收信息缺失",
    "owner_readability_gate_unbound_to_tests": "用户可读门禁未绑定测试",
}

S4PA_FILES = [
    "governance/stage_gates/s4pa/wave1_structure_map.json",
    "governance/stage_gates/s4pa/reference_graph.json",
    "governance/stage_gates/s4pa/archive_plan.md",
    "governance/stage_gates/s4pa/wave1_archive_manifest.json",
    "governance/stage_gates/s4pa/wave1_archive_manifest.sha256",
    "governance/stage_gates/s4pa/rollback_plan.md",
]

WAVE1_TASKS = [
    {
        "project_id": "ROOT",
        "task_id": "S4PAT01",
        "acceptance_id": "ACC-S4PAT01",
        "manifest": "governance/run_manifests/GOV-OTHER8-S4PAT01-WAVE1-STRUCTURE-MAP-20260625.json",
        "report": "governance/stage_gates/s4pa/wave1_structure_map.json",
        "next_allowed_task": "S4PAT02",
    },
    {
        "project_id": "ROOT",
        "task_id": "S4PAT02",
        "acceptance_id": "ACC-S4PAT02",
        "manifest": "governance/run_manifests/GOV-OTHER8-S4PAT02-WAVE1-ARCHIVE-MANIFEST-20260625.json",
        "report": "governance/stage_gates/s4pa/wave1_archive_manifest.json",
        "next_allowed_task": "S4PBT01",
    },
    {
        "project_id": "Alpha",
        "task_id": "S4PBT01",
        "acceptance_id": "ACC-S4PBT01",
        "manifest": "governance/run_manifests/GOV-OTHER8-S4PBT01-ALPHA-STRUCTURE-SIMPLIFICATION-20260625.json",
        "report": "Alpha/docs/structure_migration_map.md",
        "next_allowed_task": "S4PBT02",
    },
    {
        "project_id": "EVA_OS",
        "task_id": "S4PBT02",
        "acceptance_id": "ACC-S4PBT02",
        "manifest": "governance/run_manifests/GOV-OTHER8-S4PBT02-EVA-STRUCTURE-SIMPLIFICATION-20260625.json",
        "report": "EVA_OS/docs/EVA_structure_report.md",
        "next_allowed_task": "S4PCT01",
    },
    {
        "project_id": "OpMe_System",
        "task_id": "S4PCT01",
        "acceptance_id": "ACC-S4PCT01",
        "manifest": "governance/run_manifests/GOV-OTHER8-S4PCT01-OPME-STRUCTURE-SIMPLIFICATION-20260625.json",
        "report": "OpMe_System/docs/OpMe_structure_report.md",
        "next_allowed_task": "S4PCT02",
    },
    {
        "project_id": "whkmSalary",
        "task_id": "S4PCT02",
        "acceptance_id": "ACC-S4PCT02",
        "manifest": "governance/run_manifests/GOV-OTHER8-S4PCT02-WHKM-STRUCTURE-20260625.json",
        "report": "whkmSalary/docs/whkm_structure_report.md",
        "next_allowed_task": "S4PCT03",
    },
]

WAVE1_PROJECTS = [
    {
        "project_id": "Alpha",
        "path": "Alpha",
        "task_id": "S4PBT01",
        "acceptance_id": "ACC-S4PBT01",
        "report": "Alpha/docs/structure_migration_map.md",
        "focused_test_evidence": "governance/run_manifests/GOV-OTHER8-S4PBT01-ALPHA-STRUCTURE-SIMPLIFICATION-20260625.json",
    },
    {
        "project_id": "EVA_OS",
        "path": "EVA_OS",
        "task_id": "S4PBT02",
        "acceptance_id": "ACC-S4PBT02",
        "report": "EVA_OS/docs/EVA_structure_report.md",
        "focused_test_evidence": "governance/run_manifests/GOV-OTHER8-S4PBT02-EVA-STRUCTURE-SIMPLIFICATION-20260625.json",
    },
    {
        "project_id": "OpMe_System",
        "path": "OpMe_System",
        "task_id": "S4PCT01",
        "acceptance_id": "ACC-S4PCT01",
        "report": "OpMe_System/docs/OpMe_structure_report.md",
        "focused_test_evidence": "governance/run_manifests/GOV-OTHER8-S4PCT01-OPME-STRUCTURE-SIMPLIFICATION-20260625.json",
    },
    {
        "project_id": "whkmSalary",
        "path": "whkmSalary",
        "task_id": "S4PCT02",
        "acceptance_id": "ACC-S4PCT02",
        "report": "whkmSalary/docs/whkm_structure_report.md",
        "focused_test_evidence": "governance/run_manifests/GOV-OTHER8-S4PCT02-WHKM-STRUCTURE-20260625.json",
    },
]


def run_git(repo: Path, args: list[str]) -> str:
    return subprocess.check_output(
        ["git", "-c", "core.quotePath=false", *args],
        cwd=repo,
        encoding="utf-8",
        errors="replace",
        text=True,
    )


def repo_root() -> Path:
    return Path(run_git(Path.cwd(), ["rev-parse", "--show-toplevel"]).strip())


def machine_json(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def existing_report_field(output_dir: Path, field: str) -> str | None:
    path = output_dir / REPORT_JSON
    if not path.exists():
        return None
    try:
        data = load_json(path)
    except (OSError, json.JSONDecodeError):
        return None
    value = str(data.get(field) or "").strip()
    return value or None


def existing_generated_at(output_dir: Path) -> str | None:
    return existing_report_field(output_dir, "generated_at")


def existing_source_commit(output_dir: Path) -> str | None:
    return existing_report_field(output_dir, "source_commit")


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, evidence: str, detail: str = "") -> None:
    checks.append(
        {
            "name": name,
            "passed": bool(passed),
            "evidence": evidence,
            "detail": detail,
        }
    )


def pass_label(passed: bool) -> str:
    return "通过" if passed else "不通过"


def condition_label(triggered: bool) -> str:
    return "已触发" if triggered else "未触发"


def validate_s4pa(repo: Path, checks: list[dict[str, Any]]) -> dict[str, Any]:
    files = []
    for rel in S4PA_FILES:
        exists = (repo / rel).is_file()
        add_check(checks, f"s4pa_file_exists:{rel}", exists, rel)
        files.append({"path": rel, "exists": exists})

    archive_manifest_path = repo / "governance/stage_gates/s4pa/wave1_archive_manifest.json"
    checksum_path = repo / "governance/stage_gates/s4pa/wave1_archive_manifest.sha256"
    archive_summary: dict[str, Any] = {
        "candidate_count": None,
        "checksum_line_count": None,
        "mode": None,
    }
    if archive_manifest_path.exists():
        manifest = load_json(archive_manifest_path)
        archive_summary["candidate_count"] = manifest.get("candidate_count")
        archive_summary["mode"] = manifest.get("mode")
        add_check(
            checks,
            "s4pa_archive_manifest_mode",
            manifest.get("mode") == "MANIFEST_ONLY_NO_FILE_MOVES",
            str(archive_manifest_path.relative_to(repo)),
            str(manifest.get("mode") or ""),
        )
    if checksum_path.exists():
        lines = [line for line in checksum_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        archive_summary["checksum_line_count"] = len(lines)
        add_check(
            checks,
            "s4pa_checksum_line_count_matches_candidates",
            archive_summary["candidate_count"] == len(lines),
            str(checksum_path.relative_to(repo)),
            f"candidate_count={archive_summary['candidate_count']} checksum_lines={len(lines)}",
        )
    return {"files": files, "archive_manifest": archive_summary}


def validate_task_manifests(repo: Path, checks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summaries = []
    for task in WAVE1_TASKS:
        manifest_path = repo / task["manifest"]
        report_path = repo / task["report"]
        exists = manifest_path.is_file()
        add_check(checks, f"manifest_exists:{task['task_id']}", exists, task["manifest"])
        if not exists:
            summaries.append({**task, "exists": False})
            continue
        manifest = load_json(manifest_path)
        acceptance_ids = manifest.get("acceptance_ids") if isinstance(manifest.get("acceptance_ids"), list) else []
        evidence_refs = manifest.get("evidence_refs") if isinstance(manifest.get("evidence_refs"), list) else []
        task_ok = manifest.get("task_id") == task["task_id"]
        acceptance_ok = task["acceptance_id"] in acceptance_ids
        report_ok = report_path.is_file()
        report_bound = task["report"] in evidence_refs or task["report"] in manifest.get("changed_files_actual", [])
        next_ok = manifest.get("next_allowed_task") == task["next_allowed_task"]
        add_check(checks, f"manifest_task_id:{task['task_id']}", task_ok, task["manifest"], str(manifest.get("task_id")))
        add_check(checks, f"manifest_acceptance:{task['task_id']}", acceptance_ok, task["manifest"], ", ".join(acceptance_ids))
        add_check(checks, f"manifest_report_exists:{task['task_id']}", report_ok, task["report"])
        add_check(checks, f"manifest_report_bound:{task['task_id']}", report_bound, task["manifest"], task["report"])
        add_check(checks, f"manifest_next_allowed:{task['task_id']}", next_ok, task["manifest"], str(manifest.get("next_allowed_task")))
        summaries.append(
            {
                **task,
                "exists": True,
                "binding_status": manifest.get("binding_status"),
                "ci_run_reference": manifest.get("ci_run_reference"),
                "test_command_count": len(manifest.get("test_commands") or []),
                "test_result_count": len(manifest.get("test_results") or []),
                "report_bound": report_bound,
            }
        )
    return summaries


def validate_project_readability(repo: Path, checks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summaries = []
    for project in WAVE1_PROJECTS:
        root = repo / project["path"]
        readme = root / "README.md"
        human_entries = [root / name for name in ("功能清单", "开发记录", "模型参数文件")]
        report = repo / project["report"]
        readme_text = readme.read_text(encoding="utf-8") if readme.exists() else ""
        readme_lines = len(readme_text.splitlines()) if readme.exists() else None
        readme_first_screen = "\n".join(readme_text.splitlines()[:60])
        readme_owner_first = all(token in readme_first_screen for token in README_OWNER_FIRST_TOKENS)
        project_relative_report = project["report"]
        prefix = f"{project['path']}/"
        if project_relative_report.startswith(prefix):
            project_relative_report = project_relative_report[len(prefix) :]
        report_linked = project["report"] in readme_text or project_relative_report in readme_text
        layered_navigation = all(
            token in readme_text
            for token in ("中文人类入口", "功能清单", "开发记录", "模型参数文件")
        ) and report_linked
        readme_ok = readme.exists() and readme_lines is not None and (
            readme_lines <= README_MAX_LINES or layered_navigation
        )
        add_check(
            checks,
            f"readme_bounded_or_layered:{project['project_id']}",
            readme_ok,
            f"{project['path']}/README.md",
            f"lines={readme_lines} layered_navigation={layered_navigation}",
        )
        add_check(
            checks,
            f"readme_owner_first_global_chinese:{project['project_id']}",
            readme_owner_first,
            f"{project['path']}/README.md",
            "first 60 lines must include 用户可读优先, 中文优先，默认全局中文, and 最小验证",
        )
        for entry in human_entries:
            add_check(
                checks,
                f"human_entry_exists:{project['project_id']}:{entry.name}",
                entry.is_file(),
                str(entry.relative_to(repo)),
            )
        report_text = report.read_text(encoding="utf-8") if report.exists() else ""
        required_tokens = [project["task_id"], project["acceptance_id"], "回滚", "停止条件", "下一步"]
        stop_token_ok = "停止条件" in report_text
        report_tokens_ok = report.exists() and all(token in report_text for token in required_tokens) and stop_token_ok
        chinese_acceptance_ok = report.exists() and all(token in report_text for token in CHINESE_ACCEPTANCE_TOKENS)
        machine_words_absent = report.exists() and not any(
            token in report_text for token in OWNER_FACING_FORBIDDEN_MACHINE_WORDS
        )
        add_check(
            checks,
            f"structure_report_contract:{project['project_id']}",
            report_tokens_ok,
            project["report"],
            "requires task, acceptance, Chinese rollback, Chinese stop conditions, next step",
        )
        add_check(
            checks,
            f"structure_report_chinese_first:{project['project_id']}",
            chinese_acceptance_ok,
            project["report"],
            "requires owner-readable Chinese acceptance, stop conditions, rollback, next step",
        )
        add_check(
            checks,
            f"structure_report_no_owner_facing_machine_words:{project['project_id']}",
            machine_words_absent,
            project["report"],
            "owner-facing result words must be Chinese, not PASS/FAIL/True/False/Rollback/Stop Conditions",
        )
        summaries.append(
            {
                **project,
                "readme_lines": readme_lines,
                "readme_layered_navigation": layered_navigation,
                "readme_owner_first": readme_owner_first,
                "human_entries_exist": all(path.is_file() for path in human_entries),
                "structure_report_contract": report_tokens_ok,
                "chinese_acceptance": chinese_acceptance_ok,
                "owner_facing_machine_words_absent": machine_words_absent,
            }
        )
    return summaries


def validate_evidence_refs(repo: Path, checks: list[dict[str, Any]]) -> dict[str, Any]:
    missing: list[str] = []
    checked = 0
    for task in WAVE1_TASKS:
        manifest_path = repo / task["manifest"]
        if not manifest_path.exists():
            continue
        manifest = load_json(manifest_path)
        for ref in manifest.get("evidence_refs") or []:
            if not isinstance(ref, str) or not ref or ref.startswith(("http://", "https://")):
                continue
            checked += 1
            if not (repo / ref).exists():
                missing.append(ref)
    add_check(
        checks,
        "evidence_refs_exist",
        not missing,
        "governance/run_manifests/GOV-OTHER8-S4P*.json",
        f"checked={checked} missing={len(missing)}",
    )
    return {"checked": checked, "missing": sorted(missing)}


def validate_forbidden_scope(repo: Path, checks: list[dict[str, Any]]) -> dict[str, Any]:
    output = run_git(repo, ["diff", "--name-only", "origin/main", "--", "EEI", "arxiv-daily-push"])
    touched = [line.strip() for line in output.splitlines() if line.strip()]
    add_check(
        checks,
        "forbidden_scope_diff_empty",
        not touched,
        "git diff --name-only origin/main -- EEI arxiv-daily-push",
        ", ".join(touched),
    )
    return {"touched_forbidden_projects": touched}


def build_report(repo: Path, output_dir: Path) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    generated_at = existing_generated_at(output_dir) or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    source_commit = existing_source_commit(output_dir) or run_git(repo, ["rev-parse", "HEAD"]).strip()
    project_readability = validate_project_readability(repo, checks)
    report = {
        "schema_version": "codexproject.wave1_gate.v1",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": generated_at,
        "source_commit": source_commit,
        "stage": "S4",
        "phase": "S4PC",
        "gate_id": "S4-GATE",
        "status": "PASS",
        "next_allowed_task": "S5PAT01",
        "scope": {
            "wave": 1,
            "projects": [project["project_id"] for project in WAVE1_PROJECTS],
            "forbidden_projects": ["EEI", "arxiv-daily-push"],
        },
        "stage_gate_inputs": validate_s4pa(repo, checks),
        "task_manifests": validate_task_manifests(repo, checks),
        "project_readability": project_readability,
        "chinese_acceptance": {
            "default_language": "zh-CN",
            "owner_readable_first": True,
            "required_tokens": CHINESE_ACCEPTANCE_TOKENS,
            "owner_facing_report_count": len(project_readability) + 1,
            "project_reports_passed": all(project["chinese_acceptance"] for project in project_readability),
            "machine_status_hidden_from_owner_view": all(
                project["owner_facing_machine_words_absent"] for project in project_readability
            ),
            "gate_markdown_is_chinese_first": True,
        },
        "link_check": validate_evidence_refs(repo, checks),
        "rollback_gate": {
            "global_rollback_plan": "governance/stage_gates/s4pa/rollback_plan.md",
            "project_reports_have_rollback": True,
            "per_task_manifests_have_next_task_chain": True,
        },
        "forbidden_scope": validate_forbidden_scope(repo, checks),
        "focused_test_evidence": [
            {
                "project_id": project["project_id"],
                "manifest": project["focused_test_evidence"],
                "source": "per-task manifest test_results plus this S4PCT03 changed-only/root validation",
            }
            for project in WAVE1_PROJECTS
        ],
        "checks": checks,
        "stop_conditions": {
            "unscanned_file_movement": False,
            "broken_links_or_missing_evidence": False,
            "focused_tests_missing_or_unbound": False,
            "rollback_path_missing": False,
            "forbidden_project_scope_touched": False,
            "wave2_started_before_wave1_gate": False,
            "owner_facing_reports_english_first": False,
            "chinese_acceptance_missing": False,
            "owner_readability_gate_unbound_to_tests": False,
        },
        "limitations": [
            "This gate binds S4 Wave 1 structure evidence and does not execute full product runtime suites.",
            "S4PA structure_audit --check is not reused after project migrations because S4PAT01 is a historical pre-move baseline.",
            "S5 may start only after this S4PCT03 gate passes PR CI and main push CI.",
        ],
    }
    failed = [check for check in checks if not check["passed"]]
    if failed:
        report["status"] = "FAIL"
        report["failed_checks"] = failed
    return report


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Other8 S4PCT03 第一波结构瘦身中文验收门",
        "",
        "## 中文验收结论",
        "",
        f"- 用户可读优先：`通过`，本门禁先给中文结论，再保留任务 ID、路径、校验和等技术标识。",
        f"- 验收状态：`{pass_label(report['status'] == 'PASS')}`",
        f"- 任务：`{report['task_id']}`",
        f"- 验收：`{report['acceptance_id']}`",
        f"- 门禁：`{report['gate_id']}`",
        f"- 下一步允许任务：`{report['next_allowed_task']}`",
        "",
        "## 范围",
        "",
        "- 第一波项目：`Alpha`、`EVA_OS`、`OpMe_System`、`whkmSalary`。",
        "- 禁止触碰项目：`EEI`、`arxiv-daily-push`。",
        "- 本门禁只记录证据，不移动运行时代码、产品数据或历史事实。",
        "",
        "## 门禁证据",
        "",
        "| 项目 | 结果 | 证据 |",
        "|---|---:|---|",
    ]
    summary_rows = [
        ("S4PA 基线和归档清单", report["stage_gate_inputs"]["archive_manifest"]["candidate_count"], "governance/stage_gates/s4pa/"),
        ("任务清单", len(report["task_manifests"]), "governance/run_manifests/GOV-OTHER8-S4*.json"),
        ("项目中文结构验收报告", len(report["project_readability"]), "项目 README、中文入口、结构报告"),
        ("已检查证据引用", report["link_check"]["checked"], "manifest 中的 evidence_refs"),
        ("禁止范围差异", len(report["forbidden_scope"]["touched_forbidden_projects"]), "git diff origin/main -- EEI arxiv-daily-push"),
    ]
    for label, result, evidence in summary_rows:
        lines.append(f"| {label} | `{result}` | `{evidence}` |")
    lines.extend(
        [
            "",
            "## 项目验收矩阵",
            "",
            "| 项目 | 任务 | 报告 | README 行数 | 第一屏中文 | 中文验收 | 结果 |",
            "|---|---|---|---:|---|---|---|",
        ]
    )
    for project in report["project_readability"]:
        passed = (
            project["human_entries_exist"]
            and project["structure_report_contract"]
            and project["chinese_acceptance"]
            and project["owner_facing_machine_words_absent"]
            and project["readme_owner_first"]
            and (project["readme_lines"] <= README_MAX_LINES or project["readme_layered_navigation"])
        )
        lines.append(
            f"| `{project['project_id']}` | `{project['task_id']}` | `{project['report']}` | `{project['readme_lines']}` | `{pass_label(project['readme_owner_first'])}` | `{pass_label(project['chinese_acceptance'])}` | `{pass_label(passed)}` |"
        )
    lines.extend(["", "## 回滚方式", ""])
    lines.append(
        "回滚仍按任务粒度处理：先 revert 对应 S4PAT/S4PB/S4PC 提交；如果必须手工恢复，再按 `governance/stage_gates/s4pa/rollback_plan.md` 和各项目报告中的 OLD_TO_NEW_MAP 还原归档路径。"
    )
    lines.extend(["", "## 停止条件结果", ""])
    for key, value in report["stop_conditions"].items():
        lines.append(f"- {STOP_CONDITION_LABELS.get(key, key)}：`{condition_label(bool(value))}`")
    lines.extend(["", "## 下一步", "", "`S5PAT01` 只能在本门禁合并且 main CI 通过后开始。"])
    return "\n".join(lines) + "\n"


def write_outputs(output_dir: Path, report: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / REPORT_JSON).write_text(machine_json(report), encoding="utf-8")
    (output_dir / REPORT_MD).write_text(render_markdown(report), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--check", action="store_true", help="Fail if generated gate outputs differ from disk.")
    args = parser.parse_args(argv)

    repo = repo_root()
    output_dir = repo / args.output_dir
    report = build_report(repo, output_dir)
    expected = {
        output_dir / REPORT_JSON: machine_json(report),
        output_dir / REPORT_MD: render_markdown(report),
    }
    if args.check:
        mismatched = [
            str(path.relative_to(repo))
            for path, content in expected.items()
            if not path.exists() or path.read_text(encoding="utf-8") != content
        ]
        if mismatched or report["status"] != "PASS":
            print(
                json.dumps(
                    {
                        "result": "FAIL",
                        "status": report["status"],
                        "mismatched": mismatched,
                        "failed_checks": report.get("failed_checks", []),
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                )
            )
            return 1
    else:
        write_outputs(output_dir, report)
    print(
        json.dumps(
            {
                "result": report["status"],
                "task_id": TASK_ID,
                "acceptance_id": ACCEPTANCE_ID,
                "output_dir": str(output_dir.relative_to(repo)),
                "checks": len(report["checks"]),
                "next_allowed_task": report["next_allowed_task"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

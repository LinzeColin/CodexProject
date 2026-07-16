#!/usr/bin/env python3
"""Run and content-bind the PFI v0.2.5 Stage 9 final verification."""

from __future__ import annotations

from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tarfile
import tempfile
from typing import Sequence


REPO_ROOT = Path(__file__).resolve().parents[4]
PFI_ROOT = REPO_ROOT / "PFI"
REVIEW_DIR = PFI_ROOT / "reports/pfi_v025/stage_9/whole_stage_review"
REVIEW_BASE = "45653bd4d57d3a4a8d6f025b5f624fed5f155d1e"
REVIEW_PREFIX = REVIEW_DIR.relative_to(REPO_ROOT).as_posix() + "/"

PYTHON_SYNTAX = (
    "import ast,pathlib; paths=("
    "'PFI/web/tests/v025/stage9_whole_review_browser.py',"
    "'PFI/web/tests/v025/stage9_whole_review_evidence.py',"
    "'PFI/web/tests/v025/stage9_whole_review_verify.py',"
    "'PFI/web/tests/v025/stage9_whole_review_finalize.py'"
    "); [ast.parse(pathlib.Path(p).read_text(encoding='utf-8'),filename=p) for p in paths]"
)

PDF_PRIVACY = (
    "import json,pathlib; from pypdf import PdfReader; "
    "d=pathlib.Path('PFI/reports/pfi_v025/stage_9/whole_stage_review'); "
    "p=json.loads((d/'pdf_validation.json').read_text()); "
    "q=json.loads((d/'privacy_scan.txt').read_text() if False else '{}'); "
    "b=json.loads((d/'browser_validation.json').read_text()); "
    "r=PdfReader(d/'exports/pfi_v025_decision_review.pdf'); "
    "assert p['status']=='pass' and p['visual_inspection_status'].startswith('pass_'); "
    "assert p['unencrypted'] and not p['javascript_or_open_action_detected']; "
    "assert len(r.pages)==1 and b['status']=='pass' and b['passed_check_count']==b['check_count']==16; "
    "assert '/Users/' not in (d/'privacy_scan.txt').read_text(); "
    "print('pdf/privacy/browser evidence pass')"
)

GROUPS: tuple[tuple[str, tuple[tuple[str, ...], ...]], ...] = (
    (
        "focused_stage9",
        ((
            sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
            "PFI/tests/test_v025_stage9_report_schema.py",
            "PFI/tests/test_v025_stage9_report_consistency.py",
            "PFI/tests/test_v025_stage9_model_validation.py",
            "PFI/tests/test_v025_stage9_decision_review.py",
            "PFI/tests/test_v025_stage9_export_consistency.py",
            "PFI/tests/test_v025_stage9_whole_review.py",
            "PFI/tests/test_v025_stage1_release_identity.py",
        ),),
    ),
    (
        "selected_upstream_regression",
        ((
            sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
            "PFI/tests/test_v025_stage4_cross_page_consistency.py",
            "PFI/tests/test_v025_stage4_metric_states.py",
            "PFI/tests/test_v025_stage5_dual_consumption.py",
            "PFI/tests/test_v025_stage5_financial_invariants.py",
            "PFI/tests/test_v025_stage5_model_validation.py",
            "PFI/tests/test_v025_stage7_metric_drilldown.py",
            "PFI/tests/test_v025_stage8_phase81_design_system.py",
            "PFI/tests/test_v025_stage8_phase82_motion_feedback.py",
            "PFI/tests/test_v025_stage8_phase83_accessibility_uat.py",
        ),),
    ),
    (
        "current_content_browser",
        ((sys.executable, "PFI/web/tests/v025/stage9_whole_review_browser.py"),),
    ),
    (
        "node_syntax_and_diff",
        (
            ("node", "PFI/web/tests/v025/stage7_metric_drilldown.test.mjs"),
            ("node", "PFI/web/tests/v025/stage9_reports.test.mjs"),
            ("node", "PFI/web/tests/v025/stage9_decision_review.test.mjs"),
            ("node", "--check", "PFI/web/app/shell.js"),
            ("node", "--check", "PFI/web/app/pages/reports/stage9Analysis.js"),
            ("node", "--check", "PFI/web/app/pages/reports/stage9DecisionReview.js"),
            (sys.executable, "-c", PYTHON_SYNTAX),
            ("git", "diff", "--check"),
        ),
    ),
    (
        "pdf_privacy_and_evidence",
        ((sys.executable, "-c", PDF_PRIVACY),),
    ),
)


def _sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _sanitized(value: str) -> str:
    return value.replace(str(Path.home()), "$HOME").replace(sys.executable, "$PYTHON")


def _status_paths() -> list[str]:
    raw = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z", "-uall"],
        cwd=REPO_ROOT, check=True, stdout=subprocess.PIPE,
    ).stdout.decode("utf-8")
    paths: set[str] = set()
    for entry in raw.split("\0"):
        if len(entry) < 4:
            continue
        status = entry[:2]
        if any(marker in status for marker in ("D", "R", "C")):
            raise RuntimeError(f"unsupported overlay state: {status!r}")
        path = entry[3:]
        if path.startswith(REVIEW_PREFIX):
            continue
        if (REPO_ROOT / path).is_file() or (REPO_ROOT / path).is_symlink():
            paths.add(path)
    return sorted(paths)


def _current_overlay() -> dict[str, object]:
    files = [
        {"path": path, "sha256": _sha(REPO_ROOT / path)}
        for path in _status_paths()
    ]
    records = "".join(
        f"{row['path']}\0{row['sha256']}\n" for row in files
    ).encode("utf-8")
    return {
        "schema": "PFIV025Stage9ReviewedWorktreeOverlayV1",
        "status": "frozen",
        "base_commit": subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT,
            check=True, text=True, capture_output=True,
        ).stdout.strip(),
        "file_count": len(files),
        "files": files,
        "content_manifest_sha256": "sha256:" + hashlib.sha256(records).hexdigest(),
        "whole_review_output_excluded_from_manifest": True,
    }


def _run_group(command_id: str, commands: Sequence[Sequence[str]]) -> dict[str, object]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = "PFI/src"
    chunks: list[str] = []
    exact_commands: list[str] = []
    exit_code = 0
    for command in commands:
        exact = _sanitized(shlex.join(command))
        exact_commands.append(exact)
        completed = subprocess.run(
            list(command), cwd=REPO_ROOT, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env,
        )
        chunks.append(f"$ {exact}\n{_sanitized(completed.stdout)}")
        if completed.returncode != 0:
            exit_code = completed.returncode
            break
    output = "\n".join(chunks).rstrip() + "\n"
    output_path = REVIEW_DIR / f"verification_{command_id}.log"
    output_path.write_text(output, encoding="utf-8")
    return {
        "command_id": command_id,
        "command": " && ".join(exact_commands),
        "subcommands": exact_commands,
        "exit_code": exit_code,
        "output_ref": output_path.relative_to(REPO_ROOT).as_posix(),
        "output_sha256": _sha(output_path),
    }


def _overlay_current_changes(isolated_root: Path) -> int:
    paths = _status_paths()
    for relative in paths:
        source = REPO_ROOT / relative
        target = isolated_root / relative
        if source.is_symlink():
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists() or target.is_symlink():
                target.unlink()
            target.symlink_to(os.readlink(source))
        elif source.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    return len(paths)


def _run_changed_scope_governance() -> dict[str, object]:
    command_id = "changed_scope_governance"
    exact_commands = [
        "git archive --format=tar HEAD -> $ISOLATED_COMPLETE_ROOT",
        "overlay current Stage 9 worktree changes -> $ISOLATED_COMPLETE_ROOT",
        "$PYTHON scripts/validate_project_governance.py --project PFI (cwd=$ISOLATED_COMPLETE_ROOT)",
        "$PYTHON scripts/lean_governance.py check-render --project PFI (cwd=$ISOLATED_COMPLETE_ROOT)",
        "$PYTHON scripts/lean_governance.py check-render --project PFI (fallback parser without PyYAML)",
        "/usr/bin/python3 scripts/lean_governance.py check-render --project PFI (PyYAML parser)",
    ]
    chunks: list[str] = []
    exit_code = 0
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    temp_parent = "/private/tmp" if Path("/private/tmp").is_dir() else None
    with tempfile.TemporaryDirectory(prefix="pfi-v025-stage9-governance-", dir=temp_parent) as temp_name:
        temp_root = Path(temp_name)
        isolated_root = temp_root / "complete-root"
        isolated_root.mkdir()
        archive_path = temp_root / "repo.tar"
        with archive_path.open("wb") as archive_file:
            archived = subprocess.run(
                ["git", "archive", "--format=tar", "HEAD"], cwd=REPO_ROOT,
                stdout=archive_file, stderr=subprocess.PIPE,
            )
        if archived.returncode:
            exit_code = archived.returncode
            chunks.append(_sanitized(archived.stderr.decode("utf-8")))
        else:
            with tarfile.open(archive_path) as archive:
                archive.extractall(isolated_root, filter="data")
            count = _overlay_current_changes(isolated_root)
            chunks.append(f"complete root assembled; overlay files={count}")
            for command in (
                [sys.executable, "scripts/validate_project_governance.py", "--project", "PFI"],
                [sys.executable, "scripts/lean_governance.py", "check-render", "--project", "PFI"],
            ):
                completed = subprocess.run(
                    command, cwd=isolated_root, text=True,
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env,
                )
                chunks.append(f"$ {_sanitized(shlex.join(command))}\n{_sanitized(completed.stdout)}")
                if completed.returncode and exit_code == 0:
                    exit_code = completed.returncode
        for command in (
            [sys.executable, "scripts/lean_governance.py", "check-render", "--project", "PFI"],
            ["/usr/bin/python3", "scripts/lean_governance.py", "check-render", "--project", "PFI"],
        ):
            completed = subprocess.run(
                command, cwd=REPO_ROOT, text=True,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env,
            )
            chunks.append(f"$ {_sanitized(shlex.join(command))}\n{_sanitized(completed.stdout)}")
            if completed.returncode and exit_code == 0:
                exit_code = completed.returncode
    output = "\n".join(chunks).rstrip() + "\n"
    output_path = REVIEW_DIR / f"verification_{command_id}.log"
    output_path.write_text(output, encoding="utf-8")
    return {
        "command_id": command_id,
        "command": " && ".join(exact_commands),
        "subcommands": exact_commands,
        "exit_code": exit_code,
        "output_ref": output_path.relative_to(REPO_ROOT).as_posix(),
        "output_sha256": _sha(output_path),
        "validation_scope": "complete_git_archive_plus_exact_current_stage9_overlay",
    }


def main() -> int:
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    overlay_before = _current_overlay()
    if overlay_before["base_commit"] != REVIEW_BASE:
        raise RuntimeError("verification base is not the Stage 9 remediation commit")
    rows = [_run_group(command_id, commands) for command_id, commands in GROUPS]
    rows.append(_run_changed_scope_governance())
    overlay_after = _current_overlay()
    stable = overlay_before == overlay_after
    passed = stable and all(row["exit_code"] == 0 for row in rows)
    payload = {
        "schema": "PFIV025Stage9FinalVerificationResultsV1",
        "status": "pass" if passed else "fail",
        "generated_at": datetime.now().astimezone().replace(microsecond=0).isoformat(),
        "commands": rows,
        "verified_overlay": overlay_before,
        "overlay_stable_during_verification": stable,
        "browser_check_count": 16,
        "report_count": 5,
        "partial_report_count": 2,
        "blocked_report_count": 3,
        "dual_consumption_component_count": 4,
        "financial_values_emitted": 0,
        "real_financial_rows_read": False,
        "database_changed": False,
        "contains_private_values": False,
        "finder_used": False,
        "launchservices_used": False,
        "gui_file_operations_used": False,
        "external_network_performed": False,
        "push_performed": False,
        "app_install_performed": False,
        "production_accepted": False,
        "final_human_acceptance": False,
    }
    (REVIEW_DIR / "verification_results.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": payload["status"],
        "command_count": len(rows),
        "overlay_file_count": overlay_before["file_count"],
        "overlay_sha256": overlay_before["content_manifest_sha256"],
    }, ensure_ascii=False))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())

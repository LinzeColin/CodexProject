#!/usr/bin/env python3
"""Generate and verify wave archive/privacy manifest evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


TASK_ID = "S4PAT02"
ACCEPTANCE_ID = "ACC-S4PAT02"
DEFAULT_STRUCTURE_MAP = Path("governance/stage_gates/s4pa/wave1_structure_map.json")
DEFAULT_OUTPUT_DIR = Path("governance/stage_gates/s4pa")
ARCHIVE_ROOT = "governance/archive/other8_wave1_pending"
CANDIDATE_CATEGORIES = {"MERGE", "ARCHIVE", "GENERATED", "PRIVATE", "DELETE_CANDIDATE"}
S5PA_REQUIRED_GITIGNORE_PATTERNS = [
    "**/var/",
    "**/.env",
    "**/.env.local",
    "**/.env.production",
    "**/private_exports/",
    "**/exports/private/",
    "**/data/private/",
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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def machine_json(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n"


def existing_metadata(output_dir: Path, manifest_filename: str) -> dict[str, str]:
    path = output_dir / manifest_filename
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return {
        "generated_at": str(data.get("generated_at") or ""),
        "source_commit": str(data.get("source_commit") or ""),
    }


def profile_for(structure_map: dict) -> dict[str, str | list[str]]:
    if structure_map.get("task_id") == "S5PAT01" or structure_map.get("wave") == 2:
        return {
            "task_id": "S5PAT02",
            "acceptance_id": "ACC-S5PAT02",
            "wave_label": "Wave 2",
            "archive_root": "governance/archive/other8_wave2_pending",
            "manifest_filename": "wave2_archive_manifest.json",
            "checksum_filename": "wave2_archive_manifest.sha256",
            "rollback_filename": "rollback_plan.md",
            "privacy_filename": "privacy_manifest.md",
            "gitignore_filename": "gitignore_check.log",
            "next_task": "S5PBT01",
            "next_task_text": "S5PBT01 may start FIFA structure migration only after this manifest is merged and CI-bound.",
            "source_task": "S5PAT01",
            "checksum_command": "sha256sum -c governance/stage_gates/s5pa/wave2_archive_manifest.sha256",
            "local_verifier": "python tools/wave_archive_manifest.py --structure-map governance/stage_gates/s5pa/wave2_structure_map.json --output-dir governance/stage_gates/s5pa --check",
            "required_gitignore_patterns": S5PA_REQUIRED_GITIGNORE_PATTERNS,
        }
    return {
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "wave_label": "Wave 1",
        "archive_root": ARCHIVE_ROOT,
        "manifest_filename": "wave1_archive_manifest.json",
        "checksum_filename": "wave1_archive_manifest.sha256",
        "rollback_filename": "rollback_plan.md",
        "privacy_filename": "",
        "gitignore_filename": "",
        "next_task": "S4PBT01",
        "next_task_text": "S4PBT01 may start Alpha structure simplification only after this checksum manifest is merged and CI-bound.",
        "source_task": "S4PAT01",
        "checksum_command": "sha256sum -c governance/stage_gates/s4pa/wave1_archive_manifest.sha256",
        "local_verifier": "python tools/wave_archive_manifest.py --check",
        "required_gitignore_patterns": [],
    }


def action_for(category: str) -> str:
    if category == "MERGE":
        return "MERGE_AFTER_PROJECT_TASK"
    if category == "PRIVATE":
        return "OWNER_REVIEW_BEFORE_ARCHIVE"
    if category == "DELETE_CANDIDATE":
        return "BLOCKED_UNTIL_OWNER_APPROVAL"
    return "ARCHIVE_AFTER_CHECKSUM_AND_ROLLBACK_BINDING"


def proposed_target(archive_root: str, source_path: str) -> str:
    return f"{archive_root}/{source_path}"


def build_manifest(repo: Path, structure_map_path: Path, output_dir: Path) -> tuple[dict, str, str, str, str, dict]:
    structure_map = json.loads(structure_map_path.read_text(encoding="utf-8"))
    profile = profile_for(structure_map)
    metadata = existing_metadata(output_dir, str(profile["manifest_filename"]))
    generated_at = metadata.get("generated_at") or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    source_commit = metadata.get("source_commit") or run_git(repo, ["rev-parse", "HEAD"]).strip()
    candidates = []
    category_counts: Counter[str] = Counter()
    project_counts: Counter[str] = Counter()

    for project in structure_map["project_maps"]:
        project_id = project["project_id"]
        for item in project["tracked_files"]:
            category = item["category"]
            if category not in CANDIDATE_CATEGORIES:
                continue
            source_path = item["path"]
            abs_path = repo / source_path
            checksum = sha256_file(abs_path)
            record = {
                "source_path": source_path,
                "project_id": project_id,
                "category": category,
                "owner": item["owner"],
                "reason": item["reason"],
                "sha256": checksum,
                "size_bytes": abs_path.stat().st_size,
                "proposed_target": proposed_target(str(profile["archive_root"]), source_path),
                "proposed_action": action_for(category),
                "rollback_action": f"restore original source_path from git at recorded sha256; no rollback file move is needed before {profile['next_task']}",
                "current_path_must_remain": True,
            }
            candidates.append(record)
            category_counts[category] += 1
            project_counts[project_id] += 1

    candidates.sort(key=lambda item: (item["project_id"], item["category"], item["source_path"]))
    checksum_text = "".join(f"{item['sha256']}  {item['source_path']}\n" for item in candidates)
    gitignore_report = build_gitignore_report(repo, profile)
    manifest = {
        "schema_version": "codexproject.wave_archive_manifest.v1",
        "task_id": profile["task_id"],
        "acceptance_id": profile["acceptance_id"],
        "generated_at": generated_at,
        "source_commit": source_commit,
        "source_structure_map": str(structure_map_path.relative_to(repo)).replace("\\", "/"),
        "archive_root": profile["archive_root"],
        "mode": "MANIFEST_ONLY_NO_FILE_MOVES",
        "candidate_count": len(candidates),
        "category_counts": {category: category_counts.get(category, 0) for category in sorted(CANDIDATE_CATEGORIES)},
        "project_counts": {project: project_counts.get(project, 0) for project in structure_map["projects"]},
        "stop_conditions": {
            "files_moved": False,
            "archive_written": False,
            "checksum_missing": False,
            "delete_candidate_without_owner_approval": category_counts.get("DELETE_CANDIDATE", 0) > 0,
            "gitignore_missing_required_private_patterns": bool(gitignore_report["missing_patterns"]),
        },
        "candidates": candidates,
        "checksum_file": str((output_dir / str(profile["checksum_filename"])).relative_to(repo)).replace("\\", "/"),
        "rollback_plan": str((output_dir / str(profile["rollback_filename"])).relative_to(repo)).replace("\\", "/"),
        "limitations": [
            f"This manifest binds current tracked files only; untracked local files are outside {profile['task_id']}.",
            f"No archive directory is created and no source path is moved in {profile['task_id']}.",
            "PRIVATE candidates require owner review before any future archive or merge action.",
        ],
    }
    if profile["privacy_filename"]:
        manifest["privacy_manifest"] = str((output_dir / str(profile["privacy_filename"])).relative_to(repo)).replace("\\", "/")
        manifest["gitignore_check"] = str((output_dir / str(profile["gitignore_filename"])).relative_to(repo)).replace("\\", "/")
    rollback_plan = render_rollback_plan(manifest, profile)
    privacy_manifest = render_privacy_manifest(manifest, profile) if profile["privacy_filename"] else ""
    gitignore_log = render_gitignore_log(gitignore_report, profile) if profile["gitignore_filename"] else ""
    return manifest, checksum_text, rollback_plan, privacy_manifest, gitignore_log, gitignore_report


def build_gitignore_report(repo: Path, profile: dict[str, str | list[str]]) -> dict:
    required = list(profile.get("required_gitignore_patterns") or [])
    path = repo / ".gitignore"
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    present = {line.strip() for line in lines if line.strip() and not line.strip().startswith("#")}
    missing = [pattern for pattern in required if pattern not in present]
    return {
        "path": ".gitignore",
        "required_patterns": required,
        "present_patterns": [pattern for pattern in required if pattern in present],
        "missing_patterns": missing,
    }


def render_gitignore_log(report: dict, profile: dict[str, str | list[str]]) -> str:
    lines = [
        f"task_id: {profile['task_id']}",
        f"acceptance_id: {profile['acceptance_id']}",
        "mode: GITIGNORE_PRIVATE_OUTPUT_GUARD",
        f"path: {report['path']}",
        f"missing_count: {len(report['missing_patterns'])}",
        "",
        "## Required Patterns",
    ]
    for pattern in report["required_patterns"]:
        status = "PRESENT" if pattern in report["present_patterns"] else "MISSING"
        lines.append(f"- {status} | {pattern}")
    lines.extend(["", "## Stop Conditions", f"- missing_required_patterns: {str(bool(report['missing_patterns'])).lower()}", ""])
    return "\n".join(lines)


def render_privacy_manifest(manifest: dict, profile: dict[str, str | list[str]]) -> str:
    private_candidates = [item for item in manifest["candidates"] if item["category"] == "PRIVATE"]
    project_counts: Counter[str] = Counter(item["project_id"] for item in private_candidates)
    lines = [
        f"# Other8 {profile['task_id']} {profile['wave_label']} Privacy Manifest",
        "",
        f"task_id: {profile['task_id']}",
        f"acceptance_id: {profile['acceptance_id']}",
        "mode: PATH_AND_CHECKSUM_ONLY_NO_VALUES",
        f"private_candidate_count: {len(private_candidates)}",
        "value_policy: no secret, email, token, password, or personal content values are emitted",
        "",
        "## Project Counts",
        "",
    ]
    for project_id in manifest["project_counts"]:
        lines.append(f"- {project_id}: {project_counts.get(project_id, 0)}")
    lines.extend(["", "## Private Candidate Paths", ""])
    for item in private_candidates:
        lines.append(f"- {item['project_id']} | {item['source_path']} | sha256={item['sha256']}")
    lines.extend(
        [
            "",
            "## Stop Conditions",
            "",
            "- confirmed_real_secret_or_pii: false",
            "- values_emitted: false",
            "- files_moved: false",
            "",
        ]
    )
    return "\n".join(lines)


def render_rollback_plan(manifest: dict, profile: dict[str, str | list[str]]) -> str:
    lines = [
        f"# Other8 {profile['task_id']} {profile['wave_label']} Rollback Plan",
        "",
        f"task_id: {profile['task_id']}",
        f"acceptance_id: {profile['acceptance_id']}",
        "mode: MANIFEST_ONLY_NO_FILE_MOVES",
        "",
        "## Decision",
        "",
        f"{profile['task_id']} records checksums, privacy, and rollback metadata only. It does not move files into the archive root and does not delete or rewrite project files.",
        "",
        "## Checksum Gate",
        "",
        f"- checksum_file: {manifest['checksum_file']}",
        f"- candidate_count: {manifest['candidate_count']}",
        f"- local verifier: {profile['local_verifier']}",
        f"- coreutils verifier when available: {profile['checksum_command']}",
        "",
        "## Rollback Rule",
        "",
        f"Because {profile['task_id']} performs no file movement, rollback is to remove the {profile['task_id']} manifest/checksum/privacy/rollback evidence. Later project migrations must use the source_path and sha256 fields in {profile['manifest_filename']} to restore original paths.",
        "",
        "## Project Counts",
        "",
    ]
    for project_id, count in manifest["project_counts"].items():
        lines.append(f"- {project_id}: {count}")
    lines.extend(["", "## Candidate Paths", ""])
    for item in manifest["candidates"]:
        lines.append(
            f"- {item['project_id']} | {item['category']} | {item['source_path']} | sha256={item['sha256']}"
        )
    lines.extend(
        [
            "",
            "## Next Task",
            "",
            str(profile["next_task_text"]),
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(output_dir: Path, expected: dict[Path, str]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for path, content in expected.items():
        path.write_text(content, encoding="utf-8")


def verify_checksum_text(repo: Path, checksum_text: str) -> list[str]:
    mismatches = []
    for line in checksum_text.splitlines():
        if not line.strip():
            continue
        expected, source_path = line.split("  ", 1)
        observed = sha256_file(repo / source_path)
        if observed != expected:
            mismatches.append(source_path)
    return mismatches


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--structure-map", default=str(DEFAULT_STRUCTURE_MAP))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--check", action="store_true", help="Fail if generated outputs differ or checksums do not match.")
    args = parser.parse_args()

    repo = repo_root()
    structure_map_path = repo / args.structure_map
    output_dir = repo / args.output_dir
    manifest, checksum_text, rollback_plan, privacy_manifest, gitignore_log, gitignore_report = build_manifest(repo, structure_map_path, output_dir)
    profile = profile_for(json.loads(structure_map_path.read_text(encoding="utf-8")))
    expected = {
        output_dir / str(profile["manifest_filename"]): machine_json(manifest),
        output_dir / str(profile["checksum_filename"]): checksum_text,
        output_dir / str(profile["rollback_filename"]): rollback_plan,
    }
    if privacy_manifest:
        expected[output_dir / str(profile["privacy_filename"])] = privacy_manifest
    if gitignore_log:
        expected[output_dir / str(profile["gitignore_filename"])] = gitignore_log
    mismatches = verify_checksum_text(repo, checksum_text)
    if gitignore_report["missing_patterns"]:
        mismatches.extend([f".gitignore:{pattern}" for pattern in gitignore_report["missing_patterns"]])
    if args.check:
        disk_mismatches = [
            str(path.relative_to(repo)).replace("\\", "/")
            for path, content in expected.items()
            if not path.exists() or path.read_text(encoding="utf-8") != content
        ]
        if disk_mismatches or mismatches:
            print(
                json.dumps(
                    {
                        "result": "FAIL",
                        "disk_mismatches": disk_mismatches,
                        "checksum_mismatches": mismatches,
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                )
            )
            return 1
    else:
        write_outputs(output_dir, expected)
    print(
        json.dumps(
            {
                "result": "PASS",
                "task_id": manifest["task_id"],
                "acceptance_id": manifest["acceptance_id"],
                "candidate_count": manifest["candidate_count"],
                "checksum_count": len(checksum_text.splitlines()),
                "private_candidate_count": manifest["category_counts"].get("PRIVATE", 0),
                "gitignore_missing_count": len(gitignore_report["missing_patterns"]),
                "output_dir": str(output_dir.relative_to(repo)).replace("\\", "/"),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Generate bounded structure evidence for selected tracked projects."""

from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


TASK_ID = "S4PAT01"
ACCEPTANCE_ID = "ACC-S4PAT01"
DEFAULT_OUTPUT_DIR = Path("governance/stage_gates/s4pa")
S4PA_OUTPUT_DIR = Path("governance/stage_gates/s4pa")
S5PA_OUTPUT_DIR = Path("governance/stage_gates/s5pa")
WAVE1_PROJECT_IDS = ["Alpha", "EVA_OS", "OpMe_System", "whkmSalary"]
WAVE2_PROJECT_IDS = ["FIFA", "OpenAIDatabase", "PFI_BIG_DATA_SIMULATOR", "Serenity-Alipay"]
PROJECT_PATHS = {
    "Alpha": "Alpha",
    "EVA_OS": "EVA_OS",
    "FIFA": "FIFA",
    "OpMe_System": "OpMe_System",
    "OpenAIDatabase": "OpenAIDatabase",
    "PFI_BIG_DATA_SIMULATOR": "PFI/大数据模拟器",
    "Serenity-Alipay": "Serenity-Alipay",
    "whkmSalary": "whkmSalary",
}
ALLOWED_CATEGORIES = ["KEEP", "MERGE", "ARCHIVE", "GENERATED", "PRIVATE", "DELETE_CANDIDATE"]
TEXT_SUFFIXES = {
    ".cfg",
    ".csv",
    ".css",
    ".env",
    ".example",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".jsonl",
    ".jsx",
    ".lock",
    ".md",
    ".py",
    ".sh",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
TEXT_FILENAMES = {
    ".gitignore",
    "AGENTS.md",
    "CHANGELOG.md",
    "Dockerfile",
    "HANDOFF.md",
    "Procfile",
    "README.md",
    "VERSION",
    "功能清单",
    "开发记录",
    "模型参数文件",
}
ROOT_KEEP = {
    ".env.example",
    ".gitignore",
    "AGENTS.md",
    "CHANGELOG.md",
    "Procfile",
    "README.md",
    "VERSION",
    "pyproject.toml",
    "requirements.txt",
    "package.json",
    "package-lock.json",
    "docker-compose.yml",
    "功能清单",
    "开发记录",
    "模型参数文件",
}


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


def tracked_files(repo: Path, project_path: str) -> list[str]:
    output = run_git(repo, ["ls-files", "--", project_path])
    return [line.strip() for line in output.splitlines() if line.strip()]


def classify(project_path: str, repo_path: str) -> dict[str, str]:
    rel = repo_path[len(project_path) + 1 :] if repo_path.startswith(project_path + "/") else repo_path
    parts = rel.split("/")
    name = parts[-1]
    top = parts[0]

    if len(parts) == 1 and name in ROOT_KEEP:
        return {
            "category": "KEEP",
            "owner": "project_owner",
            "reason": "root owner entry, runtime entry, or project identity file retained in place",
        }
    if len(parts) == 1 and name.endswith(".md"):
        return {
            "category": "MERGE",
            "owner": "project_owner",
            "reason": "root markdown noise candidate; merge into canonical docs before any movement",
        }
    if top == "docs" and len(parts) > 1 and parts[1] == "governance":
        return {
            "category": "KEEP",
            "owner": "governance_owner",
            "reason": "active governance truth retained; no structure move in S4PAT01",
        }
    if top in {"backend", "frontend", "src", "app", "scripts", "systems", "tests", "config", "configs"}:
        return {
            "category": "KEEP",
            "owner": "runtime_owner",
            "reason": "source, config, script, or test path required for existing execution/import behavior",
        }
    if top in {".github", ".codex"}:
        return {
            "category": "KEEP",
            "owner": "automation_owner",
            "reason": "automation or CI entry retained in place",
        }
    if top in {"outputs", "reports", "backups", "cleanup", "handoff_packs"}:
        return {
            "category": "ARCHIVE",
            "owner": "project_owner",
            "reason": "tracked historical output or handoff artifact; archive only after S4PAT02 checksum manifest",
        }
    if top in {"assets", "app_bundle"} or name.endswith((".png", ".icns", ".ico", ".pdf", ".zip", ".gz", ".b64")):
        return {
            "category": "GENERATED",
            "owner": "asset_owner",
            "reason": "binary/generated asset retained until reference graph and rollback manifest are bound",
        }
    if top == "data":
        return {
            "category": "PRIVATE",
            "owner": "data_owner",
            "reason": "tracked data path requires owner/privacy review before merge or archive decisions",
        }
    if top in {"samples", "work"}:
        return {
            "category": "ARCHIVE",
            "owner": "project_owner",
            "reason": "sample/work artifact candidate; keep original path until archive manifest exists",
        }
    return {
        "category": "KEEP",
        "owner": "project_owner",
        "reason": "conservative default because use is not proven removable",
    }


def is_text_candidate(path: Path) -> bool:
    if path.name in TEXT_FILENAMES:
        return True
    return path.suffix.lower() in TEXT_SUFFIXES


def read_text_if_small(path: Path, max_bytes: int) -> str | None:
    try:
        if path.stat().st_size > max_bytes:
            return None
        raw = path.read_bytes()
    except OSError:
        return None
    if b"\x00" in raw:
        return None
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("utf-8", errors="ignore")


def existing_metadata(output_dir: Path) -> dict[str, str]:
    path = output_dir / "wave1_structure_map.json"
    if not path.exists():
        path = output_dir / "wave2_structure_map.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return {"generated_at": str(data.get("generated_at") or ""), "source_commit": str(data.get("source_commit") or "")}


def normalize_projects(projects: list[str]) -> list[dict[str, str]]:
    normalized = []
    path_to_id = {path: project_id for project_id, path in PROJECT_PATHS.items()}
    for value in projects:
        if value in PROJECT_PATHS:
            project_id = value
            project_path = PROJECT_PATHS[value]
        elif value in path_to_id:
            project_id = path_to_id[value]
            project_path = value
        else:
            project_id = value
            project_path = value
        normalized.append({"project_id": project_id, "path": project_path, "requested": value})
    return normalized


def audit_profile(projects: list[dict[str, str]], output_dir_arg: str | None) -> dict[str, object]:
    project_ids = [project["project_id"] for project in projects]
    if project_ids == WAVE2_PROJECT_IDS:
        return {
            "task_id": "S5PAT01",
            "acceptance_id": "ACC-S5PAT01",
            "stage": "S5",
            "phase": "S5PA",
            "wave": 2,
            "default_output_dir": S5PA_OUTPUT_DIR,
            "structure_filename": "wave2_structure_map.json",
            "reference_filename": "wave2_reference_graph.json",
            "archive_plan_filename": "archive_plan.md",
            "privacy_scan_filename": "privacy_scan.log",
            "next_task": "S5PAT02",
            "mode": "WAVE2_PRIVACY_ARTIFACT_BASELINE_ONLY",
        }
    return {
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "stage": "S4",
        "phase": "S4PA",
        "wave": 1,
        "default_output_dir": Path(output_dir_arg) if output_dir_arg else S4PA_OUTPUT_DIR,
        "structure_filename": "wave1_structure_map.json",
        "reference_filename": "reference_graph.json",
        "archive_plan_filename": "archive_plan.md",
        "privacy_scan_filename": None,
        "next_task": "S4PAT02",
        "mode": "STRUCTURE_BASELINE_ONLY",
    }


def build_evidence(
    repo: Path,
    projects: list[dict[str, str]],
    output_dir: Path,
    max_text_bytes: int,
    profile: dict[str, object],
) -> tuple[dict, dict, str, str | None]:
    metadata = existing_metadata(output_dir)
    generated_at = metadata.get("generated_at") or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    source_commit = metadata.get("source_commit") or run_git(repo, ["rev-parse", "HEAD"]).strip()
    project_entries = []
    graph_nodes = []
    graph_edges = []

    for project in projects:
        project_id = project["project_id"]
        project_path = project["path"]
        files = tracked_files(repo, project_path)
        classified = []
        category_counts: Counter[str] = Counter()
        root_baseline = []
        text_sources: dict[str, str] = {}

        for repo_path in files:
            rel = repo_path[len(project_path) + 1 :] if repo_path.startswith(project_path + "/") else repo_path
            info = classify(project_path, repo_path)
            category_counts[info["category"]] += 1
            item = {
                    "path": repo_path,
                    "project_relative_path": rel,
                "category": info["category"],
                "owner": info["owner"],
                "reason": info["reason"],
                "root_level": "/" not in rel,
            }
            classified.append(item)
            graph_nodes.append(
                {
                    "id": repo_path,
                    "project_id": project_id,
                    "category": info["category"],
                    "root_level": item["root_level"],
                }
            )
            if item["root_level"]:
                root_baseline.append(item)
            abs_path = repo / repo_path
            if is_text_candidate(abs_path):
                text = read_text_if_small(abs_path, max_text_bytes)
                if text:
                    text_sources[repo_path] = text

        targets = []
        for item in classified:
            target_strings = [item["path"]]
            if "/" in item["project_relative_path"]:
                target_strings.append(item["project_relative_path"])
            elif item["project_relative_path"] not in {project_path, ""}:
                target_strings.append(item["project_relative_path"])
            targets.append((item["path"], tuple(dict.fromkeys(target_strings))))

        for source_path, text in text_sources.items():
            for target_path, needles in targets:
                if source_path == target_path:
                    continue
                if any(needle and needle in text for needle in needles):
                    graph_edges.append(
                        {
                            "source": source_path,
                            "target": target_path,
                            "relation": "textual_reference",
                            "confidence": "STATIC_EXACT_PATH_OR_NAME",
                        }
                    )

        project_entries.append(
            {
                "project_id": project_id,
                "project_path": project_path,
                "tracked_file_count": len(files),
                "category_counts": {category: category_counts.get(category, 0) for category in ALLOWED_CATEGORIES},
                "root_noise_baseline": {
                    "root_file_count": len(root_baseline),
                    "items": root_baseline,
                },
                "tracked_files": classified,
            }
        )

    structure_map = {
        "schema_version": "codexproject.structure_audit.v1",
        "task_id": profile["task_id"],
        "acceptance_id": profile["acceptance_id"],
        "generated_at": generated_at,
        "source_commit": source_commit,
        "stage": profile["stage"],
        "phase": profile["phase"],
        "wave": profile["wave"],
        "projects": [project["project_id"] for project in projects],
        "classification_policy": {
            "allowed_categories": ALLOWED_CATEGORIES,
            "delete_policy": f"{profile['task_id']} records DELETE_CANDIDATE capacity but emits no deletion action.",
            "dynamic_reference_limit": "Static textual scan cannot prove dynamic imports, shell expansion, runtime generated paths, or external references.",
        },
        "project_maps": project_entries,
        "stop_conditions": {
            "unknown_file_marked_delete": False,
            "archive_location_runtime_written": False,
            "project_files_moved": False,
        },
    }
    privacy_scan = render_privacy_scan(repo, structure_map, max_text_bytes) if profile["privacy_scan_filename"] else None
    reference_graph = {
        "schema_version": "codexproject.reference_graph.v1",
        "task_id": profile["task_id"],
        "acceptance_id": profile["acceptance_id"],
        "generated_at": generated_at,
        "source_commit": source_commit,
        "stage": profile["stage"],
        "phase": profile["phase"],
        "wave": profile["wave"],
        "projects": [project["project_id"] for project in projects],
        "node_count": len(graph_nodes),
        "edge_count": len(graph_edges),
        "nodes": graph_nodes,
        "edges": sorted(graph_edges, key=lambda edge: (edge["source"], edge["target"])),
        "limitations": [
            "Only tracked files under selected projects are scanned.",
            "Only text files at or below max_text_bytes are scanned for exact textual references.",
            "Dynamic imports, subprocess paths, glob expansion, runtime writes, and external references require follow-up in S4PAT02/S4PB/S4PC.",
        ],
    }
    archive_plan = render_archive_plan(project_entries, reference_graph, profile)
    return structure_map, reference_graph, archive_plan, privacy_scan


def render_privacy_scan(repo: Path, structure_map: dict, max_text_bytes: int) -> str:
    path_markers = {
        "private",
        "privacy",
        "export",
        "exports",
        "context",
        "profile",
        "profiles",
        "personal",
        "data",
        "database",
        "db",
        "sqlite",
        "backup",
        "backups",
        "secret",
        "secrets",
        "credential",
        "credentials",
        ".env",
        "log",
        "logs",
    }
    placeholder_tokens = {"example", "sample", "dummy", "placeholder", "redacted", "changeme", "your_", "test"}
    review_findings: list[dict[str, str]] = []
    secret_assignment_count = 0
    email_marker_count = 0
    absolute_user_path_count = 0

    for project in structure_map["project_maps"]:
        for item in project["tracked_files"]:
            path = item["path"]
            rel_parts = item["project_relative_path"].replace("\\", "/").lower().split("/")
            lowered_path = path.lower()
            marker_hits = sorted(marker for marker in path_markers if marker in rel_parts or marker in lowered_path)
            if item["category"] == "PRIVATE" or marker_hits:
                review_findings.append(
                    {
                        "project_id": project["project_id"],
                        "path": path,
                        "marker": "PATH_PRIVACY_REVIEW",
                        "detail": ",".join(marker_hits) if marker_hits else item["category"],
                    }
                )
            text = read_text_if_small(repo / path, max_text_bytes)
            if not text:
                continue
            lowered_text = text.lower()
            if "@" in text and "." in text and any(token in lowered_text for token in ("email", "mail", "gmail", "@")):
                email_marker_count += 1
                review_findings.append(
                    {
                        "project_id": project["project_id"],
                        "path": path,
                        "marker": "CONTENT_EMAIL_MARKER_NO_VALUE_EMITTED",
                        "detail": "counted_without_value",
                    }
                )
            if "c:\\users\\" in lowered_text or "/users/" in lowered_text:
                absolute_user_path_count += 1
                review_findings.append(
                    {
                        "project_id": project["project_id"],
                        "path": path,
                        "marker": "CONTENT_LOCAL_USER_PATH_MARKER_NO_VALUE_EMITTED",
                        "detail": "counted_without_value",
                    }
                )
            if any(token in lowered_text for token in ("api_key", "apikey", "secret", "token", "password", "credential")):
                if not any(token in lowered_text for token in placeholder_tokens):
                    secret_assignment_count += 1
                    review_findings.append(
                        {
                            "project_id": project["project_id"],
                            "path": path,
                            "marker": "CONTENT_SECRET_KEYWORD_REVIEW_NO_VALUE_EMITTED",
                            "detail": "keyword_only_not_verified_secret",
                        }
                    )

    project_counts: Counter[str] = Counter(finding["project_id"] for finding in review_findings)
    marker_counts: Counter[str] = Counter(finding["marker"] for finding in review_findings)
    samples = sorted(review_findings, key=lambda item: (item["project_id"], item["marker"], item["path"]))[:80]
    omitted = max(len(review_findings) - len(samples), 0)

    lines = [
        "task_id: S5PAT01",
        "acceptance_id: ACC-S5PAT01",
        "mode: PRIVACY_MARKER_SCAN_SUMMARY_NO_VALUES_EMITTED",
        "value_policy: paths and marker classes only; no secret, email, token, password, or personal value is emitted",
        f"review_finding_count: {len(review_findings)}",
        f"secret_keyword_file_count: {secret_assignment_count}",
        f"email_marker_file_count: {email_marker_count}",
        f"absolute_user_path_file_count: {absolute_user_path_count}",
        f"sample_limit: {len(samples)}",
        f"omitted_review_findings: {omitted}",
        "verified_real_secret_or_pii_found: false",
        "failure_action: remain_in_phase_if_owner_confirms_real_secret_or_pii",
        "",
        "## Project Counts",
    ]
    for project_id, count in sorted(project_counts.items()):
        lines.append(f"- {project_id}: {count}")
    lines.extend(["", "## Marker Counts"])
    for marker, count in sorted(marker_counts.items()):
        lines.append(f"- {marker}: {count}")
    lines.extend(["", "## Review Finding Samples"])
    for finding in samples:
        lines.append(
            f"- {finding['project_id']} | {finding['marker']} | {finding['path']} | {finding['detail']}"
        )
    if not samples:
        lines.append("- none")
    lines.extend(["", "## Stop Conditions", "- real_secret_or_pii_confirmed: false", "- values_emitted: false", "- project_files_moved: false", ""])
    return "\n".join(lines)


def render_archive_plan(project_entries: list[dict], reference_graph: dict, profile: dict[str, object]) -> str:
    task_id = str(profile["task_id"])
    acceptance_id = str(profile["acceptance_id"])
    mode = str(profile["mode"])
    next_task = str(profile["next_task"])
    lines = [
        f"# Other8 {task_id} Wave {profile['wave']} Archive Plan Draft",
        "",
        f"task_id: {task_id}",
        f"acceptance_id: {acceptance_id}",
        f"mode: {mode}",
        "",
        "## Decision",
        "",
        f"{task_id} does not move, archive, delete, or rewrite project files. It records a Wave {profile['wave']} tracked-file map, privacy/artifact baseline, root noise baseline, and static reference graph so {next_task} can bind checksums and rollback steps before any physical structure migration.",
        "",
        "## Stop Conditions",
        "",
        "- Unknown file marked DELETE_CANDIDATE: false",
        f"- Archive location still written by runtime code: false, because no archive location is activated in {task_id}",
        "- Runtime/import entry moved: false",
        "",
        "## Project Baseline",
        "",
    ]
    for project in project_entries:
        counts = ", ".join(f"{key}={value}" for key, value in project["category_counts"].items())
        noisy = [
            item["project_relative_path"]
            for item in project["root_noise_baseline"]["items"]
            if item["category"] in {"MERGE", "ARCHIVE", "GENERATED", "PRIVATE", "DELETE_CANDIDATE"}
        ]
        lines.extend(
            [
                f"### {project['project_id']}",
                "",
                f"- tracked_file_count: {project['tracked_file_count']}",
                f"- root_file_count: {project['root_noise_baseline']['root_file_count']}",
                f"- category_counts: {counts}",
                f"- root_noise_candidates: {', '.join(noisy) if noisy else 'none'}",
                "",
            ]
        )
    lines.extend(
        [
            "## Reference Graph",
            "",
            f"- node_count: {reference_graph['node_count']}",
            f"- edge_count: {reference_graph['edge_count']}",
            "- limitation: static textual references only; dynamic references remain a follow-up risk.",
            "",
            "## Rollback",
            "",
            f"Rollback for {task_id} is to remove this baseline evidence and keep all original project paths untouched. Any later archive or merge action must be bound by {next_task} checksum/privacy manifest and an explicit old-to-new map.",
            "",
            "## Next Task",
            "",
            f"{next_task} may generate the Wave {profile['wave']} archive/privacy manifest, checksums, and rollback list. {task_id} itself is not permission to relocate files.",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(output_dir: Path, expected: dict[Path, str]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for path, content in expected.items():
        path.write_text(content, encoding="utf-8")


def machine_json(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--projects", nargs="+")
    parser.add_argument("--wave", choices=["1", "2"], help="Run a completed-wave gate verifier.")
    parser.add_argument("--output-dir")
    parser.add_argument("--max-text-bytes", type=int, default=512_000)
    parser.add_argument("--check", action="store_true", help="Fail if generated outputs differ from disk.")
    args = parser.parse_args()

    repo = repo_root()
    if args.wave == "1":
        import wave1_gate

        gate_args = ["--check"] if args.check else []
        return wave1_gate.main(gate_args)
    if args.wave == "2":
        import wave2_gate

        gate_args = ["--check"] if args.check else []
        return wave2_gate.main(gate_args)
    if not args.projects:
        parser.error("--projects is required unless --wave is used")
    project_specs = normalize_projects(args.projects)
    profile = audit_profile(project_specs, args.output_dir)
    output_dir = repo / (Path(args.output_dir) if args.output_dir else profile["default_output_dir"])
    structure_map, reference_graph, archive_plan, privacy_scan = build_evidence(
        repo,
        project_specs,
        output_dir,
        args.max_text_bytes,
        profile,
    )
    expected = {
        output_dir / str(profile["structure_filename"]): machine_json(structure_map),
        output_dir / str(profile["reference_filename"]): machine_json(reference_graph),
        output_dir / str(profile["archive_plan_filename"]): archive_plan,
    }
    if privacy_scan is not None:
        expected[output_dir / str(profile["privacy_scan_filename"])] = privacy_scan
    if args.check:
        mismatched = [str(path.relative_to(repo)) for path, content in expected.items() if not path.exists() or path.read_text(encoding="utf-8") != content]
        if mismatched:
            print(json.dumps({"result": "FAIL", "mismatched": mismatched}, ensure_ascii=False, sort_keys=True))
            return 1
    else:
        write_outputs(output_dir, expected)
    print(
        json.dumps(
            {
                "result": "PASS",
                "task_id": profile["task_id"],
                "acceptance_id": profile["acceptance_id"],
                "projects": [project["project_id"] for project in project_specs],
                "output_dir": str(output_dir.relative_to(repo)),
                "node_count": reference_graph["node_count"],
                "edge_count": reference_graph["edge_count"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

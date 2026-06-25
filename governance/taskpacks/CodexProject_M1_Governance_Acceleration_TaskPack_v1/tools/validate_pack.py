#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


DEFAULT_PACK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = DEFAULT_PACK_ROOT.parents[2]
TASK_RE = re.compile(r"^S[1-9][0-9]*P[A-Z]T[0-9]{2}$")

REQUIRED_FILES = [
    "00_README_FIRST.md",
    "01_BASELINE_AND_SCOPE.md",
    "02_CODEX_MASTER_PROMPT.md",
    "03_M1_DECISION_RECORD.md",
    "04_TWO_ROUND_SIX_AGENT_PROTOCOL.md",
    "05_CONSOLIDATED_FINDINGS.md",
    "06_IMPLEMENTATION_AND_QUALITY_GUARDS.md",
    "07_ACCEPTANCE_QUALITY_ROI.md",
    "08_CONTINUITY_AND_ROLLBACK.md",
    "MANIFEST.txt",
    "SHA256SUMS",
    "roadmap/roadmap.yaml",
    "roadmap/roadmap.json",
    "roadmap/roadmap.csv",
    "roadmap/ROADMAP.md",
    "roadmap/ROADMAP.pdf",
    "schemas/finding.schema.json",
    "schemas/review_report.schema.json",
    "templates/review_output.template.json",
    "templates/HANDOFF.template.md",
    "tools/validate_pack.py",
    "evidence/SOURCE_MAP.md",
    "prompts/consolidate_round1.md",
    "prompts/consolidate_final.md",
    "prompts/round1/agent_1_security_code.md",
    "prompts/round1/agent_2_runtime_stress.md",
    "prompts/round1/agent_3_information_ux_architecture.md",
    "prompts/round2/agent_4_security_adversarial.md",
    "prompts/round2/agent_5_runtime_fault_injection.md",
    "prompts/round2/agent_6_information_adversarial.md",
]


class PackValidation:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_yaml(path: Path) -> Any:
    scripts_dir = REPO_ROOT / "scripts"
    if scripts_dir.exists():
        sys.path.insert(0, str(scripts_dir))
        try:
            import validate_project_governance as governance  # type: ignore

            return governance.load_yaml(path)
        finally:
            try:
                sys.path.remove(str(scripts_dir))
            except ValueError:
                pass
    raise RuntimeError("Cannot locate repository YAML loader")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def flatten_tasks(roadmap: dict[str, Any]) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    for stage_index, stage in enumerate(roadmap.get("stages") or [], 1):
        for phase_index, phase in enumerate(stage.get("phases") or [], 1):
            for task_index, task in enumerate(phase.get("tasks") or [], 1):
                item = dict(task)
                item["_stage_id"] = stage.get("stage_id")
                item["_phase_id"] = phase.get("phase_id")
                item["_stage_index"] = stage_index
                item["_phase_index"] = phase_index
                item["_task_index"] = task_index
                tasks.append(item)
    return tasks


def compare_roadmap_views(validation: PackValidation, pack_root: Path, yaml_data: dict[str, Any], json_data: dict[str, Any]) -> None:
    if yaml_data != json_data:
        validation.error("roadmap/roadmap.yaml and roadmap/roadmap.json drift")

    tasks = flatten_tasks(yaml_data)
    by_id = {str(task.get("task_id")): task for task in tasks}
    with (pack_root / "roadmap" / "roadmap.csv").open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != len(tasks):
        validation.error(f"roadmap.csv row count drift: expected {len(tasks)}, got {len(rows)}")
    for row in rows:
        task_id = row.get("task_id") or ""
        task = by_id.get(task_id)
        if not task:
            validation.error(f"roadmap.csv unknown task_id {task_id}")
            continue
        checks = {
            "task_sequence": str(task.get("numeric_sequence") or ""),
            "estimated_hours": str(task.get("estimated_hours") or ""),
            "estimated_pct_total": str(task.get("estimated_pct_total") or ""),
            "status": str(task.get("status") or ""),
            "dependencies": ";".join(task.get("dependencies") or []),
            "depends_on": ";".join(task.get("depends_on") or []),
            "requires_gate": str(task.get("requires_gate") or ""),
            "parallel_group": str(task.get("parallel_group") or ""),
        }
        for key, expected in checks.items():
            if str(row.get(key) or "") != expected:
                validation.error(f"roadmap.csv drift for {task_id}.{key}: expected {expected!r}, got {row.get(key)!r}")

    md_text = (pack_root / "roadmap" / "ROADMAP.md").read_text(encoding="utf-8")
    for task_id in by_id:
        if task_id not in md_text:
            validation.error(f"ROADMAP.md missing task_id {task_id}")
    markdown_task_ids = set(re.findall(r"\bS[1-9][0-9]*P[A-Z]T[0-9]{2}\b", md_text))
    extra = sorted(markdown_task_ids - set(by_id))
    if extra:
        validation.error("ROADMAP.md contains task ids absent from YAML: " + ", ".join(extra))


def check_files_and_dead_refs(validation: PackValidation, pack_root: Path) -> None:
    for rel in REQUIRED_FILES:
        if not (pack_root / rel).is_file():
            validation.error(f"missing required file: {rel}")
    if (pack_root / "09_CONTINUITY_AND_ROLLBACK.md").exists():
        validation.error("unexpected stale 09_CONTINUITY_AND_ROLLBACK.md exists")
    readme = (pack_root / "00_README_FIRST.md").read_text(encoding="utf-8", errors="replace")
    if "09_CONTINUITY_AND_ROLLBACK.md" in readme:
        validation.error("00_README_FIRST.md references stale 09_CONTINUITY_AND_ROLLBACK.md")
    if "08_CONTINUITY_AND_ROLLBACK.md" not in readme:
        validation.error("00_README_FIRST.md missing 08_CONTINUITY_AND_ROLLBACK.md reference")

    roots = ("roadmap/", "prompts/", "schemas/", "templates/", "tools/", "evidence/")
    known_top_files = {Path(item).name for item in REQUIRED_FILES if "/" not in item}
    for path in pack_root.rglob("*.md"):
        text = path.read_text(encoding="utf-8", errors="replace")
        for ref in re.findall(r"(?<![A-Za-z0-9_/-])([A-Za-z0-9_./-]+\.(?:md|json|yaml|csv|pdf|py))", text):
            normalized = ref.replace("\\", "/")
            if normalized.startswith(("http", "github.com")):
                continue
            if normalized.startswith(roots) or normalized in known_top_files:
                if not (pack_root / normalized).exists():
                    validation.error(f"dead reference in {path.relative_to(pack_root).as_posix()}: {normalized}")


def parse_sha256s(path: Path) -> dict[str, str]:
    entries: dict[str, str] = {}
    if not path.is_file():
        return entries
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) >= 2 and re.fullmatch(r"[0-9a-f]{64}", parts[0]):
            entries[" ".join(parts[1:]).replace("\\", "/")] = parts[0]
    return entries


def check_sha256s(validation: PackValidation, root: Path, *, label: str = "") -> None:
    entries = parse_sha256s(root / "SHA256SUMS")
    if not entries:
        validation.error(f"{label}SHA256SUMS missing or empty")
        return

    def is_hash_tracked_file(path: Path) -> bool:
        rel_parts = path.relative_to(root).parts
        return path.name != "SHA256SUMS" and "__pycache__" not in rel_parts and path.suffix != ".pyc"

    files = sorted(path for path in root.rglob("*") if path.is_file() and is_hash_tracked_file(path))
    seen = {path.relative_to(root).as_posix() for path in files}
    for rel in seen:
        if rel not in entries:
            validation.error(f"{label}SHA256SUMS missing entry: {rel}")
            continue
        actual = sha256_file(root / rel)
        if entries[rel] != actual:
            validation.error(f"{label}SHA256 mismatch for {rel}")
    for rel in sorted(set(entries) - seen):
        validation.error(f"{label}SHA256SUMS references missing file: {rel}")


def validate_schema_instance(instance: Any, schema: dict[str, Any], schemas_dir: Path, path: str, errors: list[str]) -> None:
    if "$ref" in schema:
        ref = str(schema["$ref"])
        if ref == "finding.schema.json":
            schema = load_json(schemas_dir / "finding.schema.json")
        else:
            errors.append(f"{path}: unsupported schema ref {ref}")
            return
    if "oneOf" in schema:
        before = len(errors)
        branch_ok = False
        branch_messages: list[str] = []
        for branch in schema["oneOf"]:
            branch_errors: list[str] = []
            validate_schema_instance(instance, branch, schemas_dir, path, branch_errors)
            if not branch_errors:
                branch_ok = True
                break
            branch_messages.extend(branch_errors)
        if not branch_ok:
            errors.append(f"{path}: did not match oneOf ({'; '.join(branch_messages[:3])})")
        if branch_ok and len(errors) > before:
            del errors[before:]
        return
    expected_type = schema.get("type")
    if expected_type:
        type_ok = {
            "object": isinstance(instance, dict),
            "array": isinstance(instance, list),
            "string": isinstance(instance, str),
            "integer": isinstance(instance, int) and not isinstance(instance, bool),
            "boolean": isinstance(instance, bool),
        }.get(expected_type, True)
        if not type_ok:
            errors.append(f"{path}: expected {expected_type}")
            return
    if "const" in schema and instance != schema["const"]:
        errors.append(f"{path}: expected const {schema['const']!r}")
    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: value {instance!r} not in enum")
    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < int(schema["minLength"]):
            errors.append(f"{path}: string shorter than minLength")
        if "pattern" in schema and not re.fullmatch(str(schema["pattern"]), instance):
            errors.append(f"{path}: value {instance!r} does not match pattern")
    if isinstance(instance, list):
        if "minItems" in schema and len(instance) < int(schema["minItems"]):
            errors.append(f"{path}: array shorter than minItems")
        if "items" in schema:
            for index, item in enumerate(instance):
                validate_schema_instance(item, schema["items"], schemas_dir, f"{path}[{index}]", errors)
    if isinstance(instance, dict):
        required = schema.get("required") or []
        for key in required:
            if key not in instance:
                errors.append(f"{path}: missing required property {key}")
        properties = schema.get("properties") or {}
        if schema.get("additionalProperties") is False:
            for key in instance:
                if key not in properties:
                    errors.append(f"{path}: unexpected property {key}")
        for key, child_schema in properties.items():
            if key in instance:
                validate_schema_instance(instance[key], child_schema, schemas_dir, f"{path}.{key}", errors)


def check_schema_contracts(validation: PackValidation, pack_root: Path) -> None:
    schemas_dir = pack_root / "schemas"
    report_schema = load_json(schemas_dir / "review_report.schema.json")
    template = load_json(pack_root / "templates" / "review_output.template.json")
    errors: list[str] = []
    validate_schema_instance(template, report_schema, schemas_dir, "templates/review_output.template.json", errors)
    for error in errors:
        validation.error(error)
    for prompt in list((pack_root / "prompts" / "round1").glob("agent_*.md")) + list((pack_root / "prompts" / "round2").glob("agent_*.md")):
        text = prompt.read_text(encoding="utf-8", errors="replace")
        rel = prompt.relative_to(pack_root).as_posix()
        if "schemas/review_report.schema.json" not in text:
            validation.error(f"{rel} must require schemas/review_report.schema.json")
        if "schemas/finding.schema.json" not in text:
            validation.error(f"{rel} must mention findings[] use schemas/finding.schema.json")
    master = (pack_root / "02_CODEX_MASTER_PROMPT.md").read_text(encoding="utf-8", errors="replace")
    if "schemas/review_report.schema.json" not in master:
        validation.error("02_CODEX_MASTER_PROMPT.md missing review_report schema requirement")


def check_roadmap_dag(validation: PackValidation, roadmap: dict[str, Any]) -> None:
    tasks = flatten_tasks(roadmap)
    by_id = {str(task.get("task_id")): task for task in tasks}
    if len(by_id) != len(tasks):
        validation.error("duplicate task ids")
    for task in tasks:
        task_id = str(task.get("task_id") or "")
        if not TASK_RE.fullmatch(task_id):
            validation.error(f"{task_id}: invalid canonical id")
        for key in ("depends_on", "requires_gate", "parallel_group"):
            if key not in task:
                validation.error(f"{task_id}: missing {key}")
        if not task.get("parallel_group"):
            validation.error(f"{task_id}: empty parallel_group")
        if (task["_stage_index"], task["_phase_index"]) != (1, 1) and not task.get("requires_gate"):
            validation.error(f"{task_id}: missing requires_gate for non-initial phase/stage")
        for dep in task.get("depends_on") or []:
            if dep not in by_id:
                validation.error(f"{task_id}: depends_on unknown task {dep}")
                continue
            dep_task = by_id[dep]
            if (dep_task["_stage_index"], dep_task["_phase_index"]) > (task["_stage_index"], task["_phase_index"]):
                validation.error(f"{task_id}: depends_on future gate task {dep}")
            if dep_task["_phase_id"] != task["_phase_id"] and not task.get("requires_gate"):
                validation.error(f"{task_id}: cross-phase dependency {dep} lacks requires_gate")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(task_id: str, chain: list[str]) -> None:
        if task_id in visited:
            return
        if task_id in visiting:
            validation.error("roadmap DAG cycle: " + " -> ".join(chain + [task_id]))
            return
        visiting.add(task_id)
        for dep in by_id[task_id].get("depends_on") or []:
            if dep in by_id:
                visit(dep, chain + [task_id])
        visiting.remove(task_id)
        visited.add(task_id)

    for task_id in by_id:
        visit(task_id, [])


def check_review_bundle(validation: PackValidation, bundle_root: Path) -> None:
    required = [
        "MANIFEST.json",
        "SHA256SUMS",
        "baseline.json",
        "round1/agent1.json",
        "round1/agent2.json",
        "round1/agent3.json",
        "round1_consolidated.json",
        "candidate_m1s.json",
        "round2/agent4.json",
        "round2/agent5.json",
        "round2/agent6.json",
        "final_adjudication.json",
        "performance_summary.json",
    ]
    for rel in required:
        if not (bundle_root / rel).is_file():
            validation.error(f"review bundle missing file: {rel}")
    if not (bundle_root / "MANIFEST.json").is_file():
        return
    manifest = load_json(bundle_root / "MANIFEST.json")
    if not manifest.get("artifact_id"):
        validation.error("review bundle MANIFEST missing artifact_id")
    if not manifest.get("retention"):
        validation.error("review bundle MANIFEST missing retention")
    if "sha256s" not in manifest:
        validation.error("review bundle MANIFEST missing sha256s")
    check_sha256s(validation, bundle_root, label="review_bundle:")
    schemas_dir = DEFAULT_PACK_ROOT / "schemas"
    report_schema = load_json(schemas_dir / "review_report.schema.json")
    for rel in required:
        if re.fullmatch(r"round[12]/agent[1-6]\.json", rel):
            if not (bundle_root / rel).is_file():
                continue
            errors: list[str] = []
            validate_schema_instance(load_json(bundle_root / rel), report_schema, schemas_dir, rel, errors)
            for error in errors:
                validation.error("review bundle schema error: " + error)


def validate_pack(pack_root: Path, review_bundle: Path | None = None) -> dict[str, Any]:
    validation = PackValidation()
    check_files_and_dead_refs(validation, pack_root)
    yaml_data = load_yaml(pack_root / "roadmap" / "roadmap.yaml")
    json_data = load_json(pack_root / "roadmap" / "roadmap.json")
    if not isinstance(yaml_data, dict) or not isinstance(json_data, dict):
        validation.error("roadmap YAML/JSON must parse to objects")
        yaml_data = {}
        json_data = {}
    if json_data.get("total_estimated_hours") != 60.0:
        validation.error("total_estimated_hours must be 60.0")
    if len(json_data.get("stages") or []) != 5:
        validation.error(f"expected 5 stages, got {len(json_data.get('stages') or [])}")
    tasks = flatten_tasks(json_data)
    hours = sum(float(task.get("estimated_hours") or 0) for task in tasks)
    pct = sum(float(task.get("estimated_pct_total") or 0) for task in tasks)
    if abs(hours - 60.0) > 1e-9:
        validation.error(f"hour sum {hours}")
    if abs(pct - 100.0) > 0.2:
        validation.error(f"rounded pct sum {pct}")
    compare_roadmap_views(validation, pack_root, yaml_data, json_data)
    check_roadmap_dag(validation, json_data)
    check_schema_contracts(validation, pack_root)
    check_sha256s(validation, pack_root)
    if review_bundle is not None:
        check_review_bundle(validation, review_bundle)
    return {
        "ok": not validation.errors,
        "errors": validation.errors,
        "warnings": validation.warnings,
        "stages": len(json_data.get("stages") or []),
        "phases": sum(len(stage.get("phases") or []) for stage in json_data.get("stages") or []),
        "tasks": len(tasks),
        "hours": hours,
        "rounded_pct_sum": round(pct, 4),
        "review_bundle": str(review_bundle) if review_bundle else "",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the M1 governance acceleration TaskPack and optional review bundle.")
    parser.add_argument("--pack", default=str(DEFAULT_PACK_ROOT), help="TaskPack root directory.")
    parser.add_argument("--review-bundle", default=str(REPO_ROOT / "governance" / "review_bundles" / "m1_1"), help="Review bundle root directory.")
    parser.add_argument("--no-review-bundle", action="store_true", help="Skip review bundle validation.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args(argv)
    review_bundle = None if args.no_review_bundle else Path(args.review_bundle)
    result = validate_pack(Path(args.pack), review_bundle)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif result["ok"]:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for error in result["errors"]:
            print("ERROR: " + error)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

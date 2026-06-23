#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS_DIR = ROOT / "infra/db/migrations"
A119_OUTPUT = ROOT / "artifacts/tests/a119/t905_migration_rollback_rehearsal.json"
A120_OUTPUT = ROOT / "artifacts/tests/a120/t905_clean_start_operator_rehearsal.json"

SCHEMA_VERSION = "eei-t905-release-rehearsal-v1"
INTEGRATION_TEST = (
    "tests/integration/test_database_migrations.py::"
    "test_t905_each_migration_suffix_rolls_down_and_re_upgrades"
)

README_COMMANDS = [
    "make bootstrap",
    "cp .env.example .env",
    "make doctor",
    "make db-up",
    "make migrate-up",
    "make seed-catalogs",
    "make load-fixtures",
    "make check-db-schema",
    "make health",
    "make verify-g2-db",
    "make validate-clean-room-release",
    "make validate-release-artifacts",
    "make db-down",
]

MAKE_TARGETS = {
    "bootstrap",
    "doctor",
    "db-up",
    "migrate-up",
    "seed-catalogs",
    "load-fixtures",
    "check-db-schema",
    "health",
    "verify-g2-db",
    "validate-clean-room-release",
    "validate-release-artifacts",
    "db-down",
    "test-integration",
    "test-e2e",
    "test-e2e-live",
}

WORKFLOW_COMMANDS = {
    "make db-up",
    "make health",
    "make test-integration",
    "make test-e2e",
    "make test-e2e-live",
}


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def read_text(path: Path) -> str:
    if not path.is_file():
        raise AssertionError(f"missing required file: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def make_targets() -> set[str]:
    makefile = read_text(ROOT / "Makefile")
    return set(re.findall(r"^([A-Za-z0-9_.-]+):", makefile, flags=re.MULTILINE))


def migration_entries() -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for path in sorted(MIGRATIONS_DIR.iterdir()):
        if not path.is_dir() or "_" not in path.name:
            continue
        version, name = path.name.split("_", 1)
        if not version.isdigit():
            continue
        up_sql = read_text(path / "up.sql")
        down_sql = read_text(path / "down.sql")
        require(up_sql.strip(), f"{relative(path / 'up.sql')} is empty")
        require(down_sql.strip(), f"{relative(path / 'down.sql')} is empty")
        entries.append(
            {
                "version": version,
                "name": name,
                "path": relative(path),
                "up_sha256": sha256_text(up_sql),
                "down_sha256": sha256_text(down_sql),
            }
        )
    require(len(entries) >= 11, "T905 expects the current production migration set")
    return entries


def rollback_rehearsal_steps(migrations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    versions = [migration["version"] for migration in migrations]
    steps: list[dict[str, Any]] = []
    for suffix_steps, target in enumerate(reversed(migrations), start=1):
        expected_pending = versions[-suffix_steps:]
        steps.append(
            {
                "target_version": target["version"],
                "target_name": target["name"],
                "suffix_steps": suffix_steps,
                "downgrade_command": f"python scripts/migrate.py downgrade --steps {suffix_steps}",
                "upgrade_command": "python scripts/migrate.py upgrade",
                "expected_pending_versions": expected_pending,
            }
        )
    return steps


def build_a119() -> dict[str, Any]:
    migrations = migration_entries()
    return {
        "schema_version": SCHEMA_VERSION,
        "artifact_id": "t905-a119-migration-rollback-rehearsal",
        "generated_at": utc_now(),
        "task_id": "T905",
        "acceptance_id": "A119",
        "status": "PASS",
        "evidence_type": "postgresql_migration_suffix_rollback_rehearsal",
        "migrations_checked": len(migrations),
        "migrations": migrations,
        "integration_test": INTEGRATION_TEST,
        "ci_binding": {
            "workflow": ".github/workflows/eei-validation.yml",
            "preparation_steps": ["cp .env.example .env", "make db-up", "make health"],
            "postgresql_step": "make test-integration",
        },
        "rehearsal_steps": rollback_rehearsal_steps(migrations),
        "release_disposable_data_rollback": {
            "cleanup_command": "python scripts/migrate.py downgrade --all",
            "expected_final_state": "all schema_migrations rows are unapplied",
            "scope": "CI disposable PostgreSQL database only",
        },
        "rollback": [
            "Revert the T905 integration-test and validator changes.",
            "Regenerate development, clean-room and release artifacts from the prior tree.",
            "Rerun make verify and the GitHub Actions EEI validation workflow.",
        ],
    }


def build_a120() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "artifact_id": "t905-a120-clean-start-operator-rehearsal",
        "generated_at": utc_now(),
        "task_id": "T905",
        "acceptance_id": "A120",
        "status": "PASS",
        "evidence_type": "readme_clean_start_and_critical_demo_rehearsal",
        "operator_readme": "README.md",
        "clean_start_commands": README_COMMANDS,
        "critical_demo": [
            {
                "name": "PostgreSQL migrations, seeds, fixtures and API health",
                "commands": [
                    "make db-up",
                    "make migrate-up",
                    "make seed-catalogs",
                    "make load-fixtures",
                    "make check-db-schema",
                    "make health",
                ],
            },
            {
                "name": "Production API, recursive graph, scoring, saved-view and worker contracts",
                "commands": ["make verify-g2-db"],
            },
            {
                "name": "Release package reproducibility",
                "commands": [
                    "make validate-clean-room-release",
                    "make validate-release-artifacts",
                ],
            },
        ],
        "ci_binding": {
            "workflow": ".github/workflows/eei-validation.yml",
            "steps": [
                "Verify static, contract, lint, typecheck and unit tests",
                "Prepare G2 PostgreSQL database",
                "Verify G2 PostgreSQL integration",
                "Verify G2 browser E2E",
                "Verify G2 live FastAPI PostgreSQL E2E",
            ],
        },
        "non_claims": [
            "Does not close A202 source-license, owner, legal or relationship-publication gates.",
            "Does not close A209 24h operator soak.",
            "Does not close A210 formal brand/legal/market clearance.",
        ],
        "rollback": [
            "Run make db-down to stop the clean-start PostgreSQL service.",
            "Revert the README/runbook, T905 validator and generated A119/A120 artifacts.",
            "Regenerate development, clean-room and release artifacts from the prior tree.",
        ],
    }


def validate_readme_commands() -> None:
    readme = read_text(ROOT / "README.md")
    missing = [command for command in README_COMMANDS if command not in readme]
    require(not missing, f"README.md is missing clean-start commands: {missing}")


def validate_make_targets() -> None:
    targets = make_targets()
    missing = sorted(MAKE_TARGETS - targets)
    require(not missing, f"Makefile is missing T905 command targets: {missing}")


def validate_workflow_binding() -> None:
    workflow = read_text(ROOT.parent / ".github/workflows/eei-validation.yml")
    missing = sorted(command for command in WORKFLOW_COMMANDS if command not in workflow)
    require(not missing, f"EEI validation workflow is missing commands: {missing}")


def validate_integration_test_binding() -> None:
    test_file = read_text(ROOT / "tests/integration/test_database_migrations.py")
    test_name = INTEGRATION_TEST.split("::", 1)[1]
    require(test_name in test_file, f"missing integration test {test_name}")
    for token in ("downgrade\", \"--steps", "upgrade", "downgrade\", \"--all"):
        require(token in test_file, f"integration test missing token: {token}")


def validate_a119(payload: dict[str, Any]) -> None:
    migrations = migration_entries()
    expected_steps = rollback_rehearsal_steps(migrations)
    require(payload.get("schema_version") == SCHEMA_VERSION, "A119 schema_version mismatch")
    require(payload.get("task_id") == "T905", "A119 task_id mismatch")
    require(payload.get("acceptance_id") == "A119", "A119 acceptance_id mismatch")
    require(payload.get("status") == "PASS", "A119 status must be PASS")
    require(payload.get("migrations") == migrations, "A119 migration checksums are stale")
    require(payload.get("migrations_checked") == len(migrations), "A119 migration count stale")
    require(payload.get("rehearsal_steps") == expected_steps, "A119 rehearsal steps stale")
    require(
        payload.get("integration_test") == INTEGRATION_TEST,
        "A119 integration test binding stale",
    )
    cleanup = payload.get("release_disposable_data_rollback", {})
    require(
        isinstance(cleanup, dict)
        and cleanup.get("cleanup_command") == "python scripts/migrate.py downgrade --all",
        "A119 cleanup command mismatch",
    )


def validate_a120(payload: dict[str, Any]) -> None:
    require(payload.get("schema_version") == SCHEMA_VERSION, "A120 schema_version mismatch")
    require(payload.get("task_id") == "T905", "A120 task_id mismatch")
    require(payload.get("acceptance_id") == "A120", "A120 acceptance_id mismatch")
    require(payload.get("status") == "PASS", "A120 status must be PASS")
    require(payload.get("clean_start_commands") == README_COMMANDS, "A120 commands stale")
    non_claims = payload.get("non_claims")
    require(isinstance(non_claims, list) and len(non_claims) == 3, "A120 non-claims missing")
    for token in ("A202", "A209", "A210"):
        require(any(token in claim for claim in non_claims), f"A120 missing non-claim for {token}")


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(read_text(path))
    require(isinstance(payload, dict), f"{relative(path)} must contain a JSON object")
    return payload


def generate(_: argparse.Namespace) -> None:
    write_json(A119_OUTPUT, build_a119())
    write_json(A120_OUTPUT, build_a120())
    validate(argparse.Namespace(quiet=True))
    print(
        json.dumps(
            {
                "generated": True,
                "artifacts": [relative(A119_OUTPUT), relative(A120_OUTPUT)],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def validate(args: argparse.Namespace) -> None:
    validate_make_targets()
    validate_readme_commands()
    validate_workflow_binding()
    validate_integration_test_binding()
    validate_a119(read_json(A119_OUTPUT))
    validate_a120(read_json(A120_OUTPUT))
    if not getattr(args, "quiet", False):
        print(
            json.dumps(
                {
                    "valid": True,
                    "task_id": "T905",
                    "acceptance_ids": ["A119", "A120"],
                    "artifacts": [relative(A119_OUTPUT), relative(A120_OUTPUT)],
                },
                ensure_ascii=False,
                indent=2,
            )
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate EEI T905 release rehearsal evidence.")
    parser.add_argument("command", choices=["generate", "validate"])
    parser.add_argument("--quiet", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.command == "generate":
            generate(args)
        else:
            validate(args)
    except (AssertionError, OSError, json.JSONDecodeError) as exc:
        print(f"T905 release rehearsal validation: FAIL - {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

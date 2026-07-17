from __future__ import annotations

import copy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from governance_id_allocator import (  # noqa: E402
    allocate_identifier,
    migrate_project_aliases,
)
from governance_id_audit import (  # noqa: E402
    Reference,
    audit_references,
    audit_repository,
    collect_references,
    new_positional_identifiers,
)
from governance_ids import (  # noqa: E402
    GovernanceIdError,
    load_registry,
    parse_identifier,
    registry_sha256,
    serialize_registry,
    validate_registry,
    validate_registry_immutability,
)


BASE_SHA = "a" * 40


def task_allocation(
    sequence: int,
    *,
    dependencies: list[str] | None = None,
    key: str | None = None,
) -> dict[str, object]:
    task_id = f"TSK.Example.PROG1.{sequence:04d}"
    return {
        "kind": "TSK",
        "identifier": task_id,
        "acceptance_id": f"ACC.Example.PROG1.{sequence:04d}",
        "project": "Example",
        "program": "PROG1",
        "sequence": sequence,
        "idempotency_key": key or f"fixture:{task_id}",
        "allocated_from_base_sha": BASE_SHA,
        "source_ref": "fixture",
        "dependencies": dependencies or [],
    }


def registry(*allocations: dict[str, object]) -> dict[str, object]:
    return {
        "schema_version": 2,
        "registry_revision": 1,
        "repository": "LinzeColin/CodexProject",
        "last_updated_at": "2026-07-15T00:00:00Z",
        "bootstrap": {
            "imported_at": "2026-07-15T00:00:00Z",
            "implementation_base_sha": BASE_SHA,
            "source_package_sha256": "b" * 64,
            "task_registry_sha256": "c" * 64,
            "roadmap_sha256": "d" * 64,
            "task_count": len(allocations),
        },
        "allocations": list(allocations),
        "aliases": [],
    }


class GovernanceIdV2ContractTests(unittest.TestCase):
    def test_kind_specific_v2_grammars(self) -> None:
        values = {
            "TSK": "TSK.Example.PROG1.0001",
            "ACC": "ACC.Example.PROG1.0001",
            "EVT": "EVT.Example.PROG1.0001",
            "PG": "PG.Example.GOAL1",
        }
        for kind, value in values.items():
            with self.subTest(kind=kind):
                parsed = parse_identifier(value, kind)
                self.assertEqual(parsed.generation, "v2")
        with self.assertRaises(GovernanceIdError):
            parse_identifier("PG.Example.GOAL1.0001", "PG")

    def test_repository_bootstrap_registry_is_valid_and_complete(self) -> None:
        payload = load_registry(ROOT / "governance" / "id_registry.json")
        self.assertEqual(validate_registry(payload), [])
        self.assertEqual(
            sum(
                item["kind"] == "TSK"
                and not str(item["source_ref"]).startswith("allocator:")
                for item in payload["allocations"]
            ),
            37,
        )
        self.assertEqual(
            sum(item["kind"] == "TSK" for item in payload["allocations"]), 63
        )
        self.assertEqual(
            sum(item["kind"] == "EVT" for item in payload["allocations"]), 68
        )
        self.assertEqual(
            sum(item["kind"] == "PG" for item in payload["allocations"]), 1
        )
        self.assertEqual(payload["migrated_projects"], ["OpenAIDatabase"])
        self.assertEqual(len(payload["aliases"]), 87)

    def test_duplicate_identifier_is_rejected(self) -> None:
        first = task_allocation(1)
        duplicate = copy.deepcopy(first)
        duplicate["idempotency_key"] = "fixture:duplicate"
        errors = validate_registry(registry(first, duplicate))
        self.assertTrue(
            any("duplicate V2 identifier" in error for error in errors), errors
        )
        self.assertTrue(
            any("reused namespace slot" in error for error in errors), errors
        )

    def test_orphan_dependency_is_rejected(self) -> None:
        payload = registry(
            task_allocation(1, dependencies=["TSK.Example.PROG1.9999"]),
        )
        self.assertTrue(
            any("orphaned" in error for error in validate_registry(payload))
        )

    def test_dependency_cycle_is_rejected(self) -> None:
        payload = registry(
            task_allocation(1, dependencies=["TSK.Example.PROG1.0002"]),
            task_allocation(2, dependencies=["TSK.Example.PROG1.0001"]),
        )
        self.assertTrue(
            any("dependency cycle" in error for error in validate_registry(payload))
        )

    def test_alias_ambiguity_is_rejected(self) -> None:
        payload = registry(task_allocation(1))
        alias = {
            "project": "Example",
            "kind": "TSK",
            "legacy_id": "S1PAT01",
            "target_id": "TSK.Example.PROG1.0001",
        }
        payload["aliases"] = [alias, copy.deepcopy(alias)]
        errors = validate_registry(payload)
        self.assertTrue(
            any("ambiguous project-scoped alias" in error for error in errors), errors
        )

    def test_migrated_project_requires_exactly_one_alias(self) -> None:
        payload = registry(task_allocation(1))
        payload["migrated_projects"] = ["Example"]
        reference = Reference(
            project="Example",
            kind="TSK",
            value="OLD-TASK",
            path="roadmap.yaml",
            field="task_id",
        )
        errors, counters = audit_references([reference], payload)
        self.assertTrue(any("has no alias" in error for error in errors), errors)
        self.assertEqual(counters["strict_legacy_references_observed"], 1)
        self.assertEqual(counters["strict_legacy_references_resolved"], 0)

        payload["aliases"] = [
            {
                "project": "Example",
                "kind": "TSK",
                "legacy_id": "OLD-TASK",
                "target_id": "TSK.Example.PROG1.0001",
            }
        ]
        errors, counters = audit_references([reference], payload)
        self.assertEqual(errors, [])
        self.assertEqual(counters["strict_legacy_references_resolved"], 1)

    def test_rename_and_reuse_are_rejected(self) -> None:
        baseline = registry(task_allocation(1))
        renamed = registry(task_allocation(2, key="fixture:TSK.Example.PROG1.0001"))
        rename_errors = validate_registry_immutability(renamed, baseline)
        self.assertTrue(
            any("immutable allocation changed" in error for error in rename_errors)
        )

        reused = registry(task_allocation(1, key="fixture:replacement"))
        reuse_errors = validate_registry_immutability(reused, baseline)
        self.assertTrue(any("allocation removed" in error for error in reuse_errors))

        baseline["migrated_projects"] = ["Example"]
        current = copy.deepcopy(baseline)
        current["migrated_projects"] = []
        marker_errors = validate_registry_immutability(current, baseline)
        self.assertTrue(
            any("migrated project marker removed" in error for error in marker_errors)
        )

    def test_stage_phase_move_preserves_identity(self) -> None:
        baseline = {
            "stages": [
                {"stage_id": "ST01", "tasks": [{"task_id": "TSK.Example.PROG1.0001"}]}
            ]
        }
        moved = {
            "stages": [
                {"stage_id": "ST09", "tasks": [{"task_id": "TSK.Example.PROG1.0001"}]}
            ]
        }
        payload = registry(task_allocation(1))
        for document in (baseline, moved):
            references = collect_references(
                document, project="Example", path="roadmap.yaml"
            )
            errors, counters = audit_references(references, payload)
            self.assertEqual(errors, [])
            self.assertEqual(counters["v2_references_resolved"], 1)

    def test_orphaned_v2_metadata_reference_is_rejected(self) -> None:
        payload = registry(task_allocation(1))
        references = [
            Reference(
                project="Example",
                kind="TSK",
                value="TSK.Example.PROG1.0002",
                path="roadmap.yaml",
                field="current_task_id",
            )
        ]
        errors, counters = audit_references(references, payload)
        self.assertEqual(counters["v2_references"], 1)
        self.assertEqual(counters["v2_references_resolved"], 0)
        self.assertTrue(any("orphaned V2" in error for error in errors), errors)

    def test_new_positional_task_creation_fails_but_movement_passes(self) -> None:
        old = {("Example", "S1PAT01")}
        self.assertEqual(new_positional_identifiers(old, old), set())
        self.assertEqual(
            new_positional_identifiers(old | {("Example", "S2PBT02")}, old),
            {("Example", "S2PBT02")},
        )

    def test_repository_wide_metadata_audit_passes(self) -> None:
        summary = audit_repository(
            root=ROOT,
            registry_path=ROOT / "governance" / "id_registry.json",
            base_ref="HEAD",
        )
        self.assertEqual(summary["status"], "PASS", summary["errors"])
        self.assertEqual(summary["task_ids"], 63)
        self.assertTrue(summary["all_references_exactly_one"])
        self.assertTrue(summary["all_v2_references_exactly_one"])
        self.assertEqual(summary["migrated_projects"], ["OpenAIDatabase"])
        self.assertGreater(summary["strict_legacy_references_observed"], 0)
        self.assertEqual(
            summary["strict_legacy_references_observed"],
            summary["strict_legacy_references_resolved"],
        )
        self.assertEqual(summary["new_positional_ids"], 0)


class GovernanceIdAllocatorTests(unittest.TestCase):
    def _temporary_repo(
        self,
    ) -> tuple[tempfile.TemporaryDirectory[str], Path, Path, str]:
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        registry_path = root / "governance" / "id_registry.json"
        registry_path.parent.mkdir(parents=True)
        payload = registry(task_allocation(1))
        registry_path.write_bytes(serialize_registry(payload))
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        subprocess.run(
            ["git", "-C", str(root), "config", "user.name", "Governance Test"],
            check=True,
        )
        subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "config",
                "user.email",
                "governance@example.invalid",
            ],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(root), "add", "governance/id_registry.json"], check=True
        )
        subprocess.run(["git", "-C", str(root), "commit", "-qm", "fixture"], check=True)
        head = subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
        ).strip()
        payload["allocations"][0]["allocated_from_base_sha"] = head
        registry_path.write_bytes(serialize_registry(payload))
        subprocess.run(
            ["git", "-C", str(root), "add", "governance/id_registry.json"], check=True
        )
        subprocess.run(
            ["git", "-C", str(root), "commit", "-qm", "bind base"], check=True
        )
        head = subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
        ).strip()
        return temporary, root, registry_path, head

    def test_dry_run_apply_and_idempotent_replay(self) -> None:
        temporary, root, registry_path, head = self._temporary_repo()
        self.addCleanup(temporary.cleanup)
        before = registry_path.read_bytes()
        planned = allocate_identifier(
            repo_root=root,
            registry_path=registry_path,
            kind="TSK",
            project="Example",
            program="PROG1",
            base_sha=head,
            idempotency_key="allocator:dry-run-apply",
            apply=False,
            allocated_at="2026-07-15T00:01:00Z",
        )
        self.assertFalse(planned["mutated"])
        self.assertEqual(registry_path.read_bytes(), before)
        applied = allocate_identifier(
            repo_root=root,
            registry_path=registry_path,
            kind="TSK",
            project="Example",
            program="PROG1",
            base_sha=head,
            idempotency_key="allocator:dry-run-apply",
            apply=True,
            expected_registry_sha256=planned["registry_sha256"],
            allocated_at="2026-07-15T00:01:00Z",
        )
        self.assertTrue(applied["mutated"])
        replay = allocate_identifier(
            repo_root=root,
            registry_path=registry_path,
            kind="TSK",
            project="Example",
            program="PROG1",
            base_sha=head,
            idempotency_key="allocator:dry-run-apply",
            apply=True,
            expected_registry_sha256=planned["registry_sha256"],
            allocated_at="2026-07-15T00:01:00Z",
        )
        self.assertFalse(replay["mutated"])
        self.assertTrue(replay["idempotent_replay"])

    def test_project_alias_migration_is_one_atomic_idempotent_transaction(self) -> None:
        temporary, root, registry_path, head = self._temporary_repo()
        self.addCleanup(temporary.cleanup)
        planned = migrate_project_aliases(
            repo_root=root,
            registry_path=registry_path,
            project="Example",
            program="OPS1",
            base_sha=head,
            task_aliases={"OLD-TASK": ["OLD-ACC"]},
            task_dependencies={"OLD-TASK": []},
            event_aliases=["OLD-EVENT"],
            canonical_events=[("OPS1", "fixture:canonical-event")],
            apply=False,
            allocated_at="2026-07-15T00:02:00Z",
        )
        self.assertEqual(planned["alias_count"], 3)
        self.assertEqual(planned["aliases_added"], 3)
        applied = migrate_project_aliases(
            repo_root=root,
            registry_path=registry_path,
            project="Example",
            program="OPS1",
            base_sha=head,
            task_aliases={"OLD-TASK": ["OLD-ACC"]},
            task_dependencies={"OLD-TASK": []},
            event_aliases=["OLD-EVENT"],
            canonical_events=[("OPS1", "fixture:canonical-event")],
            apply=True,
            expected_registry_sha256=planned["registry_sha256"],
            allocated_at="2026-07-15T00:02:00Z",
        )
        self.assertTrue(applied["mutated"])
        payload = load_registry(registry_path)
        self.assertEqual(validate_registry(payload), [])
        self.assertEqual(payload["migrated_projects"], ["Example"])
        self.assertEqual(len(payload["aliases"]), 3)
        self.assertEqual(
            sum(item["kind"] == "EVT" for item in payload["allocations"]), 2
        )
        replay = migrate_project_aliases(
            repo_root=root,
            registry_path=registry_path,
            project="Example",
            program="OPS1",
            base_sha=head,
            task_aliases={"OLD-TASK": ["OLD-ACC"]},
            task_dependencies={"OLD-TASK": []},
            event_aliases=["OLD-EVENT"],
            canonical_events=[("OPS1", "fixture:canonical-event")],
            apply=True,
            expected_registry_sha256=applied["next_registry_sha256"],
            allocated_at="2026-07-15T00:02:00Z",
        )
        self.assertFalse(replay["mutated"])
        self.assertTrue(replay["idempotent_replay"])

    def test_concurrent_allocators_commit_only_one_registry_write(self) -> None:
        temporary, root, registry_path, head = self._temporary_repo()
        self.addCleanup(temporary.cleanup)
        digest = registry_sha256(load_registry(registry_path))
        common = [
            sys.executable,
            str(ROOT / "scripts" / "governance_id_allocator.py"),
            "--kind",
            "TSK",
            "--project",
            "Example",
            "--program",
            "PROG1",
            "--base-sha",
            head,
            "--repo-root",
            str(root),
            "--registry",
            str(registry_path),
            "--apply",
            "--expected-registry-sha256",
            digest,
            "--allocated-at",
            "2026-07-15T00:02:00Z",
        ]
        processes = [
            subprocess.Popen(
                [*common, "--idempotency-key", key],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            for key in ("allocator:concurrent-a", "allocator:concurrent-b")
        ]
        results = []
        for process in processes:
            output, _ = process.communicate()
            results.append((process.returncode, output))
        self.assertEqual(sorted(code for code, _ in results), [0, 1], results)
        payload = load_registry(registry_path)
        self.assertEqual(validate_registry(payload), [])
        self.assertEqual(len(payload["allocations"]), 2)


if __name__ == "__main__":
    unittest.main()

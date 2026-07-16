from __future__ import annotations

import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATABASE_DIR = ROOT / "OpenAIDatabase"
SCRIPT = DATABASE_DIR / "scripts/build_memory_migration_profile.py"
CONTRACT = DATABASE_DIR / "config/memory.profiling.json"


def load_module():
    spec = importlib.util.spec_from_file_location("build_memory_migration_profile", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MemoryMigrationProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module()
        cls.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

    @staticmethod
    def record(index: int, **overrides: object) -> dict[str, object]:
        row: dict[str, object] = {
            "id": f"mem_{index:016x}",
            "statement": f"private-fixture-statement-{index}",
            "category": "workflow",
            "sensitivity": "private",
            "source_kind": "openai_export",
            "source": f"private-fixture-source-{index}",
            "conversation_id": f"private-fixture-conversation-{index}",
            "date": "2026-07-01",
            "validity": "长期",
            "action": "add",
            "importance": "中",
            "memory_tier": "重要中长期",
            "confidence": "high",
            "evidence": [f"private-fixture-evidence-{index}"],
            "activated_at": "2026-07-02T00:00:00Z",
            "security_findings": [],
        }
        row.update(overrides)
        return row

    def make_fixture(
        self,
        root: Path,
        records: list[dict[str, object]],
        expected: dict[str, int],
        overrides: dict[str, dict[str, object]] | None = None,
    ) -> Path:
        active = root / "data/memory/active/active_memory.jsonl"
        candidates = root / "data/memory/candidates/run_fixture.memory_candidates.jsonl"
        curation = root / "data/memory/curation/core_profile_review.json"
        secret = root / "data/memory/secret_refs/run_fixture.secret_refs.jsonl"
        for path in (active, candidates, curation, secret):
            path.parent.mkdir(parents=True, exist_ok=True)
        encoded = b"".join(self.module.canonical_bytes(row, final_lf=True) for row in records)
        active.write_bytes(encoded)
        candidates.write_bytes(encoded)
        curation.write_text(
            json.dumps({"overrides": overrides or {}}, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        secret.write_bytes(b"")

        contract = copy.deepcopy(self.contract)
        paths = {
            "active": [active],
            "candidates": [candidates],
            "curation": [curation],
            "secret_refs": [secret],
        }
        for role, role_paths in paths.items():
            descriptors = [
                self.module.descriptor(
                    root,
                    path,
                    {"active": "A001", "candidates": "C001", "curation": "U001", "secret_refs": "S001"}[role],
                    role,
                )
                for path in role_paths
            ]
            contract["inputs"][role]["file_count"] = len(role_paths)
            contract["inputs"][role]["bytes"] = sum(row["bytes"] for row in descriptors)
            contract["inputs"][role]["collection_sha256"] = self.module.collection_sha256(descriptors)
            if role == "curation":
                contract["inputs"][role]["override_count"] = len(overrides or {})
            else:
                contract["inputs"][role]["record_count"] = 0 if role == "secret_refs" else len(records)
        contract["inputs"]["active"]["path"] = active.relative_to(root).as_posix()
        contract["inputs"]["candidates"]["glob"] = "data/memory/candidates/*.jsonl"
        contract["inputs"]["curation"]["path"] = curation.relative_to(root).as_posix()
        contract["inputs"]["secret_refs"]["glob"] = "data/memory/secret_refs/*.jsonl"
        contract["identity"]["expected_unique_id_count"] = len(records)
        contract["quality_contract"]["expected_disposition_counts"] = expected
        contract_path = root / "config/memory.profiling.json"
        contract_path.parent.mkdir(parents=True, exist_ok=True)
        contract_path.write_text(
            json.dumps(contract, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return contract_path

    def test_six_dispositions_write_only_redacted_derived_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            records = [
                self.record(1, curation_status="accepted_core_distilled", memory_tier="核心画像"),
                self.record(2),
                self.record(3, action="ignore", category="temporary_or_sensitive", validity="临时"),
                self.record(4, action="backup", category="temporary_or_sensitive", validity="临时"),
                self.record(5, sensitivity="secret"),
                self.record(6, source_kind="unsupported_fixture"),
            ]
            expected = {
                "migrate-active": 1,
                "migrate-candidate": 1,
                "retire": 1,
                "raw-evidence-only": 1,
                "prohibited": 1,
                "owner-decision": 1,
            }
            contract = self.make_fixture(
                root,
                records,
                expected,
                overrides={records[0]["id"]: {"status": "accepted_core_distilled"}},
            )
            summary = self.module.run(
                ["--database-dir", str(root), "--contract", contract.relative_to(root).as_posix(), "--write"]
            )
            self.assertTrue(summary["writes_files"])
            self.assertEqual(summary["disposition_counts"], expected)
            map_path = root / "data/derived/migration/memory_migration_map.v1.jsonl"
            report_path = root / "data/derived/migration/memory_quality_report.v1.json"
            output = map_path.read_text(encoding="utf-8") + report_path.read_text(encoding="utf-8")
            for index in range(1, 7):
                self.assertNotIn(f"private-fixture-statement-{index}", output)
                self.assertNotIn(f"private-fixture-source-{index}", output)
                self.assertNotIn(f"private-fixture-evidence-{index}", output)
            entries = [json.loads(line) for line in map_path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(entries), 6)
            self.assertEqual({row["migration"]["disposition"] for row in entries}, set(expected))

    def test_actual_dataset_dry_run_is_byte_deterministic_and_complete(self) -> None:
        paths = [
            DATABASE_DIR / self.contract["outputs"]["migration_map"],
            DATABASE_DIR / self.contract["outputs"]["quality_report"],
        ]
        before = {
            path: hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None for path in paths
        }
        first = self.module.run(
            ["--database-dir", str(DATABASE_DIR), "--contract", str(CONTRACT.relative_to(DATABASE_DIR)), "--dry-run"]
        )
        second = self.module.run(
            ["--database-dir", str(DATABASE_DIR), "--contract", str(CONTRACT.relative_to(DATABASE_DIR)), "--dry-run"]
        )
        after = {
            path: hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None for path in paths
        }
        self.assertEqual(first, second)
        self.assertEqual(before, after)
        self.assertEqual(first["unique_legacy_ids"], 278)
        self.assertEqual(first["record_occurrences"], 1980)
        self.assertEqual(first["owner_decision_count"], 0)
        self.assertEqual(first["credential_or_secret_id_count"], 0)
        self.assertLessEqual(first["migration_map_bytes"], 921600)
        self.assertLessEqual(first["quality_report_bytes"], 921600)

    def test_credential_shape_fails_closed_without_value_echo(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            secret_value = "sk-" + "A" * 24
            records = [self.record(1, statement=secret_value)]
            contract = self.make_fixture(
                root,
                records,
                {
                    "migrate-active": 0,
                    "migrate-candidate": 1,
                    "retire": 0,
                    "raw-evidence-only": 0,
                    "prohibited": 0,
                    "owner-decision": 0,
                },
            )
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = self.module.main(
                    ["--database-dir", str(root), "--contract", contract.relative_to(root).as_posix(), "--dry-run"]
                )
            self.assertEqual(exit_code, 2)
            self.assertIn("credential-shaped material detected", output.getvalue())
            self.assertNotIn(secret_value, output.getvalue())

    def test_output_traversal_is_rejected_before_write(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            records = [self.record(1)]
            expected = {
                "migrate-active": 0,
                "migrate-candidate": 1,
                "retire": 0,
                "raw-evidence-only": 0,
                "prohibited": 0,
                "owner-decision": 0,
            }
            contract_path = self.make_fixture(root, records, expected)
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            contract["outputs"]["migration_map"] = "../escape.jsonl"
            contract_path.write_text(json.dumps(contract, sort_keys=True) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(self.module.ProfileError, "traversal"):
                self.module.run(
                    ["--database-dir", str(root), "--contract", contract_path.relative_to(root).as_posix(), "--write"]
                )
            self.assertFalse((root.parent / "escape.jsonl").exists())

    def test_baseline_drift_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            records = [self.record(1)]
            expected = {
                "migrate-active": 0,
                "migrate-candidate": 1,
                "retire": 0,
                "raw-evidence-only": 0,
                "prohibited": 0,
                "owner-decision": 0,
            }
            contract = self.make_fixture(root, records, expected)
            active = root / "data/memory/active/active_memory.jsonl"
            active.write_bytes(active.read_bytes() + self.module.canonical_bytes(self.record(2), final_lf=True))
            with self.assertRaisesRegex(self.module.ProfileError, "baseline drift"):
                self.module.run(
                    ["--database-dir", str(root), "--contract", contract.relative_to(root).as_posix(), "--dry-run"]
                )


if __name__ == "__main__":
    unittest.main()

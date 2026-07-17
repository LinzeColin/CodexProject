from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path


DATABASE_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = DATABASE_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import evaluate_memory_production_acceptance as acceptance  # noqa: E402


class MemoryProductionAcceptanceTest(unittest.TestCase):
    def test_candidate_reuses_all_hard_gate_evidence(self) -> None:
        report = acceptance.evaluate_candidate(
            DATABASE_DIR,
            artifact_ref="CANDIDATE_TREE",
            rerun_dependencies=False,
        )
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["production_status"], "CANDIDATE_READY_NOT_PUBLISHED")
        self.assertEqual(set(report["proofs"]), {
            "Discovery",
            "Read",
            "Retrieval",
            "Mutation",
            "Forgetting",
            "Recovery",
        })
        self.assertEqual(set(report["proofs"].values()), {"PASS"})
        self.assertEqual(report["profiles"]["pass_count"], 5)
        self.assertEqual(report["hard_gates"]["benchmark_case_count"], 160)
        self.assertEqual(report["writers_and_shims"]["canonical_writer_count"], 1)
        self.assertEqual(report["writers_and_shims"]["proven_unused_shim_count"], 0)
        self.assertFalse(report["profiles"]["remote_memory_target_tested"])
        self.assertFalse(report["publication"]["asset_published"])
        self.assertEqual(
            report["publication"]["snapshot_repository"],
            acceptance.SNAPSHOT_REPOSITORY,
        )
        self.assertEqual(report["publication"]["required_visibility"], "public")
        self.assertTrue(report["publication"]["public_safe_asset_only"])

    def test_report_check_fails_closed_on_drift(self) -> None:
        report = {"schema_version": acceptance.REPORT_SCHEMA, "status": "PASS"}
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "report.json"
            acceptance.write_or_check(report, path, check=False)
            acceptance.write_or_check(report, path, check=True)
            path.write_text(json.dumps({"status": "FAIL"}), encoding="utf-8")
            with self.assertRaisesRegex(
                acceptance.ProductionAcceptanceError,
                "acceptance_report_drift",
            ):
                acceptance.write_or_check(report, path, check=True)

    def test_non_public_release_contract_is_rejected(self) -> None:
        config = acceptance.load_json_strict(
            DATABASE_DIR / acceptance.DEFAULT_CONFIG,
            "production_config",
        )
        unsafe = copy.deepcopy(config)
        unsafe["release"]["snapshot_repository_visibility"] = "private"
        with self.assertRaisesRegex(
            acceptance.ProductionAcceptanceError,
            "release_visibility_not_public",
        ):
            acceptance.validate_config(unsafe)

    def test_snapshot_repository_contract_is_pinned(self) -> None:
        config = acceptance.load_json_strict(
            DATABASE_DIR / acceptance.DEFAULT_CONFIG,
            "production_config",
        )
        unsafe = copy.deepcopy(config)
        unsafe["release"]["snapshot_repository"] = "LinzeColin/AgentDatabase-Private"
        with self.assertRaisesRegex(
            acceptance.ProductionAcceptanceError,
            "snapshot_repository_mismatch",
        ):
            acceptance.validate_config(unsafe)

    def test_published_history_fetch_depth_is_bounded(self) -> None:
        config = acceptance.load_json_strict(
            DATABASE_DIR / acceptance.DEFAULT_CONFIG,
            "production_config",
        )
        self.assertEqual(config["publication"]["accepted_history_fetch_depth"], 32)
        acceptance.validate_config(config)
        for value in (1, True, 257):
            unsafe = copy.deepcopy(config)
            unsafe["publication"]["accepted_history_fetch_depth"] = value
            with self.subTest(value=value), self.assertRaisesRegex(
                acceptance.ProductionAcceptanceError,
                "published_history_fetch_depth_invalid",
            ):
                acceptance.validate_config(unsafe)

    def test_public_snapshot_requires_commit_only_redacted_records(self) -> None:
        accepted_commit = "a" * 40
        report = {
            "status": "PASS",
            "source_commit": accepted_commit,
            "release_candidate": True,
            "all_members_from_source_commit": True,
            "file_count": 16,
            "commit_file_count": 16,
            "runtime_file_count": 0,
            "release_repository": acceptance.SNAPSHOT_REPOSITORY,
            "release_visibility": "public",
            "canonical": {"record_count": 198},
            "public_release": {
                "public_release_safe_record_count": 198,
                "public_repository_allowed_record_count": 198,
                "redacted_summary_record_count": 198,
                "credential_present_record_count": 0,
            },
        }
        summary = acceptance.validate_public_snapshot_result(
            report,
            accepted_commit=accepted_commit,
        )
        self.assertEqual(summary["public_release_safe_record_count"], 198)
        for key, value, reason in (
            ("release_candidate", False, "public_snapshot_source_boundary_failure"),
            ("runtime_file_count", 3, "public_snapshot_source_boundary_failure"),
        ):
            unsafe = copy.deepcopy(report)
            unsafe[key] = value
            with self.subTest(key=key), self.assertRaisesRegex(
                acceptance.ProductionAcceptanceError,
                reason,
            ):
                acceptance.validate_public_snapshot_result(
                    unsafe,
                    accepted_commit=accepted_commit,
                )
        unsafe = copy.deepcopy(report)
        unsafe["public_release"]["credential_present_record_count"] = 1
        with self.assertRaisesRegex(
            acceptance.ProductionAcceptanceError,
            "public_snapshot_record_boundary_failure",
        ):
            acceptance.validate_public_snapshot_result(
                unsafe,
                accepted_commit=accepted_commit,
            )

    def test_fresh_recovery_report_overrides_tracked_history_bound_report(self) -> None:
        config = acceptance.load_json_strict(
            DATABASE_DIR / acceptance.DEFAULT_CONFIG,
            "production_config",
        )
        tracked = acceptance.load_json_strict(
            DATABASE_DIR / config["required_reports"]["recovery"],
            "tracked_recovery",
        )
        fresh = copy.deepcopy(tracked)
        fresh["source"]["commit"] = "f" * 40
        reports, hashes = acceptance.load_required_reports(
            DATABASE_DIR,
            config,
            recovery_override=fresh,
        )
        self.assertEqual(reports["recovery"]["source"]["commit"], "f" * 40)
        self.assertEqual(
            hashes["recovery"],
            acceptance.sha256_prefixed(acceptance.canonical_json_bytes(fresh)),
        )

    def test_recovery_override_requires_fresh_dependency_rerun(self) -> None:
        with self.assertRaisesRegex(
            acceptance.ProductionAcceptanceError,
            "recovery_override_requires_rerun",
        ):
            acceptance.evaluate_candidate(
                DATABASE_DIR,
                artifact_ref="a" * 40,
                rerun_dependencies=False,
                recovery_source_commit="a" * 40,
            )

    def test_published_phase_requires_exact_commit(self) -> None:
        with self.assertRaisesRegex(
            acceptance.ProductionAcceptanceError,
            "published_ref_invalid",
        ):
            acceptance.evaluate_published(
                DATABASE_DIR,
                acceptance.DEFAULT_CONFIG,
                artifact_ref="main",
            )

    def test_published_hygiene_requires_zero_violations(self) -> None:
        clean = {
            "status": "PASS",
            "mode": "a" * 40,
            "baseline_tree": "b" * 40,
            "violations": [],
            "policy_errors": [],
        }
        self.assertEqual(
            acceptance.validate_repository_hygiene(clean, expected_treeish="a" * 40),
            {
                "status": "PASS",
                "baseline_tree": "b" * 40,
                "violation_count": 0,
            },
        )
        dirty = copy.deepcopy(clean)
        dirty["violations"] = [{"code": "tracked_runtime_noise"}]
        with self.assertRaisesRegex(
            acceptance.ProductionAcceptanceError,
            "repository_hygiene_not_clean",
        ):
            acceptance.validate_repository_hygiene(dirty, expected_treeish="a" * 40)

    def test_latest_required_check_run_must_succeed(self) -> None:
        accepted_commit = "c" * 40
        runs = []
        for index, name in enumerate(acceptance.REQUIRED_CHECK_NAMES, 1):
            runs.append(
                {
                    "id": index,
                    "name": name,
                    "head_sha": accepted_commit,
                    "status": "completed",
                    "conclusion": "success",
                }
            )
        summaries = acceptance.validate_required_check_runs(
            {"check_runs": runs},
            accepted_commit=accepted_commit,
            required_names=acceptance.REQUIRED_CHECK_NAMES,
        )
        self.assertEqual([item["name"] for item in summaries], list(acceptance.REQUIRED_CHECK_NAMES))
        runs.append(
            {
                "id": 99,
                "name": "governance",
                "head_sha": accepted_commit,
                "status": "completed",
                "conclusion": "failure",
            }
        )
        with self.assertRaisesRegex(
            acceptance.ProductionAcceptanceError,
            "required_check_not_success_governance",
        ):
            acceptance.validate_required_check_runs(
                {"check_runs": runs},
                accepted_commit=accepted_commit,
                required_names=acceptance.REQUIRED_CHECK_NAMES,
            )


if __name__ == "__main__":
    unittest.main()

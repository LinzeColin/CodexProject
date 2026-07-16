from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = REPO_ROOT / "scripts" / "memory_atlas_proposal_workflow.py"
HISTORICAL_BUILDER_PATH = REPO_ROOT / "scripts" / "build_memory_atlas_proposal_apply.py"


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def make_workspace(root: Path) -> tuple[Path, Path]:
    app_support = root / "app-support"
    source_root = app_support / "source"
    (source_root / "data/derived/proposals/apply_ready").mkdir(parents=True)
    (source_root / "data/derived/proposals").mkdir(parents=True, exist_ok=True)
    (source_root / "config/r4_acceptance").mkdir(parents=True)
    (source_root / "人类可读").mkdir(parents=True)
    (source_root / "memory_atlas_source_workspace.json").write_text(
        json.dumps(
            {
                "schema_version": "memory_atlas_source_workspace.v1",
                "original_repo_root": "/temporary/canonical/repo",
                "installed_git_commit": "r4-fixture",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    write_json(
        source_root / "data/derived/proposals/proposal_state_machine_report.json",
        {
            "schema_version": "openai_database.proposal_state_machine.v1_2_s13_p1",
            "proposals": [
                {
                    "proposal_id": "proposal_review_only",
                    "current_state": "pending_human_review",
                    "approval_status": "not_approved",
                    "target_type": "config",
                    "target_files": ["config/"],
                    "expires_at": "2026-08-07T08:18:30Z",
                    "expiry_bucket": "active",
                }
            ],
        },
    )
    write_json(
        source_root / "data/derived/proposals/diff_narrator_report.json",
        {
            "schema_version": "openai_database.diff_narrator.v1_2_s13_p2",
            "narrations": [
                {
                    "proposal_id": "proposal_review_only",
                    "risk_level": "medium",
                    "target_type": "config",
                    "target_files": ["config/"],
                    "what_changed_zh": "改了什么：尚未生成精确文件内容。",
                    "why_changed_zh": "为什么改：需要先补齐结构化变更。",
                    "affected_surfaces_zh": "影响什么：当前只可复核。",
                    "how_to_verify_zh": "如何验证：生成精确 bundle 后再验证。",
                    "how_to_rollback_zh": "如何回滚：当前没有写入。",
                }
            ],
        },
    )
    return app_support, source_root


def bundle_payload(
    proposal_id: str,
    target_file: str,
    *,
    expected_sha256: str,
    content: str,
    target_type: str = "config",
    expires_at: str = "2099-08-07T08:18:30Z",
    validation_ids: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": "memory_atlas_apply_ready_proposal.v1_2_r4",
        "proposal_id": proposal_id,
        "current_state": "pending_human_review",
        "target_type": target_type,
        "risk_level": "low",
        "expires_at": expires_at,
        "action_half_life": "this_week",
        "human_reason_zh": "用于验证人类授权后的结构化本地变更。",
        "narrator": {
            "what_changed_zh": "改了什么：替换一个精确目标文件。",
            "why_changed_zh": "为什么改：验证真实授权闭环。",
            "affected_surfaces_zh": f"影响什么：仅影响 {target_file}。",
            "how_to_verify_zh": "如何验证：运行固定 JSON 和 UTF-8 验证器。",
            "how_to_rollback_zh": "如何回滚：恢复事务开始前的完整字节。",
        },
        "operations": [
            {
                "operation": "replace_text",
                "target_file": target_file,
                "expected_sha256": expected_sha256,
                "content": content,
            }
        ],
        "validation_ids": validation_ids or ["utf8_nonempty", "json_document"],
        "rollback_plan_zh": "恢复事务快照并核对原始 SHA-256；raw 文件不参与回滚。",
    }


class ProposalWorkflowPresenceTests(unittest.TestCase):
    def test_r4_workflow_module_exists(self) -> None:
        self.assertTrue(WORKFLOW_PATH.is_file(), "R4 proposal workflow module is missing")


class ProposalWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module("memory_atlas_proposal_workflow_test", WORKFLOW_PATH)

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.app_support, self.source_root = make_workspace(self.root)
        self.token_values = iter(
            [
                "review-token-success",
                "review-token-failure",
                "review-token-other",
                "rollback-token-success",
                "rollback-token-review",
                "transaction-random",
            ]
            * 10
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def workflow(self, *, now_epoch: float = 1_800_000_000.0, token_ttl_seconds: int = 600) -> Any:
        return self.module.ProposalWorkflow(
            self.module.ProposalWorkflowContext(
                source_root=self.source_root,
                app_support=self.app_support,
                token_ttl_seconds=token_ttl_seconds,
            ),
            now_fn=lambda: now_epoch,
            token_factory=lambda: next(self.token_values),
        )

    def write_bundle(self, payload: dict[str, Any], name: str | None = None) -> Path:
        path = self.source_root / "data/derived/proposals/apply_ready" / f"{name or payload['proposal_id']}.json"
        write_json(path, payload)
        return path

    def test_review_separates_apply_ready_and_review_only_without_operation_content(self) -> None:
        target = self.source_root / "config/r4_acceptance/success.json"
        before = b'{"value":"before"}\n'
        target.write_bytes(before)
        self.write_bundle(
            bundle_payload(
                "proposal_success",
                "config/r4_acceptance/success.json",
                expected_sha256=sha256_bytes(before),
                content='{"value":"after"}\n',
            )
        )
        review = self.workflow().review()
        indexed = {item["proposal_id"]: item for item in review["proposals"]}
        self.assertTrue(indexed["proposal_success"]["apply_ready"])
        self.assertRegex(indexed["proposal_success"]["review_token"], r"\S+")
        self.assertFalse(indexed["proposal_review_only"]["apply_ready"])
        self.assertIn("缺少", indexed["proposal_review_only"]["blocked_reason_zh"])
        serialized = json.dumps(review, ensure_ascii=False)
        self.assertNotIn('{"value":"after"}', serialized)
        for field in self.module.REQUIRED_NARRATOR_FIELDS:
            self.assertRegex(indexed["proposal_success"]["narrator"][field], r"[\u4e00-\u9fff]")

    def test_successful_authorized_apply_and_manual_rollback_restore_exact_bytes(self) -> None:
        target = self.source_root / "config/r4_acceptance/success.json"
        before = b'{"value":"before"}\n'
        after = b'{"value":"after","approved_change":true}\n'
        target.write_bytes(before)
        self.write_bundle(
            bundle_payload(
                "proposal_success",
                "config/r4_acceptance/success.json",
                expected_sha256=sha256_bytes(before),
                content=after.decode(),
            )
        )
        workflow = self.workflow()
        review = workflow.review()
        proposal = next(item for item in review["proposals"] if item["proposal_id"] == "proposal_success")

        applied = workflow.approve_and_apply(
            proposal_id="proposal_success",
            review_token=proposal["review_token"],
            confirmation="授权应用 proposal_success",
        )
        self.assertEqual(applied["status"], "success")
        self.assertEqual(target.read_bytes(), after)
        self.assertEqual(
            applied["state_history"],
            ["pending_human_review", "approved_by_human", "applying", "applied", "validated", "committed"],
        )
        self.assertTrue(applied["rollback_available"])
        transaction_dir = self.app_support / "proposal_transactions" / applied["transaction_id"]
        self.assertTrue((transaction_dir / "transaction.json").is_file())
        self.assertTrue((transaction_dir / "snapshots/000.bin").is_file())

        rolled_back = workflow.rollback(
            transaction_id=applied["transaction_id"],
            rollback_token=applied["rollback_token"],
            confirmation=f"确认回滚 {applied['transaction_id']}",
        )
        self.assertEqual(rolled_back["status"], "success")
        self.assertEqual(rolled_back["state"], "rolled_back_by_human")
        self.assertEqual(target.read_bytes(), before)

    def test_validation_failure_automatically_restores_every_target(self) -> None:
        target = self.source_root / "config/r4_acceptance/failure.json"
        before = b'{"value":"before"}\n'
        target.write_bytes(before)
        self.write_bundle(
            bundle_payload(
                "proposal_failure",
                "config/r4_acceptance/failure.json",
                expected_sha256=sha256_bytes(before),
                content="not-json\n",
                validation_ids=["utf8_nonempty", "json_document"],
            )
        )
        workflow = self.workflow()
        proposal = next(item for item in workflow.review()["proposals"] if item["proposal_id"] == "proposal_failure")
        result = workflow.approve_and_apply(
            proposal_id="proposal_failure",
            review_token=proposal["review_token"],
            confirmation="授权应用 proposal_failure",
        )
        self.assertEqual(result["status"], "validation_failed_rolled_back")
        self.assertEqual(result["state"], "rollback_or_needs_revision")
        self.assertTrue(result["automatic_rollback"])
        self.assertEqual(target.read_bytes(), before)
        self.assertEqual(result["restored_sha256"]["config/r4_acceptance/failure.json"], sha256_bytes(before))

    def test_parent_symlink_swap_after_review_never_writes_outside_source(self) -> None:
        target_parent = self.source_root / "config/r4_acceptance"
        target = target_parent / "success.json"
        before = b'{"value":"before"}\n'
        after = b'{"value":"after"}\n'
        target.write_bytes(before)
        self.write_bundle(
            bundle_payload(
                "proposal_success",
                "config/r4_acceptance/success.json",
                expected_sha256=sha256_bytes(before),
                content=after.decode(),
            )
        )
        workflow = self.workflow()
        proposal = next(item for item in workflow.review()["proposals"] if item["proposal_id"] == "proposal_success")

        parked_parent = self.source_root / "config/r4_acceptance_original"
        outside_parent = self.root / "outside"
        outside_parent.mkdir()
        outside_target = outside_parent / "success.json"
        outside_target.write_bytes(before)
        original_parse_bundle = workflow._parse_bundle

        def parse_then_swap(*args: Any, **kwargs: Any) -> Any:
            parsed = original_parse_bundle(*args, **kwargs)
            target_parent.rename(parked_parent)
            target_parent.symlink_to(outside_parent, target_is_directory=True)
            return parsed

        workflow._parse_bundle = parse_then_swap
        with self.assertRaises(self.module.ProposalWorkflowError):
            workflow.approve_and_apply(
                proposal_id="proposal_success",
                review_token=proposal["review_token"],
                confirmation="授权应用 proposal_success",
            )

        self.assertEqual(outside_target.read_bytes(), before)
        self.assertEqual((parked_parent / "success.json").read_bytes(), before)

    def test_interrupted_apply_is_automatically_recovered_on_next_review(self) -> None:
        target = self.source_root / "config/r4_acceptance/success.json"
        before = b'{"value":"before"}\n'
        after = b'{"value":"after"}\n'
        target.write_bytes(before)
        self.write_bundle(
            bundle_payload(
                "proposal_success",
                "config/r4_acceptance/success.json",
                expected_sha256=sha256_bytes(before),
                content=after.decode(),
            )
        )
        workflow = self.workflow()
        proposal = next(item for item in workflow.review()["proposals"] if item["proposal_id"] == "proposal_success")

        class SimulatedProcessExit(BaseException):
            pass

        original_atomic_write_at = workflow._atomic_write_at

        def write_then_exit(*args: Any, **kwargs: Any) -> None:
            original_atomic_write_at(*args, **kwargs)
            raise SimulatedProcessExit()

        workflow._atomic_write_at = write_then_exit
        with self.assertRaises(SimulatedProcessExit):
            workflow.approve_and_apply(
                proposal_id="proposal_success",
                review_token=proposal["review_token"],
                confirmation="授权应用 proposal_success",
            )
        self.assertEqual(target.read_bytes(), after)

        review = self.workflow().review()
        transaction_path = next((self.app_support / "proposal_transactions").glob("txn_*/transaction.json"))
        transaction = json.loads(transaction_path.read_text(encoding="utf-8"))
        self.assertEqual(target.read_bytes(), before)
        self.assertEqual(transaction["state"], "recovered_after_interruption")
        self.assertIn("recovered_after_interruption", transaction["state_history"])
        self.assertEqual(review["summary"]["interrupted_recovery_count"], 1)

    def test_interrupted_recovery_failure_is_visible_and_can_be_manually_rolled_back(self) -> None:
        target_parent = self.source_root / "config/r4_acceptance"
        target = target_parent / "success.json"
        before = b'{"value":"before"}\n'
        after = b'{"value":"after"}\n'
        target.write_bytes(before)
        self.write_bundle(
            bundle_payload(
                "proposal_success",
                "config/r4_acceptance/success.json",
                expected_sha256=sha256_bytes(before),
                content=after.decode(),
            )
        )
        workflow = self.workflow()
        proposal = next(item for item in workflow.review()["proposals"] if item["proposal_id"] == "proposal_success")

        class SimulatedProcessExit(BaseException):
            pass

        original_atomic_write_at = workflow._atomic_write_at

        def write_then_exit(*args: Any, **kwargs: Any) -> None:
            original_atomic_write_at(*args, **kwargs)
            raise SimulatedProcessExit()

        workflow._atomic_write_at = write_then_exit
        with self.assertRaises(SimulatedProcessExit):
            workflow.approve_and_apply(
                proposal_id="proposal_success",
                review_token=proposal["review_token"],
                confirmation="授权应用 proposal_success",
            )
        self.assertEqual(target.read_bytes(), after)

        parked_parent = self.source_root / "config/r4_acceptance_original"
        outside_parent = self.root / "outside-recovery"
        outside_parent.mkdir()
        target_parent.rename(parked_parent)
        target_parent.symlink_to(outside_parent, target_is_directory=True)

        recovery_workflow = self.workflow()
        review = recovery_workflow.review()
        self.assertEqual(review["summary"]["manual_recovery_required_count"], 1)
        transaction = review["transactions"][0]
        self.assertEqual(transaction["state"], "manual_rollback_required")

        target_parent.unlink()
        parked_parent.rename(target_parent)
        result = recovery_workflow.rollback(
            transaction_id=transaction["transaction_id"],
            rollback_token=transaction["rollback_token"],
            confirmation=f"确认回滚 {transaction['transaction_id']}",
        )
        self.assertEqual(result["state"], "rolled_back_by_human")
        self.assertEqual(target.read_bytes(), before)

    def test_missing_target_parent_is_review_only_and_never_created(self) -> None:
        missing_parent = self.source_root / "config/not-created-by-proposal"
        self.write_bundle(
            bundle_payload(
                "proposal_missing_parent",
                "config/not-created-by-proposal/change.json",
                expected_sha256="missing",
                content='{"value":"after"}\n',
            )
        )
        review = self.workflow().review()
        proposal = next(item for item in review["proposals"] if item["proposal_id"] == "proposal_missing_parent")
        self.assertFalse(proposal["apply_ready"])
        self.assertFalse(missing_parent.exists())

    def test_prepare_read_failure_closes_current_parent_fd(self) -> None:
        target = self.source_root / "config/r4_acceptance/success.json"
        before = b'{"value":"before"}\n'
        target.write_bytes(before)
        bundle_path = self.write_bundle(
            bundle_payload(
                "proposal_success",
                "config/r4_acceptance/success.json",
                expected_sha256=sha256_bytes(before),
                content='{"value":"after"}\n',
            )
        )
        workflow = self.workflow()
        proposal = next(item for item in workflow.review()["proposals"] if item["proposal_id"] == "proposal_success")
        parsed = workflow._parse_bundle(bundle_path, now=1_800_000_000.0, verify_current_hash=True)
        workflow._parse_bundle = lambda *_args, **_kwargs: parsed
        opened_fds: list[int] = []
        original_open_parent = workflow._open_target_parent

        def open_and_capture(*args: Any, **kwargs: Any) -> tuple[int, str]:
            parent_fd, target_name = original_open_parent(*args, **kwargs)
            opened_fds.append(parent_fd)
            return parent_fd, target_name

        workflow._open_target_parent = open_and_capture
        workflow._read_regular_at = lambda *_args, **_kwargs: (_ for _ in ()).throw(
            self.module.ProposalBundleError("simulated safe read failure")
        )
        with self.assertRaises(self.module.ProposalBundleError):
            workflow.approve_and_apply(
                proposal_id="proposal_success",
                review_token=proposal["review_token"],
                confirmation="授权应用 proposal_success",
            )
        self.assertTrue(opened_fds)
        with self.assertRaises(OSError):
            os.fstat(opened_fds[-1])

    def test_review_token_is_bound_single_use_and_expires(self) -> None:
        target = self.source_root / "config/r4_acceptance/success.json"
        before = b'{"value":"before"}\n'
        target.write_bytes(before)
        bundle = self.write_bundle(
            bundle_payload(
                "proposal_success",
                "config/r4_acceptance/success.json",
                expected_sha256=sha256_bytes(before),
                content='{"value":"after"}\n',
            )
        )
        workflow = self.workflow(now_epoch=1_800_000_000.0, token_ttl_seconds=1)
        token = next(item for item in workflow.review()["proposals"] if item["proposal_id"] == "proposal_success")["review_token"]
        payload = json.loads(bundle.read_text(encoding="utf-8"))
        payload["human_reason_zh"] = "bundle 已在 review 后改变。"
        write_json(bundle, payload)
        with self.assertRaises(self.module.ProposalAuthorizationError):
            workflow.approve_and_apply(
                proposal_id="proposal_success",
                review_token=token,
                confirmation="授权应用 proposal_success",
            )

        fresh_workflow = self.workflow(now_epoch=1_800_000_000.0, token_ttl_seconds=1)
        fresh_token = next(item for item in fresh_workflow.review()["proposals"] if item["proposal_id"] == "proposal_success")["review_token"]
        fresh_workflow.now_fn = lambda: 1_800_000_010.0
        with self.assertRaises(self.module.ProposalAuthorizationError):
            fresh_workflow.approve_and_apply(
                proposal_id="proposal_success",
                review_token=fresh_token,
                confirmation="授权应用 proposal_success",
            )

    def test_wrong_confirmation_and_token_replay_never_write(self) -> None:
        target = self.source_root / "config/r4_acceptance/success.json"
        before = b'{"value":"before"}\n'
        target.write_bytes(before)
        self.write_bundle(
            bundle_payload(
                "proposal_success",
                "config/r4_acceptance/success.json",
                expected_sha256=sha256_bytes(before),
                content='{"value":"after"}\n',
            )
        )
        workflow = self.workflow()
        token = next(item for item in workflow.review()["proposals"] if item["proposal_id"] == "proposal_success")["review_token"]
        with self.assertRaises(self.module.ProposalAuthorizationError):
            workflow.approve_and_apply(
                proposal_id="proposal_success",
                review_token=token,
                confirmation="yes",
            )
        self.assertEqual(target.read_bytes(), before)
        result = workflow.approve_and_apply(
            proposal_id="proposal_success",
            review_token=token,
            confirmation="授权应用 proposal_success",
        )
        self.assertEqual(result["status"], "success")
        with self.assertRaises(self.module.ProposalAuthorizationError):
            workflow.approve_and_apply(
                proposal_id="proposal_success",
                review_token=token,
                confirmation="授权应用 proposal_success",
            )

    def test_raw_traversal_absolute_symlink_and_unknown_validator_bundles_are_review_only(self) -> None:
        outside = self.root / "outside.json"
        outside.write_text("outside\n", encoding="utf-8")
        symlink = self.source_root / "config/r4_acceptance/link.json"
        symlink.symlink_to(outside)
        cases = [
            ("proposal_raw_target", "data/raw/transcript.json", "config", "missing", ["json_document"]),
            ("proposal_traversal", "config/../../outside.json", "config", "missing", ["json_document"]),
            ("proposal_absolute", str(outside), "config", sha256_bytes(outside.read_bytes()), ["json_document"]),
            ("proposal_symlink_target", "config/r4_acceptance/link.json", "config", sha256_bytes(outside.read_bytes()), ["json_document"]),
            ("proposal_validator", "config/r4_acceptance/new.json", "config", "missing", ["python3 arbitrary.py"]),
            ("proposal_wrong_root", "人类可读/change.md", "config", "missing", ["utf8_nonempty"]),
        ]
        for proposal_id, target_file, target_type, expected, validation_ids in cases:
            self.write_bundle(
                bundle_payload(
                    proposal_id,
                    target_file,
                    target_type=target_type,
                    expected_sha256=expected,
                    content='{"safe":true}\n',
                    validation_ids=validation_ids,
                )
            )
        review = self.workflow().review()
        indexed = {item["proposal_id"]: item for item in review["proposals"]}
        for proposal_id, *_rest in cases:
            with self.subTest(proposal_id=proposal_id):
                self.assertFalse(indexed[proposal_id]["apply_ready"])
                self.assertNotIn("review_token", indexed[proposal_id])
        self.assertEqual(outside.read_text(encoding="utf-8"), "outside\n")

    def test_expected_sha_mismatch_fails_before_transaction_or_write(self) -> None:
        target = self.source_root / "config/r4_acceptance/success.json"
        before = b'{"value":"before"}\n'
        target.write_bytes(before)
        self.write_bundle(
            bundle_payload(
                "proposal_success",
                "config/r4_acceptance/success.json",
                expected_sha256="0" * 64,
                content='{"value":"after"}\n',
            )
        )
        review = self.workflow().review()
        item = next(item for item in review["proposals"] if item["proposal_id"] == "proposal_success")
        self.assertFalse(item["apply_ready"])
        self.assertEqual(target.read_bytes(), before)
        self.assertFalse((self.app_support / "proposal_transactions").exists())

    def test_audit_and_transaction_metadata_do_not_contain_content_or_absolute_source_path(self) -> None:
        target = self.source_root / "config/r4_acceptance/success.json"
        before = b'{"private_marker":"before"}\n'
        after = b'{"private_marker":"after"}\n'
        target.write_bytes(before)
        self.write_bundle(
            bundle_payload(
                "proposal_success",
                "config/r4_acceptance/success.json",
                expected_sha256=sha256_bytes(before),
                content=after.decode(),
            )
        )
        workflow = self.workflow()
        item = next(item for item in workflow.review()["proposals"] if item["proposal_id"] == "proposal_success")
        applied = workflow.approve_and_apply(
            proposal_id="proposal_success",
            review_token=item["review_token"],
            confirmation="授权应用 proposal_success",
        )
        audit = (self.app_support / "proposal_audit.jsonl").read_text(encoding="utf-8")
        transaction = (
            self.app_support
            / "proposal_transactions"
            / applied["transaction_id"]
            / "transaction.json"
        ).read_text(encoding="utf-8")
        for metadata in (audit, transaction):
            self.assertNotIn("private_marker", metadata)
            self.assertNotIn(str(self.source_root), metadata)
        self.assertIn("config/r4_acceptance/success.json", transaction)


class HistoricalAtlasctlApplySafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.builder = load_module("memory_atlas_historical_apply_test", HISTORICAL_BUILDER_PATH)

    def test_non_dry_run_static_fixture_cannot_write_without_r4_ui_authorization(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_dir = Path(temp_dir) / "database"
            config = database_dir / self.builder.CONFIG_PATH
            state = database_dir / self.builder.STATE_MACHINE_REPORT_PATH
            diff = database_dir / self.builder.DIFF_NARRATOR_REPORT_PATH
            config.parent.mkdir(parents=True)
            state.parent.mkdir(parents=True)
            shutil.copy2(REPO_ROOT / self.builder.CONFIG_PATH, config)
            shutil.copy2(REPO_ROOT / self.builder.STATE_MACHINE_REPORT_PATH, state)
            shutil.copy2(REPO_ROOT / self.builder.DIFF_NARRATOR_REPORT_PATH, diff)
            result = self.builder.build_apply_attempt(database_dir, "sample", dry_run=False)
            target = database_dir / "data/derived/proposals/apply_results/sample_authorized_apply_result.json"
            self.assertEqual(result["status"], "FAIL_CLOSED")
            self.assertFalse(result["writes_files"])
            self.assertFalse(result["applies_proposal"])
            self.assertIn("本地 Memory Atlas", result["failure_explanation_zh"])
            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()

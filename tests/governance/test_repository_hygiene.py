from __future__ import annotations

import copy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import repository_hygiene_audit as hygiene  # noqa: E402


class RepositoryHygieneTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = hygiene.load_policy(ROOT / "governance" / "repository_hygiene_policy.json")

    def test_current_worktree_passes_fail_closed_policy(self) -> None:
        result = hygiene.audit_repository(root=ROOT, policy=self.policy)
        self.assertEqual(result["status"], "PASS", result)
        self.assertEqual(result["metrics"]["tracked_runtime_noise_count"], 0)
        self.assertEqual(result["metrics"]["forbidden_backup_producer_count"], 0)
        # 原断言 retained_large_object_count > 0，用意是「留存机制别悄悄空转」。仓库拆分后本仓
        # 的大对象与归档全部随项目迁出（OpenAIDatabase/PFI/arxiv-daily-push 的大对象条目已剪除，
        # Alpha/EVA_OS/KM_IDSystem 归档已迁往 LinzeColin/Archive）——故当前 0 文件匹配是【真实
        # 状态】而非机制失效。原意「防策略被清空」应校验策略本身仍定义了规则，而不是要求文件存在。
        self.assertGreater(
            len(self.policy.get("retained_objects", [])),
            0,
            "留存策略 retained_objects 被清空——机制已空转。"
            "（计数为 0 属正常：受管文件已随项目迁出；此处校验策略本身仍声明了规则。）",
        )

    def test_retained_object_metadata_is_required(self) -> None:
        policy = copy.deepcopy(self.policy)
        policy["retained_objects"][0]["owner"] = ""
        errors = hygiene.validate_policy(policy, root=ROOT)
        self.assertTrue(any(".owner must be non-empty" in error for error in errors), errors)

    def test_baseline_tree_is_reachable_from_head_history(self) -> None:
        result = self._git(ROOT, "log", "--format=%T", "HEAD")
        self.assertIn(self.policy["baseline_tree"], result.stdout.splitlines())

    def test_new_large_archive_runtime_noise_and_backup_producer_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._git(root, "init", "-q")
            self._git(root, "config", "user.name", "Repository Hygiene Test")
            self._git(root, "config", "user.email", "hygiene-test@example.invalid")
            (root / "scripts").mkdir()
            (root / "scripts/ok.sh").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            (root / "existing.bin").write_bytes(b"x" * 256)
            self._git(root, "add", ".")
            self._git(root, "commit", "-qm", "baseline")
            baseline_tree = self._git(root, "rev-parse", "HEAD^{tree}").stdout.strip()

            policy = copy.deepcopy(self.policy)
            policy["baseline_tree"] = baseline_tree
            policy["regular_blob_max_bytes"] = 128
            policy["retained_objects"] = [
                {
                    "id": "TEST_BASELINE_OBJECT",
                    "path": "existing.bin",
                    "kinds": ["large"],
                    "owner": "test owner",
                    "purpose": "negative fixture baseline",
                    "consumer": "focused unit test",
                    "retention": "test lifetime",
                    "recovery": "baseline commit",
                    "confidentiality": "synthetic",
                    "change_policy": "baseline_oid_only",
                    "max_bytes": 512,
                }
            ]
            baseline = hygiene.audit_repository(root=root, policy=policy)
            self.assertEqual(baseline["status"], "PASS", baseline)

            (root / "existing.bin").write_bytes(b"z" * 256)
            changed_oid = self._git(root, "hash-object", "existing.bin").stdout.strip()
            policy["retained_objects"][0]["reviewed_oids"] = [changed_oid]
            reviewed = hygiene.audit_repository(root=root, policy=policy)
            self.assertEqual(reviewed["status"], "PASS", reviewed)
            policy["retained_objects"][0]["reviewed_oids"] = []
            (root / "new.bin").write_bytes(b"y" * 256)
            (root / "backup.tar.gz").write_bytes(b"archive")
            (root / ".DS_Store").write_bytes(b"noise")
            (root / "scripts/backup.sh").write_text(
                "#!/bin/sh\ngit bundle create repository.bundle --all\n",
                encoding="utf-8",
            )
            failed = hygiene.audit_repository(root=root, policy=policy)
            codes = {item["code"] for item in failed["violations"]}
            self.assertEqual(failed["status"], "FAIL")
            self.assertIn("large_new_or_modified", codes)
            self.assertIn("large_retention_rule_count", codes)
            self.assertIn("archive_retention_rule_count", codes)
            self.assertIn("tracked_runtime_noise", codes)
            self.assertIn("forbidden_repository_backup_producer", codes)

    @staticmethod
    def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            ["git", *args],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise AssertionError(result.stderr)
        return result


if __name__ == "__main__":
    unittest.main()

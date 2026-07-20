from __future__ import annotations

import copy
import importlib.util
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"


def load_module(name: str, path: Path):
    scripts_dir = str(SCRIPTS)
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class RetiredProjectRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load_module(
            "validate_project_governance_retirement_test",
            SCRIPTS / "validate_project_governance.py",
        )
        cls.lean = load_module(
            "lean_governance_retirement_test",
            SCRIPTS / "lean_governance.py",
        )
        cls.config = cls.validator.load_yaml(ROOT / "governance" / "projects.yaml")

    def test_wda_is_retired_not_active_and_history_is_preserved(self) -> None:
        active = {item["project_id"]: item for item in self.config["projects"]}
        retired = {item["project_id"]: item for item in self.config["retired_projects"]}
        self.assertNotIn("WDA", active)
        self.assertEqual(len(active), 0)
        self.assertEqual(retired["WDA"]["status"], "retired")
        self.assertTrue(retired["WDA"]["preserve_history"])
        self.assertTrue(retired["WDA"]["reactivation_requires_owner_authorization"])
        self.assertNotIn("ci_mode", retired["WDA"])
        self.assertNotIn("migration", retired["WDA"])
        self.assertTrue((ROOT / retired["WDA"]["path"]).is_dir())

    def test_migrated_projects_are_registered_with_evidence_and_removed(self) -> None:
        active = {item["project_id"] for item in self.config["projects"]}
        migrated = {item["project_id"]: item for item in self.config["migrated_projects"]}
        self.assertEqual(
            set(migrated),
            {"whkmSalary", "Alpha", "FIFA", "QBVS", "MetaDatabase", "Serenity-Alipay", "EEI",
             "KM_IDSystem", "OpenAIDatabase", "KMFA", "PFI", "arxiv-daily-push"},
        )
        for project_id, entry in migrated.items():
            self.assertNotIn(project_id, active)
            self.assertEqual(entry["status"], "migrated")
            self.assertTrue(entry["history_preserved_in_target"])
            self.assertTrue(entry["reactivation_requires_owner_authorization"])
            self.assertTrue(entry["target_repo"].startswith("LinzeColin/"))
            self.assertEqual(len(entry["source_tree_sha"]), 40)
            self.assertTrue(entry["evidence_refs"])
            for ref in entry["evidence_refs"]:
                self.assertTrue((ROOT / ref).is_file())
            # 目录必须真的已从本仓库移除 —— 否则迁移只做了一半
            self.assertFalse((ROOT / entry["path"]).exists())

    def test_root_change_fans_out_to_active_required_projects_only(self) -> None:
        selection = self.validator.changed_scope_selection(
            self.config,
            ["governance/projects.yaml"],
        )
        selected = {item["project_id"] for item in selection["projects"]}
        self.assertEqual(len(selected), 0)
        self.assertNotIn("WDA", selected)
        self.assertEqual(selection["required_project_count"], 0)
        self.assertEqual(selection["selected_required_project_count"], 0)
        self.assertTrue(selection["all_required_projects_covered"])
        self.assertEqual(selection["retired_project_ids"], ["WDA"])
        self.assertEqual(selection["retired_changed_files"], [])

    def test_direct_retired_project_change_fails_closed(self) -> None:
        selection = self.validator.changed_scope_selection(
            self.config,
            ["WDA/src/wda_app/main.py"],
        )
        self.assertEqual(selection["retired_changed_files"], ["WDA/src/wda_app/main.py"])
        self.assertEqual(selection["unknown_changed_files"], [])
        with patch.object(
            self.lean,
            "git_content_changed_files",
            return_value=["WDA/src/wda_app/main.py"],
        ):
            with self.assertRaises(self.lean.governance.GovernanceDiffError) as raised:
                self.lean.build_changed_scope(
                    "BASE",
                    root=ROOT,
                    projects_file=ROOT / "governance" / "projects.yaml",
                )
        self.assertEqual(raised.exception.error_code, "RETIRED_PROJECT_CHANGE")

    def test_active_and_retired_registry_entries_must_be_disjoint(self) -> None:
        config = copy.deepcopy(self.config)
        config["projects"].append(
            {
                "project_id": "WDA",
                "path": "WDA",
                "ci_mode": "required",
                "migration": {"version": "lean-v2"},
            }
        )
        validation = self.validator.Validation()
        self.validator.validate_root(validation, config)
        messages = [issue.message for issue in validation.errors]
        self.assertTrue(
            any("both active and retired" in message for message in messages),
            messages,
        )

    def test_readme_separates_active_table_from_retired_history(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        active_rows = {
            match.group(1)
            for match in re.finditer(
                r"^\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|",
                text,
                re.M,
            )
            if match.group(1) != "Project"
        }
        self.assertNotIn("WDA", active_rows)
        self.assertIn("## Retired projects", text)
        self.assertIn("WDA", text)

    def test_explicit_retired_project_is_not_reported_as_unknown(self) -> None:
        with self.assertRaises(self.lean.RetiredProjectError):
            self.lean.registered_project(self.config, "WDA")
        result = subprocess.run(
            [
                sys.executable,
                "-B",
                str(SCRIPTS / "lean_governance.py"),
                "check-render",
                "--project",
                "WDA",
            ],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(payload["error_code"], "RETIRED_PROJECT")

    def test_wda_tree_matches_retirement_implementation_base(self) -> None:
        """承重：WDA 自退休以来零改动（退休项目不得被修改）。

        权威判据是退休清单里记录的 `wda_tree_sha`——它就是退休那一刻 WDA 的树。
        原实现还额外用 `implementation_base_sha` 反解一次树来交叉验证，但仓库拆分期间
        多次 `git filter-repo` 重写了历史，该 base 提交已不可达（`bad object`），
        导致本测试自那以后永久报错、掩盖了它本该守护的不变量。现改为：树 sha 断言恒定执行；
        base 提交仅在仍可达时才做交叉验证，不可达则跳过并说明，不再 fail-closed 在一个死引用上。
        """
        manifest = json.loads(
            (ROOT / "governance" / "run_manifests" / "GOV-WDA-RETIREMENT-20260713.json").read_text(
                encoding="utf-8"
            )
        )
        current_tree = subprocess.check_output(
            ["git", "rev-parse", "HEAD:WDA"],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
        ).strip()
        # ★承重★：改动 WDA 任一字节，此断言即失败
        self.assertEqual(current_tree, manifest["wda_tree_sha"])

        base = manifest["implementation_base_sha"]
        base_reachable = subprocess.run(
            ["git", "cat-file", "-e", base],
            cwd=ROOT,
            capture_output=True,
        ).returncode == 0
        if base_reachable:
            base_tree = subprocess.check_output(
                ["git", "rev-parse", f"{base}:WDA"],
                cwd=ROOT,
                text=True,
                encoding="utf-8",
            ).strip()
            self.assertEqual(current_tree, base_tree)


if __name__ == "__main__":
    unittest.main()

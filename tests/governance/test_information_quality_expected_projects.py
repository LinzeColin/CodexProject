"""承重：`validate_information_quality.EXPECTED_PROJECTS` 必须与 projects.yaml 的活跃集一致。

背景：`EXPECTED_PROJECTS` 是 CI『Validate all information quality』步骤用来 fail-closed 校验
项目集的硬编码常量。仓库拆分把 10 个项目全部迁出后，本仓活跃项目归零（projects.yaml 的
`projects: []`），但该常量一度仍列着已迁出项目，导致每个项目误报 PROJECT_SET/PROJECT_DIR/
README_PROJECT，慢性拖红夜间 Project Governance。本测试把常量与注册表锁死，防其再次脱节。
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"


def _load(name: str, filename: str):
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ExpectedProjectsMatchesRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.viq = _load("viq_expected_projects_test", "validate_information_quality.py")
        cls.vpg = _load("vpg_expected_projects_test", "validate_project_governance.py")
        cls.registry = cls.vpg.load_yaml(ROOT / "governance" / "projects.yaml")

    def test_expected_projects_equals_active_registry(self) -> None:
        """★承重★：EXPECTED_PROJECTS 必须 == projects.yaml 的活跃 {project_id: path}。

        新增/迁出活跃项目却不同步此常量，本断言即失败——这正是拖红夜间 CI 的脱节。
        """
        active = {
            str(item.get("project_id")): str(item.get("path"))
            for item in (self.registry.get("projects") or [])
            if isinstance(item, dict)
        }
        self.assertEqual(
            dict(self.viq.EXPECTED_PROJECTS),
            active,
            "validate_information_quality.EXPECTED_PROJECTS 与 governance/projects.yaml 的活跃项目集脱节；"
            "拆分后本仓活跃项目为空，二者都应为 {}。",
        )

    def test_information_quality_all_gate_passes(self) -> None:
        """承重：`--all --fail-on-error` 必须 rc=0（CI『Validate all information quality』步骤）。"""
        import subprocess

        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "validate_information_quality.py"),
             "--all", "--fast", "--fail-on-error"],
            cwd=str(ROOT), capture_output=True, text=True,
        )
        self.assertEqual(
            result.returncode, 0,
            f"信息质量全量门禁 fail-closed 未通过：\n{result.stdout[-1200:]}",
        )


if __name__ == "__main__":
    unittest.main()

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
HUMAN_ENTRY_STEMS = ("功能清单", "开发记录", "模型参数文件")


def load_yaml(path: Path):
    """走仓库自带的 yaml-free 加载器（CI 治理测试步骤不装 pyyaml）。

    `validate_project_governance.load_yaml` 在无 pyyaml 时回退到纯 Python 的
    `fallback_yaml_load`；测试里直接 `import yaml` 会在 CI `ModuleNotFoundError`。
    """
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(
        "vpg_human_entry_test", SCRIPTS / "validate_project_governance.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["vpg_human_entry_test"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.load_yaml(path)


def registered_project_paths() -> list[str]:
    """Paths of the active projects only.

    A regex over every `path:` line also swept up retired and migrated
    projects, whose directories are not required to be present here.
    """
    registry = load_yaml(ROOT / "governance" / "projects.yaml")
    return [
        entry["path"]
        for entry in registry.get("projects", [])
        if isinstance(entry, dict) and entry.get("path")
    ]


class HumanEntryMarkdownContractTests(unittest.TestCase):
    def test_registered_projects_use_markdown_human_entries(self) -> None:
        paths = registered_project_paths()
        if not paths:
            # 仓库拆分完成后本仓活跃项目可以为零。原哨兵 assertGreaterEqual(len(paths), 1)
            # 的用意是「别让本测试悄悄变成空转」，零活跃时它会误报。改为：零活跃必须是
            # 「项目都迁出了」这一可证事实，而不是注册表被意外清空/损坏。
            registry = load_yaml(ROOT / "governance" / "projects.yaml")
            migrated = registry.get("migrated_projects") or []
            retired = registry.get("retired_projects") or []
            self.assertGreaterEqual(
                len(migrated) + len(retired), 1,
                "活跃项目为零，且注册表既无 migrated 也无 retired 记录——"
                "这不是拆分完成，而是注册表异常清空。",
            )
            return

        for project_path in paths:
            project_root = ROOT / project_path
            with self.subTest(project=project_path):
                self.assertTrue(project_root.is_dir(), project_path)
                # 采用双平面（存在 文档/ 与 machine/）的项目，人类可读入口是
                # 文档/ 下的七文件；旧三基文件已淘汰、不再要求。
                if (project_root / "文档").is_dir() and (project_root / "machine").is_dir():
                    for name in ("00_我在哪.md", "01_产品需求.md", "02_系统架构.md",
                                 "03_口径字典.md", "04_操作流程.md",
                                 "05_执行与验收.md", "06_运维手册.md"):
                        self.assertTrue((project_root / "文档" / name).is_file(),
                                        f"{project_path}/文档/{name}")
                    continue
                # 未迁移的项目仍走旧三基契约。
                for stem in HUMAN_ENTRY_STEMS:
                    self.assertFalse((project_root / stem).exists(), f"{project_path}/{stem}")
                    self.assertTrue((project_root / f"{stem}.md").is_file(), f"{project_path}/{stem}.md")


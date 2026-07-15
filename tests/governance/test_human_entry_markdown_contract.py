import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
HUMAN_ENTRY_STEMS = ("功能清单", "开发记录", "模型参数文件")


def registered_project_paths() -> list[str]:
    """Paths of the active projects only.

    A regex over every `path:` line also swept up retired and migrated
    projects, whose directories are not required to be present here.
    """
    registry = yaml.safe_load((ROOT / "governance" / "projects.yaml").read_text(encoding="utf-8"))
    return [
        entry["path"]
        for entry in registry.get("projects", [])
        if isinstance(entry, dict) and entry.get("path")
    ]


class HumanEntryMarkdownContractTests(unittest.TestCase):
    def test_registered_projects_use_markdown_human_entries(self) -> None:
        paths = registered_project_paths()
        self.assertGreaterEqual(len(paths), 1)

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


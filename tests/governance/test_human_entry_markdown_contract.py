import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HUMAN_ENTRY_STEMS = ("功能清单", "开发记录", "模型参数文件")


def registered_project_paths() -> list[str]:
    registry = (ROOT / "governance" / "projects.yaml").read_text(encoding="utf-8")
    return re.findall(r'^\s+path:\s+"([^"]+)"', registry, flags=re.MULTILINE)


class HumanEntryMarkdownContractTests(unittest.TestCase):
    def test_registered_projects_use_markdown_human_entries(self) -> None:
        paths = registered_project_paths()
        self.assertGreaterEqual(len(paths), 1)

        for project_path in paths:
            project_root = ROOT / project_path
            with self.subTest(project=project_path):
                self.assertTrue(project_root.is_dir(), project_path)
                for stem in HUMAN_ENTRY_STEMS:
                    self.assertFalse((project_root / stem).exists(), f"{project_path}/{stem}")
                    self.assertTrue((project_root / f"{stem}.md").is_file(), f"{project_path}/{stem}.md")

    def test_independent_qbvs_uses_markdown_human_entries(self) -> None:
        pfi_root = ROOT / "QBVS"
        self.assertTrue(pfi_root.is_dir())
        for stem in HUMAN_ENTRY_STEMS:
            self.assertFalse((pfi_root / stem).exists(), f"QBVS/{stem}")
            self.assertTrue((pfi_root / f"{stem}.md").is_file(), f"QBVS/{stem}.md")

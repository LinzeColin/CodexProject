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

    def test_serenity_three_base_files_are_global_chinese_readable(self) -> None:
        project_root = ROOT / "Serenity-Alipay"
        banned_english_prose = [
            "Candidate scoring and risk gates",
            "Score fund candidates",
            "Recommendation ranking and Top5 allocation",
            "Comparison and discipline alerts",
            "Business-day automation safety",
            "Actionable mail frequency control",
            "Task detail fields",
            "Stage -> Phase -> Task",
            "purpose:",
            "status:",
            "fact_level:",
            "formula_refs:",
            "parameter_refs:",
            "expression_or_pseudocode:",
            "Extracted formula",
            "Grade decision table",
            "Precise gate order",
            "Eligible rows are rows",
        ]
        required_chinese = {
            "功能清单.md": ["中文速读", "核心功能", "明确不做的事"],
            "开发记录.md": ["中文速读", "最近关键修复", "不可回归规则"],
            "模型参数文件.md": ["中文速读", "五个模型", "十二条核心公式和规则", "关键参数表"],
        }
        for filename, required_terms in required_chinese.items():
            path = project_root / filename
            text = path.read_text(encoding="utf-8")
            with self.subTest(file=filename):
                self.assertTrue(text.startswith(f"# {Path(filename).stem}"))
                for term in required_terms:
                    self.assertIn(term, text)
                for phrase in banned_english_prose:
                    self.assertNotIn(phrase, text)

                prose = re.sub(r"`[^`]*`", "", text)
                prose = re.sub(r"\[[^\]]+\]\([^)]+\)", "", prose)
                prose = re.sub(r"https?://\S+", "", prose)
                prose = re.sub(r"\b[A-Z]{2,}(?:-[A-Z0-9]+)*\b", "", prose)
                ascii_words = re.findall(r"[A-Za-z]{4,}", prose)
                cjk_chars = re.findall(r"[\u4e00-\u9fff]", prose)
                self.assertGreater(len(cjk_chars), 800, filename)
                self.assertLess(
                    len(ascii_words),
                    max(20, len(cjk_chars) // 20),
                    f"{filename} has too much English prose: {ascii_words[:20]}",
                )

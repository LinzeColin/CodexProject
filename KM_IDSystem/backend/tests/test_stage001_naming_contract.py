from pathlib import Path
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (PROJECT_ROOT / path).read_text(encoding="utf-8")


class Stage001NamingContractTests(unittest.TestCase):
    def test_active_product_surfaces_use_ids_name(self) -> None:
        required_markers = {
            "README.md": ["# IDS / Industrial Data System"],
            "docs/HANDOFF.md": ["# IDS / Industrial Data System Handoff"],
            "frontend/index.html": ["<title>IDS / Industrial Data System</title>"],
            "frontend/src/App.jsx": ["IDS / Industrial Data System", "<h1>IDS</h1>", "<p>Industrial Data System</p>"],
            "backend/app/core/config.py": ['APP_NAME = "IDS / Industrial Data System"'],
            "backend/app/api/routes.py": ['"service": "ids-industrial-data-system"'],
            "scripts/install_app_entries.sh": [
                'APP_NAME="IDS Industrial Data System.app"',
                'COMMAND_NAME="IDS Industrial Data System.command"',
            ],
            "scripts/build_app_bundle.sh": [
                'APP_NAME="IDS Industrial Data System.app"',
                "IDSIndustrialDataSystem",
                "IDS Industrial Data System",
            ],
            "scripts/run_local_services.sh": ["IDS / Industrial Data System", "ids-industrial-data-system"],
            "scripts/diagnose_app_entry.sh": [
                "IDS Industrial Data System.app",
                "IDS Industrial Data System.command",
            ],
        }

        for path, markers in required_markers.items():
            text = read(path)
            for marker in markers:
                with self.subTest(path=path, marker=marker):
                    self.assertIn(marker, text)

    def test_old_product_names_do_not_remain_on_active_surfaces(self) -> None:
        forbidden_markers = {
            "frontend/index.html": ["武汉开明智能工业运维助手", "Wuhan Kaiming OpMe"],
            "frontend/src/App.jsx": ["<h1>武汉开明</h1>", "智能工业运维助手", "Wuhan Kaiming OpMe"],
            "backend/app/core/config.py": ["武汉开明智能工业运维助手", "Wuhan Kaiming OpMe"],
            "backend/app/api/routes.py": ["wuhan-kaiming-assistant"],
            "scripts/install_app_entries.sh": ["Wuhan Kaiming OpMe"],
            "scripts/build_app_bundle.sh": ["Wuhan Kaiming OpMe"],
            "scripts/run_local_services.sh": [
                "Wuhan Kaiming OpMe",
                "武汉开明智能工业运维助手",
                "wuhan-kaiming-assistant",
            ],
            "scripts/diagnose_app_entry.sh": ["Wuhan Kaiming OpMe"],
        }

        for path, markers in forbidden_markers.items():
            text = read(path)
            for marker in markers:
                with self.subTest(path=path, marker=marker):
                    self.assertNotIn(marker, text)


if __name__ == "__main__":
    unittest.main()

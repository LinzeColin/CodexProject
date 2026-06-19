import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/audit_memory_atlas_visual_acceptance.py"


def load_module():
    spec = importlib.util.spec_from_file_location("audit_memory_atlas_visual_acceptance", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class MemoryAtlasVisualAcceptanceTests(unittest.TestCase):
    def test_visual_acceptance_passes_for_current_repo_sources(self) -> None:
        module = load_module()

        result = module.audit_visual_acceptance(ROOT)

        self.assertEqual(result["status"], "PASS")
        check_names = {check["name"] for check in result["checks"]}
        self.assertIn("galaxy_webgl_has_no_visible_html_dot_overlay", check_names)
        self.assertIn("galaxy_compact_layout_keeps_hud_visible", check_names)
        self.assertIn("graph_nodes_have_no_internal_text_labels", check_names)
        self.assertIn("contribution_grid_uses_full_scene_layout", check_names)


if __name__ == "__main__":
    unittest.main()

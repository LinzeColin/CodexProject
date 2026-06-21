import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CodexRuntimeConfigTests(unittest.TestCase):
    def test_project_runtime_config_uses_codex_shape(self) -> None:
        config_path = ROOT / ".codex/config.toml"
        payload = tomllib.loads(config_path.read_text(encoding="utf-8"))

        self.assertEqual(payload["project_doc_max_bytes"], 24576)
        self.assertFalse(payload["features"]["memories"])
        self.assertFalse(payload["sandbox_workspace_write"]["network_access"])

    def test_project_runtime_config_does_not_contain_manifest_tables(self) -> None:
        payload = tomllib.loads((ROOT / ".codex/config.toml").read_text(encoding="utf-8"))

        for table in ("project", "personalization", "logs", "rules", "codex_user_config_template"):
            self.assertNotIn(table, payload)

    def test_existing_toml_files_are_marked_as_manifests(self) -> None:
        user_manifest = tomllib.loads((ROOT / "config/codex/config.template.toml").read_text(encoding="utf-8"))
        project_manifest = tomllib.loads((ROOT / "config/codex/project.config.toml").read_text(encoding="utf-8"))

        self.assertEqual(
            user_manifest["codex_user_config_template"]["manifest_kind"],
            "user_personalization_manifest",
        )
        self.assertEqual(project_manifest["project"]["manifest_kind"], "project_personalization_manifest")


if __name__ == "__main__":
    unittest.main()

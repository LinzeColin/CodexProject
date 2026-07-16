from __future__ import annotations

import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = str(ROOT / "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


audit = load_module("root_cleanliness_audit_for_tests", ROOT / "scripts" / "root_cleanliness_audit.py")
dashboard = load_module(
    "root_cleanliness_dashboard_for_tests",
    ROOT / "scripts" / "generate_governance_dashboard.py",
)


class RootCleanlinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy_path = ROOT / "governance" / "root_cleanliness_budget.json"
        cls.registry_path = ROOT / "governance" / "projects.yaml"
        cls.policy = audit.load_policy(cls.policy_path)
        cls.registry = audit.load_registry(cls.registry_path, root=ROOT)
        cls.paths = audit.candidate_paths(ROOT)

    def run_audit(self, *, policy=None, registry=None, paths=None):
        return audit.audit_root(
            root=ROOT,
            policy=policy or self.policy,
            registry=registry or self.registry,
            paths=paths or self.paths,
            policy_path=self.policy_path,
            registry_path=self.registry_path,
        )

    def test_current_root_passes_all_cleanliness_gates(self) -> None:
        result = self.run_audit()
        self.assertTrue(result["pass"], result)
        self.assertLessEqual(result["budgets"]["agents_bytes"], 4096)
        self.assertEqual(result["root_inventory"]["unowned_item_count"], 0)
        self.assertEqual(result["broken_local_link_count"], 0)
        self.assertEqual(result["registry"]["unexpected_active_scope_exclusions"], [])

    def test_policy_and_schema_are_machine_readable_and_registered(self) -> None:
        schema_path = ROOT / "governance" / "schemas" / "root_cleanliness_budget.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["schema_version"]["const"], 1)
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(audit.validate_policy(self.policy), [])
        required = set(self.registry["root_governance"]["required_files"])
        self.assertTrue(
            {
                "docs/governance/ROOT_CLEANLINESS.md",
                "governance/root_cleanliness_budget.json",
                "governance/schemas/root_cleanliness_budget.schema.json",
                "scripts/root_cleanliness_audit.py",
                "tests/governance/test_root_cleanliness.py",
            }
            <= required
        )

    def test_readme_is_exact_deterministic_generator_output(self) -> None:
        active = [item for item in self.registry["projects"] if isinstance(item, dict)]
        retired = [item for item in self.registry["retired_projects"] if isinstance(item, dict)]
        rendered = dashboard.render_readme(active, {}, retired)
        self.assertEqual(rendered, (ROOT / "README.md").read_text(encoding="utf-8"))

    def test_unowned_root_item_fails_closed(self) -> None:
        result = self.run_audit(paths=[*self.paths, "rogue-root.txt"])
        self.assertFalse(result["pass"])
        self.assertEqual(result["root_inventory"]["unowned_items"], ["rogue-root.txt"])

    def test_duplicate_registry_identity_fails_closed(self) -> None:
        registry = copy.deepcopy(self.registry)
        registry["projects"].append(copy.deepcopy(registry["projects"][0]))
        result = self.run_audit(registry=registry)
        self.assertFalse(result["pass"])
        self.assertTrue(any("duplicate registry project_id" in item for item in result["errors"]), result)
        self.assertTrue(any("duplicate registry path" in item for item in result["errors"]), result)

    def test_unapproved_active_scope_exclusion_fails_closed(self) -> None:
        registry = copy.deepcopy(self.registry)
        registry["root_governance"]["changed_scope_excluded_projects"] = ["KMFA"]
        result = self.run_audit(registry=registry)
        self.assertFalse(result["pass"])
        self.assertEqual(result["registry"]["unexpected_active_scope_exclusions"], ["KMFA"])

    def test_temporary_state_and_broken_link_detectors_are_negative_guards(self) -> None:
        patterns = self.policy["readme_forbidden_patterns"]
        self.assertTrue(audit.temporary_state_findings("Current Task: TSK.Example.X.0001", patterns))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text("[missing](docs/missing.md)\n", encoding="utf-8")
            findings = audit.local_markdown_link_findings(root, ["README.md"])
        self.assertEqual(findings, ["broken local entry link: README.md -> docs/missing.md"])


if __name__ == "__main__":
    unittest.main()

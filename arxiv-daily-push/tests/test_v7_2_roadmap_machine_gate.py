from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from types import ModuleType


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent
V72_ROOT = PROJECT_ROOT / "docs" / "pursuing_goal" / "v7_2"
VALIDATOR_PATH = V72_ROOT / "tools" / "validate_v7_2_contract.py"


def load_validator() -> ModuleType:
    spec = importlib.util.spec_from_file_location("adp_v72_contract_validator", VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load validator from {VALIDATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class V72RoadmapMachineGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load_validator()

    def test_current_v7_2_roadmap_stop_codes_and_dependencies_are_machine_valid(self) -> None:
        roadmap = self.validator.load_yaml(V72_ROOT / "machine_readable" / "roadmap_v7_2.yaml")
        stops = self.validator.load_yaml(V72_ROOT / "machine_readable" / "stop_codes_v7_2.yaml")
        codes, registry_errors = self.validator.collect_registered_stop_codes(V72_ROOT, REPO_ROOT, stops)
        errors, metrics = self.validator.validate_roadmap_machine_gate(roadmap, codes)

        self.assertEqual([], registry_errors)
        self.assertEqual([], errors)
        self.assertGreaterEqual(metrics["registered_stop_code_count"], 9)
        self.assertEqual(metrics["roadmap_stop_condition_count"], 3)

    def test_product_contract_current_pointer_policy_matches_s3_gate(self) -> None:
        product = self.validator.load_yaml(V72_ROOT / "machine_readable" / "product_contract_v7_2.yaml")
        roadmap = self.validator.load_yaml(V72_ROOT / "machine_readable" / "roadmap_v7_2.yaml")
        pointer = self.validator.load_yaml(V72_ROOT / "machine_readable" / "current_pointer_registry_v7_2.yaml")
        policy = product["current_pointer_policy"]

        self.assertEqual(roadmap["global_current_task"], policy["global_current_task"])
        self.assertEqual(
            pointer["contextual_next_tasks"]["global_current_task"]["task_id"],
            policy["global_current_task"],
        )
        self.assertEqual(roadmap["stage2_shadow_source_next"], policy["shadow_source_next"])
        self.assertEqual(
            pointer["contextual_next_tasks"]["shadow_source_next"]["task_id"],
            policy["shadow_source_next"],
        )
        self.assertNotEqual("S2PCT02", policy["global_current_task"])
        self.assertNotEqual("S2PCT02", policy["shadow_source_next"])

    def test_unknown_stop_code_is_rejected(self) -> None:
        roadmap = {
            "workstreams": [
                {
                    "tasks": [
                        {
                            "task_id": "S2PAT05-T00",
                            "stop_conditions": ["未注册中文短语"],
                        }
                    ]
                }
            ]
        }
        errors, _metrics = self.validator.validate_roadmap_machine_gate(roadmap, {"G-DRIFT"})

        self.assertTrue(any("unknown stop code 未注册中文短语" in error for error in errors), errors)

    def test_free_text_stop_conditions_are_rejected(self) -> None:
        roadmap = {
            "workstreams": [
                {
                    "tasks": [
                        {
                            "task_id": "S2PAT05-T00",
                            "stop_conditions": "需要人工判断",
                        }
                    ]
                }
            ]
        }
        errors, _metrics = self.validator.validate_roadmap_machine_gate(roadmap, {"G-DRIFT"})

        self.assertTrue(any("stop_conditions must be a list" in error for error in errors), errors)

    def test_missing_dependency_is_rejected(self) -> None:
        roadmap = {
            "workstreams": [
                {
                    "tasks": [
                        {
                            "task_id": "S2PAT05-T01",
                            "dependencies": ["S2PAT05-T00"],
                        }
                    ]
                }
            ]
        }
        errors, _metrics = self.validator.validate_roadmap_machine_gate(roadmap, {"G-DRIFT"})

        self.assertTrue(any("references unknown task S2PAT05-T00" in error for error in errors), errors)

    def test_dependency_cycle_is_rejected(self) -> None:
        roadmap = {
            "workstreams": [
                {
                    "tasks": [
                        {
                            "task_id": "S2PAT05-T00",
                            "dependencies": ["S2PAT05-T01"],
                        },
                        {
                            "task_id": "S2PAT05-T01",
                            "dependencies": ["S2PAT05-T00"],
                        },
                    ]
                }
            ]
        }
        errors, _metrics = self.validator.validate_roadmap_machine_gate(roadmap, {"G-DRIFT"})

        self.assertTrue(any("task dependency graph contains a cycle" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()

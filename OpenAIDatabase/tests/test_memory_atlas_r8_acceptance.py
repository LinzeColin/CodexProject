from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/memory_atlas_r8_acceptance.py"
ATLASCTL = ROOT / "scripts/atlasctl.py"
HOME_BROWSER_GATE = ROOT / "apps/memory-atlas/scripts/validate_memory_atlas_v1_2_home_multiviewport.cjs"


def load_module():
    spec = importlib.util.spec_from_file_location("memory_atlas_r8_acceptance", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_atlasctl():
    scripts_dir = str(ATLASCTL.parent)
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location("atlasctl_r8_test", ATLASCTL)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class MemoryAtlasR8AcceptanceTests(unittest.TestCase):
    def test_history_replay_finds_exactly_the_five_r8_requirements(self) -> None:
        module = load_module()

        state = module.reconcile_requirement_history(ROOT)

        self.assertEqual(len(state), 58)
        self.assertEqual(
            {requirement_id for requirement_id, row in state.items() if row["status"] != "VERIFIED"},
            {"S03-AC05", "S04-AC04", "S10-AC04", "S14-AC02", "S14-AC05"},
        )

    def test_all_required_runtime_gates_promote_the_matrix_to_58_of_58(self) -> None:
        module = load_module()
        gates = [
            {"gate_id": gate_id, "status": "PASS", "command": ["validator", gate_id]}
            for gate_id in module.REQUIRED_R8_GATE_IDS
        ]

        summary = module.build_acceptance_summary(ROOT, gates, verified_commit="a" * 40)

        self.assertEqual(summary["status"], "PASS")
        self.assertEqual(summary["requirements"]["total"], 58)
        self.assertEqual(summary["requirements"]["verified"], 58)
        self.assertEqual(summary["requirements"]["remaining_non_verified"], [])
        self.assertEqual(len(summary["four_line_coverage"]), 4)
        self.assertTrue(all(line["status"] == "PASS" for line in summary["four_line_coverage"]))
        self.assertEqual(len(summary["stage_pass_gates"]), 14)
        self.assertTrue(all(stage["status"] == "VERIFIED" for stage in summary["stage_pass_gates"]))

    def test_missing_rendered_chinese_gate_keeps_final_acceptance_failed(self) -> None:
        module = load_module()
        gates = [
            {"gate_id": gate_id, "status": "PASS", "command": ["validator", gate_id]}
            for gate_id in module.REQUIRED_R8_GATE_IDS
            if gate_id != "rendered_chinese_ux"
        ]

        summary = module.build_acceptance_summary(ROOT, gates, verified_commit="b" * 40)

        self.assertEqual(summary["status"], "FAIL")
        self.assertIn("rendered_chinese_ux", summary["missing_gate_ids"])
        self.assertIn("S10-AC04", summary["requirements"]["remaining_non_verified"])
        self.assertEqual(
            next(stage for stage in summary["stage_pass_gates"] if stage["stage_id"] == "S10")["status"],
            "FAILED",
        )

    def test_atlasctl_final_audit_executes_every_r8_gate(self) -> None:
        module = load_module()
        atlasctl = load_atlasctl()

        plan = atlasctl.final_audit_gate_plan(ROOT)

        self.assertEqual(
            [gate["gate_id"] for gate in plan],
            list(module.REQUIRED_R8_GATE_IDS),
        )
        self.assertTrue(all(int(gate["timeout_seconds"]) > 0 for gate in plan))
        by_id = {gate["gate_id"]: gate for gate in plan}
        self.assertGreaterEqual(int(by_id["unit_tests"]["timeout_seconds"]), 600)
        self.assertGreaterEqual(int(by_id["stage7_privacy_accessibility"]["timeout_seconds"]), 600)
        self.assertNotIn("--publish-dir", by_id["report_contract_audit"]["command"])
        self.assertEqual(atlasctl.compact_tail(b"timeout output"), "timeout output")

    def test_rendered_chinese_gate_checks_human_copy_and_raw_manifest_pollution(self) -> None:
        source = HOME_BROWSER_GATE.read_text(encoding="utf-8")

        self.assertIn("assertRenderedChineseUx", source)
        self.assertIn('id: "raw_manifest_details"', source)
        self.assertIn("renderedChineseUx", source)

    def test_final_records_serialize_five_promotions_and_fourteen_stage_truths(self) -> None:
        module = load_module()
        gates = [
            {"gate_id": gate_id, "status": "PASS", "command": ["validator", gate_id]}
            for gate_id in module.REQUIRED_R8_GATE_IDS
        ]
        runtime_commit = "c" * 40
        summary = module.build_acceptance_summary(ROOT, gates, verified_commit=runtime_commit)
        records = module.build_final_records(
            ROOT,
            summary,
            generated_at="2026-07-11T00:00:00Z",
            runtime_commit=runtime_commit,
            delivery_context={
                "local_apps_verified": True,
                "cloudflare_live_verified": True,
                "single_push_pending": True,
            },
        )

        self.assertEqual(len(records["delta_rows"]), 5)
        self.assertTrue(all(row["after_status"] == "VERIFIED" for row in records["delta_rows"]))
        self.assertEqual(records["acceptance"]["requirements"]["verified"], 58)
        self.assertEqual(len(records["stage_ledger"]["stage_pass_gates"]), 14)
        self.assertNotIn("/Users/", json.dumps(records, ensure_ascii=False))

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            for relative_path in (module.BASE_MATRIX, *module.DELTA_PATHS):
                target = temp_root / relative_path
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / relative_path, target)
            outputs = module.write_final_records(temp_root, records)
            self.assertEqual(set(outputs), set(module.FINAL_RECORD_PATHS))
            self.assertTrue(all((temp_root / path).is_file() for path in outputs))
            audited = module.audit_final_records(temp_root, expected_runtime_commit=runtime_commit)
            self.assertEqual(audited["status"], "PASS")

            acceptance_path = temp_root / module.R8_ACCEPTANCE_PATH
            acceptance = json.loads(acceptance_path.read_text(encoding="utf-8"))
            acceptance["requirements"]["verified"] = 57
            acceptance_path.write_text(json.dumps(acceptance), encoding="utf-8")
            with self.assertRaises(module.AcceptanceHistoryError):
                module.audit_final_records(temp_root, expected_runtime_commit=runtime_commit)


if __name__ == "__main__":
    unittest.main()

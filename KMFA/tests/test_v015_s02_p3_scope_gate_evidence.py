from __future__ import annotations

import csv
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from KMFA.tools.build_v015_s02_p3_scope_gate import (
    DEFAULT_SOURCE_PACKAGE,
    _json_bytes,
    build_final_manifest,
    expected_core_outputs,
)
from KMFA.tools.check_v015_s02_p3_scope_gate import (
    MANIFEST_PATH,
    ValidationError,
    _canonical_content_hash,
    main,
    validate_v015_s02_p3_scope_gate,
)


class TestV015S02P3ScopeGateEvidence(unittest.TestCase):
    def test_builder_core_outputs_are_exact_repeatable_and_public_safe(self) -> None:
        first = expected_core_outputs(source_package=DEFAULT_SOURCE_PACKAGE)
        second = expected_core_outputs(source_package=DEFAULT_SOURCE_PACKAGE)
        self.assertEqual(first, second)
        self.assertEqual(
            {path.name for path in first},
            {
                "scope_priority_gate_public_safe.csv",
                "prohibited_action_hard_stops_public_safe.csv",
                "change_control_protocol_public_safe.json",
                "acceptance_matrix_public_safe.json",
                "scope_gate_zh.md",
            },
        )
        combined = b"\n".join(first.values())
        for token in (
            b"/Users/",
            b"/Volumes/",
            b"/private/",
            b"/tmp/",
            b"/home/",
            b"KMFA_MetaData",
        ):
            self.assertNotIn(token, combined)

        by_name = {path.name: payload for path, payload in first.items()}
        scope = list(
            csv.DictReader(
                io.StringIO(
                    by_name["scope_priority_gate_public_safe.csv"].decode("utf-8")
                )
            )
        )
        prohibitions = list(
            csv.DictReader(
                io.StringIO(
                    by_name[
                        "prohibited_action_hard_stops_public_safe.csv"
                    ].decode("utf-8")
                )
            )
        )
        protocol = json.loads(
            by_name["change_control_protocol_public_safe.json"].decode("utf-8")
        )
        self.assertEqual(len(scope), 103)
        self.assertEqual(len(prohibitions), 51)
        self.assertEqual(len(protocol["auditable_domains"]), 4)
        self.assertEqual(len(protocol["change_types"]), 5)
        self.assertFalse(protocol["runtime_or_ci_hook_implemented_in_s02_p3"])

    def test_final_manifest_rebuild_is_byte_exact_and_repeatable(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        first = build_final_manifest(
            generated_at=manifest["generated_at"],
            source_package=DEFAULT_SOURCE_PACKAGE,
        )
        second = build_final_manifest(
            generated_at=manifest["generated_at"],
            source_package=DEFAULT_SOURCE_PACKAGE,
        )
        self.assertEqual(first, second)
        self.assertEqual(MANIFEST_PATH.read_bytes(), _json_bytes(first))

    def test_strict_checker_rebuilds_core_and_final_manifest(self) -> None:
        result = validate_v015_s02_p3_scope_gate()
        self.assertEqual(result["phase_result"]["acceptance_status"], "PASSED")
        self.assertEqual(result["stage_state"]["execution_percentage"], 100)
        self.assertFalse(result["stage_state"]["stage_passed"])
        self.assertFalse(result["stage_state"]["stage_review_performed"])
        self.assertTrue(
            result["next_entry_gate"]["s02_stage_review_entry_allowed"]
        )
        self.assertFalse(result["next_entry_gate"]["s03_entry_allowed"])

    def test_skip_exact_rebuild_is_visibly_non_strict(self) -> None:
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = main(["--skip-exact-rebuild"])
        self.assertEqual(exit_code, 0)
        self.assertTrue(output.getvalue().startswith("NON_STRICT_PASS:"))

    def _assert_semantic_mutation_rejected(self, mutate) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        mutate(manifest)
        manifest["content_hash"] = _canonical_content_hash(manifest)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True)
                + "\n",
                encoding="utf-8",
            )
            with self.assertRaises(ValidationError):
                validate_v015_s02_p3_scope_gate(
                    path,
                    require_exact_rebuild=False,
                )

    def test_semantic_manifest_tampering_fails_even_after_content_rehash(self) -> None:
        cases = {
            "stage_false_pass": lambda value: value["stage_state"].update(
                stage_passed=True
            ),
            "review_falsely_performed": lambda value: value["stage_state"].update(
                stage_review_performed=True
            ),
            "s03_opened": lambda value: value["next_entry_gate"].update(
                s03_entry_allowed=True
            ),
            "runtime_hook_claim": lambda value: value[
                "change_control_accounting"
            ].update(runtime_or_ci_hook_implemented=True),
            "scope_drop": lambda value: value["scope_accounting"].update(
                scope_row_count=102
            ),
            "prohibition_drop": lambda value: value[
                "prohibition_accounting"
            ].update(prohibition_row_count=50),
            "downstream_action": lambda value: value["downstream_actions"].update(
                ui_implementation_performed=True
            ),
            "home_path_leak": lambda value: value.update(
                injected_evidence_ref="/home/private/evidence"
            ),
        }
        for name, mutate in cases.items():
            with self.subTest(name=name):
                self._assert_semantic_mutation_rejected(mutate)


if __name__ == "__main__":
    unittest.main()

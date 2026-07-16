from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest

from jsonschema import Draft202012Validator

from pfi_os.security.pfi_context_export import (
    CONTEXT_METADATA_FIELDS,
    CONTEXT_PAYLOAD_FIELDS,
    ContextExportError,
    PUBLIC_DISTRIBUTION_ROOTS,
    build_blocked_pfi_context_export,
    build_pfi_context_export,
    canonical_context_bytes,
    load_distribution_boundary_policy,
    validate_pfi_context_export,
    write_new_context_export,
)
from pfi_v02.stage5_advice_report_alpha import build_stage5_delivery_model


PFI_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PFI_ROOT.parent
POLICY_PATH = PFI_ROOT / "config/data_domains/stage11_distribution_boundaries.json"
SCHEMA_PATH = PFI_ROOT / "shared/context/pfi_context_v1.schema.json"
PUBLIC_SOURCE = PFI_ROOT / "web/cloudflare-public/public"
SCANNER = PFI_ROOT / "scripts/v025/scan_stage11_distribution_boundaries.py"
EXPORT_CLI = PFI_ROOT / "scripts/v025/pfi_context_export.py"


def blocked_context() -> dict[str, object]:
    return build_pfi_context_export(
        as_of="2026-07-16T00:00:00+10:00",
        source_or_read_model_hash="a" * 64,
        net_worth_state="blocked",
        investable_cash_state="blocked",
        cashflow_pressure="blocked",
        asset_allocation="blocked",
        risk_budget="blocked",
        investment_behavior_tags=("review_required",),
        consumption_pressure_summary="blocked",
        data_freshness="not_loaded",
    )


class Stage11DistributionBoundaryTest(unittest.TestCase):
    def test_policy_and_schema_define_the_exact_minimized_contract(self) -> None:
        policy = load_distribution_boundary_policy(POLICY_PATH)
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        expected = set(CONTEXT_METADATA_FIELDS + CONTEXT_PAYLOAD_FIELDS)

        self.assertEqual(tuple(policy["pfi_context"]["payload_fields"]), CONTEXT_PAYLOAD_FIELDS)
        self.assertEqual(tuple(policy["pfi_context"]["metadata_fields"]), CONTEXT_METADATA_FIELDS)
        self.assertEqual(set(schema["required"]), expected)
        self.assertEqual(set(schema["properties"]), expected)
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(policy["pfi_context"]["consumer"], "Alpha")
        self.assertNotIn("Ralpha", policy["pfi_context"].get("consumer", ""))
        Draft202012Validator.check_schema(schema)

    def test_context_is_state_only_read_only_and_schema_valid(self) -> None:
        context = blocked_context()
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        errors = list(Draft202012Validator(schema).iter_errors(context))

        self.assertEqual(errors, [])
        self.assertEqual(set(context), set(CONTEXT_METADATA_FIELDS + CONTEXT_PAYLOAD_FIELDS))
        self.assertEqual(context["consumer"], "Alpha")
        self.assertTrue(context["read_only"])
        self.assertFalse(context["writeback_allowed"])
        self.assertFalse(any(
            isinstance(context[field], (int, float)) and not isinstance(context[field], bool)
            for field in CONTEXT_PAYLOAD_FIELDS
        ))
        self.assertEqual(canonical_context_bytes(context), canonical_context_bytes(context))
        validate_pfi_context_export(context)

    def test_context_validation_fails_closed_on_drift(self) -> None:
        invalid_cases: list[dict[str, object]] = []
        extra = blocked_context()
        extra["financial_amount"] = "forbidden"
        invalid_cases.append(extra)
        numeric = blocked_context()
        numeric["net_worth_state"] = 1
        invalid_cases.append(numeric)
        naive_time = blocked_context()
        naive_time["as_of"] = "2026-07-16T00:00:00"
        invalid_cases.append(naive_time)
        writeback = blocked_context()
        writeback["writeback_allowed"] = True
        invalid_cases.append(writeback)
        consumer = blocked_context()
        consumer["consumer"] = "Ralpha"
        invalid_cases.append(consumer)

        for payload in invalid_cases:
            with self.subTest(fields=sorted(payload)):
                with self.assertRaises(ContextExportError):
                    validate_pfi_context_export(payload)

    def test_legacy_stage5_adapter_emits_only_blocked_state_context(self) -> None:
        context = build_stage5_delivery_model()["alpha_context_export"]
        legacy_fields = {
            "behavior_tags",
            "constraints",
            "investable_cash_aud",
            "net_worth_aud",
            "portfolio_allocation",
        }

        self.assertFalse(legacy_fields & set(context))
        self.assertEqual(context["schema_version"], "pfi_context.v1")
        self.assertEqual(context["consumer"], "Alpha")
        self.assertTrue(all(context[field] == "blocked" for field in (
            "net_worth_state",
            "investable_cash_state",
            "cashflow_pressure",
            "asset_allocation",
            "risk_budget",
            "consumption_pressure_summary",
        )))
        self.assertEqual(context["data_freshness"], "not_loaded")
        validate_pfi_context_export(context)

    def test_blocked_adapter_uses_inputs_only_for_provenance(self) -> None:
        first = build_blocked_pfi_context_export(
            as_of="2026-07-16T00:00:00+10:00",
            source_payload={"status": "blocked"},
            read_model_payload={"status": "not_loaded"},
        )
        second = build_blocked_pfi_context_export(
            as_of="2026-07-16T00:00:00+10:00",
            source_payload={"status": "not_loaded"},
            read_model_payload={"status": "not_loaded"},
        )

        self.assertNotEqual(first["source_or_read_model_hash"], second["source_or_read_model_hash"])
        self.assertEqual(
            {key: value for key, value in first.items() if key != "source_or_read_model_hash"},
            {key: value for key, value in second.items() if key != "source_or_read_model_hash"},
        )

    def test_secure_writer_is_private_path_free_and_no_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            private_dir = Path(temporary) / "alpha-context"
            output = private_dir / "context.json"
            receipt = write_new_context_export(blocked_context(), output)

            self.assertEqual(stat.S_IMODE(private_dir.stat().st_mode), 0o700)
            self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o600)
            self.assertFalse(receipt["contains_path"])
            self.assertFalse(receipt["contains_financial_values"])
            self.assertNotIn(str(output), json.dumps(receipt, sort_keys=True))
            with self.assertRaises(ContextExportError):
                write_new_context_export(blocked_context(), output)

    def test_secure_writer_rejects_preexisting_public_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            public_dir = Path(temporary) / "public"
            public_dir.mkdir(mode=0o755)
            os.chmod(public_dir, 0o755)
            with self.assertRaises(ContextExportError):
                write_new_context_export(blocked_context(), public_dir / "context.json")

    def test_secure_writer_rejects_public_distribution_even_before_file_creation(self) -> None:
        output = PUBLIC_DISTRIBUTION_ROOTS[0] / "forbidden-context.json"
        self.assertFalse(output.exists())
        with self.assertRaises(ContextExportError):
            write_new_context_export(blocked_context(), output)
        self.assertFalse(output.exists())

    def test_context_export_cli_accepts_exact_state_input_and_rejects_extra_field(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            input_path = root / "input.json"
            output_dir = root / "private"
            output_path = output_dir / "context.json"
            context = blocked_context()
            cli_input = {
                key: context[key]
                for key in ("as_of", "source_or_read_model_hash", *CONTEXT_PAYLOAD_FIELDS)
            }
            input_path.write_text(json.dumps(cli_input), encoding="utf-8")
            env = {**os.environ, "PYTHONPATH": str(PFI_ROOT / "src")}
            accepted = subprocess.run(
                [sys.executable, str(EXPORT_CLI), "--input", str(input_path), "--output", str(output_path)],
                cwd=REPO_ROOT,
                env=env,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(accepted.returncode, 0, accepted.stderr)
            receipt = json.loads(accepted.stdout)
            self.assertFalse(receipt["contains_path"])
            validate_pfi_context_export(json.loads(output_path.read_text(encoding="utf-8")))

            rejected_input = root / "rejected.json"
            cli_input["financial_amount"] = "forbidden"
            rejected_input.write_text(json.dumps(cli_input), encoding="utf-8")
            rejected = subprocess.run(
                [
                    sys.executable,
                    str(EXPORT_CLI),
                    "--input",
                    str(rejected_input),
                    "--output",
                    str(root / "rejected-output.json"),
                ],
                cwd=REPO_ROOT,
                env=env,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(rejected.returncode, 2)
            self.assertFalse((root / "rejected-output.json").exists())
            self.assertFalse(json.loads(rejected.stderr)["contains_path"])

    def test_public_build_and_both_distribution_scanners_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "dist"
            build = subprocess.run(
                [
                    "node",
                    str(REPO_ROOT / "scripts/cloudflare/build_static_surface.mjs"),
                    "--source",
                    str(PUBLIC_SOURCE),
                    "--output",
                    str(output),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(build.returncode, 0, build.stderr)
            generic_scan = subprocess.run(
                [sys.executable, str(REPO_ROOT / "scripts/cloudflare/scan_public_dist.py"), "--path", str(output)],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(generic_scan.returncode, 0, generic_scan.stdout + generic_scan.stderr)
            boundary_scan = subprocess.run(
                [sys.executable, str(SCANNER), "--public-dist", str(output)],
                cwd=REPO_ROOT,
                env={**os.environ, "PYTHONPATH": str(PFI_ROOT / "src")},
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(boundary_scan.returncode, 0, boundary_scan.stderr)
            self.assertEqual(json.loads(boundary_scan.stdout)["finding_count"], 0)

    def test_boundary_scanner_rejects_script_or_context_leakage(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            public_copy = Path(temporary) / "public"
            shutil.copytree(PUBLIC_SOURCE, public_copy)
            (public_copy / "runtime.js").write_text("const net_worth_state = 'ready';\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCANNER), "--public-source", str(public_copy)],
                cwd=REPO_ROOT,
                env={**os.environ, "PYTHONPATH": str(PFI_ROOT / "src")},
                check=False,
                capture_output=True,
                text=True,
            )
            payload = json.loads(result.stdout)

            self.assertEqual(result.returncode, 1)
            self.assertEqual(payload["status"], "fail")
            self.assertGreaterEqual(payload["finding_count"], 2)
            self.assertGreaterEqual(payload["public_context_fields_exposed"], 1)
            finding_ids = {item["finding_id"] for item in payload["findings"]}
            self.assertIn("forbidden_public_file_type", finding_ids)
            self.assertIn("pfi_context_field_exposed", finding_ids)


if __name__ == "__main__":
    unittest.main()

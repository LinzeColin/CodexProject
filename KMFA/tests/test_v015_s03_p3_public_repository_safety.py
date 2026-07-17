import copy
import hashlib
import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from KMFA.tools import build_v015_s03_p3_public_repository_safety as builder_module
from KMFA.tools import v015_s03_p3_public_repository_safety as safety_module
from KMFA.tools.v015_s03_p3_public_repository_safety import (
    MAX_SCANNED_FILE_BYTES,
    PUBLIC_ENVELOPE_FIELDS,
    SafetyError,
    audit_json_or_jsonl_bytes,
    audit_public_metadata_bytes,
    ensure_synthetic_private_dual_plane,
    read_repository_file,
    scan_candidate,
    scan_payload_for_secrets,
    scan_repository,
    validate_public_metadata_envelope,
    verify_dual_plane,
    verify_gitignore_contract,
    write_repository_file,
)


class PublicRepositorySafetyTests(unittest.TestCase):
    def test_gitignore_contract_blocks_every_sensitive_probe(self) -> None:
        result = verify_gitignore_contract()
        self.assertTrue(result["pass"])
        self.assertEqual(result["blocked_count"], result["probe_count"])
        self.assertEqual(result["missed_count"], 0)
        self.assertEqual(result["wrongly_ignored_public_count"], 0)

    def test_secret_scanner_blocks_runtime_samples_without_tracking_them(self) -> None:
        known_token_fixture = b"s" + b"k-" + b"RUNTIMEONLY" * 4
        assignment_fixture = b"api" + b"_key='" + b"live-" + b"X" * 32 + b"'"
        begin = b"-----BEGIN " + b"PRIVATE KEY-----\n"
        end = b"\n-----END " + b"PRIVATE KEY-----"
        key_block_fixture = begin + (b"QUJDREVGR0hJSktMTU5PUFFSU1RVVldYWVo=" * 3) + end
        for payload in (known_token_fixture, assignment_fixture, key_block_fixture):
            self.assertTrue(scan_payload_for_secrets("runtime-fixture", payload))
        self.assertFalse(
            scan_payload_for_secrets("placeholder", b"api" + b"_key='example-placeholder'")
        )

    def test_secret_scanner_blocks_common_config_assignments_and_ignores_placeholders(self) -> None:
        live_value = b"live-" + b"R7x9" * 6
        assignments = (
            b'{"' + b"api" + b'_key":"' + live_value + b'"}',
            b"'" + b"to" + b"ken': '" + live_value + b"'",
            b"pass" + b"word: " + live_value,
            b"SEC" + b"RET=" + live_value,
            b"private" + b"_key = '" + live_value + b"'",
            b"access" + b"-token: " + live_value,
        )
        for payload in assignments:
            self.assertTrue(scan_payload_for_secrets("runtime-fixture", payload), msg=payload)
        placeholders = (
            b'{"' + b"api" + b'_key":"example-placeholder"}',
            b"to" + b"ken=${TOKEN}",
            b"pass" + b"word: changeme",
            b"private" + b"_key='not-a-secret'",
            b"to" + b'ken = os.getenv("TOKEN")',
            b"api" + b"_key: your-api-key-here",
        )
        for payload in placeholders:
            self.assertFalse(scan_payload_for_secrets("placeholder", payload), msg=payload)
        self.assertFalse(scan_payload_for_secrets("config.py", b"to" + b"ken = token_value"))
        placeholder_fixture = b"s" + b"k-" + b"example-placeholder-1234567890"
        self.assertFalse(scan_payload_for_secrets("placeholder", placeholder_fixture))

    def test_secret_scanner_blocks_credential_alias_bearer_short_and_low_entropy_values(self) -> None:
        key_name_a = b"cred" + b"ential"
        key_name_b = key_name_a + b"s"
        key_name_c = b"pass" + b"word"
        key_name_d = b"api" + b"_key"
        header_name = b"Author" + b"ization"
        blocked = (
            key_name_a + b'="live-ABCD1234EFGH5678"',
            key_name_b + b'="live-ABCD1234EFGH5678"',
            header_name + b": Bearer live-ABCD1234EFGH5678",
            key_name_c + b'="Ab1!x"',
            key_name_c + b'="abcabcabcabc"',
            key_name_d + b'="<live-ABCD1234EFGH5678"',
        )
        for payload in blocked:
            self.assertTrue(scan_payload_for_secrets("KMFA/config.yaml", payload), msg=payload)
        strict_placeholders = (
            key_name_a + b'="${SERVICE_CREDENTIAL}"',
            key_name_b + b'="<SERVICE_CREDENTIAL>"',
            header_name + b": Bearer ${ACCESS_TOKEN}",
            key_name_c + b'="example-placeholder"',
            key_name_d + b'="ENV::SERVICE_API_KEY"',
        )
        for payload in strict_placeholders:
            self.assertFalse(scan_payload_for_secrets("KMFA/config.yaml", payload), msg=payload)

    def test_path_alias_oversize_and_binary_text_fail_closed(self) -> None:
        denied_paths = (
            "KMFA/raw_data/source.csv",
            "KMFA/vendor/runtime.so",
            "KMFA/logs/runtime.txt",
            "KMFA/reports/detail/full.csv",
            "KMFA/source.csv",
            "KMFA/foo.bin",
            "KMFA/foo.dat",
            "KMFA/inbox/source.csv",
            "KMFA/operations/inbox/source.csv",
            "KMFA/inbox/90_用户原始上传数据_仅本地私有_禁止提交GitHub/source.csv",
            "KMFA/metadata/mgmt-monthly-report-skill/logs/202607_public_safe_run_log.jsonl",
            "KMFA/.DS_Store",
            "KMFA/.coverage",
            "KMFA/tools/.pytest_cache/state.json",
            "KMFA/tools/.mypy_cache/state.json",
            "KMFA/tools/.ruff_cache/state.json",
            "KMFA/htmlcov/index.html",
            "KMFA/metadata/temporary.bak",
            "KMFA/metadata/merge.orig",
            "KMFA/metadata/conflict.rej",
            "KMFA/tools/module.py~",
        )
        for path in denied_paths:
            self.assertTrue(scan_candidate(path, b"x"), msg=path)
        self.assertTrue(scan_candidate("KMFA/metadata/link.json", b"x", mode=stat.S_IFLNK | 0o777))
        self.assertTrue(scan_candidate("KMFA/metadata/hard.json", b"x", mode=stat.S_IFREG | 0o600, nlink=2))
        self.assertTrue(scan_candidate("KMFA/metadata/submodule", b"", mode=0o160000))
        self.assertTrue(scan_candidate("KMFA/metadata/value.json", b"x\0y"))
        self.assertTrue(scan_candidate("KMFA/metadata/value.txt", b"x" * (MAX_SCANNED_FILE_BYTES + 1)))

    def test_public_metadata_format_gate_blocks_structured_aliases_and_unknown_binary(self) -> None:
        cases = {
            "KMFA/metadata/baseline/raw_export.csv": (
                b"client_name,total_amount,digest,source_filename\nSensitive Party,100,deadbeef,ledger.xlsx\n",
                {"person_customer_or_project_detail", "money_account_or_tax_detail", "credential_or_private_hash", "raw_or_source_filename"},
            ),
            "KMFA/metadata/baseline/raw_export.yaml": (
                "客户名称: Sensitive Party\n金额: 100\ndigest: deadbeef\n源文件名: ledger.xlsx\n".encode(),
                {"person_customer_or_project_detail", "money_account_or_tax_detail", "credential_or_private_hash", "raw_or_source_filename"},
            ),
            "KMFA/metadata/baseline/raw_export.toml": (
                b'client = "Sensitive Party"\ntotal = 100\ndigest = "deadbeef"\nsource = "ledger.xlsx"\n',
                {"person_customer_or_project_detail", "money_account_or_tax_detail", "credential_or_private_hash", "raw_or_source_filename"},
            ),
            "KMFA/metadata/baseline/raw_export.json": (
                b'{"client":"Sensitive Party","total":100,"digest":"deadbeef","source":"ledger.xlsx"}',
                {"person_customer_or_project_detail", "money_account_or_tax_detail", "credential_or_private_hash", "raw_or_source_filename"},
            ),
        }
        for path, (payload, expected_categories) in cases.items():
            categories = {finding.category for finding in scan_candidate(path, payload)}
            self.assertTrue(expected_categories <= categories, msg=(path, categories))
        for suffix in ("bin", "dat", "blob"):
            path = f"KMFA/metadata/baseline/private_payload.{suffix}"
            categories = {finding.category for finding in scan_candidate(path, b"\x00\x01private-business-payload")}
            self.assertIn("metadata_format", categories, msg=path)

        current_evidence = (
            "KMFA/stage_artifacts/V015_S03_P3_PUBLIC_REPOSITORY_SAFETY/machine/leak.json"
        )
        categories = {
            finding.category
            for finding in scan_candidate(
                current_evidence,
                b'{"customer_name":"Real Party","amount_yuan":100}',
            )
        }
        self.assertIn("person_customer_or_project_detail", categories)
        self.assertIn("money_account_or_tax_detail", categories)

    def test_public_metadata_parser_fails_closed_on_invalid_structured_payloads(self) -> None:
        cases = (
            ("KMFA/metadata/baseline/broken.json", b'{"status":'),
            ("KMFA/metadata/baseline/broken.jsonl", b'{"status":"PASS"}\nnot-json\n'),
            ("KMFA/metadata/baseline/broken.csv", b"a,b\n1\n"),
            ("KMFA/metadata/baseline/broken.yaml", b"status:\x00 PASS\n"),
        )
        for path, payload in cases:
            self.assertTrue(audit_public_metadata_bytes(path, payload), msg=path)

    def test_structured_audit_blocks_changed_scope_bypasses_and_yaml_edge_forms(self) -> None:
        cases = (
            ("KMFA/tools/fixtures/source.json", b'{"source_filename":"ledger.xlsx"}'),
            ("KMFA/tests/fixtures/report.json", b'{"customer_name":"Real Party"}'),
            ("KMFA/docs/source.csv", b"amount_yuan\n100\n"),
            ("KMFA/tools/fixtures/flow.yaml", b"record: {customer_name: Real Party}\n"),
            ("KMFA/tools/fixtures/literal.yaml", b"customer_name: |\n  Real Party\n"),
            ("KMFA/tools/fixtures/plain.txt", b"source_filename: ledger.xlsx\n"),
        )
        for path, payload in cases:
            self.assertTrue(audit_public_metadata_bytes(path, payload), msg=path)

    def test_repository_io_rejects_symlink_ancestors_for_reads_and_writes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="kmfa-s03p3-repo-") as temp_dir:
            repo = Path(temp_dir) / "repo"
            outside = Path(temp_dir) / "outside"
            (repo / "KMFA" / "safe").parent.mkdir(parents=True)
            outside.mkdir()
            (outside / "secret.json").write_bytes(b'{"customer_name":"Private Party"}')
            (repo / "KMFA" / "safe").symlink_to(outside, target_is_directory=True)
            with patch.object(safety_module, "REPO_ROOT", repo):
                with self.assertRaises(SafetyError):
                    read_repository_file("KMFA/safe/secret.json")
                with self.assertRaises(SafetyError):
                    write_repository_file("KMFA/safe/output.json", b"{}")
            self.assertFalse((outside / "output.json").exists())

    def test_public_identity_fields_require_role_or_private_registry_refs(self) -> None:
        blocked = (
            ("KMFA/metadata/example.json", b'{"sender_name":"Real Person"}'),
            ("KMFA/metadata/example.yaml", b"notification_owner_label: Real Person\n"),
            ("KMFA/metadata/example.json", b'{"known_no_record_names":["Real Person"]}'),
        )
        for path, payload in blocked:
            categories = {finding.category for finding in audit_public_metadata_bytes(path, payload)}
            self.assertIn("person_customer_or_project_detail", categories, msg=path)

        allowed = (
            ("KMFA/metadata/example.json", b'{"sender_name":"ROLE::CASH_DATA_OWNER"}'),
            ("KMFA/metadata/example.yaml", b"notify_target_label: TARGET::OWNER_PERSONAL_PRIVATE\n"),
            (
                "KMFA/metadata/example.json",
                b'{"known_no_record_names":["PRIVATE-REGISTRY::ATTENDANCE_EXEMPTIONS"]}',
            ),
        )
        for path, payload in allowed:
            self.assertEqual(audit_public_metadata_bytes(path, payload), [], msg=path)

    def test_public_metadata_envelope_rejects_unknown_or_sensitive_fields(self) -> None:
        with tempfile.TemporaryDirectory(prefix="kmfa-s03p3-") as temp_dir:
            private, key, public, _ = ensure_synthetic_private_dual_plane(
                Path(temp_dir) / "dual-plane",
                run_id="1" * 32,
                allow_external_test_root=True,
            )
            self.assertEqual(set(public), set(PUBLIC_ENVELOPE_FIELDS))
            tracked_ref = "KMFA/metadata/protocol/directory_manifest.json"
            public["policy_refs"] = [tracked_ref]
            public["evidence_refs"] = [tracked_ref]
            validate_public_metadata_envelope(public)

            unknown = copy.deepcopy(public)
            unknown["source_filename"] = "ledger.xlsx"
            with self.assertRaises(SafetyError):
                validate_public_metadata_envelope(unknown)

            absolute = copy.deepcopy(public)
            absolute["evidence_refs"] = ["/Users/example/private.json"]
            with self.assertRaises(SafetyError):
                validate_public_metadata_envelope(absolute)

            bad_digest = copy.deepcopy(public)
            bad_digest["public_artifact_digests"] = [
                {"artifact_ref": "KMFA/metadata/protocol/example.json", "sha256": "sha256:1234"}
            ]
            with self.assertRaises(SafetyError):
                validate_public_metadata_envelope(bad_digest)

            artifact_ref = "KMFA/metadata/protocol/directory_manifest.json"
            artifact = Path(__file__).resolve().parents[2] / artifact_ref
            valid_digest = copy.deepcopy(public)
            valid_digest["public_artifact_digests"] = [
                {
                    "artifact_ref": artifact_ref,
                    "sha256": "sha256:" + hashlib.sha256(artifact.read_bytes()).hexdigest(),
                }
            ]
            validate_public_metadata_envelope(valid_digest)

            mismatched_digest = copy.deepcopy(valid_digest)
            mismatched_digest["public_artifact_digests"][0]["sha256"] = "sha256:" + "0" * 64
            with self.assertRaises(SafetyError):
                validate_public_metadata_envelope(mismatched_digest)

            missing_digest_ref = copy.deepcopy(valid_digest)
            missing_digest_ref["public_artifact_digests"][0]["artifact_ref"] = (
                "KMFA/metadata/protocol/definitely_missing_public_artifact.json"
            )
            with self.assertRaises(SafetyError):
                validate_public_metadata_envelope(missing_digest_ref)

            missing_general_ref = copy.deepcopy(public)
            missing_general_ref["evidence_refs"] = [
                "KMFA/metadata/protocol/definitely_missing_public_artifact.json"
            ]
            with self.assertRaises(SafetyError):
                validate_public_metadata_envelope(missing_general_ref)

            _, _, original_projection, _ = ensure_synthetic_private_dual_plane(
                Path(temp_dir) / "dual-plane",
                run_id="1" * 32,
                allow_external_test_root=True,
            )
            tampered = copy.deepcopy(original_projection)
            tampered["opaque_tokens"][0]["token"] = "hmac-sha256:" + "0" * 64
            with self.assertRaises(SafetyError):
                verify_dual_plane(private, key, tampered)

    def test_public_refs_reject_traversal_backslashes_and_noncanonical_paths(self) -> None:
        with tempfile.TemporaryDirectory(prefix="kmfa-s03p3-") as temp_dir:
            _, _, public, _ = ensure_synthetic_private_dual_plane(
                Path(temp_dir) / "dual-plane",
                run_id="2" * 32,
                allow_external_test_root=True,
            )
            public["policy_refs"] = ["KMFA/metadata/protocol/directory_manifest.json"]
            invalid_refs = (
                "KMFA/metadata/protocol/../private.json",
                "KMFA/metadata/./protocol/public.json",
                "KMFA/metadata//protocol/public.json",
                "KMFA\\metadata\\protocol\\public.json",
                "KMFA/metadata/protocol/public.json/",
            )
            for invalid_ref in invalid_refs:
                invalid = copy.deepcopy(public)
                invalid["evidence_refs"] = [invalid_ref]
                with self.assertRaises(SafetyError, msg=invalid_ref):
                    validate_public_metadata_envelope(invalid)

    def test_structured_audit_detects_nested_sensitive_details(self) -> None:
        payload = (
            b'{"nested":{"source_filename":"ledger.xlsx","customer_name":"alpha",'
            b'"amount_yuan":12,"raw_sha256":"deadbeef","path":"/Users/example/raw",'
            b'"windows_path":"C:\\\\private\\\\raw"}}'
        )
        categories = {finding.category for finding in audit_json_or_jsonl_bytes("sample.json", payload)}
        self.assertEqual(
            categories,
            {
                "absolute_local_path",
                "credential_or_private_hash",
                "money_account_or_tax_detail",
                "person_customer_or_project_detail",
                "raw_or_source_filename",
            },
        )

    def test_public_artifact_hash_binding_is_allowed_only_for_exact_tracked_blob(self) -> None:
        artifact_ref = "KMFA/metadata/protocol/directory_manifest.json"
        artifact = Path(__file__).resolve().parents[2] / artifact_ref
        digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
        safe = (
            '{"artifacts":[{"target_path":"' + artifact_ref + '","sha256":"' + digest + '"}],'
            '"validation_subject_sha256":"sha256:' + "1" * 64 + '",'
            '"source_snapshot_hash":"sha256:' + "2" * 64 + '",'
            '"raw_bytes_streamed_for_hash":0,"sheet_ref":"SHEET-PUB-V2-001"}'
        ).encode()
        self.assertEqual(audit_json_or_jsonl_bytes("safe.json", safe), [])

        mismatched = safe.replace(digest.encode(), b"0" * 64)
        categories = {
            finding.category for finding in audit_json_or_jsonl_bytes("mismatched.json", mismatched)
        }
        self.assertIn("public_artifact_hash_binding", categories)

        private_source_hash = b'{"source_hash":"sha256:' + b"3" * 64 + b'"}'
        categories = {
            finding.category
            for finding in audit_json_or_jsonl_bytes("private.json", private_source_hash)
        }
        self.assertIn("credential_or_private_hash", categories)

    def test_dual_plane_rebuild_modes_and_declared_attack_model(self) -> None:
        with tempfile.TemporaryDirectory(prefix="kmfa-s03p3-") as temp_dir:
            root = Path(temp_dir) / "dual-plane"
            private, key, public, verification = ensure_synthetic_private_dual_plane(
                root,
                run_id="a" * 32,
                allow_external_test_root=True,
            )
            self.assertEqual(private["run_id"], public["run_id"])
            self.assertEqual(private["raw_root_access_count"], 0)
            self.assertTrue(verification["exact_private_to_public_rebuild"])
            self.assertTrue(verification["declared_attack_model_pass"])
            self.assertFalse(verification["information_theoretic_non_reconstruction_claimed"])
            self.assertEqual(stat.S_IMODE(os.lstat(root).st_mode), 0o700)
            self.assertEqual(stat.S_IMODE(os.lstat(root / "dual_plane_hmac.key").st_mode), 0o600)
            self.assertEqual(
                stat.S_IMODE(os.lstat(root / "synthetic_private_dual_plane_receipt.json").st_mode),
                0o600,
            )
            _, _, public_again, verification_again = ensure_synthetic_private_dual_plane(
                root,
                run_id="a" * 32,
                allow_external_test_root=True,
            )
            self.assertEqual(public, public_again)
            self.assertEqual(verification, verification_again)
            with self.assertRaises(SafetyError):
                ensure_synthetic_private_dual_plane(
                    root,
                    run_id="b" * 32,
                    allow_external_test_root=True,
                )

    def test_full_public_projection_binds_key_swap_that_summary_cannot_distinguish(self) -> None:
        with tempfile.TemporaryDirectory(prefix="kmfa-s03p3-") as temp_dir:
            _, key_a, projection_a, _ = ensure_synthetic_private_dual_plane(
                Path(temp_dir) / "plane-a",
                run_id="c" * 32,
                allow_external_test_root=True,
            )
            _, key_b, projection_b, _ = ensure_synthetic_private_dual_plane(
                Path(temp_dir) / "plane-b",
                run_id="c" * 32,
                allow_external_test_root=True,
            )
            self.assertNotEqual(key_a, key_b)
            self.assertNotEqual(projection_a["opaque_tokens"], projection_b["opaque_tokens"])
            with patch.object(safety_module, "validate_public_metadata_envelope"):
                self.assertEqual(
                    builder_module._public_projection_summary(projection_a),
                    builder_module._public_projection_summary(projection_b),
                )

    def test_current_head_index_and_worktree_have_no_path_or_secret_findings(self) -> None:
        for scope in ("head", "index", "worktree"):
            scanned, findings = scan_repository(scope=scope)
            self.assertGreater(scanned, 5000)
            self.assertEqual(findings, [], msg=f"{scope}: {findings[:5]}")


if __name__ == "__main__":
    unittest.main()

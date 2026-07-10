from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = REPO_ROOT / "scripts"
CHATGPT_SYNC = SCRIPTS_ROOT / "sync_chatgpt_memory_data.py"
CODEX_SYNC = SCRIPTS_ROOT / "sync_codex_memory_data.py"
FUTURE_AGENT_SYNC = SCRIPTS_ROOT / "sync_future_agent_data.py"
ATLASCTL = SCRIPTS_ROOT / "atlasctl.py"
REGISTRY = REPO_ROOT / "机器治理" / "同步与备份" / "sync_source_registry.json"
MAX_PUBLIC_RAW_FILE_BYTES = 40 * 1024 * 1024
SECRET_VALUE = "correct-" + "horse-battery"


def credential_fixture() -> str:
    return "pass" + "word=" + SECRET_VALUE


def load_script_module(filename: str, module_name: str):
    path = SCRIPTS_ROOT / filename
    if not path.is_file():
        raise AssertionError(f"required script does not exist: {path}")
    sys.path.insert(0, str(SCRIPTS_ROOT))
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run_json(command: list[str], *, expect_success: bool = True) -> tuple[dict, subprocess.CompletedProcess[str]]:
    result = subprocess.run(command, cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    if expect_success and result.returncode != 0:
        raise AssertionError(
            f"command failed: {command}\nstdout={result.stdout}\nstderr={result.stderr}"
        )
    if not expect_success and result.returncode == 0:
        raise AssertionError(f"command unexpectedly passed: {command}\nstdout={result.stdout}")
    start = result.stdout.find("{")
    if start < 0:
        raise AssertionError(
            f"command did not emit JSON: {command}\nstdout={result.stdout}\nstderr={result.stderr}"
        )
    return json.loads(result.stdout[start:]), result


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def write_chatgpt_export(path: Path) -> None:
    payload = [
        {
            "id": "conv_r7",
            "title": "Owner owner@example.com at /Users/alice/private/plan.md",
            "create_time": 1760000000,
            "update_time": 1760000060,
            "mapping": {
                "root": {
                    "id": "root",
                    "message": {
                        "id": "msg_user",
                        "author": {"role": "user"},
                        "create_time": 1760000001,
                        "content": {
                            "content_type": "text",
                            "parts": [
                                f"Call +61 412 345 678; {credential_fixture()}; keep the report text."
                            ],
                        },
                    },
                }
            },
        }
    ]
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def write_codex_session(codex_home: Path) -> tuple[Path, list[dict]]:
    session_id = "01999999-aaaa-bbbb-cccc-777777777777"
    rows = [
        {
            "type": "session_meta",
            "timestamp": "2026-07-11T00:00:00Z",
            "payload": {
                "id": session_id,
                "cwd": "/Users/alice/private/CodexProject",
                "originator": "codex_cli",
            },
        },
        {
            "type": "response_item",
            "timestamp": "2026-07-11T00:01:00Z",
            "payload": {
                "type": "message",
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": f"Use {credential_fixture()} and read /Users/alice/private/input.txt",
                    }
                ],
            },
        },
        {
            "type": "response_item",
            "timestamp": "2026-07-11T00:02:00Z",
            "payload": {
                "type": "function_call_output",
                "call_id": "call_r7",
                "output": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAAB",
            },
        },
        {
            "type": "event_msg",
            "timestamp": "2026-07-11T00:03:00Z",
            "payload": {"type": "agent_message", "message": "ordinary complete tool result"},
        },
    ]
    write_jsonl(codex_home / "session_index.jsonl", [{"id": session_id, "thread_name": "R7 public raw"}])
    source = codex_home / "sessions" / "2026" / "07" / "11" / "session.jsonl"
    write_jsonl(source, rows)
    return source, rows


class PublicRawSanitizerTests(unittest.TestCase):
    def load_sanitizer(self, suffix: str):
        return load_script_module("public_raw_sanitizer.py", f"public_raw_sanitizer_r7_{suffix}")

    def test_binary_marker_has_exact_shape_hash_and_utf8_byte_count(self) -> None:
        sanitizer = self.load_sanitizer("marker")
        value = "data:image/png;base64,5L2g5aW9"
        expected_sha = hashlib.sha256(value.encode("utf-8")).hexdigest()

        self.assertEqual(sanitizer.MAX_PUBLIC_RAW_FILE_BYTES, 40 * 1024 * 1024)
        self.assertEqual(sanitizer.BINARY_STRING_MIN_BYTES, 256 * 1024)
        self.assertEqual(
            sanitizer.binary_omission_marker(value),
            f"[REDACTED_BINARY sha256={expected_sha} bytes={len(value.encode('utf-8'))} "
            "reason=non_text_binary_not_transcript]",
        )

    def test_binary_detection_is_conservative_for_data_urls_and_long_text(self) -> None:
        sanitizer = self.load_sanitizer("detection")
        data_url = "data:application/octet-stream;base64,AA=="
        short_binary = base64.b64encode(bytes(range(256))).decode("ascii")
        binary_bytes = bytes(range(256)) * ((sanitizer.BINARY_STRING_MIN_BYTES // 256) + 1)
        long_binary = base64.b64encode(binary_bytes).decode("ascii")
        long_text = "This is an ordinary transcript sentence with spaces. " * 6000
        natural_letters = ("naturaltext" * sanitizer.BINARY_STRING_MIN_BYTES)[
            : sanitizer.BINARY_STRING_MIN_BYTES
        ]

        self.assertTrue(sanitizer.is_non_text_binary(data_url))
        self.assertTrue(sanitizer.is_non_text_binary(long_binary))
        self.assertFalse(sanitizer.is_non_text_binary("data:text/plain,ordinary%20text"))
        self.assertFalse(sanitizer.is_non_text_binary(short_binary))
        self.assertGreaterEqual(len(long_text.encode("utf-8")), sanitizer.BINARY_STRING_MIN_BYTES)
        self.assertFalse(sanitizer.is_non_text_binary(long_text))
        self.assertFalse(sanitizer.is_non_text_binary(natural_letters))

    def test_recursive_redaction_preserves_json_types_and_sums_nested_counts(self) -> None:
        sanitizer = self.load_sanitizer("recursive")
        value = {
            "scalars": [True, False, 7, 2.5, None],
            "message": f"{credential_fixture()} owner@example.com +61 412 345 678",
            "nested": [
                "/Users/alice/private/report.md",
                {"email": "second@example.com", "path": "/home/bob/private/input.txt"},
            ],
        }

        sanitized, counts = sanitizer.sanitize_public_value(value)
        repeated, repeated_counts = sanitizer.sanitize_public_value(value)
        serialized = json.dumps(sanitized, ensure_ascii=False, sort_keys=True)

        self.assertEqual(sanitized["scalars"], [True, False, 7, 2.5, None])
        self.assertEqual(list(sanitized), list(value))
        self.assertEqual(sanitized, repeated)
        self.assertEqual(counts, repeated_counts)
        for sensitive in (
            SECRET_VALUE,
            "owner@example.com",
            "second@example.com",
            "+61 412 345 678",
            "/Users/alice/private/report.md",
            "/home/bob/private/input.txt",
        ):
            self.assertNotIn(sensitive, serialized)
        self.assertEqual(
            counts,
            {
                "credential_passwords": 1,
                "email": 2,
                "local_absolute_path": 2,
                "phone": 1,
            },
        )

    def test_structured_hash_uuid_timestamp_and_relative_ref_are_not_phone_redacted(self) -> None:
        sanitizer = self.load_sanitizer("structured")
        values = [
            "a" * 10 + "123456789012" + "b" * 42,
            "019f4aea-fcab-7dd0-ad1a-1ce2637af2b8",
            "2026-07-11T16:52:07Z",
            "data/public_raw/codex/sessions/019f4aea-fcab-7dd0-ad1a-1ce2637af2b8."
            + "a" * 12
            + ".part-0001.jsonl",
        ]

        sanitized, counts = sanitizer.sanitize_public_value(values)

        self.assertEqual(sanitized, values)
        self.assertEqual(counts, {})

    def test_recursive_redaction_sanitizes_sensitive_mapping_keys_without_data_loss(self) -> None:
        sanitizer = self.load_sanitizer("mapping_keys")
        sensitive_key = "/Users/alice/private/2026-07-11/input.txt"
        value = {
            sensitive_key: "first",
            "[REDACTED_LOCAL_PATH]": "second",
            "ordinary": {"Call +61 412 345 678": "third"},
        }

        sanitized, counts = sanitizer.sanitize_public_value(value)
        repeated, repeated_counts = sanitizer.sanitize_public_value(sanitized)
        serialized = json.dumps(sanitized, ensure_ascii=False, sort_keys=True)

        self.assertEqual(len(sanitized), 3)
        self.assertCountEqual(
            list(sanitized.values()),
            [{"Call [REDACTED_PHONE]": "third"}, "first", "second"],
        )
        self.assertNotIn(sensitive_key, serialized)
        self.assertNotIn("+61 412 345 678", serialized)
        self.assertEqual(counts, {"local_absolute_path": 1, "phone": 2})
        collision_keys = [key for key in sanitized if "__redacted_key_" in key]
        self.assertEqual(len(collision_keys), 1)
        self.assertRegex(collision_keys[0], r"__redacted_key_[a-p]{12}$")
        self.assertEqual(repeated, sanitized)
        self.assertEqual(repeated_counts, {})

    def test_binary_replacement_counts_each_nested_string_once_without_truncating_text(self) -> None:
        sanitizer = self.load_sanitizer("replacement")
        data_url = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAAB"
        binary_bytes = bytes(range(256)) * ((sanitizer.BINARY_STRING_MIN_BYTES // 256) + 1)
        long_binary = base64.b64encode(binary_bytes).decode("ascii")
        ordinary_text = "Preserve this complete ordinary transcript paragraph. " * 6000
        value = {"first": data_url, "nested": [long_binary, ordinary_text]}

        sanitized, counts = sanitizer.sanitize_public_value(value)

        self.assertEqual(sanitized["first"], sanitizer.binary_omission_marker(data_url))
        self.assertEqual(sanitized["nested"][0], sanitizer.binary_omission_marker(long_binary))
        self.assertEqual(sanitized["nested"][1], ordinary_text)
        self.assertEqual(counts, {"binary_omission": 2})

    def test_short_encrypted_content_field_is_omitted_even_below_binary_size_threshold(self) -> None:
        sanitizer = self.load_sanitizer("encrypted_field")
        encrypted = "gAAAAA" + "AbCdEf012345_-" * 8
        value = {
            "encrypted_content": encrypted,
            "content": "ordinary complete transcript text",
        }

        self.assertLess(len(encrypted.encode("utf-8")), sanitizer.BINARY_STRING_MIN_BYTES)
        sanitized, counts = sanitizer.sanitize_public_value(value)

        self.assertEqual(
            sanitized["encrypted_content"],
            sanitizer.binary_omission_marker(encrypted),
        )
        self.assertEqual(sanitized["content"], value["content"])
        self.assertEqual(counts, {"binary_omission": 1})

    def test_git_hook_key_shaped_substring_is_redacted_without_word_boundary(self) -> None:
        sanitizer = self.load_sanitizer("git_hook_candidate")
        candidate = "prefixYsk-" + "AbCdEf0123456789XYZQ" + "::suffix"

        sanitized, counts = sanitizer.sanitize_public_text(candidate)

        self.assertNotRegex(sanitized, r"sk-[A-Za-z0-9]{20,}")
        self.assertEqual(sanitized, "prefixY[REDACTED_SECRET]::suffix")
        self.assertEqual(counts, {"openai_api_key": 1})

    def test_nested_serialized_encrypted_text_cannot_reintroduce_git_hook_candidate(self) -> None:
        sanitizer = self.load_sanitizer("nested_encrypted_text")
        candidate = "gAAAAAAbCdEfGhJkLmNoPq" + "s" + "k-QwertyAbCdEfGhJkLmNoPq"
        value = {
            "output": json.dumps(
                {"payload": {"encrypted_content": candidate}},
                ensure_ascii=False,
                separators=(",", ":"),
            )
        }

        sanitized, counts = sanitizer.sanitize_public_value(value)
        serialized = json.dumps(sanitized, ensure_ascii=False, sort_keys=True)

        self.assertNotRegex(serialized, r"sk-[A-Za-z0-9]{20,}")
        self.assertIn("[REDACTED_SECRET]", sanitized["output"])
        self.assertEqual(counts, {"openai_api_key": 1})

    def test_sanitize_jsonl_event_rejects_non_dictionary_input(self) -> None:
        sanitizer = self.load_sanitizer("jsonl")

        for value in (None, "event", ["event"]):
            with self.subTest(value=value):
                with self.assertRaises(sanitizer.PublicRawSanitizationError):
                    sanitizer.sanitize_jsonl_event(value)

        sanitized, counts = sanitizer.sanitize_jsonl_event(
            {"message": "owner@example.com", "ok": True}
        )
        self.assertIsInstance(sanitized, dict)
        self.assertEqual(sanitized, {"message": "[REDACTED_EMAIL]", "ok": True})
        self.assertEqual(counts, {"email": 1})

    def test_event_limit_measures_compact_utf8_json_plus_newline_without_mutation(self) -> None:
        sanitizer = self.load_sanitizer("limit")
        event = {"message": "你好", "ok": True}
        expected_bytes = len(
            (json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
        )

        self.assertIsNone(sanitizer.assert_json_event_within_limit(event, expected_bytes))
        self.assertEqual(event, {"message": "你好", "ok": True})
        with self.assertRaises(sanitizer.PublicRawSanitizationError) as raised:
            sanitizer.assert_json_event_within_limit(event, expected_bytes - 1)
        self.assertIn(str(expected_bytes), str(raised.exception))
        self.assertIn(str(expected_bytes - 1), str(raised.exception))


class PublicRawConnectorTest(unittest.TestCase):
    def test_codex_public_snapshot_applies_final_recursive_sanitization(self) -> None:
        module = load_script_module("sync_codex_memory_data.py", "sync_codex_memory_data_r7_snapshot")
        rows = [
            {
                "session_id": "019f4aea-fcab-7dd0-ad1a-1ce2637af2b8",
                "thread_name": "Call +61 412 345 678",
                "cwd_label": "private/202607111234",
            }
        ]
        snapshot = {
            "generated_at": "2026-07-11T16:52:07Z",
            "message_count": 1,
            "tool_call_count": 0,
        }

        public = module.build_public_raw_snapshot(rows, snapshot, [])
        serialized = json.dumps(public, ensure_ascii=False, sort_keys=True)

        self.assertIn("[REDACTED_PHONE]", serialized)
        self.assertNotIn("+61 412 345 678", serialized)
        self.assertNotIn("202607111234", serialized)
        self.assertGreaterEqual(public["redaction_counts"].get("phone", 0), 2)

    def test_chatgpt_public_backup_requires_explicit_redaction_and_writes_versioned_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            export_path = root / "official-export.json"
            write_chatgpt_export(export_path)

            strict, _ = run_json(
                [
                    sys.executable,
                    str(CHATGPT_SYNC),
                    "--database-dir",
                    str(root),
                    "--official-export",
                    str(export_path),
                ],
                expect_success=False,
            )
            self.assertEqual(strict["reason"], "credential_is_not_memory")
            self.assertFalse((root / "data/public_raw/chatgpt").exists())

            result, _ = run_json(
                [
                    sys.executable,
                    str(CHATGPT_SYNC),
                    "--database-dir",
                    str(root),
                    "--official-export",
                    str(export_path),
                    "--redact-for-public-backup",
                ]
            )

            raw_files = list((root / "data/public_raw/chatgpt").glob("conv_r7.*.json"))
            self.assertEqual(len(raw_files), 1)
            self.assertRegex(raw_files[0].name, r"^conv_r7\.[0-9a-f]{12}\.json$")
            raw_text = raw_files[0].read_text(encoding="utf-8")
            self.assertIn("[REDACTED_CREDENTIAL]", raw_text)
            self.assertIn("[REDACTED_EMAIL]", raw_text)
            self.assertIn("[REDACTED_PHONE]", raw_text)
            self.assertIn("[REDACTED_LOCAL_PATH]", raw_text)

            manifest_path = root / "data/processed/conversations/conversation_manifest.jsonl"
            manifest_rows = [json.loads(line) for line in manifest_path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(manifest_rows), 1)
            self.assertEqual(manifest_rows[0]["conversation_id"], "conv_r7")
            self.assertEqual(manifest_rows[0]["raw_ref"], result["raw_paths"][0])
            export_sha = hashlib.sha256(export_path.read_bytes()).hexdigest()
            self.assertEqual(manifest_rows[0]["export_sha256"], export_sha)
            self.assertEqual(result["export_sha256"], export_sha)
            self.assertEqual(result["processed_manifest"], "data/processed/conversations/conversation_manifest.jsonl")
            self.assertTrue(result["redact_for_public_backup"])
            self.assertGreater(sum(result["redaction_counts"].values()), 0)

            source_absolute = str(export_path.resolve())
            public_outputs = "\n".join(
                [
                    json.dumps(result, ensure_ascii=False, sort_keys=True),
                    raw_text,
                    manifest_path.read_text(encoding="utf-8"),
                    (root / "data/derived/chatgpt/chatgpt_sync_summary.json").read_text(encoding="utf-8"),
                ]
            )
            self.assertNotIn(source_absolute, public_outputs)
            self.assertLessEqual(raw_files[0].stat().st_size, MAX_PUBLIC_RAW_FILE_BYTES)
            sync_log_path = next((root / "data/run_logs/sync_runs").glob("*.jsonl"))
            sync_log = json.loads(sync_log_path.read_text(encoding="utf-8").strip())
            self.assertTrue(
                {
                    "task_id",
                    "run_type",
                    "status",
                    "context_used",
                    "tools_used",
                    "tests_run",
                    "failure_recovery",
                    "base_commit",
                    "result_commit",
                    "residual_risks",
                }.issubset(sync_log)
            )
            self.assertEqual(sync_log["run_type"], "sync_run")
            self.assertEqual(sync_log["tests_run"][0]["result"], "NOT_RUN")

    def test_codex_public_transcripts_preserve_every_event_with_relative_provenance(self) -> None:
        module = load_script_module("sync_codex_memory_data.py", "sync_codex_memory_data_r7")
        self.assertTrue(callable(module.export_codex_session_jsonl))
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            database = root / "db"
            codex_home = root / ".codex"
            _source, source_rows = write_codex_session(codex_home)

            result = module.sync_codex_data(
                database,
                codex_home,
                build_atlas=False,
                commit=False,
                push=False,
                force_full_scan=True,
                public_transcripts=True,
            )

            snapshot_path = database / result["outputs"]["public_raw_snapshot"]
            snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
            self.assertTrue(snapshot["public_transcripts_included"])
            self.assertEqual(snapshot["backup_policy"], "sanitized_public_transcripts_no_plaintext_secret")
            self.assertEqual(snapshot["public_transcript_event_count"], len(source_rows))
            self.assertEqual(len(snapshot["public_transcript_exports"]), 1)
            export = snapshot["public_transcript_exports"][0]
            self.assertEqual(export["source_relative_path"], "sessions/2026/07/11/session.jsonl")
            self.assertEqual(export["event_count"], len(source_rows))
            self.assertEqual(export["chunk_count"], len(export["chunk_refs"]))

            chunk_paths = [database / ref for ref in export["chunk_refs"]]
            self.assertTrue(all(path.is_file() for path in chunk_paths))
            self.assertTrue(
                all(
                    re.match(
                        r"^01999999-aaaa-bbbb-cccc-777777777777\.[0-9a-f]{12}\.part-\d{4}\.jsonl$",
                        path.name,
                    )
                    for path in chunk_paths
                )
            )
            exported_rows = []
            for path in chunk_paths:
                self.assertLessEqual(path.stat().st_size, MAX_PUBLIC_RAW_FILE_BYTES)
                exported_rows.extend(json.loads(line) for line in path.read_text(encoding="utf-8").splitlines())
            self.assertEqual(len(exported_rows), len(source_rows))
            exported_text = json.dumps(exported_rows, ensure_ascii=False, sort_keys=True)
            self.assertIn("[REDACTED_CREDENTIAL]", exported_text)
            self.assertIn("[REDACTED_LOCAL_PATH]", exported_text)
            self.assertIn("[REDACTED_BINARY ", exported_text)
            self.assertNotIn(SECRET_VALUE, exported_text)
            self.assertNotIn("/Users/alice", exported_text)
            self.assertNotIn(str(codex_home.resolve()), json.dumps(snapshot, ensure_ascii=False, sort_keys=True))
            report_text = (database / result["outputs"]["report"]).read_text(encoding="utf-8")
            self.assertIn("sanitized public transcripts", report_text)
            sync_log_text = (database / result["outputs"]["sync_log"]).read_text(encoding="utf-8")
            self.assertIn("sanitized public transcript chunks", sync_log_text)
            self.assertTrue(result["public_transcripts"])

    def test_codex_public_snapshot_writer_enforces_file_limit(self) -> None:
        module = load_script_module("sync_codex_memory_data.py", "sync_codex_memory_data_r7_limit")
        original_limit = module.MAX_PUBLIC_RAW_FILE_BYTES
        module.MAX_PUBLIC_RAW_FILE_BYTES = 128
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                target = Path(tmpdir) / "oversized-public-snapshot.json"
                with self.assertRaises(module.PublicRawLimitError):
                    module.write_json_append_only(target, {"payload": "x" * 256})
                self.assertFalse(target.exists())
        finally:
            module.MAX_PUBLIC_RAW_FILE_BYTES = original_limit

    def test_future_agent_markdown_import_is_versioned_and_registry_keeps_template(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            report = root / "r6-independent-review.md"
            report.write_text(
                "# R6 Independent Review\n\nReviewed /Users/alice/private/project. "
                f"Contact reviewer@example.com. {credential_fixture()}\n",
                encoding="utf-8",
            )
            result, _ = run_json(
                [
                    sys.executable,
                    str(FUTURE_AGENT_SYNC),
                    "--database-dir",
                    str(root),
                    "--agent-id",
                    "codex-reviewer",
                    "--markdown-report",
                    str(report),
                    "--event-id",
                    "r6-independent-review",
                ]
            )

            self.assertEqual(result["event_count"], 1)
            self.assertEqual(len(result["raw_paths"]), 1)
            raw_path = root / result["raw_paths"][0]
            self.assertRegex(raw_path.name, r"^r6-independent-review\.[0-9a-f]{12}\.json$")
            payload = json.loads(raw_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["agent_id"], "codex-reviewer")
            self.assertEqual(payload["event_id"], "r6-independent-review")
            self.assertEqual(payload["source_format"], "markdown_report")
            payload_text = json.dumps(payload, ensure_ascii=False, sort_keys=True)
            self.assertIn("[REDACTED_CREDENTIAL]", payload_text)
            self.assertIn("[REDACTED_EMAIL]", payload_text)
            self.assertIn("[REDACTED_LOCAL_PATH]", payload_text)
            self.assertNotIn(str(report.resolve()), payload_text)
            self.assertLessEqual(raw_path.stat().st_size, MAX_PUBLIC_RAW_FILE_BYTES)
            sync_log_path = next((root / "data/run_logs/sync_runs").glob("*.jsonl"))
            sync_log = json.loads(sync_log_path.read_text(encoding="utf-8").strip())
            self.assertTrue(
                {
                    "task_id",
                    "run_type",
                    "status",
                    "context_used",
                    "tools_used",
                    "tests_run",
                    "failure_recovery",
                    "base_commit",
                    "result_commit",
                    "residual_risks",
                }.issubset(sync_log)
            )
            self.assertEqual(sync_log["run_type"], "sync_run")
            self.assertEqual(sync_log["tests_run"][0]["result"], "NOT_RUN")

        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        sources = {row["source_id"]: row for row in registry["sources"]}
        self.assertIn("future_agent_template", sources)
        self.assertEqual(sources["codex-reviewer"]["source_type"], "other_agent")
        self.assertEqual(sources["codex-reviewer"]["raw_root"], "data/public_raw/agents/codex-reviewer")

    def test_atlasctl_wires_all_r7_connector_flags_in_dry_run_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            export_path = root / "official-export.json"
            write_chatgpt_export(export_path)
            chatgpt, _ = run_json(
                [
                    sys.executable,
                    str(ATLASCTL),
                    "sync",
                    "--source",
                    "chatgpt",
                    "--official-export",
                    str(export_path),
                    "--redact-for-public-backup",
                    "--dry-run",
                ]
            )
            self.assertTrue(chatgpt["redact_for_public_backup"])

            codex_home = root / ".codex"
            write_codex_session(codex_home)
            codex, _ = run_json(
                [
                    sys.executable,
                    str(ATLASCTL),
                    "sync",
                    "--source",
                    "codex",
                    "--codex-home",
                    str(codex_home),
                    "--public-transcripts",
                    "--dry-run",
                ]
            )
            self.assertTrue(codex["public_transcripts"])

            report = root / "review.md"
            report.write_text("# Reviewer event\n\nReal review output.\n", encoding="utf-8")
            future_agent, _ = run_json(
                [
                    sys.executable,
                    str(ATLASCTL),
                    "sync",
                    "--source",
                    "future-agent",
                    "--agent-id",
                    "codex-reviewer",
                    "--markdown-report",
                    str(report),
                    "--event-id",
                    "review-r7",
                    "--dry-run",
                ]
            )
            self.assertEqual(future_agent["event_id"], "review-r7")
            self.assertEqual(future_agent["source_format"], "markdown_report")


if __name__ == "__main__":
    unittest.main()

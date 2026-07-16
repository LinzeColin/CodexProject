from __future__ import annotations

import json
import hashlib
import importlib.util
import os
import re
import sqlite3
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

import pfi_v02.stage_v025_data_inventory as inventory_module
from pfi_v02.stage_v025_data_inventory import (
    ACCEPTANCE_ID,
    CANDIDATE_ROOT_ALIASES,
    EXPECTED_SOURCE_IDS,
    PHASE_ID,
    SOURCE_REGISTRY_PATH,
    TASK_IDS,
    _hash_git_blobs,
    assert_public_safe_payload,
    build_metric_computability_matrix,
    build_phase21_contract,
    build_privacy_scan_report,
    build_source_manifest,
    collect_data_root_inventory,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
PFI_ROOT = REPO_ROOT / "PFI"
SCRIPT_PATH = PFI_ROOT / "scripts" / "v025" / "data_inventory.py"
TASKPACK_SOURCE_SCHEMA = PFI_ROOT / "config" / "schemas" / "v025" / "data_source_manifest.schema.json"
COLLECTION_SCHEMA = PFI_ROOT / "config" / "schemas" / "v025" / "source_manifest_collection.schema.json"
REPORT_ROOT = PFI_ROOT / "reports" / "pfi_v025" / "stage_2" / "phase_2_1"


def _load_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _by_id(items: list[dict[str, object]], field: str) -> dict[str, dict[str, object]]:
    return {str(item[field]): item for item in items}


def _load_cli_module():
    spec = importlib.util.spec_from_file_location("pfi_v025_data_inventory_cli", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_phase_contract_is_exactly_phase_21_and_acceptance_is_project_assigned() -> None:
    contract = build_phase21_contract()

    assert contract["version"] == "v0.2.5"
    assert contract["stage"] == 2
    assert contract["phase_id"] == PHASE_ID == "V025-S2-P2.1"
    assert contract["task_ids"] == list(TASK_IDS) == [
        "S2-P1-T1",
        "S2-P1-T2",
        "S2-P1-T3",
        "S2-P1-T4",
    ]
    assert contract["acceptance_id"] == ACCEPTANCE_ID
    assert contract["acceptance_id_origin"] == "project_governance_assigned_not_taskpack"
    assert contract["current_phase_only"] is True
    assert contract["read_only_real_sources"] is True
    assert contract["finder_used"] is False
    assert "Phase 2.2" in contract["explicitly_not_done"]


def test_inventory_uses_only_fixed_symbolic_roots_and_one_canonical_private_root() -> None:
    inventory = collect_data_root_inventory(REPO_ROOT)
    roots = inventory["candidate_roots"]

    assert [root["path_alias"] for root in roots] == list(CANDIDATE_ROOT_ALIASES)
    assert all(not str(root["path_alias"]).startswith("/") for root in roots)
    assert sum(root["canonical_private_root"] is True for root in roots) == 1
    canonical = next(root for root in roots if root["canonical_private_root"] is True)
    assert canonical["root_id"] == "ROOT-PFI-DATA-HOME"
    assert canonical["path_alias"] == "$PFI_DATA_HOME"
    assert canonical["resolution_policy"] == "environment_or_user_state_default"
    assert canonical["within_repo"] is False
    assert inventory["canonical_candidate_conflict"] is False
    assert inventory["acceptance_gate_status"] == "pass"
    assert inventory["mutation_attempted"] is False
    assert inventory["observed_root_metadata_unchanged"] is True
    assert inventory["operational_database_unchanged"] is True
    assert_public_safe_payload(inventory)


def test_database_probe_is_fail_closed_and_before_after_identical() -> None:
    inventory = collect_data_root_inventory(REPO_ROOT)
    probe = inventory["database_probe"]
    git_surface = inventory["git_object_surface"]

    assert probe["database_path_redacted"] is True
    assert probe["query_mode"] == "mode=ro"
    assert probe["sqlite_header_mode"] == "rollback_journal"
    assert probe["query_only"] is True
    assert probe["authorizer_deny_write"] is True
    assert probe["quiescence_gate"] == "sqlite_shared_read_transaction"
    assert probe["row_values_emitted"] == 0
    assert probe["table_names_emitted"] == 0
    assert probe["content_hash_scheme"] == "sha256-file-bytes-v1"
    assert git_surface["content_hash_scheme"] == "sha256-framed-mode-path-oid-size-blob-v2"
    assert probe["content_hash_scheme"] != git_surface["content_hash_scheme"]
    if probe["status"] == "ready_metadata_only":
        assert probe["sidecars_present"] is False
        assert probe["quick_check"] == "ok"
        assert probe["sidecar_count_before"] == 0
        assert probe["sidecar_count_after"] == 0
        assert probe["before"] == probe["after"]
        assert probe["unchanged_before_after"] is True
        assert str(probe["content_hash"]).startswith("sha256:")
    else:
        assert probe["status"] in {
            "source_missing",
            "permission_denied",
            "blocked_symlink",
            "blocked_sidecar_present",
            "blocked_changed_during_probe",
            "blocked_integrity_check",
            "blocked_candidate_conflict",
        }
        assert probe["content_hash"] is None


def test_source_manifest_wrapper_and_each_source_validate_against_both_schemas() -> None:
    inventory = collect_data_root_inventory(REPO_ROOT)
    manifest = build_source_manifest(inventory)
    collection_schema = _load_json(COLLECTION_SCHEMA)
    source_schema = _load_json(TASKPACK_SOURCE_SCHEMA)

    Draft202012Validator(collection_schema).validate(manifest)
    for source in manifest["sources"]:
        Draft202012Validator(source_schema).validate(source)
        for required in (
            "label",
            "source_type",
            "capabilities",
            "path_alias",
            "parser_version",
            "record_count",
            "coverage",
            "as_of",
            "content_hash",
            "status",
            "blocking_reason_zh",
        ):
            assert required in source
    assert manifest["taskpack_schema_applies_to"] == "sources[*]"
    assert manifest["wrapper_schema_applies_to"] == "document"
    assert_public_safe_payload(manifest)


def test_taskpack_single_source_schema_is_semantically_preserved() -> None:
    taskpack = Path.home() / "Downloads" / "PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip"
    if not taskpack.is_file():
        return
    with zipfile.ZipFile(taskpack) as archive:
        upstream = json.loads(archive.read("PFI_v0.2.5_TaskPack/schemas/data_source_manifest.schema.json"))
    assert _load_json(TASKPACK_SOURCE_SCHEMA) == upstream


def test_phase_evidence_validates_against_taskpack_schema() -> None:
    taskpack = Path.home() / "Downloads" / "PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip"
    if not taskpack.is_file():
        return
    with zipfile.ZipFile(taskpack) as archive:
        schema = json.loads(archive.read("PFI_v0.2.5_TaskPack/schemas/evidence_pack.schema.json"))
    evidence = _load_json(REPORT_ROOT / "evidence.json")
    Draft202012Validator(schema).validate(evidence)
    assert evidence["git_commit"] == "SELF"
    assert evidence["git_commit_semantics"] == "commit_containing_this_evidence"
    assert evidence["requires_user_acceptance"] is True


def test_source_registry_is_the_manifest_definition_input() -> None:
    registry = _load_json(SOURCE_REGISTRY_PATH)
    inventory = collect_data_root_inventory(REPO_ROOT)
    manifest = build_source_manifest(inventory)

    assert [item["source_id"] for item in registry["sources"]] == list(EXPECTED_SOURCE_IDS)
    assert [item["source_id"] for item in manifest["sources"]] == list(EXPECTED_SOURCE_IDS)
    definitions = _by_id(registry["sources"], "source_id")
    assert definitions["SRC-HOLDINGS"]["resolution_task_ids"] == ["S4-P2-T1", "S4-P2-T3", "S4-P2-T4"]
    assert definitions["SRC-MARKET-PRICES"]["resolution_task_ids"] == ["S4-P2-T3", "S4-P2-T4"]
    for definition, source in zip(registry["sources"], manifest["sources"], strict=True):
        for field in (
            "source_id",
            "label",
            "source_type",
            "capabilities",
            "path_alias",
            "parser_version",
            "root_id",
            "observation_mode",
            "source_role",
            "resolution_task_ids",
        ):
            assert source[field] == definition[field]


def test_transactions_do_not_imply_balance_holdings_or_net_worth_computability() -> None:
    inventory = collect_data_root_inventory(REPO_ROOT)
    manifest = build_source_manifest(inventory)
    sources = _by_id(manifest["sources"], "source_id")
    matrix = build_metric_computability_matrix(manifest)
    metrics = _by_id(matrix["metrics"], "metric_id")

    transactions = sources["SRC-TRANSACTIONS-ALIPAY"]
    assert transactions["status"] == "ready"
    assert int(transactions["record_count"]) == 8815
    assert transactions["coverage"] == {"start": "2022-06-06", "end": "2026-06-03"}
    assert str(transactions["content_hash"]).startswith("sha256:")

    assert metrics["consumption_classification"]["computability"] == "blocked_missing_dependencies"
    assert metrics["consumption_classification"]["source_inputs_available"] is True
    assert "S3-P2-T3" in metrics["consumption_classification"]["missing_contract_task_ids"]
    assert metrics["cash_balance_cny"]["computability"] == "blocked_missing_dependencies"
    assert metrics["investment_market_value_cny"]["computability"] == "blocked_missing_dependencies"
    assert metrics["net_worth_cny"]["computability"] == "blocked_missing_dependencies"
    assert "S3-P3-T2" in metrics["cash_balance_cny"]["missing_contract_task_ids"]
    assert "S4-P1-T2" in metrics["cash_balance_cny"]["missing_contract_task_ids"]
    assert "S5-P2-T2" in metrics["cash_balance_cny"]["missing_contract_task_ids"]
    assert metrics["cash_balance_cny"]["value"] is None
    assert metrics["investment_market_value_cny"]["value"] is None
    assert metrics["net_worth_cny"]["value"] is None
    assert matrix["transactions_available_is_not_balance_or_holdings_proof"] is True
    assert_public_safe_payload(matrix)


def test_missing_private_input_is_blocked_without_financial_fixture(tmp_path: Path) -> None:
    missing = tmp_path / "does-not-exist"
    inventory = collect_data_root_inventory(REPO_ROOT, data_home=missing)
    manifest = build_source_manifest(inventory)
    sources = _by_id(manifest["sources"], "source_id")

    assert inventory["database_probe"]["status"] == "source_missing"
    operational = sources["SRC-OPERATIONAL-SQLITE"]
    assert operational["status"] == "source_missing"
    assert operational["record_count"] is None
    assert operational["coverage"] == {"start": None, "end": None}
    assert operational["content_hash"] is None
    assert manifest["financial_fixture_fallback_used"] is False
    for source_id in EXPECTED_SOURCE_IDS[2:]:
        assert sources[source_id]["status"] == "not_loaded"


def test_structural_sqlite_sidecar_symlink_type_permission_and_wal_fail_closed(
    tmp_path: Path,
    monkeypatch,
) -> None:
    # This is a non-financial security fixture. It never participates in
    # financial acceptance or metric computation.
    data_home = tmp_path / "data-home"
    operational = data_home / "private" / "operational"
    operational.mkdir(parents=True)
    database = operational / "pfi.sqlite"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE source_records (source_id TEXT)")

    sidecar = Path(str(database) + "-mj DEADBEEF")
    sidecar.touch()
    sidecar_inventory = collect_data_root_inventory(REPO_ROOT, data_home=data_home)
    assert sidecar_inventory["database_probe"]["status"] == "blocked_sidecar_present"
    assert sidecar_inventory["database_probe"]["content_hash"] is None
    sidecar.unlink()

    database.unlink()
    database.symlink_to(tmp_path / "outside.sqlite")
    symlink_inventory = collect_data_root_inventory(REPO_ROOT, data_home=data_home)
    assert symlink_inventory["database_probe"]["status"] == "blocked_symlink"
    assert symlink_inventory["database_probe"]["content_hash"] is None
    assert_public_safe_payload(symlink_inventory)

    database.unlink()
    database.mkdir()
    non_regular_inventory = collect_data_root_inventory(REPO_ROOT, data_home=data_home)
    assert non_regular_inventory["database_probe"]["status"] == "blocked_non_regular_database"
    assert non_regular_inventory["acceptance_gate_status"] == "blocked"
    database.rmdir()

    database.write_bytes(b"SQLite format 3\x00" + b"\x10\x00" + b"\x02\x02")
    wal_inventory = collect_data_root_inventory(REPO_ROOT, data_home=data_home)
    assert wal_inventory["database_probe"]["status"] == "blocked_wal_header"
    assert wal_inventory["database_probe"]["sqlite_header_mode"] == "wal"
    assert wal_inventory["acceptance_gate_status"] == "blocked"
    database.unlink()

    original_scandir = os.scandir

    def deny_operational_scan(path):
        if Path(path) == operational:
            raise PermissionError("structural-permission-fixture")
        return original_scandir(path)

    with monkeypatch.context() as patcher:
        patcher.setattr(inventory_module.os, "scandir", deny_operational_scan)
        denied_inventory = collect_data_root_inventory(REPO_ROOT, data_home=data_home)
    assert denied_inventory["database_probe"]["status"] == "permission_denied"
    assert denied_inventory["acceptance_gate_status"] == "blocked"


def test_root_intermediate_symlink_and_repo_containment_fail_closed(tmp_path: Path) -> None:
    target = tmp_path / "target"
    (target / "private" / "operational").mkdir(parents=True)
    root_link = tmp_path / "root-link"
    root_link.symlink_to(target, target_is_directory=True)
    root_inventory = collect_data_root_inventory(REPO_ROOT, data_home=root_link)
    assert root_inventory["canonical_root_gate"] == "blocked_symlink_component"
    assert root_inventory["database_probe"]["status"] == "blocked_unsafe_root"
    assert root_inventory["acceptance_gate_status"] == "blocked"

    intermediate = tmp_path / "intermediate"
    intermediate.mkdir()
    (intermediate / "private").symlink_to(target / "private", target_is_directory=True)
    intermediate_inventory = collect_data_root_inventory(REPO_ROOT, data_home=intermediate)
    assert intermediate_inventory["database_probe"]["status"] == "blocked_symlink"
    assert intermediate_inventory["acceptance_gate_status"] == "blocked"

    repo_inventory = collect_data_root_inventory(REPO_ROOT, data_home=PFI_ROOT / "config")
    assert repo_inventory["canonical_root_gate"] == "blocked_inside_public_git"
    assert repo_inventory["database_probe"]["status"] == "blocked_unsafe_root"
    assert repo_inventory["acceptance_gate_status"] == "blocked"


def test_distinct_existing_default_and_configured_private_roots_conflict(
    tmp_path: Path,
    monkeypatch,
) -> None:
    home = tmp_path / "home"
    default_root = home / ".pfi"
    configured_root = tmp_path / "configured"
    default_root.mkdir(parents=True)
    configured_root.mkdir()
    monkeypatch.setenv("HOME", str(home))

    inventory = collect_data_root_inventory(
        REPO_ROOT,
        env={"PFI_DATA_HOME": str(configured_root)},
    )
    roots = _by_id(inventory["candidate_roots"], "root_id")
    assert inventory["canonical_candidate_conflict"] is True
    assert inventory["canonical_root_gate"] == "blocked_distinct_private_root_candidate"
    assert inventory["database_probe"]["status"] == "blocked_unsafe_root"
    assert inventory["acceptance_gate_status"] == "blocked"
    assert roots["ROOT-USER-PFI"]["role"] == "alternate_private_root_candidate"
    assert roots["ROOT-USER-PFI"]["alias_of"] is None


def test_sidecar_appearing_after_query_blocks_publish(
    tmp_path: Path,
    monkeypatch,
) -> None:
    data_home = tmp_path / "data-home"
    operational = data_home / "private" / "operational"
    operational.mkdir(parents=True)
    database = operational / "pfi.sqlite"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE source_records (source_id TEXT)")

    calls = 0
    original = inventory_module._sidecar_count

    def sidecar_count(path: Path) -> int:
        nonlocal calls
        calls += 1
        if calls == 1:
            return original(path)
        return 1

    monkeypatch.setattr(inventory_module, "_sidecar_count", sidecar_count)
    probe = inventory_module._probe_operational_database(data_home)
    assert probe["status"] == "blocked_changed_during_probe"
    assert probe["sidecar_count_before"] == 0
    assert probe["sidecar_count_after"] == 1
    assert probe["unchanged_before_after"] is False


def test_git_content_hash_is_path_and_mode_sensitive(tmp_path: Path) -> None:
    repository = tmp_path / "git"
    repository.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repository, check=True)
    blob = b"same non-financial structural blob\n"
    oid = subprocess.run(
        ["git", "hash-object", "-w", "--stdin"],
        cwd=repository,
        input=blob,
        capture_output=True,
        check=True,
    ).stdout.decode("ascii").strip()

    first = _hash_git_blobs(repository, [(b"100644", b"first/path", oid, len(blob))])
    renamed = _hash_git_blobs(repository, [(b"100644", b"second/path", oid, len(blob))])
    executable = _hash_git_blobs(repository, [(b"100755", b"first/path", oid, len(blob))])
    assert first != renamed
    assert first != executable


def test_cli_fails_closed_for_blocked_private_root_without_output(tmp_path: Path) -> None:
    home = tmp_path / "home"
    data_home = home / ".pfi"
    operational = data_home / "private" / "operational"
    operational.mkdir(parents=True)
    database = operational / "pfi.sqlite"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE source_records (source_id TEXT)")
    Path(str(database) + "-mj DEADBEEF").touch()
    output = tmp_path / "blocked.json"
    env = {
        **os.environ,
        "HOME": str(home),
        "PFI_DATA_HOME": str(data_home),
        "PYTHONDONTWRITEBYTECODE": "1",
    }

    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--read-only",
            "--redact",
            "--json-out",
            str(output),
        ],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 1
    assert completed.stdout == ""
    assert completed.stderr.strip() == "source_manifest=FAIL|reason=redacted"
    assert not output.exists()


def test_cli_rejects_repository_output_and_preserves_no_file() -> None:
    output = PFI_ROOT / "forbidden-v025-source-manifest.json"
    assert not output.exists()
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--read-only",
            "--redact",
            "--json-out",
            str(output),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 2
    assert not output.exists()


def test_configured_private_absolute_path_never_enters_public_payload(tmp_path: Path) -> None:
    sentinel = tmp_path / "absolute-private-sentinel"
    inventory = collect_data_root_inventory(REPO_ROOT, env={"PFI_DATA_HOME": str(sentinel)})
    rendered = json.dumps(inventory, ensure_ascii=False)
    assert str(sentinel) not in rendered
    assert "/Users/" not in rendered
    assert_public_safe_payload(inventory)


def test_cli_requires_read_only_and_redact_and_writes_only_requested_temp_output(tmp_path: Path) -> None:
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    rejected = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--json-out", str(tmp_path / "rejected.json")],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert rejected.returncode == 2
    assert not (tmp_path / "rejected.json").exists()
    assert "/Users/" not in rejected.stdout + rejected.stderr

    output = tmp_path / "source_manifest.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--read-only",
            "--redact",
            "--json-out",
            str(output),
        ],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "source_manifest=PASS|read_only=true|redacted=true"
    assert completed.stderr == ""
    assert output.is_file()
    assert output.stat().st_mode & 0o777 == 0o600
    assert_public_safe_payload(_load_json(output))


def test_cli_accepts_operating_system_temp_lexical_alias() -> None:
    output = Path(tempfile.gettempdir()) / f"pfi-v025-lexical-temp-{os.getpid()}.json"
    output.unlink(missing_ok=True)
    try:
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--read-only",
                "--redact",
                "--json-out",
                str(output),
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr
        assert output.is_file()
        assert output.stat().st_mode & 0o777 == 0o600
    finally:
        output.unlink(missing_ok=True)


def test_cli_directory_fd_rejects_parent_swap_to_symlink(tmp_path: Path) -> None:
    cli = _load_cli_module()
    parent = tmp_path / "trusted-parent"
    parent.mkdir()
    output = parent / "manifest.json"
    descriptor = cli._open_output_parent_fd(output)
    os.close(descriptor)

    original_parent = tmp_path / "trusted-parent-original"
    parent.rename(original_parent)
    outside = tmp_path / "outside"
    outside.mkdir()
    parent.symlink_to(outside, target_is_directory=True)

    with pytest.raises(OSError):
        cli._open_output_parent_fd(output)
    assert not (outside / output.name).exists()


def test_cli_cleanup_error_remains_redacted_without_traceback(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    cli = _load_cli_module()
    output = tmp_path / "cleanup-error.json"
    original_unlink = os.unlink

    def fail_link(*args, **kwargs):
        del args, kwargs
        raise OSError("private-path-sentinel")

    def fail_unlink(*args, **kwargs):
        del args, kwargs
        raise OSError("private-path-sentinel")

    with monkeypatch.context() as patcher:
        patcher.setattr(cli.os, "link", fail_link)
        patcher.setattr(cli.os, "unlink", fail_unlink)
        result = cli.main(["--read-only", "--redact", "--json-out", str(output)])

    captured = capsys.readouterr()
    assert result == 1
    assert captured.out == ""
    assert captured.err.strip() == "source_manifest=FAIL|reason=redacted"
    assert "private-path-sentinel" not in captured.err
    assert "Traceback" not in captured.err
    assert not output.exists()
    for candidate in tmp_path.glob(".pfi-v025-source-manifest-*.tmp"):
        original_unlink(candidate)

    committed_output = tmp_path / "committed-after-cleanup-error.json"

    def fail_temporary_unlink(path, *args, **kwargs):
        if str(path).startswith(".pfi-v025-source-manifest-"):
            raise OSError("private-path-sentinel")
        return original_unlink(path, *args, **kwargs)

    with monkeypatch.context() as patcher:
        patcher.setattr(cli.os, "unlink", fail_temporary_unlink)
        result = cli.main(["--read-only", "--redact", "--json-out", str(committed_output)])

    captured = capsys.readouterr()
    assert result == 0
    assert captured.out.strip() == "source_manifest=PASS|read_only=true|redacted=true"
    assert captured.err == ""
    assert committed_output.is_file()
    assert committed_output.stat().st_mode & 0o777 == 0o600
    original_unlink(committed_output)
    for candidate in tmp_path.glob(".pfi-v025-source-manifest-*.tmp"):
        original_unlink(candidate)


def test_cli_direct_run_does_not_create_or_update_bytecode(tmp_path: Path) -> None:
    cache_root = PFI_ROOT / "src" / "pfi_v02" / "__pycache__"

    def snapshot() -> dict[str, tuple[int, int]]:
        if not cache_root.is_dir():
            return {}
        return {
            path.name: (path.stat().st_size, path.stat().st_mtime_ns)
            for path in cache_root.glob("*.pyc")
        }

    before = snapshot()
    env = {key: value for key, value in os.environ.items() if key != "PYTHONDONTWRITEBYTECODE"}
    output = tmp_path / "no-bytecode.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--read-only",
            "--redact",
            "--json-out",
            str(output),
        ],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert snapshot() == before


def test_tracked_phase_artifacts_are_consistent_and_public_safe() -> None:
    expected = {
        "data_root_inventory.json",
        "source_manifest.json",
        "metric_computability_matrix.json",
        "database_before_after.json",
        "evidence.json",
    }
    assert expected.issubset({path.name for path in REPORT_ROOT.glob("*.json")})
    for name in sorted(expected):
        assert_public_safe_payload(_load_json(REPORT_ROOT / name))

    privacy_scan = (REPORT_ROOT / "privacy_scan.txt").read_text(encoding="utf-8")
    assert privacy_scan.splitlines()[0] == "PASS"
    assert "scanner=pfi-v025-public-artifact-scan-v3" in privacy_scan
    for counter in (
        "absolute_private_paths",
        "raw_filenames",
        "financial_row_values",
        "account_identifiers",
        "credentials",
        "sqlite_table_names",
        "finder_operations",
        "source_mutations",
        "financial_fixture_fallback",
    ):
        assert f"{counter}=0" in privacy_scan

    scan_targets = (
        REPORT_ROOT / "data_root_inventory.json",
        REPORT_ROOT / "source_manifest.json",
        REPORT_ROOT / "metric_computability_matrix.json",
        REPORT_ROOT / "database_before_after.json",
        REPORT_ROOT / "evidence.json",
        PFI_ROOT / "docs" / "pfi_v025" / "stage_2" / "data_root_decision.md",
        REPORT_ROOT / "risk_and_rollback.md",
    )
    for target in scan_targets:
        raw = target.read_bytes()
        text = raw.decode("utf-8")
        assert "/Users/" not in text
        assert "BEGIN PRIVATE KEY" not in text
        assert "access_token" not in text.lower()
        assert "refresh_token" not in text.lower()
        relative = target.relative_to(REPO_ROOT).as_posix()
        digest = "sha256:" + hashlib.sha256(raw).hexdigest()
        assert f"input={relative}|{digest}" in privacy_scan

    fresh_inventory = collect_data_root_inventory(REPO_ROOT)
    tracked_inventory = _load_json(REPORT_ROOT / "data_root_inventory.json")
    fresh_inventory["observed_at"] = tracked_inventory["observed_at"]
    assert fresh_inventory == tracked_inventory

    fresh_manifest = build_source_manifest(fresh_inventory)
    tracked_manifest = _load_json(REPORT_ROOT / "source_manifest.json")
    assert fresh_manifest == tracked_manifest
    assert build_metric_computability_matrix(fresh_manifest) == _load_json(
        REPORT_ROOT / "metric_computability_matrix.json"
    )


def test_privacy_scan_is_deterministic_and_covers_all_public_evidence() -> None:
    tracked = (REPORT_ROOT / "privacy_scan.txt").read_text(encoding="utf-8")
    observed_at = next(
        line.removeprefix("observed_at=")
        for line in tracked.splitlines()
        if line.startswith("observed_at=")
    )
    assert build_privacy_scan_report(REPO_ROOT, observed_at) == tracked
    assert "input_count=9" in tracked
    assert "input=PFI/reports/pfi_v025/stage_2/phase_2_1/terminal.log|sha256:" in tracked
    assert "generation_contract=fixed_input_list_semantic_and_text_recompute" in tracked
    with pytest.raises(ValueError, match="invalid_privacy_observed_at"):
        build_privacy_scan_report(REPO_ROOT, observed_at + "\ncredentials=0")


def test_privacy_scanner_recomputes_every_forbidden_category(tmp_path: Path) -> None:
    counts = {
        "absolute_private_paths": 0,
        "raw_filenames": 0,
        "financial_row_values": 0,
        "account_identifiers": 0,
        "credentials": 0,
        "sqlite_table_names": 0,
        "finder_operations": 0,
        "source_mutations": 0,
        "financial_fixture_fallback": 0,
    }
    payload = {
        "path": "/" + "users/example/private",
        "raw_filename": "redacted.csv",
        "account_id": "redacted-account",
        "rows": [{"value": "CNY 1.00"}],
        "table": "source_records",
        "access_token": "redacted-token",
        "finder_used": True,
        "source_mutation_performed": True,
        "financial_fixture_fallback_used": True,
    }
    inventory_module._accumulate_privacy_violations(
        counts,
        tmp_path / "structural-fixture.json",
        json.dumps(payload),
    )
    assert all(value > 0 for value in counts.values())
    with pytest.raises(ValueError, match="privacy_scan_failed"):
        inventory_module._assert_privacy_counts_clean(counts)

    for credential_payload in (
        {"api_key": "structural-secret"},
        {"password": "structural-secret"},
        {"authorization": "Bearer structural-secret"},
    ):
        credential_counts = {key: 0 for key in counts}
        inventory_module._accumulate_privacy_violations(
            credential_counts,
            tmp_path / "credential-structural-fixture.json",
            json.dumps(credential_payload),
        )
        assert credential_counts["credentials"] > 0
        with pytest.raises(ValueError):
            assert_public_safe_payload(credential_payload)


def test_human_entries_show_current_scope_truth() -> None:
    features = (PFI_ROOT / "功能清单.md").read_text(encoding="utf-8")
    development = (PFI_ROOT / "开发记录.md").read_text(encoding="utf-8")
    parameters = (PFI_ROOT / "模型参数文件.md").read_text(encoding="utf-8")

    expected_progress = "v0.2.5 tasks=36/156 (23.08%); V025-S2 tasks=12/12 (100.00%)"
    expected_gate = "ACC-PFI-V025-S3-P31-SOURCE-ACCOUNT"
    assert expected_progress in features
    assert "- total_hours: `UNKNOWN`" in development
    assert "- completed_hours: `UNKNOWN`" in development
    assert expected_progress in development
    assert expected_gate in features
    assert expected_gate in development
    assert expected_gate in parameters
    assert "- active_formula_count: `2`" in parameters
    assert "- active_parameter_count: `27`" in parameters
    scoped = development[development.index("### V025-S0") : development.index("### V024-FD")]
    assert all(f"### V025-S{stage}" in scoped for stage in range(13))
    assert len(set(re.findall(r"\| (S\d+-P\d+-T\d+) \|", scoped))) == 156
    assert scoped.count("- derived_hours: `UNKNOWN`") >= 13
    assert scoped.count(" planned_deliverable: `") == 156
    assert scoped.count(" acceptance_summary: `") == 156
    assert scoped.count("- stop_gate_planned_evidence: `") == 13
    assert scoped.count("- human_acceptance: `") == 13
    assert "- S2-P1-T1 planned_deliverable: `data_root_inventory.json`" in scoped
    assert "- S2-P1-T4 acceptance_summary: `依赖明确`" in scoped
    assert "| S2-P2-T1 | 建立八类时间字段与时区合同 | completed | UNKNOWN | UNKNOWN |" in scoped
    assert "| S2-P3-T4 | Evidence 与用户验收 | completed | UNKNOWN | UNKNOWN |" in scoped
    assert "### V025-S2-WHOLE-REVIEW" in scoped


def test_canonical_roadmap_registers_the_complete_source_stage_task_catalog() -> None:
    source = Path.home() / "Downloads" / "PFI_v0.2.5_Production_Truth_Human_Workflow_Roadmap.md"
    if not source.is_file():
        return
    source_raw = source.read_bytes()
    source_text = source_raw.decode("utf-8")
    roadmap_text = (PFI_ROOT / "docs" / "governance" / "roadmap.yaml").read_text(encoding="utf-8")
    scoped = roadmap_text[roadmap_text.index('  - stage_id: "V025-S0"') : roadmap_text.index('  - stage_id: "V024-FD"')]

    source_task_ids = {
        columns[0]
        for line in source_text.splitlines()
        if re.match(r"^\| S\d+-P\d+-T\d+ \|", line)
        for columns in [[part.strip() for part in line.strip("|").split("|")]]
    }
    canonical_task_ids = set(re.findall(r'task_id: "(S\d+-P\d+-T\d+)"', scoped))
    assert source_task_ids == canonical_task_ids
    assert len(canonical_task_ids) == 156
    assert scoped.count("planned_deliverable:") == 156
    assert scoped.count("acceptance_summary:") == 156
    assert set(re.findall(r'stage_id: "(V025-S\d+)"', scoped)) == {
        f"V025-S{stage}" for stage in range(13)
    }
    assert "estimated_hours: 0" not in scoped
    assert hashlib.sha256(source_raw).hexdigest() in roadmap_text

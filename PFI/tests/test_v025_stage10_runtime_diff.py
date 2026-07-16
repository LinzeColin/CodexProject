from __future__ import annotations

import hashlib
import json
import shutil
import socket
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
PFI_ROOT = REPO_ROOT / "PFI"
SRC_ROOT = PFI_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pfi_v02 import runtime_diff_v025 as runtime_diff  # noqa: E402
from pfi_v02 import stage_v021_runtime_api as runtime_api  # noqa: E402


def _opaque_hashes() -> dict[str, str]:
    return {
        domain_id: hashlib.sha256(f"opaque-dependency:{domain_id}".encode("utf-8")).hexdigest()
        for domain_id in runtime_diff.DEPENDENCY_DOMAINS
    }


def _status_projection() -> dict[str, object]:
    return {
        "schema": "PFIV024Stage4ReadModelStatusV1",
        "contract_version": "PFI-V025-STAGE10-P10.2-NONFINANCIAL-PROJECTION",
        "read_model_hash": hashlib.sha256(b"opaque-read-model-status").hexdigest(),
        "source": {
            "status": "not_loaded",
            "evidence_hash": hashlib.sha256(b"opaque-source-evidence").hexdigest(),
            "as_of": None,
            "record_count": 0,
            "raw_file_count": 0,
        },
        "core_metric_states": [],
        "blocked_metric_ids": list(runtime_diff.METRIC_UNIVERSE),
        "surface_ids": ["home", "accounts", "investment", "consumption", "insights"],
    }


def test_dependency_registry_is_exact_explainable_and_acyclic() -> None:
    registry = runtime_diff.load_dependency_registry(PFI_ROOT)
    assert registry["schema"] == "PFIV025DependencyRegistryV1"
    assert [row["domain_id"] for row in registry["domains"]] == list(
        runtime_diff.DEPENDENCY_DOMAINS
    )
    assert registry["ordinary_run_network_allowed"] is False
    assert registry["cache_contract"] == {
        "ttl_seconds": 30,
        "persistent": False,
        "invalidation_mode": "composite_dependency_snapshot_hash",
        "no_diff_recompute_scope": "none",
        "no_diff_network_allowed": False,
        "no_diff_codex_allowed": False,
        "no_diff_llm_allowed": False,
    }
    seen: set[str] = set()
    for row in registry["domains"]:
        assert set(row["upstream"]).issubset(seen)
        assert row["impacted_metrics"]
        assert row["cache_scopes"]
        assert row["provenance"]
        seen.add(row["domain_id"])
    assert registry["registry_sha256"] == hashlib.sha256(
        (PFI_ROOT / runtime_diff.REGISTRY_RELATIVE_PATH).read_bytes()
    ).hexdigest()


def test_read_only_sqlite_observation_uses_empty_real_schema_without_financial_rows(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "pfi.sqlite"
    migration = (
        PFI_ROOT / "src/pfi_os/migrations/v025_stage7_import_review_ledger.sql"
    ).read_text(encoding="utf-8")
    with sqlite3.connect(db_path) as connection:
        connection.executescript(migration)
    before_hash = hashlib.sha256(db_path.read_bytes()).hexdigest()
    snapshot = runtime_diff.build_dependency_snapshot(
        PFI_ROOT,
        db_path=db_path,
    )
    after_hash = hashlib.sha256(db_path.read_bytes()).hexdigest()

    assert before_hash == after_hash
    assert not Path(f"{db_path}-wal").exists()
    assert not Path(f"{db_path}-shm").exists()
    assert snapshot["contains_private_values"] is False
    assert snapshot["financial_values_emitted"] == 0
    assert snapshot["network_calls"] == 0
    assert set(snapshot["hashes"]) == set(runtime_diff.DEPENDENCY_DOMAINS)
    for domain_id in ("raw", "source", "ledger"):
        assert snapshot["observations"][domain_id]["status"] == "not_loaded"
        assert snapshot["observations"][domain_id]["record_count"] == 0
    serialized = json.dumps(snapshot, ensure_ascii=False, sort_keys=True)
    assert str(tmp_path) not in serialized
    assert "/Users/" not in serialized


def test_each_dependency_hash_changes_cache_identity_and_diff_is_narrowed() -> None:
    registry = runtime_diff.load_dependency_registry(PFI_ROOT)
    baseline_hashes = _opaque_hashes()
    baseline = runtime_diff.build_dependency_snapshot_from_hashes(
        baseline_hashes,
        PFI_ROOT,
    )
    base_dimensions = {
        "build_id": "pfi-v025-stage10-phase10.2",
        "git_commit": "1" * 40,
        "frontend_bundle_hash": "2" * 64,
        "backend_build_hash": "3" * 64,
        "data_hash": baseline["snapshot_hash"],
        "parameter_hash": baseline_hashes["parameter"],
        "formula_hash": baseline_hashes["formula"],
        "fx_snapshot_id": "local-fx-snapshot",
        "fx_snapshot_hash": baseline_hashes["fx"],
        "read_model_hash": baseline_hashes["read_model"],
        "streamlit_version": "1.35.0",
        "requirements_lock_hash": "4" * 64,
    }
    baseline_key = runtime_api.compute_v025_streamlit_cache_key(base_dimensions)

    for domain_id in runtime_diff.DEPENDENCY_DOMAINS:
        changed_hashes = dict(baseline_hashes)
        changed_hashes[domain_id] = hashlib.sha256(
            f"opaque-dependency:{domain_id}:changed".encode("utf-8")
        ).hexdigest()
        changed = runtime_diff.build_dependency_snapshot_from_hashes(
            changed_hashes,
            PFI_ROOT,
        )
        report = runtime_diff.compare_dependency_snapshots(baseline, changed, registry)
        assert report["changed_domains"] == [domain_id]
        assert report["no_diff"] is False
        assert report["recompute_scope"] == "impacted_dependency_closure_only"
        assert report["network_calls"] == 0
        assert report["codex_calls"] == 0
        assert report["llm_calls"] == 0

        dimensions = dict(base_dimensions)
        dimensions["data_hash"] = changed["snapshot_hash"]
        dimensions["parameter_hash"] = changed_hashes["parameter"]
        dimensions["formula_hash"] = changed_hashes["formula"]
        dimensions["fx_snapshot_hash"] = changed_hashes["fx"]
        dimensions["read_model_hash"] = changed_hashes["read_model"]
        assert runtime_api.compute_v025_streamlit_cache_key(dimensions) != baseline_key

    raw_changed = dict(baseline_hashes)
    raw_changed["raw"] = hashlib.sha256(b"opaque-raw-changed").hexdigest()
    raw_report = runtime_diff.compare_dependency_snapshots(
        baseline,
        runtime_diff.build_dependency_snapshot_from_hashes(raw_changed, PFI_ROOT),
        registry,
    )
    assert raw_report["impacted_metrics"] == [
        "consumption_outflow_cny",
        "report_summary_status",
    ]
    assert raw_report["full_metric_recompute"] is False
    assert "net_worth_cny" in raw_report["not_impacted_metrics"]


def test_no_diff_means_no_recompute_network_codex_or_llm() -> None:
    registry = runtime_diff.load_dependency_registry(PFI_ROOT)
    snapshot = runtime_diff.build_dependency_snapshot_from_hashes(_opaque_hashes(), PFI_ROOT)
    report = runtime_diff.compare_dependency_snapshots(snapshot, snapshot, registry)
    assert report["no_diff"] is True
    assert report["changed_domains"] == []
    assert report["recompute_domains"] == []
    assert report["recompute_scope"] == "none"
    assert report["impacted_metrics"] == []
    assert report["invalidated_cache_scopes"] == []
    assert report["network_calls"] == 0
    assert report["codex_calls"] == 0
    assert report["llm_calls"] == 0


def test_cache_policy_binds_one_atomic_snapshot_to_streamlit_and_frontend() -> None:
    context = runtime_api.build_v025_release_cache_context(
        PFI_ROOT,
        read_model_status=_status_projection(),
        streamlit_version="1.35.0",
    )
    dimensions = context["dimensions"]
    snapshot = context["dependency_snapshot"]
    key = runtime_api.compute_v025_streamlit_cache_key(dimensions)
    policy = runtime_api.build_v025_release_cache_policy_record(
        dimensions,
        process_cache_key=key,
        running_backend_hash=dimensions["backend_build_hash"],
        asset_identity_valid=True,
        dependency_snapshot=snapshot,
    )
    assert policy["valid"] is True
    assert policy["dependency_snapshot_valid"] is True
    assert policy["data_hash"] == policy["dependency_snapshot_hash"]
    assert policy["dependency_hashes"] == snapshot["hashes"]
    assert policy["frontend_cache_key"] == policy["streamlit_cache_key"] == key
    assert policy["process_cache_key"] == key
    assert policy["ttl_seconds"] == 30
    assert policy["persistent"] is False
    assert policy["ordinary_run_network_allowed"] is False
    assert policy["no_diff_network_allowed"] is False
    assert policy["no_diff_recompute_scope"] == "none"


def test_frontend_validator_behavior_accepts_bound_policy_and_rejects_drift() -> None:
    node = shutil.which("node")
    assert node, "Node.js is required for the active frontend cache validator"
    context = runtime_api.build_v025_release_cache_context(
        PFI_ROOT,
        read_model_status=_status_projection(),
        streamlit_version="1.35.0",
    )
    dimensions = context["dimensions"]
    key = runtime_api.compute_v025_streamlit_cache_key(dimensions)
    policy = runtime_api.build_v025_release_cache_policy_record(
        dimensions,
        process_cache_key=key,
        running_backend_hash=dimensions["backend_build_hash"],
        asset_identity_valid=True,
        dependency_snapshot=context["dependency_snapshot"],
    )
    manifest = json.loads((PFI_ROOT / "config/release_manifest.json").read_text(encoding="utf-8"))
    script = f"""
import fs from "node:fs";
import vm from "node:vm";
const manifest = {json.dumps(manifest, ensure_ascii=False)};
const policy = {json.dumps(policy, ensure_ascii=False)};
const nodes = {{
  "pfi-release-manifest": {{ textContent: JSON.stringify(manifest) }},
  "pfi-runtime-config": {{ textContent: JSON.stringify({{ releaseManifestApi: false, releaseCachePolicyApi: false }}) }},
}};
const documentRef = {{
  body: {{ dataset: {{}} }},
  getElementById: (id) => nodes[id] || null,
  querySelector: () => null,
  referrer: "",
}};
globalThis.window = {{
  document: documentRef,
  location: {{ search: "", href: "http://127.0.0.1/" }},
  addEventListener: () => {{}},
}};
vm.runInThisContext(fs.readFileSync({json.dumps(str(PFI_ROOT / 'web/app/version.js'))}, "utf8"));
const validator = window.PFI_RELEASE_IDENTITY.validateReleaseCachePolicy;
const accepted = validator(policy, manifest);
if (!accepted.ok) throw new Error(`valid policy rejected: ${{accepted.issues.join(",")}}`);
const drifted = {{ ...policy, ordinary_run_network_allowed: true }};
const rejected = validator(drifted, manifest);
if (rejected.ok || !rejected.issues.includes("cache_policy:ordinary_run_network:must_be_false")) {{
  throw new Error("frontend validator accepted ordinary-run network drift");
}}
process.stdout.write(JSON.stringify({{ accepted: accepted.ok, rejected: !rejected.ok }}));
"""
    completed = subprocess.run(
        [node, "--input-type=module", "--eval", script],
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(completed.stdout) == {"accepted": True, "rejected": True}


def test_ordinary_runtime_snapshot_performs_zero_network_calls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: list[tuple[object, ...]] = []

    def forbidden_socket(*args: object, **_kwargs: object) -> object:
        observed.append(args)
        raise AssertionError("ordinary Phase 10.2 runtime attempted network access")

    monkeypatch.setattr(socket, "socket", forbidden_socket)
    snapshot = runtime_diff.build_dependency_snapshot(
        PFI_ROOT,
        read_model_status=_status_projection(),
    )
    audit = runtime_diff.build_ordinary_run_network_audit(
        observed_network_calls=len(observed)
    )
    assert snapshot["network_calls"] == 0
    assert observed == []
    assert audit == {
        "schema": "PFIV025OrdinaryRunNetworkAuditV1",
        "mode": "ordinary_local_runtime_diff_and_cache_identity",
        "network_allowed": False,
        "observed_network_calls": 0,
        "codex_calls": 0,
        "llm_calls": 0,
        "status": "pass",
    }

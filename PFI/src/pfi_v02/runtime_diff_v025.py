from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from pathlib import Path
from typing import Any, Iterable, Mapping


DEPENDENCY_REGISTRY_SCHEMA = "PFIV025DependencyRegistryV1"
DEPENDENCY_SNAPSHOT_SCHEMA = "PFIV025DependencySnapshotV1"
RUNTIME_DIFF_SCHEMA = "PFIV025RuntimeDiffV1"
NETWORK_AUDIT_SCHEMA = "PFIV025OrdinaryRunNetworkAuditV1"
DEPENDENCY_DOMAINS = (
    "raw",
    "source",
    "ledger",
    "interconnection",
    "parameter",
    "formula",
    "fx",
    "read_model",
    "report",
)
METRIC_UNIVERSE = (
    "cash_balance_cny",
    "consumption_outflow_cny",
    "investment_market_value_cny",
    "net_worth_cny",
    "report_summary_status",
)
CACHE_SCOPES = (
    "frontend_read_model",
    "report_render",
    "streamlit_read_model",
)
REGISTRY_RELATIVE_PATH = Path("config/jobs/v025_dependency_registry.json")
PARAMETER_RELATIVE_PATH = Path("config/pfi_parameters.yaml")
FORMULA_RELATIVE_PATH = Path("config/formulas/v025_formula_registry.json")
REPORT_RELATIVE_PATH = Path("config/reports/v025_stage9_reviewed_analysis_snapshot.json")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
_OBSERVATION_FIELDS = frozenset({"hash", "status", "provenance", "record_count", "snapshot_id"})


def canonical_json_sha256(payload: Any) -> str:
    raw = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _project_root(project_root: Path | str | None = None) -> Path:
    return (
        Path(project_root).expanduser().resolve()
        if project_root is not None
        else Path(__file__).resolve().parents[2]
    )


def _require_hex64(value: object, label: str) -> str:
    candidate = str(value or "")
    if not HEX64.fullmatch(candidate):
        raise ValueError(f"{label} must be a lowercase 64-character SHA-256")
    return candidate


def load_dependency_registry(
    project_root: Path | str | None = None,
) -> dict[str, Any]:
    root = _project_root(project_root)
    path = root / REGISTRY_RELATIVE_PATH
    try:
        raw = path.read_bytes()
        payload = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("v0.2.5 dependency registry is unavailable or invalid") from exc
    if not isinstance(payload, dict) or payload.get("schema") != DEPENDENCY_REGISTRY_SCHEMA:
        raise ValueError("v0.2.5 dependency registry schema is invalid")
    if payload.get("ordinary_run_network_allowed") is not False:
        raise ValueError("ordinary-run network access must be disabled")
    cache = payload.get("cache_contract")
    if not isinstance(cache, dict):
        raise ValueError("dependency registry cache contract is required")
    required_cache_contract = {
        "ttl_seconds": 30,
        "persistent": False,
        "invalidation_mode": "composite_dependency_snapshot_hash",
        "no_diff_recompute_scope": "none",
        "no_diff_network_allowed": False,
        "no_diff_codex_allowed": False,
        "no_diff_llm_allowed": False,
    }
    for key, expected in required_cache_contract.items():
        if cache.get(key) != expected:
            raise ValueError(f"dependency registry cache contract {key} is invalid")

    raw_domains = payload.get("domains")
    if not isinstance(raw_domains, list):
        raise ValueError("dependency registry domains are required")
    if [row.get("domain_id") for row in raw_domains if isinstance(row, dict)] != list(
        DEPENDENCY_DOMAINS
    ):
        raise ValueError("dependency registry must declare the canonical nine domains in order")

    domain_ids = set(DEPENDENCY_DOMAINS)
    metric_ids = set(METRIC_UNIVERSE)
    cache_scopes = set(CACHE_SCOPES)
    by_id: dict[str, dict[str, Any]] = {}
    for row in raw_domains:
        if not isinstance(row, dict):
            raise ValueError("dependency registry domain must be an object")
        domain_id = str(row.get("domain_id") or "")
        upstream = row.get("upstream")
        impacted = row.get("impacted_metrics")
        scopes = row.get("cache_scopes")
        provenance = row.get("provenance")
        if not isinstance(upstream, list) or len(upstream) != len(set(upstream)):
            raise ValueError(f"dependency registry {domain_id} upstream is invalid")
        if any(item not in domain_ids or item == domain_id for item in upstream):
            raise ValueError(f"dependency registry {domain_id} upstream is invalid")
        if not isinstance(impacted, list) or not impacted or len(impacted) != len(set(impacted)):
            raise ValueError(f"dependency registry {domain_id} metric impact is invalid")
        if any(item not in metric_ids for item in impacted):
            raise ValueError(f"dependency registry {domain_id} metric impact is unknown")
        if not isinstance(scopes, list) or not scopes or len(scopes) != len(set(scopes)):
            raise ValueError(f"dependency registry {domain_id} cache scopes are invalid")
        if any(item not in cache_scopes for item in scopes):
            raise ValueError(f"dependency registry {domain_id} cache scope is unknown")
        if not isinstance(provenance, str) or not provenance:
            raise ValueError(f"dependency registry {domain_id} provenance is required")
        by_id[domain_id] = dict(row)

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(domain_id: str) -> None:
        if domain_id in visiting:
            raise ValueError("dependency registry must be acyclic")
        if domain_id in visited:
            return
        visiting.add(domain_id)
        for upstream_id in by_id[domain_id]["upstream"]:
            visit(str(upstream_id))
        visiting.remove(domain_id)
        visited.add(domain_id)

    for domain_id in DEPENDENCY_DOMAINS:
        visit(domain_id)

    result = dict(payload)
    result["registry_sha256"] = hashlib.sha256(raw).hexdigest()
    result["domain_map"] = by_id
    return result


def _state_observation(domain_id: str, state: str, provenance: str) -> dict[str, Any]:
    return {
        "hash": canonical_json_sha256(
            {"domain_id": domain_id, "state": state, "contract": "pfi-v0.2.5-stage10-p10.2"}
        ),
        "status": state,
        "provenance": provenance,
        "record_count": 0,
    }


def _file_observation(path: Path, *, domain_id: str, provenance: str) -> dict[str, Any]:
    if not path.is_file():
        return _state_observation(domain_id, "not_loaded", provenance)
    return {
        "hash": hashlib.sha256(path.read_bytes()).hexdigest(),
        "status": "ready",
        "provenance": provenance,
        "record_count": 1,
    }


def _table_names(connection: sqlite3.Connection) -> set[str]:
    return {
        str(row[0])
        for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    }


def _row_projection_hash(rows: Iterable[sqlite3.Row]) -> tuple[str, int]:
    record_hashes: list[str] = []
    for row in rows:
        record_hashes.append(canonical_json_sha256([str(value or "") for value in tuple(row)]))
    record_hashes.sort()
    return canonical_json_sha256(record_hashes), len(record_hashes)


def _observe_sqlite_dependencies(
    db_path: Path,
    domain_map: Mapping[str, Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    if not db_path.is_file():
        return {
            domain_id: _state_observation(
                domain_id,
                "not_loaded",
                str(domain_map[domain_id]["provenance"]),
            )
            for domain_id in ("raw", "source", "ledger")
        }
    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(f"{db_path.resolve().as_uri()}?mode=ro", uri=True)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only = ON")
        connection.execute("BEGIN")
        tables = _table_names(connection)
        observations: dict[str, dict[str, Any]] = {}
        if "import_files" not in tables:
            observations["raw"] = _state_observation(
                "raw", "schema_unavailable", str(domain_map["raw"]["provenance"])
            )
            observations["source"] = _state_observation(
                "source", "schema_unavailable", str(domain_map["source"]["provenance"])
            )
        else:
            raw_hash, raw_count = _row_projection_hash(
                connection.execute(
                    "SELECT content_sha256 FROM import_files ORDER BY content_sha256"
                )
            )
            source_hash, source_count = _row_projection_hash(
                connection.execute(
                    """
                    SELECT content_sha256, COALESCE(source_id, ''),
                           COALESCE(parser_version, ''), status
                    FROM import_files
                    ORDER BY content_sha256, source_id, parser_version, status
                    """
                )
            )
            observations["raw"] = {
                "hash": raw_hash,
                "status": "ready" if raw_count else "not_loaded",
                "provenance": str(domain_map["raw"]["provenance"]),
                "record_count": raw_count,
            }
            observations["source"] = {
                "hash": source_hash,
                "status": "ready" if source_count else "not_loaded",
                "provenance": str(domain_map["source"]["provenance"]),
                "record_count": source_count,
            }
        if "ledger_entries" not in tables:
            observations["ledger"] = _state_observation(
                "ledger", "schema_unavailable", str(domain_map["ledger"]["provenance"])
            )
        else:
            ledger_hash, ledger_count = _row_projection_hash(
                connection.execute(
                    """
                    SELECT ledger_entry_id, batch_id, transaction_id, source_id,
                           event_type, occurred_at, ledger_state, category, updated_at
                    FROM ledger_entries
                    ORDER BY ledger_entry_id
                    """
                )
            )
            observations["ledger"] = {
                "hash": ledger_hash,
                "status": "ready" if ledger_count else "not_loaded",
                "provenance": str(domain_map["ledger"]["provenance"]),
                "record_count": ledger_count,
            }
        return observations
    except sqlite3.Error:
        return {
            domain_id: _state_observation(
                domain_id,
                "unavailable",
                str(domain_map[domain_id]["provenance"]),
            )
            for domain_id in ("raw", "source", "ledger")
        }
    finally:
        if connection is not None:
            try:
                connection.rollback()
            finally:
                connection.close()


def _status_projection_observations(
    read_model_status: Mapping[str, Any] | None,
    domain_map: Mapping[str, Mapping[str, Any]],
    *,
    isolated_candidate: bool,
) -> dict[str, dict[str, Any]]:
    if isolated_candidate:
        return {
            domain_id: _state_observation(
                domain_id,
                "isolated_empty",
                str(domain_map[domain_id]["provenance"]),
            )
            for domain_id in ("raw", "source", "ledger")
        }
    status = read_model_status if isinstance(read_model_status, Mapping) else {}
    source = status.get("source") if isinstance(status.get("source"), Mapping) else {}
    projection = {
        "status": source.get("status"),
        "evidence_hash": source.get("evidence_hash"),
        "as_of": source.get("as_of"),
        "record_count": source.get("record_count"),
        "raw_file_count": source.get("raw_file_count"),
    }
    source_hash = canonical_json_sha256(projection)
    return {
        "raw": {
            "hash": canonical_json_sha256(
                {"evidence_hash": projection["evidence_hash"], "raw_file_count": projection["raw_file_count"]}
            ),
            "status": str(source.get("status") or "not_loaded"),
            "provenance": str(domain_map["raw"]["provenance"]),
            "record_count": int(source.get("raw_file_count") or 0),
        },
        "source": {
            "hash": source_hash,
            "status": str(source.get("status") or "not_loaded"),
            "provenance": str(domain_map["source"]["provenance"]),
            "record_count": int(source.get("record_count") or 0),
        },
        "ledger": {
            "hash": canonical_json_sha256(
                {"source_projection_hash": source_hash, "authority": status.get("contract_version")}
            ),
            "status": str(source.get("status") or "not_loaded"),
            "provenance": str(domain_map["ledger"]["provenance"]),
            "record_count": int(source.get("record_count") or 0),
        },
    }


def _latest_fx_observation(
    project_root: Path,
    provenance: str,
    *,
    isolated_candidate: bool,
) -> dict[str, Any]:
    if isolated_candidate:
        return _state_observation("fx", "isolated_empty", provenance)
    candidates: list[tuple[str, str, Path]] = []
    for path in project_root.glob("data/fx_snapshots/*/*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict):
            continue
        snapshot_id = str(payload.get("snapshot_id") or "")
        if snapshot_id:
            candidates.append((str(payload.get("effective_date") or ""), snapshot_id, path))
    if not candidates:
        return _state_observation("fx", "not_loaded", provenance)
    _effective_date, snapshot_id, path = max(
        candidates, key=lambda item: (item[0], item[1], item[2].as_posix())
    )
    return {
        "hash": hashlib.sha256(path.read_bytes()).hexdigest(),
        "status": "ready",
        "provenance": provenance,
        "record_count": 1,
        "snapshot_id": snapshot_id,
    }


def _read_model_observation(
    read_model_status: Mapping[str, Any] | None,
    upstream_hashes: Mapping[str, str],
    provenance: str,
) -> dict[str, Any]:
    status = read_model_status if isinstance(read_model_status, Mapping) else {}
    candidate = str(status.get("read_model_hash") or "").removeprefix("sha256:")
    if HEX64.fullmatch(candidate):
        read_model_hash = candidate
        observation_status = str(status.get("source", {}).get("status") or "ready") if isinstance(
            status.get("source"), Mapping
        ) else "ready"
    else:
        read_model_hash = canonical_json_sha256(
            {
                "contract": "PFI-V025-STAGE7-DEPENDENCY-IDENTITY",
                "upstream_hashes": {
                    domain_id: upstream_hashes[domain_id]
                    for domain_id in ("interconnection", "parameter", "formula", "fx")
                },
            }
        )
        observation_status = "dependency_identity"
    return {
        "hash": read_model_hash,
        "status": observation_status,
        "provenance": provenance,
        "record_count": 1,
    }


def build_dependency_snapshot_from_observations(
    observations: Mapping[str, Mapping[str, Any]],
    registry: Mapping[str, Any],
) -> dict[str, Any]:
    if set(observations) != set(DEPENDENCY_DOMAINS):
        raise ValueError("dependency observations must contain the canonical nine domains")
    registry_hash = _require_hex64(registry.get("registry_sha256"), "registry_sha256")
    sanitized: dict[str, dict[str, Any]] = {}
    hashes: dict[str, str] = {}
    for domain_id in DEPENDENCY_DOMAINS:
        raw = observations[domain_id]
        if not isinstance(raw, Mapping) or set(raw) - _OBSERVATION_FIELDS:
            raise ValueError(f"dependency observation {domain_id} contains unsupported fields")
        digest = _require_hex64(raw.get("hash"), f"dependency {domain_id} hash")
        status = str(raw.get("status") or "")
        provenance = str(raw.get("provenance") or "")
        if not status or not provenance:
            raise ValueError(f"dependency observation {domain_id} is incomplete")
        record_count = int(raw.get("record_count") or 0)
        if record_count < 0:
            raise ValueError(f"dependency observation {domain_id} record count is invalid")
        row: dict[str, Any] = {
            "hash": digest,
            "status": status,
            "provenance": provenance,
            "record_count": record_count,
        }
        if raw.get("snapshot_id") is not None:
            row["snapshot_id"] = str(raw.get("snapshot_id") or "")
        sanitized[domain_id] = row
        hashes[domain_id] = digest
    identity = {
        "schema": DEPENDENCY_SNAPSHOT_SCHEMA,
        "registry_sha256": registry_hash,
        "hashes": hashes,
    }
    return {
        **identity,
        "snapshot_hash": canonical_json_sha256(identity),
        "observations": sanitized,
        "contains_private_values": False,
        "financial_values_emitted": 0,
        "network_calls": 0,
    }


def build_dependency_snapshot(
    project_root: Path | str | None = None,
    *,
    read_model_status: Mapping[str, Any] | None = None,
    db_path: Path | str | None = None,
    isolated_candidate: bool = False,
) -> dict[str, Any]:
    root = _project_root(project_root)
    registry = load_dependency_registry(root)
    domain_map = registry["domain_map"]
    if isolated_candidate or db_path is None:
        observations = _status_projection_observations(
            read_model_status,
            domain_map,
            isolated_candidate=isolated_candidate,
        )
    else:
        observations = _observe_sqlite_dependencies(Path(db_path).expanduser(), domain_map)
    observations["interconnection"] = {
        "hash": canonical_json_sha256(
            {
                "status": "blocked_economic_event_adapter",
                "ledger_hash": observations["ledger"]["hash"],
            }
        ),
        "status": "blocked_economic_event_adapter",
        "provenance": str(domain_map["interconnection"]["provenance"]),
        "record_count": int(observations["ledger"]["record_count"]),
    }
    observations["parameter"] = _file_observation(
        root / PARAMETER_RELATIVE_PATH,
        domain_id="parameter",
        provenance=str(domain_map["parameter"]["provenance"]),
    )
    observations["formula"] = _file_observation(
        root / FORMULA_RELATIVE_PATH,
        domain_id="formula",
        provenance=str(domain_map["formula"]["provenance"]),
    )
    observations["fx"] = _latest_fx_observation(
        root,
        str(domain_map["fx"]["provenance"]),
        isolated_candidate=isolated_candidate,
    )
    observations["read_model"] = _read_model_observation(
        read_model_status,
        {domain_id: str(row["hash"]) for domain_id, row in observations.items()},
        str(domain_map["read_model"]["provenance"]),
    )
    observations["report"] = _file_observation(
        root / REPORT_RELATIVE_PATH,
        domain_id="report",
        provenance=str(domain_map["report"]["provenance"]),
    )
    return build_dependency_snapshot_from_observations(observations, registry)


def build_dependency_snapshot_from_hashes(
    hashes: Mapping[str, str],
    project_root: Path | str | None = None,
) -> dict[str, Any]:
    registry = load_dependency_registry(project_root)
    observations = {
        domain_id: {
            "hash": _require_hex64(hashes.get(domain_id), f"dependency {domain_id} hash"),
            "status": "prehashed_observation",
            "provenance": str(registry["domain_map"][domain_id]["provenance"]),
            "record_count": 0,
        }
        for domain_id in DEPENDENCY_DOMAINS
    }
    return build_dependency_snapshot_from_observations(observations, registry)


def _validate_snapshot(snapshot: Mapping[str, Any]) -> dict[str, str]:
    if not isinstance(snapshot, Mapping) or snapshot.get("schema") != DEPENDENCY_SNAPSHOT_SCHEMA:
        raise ValueError("dependency snapshot schema is invalid")
    registry_hash = _require_hex64(snapshot.get("registry_sha256"), "registry_sha256")
    hashes = snapshot.get("hashes")
    if not isinstance(hashes, Mapping) or set(hashes) != set(DEPENDENCY_DOMAINS):
        raise ValueError("dependency snapshot hashes are incomplete")
    normalized = {
        domain_id: _require_hex64(hashes.get(domain_id), f"dependency {domain_id} hash")
        for domain_id in DEPENDENCY_DOMAINS
    }
    expected = canonical_json_sha256(
        {
            "schema": DEPENDENCY_SNAPSHOT_SCHEMA,
            "registry_sha256": registry_hash,
            "hashes": normalized,
        }
    )
    if snapshot.get("snapshot_hash") != expected:
        raise ValueError("dependency snapshot hash is invalid")
    return normalized


def compare_dependency_snapshots(
    previous: Mapping[str, Any],
    current: Mapping[str, Any],
    registry: Mapping[str, Any],
) -> dict[str, Any]:
    previous_hashes = _validate_snapshot(previous)
    current_hashes = _validate_snapshot(current)
    registry_hash = _require_hex64(registry.get("registry_sha256"), "registry_sha256")
    registry_changed = (
        previous.get("registry_sha256") != current.get("registry_sha256")
        or current.get("registry_sha256") != registry_hash
    )
    changed_domains = [
        domain_id
        for domain_id in DEPENDENCY_DOMAINS
        if registry_changed or previous_hashes[domain_id] != current_hashes[domain_id]
    ]
    changed_set = set(changed_domains)
    domain_map = registry.get("domain_map")
    if not isinstance(domain_map, Mapping):
        raise ValueError("dependency registry domain map is unavailable")

    downstream: dict[str, set[str]] = {domain_id: set() for domain_id in DEPENDENCY_DOMAINS}
    for domain_id in DEPENDENCY_DOMAINS:
        for upstream_id in domain_map[domain_id]["upstream"]:
            downstream[str(upstream_id)].add(domain_id)
    recompute_set = set(changed_set)
    queue = list(changed_domains)
    while queue:
        current_id = queue.pop(0)
        for downstream_id in sorted(downstream[current_id]):
            if downstream_id not in recompute_set:
                recompute_set.add(downstream_id)
                queue.append(downstream_id)

    impacted_metrics = sorted(
        {
            str(metric_id)
            for domain_id in changed_domains
            for metric_id in domain_map[domain_id]["impacted_metrics"]
        }
    )
    impacted_scopes = sorted(
        {
            str(scope)
            for domain_id in recompute_set
            for scope in domain_map[domain_id]["cache_scopes"]
        }
    )
    no_diff = not changed_domains
    return {
        "schema": RUNTIME_DIFF_SCHEMA,
        "registry_sha256": registry_hash,
        "previous_snapshot_hash": str(previous.get("snapshot_hash") or ""),
        "current_snapshot_hash": str(current.get("snapshot_hash") or ""),
        "registry_changed": registry_changed,
        "no_diff": no_diff,
        "changed_domains": changed_domains,
        "unchanged_domains": [
            domain_id for domain_id in DEPENDENCY_DOMAINS if domain_id not in changed_set
        ],
        "recompute_domains": []
        if no_diff
        else [domain_id for domain_id in DEPENDENCY_DOMAINS if domain_id in recompute_set],
        "recompute_scope": "none" if no_diff else "impacted_dependency_closure_only",
        "impacted_metrics": impacted_metrics,
        "not_impacted_metrics": [
            metric_id for metric_id in METRIC_UNIVERSE if metric_id not in set(impacted_metrics)
        ],
        "invalidated_cache_scopes": impacted_scopes,
        "full_metric_recompute": bool(impacted_metrics)
        and set(impacted_metrics) == set(METRIC_UNIVERSE),
        "ordinary_run_network_allowed": False,
        "network_calls": 0,
        "codex_calls": 0,
        "llm_calls": 0,
        "explanations": [
            {
                "domain_id": domain_id,
                "previous_hash": previous_hashes[domain_id],
                "current_hash": current_hashes[domain_id],
                "direct_impacted_metrics": list(domain_map[domain_id]["impacted_metrics"]),
            }
            for domain_id in changed_domains
        ],
    }


def build_ordinary_run_network_audit(*, observed_network_calls: int = 0) -> dict[str, Any]:
    calls = int(observed_network_calls)
    if calls < 0:
        raise ValueError("observed network call count cannot be negative")
    return {
        "schema": NETWORK_AUDIT_SCHEMA,
        "mode": "ordinary_local_runtime_diff_and_cache_identity",
        "network_allowed": False,
        "observed_network_calls": calls,
        "codex_calls": 0,
        "llm_calls": 0,
        "status": "pass" if calls == 0 else "fail",
    }

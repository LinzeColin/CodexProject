#!/usr/bin/env python3
"""Preview or transactionally apply an EEI model configuration.

The command is fail-closed:

* ``--dry-run`` validates files and writes a deterministic review artifact.
* ``--execute`` requires a PostgreSQL URL and delegates writes to the existing
  DomainRepository transaction methods.
* Omitting both modes writes a refused artifact and exits non-zero.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol
from uuid import UUID

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PREVIEW_OUTPUT = ROOT / "artifacts/model_config_import_preview.json"
DEFAULT_EXECUTION_OUTPUT = ROOT / "artifacts/tests/a204/t1303_model_config_apply_contract.json"
APPLY_SCHEMA_VERSION = "eei-model-config-apply-contract-v1"
ACCEPTANCE_IDS = ["A204", "A205"]
TASK_IDS = ["T1303"]
DEFAULT_AFFECTED_MODULES = [
    "business_empire",
    "group_structure",
    "business_segments",
    "supply_chain",
    "capital_network",
    "ma_transactions",
    "control_relationships",
    "policy_environment",
    "strategic_signals",
    "watchlist",
    "evidence_center",
    "model_center",
    "data_center",
]


class ModelConfigRepository(Protocol):
    def get_active_analysis_context(
        self,
        *,
        client_refresh_token: str | None = None,
    ) -> dict[str, Any]:
        ...

    def create_scoring_profile_version(
        self,
        *,
        base_profile_version_id: UUID | None,
        profile_key: str,
        name: str,
        weights: dict[str, Any] | None,
        thresholds: dict[str, Any] | None,
        half_lives_days: dict[str, int] | None,
        missing_value_policy: str,
        reason: str,
        actor: str = "local_user",
    ) -> dict[str, Any]:
        ...

    def activate_scoring_profile_version(
        self,
        *,
        profile_version_id: UUID,
        expected_active_profile_version_id: UUID | None,
        client_refresh_token: str | None,
        reason: str,
        actor: str = "local_user",
        action_type: str = "activate_scoring_profile",
    ) -> dict[str, Any]:
        ...

    def enqueue_score_recompute(
        self,
        *,
        expected_active_profile_version_id: UUID | None,
        client_refresh_token: str | None,
        scope: str,
        reason: str,
        actor: str = "local_user",
    ) -> dict[str, Any]:
        ...


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonical_hash(value: object) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def validate_model_config(profile_path: Path, thresholds_path: Path) -> None:
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/validate_model_config.py"),
            str(profile_path),
            str(thresholds_path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
    )


def build_base_contract(
    *,
    profile_path: Path,
    thresholds_path: Path,
    profile: dict[str, Any],
    thresholds: dict[str, Any],
    reason: str,
    mode: str,
    generated_at: str | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": APPLY_SCHEMA_VERSION,
        "artifact_id": "t1303-model-config-apply-contract",
        "generated_at": generated_at or utc_now(),
        "system_name": "EEI",
        "system_en_name": "Enterprise Ecosystem Intelligence",
        "system_zh_name": "商域图谱",
        "task_ids": TASK_IDS,
        "acceptance_ids": ACCEPTANCE_IDS,
        "mode": mode,
        "reason": reason,
        "profile_path": str(profile_path),
        "thresholds_path": str(thresholds_path),
        "profile_key": profile["profile_key"],
        "profile_version": profile["version"],
        "threshold_profile_key": thresholds["threshold_profile_key"],
        "threshold_version": thresholds["version"],
        "profile_sha256": canonical_hash(profile),
        "thresholds_sha256": canonical_hash(thresholds),
        "affected_modules": DEFAULT_AFFECTED_MODULES,
        "expected_flow": [
            "validate",
            "preview",
            "save immutable draft version",
            "append operation log",
            "atomic activate",
            "write transactional outbox event",
            "invalidate global refresh token",
            "queue score recomputation",
        ],
        "release_gate_closed_by_apply_model_config": False,
        "non_closure": [
            "does_not_close_A202_source_legal_owner_approval",
            "does_not_close_A209_24h_operator_soak",
            "does_not_close_A210_brand_clearance",
            "does_not_close_A026_A027_production_gold_quality",
        ],
    }


def build_refused_contract(
    *,
    profile_path: Path,
    thresholds_path: Path,
    profile: dict[str, Any],
    thresholds: dict[str, Any],
    reason: str,
    generated_at: str | None = None,
) -> dict[str, Any]:
    payload = build_base_contract(
        profile_path=profile_path,
        thresholds_path=thresholds_path,
        profile=profile,
        thresholds=thresholds,
        reason=reason,
        mode="refused",
        generated_at=generated_at,
    )
    payload.update(
        {
            "status": "REFUSED",
            "refusal_reason": (
                "pass --dry-run for preview or --execute with DATABASE_URL for "
                "PostgreSQL activation"
            ),
            "database_write_attempted": False,
            "activation_attempted": False,
        }
    )
    return payload


def build_preview_contract(
    *,
    profile_path: Path,
    thresholds_path: Path,
    profile: dict[str, Any],
    thresholds: dict[str, Any],
    reason: str,
    generated_at: str | None = None,
) -> dict[str, Any]:
    payload = build_base_contract(
        profile_path=profile_path,
        thresholds_path=thresholds_path,
        profile=profile,
        thresholds=thresholds,
        reason=reason,
        mode="dry-run",
        generated_at=generated_at,
    )
    payload.update(
        {
            "status": "DRY_RUN_READY",
            "database_write_attempted": False,
            "activation_attempted": False,
            "operator_next_step": (
                "Run the same command with --execute and DATABASE_URL after reviewing "
                "profile/threshold hashes."
            ),
        }
    )
    return payload


def repository_from_database_url(database_url: str | None) -> ModelConfigRepository:
    if not database_url:
        raise RuntimeError("DATABASE_URL or --database-url is required with --execute")
    from apps.api.app.domain_repository import DomainRepository

    return DomainRepository(database_url)


def uuid_or_none(value: str | None) -> UUID | None:
    return UUID(value) if value else None


def execute_model_config(
    *,
    repository: ModelConfigRepository,
    profile_path: Path,
    thresholds_path: Path,
    profile: dict[str, Any],
    thresholds: dict[str, Any],
    reason: str,
    actor: str,
    expected_active_profile_version_id: UUID | None = None,
    client_refresh_token: str | None = None,
    queue_score_recompute: bool = True,
    recompute_scope: str = "global",
    generated_at: str | None = None,
) -> dict[str, Any]:
    active_context = repository.get_active_analysis_context(
        client_refresh_token=client_refresh_token,
    )
    base_profile_id = UUID(str(active_context["active_scoring_profile_version_id"]))
    expected_profile_id = expected_active_profile_version_id or base_profile_id
    expected_refresh_token = client_refresh_token or str(active_context["refresh_token"])

    draft = repository.create_scoring_profile_version(
        base_profile_version_id=base_profile_id,
        profile_key=str(profile["profile_key"]),
        name=str(profile["name"]),
        weights=dict(profile["weights"]),
        thresholds=thresholds,
        half_lives_days=dict(profile["half_life_days"]),
        missing_value_policy=str(profile["missing_value_policy"]),
        reason=reason,
        actor=actor,
    )
    draft_profile_id = UUID(str(draft["profile"]["id"]))
    activation = repository.activate_scoring_profile_version(
        profile_version_id=draft_profile_id,
        expected_active_profile_version_id=expected_profile_id,
        client_refresh_token=expected_refresh_token,
        reason=reason,
        actor=actor,
    )

    recompute: dict[str, Any] | None = None
    if queue_score_recompute:
        recompute = repository.enqueue_score_recompute(
            expected_active_profile_version_id=draft_profile_id,
            client_refresh_token=str(activation["cache_invalidation"]["refresh_token"]),
            scope=recompute_scope,
            reason=reason,
            actor=actor,
        )

    payload = build_base_contract(
        profile_path=profile_path,
        thresholds_path=thresholds_path,
        profile=profile,
        thresholds=thresholds,
        reason=reason,
        mode="execute",
        generated_at=generated_at,
    )
    payload.update(
        {
            "status": "APPLIED",
            "database_write_attempted": True,
            "activation_attempted": True,
            "actor": actor,
            "base_active_profile_version_id": str(base_profile_id),
            "draft_profile_version_id": str(draft_profile_id),
            "activation": {
                "schema_version": activation.get("schema_version"),
                "status": activation.get("status"),
                "previous_profile_id": activation.get("previous_profile", {}).get("id"),
                "activated_profile_id": activation.get("activated_profile", {}).get("id"),
                "previous_refresh_token": activation.get("cache_invalidation", {}).get(
                    "previous_refresh_token"
                ),
                "refresh_token": activation.get("cache_invalidation", {}).get("refresh_token"),
                "refresh_generation": activation.get("cache_invalidation", {}).get(
                    "refresh_generation"
                ),
                "outbox_event_type": activation.get("outbox_event", {}).get("event_type"),
                "outbox_event_status": activation.get("outbox_event", {}).get("status"),
            },
            "score_recompute": (
                None
                if recompute is None
                else {
                    "schema_version": recompute.get("schema_version"),
                    "status": recompute.get("status"),
                    "job_id": recompute.get("job", {}).get("id"),
                    "job_status": recompute.get("job", {}).get("status"),
                    "idempotency_key": recompute.get("idempotency_key"),
                    "outbox_event_type": recompute.get("outbox_event", {}).get(
                        "event_type"
                    ),
                    "outbox_event_status": recompute.get("outbox_event", {}).get("status"),
                    "refresh_token": recompute.get("cache_policy", {}).get("refresh_token"),
                    "refresh_generation": recompute.get("cache_policy", {}).get(
                        "refresh_generation"
                    ),
                }
            ),
            "operator_next_step": (
                "Run apps.worker supervisor/once to execute queued score recompute, then "
                "confirm active_analysis_context refresh_generation advanced."
            )
            if queue_score_recompute
            else "Score recompute enqueue was skipped by operator flag.",
        }
    )
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--thresholds", required=True, type=Path)
    parser.add_argument("--reason", default="model config activation review")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--execute", action="store_true")
    parser.add_argument("--database-url", default=os.getenv("DATABASE_URL"))
    parser.add_argument("--actor", default="local_operator")
    parser.add_argument("--expected-active-profile-version-id")
    parser.add_argument("--client-refresh-token")
    parser.add_argument("--skip-score-recompute", action="store_true")
    parser.add_argument(
        "--recompute-scope",
        choices=["global", "active_workspace"],
        default="global",
    )
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    profile_path = args.profile
    thresholds_path = args.thresholds
    validate_model_config(profile_path, thresholds_path)
    profile = read_json(profile_path)
    thresholds = read_json(thresholds_path)

    if args.dry_run:
        payload = build_preview_contract(
            profile_path=profile_path,
            thresholds_path=thresholds_path,
            profile=profile,
            thresholds=thresholds,
            reason=args.reason,
        )
        output = args.output or DEFAULT_PREVIEW_OUTPUT
        write_json(output, payload)
        print(output)
        return 0

    if not args.execute:
        payload = build_refused_contract(
            profile_path=profile_path,
            thresholds_path=thresholds_path,
            profile=profile,
            thresholds=thresholds,
            reason=args.reason,
        )
        output = args.output or DEFAULT_PREVIEW_OUTPUT
        write_json(output, payload)
        print(
            "REFUSED: pass --dry-run for preview or --execute with DATABASE_URL for "
            "PostgreSQL activation.",
            file=sys.stderr,
        )
        print(output)
        return 3

    try:
        repository = repository_from_database_url(args.database_url)
        payload = execute_model_config(
            repository=repository,
            profile_path=profile_path,
            thresholds_path=thresholds_path,
            profile=profile,
            thresholds=thresholds,
            reason=args.reason,
            actor=args.actor,
            expected_active_profile_version_id=uuid_or_none(
                args.expected_active_profile_version_id
            ),
            client_refresh_token=args.client_refresh_token,
            queue_score_recompute=not args.skip_score_recompute,
            recompute_scope=args.recompute_scope,
        )
    except Exception as exc:
        failure = build_base_contract(
            profile_path=profile_path,
            thresholds_path=thresholds_path,
            profile=profile,
            thresholds=thresholds,
            reason=args.reason,
            mode="execute",
        )
        failure.update(
            {
                "status": "FAILED",
                "database_write_attempted": True,
                "activation_attempted": True,
                "error_type": exc.__class__.__name__,
                "error": str(exc),
                "rollback": (
                    "Repository transaction methods are responsible for rolling back "
                    "failed create/activate/enqueue operations."
                ),
            }
        )
        output = args.output or DEFAULT_EXECUTION_OUTPUT
        write_json(output, failure)
        print(output)
        print(f"FAILED: {exc}", file=sys.stderr)
        return 2

    output = args.output or DEFAULT_EXECUTION_OUTPUT
    write_json(output, payload)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

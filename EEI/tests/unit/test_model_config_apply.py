from __future__ import annotations

from uuid import UUID

from scripts import apply_model_config

ROOT = apply_model_config.ROOT
PROFILE_PATH = ROOT / "config/model_profiles/supply-chain-v3.json"
THRESHOLDS_PATH = ROOT / "config/thresholds/default-v2.json"


class FakeModelConfigRepository:
    def __init__(self) -> None:
        self.active_id = UUID("00000000-0000-0000-0000-000000000001")
        self.draft_id = UUID("00000000-0000-0000-0000-000000000002")
        self.calls: list[str] = []

    def get_active_analysis_context(
        self,
        *,
        client_refresh_token: str | None = None,
    ) -> dict:
        self.calls.append("active_context")
        return {
            "active_scoring_profile_version_id": str(self.active_id),
            "refresh_token": client_refresh_token or "refresh-token-1",
            "refresh_generation": 1,
        }

    def create_scoring_profile_version(self, **kwargs: object) -> dict:
        self.calls.append("create_draft")
        assert kwargs["base_profile_version_id"] == self.active_id
        assert kwargs["profile_key"] == "supply-chain-v3"
        assert kwargs["actor"] == "model-owner"
        assert kwargs["missing_value_policy"] == "renormalize_available"
        assert isinstance(kwargs["thresholds"], dict)
        return {
            "schema_version": "scoring-profile-draft-v1",
            "status": "created",
            "profile": {"id": str(self.draft_id), "profile_key": "supply-chain-v3"},
        }

    def activate_scoring_profile_version(self, **kwargs: object) -> dict:
        self.calls.append("activate")
        assert kwargs["profile_version_id"] == self.draft_id
        assert kwargs["expected_active_profile_version_id"] == self.active_id
        assert kwargs["client_refresh_token"] == "refresh-token-1"
        assert kwargs["actor"] == "model-owner"
        return {
            "schema_version": "model-activation-v1",
            "status": "activated",
            "previous_profile": {"id": str(self.active_id)},
            "activated_profile": {"id": str(self.draft_id)},
            "cache_invalidation": {
                "previous_refresh_token": "refresh-token-1",
                "refresh_token": "refresh-token-2",
                "refresh_generation": 2,
            },
            "outbox_event": {
                "event_type": "model.profile.activated",
                "status": "pending",
            },
        }

    def enqueue_score_recompute(self, **kwargs: object) -> dict:
        self.calls.append("enqueue_recompute")
        assert kwargs["expected_active_profile_version_id"] == self.draft_id
        assert kwargs["client_refresh_token"] == "refresh-token-2"
        assert kwargs["scope"] == "global"
        assert kwargs["actor"] == "model-owner"
        return {
            "schema_version": "score-recompute-request-v1",
            "status": "queued",
            "idempotency_key": "score-recompute:global:draft",
            "job": {"id": "job-1", "status": "queued"},
            "outbox_event": {
                "event_type": "score.recompute.requested",
                "status": "pending",
            },
            "cache_policy": {
                "refresh_token": "refresh-token-2",
                "refresh_generation": 2,
            },
        }


def test_preview_contract_is_fail_closed_and_hash_bound() -> None:
    profile = apply_model_config.read_json(PROFILE_PATH)
    thresholds = apply_model_config.read_json(THRESHOLDS_PATH)

    payload = apply_model_config.build_preview_contract(
        profile_path=PROFILE_PATH,
        thresholds_path=THRESHOLDS_PATH,
        profile=profile,
        thresholds=thresholds,
        reason="unit dry run",
        generated_at="2026-06-24T00:00:00Z",
    )

    assert payload["schema_version"] == "eei-model-config-apply-contract-v1"
    assert payload["status"] == "DRY_RUN_READY"
    assert payload["acceptance_ids"] == ["A204", "A205"]
    assert payload["release_gate_closed_by_apply_model_config"] is False
    assert payload["database_write_attempted"] is False
    assert payload["profile_sha256"] == apply_model_config.canonical_hash(profile)
    assert "does_not_close_A209_24h_operator_soak" in payload["non_closure"]


def test_execute_model_config_creates_activates_and_queues_recompute() -> None:
    repository = FakeModelConfigRepository()
    profile = apply_model_config.read_json(PROFILE_PATH)
    thresholds = apply_model_config.read_json(THRESHOLDS_PATH)

    payload = apply_model_config.execute_model_config(
        repository=repository,
        profile_path=PROFILE_PATH,
        thresholds_path=THRESHOLDS_PATH,
        profile=profile,
        thresholds=thresholds,
        reason="unit execute",
        actor="model-owner",
        generated_at="2026-06-24T00:00:00Z",
    )

    assert repository.calls == [
        "active_context",
        "create_draft",
        "activate",
        "enqueue_recompute",
    ]
    assert payload["status"] == "APPLIED"
    assert payload["database_write_attempted"] is True
    assert payload["activation"]["status"] == "activated"
    assert payload["activation"]["refresh_token"] == "refresh-token-2"
    assert payload["score_recompute"]["status"] == "queued"
    assert payload["score_recompute"]["outbox_event_type"] == "score.recompute.requested"


def test_execute_mode_requires_database_url() -> None:
    try:
        apply_model_config.repository_from_database_url(None)
    except RuntimeError as exc:
        assert "DATABASE_URL" in str(exc)
    else:  # pragma: no cover - defensive test guard.
        raise AssertionError("missing DATABASE_URL should fail closed")

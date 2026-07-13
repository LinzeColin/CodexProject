from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any, Literal
from uuid import UUID

import psycopg
from psycopg.types.json import Jsonb

from ..scoring import source_document_score_metrics

FailureStage = Literal["after_facts", "after_scores", "after_changes"]

PIPELINE_VERSION = "transactional-ingestion-pipeline-v1"
PIPELINE_AFFECTED_MODULES = [
    "business_map",
    "supply_chain",
    "evidence_center",
    "data_center",
    "change_feed",
]


class TransactionalPipelineError(RuntimeError):
    pass


class InjectedPipelineFailure(TransactionalPipelineError):
    pass


def jsonable(value: Any) -> Any:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
    if isinstance(value, dict):
        return {key: jsonable(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [jsonable(item) for item in value]
    return value


def canonical_json(payload: Any) -> str:
    return json.dumps(jsonable(payload), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def payload_hash(payload: Any) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def source_document_payload(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_document_id": row["source_document_id"],
        "source_id": row["source_id"],
        "source_code": row["source_code"],
        "source_tier": row["source_tier"],
        "source_active": row["source_active"],
        "external_id": row["external_id"],
        "url": row["url"],
        "title": row["title"],
        "publisher": row["publisher"],
        "document_date": row["document_date"],
        "observed_at": row["observed_at"],
        "retrieved_at": row["retrieved_at"],
        "content_hash": row["content_hash"],
        "media_type": row["media_type"],
        "parser_version": row["document_parser_version"],
        "raw_snapshot_id": row["raw_snapshot_id"],
        "raw_anchor_id": row["raw_anchor_id"],
        "raw_content_hash": row["raw_content_hash"],
        "raw_record_mode": row["raw_record_mode"],
        "raw_validation_status": row["raw_validation_status"],
        "raw_review_status": row["raw_review_status"],
        "raw_parser_version": row["raw_parser_version"],
    }


def classify_change_types(
    *,
    previous_payload: dict[str, Any] | None,
    current_payload: dict[str, Any],
    source_active: bool,
    review_status: str,
    stale: bool,
) -> list[str]:
    change_types: list[str] = []
    if previous_payload is None:
        change_types.append("created")
    elif payload_hash(previous_payload) != payload_hash(current_payload):
        change_types.extend(("updated", "superseded"))
    if review_status == "disputed":
        change_types.append("conflict_detected")
    if not source_active:
        change_types.append("revoked")
    if stale:
        change_types.append("stale")
    return change_types


def publication_state(connection: psycopg.Connection) -> dict[str, Any]:
    row = connection.execute(
        """
        SELECT
          (SELECT count(*)::int FROM fact_versions) AS fact_version_count,
          (SELECT count(*)::int FROM scoring_runs) AS scoring_run_count,
          (SELECT count(*)::int FROM score_results) AS score_result_count,
          (SELECT count(*)::int FROM changes) AS change_count,
          aac.active_data_snapshot_id,
          aac.active_scoring_run_id,
          aac.refresh_token::text AS refresh_token,
          aac.refresh_generation
        FROM active_analysis_contexts aac
        WHERE aac.context_key = 'global'
        """
    ).fetchone()
    if row is None:
        raise TransactionalPipelineError("No active global analysis context")
    return dict(row)


def publication_fields_unchanged(before: dict[str, Any], after: dict[str, Any]) -> bool:
    fields = (
        "fact_version_count",
        "scoring_run_count",
        "score_result_count",
        "active_data_snapshot_id",
        "active_scoring_run_id",
        "refresh_token",
        "refresh_generation",
    )
    return all(before[field] == after[field] for field in fields)


def load_batch_documents(
    connection: psycopg.Connection,
    ingestion_run_id: UUID,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    ingestion_run = connection.execute(
        """
        SELECT ir.*, s.code AS source_code
        FROM ingestion_runs ir
        JOIN sources s ON s.id = ir.source_id
        WHERE ir.id = %s
        FOR SHARE OF ir
        """,
        (ingestion_run_id,),
    ).fetchone()
    if ingestion_run is None:
        raise TransactionalPipelineError(f"Ingestion run not found: {ingestion_run_id}")
    if ingestion_run["status"] != "succeeded":
        raise TransactionalPipelineError("Only succeeded ingestion runs can be published")

    rows = connection.execute(
        """
        SELECT DISTINCT ON (sd.id)
          sd.id AS source_document_id,
          sd.source_id,
          s.code AS source_code,
          s.source_tier,
          s.active AS source_active,
          sd.external_id,
          sd.url,
          sd.title,
          sd.publisher,
          sd.document_date,
          sd.observed_at,
          sd.retrieved_at,
          sd.content_hash,
          sd.media_type,
          sd.parser_version AS document_parser_version,
          rss.id AS raw_snapshot_id,
          rss.anchor_id AS raw_anchor_id,
          rss.content_hash AS raw_content_hash,
          rss.record_mode AS raw_record_mode,
          rss.validation_status AS raw_validation_status,
          rss.review_status AS raw_review_status,
          rss.parser_version AS raw_parser_version,
          COALESCE(evidence_counts.downstream_evidence_count, 0)::int
            AS downstream_evidence_count
        FROM raw_source_snapshots rss
        JOIN source_documents sd ON sd.id = rss.source_document_id
        JOIN sources s ON s.id = sd.source_id
        LEFT JOIN LATERAL (
          SELECT count(*)::int AS downstream_evidence_count
          FROM (
            SELECT re.relationship_id::text AS downstream_id
            FROM relationship_evidence re WHERE re.source_document_id = sd.id
            UNION ALL
            SELECT ee.event_id::text FROM event_evidence ee
            WHERE ee.source_document_id = sd.id
            UNION ALL
            SELECT rfce.candidate_id::text FROM relationship_fact_candidate_evidence rfce
            WHERE rfce.source_document_id = sd.id
            UNION ALL
            SELECT iec.id::text FROM ingestion_evidence_chain iec
            WHERE iec.source_document_id = sd.id
          ) evidence
        ) evidence_counts ON true
        WHERE rss.ingestion_run_id = %s
        ORDER BY sd.id, rss.retrieved_at DESC, rss.created_at DESC
        """,
        (ingestion_run_id,),
    ).fetchall()
    if not rows:
        raise TransactionalPipelineError("Ingestion run has no raw source documents to publish")
    return dict(ingestion_run), [dict(row) for row in rows]


def latest_fact_version(
    connection: psycopg.Connection,
    object_id: UUID,
    *,
    scope: str,
    record_mode: str,
) -> dict[str, Any] | None:
    row = connection.execute(
        """
        SELECT fv.*
        FROM fact_versions fv
        JOIN data_snapshots ds ON ds.id = fv.snapshot_id
        WHERE fv.object_type = 'source_document'
          AND fv.object_id = %s
          AND ds.scope = %s
          AND ds.record_mode = %s
        ORDER BY fv.version_no DESC, fv.created_at DESC
        LIMIT 1
        """,
        (object_id, scope, record_mode),
    ).fetchone()
    return dict(row) if row else None


def insert_change(
    connection: psycopg.Connection,
    *,
    change_type: str,
    object_id: UUID,
    old_value: dict[str, Any],
    new_value: dict[str, Any],
    source_document_id: UUID,
    ingestion_run_id: UUID,
    review_required: bool,
) -> UUID:
    row = connection.execute(
        """
        INSERT INTO changes(
          change_type, object_type, object_id, old_value, new_value,
          source_document_id, ingestion_run_id, review_required
        )
        VALUES (%s, 'source_document', %s, %s, %s, %s, %s, %s)
        RETURNING id
        """,
        (
            change_type,
            object_id,
            Jsonb(jsonable(old_value)),
            Jsonb(jsonable(new_value)),
            source_document_id,
            ingestion_run_id,
            review_required,
        ),
    ).fetchone()
    return row["id"]


def insert_outbox_event(
    connection: psycopg.Connection,
    *,
    event_type: str,
    aggregate_type: str,
    aggregate_id: UUID,
    idempotency_key: str,
    payload: dict[str, Any],
) -> UUID:
    row = connection.execute(
        """
        INSERT INTO transactional_outbox(
          event_type, aggregate_type, aggregate_id, idempotency_key,
          payload, status, metadata
        )
        VALUES (%s, %s, %s, %s, %s, 'pending', %s)
        ON CONFLICT (idempotency_key) DO UPDATE SET
          updated_at = transactional_outbox.updated_at
        RETURNING id
        """,
        (
            event_type,
            aggregate_type,
            aggregate_id,
            idempotency_key,
            Jsonb(jsonable(payload)),
            Jsonb(
                {
                    "task_ids": ["T705"],
                    "acceptance_ids": ["A105", "A106", "A107"],
                    "contract": PIPELINE_VERSION,
                }
            ),
        ),
    ).fetchone()
    return row["id"]


def execute_transactional_pipeline(
    connection: psycopg.Connection,
    *,
    ingestion_run_id: UUID,
    scope: str,
    record_mode: str,
    reason: str,
    stale_after_days: int = 365,
    failure_stage: FailureStage | None = None,
) -> dict[str, Any]:
    if stale_after_days < 1:
        raise TransactionalPipelineError("stale_after_days must be positive")
    if failure_stage and record_mode != "fixture":
        raise TransactionalPipelineError("failure injection is allowed only for fixture mode")

    with connection.transaction():
        context = connection.execute(
            """
            SELECT
              aac.active_scoring_profile_version_id,
              aac.active_data_snapshot_id,
              aac.active_scoring_run_id,
              aac.refresh_token::text AS refresh_token,
              aac.refresh_generation,
              spv.model_id,
              sp.profile_key,
              spv.version AS profile_version,
              sm.model_key,
              sm.version AS model_version
            FROM active_analysis_contexts aac
            JOIN scoring_profile_versions spv
              ON spv.id = aac.active_scoring_profile_version_id
            JOIN scoring_profiles sp ON sp.id = spv.profile_id
            JOIN scoring_models sm ON sm.id = spv.model_id
            WHERE aac.context_key = 'global'
            FOR UPDATE OF aac
            """
        ).fetchone()
        if context is None:
            raise TransactionalPipelineError("No active global analysis context")
        ingestion_run, documents = load_batch_documents(connection, ingestion_run_id)
        if ingestion_run["mode"] != record_mode:
            raise TransactionalPipelineError(
                f"record_mode {record_mode!r} does not match ingestion run mode "
                f"{ingestion_run['mode']!r}"
            )

        document_payloads = [source_document_payload(row) for row in documents]
        input_hash = payload_hash(
            {
                "pipeline_version": PIPELINE_VERSION,
                "scope": scope,
                "record_mode": record_mode,
                "ingestion_run_id": ingestion_run_id,
                "documents": document_payloads,
                "active_profile_version_id": context["active_scoring_profile_version_id"],
            }
        )
        existing = connection.execute(
            """
            SELECT ds.id AS data_snapshot_id, ds.snapshot_key,
                   (ds.metadata->>'scoring_run_id')::uuid AS scoring_run_id
            FROM data_snapshots ds
            WHERE ds.scope = %s
              AND ds.record_mode = %s
              AND ds.status IN ('active', 'superseded')
              AND ds.metadata->>'pipeline_input_hash' = %s
            ORDER BY (ds.status = 'active') DESC, ds.created_at DESC
            LIMIT 1
            """,
            (scope, record_mode, input_hash),
        ).fetchone()
        if existing is not None:
            return jsonable(
                {
                    "schema_version": PIPELINE_VERSION,
                    "status": "idempotent_replay",
                    "ingestion_run_id": ingestion_run_id,
                    "input_hash": input_hash,
                    "data_snapshot_id": existing["data_snapshot_id"],
                    "data_snapshot_key": existing["snapshot_key"],
                    "scoring_run_id": existing["scoring_run_id"],
                    "fact_version_count": 0,
                    "score_result_count": 0,
                    "change_count": 0,
                    "change_types": [],
                    "acceptance_ids": ["A105", "A106", "A107"],
                }
            )

        timestamp = datetime.now(UTC)
        as_of = max(
            (row["retrieved_at"] or row["observed_at"] or timestamp for row in documents),
            default=timestamp,
        )
        snapshot_key = f"{scope}:{record_mode}:pipeline:{input_hash[:16]}"
        snapshot = connection.execute(
            """
            INSERT INTO data_snapshots(
              snapshot_key, scope, record_mode, status, built_from_ingestion_run_id,
              source_hash, as_of, metadata
            )
            VALUES (%s, %s, %s, 'building', %s, %s, %s, %s)
            RETURNING id
            """,
            (
                snapshot_key,
                scope,
                record_mode,
                ingestion_run_id,
                input_hash,
                as_of,
                Jsonb(
                    {
                        "handler_contract": PIPELINE_VERSION,
                        "pipeline_input_hash": input_hash,
                        "reason": reason,
                    }
                ),
            ),
        ).fetchone()

        derived: list[dict[str, Any]] = []
        for row, payload in zip(documents, document_payloads, strict=True):
            object_id = row["source_document_id"]
            previous = latest_fact_version(
                connection,
                object_id,
                scope=scope,
                record_mode=record_mode,
            )
            version_no = int(previous["version_no"]) + 1 if previous else 1
            fact_status = (
                "revoked"
                if not row["source_active"]
                else "disputed"
                if row["raw_review_status"] == "disputed"
                else "reported"
            )
            current_hash = payload_hash(payload)
            fact = connection.execute(
                """
                INSERT INTO fact_versions(
                  snapshot_id, object_type, object_id, version_no, fact_status,
                  record_mode, valid_from, observed_at, source_document_id,
                  ingestion_run_id, parser_version, payload_hash, payload,
                  previous_fact_version_id
                )
                VALUES (
                  %s, 'source_document', %s, %s, %s, %s, %s, %s, %s,
                  %s, %s, %s, %s, %s
                )
                RETURNING id
                """,
                (
                    snapshot["id"],
                    object_id,
                    version_no,
                    fact_status,
                    record_mode,
                    row["document_date"],
                    row["observed_at"],
                    object_id,
                    ingestion_run_id,
                    row["raw_parser_version"] or row["document_parser_version"],
                    current_hash,
                    Jsonb(jsonable(payload)),
                    previous["id"] if previous else None,
                ),
            ).fetchone()
            connection.execute(
                """
                INSERT INTO fact_version_evidence(
                  fact_version_id, source_document_id, role, locator,
                  support_excerpt, structured_fact
                )
                VALUES (%s, %s, 'context', %s, %s, %s)
                """,
                (
                    fact["id"],
                    object_id,
                    f"raw_source_snapshots/{row['raw_snapshot_id']}",
                    "Transactional source-document fact derived from validated raw snapshot.",
                    Jsonb(
                        {
                            "anchor_id": row["raw_anchor_id"],
                            "raw_content_hash": row["raw_content_hash"],
                            "record_mode": row["raw_record_mode"],
                        }
                    ),
                ),
            )
            derived.append(
                {
                    "row": row,
                    "payload": payload,
                    "previous": previous,
                    "fact_version_id": fact["id"],
                }
            )

        if failure_stage == "after_facts":
            raise InjectedPipelineFailure("Injected failure after fact derivation")

        scoring_run = connection.execute(
            """
            INSERT INTO scoring_runs(
              model_id, profile_version_id, data_snapshot_at, parameters,
              status, started_at, finished_at, content_hash
            )
            VALUES (%s, %s, %s, %s, 'completed', %s, %s, %s)
            RETURNING id
            """,
            (
                context["model_id"],
                context["active_scoring_profile_version_id"],
                as_of,
                Jsonb(
                    {
                        "handler_contract": PIPELINE_VERSION,
                        "pipeline_input_hash": input_hash,
                        "scope": scope,
                        "record_mode": record_mode,
                    }
                ),
                timestamp,
                timestamp,
                f"pipeline:{input_hash}:{snapshot['id']}",
            ),
        ).fetchone()
        for item in derived:
            row = item["row"]
            provenance_values = (
                row["source_id"],
                row["url"],
                row["content_hash"],
                row["observed_at"],
                row["retrieved_at"],
                row["publisher"] or row["title"],
            )
            metrics = source_document_score_metrics(
                source_tier=int(row["source_tier"]),
                provenance_field_count=sum(value is not None for value in provenance_values),
                parser_version_present=bool(
                    row["raw_parser_version"] or row["document_parser_version"]
                ),
                downstream_evidence_count=int(row["downstream_evidence_count"]),
                fact_version_present=True,
                source_active=bool(row["source_active"]),
            )
            connection.execute(
                """
                INSERT INTO score_results(
                  scoring_run_id, object_type, object_id, raw_score,
                  evidence_quality, adjusted_score, coverage, contributions,
                  missing_inputs
                )
                VALUES (%s, 'source_document', %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    scoring_run["id"],
                    row["source_document_id"],
                    metrics["raw_score"],
                    metrics["evidence_quality"],
                    metrics["adjusted_score"],
                    metrics["coverage"],
                    Jsonb(jsonable(metrics["contributions"])),
                    Jsonb(jsonable(metrics["missing_inputs"])),
                ),
            )

        if failure_stage == "after_scores":
            raise InjectedPipelineFailure("Injected failure after score derivation")

        change_ids: list[UUID] = []
        change_types: list[str] = []
        for item in derived:
            row = item["row"]
            previous = item["previous"]
            previous_payload = dict(previous["payload"]) if previous else None
            stale = bool(
                row["document_date"]
                and (as_of.date() - row["document_date"].date()).days > stale_after_days
            )
            item_change_types = classify_change_types(
                previous_payload=previous_payload,
                current_payload=item["payload"],
                source_active=bool(row["source_active"]),
                review_status=row["raw_review_status"],
                stale=stale,
            )
            for change_type in item_change_types:
                current_value = dict(item["payload"])
                current_value["change_semantics"] = {
                    "change_type": change_type,
                    "pipeline_input_hash": input_hash,
                    "reason": reason,
                }
                change_ids.append(
                    insert_change(
                        connection,
                        change_type=change_type,
                        object_id=row["source_document_id"],
                        old_value=previous_payload or {},
                        new_value=current_value,
                        source_document_id=row["source_document_id"],
                        ingestion_run_id=ingestion_run_id,
                        review_required=change_type
                        in {"conflict_detected", "revoked", "stale"},
                    )
                )
                change_types.append(change_type)

        if failure_stage == "after_changes":
            raise InjectedPipelineFailure("Injected failure after change derivation")

        fact_count = connection.execute(
            "SELECT count(*)::int AS count FROM fact_versions WHERE snapshot_id = %s",
            (snapshot["id"],),
        ).fetchone()["count"]
        score_count = connection.execute(
            "SELECT count(*)::int AS count FROM score_results WHERE scoring_run_id = %s",
            (scoring_run["id"],),
        ).fetchone()["count"]
        if fact_count != len(documents) or score_count != len(documents):
            raise TransactionalPipelineError("Derived fact/score count validation failed")

        previous_snapshot = connection.execute(
            """
            UPDATE data_snapshots
            SET status = 'superseded',
                metadata = metadata || %s
            WHERE scope = %s AND record_mode = %s AND status = 'active'
            RETURNING id
            """,
            (Jsonb({"superseded_by_pipeline_input_hash": input_hash}), scope, record_mode),
        ).fetchone()
        connection.execute(
            """
            UPDATE data_snapshots
            SET status = 'active', activated_at = %s,
                supersedes_snapshot_id = %s,
                metadata = metadata || %s
            WHERE id = %s
            """,
            (
                timestamp,
                previous_snapshot["id"] if previous_snapshot else None,
                Jsonb(
                    {
                        "scoring_run_id": str(scoring_run["id"]),
                        "fact_version_count": fact_count,
                        "score_result_count": score_count,
                        "change_count": len(change_ids),
                    }
                ),
                snapshot["id"],
            ),
        )
        updated_context = connection.execute(
            """
            UPDATE active_analysis_contexts
            SET active_data_snapshot_id = %s,
                active_scoring_run_id = %s,
                refresh_token = gen_random_uuid(),
                refresh_generation = refresh_generation + 1,
                status = 'active',
                activated_at = %s,
                activated_by = 'system',
                affected_modules = %s,
                metadata = metadata || %s,
                updated_at = %s
            WHERE context_key = 'global'
            RETURNING refresh_token::text AS refresh_token, refresh_generation
            """,
            (
                snapshot["id"],
                scoring_run["id"],
                timestamp,
                Jsonb(PIPELINE_AFFECTED_MODULES),
                Jsonb(
                    {
                        "last_transactional_ingestion_run_id": str(ingestion_run_id),
                        "last_transactional_pipeline_input_hash": input_hash,
                    }
                ),
                timestamp,
            ),
        ).fetchone()

        event_payload = {
            "schema_version": PIPELINE_VERSION,
            "ingestion_run_id": ingestion_run_id,
            "data_snapshot_id": snapshot["id"],
            "scoring_run_id": scoring_run["id"],
            "pipeline_input_hash": input_hash,
            "fact_version_count": fact_count,
            "score_result_count": score_count,
            "change_count": len(change_ids),
            "change_types": sorted(set(change_types)),
            "refresh_token": updated_context["refresh_token"],
            "refresh_generation": updated_context["refresh_generation"],
        }
        data_event_id = insert_outbox_event(
            connection,
            event_type="data.snapshot.activated",
            aggregate_type="data_snapshot",
            aggregate_id=snapshot["id"],
            idempotency_key=f"pipeline-data-snapshot:{input_hash}",
            payload=event_payload,
        )
        score_event_id = insert_outbox_event(
            connection,
            event_type="score.snapshot.activated",
            aggregate_type="scoring_run",
            aggregate_id=scoring_run["id"],
            idempotency_key=f"pipeline-score-snapshot:{input_hash}",
            payload=event_payload,
        )
        connection.execute(
            """
            INSERT INTO operation_logs(
              actor, action_type, object_type, object_id, old_value, new_value,
              diff, reason, model_version, profile_version, result_status
            )
            VALUES (
              'system', 'execute_transactional_ingestion_pipeline', 'ingestion_run',
              %s, %s, %s, %s, %s, %s, %s, 'success'
            )
            """,
            (
                ingestion_run_id,
                Jsonb(
                    jsonable(
                        {
                            "active_data_snapshot_id": context["active_data_snapshot_id"],
                            "active_scoring_run_id": context["active_scoring_run_id"],
                            "refresh_token": context["refresh_token"],
                            "refresh_generation": context["refresh_generation"],
                        }
                    )
                ),
                Jsonb(jsonable(event_payload)),
                Jsonb(
                    {
                        "change_types": sorted(set(change_types)),
                        "affected_modules": PIPELINE_AFFECTED_MODULES,
                    }
                ),
                reason,
                f"{context['model_key']}@{context['model_version']}",
                f"{context['profile_key']}@{context['profile_version']}",
            ),
        )
        return jsonable(
            {
                **event_payload,
                "status": "completed",
                "data_snapshot_key": snapshot_key,
                "previous_active_data_snapshot_id": context["active_data_snapshot_id"],
                "previous_active_scoring_run_id": context["active_scoring_run_id"],
                "change_ids": change_ids,
                "outbox_event_ids": [data_event_id, score_event_id],
                "affected_modules": PIPELINE_AFFECTED_MODULES,
                "acceptance_ids": ["A105", "A106", "A107"],
            }
        )


def record_pipeline_failure(
    connection: psycopg.Connection,
    *,
    ingestion_run_id: UUID,
    error: Exception,
    failure_stage: str | None,
    before_state: dict[str, Any],
    after_state: dict[str, Any],
) -> dict[str, Any]:
    source_document = connection.execute(
        """
        SELECT sd.id
        FROM raw_source_snapshots rss
        JOIN source_documents sd ON sd.id = rss.source_document_id
        WHERE rss.ingestion_run_id = %s
        ORDER BY sd.id
        LIMIT 1
        """,
        (ingestion_run_id,),
    ).fetchone()
    unchanged = publication_fields_unchanged(before_state, after_state)
    row = connection.execute(
        """
        INSERT INTO changes(
          change_type, object_type, object_id, old_value, new_value,
          source_document_id, ingestion_run_id, review_required
        )
        VALUES ('ingestion_failed', 'ingestion_batch', %s, %s, %s, %s, %s, true)
        RETURNING id
        """,
        (
            ingestion_run_id,
            Jsonb(jsonable(before_state)),
            Jsonb(
                jsonable(
                    {
                        "error_class": type(error).__name__,
                        "error_message": str(error),
                        "failure_stage": failure_stage,
                        "publication_state_after_rollback": after_state,
                        "publication_rollback_verified": unchanged,
                    }
                )
            ),
            source_document["id"] if source_document else None,
            ingestion_run_id,
        ),
    ).fetchone()
    connection.execute(
        """
        INSERT INTO operation_logs(
          actor, action_type, object_type, object_id, old_value, new_value,
          diff, reason, result_status, error
        )
        VALUES (
          'system', 'execute_transactional_ingestion_pipeline', 'ingestion_run',
          %s, %s, %s, %s, 'Transactional ingestion pipeline failed', 'failed', %s
        )
        """,
        (
            ingestion_run_id,
            Jsonb(jsonable(before_state)),
            Jsonb(jsonable(after_state)),
            Jsonb(
                {
                    "failure_stage": failure_stage,
                    "publication_rollback_verified": unchanged,
                }
            ),
            f"{type(error).__name__}: {error}",
        ),
    )
    return {
        "change_id": str(row["id"]),
        "publication_rollback_verified": unchanged,
    }

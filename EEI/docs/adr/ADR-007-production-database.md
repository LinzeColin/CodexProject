# ADR-007 - Production Database

Status: Accepted
Date: 2026-06-19

## Decision

PostgreSQL 16 is the MVP production system of record. Domain tables, source/evidence tables, data snapshots, immutable fact versions, scoring snapshots, outbox events, source health, saved views, and catalog tables must be represented through reversible migrations before the related feature gate can pass.

## Acceptance IDs

A005, A011, A012, A013, A014, A015, A016, A017, A018, A019, A020, A021, A022, A023, A024, A025, A026, A027, A028, A169, A170, A201, A202

## Consequences

No graph database is introduced in MVP. Graph semantics are implemented on indexed relationship edges with bounded query services. A future graph database requires benchmark evidence and a new ADR.

The T1300 production migration adds `data_snapshots`, `fact_versions`, and
`fact_version_evidence`. These tables keep publishable facts separate from
source evidence, time-validity windows, record mode, parser version, and
snapshot activation state so a failed publication can roll back without
mutating the previous active snapshot.

The T1301 in-progress migration adds `raw_source_snapshots`,
`entity_resolution_candidates`, and `ingestion_evidence_chain`. These tables
preserve curated official source anchors, parser version, review status,
entity-resolution confidence, evidence chain and counter-evidence before any
relationship/event fact is published.

The follow-on T1301 candidate migration adds `relationship_fact_candidates`,
`relationship_fact_candidate_evidence`, and `manual_review_queue`. A candidate
can express the Golden Vertical path before publication, but publication remains
blocked until source thresholds and human review semantics are satisfied.

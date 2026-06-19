# ADR-007 - Production Database

Status: Accepted
Date: 2026-06-19

## Decision

PostgreSQL 16 is the MVP production system of record. Domain tables, source/evidence tables, scoring snapshots, outbox events, source health, saved views, and catalog tables must be represented through migrations before the related feature gate can pass.

## Acceptance IDs

A005, A011, A012, A013, A014, A015, A016, A017, A018, A019, A020, A021, A022, A023, A024, A025, A026, A027, A028, A169, A170

## Consequences

No graph database is introduced in MVP. Graph semantics are implemented on indexed relationship edges with bounded query services. A future graph database requires benchmark evidence and a new ADR.


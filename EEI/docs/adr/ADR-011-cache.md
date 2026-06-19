# ADR-011 - Cache

Status: Accepted
Date: 2026-06-19

## Decision

MVP cache uses PostgreSQL projections/snapshot tables, HTTP validators, and frontend query caching. Redis is deferred unless benchmark evidence proves it is required.

Outbox rows are the durable event source. PostgreSQL `LISTEN/NOTIFY` may be used only as a wake-up optimization, not as the reliable queue.

## Acceptance IDs

A007, A105, A106, A107, A113, A114, A115, A178

## Consequences

Cache correctness is keyed by snapshot/version context rather than ad hoc mutable cache keys. The MVP has fewer services to operate and test.


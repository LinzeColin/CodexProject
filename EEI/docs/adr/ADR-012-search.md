# ADR-012 - Search

Status: Accepted
Date: 2026-06-19

## Decision

MVP search uses PostgreSQL `pg_trgm`, optional `unaccent`, `tsvector`, `entity_aliases`, and `entity_identifiers`. External search engines are deferred.

Search results must expose matched alias or identifier, entity type, and confidence context so that search does not silently merge distinct entities.

## Acceptance IDs

A015, A026, A038, A169, A170

## Consequences

Search can be tested with deterministic database fixtures. External search requires a benchmark and a new ADR.


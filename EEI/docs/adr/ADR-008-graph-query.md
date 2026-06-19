# ADR-008 - Graph Query

Status: Accepted
Date: 2026-06-19

## Decision

Use bounded PostgreSQL recursive CTEs and indexed relationship edge tables for MVP graph queries.

Initial limits:

- Default hop depth: 1.
- Interactive hard hop limit: 2.
- Maximum path length: 8.
- Home graph budget: 42 nodes and 64 edges.
- Active canvas budget: 500 nodes and 2000 edges.
- All truncation must include a reason and a next action.

## Acceptance IDs

A041, A042, A043, A044, A045, A046, A047, A048, A049, A050, A051, A052, A053, A054, A055, A056, A057, A058, A143, A144, A145, A146, A147, A148, A149, A150, A151, A152

## Consequences

The UI must never request or render an unbounded full network. API responses must include graph budget, truncation, evidence status, and snapshot context.


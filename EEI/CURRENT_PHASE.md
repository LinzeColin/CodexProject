# Current Phase

Updated: 2026-06-19 Australia/Sydney

## Current Gate

- Current phase: Phase 1 / G2 - Domain and data model
- Status: IN PROGRESS
- Previous gate: Phase 1 / G1 - Repository foundation
- G1 status: PASS by GitHub Actions run `27820777762`
- Previous phase: Phase 0 / G0 - Goal, scope, and architecture freeze
- Phase 0 status: APPROVED FOR IMPLEMENTATION by active pursuing goal

## Current Run Contract

Goal:

- Implement the MVP domain foundation required by G2.
- Convert `specs/domain_schema.sql` into reproducible PostgreSQL migrations.
- Add rollback and schema validation tests for entity, relationship, time, evidence, taxonomy, seed, and fixture invariants.
- Keep fixture data explicitly separated from live facts.

In scope:

- Migrations, rollback scripts, seed loader, data checks, and G2 catalog/API anchors.
- G2 task IDs: T200, T201, T202, T203, T204, T205, T206, T207, T208, T1103, T1104, T1105, T1106, T1107, T1108, T1109, T1203.
- G2 Acceptance IDs: A011, A012, A013, A014, A015, A016, A017, A018, A019, A020, A021, A022, A023, A024, A025, A026, A027, A028, A067, A090, A136, A137, A138, A139, A140, A141, A142, A143, A144, A145, A146, A147, A148, A149, A150, A151, A152, A169, A170.

Out of scope for this gate:

- Live data ingestion beyond fixture/seed loaders.
- External data scraping or live source claims.
- Graph database migration.
- Claims that the MVP is complete.

## Stop Conditions

- OpenAPI, catalog, release gate, or Task Pack validation fails for a product reason.
- Fixture data can appear as live fact.
- Any G2 task lacks Acceptance IDs or tests.
- Any migration is not reversible.
- Any schema change breaks G1 `make verify-g1`.

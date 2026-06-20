# ADR-014 - Data Ingestion

Status: Accepted
Date: 2026-06-19

## Decision

The connector interface is:

`fetch -> snapshot -> normalize -> validate -> resolve -> upsert -> derive -> report`

SEC is the first live connector. Curated official fixtures fill private-company gaps until licensed or public evidence is added. Raw snapshots must store hash, parser version, observed time, retrieved time, source semantics, and failure/retry reports.

T1301 starts this contract with deterministic NVIDIA official source anchors.
The loader writes `source_documents`, `raw_source_snapshots`,
`entity_resolution_candidates`, and `ingestion_evidence_chain` in
`curated_official_fixture` mode. These rows are discovery/evidence context only;
they must not publish relationship edges until later normalization and review
contracts pass.

The same deterministic loader also creates Golden Vertical relationship fact
candidates from official NVIDIA/SEC and ASML source snapshots. These candidates
are below the independent-source threshold and enter `manual_review_queue`
instead of becoming published relationship rows.

## Acceptance IDs

A096, A097, A098, A099, A100, A101, A102, A103, A104, A105, A106, A107, A124, A125, A126, A202

## Consequences

Live failures cannot delete the last successful snapshot. Data freshness, failure, and source mode must be visible to API and UI consumers.

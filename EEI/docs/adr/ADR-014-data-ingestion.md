# ADR-014 - Data Ingestion

Status: Accepted
Date: 2026-06-19

## Decision

The connector interface is:

`fetch -> snapshot -> normalize -> validate -> resolve -> upsert -> derive -> report`

SEC is the first live connector. Curated official fixtures fill private-company gaps until licensed or public evidence is added. Raw snapshots must store hash, parser version, observed time, retrieved time, source semantics, and failure/retry reports.

## Acceptance IDs

A096, A097, A098, A099, A100, A101, A102, A103, A104, A105, A106, A107, A124, A125, A126

## Consequences

Live failures cannot delete the last successful snapshot. Data freshness, failure, and source mode must be visible to API and UI consumers.


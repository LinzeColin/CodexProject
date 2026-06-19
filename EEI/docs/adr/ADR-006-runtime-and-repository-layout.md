# ADR-006 - Runtime and Repository Layout

Status: Accepted
Date: 2026-06-19

## Decision

Use one monorepo for the MVP with:

- `apps/web` for the Next.js App Router frontend.
- `apps/api` for the FastAPI service.
- `apps/worker` for ingestion, scoring, calibration, and outbox workers.
- `packages/*` for contracts, graph, scoring, ingestion, catalogs, and shared UI.
- `infra/*` for database, Docker, and deployment scaffolding.
- `tests/*` for unit, integration, and E2E tests.

Use pnpm for JavaScript packages and uv-compatible Python project metadata for Python packages. Local commands must be reproducible through `make` targets.

## Acceptance IDs

A004, A006, A007, A010

## Consequences

The repository can grow gate-by-gate without mixing Task Pack governance, product code, fixtures, and release artifacts. A local host may lack global pnpm or uv, so the bootstrap command must install or invoke pinned project versions rather than rely on untracked global state.


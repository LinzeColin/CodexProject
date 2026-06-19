# ADR-009 - API Contract

Status: Accepted
Date: 2026-06-19

## Decision

FastAPI owns the production API implementation. `specs/api_contract.yaml` remains the public contract and must be validated in CI. Every API response feeding a visual module must include:

- `data_snapshot_id`
- `score_snapshot_id`
- `model_version`
- `profile_version`
- `as_of`
- `generated_at`

## Acceptance IDs

A008, A009, A029, A030, A031, A032, A033, A034, A035, A036, A037, A038, A039, A040, A041, A042, A043, A044, A045, A046, A047, A048, A049, A050, A051, A052, A053, A054, A055, A056, A057, A058, A178

## Consequences

OpenAPI schemas that currently omit response context must be patched before their feature gates can pass. Contract tests must fail on response/schema drift.


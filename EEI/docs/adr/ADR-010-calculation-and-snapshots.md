# ADR-010 - Calculation, Scoring, and Snapshots

Status: Accepted
Date: 2026-06-19

## Decision

Scoring is pure-function-first. Preview changes are read-only and scoped to the user session. Activation creates immutable model/profile versions, operation log entries, outbox events, and score snapshots. Active snapshots switch atomically only after validation succeeds.

## Acceptance IDs

A076, A077, A078, A079, A080, A081, A082, A083, A084, A085, A086, A087, A088, A089, A090, A091, A092, A093, A094, A095, A171, A178, A179

## Consequences

Failed scoring or calibration cannot change active results. Every displayed score must be explainable from model version, profile version, data snapshot, and score snapshot.


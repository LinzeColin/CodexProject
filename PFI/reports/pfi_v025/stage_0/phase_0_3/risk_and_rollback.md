# PFI v0.2.5 Stage 0 Phase 0.3 Risk and Rollback

## Current risk disposition

- Correction `PFI-V025-S0-P03-COMP-FND030` supersedes only the historical FND-030 classification; it does not resolve any remaining production-acceptance gap.
- Open production-acceptance findings: 27 total (`P0=22`, `P1=5`); every open P0/P1 finding blocks v0.2.5 production acceptance but does not block a correctly classified Phase 0.3 candidate.
- Non-gap findings: 11 total (`Fixed=7`, `N/A=4`). FND-030 is N/A because `PFI/web/app/home.js` is not a designated requirement and the formal source already exists at `PFI/web/app/pages/home.js`; every Fixed result remains scope-limited and is not a production pass.
- Executable P2 gaps: 0. `FND-028` is an effective P1 scope control; `FND-036` and `FND-037` are current-contract non-applicable P2 diagnostics. None is a deferred v0.2.5 backlog item.
- Primary risks remain owner/release/App/runtime identity conflicts, split data-root truth, missing account/holding inputs, missing production proofs, unverified browser/runtime behavior, and the expected parameter-owner diagnostic baseline.

## Evidence and privacy guard

- Guard parent: `/private/tmp/pfi-v025-s0p03-guard-ede905cd96c7`.
- Current nonce run is selected only through the guard `current.path`; `run_state.json` binds Phase base `ede905cd96c7b6682cf38971de54f4544f46251b`, batch time `2026-07-12T01:09:30.659834+10:00`, and the App/raw/database proof hashes.
- The Task 1/2 guard proofs, report, and these five Task 3C surfaces retain only redacted IDs, aggregate counts, dates/ranges, statuses, hashes, permission classes and numeric exits. They contain no private filename, raw row, financial value, account, counterparty, credential or absolute private database path; the finalized exact-25 pack remains subject to the later privacy gate.
- No App launch/stop/install, service mutation, data write, database write/migration, normal fetch/ref update, push or merge is authorized or recorded.

## Rollback

- The original exact-25 implementation commit `31368570082c34eca50c72c7d7b2ef46b0e6854d` and immutable attestation SHA-256 `b439444de5a110f07f48fe0fa1d566624183a38e4d7270d0f0bc6fb2e6d696d6` are historical evidence and must remain unchanged.
- Before the compensating commit: remove only the exact 15-path compensation diff and restore the clean original Phase commit; do not touch any other path or external historical evidence.
- After the compensating commit: use another append-only-safe compensation if needed; never rewrite the original event, commit, evidence history or immutable attestation.
- Never rewrite remote history, delete prior Phase evidence, delete raw/data/database state, or alter App/runtime state as rollback.

## Stop conditions

- Stop on any 16th compensation path, protected product/runtime/data/App write, source/hash/schema/privacy/registry/event-prefix mismatch, remote PFI drift, review failure, original-attestation hash mismatch, or no-side-effect mismatch.
- Stop if private data would need to be moved, decrypted, uploaded or emitted, or if runtime provenance is outside the canonical PFI root.
- Stop before Stage 0 whole-stage review and Stage 1.

Stage 0 / Phase 0.3 candidate result only; Stage 0 whole-stage review and Stage 1 remain not_started in this run.

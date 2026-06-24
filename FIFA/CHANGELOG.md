# Changelog

## Unreleased - Other8 S3PDT02

- Changed default FIFA match export behavior to fail closed when raw parse or validation/automation gates fail.
- Failed-closed exports publish only explicit failure evidence and do not publish recommendation JSON, Markdown report, or previous baseline success deliverables.
- Added focused synthetic tests for parse failure, validation failure, ready export, and explicit legacy blocked-export mode.
- No real TAB access, private My Bets snapshot, wagering action, Bet Slip mutation, owner authorization, or delivery-readiness approval was added.

## 0.1.0 - 2026-06-20

- EXTRACTED: Product version `0.1.0` is taken from `tab-research-pipeline/package.json`.
- Added the first auditable governance baseline for FIFA under `docs/governance/`.
- No business logic, model runtime behavior, scoring rules, betting workflow, provider refresh behavior, or product feature behavior was changed.
- Current governance gate is `GOV-P13-required-passed` after project validator and focused checks passed in this run.

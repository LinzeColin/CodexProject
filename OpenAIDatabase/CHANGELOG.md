# Changelog

## Unreleased - Other8 S3PDT01 Privacy Boundary

- Added `scripts/privacy_guard.py` to import raw private sources only from external or ignored private locations and persist redacted derived outputs with an audit log.
- Added focused S3PDT01 unittest coverage for synthetic private import redaction, raw-source deletion recovery, rejected leaky derived-tree imports, and current repo privacy scan.
- Extended `.gitignore` to keep `data/raw/` and `data/private_imports/` out of Git by default.
- Recorded S3PD privacy scan evidence without approving real raw export ingestion, cookies, browser profiles, plaintext secrets, or delivery readiness.

No memory extraction heuristic, active parameter value, retrieval behavior, writeback behavior, or production privacy readiness changed.

## 0.2.0 - 2026-06-21

- Added the three-layer private context architecture for core profile, project memory, and behavior history.
- Added generated ChatGPT/Codex personalization exports, Codex config templates, resource routing, evaluation harness, and four redacted run-log categories.
- Added explicit sync-run baseline evidence and tightened the evaluation harness so required run-log categories must contain JSONL records, not only directories.
- Wired Codex sync to regenerate personalization exports after derived data refresh.
- Added focused tests and governance records for `MOD-011`, `FORM-011`, and `PARAM-083` through `PARAM-092`.

## 0.1.0 - 2026-06-20

- Added the first OpenAIDatabase governance baseline for 10 deterministic models, 10 formulas, and 82 documented active parameters.
- Separated product version, model versions, parameter profile versions, data snapshot version, governance spec version, and current gate in `docs/governance/VERSION_MATRIX.yaml`.
- Kept runtime model behavior unchanged; this is a governance documentation and CI mode change only.

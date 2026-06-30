# Changelog

## Unreleased - Memory Atlas v1.1.5 Stage 2 Planning

- Added the Stage 2.1 default-home integration plan for making `记忆总览`
  the future startup board while preserving the left sidebar navigation.
- Recorded the current route evidence: production still defaults to `galaxy`,
  and the runtime change is deferred to Stage 3 implementation.
- Added the Stage 2.2 Galaxy replacement plan, including a legacy/new renderer
  feature-flag strategy, starfield extraction boundary, rollback path, and
  screenshot/FPS/privacy validation plan.

No production route, raw/private data access, direct writeback, Cloudflare live
deployment, or visual board replacement was added.

## Unreleased - OpenAIDatabase CI Repair

- Restored OpenAIDatabase CI by accepting legacy `sync_runs` records in the evaluator while making future sync logs emit the task-run evidence schema.
- Stabilized generated path strings across Windows/Linux and made the memory-analysis archive step fail closed when `openssl` is unavailable.
- Verified local OpenAIDatabase unittest discovery, personalization export, startup routing, evaluator, py_compile, and changed-scope governance.

No raw export ingestion, plaintext secret persistence, Cloudflare live deployment, Access verification, model calibration claim, or delivery-readiness promotion was added.

## Unreleased - Memory Atlas Data Guide and Cloudflare Preflight

- Renamed the Memory Atlas Notion relationship map to `数据导图` and changed it to a four-column framework map for source/theme, profile/preference, project/decision, and action/opportunity analysis.
- Refreshed the redacted Memory Atlas visualization snapshot for the main-branch deployment build.
- Added Codex memory auto-update runtime support for Monday/Friday 03:00 scheduled refresh and backup flow.
- Re-ran local release, visual, acceptance, Cloudflare Pages + Access preflight, and unit-test gates after merging to main.
- Recorded that live Cloudflare Pages deployment remains blocked by missing local Wrangler authentication and missing `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN`, `MEMORY_ATLAS_ACCESS_HOSTNAME`, and `MEMORY_ATLAS_ALLOWED_EMAIL` environment variables.

No raw exports, plaintext secrets, cookies, browser profiles, direct frontend active-memory mutation, model-calibration claim, or production delivery-readiness promotion was added.

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

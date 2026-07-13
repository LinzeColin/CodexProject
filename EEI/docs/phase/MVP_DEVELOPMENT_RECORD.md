# MVP Development Record

## 2026-07-13 - T704/A104 source freshness contract

Status: LOCAL API/E2E VALIDATED; REMOTE CI PENDING; PHASE 1.2 IN PROGRESS; MVP RELEASE BLOCKED

### Goal and Scope

- Add a production API and connected homepage surface for connector last attempt,
  success, failure/error, latest document date and latest report period.
- Aggregate only existing `sources`, `source_documents`, `raw_source_snapshots` and
  `ingestion_runs`; add no migration or write path.
- Keep attempt/retrieval, document and report-period times semantically separate.
- Perform no live SEC request, scoring/model change, fact publication, T705 change
  pipeline work or A209 evidence mutation.

### Acceptance and Evidence

- `T704 -> A104`: `apps/api/app/domain_repository.py`, `apps/api/app/domain.py`,
  `specs/api_contract.yaml`, `apps/web/src/app/production-data-client.ts`,
  `apps/web/src/app/page.tsx`, `tests/unit/test_source_freshness.py`,
  `tests/integration/test_database_migrations.py`, `tests/e2e/home.spec.ts`,
  `tests/e2e/saved-view-live.spec.ts`, `scripts/validate_source_freshness_contract.py`,
  and `artifacts/tests/a104/t704_source_freshness_contract.json`.
- API status precedence is latest failure, running, never attempted, missing documents,
  fixture, then available. Older failed attempts remain counted but do not override a
  newer successful attempt.
- Server fetch failures remain visible as `server_error`; the UI does not relabel them
  as fixture success.

### Data and Model Boundary

- `last_attempt_at`, `last_success_at` and `last_failure_at` derive from
  `ingestion_runs`; `latest_document_date` derives from `source_documents.document_date`.
- SEC report period derives only from validated raw snapshot report/end values. The
  latest start and end are selected from the same period and historical starts cannot
  leak into a newer report period.
- Record modes remain explicit (`fixture`, `curated_official_fixture`, `dry_run`,
  `live`). No score formula, weight, threshold or active model version changed.

### Validation

- Focused Python compile/Ruff and API unit tests: PASS, `21/21`.
- Isolated PostgreSQL 16 full migration/loader/API integration: PASS, `2/2`; success
  fields and deterministic latest `TimeoutError` failure injection both validated.
- Browser E2E: PASS, `33/33`; TypeScript/Next route typecheck and OpenAPI validation:
  PASS. Temporary PostgreSQL container/volume cleanup and protected A209 container
  identity checks: PASS.
- Full unit suite: PASS, `182/182` with one third-party Starlette/httpx deprecation
  warning. Complete Ruff, Task Pack, catalog, contract, governance consistency and V5
  readiness validation: PASS. Derived artifact and checksum fixed-point validation is
  completed immediately before commit.

### Risk, Rollback, and Stop Conditions

- Risk: stale failures override recovery, retrieval time is presented as fact time,
  historical report starts pair with newer ends, or server errors are hidden by fixture
  fallback. Latest-attempt precedence, explicit time sources, paired report periods and
  visible server error state mitigate these risks.
- Rollback: revert only the T704 commit and A104 artifact/status mappings; T700-T703 SEC
  client, normalization and fixture ingestion remain intact.
- Stop on A209 failure, protected-container change, missing API/UI status or date fields,
  time-semantic conflation, server-error masking, integration/E2E failure, governance
  drift or checksum mismatch.

## 2026-07-13 - T703/A102/A103 SEC fixture ingestion contract

Status: LOCAL FOCUSED VALIDATED; REMOTE CI PENDING; PHASE 1.2 IN PROGRESS; MVP RELEASE BLOCKED

### Goal and Scope

- Add explicit `fixture` and `dry_run` execution over the T702 synthetic SEC fixtures.
- Persist fixture source documents and raw snapshots with SHA-256 idempotency keys while
  preserving `record_mode=fixture`, `fixture://` URLs and non-publishable evidence scope.
- Emit a structured report with checkpoint, counts, status and error class on success or
  failure. Fixture writes require `--allow-database-write` and an explicit database URL.
- Perform no live SEC request, schema migration, scoring/model activation, publication or
  A209 evidence mutation.

### Acceptance and Evidence

- `T703 -> A102`: `apps/api/app/ingest/sec_fixture_ingestion.py`,
  `scripts/load_sec_normalized_fixtures.py`, `tests/unit/test_sec_fixture_ingestion.py`,
  `scripts/validate_sec_fixture_ingestion_contract.py`, and
  `artifacts/tests/a102/t703_sec_fixture_idempotent_upsert_contract.json`.
- `T703 -> A103`: the same implementation/test surface plus
  `artifacts/tests/a103/t703_sec_ingestion_report_contract.json`.
- Isolated PostgreSQL 16 probe: first run inserted 2 source documents and 2 raw
  snapshots; second run inserted 0 and reused all 4; dry-run produced no database write
  and no ingestion run. Database fixed point was 1 fixture source, 2 documents, 2 raw
  snapshots and 2 succeeded ingestion runs.

### Data and Model Boundary

- Source-document key: `(source_id, external_id, content_hash)`; raw-snapshot key:
  `(anchor_id, content_hash)`. Content hash is SHA-256 over canonical source JSON.
- Synthetic fixture source tier is 5 and carries explicit non-live/non-publishable labels.
- Report release scope explicitly keeps `A202`, `A209` and MVP release readiness open.
- No schema, scoring formula, model weight, threshold or active model version changed.

### Validation

- Focused unit, compile and Ruff validation: PASS.
- A102/A103 contract generation and static validation: PASS against an isolated
  PostgreSQL 16 container; temporary container and volume cleanup: PASS.
- Active A209 `eei-postgres` and `eei-worker` container IDs/start times remained unchanged.
- Full unit suite: PASS, `180/180` with one third-party Starlette/httpx deprecation
  warning. Complete Ruff, Task Pack, catalog, contract, governance consistency and V5
  readiness validation: PASS. Derived artifact and checksum fixed-point validation is
  completed immediately before commit.

### Risk, Rollback, and Stop Conditions

- Risk: fixture/live contamination, duplicate rows, dry-run writes or accidental A209
  database access. Explicit fixture metadata, write opt-in, deterministic keys and
  before/after protected-container identity checks mitigate these risks.
- Rollback: revert only the T703 commit and remove A102/A103 artifacts; T700-T702 client,
  resilience and normalization behavior remains intact.
- Stop on A209 failure, protected-container change, non-idempotent second write, dry-run
  persistence, fixture relabeling, report-field loss, governance drift or checksum failure.

## 2026-07-13 - T702/A100/A101 SEC normalization contract

Status: LOCAL FOCUSED VALIDATED; REMOTE CI PENDING; PHASE 1.2 IN PROGRESS; MVP RELEASE BLOCKED

### Goal and Scope

- Normalize SEC Submissions compact columnar arrays into typed filing records while
  preserving accession, form, filed/report dates, accepted timestamp and document.
- Normalize Company Facts taxonomy/concept/unit arrays into typed fact records while
  preserving duration/instant period, form, filed date and optional frame.
- Preserve original and `/A` same-period facts as separate records. Do not infer a
  restatement when the source payload does not explicitly express that semantic.
- Require the caller to supply `fixture`, `curated_official_fixture`, `dry_run` or
  `live` record mode; synthetic fixtures cannot be relabeled as live data.

### Acceptance and Evidence

- `T702 -> A100`: `apps/api/app/ingest/sec_normalizer.py`,
  `tests/fixtures/sec/submissions_golden.json`, `tests/unit/test_sec_normalizer.py`,
  `scripts/validate_sec_normalization_contract.py`, and
  `artifacts/tests/a100/t702_sec_submissions_normalization_contract.json`.
- `T702 -> A101`: the same implementation/test surface plus
  `tests/fixtures/sec/companyfacts_golden.json` and
  `artifacts/tests/a101/t702_sec_companyfacts_normalization_contract.json`.
- Official schema reference:
  `https://www.sec.gov/search-filings/edgar-application-programming-interfaces`.

### Data and Model Boundary

- Submissions parallel arrays must have equal length; blank report/accepted/document
  values remain `None`, and accepted timestamps must include a timezone.
- Company Facts preserve scalar values, taxonomy, concept, unit, start/end period,
  accession, fiscal context, form, filed date and frame; invalid/inverted periods fail.
- This task adds deterministic parser versions only. It changes no scoring model,
  formula, weight, active model version, database schema, API route or publication gate.
- Evidence is fixture-only and records no live network access or database write.

### Validation

- `.venv/bin/pytest -q tests/unit/test_sec_normalizer.py`: PASS, `10/10`.
- `.venv/bin/pytest -q tests/unit`: PASS, `174/174` with one third-party
  Starlette/httpx deprecation warning.
- Focused Ruff and compile: PASS.
- A100/A101 contract generate/validate: PASS with fixture hashes and fail-closed
  `mvp_release_ready=false` scope.
- Task Pack, catalog, contract and governance validation: PASS before fixed-point
  artifact refresh; generated artifact/checksum validation remains required.

### Risk, Rollback, and Stop Conditions

- Risk: column misalignment, revision collapse or fixture/live contamination. Equal-
  length validation, explicit source mode and one-output-per-source-entry mitigate it.
- Rollback: revert only the T702 commit and remove A100/A101 artifacts/fixtures;
  T700-T701 client behavior remains intact.
- Stop on A209 failure, field loss, source-mode bypass, inferred restatement,
  traceability drift, governance failure or checksum mismatch.

## 2026-07-13 - T701/A098/A099 SEC retry and hash-cache contract

Status: LOCAL FOCUSED VALIDATED; REMOTE CI PENDING; PHASE 1.2 IN PROGRESS; MVP RELEASE BLOCKED

### Goal and Scope

- Add bounded timeout and retry semantics to the T700 SEC client without weakening
  the A096 host/User-Agent controls or A097 request-start limiter.
- Retry only `httpx.TimeoutException`, HTTP 429 and HTTP 503 by default, with at
  most three total attempts. Each attempt remains rate limited.
- Add bounded exponential backoff (`0.25s` base, `2.0s` cap), bounded jitter
  (`0.125s` cap), and bounded numeric `Retry-After` handling.
- Hash successful raw JSON response bytes with SHA-256 per canonical URL. First or
  changed content requires processing; unchanged content skips duplicate downstream
  processing. Network retrieval still occurs and cache state is in-memory only.

### Acceptance and Evidence

- `T701 -> A098`: `apps/api/app/ingest/sec_client.py`, mock timeout/429/503 tests,
  `scripts/validate_sec_client_contract.py`, and
  `artifacts/tests/a098/t701_sec_client_retry_contract.json`.
- `T701 -> A099`: repeated/changed/invalid JSON fixture tests and
  `artifacts/tests/a099/t701_sec_client_hash_cache_contract.json`.
- Contract evidence records `live_sec_request_performed=false`,
  `a202_closed_by_contract=false`, `a209_closed_by_contract=false`, and
  `mvp_release_ready=false`.

### Parameters and Model Boundary

- Runtime timeout: default `10s`, hard maximum `30s`.
- Retry attempts: maximum `3`; statuses `429,503`; base/cap/jitter `0.25/2.0/0.125s`.
- Hash algorithm: SHA-256 over successful raw response bytes, keyed by canonical URL.
- These are ingestion reliability parameters, not scoring/model weights or an
  active model version change. No database, API route, publication or release gate
  behavior is claimed complete by this task.

### Validation

- `.venv/bin/pytest -q tests/unit/test_sec_client.py`: PASS, `23/23`.
- `.venv/bin/pytest -q tests/unit`: PASS, `164/164` with one third-party
  Starlette/httpx deprecation warning.
- Focused Ruff: PASS.
- SEC contract generate/validate: PASS for A096-A099 without live network access.
- Governance/artifact/checksum fixed-point validation remains required before commit.

### Risk, Rollback, and Stop Conditions

- Risk: retry amplification or cache truth overstatement. Hard attempt/delay caps,
  per-attempt rate limiting and explicit network-fetch/cache boundaries mitigate it.
- Rollback: revert only the T701 commit and A098/A099 artifacts; T700 remains intact.
- Stop on A209 failure, unbounded retry behavior, failed-response cache mutation,
  traceability drift, governance failure or checksum mismatch.

## 2026-07-13 - T700/A096/A097 SEC EDGAR client foundation

Status: LOCAL FOCUSED VALIDATED; REMOTE CI PENDING; PHASE 1.2 IN PROGRESS; MVP RELEASE BLOCKED

### Goal and Scope

- Implement the first bounded live-source client foundation for SEC EDGAR.
- Require an explicit descriptive application identity and operator contact email.
- Allow only exact `https://data.sec.gov` and `https://www.sec.gov` request hosts,
  reject URL credentials/non-standard ports/fragments, and do not follow redirects.
- Serialize request starts with a fixed `0.125s` interval and no burst allowance,
  enforcing `SEC_MAX_REQUESTS_PER_SECOND = 8`.
- Keep validation offline with `httpx.MockTransport` and an injected fake clock.

### Acceptance and Evidence

- `T700 -> A096`: `apps/api/app/ingest/sec_client.py`,
  `tests/unit/test_sec_client.py`, and
  `artifacts/tests/a096/t700_sec_client_allowlist_contract.json`.
- `T700 -> A097`: the same client/test surface plus
  `artifacts/tests/a097/t700_sec_client_rate_limit_contract.json`.
- `scripts/validate_sec_client_contract.py` generates and validates both artifacts
  while recording that no live SEC request was performed and no release gate closed.

### Parameters and Boundaries

- Operational parameter: `SEC_MAX_REQUESTS_PER_SECOND = 8`.
- Derived fixed interval: `SEC_MIN_REQUEST_INTERVAL_SECONDS = 0.125` seconds.
- These are ingestion safety parameters, not scoring/model weights. They do not
  change active model versions or imply source freshness, ingestion completeness,
  legal clearance, A202 closure, A209 closure, or MVP release readiness.

### Validation

- `.venv/bin/pytest -q tests/unit/test_sec_client.py`: PASS, `15/15`.
- `.venv/bin/python scripts/validate_sec_client_contract.py generate`: PASS.
- `.venv/bin/python scripts/validate_sec_client_contract.py validate`: PASS.
- Focused Ruff and full unit/governance validation remain required before commit.

### Risk, Rollback, and Stop Conditions

- Risk: a future caller could weaken identity/host/rate controls or mistake mock
  evidence for live ingestion evidence; contract artifacts fail closed on those fields.
- Rollback: revert the T700 commit and remove only A096/A097 generated artifacts.
- Stop on contract/test/governance failure, unexpected external worktree changes,
  A209 failed-window evidence, or dead operator/watchdog processes.

## 2026-06-25 - T1301/A202 operator review packet freshness remote CI binding

Status: REMOTE CI ATTESTED FOR COMMIT `236d25354db7d8f9774d1f91981ae30d69b0234e`; A202 STILL IN PROGRESS; A209 WAS RUNNING AT CI-BINDING TIME BUT WAS SUPERSEDED BY THE 2026-06-26 `7/288` FAILURE; DOWNSTREAM RELEASE GATES STILL BLOCKED

### Scope

- Bound the committed A202 operator review packet freshness repair and dependent fail-closed A202/A205/A209 release preflight refresh to GitHub Actions evidence.
- Project Governance run `28194420709` completed PASS for commit `236d25354db7d8f9774d1f91981ae30d69b0234e`.
- EEI validation run `28194420774` completed PASS for the same commit, including static/contract/lint/typecheck/unit, G2 PostgreSQL integration, G2 browser E2E and live FastAPI PostgreSQL E2E.
- No product runtime code, database schema, scoring formula, model weight, threshold, frontend route, legal/source clearance or publication policy changed.

### Current Evidence

- Committed A209 point-in-time heartbeat for this historical CI-binding event was `190/288` PASS windows, `0` failed and `65.97%` completion.
- Live A209 checkpoint observed after the CI-bound commit reached at least `198/288` PASS with `0` failed; watchdog PID `61030` and operator PID `82041` were still running, with child window `199` active at that time.
- Superseding current fact: the later clean 24h attempt failed on 2026-06-25T22:08:58Z at `7/288` with `child_status=NO_OUTPUT`; see the 2026-06-26 A209 repair entry below.
- A209 finalization remains blocked until the 24h summary/checkpoint chain validates `288/288` successful windows with zero failures.

### Acceptance Mapping

- T1301 -> A202 for the operator review packet freshness repair and CI binding.
- T1303 -> A204/A205 for dependent external release-evidence, release-manager and MVP gate preflight context.
- T1307 -> A209 for background soak progress and finalization context.
- This CI binding does not close A202, A204, A205, A209, A210, A026 or A027.

### Validation

- Project Governance run `28194420709` / job `83517222542`: PASS.
- EEI validation run `28194420774` / job `83517223204`: PASS.
- A209 live checkpoint observation at this historical point: `198/288` PASS with `0` failed; progress-only and not release-ready evidence.

### Remaining Gaps

- A202 still requires signed source-license review, passage-level relationship review, production owner sign-off, legal release clearance and final attestation.
- A210 formal brand clearance or waiver, A026/A027 production gold labels, A209 24h final evidence and release-manager activation remain incomplete external gates.

### Rollback

- Revert this CI-binding governance evidence update and regenerate release artifacts with `remote_status=PENDING`.
- Preserve live A209 checkpoint, PID and log files unless a failed window or stale-process condition requires explicit operator intervention.

Append-only development ledger for 商域图谱 / Enterprise Ecosystem Intelligence.

## 2026-06-25 - T1303/A205 A202 operator-review evidence binding

Status: LOCAL FOCUSED VALIDATED; CI PENDING; RELEASE STILL BLOCKED

Completed:

- Bound the existing `artifacts/tests/a202/t1301_operator_review_packet_contract.json` into the T1303 external release-evidence bundle `source_files`.
- Added an `a202_operator_review` gate summary to the external release-evidence bundle so release-manager evidence now shows `live_capture_ready_for_review=true`, `relationship_fact_candidates_allowed=0`, `relationships_publishable=0`, `release_clearance=false` and all signed source/license/passage/owner/legal gates still missing.
- Added the A202 operator review packet as a supporting source for the A202 operator intake item without treating it as clearance.
- Regenerated the external release-evidence bundle, operator intake packet, release-manager activation preflight and MVP release-gate preflight; all remain fail-closed.

Verification status:

- `py_compile` PASS for `scripts/validate_external_release_evidence_bundle.py` and `tests/unit/test_external_release_evidence_bundle.py`.
- Focused `ruff check` PASS for the same files.
- `pytest -q tests/unit/test_external_release_evidence_bundle.py -p no:cacheprovider`: PASS, `7/7`.
- `make generate-external-release-evidence-bundle validate-external-release-evidence-bundle generate-release-manager-activation-artifact validate-release-manager-activation generate-mvp-release-gate-preflight validate-mvp-release-gate-preflight`: PASS.

Still blocked:

- This binding is review-readiness traceability only. It does not provide source-license review, passage-level approval, production owner sign-off, legal clearance, relationship publication, brand clearance, production gold labels, A209 24h completion, release-manager activation or MVP release readiness.

## 2026-06-25 - T1307/A209 live 24h soak heartbeat refresh to 173/288

Status: LOCAL FOCUSED VALIDATED; CI PENDING; A209 STILL IN PROGRESS

Completed:

- Refreshed A209 background heartbeat to the current clean operator soak run: `173/288` windows PASS, `0` failed, `115` remaining and `60.07%` completion.
- Confirmed operator PID `82041` and watchdog PID `61030` remain the active background resolution path; no double-start was performed.
- Refreshed A209 finalization, A203 production API release, external release-evidence bundle, release-manager activation and MVP release-gate artifacts from the current heartbeat.
- Kept `release_gate_closed_by_background_heartbeat=false`, `release_gate_closed_by_finalizer=false`, `downstream_release_gate_refresh_allowed=false` and every dependent release gate fail-closed.

Verification status:

- A209 heartbeat/evidence/finalization generate and validate PASS.
- A203 production API release preflight generate/validate PASS.
- External release-evidence bundle and operator intake packet generate/validate PASS.
- Release-manager activation and MVP release-gate generate/validate PASS.

Still blocked:

- A209 is not complete until `288/288` windows and final 24h summary evidence validate release-ready.
- MVP release readiness remains blocked by A202, A204/A205, A209, A210, A026 and A027.

## 2026-06-25 - T1307/A209 live 24h soak heartbeat refresh to 152/288

Status: LOCAL VERIFY PASS; CI PENDING

Completed:

- Refreshed A209 background heartbeat to the current clean operator soak run: `152/288` windows PASS, `0` failed, `136` remaining and `52.78%` completion.
- Confirmed operator PID `82041` and watchdog PID `61030` are both RUNNING in the heartbeat contract.
- Refreshed A209 finalization, A203 production API release, external release-evidence bundle, release-manager activation and MVP release-gate artifacts from the current heartbeat.
- Kept `release_gate_closed_by_background_heartbeat=false`, `release_gate_closed_by_finalizer=false`, `downstream_release_gate_refresh_allowed=false` and every dependent release gate fail-closed.

Verification status:

- A209 heartbeat/evidence/finalization generate and validate PASS.
- A203 production API release preflight generate/validate PASS.
- External release-evidence bundle and operator intake packet generate/validate PASS.
- Release-manager activation and MVP release-gate generate/validate PASS.
- Full `make verify` PASS with `PLAYWRIGHT_BROWSERS_PATH=/private/tmp/eei-ms-playwright` and `117` unit tests.

Still blocked:

- A209 is not complete until `288/288` windows and final 24h summary evidence validate release-ready.
- MVP release readiness remains blocked by A202, A204/A205, A209, A210, A026 and A027.

## 2026-06-25 - T1301/A202 signed-intake source-boundary hardening

Status: LOCAL VALIDATION PASS; REMOTE CI PASS; RELEASE STILL BLOCKED

Completed:

- Added a source-boundary policy to the A202 signed-intake validator: repository fixtures, templates, docs, config, data and test sources cannot close A202.
- Allowed only external operator files or approved repository operator-input directories (`artifacts/operator_inputs/`, `operator_inputs/`, `work/operator_inputs/`) to serve as signed-intake closure sources.
- Added `PARAM-088` / `release_decision_intake.signed_source_boundary` to bind the disallowed repository prefixes into machine-verified governance.

Verification status:

- Focused py_compile PASS, focused ruff PASS, focused A202 unit tests PASS `17/17`, A202 artifact generation/validation PASS, semantic extraction PASS with 88 parameters, task-pack validation PASS, full `make verify` PASS with 117 unit tests, changed-only Project Governance PASS, and remote CI PASS for commit `a246df94bf73b6fba7111805f3c5a02b6edeb070`.
- Remote CI evidence: Project Governance run `28179389094` PASS; EEI validation run `28179389156` PASS.
- A209 continues as a background 24h gate and is not replaced by this A202 source-boundary hardening.

Still blocked:

- A202 still lacks real source-license review, passage-level relationship approval, production owner approval, legal release clearance and production relationship publication.
- MVP release readiness remains blocked by A202, A204/A205, A209, A210, A026 and A027.

## 2026-06-25 - T1307/A209 live 24h soak heartbeat refresh

Status: FOCUSED LOCAL VALIDATION PASS; GOVERNANCE/RELEASE ARTIFACT VALIDATION AND CI PENDING

Completed:

- Refreshed A209 background heartbeat to the current clean operator soak run: `135/288` windows PASS, `0` failed, `153` remaining and `46.88%` completion.
- Refreshed A209 finalization, A203 production API release, release-manager activation, MVP release-gate and external release-evidence artifacts from the current heartbeat.
- Kept `release_gate_closed_by_background_heartbeat=false`, `release_gate_closed_by_finalizer=false` and every dependent release gate fail-closed.

Verification status:

- A209 heartbeat/evidence/finalization generate and validate PASS.
- A203 production API release preflight generate PASS.
- Release-manager activation, MVP release-gate and external release-evidence bundle generate and validate PASS.

Still blocked:

- A209 is not complete until `288/288` windows and final 24h summary evidence validate.
- MVP release readiness remains blocked by A202, A204/A205, A209, A210, A026 and A027.

## 2026-06-25 - T1303/A204-A205 external release operator intake packet

Status: FOCUSED LOCAL VALIDATION PASS; GOVERNANCE/RELEASE ARTIFACT VALIDATION AND CI PENDING

Completed:

- Added `artifacts/tests/a205/t1303_external_release_operator_intake_packet.json` as the operator-facing checklist for A202 source/license/owner/legal release, A210 brand clearance, A026/A027 production gold labels and A209 24h soak finalization.
- Added validator and Makefile coverage so the packet is generated and validated with the external release-evidence bundle.
- Added `PARAM-087` governance binding for the packet schema version.

Verification status:

- Focused ruff PASS for the validator and tests.
- `tests/unit/test_external_release_evidence_bundle.py` PASS `6/6`.
- `make generate-external-release-evidence-bundle validate-external-release-evidence-bundle` PASS, including packet generation and validation.

Still blocked:

- The packet reports `WAITING_FOR_OPERATOR_INPUTS`, `release_gate_closed_by_operator_packet=false` and no release clearance.
- MVP release readiness remains blocked by A202, A204/A205, A209, A210, A026 and A027.
- A209 remains background `IN_PROGRESS` until 24h evidence reaches `288/288` and release-ready validation passes.

## 2026-06-25 - T1302/A203 E2E CI repair, release still blocked

Status: LOCAL VALIDATION PASS; CI PENDING

Completed:

- Updated the development-status E2E contract so T1302/A203 is expected as `DONE` after implementation closure.
- Rebound governance companion records for the push-base CI delta without changing runtime behavior or release readiness.
- Re-generated clean-room and release artifacts after the E2E/governance repair.

Verification status:

- `make test-e2e` PASS `32/32`.
- `make verify` PASS with `112` unit tests.
- Changed-only governance reproduction PASS with `errors=0` and `warnings=0`.

Still blocked:

- MVP release readiness remains blocked by A202, A204/A205, A209, A210, A026 and A027.

## 2026-06-25 - T1302/A203 API implementation done, release still blocked

Status: LOCAL FOCUSED VALIDATION PASS; CHANGED-ONLY GOVERNANCE AND CI PENDING

Completed:

- Marked T1302/A203 production API implementation contract `DONE` for graph, path, catalog, evidence and scoring API coverage.
- Removed `A203_contract_status` from A203 production API preflight missing gates.
- Refreshed A209 background heartbeat and dependent release preflights to `35/288` successful windows, `0` failed, `253` remaining and `12.15%` completion.

Still blocked:

- A203 does not publish production graph edges or scores.
- MVP release readiness remains blocked by A202, A204/A205, A209, A210, A026 and A027.
- A209 remains background `IN_PROGRESS` until 24h evidence reaches `288/288` and release-ready validation passes.

Verification status:

- Focused A203/A209/A205 unit, ruff, artifact, semantic, V5 readiness, task-pack and structured parse validation passed locally for this iteration.
- Changed-only governance, final full validation, commit, push and CI are pending.

## 2026-06-19 - Phase 1 / G1 start

Status: DONE

Completed:

- Imported the v4.2.0 Task Pack into an implementation repository.
- Created a baseline Git commit before implementation changes.
- Confirmed Task Pack validation passes after import.

Current scope:

- G1 repository foundation and governance synchronization.

Current Acceptance IDs:

- A004, A005, A006, A007, A008, A009, A010, A131, A132, A133, A134, A135, A153, A169, A177.

Evidence commands:

- `PYTHONPATH=/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/lib/python3.12/site-packages python scripts/validate_task_pack.py`

Residual risks:

- `pnpm`, `uv`, and `docker` are not globally installed on the current host.
- Raw `python3 scripts/validate_task_pack.py` fails until Python dependencies are pinned through project tooling.

## 2026-06-19 - Phase 1 / G1 repository foundation batch 1

Status: IN PROGRESS

Completed:

- Added pinned root workspace files: `Makefile`, `package.json`, `pnpm-workspace.yaml`, `pyproject.toml`, `uv.lock`, and `pnpm-lock.yaml`.
- Added FastAPI health shell under `apps/api`.
- Added Watchlist-first Next.js app shell under `apps/web`.
- Added worker/package/infra/test directory anchors.
- Added contract validation and secret scan scripts.
- Added Playwright homepage smoke test.

Verification results:

- `make bootstrap`: PASS.
- `make health`: PASS.
- `make verify`: PASS.
- `npx --yes pnpm@11.8.0 --filter @eei/web build`: PASS.
- `npx --yes pnpm@11.8.0 --filter @eei/web test:e2e`: PASS after installing Playwright Chromium.

Residual risks:

- Docker is not installed on the current host, so `docker compose up -d postgres` and PostgreSQL container health checks were not executed.
- G1 remains IN PROGRESS until the Docker/PostgreSQL health path is verified or an approved non-Docker fallback is added.
- Unit tests pass with a FastAPI/Starlette deprecation warning about `httpx`; monitor when upgrading test dependencies.

## 2026-06-19 - Phase 1 / G1 database readiness contract

Status: IN PROGRESS

Completed:

- Added a PostgreSQL readiness check using pinned `psycopg[binary]==3.3.4`.
- Changed `/health/ready` and `make health` so they fail closed when `DATABASE_URL` is missing or PostgreSQL is unreachable.
- Added unit coverage for missing database configuration and successful `select 1` readiness.
- Added `make db-up`, `make db-down`, `make db-logs`, and `make verify-g1`.

Verification results:

- `make bootstrap-python`: PASS.
- `make test-unit`: PASS, 3 tests.
- `make lint`: PASS.
- `make verify`: PASS.
- `npx --yes pnpm@11.8.0 --filter @eei/web build`: PASS.
- `npx --yes pnpm@11.8.0 --filter @eei/web test:e2e`: PASS.
- `make health`: expected FAIL on current host with `status=not_ready` and `database=not_configured`.
- `make verify-g1`: expected FAIL on current host because `docker` is not installed.

Residual risks:

- G1 cannot pass until Docker/PostgreSQL readiness is verified on a host with Docker or an approved PostgreSQL service path.
- The current host has no `docker` and no `psql` executable.

## 2026-06-19 - Phase 1 / G1 environment doctor and GitHub validation entry

Status: IN PROGRESS

Completed:

- Added `scripts/env_doctor.py` and `make doctor` for structured local environment diagnostics.
- Confirmed the current host reports `docker=null`, `psql=null`, `postgres=null`, `initdb=null`, `database.status=not_configured`, and `g1_ready=false`.
- Added a root GitHub Actions workflow in `LinzeColin/CodexProject` at `.github/workflows/eei-validation.yml` because nested `EEI/.github/workflows/*` files do not run when EEI is stored as a subdirectory.

Verification results:

- `make doctor`: PASS as diagnostic output; reports G1 not ready.
- `.github/workflows/eei-validation.yml` YAML parse: PASS.
- `make lint`: PASS.
- `make verify`: PASS.
- `make verify-g1`: expected FAIL on current host because `docker` is not installed.

Residual risks:

- The root GitHub workflow has been added for future remote verification, but remote Actions status still needs to be inspected after push.
- G1 remains blocked on an actual Docker/PostgreSQL-capable runtime.

## 2026-06-19 - Phase 1 / G1 PostgreSQL startup wait contract

Status: IN PROGRESS

Completed:

- Confirmed the first root GitHub Actions run reached the G1 PostgreSQL/E2E step and failed there after static, contract, lint, typecheck, and unit tests passed.
- Added `scripts/wait_for_database.py` to poll the same `select 1` database readiness contract used by `/health/ready`.
- Added `make wait-db` and changed `make db-up` so Docker startup waits for PostgreSQL before `make health`.
- Added the wait script to `make lint`.

Verification results:

- `make lint`: PASS.
- `make verify`: PASS.
- `env -u DATABASE_URL .venv/bin/uv run python scripts/wait_for_database.py --timeout 1`: expected FAIL with `ERROR: DATABASE_URL is required before waiting for PostgreSQL`.
- `make verify-g1`: expected FAIL on current host because `docker` is not installed.

Residual risks:

- The current host still has no Docker runtime, so local `make verify-g1` remains an expected fail-closed check until Docker/PostgreSQL is available.
- Remote GitHub Actions must be re-run after this change to determine whether the failure was solely a PostgreSQL startup race.

## 2026-06-19 - Phase 1 / G1 close and G2 start

Status: G1 PASS; G2 IN PROGRESS

Completed:

- Pushed `LinzeColin/CodexProject` commit `5de38fd` with the PostgreSQL wait contract.
- Confirmed GitHub Actions run `27820777762` completed with conclusion `success`.
- Confirmed the `verify` job and all steps passed, including `Verify G1 PostgreSQL readiness and E2E`.
- Advanced `data/release_gate_catalog.csv` to `G1=PASS` and `G2=IN PROGRESS`.

Verification results:

- GitHub Actions run: `https://github.com/LinzeColin/CodexProject/actions/runs/27820777762`.
- GitHub Actions job: `https://github.com/LinzeColin/CodexProject/actions/runs/27820777762/job/82333085277`.
- Step 8 `Verify G1 PostgreSQL readiness and E2E`: PASS.

G2 scope and Acceptance IDs:

- T200: A011, A012, A013, A014, A015, A022.
- T201: A016, A020, A021.
- T202: A019.
- T203: A011, A090.
- T204: A017, A018, A028.
- T205: A016, A025, A067.
- T206: A023.
- T207: A024, A028.
- T208: A011, A026, A027.
- T1103: A136, A137.
- T1104: A138, A139, A140.
- T1105: A141, A142.
- T1106: A143, A144, A145.
- T1107: A146, A147.
- T1108: A148, A149, A150.
- T1109: A151, A152.
- T1203: A169, A170.

Residual risks:

- Local host still cannot run Docker-based `make verify-g1`; G1 PASS is based on GitHub Actions evidence.
- G2 has a wide acceptance surface; implementation should split database migrations/data checks from visual canvas work to keep diffs reviewable.

## 2026-06-19 - Phase 1 / G2 database foundation batch 1

Status: IN PROGRESS

Completed:

- Added `infra/db/migrations/0001_core_domain/up.sql` and `down.sql`.
- Added `scripts/migrate.py` for versioned PostgreSQL upgrade/downgrade/status operations.
- Added `scripts/load_seed_catalogs.py` for deterministic catalog and research-universe seed loading.
- Added `scripts/check_database_schema.py` for table and seed-count invariants.
- Added `tests/integration/test_database_migrations.py` for migration, seed idempotency, and rollback.
- Added `make verify-g2-db` to run Docker PostgreSQL, health, static verification, integration tests, and E2E.
- Extended `specs/domain_schema.sql` with catalog-backed relationship families, relationship types, supply-chain stages, seed runs, and research-universe tables.
- Marked T200, T201, T202, T203, T204, T206, T207, and T208 as `IN PROGRESS`.

Verification results:

- `make lint`: PASS.
- `make verify`: PASS.
- `env -u DATABASE_URL .venv/bin/uv run pytest tests/integration -q`: PASS with 1 expected skip.
- `make verify-g2-db`: expected FAIL on current host because `docker` is not installed.

Acceptance IDs touched:

- A011, A012, A013, A014, A015, A016, A017, A018, A019, A020, A021, A022, A023, A024, A026, A027, A028, A090.

Residual risks:

- Actual PostgreSQL migration execution has not been proven locally because Docker is unavailable.
- GitHub Actions must be updated to run `make verify-g2-db` and prove migration/seed/rollback on PostgreSQL.
- T205 synthetic recursive supply-chain fixtures and T1103-T1109 visual canvas tasks are not started.

## 2026-06-20 - Phase 1 / T1306 A208 scale benchmark contracts

Status: IN PROGRESS

Completed:

- Added `scripts/run_scale_benchmarks.py` as a deterministic benchmark contract for API projection, layout, render payload, memory payload, estimated frame budget and synthetic long-task counts.
- Added `tests/unit/test_scale_benchmarks.py` to lock the A208 payload schema, target scale coverage semantics and per-scale pass/fail budget output.
- Added `make validate-scale-benchmark-smoke` and wired it into `make verify`.
- Added `make validate-scale-benchmark-operator` for the manual 10k/100k/1m operator contract.
- Added `scripts/run_browser_scale_benchmarks.mjs` for Chromium browser runtime frame, memory and long-task measurement.
- Advanced T1306/A208 governance from `NOT_STARTED` to `DONE`.

Verification results:

- `.venv/bin/python -m compileall scripts/run_scale_benchmarks.py tests/unit/test_scale_benchmarks.py scripts/validate_v5_production_readiness_sync.py`: PASS.
- `.venv/bin/python scripts/run_scale_benchmarks.py --scales 1000 --iterations 2 --mode ci_smoke --output artifacts/tests/a208/t1306_scale_benchmark_smoke.json --fail-on-budget --quiet`: PASS; output status remains `PARTIAL`.
- `node scripts/run_browser_scale_benchmarks.mjs --scales 10000,100000,1000000 --iterations 1 --output artifacts/tests/a208/t1306_browser_runtime_benchmark.json --fail-on-budget --quiet`: PASS; Chromium browser runtime status is `PASS`.
- `.venv/bin/python scripts/run_scale_benchmarks.py --scales 10000,100000,1000000 --iterations 1 --mode operator_full --output artifacts/tests/a208/t1306_scale_benchmark_operator_contract.json --browser-runtime-artifact artifacts/tests/a208/t1306_browser_runtime_benchmark.json --fail-on-budget --require-full-targets --quiet`: PASS; full A208 coverage status is `PASS`.
- `make validate-scale-benchmark-operator`: PASS with Chromium browser runtime and merged operator contract.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache PNPM=/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/pnpm make verify`: PASS; includes A208 browser benchmark, merged operator contract, governance validators, lint, typecheck and 11 unit tests.
- GitHub Actions `EEI validation` run `27860478421`, job `82455538742`: PASS, including static/contract/lint/typecheck/unit and G2 PostgreSQL/E2E.

Residual risks:

- Browser runtime benchmark uses a bounded SVG runtime contract with 500 visible nodes and 2000 visible edges; production componentized frontend remains T1308/A211.
- Long-duration memory/timer/listener stability remains T1307/A209 soak scope.

## 2026-06-20 - Phase 1 / T1307 A209 soak smoke harness

Status: IN PROGRESS

Completed:

- Added `scripts/run_soak_smoke.mjs` as a browser+worker soak harness.
- Added `make validate-soak-smoke` and wired it into `make verify`.
- Generated `artifacts/tests/a209/t1307_soak_smoke.json` with heap, DOM, listener, timer, frame, long-task, CPU, retry and recovery metrics.
- Advanced T1307/A209 governance from `NOT_STARTED` to `IN PROGRESS`.

Verification results:

- `node --check scripts/run_soak_smoke.mjs`: PASS.
- `node scripts/run_soak_smoke.mjs --mode ci_smoke --duration-seconds 3 --output artifacts/tests/a209/t1307_soak_smoke.json --fail-on-budget --quiet`: PASS; output status remains `PARTIAL` because 4h/24h durations are not measured.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache PNPM=/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/pnpm make verify`: PASS; includes T1307 soak smoke, A208 benchmark contracts, governance validators, lint, typecheck and 11 unit tests.
- GitHub Actions `EEI validation` run `27860819378`, job `82456417742`: PASS, including static/contract/lint/typecheck/unit and G2 PostgreSQL/E2E.

Residual risks:

- A209 is not complete until the same harness runs and records 4h and 24h operator soak evidence.
- Smoke validates the measurement contract and budget checks only; it does not prove long-duration memory, timer, listener or retry stability.

## 2026-06-19 - Phase 1 / G2 database CI repair loop 1

Status: IN PROGRESS

Failure evidence:

- GitHub Actions run `27821508751` failed in `Verify G2 PostgreSQL migrations and E2E`.
- Migration upgrade and schema table checks passed.
- `scripts/load_seed_catalogs.py` failed while loading `relationship_taxonomy.csv`.
- Root cause: `relationship_type_catalog.direction` allowed only `directed` and `undirected`, but the canonical taxonomy contains 6 `bidirectional` relationship types.

Fix:

- Updated `specs/domain_schema.sql` so `relationship_type_catalog.direction` allows `directed`, `undirected`, and `bidirectional`.

Verification to run:

- `make verify`.
- Push and rerun GitHub Actions `make verify-g2-db`.

## 2026-06-19 - Phase 1 / G2 database CI repair loop 2

Status: IN PROGRESS

Failure evidence:

- GitHub Actions run `27821664492` failed in `Verify G2 PostgreSQL migrations and E2E`.
- Migration upgrade and relationship taxonomy loading passed after repair loop 1.
- `scripts/load_seed_catalogs.py` failed while loading `supply_chain_stage_taxonomy.csv`.
- Root cause: `supply_chain_stages.default_direction` allowed an invented set, while the canonical taxonomy contains `upstream`, `downstream`, `midstream`, and `crosscutting`.

Fix:

- Updated `specs/domain_schema.sql` so `supply_chain_stages.default_direction` matches the canonical taxonomy.

Verification to run:

- `make verify`.
- Push and rerun GitHub Actions `make verify-g2-db`.

## 2026-06-19 - Phase 1 / G2 database foundation CI pass

Status: DATABASE SUBSET PASS; G2 IN PROGRESS

Completed:

- GitHub Actions run `27821808812` completed with conclusion `success`.
- Step 8 `Verify G2 PostgreSQL migrations and E2E` passed.
- Integration test `tests/integration/test_database_migrations.py` passed on PostgreSQL.
- E2E smoke test passed after the database integration test.
- Marked T200, T201, T202, T204, T207, and T208 as `DONE`.

Verification evidence:

- GitHub Actions run: `https://github.com/LinzeColin/CodexProject/actions/runs/27821808812`.
- GitHub Actions job: `82336483266`.
- `make verify-g2-db`: PASS in GitHub Actions.
- PostgreSQL readiness: PASS.
- Migration upgrade/schema check/seed idempotency/rollback integration test: PASS.
- Playwright E2E smoke: PASS.

Still open in G2:

- T203 remains `IN PROGRESS` because exploration, Watchlist, scoring, audit, and calibration repository/API behavior is not implemented yet.
- T205 remains `NOT STARTED` because synthetic recursive supply-chain fixtures are not loaded yet.
- T206 remains `IN PROGRESS` because supersession/conflict repository behavior is not implemented beyond schema fields.
- T1103-T1109 and T1203 remain not started or only indirectly scaffolded.

## 2026-06-19 - Phase 1 / G2 T205 synthetic fixture loader

Status: IN PROGRESS

Completed:

- Added fixture dataset, fixture entity notice, and fixture relationship notice tables to the core migration.
- Added `scripts/load_synthetic_fixtures.py` to load `data/mock_entities.json` and `data/mock_relationships.json` idempotently.
- Added fixture checks for A016, A025, and A067 into `scripts/check_database_schema.py`.
- Updated integration test flow to load fixtures twice and verify relationship families, fixture notices, and NVIDIA recursive supply-chain stage coverage.
- Marked T205 as `IN PROGRESS`.

Verification results:

- `make lint`: PASS.
- `make verify`: PASS.
- `env -u DATABASE_URL .venv/bin/uv run pytest tests/integration -q`: PASS with 1 expected skip.

Acceptance IDs touched:

- A016, A025, A067.

Residual risks:

- Actual fixture loading has not been proven on PostgreSQL yet because local Docker is unavailable.
- GitHub Actions must run `make verify-g2-db` to prove fixture migration, load, idempotency, and rollback.

## 2026-06-19 - Phase 1 / G2 T205 backend fixture CI pass

Status: BACKEND FIXTURE SUBSET PASS; T205 IN PROGRESS

Completed:

- GitHub Actions run `27822341025` completed with conclusion `success`.
- Step 8 `Verify G2 PostgreSQL migrations and E2E` passed after adding fixture loading.
- The integration test now proves migration upgrade, seed loading, fixture loading twice, fixture/live separation checks, NVIDIA stage coverage checks, and rollback.

Verification evidence:

- GitHub Actions run: `https://github.com/LinzeColin/CodexProject/actions/runs/27822341025`.
- GitHub Actions job: `82338210943`.
- `make verify-g2-db`: PASS in GitHub Actions.

Acceptance status:

- A016 backend data check is covered by fixture family validation.
- A025 is not fully accepted yet because visible UI/API content tests are not implemented.
- A067 is not fully accepted yet because scenario-level recursive exploration E2E is not implemented.

Residual risks:

- T205 remains `IN PROGRESS` until UI/API fixture marking and recursive scenario E2E exist.
- T203/T206 repository/API behavior is still needed before those acceptance IDs can close.

## 2026-06-19 - Phase 1 / G2 T203/T206 domain API repository pass

Status: DOMAIN API SUBSET PASS; G2 IN PROGRESS

Completed:

- Added database-backed FastAPI routes for `/v1/home`, `/v1/explore`, `/v1/explore/reroot`, `/v1/watchlists`, `/v1/changes`, `/v1/audit-logs`, `/v1/scoring/profiles`, and `/v1/calibrations`.
- Added `DomainRepository` methods for Watchlist persistence, exploration session history, bounded one-hop graph response, audit logging, calibration queueing, scoring profile reads, and relationship supersession/conflict recording.
- Seeded the default `balanced-v2` scoring model/profile/version from `config/model_profiles/balanced-v2.json` and `config/thresholds/default-v2.json`.
- Extended database checks to require the exploration/watchlist/scoring/change/audit/calibration tables, one active scoring profile, weight sum `1.0`, and fixed 14-day calibration cadence.
- Extended PostgreSQL integration coverage to exercise Watchlist add/list, home aggregation, exploration graph fixture disclosure, audit logs, manual calibration queueing, relationship supersession, conflict change feed, and rollback.
- Marked T203 and T206 as `DONE`.
- Marked A011, A023, and A090 as `DONE` with evidence in `tests/integration/test_database_migrations.py`.

Verification evidence:

- Local `make verify`: PASS.
- Local `env -u DATABASE_URL .venv/bin/uv run pytest tests/integration -q`: PASS with 1 expected skip.
- Local `make verify-g2-db`: FAIL CLOSED because Docker is not installed on this host.
- GitHub Actions run: `https://github.com/LinzeColin/CodexProject/actions/runs/27823282804`.
- GitHub Actions job: `82341300203`.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A011 is covered by migration upgrade/downgrade and schema checks in PostgreSQL CI.
- A023 is covered by repository integration tests that preserve superseded relationship history and emit conflict changes without deleting the source relationship.
- A090 is covered by seed/check/API tests that preserve a fixed 14-day calibration cadence and queue manual calibration without auto-activating model changes.
- A025 is partially covered at API level because graph edges expose `synthetic` and `fixture_notice`, but visible frontend content tests are still open.
- A067 remains open because scenario-level recursive exploration E2E is not implemented.

Residual risks:

- T205 remains `IN PROGRESS` until UI fixture marking and recursive scenario E2E exist.
- T1103-T1109 visual company workspace tasks remain not started.
- T1203 taxonomy/object-scope API remains not started.

## 2026-06-19 - Phase 1 / G2 T205 fixture visibility and reroot E2E pass

Status: FIXTURE VISIBILITY AND RECURSIVE SUPPLY-CHAIN E2E PASS; G2 IN PROGRESS

Completed:

- Rebuilt the Next.js workspace shell into a visual-first company workspace with a persistent EEI navigation rail, current-focus panel, central relationship graph, stage coverage rail, evidence inspector, and reroot breadcrumb.
- Added visible fixture disclosures: `Synthetic fixture`, `Fixture-only data`, `Live facts: disabled`, relationship-level fixture notices, and stage-level synthetic supply-chain coverage.
- Added a deterministic NVIDIA fixture scenario spanning materials, equipment, manufacturing, design/IP, advanced packaging, system integration, data center, energy, and customer stages.
- Added set-as-center interactions for NVIDIA -> Synthetic Advanced Foundry -> Synthetic Lithography Equipment Co. -> Synthetic Specialty Materials Co.
- Extended Playwright E2E to assert visible fixture marking and the recursive NVIDIA supply-chain reroot path.
- Marked T205 as `DONE`.
- Marked A025 and A067 as `DONE` with evidence in `tests/e2e/home.spec.ts`.
- Marked T1103, T1104, T1107, and T1108 as `IN PROGRESS` because the workspace, directional layout, inspector, and set-as-center interaction have started but their full acceptance sets are not closed.

Verification evidence:

- Local `make verify`: PASS.
- Local `npx --yes pnpm@11.8.0 --filter @eei/web build`: PASS.
- Local `npx --yes pnpm@11.8.0 --filter @eei/web test:e2e`: PASS, 2 tests.
- Local `env -u DATABASE_URL .venv/bin/uv run pytest tests/integration -q`: PASS with 1 expected skip.
- Local `make verify-g2-db`: FAIL CLOSED because Docker is not installed on this host.
- GitHub Actions run: `https://github.com/LinzeColin/CodexProject/actions/runs/27824233483`.
- GitHub Actions job: `82344470407`.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A025 is covered by Playwright assertions for visible fixture disclosure and disabled live-fact status.
- A067 is covered by Playwright assertions for NVIDIA synthetic scenario stage coverage and three-step recursive reroot path.
- A136-A152 remain open unless separately proven by visual measurement, screenshot/DOM assertions, lens behavior, semantic zoom/grouping, inspector coverage, set-as-center keyboard/touch behavior, mental-map regression, and failure-state tests.

Residual risks:

- The current workspace is still static fixture-driven and not bound to live API graph responses.
- T1105/T1106/T1109 remain not started.
- T1203 taxonomy/object-scope API remains not started.

## 2026-06-19 - Phase 1 / G2 T1103/T1104/T1107/T1108 visual workspace acceptance pass

Status: VISUAL WORKSPACE ACCEPTANCE SUBSET PASS; G2 IN PROGRESS

Completed:

- Added business, capital/control, and policy/risk synthetic relationship layers to the default NVIDIA commercial map without claiming live facts.
- Added deterministic reroot scenarios for business segment, capital commitment, and policy context nodes so every selectable node offered by the workspace has a bounded center contract.
- Split node selection from subject rerooting: clicking or keyboard-selecting a node updates the inspector while preserving the current subject until the explicit primary set-as-center action is used.
- Added inspector detail for selected node stage, role, and current subject plus set-as-center, upstream, downstream, watch, path, and evidence actions.
- Added keyboard-reachable SVG node controls and Playwright coverage proving primary navigation does not require double-click, right-click, hover, or drag.
- Added visual measurement and DOM/SVG assertions for central canvas coverage, upstream-left/focus-center/downstream-right layout, capital-above/policy-below layout, directed edges, and human-language relationship labels.
- Marked T1103, T1104, T1107, and T1108 as `DONE`.
- Marked A136, A137, A138, A139, A140, A146, A147, A148, A149, and A150 as `DONE` with evidence in `tests/e2e/home.spec.ts`.

Verification evidence:

- Local `npx --yes pnpm@11.8.0 --filter @eei/web typecheck`: PASS.
- Local `npx --yes pnpm@11.8.0 --filter @eei/web test:e2e`: PASS, 5 tests.
- Local `npx --yes pnpm@11.8.0 --filter @eei/web build`: PASS.
- Local `make verify`: PASS.
- Local `env -u DATABASE_URL .venv/bin/uv run pytest tests/integration -q`: PASS with 1 expected skip.
- Local `make verify-g2-db`: FAIL CLOSED because Docker is not installed on this host.
- GitHub Actions run: `https://github.com/LinzeColin/CodexProject/actions/runs/27825230977`.
- GitHub Actions job: `82347837228`.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A136 is covered by Playwright visual coverage measurement of `ecosystem-map-surface` within `visual-canvas`.
- A137 is covered by visible upstream, downstream, business, capital/control, and policy/risk fixture nodes and labels.
- A138 is covered by SVG bounding-box assertions for upstream-left, focus-center, and downstream-right positions.
- A139 is covered by SVG bounding-box assertions for capital/control above and policy/risk below the focus node.
- A140 is covered by directed SVG edge assertions and human-language relationship-label assertions.
- A146 is covered by selecting a node into the inspector without changing `current-focus-title`.
- A147 is covered by inspector action assertions for set-as-center, upstream, downstream, watch, path, and evidence actions.
- A148 is covered by the visible primary set-as-center action completing reroot in one action after node selection.
- A149 is covered by keyboard node selection plus single primary action navigation.
- A150 is covered by the three-step reroot path preserving the same `recursive-enterprise-map` workspace model.

Residual risks:

- The current visual workspace remains static fixture-driven and not yet bound to live API graph responses.
- T1105/T1106/T1109 remain not started, so lens filtering, semantic zoom/grouping, and retained-node mental-map behavior are still open.
- T1203 taxonomy/object-scope API remains not started.

## 2026-06-19 - Phase 1 / G2 T1105/T1106/T1109 lens zoom mental-map pass

Status: VISUAL LENS, SEMANTIC ZOOM, AND MENTAL-MAP SUBSET PASS; G2 IN PROGRESS

Completed:

- Implemented persistent canvas lenses for all, supply-chain, business-segment, capital/transaction, and policy/risk views.
- Lens switching now fades nonmatching relationship layers without navigating away from the current workspace and preserves current subject, selected node, path length, semantic zoom, and viewport anchor.
- Implemented semantic zoom levels `L0`, `L1`, `L2`, and `L3` with an explicit UI contract and machine-testable `data-semantic-zoom` state.
- Added L0 anti-hairball grouping for dense synthetic system-maker nodes with an aggregate count and a list-view expansion path.
- Added L2 evidence-state edge annotations and L3 node-role labels without relying on hover-only discovery.
- Added transition loading and fallback states for reroot requests so subject changes indicate progress and failed center requests preserve the existing nonblank canvas.
- Added directional grammar assertions for retained nodes after rerooting.
- Marked T1105, T1106, and T1109 as `DONE`.
- Marked A141, A142, A143, A144, A145, A151, and A152 as `DONE` with evidence in `tests/e2e/home.spec.ts`.

Verification evidence:

- Local `npx --yes pnpm@11.8.0 --filter @eei/web typecheck`: PASS.
- Local `npx --yes pnpm@11.8.0 --filter @eei/web test:e2e`: PASS, 9 tests.
- Local `npx --yes pnpm@11.8.0 --filter @eei/web build`: PASS.
- Local `make verify`: PASS.
- Local `env -u DATABASE_URL .venv/bin/uv run pytest tests/integration -q`: PASS with 1 expected skip.
- Local `make verify-g2-db`: FAIL CLOSED because Docker is not installed on this host.
- GitHub Actions run: `https://github.com/LinzeColin/CodexProject/actions/runs/27826081868`.
- GitHub Actions job: `82350766117`.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A141 is covered by Playwright lens switching assertions for faded nonmatching edges on the same workspace URL.
- A142 is covered by state assertions preserving subject, selected node, path length, semantic zoom, and viewport anchor across lens changes.
- A143 is covered by `L0-L3` zoom controls and semantic-zoom state assertions.
- A144 is covered by the synthetic grouped system-maker node with count `8` and an inspector list-view expansion.
- A145 is covered by default node/edge budget assertions below the 40-edge first-screen anti-hairball threshold.
- A151 is covered by directional grammar assertions after reroot from NVIDIA to Synthetic Advanced Foundry.
- A152 is covered by transition-loading and invalid-center fallback assertions that keep the canvas populated.

Residual risks:

- The current visual workspace remains static fixture-driven and not yet bound to live API graph responses.
- T1203 taxonomy/object-scope API remains not started.
- G2 remains open until T1203 and any remaining G2 gate checks are complete.

## 2026-06-19 - Phase 1 / G2 T1203 taxonomy and object-scope API pass

Status: TAXONOMY AND OBJECT-SCOPE API LOCAL PASS; G2 IN PROGRESS

Completed:

- Added a CSV-backed canonical catalog repository for relationship families, relationship types, upstream/downstream roles, supply-chain stages, industries, sectors, business segments, capital objects, domain objects, and companies.
- Added machine-readable API endpoints for `GET /v1/catalogs`, `GET /v1/catalogs/{catalogKey}`, CSV export via `format=csv`, and `GET /v1/system/object-scope`.
- Exposed an Objects and Scope navigation contract with module label, route, source document, Acceptance IDs, coverage counts, catalog summaries, and export links without requiring `DATABASE_URL`.
- Updated `specs/api_contract.yaml` for catalog inventory, catalog detail, CSV export, and object-scope responses.
- Added unit and integration coverage proving A169 catalog availability, row counts, definitions, and CSV export.
- Marked T1203 and A169 as `DONE`.

Verification evidence:

- Local `.venv/bin/uv run pytest tests/unit/test_api_health.py -q`: PASS, 7 tests.
- Local `.venv/bin/uv run python scripts/validate_contracts.py`: PASS.
- Local `.venv/bin/uv run ruff check apps/api/app/domain.py apps/api/app/domain_repository.py tests/unit/test_api_health.py tests/integration/test_database_migrations.py`: PASS.
- Local `make verify`: PASS.
- Local `env -u DATABASE_URL .venv/bin/uv run pytest tests/integration -q`: PASS with 1 expected skip.
- Local `make verify-g2-db`: FAIL CLOSED because Docker is not installed on this host.
- GitHub Actions run: `https://github.com/LinzeColin/CodexProject/actions/runs/27826870509`.
- GitHub Actions job: `82353421402`.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A169 is covered by `tests/unit/test_api_health.py`, `tests/integration/test_database_migrations.py`, and `specs/api_contract.yaml`.
- A170 is not closed by this run. The API now exposes the Objects and Scope module contract, counts, definitions, coverage, and export links, but T1204 still needs the visible navigation screen plus E2E/visual regression evidence.

Residual risks:

- The G2 task list is complete, but `data/release_gate_catalog.csv` remains `IN PROGRESS` until a separate acceptance audit resolves G2-linked IDs that are still `NOT STARTED`.
- T1204 / A170 remains open.
- MVP is not complete.

## 2026-06-19 - Phase 1 / G2 acceptance audit pass 1

Status: ACCEPTANCE TRACEABILITY PARTIAL CLOSE; G2 IN PROGRESS

Completed:

- Added schema-check assertions for required entity type labels, supply-chain attribute columns, temporal columns, research universe tier counts, industry parent/child taxonomy, and multi-label industry membership support.
- Marked A015, A016, A017, A018, A019, A020, A021, A022, A024, and A028 as `DONE` only where existing validators/integration tests now provide explicit evidence.
- Updated duplicate traceability rows for the closed IDs so each function-level trace points to concrete scripts, schemas, data files, and integration tests.
- Left A012, A013, A014, A026, A027, and A170 as `NOT STARTED`.

Verification evidence:

- Local `make verify`: PASS.
- Local `.venv/bin/uv run ruff check scripts/check_database_schema.py`: PASS.
- Local `env -u DATABASE_URL .venv/bin/uv run pytest tests/integration -q`: PASS with 1 expected skip.
- GitHub Actions run: `https://github.com/LinzeColin/CodexProject/actions/runs/27827498238`.
- GitHub Actions job: `82355514060`.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A015-A022, A024, and A028 are covered by `scripts/check_database_schema.py`, `tests/integration/test_database_migrations.py`, `specs/domain_schema.sql`, and the canonical CSV validators.
- A012 still needs a publishable relationship/event evidence enforcement contract, not only evidence tables.
- A013 still needs explicit unknown/null coercion regression tests.
- A014 still needs amount-kind compatibility and non-summing regression tests beyond the basic currency/kind constraint.
- A026 and A027 still require gold-set precision evaluation.
- A170 still requires T1204 UI plus E2E/visual regression.

Residual risks:

- `data/release_gate_catalog.csv` remains `G2=IN PROGRESS`.
- Remaining G2-linked open IDs are A012, A013, A014, A026, A027, and A170.

## 2026-06-19 - Phase 1 / G4 T1204 Objects and Scope screen

Status: OBJECTS AND SCOPE SCREEN LOCAL PASS; G4 IN PROGRESS

Completed:

- Added `/objects-scope` as a visible Objects and Scope navigation screen.
- Added a secondary system-module navigation entry labelled `对象与范围` without changing the frozen 16 primary product navigation modules.
- The screen reads canonical CSV catalogs at build time and exposes counts, definitions, coverage, primary keys, source files, and JSON/CSV export links.
- Added E2E coverage for A170 navigation visibility, counts, definitions, export links, and visual layout contract.
- Marked T1204 and A170 as `DONE`.

Verification evidence:

- Local `npx --yes pnpm@11.8.0 --filter @eei/web typecheck`: PASS.
- Local `npx --yes pnpm@11.8.0 --filter @eei/web test:e2e`: PASS, 10 tests.
- Local `npx --yes pnpm@11.8.0 --filter @eei/web build`: PASS, static routes `/` and `/objects-scope`.
- Local `make verify`: PASS.
- GitHub Actions run: `https://github.com/LinzeColin/CodexProject/actions/runs/27828194718`.
- GitHub Actions job: `82357916025`.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A170 is covered by `tests/e2e/home.spec.ts` and `apps/web/src/app/objects-scope/page.tsx`.
- At this checkpoint, G4 remained open because T1205 and T1208 were not complete.

Residual risks:

- The remaining G2-linked open IDs after A170 closure are A012, A013, A014, A026, and A027.
- At this checkpoint, G4 remained open because T1205 and T1208 were not complete.

## 2026-06-19 - Phase 1 / G2 data contract audit pass 2

Status: DATA CONTRACT LOCAL PASS; G2 IN PROGRESS

Completed:

- Added PostgreSQL-backed data quality checks for publishable relationship/event evidence coverage.
- Added unknown-semantics regression checks so intentionally unknown relationships remain `unknown` and are not coerced to numeric zero.
- Added amount semantics checks and an integration regression proving amount facts without `currency` and `amount_kind` are rejected.
- Marked A012, A013, and A014 as `DONE`.
- Left A026 and A027 as `NOT STARTED` because they require real gold precision evaluation, not synthetic fixture self-grading.

Verification evidence:

- Local `.venv/bin/uv run ruff check scripts/check_database_schema.py tests/integration/test_database_migrations.py`: PASS.
- Local `make verify`: PASS.
- Local `env -u DATABASE_URL .venv/bin/uv run pytest tests/integration -q`: PASS with 1 expected skip.
- GitHub Actions run: `https://github.com/LinzeColin/CodexProject/actions/runs/27828738097`.
- GitHub Actions job: `82359769929`.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A012 is covered by `scripts/check_database_schema.py` and `tests/integration/test_database_migrations.py`.
- A013 is covered by `scripts/check_database_schema.py`, `tests/integration/test_database_migrations.py`, and `data/mock_relationships.json`.
- A014 is covered by `specs/domain_schema.sql`, `scripts/check_database_schema.py`, and `tests/integration/test_database_migrations.py`.
- A026 and A027 remain open and should be handled by T904 quality evaluation or an explicit approved defer decision.

Residual risks:

- `data/release_gate_catalog.csv` remains `G2=IN PROGRESS` while A026 and A027 remain open.

## 2026-06-19 - Phase 1 / G2 gate close with gold-evaluation deferral

Status: G2 PASS; G3 IN PROGRESS

Completed:

- Recorded `DEFER-003` for A026/A027 because entity-resolution and relationship precision require real gold evaluation and must not be satisfied by synthetic self-graded fixtures.
- Left A026 and A027 as `NOT STARTED` in `data/acceptance_matrix.csv`.
- Advanced `data/release_gate_catalog.csv` from `G2=IN PROGRESS` to `G2=PASS` because the explicit G2 stop condition is `Migrations+catalog validation pass` and remote CI has repeatedly passed that gate.
- Advanced `G3` to `IN PROGRESS`.

Verification evidence:

- GitHub Actions run `27828738097`: PASS for strengthened A012-A014 PostgreSQL data contracts.
- GitHub Actions run `27828895082`: PASS for the final documentation commit after A012-A014 evidence recording.
- GitHub Actions run `27829131193`: PASS for the G2 gate-close commit with `DEFER-003`.
- GitHub Actions job `82361095081`: PASS.

Residual risks:

- A026 and A027 remain P0 release-quality acceptance IDs and must be implemented by T904/G9 or an explicit later release deferral.
- G3 implementation has not started yet.

## 2026-06-19 - Phase 1 / G3 T301 Home aggregation API

Status: T301 PASS; G3 IN PROGRESS

Completed:

- Added `/v1/home` aggregation fields for global search metadata, freshness, Watchlist, recent explorations, changes, active scoring profile, fixture policy, entity/relationship counts, and last/next calibration status.
- Updated the OpenAPI `HomeResponse` contract so `global_search` and `freshness` are required.
- Added PostgreSQL-backed integration assertions for search entry metadata, Watchlist presence, recent exploration state, synthetic fixture freshness, active model profile, and queued calibration status.
- Marked T301 as `DONE` in `data/task_backlog.csv`; A029/A030 remain open until the user-facing home UI and E2E coverage in T304/T306.
- Fixed a CI-only lifecycle assertion by allowing `home.changes` to be an empty list before any change records exist, then asserting non-empty home changes after supersession/conflict records are created.

Verification evidence:

- Local `make verify`: PASS.
- Local `env -u DATABASE_URL .venv/bin/uv run pytest tests/integration -q`: PASS with 1 expected skip.
- GitHub Actions run `27830933960`: FAIL in step 8 because the integration test asserted `len(home["changes"]) >= 1` before any `changes` rows existed.
- GitHub Actions job `82367238904`: FAIL.
- GitHub Actions run `27831147683`: PASS after the test lifecycle fix.
- GitHub Actions job `82367964670`: PASS.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- T301 is complete for API/data contract coverage.
- A029 and A030 remain `NOT STARTED` in `data/acceptance_matrix.csv` because their declared evidence type is E2E and will close through T304/T306, not by API assertions alone.

Residual risks:

- Home UI still needs to consume the new aggregation fields.
- Industry API/page and Watchlist item-type breadth remain open in T302/T303/T305/T306.

## 2026-06-19 - Phase 1 / G3 T302 Industry list and landscape API

Status: T302 PASS; G3 IN PROGRESS

Completed:

- Added `/v1/industries` with human-readable, versioned taxonomy rows and optional parent filtering.
- Added `/v1/industries/{industryId}/landscape` with industry summary, subindustries, chain stages, entities, bottlenecks, capital relationships, policy relationships, changes, cross-industry links, coverage, and explicit fixture/data mode.
- Added synthetic fixture industry memberships for primary, secondary, and supply-chain roles across semiconductor, AI cloud, software, energy, telecom, real-estate and industrial nodes.
- Updated OpenAPI with `IndustryLandscapeResponse`.
- Added PostgreSQL-backed integration assertions for A031 and A033, plus API-level coverage for chain stages, bottlenecks, capital, policy, and cross-industry navigation payloads.
- Marked T302 as `DONE`, A031 as `DONE`, and A033 as `DONE`; A032/A034 remain open because their declared evidence type is UI/E2E.

Verification evidence:

- Local `.venv/bin/uv run ruff check apps/api/app/domain.py apps/api/app/domain_repository.py scripts/load_synthetic_fixtures.py tests/integration/test_database_migrations.py`: PASS.
- Local `.venv/bin/uv run python scripts/validate_contracts.py`: PASS.
- Local `.venv/bin/uv run python scripts/validate_task_pack.py`: PASS.
- Local `make verify`: PASS.
- Local `env -u DATABASE_URL .venv/bin/uv run pytest tests/integration -q`: PASS with 1 expected skip.
- GitHub Actions run `27831861052`: PASS.
- GitHub Actions job `82370353436`: PASS.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A031 is covered by `/v1/industries`, `specs/api_contract.yaml`, and `tests/integration/test_database_migrations.py`.
- A033 is covered by `entity_industry_memberships`, `scripts/load_synthetic_fixtures.py`, `/v1/industries/{industryId}/landscape`, and PostgreSQL integration assertions.
- A032 and A034 remain `NOT STARTED` until T305/T306 provide user-facing industry landscape and visible cross-industry E2E evidence.

Residual risks:

- Industry landscape UI is still not implemented.
- Landscape aggregation currently uses synthetic fixture memberships and relationship rows; live ingestion still belongs to later data-ingestion tasks.

## 2026-06-19 - Phase 1 / G3 T303 Watchlist CRUD and persistence API

Status: T303 PASS; G3 IN PROGRESS

Completed:

- Added `/v1/watchlists/{watchlistId}` detail retrieval.
- Added PostgreSQL-backed Watchlist item remove/restore assertions.
- Enforced Watchlist item object validation for `entity`, `industry`, `theme`, and `facility`.
- Preserved `saved_state` for restored Watchlist items.
- Added operation-log assertions for Watchlist item removal.
- Marked T303 as `DONE`, A035 as `DONE`, and A036 as `DONE`; A037 remains open because its declared evidence type is E2E.
- Fixed a CI-only DELETE response bug by returning an explicit `Response(status_code=204)` from `/v1/watchlists/{watchlistId}/items`.

Verification evidence:

- Local `git diff --check`: PASS.
- Local `.venv/bin/uv run ruff check apps/api/app/domain.py tests/integration/test_database_migrations.py`: PASS.
- Local `.venv/bin/uv run python scripts/validate_contracts.py`: PASS.
- Local `.venv/bin/uv run python scripts/validate_task_pack.py`: PASS.
- Local `make verify`: PASS.
- Local `env -u DATABASE_URL .venv/bin/uv run pytest tests/integration -q`: PASS with 1 expected skip.
- GitHub Actions run `27832285368`: FAIL in step 8 because the DELETE Watchlist item route returned a response object with status code `None`.
- GitHub Actions job `82371769481`: FAIL.
- GitHub Actions run `27832504683`: PASS after the explicit 204 response fix.
- GitHub Actions job `82372497975`: PASS.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A035 is covered by `/v1/watchlists/{watchlistId}`, item remove/restore integration assertions, and PostgreSQL persistence checks.
- A036 is covered by item-type validation for `entity`, `industry`, `theme`, and `facility`.
- A037 remains `NOT STARTED` until T306 provides user-facing unread-change and saved-view/profile E2E evidence.

Residual risks:

- Watchlist UI still needs to consume detail, saved state, unread changes, and restore flows.
- Current Watchlist API is proven on synthetic fixtures; live ingestion and alert freshness remain later MVP tasks.

## 2026-06-19 - Phase 1 / G3 T304 User-oriented home page

Status: T304 PASS; G3 IN PROGRESS

Completed:

- Added user-oriented home entry controls to the existing Watchlist-first graph workspace without reverting to an industry-card dashboard.
- Added global search projection for `/v1/entities`, with legal-entity, industry, theme, and facility supported-type metadata.
- Added visible industries, Watchlist, recent explorations, important changes, freshness, active scoring profile, and calibration cadence/status.
- Added keyboard-reachable home controls for search, industry, Watchlist, recent exploration, and change-feed entry points.
- Added a new-user path from search query `tsmc` to a company focus within two primary actions.
- Marked T304 as `DONE`; marked A029, A030, A039, and A040 as `DONE`.
- Added missing A039/A040 acceptance traceability rows and updated the canonical trace count from 213 to 215.
- Adjusted the reroot loading state to 360ms so the existing transition test observes the loading state and the interaction remains within the documented 320-420ms animation threshold.

Verification evidence:

- Local `.venv/bin/uv run python scripts/validate_task_pack.py`: PASS.
- Local `npx --yes pnpm@11.8.0 --filter @eei/web typecheck`: PASS.
- Local `npx --yes pnpm@11.8.0 --filter @eei/web test:e2e`: PASS, 12 tests.
- Local `make verify`: PASS.
- Local `git diff --check`: PASS.
- GitHub Actions run `27833468626`: PASS.
- GitHub Actions job `82375686964`: PASS.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A029 is covered by `apps/web/src/app/page.tsx` and `tests/e2e/home.spec.ts` for global search, industries, Watchlist, recent explorations, changes, and freshness.
- A030 is covered by the model status E2E assertions for active profile, calibration status, cadence, and next scheduled date.
- A039 is covered by the search-to-company-focus E2E path with `data-primary-actions-to-focus="2"`.
- A040 is covered by keyboard E2E assertions across home search, industry, Watchlist, recent exploration, and change-feed controls.

Residual risks:

- Homepage data is still a synthetic UI projection of the already-proven `/v1/home` contract; live frontend API hydration is not implemented in T304.
- Industry landscape UI remains open in T305, and Watchlist unread/saved-view E2E remains open in T306/A037.

## 2026-06-19 - Phase 1 / G3 T305 Industry landscape page

Status: T305 PASS; G3 IN PROGRESS

Completed:

- Added `/industries` as a user-facing industry landscape page.
- Added visible industry chain stages, subindustries, top entities, bottlenecks, capital items, policy items, and changes.
- Added cross-industry navigation between semiconductors, AI cloud infrastructure, and power/data-center energy.
- Added a visible cross-industry path indicator so industry jumps are preserved and inspectable.
- Added homepage link to the industry map from the industry entry section.
- Marked T305 as `DONE`; marked A032 and A034 as `DONE`.

Verification evidence:

- Local `npx --yes pnpm@11.8.0 --filter @eei/web typecheck`: PASS.
- Local `npx --yes pnpm@11.8.0 --filter @eei/web test:e2e -- tests/e2e/industry.spec.ts`: PASS, 14 tests ran and passed.
- Local `.venv/bin/uv run python scripts/validate_task_pack.py`: PASS.
- Local `npx --yes pnpm@11.8.0 --filter @eei/web build`: PASS, static route `/industries`.
- Local `make verify`: PASS.
- Local `git diff --check`: PASS.
- GitHub Actions run `27834152257`: PASS.
- GitHub Actions job `82377987783`: PASS.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A032 is covered by `apps/web/src/app/industries/page.tsx` and `tests/e2e/industry.spec.ts`.
- A034 is covered by cross-industry navigation controls and visible path assertions in `tests/e2e/industry.spec.ts`.

Residual risks:

- Industry page still uses synthetic UI projection; live frontend API hydration remains future work.
- T306 remains open for consolidated home/industry/watchlist E2E and A037 Watchlist unread/saved-view evidence.

## 2026-06-19 - Phase 1 / G3 T306 Home, industry and Watchlist E2E

Status: T306 PASS; G3 IN PROGRESS

Completed:

- Added Watchlist unread-change and saved-view/profile state display to the home workspace.
- Added Watchlist restore behavior so selecting a Watchlist item restores saved lens, semantic zoom, profile context, and focus subject.
- Added Playwright coverage for A037 saved view/profile state restoration.
- Updated T306 to include A037 alongside A029/A035/A039/A040.
- Marked T306 as `DONE`; marked A037 as `DONE`.

Verification evidence:

- Local `npx --yes pnpm@11.8.0 --filter @eei/web typecheck`: PASS.
- Local `npx --yes pnpm@11.8.0 --filter @eei/web test:e2e`: PASS, 15 tests.
- Local `.venv/bin/uv run python scripts/validate_task_pack.py`: PASS.
- Local `npx --yes pnpm@11.8.0 --filter @eei/web build`: PASS, static routes `/`, `/industries`, and `/objects-scope`.
- Local `make verify`: PASS.
- Local `git diff --check`: PASS.
- GitHub Actions run `27834549643`: PASS.
- GitHub Actions job `82379303157`: PASS.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A037 is covered by `apps/web/src/app/page.tsx` and `tests/e2e/home.spec.ts`.
- A035 now has both PostgreSQL persistence coverage and frontend Watchlist restore E2E coverage.

Residual risks:

- The MVP still lacks full create/remove Watchlist controls in the browser UI; API persistence for those actions is proven in T303.
- G3 still remains open for model registry/config import tasks listed in the gate, unless explicitly deferred.

## 2026-06-19 - Phase 1 / G3 State history, saved views, timeline and active context

Status: T1110/T1111/T1112/T1113/T1201/T1206 PASS; G3 PASS; G4 IN PROGRESS

Completed:

- Added a shared active analysis context for model/profile/data/score snapshot versions.
- Added URL/session/localStorage workspace state for subject, selected node, lens, as-of time, filters, path, and semantic zoom.
- Added browser back, app back, and clickable breadcrumb restoration.
- Added versioned local saved views with subject, lens, time, filters, layout, notes, model version, and data snapshot.
- Added as-of timeline controls and change overlay with explicit non-real-time fixture language.
- Added cross-page active model/profile/data/score snapshot reporting on `/`, `/industries`, and `/objects-scope`.
- Added model configuration validation to `scripts/validate_task_pack.py`.
- Marked T1110, T1111, T1112, T1113, T1201, and T1206 as `DONE`.
- Marked A154, A155, A156, A157, A158, A159, A160, A171, and A178 as `DONE`.

Verification evidence:

- Local `npx --yes pnpm@11.8.0 --filter @eei/web typecheck`: PASS.
- Local `npx --yes pnpm@11.8.0 --filter @eei/web test:e2e`: PASS, 19 tests.
- Local `.venv/bin/uv run python scripts/validate_task_pack.py`: PASS, including `validate_model_config.py`.
- Local `npx --yes pnpm@11.8.0 --filter @eei/web build`: PASS.
- Local `make verify`: PASS.
- Local `git diff --check`: PASS.
- GitHub Actions run `27835479352`: PASS.
- GitHub Actions job `82382357217`: PASS.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A154/A155 are covered by `tests/e2e/state-contract.spec.ts` browser back, app back, and breadcrumb assertions.
- A156/A157 are covered by URL/session/reload assertions in `tests/e2e/state-contract.spec.ts`.
- A158/A159 are covered by versioned saved-view save/restore assertions in `tests/e2e/state-contract.spec.ts`.
- A160 is covered by timeline/as-of overlay assertions in `tests/e2e/state-contract.spec.ts`.
- A171 is covered by canonical model registry files plus `scripts/validate_model_config.py` through `scripts/validate_task_pack.py`.
- A178 is covered by cross-page active context assertions in `tests/e2e/state-contract.spec.ts`.

Residual risks:

- Saved views are local browser persistence only; production `/v1/saved-views` create/share/export remains future work.
- Timeline uses synthetic fixture snapshots; real snapshot comparison and change_events API remain future work.
- Model online edit, preview, activation, rollback, score recomputation, and operation-log UI remain future work.
- G4 remains open for recursive exploration, live context, model preview propagation, governance/status screens, accessibility/list equivalents, and visual regression/performance checks.

## 2026-06-19 - Phase 1 / G4 T1205 Development Status navigation

Status: PASS

Completed:

- Added `/development-status` as a visible development governance screen.
- Added status lanes for resolved, prototyped, specified, not started, blocked, and out-of-scope work.
- Linked tasks, risks, controls, and acceptance evidence to their canonical CSV sources.
- Added function status, recent task evidence, acceptance evidence, and risk-control panels.
- Added system navigation entry from the main workspace and Objects and Scope page.
- Marked T1205 as `DONE`; marked A173 and A174 as `DONE`.

Verification evidence:

- Local `npx --yes pnpm@11.8.0 --filter @eei/web typecheck`: PASS.
- Local `npx --yes pnpm@11.8.0 --filter @eei/web test:e2e`: PASS, 21 tests.
- Local `.venv/bin/uv run python scripts/validate_task_pack.py`: PASS.
- Local `npx --yes pnpm@11.8.0 --filter @eei/web build`: PASS, static route `/development-status`.
- Local `make verify`: PASS.
- GitHub Actions run `27836121209`: PASS.
- GitHub Actions job `82384436376`: PASS.

Acceptance status:

- A173 is covered by `apps/web/src/app/development-status/page.tsx` and `tests/e2e/development-status.spec.ts`.
- A174 is covered by visible system navigation, evidence links, and E2E link assertions in `tests/e2e/development-status.spec.ts`.

Residual risks:

- The page is server-rendered from local CSV files; live `/v1/governance/status` and `/v1/governance/traceability` APIs remain future work.
- GitHub issue forms, PR template enforcement, branch rules, release checklist, and clean-room governance validation remain future work.

## 2026-06-19 - Phase 1 / G4 T400 Bounded graph query service

Status: PASS

Completed:

- Added server-side defaults for `/v1/explore`: one hop, both directions, `supply_chain_operations`, and initial budget `max_nodes=42`, `max_edges=64`, `expand_nodes=12`.
- Enforced request hard limits through the API model: `hops<=2`, `max_nodes<=500`, `max_edges<=2000`, and `expand_nodes<=100`.
- Added bounded graph response metadata: query echo, hard limits, truncation reasons, returned counts, warnings, and continuation pointer.
- Aligned reroot-generated exploration requests with the same initial graph budget defaults.
- Updated the OpenAPI contract for default request fields, graph budget defaults, and truncation/continuation response shape.
- Added PostgreSQL-backed integration assertions for A041-A044 in `tests/integration/test_database_migrations.py`.
- Marked T400 as `DONE`; marked A041, A042, A043, and A044 as `DONE`.

Verification evidence:

- Local `.venv/bin/uv run python scripts/validate_task_pack.py`: PASS.
- Local `env -u DATABASE_URL .venv/bin/uv run pytest tests/integration -q`: PASS with 1 expected skip because the current host has no configured database.
- Local `make verify`: PASS.
- Local `git diff --check`: PASS.
- GitHub Actions run `27836910412`: PASS.
- GitHub Actions job `82386959577`: PASS.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A041 is covered by explicit `/v1/explore` request fields and query echo assertions for focus, layers, direction, hops, as-of, profile, filters, and budget.
- A042 is covered by default `/v1/explore` assertions for one-hop, both-direction, `supply_chain_operations`, and 42/64/12 initial budget.
- A043 is covered by negative 422 assertions for `hops=3`, `max_nodes=501`, and `max_edges=2001`, plus response hard-limit metadata.
- A044 is covered by over-budget assertions for truncated graph responses, reasons, bounded returned counts, warnings, and `/v1/explore/expand` continuation metadata.

Residual risks:

- Local PostgreSQL execution is still unavailable on this host; GitHub Actions run `27836910412` proved the new integration assertions against the real migration/seed/fixture path.
- `/v1/explore/expand` is referenced only as continuation metadata; the actual incremental expand endpoint remains T403.
- Two-hop traversal accepts and records `hops=2`, but bounded multi-hop traversal semantics remain future work outside T400.

## 2026-06-19 - Phase 1 / G4 Saved-view restore CI hardening

Status: PASS

Completed:

- Investigated GitHub Actions run `27836653255`, where Step 8 passed PostgreSQL integration but failed one E2E state restoration assertion.
- Identified the failure as a hydration/storage race: after reload, `restoreSavedView()` could use the default React state before `useEffect` had reloaded the saved view from `localStorage`.
- Changed `restoreSavedView()` to synchronously read the latest `localStorage` saved-view payload before applying workspace state.

Verification evidence:

- Local `npx --yes pnpm@11.8.0 --filter @eei/web test:e2e -- tests/e2e/state-contract.spec.ts`: PASS, 21 tests.
- Local `make verify`: PASS.
- Local `git diff --check`: PASS.
- GitHub Actions run `27836910412`: PASS.
- GitHub Actions job `82386959577`: PASS.

Residual risks:

- Saved-view persistence is still browser-local; production shared saved-view APIs remain future work.

## 2026-06-19 - Phase 1 / G4 T401 Exploration session and URL state

Status: PASS

Completed:

- Added migration `0002_exploration_state` to persist exploration `state_version`, `direction`, `hops`, and `budget` on `exploration_sessions`.
- Updated the logical PostgreSQL schema and schema checker so exploration session state columns are required.
- Added canonical `state` and `state.url_state` to `/v1/explore` responses, including URL query fields and a full `restore_payload`.
- Updated `/v1/explore` create/update paths to persist direction, hops, budget, active layers, as-of time, scoring profile, and filters.
- Updated recent exploration rows returned by `/v1/home` to include persisted session state fields.
- Added integration assertions that serialize focus/layers/direction/time/profile/filters into URL state, POST the restore payload, and verify the same session state is persisted.
- Marked T401 and A051 as `DONE`.

Verification evidence:

- Local `make verify`: PASS.
- Local `env -u DATABASE_URL .venv/bin/uv run pytest tests/integration -q`: PASS with 1 expected skip because the current host has no configured PostgreSQL.
- Local `git diff --check`: PASS.
- GitHub Actions run `27837609322`: PASS.
- GitHub Actions job `82389170752`: PASS.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A051 is covered by `state.url_state.query`, `state.url_state.query_string`, and `state.url_state.restore_payload` assertions in `tests/integration/test_database_migrations.py`.
- Existing G3 URL/session browser coverage in `tests/e2e/state-contract.spec.ts` remains part of the traceability evidence for A051.

Residual risks:

- GitHub Actions run `27837609322` proved the new migration and integration assertions against PostgreSQL.
- T404 still owns breadcrumb/browser-history synchronization for reroot flows; T401 only closes canonical session and URL state serialization/restoration.

## 2026-06-19 - Phase 1 / G4 T402 Reroot inherited and reset state

Status: REMOTE CI PASS

Completed:

- Updated `/v1/explore/reroot` so default reroot preserves active layers, direction, hops, as-of time, scoring profile, filters, and graph budget.
- Updated `inherit_state=false` reroot to reset to default exploration state: `supply_chain_operations`, `both`, one hop, default 42/64/12 budget, no as-of time, no scoring profile, and empty filters.
- Added integration assertions that reroot from NVIDIA to a facility entity preserves state by default.
- Added integration assertions that reroot from the same session to a theme entity resets state and persists the reset values in `exploration_sessions`.
- Updated the OpenAPI contract so `inherit_state` is optional with default `true`.
- Canonicalized UTC `datetime` API serialization to `Z` so inherited reroot state matches URL/session restore contracts after PostgreSQL round-trips.
- Aligned the reset-reroot fixture assertion with `data/mock_entities.json` for the `AI Infrastructure` theme entity.
- Marked T402, A045, A046, and A047 as `DONE`.

Verification evidence:

- Local `make verify`: PASS.
- Local `env -u DATABASE_URL .venv/bin/uv run pytest tests/integration -q`: PASS with 1 expected skip because the current host has no configured PostgreSQL.
- Local `git diff --check`: PASS.
- GitHub Actions run `27838042448`: FAIL in step 8 on inherited `as_of` timestamp serialization (`+00:00` vs `Z`); fixed by canonical UTC serialization.
- GitHub Actions run `27838285776`: FAIL in step 8 on reset-reroot fixture display name (`AI Infrastructure` vs stale expected label); fixed by aligning the test with the fixture catalog.
- GitHub Actions run `27838436423`: PASS.
- GitHub Actions job `82391789245`: PASS.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A045 is covered by rerooting to non-legal-entity focusable entities in `tests/integration/test_database_migrations.py`.
- A046 is covered by inherited state assertions for layers, time, profile, filters, direction, hops, and budget.
- A047 is covered by reset/default state assertions plus direct persisted-session checks.

Residual risks:

- At T402 closeout, T404 still owned breadcrumb/browser-history synchronization and T408 still owned critical three-reroot E2E; both are now completed below.

## 2026-06-19 - Phase 1 / G4 T403 Incremental directional expand

Status: REMOTE CI PASS

Completed:

- Added the FastAPI `/v1/explore/expand` route with an explicit `ExpandRequest` model.
- Added repository support for incremental expansion from a selected `anchor_entity_id` without changing the session root.
- Added layer-to-relationship-family filtering so graph queries and expansions only return selected relationship families.
- Added expand-mode graph bounds so incremental expansion returns at most `expand_nodes` edges and `expand_nodes + 1` nodes including the anchor.
- Added integration assertions that upstream supply-chain expansion from NVIDIA returns only selected direction/layer edges within the expand budget.
- Marked T403 and A052 as `DONE`.

Verification evidence:

- Local `make verify`: PASS.
- Local `env -u DATABASE_URL .venv/bin/uv run pytest tests/integration -q`: PASS with 1 expected skip because the current host has no configured PostgreSQL.
- Local `git diff --check`: PASS.
- GitHub Actions run `27839023906`: PASS.
- GitHub Actions job `82393647163`: PASS.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A052 is covered by `/v1/explore/expand` integration assertions for upstream direction, `supply_chain_operations` layer filtering, and `expand_nodes=2` node/edge bounds.

Residual risks:

- At T403 closeout, T405 still owned full graph/table explorer node actions and T406 still owned bounded evidence-bearing path queries; both are now completed below, with T406 awaiting remote PostgreSQL CI evidence.

## 2026-06-19 - Phase 1 / G4 T404 Breadcrumb and browser history synchronization

Status: REMOTE CI PASS

Completed:

- Added stable workspace attributes for current focus key and serialized focus path so browser/history assertions can compare UI state and URL state.
- Strengthened the state-contract E2E to cover reroot browser back, browser forward, app back, full breadcrumb visibility, and clickable intermediate breadcrumb restoration.
- Marked T404, A049, and A050 as `DONE`; A051 was already done by T401 and remains covered by state-contract URL assertions.

Verification evidence:

- Local `npx --yes pnpm@11.8.0 --filter @eei/web typecheck`: PASS.
- Local `npx --yes pnpm@11.8.0 --filter @eei/web test:e2e -- tests/e2e/state-contract.spec.ts`: PASS, 21 tests.
- Local `make verify`: PASS.
- Local `git diff --check`: PASS.
- GitHub Actions run `27839493483`: PASS.
- GitHub Actions job `82395103164`: PASS.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A049 is covered by full path breadcrumb assertions for `nvidia.foundry.equipment.materials` and clickable restoration to `nvidia.foundry`.
- A050 is covered by browser `goBack`, browser `goForward`, and in-app back assertions restoring identical focus/path state.
- A051 remains covered by URL/session path and state assertions in `tests/e2e/state-contract.spec.ts` plus the T401 API state contract.

Residual risks:

- At T404 closeout, T408 still owned the critical three-reroot E2E acceptance A048; T408 is now completed below.

## 2026-06-19 - Phase 1 / G4 T405 Graph table explorer and node actions

Status: REMOTE CI PASS

Completed:

- Added selected-node actions for reroot, upstream, downstream, path, compare, pin, Watchlist and evidence entry points.
- Added pinned, comparison and Watchlist state summaries that persist while the user changes semantic zoom/layout level.
- Added a filterable graph table alternative backed by the same visible relationship edges as the graph.
- Added explicit visual semantics metadata and copy stating that layout position is not control semantics and color is not the only encoding; labels, arrows, stages, roles and evidence carry semantics.
- Strengthened the home E2E suite for node actions, layout-preserved pinned/comparison state, table filtering and non-color encoding semantics.
- Marked T405, A053, A054, A055 and A058 as `DONE`.

Verification evidence:

- Local `npx --yes pnpm@11.8.0 --filter @eei/web test:e2e -- tests/e2e/home.spec.ts`: PASS, 22 tests.
- Local `npx --yes pnpm@11.8.0 --filter @eei/web typecheck`: PASS.
- Local `make verify`: PASS.
- Local `git diff --check`: PASS.
- GitHub Actions run `27840198892`: PASS.
- GitHub Actions job `82397301394`: PASS.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A053 is covered by visible action buttons and action-state assertions in `tests/e2e/home.spec.ts`.
- A054 is covered by pin/compare persistence after semantic zoom/layout changes.
- A055 is covered by the `graph-table-alternative` table and `graph-table-filter` lens assertions.
- A058 is covered by explicit semantic metadata plus visible arrow and edge-label assertions.

Residual risks:

- T406 is completed below and awaits remote PostgreSQL CI evidence.
- T407 is completed below and awaits remote CI evidence.
- T408 is completed below and awaits remote CI evidence.

## 2026-06-19 - Phase 1 / G4 T406 Bounded evidence-bearing path queries

Status: REMOTE CI PASS

Completed:

- Added `GET /v1/paths` with `from`, `to`, `path_type`, `max_length` and `as_of` query parameters.
- Implemented bounded recursive path search with `max_length <= 8`, `max_paths <= 8`, no repeated nodes, active/supersession filtering and as-of filtering.
- Supported `shortest`, `upstream`, `downstream`, `control`, `capital`, `policy` and `bottleneck` path types with explicit relationship-family filters.
- Required every returned path edge to have at least one `relationship_evidence` row and expanded source document evidence into the response.
- Added OpenAPI `PathResponse`, `PathResult` and `PathEdge` contracts for evidence-bearing bounded paths.
- Added PostgreSQL integration assertions for all seven A056 path types, evidence/source payloads, path bounds, hard limit metadata and `max_length=9` rejection.
- Marked T406 and A056 as `DONE`.

Verification evidence:

- Local `make verify`: PASS.
- Local `env -u DATABASE_URL .venv/bin/uv run pytest tests/integration -q`: PASS with 1 expected skip because the current host has no configured PostgreSQL.
- Local `git diff --check`: PASS.
- GitHub Actions run `27840744734`: PASS.
- GitHub Actions job `82399027153`: PASS.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A056 is covered by `tests/integration/test_database_migrations.py` assertions over `/v1/paths` for shortest/upstream/downstream/control/capital/policy/bottleneck path types.

Residual risks:

- T407 is completed below and awaits remote CI evidence.
- T408 is completed below and awaits remote CI evidence.

## 2026-06-19 - Phase 1 / G4 T407 Inclusion and truncation explanations

Status: REMOTE CI PASS

Completed:

- Added a visible inclusion/truncation explanation panel to the graph inspector.
- Exposed machine-readable UI contract attributes for inclusion sorting keys, truncation reasons and continuation endpoint.
- Documented the inclusion order as active lens, evidence-bearing edges, confidence, observed time and stable id.
- Documented truncation reasons as `edge_budget` and `node_budget`, with returned counts and `/v1/explore/expand` continuation metadata.
- Strengthened home E2E coverage to assert the visible explanation and contract attributes.
- Marked T407 and A057 as `DONE`; A044 remains `DONE` with additional UI evidence.

Verification evidence:

- Local `npx --yes pnpm@11.8.0 --filter @eei/web test:e2e -- tests/e2e/home.spec.ts`: PASS, 22 tests.
- Local `make verify`: PASS.
- Local `git diff --check`: PASS.
- GitHub Actions run `27841131928`: PASS.
- GitHub Actions job `82400216009`: PASS.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A057 is covered by `tests/e2e/home.spec.ts` assertions for `inclusion-truncation-explanation`.
- A044 retains API coverage from T400 and now has UI coverage for visible truncation reasons and continuation metadata.

Residual risks:

- T408 is completed below and awaits remote CI evidence.

## 2026-06-19 - Phase 1 / G4 T408 Critical three-reroot E2E

Status: REMOTE CI PASS

Completed:

- Added a dedicated A048 state-contract E2E named `A048 completes three consecutive semiconductor reroots without fallback`.
- The test reroots from NVIDIA to `Synthetic Advanced Foundry`, then `Synthetic Lithography Equipment Co.`, then `Synthetic Specialty Materials Co.`.
- The test asserts canonical path state, URL path serialization, `data-reroot-state=ready`, final `data-path-length=4`, full breadcrumb visibility, the materials graph node, and no transition fallback.
- Marked T408 and A048 as `DONE`.

Verification evidence:

- Local `npx --yes pnpm@11.8.0 --filter @eei/web test:e2e -- tests/e2e/state-contract.spec.ts`: PASS, 23 tests.
- Local `make verify`: PASS.
- GitHub Actions run `27841663304`: PASS.
- GitHub Actions job `82401845967`: PASS.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A048 is covered by `tests/e2e/state-contract.spec.ts` with three consecutive semiconductor-fixture reroots ending at `nvidia.foundry.equipment.materials`.

Residual risks:

- T409 is completed below and awaits remote CI evidence.

## 2026-06-19 - Phase 1 / G4 T409 Cross-industry reroot E2E

Status: REMOTE CI PASS

Completed:

- Added a visible cross-industry reroot notice to the commercial-map workspace.
- Added a deterministic focus-to-industry mapping for the synthetic fixture path.
- The workspace now exposes `data-cross-industry` and `data-industry-path` attributes for the current reroot path.
- Added an A034 state-contract E2E named `A034 visibly marks cross-industry reroot path from chips to energy`.
- The test reroots from NVIDIA to cloud, data center and grid utility, then verifies visible industry path, breadcrumb and ready reroot state.
- Marked T409 as `DONE`; A034 remains `DONE` with additional workspace reroot evidence.

Verification evidence:

- Local `npx --yes pnpm@11.8.0 --filter @eei/web test:e2e -- tests/e2e/state-contract.spec.ts`: PASS, 24 tests.
- Local `make verify`: PASS.
- GitHub Actions run `27842200422`: PASS.
- GitHub Actions job `82403504484`: PASS.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A034 is covered by `/industries` cross-industry navigation and now by `tests/e2e/state-contract.spec.ts` workspace reroot assertions for `nvidia.cloud.datacenter.energy`.

Residual risks:

- T1114/T1115/T1116/T1117 are completed below and await remote CI evidence.

## 2026-06-19 - Phase 1 / G4 T1114-T1117 Accessibility and UI copy contract

Status: REMOTE CI PASS

Completed:

- Strengthened the graph table alternative into a graph-equivalent accessible list with `direction`, `type`, `evidence_status` and `observed_at` fields.
- Added visible evidence labels and retained non-color encodings through labels, arrows, stages, roles and evidence pills.
- Added global visible focus styling and E2E assertions for keyboard-reachable graph node, primary center action and table filter.
- Added target-size assertions for dense graph nodes and equivalent controls.
- Added `scripts/validate_ui_copy.py` and wired `copy-lint` into `make verify`.
- Replaced visible internal copy such as `Rerooted`, `Profile`, `Calibration` and `Gate` with user-facing wording.
- Marked T1114, T1115, T1116, T1117 and A161-A166 as `DONE`.

Verification evidence:

- Local `.venv/bin/uv run python scripts/validate_ui_copy.py`: PASS.
- Local `npx --yes pnpm@11.8.0 --filter @eei/web test:e2e -- tests/e2e/home.spec.ts`: PASS, 25 tests.
- Local `make verify`: PASS.
- GitHub Actions run `27842880134`: PASS.
- GitHub Actions job `82405633120`: PASS.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A161/A162 are covered by `graph-table-alternative` contract attributes and table row assertions in `tests/e2e/home.spec.ts`.
- A163/A164 are covered by keyboard focus and 24px target-size assertions in `tests/e2e/home.spec.ts`.
- A165 is covered by non-color encoding metadata and evidence labels in `apps/web/src/app/page.tsx`.
- A166 is covered by `scripts/validate_ui_copy.py` and the `copy-lint` Makefile target.

Residual risks:

- T1207 is completed below and awaits remote CI evidence.

## 2026-06-19 - Phase 1 / G4 T1207 Model preview context propagation

Status: REMOTE CI PASS

Completed:

- Added a typed shared analysis context hook with active and preview model/profile/data/score snapshots.
- Added a visible model preview panel on the commercial-map workspace with explicit preview scope and storage contract metadata.
- Persisted preview profile and score snapshot metadata into versioned saved-view records.
- Propagated preview context from the home workspace to the industry landscape page through session localStorage.
- Added an E2E contract that previews a supply-chain-emphasis model edit, saves the previewed view, navigates to `/industries`, returns to `/`, and clears the preview.
- Marked T1207 as `DONE`; A157/A158/A178 remain `DONE` with added preview propagation evidence.

Verification evidence:

- Local `npx --yes pnpm@11.8.0 --filter @eei/web test:e2e -- tests/e2e/state-contract.spec.ts`: PASS, 26 tests.
- Local `make verify`: PASS.
- Local `git diff --check`: PASS.
- GitHub Actions run `27843659754`: PASS.
- GitHub Actions job `82408058091`: PASS.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A157 is covered by reload/session context assertions in `tests/e2e/state-contract.spec.ts`.
- A158 is covered by saved-view preview profile and score snapshot persistence assertions.
- A178 is covered by cross-page active/preview context assertions on `/` and `/industries`.

Residual risks:

- T1207 is a local session preview contract, not a real online model editor. Real edit, activation, rollback, score recompute and model-center UI remain in T600-T604.

## 2026-06-19 - Phase 1 / G5 T1208 Global model/data version consistency E2E

Status: REMOTE CI PASS

Completed:

- Extended the global active context E2E to include `/development-status` in addition to `/`, `/industries` and `/objects-scope`.
- Confirmed the development governance screen participates in the same active model/profile/data/score snapshot contract through `data-active-*` attributes.
- Marked T1208 as `DONE`; A178 remains `DONE` with added all-current-navigation-page consistency evidence.

Verification evidence:

- Local `./node_modules/.bin/playwright test --config=../../playwright.config.ts state-contract.spec.ts --grep "reports one active model profile" --workers=1`: PASS, 1 test.
- Local `./node_modules/.bin/playwright test --config=../../playwright.config.ts --workers=1`: PASS, 26 tests.
- Local `make verify`: PASS.
- Local `git diff --check`: PASS.
- GitHub Actions run `27844479321`: PASS.
- GitHub Actions job `82410608346`: PASS.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A178 is covered by cross-page active context assertions on `/`, `/industries`, `/objects-scope` and `/development-status`.

Residual risks:

- T1208 only verifies the active context contract across current navigation pages; real model editing, activation, rollback and recalculation remain in T600-T604.

## 2026-06-19 - Phase 1 / G5 T1209 Prototype parity smoke test

Status: REMOTE CI PASS

Completed:

- Added `scripts/validate_prototype_parity.py` to compare `prototype/index.html` and `prototype/standalone.html` by bytes and SHA-256 hash.
- The parity validator rejects external script and stylesheet references so the canonical prototype cannot silently point at stale JS/CSS.
- The validator asserts required prototype views and graph/model DOM anchors are present in the canonical HTML.
- Wired `validate-prototype-parity` into `make verify` and registered the script in the repository document registry.
- Marked T1209 and A176 as `DONE`.

Verification evidence:

- Local `.venv/bin/uv run python scripts/validate_prototype_parity.py`: PASS; canonical hash `7f06f96c917ff14fc42c94de09b0e5f89f622a22a44a0dd64da3941429486719`.
- Local `make verify`: PASS.
- Local `git diff --check`: PASS.
- GitHub Actions run `27844984873`: PASS.
- GitHub Actions job `82412132613`: PASS.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A176 is covered by `scripts/validate_prototype_parity.py`, `prototype/index.html`, `prototype/standalone.html` and the `validate-prototype-parity` Makefile target.

Residual risks:

- T1209 validates static parity and stale asset references; it does not replace later visual-regression screenshots or clean-room release packaging in T1118/T1119/T1123/T1215.

## 2026-06-19 - Phase 1 / G8 T1210 GitHub governance contract and required checks

Status: REMOTE CI PASS

Completed:

- Added `.github/branch_protection.md` as the versioned source contract for required `main` branch protection.
- Added `.github/release_checklist.md` for release gate commands, required checks, manifest/checksum refresh and rollback evidence.
- Expanded `.github/CODEOWNERS` to cover `.github/` and `scripts/`.
- Added `scripts/validate_github_governance.py` to validate issue forms, PR template, CODEOWNERS, governance workflow, release categories, branch protection contract, release checklist and backup registry coverage.
- Wired `validate-github-governance` into `make verify` and `ruff`.
- Registered the new governance files and validator in `data/github_document_registry.csv`.
- Stabilized the reroot fallback E2E by removing assertions on a transient loading overlay while retaining focus, fallback, graph nonblank and directional-grammar assertions.
- Marked T1210 and A177 as `DONE`; A175 remains `NOT STARTED` until T1211 adds immutable release artifact and operation-log evidence.

Verification evidence:

- Local `.venv/bin/uv run python scripts/validate_github_governance.py`: PASS.
- Local `make verify`: PASS.
- Local `git diff --check`: PASS.
- Local `./node_modules/.bin/playwright test --config=../../playwright.config.ts home.spec.ts --grep "Objects and Scope|directional grammar" --workers=1`: PASS, 2 tests.
- Local `npx --yes pnpm@11.8.0 --filter @eei/web test:e2e`: PASS, 26 tests.
- GitHub Actions run `27845697888`: FAIL, isolated to brittle transient loading overlay E2E assertion and fixed by `tests/e2e/home.spec.ts`.
- GitHub Actions run `27846173368`: PASS.
- GitHub Actions job `82415726115`: PASS.

Acceptance status:

- A177 is covered by `.github/CODEOWNERS`, `.github/branch_protection.md`, `.github/release_checklist.md`, `.github/workflows/governance-validation.yml`, `scripts/validate_github_governance.py` and `data/github_document_registry.csv`.

Residual risks:

- Actual GitHub branch protection must still be applied in repository settings or through the GitHub API; T1210 versions and validates the required contract.
- A175 still depends on T1211 reproducible release evidence and immutable operation-log/release artifacts.

## 2026-06-19 - Phase 1 / G9 T1211 Reproducible release evidence

Status: REMOTE CI PASS

Completed:

- Added `scripts/manage_release_artifacts.py` to generate and validate release artifacts from tracked repository paths plus required release evidence files.
- Regenerated `manifest.txt`, `DIRECTORY_TREE.txt` and `CHECKSUMS.sha256` for the current EEI product repository tree.
- Added `artifacts/release_evidence_t1211.json` with release commands, rollback procedure, artifact paths and remote verification fields.
- Added `artifacts/release_operation_log_t1211.jsonl` with one immutable `release_artifact_publish` operation for T1211.
- Wired `validate-release-artifacts` into `make verify`.
- Marked T1211 and A175 as `DONE`; A177 remains `DONE` with release artifact evidence added.

Verification evidence:

- Local `.venv/bin/uv run python scripts/manage_release_artifacts.py generate`: PASS; manifest paths 273, checksum paths 272.
- Local `.venv/bin/uv run python scripts/manage_release_artifacts.py validate`: PASS.
- Local `sha256sum -c CHECKSUMS.sha256`: PASS.
- Local `make verify`: PASS.
- GitHub Actions run `27846828768`: PASS.
- GitHub Actions job `82417667186`: PASS.

Acceptance status:

- A175 is covered by `.github/pull_request_template.md`, `artifacts/release_evidence_t1211.json`, `artifacts/release_operation_log_t1211.jsonl`, `manifest.txt`, `DIRECTORY_TREE.txt`, `CHECKSUMS.sha256` and `scripts/manage_release_artifacts.py`.
- A177 remains covered by GitHub governance files plus manifest/checksum/release evidence.

Residual risks:

- T1211 does not replace T1215 clean-room Markdown/CSV/JSON/GitHub/prototype/PDF/ZIP validation.

## 2026-06-19 - Phase 1 / G0 T1212 GitHub governance consistency workflow

Status: REMOTE CI PASS

Completed:

- Added `scripts/validate_governance_consistency.py` to validate governance workflow path triggers, required workflow commands, `make verify` wiring, P0 function traceability and release clean-room preflight files.
- Wired `validate-governance-consistency` into `make verify` and the packaged `.github/workflows/governance-validation.yml`.
- Added acceptance evidence files for A182, A183 and the A200 clean-room preflight contract.
- Marked T1212, A182 and A183 as `DONE`; A200 remains open for the final T1215 clean-room release run.

Verification evidence:

- Local `.venv/bin/uv run python scripts/validate_governance_consistency.py`: PASS.
- Local `.venv/bin/uv run python scripts/validate_github_governance.py`: PASS.
- Local `.venv/bin/uv run python scripts/manage_release_artifacts.py validate`: PASS.
- Local `sha256sum -c CHECKSUMS.sha256`: PASS.
- Local `make verify`: PASS.
- Local `git diff --check`: PASS.
- GitHub Actions run `27847728171`: PASS.
- GitHub Actions job `82420393869`: PASS.

Acceptance status:

- A182 is covered by `.github/workflows/governance-validation.yml`, `Makefile`, `scripts/validate_governance_consistency.py`, `scripts/validate_github_governance.py` and `artifacts/tests/a182/t1212_governance_consistency_workflow.json`.
- A183 is covered by `scripts/validate_governance_consistency.py`, the canonical function/task/acceptance/traceability CSVs and `artifacts/tests/a183/t1212_p0_traceability_validator.json`.
- A200 has a T1212 preflight contract in `artifacts/tests/a200/t1212_clean_room_preflight.json`, but remains `NOT_STARTED` until T1215 completes the full clean-room release verification.

Residual risks:

- T1212 validates that the clean-room prerequisites exist and are checksummed; it does not run the final Markdown/CSV/JSON/GitHub/prototype/PDF/ZIP clean-room package validation.

## 2026-06-19 - Phase 1 / G0 T1213 Development status and traceability artifacts

Status: REMOTE CI PASS

Completed:

- Added `scripts/manage_development_status_artifacts.py` to generate and validate `artifacts/development_status_summary_t1213.json`, `artifacts/requirement_function_task_test_traceability_t1213.csv`, A183 evidence and A184 evidence.
- Wired `validate-development-status-artifacts` into `make verify` and `.github/workflows/governance-validation.yml`.
- Marked T1213 and A184 as `DONE`; A183 remains `DONE` with added T1213 matrix evidence.
- Updated stale traceability count documentation to the canonical 221 rows in `data/acceptance_traceability.csv`.

Verification evidence:

- Local `.venv/bin/uv run python scripts/manage_development_status_artifacts.py generate`: PASS.
- Local `.venv/bin/uv run python scripts/manage_development_status_artifacts.py validate`: PASS.
- Local `.venv/bin/uv run python scripts/validate_governance_consistency.py`: PASS.
- Local `.venv/bin/uv run python scripts/validate_github_governance.py`: PASS.
- Local `.venv/bin/uv run ruff check scripts/manage_development_status_artifacts.py scripts/validate_governance_consistency.py scripts/validate_github_governance.py`: PASS.
- Local `make verify`: PASS.
- Local `git diff --check`: PASS.
- GitHub Actions run `27848308523`: PASS.
- GitHub Actions job `82422115246`: PASS.

Acceptance status:

- A183 is additionally covered by `artifacts/requirement_function_task_test_traceability_t1213.csv` and `artifacts/tests/a183/t1213_requirement_function_task_test_traceability.json`.
- A184 is covered by `scripts/manage_development_status_artifacts.py`, `data/development_status_ledger.csv`, `data/resolved_unresolved_register.csv`, `artifacts/development_status_summary_t1213.json` and `artifacts/tests/a184/t1213_development_status_ledger.json`.

Residual risks:

- T1213 does not close risk-control traceability for high-risk items; that remains T1214 / A185.

## 2026-06-19 - Phase 1 / G0 T1214 Risk-control traceability artifacts

Status: REMOTE CI PASS

Completed:

- Added `scripts/manage_risk_control_artifacts.py` to generate and validate `artifacts/risk_control_summary_t1214.json`, `artifacts/risk_control_mapping_t1214.csv` and `artifacts/tests/a185/t1214_high_risk_traceability.json`.
- Wired `validate-risk-control-artifacts` into `make verify` and `.github/workflows/governance-validation.yml`.
- Filled missing T1214/A185 mappings for high/critical risk rows and replaced high-risk `cross-cutting` placeholders with concrete function IDs.
- Marked T1214 and A185 as `DONE`.

Verification evidence:

- Local `.venv/bin/uv run python scripts/manage_risk_control_artifacts.py generate`: PASS.
- Local `.venv/bin/uv run python scripts/manage_risk_control_artifacts.py validate`: PASS.
- Local `.venv/bin/uv run python scripts/validate_governance_consistency.py`: PASS.
- Local `.venv/bin/uv run python scripts/validate_github_governance.py`: PASS.
- Local `.venv/bin/uv run ruff check scripts/manage_risk_control_artifacts.py scripts/validate_governance_consistency.py scripts/validate_github_governance.py`: PASS.
- Local `make verify`: PASS.
- GitHub Actions run: `https://github.com/LinzeColin/CodexProject/actions/runs/27848881308`.
- GitHub Actions job: `82423801118`.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A185 is covered by `scripts/manage_risk_control_artifacts.py`, `data/risk_register.csv`, `data/risk_control_traceability.csv`, `artifacts/risk_control_summary_t1214.json`, `artifacts/risk_control_mapping_t1214.csv` and `artifacts/tests/a185/t1214_high_risk_traceability.json`.

Residual risks:

- T1214 validates risk-control traceability; final clean-room Markdown/CSV/JSON/GitHub/prototype/PDF/ZIP verification remains T1215 / A200.

## 2026-06-19 - Phase 1 / G9 T1215 Clean-room release validation

Status: REMOTE CI PASS

Completed:

- Added `scripts/manage_clean_room_release.py` to generate and validate `artifacts/tests/a200/t1215_clean_room_release.json` and `artifacts/tests/a200/Enterprise_Ecosystem_Intelligence_clean_room_t1215.zip`.
- The clean-room ZIP includes an internal `PACKAGE_MANIFEST.json` and `PACKAGE_CHECKSUMS.sha256`, excludes its own package/evidence files, and validates Markdown, CSV, JSON, GitHub workflow, prototype and PDF categories.
- Wired `validate-clean-room-release` into `make verify` and `.github/workflows/governance-validation.yml`.
- Marked T1215 and A200 as `DONE`.

Verification evidence:

- Local `.venv/bin/uv run python scripts/manage_clean_room_release.py generate`: PASS.
- Local `.venv/bin/uv run python scripts/manage_clean_room_release.py validate`: PASS.
- Local `make verify`: PASS.
- Local `sha256sum --quiet -c CHECKSUMS.sha256`: PASS.
- GitHub Actions run: `https://github.com/LinzeColin/CodexProject/actions/runs/27849578583`.
- GitHub Actions job: `82425860903`.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A200 is covered by `scripts/manage_clean_room_release.py`, `scripts/validate_governance_consistency.py`, `scripts/manage_release_artifacts.py`, `artifacts/tests/a200/t1215_clean_room_release.json` and `artifacts/tests/a200/Enterprise_Ecosystem_Intelligence_clean_room_t1215.zip`.

Residual risks:

- T1215 closes A200 clean-room release verification only. A180, A181, A186 and A199 remain open and are not claimed by this run.

## 2026-06-19 - Phase 1 / G5 T500 Entity dossier and human summary API

Status: REMOTE CI PASS

Completed:

- Expanded `/v1/entities/{entityId}` from a thin entity summary into an entity dossier response with aliases, industry memberships, relationship-family counts, dossier layers, recent events, freshness, coverage and `human_summary`.
- Added dossier layers for business, group, dependencies, capital, policy and signals without introducing new database tables or product dependencies.
- Added explicit data-gap language for missing capital and policy records so unknown fixture coverage is not rendered as zero or false.
- Updated `specs/api_contract.yaml` with `EntityDossier`, `EntityDossierLayer` and `EntityDossierHumanSummary` contract fields.
- Added integration assertions that every 30-row fixture seed from `data/mock_entities.json` opens through `/v1/entities/{entityId}` and that NVIDIA's golden dossier covers business, group, dependencies, capital, policy, signals and data gaps.
- Added A059 and A060 evidence artifacts under `artifacts/tests/a059/` and `artifacts/tests/a060/`.
- Marked T500, A059 and A060 as `DONE`; FUN-EXP-03 is now `PARTIAL` because T501-T508 workspace/detail tasks remain open.

Verification evidence:

- Local `.venv/bin/uv run python scripts/validate_contracts.py`: PASS.
- Local `.venv/bin/uv run python scripts/validate_catalog_integrity.py`: PASS.
- Local `.venv/bin/uv run ruff check apps/api/app/domain_repository.py tests/integration/test_database_migrations.py`: PASS.
- Local `.venv/bin/uv run pytest tests/unit -q`: PASS.
- Local `.venv/bin/uv run python scripts/manage_development_status_artifacts.py validate`: PASS.
- Local `.venv/bin/uv run pytest tests/integration -q`: SKIPPED because this host has no `.env` and no Docker-backed PostgreSQL.
- GitHub Actions run: `https://github.com/LinzeColin/CodexProject/actions/runs/27850433769`.
- GitHub Actions job: `82428282411`.
- GitHub Actions step `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A059 is covered by `apps/api/app/domain_repository.py`, `tests/integration/test_database_migrations.py` and `artifacts/tests/a059/t500_entity_focus_dossier_api.json`.
- A060 is covered by `apps/api/app/domain_repository.py`, `specs/api_contract.yaml`, `tests/integration/test_database_migrations.py` and `artifacts/tests/a060/t500_human_summary_dossier_api.json`.

Residual risks:

- T500 does not implement the full eight-layer workspace UI; T501-T508 still own group structure, supply-chain, capital/policy/technology layers, strategic signals, evidence drawer, timeline and export UX.
- Local database integration could not run on this host; GitHub Actions PostgreSQL validation passed and is the database/E2E evidence for this run.

## 2026-06-20 - Phase 1 / G5 T501 Group, business and structure workspace

Status: REMOTE CI PASS

Completed:

- Added `/v1/entities/{entityId}/empire` as the bounded company empire structure endpoint without adding new database tables.
- Added an eight-layer company focus workspace strip for group structure, business segments, supply chain, capital network, M&A transactions, control relationships, policy environment and strategic signals.
- Added a structure matrix that separates legal group, business segment, brand, product and facility rows.
- Preserved missing coverage semantics for brands and adjacent ecosystem semantics for facilities.
- Added the explicit rule that commercial empire is an ecosystem relationship view, not a legal-control assertion.
- Added A061, A062 and A063 evidence artifacts under `artifacts/tests/a061/`, `artifacts/tests/a062/` and `artifacts/tests/a063/`.
- Marked T501, A061, A062 and A063 as `DONE`; FUN-EXP-03 remains `PARTIAL` because T502/T503/T506-T508 still own deeper layer detail, evidence drawer and timeline scope.

Verification evidence:

- Local `.venv/bin/uv run ruff check apps/api/app/domain.py apps/api/app/domain_repository.py tests/integration/test_database_migrations.py`: PASS.
- Local `.venv/bin/uv run python scripts/validate_contracts.py`: PASS.
- Local `.venv/bin/uv run pytest tests/unit -q`: PASS.
- Local `npx --yes pnpm@11.8.0 --filter @eei/web typecheck`: PASS.
- Local `npx --yes pnpm@11.8.0 --filter @eei/web exec playwright test --config=../../playwright.config.ts --grep "eight company layers"`: PASS.
- Local `git diff --check`: PASS.
- GitHub Actions run: `https://github.com/LinzeColin/CodexProject/actions/runs/27851485026`.
- GitHub Actions job: `82431234525`.
- GitHub Actions step `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A061 is covered by `apps/web/src/app/page.tsx`, `apps/web/src/app/globals.css`, `tests/e2e/home.spec.ts` and `artifacts/tests/a061/t501_company_workspace_layers.json`.
- A062 is covered by `apps/api/app/domain_repository.py`, `apps/api/app/domain.py`, `specs/api_contract.yaml`, `tests/integration/test_database_migrations.py`, `apps/web/src/app/page.tsx`, `tests/e2e/home.spec.ts` and `artifacts/tests/a062/t501_structure_type_separation.json`.
- A063 is covered by `apps/api/app/domain_repository.py`, `apps/web/src/app/page.tsx`, `tests/e2e/home.spec.ts` and `artifacts/tests/a063/t501_commercial_empire_not_control.json`.

Residual risks:

- Local database integration remains unrun on this host because there is no `.env` and no Docker-backed PostgreSQL.
- T501 creates the bounded structure workspace and API contract only; T502/T503/T506-T508 still own full supply-chain, capital/policy/technology, evidence drawer, timeline, export and cross-layer workspace depth.

## 2026-06-20 - v5 Task Pack synchronization and MVP v0.1 blocker registration

Status: LOCAL GOVERNANCE SYNC IN PROGRESS

Completed:

- Imported v5 review evidence into `reviews/`, `data/review_issue_register.csv`, `TEST_STRATEGY.md` and `CONTINUITY_PLAN.md`.
- Adapted v5 brand/competitive research to the active EEI identity without changing the system name: 商域图谱 / Enterprise Ecosystem Intelligence.
- Added `docs/phase/V5_TASK_PACK_SYNCHRONIZATION.md` as the source-of-truth mapping from v5 production blockers to EEI tasks, Acceptance IDs, rollback rules and unresolved decisions.
- Added T1300-T1309 to `data/task_backlog.csv` for PostgreSQL, real ingestion, production API/query/scoring, model activation/refresh, scheduler/dead-letter, saved views, 10k/100k/1m scale, 4h/24h soak, production frontend and brand clearance.
- Added A201-A211 to `data/acceptance_matrix.csv` and corresponding trace rows in `data/acceptance_traceability.csv`.
- Added 15 production runtime/model governance parameters to `data/parameter_catalog.csv` and `config/model_runtime_defaults.yaml`.
- Added V5-001 through V5-010 to `data/development_status_ledger.csv` so the blocker list appears in the development record.

Important boundary:

- This synchronization does not implement the blockers. T1300-T1309 and A201-A211 remain `NOT STARTED`.
- Current pursuing goal may only become v0.1 after these blockers have implementation, tests, rollback evidence and CI evidence.

Residual risks:

- Formal EEI legal/market clearance is not complete.
- Production-scale benchmarks and soak tests are not yet executable evidence.
- Production PostgreSQL, ingestion, graph/API/scoring, scheduler, saved views and componentized frontend remain active MVP blockers.

## 2026-06-20 - T1300/A201 PostgreSQL production fact-version migration

Status: LOCAL STATIC PASS; REMOTE CI PASS

Completed:

- Added `infra/db/migrations/0003_production_fact_version_layers/up.sql` and `down.sql`.
- Added `data_snapshots` for snapshot-scoped publication with record mode, active-state, source hash, activation time and supersession metadata.
- Added `fact_versions` for immutable object versions with fact status, record mode, time-validity windows, observed time, parser version, payload hash, previous version link and source/ingestion references.
- Added `fact_version_evidence` so versioned facts keep evidence as a separate layer.
- Updated `specs/domain_schema.sql`, `scripts/check_database_schema.py`, and `tests/integration/test_database_migrations.py` to validate A201.
- Marked T1300 and A201 as `DONE` in `data/task_backlog.csv`, `data/acceptance_matrix.csv`, and `data/acceptance_traceability.csv`.

Verification evidence:

- Local `python3 scripts/validate_catalog_integrity.py`: PASS.
- Local `PYTHONPATH=/private/tmp/eei-pydeps python3 scripts/validate_governance.py`: PASS.
- Local `PYTHONPATH=/private/tmp/eei-pydeps python3 scripts/validate_task_pack.py`: PASS.
- Local `PYTHONPATH=/private/tmp/eei-ruff:/private/tmp/eei-pydeps python3 -m ruff check scripts/check_database_schema.py tests/integration/test_database_migrations.py`: PASS.
- Local `PYTHONPATH=scripts:. .venv/bin/python -c 'from migrate import discover_migrations; print([(m.version, m.name) for m in discover_migrations()])'`: PASS and includes `0003 production_fact_version_layers`.
- Local `git diff --check`: PASS.
- GitHub Actions run `27853994985`: PASS.
- GitHub Actions job `82437995756`.
- GitHub Actions step `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A201 is covered by `infra/db/migrations/0003_production_fact_version_layers/up.sql`, `infra/db/migrations/0003_production_fact_version_layers/down.sql`, `scripts/check_database_schema.py`, and `tests/integration/test_database_migrations.py`.

Residual risks:

- Local Docker/PostgreSQL is not available on this host, so migration upgrade/downgrade and integration execution still require GitHub Actions for database proof.
- T1300 closes the database version-layer blocker only. T1301-T1309 remain required before v0.1: real ingestion, production API/query/scoring, model activation/refresh, scheduler, saved views, scale, soak, production frontend and brand clearance.

## 2026-06-20 - T1301/A202 curated official ingestion audit layer

Status: LOCAL STATIC PASS; REMOTE CI PASS

Completed:

- Added `infra/db/migrations/0004_curated_ingestion_audit_layers/up.sql` and `down.sql`.
- Added `raw_source_snapshots` to preserve official anchor URL, source date, publisher, title, scope, record mode, validation status, parser version, content hash, raw payload and review status.
- Added `entity_resolution_candidates` to preserve candidate name, normalized name, matched entity/research IDs when available, match method, confidence, decision reason, review status and parser version.
- Added `ingestion_evidence_chain` to preserve anchor-level evidence context, relationship family, locator, support excerpt, structured fact payload, counter_evidence array, parser version, confidence and review status.
- Added `scripts/load_curated_ingestion_anchors.py` for deterministic ingestion of `data/nvidia_public_source_anchors.csv` in `curated_official_fixture` mode.
- Updated `scripts/check_database_schema.py` with `--expect-curated-ingestion`.
- Updated `tests/integration/test_database_migrations.py` to run the curated loader twice and assert raw snapshot, source document, entity resolution, evidence chain and non-publication invariants.
- Marked T1301/A202 as `IN PROGRESS` in task, acceptance, traceability and development status files.

Acceptance status:

- A202 is in progress, not done.
- Current evidence covers curated official NVIDIA source anchors and ingestion audit layers.
- The loader intentionally does not publish relationship edges from discovery anchors.

Residual risks:

- live/full-text official connector is not implemented.
- reviewed NVIDIA -> TSMC -> ASML relationship facts are not published.
- independent source cross-check and human review workflow are not implemented.
- source health, retry, dead-letter and scheduler semantics remain owned by T1304/A206.

Verification evidence:

- GitHub Actions run `27854549380`: PASS.
- GitHub Actions job `82439458056`.
- GitHub Actions step `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step `Verify G2 PostgreSQL migrations and E2E`: PASS.

## 2026-06-20 - T1301/A202 Golden Vertical relationship fact candidates

Status: LOCAL STATIC IN PROGRESS

Completed:

- Added `infra/db/migrations/0005_relationship_fact_candidates/up.sql` and `down.sql`.
- Added `relationship_fact_candidates` to preserve candidate Golden Vertical facts with relationship type/family, record mode, fact status, publication status, confidence, independent source count, review status, parser version, structured fact and counter_evidence.
- Added `relationship_fact_candidate_evidence` to link candidate facts back to `ingestion_evidence_chain` and `source_documents`.
- Added `manual_review_queue` so single-source candidate facts remain open for review instead of being published.
- Added `data/golden_vertical_fact_candidates.json` with deterministic official source snapshots from SEC-hosted NVIDIA Form 10-K and ASML official source material.
- Extended `scripts/load_curated_ingestion_anchors.py` so it loads the candidate NVIDIA/TSMC/ASML chain without inserting production `relationships` rows.
- Extended `scripts/check_database_schema.py` and `tests/integration/test_database_migrations.py` to validate two candidate facts, two evidence links, two open review items and no relationship publication side effect.

Acceptance status:

- A202 remains `IN PROGRESS`.
- The Golden Vertical path exists as candidate fact evidence only:
  - TSMC `wafer_foundry_for` NVIDIA.
  - ASML `equipment_provider_to` TSMC.
- Both candidates are below the independent-source threshold and require review before publication.

Residual risks:

- live/full-text connector is still not implemented.
- independent-source threshold is not satisfied for the two candidate facts.
- no human review approval has been recorded.
- production API and graph query do not yet consume these candidate tables.

## 2026-06-21 - T1301/A202 reviewed publication mechanism

Status: CI VALIDATED; A202 STILL IN PROGRESS

Completed:

- Added `scripts/publish_reviewed_relationship_facts.py` for explicit review-decision driven publication of `relationship_fact_candidates`.
- Added `tests/fixtures/golden_vertical_review_decisions.json` as fixture-only review decisions; it is explicitly not production legal or data clearance.
- The publication script fails closed unless a review decision file is supplied, fixture review is explicitly allowed, endpoints are resolved or materialized from matched research-universe entities, evidence exists, counter-evidence is reviewed, and single-source candidates carry a source-threshold override reason and attestation.
- The script writes deterministic reviewed `relationships`, copies `relationship_evidence`, activates a `data_snapshots` row, writes `fact_versions` and `fact_version_evidence`, marks candidates `published`/`human_verified`, and resolves `manual_review_queue` in one transaction.
- The script can materialize matched research-universe endpoints as `research_target` legal entities and backfill `entity_resolution_candidates`; fully unresolved endpoints still fail closed.
- Extended `tests/integration/test_database_migrations.py` with the A202 reviewed-publication contract after the existing candidate-state/API assertions, preserving the candidate-vs-published boundary.
- Added the new script to `make lint` and A202 traceability/evidence artifacts.

Acceptance status:

- A202 remains `IN PROGRESS`.
- This closes the missing mechanism for reviewed publication in code, but not the production data approval requirement.
- The local host has no `.env`, `DATABASE_URL` or `docker` binary, so the new PostgreSQL integration assertions were not executed locally.
- GitHub Actions run `27877209505` / job `82498609174` validated the A202 reviewed-publication database path remotely under G2 PostgreSQL integration, browser E2E and live FastAPI/PostgreSQL E2E on commit `5e98141f756c1fc55211b23636f9af7cc14fbbdf`.

Verification evidence:

- `.venv/bin/ruff check scripts/publish_reviewed_relationship_facts.py tests/integration/test_database_migrations.py`: PASS.
- `python3 -m json.tool tests/fixtures/golden_vertical_review_decisions.json`: PASS.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/pytest tests/integration/test_database_migrations.py -q`: SKIPPED locally because PostgreSQL is not configured on this host.
- GitHub Actions `EEI validation` run `27877209505`, job `82498609174`: PASS.

Residual risks:

- live/full-text connector is still not implemented.
- second independent source or production owner review signature is still required before any real Golden Vertical fact can be considered production-approved.
- source health, retry, dead-letter and scheduler semantics remain owned by T1304/A206.

## 2026-06-20 - T1302/A203 production graph and scoring contract slice

Status: LOCAL VALIDATED; REMOTE CI PASS

Completed:

- Added production context to graph/path responses with active data snapshot, active scoring profile, graph query version, scoring service version, record modes and publication policy.
- Added `GET /v1/scoring/explain/{objectType}/{objectId}` for `relationship_fact_candidate` explanations.
- Added candidate-fact coverage so Golden Vertical candidates remain excluded from graph edges until source threshold and human review gates pass.
- Updated `specs/api_contract.yaml` and `tests/integration/test_database_migrations.py` for the A203 contract.
- Added `artifacts/tests/a203/t1302_production_api_graph_scoring_contract.json`.
- Marked T1302/A203 as `IN PROGRESS`, not DONE.

Acceptance status:

- A203 is in progress.
- Current evidence covers candidate fact scoring explanations and graph/path publication context.

Residual risks:

- Full multi-object production scoring service is not complete.
- Candidate review approval and publication into relationship facts remain open.
- Scale, soak and downstream frontend production wiring remain separate blockers.

Verification evidence:

- GitHub Actions run `27856517135`: PASS.
- GitHub Actions job `82444936213`.
- GitHub Actions step `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step `Verify G2 PostgreSQL migrations and E2E`: PASS.

## 2026-06-20 - T1303/A204-A205 transactional activation and refresh context slice

Status: LOCAL STATIC IN PROGRESS

Completed:

- Added `infra/db/migrations/0006_model_activation_refresh_state/up.sql` and `down.sql`.
- Added a database-level global active scoring profile unique index.
- Added `active_analysis_contexts` for active profile, data snapshot, score snapshot, refresh token, refresh generation, affected modules and metadata.
- Extended `scripts/load_seed_catalogs.py` to initialize the global active context idempotently.
- Added `GET /v1/scoring/active-context` so clients can detect stale refresh tokens.
- Added `POST /v1/scoring/profiles/{profileVersionId}/activate` for transaction-scoped activation.
- Activation now locks current/target profile versions, creates a completed `scoring_runs` score snapshot, switches active profile, updates active context and writes operation logs in one transaction.
- Stale expected active profile requests return 409 and leave the active profile unchanged while logging a conflict operation.
- Extended `tests/integration/test_database_migrations.py` to assert success, conflict and database uniqueness semantics.
- Added A204/A205 evidence files under `artifacts/tests/a204/` and `artifacts/tests/a205/`.

Acceptance status:

- A204 and A205 are `IN PROGRESS`, not DONE.
- A204 has service/database transaction evidence pending CI database execution.
- A205 has server-side refresh token semantics, but not production frontend cross-view E2E completion.

Residual risks:

- Frontend modules still use the static analysis context and are not yet wired to `/v1/scoring/active-context`.
- Model-center edit/activate/rollback controls are not complete.
- Worker-driven data snapshot activation, transactional outbox, scheduler and dead-letter remain T1304 and later tasks.

## 2026-06-20 - T1304/A206 scheduler retry and dead-letter core slice

### Scope

- Added PostgreSQL scheduler state tables: `background_jobs`, `background_job_attempts`, and `dead_letter_jobs`.
- Added `scripts/job_scheduler.py` with idempotent enqueue, due-job lease, heartbeat, graceful release, bounded retry, expired lease recovery, completion and dead-letter transitions.
- Extended schema validation and integration coverage for A206.

### Files changed

- `infra/db/migrations/0007_scheduler_job_queue/up.sql`
- `infra/db/migrations/0007_scheduler_job_queue/down.sql`
- `specs/domain_schema.sql`
- `scripts/job_scheduler.py`
- `scripts/check_database_schema.py`
- `tests/integration/test_database_migrations.py`
- `artifacts/tests/a206/t1304_scheduler_retry_dead_letter_contract.json`
- `data/task_backlog.csv`
- `data/acceptance_matrix.csv`
- `data/acceptance_traceability.csv`
- `data/development_status_ledger.csv`
- `data/release_gate_catalog.csv`
- `docs/phase/V5_TASK_PACK_SYNCHRONIZATION.md`

### Acceptance mapping

- T1304 -> A206.
- A206 is now `IN PROGRESS`, not `DONE`.

### Validation

- Local ruff target: PASS for `scripts/job_scheduler.py`, `scripts/check_database_schema.py`, and `tests/integration/test_database_migrations.py`.
- PostgreSQL integration proof is required from GitHub Actions `make verify-g2-db` because this host has no local Docker/PostgreSQL.

### Remaining gaps

- Real curated ingestion and calibration handlers are not yet registered on the scheduler.
- Deployment-level wake/supervision is not yet packaged.
- T1307 4h/24h soak remains required before scheduler stability can be called production-ready.
- Local Docker/PostgreSQL is not available on this host, so database proof requires GitHub Actions.

## 2026-06-20 - T1305/A207 server-side saved-view conflict and recovery slice

### Scope

- Added PostgreSQL saved-view state tables: `saved_views` and `saved_view_versions`.
- Added `/v1/saved-views` list/create/get/update/version-list/restore routes.
- Added repository-level `FOR UPDATE` optimistic conflict control using `expected_version`.
- Added 409 `saved-view-conflict-v1` responses for duplicate names, stale updates and stale restores.
- Added recovery semantics where restoring a historical version appends a new current version instead of rewriting history.
- Extended schema validation, OpenAPI and PostgreSQL integration coverage for A207.

### Files changed

- `infra/db/migrations/0008_server_saved_views/up.sql`
- `infra/db/migrations/0008_server_saved_views/down.sql`
- `specs/domain_schema.sql`
- `apps/api/app/domain.py`
- `apps/api/app/domain_repository.py`
- `specs/api_contract.yaml`
- `scripts/check_database_schema.py`
- `tests/integration/test_database_migrations.py`
- `artifacts/tests/a207/t1305_server_saved_view_conflict_recovery_contract.json`
- `data/task_backlog.csv`
- `data/acceptance_matrix.csv`
- `data/acceptance_traceability.csv`
- `data/development_status_ledger.csv`
- `docs/phase/V5_TASK_PACK_SYNCHRONIZATION.md`

### Acceptance mapping

- T1305 -> A207.
- A207 is now `IN PROGRESS`, not `DONE`.

### Validation

- Local static and governance validation pending in this run.
- PostgreSQL integration proof is required from GitHub Actions `make verify-g2-db` because this host has no local Docker/PostgreSQL.

### Remaining gaps

- Superseded by the later frontend API-first adapter slice: saved-view controls now attempt `/v1/saved-views` and explicitly fall back locally when the API base/server id is missing.
- A real multi-session browser E2E with two contexts against live FastAPI/PostgreSQL is still required.
- Authn/authz user/workspace scoping remains required before public multi-user use.

## 2026-06-20 - T1308/A211 WorkspaceContext and production navigation slice

### Scope

- Added a `WorkspaceContext` contract for the 16 EEI navigation modules without changing the EEI system name.
- Added a componentized workspace navigation rail with route, lens, section and planned-disabled control states.
- Wired real lens controls to workspace state, section controls to existing work surfaces, and route controls to `/`, `/objects-scope`, and `/development-status`.
- Added disabled states and explicit reasons for unfinished M&A, control-path and strategic-signal modules.
- Exposed URL, sessionStorage and localStorage persistence keys plus server endpoint mappings for saved views, model context, exploration and catalogs.
- Added Playwright coverage for A211.

### Files changed

- `apps/web/src/app/workspace-context.tsx`
- `apps/web/src/app/workspace-navigation.tsx`
- `apps/web/src/app/page.tsx`
- `apps/web/src/app/globals.css`
- `tests/e2e/home.spec.ts`
- `artifacts/tests/a211/t1308_frontend_workspace_context_contract.json`
- `data/task_backlog.csv`
- `data/acceptance_matrix.csv`
- `data/acceptance_traceability.csv`
- `data/development_status_ledger.csv`
- `data/release_gate_catalog.csv`
- `scripts/validate_v5_production_readiness_sync.py`
- `docs/phase/V5_TASK_PACK_SYNCHRONIZATION.md`
- `DEVELOPMENT_STATUS.md`
- `README.md`

### Acceptance mapping

- T1308 -> A211.
- A211 is now `IN PROGRESS`, not `DONE`.

### Validation

- Local `PNPM=/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/pnpm make typecheck`: PASS.
- Local Playwright E2E command ran the full E2E set and passed: 28/28.

### Remaining gaps

- Frontend data loading still needs production API hydration against a configured FastAPI base URL.
- Saved-view UI now has an API-first adapter and mock server E2E; live FastAPI/PostgreSQL multi-session E2E and 409 conflict-recovery UI remain open.
- Model-center controls still need transactional activation, rollback and stale-client refresh semantics.
- A live FastAPI/PostgreSQL cross-route E2E is still required before closing A211.

## 2026-06-20 - T1215/T1211 release package generated-file exclusion

### Scope

- Excluded `apps/web/next-env.d.ts` from clean-room ZIP, release manifest and release checksums.
- Reason: Next.js rewrites this generated type-reference file during CI bootstrap/type generation, making strict package checks fail even when source and artifacts are otherwise synchronized.
- Regenerated clean-room release and release manifest/checksum artifacts after the exclusion.

### Files changed

- `scripts/manage_clean_room_release.py`
- `scripts/manage_release_artifacts.py`
- `artifacts/tests/a200/Enterprise_Ecosystem_Intelligence_clean_room_t1215.zip`
- `artifacts/tests/a200/t1215_clean_room_release.json`
- `artifacts/release_evidence_t1211.json`
- `manifest.txt`
- `DIRECTORY_TREE.txt`
- `CHECKSUMS.sha256`

### Validation

- Local `make generate-clean-room-release validate-clean-room-release generate-release-artifacts validate-release-artifacts`: PASS.
- Local `make verify`: PASS.

### Remaining gaps

- This only fixes release packaging determinism for generated Next type files; it does not close A211 or v0.1 production blockers.

## 2026-06-20 - T1305/A207 frontend saved-view API-first adapter slice

### Scope

- Added a browser saved-view API adapter that targets `/v1/saved-views` through `NEXT_PUBLIC_EEI_API_BASE_URL` or localStorage key `eei.apiBaseUrl.v1`.
- Changed saved-view save/restore controls from local-only behavior to API-first behavior with explicit local fallback when the API base URL or server id is missing.
- Added DOM contract fields for sync mode, sync reason, server id, server version, server endpoint, workspace key and API-base storage key.
- Added Playwright coverage for local fallback (`local-saved`/`local-restored`) and mock server API create/restore (`server-saved`/`server-restored`).
- Added A207 frontend adapter evidence while keeping A207 `IN PROGRESS`.

### Files changed

- `apps/web/src/app/saved-view-client.ts`
- `apps/web/src/app/page.tsx`
- `tests/e2e/state-contract.spec.ts`
- `artifacts/tests/a207/t1305_frontend_saved_view_api_adapter_contract.json`
- `artifacts/tests/a207/t1305_server_saved_view_conflict_recovery_contract.json`
- `scripts/validate_v5_production_readiness_sync.py`
- `data/acceptance_traceability.csv`
- `data/development_status_ledger.csv`
- `DEVELOPMENT_STATUS.md`
- `README.md`

### Acceptance mapping

- T1305 -> A207.
- A207 remains `IN PROGRESS`, not `DONE`.

### Validation

- Local `PNPM=/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/pnpm make typecheck`: PASS.
- Local `PNPM=/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/pnpm /Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/pnpm --filter @eei/web test:e2e`: PASS, 29/29.

### Remaining gaps

- Superseded by the later live multisession E2E harness slice: live two-context harness and 409 fetch-latest conflict recovery UI now exist and have GitHub Actions `verify-g2-db` PASS evidence in run `27862471613`, job `82460665725`.
- User/workspace authn/authz remains required before public multi-user saved-view deployment.

## 2026-06-20 - T1305/A207 live multisession saved-view E2E harness and conflict recovery UI

### Scope

- Added configured FastAPI CORS support for browser saved-view requests from the local EEI web origin.
- Added a dedicated live Playwright config that starts FastAPI and Next.js with `NEXT_PUBLIC_EEI_API_BASE_URL`.
- Added `scripts/run_live_e2e_api.sh` to reset the local E2E PostgreSQL database, run migrations, seed catalogs, load synthetic fixtures and start uvicorn.
- Added a live two-browser-context E2E that creates server saved-view version 1, updates it to version 2 in another context, triggers stale-version 409 from the first context and resolves via the new conflict recovery UI.
- Added a visible `server-conflict` recovery button that fetches the latest saved view and reports `server-conflict-resolved`.
- Added CORS unit coverage and wired `test-e2e-live` into `verify-g2-db`.

### Files changed

- `Makefile`
- `apps/api/app/main.py`
- `apps/api/app/settings.py`
- `apps/web/src/app/page.tsx`
- `playwright.config.ts`
- `playwright.live.config.ts`
- `scripts/run_live_e2e_api.sh`
- `tests/e2e/saved-view-live.spec.ts`
- `tests/unit/test_api_health.py`
- `artifacts/tests/a207/t1305_live_saved_view_multisession_e2e_contract.json`
- `scripts/validate_v5_production_readiness_sync.py`
- `data/acceptance_traceability.csv`
- `data/development_status_ledger.csv`
- `DEVELOPMENT_STATUS.md`
- `README.md`
- `docs/phase/V5_TASK_PACK_SYNCHRONIZATION.md`

### Acceptance mapping

- T1305 -> A207.
- A207 remains `IN PROGRESS`, not `DONE`, until user/workspace authn/authz is present.

### Validation

- Local `PNPM=/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/pnpm make typecheck`: PASS.
- Local `UV_CACHE_DIR=/private/tmp/eei-uv-cache make lint`: PASS.
- Local `UV_CACHE_DIR=/private/tmp/eei-uv-cache make test-unit`: PASS, 13/13 with existing Starlette `httpx` deprecation warning.
- Local default Playwright E2E: PASS, 29/29.
- Local live Playwright E2E: NOT RUN; this host does not have `docker`.
- GitHub Actions run `27862471613`: PASS.
- GitHub Actions job `82460665725`: PASS.
- GitHub Actions step `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step `Verify G2 PostgreSQL migrations and E2E`: PASS, including the live FastAPI/PostgreSQL multisession saved-view E2E harness.

### Remaining gaps

- User/workspace authn/authz remains required before public multi-user saved-view deployment.

## 2026-06-20 - T1303/A204-A205 model-center API-first transaction controls

### Scope

- Added a frontend `model-activation-client.ts` adapter for `/v1/scoring/active-context`, `/v1/scoring/profiles` and `/v1/scoring/profiles/{profileVersionId}/activate`.
- Added model-center API-first hydration with explicit local fallback when no API base is configured.
- Added model-center transaction activation controls that send `expected_active_profile_version_id` and `client_refresh_token`.
- Added rollback control by reactivating the previous profile through the same transaction endpoint.
- Added stale-client refresh detection by refetching active context with the previous refresh token and surfacing `stale_client_refetched`.
- Mapped server active context into the shared frontend `AnalysisContext`, so workspace shell, saved views and visible modules receive the active model/profile/data/score snapshot.
- Added Playwright mock-server E2E coverage for hydration, activation, stale refresh and rollback.

### Files changed

- `apps/web/src/app/model-activation-client.ts`
- `apps/web/src/app/use-analysis-context.ts`
- `apps/web/src/app/page.tsx`
- `tests/e2e/state-contract.spec.ts`
- `artifacts/tests/a204/t1303_transactional_model_activation_contract.json`
- `artifacts/tests/a205/t1303_atomic_refresh_context_contract.json`
- `artifacts/tests/a211/t1308_frontend_workspace_context_contract.json`
- `scripts/validate_v5_production_readiness_sync.py`
- `data/acceptance_traceability.csv`
- `data/development_status_ledger.csv`
- `DEVELOPMENT_STATUS.md`
- `README.md`
- `docs/phase/V5_TASK_PACK_SYNCHRONIZATION.md`

### Acceptance mapping

- T1303 -> A204/A205.
- T1308 -> A211.
- A204/A205/A211 remain `IN PROGRESS`, not `DONE`.

### Validation

- Local `PNPM=/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/pnpm make typecheck`: PASS.
- Local targeted Playwright E2E with non-sandbox browser/server access: PASS, 1/1 for `A204 and A205 hydrate activate refresh and rollback model context through the server API`.
- Local default Playwright E2E with non-sandbox browser/server access: PASS, 30/30.
- Local `UV_CACHE_DIR=/private/tmp/eei-uv-cache make lint test-unit`: PASS; unit tests 13/13 with existing Starlette `httpx` deprecation warning.
- Local `UV_CACHE_DIR=/private/tmp/eei-uv-cache make secret-scan copy-lint`: PASS.
- Local v5/development/release validation: PASS.
- GitHub Actions run `27863334141`: PASS.
- GitHub Actions job `82463054603`: PASS.
- GitHub Actions step `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step `Verify G2 PostgreSQL migrations and E2E`: PASS.

### Remaining gaps

- Live FastAPI/PostgreSQL cross-route E2E for model activation and stale refresh is still required.
- Model-center online editing, dedicated rollback endpoint and score recompute UI remain open.

## 2026-06-20 - T1303/A204-A205 live model activation harness

### Scope

- Added `config/model_profiles/supply-chain-v3.json` as an inactive immutable profile for supply-chain recursive exploration.
- Updated seed loading to create two model/profile versions while keeping exactly one active global profile.
- Ordered `/v1/scoring/profiles` with the active profile first so clients can reliably identify the current version and inactive activation candidate.
- Extended the live FastAPI/PostgreSQL Playwright harness to configure `eei.modelApiBaseUrl.v1`.
- Added a live E2E path that activates `supply-chain-v3`, observes a transaction-created scoring run snapshot, checks stale refresh semantics and rolls back to `balanced-v2`.
- Synchronized A204/A205/A211 evidence, acceptance traceability, development status and model-management docs.

### Files changed

- `config/model_profiles/supply-chain-v3.json`
- `scripts/load_seed_catalogs.py`
- `scripts/check_database_schema.py`
- `scripts/validate_governance.py`
- `scripts/validate_task_pack.py`
- `apps/api/app/domain_repository.py`
- `tests/integration/test_database_migrations.py`
- `tests/e2e/saved-view-live.spec.ts`
- `artifacts/tests/a204/t1303_transactional_model_activation_contract.json`
- `artifacts/tests/a205/t1303_atomic_refresh_context_contract.json`
- `artifacts/tests/a211/t1308_frontend_workspace_context_contract.json`
- `data/acceptance_traceability.csv`
- `data/development_status_ledger.csv`
- `data/github_document_registry.csv`
- `DEVELOPMENT_STATUS.md`
- `docs/30_MODEL_MANAGEMENT.md`
- `docs/phase/V5_TASK_PACK_SYNCHRONIZATION.md`

### Acceptance mapping

- T1303 -> A204/A205.
- T1308 -> A211.
- A204/A205/A211 remain `IN PROGRESS`, not `DONE`.

### Validation so far

- Local `python3 -m py_compile scripts/load_seed_catalogs.py scripts/check_database_schema.py apps/api/app/domain_repository.py tests/integration/test_database_migrations.py`: PASS.
- Local `.venv/bin/python scripts/validate_model_config.py config/model_profiles/supply-chain-v3.json config/thresholds/default-v2.json`: PASS.
- Local `.venv/bin/python -m ruff check apps/api/app/domain_repository.py scripts/check_database_schema.py scripts/load_seed_catalogs.py tests/integration/test_database_migrations.py`: PASS.
- Local escalated `npx --yes pnpm@11.8.0 --filter @eei/web typecheck`: PASS.
- Local `.venv/bin/python scripts/validate_governance.py`: PASS.
- Local `.venv/bin/python scripts/validate_catalog_integrity.py`: PASS.
- Local `.venv/bin/python scripts/validate_task_pack.py`: PASS.
- Local `.venv/bin/python scripts/validate_v5_production_readiness_sync.py`: PASS.
- Local `.venv/bin/python -m pytest -q tests/unit/test_api_health.py`: PASS, 9/9.
- Local `.venv/bin/python -m pytest -q tests/integration/test_database_migrations.py`: SKIPPED, 1/1 because local `.env`/`DATABASE_URL` is absent.
- Local escalated `npx --yes pnpm@11.8.0 --filter @eei/web exec playwright install chromium`: PASS; installed Chromium/Headless Shell for the current Playwright version.
- Local escalated `npx --yes pnpm@11.8.0 --filter @eei/web exec playwright test --config=../../playwright.config.ts tests/e2e/state-contract.spec.ts -g "A204 and A205"`: PASS, 1/1.
- Local escalated `npx --yes pnpm@11.8.0 --filter @eei/web exec playwright test --config=../../playwright.live.config.ts`: FAIL CLOSED before test execution because `DATABASE_URL` is not configured on this host.
- Local escalated `make verify`: PASS, including Task Pack validation, contract validation, prototype parity, GitHub governance, governance consistency, v5 sync, development/risk/release artifact validation, scale benchmark smoke, browser scale benchmark, soak smoke, secret scan, UI copy lint, ruff, web typecheck and unit tests 13/13.
- Regenerated clean-room release package; authoritative package SHA256 is recorded in `artifacts/tests/a200/t1215_clean_room_release.json`.
- Regenerated release artifacts with `remote_status=PENDING`.

### CI evidence

- GitHub Actions run `27868141438`, job `82475530819`: PASS.
- Steps 7-12 all succeeded, including `Verify G2 PostgreSQL integration`, `Verify G2 browser E2E` and `Verify G2 live FastAPI PostgreSQL E2E`.

### Remaining gaps

- Model-center online editing, dedicated rollback endpoint, worker-driven data snapshot refresh/outbox and dedicated score recompute controls remain open.

## 2026-06-20 - T1302/A203 and T1308/A211 commercial-map graph API context hydration

### Scope

- Added `explore-api-client.ts` for API-first `POST /v1/explore` hydration with explicit local fixture fallback.
- Mapped homepage subject, lens, semantic zoom, as-of time, scoring profile id and default 42/64/12 budget into the backend `ExploreRequest` contract.
- Added a production graph context panel that surfaces `production_context`, graph query version, scoring service version, server coverage, publication gate and candidate-fact exclusion counts.
- At that point, visible graph rendering still used the fixture projection. The follow-on server graph rendering slice below closes that specific rendering gap while leaving A203/A211 open.
- Added Playwright mock-server E2E coverage for initial hydration and manual lens-driven refresh.
- Recorded the current contract gap: the `capital` visual node still falls back to the NVIDIA entity id until a first-class capital object/entity contract is implemented.

### Files changed

- `apps/web/src/app/explore-api-client.ts`
- `apps/web/src/app/page.tsx`
- `tests/e2e/state-contract.spec.ts`
- `artifacts/tests/a203/t1302_production_api_graph_scoring_contract.json`
- `artifacts/tests/a211/t1308_frontend_workspace_context_contract.json`
- `scripts/validate_v5_production_readiness_sync.py`
- `data/acceptance_traceability.csv`
- `data/development_status_ledger.csv`
- `DEVELOPMENT_STATUS.md`
- `README.md`
- `docs/phase/V5_TASK_PACK_SYNCHRONIZATION.md`

### Acceptance mapping

- T1302 -> A203.
- T1308 -> A211.
- A203/A211 remain `IN PROGRESS`, not `DONE`.

### Validation

- Local `PNPM=/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/pnpm make typecheck`: PASS.
- Local targeted Playwright E2E with non-sandbox browser/server access: PASS, 1/1 for `A203 and A211 hydrate production graph context through the explore API`.
- Local default Playwright E2E with non-sandbox browser/server access: PASS, 31/31.

### Remaining gaps at that point

- The commercial-map render layer still had to consume server-returned graph records. This was addressed by the following bounded server graph rendering slice, but A203/A211 remain open.
- Evidence center, catalog and score explanation API hydration remained open after this server-rendering slice; catalog and score hydration are addressed by the following bounded slice, while evidence detail/source-snippet hydration remains open.
- Live FastAPI/PostgreSQL cross-route E2E remains required before A211 can close.
- Full multi-object scoring and formally published relationship edges remain required before A203 can close.

## 2026-06-20 - T1302/A203 and T1308/A211 commercial-map server graph rendering

### Scope

- Connected typed `/v1/explore` response nodes and edges to the commercial-map SVG render layer and accessible relationship table.
- Added runtime API guards for server node and edge records so malformed graph payloads fall back to the local fixture path instead of partially rendering invalid data.
- Added deterministic server-node layout, relationship-family lens mapping, server edge labels, server source-count metadata and server render count attributes for E2E assertions.
- Added server selected-node support in the inspection card. Unknown server-only objects can be selected and inspected, while local-only actions such as set-center, pin, compare and watchlist are disabled unless the server entity maps to an existing local object key.
- Preserved restored local selected-node state during server graph hydration, so saved-view/URL restores such as `subject=cloud&selected=datacenter` keep the local inspection card until the user explicitly selects a server-rendered graph node.
- Delayed initial production graph hydration until workspace state is ready, preventing default NVIDIA graph requests from racing ahead of URL/session saved-view restoration.
- Retained fixture rendering as the explicit fallback when the API is unavailable or returns no usable graph edges.
- Extended the A203/A211 Playwright mock server with a server-only packaging supplier node and two server-returned relationship edges, then asserted SVG, table, selected-card rendering from the server graph and restored local selected-node preservation.

### Files changed

- `apps/web/src/app/explore-api-client.ts`
- `apps/web/src/app/page.tsx`
- `tests/e2e/state-contract.spec.ts`
- `artifacts/tests/a203/t1302_production_api_graph_scoring_contract.json`
- `artifacts/tests/a211/t1308_frontend_workspace_context_contract.json`
- `data/acceptance_traceability.csv`
- `data/development_status_ledger.csv`
- `DEVELOPMENT_STATUS.md`
- `FUNCTION_CATALOG.md`
- `README.md`
- `docs/phase/V5_TASK_PACK_SYNCHRONIZATION.md`
- `docs/phase/MVP_DEVELOPMENT_RECORD.md`

### Acceptance mapping

- T1302 -> A203.
- T1308 -> A211.
- A203/A211 remain `IN_PROGRESS`, not `DONE`.

### Validation

- Local `PNPM=/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/pnpm make typecheck`: PASS.
- Local targeted Playwright E2E with non-sandbox browser/server access: PASS, 2/2 for A203/A211 production graph context and restored local selected-node preservation.
- Local default Playwright E2E with non-sandbox browser/server access: PASS, 32/32.
- Local live PostgreSQL G2 E2E was not runnable on this Mac because `docker` is not installed; GitHub Actions remains the live G2 evidence source.

### Remaining gaps

- Evidence center, catalog and score explanation API hydration remain open.
- Live FastAPI/PostgreSQL cross-route E2E remains required before A211 can close.
- Full multi-object scoring and formally published relationship edges remain required before A203 can close.
- Server graph rendering currently requires a usable edge set; node-only production graph payload behavior remains a future product contract decision.

## 2026-06-20 - T1302/A203 and T1308/A211 catalog and score production data hydration

### Scope

- Added a production data API client for `/v1/catalogs` and `/v1/scoring/explain/relationship_fact_candidate/{objectId}` with runtime response guards and explicit local fallback/error modes.
- Extended backend `production_context.candidate_fact_summary` with bounded `sample_candidates` so the frontend can discover a live score explanation target without hard-coding randomly generated PostgreSQL UUIDs.
- Added a homepage production data panel that surfaces catalog version, catalog count, source-of-truth count, declared row count, score adjusted value, evidence count, missing-input count, publication status and scoring service version.
- Wired successful `/v1/explore` graph hydration to automatically hydrate catalog inventory and the first candidate score explanation.
- Preserved the existing publication boundary: relationship_fact_candidates remain excluded from graph edges until source threshold and human review gates pass.

### Files changed

- `apps/api/app/domain_repository.py`
- `apps/web/src/app/explore-api-client.ts`
- `apps/web/src/app/production-data-client.ts`
- `apps/web/src/app/page.tsx`
- `tests/e2e/state-contract.spec.ts`
- `artifacts/tests/a203/t1302_production_api_graph_scoring_contract.json`
- `artifacts/tests/a211/t1308_frontend_workspace_context_contract.json`
- `data/acceptance_traceability.csv`
- `data/development_status_ledger.csv`
- `DEVELOPMENT_STATUS.md`
- `README.md`
- `docs/phase/V5_TASK_PACK_SYNCHRONIZATION.md`
- `docs/phase/MVP_DEVELOPMENT_RECORD.md`

### Acceptance mapping

- T1302 -> A203.
- T1308 -> A211.
- A203/A211 remain `IN_PROGRESS`, not `DONE`.

### Validation

- Local `npm run typecheck` from `apps/web`: PASS.
- Local `python3 -m py_compile EEI/apps/api/app/domain_repository.py`: PASS.
- Local `.venv/bin/python -m pytest -q tests/unit/test_api_health.py`: PASS, 9/9.
- Local targeted Playwright E2E with non-sandbox browser/server access: PASS, 2/2 for A203/A211 production graph, catalog and score hydration.
- Local default Playwright E2E with non-sandbox browser/server access: PASS, 32/32.
- GitHub Actions `EEI validation` on `c2ce25603ed12e4dabfb02517af3821f70b631f3`: PASS, run `27865890074`, job `82469817036`; Step 7 static/contract/lint/typecheck/unit and Step 8 G2 PostgreSQL migrations/E2E both succeeded.

### Remaining gaps

- Evidence detail/source-snippet production API hydration remains open.
- Live FastAPI/PostgreSQL cross-route E2E remains required before A211 can close.
- Full multi-object scoring and formally published relationship edges remain required before A203 can close.
- 4h/24h soak, saved-view authn/authz, real scheduler handlers/deployment wake and brand clearance remain v0.1 blockers.

## 2026-06-20 - T1302/A203 and T1308/A211 evidence detail/source snippet hydration

### Scope

- Added production API route `/v1/evidence/{objectType}/{objectId}` with bounded `limit` validation for `relationship_fact_candidate` and published `relationship` objects.
- Added repository evidence detail payloads using existing PostgreSQL evidence tables: `relationship_fact_candidate_evidence`, `ingestion_evidence_chain`, `relationship_evidence`, `source_documents` and `sources`.
- Hardened the published `relationship` evidence detail branch to read fixture disclosure from `fixture_relationship_notices`, matching the production schema instead of assuming fixture columns on `relationships`.
- Hardened evidence detail payload generation so nullable PostgreSQL evidence fields still return contract-safe `structured_fact` objects, `counter_evidence` arrays and string snippets.
- Rebased the PostgreSQL integration assertions on the evidence detail contract instead of fixture-specific row counts or a single sample relationship notice.
- Fixed evidence detail production context hydration to call `production_context_for_connection(..., as_of=None)`, matching the existing production-context contract used by scoring, graph and path APIs.
- Extended `specs/api_contract.yaml` with `EvidenceDetailResponse`, `EvidenceDetailItem`, `EvidenceSnippet` and `EvidenceDetailSourceDocument`.
- Extended the frontend production data client with guarded `loadEvidenceDetail` support and local fallback/error modes.
- Wired the commercial-map homepage so successful `/v1/explore` hydration loads catalog, score explanation and evidence detail in parallel.
- Added a production evidence panel in Evidence Center showing evidence count, source-document count, endpoint, truncation state and source snippets.
- Wired the "打开证据" action to refresh production evidence detail instead of only changing a local status marker.
- Extended live saved-view E2E setup to explicitly configure the production data API base key when exercising the live FastAPI/PostgreSQL stack.
- Preserved the candidate-vs-published-fact boundary: candidate evidence is visible as evidence detail, but relationship_fact_candidates are still excluded from graph edges until publication gates pass.

### Files changed

- `apps/api/app/domain.py`
- `apps/api/app/domain_repository.py`
- `apps/web/src/app/production-data-client.ts`
- `apps/web/src/app/page.tsx`
- `specs/api_contract.yaml`
- `tests/e2e/state-contract.spec.ts`
- `tests/integration/test_database_migrations.py`
- `DEVELOPMENT_STATUS.md`
- `data/development_status_ledger.csv`
- `data/acceptance_traceability.csv`
- `docs/phase/V5_TASK_PACK_SYNCHRONIZATION.md`
- `docs/phase/MVP_DEVELOPMENT_RECORD.md`

### Acceptance mapping

- T1302 -> A203.
- T1308 -> A211.
- A203/A211 remain `IN_PROGRESS`, not `DONE`.

### Validation

- Local `python3 -m py_compile apps/api/app/domain_repository.py apps/api/app/domain.py tests/integration/test_database_migrations.py`: PASS.
- Local `python3 -m py_compile apps/api/app/domain_repository.py tests/integration/test_database_migrations.py`: PASS after published relationship evidence hardening.
- Local `git diff --check`: PASS.
- Local `npm run typecheck` from `apps/web`: PASS.
- Local `./node_modules/.bin/tsc --noEmit` from `apps/web`: PASS after live E2E setup hardening.
- Local `.venv/bin/python -m pytest -q tests/unit/test_api_health.py`: PASS, 9/9.
- Local `.venv/bin/python -m pytest -q tests/integration/test_database_migrations.py`: SKIPPED, 1/1 because local `.env`/`DATABASE_URL` is absent; CI remains the destructive PostgreSQL migration/reset evidence source.
- Local `.venv/bin/python -m ruff check apps/api/app/domain_repository.py tests/integration/test_database_migrations.py`: PASS after evidence detail contract hardening.
- Local targeted Playwright E2E with non-sandbox browser/server access: PASS, 2/2 for A203/A211 production graph and evidence hydration.
- Local default Playwright E2E with non-sandbox browser/server access: PASS, 32/32.
- GitHub Actions run `27866692631` on commit `b996803f8ce442ed339ec89981cab755ea889092`: FAILED in Step 8 `Verify G2 PostgreSQL migrations and E2E`; Step 7 static/contract/lint/typecheck/unit succeeded. Follow-up fix added relationship evidence schema compatibility and live E2E production data API base setup for the next CI run.
- GitHub Actions run `27866865460` on commit `5822f15a13e999692786cf64bccba7016e596b83`: FAILED in the same aggregated Step 8 after the first follow-up fix.
- GitHub Actions run `27866974650` on commit `aefe932a7b3272895ef2c26ba48a8cd4746a510a`: FAILED after workflow split, now isolated to Step 10 `Verify G2 PostgreSQL integration`; Steps 7, 8 and 9 succeeded. This confirmed the remaining failure was in PostgreSQL migration/integration contract, not static/unit/browser setup.
- GitHub Actions run `27867248690` on commit `e3c77499064a2c33e48a2430e4419a10f5dbaa63`: FAILED in Step 10 with `TypeError: DomainRepository.production_context_for_connection() missing 1 required keyword-only argument: 'as_of'`. Follow-up fix passes `as_of=None` from both evidence detail branches before the next CI run.
- GitHub Actions run `27867365117` on commit `b3750ca0285a6ae05a1d7c7c33246aa9f1d0f5cd`, job `82473570232`: PASS. Steps 7-12 all succeeded, including G2 PostgreSQL integration, browser E2E and live FastAPI/PostgreSQL E2E.

### Remaining gaps

- Live FastAPI/PostgreSQL cross-route E2E remains required before A211 can close.
- Full multi-object scoring, formally published relationship edges and complete graph evidence drawer semantics remain required before A203 can close.
- 4h/24h soak, saved-view authn/authz, real scheduler handlers/deployment wake and brand clearance remain v0.1 blockers.

## 2026-06-20 - T1303/A204-A205 dedicated rollback endpoint

### Scope

- Added dedicated FastAPI route `POST /v1/scoring/profiles/{profileVersionId}/rollback`.
- Reused the existing transaction-scoped activation kernel so rollback still locks the active profile, checks `expected_active_profile_version_id`, advances `active_analysis_contexts.refresh_token`, creates a completed `scoring_runs` row and preserves stale-client conflict semantics.
- Split `operation_logs.action_type` between `activate_scoring_profile` and `rollback_scoring_profile` so rollback is auditable as its own operation.
- Added `ScoringRollbackRequest` to the OpenAPI contract and connected rollback responses to the existing activation response schema.
- Added frontend `rollbackModelProfile()` and changed the model-center rollback control to call `/rollback` instead of reusing `/activate`.
- Extended PostgreSQL integration coverage to prove dedicated rollback success, rollback stale conflict, operation-log action types and the global active-profile uniqueness invariant.
- Updated the A204/A205 mock E2E so activation and rollback are intercepted as separate API endpoints.

### Files changed

- `apps/api/app/domain.py`
- `apps/api/app/domain_repository.py`
- `apps/web/src/app/model-activation-client.ts`
- `apps/web/src/app/page.tsx`
- `specs/api_contract.yaml`
- `tests/e2e/state-contract.spec.ts`
- `tests/integration/test_database_migrations.py`
- `artifacts/tests/a204/t1303_transactional_model_activation_contract.json`
- `artifacts/tests/a205/t1303_atomic_refresh_context_contract.json`
- `DEVELOPMENT_STATUS.md`
- `README.md`
- `data/development_status_ledger.csv`
- `data/acceptance_traceability.csv`
- `docs/phase/V5_TASK_PACK_SYNCHRONIZATION.md`
- `docs/phase/MVP_DEVELOPMENT_RECORD.md`

### Acceptance mapping

- T1303 -> A204, A205.
- A204/A205 remain `IN_PROGRESS`, not `DONE`, because online model editing, dedicated score recompute controls and worker-driven data refresh/outbox are still open.

### Validation

- Local `python3 -m py_compile apps/api/app/domain.py apps/api/app/domain_repository.py tests/integration/test_database_migrations.py`: PASS.
- Local `PYTHONPATH=/private/tmp/eei-ruff:/private/tmp/eei-pydeps .venv/bin/ruff check apps/api/app/domain.py apps/api/app/domain_repository.py tests/integration/test_database_migrations.py`: PASS.
- Local `.venv/bin/python scripts/validate_contracts.py`: PASS.
- Local `/usr/local/bin/npx --yes pnpm@11.8.0 --filter @eei/web typecheck` with non-sandbox network after sandbox DNS failure: PASS.
- Local `/usr/local/bin/npx --yes pnpm@11.8.0 --filter @eei/web exec playwright test --config=../../playwright.config.ts tests/e2e/state-contract.spec.ts -g "A204 and A205"` with non-sandbox network/browser after sandbox DNS failure: PASS, 1/1.
- Local `make verify`: PASS.
- Local `make verify-g2-db`: BLOCKED before tests because Docker is not installed in this environment; GitHub Actions remains the PostgreSQL/live E2E evidence source for this run.
- GitHub Actions `EEI validation` on `2b5b31ba2ed85b83d5526299cfed2e6e47073bb9`: PASS, run `27868806332`, job `82477214953`; Steps 7-12 all succeeded, including G2 PostgreSQL integration, browser E2E and live FastAPI/PostgreSQL E2E.

### Remaining gaps

- Model-center online profile editing remains open.
- At this rollback-endpoint slice point, dedicated score recompute controls were still open; they are addressed by the follow-on enqueue slice below, while the worker handler remains open.
- Worker-driven data snapshot refresh and transactional outbox remain open.
- Online model editing, the worker-driven score recompute handler and worker-driven data refresh/outbox still keep T1303/A204-A205 open despite this CI-validated rollback endpoint slice.

## 2026-06-20 - T1303/T1304/A204-A206 score recompute enqueue control

### Scope

- Added FastAPI route `POST /v1/scoring/recompute`.
- Implemented `DomainRepository.enqueue_score_recompute()` as a transaction-scoped active-context guard:
  - locks `active_analysis_contexts.context_key='global'`;
  - checks `expected_active_profile_version_id`;
  - checks `client_refresh_token`;
  - returns 409 with `score-recompute-conflict-v1` for stale active profile or stale refresh token;
  - inserts idempotent `background_jobs.job_type='score_recompute'` with active profile, active data snapshot, active scoring run and refresh generation in payload;
  - writes `operation_logs.action_type='enqueue_score_recompute'` for success and conflict.
- Added frontend `requestScoreRecompute()` client and a model-center `Recompute scores` control.
- Exposed recompute status through `data-score-recompute-*` DOM attributes for E2E and future operator checks.
- Corrected WorkspaceContext model-center server endpoints from the obsolete `/v1/model/active-context` to `/v1/scoring/active-context` and added `/v1/scoring/recompute`.
- Extended integration and Playwright contracts for activate -> stale refresh -> recompute enqueue -> rollback.

### Files changed

- `apps/api/app/domain.py`
- `apps/api/app/domain_repository.py`
- `apps/web/src/app/model-activation-client.ts`
- `apps/web/src/app/page.tsx`
- `apps/web/src/app/workspace-context.tsx`
- `specs/api_contract.yaml`
- `tests/e2e/home.spec.ts`
- `tests/e2e/state-contract.spec.ts`
- `tests/integration/test_database_migrations.py`
- `artifacts/tests/a204/t1303_transactional_model_activation_contract.json`
- `artifacts/tests/a205/t1303_atomic_refresh_context_contract.json`
- `artifacts/tests/a206/t1304_scheduler_retry_dead_letter_contract.json`
- `DEVELOPMENT_STATUS.md`
- `README.md`
- `MODEL_MANAGEMENT.md`
- `data/development_status_ledger.csv`
- `data/function_catalog.csv`
- `data/acceptance_traceability.csv`
- `docs/phase/V5_TASK_PACK_SYNCHRONIZATION.md`
- `docs/phase/MVP_DEVELOPMENT_RECORD.md`

### Acceptance mapping

- T1303 -> A204, A205.
- T1304 -> A206.
- At this enqueue-control slice point, A204/A205/A206 remained `IN_PROGRESS`, not `DONE`, because online model editing, the actual `score_recompute` worker handler, worker-driven data refresh/outbox, deployment wake and soak evidence were still open. The follow-on worker execution slice below addresses the handler portion, while the other blockers remain open.

### Validation

- Local `python3 -m py_compile apps/api/app/domain.py apps/api/app/domain_repository.py tests/integration/test_database_migrations.py`: PASS.
- Local `.venv/bin/python scripts/validate_contracts.py`: PASS.
- Local `.venv/bin/ruff check apps/api/app/domain.py apps/api/app/domain_repository.py tests/integration/test_database_migrations.py`: PASS.
- Local `npx --yes pnpm@11.8.0 --filter @eei/web typecheck` with non-sandbox network after sandbox DNS failure: PASS.
- Local `npx --yes pnpm@11.8.0 --filter @eei/web exec playwright test --config=../../playwright.config.ts tests/e2e/state-contract.spec.ts -g "A204 and A205"` with non-sandbox browser/network: PASS, 1/1.
- Local `npx --yes pnpm@11.8.0 --filter @eei/web exec playwright test --config=../../playwright.config.ts tests/e2e/home.spec.ts -g "A211 exposes WorkspaceContext"` with non-sandbox browser/network: PASS, 1/1.
- Local `make verify`: PASS.
- Local `make verify-g2-db`: BLOCKED before tests because Docker is not installed in this environment; GitHub Actions remains the PostgreSQL/live E2E evidence source for this DB-backed slice.
- GitHub Actions `EEI validation` on `f3ed3cfca557b8cef8e6ed07a5d0a8fdcc421aef`: PASS, run `27869583493`, job `82479246130`; Steps 7-12 all succeeded, including G2 PostgreSQL integration, browser E2E and live FastAPI/PostgreSQL E2E.

### Remaining gaps

- At this enqueue-control slice point, `score_recompute` jobs were enqueued but no worker handler executed score recomputation yet; the follow-on worker execution slice below addresses that gap.
- Worker-driven data snapshot refresh remains open; transactional outbox event sourcing was added in the following T1303/T1304 slice.
- 4h/24h soak, authn/authz, formal fact publication, multi-object scoring and brand clearance remain v0.1 blockers.

## 2026-06-20 - T1303/T1304/A204-A206 score recompute worker execution

### Scope

- Added `apps/api/app/scoring.py` as the shared relationship fact candidate scoring helper.
- Updated API score explanation to reuse the shared helper instead of carrying a separate formula path.
- Added a real `score_recompute` handler to `scripts/job_scheduler.py`:
  - validates `score-recompute-job-v1` payloads and active-context freshness;
  - treats stale active profile or stale refresh token as `skipped_stale_context` completion instead of an infinite retry loop;
  - creates a completed `scoring_runs` row for the active profile and data snapshot;
  - writes `score_results` for `relationship_fact_candidate` objects using the same confidence/evidence-quality formula as the explanation API;
  - advances `active_analysis_contexts.refresh_token` and `refresh_generation`;
  - logs `operation_logs.action_type='execute_score_recompute'`.
- Hardened scheduler clock precision after GitHub Actions run `27870437760` exposed a race where PostgreSQL `scheduled_for DEFAULT now()` kept microseconds while the worker clock was truncated to whole seconds, making a newly queued `score_recompute` job temporarily invisible to `lease_next_job()`.
- Extended the PostgreSQL integration contract so API enqueue -> scheduler `run_once` -> scoring run -> score_results -> refresh-token advance is verified in one flow.
- Added unit coverage for the candidate scoring helper.

### Files changed

- `apps/api/app/scoring.py`
- `apps/api/app/domain_repository.py`
- `scripts/job_scheduler.py`
- `tests/integration/test_database_migrations.py`
- `tests/unit/test_scoring.py`
- `README.md`
- `DEVELOPMENT_STATUS.md`
- `MODEL_MANAGEMENT.md`
- `data/function_catalog.csv`
- `data/development_status_ledger.csv`
- `data/acceptance_traceability.csv`
- `docs/phase/V5_TASK_PACK_SYNCHRONIZATION.md`
- `docs/phase/MVP_DEVELOPMENT_RECORD.md`
- `artifacts/tests/a204/t1303_transactional_model_activation_contract.json`
- `artifacts/tests/a205/t1303_atomic_refresh_context_contract.json`
- `artifacts/tests/a206/t1304_scheduler_retry_dead_letter_contract.json`
- `artifacts/tests/a211/t1308_frontend_workspace_context_contract.json`

### Acceptance mapping

- T1303 -> A204, A205.
- T1304 -> A206.
- A204/A205/A206 remain `IN_PROGRESS`, not `DONE`, because online model editing, transactional outbox, worker-driven data snapshot refresh, deployment wake/supervision, ingestion/calibration handlers and 4h/24h soak evidence remain open.

### Validation

- Local `python3 -m py_compile apps/api/app/scoring.py apps/api/app/domain_repository.py scripts/job_scheduler.py tests/integration/test_database_migrations.py`: PASS.
- Local `.venv/bin/ruff check apps/api/app/scoring.py apps/api/app/domain_repository.py scripts/job_scheduler.py tests/integration/test_database_migrations.py tests/unit/test_scoring.py`: PASS.
- Local `.venv/bin/python -m pytest -q tests/unit/test_scoring.py`: PASS, 2/2.
- Local `.venv/bin/python scripts/validate_contracts.py`: PASS.
- Local `UV_CACHE_DIR=/private/tmp/eei-uv-cache make verify` with non-sandbox browser permission after sandbox Chromium Mach-port denial: PASS; unit tests 15/15.
- GitHub Actions `EEI validation` on `721959ec84832bf158b237bf3d131b4cdde28c15`: FAIL, run `27870437760`, job `82481349638`; Steps 7-9 passed, Step 10 `Verify G2 PostgreSQL integration` failed because `run_once(job_type='score_recompute')` could return `None` before the database-default `scheduled_for` timestamp became due. This was fixed by retaining microsecond precision in the scheduler clock.
- GitHub Actions `EEI validation` on `b30f187c23d3bcb0da3ba2aac6cbcf195b4b5a30`: PASS, run `27870596002`, job `82481735289`; Steps 7-12 all succeeded, including G2 PostgreSQL integration, browser E2E and live FastAPI/PostgreSQL E2E.
- Local `make verify-g2-db`: BLOCKED before tests because Docker is not installed in this environment.
- PostgreSQL execution proof is expected from GitHub Actions G2 integration because this local environment does not provide Docker/PostgreSQL.

### Remaining gaps

- The scheduler still lacks real curated ingestion and calibration handlers.
- Continuous deployment wake/supervision is not implemented.
- Transactional outbox and worker-driven data snapshot refresh remain open.
- 4h/24h soak, authn/authz, formal fact publication, multi-object scoring and brand clearance remain v0.1 blockers.

## 2026-06-20 - T1303/T1304/A204-A206 transactional outbox refresh events

### Scope

- Added migration `0009_transactional_outbox` as the durable refresh event source required by the v5 live recalculation architecture.
- Added `transactional_outbox` schema validation for required columns, temporal fields and indexes.
- Model activation and rollback now write `model.profile.activated` outbox events in the same transaction that switches the active profile and refresh token.
- `POST /v1/scoring/recompute` now writes a `score.recompute.requested` outbox event using the same idempotent active-context key as the background job.
- The `score_recompute` worker now writes `score.snapshot.activated` after it creates the scoring run, score results and new active-context refresh token.
- Added scheduler outbox dispatch support through `dispatch_outbox_once()` and CLI `dispatch-outbox-once`, with dispatched/failed/dead-letter state and `dispatch_outbox_event` operation logs.
- Extended the PostgreSQL integration contract to assert outbox idempotency, dispatch status and operation-log evidence.

### Files changed

- `infra/db/migrations/0009_transactional_outbox/up.sql`
- `infra/db/migrations/0009_transactional_outbox/down.sql`
- `apps/api/app/domain_repository.py`
- `scripts/job_scheduler.py`
- `scripts/check_database_schema.py`
- `scripts/validate_v5_production_readiness_sync.py`
- `tests/integration/test_database_migrations.py`
- `README.md`
- `DEVELOPMENT_STATUS.md`
- `MODEL_MANAGEMENT.md`
- `data/function_catalog.csv`
- `data/development_status_ledger.csv`
- `data/acceptance_traceability.csv`
- `docs/phase/V5_TASK_PACK_SYNCHRONIZATION.md`
- `docs/phase/MVP_DEVELOPMENT_RECORD.md`
- `artifacts/tests/a204/t1303_transactional_model_activation_contract.json`
- `artifacts/tests/a205/t1303_atomic_refresh_context_contract.json`
- `artifacts/tests/a206/t1304_scheduler_retry_dead_letter_contract.json`

### Acceptance mapping

- T1303 -> A204, A205.
- T1304 -> A206.
- A204/A205/A206 remain `IN_PROGRESS`, not `DONE`, because online model editing, worker-driven data snapshot refresh, deployment wake/supervision, ingestion/calibration handlers and 4h/24h soak evidence remain open.

### Validation

- Local `python3 -m py_compile apps/api/app/domain_repository.py scripts/job_scheduler.py scripts/check_database_schema.py tests/integration/test_database_migrations.py`: PASS.
- Local `.venv/bin/ruff check apps/api/app/domain_repository.py scripts/job_scheduler.py scripts/check_database_schema.py tests/integration/test_database_migrations.py`: PASS.
- Local `UV_CACHE_DIR=/private/tmp/eei-uv-cache make verify` with non-sandbox browser permission: PASS; unit tests 15/15.
- GitHub Actions `EEI validation` on `253bd76a8b8dfe3fbe187486adbd3d2063d27d28`: PASS, run `27871229983`, job `82483284402`; Steps 7-12 all succeeded, including G2 PostgreSQL integration, browser E2E and live FastAPI/PostgreSQL E2E.
- PostgreSQL execution proof must come from GitHub Actions G2 integration because this local environment does not provide Docker/PostgreSQL.

### Remaining gaps

- Outbox dispatch currently marks durable events as dispatched; SSE gateway, deployment wake and worker supervision remain open.
- Worker-driven data snapshot activation was added in the following T1303/T1304 slice.
- Real curated ingestion and calibration handlers remain unregistered.
- 4h/24h soak, authn/authz, formal fact publication, multi-object scoring and brand clearance remain v0.1 blockers.

## 2026-06-20 - T1303/T1304/A204-A206 worker-driven data snapshot refresh

### Scope

- Added `POST /v1/data/snapshots/refresh` as the active-context guarded enqueue API for worker-driven data snapshot refresh.
- Added `data_snapshot_refresh` background jobs using the same active profile, refresh token and refresh generation idempotency semantics as `score_recompute`.
- Added `data.snapshot.refresh.requested` transactional outbox events at enqueue time.
- Added a `data_snapshot_refresh` scheduler handler that validates active-context freshness, creates a new active `data_snapshots` row, supersedes the prior active snapshot for the same scope and record mode, advances `active_analysis_contexts.refresh_token`, logs `execute_data_snapshot_refresh` and writes `data.snapshot.activated`.
- Extended the PostgreSQL integration contract so the same flow now verifies model activation, score recompute, data snapshot refresh, outbox dispatch and rollback in one refresh-token chain.

### Files changed

- `apps/api/app/domain.py`
- `apps/api/app/domain_repository.py`
- `scripts/job_scheduler.py`
- `specs/api_contract.yaml`
- `tests/integration/test_database_migrations.py`
- `README.md`
- `DEVELOPMENT_STATUS.md`
- `MODEL_MANAGEMENT.md`
- `data/function_catalog.csv`
- `data/development_status_ledger.csv`
- `data/acceptance_traceability.csv`
- `docs/phase/V5_TASK_PACK_SYNCHRONIZATION.md`
- `docs/phase/MVP_DEVELOPMENT_RECORD.md`
- `artifacts/tests/a204/t1303_transactional_model_activation_contract.json`
- `artifacts/tests/a205/t1303_atomic_refresh_context_contract.json`
- `artifacts/tests/a206/t1304_scheduler_retry_dead_letter_contract.json`

### Acceptance mapping

- T1303 -> A204, A205.
- T1304 -> A206.
- A204/A205/A206 remain `IN_PROGRESS`, not `DONE`, because model-center online editing, deployment wake/supervision, ingestion/calibration handlers and 4h/24h soak evidence remain open.

### Validation

- Local `python3 -m py_compile apps/api/app/domain.py apps/api/app/domain_repository.py scripts/job_scheduler.py tests/integration/test_database_migrations.py`: PASS.
- Local `.venv/bin/ruff check apps/api/app/domain.py apps/api/app/domain_repository.py scripts/job_scheduler.py tests/integration/test_database_migrations.py`: PASS.
- Local `.venv/bin/python scripts/validate_contracts.py`: PASS.
- Local `.venv/bin/python -m pytest -q tests/unit/test_scoring.py tests/unit/test_api_health.py`: PASS, 11/11.
- Local `UV_CACHE_DIR=/private/tmp/eei-uv-cache make verify` with non-sandbox browser permission: PASS; unit tests 15/15.
- GitHub Actions `EEI validation` on `405d664b53f872b72be6ee14fe83242a2dd13820`: PASS, run `27871752533`, job `82484659437`; Steps 7-12 all succeeded, including G2 PostgreSQL integration, browser E2E and live FastAPI/PostgreSQL E2E.
- PostgreSQL execution proof must come from GitHub Actions G2 integration because this local environment does not provide Docker/PostgreSQL.

### Remaining gaps

- This is a database snapshot activation contract over curated fixture/current database state; it is not live/full-text ingestion.
- SSE gateway, LISTEN/NOTIFY wake, deployment worker supervision and 4h/24h soak remain open.
- Real curated ingestion and calibration handlers remain unregistered.
- Authn/authz, formal fact publication, multi-object scoring and brand clearance remain v0.1 blockers.

## 2026-06-20 - T1305/A207 saved-view namespace isolation boundary

### Scope

- Added saved-view principal resolution through `X-EEI-User-Namespace` and `X-EEI-Actor` headers, with `local_user` retained as the local MVP default.
- Added `0010_operation_log_actor_principal` so `operation_logs.actor` can store trusted principal ids that match the saved-view header pattern.
- Constrained `/v1/saved-views/{savedViewId}` get/update/version-list/restore repository lookups by `saved_views.namespace`.
- Added cross-namespace fail-closed semantics: another namespace cannot read, update, list versions or restore a saved view id and receives 404.
- Preserved same-name saved views across different namespaces while keeping duplicate-name conflict inside one namespace/workspace.
- Updated the OpenAPI contract, A207 integration evidence and v5 production-readiness ledgers.

### Files changed

- `apps/api/app/domain.py`
- `apps/api/app/domain_repository.py`
- `infra/db/migrations/0010_operation_log_actor_principal/up.sql`
- `infra/db/migrations/0010_operation_log_actor_principal/down.sql`
- `specs/domain_schema.sql`
- `specs/api_contract.yaml`
- `tests/integration/test_database_migrations.py`
- `artifacts/tests/a207/t1305_server_saved_view_conflict_recovery_contract.json`
- `README.md`
- `DEVELOPMENT_STATUS.md`
- `data/development_status_ledger.csv`
- `data/acceptance_traceability.csv`
- `docs/phase/V5_TASK_PACK_SYNCHRONIZATION.md`
- `docs/phase/MVP_DEVELOPMENT_RECORD.md`

### Acceptance mapping

- T1305 -> A207.
- A207 remains `IN_PROGRESS`, not `DONE`, because public multi-user deployment still needs trusted production identity/gateway binding for the saved-view headers.

### Validation

- Pending in this run: py_compile, ruff, contract/catalog/status validators, targeted PostgreSQL integration and full `make verify`.

### Remaining gaps

- `X-EEI-User-Namespace` and `X-EEI-Actor` must be set by trusted middleware/gateway or an identity provider before public use; direct client-provided identity headers are not production authn.
- Sharing links, export and final cross-user collaboration policy remain open.

## 2026-06-20 - T1304/A206 ingestion and calibration scheduler handlers

### Scope

- Registered `curated_ingestion_refresh` in `scripts/job_scheduler.py`, reusing the curated official NVIDIA/ASML loader idempotently and emitting `data.ingestion.completed`.
- Registered `calibration_run` in `scripts/job_scheduler.py`, writing calibration coverage metrics, drift warnings, `proposal_status=none`, `execute_calibration_run` operation logs and `calibration.run.completed`.
- Changed `POST /v1/calibrations/run` from a calibration row-only API into a transactional calibration row + `background_jobs` + `calibration.run.requested` outbox enqueue contract.
- Preserved the MVP no-auto-activation rule for calibration proposals.
- Updated A206 evidence, README, model/calibration docs, v5 sync docs, function catalog, development ledger and acceptance traceability.

### Files changed

- `apps/api/app/domain_repository.py`
- `scripts/job_scheduler.py`
- `scripts/load_curated_ingestion_anchors.py`
- `tests/integration/test_database_migrations.py`
- `artifacts/tests/a206/t1304_scheduler_retry_dead_letter_contract.json`
- `data/acceptance_traceability.csv`
- `data/development_status_ledger.csv`
- `data/function_catalog.csv`
- `README.md`
- `DEVELOPMENT_STATUS.md`
- `MODEL_MANAGEMENT.md`
- `docs/16_OPERATION_LOG_AND_BIWEEKLY_CALIBRATION.md`
- `docs/phase/V5_TASK_PACK_SYNCHRONIZATION.md`
- generated release/status artifacts

### Acceptance mapping

- T1301 -> A202 for curated official ingestion evidence; still `IN_PROGRESS` because live/full-text ingestion, independent-source approval and formal publication remain open.
- T1304 -> A206 for scheduler lease/retry/dead-letter plus `score_recompute`, `data_snapshot_refresh`, `curated_ingestion_refresh` and `calibration_run` execution contracts.
- T605/T606 -> A090-A093 partial coverage through 14-day queue, metrics/drift report and no-auto-activation; accept/reject and failure-injection coverage remain open.
- A206 remains `IN_PROGRESS`, not `DONE`, because deployment wake/supervision and 4h/24h soak are still open.

### Validation

- Local `python3 -m py_compile scripts/job_scheduler.py scripts/load_curated_ingestion_anchors.py apps/api/app/domain_repository.py tests/integration/test_database_migrations.py`: PASS.
- Local `.venv/bin/ruff check scripts/job_scheduler.py scripts/load_curated_ingestion_anchors.py apps/api/app/domain_repository.py tests/integration/test_database_migrations.py`: PASS.
- Local `.venv/bin/python scripts/validate_contracts.py`: PASS.
- Local `.venv/bin/python scripts/validate_catalog_integrity.py`: PASS.
- Local `.venv/bin/python scripts/validate_v5_production_readiness_sync.py`: PASS.
- Local `.venv/bin/python scripts/manage_development_status_artifacts.py generate`: PASS.
- Local `.venv/bin/python scripts/manage_development_status_artifacts.py validate`: PASS.
- Local `UV_CACHE_DIR=/private/tmp/eei-uv-cache make generate-clean-room-release`: PASS.
- Local `UV_CACHE_DIR=/private/tmp/eei-uv-cache make generate-release-artifacts`: PASS after sequential rerun; one earlier parallel generation attempt failed due clean-room ZIP checksum race.
- Local `UV_CACHE_DIR=/private/tmp/eei-uv-cache make validate-clean-room-release`: PASS.
- Local `UV_CACHE_DIR=/private/tmp/eei-uv-cache make validate-release-artifacts`: PASS.
- Local `shasum -a 256 -c CHECKSUMS.sha256`: PASS.
- Local `UV_CACHE_DIR=/private/tmp/eei-uv-cache make verify`: PASS after installing project-local Playwright Chromium; unit tests 15/15 with one existing Starlette/httpx deprecation warning.
- GitHub Actions `EEI validation` on `c67c1d7cab139f56555c57c31645fdf982da72c9`: PASS, run `27873417595`, job `82488885381`; Steps 7-12 all succeeded, including G2 PostgreSQL integration, browser E2E and live FastAPI/PostgreSQL E2E.
- PostgreSQL execution proof comes from GitHub Actions G2 because this local host does not provide Docker/PostgreSQL.

### Remaining gaps

- `curated_ingestion_refresh` is still curated official fixture/current-anchor ingestion, not live/full-text ingestion.
- Calibration accept/reject proposal API/UI and failure-injection coverage remain open.
- Deployment-level worker wake/supervision, LISTEN/NOTIFY or equivalent scheduler automation and 4h/24h soak remain open.
- Formal fact publication, multi-object scoring, trusted saved-view identity boundary and brand clearance remain v0.1 blockers.

## 2026-06-21 - T1304/A206 worker supervisor CLI

### Scope

- Replaced the placeholder worker shell with `apps.worker` health, once and supervise commands.
- `health` emits `eei-worker-health-v1` JSON with background job counts, outbox counts, expired leases, latest heartbeats and dead-letter count.
- `once` runs one bounded recover -> job execution -> outbox dispatch cycle and emits `eei-worker-cycle-v1`.
- `supervise` loops bounded cycles, supports idle stop for operator probes, and handles SIGTERM/SIGINT for graceful stop.
- Added Makefile operator commands: `worker-health`, `worker-once` and `worker-supervise`.
- Extended PostgreSQL integration coverage so the supervisor executes a real queued job, dispatches outbox events and proves idle-stop behavior.

### Files changed

- `apps/worker/app/main.py`
- `Makefile`
- `tests/integration/test_database_migrations.py`
- `artifacts/tests/a206/t1304_scheduler_retry_dead_letter_contract.json`
- `data/acceptance_traceability.csv`
- `data/development_status_ledger.csv`
- `DEVELOPMENT_STATUS.md`
- `README.md`
- `MODEL_MANAGEMENT.md`
- `docs/16_OPERATION_LOG_AND_BIWEEKLY_CALIBRATION.md`
- `docs/phase/V5_TASK_PACK_SYNCHRONIZATION.md`
- generated development-status artifacts

### Acceptance mapping

- T1304 -> A206 for worker supervision, scheduler recovery and outbox dispatch execution.
- T1307 -> A209 remains partial because this CLI produces soak-observable worker metrics but does not replace 4h/24h operator soak evidence.
- A206 remains `IN_PROGRESS`, not `DONE`, until the target deployment runtime binds `worker-supervise` to a process manager and long-duration soak evidence is attached.

### Validation

- Local `python3 -m py_compile apps/worker/app/main.py tests/integration/test_database_migrations.py`: PASS.
- Local `.venv/bin/ruff check apps/worker/app/main.py tests/integration/test_database_migrations.py`: PASS after import sorting.
- Local `.venv/bin/python scripts/validate_contracts.py`: PASS.
- Local `.venv/bin/python scripts/validate_catalog_integrity.py`: PASS.
- Local `.venv/bin/python scripts/validate_v5_production_readiness_sync.py`: PASS.
- Local `.venv/bin/python scripts/manage_development_status_artifacts.py generate`: PASS.
- Local `.venv/bin/python scripts/manage_development_status_artifacts.py validate`: PASS.
- Local `.venv/bin/python -m pytest -q tests/unit/test_scoring.py tests/unit/test_api_health.py`: PASS, 11 tests with one existing Starlette/httpx deprecation warning.
- Local `env -u DATABASE_URL .venv/bin/python -m pytest -q tests/integration/test_database_migrations.py`: expected SKIP on this host because no local PostgreSQL is configured.
- Local `UV_CACHE_DIR=/private/tmp/eei-uv-cache make generate-clean-room-release`: PASS; clean-room ZIP regenerated.
- Local `UV_CACHE_DIR=/private/tmp/eei-uv-cache make generate-release-artifacts`: PASS; remote status remains `PENDING` until this commit has GitHub Actions evidence.
- Local `UV_CACHE_DIR=/private/tmp/eei-uv-cache make validate-clean-room-release`: PASS.
- Local `UV_CACHE_DIR=/private/tmp/eei-uv-cache make validate-release-artifacts`: PASS.
- Local `shasum -a 256 -c CHECKSUMS.sha256`: PASS.
- Local sandboxed `UV_CACHE_DIR=/private/tmp/eei-uv-cache make verify`: expected FAIL at Chromium launch with macOS `bootstrap_check_in ... Permission denied`; rerun with approved elevated browser permission.
- Local elevated `UV_CACHE_DIR=/private/tmp/eei-uv-cache make verify`: PASS; includes governance, contract, prototype parity, GitHub governance, v5 sync, development/risk/release validation, scale benchmark, Chromium browser benchmark, soak smoke, secret scan, UI copy lint, ruff, web typecheck and unit tests 15/15.
- GitHub Actions `EEI validation` on `741a1968e7b4633fa4e7d693c638841c8143f9c1`: PASS, run `27873931210`, job `82490200774`; Steps 7-12 all succeeded, including G2 PostgreSQL integration, browser E2E and live FastAPI/PostgreSQL E2E.

### Remaining gaps

- Target deployment runtime process-manager binding was superseded by the 2026-06-21 Docker Compose worker binding entry below.
- T1307 4h and 24h soak runs remain required before A209 or scheduler stability can be called production-ready.
- LISTEN/NOTIFY or an equivalent low-latency wake path remains optional for v0.1 but would reduce polling latency.

## 2026-06-21 - T1304/A206 Docker Compose worker process binding

### Scope

- Added `migrate` and `worker` services to `docker-compose.yml` under the `worker` profile.
- Added `infra/docker/worker.Dockerfile` for the worker/migration runtime.
- Added `scripts/validate_worker_deployment.py` to validate the process-manager contract without starting containers.
- Wired `make validate-worker-deployment` into `make verify`.
- Extended `scripts/run_soak_smoke.mjs` so A209 smoke output references the A206 Docker Compose worker binding.
- Updated A206/A209 traceability, status ledger, Docker docs and v5 synchronization records.

### Files changed

- `docker-compose.yml`
- `infra/docker/README.md`
- `infra/docker/worker.Dockerfile`
- `scripts/validate_worker_deployment.py`
- `scripts/run_soak_smoke.mjs`
- `Makefile`
- `artifacts/tests/a206/t1304_scheduler_retry_dead_letter_contract.json`
- `artifacts/tests/a206/t1304_worker_deployment_binding_contract.json`
- `artifacts/tests/a209/t1307_soak_smoke.json`
- `data/acceptance_traceability.csv`
- `data/development_status_ledger.csv`
- `README.md`
- `DEVELOPMENT_STATUS.md`
- `MODEL_MANAGEMENT.md`
- `docs/16_OPERATION_LOG_AND_BIWEEKLY_CALIBRATION.md`
- `docs/phase/V5_TASK_PACK_SYNCHRONIZATION.md`
- generated release/status artifacts

### Acceptance mapping

- T1304 -> A206 for Docker Compose worker process-manager binding.
- T1307 -> A209 remains partial; the smoke harness now points operator soak to the Compose binding but does not replace 4h/24h runs.
- A206 remains `IN_PROGRESS`, not `DONE`, until the 4h/24h operator soak is attached.

### Validation

- Local `python3 -m py_compile scripts/validate_worker_deployment.py`: PASS.
- Local `.venv/bin/ruff check scripts/validate_worker_deployment.py apps/worker/app/main.py tests/integration/test_database_migrations.py`: PASS.
- Local `.venv/bin/python scripts/validate_worker_deployment.py`: PASS and generated `artifacts/tests/a206/t1304_worker_deployment_binding_contract.json`.
- Local sandboxed `node scripts/run_soak_smoke.mjs --mode ci_smoke --duration-seconds 3 --output artifacts/tests/a209/t1307_soak_smoke.json --fail-on-budget --quiet`: expected FAIL at Chromium launch with macOS `bootstrap_check_in ... Permission denied`; rerun with approved elevated browser permission.
- Local elevated `node scripts/run_soak_smoke.mjs --mode ci_smoke --duration-seconds 3 --output artifacts/tests/a209/t1307_soak_smoke.json --fail-on-budget --quiet`: PASS; A209 remains `PARTIAL` and includes `worker_supervisor_binding_available=true`.
- Local `.venv/bin/python scripts/validate_contracts.py`: PASS.
- Local `.venv/bin/python scripts/validate_catalog_integrity.py`: PASS.
- Local `.venv/bin/python scripts/validate_v5_production_readiness_sync.py`: PASS.
- Local `.venv/bin/python scripts/manage_development_status_artifacts.py generate`: PASS.
- Local `.venv/bin/python scripts/manage_development_status_artifacts.py validate`: PASS.
- Local `UV_CACHE_DIR=/private/tmp/eei-uv-cache make generate-clean-room-release`: PASS; clean-room ZIP now includes 352 paths.
- Local `UV_CACHE_DIR=/private/tmp/eei-uv-cache make generate-release-artifacts`: PASS; manifest now includes 359 paths.
- Local `UV_CACHE_DIR=/private/tmp/eei-uv-cache make validate-clean-room-release`: PASS.
- Local `UV_CACHE_DIR=/private/tmp/eei-uv-cache make validate-release-artifacts`: PASS.
- Local `shasum -a 256 -c CHECKSUMS.sha256`: PASS.
- Local elevated `UV_CACHE_DIR=/private/tmp/eei-uv-cache make verify`: PASS; includes governance, contract, prototype parity, GitHub governance, v5 sync, worker deployment validator, development/risk/release validation, scale benchmark, Chromium browser benchmark, soak smoke, secret scan, UI copy lint, ruff, web typecheck and unit tests 15/15.
- GitHub Actions `EEI validation` on `a7675452963ab7102f8edaa2af502cb2496b9924`: PASS, run `27874568202`, job `82491806968`; Steps 7-12 all succeeded, including G2 PostgreSQL integration, browser E2E and live FastAPI/PostgreSQL E2E.

### Remaining gaps

- T1307 4h and 24h operator soak runs remain required before A206/A209 can be called production-ready.
- Docker Compose is the default MVP local process manager; non-Compose deployment bindings remain out of scope unless a target hosting runtime is selected.
- LISTEN/NOTIFY or an equivalent low-latency wake path remains optional for v0.1 but would reduce polling latency.

## 2026-06-21 - T1305/A207 saved-view trusted gateway identity binding

### Scope

- Added production saved-view identity mode `trusted_gateway`.
- Kept `local` identity mode as the explicit local-development path.
- Defaulted `EEI_ENV=prod|production` to `trusted_gateway`.
- Added fail-closed gateway checks for missing `EEI_SAVED_VIEW_GATEWAY_SECRET`, missing identity headers, invalid signatures and expired timestamps.
- Added HMAC-SHA256 signature verification over signature version, HTTP method, request path, namespace, actor and timestamp.
- Added `X-EEI-Auth-Timestamp` and `X-EEI-Auth-Signature` to CORS and OpenAPI saved-view operations.
- Added saved-view identity runtime parameters to `data/parameter_catalog.csv` and `config/model_runtime_defaults.yaml`.
- Updated A207 evidence, traceability, task backlog, status ledger, v5 sync and README records.

### Files changed

- `.env.example`
- `apps/api/app/domain.py`
- `apps/api/app/main.py`
- `apps/api/app/settings.py`
- `specs/api_contract.yaml`
- `tests/unit/test_api_health.py`
- `data/parameter_catalog.csv`
- `config/model_runtime_defaults.yaml`
- `data/task_backlog.csv`
- `data/acceptance_matrix.csv`
- `data/acceptance_traceability.csv`
- `data/development_status_ledger.csv`
- `artifacts/tests/a207/t1305_server_saved_view_conflict_recovery_contract.json`
- `artifacts/tests/a207/t1305_frontend_saved_view_api_adapter_contract.json`
- `artifacts/tests/a207/t1305_live_saved_view_multisession_e2e_contract.json`
- `artifacts/tests/a207/t1305_saved_view_trusted_gateway_contract.json`
- `README.md`
- `DEVELOPMENT_STATUS.md`
- `MODEL_MANAGEMENT.md`
- `docs/phase/V5_TASK_PACK_SYNCHRONIZATION.md`
- `docs/STATUS.md`
- `docs/30_MODEL_MANAGEMENT.md`
- `scripts/validate_catalog_integrity.py`
- `scripts/validate_governance.py`
- `scripts/generate_governance_pdf.py`

### Acceptance mapping

- T1305 -> A207.
- A207 is now `DONE` for the saved-view server conflict, version history, recovery, schema migration, namespace isolation and trusted gateway identity boundary.
- Share links, export and cross-user publication strategy remain future FUN-RM-03 enhancements and do not block A207.

### Validation

- Local `python3 -m py_compile apps/api/app/domain.py apps/api/app/settings.py tests/unit/test_api_health.py`: PASS.
- Local `.venv/bin/ruff check apps/api/app/domain.py apps/api/app/settings.py tests/unit/test_api_health.py`: PASS.
- Local `.venv/bin/python -m pytest -q tests/unit/test_api_health.py`: PASS, 17 tests with one existing Starlette/httpx deprecation warning.
- Local `.venv/bin/python scripts/validate_contracts.py`: PASS.
- Local `UV_CACHE_DIR=/private/tmp/eei-uv-cache make generate-clean-room-release`: PASS; clean-room ZIP now includes 353 paths.
- Local `UV_CACHE_DIR=/private/tmp/eei-uv-cache make generate-release-artifacts`: PASS; release manifest now includes 360 paths and checksum manifest includes 359 paths.
- Local `UV_CACHE_DIR=/private/tmp/eei-uv-cache make validate-clean-room-release`: PASS.
- Local `UV_CACHE_DIR=/private/tmp/eei-uv-cache make validate-release-artifacts`: PASS.
- Local `shasum -a 256 -c CHECKSUMS.sha256`: PASS.
- Local elevated `UV_CACHE_DIR=/private/tmp/eei-uv-cache make verify`: PASS; includes governance, contract, prototype parity, GitHub governance, v5 sync, worker deployment validator, development/risk/release validation, scale benchmark, Chromium browser benchmark, soak smoke, secret scan, UI copy lint, ruff, web typecheck and unit tests 23/23.
- GitHub Actions `EEI validation` on `6e95b450250a447a50061fb926b80e164bdbf9c5`: PASS, run `27875473970`, job `82494131119`; Steps 7-12 all succeeded, including static/contract/lint/typecheck/unit, G2 PostgreSQL integration, browser E2E and live FastAPI/PostgreSQL E2E.

### Remaining gaps

- This closes T1305/A207 with local and GitHub Actions evidence.
- T1301/A202, T1302/A203, T1303/A204-A205, T1304/A206, T1307/A209, T1308/A211 and T1309/A210 remain v0.1 blockers.
- T1307 4h and 24h operator soak still cannot be closed on the current host because Docker is not installed and the required duration has not been run.

## 2026-06-21 - T1308/A211 live production frontend cross-route closure

### Scope

- Extended the live FastAPI/PostgreSQL E2E reset path to load curated official ingestion anchors before the API starts.
- Added live A211 Playwright coverage for production graph hydration, catalog inventory, relationship_fact_candidate score explanation, evidence snippets, supply-chain lens controls, evidence center refresh, Objects and Scope, Industries and System Status routes.
- Converted A211 from `IN_PROGRESS` to `DONE` after GitHub Actions proved the new live cross-route path.
- Updated A211 evidence, task backlog, acceptance matrix, traceability, development status, v5 sync and release artifacts.

### Files changed

- `scripts/run_live_e2e_api.sh`
- `tests/e2e/saved-view-live.spec.ts`
- `artifacts/tests/a211/t1308_frontend_workspace_context_contract.json`
- `data/task_backlog.csv`
- `data/acceptance_matrix.csv`
- `data/acceptance_traceability.csv`
- `data/development_status_ledger.csv`
- `scripts/validate_v5_production_readiness_sync.py`
- `README.md`
- `DEVELOPMENT_STATUS.md`
- `docs/phase/V5_TASK_PACK_SYNCHRONIZATION.md`

### Acceptance mapping

- T1308 -> A211.
- A211 is now `DONE` for production componentized frontend routes, WorkspaceContext, real controls, disabled unfinished entries, persisted state/query wiring and live FastAPI/PostgreSQL cross-route hydration.

### Validation

- Local `npx --yes pnpm@11.8.0 --filter @eei/web exec playwright test --config=../../playwright.live.config.ts --list`: PASS; 3 live tests discovered including the new A211 live cross-route test.
- Local `npx --yes pnpm@11.8.0 --filter @eei/web typecheck`: PASS after rerun with network access.
- Local elevated `npx --yes pnpm@11.8.0 --filter @eei/web test:e2e -- tests/e2e/home.spec.ts`: PASS, 32/32 Playwright tests.
- Local elevated `UV_CACHE_DIR=/private/tmp/eei-uv-cache make verify`: PASS; includes governance, contract, prototype parity, GitHub governance, v5 sync, worker deployment validator, development/risk/release validation, scale benchmark, Chromium browser benchmark, soak smoke, secret scan, UI copy lint, ruff, web typecheck and unit tests 23/23.
- GitHub Actions `EEI validation` on `a57d1108a3c30da79ef3e35b1d3617f2efd4293a`: PASS, run `27876091338`, job `82495713946`; Steps 7-13 all succeeded, including G2 PostgreSQL integration, browser E2E and live FastAPI/PostgreSQL E2E.

### Remaining gaps

- This closes T1308/A211 with local and GitHub Actions evidence.
- T1301/A202, T1302/A203, T1303/A204-A205, T1304/A206, T1307/A209 and T1309/A210 remain v0.1 blockers.
- T1307 4h and 24h operator soak still cannot be closed on the current host because Docker is not installed and the required duration has not been run.

## 2026-06-21 - T1302/A203 published relationship scoring explain slice

### Scope

- Extended `/v1/scoring/explain/{objectType}/{objectId}` from candidate-only scoring to support `objectType=relationship`.
- Added `relationship_score_metrics()` for versioned published relationships, using confidence, source-threshold policy, review status, publication status, fact-version presence and evidence presence.
- Added repository support for relationship scoring payloads backed by `relationships`, `relationship_evidence`, `fact_versions`, `data_snapshots`, publication qualifiers and production context.
- Extended A202 reviewed-publication integration assertions so a published relationship can be scored after fixture review publication.

### Files changed

- `apps/api/app/scoring.py`
- `apps/api/app/domain_repository.py`
- `specs/api_contract.yaml`
- `tests/unit/test_scoring.py`
- `tests/integration/test_database_migrations.py`
- `artifacts/tests/a203/t1302_production_api_graph_scoring_contract.json`
- `data/development_status_ledger.csv`
- `DEVELOPMENT_STATUS.md`
- `README.md`
- `docs/phase/V5_TASK_PACK_SYNCHRONIZATION.md`

### Acceptance mapping

- T1302 -> A203.
- A203 remains `IN_PROGRESS`, not `DONE`.
- This closes the relationship-object scoring explanation gap for published relationship records. At that point, entity, event and industry scoring were still open; the subsequent entity slice below narrows this gap.

### Local validation

- `.venv/bin/ruff check apps/api/app/scoring.py apps/api/app/domain_repository.py tests/unit/test_scoring.py tests/integration/test_database_migrations.py`: PASS.
- `.venv/bin/python -m pytest -q tests/unit/test_scoring.py`: PASS, 4/4.
- `python3 -m py_compile apps/api/app/scoring.py apps/api/app/domain_repository.py tests/integration/test_database_migrations.py`: PASS.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/pytest -q tests/integration/test_database_migrations.py`: SKIPPED locally because this host has no database runtime.
- Elevated `UV_CACHE_DIR=/private/tmp/eei-uv-cache make verify`: PASS; includes governance, contract validation, v5 sync, release validation, scale/browser/soak smoke, secret scan, UI copy lint, ruff, web typecheck and unit tests 25/25.

### Remaining gaps

- At that point, A203 still needed full scoring service coverage for entity, event, industry and other non-relationship object families.
- At that point, A203 still depended on A202 for production-approved live relationship facts and on A208/A209 for release-scale and soak evidence; A208 was closed later and A209 remains open.

## 2026-06-21 - T1302/A203 entity scoring explain slice

### Scope

- Extended `/v1/scoring/explain/{objectType}/{objectId}` to support `objectType=entity`.
- Added `entity_score_metrics()` for entity coverage scoring using identifiers, aliases, relationship context, relationship-family diversity, relationship evidence source count, industry membership, active status and optional entity fact-version presence.
- Added repository support for entity scoring payloads backed by `entities`, `entity_identifiers`, `entity_aliases`, `relationships`, `relationship_evidence`, `entity_industry_memberships`, optional `fact_versions` and `production_context`.
- Extended PostgreSQL/FastAPI integration assertions for the NVIDIA Golden Vertical entity score explanation.

### Files changed

- `apps/api/app/scoring.py`
- `apps/api/app/domain_repository.py`
- `specs/api_contract.yaml`
- `tests/unit/test_scoring.py`
- `tests/integration/test_database_migrations.py`
- `artifacts/tests/a203/t1302_production_api_graph_scoring_contract.json`
- `data/development_status_ledger.csv`
- `DEVELOPMENT_STATUS.md`
- `README.md`
- `docs/phase/V5_TASK_PACK_SYNCHRONIZATION.md`

### Acceptance mapping

- T1302 -> A203.
- A203 remains `IN_PROGRESS`, not `DONE`.
- This closes the entity-object scoring explanation API slice, but not event/industry scoring, formally production-approved live relationship facts, or long-duration release gates.

### Local validation

- `.venv/bin/ruff check apps/api/app/scoring.py apps/api/app/domain_repository.py tests/unit/test_scoring.py tests/integration/test_database_migrations.py`: PASS.
- `.venv/bin/python -m pytest -q tests/unit/test_scoring.py`: PASS, 6/6.
- `python3 -m py_compile apps/api/app/scoring.py apps/api/app/domain_repository.py tests/integration/test_database_migrations.py`: PASS.
- `.venv/bin/python scripts/validate_contracts.py`: PASS.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache make generate-clean-room-release`: PASS.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache make generate-release-artifacts`: PASS after regenerating release checksums from the updated clean-room ZIP.
- Elevated `UV_CACHE_DIR=/private/tmp/eei-uv-cache make verify`: PASS; includes governance, contract validation, v5 sync, release validation, scale/browser/soak smoke, secret scan, UI copy lint, ruff, web typecheck and unit tests 27/27.
- GitHub Actions run `27878302123` / job `82501418538` for commit `ac6693539c4ff961a126921d56c043b7084cc27d`: FAIL in Step 10 G2 PostgreSQL integration because the entity score endpoint returned fixture record mode as `publication_status=fixture` where the contract expected published entity publication semantics.
- GitHub Actions run `27878398112` / job `82501662399` for commit `d2f35dbba2c508a6d39debf6a9c2431a1f694066`: PASS after fixing entity score `publication_status` to report `published` for active or fixture-backed entity records while retaining fixture semantics in `entity_status` and `record_mode`; Steps 10 G2 PostgreSQL integration, 11 browser E2E and 12 live FastAPI/PostgreSQL E2E all passed.

### Remaining gaps

- A203 still needs event/industry and remaining non-relationship object scoring coverage.
- A203 still depends on A202 for production-approved live relationship facts and on A209 for 4h/24h soak evidence.

## 2026-06-21 - T1302/A203 event and industry scoring explain slice

### Scope

- Extended `/v1/scoring/explain/{objectType}/{objectId}` to support `objectType=event` and `objectType=industry`.
- Added `event_score_metrics()` for event coverage scoring using participant context, independent source count, timing context, amount semantics, active event status, evidence chain and optional event fact-version presence.
- Added `industry_score_metrics()` for industry coverage scoring using member entity context, relationship context, relationship-family diversity, independent source count, taxonomy hierarchy, active industry status and optional industry fact-version presence.
- Connected the existing `data/mock_events.json` fixture file to `scripts/load_synthetic_fixtures.py` so PostgreSQL tests load event records, participants and event evidence idempotently.
- Changed event fixture source document ids to avoid overwriting existing relationship evidence documents and preserve `fixture://relationship/` evidence URLs.
- Extended PostgreSQL/FastAPI integration assertions for NVIDIA capex event and semiconductor industry score explanations.

### Files changed

- `apps/api/app/scoring.py`
- `apps/api/app/domain_repository.py`
- `scripts/load_synthetic_fixtures.py`
- `data/mock_events.json`
- `specs/api_contract.yaml`
- `tests/unit/test_scoring.py`
- `tests/integration/test_database_migrations.py`
- `artifacts/tests/a203/t1302_production_api_graph_scoring_contract.json`

### Acceptance mapping

- T1302 -> A203.
- A203 remains `IN_PROGRESS`, not `DONE`.
- This closes the event and industry scoring explanation API slice, but not remaining non-relationship object families, formally production-approved live relationship facts, or long-duration release gates.

### Formula and threshold contract

- Event minimum independent sources: `1`; minimum participant context: `1`.
- Event formula: participant context `20` + source threshold `20` + timing context `15` + amount semantics `10` + active event status `10` + evidence chain `15` + fact version `10`, multiplied by active event status.
- Industry minimum independent sources: `1`; minimum entity context: `3`; minimum relationship context: `3`; minimum relationship-family context: `3`.
- Industry formula: entity context `20` + relationship context `20` + relationship-family diversity `15` + source threshold `15` + taxonomy hierarchy `10` + active industry status `10` + fact version `10`, multiplied by active industry status.

### Local validation

- `python3 -m json.tool data/mock_events.json`: PASS.
- `python3 -m py_compile apps/api/app/scoring.py apps/api/app/domain_repository.py scripts/load_synthetic_fixtures.py tests/unit/test_scoring.py tests/integration/test_database_migrations.py`: PASS.
- `.venv/bin/ruff check apps/api/app/scoring.py apps/api/app/domain_repository.py scripts/load_synthetic_fixtures.py tests/unit/test_scoring.py tests/integration/test_database_migrations.py`: PASS.
- `.venv/bin/python -m pytest -q tests/unit/test_scoring.py`: PASS, 10/10.
- `.venv/bin/python scripts/validate_contracts.py`: PASS.
- `.venv/bin/python scripts/validate_v5_production_readiness_sync.py`: PASS.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/python -m pytest -q tests/integration/test_database_migrations.py`: SKIPPED locally because this host has no `DATABASE_URL` or `.env`.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache make verify`: PASS after the event/industry scoring slice and fixture query fix; unit tests 31/31.

### Remote CI validation

- GitHub Actions run `27879315501` / job `82504009018`: FAIL at Step 10 because SQL `LIKE 'fixture://%'` in the new fixture evidence checks used an unescaped `%` in psycopg query text.
- Commit `fe1d34fb216a4a09cbb0bc897dfaeac91d808f5c` fixed the query text by escaping the literal wildcard as `LIKE 'fixture://%%'`.
- GitHub Actions run `27879503435` / job `82504489377`: PASS for commit `fe1d34fb216a4a09cbb0bc897dfaeac91d808f5c`; Step 10 G2 PostgreSQL integration, Step 11 browser E2E and Step 12 live FastAPI/PostgreSQL E2E all succeeded for the event/industry scoring slice.

### Remaining gaps

- A203 still needs remaining non-relationship object family scoring coverage beyond entity/event/industry.
- A203 still depends on A202 for production-approved live relationship facts and on A209 for 4h/24h soak evidence.

## 2026-06-21 - T1301/A202 production owner sign-off contract slice

Status: CI VALIDATED; A202 STILL IN PROGRESS

### Scope

- Extended `scripts/publish_reviewed_relationship_facts.py` so fixture review and production owner sign-off are mutually exclusive clearance modes.
- Added `--allow-production-owner-signoff`; owner sign-off decision files now fail closed unless `review_context=production_owner_signoff_contract`, `production_owner_signoff=true`, and every approved decision carries `owner_actor`, `owner_role`, `authority_scope` and `signature`.
- Persisted owner sign-off metadata and `owner_signature_hash` into `data_snapshots.metadata`, `relationships.qualifiers`, `relationship_evidence.structured_fact` and `fact_versions.payload`.
- Added `tests/fixtures/golden_vertical_owner_signoff_decisions.json` as a contract fixture for signed owner approval semantics.
- Extended PostgreSQL integration assertions to prove the owner sign-off gate, snapshot metadata, relationship qualifiers, evidence payloads, fact-version payloads, review queue resolution and idempotency.

### Files changed

- `scripts/publish_reviewed_relationship_facts.py`
- `tests/integration/test_database_migrations.py`
- `tests/fixtures/golden_vertical_owner_signoff_decisions.json`
- `artifacts/tests/a202/t1301_curated_official_ingestion_contract.json`
- `data/acceptance_traceability.csv`
- `data/development_status_ledger.csv`
- `scripts/validate_v5_production_readiness_sync.py`
- `README.md`
- `DEVELOPMENT_STATUS.md`
- `docs/phase/V5_TASK_PACK_SYNCHRONIZATION.md`

### Acceptance mapping

- T1301 -> A202.
- A202 remains `IN_PROGRESS`, not `DONE`.
- This slice narrows the production-owner approval contract gap but does not close live/full-text ingestion, real operator-supplied owner approval, second-source closure, source health, retry or dead-letter coverage.

### Local validation

- `python3 -m json.tool tests/fixtures/golden_vertical_owner_signoff_decisions.json`: PASS.
- `python3 -m py_compile scripts/publish_reviewed_relationship_facts.py tests/integration/test_database_migrations.py`: PASS.
- `.venv/bin/ruff check scripts/publish_reviewed_relationship_facts.py tests/integration/test_database_migrations.py`: PASS.
- `.venv/bin/python -m pytest -q tests/unit/test_api_health.py tests/unit/test_scoring.py`: PASS, 27/27 with one existing Starlette/httpx deprecation warning.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/python -m pytest -q tests/integration/test_database_migrations.py`: SKIPPED locally because this host has no `.env`, `DATABASE_URL` or Docker runtime.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache make verify`: PASS after non-sandbox rerun; first sandbox attempt failed only at the Chromium browser benchmark with macOS MachPort permission denied.

### Remote CI validation

- GitHub Actions run `27880295243` / job `82506543351`: PASS for commit `6c6df28c48fbd7be4bdca9afecaef0c68f3b7aa9`.
- Step 10 G2 PostgreSQL integration, Step 11 browser E2E and Step 12 live FastAPI/PostgreSQL E2E all passed for the owner sign-off publication contract slice.

### Remaining gaps

- A202 still needs live/full-text official-source ingestion or an approved dry-run connector.
- A202 still needs an actual operator-supplied owner decision or second independent source closure before any real Golden Vertical fact is production-approved.
- Source health, retry and dead-letter behavior remain owned by T1304/A206 and long-duration proof by T1307/A209.

## 2026-06-21 - T1301/A202 official-source full-text dry-run and source-health slice

Status: LOCAL AND REMOTE CI VALIDATED; A202/A206 STILL IN PROGRESS

### Scope

- Added `scripts/fetch_official_source_full_text.py` as an idempotent dry-run connector for the NVIDIA official-source anchors.
- Added `tests/fixtures/official_source_full_text/nvidia_official_full_text_dry_run.json` as a deterministic parser fixture. The fixture is explicitly not live retrieval, not an official-page reproduction, and not legal or market clearance.
- The connector validates source URL agreement, capture status, minimum text length, and 100% expected-token coverage before writing database rows.
- The connector writes `raw_source_snapshots`, `source_documents`, `entity_resolution_candidates`, and context-only `ingestion_evidence_chain` rows under parser version `nvidia-official-fulltext-dry-run-v1`.
- Dry-run payloads preserve `source_health`, `retry_policy`, `attempts`, `live_retrieval=false`, and `release_clearance=false`.
- PostgreSQL integration now runs the dry-run connector twice and asserts idempotency, 4 raw snapshots, 4 evidence rows, 52 resolution candidates, 13 high-confidence/matched-research candidates, healthy coverage, and zero `relationship_fact_candidates` for the dry-run parser.

### Files changed

- `scripts/fetch_official_source_full_text.py`
- `tests/fixtures/official_source_full_text/nvidia_official_full_text_dry_run.json`
- `tests/integration/test_database_migrations.py`
- `Makefile`
- `artifacts/tests/a202/t1301_curated_official_ingestion_contract.json`
- `artifacts/tests/a202/t1301_official_full_text_dry_run_contract.json`
- `artifacts/tests/a206/t1304_scheduler_retry_dead_letter_contract.json`
- `data/acceptance_matrix.csv`
- `data/acceptance_traceability.csv`
- `data/development_status_ledger.csv`
- `scripts/validate_v5_production_readiness_sync.py`
- `README.md`
- `DEVELOPMENT_STATUS.md`
- `docs/phase/V5_TASK_PACK_SYNCHRONIZATION.md`

### Acceptance mapping

- T1301 -> A202.
- T1304 -> A206 for source-health/retry metadata only.
- A202 remains `IN_PROGRESS`: live official retrieval and production approval are still not complete.
- A206 remains `IN_PROGRESS`: dry-run source-health metadata is not a substitute for 4h/24h operator soak and live dead-letter proof.

### Local validation

- `python3 -m json.tool tests/fixtures/official_source_full_text/nvidia_official_full_text_dry_run.json`: PASS.
- `python3 -m json.tool artifacts/tests/a202/t1301_official_full_text_dry_run_contract.json`: PASS.
- `python3 -m json.tool artifacts/tests/a202/t1301_curated_official_ingestion_contract.json`: PASS.
- `python3 -m json.tool artifacts/tests/a206/t1304_scheduler_retry_dead_letter_contract.json`: PASS.
- `python3 -m py_compile scripts/fetch_official_source_full_text.py tests/integration/test_database_migrations.py`: PASS.
- `.venv/bin/ruff check scripts/fetch_official_source_full_text.py scripts/validate_v5_production_readiness_sync.py tests/integration/test_database_migrations.py`: PASS.
- `.venv/bin/python scripts/validate_v5_production_readiness_sync.py`: PASS.
- `.venv/bin/python scripts/validate_catalog_integrity.py`: PASS.
- `.venv/bin/python scripts/validate_contracts.py`: PASS.
- `.venv/bin/python -m pytest -q tests/unit/test_api_health.py tests/unit/test_scoring.py`: PASS, 27/27 with one existing Starlette/httpx deprecation warning.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/python -m pytest -q tests/integration/test_database_migrations.py`: SKIPPED locally because this host has no `.env` or `DATABASE_URL`.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache make verify`: PASS after non-sandbox rerun; first sandbox run failed only at Chromium browser benchmark with macOS MachPort permission denied. Unit tests: 31/31.

### Remote CI validation

- GitHub Actions run `27881176915` / job `82508895982` for commit `58eba46676c8d09af57e6a15d884144a6af1b47f`: FAIL in Step 10 `Verify G2 PostgreSQL integration`; PostgreSQL output was `(52, 13, 13, 4, 3)` for dry-run candidates while the test still expected `(52, 10, 10, 4, 3)`. The follow-up fix aligns the assertion and evidence artifact to the real database output.
- GitHub Actions run `27881361500` / job `82509391127` for commit `660465e9d5041c20ec667781e8d1b399c1ef638e`: PASS; Steps 7-12 all succeeded, including Step 10 `Verify G2 PostgreSQL integration`, Step 11 browser E2E and Step 12 live FastAPI/PostgreSQL E2E for the dry-run official-source full-text connector.

### Remaining gaps

- A202 still needs live official retrieval, or an approved operator-provided source capture process, before production use.
- A202 still needs an actual operator-supplied owner decision or second independent source closure before any real Golden Vertical fact is production-approved.
- A206/A209 still need 4h and 24h operator soak evidence for worker wake, retry, recovery, and dead-letter stability.

## 2026-06-21 - T1301/A202 operator-provided official source capture contract

Status: LOCAL AND REMOTE CI VALIDATED; A202 STILL IN PROGRESS

### Scope

- Added `scripts/load_operator_source_captures.py` as an idempotent operator-provided official-source capture loader for the NVIDIA Golden Vertical official anchor registry.
- Added `tests/fixtures/operator_source_captures/nvidia_operator_source_captures.json` as the deterministic contract fixture for operator capture provenance and hash validation.
- Added `infra/db/migrations/0011_operator_source_capture_constraints` to allow `operator_source_capture` raw snapshots and `operator_verified` review rows under an explicit rollback contract.
- The loader validates source URL agreement, `captured_by`, `captured_at`, `capture_method`, `approval_scope`, `operator_signature`, `source_text_sha256`, required usage attestations, minimum text length and 100% expected-token coverage before writing database rows.
- The loader writes `raw_source_snapshots`, `source_documents`, `entity_resolution_candidates` and context-only `ingestion_evidence_chain` rows under parser version `nvidia-operator-source-capture-v1`.
- Operator capture payloads preserve `operator_supplied_capture=true`, `live_retrieval=false`, `release_clearance=false` and `relationship_publication=false`.
- PostgreSQL integration now runs the operator loader twice and asserts idempotency, 2 raw snapshots, 2 evidence rows, 30 resolution candidates, 2 NVIDIA subject candidates, 2 TSMC candidates and zero `relationship_fact_candidates` for the operator parser.

### Parameters and thresholds

- `ingestion.operator_capture_min_text_chars`: 240.
- `ingestion.operator_capture_min_token_coverage_ratio`: 1.0.
- Required usage attestations: `official_source_observed`, `source_url_matches_anchor`, `no_paywall_or_login_bypass`, `copyright_excerpt_only_for_evidence`, `not_production_fact_approval`.
- `operator_supplied_capture`: true.
- `live_retrieval`: false.
- `release_clearance`: false.
- `relationship_publication`: false.

These are recorded in `artifacts/tests/a202/t1301_operator_source_capture_contract.json` instead of `data/parameter_catalog.csv` because the canonical parameter catalog is locked at 78 rows by `scripts/validate_catalog_integrity.py`.

### Files changed

- `scripts/load_operator_source_captures.py`
- `infra/db/migrations/0011_operator_source_capture_constraints/up.sql`
- `infra/db/migrations/0011_operator_source_capture_constraints/down.sql`
- `tests/fixtures/operator_source_captures/nvidia_operator_source_captures.json`
- `tests/integration/test_database_migrations.py`
- `Makefile`
- `scripts/validate_v5_production_readiness_sync.py`
- `artifacts/tests/a202/t1301_operator_source_capture_contract.json`
- `data/acceptance_traceability.csv`
- `data/development_status_ledger.csv`
- `README.md`
- `DEVELOPMENT_STATUS.md`
- `docs/phase/V5_TASK_PACK_SYNCHRONIZATION.md`
- `docs/phase/MVP_DEVELOPMENT_RECORD.md`

### Acceptance mapping

- T1301 -> A202.
- A202 remains `IN_PROGRESS`: this is an operator capture contract, not live retrieval, legal clearance, owner approval or second-source production closure.

### Local validation

- `python3 -m json.tool tests/fixtures/operator_source_captures/nvidia_operator_source_captures.json`: PASS.
- `python3 -m json.tool artifacts/tests/a202/t1301_operator_source_capture_contract.json`: PASS.
- `python3 -m py_compile scripts/load_operator_source_captures.py tests/integration/test_database_migrations.py`: PASS.
- `.venv/bin/ruff check scripts/load_operator_source_captures.py tests/integration/test_database_migrations.py scripts/validate_v5_production_readiness_sync.py`: PASS.
- `.venv/bin/python scripts/validate_v5_production_readiness_sync.py`: PASS.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache make verify`: PASS locally after non-sandbox Chromium permission rerun; 31 unit tests passed, typecheck passed and browser/scale/soak smoke passed.

### Remote validation

- GitHub Actions run `27882366565` / job `82512011341` on commit `bea28f893fd73af4c4e78c6c701365f6e95d9b51`: PASS.
- Step 10 `Verify G2 PostgreSQL integration`: PASS, proving `0011_operator_source_capture_constraints` accepts `operator_source_capture` and `operator_verified` rows.
- Step 11 `Verify G2 browser E2E`: PASS.
- Step 12 `Verify G2 live FastAPI PostgreSQL E2E`: PASS.

### Remaining gaps

- A202 still needs live official retrieval or real operator-supplied capture evidence outside the deterministic fixture.
- A202 still needs actual owner approval or second independent-source closure before any real Golden Vertical fact can be production-approved.
- This loader intentionally does not create `relationship_fact_candidates` or production `relationships`.
- A206/A209 still need 4h and 24h operator soak evidence for wake, retry, recovery and dead-letter stability.

## 2026-06-21 - T1302/A203 source-document and score-result scoring explain slice

Status: LOCAL AND REMOTE CI VALIDATED; A203 STILL IN PROGRESS

### Scope

- Extended `/v1/scoring/explain/{objectType}/{objectId}` to support `source_document` and `score_result` in addition to `entity`, `event`, `industry`, `relationship_fact_candidate` and `relationship`.
- Added `source_document_score_metrics` for source provenance health: source tier, provenance-field completeness, parser version, downstream evidence references, optional source-document fact version and active source state.
- Added `score_result_score_metrics` for score-result health: stored score value fields, contribution rows, missing-input array contract, completed scoring run and active analysis context.
- Added repository SQL that explains source documents from `sources`, `source_documents`, `raw_source_snapshots`, relationship/event/candidate/ingestion/fact-version evidence references, optional `fact_versions` and current production context.
- Added repository SQL that explains score results from `score_results`, `scoring_runs`, model/profile versions and `active_analysis_contexts`.
- Expanded the OpenAPI `objectType` path enum and `ScoreExplanation.object_type` schema enum to the seven supported MVP scoring explain object types.
- Extended unit tests and the PostgreSQL integration contract assertions for source-document and score-result scoring explanations.

### Parameters and formulas

- `source_document.source_tier_max`: 5.
- `source_document.minimum_downstream_evidence`: 1.
- `source_document.provenance_field_count`: 6 fields: source_id, url, content_hash, observed_at, retrieved_at, publisher/title.
- `source_document` formula: source tier 20 + provenance fields 20 + parser version 15 + downstream evidence 25 + source-document fact version 10 + active source 10; inactive sources apply a 0.75 adjusted-score multiplier.
- `score_result.required_value_fields`: 4 fields: raw_score, evidence_quality, adjusted_score, coverage.
- `score_result` formula: stored metric values 35 + contribution records 20 + missing-inputs array contract 10 + completed scoring run 25 + active analysis context 10; incomplete scoring runs apply a 0.70 adjusted-score multiplier.
- These slice-specific thresholds are recorded in `artifacts/tests/a203/t1302_production_api_graph_scoring_contract.json`. The canonical `data/parameter_catalog.csv`, `data/formula_registry.csv` and `data/threshold_registry.csv` remain at validator-locked row counts until the broader model-governance task explicitly expands the catalogs.

### Files changed

- `apps/api/app/scoring.py`
- `apps/api/app/domain_repository.py`
- `specs/api_contract.yaml`
- `tests/unit/test_scoring.py`
- `tests/integration/test_database_migrations.py`
- `artifacts/tests/a203/t1302_production_api_graph_scoring_contract.json`
- `data/acceptance_traceability.csv`
- `data/development_status_ledger.csv`
- `README.md`
- `DEVELOPMENT_STATUS.md`
- `docs/phase/V5_TASK_PACK_SYNCHRONIZATION.md`
- `docs/phase/MVP_DEVELOPMENT_RECORD.md`

### Acceptance mapping

- T1302 -> A203.
- A203 remains `IN_PROGRESS`, not `DONE`.
- This slice closes the scoring-explain API enum coverage gap for `source_document` and `score_result`.

### Local validation

- `python3 -m py_compile apps/api/app/scoring.py apps/api/app/domain_repository.py tests/unit/test_scoring.py tests/integration/test_database_migrations.py`: PASS.
- `.venv/bin/ruff check apps/api/app/scoring.py apps/api/app/domain_repository.py tests/unit/test_scoring.py tests/integration/test_database_migrations.py`: PASS.
- `.venv/bin/python -m pytest -q tests/unit/test_scoring.py`: PASS, 14/14.
- `.venv/bin/python scripts/validate_contracts.py`: PASS.
- `.venv/bin/python scripts/validate_v5_production_readiness_sync.py`: PASS.
- `.venv/bin/python -m pytest -q tests/integration/test_database_migrations.py`: SKIPPED locally because this host has no `.env` or `DATABASE_URL`.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache make verify`: PASS after non-sandbox Chromium permission rerun; 35 unit tests passed, typecheck passed, release checksum validation passed, browser scale smoke passed and soak smoke passed.

### Remote CI validation

- GitHub Actions run `27883167817` / job `82514084247` on commit `f83389577d79c10b8c5184f858d318d52ffac9ae`: PASS.
- Step 10 `Verify G2 PostgreSQL integration`: PASS, proving source_document and score_result scoring explanation SQL against the real migration/seed path.
- Step 11 `Verify G2 browser E2E`: PASS.
- Step 12 `Verify G2 live FastAPI PostgreSQL E2E`: PASS.

### Remaining gaps

- At this point, `score_recompute` still persisted `score_results` only for `relationship_fact_candidate` objects. The follow-on slice below addresses MVP object-family recompute persistence.
- A203 still depends on A202 for production-approved live relationship facts and on A209 for 4h/24h soak evidence.

## 2026-06-21 - T1302/T1303/T1304 full MVP score-result recompute persistence slice

Status: LOCAL AND REMOTE CI VALIDATED; A203/A204-A206 STILL IN PROGRESS

### Scope

- Extended `scripts/job_scheduler.py` so `score_recompute` writes one active scoring run covering the MVP object families:
  - `relationship_fact_candidate`
  - `relationship`
  - `entity`
  - `event`
  - `industry`
  - `source_document`
- Reused existing scoring formulas from `apps/api/app/scoring.py` rather than introducing a parallel worker-only formula.
- Added object-family collectors for the minimum fields needed to persist `raw_score`, `evidence_quality`, `adjusted_score`, `coverage`, `contributions` and `missing_inputs`.
- Added `score_result_object_types` and `score_result_object_counts` to scoring-run parameters, active-analysis-context metadata, outbox payload, operation-log diff and worker result.
- Extended the PostgreSQL integration contract so the recompute flow verifies all six object families have non-null metric values in `score_results`.

### Acceptance mapping

- T1302 -> A203 for production scoring service persistence.
- T1303 -> A204/A205 for active scoring run activation, refresh token advance and atomic score snapshot context.
- T1304 -> A206 for worker execution, outbox payload and idempotent background-job contract.
- These IDs remain `IN_PROGRESS`, not `DONE`, until downstream production release gates are current.

### Local validation

- `python3 -m py_compile scripts/job_scheduler.py tests/integration/test_database_migrations.py`: PASS.
- `.venv/bin/ruff check scripts/job_scheduler.py tests/integration/test_database_migrations.py`: PASS.

### Remote CI validation

- GitHub Actions run `27883953630` / job `82516108840` on commit `f2bf996c1ea57f652f6d4d5da517f1f4b501e6ad`: PASS.
- Step 10 `Verify G2 PostgreSQL integration`: PASS, proving the recompute flow writes `score_results` for relationship_fact_candidate, relationship, entity, event, industry and source_document object families with non-null metric values.
- Step 11 `Verify G2 browser E2E`: PASS.
- Step 12 `Verify G2 live FastAPI PostgreSQL E2E`: PASS.

### Remaining gaps

- A203 still depends on production-approved relationship edges and current downstream release gates.
- At this score-result recompute slice point, A204/A205 still needed online model editing and long-duration refresh stability. The follow-on online draft editing slice below addresses the online-editing portion.
- A206/A209 still need 4h and 24h operator soak evidence for worker wake, retry, recovery and dead-letter stability.

## 2026-06-22 - T1302/A203 theme and facility scoring explain slice

Status: LOCAL VALIDATED; REMOTE CI PENDING; A203 STILL IN PROGRESS

### Scope

- Extended `GET /v1/scoring/explain/{objectType}/{objectId}` to support `theme` and `facility` as first-class scoring object types.
- The implementation reuses the entity coverage scoring formula, but it fail-closes unless `entities.entity_type` matches the requested object type.
- The response preserves the `entity` subobject while returning `object_type=theme` or `object_type=facility`, so Watchlist, Strategic Signals and Supply Chain facility flows can request score explanations without pretending these objects are generic legal entities.
- Expanded the OpenAPI scoring `objectType` enum and `ScoreExplanation.object_type` enum to include `theme` and `facility`.
- Extended `score_recompute` so the active scoring run now writes `score_results` for eight MVP object families: `relationship_fact_candidate`, `relationship`, `entity`, `theme`, `facility`, `event`, `industry` and `source_document`.
- Added PostgreSQL integration assertions for theme scoring, facility scoring, mismatched facility ID 404, and the expanded score-result object-family counts.

### Acceptance mapping

- T1302 -> A203.
- A203 remains `IN_PROGRESS`, not `DONE`.
- This slice reduces the remaining non-relationship object-family scoring gap for `theme` and `facility`; it does not publish production-approved relationship edges.

### Local validation

- `python3 -m py_compile apps/api/app/domain_repository.py scripts/job_scheduler.py tests/integration/test_database_migrations.py`: PASS.
- `.venv/bin/ruff check apps/api/app/domain_repository.py scripts/job_scheduler.py tests/integration/test_database_migrations.py`: PASS.
- `.venv/bin/python scripts/validate_contracts.py`: PASS.
- `.venv/bin/pytest tests/unit/test_scoring.py -q -p no:cacheprovider`: PASS, 14/14.
- `.venv/bin/pytest tests/integration/test_database_migrations.py -q -p no:cacheprovider`: SKIPPED locally because this host has no `.env` or `DATABASE_URL`.

### Remaining gaps

- Remote GitHub Actions still must prove the new theme/facility integration assertions under PostgreSQL, browser E2E and live FastAPI/PostgreSQL E2E.
- A203 still depends on A202 for production-approved live relationship facts and on A209 for long-duration stability evidence; A209 continues as a background gate and does not block this bounded feature work.

## 2026-06-21 - T1303/A204-A205 model-center online draft editing slice

Status: LOCAL AND REMOTE CI VALIDATED; A204-A205 STILL IN PROGRESS

### Scope

- Implemented `POST /v1/scoring/profiles` as the API-first model-center online editing path.
- The endpoint creates an inactive draft `scoring_profile_versions` row from a base profile, validates exact weight keys, per-weight range `0..0.7`, total weight `1.0 +/- 0.001`, optional half-life key coverage and allowed missing-value policy.
- The draft creation transaction preserves the current active analysis context and writes `create_scoring_profile_version` into `operation_logs`.
- Updated the frontend model-center preview button so it creates a server-side draft and sets that draft as the activation target; when no API base exists it keeps the explicit local preview fallback.
- Extended the A204/A205 mock E2E to cover draft creation -> activation -> stale refresh -> score recompute enqueue -> rollback.
- Extended the PostgreSQL integration flow so the activation target is created through the public API instead of by direct SQL insertion, and invalid draft weights fail closed with HTTP 422.
- Added unit regressions that keep draft `weights` required at the API schema boundary and reject boolean `half_lives_days` values before they can masquerade as integers.

### Acceptance mapping

- T1303 -> A204 for model config version creation, operation log and transactional activation target handoff.
- T1303 -> A205 for preserving active context until explicit activation and then refreshing global visible state after activation.
- A204/A205 remain `IN_PROGRESS`, not `DONE`, until process-manager wake and long-duration refresh stability evidence are current.

### Local validation

- `python3 -m py_compile apps/api/app/domain.py apps/api/app/domain_repository.py tests/integration/test_database_migrations.py`: PASS.
- `.venv/bin/ruff check apps/api/app/domain.py apps/api/app/domain_repository.py tests/integration/test_database_migrations.py`: PASS.
- `.venv/bin/python scripts/validate_contracts.py`: PASS.
- `npx --yes pnpm@11.8.0 --filter @eei/web typecheck`: PASS after rerun with network access because sandbox DNS blocked npx registry resolution.
- `.venv/bin/python -m pytest -q tests/unit/test_api_health.py tests/unit/test_scale_benchmarks.py tests/unit/test_scoring.py`: PASS with 37/37.
- `.venv/bin/python -m pytest -q tests/integration/test_database_migrations.py`: SKIPPED locally because this host has no `.env`/`DATABASE_URL`; remote GitHub Actions must provide PostgreSQL proof.
- `npx --yes pnpm@11.8.0 --filter @eei/web exec playwright test --config=../../playwright.config.ts tests/e2e/state-contract.spec.ts -g "A204 and A205" --workers=1`: PASS with 1/1.

### Remote CI validation

- GitHub Actions run `27885349105` / job `82519730263` on commit `0e5fe53e`: PASS.
- Step 10 `Verify G2 PostgreSQL integration`: PASS, proving public `POST /v1/scoring/profiles` draft creation, invalid-weight fail-closed behavior, transactional activation, stale refresh, recompute enqueue and rollback against migrations/seeds.
- Step 11 `Verify G2 browser E2E`: PASS.
- Step 12 `Verify G2 live FastAPI PostgreSQL E2E`: PASS.

### Remaining gaps

- A204/A205 still need process-manager wake and 4h/24h refresh stability evidence before closure.
- A206/A209 still need 4h and 24h operator soak evidence for worker wake, retry, recovery and dead-letter stability.

## 2026-06-21 - T1306/A208 scale benchmark projection hardening slice

Status: LOCAL AND REMOTE CI VALIDATED; A208 REMAINS CLOSED AFTER REVALIDATION

### Scope

- Optimized `scripts/run_scale_benchmarks.py` API projection so the benchmark keeps scalar rank fields in the bounded top-k heap and only instantiates `SyntheticEdge` objects for returned visible edges.
- Preserved the existing deterministic family filter, rank key, visible edge limit, node counting, layout, render, memory, frame and long-task output contracts.
- Regenerated the formal A208 benchmark artifacts:
  - `artifacts/tests/a208/t1306_scale_benchmark_smoke.json`
  - `artifacts/tests/a208/t1306_browser_runtime_benchmark.json`
  - `artifacts/tests/a208/t1306_scale_benchmark_operator_contract.json`
- The regenerated operator artifact reports 10k, 100k and 1m relationship measurements with full A208 coverage and zero remaining A208 items.

### Acceptance mapping

- T1306 -> A208.
- This is a performance hardening and evidence refresh for an already closed A208 scope; it does not close A209 soak or any v0.1 production blocker outside T1306.

### Local validation

- `python3 -m py_compile scripts/run_scale_benchmarks.py tests/unit/test_scale_benchmarks.py`: PASS.
- `.venv/bin/ruff check scripts/run_scale_benchmarks.py tests/unit/test_scale_benchmarks.py`: PASS.
- `.venv/bin/python -m pytest -q tests/unit/test_scale_benchmarks.py`: PASS with 4/4.
- `.venv/bin/python scripts/run_scale_benchmarks.py --scales 1000000 --iterations 1 --mode operator_full --output /tmp/eei-scale-benchmark-1m-after-opt.json --fail-on-budget --quiet`: PASS; 1m total p95 about 703 ms versus the 10000 ms budget in this local run.
- `node scripts/run_browser_scale_benchmarks.mjs --scales 10000,100000,1000000 --iterations 1 --output artifacts/tests/a208/t1306_browser_runtime_benchmark.json --fail-on-budget --quiet`: PASS.
- `.venv/bin/python scripts/run_scale_benchmarks.py --scales 1000 --iterations 2 --mode ci_smoke --output artifacts/tests/a208/t1306_scale_benchmark_smoke.json --fail-on-budget --quiet`: PASS.
- `.venv/bin/python scripts/run_scale_benchmarks.py --scales 10000,100000,1000000 --iterations 1 --mode operator_full --output artifacts/tests/a208/t1306_scale_benchmark_operator_contract.json --browser-runtime-artifact artifacts/tests/a208/t1306_browser_runtime_benchmark.json --fail-on-budget --require-full-targets --quiet`: PASS.

### Remote CI validation

- GitHub Actions run `27885349105` / job `82519730263` on commit `0e5fe53e`: PASS.
- The `make verify` workflow includes A208 scale benchmark smoke, Chromium browser runtime and merged 10k/100k/1m operator_full benchmark.
- Step 10 `Verify G2 PostgreSQL integration`: PASS.
- Step 11 `Verify G2 browser E2E`: PASS.
- Step 12 `Verify G2 live FastAPI PostgreSQL E2E`: PASS.

### Remaining gaps

- A209 4h/24h soak remains open and is intentionally not affected by this A208 hardening slice.

## 2026-06-21 - T1304/T1307 A206/A209 worker supervisor CLI wake contract

Status: LOCAL AND REMOTE CI VALIDATED; A206/A209 STILL IN PROGRESS

### Scope

- Extended the PostgreSQL integration contract to exercise the production worker CLI entry point:
  - `python -m apps.worker.app.main supervise`
  - `--max-cycles 2`
  - `--stop-when-idle`
  - `--job-type noop`
  - `--event-type a206.worker.cli.wake`
- The new contract enqueues a real `background_jobs` row and a real `transactional_outbox` event, then verifies the CLI supervisor wakes, processes one job, dispatches one outbox event, stops on an idle cycle and emits the `eei-worker-supervision-summary-v1` JSON contract.
- The test also verifies final PostgreSQL state:
  - the job is `succeeded`
  - the noop handler result carries `A206`
  - the outbox event is `dispatched`
  - the dispatch result carries `outbox-dispatch-v1` and `A206/A209`

### Acceptance mapping

- T1304 -> A206 for production CLI wake, job execution, outbox dispatch and process entry point behavior.
- T1307 -> A209 only for the worker-wake portion of soak readiness.
- A206 and A209 remain `IN_PROGRESS`, not `DONE`, until 4h and 24h operator soak evidence is attached.

### Local validation

- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/ruff check tests/integration/test_database_migrations.py`: PASS.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/python -m pytest -q tests/integration/test_database_migrations.py`: SKIPPED locally because this host has no `.env`/`DATABASE_URL`; remote GitHub Actions must provide PostgreSQL proof.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache make verify`: PASS after rerun with elevated permissions because local Chromium browser benchmarks require macOS Mach port access outside the sandbox.

### Remote CI validation

- GitHub Actions run `27886021414` / job `82521454825` on commit `ea111c9`: PASS.
- Step 10 `Verify G2 PostgreSQL integration`: PASS, proving `python -m apps.worker.app.main supervise` wakes through the production CLI, processes a real PostgreSQL `background_jobs` row, dispatches a real `transactional_outbox` event and stops on an idle cycle.
- Step 11 `Verify G2 browser E2E`: PASS.
- Step 12 `Verify G2 live FastAPI PostgreSQL E2E`: PASS.

### Remaining gaps

- 4h and 24h soak are still not executed.
- Docker is still unavailable on the current host, so local Docker Compose worker soak cannot be completed here.

## 2026-06-21 - T1307/A209 resumable operator soak runner readiness

Status: LOCAL AND REMOTE CI VALIDATED; A209 STILL IN PROGRESS

### Scope

- Added `scripts/run_operator_soak.mjs` as the operator-facing wrapper around `scripts/run_soak_smoke.mjs`.
- The runner supports:
  - windowed execution using `soak.operator_window_seconds` from `data/parameter_catalog.csv`
  - checkpoint JSONL audit output
  - `--resume` from successful checkpoint windows
  - `--duration-hours 4` and `--duration-hours 24` operator commands
  - `--fail-on-budget` propagation from the child browser+worker soak harness
  - explicit Docker Compose worker binding reference through the child A206 artifact
- Added `make validate-operator-soak-runner` and wired it into `make verify`.
- Added A209 readiness evidence:
  - `artifacts/tests/a209/t1307_operator_soak_readiness.json`
  - `artifacts/tests/a209/t1307_operator_soak_readiness.checkpoints.jsonl`
- Added governed parameter `soak.operator_window_seconds=300`.

### Acceptance mapping

- T1307 -> A209 for operator runner readiness, checkpoint/resume contract and command surface.
- T1304 -> A206 indirectly through the Docker Compose worker binding referenced by the child soak harness.
- A209 remains `IN_PROGRESS`: 3-second readiness and CI smoke are not substitutes for committed 4h and 24h operator soak artifacts.

### Local validation

- Local sandboxed `node scripts/run_operator_soak.mjs --mode ci_smoke --duration-seconds 3 --window-seconds 3 --output artifacts/tests/a209/t1307_operator_soak_readiness.json --checkpoint artifacts/tests/a209/t1307_operator_soak_readiness.checkpoints.jsonl --fail-on-budget --quiet`: expected FAIL at Chromium launch with macOS `bootstrap_check_in ... Permission denied`.
- Local elevated rerun of the same command: PASS; output status `PASS`, `a209_release_gate.status=PARTIAL_UNTIL_4H_24H_OPERATOR_EVIDENCE`, `checkpoint_resume_supported=true`, `worker_supervisor_binding_available=true`, one successful 3-second window.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/uv run python scripts/generate_governance_pdf.py`: BLOCKED in the current environment because Python `playwright.sync_api` is not installed; `scripts/generate_governance_pdf.py` now says 79 parameters, but the existing PDF binary was not regenerated in this slice.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache make verify`: PASS; includes governance count 17/11/11/79/17, v5 sync, clean-room/release validation, scale/browser/soak smoke, operator soak runner, secret scan, UI copy lint, ruff, web typecheck and unit tests 37/37.

### Remote CI validation

- GitHub Actions run `27886864382` / job `82523564731` on commit `954b534`: PASS.
- Step 10 `Verify G2 PostgreSQL integration`: PASS.
- Step 11 `Verify G2 browser E2E`: PASS.
- Step 12 `Verify G2 live FastAPI PostgreSQL E2E`: PASS.
- This validates the committed runner readiness and CI-safe operator soak command surface only; it does not close the 4h/24h soak requirement.

### Operator commands

- 4h: `node scripts/run_operator_soak.mjs --mode operator_4h --duration-hours 4 --window-seconds 300 --output artifacts/tests/a209/t1307_operator_soak_4h.json --checkpoint artifacts/tests/a209/t1307_operator_soak_4h.checkpoints.jsonl --fail-on-budget`
- 24h: `node scripts/run_operator_soak.mjs --mode operator_24h --duration-hours 24 --window-seconds 300 --output artifacts/tests/a209/t1307_operator_soak_24h.json --checkpoint artifacts/tests/a209/t1307_operator_soak_24h.checkpoints.jsonl --fail-on-budget`
- Resume: rerun the same command with `--resume` and the same checkpoint path.

### Remaining gaps

- 4h and 24h operator soak runs are still not executed.
- A209 cannot close until both long-duration JSON and checkpoint JSONL artifacts are committed, release evidence is regenerated and CI validates the committed evidence.
- Local host still lacks Docker, so this slice proves runner readiness and child harness behavior, not a full Docker Compose operator soak.

## 2026-06-21 - T1301/A202 second independent official-source closure

Status: LOCAL STATIC VALIDATED; REMOTE POSTGRESQL CI PENDING; A202 STILL IN PROGRESS

### Scope

- Added two secondary official-source anchors to `data/golden_vertical_fact_candidates.json`:
  - `GV-SNAPSHOT-003`: TSMC Press Center official NVIDIA/TSMC manufacturing relationship support.
  - `GV-SNAPSHOT-004`: TSMC Press Center official ASML/TSMC lithography technology relationship support.
- Extended `scripts/load_curated_ingestion_anchors.py` so each relationship candidate may carry `supporting_source_anchor_ids`.
- The loader now validates that `independent_source_count` equals the de-duplicated source-anchor count and writes one `relationship_fact_candidate_evidence` row per official source.
- Updated `GV-FACT-001` and `GV-FACT-002` to `independent_source_count=2`, `source_threshold_met=true`, `publication_status=ready_for_review` and database-valid `review_status=machine_verified`.
- Updated fixture and owner-signoff decision files so source-threshold override is no longer used for these two candidates.

### Acceptance mapping

- T1301 -> A202 for real-data evidence-chain strengthening, entity-resolution path preservation and second-source threshold closure.
- T1302 -> A203 indirectly through score explanation semantics for relationship_fact_candidate evidence quality.
- A202 remains `IN_PROGRESS`: this slice does not prove live network retrieval, real operator production-owner decision, legal clearance or full production approval.

### Model, formulas and thresholds

- No scoring formula changed.
- Existing candidate threshold remains `minimum_independent_sources=2`.
- Candidate evidence quality now reaches 100 for the two Golden Vertical candidates because `independent_source_count=2` meets the threshold.
- Missing inputs remain `human_review_verification` and `published_relationship_version` until explicit review/publication occurs.

### Local validation

- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/ruff check scripts/load_curated_ingestion_anchors.py scripts/check_database_schema.py tests/integration/test_database_migrations.py`: PASS.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/uv run pytest tests/unit`: PASS; 37 passed, 1 Starlette/httpx deprecation warning.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/uv run python scripts/validate_task_pack.py`: PASS.
- Sandboxed `npx --yes pnpm@11.8.0 --filter @eei/web typecheck`: BLOCKED by DNS access to npm registry.
- Elevated `npx --yes pnpm@11.8.0 --filter @eei/web typecheck`: BLOCKED by Codex usage-limit escalation rejection, not by project code.
- `NEXT_TELEMETRY_DISABLED=1 ./node_modules/.bin/next typegen` in `apps/web`: PASS.
- `./node_modules/.bin/tsc --noEmit` in `apps/web`: PASS.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/uv run pytest -q tests/integration/test_database_migrations.py`: SKIPPED locally because this host has no `.env`/`DATABASE_URL`; remote CI remains required for PostgreSQL proof.
- Local `make verify` subset through governance, contracts, release artifacts, secret scan, copy lint, ruff and unit tests: PASS for runnable non-browser targets.
- Local browser scale/soak targets: BLOCKED by macOS Playwright MachPort sandbox permission; elevated reruns were blocked by Codex usage-limit escalation rejection. Remote CI remains required for browser-scale and soak smoke proof.

### Source notes

- The secondary sources are official publisher pages and are used as structured metadata and short support summaries only.
- This slice avoids copying long source text into the repo.

### Remaining gaps

- Remote PostgreSQL CI has not yet validated the new multi-source candidate loader.
- Live official retrieval is still not implemented as a production network connector.
- Real operator-supplied owner decision and formal legal/market clearance remain outside this slice.

### Rollback

- Revert `data/golden_vertical_fact_candidates.json`, `scripts/load_curated_ingestion_anchors.py`, the updated fixtures and test assertions.
- Regenerate clean-room/release artifacts.
- Rerun `make verify` and remote CI.

## 2026-06-21 - T1309/A210 brand-clearance fail-closed preflight

Status: LOCAL VALIDATED; FORMAL LEGAL/MARKET CLEARANCE PENDING; A210 STILL IN PROGRESS

### Scope

- Added `scripts/validate_brand_clearance.py` with `generate` and `validate` commands.
- Added `artifacts/tests/a210/t1309_brand_clearance_preflight_contract.json`.
- The preflight verifies:
  - system name remains `商域图谱` / `Enterprise Ecosystem Intelligence` / `EEI`;
  - `BRAND-G1` remains the public-launch release gate;
  - public disclosure status remains `not_cleared_for_public_brand_launch`;
  - forbidden active names in `config/brand_policy.yaml` are covered by `data/brand_name_conflict_register.csv`;
  - public domain registration, app store publication, public SaaS launch, trademark filing and paid public marketing remain blocked unless formal clearance or a signed risk waiver exists.
- Wired `validate-brand-clearance` into `Makefile verify` and added the script to ruff lint coverage.

### Acceptance mapping

- T1309 -> A210.
- A210 moves from `NOT_STARTED` to `IN_PROGRESS` because the repository now has a verifiable fail-closed preflight gate.
- A210 remains open: this slice does not provide legal counsel sign-off, trademark availability, domain/social/app-store/package search evidence, market clearance, or a signed risk waiver.

### Model, formulas and thresholds

- No scoring model or graph formula changed.
- Existing parameter `brand.clearance_required=true` remains active.
- The gate is binary and fail-closed: `public_release_allowed=false` until formal legal/market clearance or signed risk waiver is attached.

### Local validation

- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/uv run python scripts/validate_brand_clearance.py generate`: PASS.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/uv run python scripts/validate_brand_clearance.py validate`: PASS.

### Remaining gaps

- No formal legal opinion is attached.
- No current CN/US/EU/UK/AU trademark knockout evidence is attached.
- No current domain, social handle, app store, GitHub/npm/PyPI or company-name search evidence is attached.
- No legal counsel sign-off or repository-owner risk waiver is attached.

### Rollback

- Revert `scripts/validate_brand_clearance.py`, `artifacts/tests/a210/t1309_brand_clearance_preflight_contract.json`, status CSV changes and Makefile wiring.
- Regenerate clean-room/release artifacts.
- Rerun governance, brand-clearance and release validations.

## 2026-06-21 - T1301/A202 database review-status CI repair

Status: LOCAL STATIC VALIDATED; REMOTE POSTGRESQL CI PENDING

### Scope

- GitHub Actions run `27890945803` failed at Step 10 `Verify G2 PostgreSQL integration` after static, contract, lint, typecheck and unit checks passed.
- First static diagnosis found `ingestion_evidence_chain.review_status` is constrained to `unreviewed`, `machine_verified`, `human_verified` or `disputed`.
- GitHub Actions run `27891135295` then failed again at Step 10 after Step 7 and Step 9 passed, exposing the same semantic mismatch for `relationship_fact_candidates.review_status`.
- `ready_for_review` is now treated strictly as `publication_status`, while database `review_status` remains `machine_verified` until human review publishes the candidate.
- Added `database_review_status()` in `scripts/load_curated_ingestion_anchors.py` so candidate and evidence-chain rows stay inside the PostgreSQL review-status contract.
- Updated A202 integration, schema-check and E2E fixture assertions to expect `publication_status=ready_for_review` plus `review_status=machine_verified`.

### Acceptance mapping

- T1301 -> A202.
- The relationship fact candidate remains publication-gated via `publication_status=ready_for_review`; its database review state is normalized to `machine_verified`.
- A202 remains `IN_PROGRESS` until remote PostgreSQL CI passes and live retrieval / owner approval / release clearance are complete.

### Local validation

- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/ruff check scripts/load_curated_ingestion_anchors.py tests/integration/test_database_migrations.py scripts/check_database_schema.py scripts/validate_brand_clearance.py scripts/validate_v5_production_readiness_sync.py`: PASS.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/uv run python scripts/validate_task_pack.py`: PASS.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/uv run python scripts/validate_v5_production_readiness_sync.py`: PASS.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/uv run python scripts/validate_brand_clearance.py validate`: PASS.
- Local PostgreSQL integration remains unavailable because this host has no Docker/PostgreSQL; remote CI rerun remains required.

### Follow-up validation after second Step 10 failure

- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/ruff check scripts/load_curated_ingestion_anchors.py tests/integration/test_database_migrations.py scripts/check_database_schema.py scripts/validate_v5_production_readiness_sync.py scripts/validate_brand_clearance.py`: PASS.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/uv run python scripts/validate_task_pack.py`: PASS.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/uv run python scripts/validate_v5_production_readiness_sync.py`: PASS.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/uv run python scripts/validate_brand_clearance.py validate`: PASS.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/uv run python -m json.tool data/golden_vertical_fact_candidates.json`: PASS.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/uv run pytest tests/unit -q`: PASS; 37 passed, 1 Starlette/httpx deprecation warning.
- `NEXT_TELEMETRY_DISABLED=1 ./node_modules/.bin/next typegen` in `apps/web`: PASS.
- `./node_modules/.bin/tsc --noEmit` in `apps/web`: PASS.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/uv run python scripts/manage_clean_room_release.py generate`: PASS; authoritative package SHA is recorded in `artifacts/tests/a200/t1215_clean_room_release.json`.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/uv run python scripts/manage_release_artifacts.py generate`: PASS.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/uv run python scripts/manage_clean_room_release.py validate`: PASS.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/uv run python scripts/manage_release_artifacts.py validate`: PASS with `remote_status=PENDING`.
- `shasum -a 256 -c CHECKSUMS.sha256`: PASS.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache PNPM=./node_modules/.bin/pnpm make verify`: LOCAL ENV BLOCKED at `validate-scale-browser-benchmark` because Chromium cannot register MachPort inside the macOS sandbox.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache PNPM=./node_modules/.bin/pnpm make secret-scan copy-lint lint typecheck test`: command selection failure at `typecheck` because that root-relative PNPM path does not exist; preceding secret scan, copy lint and full ruff passed.
- Local Docker/PostgreSQL is still unavailable, so Step 10 proof must come from GitHub Actions.

### Rollback

- Revert the database status mapper, A202 fixture data, schema/integration/E2E assertions and rerun G2 PostgreSQL integration.

## 2026-06-21 - T1301/A202 live E2E publication-status contract repair

Status: LOCAL AND REMOTE CI VALIDATED; A202 STILL IN PROGRESS

### Scope

- GitHub Actions run `27891379096` for commit `9fbbb87` passed Step 7 static/contract/lint/typecheck/unit, Step 8 PostgreSQL preparation, Step 9 G2 static/contract/lint/typecheck/unit, Step 10 G2 PostgreSQL integration and Step 11 G2 browser E2E.
- The same run failed only at Step 12 live FastAPI/PostgreSQL E2E.
- Static diagnosis found `tests/e2e/saved-view-live.spec.ts` still expected the production score candidate text to include the older `candidate` publication state.
- A202 second-source closure intentionally moved Golden Vertical candidates to `publication_status=ready_for_review` while keeping graph-edge publication blocked.
- Updated the live E2E assertion to expect `ready_for_review`.

### Acceptance mapping

- T1301 -> A202.
- T1308 -> A211 only as a live production-route consumer of the A202 candidate status.
- A202 remains `IN_PROGRESS`: this repair does not publish candidate facts, perform live official retrieval, attach legal clearance or complete production owner sign-off.

### Validation

- `./node_modules/.bin/tsc --noEmit` in `apps/web`: PASS.
- `NEXT_TELEMETRY_DISABLED=1 ./node_modules/.bin/next typegen` in `apps/web`: PASS.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/uv run python scripts/validate_v5_production_readiness_sync.py`: PASS.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/uv run python scripts/manage_clean_room_release.py generate`: PASS.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/uv run python scripts/manage_release_artifacts.py generate`: PASS.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/uv run python scripts/manage_clean_room_release.py validate`: PASS.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/uv run python scripts/manage_release_artifacts.py validate`: PASS.
- `shasum -a 256 -c CHECKSUMS.sha256`: PASS.
- GitHub Actions EEI validation run `27891576364` / job `82535792245`: PASS; Step 10 G2 PostgreSQL integration, Step 11 browser E2E and Step 12 live FastAPI PostgreSQL E2E all succeeded.
- GitHub Actions Project Governance run `27891576355`: PASS.

### Rollback

- Revert `tests/e2e/saved-view-live.spec.ts` expectation and rerun live E2E.

## 2026-06-21 - T1307/A209 fail-closed long-duration soak evidence validator

Status: LOCAL AND REMOTE CI VALIDATED; A209 STILL IN PROGRESS

### Scope

- Added `scripts/validate_operator_soak_evidence.py` as an independent validator for future committed 4h and 24h operator soak artifacts.
- The validator checks both summary JSON and checkpoint JSONL for `operator_4h` and `operator_24h`, required target durations, window pass status, worker job completion, browser heap/DOM budgets, worker event-loop lag budget, Docker Compose worker binding and release-gate semantics.
- Generated `artifacts/tests/a209/t1307_operator_soak_evidence_validation.json` with status `MISSING_OPERATOR_EVIDENCE`, which is the expected current state because the actual 4h and 24h artifacts do not exist.
- Wired `validate-operator-soak-evidence` into `make verify` and added `generate-operator-soak-evidence-artifact`.
- Updated T1307/A209 traceability, v5 readiness sync and development status ledger.

### Acceptance mapping

- T1307 -> A209.
- This is a control-plane hardening slice only: it prevents false positive A209 release evidence but does not run the missing 4h/24h soaks.
- A209 remains `IN_PROGRESS`; `MISSING_OPERATOR_EVIDENCE` and 3-second readiness are not substitutes for long-duration soak evidence.

### Validation

- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/uv run ruff check scripts/validate_operator_soak_evidence.py tests/unit/test_operator_soak_evidence.py scripts/validate_v5_production_readiness_sync.py`: PASS.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/uv run pytest tests/unit/test_operator_soak_evidence.py -q`: PASS; 3 passed.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/uv run python scripts/validate_operator_soak_evidence.py validate --quiet`: PASS; status remains `MISSING_OPERATOR_EVIDENCE`.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/uv run python scripts/validate_operator_soak_evidence.py validate --require-release-ready --quiet`: EXPECTED FAIL; exits non-zero because 4h/24h artifacts are absent.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/uv run python scripts/validate_v5_production_readiness_sync.py`: PASS; implemented tasks 4, partial tasks 6, not-done tasks 6.
- GitHub Actions EEI validation run `27891998013` / job `82536980138`: PASS; Step 7 static/contract/lint/typecheck/unit, Step 8 PostgreSQL preparation, Step 9 G2 static/contract/lint/typecheck/unit, Step 10 G2 PostgreSQL integration, Step 11 browser E2E and Step 12 live FastAPI PostgreSQL E2E all succeeded.
- GitHub Actions Project Governance run `27891998018`: PASS.

### Rollback

- Revert `scripts/validate_operator_soak_evidence.py`, `tests/unit/test_operator_soak_evidence.py`, the generated A209 evidence-validation artifact, Makefile wiring and A209 traceability/docs changes.

## 2026-06-21 - T1301/A202 live official retrieval adapter contract

Status: LOCAL AND REMOTE CI VALIDATED; A202/A206 STILL IN PROGRESS

### Scope

- Extended `scripts/fetch_official_source_full_text.py` with an explicit live official-source retrieval adapter for the NVIDIA Golden Vertical official source registry.
- Live capture is fail-closed behind `--capture-live --allow-live-network`; default CI does not access the network.
- The adapter extracts normalized text from HTML or PDF responses, computes `source_text_sha256`, stores only a short excerpt, validates expected-token coverage, and records HTTP attempt, retry and `source_health` metadata.
- Generated `artifacts/tests/a202/t1301_live_official_retrieval_contract.json` with status `NETWORK_EVIDENCE_MISSING`.
- Added `tests/unit/test_official_source_live_capture.py` using `httpx.MockTransport`, so unit coverage proves parsing and contract fields without real network access.

### Acceptance mapping

- T1301 -> A202 for official-source ingestion, entity-resolution evidence and source-health contract hardening.
- T1304 -> A206 only for retry/source-health metadata shape; this does not prove long-duration scheduler retry/dead-letter behavior.
- A202 remains `IN_PROGRESS`: no operator-approved live payload is committed, no live payload is loaded into PostgreSQL evidence tables, no relationship facts are published, and no legal/release clearance is implied.

### Parameters and formulas

- `min_text_chars`: 240, inherited from the existing official-source full-text contract.
- `min_token_coverage_ratio`: 1.0, inherited from the Golden Vertical expected-token evidence gate.
- `timeout_seconds`: default 20.0 for operator live capture.
- `max_bytes`: default 8 MiB per source response.
- `retry_policy`: max attempts 3; retryable statuses 408, 425, 429, 500, 502, 503, 504; backoff seconds 0, 2, 5; dead-letter-after-attempts 3.
- No scoring model or formula changed.

### Local validation

- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/ruff check scripts/fetch_official_source_full_text.py tests/unit/test_official_source_live_capture.py`: PASS.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/uv run pytest tests/unit/test_official_source_live_capture.py -q`: PASS; 4 passed.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/uv run python scripts/fetch_official_source_full_text.py --generate-live-contract --output artifacts/tests/a202/t1301_live_official_retrieval_contract.json --quiet`: PASS.
- `.venv/bin/python -m json.tool artifacts/tests/a202/t1301_live_official_retrieval_contract.json`: PASS.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/uv run pytest tests/unit -q`: PASS; 44 passed, 1 Starlette/httpx deprecation warning.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/uv run python scripts/validate_task_pack.py`: PASS.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/uv run python scripts/manage_development_status_artifacts.py generate`: PASS.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/uv run python scripts/manage_clean_room_release.py generate`: PASS; package paths 384.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/uv run python scripts/manage_release_artifacts.py generate`: PASS; manifest paths 391, checksum paths 390, `remote_status=PENDING` before remote CI evidence update.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/uv run python scripts/manage_clean_room_release.py validate`: PASS.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/uv run python scripts/manage_release_artifacts.py validate`: PASS.
- `shasum -a 256 -c CHECKSUMS.sha256`: PASS.

### Remote validation

- GitHub Actions EEI validation run `27892494323` / job `82538366876`: PASS on commit `f5fa298bc468430b68e75d311582b9f491b4d078`.
- Step 7 static/contract/lint/typecheck/unit: PASS.
- Step 8 G2 PostgreSQL preparation: PASS.
- Step 9 G2 static/contract/lint/typecheck/unit: PASS.
- Step 10 G2 PostgreSQL integration: PASS.
- Step 11 G2 browser E2E: PASS.
- Step 12 G2 live FastAPI PostgreSQL E2E: PASS.
- GitHub Actions Project Governance run `27892494331`: PASS.

### Rollback

- Revert the live adapter additions in `scripts/fetch_official_source_full_text.py`, remove `tests/unit/test_official_source_live_capture.py`, remove `artifacts/tests/a202/t1301_live_official_retrieval_contract.json`, restore A202/A206 traceability/status entries, regenerate development/release artifacts, and rerun validations.

## 2026-06-21 - T1301/A202 live capture PostgreSQL ingestion contract

Status: LOCAL AND REMOTE CI VALIDATED; A202/A206 STILL IN PROGRESS

### Scope

- Added `scripts/load_live_official_captures.py` to validate a live official-source retrieval artifact and write it into PostgreSQL evidence tables.
- The loader stores `source_text_sha256`, a short `source_text_excerpt`, `source_health`, retry metadata and context evidence; it rejects committed `source_text`.
- The loader upserts `source_documents`, `raw_source_snapshots`, `entity_resolution_candidates` and `ingestion_evidence_chain` under `record_mode=live`.
- Added `tests/fixtures/live_official_captures/nvidia_live_official_capture_fixture.json` as a CI-only `fixture_artifact` that requires `--allow-fixture-capture`.
- Added `artifacts/tests/a202/t1301_live_capture_postgres_ingestion_contract.json` with status `MISSING_OPERATOR_LIVE_PAYLOAD`.

### Acceptance mapping

- T1301 -> A202 for live capture ingestion, hash/excerpt retention, entity resolution and evidence-chain persistence.
- T1304 -> A206 only for source-health/retry metadata persistence; this does not prove long-duration retry/dead-letter behavior.
- A202 remains `IN_PROGRESS`: this contract does not include a real operator live payload, production owner decision, legal/release clearance or relationship publication.

### Parameters and formulas

- `min_text_chars`: 240.
- `min_token_coverage_ratio`: 1.0.
- `record_mode`: `live`.
- `review_status`: `machine_verified` until operator review and production owner sign-off are attached.
- No scoring formula or model profile changed.

### Local validation

- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/ruff check scripts/load_live_official_captures.py tests/unit/test_official_source_live_capture.py tests/integration/test_database_migrations.py scripts/validate_v5_production_readiness_sync.py`: PASS.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/uv run pytest tests/unit/test_official_source_live_capture.py -q`: PASS; 7 passed.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/uv run python scripts/load_live_official_captures.py --generate-contract --output artifacts/tests/a202/t1301_live_capture_postgres_ingestion_contract.json --quiet`: PASS.
- `.venv/bin/python -m json.tool tests/fixtures/live_official_captures/nvidia_live_official_capture_fixture.json`: PASS.
- `.venv/bin/python -m json.tool artifacts/tests/a202/t1301_live_capture_postgres_ingestion_contract.json`: PASS.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/uv run python scripts/validate_v5_production_readiness_sync.py`: PASS.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache PNPM=/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/pnpm make verify`: PASS after rerun outside the macOS sandbox for Chromium browser benchmark; release package paths 387, manifest paths 394, checksum paths 393.

### Remote validation

- GitHub Actions EEI validation run `27893172875` / job `82540125436`: PASS on commit `4c9c63a7ccbb9a925ed97af64b2e31d46b73c6cf`.
- Step 7 static/contract/lint/typecheck/unit: PASS.
- Step 8 G2 PostgreSQL preparation: PASS.
- Step 9 G2 static/contract/lint/typecheck/unit: PASS.
- Step 10 G2 PostgreSQL integration: PASS.
- Step 11 G2 browser E2E: PASS.
- Step 12 G2 live FastAPI PostgreSQL E2E: PASS.
- GitHub Actions Project Governance run `27893172917`: PASS.

### Rollback

- Remove `scripts/load_live_official_captures.py`, the live fixture, the A202 ingestion contract artifact, the integration/unit test additions and the status/traceability updates.
- If live parser rows were written to a deployed database, delete rows by `parser_version='nvidia-official-fulltext-live-v1'` before release or restore from a data snapshot.

## 2026-06-21 - T1301/A202 selected live official capture evidence

Status: LOCAL AND REMOTE CI VALIDATED; A202/A206 STILL IN PROGRESS

### Scope

- Added `official-source-token-alias-v1` to `scripts/fetch_official_source_full_text.py` so canonical expected-token coverage can match governed aliases such as `NVIDIA Corporation` -> `NVIDIA` and `Hon Hai/Foxconn` -> `Hon Hai` / `Foxconn` without lowering `min_token_coverage_ratio=1.0`.
- Added composite token handling for `packaging/test` that requires `packaging` plus either `test` or `testing`; a source containing only `packaging` still fails.
- Added repeatable `--anchor-id` support for operator live capture so selected official anchors can be captured fail-closed without treating unsupported anchors as healthy.
- Generated `artifacts/tests/a202/t1301_live_official_selected_capture_evidence.json` from real NVIDIA official sources `NVDA-ANCHOR-002`, `NVDA-ANCHOR-003` and `NVDA-ANCHOR-004`.
- The selected live artifact has status `LIVE_CAPTURE_READY_FOR_OPERATOR_REVIEW`, `anchors_total=3`, `anchors_failed=0`, 100% token coverage, no `source_text`, `release_clearance=false` and `relationship_publication=false`.
- Extended `tests/integration/test_database_migrations.py` so GitHub Actions G2 PostgreSQL loads the selected live artifact twice without `--allow-fixture-capture` and asserts idempotent non-fixture evidence rows.
- `NVDA-ANCHOR-001` intentionally remains outside the selected live artifact because the live page did not support the current `packaging/test` expected-token contract; this is a source-registry semantic review item, not a forced pass.

### Acceptance mapping

- T1301 -> A202 for real selected-anchor live retrieval evidence, non-fixture PostgreSQL ingestion assertions, source-health metadata and evidence-chain persistence.
- T1304 -> A206 only for retry/source-health metadata persistence; this does not prove long-duration retry/dead-letter behavior.
- A202 remains `IN_PROGRESS`: the artifact is ready for operator review but lacks production owner sign-off, formal source-license/legal clearance, production relationship publication and the `NVDA-ANCHOR-001` semantic review.
- A206 remains `IN_PROGRESS`: source-health metadata and retry attempts are not substitutes for 4h/24h scheduler/worker soak.

### Parameters and formulas

- `min_text_chars`: 240.
- `min_token_coverage_ratio`: 1.0.
- `token_alias_policy_version`: `official-source-token-alias-v1`.
- `timeout_seconds`: 30.0 for the generated selected live capture artifact.
- `max_bytes`: 8 MiB per source response.
- No scoring formula or model profile changed.

### Local validation

- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/ruff check scripts/fetch_official_source_full_text.py scripts/load_live_official_captures.py tests/unit/test_official_source_live_capture.py tests/integration/test_database_migrations.py scripts/validate_v5_production_readiness_sync.py`: PASS.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/uv run pytest tests/unit/test_official_source_live_capture.py -q`: PASS; 9 passed.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/uv run python scripts/fetch_official_source_full_text.py --capture-live --allow-live-network --anchor-id NVDA-ANCHOR-002 --anchor-id NVDA-ANCHOR-003 --anchor-id NVDA-ANCHOR-004 --output artifacts/tests/a202/t1301_live_official_selected_capture_evidence.json --timeout-seconds 30 --quiet`: PASS.
- `jq -e '(.status == "LIVE_CAPTURE_READY_FOR_OPERATOR_REVIEW") and (.counts.anchors_total == 3) and (.counts.anchors_failed == 0) and ([.. | objects | has("source_text")] | all(. == false)) and (.capture_policy.committed_full_text == false) and (.capture_policy.relationship_publication == false) and (.capture_policy.release_clearance == false)' artifacts/tests/a202/t1301_live_official_selected_capture_evidence.json`: PASS.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/uv run python scripts/validate_v5_production_readiness_sync.py`: PASS.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache PNPM=/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/pnpm make verify`: PASS after rerun outside the macOS sandbox for Chromium browser benchmark; includes governance validation, contracts, v5 readiness sync, worker/brand validators, scale benchmarks, soak smoke, operator-soak evidence validator, secret scan, UI copy validation, ruff, Next typecheck and 49 unit tests.

Local PostgreSQL integration was not run because the current shell has no `docker`, no `.env`, no `DATABASE_URL`, no `psql` and no `pg_ctl`. Remote G2 PostgreSQL validation is therefore the authoritative database evidence for this slice.

### Remote validation

- GitHub Actions EEI validation run `27893872934` / job `82541974047`: PASS on commit `d2c74426802e6d1792d160c16bc9a1561d84f87a`.
- Step 7 static/contract/lint/typecheck/unit: PASS.
- Step 8 G2 PostgreSQL preparation: PASS.
- Step 9 G2 static/contract/lint/typecheck/unit: PASS.
- Step 10 G2 PostgreSQL integration: PASS; validates the selected live artifact non-fixture PostgreSQL ingestion path.
- Step 11 G2 browser E2E: PASS.
- Step 12 G2 live FastAPI PostgreSQL E2E: PASS.
- GitHub Actions Project Governance run `27893872928`: PASS.

This remote PASS does not close A202/A206: the selected artifact is not production owner approval, source-license/legal clearance, relationship publication, `NVDA-ANCHOR-001` semantic resolution, or 4h/24h retry/dead-letter soak evidence.

### Rollback

- Revert the token alias and `--anchor-id` changes in `scripts/fetch_official_source_full_text.py`.
- Remove `artifacts/tests/a202/t1301_live_official_selected_capture_evidence.json`.
- Restore `tests/integration/test_database_migrations.py` to fixture-only live-capture assertions.
- Regenerate development, clean-room and release artifacts, then rerun validation.

## 2026-06-21 - T1307/A209 operator soak parallel-window contract repair

Status: LOCAL VALIDATED; REMOTE CI VALIDATED; A209 STILL IN PROGRESS

### Scope

- Attempted to start the documented 4h operator soak command and interrupted it after the first checkpoint stayed empty beyond the expected first-window boundary.
- Root cause: `scripts/run_soak_smoke.mjs` measured browser soak and worker soak serially, so a nominal 300-second operator window needed about 600 seconds of wall-clock time before checkpointing.
- Updated `scripts/run_soak_smoke.mjs` to run browser and worker soak in parallel inside each operator window and record `measurement.strategy=parallel_browser_worker_v1`.
- Updated `scripts/validate_operator_soak_evidence.py` so future committed 4h/24h evidence fails closed when `elapsed_wall_seconds` exceeds `measured_duration_seconds + max(60, measured_duration_seconds * 0.25)`.
- Added a regression test proving serialized double-wall-clock windows are rejected.
- Regenerated `artifacts/tests/a209/t1307_operator_soak_evidence_validation.json`; it still reports `MISSING_OPERATOR_EVIDENCE` because actual 4h and 24h artifacts are not committed.

### Acceptance mapping

- T1307 -> A209 for long-duration soak evidence quality control.
- T1304 -> A206 only indirectly: this improves the future worker/retry/dead-letter soak evidence contract but does not prove 4h/24h stability.
- A209 remains `IN_PROGRESS`; the 5-second parallel probe and validator hardening are not substitutes for committed 4h and 24h operator artifacts.

### Validation

- `node --check scripts/run_soak_smoke.mjs`: PASS.
- `node --check scripts/run_operator_soak.mjs`: PASS.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/uv run pytest tests/unit/test_operator_soak_evidence.py -q`: PASS; 4 passed.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/ruff check scripts/validate_operator_soak_evidence.py tests/unit/test_operator_soak_evidence.py`: PASS.
- `node scripts/run_operator_soak.mjs --mode ci_parallel_probe --duration-seconds 5 --window-seconds 5 --output /tmp/eei-operator-soak-parallel-probe.json --checkpoint /tmp/eei-operator-soak-parallel-probe.checkpoints.jsonl --fail-on-budget --quiet`: PASS outside the macOS sandbox; output status PASS, completed duration 5 seconds, elapsed wall 6.5612 seconds, worker jobs 12/12.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache PNPM=/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/pnpm make verify`: PASS locally after rerun outside the macOS sandbox for Chromium; includes governance validation, contracts, v5 readiness sync, worker/brand validators, scale benchmarks, soak smoke, operator-soak evidence validator, secret scan, UI copy validation, ruff, Next typecheck and 50 unit tests.

### Remote validation

- GitHub Actions EEI validation run `27894602887` / job `82543882466`: PASS on commit `5b9fe87b9d8c3344647525ff27f57ae9bd8c7e34`.
- Step 7 static/contract/lint/typecheck/unit: PASS.
- Step 8 G2 PostgreSQL preparation: PASS.
- Step 9 G2 static/contract/lint/typecheck/unit: PASS.
- Step 10 G2 PostgreSQL integration: PASS.
- Step 11 G2 browser E2E: PASS.
- Step 12 G2 live FastAPI PostgreSQL E2E: PASS.
- Step 13 Stop PostgreSQL: PASS.
- GitHub Actions Project Governance run `27894602898`: PASS.

This remote PASS does not close A209/A206: it validates the runner and fail-closed validator repair only, not committed 4h or 24h operator soak evidence.

### Rollback

- Revert the parallel `Promise.all` measurement in `scripts/run_soak_smoke.mjs`.
- Revert the elapsed-wall validator rule and regression test.
- Regenerate the A209 evidence-validation artifact and rerun validation.

## 2026-06-21 - T1307/A209 4h operator soak evidence

Status: LOCAL VALIDATED; REMOTE CI PENDING; A209 STILL IN PROGRESS

### Scope

- Produced `artifacts/tests/a209/t1307_operator_soak_4h.json`.
- Produced `artifacts/tests/a209/t1307_operator_soak_4h.checkpoints.jsonl`.
- Regenerated `artifacts/tests/a209/t1307_operator_soak_evidence_validation.json`.
- The accepted run used `PLAYWRIGHT_BROWSERS_PATH=/private/tmp/eei-ms-playwright` after an earlier attempt failed at window 33 because the default macOS Playwright cache no longer contained `chromium_headless_shell-1228`.

### Acceptance mapping

- T1307 -> A209 for 4h long-duration soak evidence.
- T1304 -> A206 only indirectly because the run exercises browser+worker soak with the worker supervisor binding, but it is not full retry/dead-letter production soak proof.
- A209 remains `IN_PROGRESS`: 24h operator evidence is still missing.

### Validation

- `env PLAYWRIGHT_BROWSERS_PATH=/private/tmp/eei-ms-playwright apps/web/node_modules/.bin/playwright install chromium`: PASS.
- `env PLAYWRIGHT_BROWSERS_PATH=/private/tmp/eei-ms-playwright node scripts/run_operator_soak.mjs --mode ci_fixed_browser_path_probe --duration-seconds 5 --window-seconds 5 --output /tmp/eei-fixed-browser-path-probe.json --checkpoint /tmp/eei-fixed-browser-path-probe.checkpoints.jsonl --fail-on-budget --quiet`: PASS.
- `env PLAYWRIGHT_BROWSERS_PATH=/private/tmp/eei-ms-playwright node scripts/run_operator_soak.mjs --mode operator_4h --duration-hours 4 --window-seconds 300 --output artifacts/tests/a209/t1307_operator_soak_4h.json --checkpoint artifacts/tests/a209/t1307_operator_soak_4h.checkpoints.jsonl --fail-on-budget --quiet`: PASS.
- 4h run summary: status PASS; requested duration 14400 seconds; completed duration 14400 seconds; windows_completed 48; windows_failed 0; checkpoint rows 48; every checkpoint window PASS.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/uv run python scripts/validate_operator_soak_evidence.py generate --quiet`: PASS.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/uv run python scripts/validate_operator_soak_evidence.py validate --quiet`: PASS.
- Validation artifact status: `PARTIAL_OPERATOR_EVIDENCE`; `operator_4h` PASS, `operator_24h` MISSING.

### Rollback

- Remove `artifacts/tests/a209/t1307_operator_soak_4h.json`.
- Remove `artifacts/tests/a209/t1307_operator_soak_4h.checkpoints.jsonl`.
- Regenerate `artifacts/tests/a209/t1307_operator_soak_evidence_validation.json`.
- Regenerate development, clean-room and release artifacts, then rerun validation.

## 2026-06-22 - T1301/A202 context-only source anchor semantic revision

Status: LOCAL VALIDATED; REMOTE POSTGRESQL CI PENDING; A202 STILL IN PROGRESS

### Scope

- Revised `data/nvidia_public_source_anchors.csv` so `NVDA-ANCHOR-001` is explicitly `publication_scope=discovery_context_only`.
- Removed `packaging/test`, `wafer`, `chip`, `manufacturing` and `systems` from the 001 expected-token contract and replaced them with discovery-context terms `AI infrastructure`, `ecosystem` and `Taiwan`.
- Added `anchor_scope` persistence to curated, dry-run, operator-source and live-capture ingestion payloads and evidence-chain structured facts.
- Added `artifacts/tests/a202/t1301_context_anchor_semantic_revision_contract.json` as the machine-readable contract for this revision.
- Updated A202 unit/integration tests and fixtures so candidate counts reflect the revised context-only token set.

### Acceptance mapping

- T1301 -> A202 for source-registry semantic correctness and evidence-chain provenance.
- A202 remains `IN_PROGRESS`: this does not provide production owner sign-off, formal source-license/legal clearance, relationship publication or A206/A209 long-duration evidence.

### Parameters and formulas

- No scoring formula changed.
- No canonical runtime parameter changed.
- `NVDA-ANCHOR-001` source metadata now has `evidence_role=context` and `publication_scope=discovery_context_only`.

### Validation

- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/ruff check scripts/load_curated_ingestion_anchors.py scripts/fetch_official_source_full_text.py scripts/load_operator_source_captures.py scripts/load_live_official_captures.py tests/unit/test_official_source_live_capture.py tests/integration/test_database_migrations.py scripts/validate_v5_production_readiness_sync.py`: PASS.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/pytest tests/unit/test_official_source_live_capture.py -q`: PASS; 10 passed.
- `.venv/bin/python -m json.tool artifacts/tests/a202/t1301_context_anchor_semantic_revision_contract.json`: PASS.
- `.venv/bin/python -m json.tool tests/fixtures/official_source_full_text/nvidia_official_full_text_dry_run.json`: PASS.
- `.venv/bin/python -m json.tool tests/fixtures/operator_source_captures/nvidia_operator_source_captures.json`: PASS.
- `.venv/bin/python -m json.tool tests/fixtures/live_official_captures/nvidia_live_official_capture_fixture.json`: PASS.
- `.venv/bin/python -m json.tool artifacts/tests/a202/t1301_live_official_selected_capture_evidence.json`: PASS.
- `.venv/bin/python -m json.tool artifacts/tests/a202/t1301_live_official_retrieval_contract.json`: PASS.
- `.venv/bin/python -m json.tool artifacts/tests/a202/t1301_live_capture_postgres_ingestion_contract.json`: PASS.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/python scripts/validate_v5_production_readiness_sync.py`: PASS.

Local PostgreSQL integration was not run in this shell; remote G2 PostgreSQL must validate the updated candidate-count contracts.

### Rollback

- Restore the prior `NVDA-ANCHOR-001` expected token list.
- Remove `anchor_scope` fields from ingestion structured facts.
- Remove `artifacts/tests/a202/t1301_context_anchor_semantic_revision_contract.json`.
- Restore previous A202 candidate-count assertions and rerun validation.

## 2026-06-22 - T1301/A202 operator/legal review packet contract

Status: LOCAL VALIDATED; REMOTE CI PENDING; A202 STILL IN PROGRESS

### Scope

- Added `scripts/validate_a202_operator_review_packet.py`.
- Generated `artifacts/tests/a202/t1301_operator_review_packet_contract.json` from the selected live official-source capture artifact.
- Extended `tests/unit/test_official_source_live_capture.py` so the packet stays fail-closed and rejects any claimed clearance.
- Added the validator to `make lint`.
- Updated A202 acceptance, traceability, V5 status and task records.

### Acceptance mapping

- T1301 -> A202 for the real-data evidence-chain review handoff.
- A202 remains `IN_PROGRESS`: this contract is review input only and does not provide source-license review, passage-level relationship approval, production owner sign-off, legal release clearance or A209 24h operator soak evidence. A206 scheduler/retry/dead-letter functionality is now a separate closed gate.

### Parameters and formulas

- No scoring formula changed.
- No canonical model parameter changed.
- New fail-closed review-packet status: `PENDING_OWNER_LEGAL_CLEARANCE`.
- Required gate set: `live_capture_ready_for_review`, `source_license_review`, `passage_level_relationship_review`, `production_owner_signoff`, `legal_release_clearance`, `a206_scheduler_retry_dead_letter`, `a209_24h_operator_soak`.

### Validation

- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/ruff check scripts/validate_a202_operator_review_packet.py tests/unit/test_official_source_live_capture.py`: PASS.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/python -m py_compile scripts/validate_a202_operator_review_packet.py tests/unit/test_official_source_live_capture.py`: PASS.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/python -m pytest -q tests/unit/test_official_source_live_capture.py`: PASS; 12 passed.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/python scripts/validate_a202_operator_review_packet.py generate --packet artifacts/tests/a202/t1301_operator_review_packet_contract.json`: PASS; 3 anchors, publication allowed false.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/python scripts/validate_a202_operator_review_packet.py validate --packet artifacts/tests/a202/t1301_operator_review_packet_contract.json`: PASS.
- `python3 -m json.tool artifacts/tests/a202/t1301_operator_review_packet_contract.json`: PASS.

### Rollback

- Remove `scripts/validate_a202_operator_review_packet.py`.
- Remove `artifacts/tests/a202/t1301_operator_review_packet_contract.json`.
- Revert the unit-test, Makefile, acceptance, traceability and task-record updates.
- Regenerate development, clean-room and release artifacts, then rerun validation.

## 2026-06-22 - T1304/A206 scheduler closure decoupled from A209 soak

Status: LOCAL VALIDATED; REMOTE CI PENDING; A206 DONE; A209 STILL IN PROGRESS

### Scope

- Closed T1304/A206 as scheduler functionality: lease, auto wake, idempotency key, heartbeat, retry cap, dead-letter, graceful shutdown, transactional outbox dispatch, Docker Compose worker binding and worker supervisor execution.
- Kept T1307/A209 as the separate long-duration stability gate for 24h operator soak evidence.
- Updated `scripts/validate_v5_production_readiness_sync.py` so A206 is implemented while A209 remains partial.
- Updated `data/task_backlog.csv`, `data/acceptance_matrix.csv`, `data/acceptance_traceability.csv`, `data/development_status_ledger.csv`, `artifacts/tests/a206/t1304_scheduler_retry_dead_letter_contract.json`, and the A202 operator-review packet gate status.

### Acceptance mapping

- T1304 -> A206 is now `DONE`.
- T1307 -> A209 remains `IN_PROGRESS`; the failed/incomplete 24h operator run is a production stability gate, not a blocker for A206 functionality.
- A202 remains `IN_PROGRESS` because source-license review, passage-level relationship review, production owner sign-off, legal release clearance and A209 24h operator soak are still missing.

### Parameters and formulas

- No scoring formula changed.
- No scheduler threshold changed.
- A202 review packet required-gate count remains 7; the A206 gate changed from missing soak evidence to present scheduler/retry/dead-letter closure evidence.

### Validation

- Baseline GitHub Actions evidence before this status closure: EEI validation run `27934137278` / job `82651968987` passed Step 7 `make verify`, Step 10 G2 PostgreSQL integration, Step 11 browser E2E and Step 12 live FastAPI PostgreSQL E2E on commit `f3fdd649`.
- Project Governance run `27934137279` passed and produced artifact `project-governance-ci-attestation-27934137279-1`.
- Final local validation for this status update is recorded in the run output and must be followed by remote CI for the closure commit.

### Rollback

- Revert the A206 status rows, validator move from implemented back to partial, A206 contract status change and A202 gate rename.
- Regenerate A202 packet, development artifacts, clean-room package and release checksums.
- Rerun `make verify` and keep A206 `IN_PROGRESS` if the scheduler closure evidence no longer validates.

## 2026-06-22 - T1301/A202 and T1309/A210 signed release decision bundle contract

Status: LOCAL VALIDATED; REMOTE CI PENDING; A202/A210 STILL IN PROGRESS

### Scope

- Added `scripts/validate_release_decision_bundle.py`.
- Added `tests/fixtures/release_decision_bundle/a202_a210_release_decision_bundle_template.json`.
- Added `tests/unit/test_release_decision_bundle.py`.
- Generated `artifacts/tests/a202/t1301_a202_a210_release_decision_bundle_contract.json`.
- Wired `validate-release-decision-bundle` into `make verify`.
- Updated A202/A210 acceptance, traceability, v5 readiness and task records.

### Acceptance mapping

- T1301 -> A202 for source-license, passage-level relationship review, production owner sign-off and legal release-clearance decision inputs.
- T1309 -> A210 for brand clearance or signed risk waiver decision inputs.
- A209 remains a separate long-running production stability gate; this contract does not replace 24h soak evidence.
- A202 and A210 remain `IN_PROGRESS`: repository templates and contract tests are not real legal advice, source-license clearance, production owner approval, brand clearance, relationship publication or public launch approval.

### Parameters and formulas

- No scoring formula changed.
- No graph traversal, extraction or model-weight behavior changed.
- New governance contract constants: `eei-a202-a210-release-decision-bundle-v1` and `eei-a202-a210-release-decision-bundle-contract-v1`.
- Signed-bundle CLI semantics: a complete signed bundle reports `signed_decision_complete=true` and `release_ready=false` until A209 24h soak and release-manager activation are separately satisfied.

### Validation

- `PYTHONPYCACHEPREFIX=/private/tmp/eei-release-decision-pycache python3 -m py_compile scripts/validate_release_decision_bundle.py tests/unit/test_release_decision_bundle.py`: PASS.
- `.venv/bin/python -m pytest -q tests/unit/test_release_decision_bundle.py`: PASS; 4 passed.
- `.venv/bin/ruff check scripts/validate_release_decision_bundle.py tests/unit/test_release_decision_bundle.py`: PASS.
- `.venv/bin/python scripts/validate_release_decision_bundle.py generate`: PASS.
- `.venv/bin/python scripts/validate_release_decision_bundle.py validate`: PASS.
- `.venv/bin/python scripts/validate_release_decision_bundle.py validate-bundle --template-only`: PASS; `release_ready=false`.
- `make validate-release-decision-bundle`: PASS.
- `.venv/bin/python -m pytest -q tests/unit/test_release_decision_bundle.py tests/unit/test_official_source_live_capture.py`: PASS; 16 passed.
- `.venv/bin/python scripts/validate_v5_production_readiness_sync.py`: PASS.
- `.venv/bin/python scripts/validate_task_pack.py`: PASS.

### Rollback

- Remove `scripts/validate_release_decision_bundle.py`.
- Remove `tests/fixtures/release_decision_bundle/a202_a210_release_decision_bundle_template.json`.
- Remove `tests/unit/test_release_decision_bundle.py`.
- Remove `artifacts/tests/a202/t1301_a202_a210_release_decision_bundle_contract.json`.
- Revert Makefile, acceptance, traceability and governance-record updates.
- Regenerate development, clean-room and release artifacts, then rerun validation.

## 2026-06-22 - T904/A026-A027 gold-quality evaluation contract

Status: LOCAL FOCUSED VALIDATED; REMOTE CI PENDING; A026/A027 STILL IN PROGRESS

### Scope

- Added `scripts/validate_gold_quality_evaluation.py`.
- Added `tests/fixtures/gold_quality/golden_vertical_gold_labels_sample.json`.
- Added `tests/unit/test_gold_quality_evaluation.py`.
- Generated `artifacts/tests/a026/t904_entity_resolution_gold_evaluation_contract.json`.
- Generated `artifacts/tests/a027/t904_relationship_gold_evaluation_contract.json`.
- Wired `validate-gold-quality-evaluation` into `make verify`.
- Updated A026/A027 acceptance, traceability, T904 backlog status, V5 readiness and governance parameter/model records.

### Acceptance mapping

- T904 -> A026 for entity-resolution gold-label precision/recall/source-coverage reporting.
- T904 -> A027 for relationship gold-label precision/recall/source-coverage reporting.
- T1301 -> A202 remains linked because production real-data ingestion cannot be accepted without a production-quality evidence chain.
- A026 and A027 remain `IN_PROGRESS`: the repository fixture is intentionally small, `production_gold_set=false`, and `release_gate_closure_allowed=false`.
- A209 remains a separate long-running production stability gate; 24h soak continues in the background and must not block this bounded quality-contract work.

### Parameters and formulas

- No scoring formula changed.
- No graph traversal, extraction or model-weight behavior changed.
- New MOD-012/FORM-012 gate parameters:
  - `PARAM-064` / `gold_quality.entity_min_cases = 50`.
  - `PARAM-065` / `gold_quality.entity_min_precision = 0.95`.
  - `PARAM-066` / `gold_quality.relationship_min_cases = 100`.
  - `PARAM-067` / `gold_quality.relationship_min_precision = 0.90`.
  - `PARAM-068` / `gold_quality.source_coverage_min = 1.0`.

### Validation

- `TMPDIR=/private/tmp PYTHONPYCACHEPREFIX=/private/tmp/eei-gold-pycache python3 -m py_compile scripts/validate_gold_quality_evaluation.py tests/unit/test_gold_quality_evaluation.py`: PASS.
- `TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q tests/unit/test_gold_quality_evaluation.py -p no:cacheprovider`: PASS; 4 passed.
- `TMPDIR=/private/tmp .venv/bin/ruff check scripts/validate_gold_quality_evaluation.py tests/unit/test_gold_quality_evaluation.py`: PASS.
- `.venv/bin/python scripts/validate_gold_quality_evaluation.py generate`: PASS; `release_gate_closure_allowed=false`.
- `.venv/bin/python scripts/validate_gold_quality_evaluation.py validate`: PASS; A026/A027 `IN_PROGRESS`.

### Rollback

- Remove `scripts/validate_gold_quality_evaluation.py`.
- Remove `tests/fixtures/gold_quality/golden_vertical_gold_labels_sample.json`.
- Remove `tests/unit/test_gold_quality_evaluation.py`.
- Remove A026/A027 gold-quality contract artifacts.
- Revert Makefile, A026/A027 acceptance, T904 backlog, parameter/model and V5 readiness updates.
- Regenerate development, clean-room and release artifacts, then rerun validation.

## 2026-06-22 - T1301/A202 signed bundle publication binding

Status: LOCAL FOCUSED VALIDATED; REMOTE POSTGRESQL CI PENDING; A202/A210/A209 STILL IN PROGRESS

### Scope

- Extended `scripts/publish_reviewed_relationship_facts.py` so `production_owner_signoff=true` publication requires `--release-decision-bundle`.
- Added `tests/fixtures/release_decision_bundle/a202_a210_signed_decision_bundle_contract_test.json` as a contract-test signed bundle that validates signatures but is not real legal, brand, source-license or owner clearance.
- Extended `scripts/validate_release_decision_bundle.py` and the A202 contract artifact so the signed fixture is tracked as validation input with `signed_contract_test_counts_as_clearance=false`.
- Extended PostgreSQL integration assertions so owner-signoff publication fails without a signed bundle, rejects the template bundle, and persists bundle hash/signature summaries into `data_snapshots`, relationship qualifiers, relationship evidence and fact-version payloads.

### Acceptance mapping

- T1301 -> A202 for real-data evidence-chain strengthening and production owner publication gating.
- T1309 -> A210 remains linked through the signed bundle legal/brand clearance inputs.
- A202 remains `IN_PROGRESS`: the committed signed bundle is only a contract-test fixture.
- A209 remains an independent background stability gate and is not replaced by signed-bundle completion.

### Parameters and formulas

- No scoring formula changed.
- No graph traversal, extraction or model-weight behavior changed.
- No active threshold value changed; existing release-decision bundle schema governance remains in force.

### Validation

- `python3 -m json.tool tests/fixtures/release_decision_bundle/a202_a210_signed_decision_bundle_contract_test.json`: PASS.
- `python3 -m py_compile scripts/publish_reviewed_relationship_facts.py scripts/validate_release_decision_bundle.py tests/unit/test_release_decision_bundle.py tests/integration/test_database_migrations.py`: PASS.
- `.venv/bin/ruff check scripts/publish_reviewed_relationship_facts.py scripts/validate_release_decision_bundle.py tests/unit/test_release_decision_bundle.py tests/integration/test_database_migrations.py`: PASS.
- `.venv/bin/python -m pytest -q tests/unit/test_release_decision_bundle.py -p no:cacheprovider`: PASS; 5 passed.
- `.venv/bin/python scripts/validate_release_decision_bundle.py validate-bundle --bundle tests/fixtures/release_decision_bundle/a202_a210_signed_decision_bundle_contract_test.json`: PASS; `signed_decision_complete=true`, `release_ready=false`.
- `.venv/bin/python scripts/validate_release_decision_bundle.py generate`: PASS.
- `.venv/bin/python scripts/validate_release_decision_bundle.py validate`: PASS.

### Remaining gaps

- Real source-license review, passage-level relationship review, production owner approval, legal/brand clearance, release-manager activation, production gold-set evidence and A209 24h soak are still missing.
- Local PostgreSQL integration is skipped on this host unless `DATABASE_URL` or `.env` is present; remote CI must prove the integration assertions.

### Rollback

- Revert `scripts/publish_reviewed_relationship_facts.py`, `scripts/validate_release_decision_bundle.py`, the signed fixture, unit/integration tests, A202 artifact and governance/status records.
- Regenerate development, clean-room and release artifacts, then rerun validation.

## 2026-06-23 - T1303/A204-A205 supervised model refresh worker wake

Status: LOCAL STATIC VALIDATED; REMOTE POSTGRESQL CI PENDING; A204/A205/A209 STILL IN PROGRESS

### Scope

- Added `apps.worker.app.main` model-refresh wake metadata for supervised `score_recompute` and `data_snapshot_refresh` filters.
- Bound the model-refresh supervisor path to A204/A205/A206/A209 while explicitly declaring that A209 4h/24h soak is not closed by worker wake evidence.
- Updated PostgreSQL integration assertions so T1303 recompute and data snapshot refresh jobs execute through `python -m apps.worker.app.main supervise`, not direct in-process `run_once` only.
- Kept score formulas, model weights, graph traversal, extraction logic, database migrations and public API semantics unchanged.

### Acceptance mapping

- T1303 -> A204 for transactional activation and supervised score/data refresh execution evidence.
- T1303 -> A205 for atomic active-context refresh token advancement and stale-client semantics after supervised worker completion.
- T1304/A206 remains the scheduler/worker functionality gate; this slice reuses its supervisor CLI surface without reopening A206.
- T1307/A209 remains a separate background long-duration stability gate and must not block this bounded feature work.

### Parameters and formulas

- No scoring formula changed.
- No graph traversal, extraction model or model-weight behavior changed.
- No threshold or parameter value changed.
- New contract label only: `t1303-a204-a205-supervised-refresh-wake-v1`.

### Validation

- `PYTHONPYCACHEPREFIX=/private/tmp/eei-verify-pycache .venv/bin/python -m py_compile apps/worker/app/main.py tests/integration/test_database_migrations.py`: PASS.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/ruff check apps/worker/app/main.py tests/integration/test_database_migrations.py`: PASS.
- Remote GitHub Actions G2 PostgreSQL integration is still required to execute the new supervisor CLI assertions against PostgreSQL.

### Remaining gaps

- A204/A205 remain `IN_PROGRESS` until this supervised wake slice is remote-CI bound and release-manager plus long-duration refresh evidence are current.
- A209 24h soak remains a background independent gate with checkpoint evidence; it is not replaced by this slice.
- Production relationship approval, legal/source clearance and brand clearance remain separate blockers.

### Rollback

- Revert `apps/worker/app/main.py` model-refresh wake metadata and the T1303 integration-test supervisor CLI assertions.
- Revert A204/A205 artifact, acceptance traceability, development status, V5 sync, delivery task and ledger updates.
- Regenerate development, clean-room and release artifacts, then rerun local validation and GitHub CI.

## 2026-06-23 - T1303/A204-A205 supervised worker wake CI binding

Status: REMOTE CI VALIDATED FOR THIS SLICE; A204/A205/A209 STILL IN PROGRESS

### Scope

- Bound commit `df1925aa6c8d2e2c5cd6e4f0c760ebc21b168ed4` remote CI proof into T1303/A204-A205 supervised model refresh worker wake records.
- Project Governance run `27986420238` / job `82828868078` passed governance validator, changed-scope, information quality, dashboard verification and CI attestation steps.
- EEI validation run `27986420494` / job `82828868875` passed Step 10 G2 PostgreSQL integration, Step 11 browser E2E and Step 12 live FastAPI/PostgreSQL E2E for the supervisor CLI wake assertions.

### Acceptance mapping

- T1303 -> A204/A205 evidence is stronger: worker wake is no longer local-only or remote-pending.
- T1307/A209 remains independent and open; this CI binding does not substitute for 24h soak evidence.

### Parameters and formulas

- No scoring formula changed.
- No graph traversal, extraction model, model-weight, threshold or parameter value changed.

### Remaining gaps

- A204/A205 remain `IN_PROGRESS` until release-manager activation and long-duration refresh evidence are current.
- A209 24h soak remains a background independent gate.
- Production relationship approval and formal legal/source/brand clearance remain separate blockers.

### Rollback

- Revert this CI-binding governance update and restore the previous precommit-pending T1303 worker wake evidence records.
- Regenerate development, clean-room and release artifacts, then rerun local validation and GitHub CI.

## 2026-06-23 - T1301/A202 publication operation-log audit

Status: LOCAL AND REMOTE CI VALIDATED; A202/A209/A210 STILL IN PROGRESS

### Scope

- Added deterministic `operation_logs` writes to `scripts/publish_reviewed_relationship_facts.py` for each reviewed relationship publication.
- Each audit row uses action `a202_publish_reviewed_relationship_fact`, object type `relationship`, deterministic `request_id`, old/new publication payloads, A202 task/acceptance metadata, release-decision bundle hashes when present, and explicit non-closure flags for A202/A209/release-manager gates.
- Extended the PostgreSQL integration contract so fixture-review and production-owner-signoff contract paths assert audit rows and idempotent reruns do not duplicate them.
- Added `production_owner_publication_writes_operation_log=true` to the A202/A210 release decision contract artifact.

### Acceptance mapping

- T1301 -> A202 for real-data evidence-chain auditability and recovery traceability.
- This does not close A202: source-license review, passage-level relationship approval, real production owner approval, formal legal/brand clearance, production gold labels, release-manager activation and A209 24h soak are still missing.

### Parameters and formulas

- No scoring formula changed.
- No graph traversal, extraction model, model-weight, threshold or parameter value changed.

### Validation

- `PYTHONPYCACHEPREFIX=/private/tmp/eei-a202-pycache .venv/bin/python -m py_compile scripts/publish_reviewed_relationship_facts.py scripts/validate_release_decision_bundle.py tests/unit/test_release_decision_bundle.py tests/integration/test_database_migrations.py`: PASS.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/ruff check scripts/publish_reviewed_relationship_facts.py scripts/validate_release_decision_bundle.py tests/unit/test_release_decision_bundle.py tests/integration/test_database_migrations.py`: PASS.
- `PYTHONPYCACHEPREFIX=/private/tmp/eei-a202-pycache UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/uv run pytest tests/unit/test_release_decision_bundle.py tests/unit/test_scoring.py -q -p no:cacheprovider`: PASS, 19 passed.
- `env -u DATABASE_URL PYTHONPYCACHEPREFIX=/private/tmp/eei-a202-pycache UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/uv run pytest tests/integration/test_database_migrations.py -q -p no:cacheprovider`: SKIPPED locally because this host has no `DATABASE_URL`; remote PostgreSQL CI is required.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/python scripts/validate_release_decision_bundle.py validate`: PASS.
- Local `make verify`: PASS after artifact regeneration and dashboard-drift repair.
- Root governance sync: PASS.
- Root governance pytest: PASS, 129 passed and 4 subtests passed.
- Project Governance run `27989821924` job `82839592718`: PASS.
- EEI validation run `27989821946` job `82839592720`: PASS, including Step 10 PostgreSQL integration, Step 11 browser E2E and Step 12 live FastAPI/PostgreSQL E2E.

### Remaining gaps

- A202 remains `IN_PROGRESS` until real signed source/legal/owner/brand evidence and production gold labels are attached.
- A209 24h soak remains a background independent gate and is not replaced by operation logs.

### Rollback

- Revert `scripts/publish_reviewed_relationship_facts.py`, `scripts/validate_release_decision_bundle.py`, `tests/integration/test_database_migrations.py` and the regenerated A202 contract artifact.
- Regenerate development, clean-room and release artifacts, then rerun local validation and GitHub CI.

## 2026-06-23 - T1301/A202 source withdrawal and counter-evidence fail-closed publication gate

Status: LOCAL STATIC VALIDATED; REMOTE POSTGRESQL CI PENDING; A202/A209/A210 STILL IN PROGRESS

### Scope

- Added publication-time checks in `scripts/publish_reviewed_relationship_facts.py` so reviewed relationship facts fail closed when linked `raw_source_snapshots` are `disputed`, linked `ingestion_evidence_chain` rows are `disputed`, or linked evidence-chain rows contain counter-evidence without explicit counter-evidence review.
- Propagated `counter_evidence_reviewed` from the signed A202/A210 release decision bundle into the production owner sign-off publication validation path.
- Extended the PostgreSQL integration contract with a source-withdrawal rehearsal that mutates database state before publication and asserts failed publication leaves relationships, fact versions and publication operation logs unchanged.
- A209 24h soak remains a background long-running stability gate and does not block this bounded A202 source-withdrawal protection slice.

### Acceptance mapping

- T1301 -> A202 for real-data evidence-chain safety, source withdrawal rehearsal and counter-evidence control.
- This does not close A202: real source-license review, passage-level relationship approval, real production owner approval, formal legal/brand clearance, production gold labels, release-manager activation and A209 24h soak are still missing.

### Parameters and formulas

- No scoring formula changed.
- No graph traversal, extraction model, model weight, threshold or active parameter value changed.
- This is a publication-control and evidence-chain gate change under the existing MOD-012 operational-controls contract.

### Validation

- `PYTHONPYCACHEPREFIX=/private/tmp/eei-a202-pycache .venv/bin/python -m py_compile scripts/publish_reviewed_relationship_facts.py tests/integration/test_database_migrations.py`: PASS.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/ruff check scripts/publish_reviewed_relationship_facts.py tests/integration/test_database_migrations.py`: PASS.
- `PYTHONPYCACHEPREFIX=/private/tmp/eei-a202-pycache UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/uv run pytest tests/unit/test_release_decision_bundle.py tests/unit/test_scoring.py -q -p no:cacheprovider`: PASS, 19 passed.
- `env -u DATABASE_URL PYTHONPYCACHEPREFIX=/private/tmp/eei-a202-pycache UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/uv run pytest tests/integration/test_database_migrations.py -q -p no:cacheprovider`: SKIPPED locally because this host has no `DATABASE_URL`; remote PostgreSQL CI is required for the new rehearsal assertions.
- `TMPDIR=/private/tmp PLAYWRIGHT_BROWSERS_PATH=/private/tmp/eei-ms-playwright PYTHONPYCACHEPREFIX=/private/tmp/eei-verify-pycache UV_CACHE_DIR=/private/tmp/eei-uv-cache make verify`: PASS, including governance/catalog validators, release artifacts, scale/soak smoke, secret scan, UI copy, ruff, web typecheck and 62 unit tests.

### Remaining gaps

- A202 remains `IN_PROGRESS` until real signed source/legal/owner/brand evidence and production gold labels are attached.
- A209 24h soak remains a background independent gate and is not replaced by source-withdrawal rehearsal.
- Formal market/legal brand clearance remains A210 work.

### Rollback

- Revert `scripts/publish_reviewed_relationship_facts.py`, `tests/integration/test_database_migrations.py` and the governance/artifact updates from this slice.
- Regenerate development, clean-room and release artifacts, then rerun local validation and GitHub CI.

## 2026-06-23 - T1301/A202 source-withdrawal CI binding

Status: REMOTE CI VALIDATED FOR THIS SLICE; A202/A209/A210 STILL IN PROGRESS

### Scope

- Bound commit `6563e59533b1e0852fbafc73cac31c0f03f0e375` remote CI proof into the A202 source-withdrawal and counter-evidence fail-closed publication rehearsal.
- Project Governance run `27991823179` completed successfully.
- EEI validation run `27991823195` job `82845668499` completed successfully, including Step 10 G2 PostgreSQL integration, Step 11 browser E2E and Step 12 live FastAPI/PostgreSQL E2E.

### Acceptance mapping

- T1301 -> A202 evidence is stronger: the source-withdrawal and counter-evidence PostgreSQL state-mutation assertions are no longer local-only.
- A202 remains `IN_PROGRESS`: CI validation of the repository rehearsal is not real operator withdrawal evidence, source-license review, passage-level approval, production owner approval, formal legal/brand clearance, production gold labels, release-manager activation or A209 24h soak.

### Rollback

- Revert this CI-binding governance update and restore the previous remote-pending source-withdrawal evidence records if the cited GitHub Actions runs are invalidated.

## 2026-06-23 - T1303/A204-A205 release-manager activation preflight

Status: LOCAL VALIDATED; REMOTE CI ATTESTED BY FOLLOW-UP BINDING; A204/A205/A209/A210/A026/A027 STILL IN PROGRESS

### Scope

- Added `scripts/validate_release_manager_activation.py`.
- Added `artifacts/tests/a205/t1303_release_manager_activation_preflight.json`.
- Added `tests/unit/test_release_manager_activation.py`.
- The preflight aggregates A202 signed-decision evidence, A026/A027 gold-quality evidence, A209 operator soak evidence and A210 brand-clearance evidence before final release-manager activation.
- Current repository state intentionally reports `RELEASE_MANAGER_ACTIVATION_BLOCKED`, `activation_ready=false`, `relationship_publication_allowed=false` and `public_brand_launch_allowed=false`.

### Acceptance mapping

- T1303 -> A204/A205 for release-manager activation preflight governance around transactional model activation and global refresh release.
- T1301/T1307/T1309/T904 remain linked because A202 real source/legal/owner evidence, A209 24h soak, A210 formal clearance and A026/A027 production gold labels are required before activation can be ready.

### Parameters and formulas

- No scoring formula changed.
- No graph traversal, extraction model, model weight, threshold or active parameter value changed.
- This is a MOD-012 operational release-control contract only.

### Validation

- `PYTHONPYCACHEPREFIX=/private/tmp/eei-release-manager-pycache .venv/bin/python -m py_compile scripts/validate_release_manager_activation.py tests/unit/test_release_manager_activation.py`: PASS.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/ruff check scripts/validate_release_manager_activation.py tests/unit/test_release_manager_activation.py scripts/validate_v5_production_readiness_sync.py`: PASS.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/python scripts/validate_release_manager_activation.py validate`: PASS.
- `PYTHONPYCACHEPREFIX=/private/tmp/eei-release-manager-pycache UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/uv run pytest tests/unit/test_release_manager_activation.py tests/unit/test_release_decision_bundle.py -q -p no:cacheprovider`: PASS, 7 passed.

### Remaining gaps

- A204/A205 remain `IN_PROGRESS` until release-manager activation preflight is ready with real signed source/license/owner/legal/brand evidence, A026/A027 production gold labels and A209 24h soak evidence.
- The committed signed decision fixture is schema evidence only and does not count as real clearance.
- A209 24h soak remains a background independent gate.

### Rollback

- Remove `scripts/validate_release_manager_activation.py`, `tests/unit/test_release_manager_activation.py` and `artifacts/tests/a205/t1303_release_manager_activation_preflight.json`.
- Revert A204/A205 traceability, V5 sync, delivery task and generated release/governance artifacts, then rerun validation.

## 2026-06-23 - T1303/A204-A205 release-manager preflight CI binding

Status: REMOTE CI VALIDATED FOR THIS SLICE; A204/A205/A209/A210/A026/A027 STILL IN PROGRESS

### Scope

- Bound commit `baaaee0fd74a9435810eb005ebb5db5b7f1c2c9d` remote CI proof into the T1303/A204-A205 release-manager activation preflight.
- Project Governance run `27994465700` completed successfully.
- EEI validation run `27994465691` job `82853640406` completed successfully.
- EEI validation Step 7 static/contract/lint/typecheck/unit, Step 10 G2 PostgreSQL integration, Step 11 browser E2E and Step 12 live FastAPI/PostgreSQL E2E all passed.

### Acceptance mapping

- T1303 -> A204/A205 evidence is stronger: the fail-closed release-manager activation preflight is no longer local-only or remote-pending.
- T1301/T1307/T1309/T904 remain linked because A202 real source/legal/owner evidence, A209 24h soak, A210 formal clearance and A026/A027 production gold labels are still required before activation can be ready.

### Parameters and formulas

- No scoring formula changed.
- No graph traversal, extraction model, model weight, threshold or active parameter value changed.
- This is a remote CI evidence-binding update only.

### Remaining gaps

- A204/A205 remain `IN_PROGRESS`: CI validation of a blocked preflight is not release-manager activation.
- A202 still lacks real signed source-license review, passage-level relationship approval, production owner approval and legal release clearance.
- A026/A027 still require production human-labeled gold cases.
- A209 24h soak remains a background independent gate.
- A210 formal brand legal/market clearance or signed risk waiver is still missing.

### Rollback

- Revert this CI-binding governance update and restore the preflight manifest to remote-pending if the cited GitHub Actions evidence is invalidated.

## 2026-06-24 - T1303/A204-A205 model config apply operator CLI

Status: LOCAL VALIDATED; REMOTE CI PENDING; A204/A205/A209/A210/A026/A027 STILL IN PROGRESS

### Scope

- Upgraded `scripts/apply_model_config.py` from preview-only to a fail-closed operator CLI.
- `--dry-run` validates the model profile and threshold files, emits hash-bound A204/A205 preview evidence and performs no database write.
- `--execute` now requires `DATABASE_URL` or `--database-url` and reuses `DomainRepository` to create a draft profile version, atomically activate it and enqueue a score recompute job.
- Added `tests/unit/test_model_config_apply.py` with a fake repository to assert call order, refresh-token propagation and recompute enqueue semantics without touching a live database.
- Added `scripts/apply_model_config.py` to `make lint`.
- Regenerated `artifacts/model_config_import_preview.json` under the new `eei-model-config-apply-contract-v1` schema.

### Acceptance Mapping

- T1303 -> A204 for immutable draft creation, transactional activation and operation entrypoint readiness.
- T1303 -> A205 for refresh-token propagation and score recompute enqueue from the activated context.
- A204/A205 remain `IN_PROGRESS`, not `DONE`, because final release-manager activation still requires real A202 source/license/owner/legal clearance, A026/A027 production gold labels, A209 24h soak and A210 brand clearance.

### Validation

- `python -m py_compile scripts/apply_model_config.py tests/unit/test_model_config_apply.py`: PASS.
- `ruff check scripts/apply_model_config.py tests/unit/test_model_config_apply.py`: PASS after import ordering and line-length fixes.
- `pytest -q tests/unit/test_model_config_apply.py tests/unit/test_release_manager_activation.py`: PASS, 5/5.
- `python scripts/apply_model_config.py --profile config/model_profiles/supply-chain-v3.json --thresholds config/thresholds/default-v2.json --reason 'T1303/A204-A205 model config apply dry-run evidence' --dry-run`: PASS, generated `artifacts/model_config_import_preview.json`.

### Non-Closure Rules

- The dry-run artifact has `release_gate_closed_by_apply_model_config=false`.
- The CLI does not close A202, A209, A210, A026 or A027.
- Unit tests with a fake repository prove call contracts only; PostgreSQL execution remains covered by existing integration/CI paths and by any future operator `--execute` run against a real database.

### Rollback

- Revert `scripts/apply_model_config.py`, `tests/unit/test_model_config_apply.py`, Makefile lint inclusion, `artifacts/model_config_import_preview.json` and the associated governance records.
- Rerun focused T1303 tests, regenerate release artifacts and rerun `make verify`.

## 2026-06-23 - T904/A026-A027 production gold-label intake contract

Status: LOCAL VALIDATED; A026/A027 STILL IN PROGRESS UNTIL REAL PRODUCTION LABELS EXIST

### Scope

- Extended `scripts/validate_gold_quality_evaluation.py` so repository fixtures remain fail-closed by default.
- Added explicit `--allow-production-gold-set` handling for future operator-supplied production labels.
- Added required `production_gold_evidence` metadata: owner, owner role, sampling frame, labeling protocol, frozen dataset hash, reviewer, reviewer signature hash, source-license review reference, passage-review policy reference, source document refs, labeler qualification refs and fixture-exclusion booleans.
- Added tests proving production labels are rejected without the explicit flag, rejected without evidence metadata, and can close only A026/A027 quality gates when sample counts, precision and source coverage thresholds are satisfied.

### Acceptance mapping

- T904 -> A026/A027.
- A026 remains `IN_PROGRESS`: no real 50-case operator-supplied entity-resolution gold set is committed.
- A027 remains `IN_PROGRESS`: no real 100-case operator-supplied relationship gold set is committed.
- T1303 release-manager activation remains blocked because A202, A209 and A210 are still external gates.

### Parameters and formulas

- No scoring formula changed.
- No graph traversal, extraction model, model weight or threshold value changed.
- Existing thresholds remain unchanged: A026 sample >= 50 and precision >= 95.00%; A027 sample >= 100 and precision >= 90.00%; minimum source coverage = 1.00.
- Parameter profile `gold-quality-evaluation` remains `1` because threshold values did not change; this slice changes the label-intake evidence contract only.

### Validation

- `PYTHONPYCACHEPREFIX=/private/tmp/eei-gold-pycache EEI/.venv/bin/python -m py_compile EEI/scripts/validate_gold_quality_evaluation.py EEI/tests/unit/test_gold_quality_evaluation.py`: PASS.
- `PYTHONPYCACHEPREFIX=/private/tmp/eei-gold-pycache UV_CACHE_DIR=/private/tmp/eei-uv-cache EEI/.venv/bin/uv run --directory EEI pytest tests/unit/test_gold_quality_evaluation.py -q -p no:cacheprovider`: PASS, 7 passed.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache EEI/.venv/bin/ruff check EEI/scripts/validate_gold_quality_evaluation.py EEI/tests/unit/test_gold_quality_evaluation.py`: PASS.
- `PYTHONPYCACHEPREFIX=/private/tmp/eei-gold-pycache EEI/.venv/bin/python EEI/scripts/validate_gold_quality_evaluation.py generate`: PASS with `release_gate_closure_allowed=false`.
- `PYTHONPYCACHEPREFIX=/private/tmp/eei-gold-pycache EEI/.venv/bin/python EEI/scripts/validate_gold_quality_evaluation.py validate`: PASS with A026/A027 `IN_PROGRESS`.

### Remaining gaps

- Real production labels are not present.
- External source-license, passage-level, owner, legal, brand and 24h soak gates remain incomplete.
- The validator enforces required metadata, but it cannot independently verify legal authority without the external evidence files.

### Rollback

- Revert `scripts/validate_gold_quality_evaluation.py`, `tests/unit/test_gold_quality_evaluation.py`, A026/A027 artifacts and governance records.
- Regenerate development, clean-room and release artifacts, then rerun validation.

## 2026-06-23 - T905/A119-A120 migration rollback and clean-start release rehearsal

Status: LOCAL VALIDATED; REMOTE POSTGRESQL CI BINDING PENDING

### Scope

- Added `scripts/validate_t905_release_rehearsal.py` to generate and validate A119/A120 release rehearsal evidence.
- Added `tests/integration/test_database_migrations.py::test_t905_each_migration_suffix_rolls_down_and_re_upgrades` so GitHub Actions G2 PostgreSQL rehearses every migration suffix with `downgrade --steps N` followed by `upgrade`, then ends with `downgrade --all`.
- Added README clean-start commands for a new operator: bootstrap, env copy, doctor, PostgreSQL start, migration, seeds, fixtures, schema/health, `make verify-g2-db`, clean-room/release validation and database shutdown.
- Generated `artifacts/tests/a119/t905_migration_rollback_rehearsal.json` and `artifacts/tests/a120/t905_clean_start_operator_rehearsal.json`.
- Wired `validate-t905-release-rehearsal` into `make verify`.

### Acceptance mapping

- T905 -> A119/A120.
- A119 is now DONE for the migration/runbook contract; remote CI Step 10 must bind the PostgreSQL execution proof for this commit.
- A120 is now DONE for README clean-start and critical-demo reproduction contract; it does not imply public release readiness.

### Parameters and formulas

- No scoring formula changed.
- No graph traversal, extraction model, model weight, threshold or active parameter value changed.
- T905 introduces validation/runbook evidence only.

### Remaining gaps

- A202 still lacks real signed source-license review, passage-level relationship approval, production owner approval and legal release clearance.
- A026/A027 still require production human-labeled gold cases.
- A209 24h soak remains a background independent gate.
- A210 formal brand legal/market clearance or signed risk waiver is still missing.
- Release-manager activation remains blocked until the external gates above are complete.

### Rollback

- Revert the T905 validator, integration-test, README, artifacts and A119/A120/T905 governance rows.
- Regenerate development, clean-room and release artifacts, then rerun validation.

## 2026-06-23 - T1301/A202 candidate-source-anchor release bundle coverage

Status: LOCAL VALIDATED; A202 STILL IN PROGRESS

### Scope

- Extended `scripts/validate_release_decision_bundle.py` so the signed release decision bundle loads `data/golden_vertical_fact_candidates.json`.
- Added fail-closed validation that every passage-level relationship review covers the candidate's required primary and supporting source anchors.
- Updated the A202/A210 template and signed contract-test fixture to use publication-level `GV-SNAPSHOT-001..004` anchors.
- Regenerated `artifacts/tests/a202/t1301_a202_a210_release_decision_bundle_contract.json` with `candidate_source_anchor_requirements` and `candidate_source_anchor_coverage`.

### Acceptance mapping

- T1301 -> A202.
- A202 remains `IN_PROGRESS`: this proves a machine contract for evidence-chain coverage, not real source-license review, passage approval, production owner approval, legal clearance, brand clearance or relationship publication.
- A209 24h soak remains a background release gate and does not block this bounded A202 contract improvement.

### Parameters and formulas

- No scoring formula changed.
- No graph traversal, extraction model, model weight, threshold or active parameter value changed.
- The release-decision-bundle evidence contract now requires candidate source-anchor coverage before signed publication evidence can validate.

### Validation

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/private/tmp/eei-a202-anchor-pycache UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/python -m pytest -q tests/unit/test_release_decision_bundle.py -p no:cacheprovider`: PASS, 6 passed.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/private/tmp/eei-a202-anchor-pycache .venv/bin/python -m py_compile scripts/validate_release_decision_bundle.py tests/unit/test_release_decision_bundle.py`: PASS.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/ruff check scripts/validate_release_decision_bundle.py tests/unit/test_release_decision_bundle.py`: PASS.
- `.venv/bin/python scripts/validate_release_decision_bundle.py generate`: PASS.
- `.venv/bin/python scripts/validate_release_decision_bundle.py validate`: PASS.
- `.venv/bin/python scripts/validate_release_decision_bundle.py validate-bundle --template-only`: PASS with `release_ready=false`.
- `.venv/bin/python scripts/validate_release_decision_bundle.py validate-bundle --bundle tests/fixtures/release_decision_bundle/a202_a210_signed_decision_bundle_contract_test.json`: PASS with `GV-SNAPSHOT-001..004` coverage and `release_ready=false`.
- `python3 scripts/validate_information_quality.py --all --fast --fail-on-error`: PASS after recognizing explicit stale pending PR/CI/manual-rerun rationale.
- `python3 -m pytest -q tests/governance/test_project_governance_validator.py -p no:cacheprovider`: PASS, 130 passed and 4 subtests passed.

### Remaining gaps

- Real source-license review, passage-level human approval, production owner sign-off, legal/brand clearance and relationship publication are still absent.
- Production gold labels and A209 24h soak evidence remain external gates.
- The signed fixture is a contract test only and is not real clearance.

### Rollback

- Revert `scripts/validate_release_decision_bundle.py`, release-decision fixtures, `tests/unit/test_release_decision_bundle.py`, the A202 contract artifact and governance records.
- Regenerate development, clean-room and release artifacts, then rerun validation.

## 2026-06-23 - GOV-SEMANTIC-EEI-001 active parameter/formula machine binding closure

Status: LOCAL VALIDATED; RELEASE GATES STILL OPEN

### Scope

- Added motion token validation to `scripts/validate_model_config.py`.
- Bound `PARAM-052` through `PARAM-058` to `config/ui/motion-tokens.json::durations_ms`.
- Bound FORM-012 deterministic configuration lookup to machine implementation refs and evidence hash.
- Marked `GOV-SEMANTIC-EEI-001` as done and `governance/projects.yaml` semantic coverage as `machine_verified`.

### Acceptance mapping

- `GOV-SEMANTIC-EEI-001` -> `ACC-SEMANTIC-EEI-001`.
- This closes active parameter/formula machine-source coverage only.
- It does not close A026/A027 production gold labels, A202 source/legal/owner approval, A209 24h soak, A210 formal brand clearance, or release-manager activation.

### Parameters and formulas

- No runtime numeric value changed.
- Motion active values now extract from `config/ui/motion-tokens.json`: instant 80ms, local 160ms, panel 220ms, data update 280ms, lens change 320ms, reroot 380ms, full relayout max 480ms.
- FORM-012 remains a deterministic configuration lookup contract, not a scoring formula.

### Validation

- `python3 scripts/validate_semantic_extractors.py EEI`: PASS, `semantic_parameters_checked=68`, `semantic_formulas_checked=11`.
- `python3 scripts/validate_project_governance.py --project EEI --semantic`: PASS, errors 0, warnings 0.
- `.venv/bin/python scripts/validate_model_config.py config/model_profiles/balanced-v2.json config/thresholds/default-v2.json`: PASS.
- `.venv/bin/python scripts/validate_model_config.py config/model_profiles/supply-chain-v3.json config/thresholds/default-v2.json`: PASS.
- parameter registry CSV width check: PASS, 68 rows, width 34.
- `git diff --check`: PASS.

### Remaining gaps

- A026/A027 still require production human-labeled gold cases.
- A202 still requires real source-license review, passage-level approval, owner sign-off, legal clearance, and relationship publication clearance.
- A209 24h soak remains a background independent gate.
- A210 formal brand legal/market clearance or signed risk waiver remains missing.
- Release-manager activation remains blocked by the external gates above.

### Rollback

- Revert the model-config validator, parameter/formula registry, governance project status, task status, and event/ledger records.
- Regenerate governance, clean-room, and release artifacts, then rerun semantic validation.

## 2026-06-23 - T1301/A202 operator review candidate queue binding

Status: LOCAL FOCUSED VALIDATED; A202/A209/A210/A026/A027 STILL IN PROGRESS

### Scope

- Extended `scripts/validate_a202_operator_review_packet.py` so the A202 operator/legal review packet reads `data/golden_vertical_fact_candidates.json`.
- Added `relationship_candidate_review_queue` to `artifacts/tests/a202/t1301_operator_review_packet_contract.json`.
- Bound `GV-FACT-001` and `GV-FACT-002` to required official-source anchors `GV-SNAPSHOT-001..004`, with required source-license, passage-level relationship, production-owner and legal-clearance decision fields.
- Preserved fail-closed publication controls: no relationship fact publication, no graph-edge publication, no release clearance and no production approval.
- Regenerated the dependent A202/A210 release-decision bundle and T1303 release-manager activation preflight so downstream hashes remain current.

### Acceptance mapping

- T1301 -> A202.
- A202 remains `IN_PROGRESS`: this is a review handoff queue, not real source-license review, passage approval, production owner approval, legal clearance, brand clearance, relationship publication or release-manager activation.
- A209 24h soak remains a background release gate and does not block this bounded A202 review-packet hardening.

### Parameters and formulas

- No scoring formula changed.
- No graph traversal, extraction model, model weight, threshold value or active runtime parameter changed.
- `operator-review-packet` governance profile version moves from `1` to `2` because the packet now exposes candidate-level review requirements.

### Validation

- `PYTHONPYCACHEPREFIX=/private/tmp/eei-a202-pycache .venv/bin/python -m py_compile scripts/validate_a202_operator_review_packet.py tests/unit/test_official_source_live_capture.py`: PASS.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/ruff check scripts/validate_a202_operator_review_packet.py tests/unit/test_official_source_live_capture.py`: PASS.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/private/tmp/eei-a202-pycache UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/python -m pytest -q tests/unit/test_official_source_live_capture.py -p no:cacheprovider`: PASS, 13 passed.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/python scripts/validate_a202_operator_review_packet.py generate`: PASS.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/python scripts/validate_a202_operator_review_packet.py validate`: PASS.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/python scripts/validate_release_decision_bundle.py generate`: PASS.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/python scripts/validate_release_decision_bundle.py validate`: PASS.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/python scripts/validate_release_decision_bundle.py validate-bundle --bundle tests/fixtures/release_decision_bundle/a202_a210_signed_decision_bundle_contract_test.json`: PASS with `release_ready=false`.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/python scripts/validate_release_manager_activation.py generate`: PASS.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/python scripts/validate_release_manager_activation.py validate`: PASS with release-manager activation blocked.

### Remaining gaps

- Real source-license review, passage-level human approval, production owner sign-off, legal/brand clearance and relationship publication are still absent.
- Production gold labels and A209 24h soak evidence remain external gates.
- The operator review queue is machine-generated review input and cannot be treated as public-use clearance.

### Rollback

- Revert `scripts/validate_a202_operator_review_packet.py`, `tests/unit/test_official_source_live_capture.py`, the regenerated A202/A210 and T1303 preflight artifacts, and the governance records for this iteration.
- Regenerate development, clean-room and release artifacts, then rerun the A202 validation subset and root governance validation.

## 2026-06-23 - T1307/A209 operator soak monitor and recovery contract

Status: LOCAL FOCUSED VALIDATED; A209 STILL IN PROGRESS; 24H SOAK RUNNING IN BACKGROUND

### Scope

- Added `scripts/monitor_operator_soak.py` as a read-only status contract for the detached 24h operator soak.
- The monitor reads the 24h output JSON, checkpoint JSONL, PID file and log file, then reports process status, target windows, successful windows, failed windows, remaining windows, completion percent, latest successful window and a `--resume` command.
- The monitor explicitly reports `release_gate_closed_by_monitor=false` and keeps `a209_task_status_required=IN_PROGRESS`.
- Added `make monitor-operator-soak` so operators and CI-style checks can inspect progress without mutating the run.
- Extended A209 unit coverage for missing, resumable partial, failed-window and complete-summary-pending states.

### Acceptance mapping

- T1307 -> A209.
- A209 remains `IN_PROGRESS`: this monitor proves progress visibility and recovery behavior only.
- The running 24h checkpoint and output artifacts are not committed by this slice; they must be committed only after all 288 windows complete and `scripts/validate_operator_soak_evidence.py validate --require-release-ready` passes.

### Parameters and formulas

- No scoring formula changed.
- No graph traversal, extraction model, model weight, threshold value or runtime parameter changed.
- The monitor reads existing soak parameters: `soak.long_duration_hours=24` and `soak.operator_window_seconds=300`.

### Validation

- `TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/private/tmp/eei-a209-monitor-pycache .venv/bin/python -m py_compile scripts/monitor_operator_soak.py scripts/validate_operator_soak_evidence.py tests/unit/test_operator_soak_evidence.py scripts/validate_v5_production_readiness_sync.py`: PASS.
- `TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/private/tmp/eei-a209-monitor-pycache RUFF_CACHE_DIR=/private/tmp/eei-ruff-cache UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/ruff check scripts/monitor_operator_soak.py scripts/validate_operator_soak_evidence.py tests/unit/test_operator_soak_evidence.py scripts/validate_v5_production_readiness_sync.py`: PASS.
- `TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/private/tmp/eei-a209-monitor-pycache .venv/bin/python -m pytest -q tests/unit/test_operator_soak_evidence.py -p no:cacheprovider`: PASS, 8 passed.
- `TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/private/tmp/eei-a209-monitor-pycache .venv/bin/python scripts/validate_v5_production_readiness_sync.py`: PASS.
- `TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/private/tmp/eei-a209-monitor-pycache .venv/bin/python scripts/monitor_operator_soak.py --write-output /private/tmp/eei-a209-operator-soak-progress.json --quiet`: PASS; observed `RUNNING_PARTIAL`, PID `12478`, 14/288 windows and `release_gate_closed_by_monitor=false`.
- Live checkpoint inspection after monitor run observed 15/288 PASS windows, latest window `index=15`, `worker_jobs_completed=12`, `worker_jobs_total=12`, `worker_event_loop_lag_p95_ms=12.5951`.

### Remaining gaps

- Full 24h evidence is still missing until 288 successful 300-second windows complete and the final summary JSON exists.
- Release-manager activation remains blocked by A202, A209, A210 and production gold-label gates.
- If the detached process exits or a window fails, the checkpoint must be resumed or rerun and validated before any A209 closure review.

### Rollback

- Revert `scripts/monitor_operator_soak.py`, `tests/unit/test_operator_soak_evidence.py`, `Makefile`, `scripts/validate_v5_production_readiness_sync.py` and this governance record.
- Keep A209 `IN_PROGRESS`; do not remove valid partial checkpoint evidence unless it is corrupted or explicitly superseded.

## 2026-06-23 - T1307/A209 operator soak supervisor and background recovery contract

Status: LOCAL FOCUSED VALIDATED; A209 STILL IN PROGRESS; 24H SOAK RUNNING IN BACKGROUND

### Scope

- Added `scripts/supervise_operator_soak.py` as an explicit A209 background supervisor contract.
- The supervisor consumes the existing 24h progress monitor payload, observes a live PID without launching a second process, and writes `release_gate_closed_by_supervisor=false`.
- Paused runs are dry-run recovery candidates by default; actual launch requires both `--auto-resume` and `--execute`.
- Failed checkpoint windows block recovery and require operator inspection before any resume.
- Added `make supervise-operator-soak` as a safe default dry-run target and lint coverage for the supervisor.
- Extended A209 unit tests for live-process observation, explicit auto-resume requirement, dry-run recovery and failed-window blocking.

### Acceptance mapping

- T1307 -> A209.
- A209 remains `IN_PROGRESS`: supervisor evidence proves background recovery control only.
- Partial 24h checkpoints remain local runtime evidence and must not be committed or treated as release-ready until all 288 windows pass and `scripts/validate_operator_soak_evidence.py validate --require-release-ready` passes.

### Parameters and formulas

- No scoring formula changed.
- No graph traversal, extraction model, model weight, threshold value or runtime parameter changed.
- The supervisor reads existing soak parameters and command defaults: 24 hours total, 300 seconds per operator window.

### Validation

- `TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/private/tmp/eei-a209-supervisor-pycache .venv/bin/python -m py_compile scripts/supervise_operator_soak.py scripts/monitor_operator_soak.py tests/unit/test_operator_soak_evidence.py`: PASS.
- `TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/private/tmp/eei-a209-supervisor-pycache RUFF_CACHE_DIR=/private/tmp/eei-ruff-cache UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/ruff check scripts/supervise_operator_soak.py scripts/monitor_operator_soak.py tests/unit/test_operator_soak_evidence.py`: PASS.
- `TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/private/tmp/eei-a209-supervisor-pycache .venv/bin/python -m pytest -q tests/unit/test_operator_soak_evidence.py -p no:cacheprovider`: PASS, 12 passed.
- `TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/private/tmp/eei-a209-supervisor-pycache .venv/bin/python scripts/supervise_operator_soak.py --write-output /private/tmp/eei-a209-operator-soak-supervisor.json --quiet`: PASS; observed `observe_existing_run`, PID `12478`, `25/288` windows, `release_gate_closed_by_supervisor=false` and no second process launch.
- Live checkpoint inspection after supervisor dry-run observed 25/288 PASS windows, latest window `index=25`, `worker_jobs_completed=12`, `worker_jobs_total=12`, `worker_event_loop_lag_p95_ms=2.8238`.

### Remaining gaps

- Full 24h evidence is still missing until 288 successful 300-second windows complete and the final summary JSON exists.
- Release-manager activation remains blocked by A202, A209, A210 and production gold-label gates.
- The supervisor must not be run with `--execute` while the existing PID is alive; the default target intentionally dry-runs.

### Rollback

- Revert `scripts/supervise_operator_soak.py`, `tests/unit/test_operator_soak_evidence.py`, `Makefile`, `scripts/validate_v5_production_readiness_sync.py` and this governance record.
- Keep A209 `IN_PROGRESS`; do not remove valid partial checkpoint evidence unless it is corrupted or explicitly superseded.

## 2026-06-23 - T1307/A209 operator soak supervisor clean-room package binding

Status: LOCAL VALIDATED; A209 STILL IN PROGRESS; 24H SOAK RUNNING IN BACKGROUND

### Scope

- Bound `scripts/supervise_operator_soak.py` into the clean-room release package boundary via `scripts/manage_clean_room_release.py`.
- Regenerated clean-room ZIP, release evidence, checksums, manifest and directory tree so the release package includes the supervisor script.
- Preserved A209 non-closure semantics: package inclusion proves deliverability of the supervisor, not completion of the 24h soak.

### Acceptance mapping

- T1307 -> A209.
- A209 remains `IN_PROGRESS` until all 288 five-minute windows pass and the release-ready A209 validator passes.

### Validation

- `make validate-clean-room-release validate-release-artifacts`: PASS; clean-room package paths 414; release manifest paths 421; checksum paths 420.
- `make verify`: PASS; includes clean-room validation, scale benchmark operator path, soak smoke, ruff, typecheck and 77 unit tests.
- GitHub Actions `28029125423` previously failed before this binding because the clean-room ZIP missed `scripts/supervise_operator_soak.py`; this section records the local fix prepared for retry.

### Remaining gaps

- The background 24h soak remains partial runtime evidence until complete.
- A209 monitor/supervisor/package evidence must not be used as release-ready A209 closure.

## 2026-06-23 - T1307/A209 operator soak watchdog detached background recovery

Status: LOCAL FOCUSED VALIDATED; A209 STILL IN PROGRESS; 24H SOAK AND WATCHDOG RUNNING IN BACKGROUND

### Scope

- Added `scripts/watch_operator_soak.py` as an A209 watchdog layer over the existing progress monitor and supervisor.
- The watchdog runs one CI-safe dry-run cycle by default and is exposed through `make watch-operator-soak`.
- Real background recovery requires `--detach --execute --auto-resume`; it observes an existing live PID without double-starting and resumes only paused, successful checkpoints.
- Live PID staleness is detected with `stale_after_seconds=900` and reported as operator intervention required; the watchdog does not kill or replace a live process.
- Bound the watchdog into lint, `make verify`, v5 production readiness synchronization and clean-room release packaging.
- Started a detached watchdog for the current 24h run: watchdog PID `62233`, operator soak PID `12478`, `cycles=300`, `interval_seconds=300`.

### Acceptance mapping

- T1307 -> A209.
- A209 remains `IN_PROGRESS`: watchdog evidence proves background watch/recovery control only.
- Partial 24h checkpoints remain local runtime evidence and must not be committed or treated as release-ready until all 288 windows pass and `scripts/validate_operator_soak_evidence.py validate --require-release-ready` passes.

### Parameters and formulas

- No scoring formula changed.
- No graph traversal, extraction model, model weight, threshold value or runtime parameter changed.
- The watchdog uses existing soak duration/window parameters and adds no new governed model parameter; operational defaults are `interval_seconds=300` and `stale_after_seconds=900`.

### Validation

- `TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/private/tmp/eei-a209-watchdog-pycache .venv/bin/python -m py_compile scripts/watch_operator_soak.py scripts/supervise_operator_soak.py scripts/monitor_operator_soak.py tests/unit/test_operator_soak_evidence.py scripts/validate_v5_production_readiness_sync.py scripts/manage_clean_room_release.py`: PASS.
- `TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/private/tmp/eei-a209-watchdog-pycache RUFF_CACHE_DIR=/private/tmp/eei-ruff-cache UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/ruff check scripts/watch_operator_soak.py scripts/supervise_operator_soak.py scripts/monitor_operator_soak.py tests/unit/test_operator_soak_evidence.py scripts/validate_v5_production_readiness_sync.py scripts/manage_clean_room_release.py`: PASS.
- `TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/private/tmp/eei-a209-watchdog-pycache UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/python -m pytest -q tests/unit/test_operator_soak_evidence.py -p no:cacheprovider`: PASS, 16 passed.
- `TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/private/tmp/eei-a209-watchdog-pycache UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/python scripts/watch_operator_soak.py --cycles 1 --write-output /private/tmp/eei-a209-operator-soak-watchdog.json`: PASS; observed `OBSERVING_RUNNING_SOAK`, PID `12478`, `38/288` windows and `release_gate_closed_by_watchdog=false`.
- `TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/private/tmp/eei-a209-watchdog-pycache UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/python scripts/watch_operator_soak.py --detach --execute --auto-resume --cycles 300 --interval-seconds 300 --write-output /private/tmp/eei-a209-operator-soak-watchdog-detached.json`: PASS; launched detached watchdog PID `62233`.
- `/bin/ps -p 12478 -o pid=,ppid=,stat=,etime=,command=`: PASS; operator soak process running.
- `/bin/ps -p 62233 -o pid=,ppid=,stat=,etime=,command=`: PASS; watchdog process running with PPID `1`.
- `TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/private/tmp/eei-verify-pycache RUFF_CACHE_DIR=/private/tmp/eei-ruff-cache UV_CACHE_DIR=/private/tmp/eei-uv-cache make verify`: PASS; includes `watch-operator-soak`, clean-room/release validation, scale/soak smoke, secret scan, ruff, web typecheck and unit tests `81 passed`.
- Post-verify A209 supervisor check: PASS; observed `RUNNING_PARTIAL`, PID `12478`, `40/288` windows, latest window generated at `2026-06-23T13:59:27Z`, detached watchdog PID `62233` still running, and `release_gate_closed_by_supervisor=false`.

### Remaining gaps

- Full 24h evidence is still missing until 288 successful 300-second windows complete and the final summary JSON exists.
- Release-manager activation remains blocked by A202, A209, A210 and production gold-label gates.
- If the watchdog reports a stale live PID, operator intervention is required; the watchdog intentionally avoids killing live soak processes.

### Rollback

- Stop only watchdog PID `62233` if watchdog monitoring must be disabled.
- Revert `scripts/watch_operator_soak.py`, `tests/unit/test_operator_soak_evidence.py`, `Makefile`, `scripts/validate_v5_production_readiness_sync.py`, `scripts/manage_clean_room_release.py` and this governance record.
- Keep valid A209 partial checkpoints; do not remove or commit them as release-ready evidence until final validation passes.
## 2026-06-24 - T1307/A209 Background Heartbeat Evidence

- Task: `T1307`
- Acceptance IDs: `A209`
- Scope: add `scripts/record_operator_soak_heartbeat.py`, repository-local heartbeat artifact, Makefile targets, unit validation, v5 readiness sync and clean-room package inclusion.
- Current heartbeat artifact: `artifacts/tests/a209/t1307_operator_soak_background_progress.json`
- Current heartbeat state: operator PID `12478` RUNNING; watchdog PID `62233` RUNNING; `65/288` successful windows; `0` failed; `223` remaining; `22.57%` complete.
- Non-closure: `release_gate_closed_by_background_heartbeat=false`; A209 remains `IN_PROGRESS` until the 24h summary JSON exists and `scripts/validate_operator_soak_evidence.py validate --require-release-ready` passes.
- Validation: py_compile PASS; focused ruff PASS; `tests/unit/test_operator_soak_evidence.py` PASS `18/18`; heartbeat generate/validate PASS; v5 production readiness sync PASS.

## 2026-06-24 - T1303/A204-A205 Release-Manager Ready-State Validator

Status: LOCAL FOCUSED VALIDATED; A204/A205/A209/A210/A026/A027 STILL IN PROGRESS

### Scope

- Updated `scripts/validate_release_manager_activation.py` so it validates the evidence-derived release-manager preflight state instead of hard-coding repository preflight validation to `activation_ready=false`.
- Preserved the committed repository default: `artifacts/tests/a205/t1303_release_manager_activation_preflight.json` still validates as `RELEASE_MANAGER_ACTIVATION_BLOCKED`.
- Added unit coverage proving an all-real-gates fixture can validate `RELEASE_MANAGER_ACTIVATION_READY` only when A202 signed clearance, A026/A027 production gold labels, A209 24h soak and A210 brand clearance artifacts are all ready.
- Refreshed A209 repository heartbeat evidence to `65/288` successful windows, `0` failed, operator PID `12478` RUNNING and watchdog PID `62233` RUNNING.

### Acceptance mapping

- T1303 -> A204/A205.
- T1307 -> A209 heartbeat evidence only.
- A204/A205 remain `IN_PROGRESS`: this validator unblocks future final activation validation but does not activate release-manager state.
- A209 remains `IN_PROGRESS`: heartbeat evidence is background progress, not 24h release-ready evidence.
- A202, A026, A027 and A210 remain external release gates.

### Parameters and formulas

- No scoring formula changed.
- No graph traversal, extraction model, model weight, threshold value or runtime scoring parameter changed.
- Release-manager validation now uses existing gate artifacts as the source of truth for READY/BLOCKED state.

### Validation

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/private/tmp/eei-release-manager-pycache .venv/bin/python -m py_compile scripts/validate_release_manager_activation.py tests/unit/test_release_manager_activation.py`: PASS.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/private/tmp/eei-release-manager-pycache RUFF_CACHE_DIR=/private/tmp/eei-ruff-cache UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/ruff check scripts/validate_release_manager_activation.py tests/unit/test_release_manager_activation.py`: PASS.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/private/tmp/eei-release-manager-pycache UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/python -m pytest -q tests/unit/test_release_manager_activation.py -p no:cacheprovider`: PASS, 2 passed.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/private/tmp/eei-release-manager-pycache UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/python scripts/validate_release_manager_activation.py validate`: PASS, default artifact still blocked.
- `python3 scripts/record_operator_soak_heartbeat.py generate --quiet`: PASS, observed `65/288` windows.
- `python3 scripts/record_operator_soak_heartbeat.py validate --quiet`: PASS, `release_gate_closed_by_background_heartbeat=false`.
- `python3 scripts/validate_operator_soak_evidence.py validate`: PASS, `PARTIAL_OPERATOR_EVIDENCE`; `operator_24h` still missing final summary JSON.
- `python3 scripts/validate_gold_quality_evaluation.py validate`: PASS, A026/A027 remain `IN_PROGRESS`.

### Remaining gaps

- A209 must still reach all 288 successful windows and pass `scripts/validate_operator_soak_evidence.py validate --require-release-ready`.
- A026/A027 still require production human-labeled gold cases.
- A202 still requires real signed source-license review, passage-level approval, owner sign-off and legal release clearance.
- A210 formal brand legal/market clearance or signed risk waiver remains missing.

### Rollback

- Revert `scripts/validate_release_manager_activation.py`, `tests/unit/test_release_manager_activation.py`, refreshed A209 heartbeat artifact and the governance/documentation updates from this section.
- Regenerate release-manager and A209 heartbeat artifacts, then rerun focused release-manager and A209 validators.

## 2026-06-24 - T904/A026-A027 production gold-label intake template

Status: LOCAL FOCUSED VALIDATED; A026/A027 STILL IN PROGRESS UNTIL REAL PRODUCTION LABELS EXIST

### Scope

- Added `generate-template` and `validate-template` subcommands to `scripts/validate_gold_quality_evaluation.py`.
- Generated `artifacts/tests/a026/t904_a026_a027_production_gold_label_intake_template.json` as a shared A026/A027 operator-fillable template for production label evidence.
- The template binds the required `production_gold_evidence` fields, A026/A027 minimum case counts, entity-resolution case schema, relationship case schema and downstream validation commands.
- Added unit coverage proving the template is fail-closed and that threshold drift is rejected.

### Acceptance mapping

- T904 -> A026/A027.
- A026 remains `IN_PROGRESS`: the repository still has no real 50-case operator-supplied entity-resolution gold set.
- A027 remains `IN_PROGRESS`: the repository still has no real 100-case operator-supplied relationship gold set.
- The template does not close A202, A209, A210 or release-manager activation.

### Parameters and formulas

- No scoring formula changed.
- No graph traversal, extraction model, model weight or threshold value changed.
- Existing thresholds remain unchanged: A026 sample >= 50 and precision >= 95.00%; A027 sample >= 100 and precision >= 90.00%; minimum source coverage = 1.00.

### Validation

- `.venv/bin/python scripts/validate_gold_quality_evaluation.py generate-template`: PASS, generated `TEMPLATE_ONLY` artifact with `release_gate_closure_allowed=false`.
- `.venv/bin/python scripts/validate_gold_quality_evaluation.py validate-template`: PASS.
- `.venv/bin/ruff check scripts/validate_gold_quality_evaluation.py tests/unit/test_gold_quality_evaluation.py`: PASS.
- `.venv/bin/python -m pytest -q tests/unit/test_gold_quality_evaluation.py -p no:cacheprovider`: PASS, 9 passed.
- `.venv/bin/python scripts/validate_gold_quality_evaluation.py validate`: PASS, A026/A027 remain `IN_PROGRESS`.

### Remaining gaps

- Real production labels are still not present.
- External source-license, passage-level, owner, legal, brand and 24h soak gates remain incomplete.
- A209 live supervisor currently observes the background 24h soak as `RUNNING_PARTIAL`; this template does not affect A209 closure.

### Rollback

- Revert `scripts/validate_gold_quality_evaluation.py`, `tests/unit/test_gold_quality_evaluation.py`, `artifacts/tests/a026/t904_a026_a027_production_gold_label_intake_template.json` and this governance/documentation update.
- Regenerate development, clean-room and release artifacts, then rerun focused T904 validation.

## 2026-06-24 - T904/A026-A027 production gold-set fixture-ref exclusion

Status: LOCAL FOCUSED VALIDATED; A026/A027 STILL IN PROGRESS UNTIL REAL PRODUCTION LABELS EXIST

### Scope

- Hardened `scripts/validate_gold_quality_evaluation.py` so `production_gold_set=true` rejects repository fixture evidence references before A026/A027 can close.
- Rejected production gold cases whose `evidence_refs` start with `data/`, `tests/` or `fixture://`.
- Rejected `fixture_reviewer` and `fixture_*` labelers for production gold sets.
- Exposed the forbidden reference prefixes and forbidden labelers in the A026/A027 production gold-label intake template.
- Updated unit tests so the release-capable production contract-test payload uses `operator-gold-evidence:*` refs rather than copied repository fixture refs.

### Acceptance mapping

- T904 -> A026/A027.
- A026 remains `IN_PROGRESS`: no real 50-case operator-supplied entity-resolution gold set is committed.
- A027 remains `IN_PROGRESS`: no real 100-case operator-supplied relationship gold set is committed.
- This hardening does not close A202, A209, A210 or release-manager activation.

### Parameters and formulas

- No scoring formula changed.
- No graph traversal, extraction model, model weight or threshold value changed.
- Existing thresholds remain unchanged: A026 sample >= 50 and precision >= 95.00%; A027 sample >= 100 and precision >= 90.00%; minimum source coverage = 1.00.
- This is a validation-rule hardening for the existing gold-quality gate.

### Validation

- `python3 -m py_compile scripts/validate_gold_quality_evaluation.py tests/unit/test_gold_quality_evaluation.py`: PASS.
- `.venv/bin/ruff check scripts/validate_gold_quality_evaluation.py tests/unit/test_gold_quality_evaluation.py`: PASS.
- `.venv/bin/python -m pytest -q tests/unit/test_gold_quality_evaluation.py`: PASS, 11 passed.
- `.venv/bin/python scripts/validate_gold_quality_evaluation.py generate`: PASS with `release_gate_closure_allowed=false`.
- `.venv/bin/python scripts/validate_gold_quality_evaluation.py validate`: PASS with A026/A027 `IN_PROGRESS`.
- `.venv/bin/python scripts/validate_gold_quality_evaluation.py generate-template`: PASS with `TEMPLATE_ONLY`.
- `.venv/bin/python scripts/validate_gold_quality_evaluation.py validate-template`: PASS.

### Remaining gaps

- Real production labels are still not present.
- External source-license, passage-level, owner, legal, brand and 24h soak gates remain incomplete.
- A209 continues as a background 24h soak gate and is not affected by this T904 hardening.

### Rollback

- Revert `scripts/validate_gold_quality_evaluation.py`, `tests/unit/test_gold_quality_evaluation.py`, A026/A027 artifacts and this governance/documentation update.
- Regenerate clean-room and release artifacts, then rerun focused T904 validation.

## 2026-06-24 - T1309/A210 brand-clearance intake template

Status: LOCAL FOCUSED VALIDATED; A210 STILL IN PROGRESS

### Scope

- Added `generate-template`, `validate-template` and `validate-signed --bundle` subcommands to `scripts/validate_brand_clearance.py`.
- Generated `artifacts/tests/a210/t1309_brand_clearance_intake_template.json` as the operator/legal fill-in contract for formal brand legal and market clearance evidence.
- Added `tests/unit/test_brand_clearance.py` covering fail-closed template behavior, signed-bundle field requirements and non-release-ready semantics.
- Wired `validate-template` into `make verify` through `validate-brand-clearance`.

### Acceptance mapping

- T1309 -> A210.
- A210 remains `IN_PROGRESS`: the committed template is `TEMPLATE_ONLY` and does not provide legal advice, trademark availability, market clearance, signed risk waiver, public launch approval or A210 closure.

### Evidence and controls

- Required trademark knockout jurisdictions: CN, US, EU, UK and AU.
- Required market search surfaces: company name, domain, social handle, app store, GitHub, npm and PyPI.
- Required signed sections: phonetic/semantic Chinese-English review, legal-or-owner decision and final attestation.
- Signed-bundle validation can prove `a210_clearance_complete=true` for a supplied bundle but still returns `release_ready=false` until A202, A026/A027, A209 and release-manager activation are complete.

### Validation

- `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/validate_brand_clearance.py generate-template`: PASS.
- `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/validate_brand_clearance.py validate-template`: PASS.
- `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/validate_brand_clearance.py validate`: PASS.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/private/tmp/eei-a210-pycache .venv/bin/python -m pytest -q tests/unit/test_brand_clearance.py -p no:cacheprovider`: PASS, 3 passed.
- `PYTHONDONTWRITEBYTECODE=1 RUFF_CACHE_DIR=/private/tmp/eei-ruff-cache .venv/bin/ruff check scripts/validate_brand_clearance.py tests/unit/test_brand_clearance.py`: PASS.

### Remaining gaps

- Real trademark, company-name, domain, social, app-store, package-index, phonetic/semantic, legal/owner clearance evidence is not supplied.
- A202 source/legal/owner clearance, A026/A027 production gold labels, A209 24h soak and release-manager activation remain incomplete.

### Rollback

- Revert `scripts/validate_brand_clearance.py`, `tests/unit/test_brand_clearance.py`, `artifacts/tests/a210/t1309_brand_clearance_intake_template.json`, `Makefile` and this governance/documentation update.
- Regenerate development, clean-room and release artifacts, then rerun focused A210 validation.

## 2026-06-24 - T1301/A202 release-decision intake template

Status: LOCAL FOCUSED VALIDATED; A202/A209/A210/A026/A027 STILL IN PROGRESS

### Scope

- Added `generate-template`, `validate-template` and `validate-signed-intake --bundle` subcommands to `scripts/validate_release_decision_bundle.py`.
- Generated `artifacts/tests/a202/t1301_a202_release_decision_intake_template.json` as the operator/legal fill-in contract for source-license review, passage-level relationship review, production owner sign-off, legal release clearance and final attestation.
- Wired `validate-template` into `make verify` through `validate-release-decision-bundle`.
- Added unit coverage proving the committed template is fail-closed and that a complete signed A202 intake still reports `release_ready=false` until A210, A026/A027, A209 and release-manager activation are complete.

### Acceptance mapping

- T1301 -> A202.
- A202 remains `IN_PROGRESS`: the committed intake artifact is `TEMPLATE_ONLY` and does not provide source-license approval, passage-level relationship approval, production owner approval, legal clearance, relationship publication or A202 closure.
- A209 remains a background independent gate and is not replaced by A202 intake evidence.

### Parameters and formulas

- Added `PARAM-076` / `release_decision_intake.schema_version = eei-a202-release-decision-intake-v1`.
- No scoring formula, graph traversal formula, extraction model, model weight, threshold value or runtime scoring behavior changed.

### Validation

- `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/validate_release_decision_bundle.py generate-template`: PASS.
- `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/validate_release_decision_bundle.py validate-template`: PASS with `release_gate_closure_allowed=false`.
- `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/validate_release_decision_bundle.py validate`: PASS.
- `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/validate_release_decision_bundle.py validate-bundle --template-only`: PASS with `release_ready=false`.
- `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/validate_release_decision_bundle.py validate-bundle --bundle tests/fixtures/release_decision_bundle/a202_a210_signed_decision_bundle_contract_test.json`: PASS with `release_ready=false`.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/private/tmp/eei-a202-intake-pycache .venv/bin/python -m pytest -q tests/unit/test_release_decision_bundle.py -p no:cacheprovider`: PASS, 8 passed.
- `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m ruff check scripts/validate_release_decision_bundle.py tests/unit/test_release_decision_bundle.py`: PASS.

### Remaining gaps

- Real source-license reviews, passage-level approvals, production owner sign-offs and legal release clearance are still not supplied.
- A210 brand clearance, A026/A027 production gold labels, A209 24h soak and release-manager activation remain incomplete.

### Rollback

- Revert `scripts/validate_release_decision_bundle.py`, `tests/unit/test_release_decision_bundle.py`, `artifacts/tests/a202/t1301_a202_release_decision_intake_template.json`, `artifacts/tests/a202/t1301_a202_a210_release_decision_bundle_contract.json`, `Makefile` and this governance/documentation update.
- Regenerate development, clean-room and release artifacts, then rerun focused A202 release-decision validation.

## 2026-06-24 - T1303/A204-A205 release-manager A209 heartbeat context

Status: LOCAL FOCUSED VALIDATED; A204/A205/A209 STILL IN PROGRESS

### Scope

- Added `operator_soak_background_heartbeat` to `scripts/validate_release_manager_activation.py`.
- Source-hashed `artifacts/tests/a209/t1307_operator_soak_background_progress.json` into `artifacts/tests/a205/t1303_release_manager_activation_preflight.json`.
- Refreshed the A209 heartbeat to `92/288` successful windows, `0` failed, `31.94%` completion.
- Kept `counts_as_release_ready=false`, `activation_ready=false` and `release_manager_activation_allowed=false`.

### Acceptance mapping

- T1303 -> A204/A205.
- T1307 -> A209 as referenced background context only.
- A209 remains `IN_PROGRESS` until all `288/288` 24h windows and final release-ready validation pass.

### Validation

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/private/tmp/eei-release-manager-pycache .venv/bin/python -m pytest -q tests/unit/test_release_manager_activation.py -p no:cacheprovider`: PASS, 2 passed.
- `PYTHONDONTWRITEBYTECODE=1 .venv/bin/ruff check scripts/validate_release_manager_activation.py tests/unit/test_release_manager_activation.py`: PASS.
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/record_operator_soak_heartbeat.py validate --quiet`: PASS.
- `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/validate_release_manager_activation.py validate`: PASS.

### Remaining gaps

- A209 24h run is still partial: `92/288` windows at the time of this record.
- A202 source/legal/owner decisions, A210 clearance and A026/A027 production gold labels remain external release blockers.

### Rollback

- Revert `scripts/validate_release_manager_activation.py`, `tests/unit/test_release_manager_activation.py`, `artifacts/tests/a205/t1303_release_manager_activation_preflight.json`, the heartbeat refresh and generated release artifacts; keep live A209 checkpoints/logs.

## 2026-06-24 - T1302/A203 production API release preflight

Status: LOCAL FOCUSED VALIDATED; A203/A209 STILL IN PROGRESS

### Scope

- Added `scripts/validate_production_api_release_preflight.py`.
- Generated `artifacts/tests/a203/t1302_production_api_release_preflight.json`.
- Added `tests/unit/test_production_api_release_preflight.py`.
- Wired `generate-production-api-release-preflight` and `validate-production-api-release-preflight` into `Makefile`.
- Registered the preflight in `scripts/validate_v5_production_readiness_sync.py`.

### Product and functional boundary

- Covers the EEI navigation surfaces that depend on production graph/scoring/evidence APIs: 商业版图, 供应链, 资本网络, 控制关系, 证据中心, 模型中心 and 系统状态.
- Confirms the A203 API surface is present for `/v1/explore`, `/v1/paths`, `/v1/catalogs`, `/v1/scoring/explain/{objectType}/{objectId}` and `/v1/evidence/{objectType}/{objectId}`.
- Confirms scoring object-family coverage for `entity`, `theme`, `facility`, `event`, `industry`, `source_document`, `score_result`, `relationship_fact_candidate` and `relationship`.
- Keeps relationship fact candidates outside production graph edges unless A202 publication clearance is real and current.

### Acceptance mapping

- T1302 -> A203.
- T1301/A202, T1303/A204-A205 and T1307/A209 are upstream/downstream release gates referenced by this preflight.
- A203 remains `IN_PROGRESS`: `api_surface_ready=true` does not imply `release_ready=true`, graph publication, score publication, legal/source clearance, owner approval or 24h soak closure.

### Parameters and formulas

- Added `PARAM-077` / `production_api.release_preflight_schema_version = eei-t1302-a203-production-api-release-preflight-v1`.
- No scoring formula, graph traversal formula, extraction model, model weight, threshold value or runtime scoring behavior changed.
- Release readiness formula is fail-closed: A203 contract status must be DONE or RELEASE_READY, required API paths and object families must be covered, candidate publication boundary must hold, A202 relationship publication must be allowed, A204/A205 release-manager activation must be allowed and A209 24h operator soak validator must pass.

### A209 background status

- Refreshed `artifacts/tests/a209/t1307_operator_soak_background_progress.json` to `98/288` successful windows, `0` failed, `34.03%` completion.
- The detached watchdog and operator process remain the active A209 resolution path.
- Heartbeat evidence remains `counts_as_release_ready=false` and does not close A209.

### Validation

- `TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/private/tmp/eei-a203-preflight-pycache python3 -m py_compile scripts/validate_production_api_release_preflight.py tests/unit/test_production_api_release_preflight.py`: PASS.
- `TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 RUFF_CACHE_DIR=/private/tmp/eei-ruff-cache .venv/bin/ruff check scripts/validate_production_api_release_preflight.py tests/unit/test_production_api_release_preflight.py scripts/validate_v5_production_readiness_sync.py`: PASS.
- `TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/private/tmp/eei-a203-preflight-pycache .venv/bin/python -m pytest -q tests/unit/test_production_api_release_preflight.py -p no:cacheprovider`: PASS, 2 passed.
- `TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/private/tmp/eei-a203-preflight-pycache .venv/bin/python scripts/validate_production_api_release_preflight.py validate`: PASS.

### Remaining gaps

- A203 is still blocked by missing production-approved relationship publication, A202 external source/legal/owner clearance, A204/A205 release-manager activation and A209 24h operator soak evidence.
- A209 is actively running in the background but remains partial until all `288/288` windows and final release-ready validation pass.

### Rollback

- Revert `scripts/validate_production_api_release_preflight.py`, `tests/unit/test_production_api_release_preflight.py`, `artifacts/tests/a203/t1302_production_api_release_preflight.json`, `Makefile`, `scripts/validate_v5_production_readiness_sync.py` and this governance/documentation update.
- Regenerate development, clean-room and release artifacts, then rerun focused A203 and A209 heartbeat validation.

## 2026-06-24 - T1303/A204-A205 MVP release gate preflight

Status: LOCAL FOCUSED VALIDATED; MVP RELEASE BLOCKED BY EXTERNAL GATES; A209 BACKGROUND SOAK STILL RUNNING

### Scope

- Added `scripts/validate_mvp_release_gate.py`.
- Generated `artifacts/tests/a205/t1303_mvp_release_gate_preflight.json`.
- Added `tests/unit/test_mvp_release_gate.py`.
- Wired `generate-mvp-release-gate-preflight` and `validate-mvp-release-gate-preflight` into `Makefile` and `make verify`.
- Registered the new artifact in `scripts/validate_v5_production_readiness_sync.py`.

### Product and functional boundary

- This is the final v0.1 release-readiness aggregator for EEI / 商域图谱, not a production release action.
- It checks A202 relationship publication clearance, A203 production API release preflight, A204/A205 release-manager activation, A209 24h operator soak, A210 brand clearance or risk waiver, A026 entity-resolution production gold set and A027 relationship-extraction production gold set.
- It intentionally keeps `release_ready=false`, `production_publication_allowed=false`, `score_publication_allowed=false` and `public_brand_launch_allowed=false` until every required external gate is real and current.

### Acceptance mapping

- T1303 -> A204, A205.
- Upstream/downstream gates surfaced by this preflight: T1301/A202, T1302/A203, T1307/A209, T1309/A210 and T904/A026-A027.
- Every proposed closure path remains bounded by the corresponding gate artifact and Acceptance ID; templates, fixtures and A209 heartbeat progress do not count as production clearance.

### Parameters and formulas

- Added `PARAM-078` / `mvp_release_gate.preflight_schema_version = eei-t1303-mvp-release-gate-preflight-v1`.
- No scoring formula, graph traversal formula, extraction model, model weight, business threshold, route behavior or runtime scoring behavior changed.
- Release readiness formula is fail-closed: all required gate IDs must pass and no `missing_gates` rows may remain.

### A209 background status

- Background process check at `2026-06-23T19:43:25Z`: screen PID `12452`, operator PID `12478` and watchdog PID `62233` were running.
- Repository heartbeat was refreshed to `110/288` successful windows, `0` failed, `178` remaining and `38.19%` complete; the latest successful window recorded in the artifact is `operator_24h:window-110`.
- A209 remains open until the full 24h summary and checkpoint evidence pass `validate_operator_soak_evidence.py` as release-ready.

### Validation

- `python3 -m py_compile scripts/validate_mvp_release_gate.py tests/unit/test_mvp_release_gate.py`: PASS.
- focused `ruff check` for the new script/test: PASS.
- `pytest -q tests/unit/test_mvp_release_gate.py`: PASS, 2 passed.
- `scripts/validate_mvp_release_gate.py generate`: PASS; generated artifact status `MVP_RELEASE_BLOCKED` with seven explicit missing gates.
- Semantic extractor: PASS with `semantic_parameters_checked=78` and `semantic_formulas_checked=11`.
- Generated development/risk/clean-room/release artifacts after staging MVP release-gate files: PASS with `package_paths=428`, `manifest_paths=435` and `checksum_paths=434`.

### Remaining gaps

- A202 source/license/owner/legal relationship publication clearance is not supplied.
- A210 brand legal/market clearance or signed risk waiver is not supplied.
- A026/A027 production human-labeled gold sets are not supplied.
- A204/A205 release-manager activation remains blocked until every external gate is real.
- A209 24h soak is still running and has not completed `288/288` windows.

### Rollback

- Revert `scripts/validate_mvp_release_gate.py`, `tests/unit/test_mvp_release_gate.py`, `artifacts/tests/a205/t1303_mvp_release_gate_preflight.json`, `Makefile`, `scripts/validate_v5_production_readiness_sync.py` and this governance/documentation update.
- Preserve live A209 checkpoint, log and watchdog artifacts so the background soak can continue independently.


## 2026-06-24 - T1307/A209 operator soak finalization preflight

### Scope

- Added `scripts/finalize_operator_soak_evidence.py` and `artifacts/tests/a209/t1307_operator_soak_finalization_preflight.json` as the operator handoff between background soak progress and downstream release-gate regeneration.
- Added `tests/unit/test_operator_soak_finalization.py` to prove three states: partial running blocks downstream refresh, 288/288 release-ready evidence allows downstream regeneration, and failed evidence requires operator intervention.
- Wired `make generate-operator-soak-finalization-preflight`, `make validate-operator-soak-finalization-preflight`, `make verify` and v5 readiness sync to include the finalization artifact.

### Current A209 evidence

- Detached screen/operator/watchdog are still the active 24h path; this run did not stop, restart or close them.
- Repository heartbeat refreshed to `119/288` successful windows, `0` failed, `169` remaining, `41.32%` complete, operator PID `12478` RUNNING and watchdog PID `62233` RUNNING.
- Finalization artifact status is `A209_FINALIZATION_BLOCKED_RUNNING_PARTIAL`; `downstream_release_gate_refresh_allowed=false`; `release_gate_closed_by_finalizer=false`.

### Acceptance mapping

- T1307 -> A209.
- The finalizer does not satisfy A209 completion. It bounds the remaining operator procedure: keep soak running, refresh heartbeat, validate evidence, and regenerate A203/release-manager/MVP release-gate artifacts only after 288/288 release-ready evidence exists.

### Validation

- `python3 -m py_compile scripts/finalize_operator_soak_evidence.py tests/unit/test_operator_soak_finalization.py`: PASS.
- focused `ruff check scripts/finalize_operator_soak_evidence.py tests/unit/test_operator_soak_finalization.py`: PASS.
- `pytest -q tests/unit/test_operator_soak_finalization.py`: PASS, 3 passed.
- `scripts/finalize_operator_soak_evidence.py generate --refresh-upstream`: PASS; generated `A209_FINALIZATION_BLOCKED_RUNNING_PARTIAL` at `119/288`.
- Development/risk/clean-room/release artifact generation after staging finalizer files: PASS; clean-room `package_paths=434`, release `manifest_paths=441`, `checksum_paths=440`.

### Remaining gaps

- Full A209 closure still requires the 24h summary/checkpoint evidence to validate at `288/288` windows with zero failures.
- A202, A210, A026/A027 and A204/A205 remain external release blockers for MVP v0.1.

### Rollback

- Revert the finalizer script, unit tests, Makefile target, v5 sync registration, finalization artifact and governance rows. Preserve `artifacts/tests/a209/t1307_operator_soak_24h.*` and `/private/tmp/eei-operator-soak-*` so the background soak can continue independently.


## 2026-06-24 - T1303 external release evidence bundle preflight

### Scope

- Added `scripts/validate_external_release_evidence_bundle.py` and `artifacts/tests/a205/t1303_external_release_evidence_bundle_preflight.json`.
- Added `tests/unit/test_external_release_evidence_bundle.py` with blocked, ready and drift-detection coverage.
- Wired `make generate-external-release-evidence-bundle`, `make validate-external-release-evidence-bundle`, `make verify` and v5 readiness sync.

### Current evidence

- Artifact status: `EXTERNAL_RELEASE_EVIDENCE_BUNDLE_BLOCKED`.
- `external_release_evidence_ready=false`; `release_manager_preflight_refresh_allowed=false`; `mvp_release_gate_refresh_allowed=false`; `release_gate_closed_by_bundle_preflight=false`.
- Missing external inputs: A202 source/license/passage/owner/legal release, A210 brand legal/market clearance or risk waiver, A026 production entity-resolution gold set, A027 production relationship-extraction gold set, and A209 24h operator-soak finalization.

### Acceptance mapping

- T1303 -> A204/A205.
- Upstream inputs remain mapped to existing acceptance IDs: T1301/A202, T1309/A210, T904/A026-A027 and T1307/A209.
- This bundle does not close any upstream gate; it bounds the operator evidence packet required before release-manager refresh.

### Validation

- `python3 -m py_compile scripts/validate_external_release_evidence_bundle.py tests/unit/test_external_release_evidence_bundle.py`: PASS.
- focused `ruff check scripts/validate_external_release_evidence_bundle.py tests/unit/test_external_release_evidence_bundle.py`: PASS.
- `pytest -q tests/unit/test_external_release_evidence_bundle.py`: PASS, 3 passed.
- `scripts/validate_external_release_evidence_bundle.py generate`: PASS; generated `EXTERNAL_RELEASE_EVIDENCE_BUNDLE_BLOCKED`.

### Remaining gaps

- A202, A210, A026/A027 and A209 remain incomplete external gates.
- A204/A205 release-manager activation remains blocked until the external bundle, release-manager preflight and MVP release-gate preflight are all ready with real evidence.

### Rollback

- Revert the external bundle script, unit tests, Makefile targets, v5 sync registration, generated artifact and governance rows.
- Preserve live A209 checkpoint/log files and any future operator-supplied signed evidence bundles.


## 2026-06-25 - T1307/A209 current heartbeat and release preflight refresh

Status: LOCAL FOCUSED VALIDATED; A209 STILL IN PROGRESS; DOWNSTREAM RELEASE GATES STILL BLOCKED

### Scope

- Refreshed `artifacts/tests/a209/t1307_operator_soak_background_progress.json` and `artifacts/tests/a209/t1307_operator_soak_finalization_preflight.json` from the live clean-restart 24h operator soak.
- Serially regenerated `artifacts/tests/a205/t1303_external_release_evidence_bundle_preflight.json`, `artifacts/tests/a205/t1303_release_manager_activation_preflight.json`, `artifacts/tests/a203/t1302_production_api_release_preflight.json` and `artifacts/tests/a205/t1303_mvp_release_gate_preflight.json` so their `source_files` hashes bind to the latest upstream artifacts.
- No product runtime code, database schema, scoring formula, model weight, threshold, frontend route or publication policy changed.

### Current A209 evidence

- Operator PID `82041` and watchdog PID `61030` are reported RUNNING in the committed heartbeat artifact.
- Latest committed point-in-time heartbeat: `27/288` windows PASS, `0` failed, `261` remaining, `9.38%` completion.
- Finalization remains `A209_FINALIZATION_BLOCKED_RUNNING_PARTIAL`; `a209_evidence_ready_for_release_manager=false`; `downstream_release_gate_refresh_allowed=false`; `release_gate_closed_by_finalizer=false`.
- The live checkpoint may advance beyond this committed snapshot while CI runs; that is expected and remains progress-only evidence until `288/288` validates.

### Acceptance mapping

- T1307 -> A209 for background soak progress and finalization preflight.
- T1302 -> A203 for the dependent production API release preflight refresh.
- T1303 -> A204/A205 for the dependent external bundle, release-manager activation and MVP release-gate preflight refresh.
- This refresh does not close A202, A203, A204, A205, A209, A210, A026 or A027.

### Validation

- `scripts/record_operator_soak_heartbeat.py validate --quiet`: PASS.
- `scripts/finalize_operator_soak_evidence.py validate --quiet`: PASS.
- `scripts/validate_external_release_evidence_bundle.py validate`: PASS.
- `scripts/validate_release_manager_activation.py validate`: PASS.
- `scripts/validate_production_api_release_preflight.py validate`: PASS.
- `scripts/validate_mvp_release_gate.py validate`: PASS.

### Remaining gaps

- Full A209 closure still requires a 24h summary/checkpoint chain at `288/288` successful windows with zero failures and release-ready validation.
- A202 source/license/passage/owner/legal clearance, A210 formal brand clearance or waiver, A026/A027 production gold labels and release-manager activation remain incomplete external gates.

### Rollback

- Revert this heartbeat/preflight artifact refresh and governance companion records, then regenerate release artifacts from the prior heartbeat if required.
- Preserve live A209 checkpoint, PID and log files unless a failed window or stale-process condition requires explicit operator intervention.


## 2026-06-25 - T1307/A209 173/288 heartbeat remote CI binding

Status: REMOTE CI ATTESTED FOR COMMIT `edddaad16a42d7eb15c7da3b662b2ee05107a618`; A209 STILL IN PROGRESS; DOWNSTREAM RELEASE GATES STILL BLOCKED

### Scope

- Bound the committed T1307/A209 `173/288` heartbeat and dependent fail-closed release preflight refresh to GitHub Actions evidence.
- Project Governance run `28188342130` completed PASS for commit `edddaad16a42d7eb15c7da3b662b2ee05107a618`.
- EEI validation run `28188342002` completed PASS for the same commit, including static/contract/lint/typecheck/unit, G2 PostgreSQL integration, G2 browser E2E and live FastAPI PostgreSQL E2E.
- No product runtime code, database schema, scoring formula, model weight, threshold, frontend route or publication policy changed.

### Current A209 evidence

- Committed point-in-time heartbeat: `173/288` windows PASS, `0` failed, `115` remaining, `60.07%` completion.
- Live checkpoint observed after the CI-bound commit: at least `176/288` windows PASS, `0` failed.
- Finalization remains blocked until the 24h summary/checkpoint chain validates `288/288` successful windows with zero failures.

### Acceptance mapping

- T1307 -> A209 for background soak progress and finalization preflight.
- T1302 -> A203 for the dependent production API release preflight refresh.
- T1303 -> A204/A205 for the dependent external bundle, release-manager activation and MVP release-gate preflight refresh.
- This CI binding does not close A202, A203, A204, A205, A209, A210, A026 or A027.

### Validation

- Project Governance run `28188342130`: PASS.
- EEI validation run `28188342002`: PASS.
- A209 live checkpoint observation: `176/288` PASS with `0` failed; progress-only and not release-ready evidence.

### Remaining gaps

- Full A209 closure still requires a 24h summary/checkpoint chain at `288/288` successful windows with zero failures and release-ready validation.
- A202 source/license/passage/owner/legal clearance, A210 formal brand clearance or waiver, A026/A027 production gold labels and release-manager activation remain incomplete external gates.

### Rollback

- Revert this CI-binding governance evidence update and regenerate release artifacts with `remote_status=PENDING`.
- Preserve live A209 checkpoint, PID and log files unless a failed window or stale-process condition requires explicit operator intervention.


## 2026-06-25 - T1301/A202 operator review packet freshness repair

Status: LOCAL FOCUSED VALIDATED; A202 STILL IN PROGRESS; DOWNSTREAM RELEASE GATES STILL BLOCKED

### Scope

- Repaired the validator-detected hash drift between `artifacts/tests/a202/t1301_operator_review_packet_contract.json` and the current `artifacts/tests/a202/t1301_live_official_selected_capture_evidence.json`.
- Refreshed dependent A202 release-decision intake template, A202/A210 release-decision bundle and A202 signed-intake preflight after `validate-release-decision-bundle` exposed template drift.
- Refreshed dependent T1303/A205 external release-evidence bundle, operator intake packet, release-manager activation preflight and MVP release-gate preflight.
- Refreshed T1307/A209 background heartbeat and finalization preflight to the current clean-run point-in-time snapshot.
- No product runtime code, database schema, scoring formula, model weight, threshold, frontend route, legal/source clearance or publication policy changed.

### Current Evidence

- Pre-repair validation failed with `source_capture_artifact_sha256 does not match capture artifact`.
- Refreshed A202 packet validates with `status=PENDING_OWNER_LEGAL_CLEARANCE`, `relationship_fact_candidates_allowed=0`, `relationships_publishable=0` and no committed source text.
- A209 point-in-time heartbeat reports `190/288` PASS windows, `0` failed, `98` remaining and `65.97%` completion.
- A209 finalization remains `A209_FINALIZATION_BLOCKED_RUNNING_PARTIAL`; partial heartbeat evidence does not count as release-ready evidence.

### Acceptance Mapping

- T1301 -> A202 for the operator review packet freshness repair.
- T1303 -> A204/A205 for dependent external release-evidence, release-manager and MVP gate preflight refresh.
- T1307 -> A209 for the background heartbeat/finalization snapshot.
- This repair does not close A202, A204, A205, A209, A210, A026 or A027.

### Validation

- `scripts/validate_a202_operator_review_packet.py generate`: PASS.
- `scripts/validate_a202_operator_review_packet.py validate`: PASS.
- `scripts/validate_release_decision_bundle.py generate-template/generate/validate-template/validate/validate-bundle`: PASS.
- `scripts/validate_a202_signed_intake_preflight.py generate/validate`: PASS.
- `scripts/record_operator_soak_heartbeat.py generate/validate`: PASS.
- `scripts/finalize_operator_soak_evidence.py generate/validate`: PASS.
- `scripts/validate_external_release_evidence_bundle.py generate/validate/generate-packet/validate-packet`: PASS.
- `scripts/validate_release_manager_activation.py generate/validate`: PASS.
- `scripts/validate_mvp_release_gate.py generate/validate`: PASS.

### Remaining Gaps

- A202 still requires signed source-license review, passage-level relationship review, production owner sign-off, legal release clearance and final attestation.
- A210 formal brand clearance or waiver, A026/A027 production gold labels, A209 24h final evidence and release-manager activation remain incomplete external gates.

### Rollback

- Revert the refreshed A202/A205/A209 artifacts and governance companion records, then regenerate release artifacts from the previous packet hash.
- Preserve live A209 checkpoint, PID and log files unless a failed window or stale-process condition requires explicit operator intervention.


## 2026-06-26 - T1307/A209 NO_OUTPUT soak harness repair

Status: LOCAL REPAIR IN PROGRESS; A209 STILL IN PROGRESS; 24H EVIDENCE FAILED AT 7/288

### Scope

- Inspected the repository-local A209 24h checkpoint chain after the clean restart.
- Recorded the failed state: 7 checkpoint rows, 6 PASS windows, 1 FAIL window, latest generated_at `2026-06-25T22:08:58Z`.
- Window 7 failed with `child_status=NO_OUTPUT`, `exit_status=1` and Playwright `page.evaluate: Target page, context or browser has been closed`; `/private/tmp/eei-operator-soak-61143-7.json` was absent.
- Hardened `scripts/run_soak_smoke.mjs` so a long browser measurement is split into short slices, Playwright browser path can fall back to `/private/tmp/eei-ms-playwright`, browser/worker outcomes are collected with `Promise.allSettled`, and measurement errors are written into structured output.
- Hardened `scripts/run_operator_soak.mjs` so checkpoints include `browser_slices_completed` and `browser_measurement_error`.
- Hardened `scripts/watch_operator_soak.py` verification semantics with `--allow-operator-intervention-status`; the default script still exits non-zero for operator intervention, while the Makefile verification target can accept the correct fail-closed status without mutating the payload or closing A209.

### Acceptance Mapping

- T1307 -> A209 for 4h/24h soak evidence and fail-closed finalization.
- This repair does not close A209 and does not replace 24h evidence.

### Validation

- `node --check scripts/run_soak_smoke.mjs`: PASS.
- `node --check scripts/run_operator_soak.mjs`: PASS.
- `node scripts/run_soak_smoke.mjs --mode ci_smoke_slice_probe --duration-seconds 3 --browser-slice-seconds 1 --output /tmp/eei-soak-slice-probe.json --fail-on-budget --quiet`: PASS; `slices_completed=3`, `measurement_error=null`, local Playwright fallback used.
- `node scripts/run_operator_soak.mjs --mode ci_smoke_slice_probe --duration-seconds 3 --window-seconds 3 --output /tmp/eei-operator-slice-probe.json --checkpoint /tmp/eei-operator-slice-probe.checkpoints.jsonl --fail-on-budget --quiet`: PASS; `1/1` checkpoint window PASS.
- `ruff check scripts/watch_operator_soak.py tests/unit/test_operator_soak_evidence.py`: PASS.
- `.venv/bin/python -m pytest -q tests/unit/test_operator_soak_evidence.py -p no:cacheprovider`: PASS `19/19`.

### Remaining Gaps

- A209 still requires a new clean 24h run reaching `288/288` windows with zero failures and release-ready validation.
- Failed `7/288` evidence must remain incident evidence only.

### Rollback

- Revert `scripts/run_soak_smoke.mjs` and `scripts/run_operator_soak.mjs`, restore prior release artifacts/checksums, and keep the failed checkpoint/log files for incident analysis.


## 2026-06-26 - T904/A026-A027 operator labeling packet

Status: LOCAL FOCUSED VALIDATED; A026/A027 STILL IN PROGRESS

### Scope

- Added a source-bound operator labeling packet generated from the current A202 operator review packet and Golden Vertical fact candidates.
- The packet contains exactly 50 A026 entity-resolution slots and 100 A027 relationship-extraction slots.
- Each slot remains `OPERATOR_TO_LABEL` and requires operator-provided labeler, timestamp, expected/predicted fields, evidence refs and counter-evidence review.
- The packet is explicitly not a production gold set: `production_gold_set=false`, `release_gate_closure_allowed=false`, `production_claim_allowed=false`, `relationship_publication_allowed=false` and `label_payload_generated=false`.
- Bound the packet into the external release operator intake packet as supporting source evidence for A026/A027.

### Acceptance Mapping

- T904 -> A026/A027 for production gold quality evaluation readiness.
- T1303 -> A204/A205 for external release operator intake packet visibility.
- This packet does not close A026/A027; only a completed, signed, non-repository production gold label payload can do that.

### Validation

- `make generate-gold-quality-evaluation-artifacts`: PASS before governance sync.
- `make validate-gold-quality-evaluation`: PASS before governance sync.
- `.venv/bin/python -m pytest -q tests/unit/test_gold_quality_evaluation.py -p no:cacheprovider`: PASS `13/13`.
- `.venv/bin/ruff check scripts/validate_gold_quality_evaluation.py tests/unit/test_gold_quality_evaluation.py`: PASS.
- `make generate-external-release-evidence-bundle validate-external-release-evidence-bundle`: PASS before governance sync.

### Remaining Gaps

- A026 still requires at least 50 real operator-supplied human-labeled entity-resolution cases with precision >=95%.
- A027 still requires at least 100 real operator-supplied human-labeled relationship cases with precision >=90%.
- A202 source/legal/owner clearance, A209 24h soak and A210 brand clearance remain separate release gates.

### Rollback

- Revert the operator packet generator/tests and generated packet, regenerate A026/A027/A205 artifacts without the packet source, and rerun gold-quality plus external release validators.


## 2026-06-26 - T1307/A209 failed-evidence validator sync

Status: LOCAL FOCUSED VALIDATED; A209 STILL IN PROGRESS; RELEASE-READY MODE STILL BLOCKED

### Scope

- Updated `scripts/validate_operator_soak_evidence.py` so a truthfully declared failed operator run is recorded as `FAILED_OPERATOR_EVIDENCE` instead of a structural validator failure.
- Kept structural invalid evidence fail-closed: a purported PASS artifact that misses duration, window, schema, path, release-gate or worker-binding requirements still returns `FAIL`.
- Updated `scripts/record_operator_soak_heartbeat.py` so `BACKGROUND_SOAK_OPERATOR_INTERVENTION_REQUIRED` validates only when failed windows are present, the release gate remains open and the failed operator is not still claimed as running.
- Updated `scripts/finalize_operator_soak_evidence.py` so `FAILED_OPERATOR_EVIDENCE` produces `A209_FINALIZATION_OPERATOR_INTERVENTION_REQUIRED` and keeps downstream release-gate refresh blocked.
- Regenerated A209 heartbeat/evidence/finalization artifacts and dependent A203/A204/A205 release preflights from the current failed `7/288` state.

### Acceptance Mapping

- T1307 -> A209 for fail-closed 24h soak evidence validation and finalization semantics.
- T1302 -> A203 and T1303 -> A204/A205 only for dependent blocked release-preflight hash refresh.
- This does not close A209, release-manager activation, MVP release readiness, A202, A210, A026 or A027.

### Validation

- `py_compile` for A209 validator/heartbeat/finalizer/tests: PASS.
- `ruff check` for A209 validator/heartbeat/finalizer/tests: PASS.
- `.venv/bin/uv run pytest tests/unit/test_operator_soak_evidence.py tests/unit/test_operator_soak_finalization.py -q`: PASS `25/25`.
- `make generate-operator-soak-background-heartbeat generate-operator-soak-evidence-artifact generate-operator-soak-finalization-preflight validate-operator-soak-background-heartbeat validate-operator-soak-evidence validate-operator-soak-finalization-preflight`: PASS.
- `python3 scripts/validate_operator_soak_evidence.py validate --require-release-ready --quiet`: EXPECTED FAIL; the failed 24h chain is not release-ready.
- Fixed-point release artifact refresh/validation: release-manager activation, A203 production API preflight, MVP release gate, external release evidence bundle, development status, risk control, clean-room release and release artifacts all PASS.

### Current Evidence State

- `artifacts/tests/a209/t1307_operator_soak_evidence_validation.json`: `FAILED_OPERATOR_EVIDENCE`.
- `artifacts/tests/a209/t1307_operator_soak_background_progress.json`: `BACKGROUND_SOAK_OPERATOR_INTERVENTION_REQUIRED`, `6` completed windows, `1` failed window.
- `artifacts/tests/a209/t1307_operator_soak_finalization_preflight.json`: `A209_FINALIZATION_OPERATOR_INTERVENTION_REQUIRED`, `downstream_release_gate_refresh_allowed=false`.

### Remaining Gaps

- A209 still requires a fresh 24h run with `288/288` PASS windows and `0` failed windows.
- The failed canonical checkpoint remains incident evidence and must not be overwritten before being preserved.
- Background rerun evidence is not release-ready until copied into canonical artifacts and validated after completion.

### Rollback

- Revert the validator/heartbeat/finalizer semantic changes, A209 tests, regenerated A209/A203/A205/release artifacts and VERSION_MATRIX iteration update.
- Preserve failed `7/288` checkpoint/log evidence for incident analysis.


## 2026-06-26 - T1307/A209 isolated 24h rerun started

Status: BACKGROUND RERUN STARTED; A209 STILL IN PROGRESS; RELEASE-READY MODE STILL BLOCKED

### Scope

- Started a fresh detached A209 24h operator rerun under `/private/tmp/eei-a209-rerun-20260626-0918/`.
- Preserved the failed canonical `artifacts/tests/a209/t1307_operator_soak_24h.*` chain as incident evidence and did not overwrite repository-local failed evidence.
- Started the operator and watchdog against the same isolated output, checkpoint, PID and log paths.

### Acceptance Mapping

- T1307 -> A209 for 24h operator-soak evidence recovery.
- This does not close A209; completion still requires `288/288` successful windows, zero failed windows, promotion to canonical evidence and `validate_operator_soak_evidence.py validate --require-release-ready` PASS.

### Runtime Evidence

- Isolated checkpoint: `/private/tmp/eei-a209-rerun-20260626-0918/operator_soak_24h.checkpoints.jsonl`.
- First observed checkpoint: window `1/288` PASS, `0` failed, generated at `2026-06-25T23:04:42Z`, `browser_slices_completed=20`, `browser_measurement_error=null`, `worker_jobs_completed=12/12`.
- Operator PID: `80478`.
- Watchdog PID: `80732`.
- Process check: both PIDs were observed running after the first checkpoint.

### Remaining Gaps

- A209 remains open until the isolated rerun reaches `288/288` PASS windows with `0` failed and is explicitly promoted/validated.
- Host sleep, Playwright closure, browser/runtime resource pressure or stale checkpoint windows can still require operator recovery.
- `/private/tmp` evidence must be preserved before any promotion to repository-local canonical artifacts.

### Rollback

- If this isolated rerun is invalid, stop only operator PID `80478` and watchdog PID `80732` after explicit operator authorization.
- Leave the canonical failed `7/288` evidence untouched and rerun from a new isolated checkpoint path.

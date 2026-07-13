# IDS / Industrial Data System Handoff

## Purpose

IDS / Industrial Data System turns the original industrial-operations CLI prototype into a local Web + PDF industrial data and operations console. It provides dashboard views, module-specific analysis, visualization, report generation, model routing configuration, and recoverable local app launchers.

Legacy aliases such as `Wuhan Kaiming OpMe`, `OpMe`, and the Chinese legacy display name may remain only in migration notes, historical evidence, compatibility paths, or rollback context. New UI, reports, generated titles, and formal documentation should use `IDS / Industrial Data System`.

## Delivery Standard

Any future agent should preserve these standards:

- The app must start locally from `./scripts/run_local_services.sh` or the macOS click entry. Prefer the installed `.command` launcher when Gatekeeper blocks the `.app`.
- The backend health endpoint must return ok at `http://127.0.0.1:8000/api/health`.
- The frontend must load at `http://127.0.0.1:5173/`.
- Four core modules must keep working: dynamic kiln monitoring, fault diagnosis, gear repair, machining service.
- Every case should support dashboard visualization and PDF report generation.
- Missing model API keys must not block operation; offline rules must remain the fail-closed fallback.
- Formal user-facing outputs should remain PDF-first; JSON, CSV, SQLite, and Markdown are support artifacts.

## Current Architecture

- `backend/`: FastAPI service, SQLite persistence, rule analysis, model routing, PDF generation.
- `frontend/`: React + ECharts dashboard and workbench UI.
- `samples/`: small JSON/CSV inputs for demos and tests.
- `scripts/`: local service launcher, smoke test, sample report generation.
- `docs/`: handoff, cleanup, and continuity documents.
- `app_bundle/`: source macOS `.app` bundle resources and icon assets. `scripts/install_app_entries.sh` also installs `.command` launchers to Downloads and Applications.

## Runbook

```bash
./scripts/run_local_services.sh
```

Install local click entries:

```bash
./scripts/install_app_entries.sh
```

Installed entries:

- `/Applications/IDS Industrial Data System.command`
- `/Users/linzezhang/Downloads/IDS Industrial Data System.command`
- `/Applications/IDS Industrial Data System.app`
- `/Users/linzezhang/Downloads/IDS Industrial Data System.app`

Use `.command` as the primary local double-click entry. It runs the same service launcher in Terminal and avoids macOS LaunchServices/Gatekeeper silently blocking ad-hoc `.app` bundles. Keep the Terminal window open while using the app; closing it stops the local runtime.

Regenerate the macOS app icon:

```bash
.venv/bin/python scripts/generate_app_icon.py
./scripts/install_app_entries.sh
```

The tracked final assets remain `app_bundle/assets/OpMeIcon.png` and `app_bundle/assets/OpMeIcon.icns` as legacy asset paths; the intermediate `.iconset` directory is intentionally ignored.

For verification:

```bash
./scripts/smoke_test.sh
```

Quick launcher verification:

```bash
OPEN_BROWSER=0 ./scripts/run_local_services.sh
cat data/backend_port data/frontend_port
curl -fsS "http://127.0.0.1:$(cat data/backend_port)/api/health"
curl -fsS "http://127.0.0.1:$(cat data/frontend_port)/api/health"
```

If dependencies were removed during cleanup, the launcher restores them from:

- `backend/requirements.txt`
- `frontend/package-lock.json`

## GitHub Continuity Rule

All future development for this system should be synchronized into:

`LinzeColin/CodexProject`

Use the subdirectory:

`KM_IDSystem/`

Commit/PR summaries must include:

- task purpose
- changed subsystems
- validation commands and results
- remaining risks
- local files that are intentionally not tracked

## IDS v0.1 Staged Development

- Canonical worktree: `/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/KM_IDS`
- Project scope: `KM_IDSystem/` only.
- Current local state: `STAGE-039 · 重试与死信策略` Phase 1 through Phase 3 are complete; STAGE-038 remains `completed_reviewed_local`.
- Current task: `IDS-V0_1-STAGE039-P3`; acceptance: `ACC-STAGE-039`; next separate gate: `IDS-STAGE039-P4-GATE`.
- Exact source status: `SOURCE_VERIFIED`; the unique Stage039 member is `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-039_重试与死信策略.md` with SHA-256 `504caf72a6aeab67a650b4b096e728f03269f6ca8798f6e8a5c51210c8ddd7d9`.
- Corrected Phase 1 defines queue/worker separation, envelope idempotency, retry/dead-letter, backpressure, lock granularity, automatic lifecycle, crash-recovery checkpoint, and cleanup allowlist interfaces. STAGE-039..044 retain dedicated runtime policy and implementation ownership.
- A six-surface finite-state check binds batch, roadmap, entry, Phase 1, source evidence, and review evidence. Independent review repaired `1 Critical / 1 Important / 0 Minor` and ended at `0 / 0 / 0`.
- Phase 2 implements one `asyncio` in-memory queue and worker over a real Git-tracked Phase 1 control document. Submission returns before completion; STAGE-037 transitions, Chinese status, duplicate admission, bounded-capacity backpressure, and input/output/error/checkpoint fields are exercised without persistence.
- The Phase 2 smoke runs only in `ISOLATED_NON_PRODUCTION_ASYNC_CONTROL_METADATA_SLICE` mode. It creates one real isolated control job, not an IDS business job, and does not activate a production service.
- Phase 3 repairs the resource conflict domain so `ARCHIVE`, `PARSE`, `INDEX`, and `REPORT` over one input share one lock key. Active conflicts pause before queue admission; terminal records permit a later same-source job.
- The seven Phase 3 scenarios validate duplicate click, an actual isolated worker exception, external-drive-offline control gating, actual project-volume free-space insufficiency, external-API-budget insufficiency without an API call, same-source cross-operation conflict, and protected cleanup denial. Physical drive removal, disk allocation, process termination, cleanup execution, and production runtime are not claimed.
- Phase 4 delivers the exact 8-type/11-state/21-transition graph, actual isolated failure record, capacity/resource/lock backpressure proofs, a two-class cleanup allowlist, an empty automatic-recovery set, six manual-action cases, orderly isolated shutdown proof, rollback steps, and known limits.
- The Phase 4 delivery checker returns `PASS_ISOLATED_CLOSEOUT_PRODUCTION_DISABLED`; this is closeout evidence, not production readiness or whole-stage acceptance.
- Whole-stage review repaired exact contract shapes, the missing API-budget pause proof, and the false same-operation resubmission instruction; all review sources must match the Git index before `completed_reviewed_local` is valid.
- Stage039 Phase 1 publishes `ids.retry_dead_letter.v0_1.p1`. It keeps `FAILED`, `DEAD_LETTERED`, `SUCCEEDED`, and `CANCELLED` immutable; retryable failure uses `RUNNING -> RETRY_WAIT`, exhaustion uses only `RETRY_WAIT -> DEAD_LETTERED`, and permanent failure uses `RUNNING -> FAILED`.
- Retry reservation does not consume budget; only atomic eligible admission increments `retry_count`. Resource pauses consume no retry budget. Duplicate transition replay cannot consume twice.
- A terminal manual rerun creates a new owner-authorized linked job with new job/idempotency identity and lineage; the old terminal job is never reopened.
- Phase 2 supplies `ids.retry_policy.v0_1.stage039.p2` with `max_retries=2`, total-attempt limit `3`, `[5, 30]` backoff ceilings, deterministic bounded nonzero hash jitter, and an exact retryable-safe-error allowlist. These values are `ASSUMPTION`, are not production calibrated, and roll back to `NO_AUTOMATIC_RETRY`.
- The isolated slice uses one real Git-tracked Stage039 control reference, a Stage038 in-memory transport admission, and a separately derived Stage039 policy job with Stage037 candidate-only CAS transitions. The two job IDs differ, so `max_retries` remains immutable. Two due admissions increment budget once each; duplicate failure/admission replay does not increment; exhaustion reaches `DEAD_LETTERED` at `retry_count=2`.
- Input refs, empty failure output refs, safe error, actual tracked-control checkpoint digest, policy version, audit ref, and Chinese owner status are preserved without persistence.
- Phase 3 validates exactly ten isolated scenarios: duplicate retry reservation/admission, actual worker exception with process-crash recovery deferred, drive/disk/API resource pauses, same-source cross-operation locking, retry exhaustion, immutable terminal replay, owner-authorized manual-rerun candidate lineage, and five-class protected cleanup denial.
- Stage038 supplies the actual isolated worker exception and actual local disk-free observation. Phase 3 performs no process termination, physical drive removal, disk allocation, API call, cleanup/delete, production runtime, persistence, database action, raw metadata access, or fake IDS business-data use.
- Manual rerun is candidate-only and idempotent: it requires owner authorization plus a new linked job ID and idempotency key, but creates no job and writes no queue or database state. Protected cleanup verifies exact Git-tracked refs and exposes no deletion path.
- Only `IDS-V0_1-STAGE039-P4` may run next, in a separate run. Phase 3 did not enter Phase 4 or STAGE-040.
- `BATCH031_040` remains locked with `push_allowed=false`; do not upload, merge, reinstall app entries, or run batch gates before all ten stages are complete and reviewed.
- Current evidence adds `STAGE039_PHASE3_SCENARIO_VALIDATION.md`, `retry_dead_letter/stage039_retry_dead_letter_scenarios.json`, `scripts/check_retry_dead_letter_scenarios.py`, and `tests/test_stage039_retry_dead_letter_scenarios.py` to the Phase 1-2 sources.
- The real metadata root `/Users/linzezhang/Downloads/IDS_MetaData` is path-only governance context. Do not read, list, hash, open, copy, move, delete, modify, dump, scan, normalize, or commit its contents.
- Do not use fake IDS business data, fake database rows, placeholder corpus, fabricated profiles, dumps, execution logs, or evidence.

## Local Files Intentionally Not Tracked

- `.venv/`
- `frontend/node_modules/`
- `frontend/dist/`
- `.pytest_cache/`
- `__pycache__/`
- runtime SQLite/log files under `data/`
- generated PDF/ZIP artifacts under `reports/` and `outputs/`

These are recoverable from source, scripts, and GitHub.

## Known Limits

- Docker was not available on this Mac during validation, so Docker Compose syntax could not be executed locally.
- macOS may reject the ad-hoc `.app` bundle through Gatekeeper/LaunchServices. The `.command` launcher is the current reliable click path.
- Real MQTT/OPC-UA/Modbus device ingestion is not implemented in this version.
- Model providers are configurable, but no plaintext API keys should be committed.
- STAGE-039 Phase 3 is isolated scenario evidence, not production readiness. Persistent queue/claim state, measured backpressure/fairness, production lock/lease/fencing, automatic lifecycle, process crash recovery, cleanup execution, PostgreSQL actions, raw source reads, and IDS business job execution remain absent. The selected Phase 2 values remain uncalibrated assumptions and production automatic retry remains disabled.

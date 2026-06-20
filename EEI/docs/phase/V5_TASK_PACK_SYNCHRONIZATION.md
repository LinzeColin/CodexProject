# v5 Task Pack Synchronization and MVP v0.1 Blocker Map

Generated: 2026-06-20 Australia/Sydney

## Executive Summary

This file records the controlled synchronization of the v5 source package into EEI governance. It does not implement production features. It converts the v5 review findings and the user's current "still to build" list into bounded tasks, Acceptance IDs, model/runtime parameters, documentation and validation checks.

EEI identity is unchanged:

- Chinese name: 商域图谱
- English name: Enterprise Ecosystem Intelligence
- Subtitle: 企业商业版图与供应链递归探索系统
- Target repository: LinzeColin/CodexProject/EEI
- Target product release: v0.1 only after all MVP blockers below have current evidence.

## Source Evidence

| Source | Imported into EEI |
|---|---|
| `/Users/linzezhang/Downloads/US_Corporate_Power_Map_Codex_MVP_Task_Pack_v5.0_2026-06-19.zip` | User-referenced source archive name; the original zip path was not present during the 2026-06-20 sync run |
| `/Users/linzezhang/Documents/Codex/2026-06-19/current-phase-phase-0-goal-scope/work/v5_task_pack/US_Corporate_Power_Map_Codex_MVP_Task_Pack_v5.0_2026-06-19` | Extracted v5 Task Pack mirror used for current governance and development sync |
| `reviews/00_CONSOLIDATED_REVIEW.md` | 16 production blockers and merge/release decision |
| `data/review_issue_register.csv` | 40 issue rows including `OPEN_PRODUCTION`, `PARTIAL_V5` and `FIXED_IN_V5` status |
| `brand/BRAND_AND_COMPETITIVE_LANDSCAPE_RESEARCH.md` | EEI-adapted brand and market clearance summary |
| `data/competitive_product_landscape.csv` | 49 representative mature products |
| `data/brand_name_conflict_register.csv` | 7 naming conflict records |
| `TEST_STRATEGY.md` | layered static/unit/contract/integration/E2E/non-functional test strategy |
| `CONTINUITY_PLAN.md` | phase chain, issue closure and GitHub anti-drift rules |

## MVP v0.1 Blocking Scope

| Blocker | Source issue(s) | EEI task(s) | Acceptance ID(s) | Default status |
|---|---|---|---|---|
| PostgreSQL database and reversible migrations | ARCH-001 | T1300 | A201 | DONE |
| Real data ingestion, entity resolution and evidence chain | ARCH-003, UX-010 | T1301 | A202 | IN_PROGRESS |
| Production API, recursive graph query and scoring service | ARCH-002, UX-008, UX-011 | T1302 | A203 | IN_PROGRESS |
| Model config versioning, transactional activation and atomic global refresh | STRESS-010 | T1303 | A204, A205 | IN_PROGRESS |
| Scheduler, auto wake, idempotency, retry and dead-letter | STRESS-007 | T1304 | A206 | IN_PROGRESS |
| Server-side saved views, conflict control and recovery | STRESS-011 | T1305 | A207 | DONE |
| 10k, 100k and 1m relationship scale tests | STRESS-008 | T1306 | A208 | DONE |
| 4h and 24h soak tests | STRESS-012 | T1307 | A209 | IN_PROGRESS |
| Production componentized frontend, real routes and real controls | UX-003, UX-009, UX-012 | T1308 | A211 | DONE |
| Formal brand legal and market clearance | BRAND-001 and EEI user constraint | T1309 | A210 | NOT_STARTED |

## Implementation Boundaries

T1301-T1304, T1307 and T1309 remain MVP production blockers. T1300/A201 is implemented by the `0003_production_fact_version_layers` migration and its schema/integration checks. T1301/A202 is in progress through the `0004_curated_ingestion_audit_layers` and `0005_relationship_fact_candidates` migrations plus `scripts/load_curated_ingestion_anchors.py`, `scripts/publish_reviewed_relationship_facts.py`, `tests/fixtures/golden_vertical_review_decisions.json` and `tests/fixtures/golden_vertical_owner_signoff_decisions.json`; the publication script can transactionally convert explicitly reviewed candidates into `relationships`, `relationship_evidence`, `data_snapshots`, `fact_versions` and `fact_version_evidence`, and GitHub Actions run `27877209505` / job `82498609174` proves the fixture reviewed-publication path under G2 PostgreSQL integration, browser E2E and live FastAPI/PostgreSQL E2E. The new owner sign-off contract separates fixture review from production owner sign-off, requires `--allow-production-owner-signoff`, requires `owner_actor`, `owner_role`, `authority_scope` and `signature`, and persists `owner_signature_hash` into relationship qualifiers, relationship evidence and fact-version payloads; it has local static/unit evidence and still needs remote PostgreSQL CI plus an actual operator-supplied owner decision before release use. A202 is still not release-ready until live/full-text ingestion, real owner decision or second independent source closure, and source health/retry/dead-letter coverage are complete. T1302/A203 is now in progress through production context on graph/path responses, entity/event/industry/candidate fact/published relationship score explanations, event fixture PostgreSQL loading, evidence detail/source snippets, production_context `sample_candidates`, homepage `/v1/explore` production_context hydration, server-returned graph rendering, catalog inventory hydration, score explanation hydration and evidence detail hydration; GitHub Actions run `27878398112` / job `82501662399` proves the entity score explanation slice under G2 PostgreSQL integration, browser E2E and live FastAPI/PostgreSQL E2E, and GitHub Actions run `27879503435` / job `82504489377` proves the event/industry scoring slice under Step 10 G2 PostgreSQL integration, Step 11 browser E2E and Step 12 live FastAPI/PostgreSQL E2E. A203 is not closed until remaining non-relationship object scoring, formally production-approved edges and downstream release gates have current evidence. T1303/A204-A205 is in progress through `0006_model_activation_refresh_state`, `0009_transactional_outbox`, active context, transaction activation API, dedicated rollback endpoint, `POST /v1/scoring/recompute`, `POST /v1/data/snapshots/refresh`, `score_recompute` worker execution, `data_snapshot_refresh` worker execution, operation log, refresh-token stale-client semantics, inactive `supply-chain-v3` candidate profile, frontend API-first model-center hydration, activation, rollback control, recompute enqueue control, stale refresh mock E2E and live FastAPI/PostgreSQL activation/stale-refresh/rollback harness, but it is not closed until online editing, process-manager wake and 4h/24h refresh stability evidence are complete. T1304/A206 is in progress through `0007_scheduler_job_queue`, `0009_transactional_outbox`, `scripts/job_scheduler.py`, PostgreSQL integration coverage for lease, heartbeat, idempotency, retry, graceful release, expired lease recovery, dead-letter and outbox dispatch, plus `score_recompute`, `data_snapshot_refresh`, `curated_ingestion_refresh` and `calibration_run` job enqueue/execution idempotency; `apps/worker/app/main.py` exposes `health`, `once` and `supervise` worker supervisor commands, and `docker-compose.yml` now binds `postgres`, one-shot `migrate` and `worker` under the `worker` profile as the default MVP process-manager binding. T1304/A206 remains open until T1307 4h/24h soak evidence proves that binding under operator duration. T1305/A207 is closed for MVP through server-side saved views, optimistic conflict/version history/restore contracts, `0010_operation_log_actor_principal`, `X-EEI-User-Namespace`/`X-EEI-Actor` namespace isolation, cross-namespace 404 protection, the frontend API-first saved-view adapter with local fallback plus mock server E2E, 409 conflict recovery UI, a live FastAPI/PostgreSQL multisession E2E harness proven by GitHub Actions `verify-g2-db` run `27862471613` job `82460665725`, and a trusted_gateway HMAC identity mode that fails closed on missing secret, unsigned headers, invalid signatures or expired timestamps; the final trusted_gateway closure is proven by GitHub Actions run `27875473970` job `82494131119`. T1308/A211 is closed through `workspace-context.tsx`, `workspace-navigation.tsx`, `explore-api-client.ts`, `production-data-client.ts`, the 16-module EEI navigation contract, route/lens/section/planned control states, disabled unfinished entries, saved-view controls, trusted_gateway saved-view identity boundary, model-center transaction/recompute controls, live model activation/stale-refresh/rollback harness, commercial-map graph context hydration, server graph rendering, catalog/score/evidence production data panel, Objects and Scope/Industries/System Status live route coverage and GitHub Actions run `27876091338` job `82495713946` browser/live FastAPI PostgreSQL E2E proof. Each remaining task must close in a separate bounded implementation run with:

- explicit files and services changed;
- migration or rollback path where applicable;
- unit/contract/integration/E2E/performance evidence as applicable;
- updated `data/acceptance_traceability.csv`;
- updated `data/development_status_ledger.csv`;
- release evidence under `artifacts/tests/<acceptance_id>/`;
- CI evidence from GitHub before any production-ready claim.

## Default Architecture Decisions Reaffirmed

| Area | Decision for MVP v0.1 |
|---|---|
| Production database | PostgreSQL remains the system of record; facts, evidence, time validity and version pointers must be separate layers. |
| Graph query | Recursive query responses must be bounded, snapshot-scoped and evidence-bearing; large graph rendering must use server-side subgraphs, budgets and aggregation. |
| API | API responses must expose data snapshot, model config version, source state and request budget metadata. |
| Calculation | Scoring stays research-oriented; model changes activate transactionally and never auto-activate calibration proposals. |
| Cache | Cache invalidation is tied to atomic snapshot and config version switches; stale clients must see conflict/refresh semantics. |
| Search | Evidence search must preserve source, snippet, parser version, confidence, review status and counter-evidence. |
| Frontend visualization | Production frontend must be componentized with real route/state/query wiring; toast-only controls are not accepted. |
| Data ingestion | The Golden Vertical is NVIDIA-centered semiconductor and AI infrastructure, with minimum path NVIDIA -> TSMC -> ASML and at least one data-center or energy branch. |
| Background jobs | Job lease, idempotency key, heartbeat, retry cap, dead-letter and graceful shutdown are mandatory. |
| Brand | EEI remains the system name; formal legal/market clearance remains a release blocker for public brand use. |

## Rollback Procedures

| Change type | Rollback rule |
|---|---|
| Migration | `make migrate-down` must restore the prior schema for T1300 evidence; destructive data migration requires snapshot backup and restore drill. |
| Data ingestion | Disable the source connector, keep raw snapshots immutable, mark derived facts revoked/disputed rather than deleting lineage. |
| Model activation | Failed activation leaves the previous active config version and snapshot pointer unchanged. |
| Global refresh | Failed refresh keeps the previous successful snapshot visible and records the failed run in operation logs/dead-letter. |
| Saved views | Schema migrations must preserve version history or provide reversible export/import recovery. |
| Frontend route/control rollout | Incomplete controls must be disabled or marked as planned; no toast-only fake success. |
| Brand/public launch | If clearance fails, halt public launch and keep EEI internal until a cleared identity or signed waiver exists. |

## Unresolved Decisions

| Decision | Default for now | Required closure |
|---|---|---|
| Commercial data source licensing | Use public/official or explicitly licensed sources only. | Source license register before live ingestion. |
| Authn/authz boundary | Closed for A207 by `trusted_gateway` mode: production saved-view requests require HMAC-signed namespace, actor and timestamp headers and fail closed without `EEI_SAVED_VIEW_GATEWAY_SECRET`. | Future replacement with a full identity-provider middleware is allowed, but not required to close A207. |
| Large graph rendering engine | Server-side subgraph + aggregation is mandatory; client library remains benchmark-driven. | T1306 benchmark evidence. |
| Search backend | Keep evidence search contract first; engine choice remains open. | ADR before production implementation. |
| Brand clearance jurisdiction depth | Minimum CN/US/EU/UK/AU from v5. | Legal sign-off or risk waiver before public launch. |

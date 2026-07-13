# Changelog

## T705/A105-A107 transactional ingestion publication - 2026-07-13

- Added one PostgreSQL transaction for source-document fact/evidence derivation, scoring,
  seven-type change generation, active data/scoring pointer switch, outbox and audit log.
- Added fixture-only failure injection and a separate review-required failure audit;
  failed publication leaves fact/score rows, active pointers and refresh state unchanged.
- Added idempotent replay and scope/record-mode-isolated fact version chains.
- Extended `/v1/changes` and OpenAPI with old/new values, trigger source and review need.
- Added full isolated PostgreSQL integration and A105-A107 contract artifacts. T706,
  T1301/A202, A209 and MVP release readiness remain open.

## T704/A104 source freshness - 2026-07-13

- Added PostgreSQL-backed `/v1/sources/freshness` status with per-source attempt,
  success, failure, error, document and report-period fields.
- Kept connector attempt time, source-document date and SEC report period as separate
  semantics; latest report start/end remain paired to the same period.
- Connected the homepage freshness surface to the production API with explicit fixture,
  hydrated and server-error states instead of masking failed server requests.
- Added isolated PostgreSQL success/failure API integration and browser E2E coverage.
- T705-T706, T1301/A202, A209 and MVP release readiness remain open.

## T703/A102/A103 SEC fixture ingestion - 2026-07-13

- Added explicit fixture and dry-run SEC ingestion over the T702 typed normalizers.
- Added SHA-256 keyed idempotent PostgreSQL upsert for synthetic fixture source
  documents and raw snapshots; database writes require an explicit CLI opt-in.
- Added structured ingestion reports containing checkpoint, counts, status and error
  class, with failure reporting and fixture/live separation kept fail closed.
- Added an isolated PostgreSQL 16 double-upsert validator. It removes its temporary
  container/volume and proves the active A209 PostgreSQL/worker identities are unchanged.
- T704-T706, T1301/A202, A209 and MVP release readiness remain open.

## T702/A100/A101 SEC normalization - 2026-07-13

- Added typed SEC Submissions normalization for compact parallel filing arrays,
  preserving accession, form, filed/report dates, accepted timestamp, primary
  document, amendment semantics and historical file references.
- Added typed Company Facts normalization across taxonomy/concept/unit arrays,
  preserving scalar value, duration/instant period, accession, fiscal context,
  form, filed date and optional frame without collapsing same-period revisions.
- Added synthetic fixture-only golden payloads with fail-closed source-mode guards;
  fixtures cannot be relabeled `live`, invalid array alignment/dates/values fail,
  and no restatement is inferred without source evidence.
- Added A100/A101 fixture-hashed artifacts. T703-T706, T1301/A202, A209 and MVP
  release readiness remain open.

## T701/A098/A099 SEC retry and hash cache - 2026-07-13

- Added a 10-second default/30-second maximum timeout and at most three attempts
  for SEC requests, with bounded exponential backoff, bounded jitter, Retry-After
  capping, and explicit timeout/429/503 retry behavior.
- Every retry remains subject to the existing 8 request starts/second limiter;
  non-retryable statuses fail immediately and exhausted retries preserve the final
  HTTPX exception/status error.
- Added per-canonical-URL SHA-256 tracking of successful raw JSON response bytes.
  Unchanged responses set `processing_required=false`; failed or invalid JSON does
  not replace the last successful hash. The in-memory cache does not skip network
  retrieval and does not claim persistent ingestion state.
- Added mock/repeated-fixture A098/A099 artifacts. T702-T706, T1301/A202, A209 and
  MVP release readiness remain open.

## T700/A096/A097 SEC client foundation - 2026-07-13

- Added a fail-closed async SEC EDGAR client with descriptive contact-bearing
  `User-Agent` validation, exact HTTPS SEC host allowlisting, canonical CIK URL
  construction and redirects disabled.
- Added a serialized fixed-interval limiter capped at 8 request starts per second,
  with deterministic fake-clock tests and no burst allowance.
- Added mock-only A096/A097 contract artifacts and validators. No live SEC request
  was performed; T701-T706, T1301/A202, A209 and MVP release readiness remain open.

## T101/A005 PostgreSQL clean environment - 2026-07-13

- Added an isolated PostgreSQL 16 Compose clean-start validator using a dedicated
  project, container, localhost port and disposable volume.
- The first probe correctly failed its cleanup contract after the temporary
  override expired before `compose down`; only the isolated container, volume and
  network were removed manually, while the active A209 PostgreSQL and worker IDs,
  start times and health remained unchanged.
- The corrected probe passes clean-start, health, SQL identity and full teardown,
  closes T101/A005 locally, and keeps A209 plus MVP release readiness open.

## Cloudflare L2 public explorer — 2026-07-10

- 新增隔离的 `apps/cloudflare-public` 静态 explorer、Workers Static Assets 配置、隐私扫描和兼容性回归。
- 仅使用示意拓扑，不连接生产关系数据库，不关闭 A209/A210，不声明 production data publication、legal release 或 brand clearance 完成。
- build、private scan、响应式浏览器验收和 Wrangler dry-run 已通过；真实部署仍因 Workers 授权阻塞，未填写 live URL。

## 0.1.0 - 2026-06-20

- Established CodexProject canonical governance baseline under `docs/governance/`.
- Separated product version `0.1.0` from legacy Task Pack label `v4.2.0`.
- Mapped legacy model, formula, parameter, task, acceptance, risk, and release-gate evidence into validator-readable governance files.
- Converted legacy governance Markdown entrypoints into compatibility indexes to prevent duplicate editable fact sources.
- No model runtime logic, business behavior, data generation, or product feature code changed.
- `EVENT-20260627-010`: Repaired the A209 operator wall-clock budget to `measured_duration_seconds + max(180, measured_duration_seconds * 0.5)` after originmain/fd66 concurrent 300 second windows failed around 398 seconds; serialized 600 second elapsed evidence remains rejected and A209 stays `IN_PROGRESS` until fresh `288/288` zero-failure 24h evidence validates.
- Added T1307/A209 4h operator soak evidence: 48/48 checkpoint windows PASS over 14400 seconds; A209 remains open until 24h operator soak evidence and CI validation exist.
- Repaired the T1301/A202 operator-source capture fixture hash after G2 PostgreSQL CI flagged `NVDA-ANCHOR-001 source_text_sha256 does not match text`; 24h soak remains a background evidence task and does not block this fixture/CI repair.
- Added a T1301/A202 fail-closed operator/legal review packet for selected live official-source evidence; it records seven required closure gates and keeps relationship publication and legal clearance disabled.
- Closed T1304/A206 scheduler functionality independently from A209 soak: lease, auto wake, idempotency, heartbeat, retry cap, dead-letter, graceful shutdown, outbox dispatch, Docker Compose worker binding and supervisor execution are treated as DONE while 24h soak remains A209-only.
- Added a T1301/A202 plus T1309/A210 signed release decision bundle contract; it enumerates the exact source-license, passage-level, owner, legal and brand signed inputs still required, while keeping `release_ready=false` until A209 24h soak and release-manager activation are separately satisfied.
- Added a T904/A026-A027 gold-quality evaluation contract; it reports precision, recall and source coverage, but keeps A026/A027 `IN_PROGRESS` until production human-labeled gold sets meet the 50/95% entity and 100/90% relationship gates.
- Added a T904/A026-A027 production gold-label intake template artifact and validator commands; the template is `TEMPLATE_ONLY` and keeps `release_gate_closure_allowed=false`.
- Hardened the T904/A026-A027 production gold-set path so `production_gold_set=true` rejects repository fixture evidence references (`data/`, `tests/`, `fixture://`) and fixture labelers before A026/A027 can close.
- Added a T1309/A210 brand-clearance intake template and validator commands; the template covers CN/US/EU/UK/AU trademark knockout, company/domain/social/app-store/GitHub/npm/PyPI searches, phonetic/semantic review and legal/owner decision fields while keeping `release_gate_closure_allowed=false`.
- Added a T1301/A202 source-withdrawal and counter-evidence fail-closed publication rehearsal; disputed raw source snapshots, disputed evidence-chain rows and unreviewed evidence-chain counter-evidence now block reviewed relationship publication before relationship, fact-version or operation-log writes.
- Added a T1303/A204-A205 release-manager activation preflight; it aggregates A202 signed-decision, A026/A027 gold-quality, A209 soak and A210 brand-clearance evidence and fails closed while any external release gate is missing.
- Added a T905/A119-A120 release rehearsal: every PostgreSQL migration suffix now has a CI-bound rollback/re-upgrade integration test, and README clean-start commands are machine-checked against Makefile and EEI validation workflow bindings.
- Added a T1301/A202 candidate-source-anchor coverage contract for signed release decision bundles; passage-level reviews must cover `GV-SNAPSHOT-001..004` from `golden_vertical_fact_candidates.json`, while A202 remains blocked on real source/license/owner/legal evidence.
- Added a T1301/A202 release-decision intake template and validator path; the template covers source-license review, passage-level relationship review, production owner sign-off and legal release clearance fields while keeping `release_gate_closure_allowed=false`.
- Added a T1301/A202 signed-intake preflight artifact and validator; the default repository artifact reports `A202_SIGNED_INTAKE_MISSING` with five missing signed input groups and keeps `release_ready=false`.
- Closed `GOV-SEMANTIC-EEI-001` machine semantic coverage for active parameters and formulas: motion parameters now extract from `config/ui/motion-tokens.json`, FORM-012 has machine implementation refs, and production release gates remain open.
- Added a T1301/A202 operator-review candidate queue: the packet now binds `GV-FACT-001..002` to required official-source anchors `GV-SNAPSHOT-001..004` for human/legal review, while publication, legal clearance and release readiness remain fail-closed.
- Added a T1307/A209 operator-soak progress monitor: the detached 24h soak now has a read-only status contract for PID, successful windows, remaining windows, resume command and `release_gate_closed_by_monitor=false`; A209 remains open until full 24h evidence validates.
- Added a T1307/A209 operator-soak supervisor: it observes the existing 24h PID without double-starting, dry-runs recovery by default, requires explicit `--auto-resume --execute` for paused-run recovery, and keeps `release_gate_closed_by_supervisor=false`.
- Bound the A209 supervisor into clean-room release packaging and governance evidence so `scripts/supervise_operator_soak.py` is included in release artifacts while A209 remains open.
- Added a T1307/A209 operator-soak watchdog: it can run detached in the background, checks every 300 seconds, resumes only paused successful checkpoints when explicitly launched with `--execute --auto-resume`, reports stale live PIDs without killing them, and keeps `release_gate_closed_by_watchdog=false`.
- Upgraded `scripts/apply_model_config.py` from dry-run-only preview to a fail-closed T1303/A204-A205 operator CLI: `--dry-run` remains hash-bound and non-writing, while explicit `--execute` requires PostgreSQL and delegates draft creation, transactional activation and score recompute enqueue to the existing repository transaction layer.
- Added a T1307/A209 background heartbeat artifact: `scripts/record_operator_soak_heartbeat.py` records the live operator/watchdog PIDs, current 24h window progress and non-closure semantics into `artifacts/tests/a209/t1307_operator_soak_background_progress.json`; current heartbeat shows `88/288` windows PASS and keeps A209 `IN_PROGRESS`.
- Synchronized A209 heartbeat governance for CI: registered operational parameters `PARAM-069` through `PARAM-071`, refreshed clean-room release evidence to `package_paths=418`, and kept `release_gate_closed_by_background_heartbeat=false`.
- Updated the T1303/A204-A205 release-manager activation validator so it accepts evidence-derived READY preflight states only when A202, A026/A027, A209 and A210 gate artifacts are all release-ready; the committed repository preflight remains `RELEASE_MANAGER_ACTIVATION_BLOCKED`.
- Bound A209 background heartbeat into the T1303/A204-A205 release-manager preflight as source-hashed non-closure context; current heartbeat shows `92/288` windows PASS, `0` failed and `counts_as_release_ready=false`.
- Added a T1302/A203 production API release preflight; it reports `api_surface_ready=true` for the current graph/path/catalog/scoring/evidence API surface while keeping `release_ready=false`, graph publication and score publication blocked until A202, A204/A205 and A209 are release-ready.
- Refreshed the A209 background heartbeat during release-gate work to `110/288` windows PASS, `0` failed, `178` remaining and `release_gate_closed_by_background_heartbeat=false`; A209 remains an active background 24h soak gate.
- Refreshed clean-room and release artifacts after the A203 preflight files became tracked, so fresh checkouts now validate `package_paths=425` and `manifest_paths=432`.
- Added a T1303/A204-A205 MVP release-gate preflight that aggregates A202, A203, A204/A205, A209, A210 and A026/A027 into one fail-closed artifact; it reports `MVP_RELEASE_BLOCKED`, keeps every missing production gate visible, and refreshes staged clean-room/release evidence to `package_paths=428`, `manifest_paths=435` and `checksum_paths=434`.
- Added a T1307/A209 operator-soak finalization preflight: it refreshes/validates the heartbeat and evidence-validation state, reports `A209_FINALIZATION_BLOCKED_RUNNING_PARTIAL` at `119/288` windows PASS, blocks downstream release-gate refresh until 288/288 release-ready evidence exists, and keeps `release_gate_closed_by_finalizer=false`; refreshed clean-room/release evidence now reports `package_paths=434`, `manifest_paths=441` and `checksum_paths=440`.
- Added a T1303 external release-evidence bundle preflight: it consolidates A202, A210, A026, A027 and A209 gate artifacts into one fail-closed operator checklist, reports `EXTERNAL_RELEASE_EVIDENCE_BUNDLE_BLOCKED`, and keeps release-manager/MVP refresh disallowed until every external input is real and ready.
- Refreshed the live T1307/A209 background heartbeat and dependent preflight artifacts to `128/288` windows PASS, `0` failed, `160` remaining and `44.44%` complete while keeping `A209_FINALIZATION_BLOCKED_RUNNING_PARTIAL`, `release_gate_closed_by_finalizer=false` and all release gates blocked until 288/288 release-ready evidence exists.
- Added `PARAM-082` and traceability coverage for the invariant A209 heartbeat policy `counts_as_release_ready=false`, so partial heartbeat evidence cannot be misread as release closure.
- Recorded the Codex crash/local-record recovery audit: Git and Chronicle evidence survived, the old A209 run reached `135/288`, and the attempted resume failed at `2026-06-24T10:43:46Z` because the fixed Playwright browser path was missing.
- Repaired the A209 browser runtime, preserved the failed resumed chain as incident evidence, restarted a clean 24h attempt, and refreshed point-in-time working-tree heartbeat evidence to `3/288` clean-restart windows PASS with operator PID `57281` and watchdog PID `17163`.
- Fixed a T1302/T1308 workspace-layer hydration race in the production frontend: layer controls now stay disabled until `stateReady` and route through an explicit layer-to-lens mapping. Local G2 browser E2E regression and full 32-test Playwright suite pass; A203/A211 release blockers are unchanged and A209 continues in the background.

- `EVENT-20260625-001`: Hardened A202 signed-decision/signed-intake exact coverage validation for duplicate, unknown and missing candidate/source/owner inputs; release readiness remains blocked pending real clearance, gold evidence and A209.
- `EVENT-20260625-002`: Refreshed A209 clean-restart heartbeat and dependent release preflights to operator PID `82041`, watchdog PID `61030`, `9/288` windows PASS and `0` failed while keeping A209 and MVP release readiness blocked.
- `EVENT-20260625-003`: Refreshed selected A202 live official-source capture evidence to the current healthy NVIDIA official-source hashes while keeping relationship publication, legal clearance, owner sign-off, A202 closure and MVP release readiness blocked.
- `EVENT-20260625-004`: Refreshed A209 heartbeat/finalization and dependent A203/A204/A205 release preflights to `27/288` windows PASS, `0` failed and `9.38%` completion while keeping A209 and all release gates blocked.
- `EVENT-20260625-005`: Synchronized VERSION_MATRIX, governance status, clean-room package and release evidence for the A209 `27/288` heartbeat refresh while keeping delivery readiness `FAILED`.
- `EVENT-20260625-006`: Marked T1302/A203 API implementation coverage `DONE` while keeping production graph publication, score publication and MVP release readiness blocked; refreshed A209 background evidence to `35/288` windows PASS, `0` failed and `12.15%` completion.
- `EVENT-20260625-007`: Bound the T1302/A203 development-status E2E CI repair after T1302 moved to `DONE`; local `make test-e2e` passes `32/32`, and A203 remains release-blocked pending A202/A204-A205/A209/A210/A026/A027.
- `EVENT-20260625-008`: Added a T1303/A204-A205 external release operator intake packet that source-hashes required A202/A210/A026/A027/A209 inputs, validates with `WAITING_FOR_OPERATOR_INPUTS`, and keeps release-manager activation plus MVP release readiness blocked until real operator evidence is supplied.
- `EVENT-20260625-009`: Refreshed the live T1307/A209 heartbeat, finalization preflight and dependent release preflights to `135/288` windows PASS, `0` failed and `46.88%` completion while keeping A209 `IN_PROGRESS`, `release_gate_closed_by_finalizer=false` and all release gates blocked.
- `EVENT-20260625-010`: Hardened T1301/A202 signed-intake source boundaries so repository fixtures, templates, docs, config, data and tests cannot close A202; approved operator-input paths and external operator files remain the only accepted signed-intake sources, and release readiness remains blocked.
- `EVENT-20260625-014`: Bound the T1301/A202 signed-intake source-boundary hardening to commit `a246df94bf73b6fba7111805f3c5a02b6edeb070` with Project Governance run `28179389094` PASS and EEI validation run `28179389156` PASS; A202, A209 and MVP release readiness remain blocked pending real external release evidence.
- `EVENT-20260625-015`: Refreshed the live T1307/A209 heartbeat and dependent A203/A205 release preflights to `152/288` windows PASS, `0` failed and `52.78%` completion while keeping A209 finalization, release-manager activation and MVP release readiness blocked.
- `EVENT-20260625-016`: Repaired changed-only Project Governance companion coverage for the `0b552060` A209 `152/288` heartbeat refresh by updating the development ledger, traceability matrix, delivery task record and `PARAM-082` evidence narrative while keeping `counts_as_release_ready=false`.
- `EVENT-20260625-017`: Bound the A209 companion governance repair commit `842b4f0999ac3fd0d2ce4ebf023f81fd9fc5f544` to successful Project Governance run `28183575921` and EEI validation run `28183575964`; A209 remains a background gate and MVP release remains blocked.
- `EVENT-20260625-018`: Refreshed the live T1307/A209 heartbeat and dependent A203/A205 release preflights to `173/288` windows PASS, `0` failed and `60.07%` completion while keeping A209 finalization, release-manager activation and MVP release readiness blocked.
- `EVENT-20260625-019`: Bound commit `edddaad16a42d7eb15c7da3b662b2ee05107a618` to Project Governance run `28188342130` PASS and EEI validation run `28188342002` PASS; live A209 was observed at `176/288` windows PASS with `0` failed and remains progress-only evidence.
- `EVENT-20260625-021`: Bound the existing T1301/A202 operator review packet into the T1303 external release-evidence bundle and operator intake packet as source-hashed supporting evidence; A202 review readiness is now visible in A205 release preflight summaries, but source/license/passage/owner/legal clearance, release-manager activation and MVP release remain blocked.
- `EVENT-20260625-022`: Repaired stale T1301/A202 operator review packet freshness after validation found the packet hash no longer matched the current live selected official-source capture artifact; refreshed dependent A202 release-decision/signed-intake artifacts, A205 release evidence, release-manager and MVP preflights plus A209 heartbeat to `190/288` PASS while keeping every release gate blocked.
- `EVENT-20260625-023`: Bound the A202 operator review packet freshness repair commit `236d2535` to Project Governance run `28194420709` PASS and EEI validation run `28194420774` PASS; live A209 continued at `198/288` PASS with `0` failed and remains progress-only evidence.
- `EVENT-20260626-001`: Recorded the clean A209 24h run failure at `7/288` with `child_status=NO_OUTPUT`, hardened the browser soak child harness with short slices and structured measurement errors, and added a T904/A026-A027 source-bound operator labeling packet with 50 entity slots and 100 relationship slots; A209, A026 and A027 remain open.
- `EVENT-20260626-002`: Synchronized A209 failed-evidence validation semantics so the current `7/288` failed chain validates as `FAILED_OPERATOR_EVIDENCE` / `BACKGROUND_SOAK_OPERATOR_INTERVENTION_REQUIRED` / `A209_FINALIZATION_OPERATOR_INTERVENTION_REQUIRED` while `--require-release-ready` remains blocked until a fresh `288/288` zero-failure 24h run exists.
- `EVENT-20260626-003`: Started an isolated detached A209 24h rerun under `/private/tmp/eei-a209-rerun-20260626-0918/` without overwriting the failed canonical `7/288` evidence; first observed checkpoint is `1/288` PASS with `0` failed, operator PID `80478`, watchdog PID `80732`, and A209 remains open until `288/288` zero-failure release-ready validation passes.
- `EVENT-20260627-001`: Added A210 signed brand-clearance bundle source-boundary validation and A209 Playwright browser runtime parameter evidence; local short browser/operator probes pass after the runtime repair, but the active 24h rerun evidence remains failed/stale and A209 stays open.
- `EVENT-20260627-002`: Refreshed the A202/A210 release-decision bundle, A205 external release bundle, release-manager activation, MVP gate, clean-room package and release evidence after A210 preflight hash drift; local `make verify` passes with 133 unit tests while release readiness remains blocked.
- `EVENT-20260627-003`: Hardened the A209 background heartbeat so watchdog stale checkpoint observations are promoted to `BACKGROUND_SOAK_OPERATOR_INTERVENTION_REQUIRED`; the live origin/main rerun probe reports `10/288` PASS, `0` failed and remains progress-only evidence.
- `EVENT-20260627-006`: Refreshed the active origin/main A209 heartbeat to `20/288` PASS windows with `0` failed, separated healthy running-partial finalization from historical failed evidence, and bound A210 `PARAM-089` extraction to a repo-local policy value while keeping A209, release-manager activation and MVP release readiness blocked.
- `EVENT-20260627-007`: Added the EEI app icon asset pipeline and installed `EEIAppIcon.icns` into `/Applications/EEI.app`; web metadata now points to matching SVG/PNG icon assets, while A210 formal brand legal/market clearance remains blocked. During the same fixed-point sync, the active A209 origin/main rerun failed at `32/288` and remains `IN_PROGRESS` / operator-intervention required.
- `EVENT-20260627-008`: Hardened the A209 browser-soak slice runtime so short measurement slices reuse one Chromium process while still creating a fresh page per slice; the 300-second operator probe now passes with `elapsed_wall_seconds=346.5261 <= 375` after the previous attempt exposed required governance companion sync. A209 remains `IN_PROGRESS`; this is not 24h release evidence.
- `EVENT-20260627-009`: Refreshed selected A202 live official-source capture evidence for `NVDA-ANCHOR-002..004`, regenerated the A202 review packet and dependent release evidence hashes, and kept A202, A209, release-manager activation and MVP release readiness blocked.

## Legacy Task Pack v4.2.0 - 2026-06-19

- Historical EEI Task Pack and prototype governance snapshot preserved in Git history and legacy `data/*.csv` evidence inputs.
- Current counts and active governance facts must be read from `docs/governance/*`, not this changelog.

# Changelog

## IDS v0.1 STAGE-040 Phase 3 - 2026-07-13

- Added an exact-hash-bound eight-scenario contract and stdout-only checker for duplicate decisions, actual isolated worker-exception boundaries, drive/disk/API pressure, same-source cross-operation concurrency, reviewed lock conflicts, and protected cleanup denial.
- Reused the reviewed Stage038/039 isolated worker and lock evidence while keeping production locks with STAGE-041, crash recovery with STAGE-043, and cleanup execution with STAGE-044. Actual project free space is observed read-only; low disk is tested at a deterministic boundary without allocation.
- Verified fail-closed idempotency, legal pause paths, zero retry-budget consumption, zero job creation under throttle, one control lock invocation with three conflicts, and five Git-tracked protected refs with no delete path. No physical drive removal, process termination, disk allocation, API call, cleanup, persistence, database, raw metadata, fake IDS data, production, GitHub, batch gate, Phase 4, review, or app reinstall ran.

## IDS v0.1 STAGE-040 Phase 2 - 2026-07-13

- Added `ids.backpressure_policy.v0_1.stage040.p2`, a versioned isolated decision contract and standard-library checker covering queue depth, admission rate, same-type concurrency, actual project-filesystem free space, external-drive availability, API budget, observation TTL, and hysteresis.
- Registered `MOD-009`, `FORM-009`, and `PARAM-056..064` as `planned` / `PROPOSED`, linked production calibration to `TASK-OPME-B-001`, and updated total registry counts to `9/9/64` while preserving active counts `7/7/49`.
- Implemented deterministic fail-closed admit/throttle/deny/legal-pause/manual-review decisions, in-memory idempotent replay, immutable terminal handling, bounded refs, Chinese owner status, and a Phase3-only route. No queue, worker, retry scheduler, lock, resume, cleanup, persistence, database, raw metadata, fake IDS data, external API, production activation, GitHub action, batch gate, or app reinstall ran.

## IDS v0.1 STAGE-040 Phase 1 - 2026-07-13

- Bound the unique approved Stage040 taskpack member and reviewed Stage037-039 control sources into an exact-shaped metadata-only backpressure engineering contract and stdout-only checker under `ACC-STAGE-040`.
- Defined fail-closed queue soft/hard pressure, external-drive, disk, and API-budget decisions; legal pause paths; retry/idempotency/fairness invariants; restrained Chinese status; and protected partial-output cleanup boundaries.
- Deferred all numeric thresholds and scheduling parameters to a separately evidenced Phase 2, while preserving STAGE-041 lock, STAGE-042 automatic-resume, STAGE-043 crash-recovery, and STAGE-044 cleanup ownership. No runtime, database, raw metadata, fake IDS data, GitHub action, batch gate, or app reinstall ran.

## IDS v0.1 STAGE-039 Review - 2026-07-13

- Completed the local whole-stage review under `ACC-STAGE-039` and repaired four Important findings: invalid governance status/fact enums and missing calibration-task links, total registry count drift, overclaimed terminal manual-rerun job creation wording, and absent Git-index-bound review evidence.
- Registered the Stage039 policy as `planned` / `PROPOSED`, linked unresolved production calibration to `TASK-OPME-B-001`, and separated total model/formula/parameter counts `8/8/55` from active counts `7/7/49`.
- Added the fail-closed Stage039 review checker, tests, reviewed-local batch/roadmap/event evidence, and next gate `IDS-STAGE040-P1-GATE`. Production runtime, raw metadata access, fake IDS data, GitHub upload, batch gates, Stage040 execution, and app reinstall remain disabled.

## IDS v0.1 STAGE-039 Phase 4 - 2026-07-13

- Added a hash-bound Phase 4 delivery contract and stdout-only checker that expose the exact Stage037 8-type/11-state/21-transition graph, six failure decisions, and the actual isolated three-attempt retry/dead-letter history ending at `DEAD_LETTERED` with `retry_count=2`.
- Delivered five bounded capacity/resource/conflict signals, a two-class cleanup allowlist with eight protected classes, two automatically retry-eligible safe codes, zero observed successful automatic recoveries, eight manual-action cases, reviewed orderly transport shutdown, and fail-closed recovery/rollback instructions.
- Routed the only next task to the separate `IDS-V0_1-STAGE039-REVIEW` run. Production, persistence, database, raw metadata, fake IDS business data, Stage040-044 runtime ownership, whole-stage review, GitHub upload, and app reinstall remain disabled.

## IDS v0.1 STAGE-039 Phase 3 - 2026-07-13

- Added an exact-hash-bound ten-scenario contract and stdout-only checker for duplicate retry requests, worker-exception/crash boundary, drive/disk/API resource pauses, same-source cross-operation locking, retry exhaustion, immutable terminal replay, owner-authorized manual-rerun lineage, and protected cleanup denial.
- Reused the reviewed Stage038 isolated queue evidence for one actual worker exception and one actual local free-space observation. No process termination, physical drive removal, disk allocation, external API call, cleanup/delete, production runtime, persistence, or database action was performed.
- Verified that resource pauses consume no retry budget, duplicate reservation/admission replay is idempotent, exhaustion stops at `retry_count=2`, terminal jobs are not reopened, manual rerun creates only a new in-memory candidate, and five protected evidence classes remain Git-tracked and undeleted. Phase 4, Stage040+, whole-stage review, GitHub upload, and app reinstall remain separate and disabled.

## IDS v0.1 STAGE-039 Phase 2 - 2026-07-13

- Added `ids.retry_policy.v0_1.stage039.p2` with `max_retries=2`, bounded `[5, 30]` backoff ceilings, deterministic nonzero hash jitter, an exact two-code retry allowlist, default-deny unknown errors, explicit `ASSUMPTION` fact level, and production calibration still required.
- Composed the reviewed Stage038 in-memory transport admission with a separately derived Stage039 policy job and Stage037 CAS transitions, so the Stage038 `max_retries=0` job is never mutated into the Stage039 `max_retries=2` job. Retry reservation consumes no budget; failure/admission replays are idempotent; due admission increments exactly once; resource pause preserves pending retry; exhaustion follows `RUNNING -> RETRY_WAIT -> DEAD_LETTERED`.
- Recorded the tracked control input, empty failure output refs, safe error, actual checkpoint digest, Chinese owner status, rollback, and no-side-effect flags. No production service, persistence, database, raw metadata, fake IDS data, API, runtime output, GitHub action, app reinstall, Phase 3, or Stage040+ runtime ran.

## IDS v0.1 STAGE-039 Phase 1 - 2026-07-13

- Bound the unique approved Stage039 taskpack member and the reviewed Stage037/038 state/queue sources into an exact-shaped metadata-only retry/dead-letter engineering contract and stdout-only checker under `ACC-STAGE-039`; unknown root or nested contract fields fail closed.
- Defined immutable terminal states, retry budget and atomic admission semantics, exact failure classes, resource pause without budget consumption, bounded dead-letter evidence, and owner-authorized new linked jobs for terminal manual reruns.
- Deferred numeric retry/backoff/jitter/error-allowlist values to a separately evidenced Phase 2 and defaulted missing or unversioned policy to no automatic retry. No scheduler, dead-letter runtime, queue/worker, database, raw metadata, fake IDS data, GitHub action, app reinstall, or later phase ran.

## IDS v0.1 STAGE-038 Review - 2026-07-13

- Completed the local whole-stage review under `ACC-STAGE-038` and repaired four Important findings: exact contract-shape enforcement, the missing external-API-budget pause proof, false same-operation resubmission guidance, and absent Git-index-bound review evidence.
- Added a seventh isolated Phase 3 scenario that returns `PAUSED_EXTERNAL_API_BUDGET_INSUFFICIENT` without calling an API; terminal same-operation replay now remains explicitly unavailable until STAGE-039 defines retry/new-attempt policy.
- Added the Stage038 review checker, structured Stage005 review governance, reviewed-local batch/roadmap/event evidence, and the next gate `IDS-STAGE039-P1-GATE`. Production runtime, raw metadata access, fake IDS data, GitHub upload, batch gates, and app reinstall remain disabled.

## IDS v0.1 STAGE-038 Phase 4 - 2026-07-13

- Added a hash-bound Phase 4 delivery contract and stdout-only checker that expose the exact STAGE-037 job-state graph, the actual isolated failure record, capacity/resource/lock backpressure proofs, and orderly isolated shutdown evidence.
- Delivered a cleanup allowlist limited to temporary partial output and rebuildable cache, with original data, facts, manifests, evidence, report snapshots, audit logs, active indexes, and required checkpoints protected.
- Recorded `automatic_recovery_cases=[]`, six manual-action conditions, rollback steps, known limits, restrained Chinese feedback, and `PASS_ISOLATED_CLOSEOUT_PRODUCTION_DISABLED`. Whole-stage review, STAGE-039, production runtime, raw metadata access, fake IDS data, cleanup execution, GitHub, and app reinstall remain disabled.

## IDS v0.1 STAGE-038 Phase 3 - 2026-07-13

- Repaired the resource conflict identity so archive, parse, index, and report jobs over one tracked input share one lock key; active conflicts now return `RESOURCE_CONFLICT_ACTIVE` before a second queue record is created.
- Added six isolated scenarios for duplicate clicks, an actual worker exception and lock release, external-drive-offline gating, actual low-disk boundary observation without allocation, same-source cross-operation locking, and protected cleanup denial.
- Added a hash-bound Phase 3 machine contract, stdout-only checker, focused tests, and governance evidence. No physical drive removal, process termination, cleanup execution, raw metadata access, fake IDS data, production activation, GitHub upload, app reinstall, Phase 4, or whole-stage review occurred.

## IDS v0.1 STAGE-038 Phase 2 - 2026-07-13

- Added a standard-library `asyncio` in-memory queue and one isolated worker that returns submission acknowledgement before completion and processes only real Git-tracked control references.
- Reused STAGE-037 `QUEUED -> CLAIMED -> RUNNING -> SUCCEEDED/FAILED` transitions and Chinese owner projections; records now carry bounded input, output, error, checkpoint, state-history, and audit refs.
- Added idempotent duplicate admission, bounded capacity backpressure, fail-closed raw/untracked/secret rejection, and an actual worker-failure path without persisting runtime files.
- Pinned the Stage037 checker/index and Phase1 source evidence hashes in a machine contract. Production queue activation, database/schema writes, IDS_MetaData access, fake business data, GitHub, app reinstall, Phase 3, and whole-stage review remain disabled.

## IDS v0.1 STAGE-038 Phase 1 Source Reverification - 2026-07-11

- Reverified the unique approved Stage038 taskpack member and recorded the exact archive, member, roadmap, and instruction SHA-256 values under `ACC-STAGE-038`.
- Reconciled Phase 1 with the restored source: STAGE-038 now defines queue/worker separation, idempotency, retry/dead-letter, backpressure, lock, lifecycle, crash-recovery, and cleanup interfaces while STAGE-039..044 retain dedicated runtime ownership.
- Added a six-surface finite-state validator and negative cross-file mutations so mixed hashes, counts, review states, or Phase 2 authorization fail closed.
- Repaired the Phase 2/3 plan to allow a separate isolated non-production queue/worker slice and the exact source scenarios without raw metadata, fake IDS data, production activation, or runtime-ownership takeover.
- Independent review progressed from `1 Critical / 1 Important / 0 Minor` to `0 / 0 / 0`; only the next separate Phase 2 run is authorized. No Phase 2, GitHub upload, app reinstall, stage review, or batch gate ran.

## IDS v0.1 STAGE-038 Phase 1 - 2026-07-11

- Recorded the source-limited Worker queue boundary under `ACC-STAGE-038`: inherited STAGE-037/022/030 constraints and STAGE-039..044 ownership are fixed, while exact ordering, idempotency, dependency, queue-entry, and claim contracts remain unassigned.
- Recorded the absent external taskpack truthfully with no fabricated SHA-256, set `phase2_entry_authorized=false`, and routed the next run only to a P1 source-reverification gate.
- Kept queue/worker runtime, claim persistence, PostgreSQL/schema actions, raw metadata access, fake IDS data, runtime outputs, GitHub upload, app reinstall, stage review, and batch gates out of this phase.

## IDS v0.1 STAGE-037 Review - 2026-07-11

- Reviewed and repaired the STAGE-037 unified job-state engineering contract under `ACC-STAGE-037` without running a queue, worker, retry scheduler, database, cleanup action, or real IDS job.
- Added fail-closed direct and paused retry eligibility, cancellation stop reasons, `ids.job_control_envelope.v1`, distinct “暂停中” projection, structured review governance, and Git-index-bound delivery/review sources.
- Kept raw metadata content, fake IDS data, runtime outputs, GitHub upload, app reinstall, batch gates, and STAGE-038 execution out of this review.

## IDS v0.1 STAGE-036 Review - 2026-07-11

- Reviewed and repaired the STAGE-036 database-quality engineering contract under `ACC-STAGE-036` without changing product version, diagnostic models, formulas, or active parameter values.
- Added hash-pinned migration section selection, ownership-safe public-schema rollback, bounded real-data authorization queries, dependency/snapshot provenance checks, and fail-closed governance regressions.
- Kept PostgreSQL access, raw metadata access, fake IDS data, runtime outputs, GitHub upload, app reinstall, batch gates, and STAGE-037 execution out of this review.

## 1.0.0 - 2026-06-24

- Added Other8 S3PCT01 lifecycle contract coverage for dependency fail-fast entrypoints, owned launcher PID cleanup, and temporary SQLite persistence recovery.
- Added `stop_local_services.sh` and LF enforcement for OpMe shell scripts.
- Kept diagnostic formulas, LLM routing values, provider calls, and production readiness unchanged.

## 1.0.0 - 2026-06-20

- Established CodexProject governance baseline for KM_IDSystem without changing backend/frontend behavior.
- Recorded offline rule models, risk scoring formulas, LLM routing/fallback strategy, parameters, version matrix, and traceability.
- Marked engineering calibration, prompt/provider governance, and signoff evidence as UNKNOWN under `TASK-OPME-B-001`.

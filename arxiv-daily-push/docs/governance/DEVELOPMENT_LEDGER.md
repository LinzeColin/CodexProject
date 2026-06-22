# DEVELOPMENT_LEDGER

Project: `arxiv-daily-push`
Active product version: `0.12.0`
Governance spec version: `1.0.0`

The append-only machine record is `development_events.jsonl`.

## Current State

- Product version: 0.12.0
- Current phase: E
- Current gate: ADP-PHASE12-ALL-ARXIV-QUEUE-DELIVERY-PASS
- Confirmed iteration count: 47
- Reconstructed event count: 0
- Current task: ADP-PHASE12-ALL-ARXIV-QUEUE-DELIVERY-031
- Blockers: Phase 12 all-arXiv scan, candidate queue persistence, ROI ranking, daily lead selection, Release-hosted video artifact link gating, and email queue summary pass focused local tests. Production launch remains blocked by PR CI completion, owner-provisioned default-branch runner networking/TLS, durable readiness refs for `runner_ref`, `smtp_secret_ref`, `release_target_ref`, and `workflow_vars_ref`, explicit launch confirmation, default-branch Phase 12 workflow evidence, real Gmail SMTP evidence to `linzezhang35@gmail.com`, real GitHub Release video-link evidence, resource telemetry, replay/recovery evidence, 30 unique daily production entries, and explicitly disabled production variables.

## Phase Matrix

| Phase | Name | Status | Exit criteria | Evidence |
|---|---|---|---|---|
| A | Phase 1 repository foundation | completed | CLI skeleton, governance records, and tests pass | `docs/phase_records/PHASE_01.md` |
| B | Data contracts and arXiv source/ranking | completed | generic schemas and arXiv adapter/ranking gates pass | `docs/phase_records/PHASE_02.md`; `docs/phase_records/PHASE_03.md`; `docs/phase_records/PHASE_04.md` |
| C | Evidence and text lesson | completed | Claim Ledger and lesson verification pass | `docs/phase_records/PHASE_05.md`; `docs/phase_records/PHASE_06.md` |
| D | TTS/video/local pipeline/GitHub automation | completed | media gates, daily pipeline, and handoff gate pass | `docs/phase_records/PHASE_07.md`; `docs/phase_records/PHASE_08.md`; `docs/phase_records/PHASE_09.md`; `docs/phase_records/PHASE_10.md` |
| E | Weekly/monthly trial, all-arXiv queue delivery, and production handoff | completed | Phase 11 production gates plus Phase 12 all-arXiv scan, candidate queue, ROI ranking, daily lead, Release video-link email gate, and production blockers documented | `docs/phase_records/PHASE_11.md`; `docs/phase_records/PHASE_11_TRIAL_EVIDENCE_VALIDATOR.md`; `docs/phase_records/PHASE_11_PRODUCTION_PREFLIGHT.md`; `docs/phase_records/PHASE_11_LIVE_ARXIV_INGEST.md`; `docs/phase_records/PHASE_11_SMTP_DELIVERY.md`; `docs/phase_records/PHASE_11_RELEASE_DELIVERY.md`; `docs/phase_records/PHASE_11_PRODUCTION_SCHEDULER.md`; `docs/phase_records/PHASE_11_SCHEDULED_EXECUTION_DRIVER.md`; `docs/phase_records/PHASE_11_DAILY_INPUT_BUILDER.md`; `docs/phase_records/PHASE_11_TRIAL_LEDGER_UPDATE.md`; `docs/phase_records/PHASE_11_TRIAL_LEDGER_STATE.md`; `docs/phase_records/PHASE_11_TRIAL_OPS_EVIDENCE.md`; `docs/phase_records/PHASE_11_TRIAL_REPLAY_EVIDENCE.md`; `docs/phase_records/PHASE_11_TRIAL_RECOVERY_EVIDENCE.md`; `docs/phase_records/PHASE_11_TRIAL_RESOURCE_EVIDENCE.md`; `docs/phase_records/PHASE_11_TRIAL_START_GATE.md`; `docs/phase_records/PHASE_11_TRIAL_START_WORKFLOW.md`; `docs/phase_records/PHASE_11_PRODUCTION_LAUNCH_READINESS.md`; `docs/phase_records/PHASE_11_POST_MERGE_LAUNCH_AUDIT.md`; `docs/phase_records/PHASE_11_PRODUCTION_REFS_READINESS.md`; `docs/phase_records/PHASE_11_PRODUCTION_REFS_TEMPLATE.md`; `docs/phase_records/PHASE_11_PRODUCTION_REFS_GITHUB_DISCOVERY.md`; `docs/phase_records/PHASE_11_TRIAL_START_LAUNCH_PREFLIGHT.md`; `docs/phase_records/PHASE_11_PROVISIONING_AUDIT_WORKFLOW.md`; `docs/phase_records/PHASE_11_PROVISIONING_AUDIT_REVIEW.md`; `docs/phase_records/PHASE_11_TWO_DAY_SIMULATION.md`; `docs/phase_records/PHASE_12_ALL_ARXIV_QUEUE_DELIVERY.md` |

## Iteration Records

### `ITER-20260621-001`

- Date: 2026-06-21
- Fact level: EXTRACTED for created Phase 1 files and PROPOSED for future phases
- Version before: none
- Version after: 0.1.0
- Base commit: 18c3773dd5cb9d618993a5685eed7fb668349ac3
- Result commit: 4090ec69fea8fd5329eeee03a8ab842a5347b909
- Task IDs: ADP-PHASE1-FOUNDATION-001
- Goal: Start arXiv Daily Push inside CodexProject using the prepared pursuing goal baseline.
- Assumptions: Phase 1 remains foundation-only and does not implement ingest, ranking, evidence, TTS, video, runner, or SMTP transport.
- Files read: root AGENTS, governance standard, projects registry, codex-dex, project-governance skill, Phase 0 and pursuing goal preparation outputs.
- Files changed: arxiv-daily-push project files, root README, governance/projects.yaml.
- Model changes: Added MOD-ADP-001 active foundation gate and planned MOD-ADP-002/MOD-ADP-003.
- Parameter changes: Added PARAM-ADP-001 through PARAM-ADP-019.
- Commands run: `PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q`; `python3 scripts/validate_project_governance.py --project arxiv-daily-push`; `python3 scripts/validate_project_governance.py --changed-only`; `git diff --check`.
- Test results: 4 unit tests OK; project governance errors 0 warnings 0; changed-only governance errors 0 warnings 0; diff check exit 0.
- Successes: Project skeleton and governance records created.
- Failures: none recorded at file creation time.
- Decisions: Use public CodexProject path `arxiv-daily-push` and preserve future multi-source boundaries.
- Remaining risks: Later phases need environment setup and additional implementation.
- Rollback: Remove `arxiv-daily-push/` and restore `README.md` plus `governance/projects.yaml`.
- Next step: Start Phase 2 data contracts after the next run contract.

### `ITER-20260621-002`

- Date: 2026-06-21
- Fact level: EXTRACTED for Phase 2 contracts, schemas, state machine, tests, and governance updates.
- Version before: 0.1.0
- Version after: 0.2.0
- Base commit: 4090ec69fea8fd5329eeee03a8ab842a5347b909
- Result commit: PENDING
- Task IDs: ADP-PHASE2-DATA-CONTRACTS-001
- Goal: Implement generic SourceItem, EvidenceClaim, Lesson, Storyboard, Publication, and RunRecord contracts without network or media side effects.
- Assumptions: Phase 2 remains offline-only and does not implement arXiv ingest, ranking, evidence extraction, lesson generation, media generation, runner automation, or SMTP transport.
- Files changed: contract/state code, schema files, tests, README, CHANGELOG, VERSION, and governance records.
- Model changes: Added MOD-ADP-004 active generic contract and RunRecord state gate.
- Parameter changes: Added PARAM-ADP-020 through PARAM-ADP-028.
- Commands run: `PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q`; `python3 -m json.tool arxiv-daily-push/schemas/*.schema.json`.
- Test results: 13 unit tests OK; all schema JSON files parse OK.
- Successes: Generic source boundary accepts arXiv and a future GitHub source; P0 locator requirement and skipped state transitions fail closed.
- Failures: Initial `RunRecord.stages` empty-array validation failed and was fixed in `state_machine.py`.
- Decisions: Keep runtime validation dependency-free; use schemas as external contract and stdlib validators for local gates.
- Remaining risks: Phase 4 ranking and real arXiv adapter are not implemented.
- Rollback: Revert Phase 2 commit and restore version/governance records to 0.1.0.
- Next step: Start Phase 4 arXiv adapter/ranking only after final Phase 2 validation passes.

### `ITER-20260621-003`

- Date: 2026-06-21
- Fact level: EXTRACTED for arXiv adapter code, local fixture, CLI commands, tests, and governance updates.
- Version before: 0.2.0
- Version after: 0.3.0
- Base commit: e5f15384887e8e4878a228673dfb487345d1a5c1
- Result commit: PENDING
- Task IDs: ADP-PHASE3-ARXIV-ADAPTER-001
- Goal: Implement the first concrete arXiv SourceAdapter without bulk ingest or media side effects.
- Assumptions: Phase 3 validates URL construction and Atom parsing locally; live scheduled ingestion remains future work.
- Files changed: arXiv adapter code, CLI commands, fixture, tests, source config, version files, and governance records.
- Model changes: Added MOD-ADP-005 active arXiv Atom source adapter.
- Parameter changes: Added PARAM-ADP-029 through PARAM-ADP-034.
- Commands run: `PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q`.
- Test results: 19 unit tests OK.
- Successes: arXiv Atom fixture maps into generic SourceItem and validates against Phase 2 contract.
- Failures: Initial CLI indentation error was caught by tests and fixed before governance validation.
- Decisions: Keep Phase 3 tests offline and cap Phase 3 query construction at 50 results per call.
- Remaining risks: Live arXiv API availability, rate limits, and daily freshness are not yet covered by scheduler/runner gates.
- Rollback: Revert Phase 3 adapter code, tests, fixture, and governance updates.
- Next step: Start Phase 4 queue/ranking once final Phase 3 validation passes.

### `ITER-20260621-004`

- Date: 2026-06-21
- Fact level: EXTRACTED for ranking code, CLI command, local fixture, golden tests, and governance updates.
- Version before: 0.3.0
- Version after: 0.4.0
- Base commit: 8538e98f62838c1f2c1fad86f564b10838691219
- Result commit: PENDING
- Task IDs: ADP-PHASE4-RANKING-001
- Goal: Implement deterministic 100-point candidate ranking with auditable component scores and fail-closed eligibility gates.
- Assumptions: Phase 4 ranks explicit candidate inputs only and does not fetch live sources, extract claims, generate lessons, send email, or create media.
- Files changed: ranking code, CLI command, ranking fixture, ranking tests, version files, and governance records.
- Model changes: Activated MOD-ADP-002 as adp-ranking-v1.
- Parameter changes: Activated PARAM-ADP-009 through PARAM-ADP-016 as adp-ranking-parameters-v1.
- Commands run: `PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q`.
- Test results: 26 unit tests OK.
- Successes: Golden candidate scores 85.5 points; missing P0 evidence, metadata conflicts, and recent duplicate selections fail closed.
- Failures: none recorded at implementation time.
- Decisions: Use normalized 0..1 component signals multiplied by fixed weights summing to 100.
- Remaining risks: Live source freshness and automatic Claim Ledger extraction remain future gates.
- Rollback: Revert Phase 4 ranking code, tests, fixture, and governance updates.
- Next step: Start Phase 5 Claim Ledger extraction and publication gate after final Phase 4 validation passes.

### `ITER-20260621-005`

- Date: 2026-06-21
- Fact level: EXTRACTED for Claim Ledger gate code, CLI command, local fixture, tests, and governance updates.
- Version before: 0.4.0
- Version after: 0.5.0
- Base commit: 5a8034552810fb1efa2b9ff85f774180c85ac1f2
- Result commit: PENDING
- Task IDs: ADP-PHASE5-EVIDENCE-GATE-001
- Goal: Implement deterministic Claim Ledger construction and publication hard-block gates.
- Assumptions: Phase 5 consumes explicit evidence claims and does not parse PDFs, generate lesson text, send email, or create media.
- Files changed: evidence gate code, CLI command, Claim Ledger fixture, evidence gate tests, version files, and governance records.
- Model changes: Activated MOD-ADP-003 as adp-claim-gate-v1.
- Parameter changes: Activated PARAM-ADP-017 and PARAM-ADP-018 as adp-evidence-parameters-v1.
- Commands run: `PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q`.
- Test results: 32 unit tests OK.
- Successes: Missing P0 locator, unsupported P0, metadata conflict, and unsupported arXiv peer-review claims block publication.
- Failures: Initial empty `Publication.artifacts` output failed validation and was fixed by recording the Claim Ledger artifact.
- Decisions: Treat Claim Ledger as a required publication artifact before publication is ready.
- Remaining risks: Lesson generation and text-level claim coverage remain future gates.
- Rollback: Revert Phase 5 evidence gate code, tests, fixture, and governance updates.
- Next step: Start Phase 6 evidence-linked lesson generation.


### `ITER-20260621-006`

- Date: 2026-06-21
- Fact level: EXTRACTED for lesson generation code, CLI command, local fixture, tests, and governance updates.
- Version before: 0.5.0
- Version after: 0.6.0
- Base commit: 7d67c585ec1a808da23ffd0e097dddc6af617b02
- Result commit: PENDING
- Task IDs: ADP-PHASE6-LESSON-001
- Goal: Implement deterministic Chinese Lesson JSON generation from supported Claim Ledger evidence.
- Assumptions: Phase 6 remains text-only and does not synthesize narration, download models, render video, run schedulers, or send SMTP mail.
- Files changed: lesson generation code, CLI command, lesson fixture, lesson tests, version files, and governance records.
- Model changes: Activated MOD-ADP-006 as adp-lesson-v1.
- Parameter changes: Activated PARAM-ADP-035 and PARAM-ADP-036 as adp-lesson-parameters-v1.
- Commands run: `PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q`.
- Test results: 37 unit tests OK.
- Successes: Generated Lesson JSON references only supported claim IDs; unverified non-P0 claims are excluded; blocked ledgers prevent generation; unregistered section claims fail validation.
- Failures: none recorded at implementation time.
- Decisions: Use deterministic template generation with visible `[claim_id]` markers rather than model-generated free text.
- Remaining risks: Narration/TTS, media rendering, daily scheduler, Release upload, and real SMTP transport remain future gates.
- Rollback: Revert Phase 6 lesson code, tests, fixture, and governance updates.
- Next step: Start Phase 7 narration/TTS dry-run and resource gate.


### `ITER-20260621-007`

- Date: 2026-06-21
- Fact level: EXTRACTED for narration dry-run code, CLI command, schema, local fixture, tests, and governance updates.
- Version before: 0.6.0
- Version after: 0.7.0
- Base commit: 847652080c949a6678231677409de9d9dbb96989
- Result commit: PENDING
- Task IDs: ADP-PHASE7-TTS-001
- Goal: Implement narration/TTS-ready dry-run JSON and resource gates without audio synthesis or retained media.
- Assumptions: Phase 7 remains dry-run only and does not download models, synthesize voice, write audio files, render video, run schedulers, or send SMTP mail.
- Files changed: narration dry-run code, CLI command, narration schema, narration fixture, tests, version files, and governance records.
- Model changes: Activated MOD-ADP-007 as adp-narration-v1.
- Parameter changes: Activated PARAM-ADP-037 through PARAM-ADP-040 as adp-narration-parameters-v1.
- Commands run: `PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q`.
- Test results: 42 unit tests OK.
- Successes: Dry-run narration plan maps Lesson sections to segments, real TTS mode is blocked, audio paths are rejected, and runtime parameters expose real synthesis disabled.
- Failures: none recorded at implementation time.
- Decisions: Keep Phase 7 artifact as JSON only and defer any media writes until later resource gates pass.
- Remaining risks: Video rendering, daily scheduler, Release upload, and real SMTP transport remain future gates.
- Rollback: Revert Phase 7 narration code, schema, tests, fixture, and governance updates.
- Next step: Start Phase 8 video/storyboard dry-run and media QA gate.


### `ITER-20260621-008`

- Date: 2026-06-21
- Fact level: EXTRACTED for storyboard/video dry-run code, CLI command, fixture, tests, and governance updates.
- Version before: 0.7.0
- Version after: 0.8.0
- Base commit: 7332df2c5abed8aefbf694afe839ac496efafe06
- Result commit: PENDING
- Task IDs: ADP-PHASE8-VIDEO-001
- Goal: Implement Storyboard dry-run and video media gate without rendering or retained media.
- Assumptions: Phase 8 remains dry-run only and does not render video, write media, download assets, run schedulers, or send SMTP mail.
- Files changed: video dry-run code, CLI command, video fixture, tests, version files, and governance records.
- Model changes: Activated MOD-ADP-008 as adp-video-dry-run-v1.
- Parameter changes: Activated PARAM-ADP-041 through PARAM-ADP-044 as adp-video-parameters-v1.
- Commands run: `PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q`.
- Test results: 47 unit tests OK.
- Successes: Storyboard dry-run maps narration segments to scenes, media gate blocks real rendering/writes/downloads, media paths are rejected, and scene claims must stay inside narration claims.
- Failures: none recorded at implementation time.
- Decisions: Keep Phase 8 artifact as JSON storyboard only and defer real video rendering until resource gates pass.
- Remaining risks: Local pipeline orchestration, Release upload, runner scheduling, and real SMTP transport remain future gates.
- Rollback: Revert Phase 8 video dry-run code, tests, fixture, and governance updates.
- Next step: Start Phase 9 local daily pipeline dry-run.

### `ITER-20260621-009`

- Date: 2026-06-21
- Fact level: EXTRACTED for local dry-run pipeline code, CLI command, fixture, tests, and governance updates.
- Version before: 0.8.0
- Version after: 0.9.0
- Base commit: 8eda3772f881a0aaaa388c3c488de7e3a0ef773c
- Result commit: PENDING
- Task IDs: ADP-PHASE9-LOCAL-PIPELINE-001
- Goal: Implement local daily dry-run orchestration through completed RunRecord and email preview.
- Assumptions: Phase 9 remains manual dry-run only and does not schedule runs, upload Releases, send SMTP mail, or retain media.
- Test results: 51 unit tests OK.
- Next step: Start Phase 10 runner/release/email dry-run handoff.

### `ITER-20260621-010`

- Date: 2026-06-21
- Fact level: EXTRACTED for runner/release/email dry-run handoff code, CLI command, tests, and governance updates.
- Version before: 0.9.0
- Version after: 0.10.0
- Base commit: f7615d001c21ddc2778f802b2ca264702dd37308
- Result commit: PENDING
- Task IDs: ADP-PHASE10-RUNNER-RELEASE-EMAIL-001
- Goal: Implement Phase 10 handoff preview for runner, release, and email transport without enabling any external side effect.
- Assumptions: Phase 10 requires a completed local dry-run RunRecord and keeps scheduler, GitHub Actions runner, unattended execution, Release upload, and real SMTP sending disabled.
- Files changed: handoff code, CLI command, handoff tests, version files, and governance records.
- Model changes: Activated MOD-ADP-010 as adp-handoff-v1.
- Parameter changes: Activated PARAM-ADP-048 through PARAM-ADP-050 as adp-handoff-parameters-v1.
- Commands run: project unit tests; root governance tests; schema parse; project governance validator; changed-only enforce-sync; dashboard generation; git diff check.
- Test results: 55 project tests OK; 30 root governance tests OK; schemas parse; project governance errors 0 warnings 0; changed-only enforce-sync errors 0 warnings 0; dashboard PASS; git diff check exit 0.
- Successes: Handoff contract encodes disabled runner/release/email transport side effects.
- Failures: none recorded at implementation time.
- Decisions: Use dry-run artifact previews rather than writing release assets or sending email.
- Remaining risks: Phase 11 final acceptance handoff is still pending; no live 30-day run evidence is claimed.
- Rollback: Revert Phase 10 handoff code, tests, and governance updates.
- Next step: Start Phase 11 final acceptance and handoff package after Phase 10 validation passes.

### `ITER-20260621-011`

- Date: 2026-06-21
- Fact level: EXTRACTED for final acceptance/handoff readiness code, CLI command, tests, and governance updates.
- Version before: 0.10.0
- Version after: 0.11.0
- Base commit: 06ce53098bb5f84b05e8f3e6c0a4c789ece298d8
- Result commit: PENDING
- Task IDs: ADP-PHASE11-ACCEPTANCE-HANDOFF-001
- Goal: Generate final acceptance and handoff readiness package without making unsupported production or 30-day trial claims.
- Assumptions: Handoff readiness can pass locally, but production acceptance remains blocked until real 30-day, scheduler, Release, SMTP, and resource evidence exists.
- Files changed: acceptance code, CLI command, acceptance tests, version files, and governance records.
- Model changes: Activated MOD-ADP-011 as adp-acceptance-v1.
- Parameter changes: Activated PARAM-ADP-051 through PARAM-ADP-055 as adp-acceptance-parameters-v1.
- Commands run: project unit tests; root governance tests; schema parse; project governance validator; changed-only enforce-sync; dashboard generation; git diff check.
- Test results: 60 project tests OK; 31 root governance tests OK; schemas parse; project governance errors 0 warnings 0; changed-only enforce-sync errors 0 warnings 0; dashboard PASS; git diff check exit 0.
- Successes: Acceptance package separates dry-run readiness from production acceptance.
- Failures: none recorded at implementation time.
- Decisions: Do not mark production acceptance pass without explicit operational evidence references.
- Remaining risks: Live production readiness still requires external runner, SMTP, Release, and 30-day trial execution.
- Rollback: Revert Phase 11 acceptance code, tests, and governance updates.
- Next step: Provide final handoff and stop unless operational prerequisites are supplied.

### `ITER-20260621-012`

- Date: 2026-06-21
- Fact level: EXTRACTED for acceptance evidence-reference hardening, tests, and governance updates.
- Version before: 0.11.0
- Version after: 0.11.1
- Base commit: b6c1dce15a4fc850c7e555af178deda92899d120
- Result commit: PENDING
- Task IDs: ADP-PHASE11-EVIDENCE-REF-HARDENING-002
- Goal: Prevent boolean-only operational evidence from marking production acceptance as passed.
- Assumptions: Every production pass requirement must include a non-empty evidence reference.
- Files changed: acceptance code, acceptance tests, version files, and governance records.
- Model changes: Updated MOD-ADP-011 to adp-acceptance-v1.1.
- Parameter changes: Added PARAM-ADP-056 for evidence-reference requirements.
- Commands run: project unit tests; root governance tests; schema parse; project governance validator; changed-only enforce-sync; dashboard generation; git diff check.
- Test results: 61 project tests OK; 32 root governance tests OK; schemas parse; project governance errors 0 warnings 0; changed-only enforce-sync errors 0 warnings 0; dashboard PASS; git diff check exit 0.
- Successes: Production acceptance cannot pass on true flags without evidence refs.
- Failures: none recorded at implementation time.
- Decisions: Keep production acceptance blocked unless both requirement flags and evidence references are present.
- Remaining risks: Live production readiness still requires external runner, SMTP, Release, and 30-day trial execution.
- Rollback: Revert evidence-reference hardening and restore version 0.11.0.
- Next step: Continue only with real operational prerequisite setup or evidence collection.

### `ITER-20260621-013`

- Date: 2026-06-21
- Fact level: EXTRACTED for 30-day trial evidence validator, acceptance integration, CLI command, tests, schema, and governance updates.
- Version before: 0.11.1
- Version after: 0.11.2
- Base commit: a67a988acf3778392ae584742fad8bf2c89d7d1d
- Result commit: PENDING
- Task IDs: ADP-PHASE11-TRIAL-EVIDENCE-VALIDATOR-003
- Goal: Require a validated 30-day trial evidence report before production acceptance can pass.
- Assumptions: The validator defines and enforces the evidence package but does not fabricate or execute the live 30-day trial.
- Files changed: trial evidence validator, acceptance gate, CLI command, tests, schema, README, CHANGELOG, phase record, version files, and governance records.
- Model changes: Added MOD-ADP-012 as adp-trial-evidence-v1 and updated MOD-ADP-011 to adp-acceptance-v1.2.
- Parameter changes: Added PARAM-ADP-057 through PARAM-ADP-064.
- Commands run: project unit tests; root governance tests; schema parse; project governance validator; changed-only enforce-sync; dashboard generation; git diff check.
- Test results: 67 project tests OK; 33 root governance tests OK; schemas parse; project governance errors 0 warnings 0; changed-only enforce-sync errors 0 warnings 0; dashboard PASS; git diff check exit 0.
- Successes: Production acceptance now rejects raw refs/booleans unless they come from a validated trial report.
- Failures: initial changed-only sync failed because the latest event did not cover the full branch diff; fixed by updating the latest development event and run manifest to the current 100-file diff list.
- Decisions: Treat weekly/monthly replay and recovery drill evidence as required parts of the 30-day trial evidence package.
- Remaining risks: Live production acceptance still requires external scheduler, SMTP, Release, resources, and actual 30-day run evidence.
- Rollback: Revert Phase 11 trial evidence validator and restore version 0.11.1.
- Next step: Run project and governance validation, then sync the PR.

### `ITER-20260621-014`

- Date: 2026-06-21
- Fact level: EXTRACTED for production preflight gate, CLI command, schema, tests, and governance updates.
- Version before: 0.11.2
- Version after: 0.11.3
- Base commit: 0d0e23fda99410770283401bfdb70ee8026cd489
- Result commit: PENDING
- Task IDs: ADP-PHASE11-PRODUCTION-PREFLIGHT-004
- Goal: Add a fail-closed gate before any scheduled production execution.
- Assumptions: Production runs must block if runtime commands, secret key presence, disk, memory, Git artifact hygiene, or cache/staging checks fail.
- Files changed: production preflight code, CLI command, tests, schema, README, CHANGELOG, phase record, version files, and governance records.
- Model changes: Added MOD-ADP-013 as adp-production-preflight-v1.
- Parameter changes: Added PARAM-ADP-065 through PARAM-ADP-070.
- Commands run: project unit tests; root governance tests; schema parse; project governance validator; changed-only enforce-sync; production preflight CLI; dashboard generation; git diff check.
- Test results: 71 project tests OK; 34 root governance tests OK; schemas parse; project governance errors 0 warnings 0; changed-only enforce-sync errors 0 warnings 0; production preflight exits 2 with blocked status as expected on current environment; dashboard PASS; git diff check exit 0.
- Successes: Preflight does not log secret values and does not read Codex auth.
- Failures: production preflight correctly blocks current environment because `gh`, `ffmpeg`, and `docker` are missing; SMTP/Release/runner env keys are missing; free disk is 25.36 GiB below the 80 GiB threshold.
- Decisions: Treat current local missing `gh`, `ffmpeg`, `docker`, SMTP env keys, Release target, and runner label as expected production blockers.
- Remaining risks: Production acceptance still requires provisioning the blocked prerequisites and running a real 30-day trial.
- Rollback: Revert Phase 11 production preflight gate and restore version 0.11.2.
- Next step: Run project and governance validation, then sync the PR.

### `ITER-20260621-015`

- Date: 2026-06-21
- Fact level: EXTRACTED for manual production trial bootstrap workflow, runbook, CLI validator, schema, tests, and governance updates.
- Version before: 0.11.3
- Version after: 0.11.4
- Base commit: 6ca3847899ea4c2647d90d219e0c5995fd6aedc5
- Result commit: PENDING
- Task IDs: ADP-PHASE11-TRIAL-BOOTSTRAP-005
- Goal: Add a manual GitHub Actions entrypoint that can start the real trial path only after production preflight succeeds.
- Assumptions: Bootstrap mode is manual-only and does not schedule production, upload Releases, send SMTP mail, render media, download models, or claim 30-day acceptance.
- Files changed: trial bootstrap validator, CLI command, workflow, runbook, tests, schema, README, CHANGELOG, phase record, version files, and governance records.
- Model changes: Added MOD-ADP-014 as adp-trial-bootstrap-v1.
- Parameter changes: Added PARAM-ADP-071 through PARAM-ADP-074.
- Commands run: project unit tests; schema parse; trial bootstrap CLI; root governance tests; project governance validator; changed-only enforce-sync; dashboard generation; git diff check.
- Test results: 74 project tests OK; 35 root governance tests OK; schemas parse; trial bootstrap plan pass; project governance errors 0 warnings 0; changed-only enforce-sync errors 0 warnings 0; dashboard PASS; git diff check exit 0.
- Successes: Bootstrap workflow requires explicit confirmation, targets a private self-hosted runner label, runs production preflight first, uploads preflight evidence, and leaves Release/SMTP side effects disabled.
- Failures: none recorded at implementation time.
- Decisions: Keep cron scheduling and real production side effects disabled until a provisioned runner produces a passing preflight artifact.
- Remaining risks: Production acceptance still requires actual runner provisioning, SMTP/Release configuration, preflight pass on runner, scheduled execution, and 30-day trial evidence.
- Rollback: Revert Phase 11 trial bootstrap workflow, runbook, validator, tests, and restore version 0.11.3.
- Next step: Run root governance validation, update run manifest, and sync the PR.

### `ITER-20260621-016`

- Date: 2026-06-21
- Fact level: EXTRACTED for live arXiv source ingest code, CLI command, SourceBatch schema, tests, phase record, and governance updates.
- Version before: 0.11.4
- Version after: 0.11.5
- Base commit: 26d82979344b49ad0628264713bf6423c4a1c11e
- Result commit: PENDING
- Task IDs: ADP-PHASE11-LIVE-ARXIV-INGEST-006
- Goal: Add a real arXiv latest-source ingest command with incremental duplicate filtering and fail-closed network/API behavior.
- Assumptions: Source ingest may use live arXiv Atom metadata but must not download PDFs, bulk harvest, bypass TLS, schedule runs, send email, or publish content.
- Files changed: source ingest code, CLI command, tests, SourceBatch schema, README, CHANGELOG, runbook, phase record, version files, and governance records.
- Model changes: Added MOD-ADP-015 as adp-live-arxiv-ingest-v1.
- Parameter changes: Added PARAM-ADP-075 through PARAM-ADP-080.
- Commands run: project unit tests; schema parse; live arXiv fetch command; root governance tests; project governance validator; changed-only enforce-sync; dashboard generation; git diff check.
- Test results: 78 project tests OK; 36 root governance tests OK; schemas parse; live fetch command blocked on current local Python SSL certificate verification; project governance errors 0 warnings 0; changed-only enforce-sync errors 0 warnings 0; dashboard PASS; git diff check exit 0.
- Successes: Source ingest returns valid SourceBatch objects, filters duplicate source IDs, blocks duplicate-only batches, and blocks network/API failures.
- Failures: Current local machine cannot complete HTTPS arXiv fetch because Python certificate verification fails for `https://export.arxiv.org/api/query`.
- Decisions: Do not bypass TLS verification or switch to insecure fetch behavior; require runner CA trust repair before live trial source collection.
- Remaining risks: Production acceptance still requires actual runner provisioning, CA trust fix, SMTP/Release configuration, preflight pass on runner, scheduled execution, and 30-day trial evidence.
- Rollback: Revert live arXiv ingest command, SourceBatch schema, tests, and restore version 0.11.4.
- Next step: Run root governance validation, update run manifest, and sync the PR.

### `ITER-20260621-017`

- Date: 2026-06-21
- Fact level: EXTRACTED for SMTP delivery boundary code, CLI command, schema, tests, runbook, and governance updates.
- Version before: 0.11.5
- Version after: 0.11.6
- Base commit: 3d8efa4017d15e00d4e1202faa42209ff3c7e227
- Result commit: PENDING
- Task IDs: ADP-PHASE11-SMTP-DELIVERY-007
- Goal: Add a fail-closed SMTP notification delivery boundary with dry-run evidence and explicit real-send gating.
- Assumptions: Notification delivery must default to dry-run; real SMTP requires explicit `--allow-send`, configured SMTP environment keys, TLS, and no secret/body logging.
- Files changed: SMTP delivery code, CLI command, tests, SMTP delivery schema, notification example, runbook, README, CHANGELOG, phase record, version files, and governance records.
- Model changes: Added MOD-ADP-016 as adp-smtp-delivery-v1.
- Parameter changes: Added PARAM-ADP-081 through PARAM-ADP-085.
- Commands run: focused notification/CLI tests; send-notification dry-run CLI. Full project and governance validation pending in this iteration.
- Test results: focused notification/CLI tests 9 OK; send-notification dry-run evidence emitted.
- Successes: Dry-run mode requires no secrets and makes no SMTP connection; real send blocks without env keys; mocked SMTP send starts TLS, logs in, sends to `linzezhang35@gmail.com`, and does not log password values in the report.
- Failures: none for focused tests; real production SMTP remains unverified because SMTP secrets and runner are not provisioned in this local environment.
- Decisions: Keep scheduler/workflow SMTP side effects disabled until production preflight and explicit production enablement exist.
- Remaining risks: Production acceptance still requires actual runner provisioning, CA trust fix, SMTP/Release configuration, preflight pass on runner, scheduled execution, weekly/monthly replay, recovery drill, and 30-day trial evidence.
- Rollback: Revert SMTP delivery command, schema, tests, and restore version 0.11.5.
- Next step: Run full project and governance validation, update run manifest, and sync the PR.

### `ITER-20260621-018`

- Date: 2026-06-21
- Fact level: EXTRACTED for Release delivery boundary code, CLI command, schema, tests, runbook, and governance updates.
- Version before: 0.11.6
- Version after: 0.11.7
- Base commit: cf8af2b082385f118d40e34f03bd91af5d1c270e
- Result commit: PENDING
- Task IDs: ADP-PHASE11-RELEASE-DELIVERY-008
- Goal: Add a fail-closed GitHub Release delivery boundary with dry-run evidence and explicit real-upload gating.
- Assumptions: Release delivery must default to dry-run; real GitHub Release creation requires explicit `--allow-upload`, a configured target, safe assets, `gh`, no clobber upload, and no notes/stdout/stderr logging.
- Files changed: Release delivery code, CLI command, tests, Release delivery schema, runtime example, runbook, README, CHANGELOG, phase record, version files, and governance records.
- Model changes: Added MOD-ADP-017 as adp-release-delivery-v1.
- Parameter changes: Added PARAM-ADP-086 through PARAM-ADP-091.
- Commands run: focused Release/CLI tests; full project tests; schema parse; publish-release dry-run CLI; root governance tests; project governance validator; changed-only enforce-sync; dashboard generation; git diff check.
- Test results: focused Release/CLI tests 9 OK; project tests 88 OK; schemas parse; publish-release dry-run evidence emitted; root governance tests 38 OK; project governance errors 0 warnings 0; changed-only enforce-sync errors 0 warnings 0; dashboard PASS; git diff check exit 0.
- Successes: Dry-run mode makes no `gh` call; real upload blocks without `ADP_RELEASE_TARGET`; forbidden secret-like assets block before command execution; mocked `gh release create` succeeds without `--clobber` and without logging notes, stdout, or stderr.
- Failures: none for focused tests; real private Release delivery remains unverified because `gh` auth, runner, target, and production assets are not provisioned in this local environment.
- Decisions: Keep scheduled Release side effects disabled until production preflight and explicit production enablement exist.
- Remaining risks: Production acceptance still requires actual runner provisioning, CA trust fix, SMTP/Release configuration, preflight pass on runner, scheduled execution, weekly/monthly replay, recovery drill, and 30-day trial evidence.
- Rollback: Revert Release delivery command, schema, tests, and restore version 0.11.6.
- Next step: Run full project and governance validation, update run manifest, and sync the PR.

### `ITER-20260621-019`

- Date: 2026-06-21
- Fact level: EXTRACTED for scheduled production workflow gate, CLI validator, schema, tests, runbook, and governance updates.
- Version before: 0.11.7
- Version after: 0.11.8
- Base commit: fecc32812a863d151f0ea4070ebbb814ec62bc39
- Result commit: PENDING
- Task IDs: ADP-PHASE11-PRODUCTION-SCHEDULER-009
- Goal: Add a fail-closed scheduled production workflow gate for 04:45 health check, 05:00 daily run, and 05:10 watchdog in Australia/Sydney.
- Assumptions: GitHub Actions schedule supports IANA timezone fields; scheduled workflows run from the default branch; production work must remain disabled unless explicit GitHub variables are configured.
- Files changed: scheduled GitHub workflow, production scheduler validator, CLI command, tests, production scheduler schema, runtime example, runbook, README, CHANGELOG, phase record, version files, and governance records.
- Model changes: Added MOD-ADP-018 as adp-production-scheduler-v1.
- Parameter changes: Added PARAM-ADP-092 through PARAM-ADP-096.
- Commands run: focused scheduler/CLI tests; full project tests; schema parse; plan-production-scheduler CLI; root governance tests; project governance validator; changed-only enforce-sync; dashboard generation; git diff check.
- Test results: focused scheduler/CLI tests 8 OK; project tests 91 OK; schemas parse; scheduler plan evidence emitted with status pass; root governance tests 39 OK; project governance errors 0 warnings 0; changed-only enforce-sync errors 0 warnings 0; dashboard PASS; git diff check exit 0.
- Successes: Workflow declares Australia/Sydney 04:45, 05:00, and 05:10 slots; scheduled runs skip unless `ADP_PRODUCTION_ENABLED=true`; preflight runs before scheduled mode; scheduled gate contains no SMTP send or Release upload commands.
- Failures: none for focused tests; real scheduled production remains unverified because workflow is not merged to default, production variables are not enabled, and private runner/preflight evidence is not present.
- Decisions: Use timezone-aware schedule syntax from current GitHub Actions documentation and keep scheduled production side effects disabled by default.
- Remaining risks: Production acceptance still requires actual default-branch scheduling, runner provisioning, CA trust fix, SMTP/Release configuration, preflight pass on runner, scheduled execution, weekly/monthly replay, recovery drill, and 30-day trial evidence.
- Rollback: Revert scheduled production workflow, scheduler validator, schema, tests, and restore version 0.11.7.
- Next step: Run full project and governance validation, update run manifest, and sync the PR.

### `ITER-20260621-020`

- Date: 2026-06-21
- Fact level: EXTRACTED for scheduled execution driver code, CLI command, workflow artifact wiring, schema, tests, runbook, and governance updates.
- Version before: 0.11.8
- Version after: 0.11.9
- Base commit: 04d7d9e
- Result commit: PENDING
- Task IDs: ADP-PHASE11-SCHEDULED-EXECUTION-010
- Goal: Add the controlled runtime bridge that produces scheduled health-check, daily-run, and watchdog evidence after production preflight.
- Assumptions: Scheduled execution must still fail closed unless preflight passes, daily-run is explicitly enabled, daily input exists, and real SMTP/Release evidence is produced.
- Files changed: scheduled execution driver, CLI command, scheduled GitHub workflow, scheduled execution schema, tests, runtime example, runbook, README, CHANGELOG, phase record, version files, and governance records.
- Model changes: Added MOD-ADP-019 as adp-scheduled-execution-v1 and updated MOD-ADP-018 scheduler validation to require the execution artifact.
- Parameter changes: Added PARAM-ADP-097 through PARAM-ADP-101.
- Commands run: focused scheduled execution/scheduler/CLI tests; full project tests; schema parse; run-scheduled-production health-check CLI; root governance tests; project governance validator; changed-only enforce-sync; dashboard generation; git diff check.
- Test results: focused scheduled execution/scheduler/CLI tests 13 OK; final full validation recorded in the run manifest after this iteration.
- Successes: Health-check creates evidence after preflight; daily-run blocks until `ADP_SCHEDULED_RUN_ENABLED=true`; dry-run SMTP/Release produces degraded exit 2; mocked real SMTP and Release create production-ready evidence refs.
- Failures: none for focused tests; real production evidence remains unavailable without default-branch schedule, private runner, daily input, SMTP, Release, and resource evidence.
- Decisions: Keep the workflow free of `--allow-send` and `--allow-upload` flags; real side effects are only requested through explicit environment variables and dedicated transport validators.
- Remaining risks: Production acceptance still requires live source pass, real daily content generation input, SMTP/Release secrets, runner preflight pass, weekly/monthly replay, recovery drill, and 30 unique daily production evidence entries.
- Rollback: Revert scheduled execution driver, workflow execution artifact changes, schema, tests, and restore version 0.11.8.
- Next step: Provision runner variables/secrets and run a controlled preflight plus health-check evidence pass.

### `ITER-20260621-021`

- Date: 2026-06-21
- Fact level: EXTRACTED for daily input builder code, CLI command, scheduled workflow artifact wiring, schema, tests, runbook, and governance updates.
- Version before: 0.11.9
- Version after: 0.11.10
- Base commit: 267c879
- Result commit: PENDING
- Task IDs: ADP-PHASE11-DAILY-INPUT-BUILDER-011
- Goal: Add the deterministic bridge from live arXiv SourceBatch output to scheduled daily pipeline input.
- Assumptions: Daily input may only use arXiv Atom summary and metadata claims; it must not download PDFs, perform bulk harvest, infer peer review, send email, upload Releases, or claim 30-day production acceptance.
- Files changed: daily input builder, CLI command, scheduled execution compatibility, scheduled workflow source/daily-input artifacts, daily input schema, tests, runtime example, runbook, README, CHANGELOG, phase record, version files, and governance records.
- Model changes: Added MOD-ADP-020 as adp-daily-input-builder-v1 and updated MOD-ADP-018 scheduler validation to require daily input artifact wiring.
- Parameter changes: Added PARAM-ADP-102 through PARAM-ADP-107.
- Commands run: focused daily input/scheduled/scheduler/CLI tests; full project tests; schema parse; fixture build-daily-input CLI; root governance tests; project governance validator; changed-only enforce-sync; dashboard generation; git diff check.
- Test results: focused daily input/scheduled/scheduler/CLI tests: 18 tests OK; final full validation recorded in the run manifest after this iteration.
- Successes: Builder converts a fixture SourceBatch into a daily input package with P0 Atom summary evidence; missing summaries and recent duplicate selections block; scheduled daily-run accepts builder reports; scheduled workflow uploads source batch and daily input artifacts when no override path is set.
- Failures: none for focused tests; real production evidence remains unavailable without default-branch schedule, private runner, live source pass, SMTP, Release, and resource evidence.
- Decisions: Keep automatic daily input claims conservative and restricted to arXiv Atom metadata until a later evidence extraction phase is explicitly implemented.
- Remaining risks: Production acceptance still requires live source pass on the runner, real SMTP/Release secrets and refs, weekly/monthly replay, recovery drill, resource telemetry, and 30 unique daily production evidence entries.
- Rollback: Revert daily input builder, workflow source/daily-input artifact changes, schema, tests, and restore version 0.11.9.
- Next step: Provision runner variables/secrets and run a controlled preflight plus health-check/daily input evidence pass without claiming production acceptance.

### `ITER-20260621-022`

- Date: 2026-06-21
- Fact level: EXTRACTED for trial ledger updater code, CLI command, scheduled workflow artifact wiring, schema, tests, runbook, and governance updates.
- Version before: 0.11.10
- Version after: 0.11.11
- Base commit: 76d976b
- Result commit: PENDING
- Task IDs: ADP-PHASE11-TRIAL-LEDGER-012
- Goal: Add the deterministic bridge from production-ready scheduled daily-run evidence to the 30-day trial evidence ledger.
- Assumptions: Ledger updates may append one daily entry but must not claim 30-day acceptance until the embedded trial validator passes every gate.
- Files changed: trial ledger updater, CLI command, scheduled execution compatibility fields, scheduled workflow ledger artifact, trial ledger schema, tests, runtime example, runbook, README, CHANGELOG, phase record, version files, and governance records.
- Model changes: Added MOD-ADP-021 as adp-trial-ledger-v1 and updated MOD-ADP-018 scheduler validation to require the trial ledger update artifact.
- Parameter changes: Added PARAM-ADP-108 through PARAM-ADP-112.
- Commands run: focused trial ledger/scheduled/scheduler/CLI tests; workflow Build scheduled daily input bash syntax; workflow Update trial evidence ledger bash syntax. Full validation is recorded in the run manifest after this iteration.
- Test results: focused trial ledger and scheduled tests: 19 tests OK; workflow ledger step bash -n pass.
- Successes: Ledger update blocks non-production scheduled reports and duplicate daily evidence; it can upgrade global Release/SMTP/resource flags only when explicit production evidence is provided; scheduled workflow uploads a trial ledger update artifact after daily-run.
- Failures: none for focused tests; real production acceptance remains unavailable without default-branch schedule, private runner, live source pass, SMTP, Release, weekly/monthly, recovery, and 30-day evidence.
- Decisions: Keep weekly/monthly replay and recovery drill evidence outside automatic daily ledger updates.
- Remaining risks: Production acceptance still requires live source pass on the runner, real SMTP/Release refs, resource telemetry, weekly/monthly replay, recovery drill, and 30 unique daily production evidence entries.
- Rollback: Revert trial ledger updater, workflow ledger artifact changes, schema, tests, and restore version 0.11.10.
- Next step: Provision runner variables/secrets and run controlled preflight plus production-ready daily evidence collection without claiming 30-day acceptance.

### `ITER-20260621-023`

- Date: 2026-06-22
- Fact level: EXTRACTED for trial ledger state persistence workflow wiring, CLI exporter, tests, runbook, and governance updates.
- Version before: 0.11.11
- Version after: 0.11.12
- Base commit: 94f1d1f
- Result commit: PENDING
- Task IDs: ADP-PHASE11-TRIAL-LEDGER-STATE-013
- Goal: Carry the 30-day trial evidence ledger forward across scheduled GitHub Actions runs without retaining local media, model, secret, or cache artifacts.
- Assumptions: GitHub Actions artifact restore is the durable state channel; explicit configured state files take priority; blocked ledger updates must not overwrite the prior state artifact.
- Files changed: scheduled workflow state restore/export wiring, CLI export command, trial ledger and scheduler tests, runtime example, runbook, README, CHANGELOG, phase record, version files, and governance records.
- Model changes: Added MOD-ADP-022 as adp-trial-ledger-state-v1 and updated scheduler validation to require state artifact restore/export wiring.
- Parameter changes: Added PARAM-ADP-113 through PARAM-ADP-117.
- Commands run: focused trial ledger/scheduler/CLI tests; workflow Build scheduled daily input bash syntax; workflow Resolve trial ledger state bash syntax; workflow Update trial evidence ledger bash syntax; workflow Export trial evidence ledger state bash syntax; export-trial-ledger-state fixture CLI. Full validation is recorded in the run manifest after this iteration.
- Test results: focused trial ledger state tests: 15 tests OK; workflow restore/export bash -n pass; export-trial-ledger-state fixture CLI pass and JSON parse OK.
- Successes: Scheduled daily-run now restores prior `adp-trial-evidence-ledger` state when available, appends through `update-trial-ledger --path`, exports only the `trial_evidence` object after a successful append, and uploads a replacement state artifact only on export success.
- Failures: none for focused tests; real artifact restore remains unverified until the workflow runs on the default branch with retained artifacts.
- Decisions: Keep trial evidence state in GitHub Actions artifacts rather than Git, and never upload a replacement state artifact for blocked ledger updates.
- Remaining risks: Production acceptance still requires live source pass on the runner, real SMTP/Release refs, resource telemetry, weekly/monthly replay, recovery drill, and 30 unique daily production evidence entries.
- Rollback: Revert trial ledger state restore/export workflow changes, export command, tests, and restore version 0.11.11.
- Next step: Provision runner variables/secrets and run controlled default-branch scheduled evidence collection with artifact retention.

### `ITER-20260621-024`

- Date: 2026-06-22
- Fact level: EXTRACTED for trial operational evidence annotation code, CLI commands, tests, runbook, and governance updates.
- Version before: 0.11.12
- Version after: 0.11.13
- Base commit: f9cb3de
- Result commit: PENDING
- Task IDs: ADP-PHASE11-TRIAL-OPS-EVIDENCE-014
- Goal: Add an audited merge path for weekly/monthly replay, recovery drill, and other operational evidence refs without hand-editing trial evidence JSON.
- Assumptions: Operational evidence refs are produced by future controlled operations; this command only validates and merges explicit refs and cannot create the underlying weekly/monthly/recovery evidence.
- Files changed: trial ops annotator, CLI commands, tests, runtime example, runbook, README, CHANGELOG, phase record, version files, and governance records.
- Model changes: Added MOD-ADP-023 as adp-trial-ops-evidence-v1.
- Parameter changes: Added PARAM-ADP-118 through PARAM-ADP-122.
- Commands run: focused trial ops/trial/CLI tests. Full validation is recorded in the run manifest after this iteration.
- Test results: focused trial ops tests: 16 tests OK.
- Successes: The annotator merges weekly/monthly replay and recovery refs, can unlock the final trial validator when complete daily evidence already exists, blocks verified flags without refs, and blocks exporting unupdated evidence.
- Failures: none for focused tests; real weekly/monthly replay and recovery drill remain unverified until controlled production operations emit durable refs.
- Decisions: Keep operational evidence annotation as explicit-ref-only; do not infer that replay or recovery occurred from the existence of daily ledger state.
- Remaining risks: Production acceptance still requires live source pass on the runner, real SMTP/Release refs, resource telemetry, weekly/monthly replay, recovery drill, and 30 unique daily production evidence entries.
- Rollback: Revert trial ops annotator, CLI commands, tests, runbook/docs/governance updates, and restore version 0.11.12.
- Next step: Provision runner variables/secrets and run controlled default-branch scheduled evidence collection with explicit weekly/monthly and recovery evidence refs.

### `ITER-20260621-025`

- Date: 2026-06-22
- Fact level: EXTRACTED for trial replay evidence code, CLI command, schema, tests, runbook, and governance updates.
- Version before: 0.11.13
- Version after: 0.11.14
- Base commit: 010e9ba
- Result commit: PENDING
- Task IDs: ADP-PHASE11-TRIAL-REPLAY-EVIDENCE-015
- Goal: Add an audited weekly/monthly replay evidence builder from accumulated production daily trial entries.
- Assumptions: Replay evidence must be generated from production-ready daily refs and archived under a durable ref before it can be merged into trial evidence.
- Files changed: trial replay builder, CLI command, replay schema, tests, runbook, README, CHANGELOG, phase record, version files, and governance records.
- Model changes: Added MOD-ADP-024 as adp-trial-replay-v1.
- Parameter changes: Added PARAM-ADP-123 through PARAM-ADP-127.
- Commands run: focused trial replay/trial ops/CLI tests. Full validation is recorded in the run manifest after this iteration.
- Test results: focused trial replay tests: 16 tests OK.
- Successes: The replay builder validates production daily refs, duplicate-free daily coverage, 7 consecutive days for weekly replay, 30 consecutive days for monthly replay, and durable replay refs before emitting annotation hints.
- Failures: Initial monthly replay logic trusted a lowered `period.expected_days`; focused tests caught it and the implementation now requires at least 30 days.
- Decisions: Keep replay evidence generation separate from trial evidence mutation; `annotate-trial-ops-evidence` remains the only merge path.
- Remaining risks: Production acceptance still requires live source pass on the runner, real SMTP/Release refs, resource telemetry, recovery drill, actual archived weekly/monthly replay evidence, and 30 unique daily production evidence entries.
- Rollback: Revert trial replay builder, CLI command, schema, tests, runbook/docs/governance updates, and restore version 0.11.13.
- Next step: Provision runner variables/secrets and run controlled default-branch scheduled evidence collection with replay and recovery artifacts.

### `ITER-20260621-026`

- Date: 2026-06-22
- Fact level: EXTRACTED for trial recovery evidence code, CLI command, schema, tests, runbook, and governance updates.
- Version before: 0.11.14
- Version after: 0.11.15
- Base commit: c28ea57
- Result commit: PENDING
- Task IDs: ADP-PHASE11-TRIAL-RECOVERY-EVIDENCE-016
- Goal: Add an audited recovery drill evidence builder from failed/degraded and recovered scheduled daily-run reports.
- Assumptions: Recovery evidence must be generated from archived scheduled execution reports with real sent notifications and durable refs before it can be merged into trial evidence.
- Files changed: trial recovery builder, CLI command, recovery schema, tests, runbook, README, CHANGELOG, phase record, version files, and governance records.
- Model changes: Added MOD-ADP-025 as adp-trial-recovery-v1.
- Parameter changes: Added PARAM-ADP-128 through PARAM-ADP-132.
- Commands run: focused trial recovery/replay/ops/CLI tests. Full validation is recorded in the run manifest after this iteration.
- Test results: focused trial recovery/replay/ops/CLI tests: 21 tests OK.
- Successes: The recovery builder validates failed or degraded scheduled execution evidence, real sent failure/recovery notifications, production-ready recovery refs, durable failure/recovery refs, and date consistency before emitting annotation hints.
- Failures: none for focused tests; real production recovery drill remains unverified until controlled production operations emit durable refs.
- Decisions: Keep recovery evidence generation separate from scheduler execution and trial evidence mutation; `annotate-trial-ops-evidence` remains the only merge path.
- Remaining risks: Production acceptance still requires live source pass on the runner, real SMTP/Release refs, resource telemetry, archived weekly/monthly replay evidence, archived recovery drill evidence, and 30 unique daily production evidence entries.
- Rollback: Revert trial recovery builder, CLI command, schema, tests, runbook/docs/governance updates, and restore version 0.11.14.
- Next step: Provision runner variables/secrets and run controlled default-branch scheduled evidence collection with replay and recovery artifacts.

### `ITER-20260621-027`

- Date: 2026-06-22
- Fact level: EXTRACTED for trial resource evidence code, timestamped preflight resource refs, CLI command, schema, tests, runbook, and governance updates.
- Version before: 0.11.15
- Version after: 0.11.16
- Base commit: 750155b
- Result commit: PENDING
- Task IDs: ADP-PHASE11-TRIAL-RESOURCE-EVIDENCE-017
- Goal: Add an audited resource telemetry evidence builder for 30-day trial daily resource refs.
- Assumptions: Global resource evidence must be generated from 30 unique daily resource refs that match passing production preflight reports and a durable resource evidence ref before it can be merged into trial evidence.
- Files changed: trial resource builder, production preflight resource ref generation, CLI command, resource schema, tests, runbook, README, CHANGELOG, phase record, version files, and governance records.
- Model changes: Added MOD-ADP-026 as adp-trial-resource-v1.
- Parameter changes: Added PARAM-ADP-133 through PARAM-ADP-137.
- Commands run: focused trial resource/preflight/scheduled/ops/CLI tests. Full validation is recorded in the run manifest after this iteration.
- Test results: focused trial resource/preflight/scheduled/ops/CLI tests: 27 tests OK.
- Successes: The resource builder validates 30 unique daily resource refs, matching passing production preflight reports, required resource gates, durable resource refs, and blocks lowered expected-day attempts.
- Failures: none for focused tests; real 30-day production resource telemetry remains unverified until controlled production operations emit durable refs.
- Decisions: Use timestamped production preflight resource refs so every daily run can be matched to its own resource gate evidence.
- Remaining risks: Production acceptance still requires live source pass on the runner, real SMTP/Release refs, archived weekly/monthly replay evidence, archived recovery drill evidence, actual resource telemetry, and 30 unique daily production evidence entries.
- Rollback: Revert trial resource builder, timestamped preflight resource ref change, CLI command, schema, tests, runbook/docs/governance updates, and restore version 0.11.15.
- Next step: Provision runner variables/secrets and run controlled default-branch scheduled evidence collection with resource, replay, and recovery artifacts.

### `ITER-20260621-028`

- Date: 2026-06-22
- Fact level: EXTRACTED for trial start gate code, CLI command, schema, tests, runbook, and governance updates.
- Version before: 0.11.16
- Version after: 0.11.17
- Base commit: 4e572b8
- Result commit: PENDING
- Task IDs: ADP-PHASE11-TRIAL-START-GATE-018
- Goal: Add an audited start-readiness gate for the real 30-day production trial.
- Assumptions: A real trial may be marked start-ready only after production preflight, bootstrap, scheduler, live source ingest, real SMTP, real Release, durable refs, and explicit confirmation all pass.
- Files changed: trial start gate, CLI command, schema, tests, runbook, README, CHANGELOG, phase record, version files, and governance records.
- Model changes: Added MOD-ADP-027 as adp-trial-start-v1.
- Parameter changes: Added PARAM-ADP-138 through PARAM-ADP-143.
- Commands run: focused trial start/bootstrap/scheduler/preflight/source/SMTP/Release/CLI tests. Full validation is recorded in the run manifest after this iteration.
- Test results: focused trial start/bootstrap/scheduler/preflight/source/SMTP/Release/CLI tests: 34 tests OK.
- Successes: The start gate validates all required upstream reports, real SMTP and Release probes, durable refs, explicit confirmation, and blocks dry-run or incomplete start evidence.
- Failures: none for focused tests; real default-branch trial start evidence remains unverified until controlled production operations archive durable refs.
- Decisions: Keep trial start as a no-side-effect gate so setup can be audited before enabling daily production evidence collection.
- Remaining risks: Production acceptance still requires default-branch trial start evidence, live source pass on the runner, real SMTP/Release refs, archived weekly/monthly replay evidence, archived recovery drill evidence, actual resource telemetry, and 30 unique daily production evidence entries.
- Rollback: Revert trial start gate, CLI command, schema, tests, runbook/docs/governance updates, and restore version 0.11.16.
- Next step: Run controlled default-branch trial start evidence after runner variables/secrets and durable refs are provisioned.

### `ITER-20260621-029`

- Date: 2026-06-22
- Fact level: EXTRACTED for trial start workflow, validator code, CLI command, schema, tests, runbook, and governance updates.
- Version before: 0.11.17
- Version after: 0.11.18
- Base commit: 6caec78
- Result commit: PENDING
- Task IDs: ADP-PHASE11-TRIAL-START-WORKFLOW-019
- Goal: Add an audited manual default-branch workflow that can collect trial start evidence artifacts after runner variables, SMTP secrets, and Release target are provisioned.
- Assumptions: The workflow remains manual-only, preflight-first, artifact-backed, and cannot run real SMTP or Release probes unless explicit GitHub variables enable them.
- Files changed: trial start workflow, workflow validator, CLI command, workflow schema, tests, runbook, README, CHANGELOG, phase record, version files, and governance records.
- Model changes: Added MOD-ADP-028 as adp-trial-start-workflow-v1.
- Parameter changes: Added PARAM-ADP-144 through PARAM-ADP-148.
- Commands run: focused trial start workflow/start/bootstrap/scheduler/CLI tests. Full validation is recorded in the run manifest after this iteration.
- Test results: focused trial start workflow/start/bootstrap/scheduler/CLI tests: 20 tests OK.
- Successes: The workflow validator checks manual dispatch, confirmation gate, private runner targeting, preflight-first ordering, source-before-delivery ordering, complete artifact uploads, durable start refs, side-effect vars, and secret safety.
- Failures: none for focused tests; real workflow evidence remains unverified until the workflow is merged to default branch and run on the private runner with configured GitHub variables/secrets.
- Decisions: Keep the workflow dispatch explicit and leave SMTP/Release side effects disabled unless `ADP_ALLOW_SMTP_SEND` and `ADP_ALLOW_RELEASE_UPLOAD` are true for a controlled start probe.
- Remaining risks: Production acceptance still requires a passing default-branch trial start workflow run, live source pass on the runner, real SMTP/Release refs, archived weekly/monthly replay evidence, archived recovery drill evidence, actual resource telemetry, and 30 unique daily production evidence entries.
- Rollback: Revert trial start workflow, validator, CLI command, schema, tests, runbook/docs/governance updates, and restore version 0.11.17.
- Next step: Merge to default branch, provision runner/secrets/vars, run the manual trial start workflow, archive `adp-trial-start-gate`, then begin controlled 30-day evidence collection.

### `ITER-20260621-030`

- Date: 2026-06-22
- Fact level: EXTRACTED for production launch readiness code, CLI command, schema, tests, runbook, and governance updates; EXTRACTED from GitHub connector for current PR #14 draft/unmerged state.
- Version before: 0.11.18
- Version after: 0.11.19
- Base commit: fc5a100
- Result commit: PENDING
- Task IDs: ADP-PHASE11-PRODUCTION-LAUNCH-READINESS-020
- Goal: Add an audited launch readiness gate before dispatching the default-branch trial start workflow.
- Assumptions: Launch may proceed only after PR #14 is non-draft and merged to `main`, the expected head SHA is bound, the trial start workflow contract is ready, and runner/secrets/Release/vars/default-branch refs are durable.
- Files changed: production launch readiness gate, CLI command, launch schema, tests, runbook, README, CHANGELOG, phase record, version files, and governance records.
- Model changes: Added MOD-ADP-029 as adp-production-launch-readiness-v1.
- Parameter changes: Added PARAM-ADP-149 through PARAM-ADP-153.
- Commands run: focused production launch/workflow/CLI tests. Full validation is recorded in the run manifest after this iteration.
- Test results: focused production launch/workflow/CLI tests: 12 tests OK.
- Successes: The launch gate validates PR merged/non-draft state, expected head SHA binding, trial start workflow readiness, durable external readiness refs, explicit launch confirmation, and no secret/auth/side-effect behavior.
- Failures: none for focused tests; current PR #14 is draft and unmerged, so real launch readiness correctly remains blocked.
- Decisions: Keep launch readiness as an explicit input gate that consumes current PR metadata JSON and durable readiness refs rather than merging PRs, dispatching workflows, or reading secret values.
- Remaining risks: Production launch still requires PR ready/merge, private runner provisioning, GitHub secrets and vars, default-branch workflow dispatch, real SMTP/Release evidence, and archived start-gate artifacts; production acceptance still requires 30 unique daily production evidence entries plus replay, recovery, and resource evidence.
- Rollback: Revert production launch readiness gate, CLI command, schema, tests, runbook/docs/governance updates, and restore version 0.11.18.
- Next step: Mark PR ready, merge to `main`, provision runner/secrets/vars, rerun `plan-production-launch` with durable refs, then dispatch the default-branch trial start workflow.

### `ITER-20260621-031`

- Date: 2026-06-22
- Fact level: EXTRACTED for latest main governance requirements and root `semantic_coverage` validation behavior; PLANNED for future arXiv semantic extractor work.
- Version before: 0.11.19
- Version after: 0.11.19
- Base commit: 21f97f2
- Result commit: PENDING
- Task IDs: GOV-SEMANTIC-ADP-001
- Goal: Synchronize PR #14 with the latest `main` governance semantic coverage rollout contract without changing arXiv Daily Push runtime behavior.
- Assumptions: arXiv Daily Push cannot claim `machine_verified` semantic coverage until active parameter values and formula implementation fingerprints are extracted and validated by a dedicated machine extractor.
- Files changed: root semantic coverage project registry entry, arXiv delivery task binding, generated dashboard/status/owner status views, run manifest, and governance ledger records.
- Model changes: No runtime model behavior change.
- Parameter changes: No active parameter value change.
- Commands run: pending final validation after merge conflict resolution and generated status refresh.
- Test results: semantic extractor checked 93 active parameters and 31 active formulas with no errors; project governance errors 0 warnings 0; root governance tests 86 OK; arXiv unit tests 143 OK; dashboard generation PASS after temporarily restoring full registered project validation context; changed-only enforce-sync semantic errors 0 warnings 0 with `arxiv-daily-push` changed and all registered project validation errors 0 warnings 0; `git diff --check` exit 0; no arXiv `__pycache__` or `.pyc`; pre-shrink storage worktree 222M, `arxiv-daily-push` 1.7M, `.git` 90M.
- Successes: The semantic coverage rollout is task-bound and explicitly non-terminal, preventing the project from silently bypassing the new root governance gate.
- Failures: none recorded yet; semantic extraction remains unimplemented and therefore planned.
- Decisions: Keep `semantic_extractors` disabled for arXiv Daily Push until extractor evidence exists; do not mark semantic coverage as machine verified in this merge-sync increment.
- Remaining risks: Production launch still requires PR ready/merge, private runner provisioning, GitHub secrets and vars, default-branch workflow dispatch, real SMTP/Release evidence, and archived start-gate artifacts; production acceptance still requires 30 unique daily production evidence entries plus replay, recovery, and resource evidence.
- Rollback: Remove the arXiv `semantic_coverage` block, `GOV-SEMANTIC-ADP-001` task, generated owner/status changes, run manifest, and this ledger/event update.
- Next step: After governance validation passes, finish merging latest `main` into PR #14, push, then reassess ready/merge and default-branch trial-start prerequisites.

### `ITER-20260621-032`

- Date: 2026-06-22
- Fact level: EXTRACTED from GitHub PR #14 merge metadata, local `main`, workflow file presence, workflow run/status checks, and the `plan-production-launch` post-merge gate result.
- Version before: 0.11.19
- Version after: 0.11.19
- Base commit: 9616264221cecc8077fc862692ec6025f1e4872b
- Result commit: PENDING
- Task IDs: ADP-PHASE11-POST-MERGE-LAUNCH-AUDIT-021
- Goal: Record the post-merge production launch audit after PR #14 was merged to `main`.
- Assumptions: This iteration must not dispatch workflows, provision runners, read or write secrets, send SMTP mail, create Releases, or claim 30-day production acceptance.
- Files changed: post-merge phase record, delivery plan/task records, development ledger/status, production trial runbook, development event, run manifest, and generated governance dashboard/status views.
- Model changes: No runtime model behavior change.
- Parameter changes: No active parameter value change.
- Commands run: `plan-production-launch` with merged PR #14 metadata and expected head SHA; arXiv unit tests; root governance tests; project governance validator; dashboard generator; changed-only enforce-sync semantic validator; `git diff --check`; project cache scan; storage check.
- Test results: launch gate expected blocked with PR/default-branch gates passing and only `launch_confirmed`, `default_branch_ref`, `runner_ref`, `smtp_secret_ref`, `release_target_ref`, `workflow_vars_ref`, and `trial_start_workflow_ref` missing; 143 arXiv tests OK; 83 root governance tests OK; project governance errors 0 warnings 0; changed-only enforce-sync semantic errors 0 warnings 0; dashboard generation PASS; diff check exit 0; no arXiv `__pycache__` or `.pyc`; pre-shrink storage arXiv 1.6M, `.git` 89M, worktree 221M.
- Successes: PR #14 is merged; local `main` is at merge commit `9616264221cecc8077fc862692ec6025f1e4872b`; workflow files are present on default branch; post-merge `plan-production-launch` no longer blocks on draft/unmerged PR or head SHA mismatch.
- Failures: No workflow runs or combined status checks exist for the merge commit; launch still blocks because durable external refs and explicit confirmation are missing.
- Decisions: Do not dispatch the trial start workflow until durable refs and explicit launch confirmation are available.
- Remaining risks: Semantic coverage remains planned and not machine verified; production acceptance still requires default-branch trial start evidence, live source pass on the runner, real SMTP and Release refs, resource telemetry, weekly/monthly replay, recovery drill, and 30 unique daily production evidence entries.
- Rollback: Revert the post-merge phase record, delivery task, ledger/status/runbook updates, run manifest, event record, and generated dashboard/status changes.
- Next step: Provision or record durable readiness refs for runner, SMTP secrets, Release target, workflow variables, default-branch workflow location, and launch confirmation; then rerun `plan-production-launch` before dispatching the trial start workflow.

### `ITER-20260621-033`

- Date: 2026-06-22
- Fact level: EXTRACTED for machine selector/fingerprint validation and HUMAN_REVIEW_REQUIRED remainder binding.
- Version before: 0.11.19
- Version after: 0.11.19
- Base commit: b52b88c1c7eadba64cb98fef655edc828f92b751
- Result commit: PENDING
- Task IDs: GOV-SEMANTIC-ADP-001
- Goal: Move arXiv Daily Push semantic coverage from planned to in-progress without changing runtime behavior.
- Assumptions: Partial semantic extraction is valuable only when machine selectors point at implementation/config/test surfaces, not at the governance registry itself.
- Files changed: governance project registry, arXiv parameter registry semantic columns, formula registry semantic fields, delivery task, version matrix, ledger/status, run manifest, and root governance tests/dashboard.
- Model changes: No runtime model behavior change.
- Parameter changes: No active parameter value change; semantic metadata added for 45 active parameter selectors.
- Commands run: `validate_semantic_extractors.py arxiv-daily-push`; `validate_project_governance.py --project arxiv-daily-push`; root governance unittest discover; arXiv unit test discover; `generate_governance_dashboard.py --write`; `validate_project_governance.py --changed-only --enforce-sync --semantic --base-ref origin/main`; `git diff --check`; arXiv cache scan; storage check.
- Test results: semantic extractor checked 45 active parameters and 9 active formulas with no errors; project governance errors 0 warnings 0; root governance tests 84 OK; arXiv unit tests 143 OK; dashboard generation PASS; changed-only enforce-sync semantic errors 0 warnings 0 with `arxiv-daily-push` changed and all registered project validation errors 0 warnings 0; `git diff --check` exit 0; no arXiv `__pycache__` or `.pyc`; pre-shrink storage worktree 221M, `arxiv-daily-push` 1.7M, `.git` 89M.
- Successes: `validate_semantic_extractors.py arxiv-daily-push` checks 45 active parameters and 9 active formula fingerprints with no errors; the all-project semantic drift gate also passes after temporarily restoring full registered project validation context.
- Failures: 107 active parameters and 22 active formulas still require follow-up machine selectors or explicit human review before semantic coverage can become machine_verified.
- Decisions: Keep semantic coverage `in_progress` and keep `GOV-SEMANTIC-ADP-001` open until the remaining semantic surface is resolved.
- Remaining risks: Production launch and production acceptance remain blocked by external refs, runner/secrets/Release evidence, trial start evidence, and 30-day operational evidence.
- Rollback: Remove ArXiv semantic extractor enablement, semantic registry columns/fields, semantic run manifest/event, generated status/dashboard changes, and this test update.
- Next step: Expand selectors for the remaining active parameters/formulas or decide which should stay as owner-approved HUMAN_REVIEW_REQUIRED.

### `ITER-20260621-034`

- Date: 2026-06-22
- Fact level: EXTRACTED for additional machine selector/fingerprint validation and HUMAN_REVIEW_REQUIRED remainder binding.
- Version before: 0.11.19
- Version after: 0.11.19
- Base commit: cc893e4e11ffe690a8f0d6010053c7a1ab5a09b4
- Result commit: PENDING
- Task IDs: GOV-SEMANTIC-ADP-001
- Goal: Expand arXiv Daily Push semantic coverage without changing runtime behavior.
- Assumptions: Remaining parameters that describe external production refs, operational evidence, or composite behavioral assertions stay HUMAN_REVIEW_REQUIRED until a durable source selector is explicit.
- Files changed: arXiv parameter registry semantic columns, formula registry semantic fields, governance project registry, delivery task, version matrix, ledger/status, run manifest, development event, and root governance tests/dashboard.
- Model changes: No runtime model behavior change.
- Parameter changes: No active parameter value change; semantic metadata added for 27 more active parameter selectors.
- Commands run: `validate_semantic_extractors.py arxiv-daily-push`; `validate_project_governance.py --project arxiv-daily-push`; root governance unittest discover; arXiv unit test discover; `generate_governance_dashboard.py --write`; `validate_project_governance.py --changed-only --enforce-sync --semantic --base-ref origin/main`; `git diff --check`; arXiv cache scan; storage check.
- Test results: semantic extractor checked 72 active parameters and 31 active formulas with no errors; project governance errors 0 warnings 0 after temporarily restoring full registered project validation context; root governance tests 85 OK; arXiv unit tests 143 OK; dashboard generation PASS; changed-only enforce-sync semantic errors 0 warnings 0 with `arxiv-daily-push` changed and all registered project validation errors 0 warnings 0; `git diff --check` exit 0 after LF normalization; no arXiv `__pycache__` or `.pyc`; pre-shrink storage worktree 221M, `arxiv-daily-push` 1.7M, `.git` 89M.
- Successes: `validate_semantic_extractors.py arxiv-daily-push` checks 72 active parameters and all 31 active formula fingerprints with no errors; the all-project semantic drift gate also passes after temporarily restoring full registered project validation context.
- Failures: 80 active parameters still require follow-up machine selectors or explicit human review before semantic coverage can become machine_verified.
- Decisions: Keep semantic coverage `in_progress` and keep `GOV-SEMANTIC-ADP-001` open until the remaining parameter surface is resolved.
- Remaining risks: Production launch and production acceptance remain blocked by external refs, runner/secrets/Release evidence, trial start evidence, and 30-day operational evidence.
- Rollback: Remove the second semantic extractor expansion, `GOV-SEMANTIC-ADP-EXTRACT-002.json`, generated status/dashboard changes, event update, and this test update.
- Next step: Resolve the remaining 80 parameters through machine selectors where possible, then provision durable production launch refs before trial start.

### `ITER-20260621-035`

- Date: 2026-06-22
- Fact level: EXTRACTED for additional existing-selector parameter validation and HUMAN_REVIEW_REQUIRED remainder binding.
- Version before: 0.11.19
- Version after: 0.11.19
- Base commit: 579b9a0b621ac7b1cb8b26216664ec3eda1b920c
- Result commit: PENDING
- Task IDs: GOV-SEMANTIC-ADP-001
- Goal: Narrow the remaining arXiv Daily Push semantic review surface without changing runtime behavior.
- Assumptions: Only direct existing selectors that matched `active_value` in preflight are promoted to MACHINE_VERIFIED; production refs, real delivery probes, composite behavioral assertions, and 30-day operating evidence remain HUMAN_REVIEW_REQUIRED.
- Files changed: arXiv parameter registry semantic columns, governance project registry, delivery task, version matrix, ledger/status, run manifest, development event, and root governance tests/dashboard.
- Model changes: No runtime model behavior change.
- Parameter changes: No active parameter value change; semantic metadata added for 21 more active parameter selectors.
- Commands run: `validate_semantic_extractors.py arxiv-daily-push`; `validate_project_governance.py --project arxiv-daily-push`; root governance unittest discover; arXiv unit test discover; `generate_governance_dashboard.py --write`; `validate_project_governance.py --changed-only --enforce-sync --semantic --base-ref origin/main`; `git diff --check`; arXiv cache scan; storage check.
- Test results: semantic extractor checked 93 active parameters and 31 active formulas with no errors; project governance errors 0 warnings 0; root governance tests 86 OK; arXiv unit tests 143 OK; dashboard generation PASS after temporarily restoring full registered project validation context; changed-only enforce-sync semantic errors 0 warnings 0 with `arxiv-daily-push` changed and all registered project validation errors 0 warnings 0; `git diff --check` exit 0; no arXiv `__pycache__` or `.pyc`; pre-shrink storage worktree 222M, `arxiv-daily-push` 1.7M, `.git` 90M.
- Successes: Existing selector preflight promoted run/stage enums, arXiv adapter id, media/download disabled gates, scheduler workflow fields, trial-day constants, and trial-start manual confirmation to machine-checked evidence.
- Failures: 59 active parameters still require follow-up machine selectors, explicit owner review, or external production evidence before semantic coverage can become machine_verified.
- Decisions: Keep semantic coverage `in_progress` and keep `GOV-SEMANTIC-ADP-001` open until the remaining parameter surface is resolved.
- Remaining risks: Production launch and production acceptance remain blocked by external refs, runner/secrets/Release evidence, trial start evidence, and 30-day operational evidence.
- Rollback: Remove the third semantic extractor expansion, `GOV-SEMANTIC-ADP-EXTRACT-003.json`, generated status/dashboard changes, event update, and this test update.
- Next step: Either add narrowly scoped selector transforms for composite remaining parameters or provision durable production launch refs before trial start.

### `ITER-20260621-036`

- Date: 2026-06-22
- Fact level: EXTRACTED for selector transform behavior, additional parameter validation, and HUMAN_REVIEW_REQUIRED remainder binding.
- Version before: 0.11.19
- Version after: 0.11.19
- Base commit: 662451767eb280765ea01f0d08bf7f54c2add0ec
- Result commit: PENDING
- Task IDs: GOV-SEMANTIC-ADP-001
- Goal: Add narrowly scoped semantic selector transforms and reduce the remaining arXiv Daily Push review surface without changing runtime behavior.
- Assumptions: `contains`, `contains_all`, `filter`, and ordered join transforms only inspect deterministic source/config/workflow text and constants; parameters that depend on real external refs or production evidence remain HUMAN_REVIEW_REQUIRED.
- Files changed: semantic extractor validator, root governance tests, arXiv parameter registry semantic columns, governance project registry, delivery task, version matrix, ledger/status, run manifest, development event, and dashboard.
- Model changes: No arXiv Daily Push runtime model behavior change; root semantic extractor selector behavior expanded for governance validation only.
- Parameter changes: No active parameter value change; semantic metadata added for 38 more active parameter selectors.
- Commands run: selector transform focused tests; `validate_semantic_extractors.py arxiv-daily-push`; `validate_project_governance.py --project arxiv-daily-push`; root governance unittest discover; arXiv unit test discover; `generate_governance_dashboard.py --write`; `validate_project_governance.py --changed-only --enforce-sync --semantic --base-ref origin/main`; `git diff --check`; arXiv cache scan; storage check.
- Test results: selector transform focused tests 2 OK; semantic extractor checked 131 active parameters and 31 active formulas with no errors; project governance errors 0 warnings 0; root governance tests 88 OK; arXiv unit tests 143 OK; dashboard generation PASS after temporarily restoring full registered project validation context; changed-only enforce-sync semantic errors 0 warnings 0 with `arxiv-daily-push` changed and all registered project validation errors 0 warnings 0; manifest JSON and `git diff --check` pass; no arXiv `__pycache__` or `.pyc`; pre-shrink storage worktree 222M, `arxiv-daily-push` 1.8M, `.git` 90M.
- Successes: Selector transforms can now machine-check source text containment, subset filtering, and deterministic set ordering; 38 additional active parameters are machine-checked.
- Failures: 21 active parameters still require follow-up machine selectors, explicit owner review, or external production evidence before semantic coverage can become machine_verified.
- Decisions: Keep semantic coverage `in_progress` and keep `GOV-SEMANTIC-ADP-001` open.
- Remaining risks: Production launch and production acceptance remain blocked by external refs, runner/secrets/Release evidence, trial start evidence, and 30-day operational evidence.
- Rollback: Revert the selector transform changes, remove the fourth semantic extractor expansion, `GOV-SEMANTIC-ADP-EXTRACT-004.json`, generated status/dashboard changes, event update, and test update.
- Next step: Resolve the remaining external/composite parameters or provision durable production launch refs before trial start.

### `ITER-20260621-037`

- Date: 2026-06-22
- Fact level: EXTRACTED for final semantic selector behavior, active parameter validation, and machine_verified coverage binding.
- Version before: 0.11.19
- Version after: 0.11.19
- Base commit: d7ad354519374946c70440abae213410c2cb061d
- Result commit: PENDING
- Task IDs: GOV-SEMANTIC-ADP-001
- Goal: Complete machine semantic coverage for arXiv Daily Push active parameters and formulas without changing runtime behavior.
- Assumptions: Final selectors inspect deterministic source/config/workflow text and Python AST constants only; external production evidence remains outside semantic registry completion and still blocks Phase 11 production acceptance.
- Files changed: semantic extractor validator, root governance tests, arXiv parameter registry semantic columns, governance project registry, delivery task, version matrix, ledger/status, run manifest, development event, and dashboard.
- Model changes: No arXiv Daily Push runtime model behavior change; root semantic extractor selector behavior expanded for governance validation only.
- Parameter changes: No active parameter value change; semantic metadata added for the final 21 active parameter selectors.
- Commands run: selector transform focused test; selector probe for the final 21 parameters; `validate_semantic_extractors.py arxiv-daily-push`; `validate_project_governance.py --project arxiv-daily-push`; root governance unittest discover; arXiv unit test discover; `generate_governance_dashboard.py --write`; `validate_project_governance.py --changed-only --enforce-sync --semantic --base-ref origin/main`; manifest JSON parse; `git diff --check`; arXiv cache scan; storage check.
- Test results: selector transform focused test 1 OK; selector probe matched all final 21 active parameter values; semantic extractor checked 152 active parameters and 31 active formulas with no errors; project governance errors 0 warnings 0; root governance tests 89 OK; arXiv unit tests 143 OK; dashboard generation PASS after temporarily restoring full registered project validation context; changed-only enforce-sync semantic errors 0 warnings 0 with `arxiv-daily-push` changed and all registered project validation errors 0 warnings 0; manifest JSON parse passed; `git diff --check` passed after EOF cleanup; no arXiv `__pycache__` or `.pyc`; pre-shrink storage worktree 222M, `arxiv-daily-push` 1.8M, `.git` 90M.
- Successes: All 152 active parameters and all 31 active formulas machine-check under `GOV-SEMANTIC-ADP-001`; next tracked task is external production trial start provisioning.
- Failures: No active semantic registry rows remain HUMAN_REVIEW_REQUIRED; production launch and production acceptance remain blocked by external runner/secrets/Release/workflow/trial evidence.
- Decisions: Mark semantic coverage `machine_verified` and complete `GOV-SEMANTIC-ADP-001`; keep production launch/30-day acceptance blocked until real external evidence exists.
- Remaining risks: Production launch and production acceptance remain blocked by external refs, runner/secrets/Release evidence, trial start evidence, and 30-day operational evidence.
- Rollback: Revert the final selector transform changes, remove the fifth semantic extractor expansion, `GOV-SEMANTIC-ADP-EXTRACT-005.json`, generated status/dashboard changes, event update, and test update.
- Next step: Provision durable production refs and run the default-branch trial start workflow with explicit confirmation.

### `ITER-20260621-038`

- Date: 2026-06-22
- Fact level: EXTRACTED from GitHub PR #32 metadata, main Project Governance CI metadata, local default-branch workflow file presence, and the `plan-production-launch` precheck result.
- Version before: 0.11.19
- Version after: 0.11.19
- Base commit: df28c70f255d4db0cabf15d6555ce34a8b2fa560
- Result commit: PENDING
- Task IDs: ADP-PHASE11-PRODUCTION-TRIAL-START-022
- Goal: Record a no-secret production trial start precheck after PR #32 merged to `main`.
- Assumptions: `default_branch_ref` and `trial_start_workflow_ref` can be proven from current Git/default-branch state without reading secrets or dispatching workflows; private runner, SMTP secret, Release target, workflow variable readiness, and explicit launch confirmation still require external owner-provisioned refs.
- Files changed: production trial start precheck phase record, run manifest, development event, delivery task/status sources, runbook, version matrix, and generated governance dashboard/status files.
- Model changes: No arXiv Daily Push runtime model behavior change.
- Parameter changes: No active parameter value change.
- Commands run: GitHub PR #32 metadata fetch; GitHub Actions run lookup for merge commit `df28c70f255d4db0cabf15d6555ce34a8b2fa560`; `plan-production-launch` with PR #32 metadata, expected head SHA, merged default-branch ref, and default-branch trial-start workflow ref; focused production launch/workflow/CLI tests; arXiv unit test discover; root governance unittest discover; dashboard generation; project governance validation; changed-only enforce-sync semantic validation; `git diff --check`.
- Test results: PR #32 metadata shows closed/merged/non-draft/base main with head SHA `426709648fde32bbaf0d0a1f4f6006318891f5f2` and merge commit `df28c70f255d4db0cabf15d6555ce34a8b2fa560`; main Project Governance CI run `27913796642` completed success with attestation artifact `project-governance-ci-attestation-27913796642-1`; launch precheck exited 2 as expected, with PR/default-branch/workflow gates passing and only `launch_confirmed`, `runner_ref`, `smtp_secret_ref`, `release_target_ref`, and `workflow_vars_ref` blocking; focused production launch/workflow/CLI tests 12 OK; arXiv unit tests 143 OK; root governance tests 91 OK; dashboard generation PASS; project governance errors 0 warnings 0; changed-only enforce-sync semantic errors 0 warnings 0 with all registered project validation errors 0 warnings 0; `git diff --check` pass.
- Successes: `default_branch_ref` and `trial_start_workflow_ref` are now durable and recorded without reading secrets or triggering production side effects.
- Failures: Production launch remains blocked by missing explicit launch confirmation and missing durable runner, SMTP secret, Release target, and workflow variable readiness refs.
- Decisions: Keep `ADP-PHASE11-PRODUCTION-TRIAL-START-022` blocked until remaining external refs exist; do not dispatch `.github/workflows/arxiv-daily-push-trial-start.yml` yet.
- Remaining risks: Production acceptance still requires passing default-branch trial start evidence, live source pass on the runner, real SMTP/Release refs, archived weekly/monthly replay evidence, archived recovery drill evidence, actual resource telemetry, and 30 unique daily production evidence entries.
- Rollback: Remove the precheck phase record, run manifest, development event, runbook/status/delivery task updates, and generated dashboard/status changes.
- Next step: Provision durable `runner_ref`, `smtp_secret_ref`, `release_target_ref`, and `workflow_vars_ref`; then rerun `plan-production-launch` with `--confirm-launch`.

### `ITER-20260621-039`

- Date: 2026-06-22
- Fact level: EXTRACTED from production refs code, CLI command, schema, tests, runbook, and machine semantic registry validation.
- Version before: 0.11.19
- Version after: 0.11.20
- Base commit: 468738d44a2bf99b6fbdebaab85d7360ab731f4f
- Result commit: PENDING
- Task IDs: ADP-PHASE11-PRODUCTION-REFS-BUNDLE-023
- Goal: Add a no-secret production refs readiness bundle before default-branch launch readiness consumes external runner, SMTP, Release, and workflow variable refs.
- Assumptions: The bundle may validate names, ready flags, labels, targets, and durable refs, but it must not read or store SMTP hosts, SMTP ports, usernames, passwords, tokens, API keys, Codex auth, or any credential values.
- Files changed: production refs validator, CLI command and launch integration, production refs schema, focused tests, runbook section, phase record, changelog/version files, model/formula/parameter/traceability registries, delivery task, delivery plan, model spec, and development ledger.
- Model changes: Added MOD-ADP-030 `adp-production-refs-v1`; updated FORM-ADP-024 fingerprint because `cli.py::main` changed; added FORM-ADP-032.
- Parameter changes: Added PARAM-ADP-154 through PARAM-ADP-159 for production refs validator id, required SMTP secret names, required workflow var names, required ref keys, secret-value key blocklist, and no-side-effect safety.
- Commands run: focused production refs/launch pytest; semantic extractor validation; project governance validation; pending full local validation and GitHub CI.
- Test results: focused production refs/launch pytest 9 OK; semantic extractor checked 158 active parameters and 32 active formulas with no errors; project governance content errors reduced to sparse-checkout missing registered project noise plus generated view sync before final pass.
- Successes: `plan-production-refs` now blocks missing required names and secret-like payloads, emits a no-side-effect readiness report, and `plan-production-launch` can consume a passing refs report to fill external readiness refs.
- Failures: No real owner-provisioned runner/SMTP/Release/workflow refs were available in this run; production launch and 30-day acceptance remain blocked.
- Decisions: Keep `ADP-PHASE11-PRODUCTION-TRIAL-START-022` blocked until a real passing production refs report, explicit launch confirmation, and default-branch trial-start workflow evidence exist.
- Remaining risks: Production acceptance still requires passing default-branch trial start evidence, live source pass on the runner, real SMTP/Release refs, archived weekly/monthly replay evidence, archived recovery drill evidence, actual resource telemetry, and 30 unique daily production evidence entries.
- Rollback: Revert production refs module, CLI integration, schema, tests, runbook/phase record/governance updates, and restore version 0.11.19.
- Next step: Provision owner-approved durable `runner_ref`, `smtp_secret_ref`, `release_target_ref`, and `workflow_vars_ref` through `plan-production-refs`, then rerun `plan-production-launch --confirm-launch`.

### `ITER-20260621-040`

- Date: 2026-06-22
- Fact level: EXTRACTED from workflow permissions, scheduler/workflow validators, focused tests, and semantic registry checks.
- Version before: 0.11.20
- Version after: 0.11.21
- Base commit: 4795473858926de7e8e2b9f3eb4e8346ca3a20a2
- Result commit: PENDING
- Task IDs: ADP-PHASE11-RELEASE-PERMISSIONS-024, ADP-PHASE11-PRODUCTION-TRIAL-START-022
- Goal: Require GitHub Actions `contents: write` for the controlled Release evidence paths used by trial-start and scheduled production workflows.
- Assumptions: The permission is necessary for real draft Release evidence, but does not authorize upload by itself; `ADP_ALLOW_RELEASE_UPLOAD=true`, Release target, safe assets, `gh`, and Release delivery validation are still required.
- Files changed: trial-start workflow, scheduled production workflow, scheduler validator, trial-start workflow validator, focused tests, runbook, phase record, version/changelog files, model/formula/parameter/traceability registries, delivery task, and run manifest.
- Model changes: No new runtime model; MOD-ADP-018 and MOD-ADP-028 now include machine-checked Release write permission parameters.
- Formula changes: Refreshed FORM-ADP-020 and FORM-ADP-030 implementation fingerprints after adding Release write permission checks.
- Parameter changes: Added PARAM-ADP-160 and PARAM-ADP-161 for scheduled and trial-start workflow `contents: write` permission requirements.
- Commands run: focused workflow/scheduler tests; trial-start workflow plan CLI JSON parse; production scheduler plan CLI JSON parse; semantic extractor validation; project governance validation; root governance tests; arXiv unit tests; changed-only enforce-sync semantic validation; manifest JSON parse; development_events JSONL parse; git diff check.
- Test results: focused workflow/scheduler tests 6 OK; trial-start workflow plan JSON OK; production scheduler plan JSON OK; semantic extractor checked 160 active parameters and 32 active formulas with no errors; project governance errors 0 warnings 0; root governance tests 93 OK; arXiv unit tests 148 OK; changed-only enforce-sync semantic validation errors 0 warnings 0 across all registered projects; manifest JSON and development_events JSONL parse OK; git diff check OK.
- Successes: Real Release evidence paths will no longer fail only because workflow token permissions are read-only.
- Failures: No workflow dispatch, SMTP send, Release upload, or trial-start evidence was produced in this run.
- Decisions: Keep production launch blocked until external refs and explicit confirmation exist; keep Release upload disabled by default despite `contents: write`.
- Remaining risks: Production acceptance still requires passing default-branch trial start evidence, live source pass on the runner, real SMTP/Release refs, archived weekly/monthly replay evidence, archived recovery drill evidence, actual resource telemetry, and 30 unique daily production evidence entries.
- Rollback: Restore workflow `contents` permissions to read, remove release write permission checks, remove PARAM-ADP-160/161, phase record, manifest, and related governance updates, then restore version 0.11.20.
- Next step: Provision owner-approved durable `runner_ref`, `smtp_secret_ref`, `release_target_ref`, and `workflow_vars_ref`; run `plan-production-refs`, then rerun `plan-production-launch --confirm-launch`.

### `ITER-20260621-041`

- Date: 2026-06-22
- Fact level: EXTRACTED from production refs template code, CLI output, no-secret example JSON, focused tests, and semantic registry checks.
- Version before: 0.11.21
- Version after: 0.11.22
- Base commit: bd3512a3ee85d9b943fa1bf9ef39e7c1fc02cb6c
- Result commit: PENDING
- Task IDs: ADP-PHASE11-PRODUCTION-REFS-TEMPLATE-025, ADP-PHASE11-PRODUCTION-TRIAL-START-022
- Goal: Add a no-secret owner-fillable production refs input template so external runner, SMTP secret-name, Release target, and workflow variable refs can be provisioned without hand-writing the JSON contract or exposing secret values.
- Assumptions: The template may include required GitHub secret names and workflow variable names, but must not include SMTP host values, SMTP port values, usernames, passwords, tokens, API keys, Codex auth, or credential blobs.
- Files changed: production refs module, CLI command, no-secret example input JSON, focused tests, runbook, phase record, version/changelog files, model/formula/parameter/traceability registries, delivery task, and run manifest.
- Model changes: No new runtime model; MOD-ADP-030 now also generates the no-secret input template for the same production refs readiness contract.
- Formula changes: Refreshed FORM-ADP-024 because `cli.py::main` changed, and refreshed FORM-ADP-032 after adding `build_production_refs_input_template`.
- Parameter changes: Added PARAM-ADP-162 for required production refs template sections.
- Commands run: focused production refs/launch/CLI tests; print-production-refs-template JSON parse; generated template through plan-production-refs expected blocked path; example JSON parse; semantic extractor validation; project governance validation; root governance tests; arXiv unit tests; changed-only enforce-sync semantic validation; manifest JSON parse; development_events JSONL parse; git diff check; cache check.
- Test results: focused production refs/launch/CLI tests 16 OK; print-production-refs-template JSON OK; generated template plan-production-refs blocked as expected; example production refs JSON parsed OK; semantic extractor checked 161 active parameters and 32 active formulas with no errors; project governance errors 0 warnings 0; root governance tests 94 OK; arXiv unit tests 150 OK; changed-only enforce-sync semantic validation errors 0 warnings 0 across all registered projects; manifest JSON and development_events JSONL parse OK; git diff check OK; no __pycache__, pyc, pytest, mypy, or ruff cache files remained.
- Successes: Owner provisioning now has a deterministic no-secret template that defaults blocked until real durable refs are filled.
- Failures: No owner-provisioned runner/SMTP/Release/workflow refs, launch confirmation, workflow dispatch, SMTP send, Release upload, or trial-start evidence was produced in this run.
- Decisions: Keep production launch blocked until a filled passing production refs report, explicit launch confirmation, and default-branch trial-start workflow evidence exist.
- Remaining risks: Production acceptance still requires passing default-branch trial start evidence, live source pass on the runner, real SMTP/Release refs, archived weekly/monthly replay evidence, archived recovery drill evidence, actual resource telemetry, and 30 unique daily production evidence entries.
- Rollback: Remove the template function, CLI command, example JSON, tests, runbook/phase record/governance updates, and restore version 0.11.21.
- Next step: Fill the no-secret production refs template with owner-approved durable `runner_ref`, `smtp_secret_ref`, `release_target_ref`, and `workflow_vars_ref`; run `plan-production-refs`, then rerun `plan-production-launch --confirm-launch`.

### `ITER-20260621-042`

- Date: 2026-06-22
- Fact level: EXTRACTED from GitHub metadata discovery code, focused tests, local blocked CLI evidence, and semantic registry checks.
- Version before: 0.11.22
- Version after: 0.11.23
- Base commit: aa8a31f8033f337a7ea0c62ffa446a1c8ca0200b
- Result commit: PENDING
- Task IDs: ADP-PHASE11-PRODUCTION-REFS-GITHUB-DISCOVERY-026, ADP-PHASE11-PRODUCTION-TRIAL-START-022
- Goal: Add a runner-side no-secret GitHub metadata discovery command so external production refs can be produced from actual Actions metadata instead of hand-filled JSON where possible.
- Assumptions: `gh api` can list secret names, variables, and self-hosted runners on the provisioned private runner; secret values remain unreadable and must never be logged.
- Files changed: production refs module, CLI command, focused tests, runbook, phase record, version/changelog files, model/formula/parameter/traceability registries, delivery task, and run manifest.
- Model changes: No new runtime model; MOD-ADP-030 now includes no-secret GitHub metadata discovery for production refs readiness input.
- Formula changes: Refreshed FORM-ADP-024 because `cli.py::main` changed, and refreshed FORM-ADP-032 after adding GitHub metadata discovery helpers.
- Parameter changes: Added PARAM-ADP-163 for the default GitHub repository used by production refs metadata discovery.
- Commands run: focused production refs/launch/CLI tests; local `discover-production-refs` blocked path with missing `gh`; semantic extractor validation; project governance validation; root governance tests; arXiv unit tests; changed-only enforce-sync semantic validation; manifest JSON parse; development_events JSONL parse; git diff check; cache check.
- Test results: focused production refs/launch/CLI tests 19 OK; local `discover-production-refs` exited 2 as expected because `gh` is unavailable and emitted a redacted JSON error; final semantic/governance results recorded in the run manifest.
- Successes: Provisioned-runner refs discovery can now generate the same `adp-production-refs-v1` report from GitHub Actions metadata without exposing secrets.
- Failures: No owner-provisioned runner/SMTP/Release/workflow refs, launch confirmation, workflow dispatch, SMTP send, Release upload, or trial-start evidence was produced in this run.
- Decisions: Keep production launch blocked until a passing discovered or filled production refs report, explicit launch confirmation, and default-branch trial-start workflow evidence exist.
- Remaining risks: Production acceptance still requires passing default-branch trial start evidence, live source pass on the runner, real SMTP/Release refs, archived weekly/monthly replay evidence, archived recovery drill evidence, actual resource telemetry, and 30 unique daily production evidence entries.
- Rollback: Remove GitHub metadata discovery functions, CLI command, tests, runbook/phase record/governance updates, and restore version 0.11.22.
- Next step: Run `discover-production-refs` on the provisioned private runner after owner secrets/vars/runner are configured; feed the report to `plan-production-launch --confirm-launch`.

### `ITER-20260621-043`

- Date: 2026-06-22
- Fact level: EXTRACTED from trial-start workflow ordering, validator checks, focused tests, runbook, and semantic registry checks.
- Version before: 0.11.23
- Version after: 0.11.24
- Base commit: 46932dd4535695326a9f90c34f5f42bdca49d7df
- Result commit: PENDING
- Task IDs: ADP-PHASE11-TRIAL-START-LAUNCH-PREFLIGHT-027, ADP-PHASE11-PRODUCTION-TRIAL-START-022
- Goal: Make the default-branch trial-start workflow run production refs discovery and launch readiness before live source, SMTP, Release, or trial-start gate work.
- Assumptions: The private runner will have `gh` metadata access only after owner provisioning; the workflow may read secret names and variable names but must never read secret values or Codex auth.
- Files changed: trial-start workflow, workflow validator, focused tests, runbook, phase record, version/changelog files, model/formula/parameter/traceability registries, delivery task, event, and run manifest.
- Model changes: No new runtime model; MOD-ADP-028 now requires production refs discovery and launch readiness before trial-start workflow source, SMTP, Release, or start-gate work.
- Formula changes: Refreshed FORM-ADP-030 after adding production refs and launch readiness ordering checks.
- Parameter changes: Updated PARAM-ADP-145 artifact coverage and added PARAM-ADP-164 for trial-start launch preflight ordering.
- Commands run: focused trial-start workflow/production launch/CLI tests; trial-start workflow plan CLI JSON; semantic extractor validation; project governance validation; root governance tests; arXiv unit tests; changed-only enforce-sync semantic validation; manifest JSON parse; development_events JSONL parse; git diff check.
- Test results: focused tests 13 OK; `plan-trial-start-workflow` returned pass with production refs and launch readiness ordering checks; semantic extractor checked 163 active machine-checked parameters and 32 active formulas with no errors; project governance errors 0 warnings 0; root governance tests 96 OK; arXiv unit tests 153 OK; changed-only enforce-sync semantic validation errors 0 warnings 0 across all registered projects; manifest JSON and development_events JSONL parse OK; git diff check OK.
- Successes: The trial-start workflow now fails closed before source/SMTP/Release work if production refs discovery or launch readiness blocks.
- Failures: No owner-provisioned runner/SMTP/Release/workflow refs, workflow dispatch, SMTP send, Release upload, or trial-start evidence was produced in this run.
- Decisions: Keep production launch and Phase 11 acceptance blocked until the default-branch workflow produces real start evidence and the 30-day trial evidence package passes.
- Remaining risks: Production acceptance still requires passing default-branch trial start evidence, live source pass on the runner, real SMTP/Release refs, archived weekly/monthly replay evidence, archived recovery drill evidence, actual resource telemetry, and 30 unique daily production evidence entries.
- Rollback: Remove trial-start workflow production refs and launch precheck steps, revert workflow contract checks, remove PARAM-ADP-164 and related governance records, and restore version 0.11.23.
- Next step: After owner provisioning, dispatch the default-branch trial-start workflow with explicit confirmation and archive the new refs, launch, source, SMTP, Release, and start-gate artifacts.

### `ITER-20260621-044`

- Date: 2026-06-22
- Fact level: EXTRACTED from GitHub-hosted provisioning audit workflow text, focused workflow tests, local blocked discovery output, and semantic registry checks.
- Version before: 0.11.24
- Version after: 0.11.25
- Base commit: 12d022784bc79863ed4ae380ac1638c6bf85ca19
- Result commit: PENDING
- Task IDs: ADP-PHASE11-PROVISIONING-AUDIT-WORKFLOW-028, ADP-PHASE11-PRODUCTION-TRIAL-START-022
- Goal: Add a GitHub-hosted no-secret provisioning audit workflow before private-runner trial-start dispatch.
- Assumptions: The workflow may inspect GitHub Actions metadata for runner labels, secret names, and variable names through `ADP_GITHUB_METADATA_TOKEN` or `github.token`, but it must not read secret values, Codex auth, local media/model/cache artifacts, or dispatch production trial-start work.
- Files changed: provisioning audit workflow, production refs workflow test, runbook, phase record, version/changelog files, model/formula/parameter/traceability registries, delivery task, event, and run manifest.
- Model changes: No new runtime model; MOD-ADP-030 now includes a GitHub-hosted no-secret provisioning audit workflow before private-runner trial-start dispatch.
- Formula changes: No implementation formula change; FORM-ADP-032 documents the provisioning audit wrapper around existing no-secret discovery.
- Parameter changes: Added PARAM-ADP-165 for the GitHub-hosted production provisioning audit workflow.
- Commands run: focused production refs/launch/CLI tests; local `discover-production-refs` blocked path with missing `gh`; semantic extractor validation; project governance validation; root governance tests; arXiv unit tests; changed-only enforce-sync semantic validation; manifest JSON parse; development_events JSONL parse; git diff check.
- Test results: Focused tests and blocked local discovery passed before final governance validation; final validation results are recorded in the run manifest for this iteration.
- Successes: Owner can now run a no-secret GitHub-hosted provisioning audit and archive `adp-production-provisioning-audit` before occupying the private self-hosted runner.
- Failures: No owner-provisioned runner/SMTP/Release/workflow refs, workflow dispatch, SMTP send, Release upload, or trial-start evidence was produced in this run.
- Decisions: Keep production launch and Phase 11 acceptance blocked until provisioning audit, default-branch trial-start, SMTP/Release, replay/recovery/resource, and 30-day daily evidence pass.
- Remaining risks: The audit can prove GitHub metadata only when token permissions can list self-hosted runners, repository secret names, and variables; production acceptance still requires passing default-branch trial start evidence, live source pass on the runner, real SMTP/Release refs, archived weekly/monthly replay evidence, archived recovery drill evidence, actual resource telemetry, and 30 unique daily production evidence entries.
- Rollback: Remove provisioning audit workflow, workflow test, PARAM-ADP-165, phase record, manifest, and related governance records, then restore version 0.11.24.
- Next step: Configure owner-approved GitHub metadata permissions, run the provisioning audit workflow on `main`, then dispatch the default-branch trial-start workflow only after the audit and launch readiness pass.

### `ITER-20260621-045`

- Date: 2026-06-22
- Fact level: EXTRACTED from provisioning audit review code, CLI fixture output, focused tests, and semantic registry checks.
- Version before: 0.11.25
- Version after: 0.11.26
- Base commit: 4e25ce2db01466b1053809d9b4aaeb949837fb4e
- Result commit: PENDING
- Task IDs: ADP-PHASE11-PROVISIONING-AUDIT-REVIEW-029, ADP-PHASE11-PRODUCTION-TRIAL-START-022
- Goal: Add a no-side-effect review gate for downloaded provisioning audit artifacts before private-runner trial-start dispatch.
- Assumptions: The downloaded audit artifact must already be no-secret and generated by the GitHub-hosted provisioning audit workflow; the review command only validates and binds durable refs.
- Files changed: production refs module, CLI command, focused tests, runbook, phase record, version/changelog files, model/formula/parameter/traceability registries, delivery task, event, and run manifest.
- Model changes: No new runtime model; MOD-ADP-030 now includes provisioning audit artifact review.
- Formula changes: Refreshed FORM-ADP-032 after adding `build_provisioning_audit_review` and `validate_provisioning_audit_review`.
- Parameter changes: Added PARAM-ADP-166 for the provisioning audit review validator identifier.
- Commands run: focused production refs/launch/CLI tests; review-provisioning-audit fixture pass and blocked sample; semantic extractor validation; project governance validation; root governance tests; arXiv unit tests; changed-only enforce-sync semantic validation; manifest JSON parse; development_events JSONL parse; git diff check.
- Test results: Focused tests and CLI samples passed before final governance validation; final validation results are recorded in the run manifest for this iteration.
- Successes: A downloaded audit artifact can now be machine-reviewed and bound to durable workflow run and artifact refs before any trial-start dispatch.
- Failures: No owner-run provisioning audit artifact, owner-provisioned runner/SMTP/Release/workflow refs, workflow dispatch, SMTP send, Release upload, or trial-start evidence was produced in this run.
- Decisions: Keep production launch and Phase 11 acceptance blocked until provisioning audit review, default-branch trial-start, SMTP/Release, replay/recovery/resource, and 30-day daily evidence pass.
- Remaining risks: The review proves only downloaded artifact registration; production acceptance still requires passing default-branch trial start evidence, live source pass on the runner, real SMTP/Release refs, archived weekly/monthly replay evidence, archived recovery drill evidence, actual resource telemetry, and 30 unique daily production evidence entries.
- Rollback: Remove provisioning audit review function, CLI command, tests, PARAM-ADP-166, phase record, manifest, and related governance records, then restore version 0.11.25.
- Next step: Run the provisioning audit workflow on `main`, download its artifact, run `review-provisioning-audit` with durable refs, then dispatch the default-branch trial-start workflow only after audit review and launch readiness pass.

### `ITER-20260621-046`

- Date: 2026-06-22
- Fact level: EXTRACTED from two-day simulation code, CLI report, focused tests, full arXiv tests, and semantic registry checks.
- Version before: 0.11.26
- Version after: 0.11.27
- Base commit: c75fa25fc79eed87ef510b4ce990ab663e362db5
- Result commit: PENDING
- Task IDs: ADP-PHASE11-TWO-DAY-SIMULATION-030
- Goal: Satisfy the updated Phase 11 local acceptance target with a deterministic two-day simulation instead of requiring 30 production days.
- Assumptions: The simulation can prove only the local scheduled-path behavior with mocked SMTP and mocked Release boundaries; it must not fetch live network data, read secret values, read Codex auth, retain media/model/cache artifacts, or claim production acceptance.
- Files changed: simulation module, CLI command, focused tests, version/changelog files, model/formula/parameter/traceability registries, delivery task, phase record, event, and run manifest.
- Model changes: Added MOD-ADP-031 for the two-day simulation acceptance gate.
- Formula changes: Refreshed FORM-ADP-024 because `cli.py::main` changed, and added FORM-ADP-033 for two-day simulation validation.
- Parameter changes: Added PARAM-ADP-167 through PARAM-ADP-169 for the simulation model ID, required simulated day count, and no-production-claim safety flags.
- Commands run: focused simulation tests; `run-two-day-simulation` CLI with start date 2026-06-22; simulation report JSON parse; full arXiv unit test discovery; semantic extractor validation; governance manifest and JSONL parse.
- Test results: focused two-day simulation tests 3 OK; two-day simulation CLI status pass with `two_day_simulation_ready=true`, `observed_day_count=2`, and `production_acceptance_claimed=false`; simulation report JSON parse OK; arXiv unit tests 160 OK; semantic extractor checked 168 active parameters and 33 active formulas with no errors.
- Successes: The updated local goal has a durable two-day simulation report covering 2026-06-22 and 2026-06-23, with unique simulated source/publication IDs and explicit no-real-side-effect gates.
- Failures: No real owner-run provisioning audit artifact, owner-provisioned runner/SMTP/Release/workflow refs, workflow dispatch, SMTP send, Release upload, default-branch trial-start run, or 30-day production evidence was produced in this run.
- Decisions: Treat the two-day simulation as sufficient for the updated local Phase 11 acceptance target while preserving the separate real production-trial path as blocked until external owner evidence exists.
- Remaining risks: Real production launch still requires owner-provisioned durable refs, explicit launch confirmation, default-branch workflow evidence, and real SMTP/Release/resource evidence.
- Rollback: Remove the two-day simulation module, CLI command, tests, MOD-ADP-031, FORM-ADP-033, PARAM-ADP-167 through PARAM-ADP-169, phase record, manifest, and related governance records, then restore version 0.11.26.
- Next step: Sync the two-day simulation changes to GitHub and, only if real production launch is requested later, run the provisioning audit and default-branch trial-start path with owner-provided refs.

### `ITER-20260621-047`

- Date: 2026-06-22
- Fact level: EXTRACTED from official arXiv taxonomy/API documentation, Phase 12 implementation, focused tests, and workflow contract checks.
- Version before: 0.11.27
- Version after: 0.12.0
- Base commit: c775a956b29e976c965c0c58e7ba25d250c70eae
- Result commit: PENDING
- Task IDs: ADP-PHASE12-ALL-ARXIV-QUEUE-DELIVERY-031
- Goal: Upgrade scheduled production input from legacy cs.AI-only defaults to all-arXiv primary archive scanning with candidate queue persistence, ROI ranking, one daily lead paper, Release-hosted video artifact link, and email queue summary.
- Assumptions: Phase 12 may prove code and workflow gates with local fixture source batches, but real production remains disabled until owner-provisioned runner networking/TLS, SMTP, Release target, and default-branch workflow evidence pass.
- Files changed: global scan module, CLI, scheduled execution, scheduler validator, trial-start gate/workflow validator, scheduled and trial-start workflows, focused tests, runbook, config examples, README, version/changelog files, model/formula/parameter/traceability registries, delivery task, phase record, event, and run manifest.
- Model changes: Added MOD-ADP-032 `adp-all-arxiv-scan-v1`.
- Formula changes: Added FORM-ADP-034 Phase 12 all-arXiv scan queue delivery gate.
- Parameter changes: Added PARAM-ADP-170 through PARAM-ADP-176 for all-arXiv model id, archive count, per-archive window, queue size, ROI thresholds, ROI weights, and mail video-link policy.
- Commands run: full arXiv unit test discovery; project semantic extractor; targeted root governance manifest tests; project governance changed-only sync check; workflow legacy-query grep; JSON/CSV format checks; git diff check.
- Test results: arXiv unit tests 165 OK; semantic extractor checked 34 active formulas and 175 active parameters with no errors; targeted root governance tests 2 OK; changed-only governance sync reported 0 errors and 0 warnings before the validator continued into unrelated missing project directories; workflow legacy-query grep found no `ADP_ARXIV_QUERY` or `cat:cs.AI` production entry; manifest JSON, JSONL, CSV width, and git diff checks passed.
- Successes: Production workflows no longer default to `cat:cs.AI`; scheduled daily-run can restore/persist a candidate queue, scan the arXiv primary archive set, rank by requested ROI/learning criteria, emit Phase 12 artifacts, and require a Release video artifact link before real SMTP can count.
- Failures: No production variables were enabled, no real SMTP message was sent, no real Release was uploaded, no live runner all-arXiv fetch was proven, and no real MP4 rendering was claimed.
- Decisions: Keep `ADP_PRODUCTION_ENABLED`, `ADP_SCHEDULED_RUN_ENABLED`, `ADP_ALLOW_SMTP_SEND`, and `ADP_ALLOW_RELEASE_UPLOAD` disabled until Phase 12 is verified on the owner-provisioned runner and Release/SMTP evidence passes.
- Remaining risks: Real production launch still requires owner-provisioned GitHub Actions runner networking/TLS, SMTP app password, Release target, default-branch workflow evidence, real Release-hosted video/MP4 artifacts, resource telemetry, replay/recovery evidence, and 30 daily production entries.
- Rollback: Remove `global_scan.py`, Phase 12 CLI commands, workflow updates, delivery-package gates, tests, runbook/config/governance updates, and restore version 0.11.27.
- Next step: Open PR for Phase 12, wait for CI, merge only after checks pass, then configure production variables only after runner-side all-arXiv scan, queue, Release link, and SMTP evidence pass.

### `ITER-20260621-048`

- Date: 2026-06-22
- Fact level: EXTRACTED from workflow contracts, live dry-run command implementation, MP4 render implementation, focused tests, and full arXiv unit tests.
- Version before: 0.12.0
- Version after: 0.12.1
- Base commit: 05c69c6522a74901f33350e03046f03a6f47b061
- Result commit: PENDING
- Task IDs: ADP-PHASE12-PRODUCTION-ENABLEMENT-032
- Goal: Prepare Phase 12 production enablement for true cloud execution without self-hosted runner dependency, while adding live all-arXiv dry-run and real MP4 artifact gates before production can be enabled.
- Assumptions: GitHub-hosted `ubuntu-latest` with installed `ffmpeg` is sufficient for the lightweight MP4 artifact; production schedule, SMTP, and Release uploads remain disabled until explicit cloud evidence and owner-controlled manual tests pass.
- Files changed: cloud dry-run workflow, scheduled/trial-start/production-trial/provisioning-audit workflows, global scan, video rendering, production preflight, scheduler/trial workflow validators, simulation fixtures, focused tests, version/changelog/governance records, and Phase 12 cloud phase record.
- Model changes: Added MOD-ADP-033 `adp-phase12-cloud-enablement-v1`.
- Formula changes: Added FORM-ADP-035 for cloud dry-run, GitHub-hosted runner, real MP4, and side-effect gates; FORM-ADP-034 requires `.mp4` video links rather than JSON manifests.
- Parameter changes: Added PARAM-ADP-177 through PARAM-ADP-180 for live dry-run id, MP4 render id, cloud disk threshold, and GitHub-hosted runner requirement.
- Commands run: full arXiv unit tests; workflow self-hosted grep; focused workflow/preflight/video/global scan tests; changed-only governance validation; GitHub Actions run `27924078126`.
- Test results: arXiv unit tests 171 OK; all arXiv workflow YAML files contain no `self-hosted`, `runner_label`, or `ADP_SELF_HOSTED`; GitHub Actions run `27924078126` passed with 20/20 archive buckets, 16 candidates, sample daily input, and a real MP4 artifact of 80246 bytes.
- Successes: Active workflows now target GitHub-hosted runners, live dry-run verified all 20 archive buckets and emitted a sample daily input, real MP4 rendering succeeded through ffmpeg, and email video links require a Release `.mp4` asset.
- Failures: No real GitHub Release was uploaded, no Gmail SMTP test email was sent, and no production schedule variables were enabled.
- Decisions: Keep production launch blocked until Release `.mp4`, Gmail SMTP manual test, PR CI, and owner confirmation pass.
- Remaining risks: PR CI, SMTP secret configuration, Release permissions, and controlled manual side-effect tests remain before production enablement.
- Rollback: Revert version 0.12.1 changes, remove the cloud dry-run workflow and MP4 render command, restore version 0.12.0, and keep production variables disabled.
- Next step: Push branch, open PR, run the Phase 12 cloud dry-run on GitHub-hosted Actions, inspect `adp-phase12-cloud-dry-run`, then run controlled Release/Gmail SMTP manual test only after dry-run passes.

### `ITER-20260621-049`

- Date: 2026-06-22
- Fact level: EXTRACTED from manual workflow contract, focused tests, and scheduled execution delivery-package behavior.
- Version before: 0.12.1
- Version after: 0.12.2
- Base commit: beb075a419b8b4c6cb6f73807284dcaa930866e2
- Result commit: PENDING
- Task IDs: ADP-PHASE12-MANUAL-DELIVERY-TEST-033
- Goal: Prepare the controlled GitHub Release plus Gmail SMTP manual test path requested after PR CI, without enabling production scheduling.
- Assumptions: The manual workflow will be dispatched from the default branch after PR CI and merge; it may perform one Release upload and one Gmail SMTP send only after the exact confirmation string is supplied.
- Files changed: manual delivery workflow, focused workflow test, scheduled execution email-link assertion, version/changelog files, model/formula/parameter/traceability registries, delivery task, phase record, event, and run manifest.
- Model changes: Added MOD-ADP-034 `adp-manual-delivery-test-v1`.
- Formula changes: Added FORM-ADP-036 for default-branch manual Release + SMTP test gating.
- Parameter changes: Added PARAM-ADP-181 through PARAM-ADP-184 for confirmation string, default-branch guard, real side-effect flags, and Release-backed email path.
- Commands run: focused manual workflow and scheduled execution tests.
- Test results: focused manual workflow and scheduled execution tests 8 OK.
- Successes: The manual workflow has no schedule trigger, uses GitHub-hosted `ubuntu-latest`, defaults Gmail SMTP host/port/username, requires `ADP_SMTP_PASSWORD`, creates Release assets before SMTP, and sends no video attachment.
- Failures: No real GitHub Release has been uploaded and no Gmail SMTP email has been sent in this preparation commit.
- Decisions: Keep production schedule disabled until this manual workflow is merged, dispatched, and verified by received email plus Release/video links.
- Remaining risks: GitHub workflow_dispatch availability requires the workflow on the default branch; missing/invalid Gmail app password or GitHub token Release permission will fail the manual test.
- Rollback: Remove the manual delivery workflow, tests, version 0.12.2 governance records, and restore version 0.12.1 while keeping production variables disabled.
- Next step: Commit and push this PR update, wait for PR CI green, merge the safe manual-test entrypoint to main, then run the GitHub Actions manual delivery workflow with the confirmation string.

## Unknown Historical Periods

None for this new project baseline.

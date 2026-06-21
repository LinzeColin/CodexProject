# DEVELOPMENT_LEDGER

Project: `arxiv-daily-push`
Active product version: `0.11.15`
Governance spec version: `1.0.0`

The append-only machine record is `development_events.jsonl`.

## Current State

- Product version: 0.11.15
- Current phase: E
- Current gate: ADP-PHASE11-TRIAL-RECOVERY-EVIDENCE-PASS
- Confirmed iteration count: 26
- Reconstructed event count: 0
- Current task: NONE
- Blockers: Production acceptance still requires default-branch scheduled execution, live source ingest pass on the runner, real SMTP and Release refs, resource telemetry, weekly/monthly replay, recovery drill, and 30 unique daily production evidence entries; those are not claimed by this handoff.

## Phase Matrix

| Phase | Name | Status | Exit criteria | Evidence |
|---|---|---|---|---|
| A | Phase 1 repository foundation | completed | CLI skeleton, governance records, and tests pass | `docs/phase_records/PHASE_01.md` |
| B | Data contracts and arXiv source/ranking | completed | generic schemas and arXiv adapter/ranking gates pass | `docs/phase_records/PHASE_02.md`; `docs/phase_records/PHASE_03.md`; `docs/phase_records/PHASE_04.md` |
| C | Evidence and text lesson | completed | Claim Ledger and lesson verification pass | `docs/phase_records/PHASE_05.md`; `docs/phase_records/PHASE_06.md` |
| D | TTS/video/local pipeline/GitHub automation | completed | media gates, daily pipeline, and handoff gate pass | `docs/phase_records/PHASE_07.md`; `docs/phase_records/PHASE_08.md`; `docs/phase_records/PHASE_09.md`; `docs/phase_records/PHASE_10.md` |
| E | Weekly/monthly trial and handoff | completed | handoff readiness, trial evidence validator, production preflight, live ingest, SMTP delivery, Release delivery, scheduler gate, scheduled execution driver, daily input builder, trial ledger update, trial ledger state persistence, trial ops evidence annotation, trial replay evidence, and trial recovery evidence generated; production acceptance blockers documented | `docs/phase_records/PHASE_11.md`; `docs/phase_records/PHASE_11_TRIAL_EVIDENCE_VALIDATOR.md`; `docs/phase_records/PHASE_11_PRODUCTION_PREFLIGHT.md`; `docs/phase_records/PHASE_11_LIVE_ARXIV_INGEST.md`; `docs/phase_records/PHASE_11_SMTP_DELIVERY.md`; `docs/phase_records/PHASE_11_RELEASE_DELIVERY.md`; `docs/phase_records/PHASE_11_PRODUCTION_SCHEDULER.md`; `docs/phase_records/PHASE_11_SCHEDULED_EXECUTION_DRIVER.md`; `docs/phase_records/PHASE_11_DAILY_INPUT_BUILDER.md`; `docs/phase_records/PHASE_11_TRIAL_LEDGER_UPDATE.md`; `docs/phase_records/PHASE_11_TRIAL_LEDGER_STATE.md`; `docs/phase_records/PHASE_11_TRIAL_OPS_EVIDENCE.md`; `docs/phase_records/PHASE_11_TRIAL_REPLAY_EVIDENCE.md`; `docs/phase_records/PHASE_11_TRIAL_RECOVERY_EVIDENCE.md` |

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

## Unknown Historical Periods

None for this new project baseline.
